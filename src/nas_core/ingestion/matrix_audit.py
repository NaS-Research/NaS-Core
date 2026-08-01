"""Streaming, outcome-blind audit of the governed GSE81538 matrix."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import math
from datetime import UTC, datetime
from pathlib import Path

from nas_core.domain.matrix_audit import (
    GSE81538MatrixAuditPlan,
    GSE81538MatrixAuditReceipt,
    MatrixAuditDecision,
)
from nas_core.domain.method_dependency import Pam50CentroidCandidateArtifact
from nas_core.domain.public_artifact import PublicArtifactAcquisitionReceipt
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore


class MatrixAuditError(RuntimeError):
    """Raised when matrix audit inputs or structure fail closed."""


class GSE81538MatrixAuditService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def audit(
        self,
        plan: GSE81538MatrixAuditPlan,
        acquisition: PublicArtifactAcquisitionReceipt,
        candidate: Pam50CentroidCandidateArtifact,
        *,
        plan_path: Path,
        acquisition_path: Path,
        candidate_path: Path,
        reference_protocol_path: Path,
        code_revision: str,
        audited_at: datetime | None = None,
    ) -> GSE81538MatrixAuditReceipt:
        self._validate_provenance(
            plan,
            acquisition,
            candidate,
            acquisition_path=acquisition_path,
            candidate_path=candidate_path,
            reference_protocol_path=reference_protocol_path,
        )
        observed_sha, observed_bytes = self._hash_object(plan.object_key)
        if (
            observed_sha != plan.expected_compressed_sha256
            or observed_sha != acquisition.sha256
            or observed_bytes != plan.expected_compressed_bytes
            or observed_bytes != acquisition.content_length_bytes
        ):
            raise MatrixAuditError("stored object does not match acquisition provenance")

        required = set(candidate.gene_order)
        aliases = candidate.historical_aliases
        seen_genes: set[str] = set()
        resolved: dict[str, str] = {}
        duplicate_gene_count = 0
        duplicate_pam50: set[str] = set()
        aliases_applied: dict[str, str] = {}
        row_count = 0
        total_count = 0
        finite_count = 0
        missing_count = 0
        nonfinite_count = 0
        minimum = math.inf
        maximum = -math.inf
        floor_count = 0
        below_floor = 0

        with (
            self._store.open_binary(plan.object_key) as raw,
            gzip.GzipFile(fileobj=raw, mode="rb") as compressed,
            io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text,
        ):
            reader = csv.reader(text)
            try:
                header = next(reader)
            except StopIteration as error:
                raise MatrixAuditError("matrix is empty") from error
            expected_header = [
                "",
                *[
                    f"{plan.sample_column_prefix}{index}"
                    for index in range(1, plan.expected_sample_columns + 1)
                ],
            ]
            header_verified = header == expected_header
            if len(header) != plan.expected_sample_columns + 1:
                raise MatrixAuditError("matrix sample-column count changed")

            for row in reader:
                if len(row) != len(header):
                    raise MatrixAuditError("matrix row width changed")
                gene = row[0].strip()
                if not gene:
                    raise MatrixAuditError("matrix contains an empty gene identifier")
                if gene in seen_genes:
                    duplicate_gene_count += 1
                seen_genes.add(gene)
                canonical = aliases.get(gene, gene)
                if canonical in required:
                    if canonical in resolved:
                        duplicate_pam50.add(canonical)
                    else:
                        resolved[canonical] = gene
                        if canonical != gene:
                            aliases_applied[gene] = canonical
                row_count += 1
                for raw_value in row[1:]:
                    total_count += 1
                    if raw_value.strip() == "":
                        missing_count += 1
                        continue
                    try:
                        value = float(raw_value)
                    except ValueError:
                        nonfinite_count += 1
                        continue
                    if not math.isfinite(value):
                        nonfinite_count += 1
                        continue
                    finite_count += 1
                    minimum = min(minimum, value)
                    maximum = max(maximum, value)
                    if abs(value - plan.expected_zero_floor) <= plan.floor_absolute_tolerance:
                        floor_count += 1
                    elif value < plan.expected_zero_floor - plan.floor_absolute_tolerance:
                        below_floor += 1

        if row_count != plan.expected_gene_rows:
            raise MatrixAuditError("matrix gene-row count changed")
        if not math.isfinite(minimum) or not math.isfinite(maximum):
            raise MatrixAuditError("matrix contains no finite measurements")
        floor_matches = (
            abs(minimum - plan.expected_zero_floor) <= plan.floor_absolute_tolerance
            and floor_count > 0
            and below_floor == 0
        )
        missing_genes = sorted(required - set(resolved))
        pass_state = all(
            (
                header_verified,
                duplicate_gene_count == 0,
                finite_count == total_count,
                missing_count == 0,
                nonfinite_count == 0,
                floor_matches,
                len(resolved) == len(required),
                not duplicate_pam50,
            )
        )
        return GSE81538MatrixAuditReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            source_id=plan.source_id,
            source_accession=plan.source_accession,
            code_revision=code_revision,
            audited_at=audited_at or datetime.now(UTC),
            plan_sha256=sha256(plan_path.read_bytes()),
            acquisition_receipt_sha256=sha256(acquisition_path.read_bytes()),
            object_sha256_verified=True,
            compressed_bytes=observed_bytes,
            expected_gene_row_count=plan.expected_gene_rows,
            gene_row_count=row_count,
            unique_gene_identifier_count=len(seen_genes),
            duplicate_gene_identifier_count=duplicate_gene_count,
            expected_sample_column_count=plan.expected_sample_columns,
            sample_column_count=plan.expected_sample_columns,
            sample_header_sequence_verified=header_verified,
            total_measurement_count=total_count,
            finite_measurement_count=finite_count,
            missing_measurement_count=missing_count,
            nonfinite_measurement_count=nonfinite_count,
            minimum_value=minimum,
            maximum_value=maximum,
            expected_zero_floor=plan.expected_zero_floor,
            zero_floor_count=floor_count,
            values_below_expected_floor=below_floor,
            official_transform_declared=plan.declared_transform,
            observed_floor_matches_declared_transform=floor_matches,
            input_scale_verified=floor_matches,
            required_pam50_gene_count=len(required),
            resolved_pam50_gene_count=len(resolved),
            missing_pam50_genes=missing_genes,
            duplicate_pam50_mappings=sorted(duplicate_pam50),
            historical_aliases_applied=aliases_applied,
            decision=(
                MatrixAuditDecision.PASS if pass_state else MatrixAuditDecision.CHANGES_REQUIRED
            ),
            limitations=[
                "The audit verifies structure, finite values, scale, and panel coverage only.",
                "The transform statement is source metadata, not an independent assay validation.",
                "No sample row, classifier score, subtype, reference vector, "
                "or outcome is retained.",
            ],
            molecular_values_parsed=True,
            sample_rows_retained=False,
            outcome_values_accessed=False,
            classifier_executed=False,
            reference_vector_materialized=False,
            reference_locked=False,
        )

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
        plan: GSE81538MatrixAuditPlan,
        acquisition: PublicArtifactAcquisitionReceipt,
        candidate: Pam50CentroidCandidateArtifact,
        *,
        acquisition_path: Path,
        candidate_path: Path,
        reference_protocol_path: Path,
    ) -> None:
        if acquisition.object_key != plan.object_key:
            raise MatrixAuditError("acquisition receipt identifies another object")
        if len(candidate.gene_order) != 50:
            raise MatrixAuditError("centroid candidate is not the governed 50-gene panel")
        declared = {
            "acquisition receipt": (plan.acquisition_receipt_sha256, acquisition_path),
            "centroid candidate": (plan.centroid_candidate_sha256, candidate_path),
            "reference protocol": (
                plan.reference_protocol_sha256,
                reference_protocol_path,
            ),
        }
        changed = [
            label
            for label, (expected, path) in declared.items()
            if expected != sha256(path.read_bytes())
        ]
        if changed:
            raise MatrixAuditError(f"matrix-audit provenance changed: {', '.join(changed)}")
