"""Outcome-blind construction of the fixed GSE81538 PAM50 reference."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from nas_core.domain.matrix_audit import GSE81538MatrixAuditReceipt, MatrixAuditDecision
from nas_core.domain.method_dependency import Pam50CentroidCandidateArtifact
from nas_core.domain.reference_construction import (
    GSE81538ReferenceConstructionPlan,
    GSE81538ReferenceConstructionReceipt,
    ReferenceConstructionDecision,
)
from nas_core.domain.reference_development import ReferenceDevelopmentProtocol
from nas_core.domain.reference_metadata import GSE81538ReferenceMetadataReceipt
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore


class ReferenceConstructionError(RuntimeError):
    """Raised when reference construction changes provenance or boundaries."""


class GSE81538ReferenceConstructionService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def construct(
        self,
        plan: GSE81538ReferenceConstructionPlan,
        matrix_audit: GSE81538MatrixAuditReceipt,
        metadata_receipt: GSE81538ReferenceMetadataReceipt,
        protocol: ReferenceDevelopmentProtocol,
        candidate: Pam50CentroidCandidateArtifact,
        *,
        plan_path: Path,
        matrix_audit_path: Path,
        metadata_receipt_path: Path,
        protocol_path: Path,
        candidate_path: Path,
        code_revision: str,
        constructed_at: datetime | None = None,
    ) -> GSE81538ReferenceConstructionReceipt:
        self._validate_provenance(
            plan,
            matrix_audit,
            metadata_receipt,
            protocol,
            candidate,
            matrix_audit_path=matrix_audit_path,
            metadata_receipt_path=metadata_receipt_path,
            protocol_path=protocol_path,
            candidate_path=candidate_path,
        )
        matrix_sha, matrix_bytes = self._hash_object(plan.matrix_object_key)
        if matrix_sha != plan.matrix_sha256 or matrix_bytes != plan.matrix_bytes:
            raise ReferenceConstructionError("matrix object changed after audit")
        manifest_bytes = self._store.get_bytes(plan.selection_manifest_object_key)
        if hashlib.sha256(manifest_bytes).hexdigest() != plan.selection_manifest_sha256:
            raise ReferenceConstructionError("selection manifest changed")
        manifest = json.loads(manifest_bytes)
        records = manifest.get("records")
        if not isinstance(records, list) or len(records) != plan.expected_sample_count:
            raise ReferenceConstructionError("selection manifest has changed dimensions")
        titles = [record.get("sample_title") for record in records]
        if len(set(titles)) != len(titles) or not all(isinstance(item, str) for item in titles):
            raise ReferenceConstructionError("selection manifest titles are invalid")
        strata = Counter(record.get("er_stratum") for record in records)
        if strata != {"ER-negative": 50, "ER-positive": 50}:
            raise ReferenceConstructionError("selection manifest strata changed")

        vectors = self._read_selected_panel(
            plan.matrix_object_key,
            selected_titles=titles,
            gene_order=candidate.gene_order,
            aliases=candidate.historical_aliases,
        )
        reference = {
            gene: statistics.median(vectors[gene]) for gene in candidate.gene_order
        }
        values = list(reference.values())
        artifact = {
            "schema_version": "1.0.0",
            "study_id": plan.study_id,
            "source_accession": plan.source_accession,
            "input_scale": plan.input_scale,
            "additional_transform": plan.additional_transform,
            "reference_statistic": plan.reference_statistic,
            "sample_count": len(titles),
            "gene_order": candidate.gene_order,
            "reference": reference,
            "selection_manifest_sha256": plan.selection_manifest_sha256,
        }
        artifact_bytes = (
            json.dumps(artifact, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
            + "\n"
        ).encode("utf-8")
        if self._store.exists(plan.reference_object_key):
            raise ReferenceConstructionError("immutable reference artifact already exists")
        self._store.put_bytes(
            plan.reference_object_key,
            artifact_bytes,
            content_type="application/json",
        )
        stored = self._store.get_bytes(plan.reference_object_key)
        if stored != artifact_bytes:
            raise ReferenceConstructionError("stored reference artifact changed")
        return GSE81538ReferenceConstructionReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            source_accession=plan.source_accession,
            code_revision=code_revision,
            constructed_at=constructed_at or datetime.now(UTC),
            plan_sha256=sha256(plan_path.read_bytes()),
            matrix_audit_receipt_sha256=sha256(matrix_audit_path.read_bytes()),
            reference_metadata_receipt_sha256=sha256(metadata_receipt_path.read_bytes()),
            reference_protocol_sha256=sha256(protocol_path.read_bytes()),
            centroid_candidate_sha256=sha256(candidate_path.read_bytes()),
            matrix_object_sha256_verified=True,
            selection_manifest_sha256_verified=True,
            selected_sample_count=len(titles),
            selected_er_negative_count=strata["ER-negative"],
            selected_er_positive_count=strata["ER-positive"],
            retained_gene_count=len(reference),
            parsed_measurement_count=len(titles) * len(reference),
            finite_measurement_count=len(titles) * len(reference),
            input_scale=plan.input_scale,
            additional_transform_applied=False,
            reference_statistic=plan.reference_statistic,
            reference_minimum=min(values),
            reference_maximum=max(values),
            reference_mean=statistics.fmean(values),
            reference_object_key=plan.reference_object_key,
            reference_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
            reference_bytes=len(artifact_bytes),
            reference_gene_count=len(reference),
            reference_immutable_verified=True,
            decision=ReferenceConstructionDecision.PASS,
            limitations=[
                "The reference inherits the founder-approved ER-code inference.",
                "The deterministic subset may not represent all source variation.",
                "Reference construction does not establish analytical or clinical validity.",
                "Outcome-blind sensitivity diagnostics and technical calibration remain open.",
            ],
            participant_identifiers_retained_in_git=False,
            reference_values_retained_in_git=False,
            molecular_values_parsed=True,
            outcome_values_accessed=False,
            validation_data_accessed=False,
            classifier_executed=False,
            generative_ai_received_participant_data=False,
            reference_locked=False,
        )

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
                raise ReferenceConstructionError("matrix is empty") from error
            header_index = {title: index for index, title in enumerate(header)}
            if any(title not in header_index for title in selected_titles):
                raise ReferenceConstructionError("selected title is absent from matrix")
            indices = [header_index[title] for title in selected_titles]
            for row in reader:
                if len(row) != len(header):
                    raise ReferenceConstructionError("matrix row width changed")
                canonical = aliases.get(row[0].strip(), row[0].strip())
                if canonical not in required:
                    continue
                if canonical in vectors:
                    raise ReferenceConstructionError("duplicate retained PAM50 row")
                try:
                    values = [float(row[index]) for index in indices]
                except ValueError as error:
                    raise ReferenceConstructionError("selected value is not numeric") from error
                if not all(math.isfinite(value) for value in values):
                    raise ReferenceConstructionError("selected value is not finite")
                vectors[canonical] = values
        if set(vectors) != required:
            raise ReferenceConstructionError("matrix lacks the complete PAM50 panel")
        return vectors

    def _hash_object(self, key: str) -> tuple[str, int]:
        digest = hashlib.sha256()
        size = 0
        with self._store.open_binary(key) as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
        return digest.hexdigest(), size

    @staticmethod
    def _validate_provenance(
        plan: GSE81538ReferenceConstructionPlan,
        matrix_audit: GSE81538MatrixAuditReceipt,
        metadata_receipt: GSE81538ReferenceMetadataReceipt,
        protocol: ReferenceDevelopmentProtocol,
        candidate: Pam50CentroidCandidateArtifact,
        *,
        matrix_audit_path: Path,
        metadata_receipt_path: Path,
        protocol_path: Path,
        candidate_path: Path,
    ) -> None:
        declared = {
            "matrix audit": (plan.matrix_audit_receipt_sha256, matrix_audit_path),
            "metadata receipt": (
                plan.reference_metadata_receipt_sha256,
                metadata_receipt_path,
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
            raise ReferenceConstructionError(
                f"reference-construction provenance changed: {', '.join(changed)}"
            )
        if matrix_audit.decision is not MatrixAuditDecision.PASS:
            raise ReferenceConstructionError("matrix audit did not pass")
        if metadata_receipt.manifest_sha256 != plan.selection_manifest_sha256:
            raise ReferenceConstructionError("metadata receipt identifies another manifest")
        if (
            protocol.protocol_version != "1.1.0"
            or not protocol.preprocessing_bridge.transformation_locked
        ):
            raise ReferenceConstructionError("reference protocol does not authorize construction")
        if len(candidate.gene_order) != plan.expected_gene_count:
            raise ReferenceConstructionError("centroid candidate gene count changed")
