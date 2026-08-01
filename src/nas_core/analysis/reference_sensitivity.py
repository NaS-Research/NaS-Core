"""Outcome-blind fixed-reference sensitivity diagnostics for GSE81538."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import re
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from nas_core.domain.matrix_audit import GSE81538MatrixAuditReceipt, MatrixAuditDecision
from nas_core.domain.method_dependency import Pam50CentroidCandidateArtifact
from nas_core.domain.reference_construction import GSE81538ReferenceConstructionReceipt
from nas_core.domain.reference_development import ReferenceDevelopmentProtocol
from nas_core.domain.reference_metadata import GSE81538ReferenceMetadataReceipt
from nas_core.domain.reference_sensitivity import (
    GSE81538ReferenceSensitivityPlan,
    GSE81538ReferenceSensitivityReceipt,
    ReferenceSensitivityDecision,
)
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore

ER_PATTERN = re.compile(
    r"^!Sample_characteristics_ch1 = er consensus: (?P<code>[0-3])$"
)


class ReferenceSensitivityError(RuntimeError):
    """Raised when sensitivity provenance or field isolation changes."""


class GSE81538ReferenceSensitivityService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def execute(
        self,
        plan: GSE81538ReferenceSensitivityPlan,
        matrix_audit: GSE81538MatrixAuditReceipt,
        metadata_receipt: GSE81538ReferenceMetadataReceipt,
        construction_receipt: GSE81538ReferenceConstructionReceipt,
        protocol: ReferenceDevelopmentProtocol,
        candidate: Pam50CentroidCandidateArtifact,
        *,
        plan_path: Path,
        matrix_audit_path: Path,
        metadata_receipt_path: Path,
        construction_receipt_path: Path,
        protocol_path: Path,
        candidate_path: Path,
        code_revision: str,
        executed_at: datetime | None = None,
    ) -> GSE81538ReferenceSensitivityReceipt:
        self._validate_provenance(
            plan,
            matrix_audit,
            metadata_receipt,
            construction_receipt,
            protocol,
            candidate,
            matrix_audit_path=matrix_audit_path,
            metadata_receipt_path=metadata_receipt_path,
            construction_receipt_path=construction_receipt_path,
            protocol_path=protocol_path,
            candidate_path=candidate_path,
        )
        self._verify_object(plan.matrix_object_key, plan.matrix_sha256)
        self._verify_object(plan.metadata_object_key, plan.metadata_sha256)
        manifest_bytes = self._verify_object(
            plan.selection_manifest_object_key,
            plan.selection_manifest_sha256,
        )
        reference_bytes = self._verify_object(
            plan.primary_reference_object_key,
            plan.primary_reference_sha256,
        )
        manifest = json.loads(manifest_bytes)
        records = manifest.get("records")
        if not isinstance(records, list) or len(records) != plan.expected_sample_count:
            raise ReferenceSensitivityError("selection manifest dimensions changed")
        selected_titles = [record.get("sample_title") for record in records]
        raw_accessions = [record.get("geo_accession") for record in records]
        if (
            not all(isinstance(item, str) for item in selected_titles)
            or len(set(selected_titles)) != plan.expected_sample_count
            or not all(isinstance(item, str) for item in raw_accessions)
            or len(set(raw_accessions)) != plan.expected_sample_count
        ):
            raise ReferenceSensitivityError("selection manifest identifiers are invalid")
        selected_accessions = {str(item) for item in raw_accessions}

        reference_artifact = json.loads(reference_bytes)
        primary_reference = reference_artifact.get("reference")
        if not isinstance(primary_reference, dict):
            raise ReferenceSensitivityError("primary reference is invalid")
        if list(reference_artifact.get("gene_order", [])) != candidate.gene_order:
            raise ReferenceSensitivityError("primary reference gene order changed")

        vectors = self._read_selected_panel(
            plan.matrix_object_key,
            selected_titles=selected_titles,
            gene_order=candidate.gene_order,
            aliases=candidate.historical_aliases,
        )
        median_reference = np.asarray(
            [statistics.median(vectors[gene]) for gene in candidate.gene_order],
            dtype=float,
        )
        stored_reference = np.asarray(
            [primary_reference[gene] for gene in candidate.gene_order],
            dtype=float,
        )
        if not np.array_equal(median_reference, stored_reference):
            raise ReferenceSensitivityError("primary reference cannot be reproduced exactly")
        trimmed_reference = np.asarray(
            [
                self._trimmed_mean(
                    vectors[gene],
                    plan.trimmed_mean_fraction_each_tail,
                )
                for gene in candidate.gene_order
            ],
            dtype=float,
        )
        difference = trimmed_reference - median_reference
        matrix = np.asarray(
            [[vectors[gene][index] for gene in candidate.gene_order] for index in range(100)],
            dtype=float,
        )
        profile_correlations = [
            self._spearman(row - median_reference, row - trimmed_reference)
            for row in matrix
        ]
        if not all(math.isfinite(value) for value in profile_correlations):
            raise ReferenceSensitivityError("centered-profile correlation is undefined")

        remaining_counts = self._remaining_eligible_counts(
            plan.metadata_object_key,
            selected_accessions=selected_accessions,
        )
        negative_available = remaining_counts[0]
        positive_available = remaining_counts[3]
        alternative_feasible = (
            min(negative_available, positive_available)
            >= plan.alternative_target_per_stratum
        )
        artifact = {
            "schema_version": "1.0.0",
            "study_id": plan.study_id,
            "source_accession": plan.source_accession,
            "input_scale": plan.input_scale,
            "primary_reference_sha256": plan.primary_reference_sha256,
            "selection_manifest_sha256": plan.selection_manifest_sha256,
            "trimmed_mean_fraction_each_tail": plan.trimmed_mean_fraction_each_tail,
            "gene_order": candidate.gene_order,
            "trimmed_mean_reference": {
                gene: float(trimmed_reference[index])
                for index, gene in enumerate(candidate.gene_order)
            },
            "aggregate_diagnostics": {
                "vector_pearson_correlation": self._pearson(
                    median_reference,
                    trimmed_reference,
                ),
                "vector_spearman_correlation": self._spearman(
                    median_reference,
                    trimmed_reference,
                ),
                "vector_mean_absolute_difference": float(np.mean(np.abs(difference))),
                "vector_maximum_absolute_difference": float(np.max(np.abs(difference))),
                "vector_root_mean_square_difference": float(
                    np.sqrt(np.mean(np.square(difference)))
                ),
                "centered_profile_correlation_minimum": min(profile_correlations),
                "centered_profile_correlation_median": statistics.median(
                    profile_correlations
                ),
                "centered_profile_correlation_mean": statistics.fmean(
                    profile_correlations
                ),
                "next_er_negative_available": negative_available,
                "next_er_positive_available": positive_available,
                "exact_alternative_balanced_reference_feasible": alternative_feasible,
            },
        }
        artifact_bytes = (
            json.dumps(artifact, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
            + "\n"
        ).encode("utf-8")
        if self._store.exists(plan.sensitivity_object_key):
            raise ReferenceSensitivityError("immutable sensitivity artifact already exists")
        self._store.put_bytes(
            plan.sensitivity_object_key,
            artifact_bytes,
            content_type="application/json",
        )
        if self._store.get_bytes(plan.sensitivity_object_key) != artifact_bytes:
            raise ReferenceSensitivityError("stored sensitivity artifact changed")

        return GSE81538ReferenceSensitivityReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            source_accession=plan.source_accession,
            code_revision=code_revision,
            executed_at=executed_at or datetime.now(UTC),
            plan_sha256=sha256(plan_path.read_bytes()),
            matrix_audit_receipt_sha256=sha256(matrix_audit_path.read_bytes()),
            reference_metadata_receipt_sha256=sha256(metadata_receipt_path.read_bytes()),
            reference_construction_receipt_sha256=sha256(
                construction_receipt_path.read_bytes()
            ),
            reference_protocol_sha256=sha256(protocol_path.read_bytes()),
            centroid_candidate_sha256=sha256(candidate_path.read_bytes()),
            all_object_checksums_verified=True,
            primary_sample_count=100,
            primary_gene_count=50,
            parsed_measurement_count=5000,
            trimmed_mean_fraction_each_tail=plan.trimmed_mean_fraction_each_tail,
            trimmed_observations_per_gene=60,
            vector_pearson_correlation=self._pearson(
                median_reference,
                trimmed_reference,
            ),
            vector_spearman_correlation=self._spearman(
                median_reference,
                trimmed_reference,
            ),
            vector_mean_absolute_difference=float(np.mean(np.abs(difference))),
            vector_maximum_absolute_difference=float(np.max(np.abs(difference))),
            vector_root_mean_square_difference=float(
                np.sqrt(np.mean(np.square(difference)))
            ),
            centered_profile_correlation_minimum=min(profile_correlations),
            centered_profile_correlation_median=statistics.median(profile_correlations),
            centered_profile_correlation_mean=statistics.fmean(profile_correlations),
            next_er_negative_available=negative_available,
            next_er_positive_available=positive_available,
            alternative_target_per_stratum=plan.alternative_target_per_stratum,
            exact_alternative_balanced_reference_feasible=alternative_feasible,
            exact_alternative_reference_constructed=False,
            sensitivity_object_key=plan.sensitivity_object_key,
            sensitivity_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
            sensitivity_bytes=len(artifact_bytes),
            sensitivity_immutable_verified=True,
            decision=ReferenceSensitivityDecision.PASS_WITH_LIMITATION,
            limitations=[
                "Only 32 unselected ER-negative records remain, so the exact "
                "next-50-per-stratum alternative is not estimable.",
                "Centered-profile correlations do not execute or validate the PAM50 classifier.",
                "The diagnostics remain conditional on the founder-approved ER-code inference.",
                "No outcome, validation, threshold, or technical-error evidence was used.",
            ],
            participant_identifiers_retained_in_git=False,
            reference_values_retained_in_git=False,
            molecular_values_parsed=True,
            outcome_values_accessed=False,
            validation_data_accessed=False,
            classifier_executed=False,
            generative_ai_received_participant_data=False,
            threshold_tuning_performed=False,
            reference_locked=False,
        )

    @staticmethod
    def _trimmed_mean(values: list[float], fraction: float) -> float:
        ordered = sorted(values)
        trim = int(len(ordered) * fraction)
        retained = ordered[trim : len(ordered) - trim]
        if not retained:
            raise ReferenceSensitivityError("trimmed mean removed every observation")
        return statistics.fmean(retained)

    @staticmethod
    def _pearson(left: np.ndarray, right: np.ndarray) -> float:
        result = float(np.corrcoef(left, right)[0, 1])
        if not math.isfinite(result):
            raise ReferenceSensitivityError("Pearson correlation is undefined")
        return result

    @classmethod
    def _spearman(cls, left: np.ndarray, right: np.ndarray) -> float:
        return cls._pearson(cls._average_ranks(left), cls._average_ranks(right))

    @staticmethod
    def _average_ranks(values: np.ndarray) -> np.ndarray:
        order = np.argsort(values, kind="mergesort")
        ranks = np.empty(len(values), dtype=float)
        cursor = 0
        while cursor < len(values):
            end = cursor + 1
            while end < len(values) and values[order[end]] == values[order[cursor]]:
                end += 1
            ranks[order[cursor:end]] = (cursor + 1 + end) / 2
            cursor = end
        return ranks

    def _verify_object(self, key: str, expected_sha256: str) -> bytes:
        data = self._store.get_bytes(key)
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ReferenceSensitivityError(f"object checksum changed: {key}")
        return data

    def _read_selected_panel(
        self,
        key: str,
        *,
        selected_titles: list[str],
        gene_order: list[str],
        aliases: dict[str, str],
    ) -> dict[str, list[float]]:
        required = set(gene_order)
        vectors: dict[str, list[float]] = {}
        with (
            self._store.open_binary(key) as raw,
            gzip.GzipFile(fileobj=raw, mode="rb") as compressed,
            io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text,
        ):
            reader = csv.reader(text)
            try:
                header = next(reader)
            except StopIteration as error:
                raise ReferenceSensitivityError("matrix is empty") from error
            header_index = {title: index for index, title in enumerate(header)}
            if any(title not in header_index for title in selected_titles):
                raise ReferenceSensitivityError("selected title is absent from matrix")
            indices = [header_index[title] for title in selected_titles]
            for row in reader:
                if len(row) != len(header):
                    raise ReferenceSensitivityError("matrix row width changed")
                canonical = aliases.get(row[0].strip(), row[0].strip())
                if canonical not in required:
                    continue
                if canonical in vectors:
                    raise ReferenceSensitivityError("duplicate retained PAM50 row")
                try:
                    values = [float(row[index]) for index in indices]
                except ValueError as error:
                    raise ReferenceSensitivityError(
                        "selected value is not numeric"
                    ) from error
                if not all(math.isfinite(value) for value in values):
                    raise ReferenceSensitivityError("selected value is not finite")
                vectors[canonical] = values
        if set(vectors) != required:
            raise ReferenceSensitivityError("matrix lacks the complete PAM50 panel")
        return vectors

    def _remaining_eligible_counts(
        self,
        key: str,
        *,
        selected_accessions: set[str],
    ) -> Counter[int]:
        counts: Counter[int] = Counter()
        accession: str | None = None
        er_code: int | None = None

        def finish() -> None:
            if accession is None and er_code is None:
                return
            if accession is None or er_code is None:
                raise ReferenceSensitivityError("metadata record is incomplete")
            if accession not in selected_accessions and er_code in {0, 3}:
                counts[er_code] += 1

        with (
            self._store.open_binary(key) as raw,
            gzip.GzipFile(fileobj=raw, mode="rb") as compressed,
            io.TextIOWrapper(compressed, encoding="utf-8") as text,
        ):
            for raw_line in text:
                line = raw_line.rstrip("\r\n")
                if line.startswith("^SAMPLE = "):
                    finish()
                    accession = None
                    er_code = None
                elif line.startswith("!Sample_geo_accession = "):
                    if accession is not None:
                        raise ReferenceSensitivityError("duplicate metadata accession")
                    accession = line.removeprefix("!Sample_geo_accession = ")
                else:
                    match = ER_PATTERN.fullmatch(line)
                    if match is not None:
                        if er_code is not None:
                            raise ReferenceSensitivityError("duplicate ER consensus")
                        er_code = int(match.group("code"))
        finish()
        return counts

    @staticmethod
    def _validate_provenance(
        plan: GSE81538ReferenceSensitivityPlan,
        matrix_audit: GSE81538MatrixAuditReceipt,
        metadata_receipt: GSE81538ReferenceMetadataReceipt,
        construction_receipt: GSE81538ReferenceConstructionReceipt,
        protocol: ReferenceDevelopmentProtocol,
        candidate: Pam50CentroidCandidateArtifact,
        *,
        matrix_audit_path: Path,
        metadata_receipt_path: Path,
        construction_receipt_path: Path,
        protocol_path: Path,
        candidate_path: Path,
    ) -> None:
        declared = {
            "matrix audit": (plan.matrix_audit_receipt_sha256, matrix_audit_path),
            "metadata receipt": (
                plan.reference_metadata_receipt_sha256,
                metadata_receipt_path,
            ),
            "construction receipt": (
                plan.reference_construction_receipt_sha256,
                construction_receipt_path,
            ),
            "protocol": (plan.reference_protocol_sha256, protocol_path),
            "centroid candidate": (plan.centroid_candidate_sha256, candidate_path),
        }
        changed = [
            label
            for label, (expected, path) in declared.items()
            if expected != sha256(path.read_bytes())
        ]
        if changed:
            raise ReferenceSensitivityError(
                f"reference-sensitivity provenance changed: {', '.join(changed)}"
            )
        if matrix_audit.decision is not MatrixAuditDecision.PASS:
            raise ReferenceSensitivityError("matrix audit did not pass")
        if metadata_receipt.manifest_sha256 != plan.selection_manifest_sha256:
            raise ReferenceSensitivityError("metadata receipt identifies another manifest")
        if construction_receipt.reference_sha256 != plan.primary_reference_sha256:
            raise ReferenceSensitivityError("construction receipt identifies another reference")
        if protocol.protocol_version != "1.1.0":
            raise ReferenceSensitivityError("protocol version changed")
        if len(candidate.gene_order) != plan.expected_gene_count:
            raise ReferenceSensitivityError("PAM50 panel changed")
