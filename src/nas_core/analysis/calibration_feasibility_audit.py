"""Deterministic source-isolated audit of public calibration-feasibility files."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import math
import re
from pathlib import Path

from nas_core.domain.calibration_feasibility_artifact import (
    CalibrationFeasibilityAcquisitionReceipt,
    CalibrationFeasibilityArtifactKind,
)
from nas_core.domain.calibration_feasibility_audit import (
    CalibrationFeasibilityAuditPlan,
    CalibrationFeasibilityAuditReceipt,
    PanelMappingStatus,
    SourceFeasibilityProjection,
)
from nas_core.domain.reliability import SingleSampleReliabilitySpecification
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore


class CalibrationFeasibilityAuditError(RuntimeError):
    """Raised when the bounded feasibility audit cannot be reproduced."""


class CalibrationFeasibilityAuditService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def execute(
        self,
        plan: CalibrationFeasibilityAuditPlan,
        acquisition: CalibrationFeasibilityAcquisitionReceipt,
        specification: SingleSampleReliabilitySpecification,
        *,
        plan_path: Path,
        acquisition_receipt_path: Path,
        reliability_specification_path: Path,
        code_revision: str,
    ) -> CalibrationFeasibilityAuditReceipt:
        self._validate_provenance(
            plan,
            acquisition_receipt_path=acquisition_receipt_path,
            reliability_specification_path=reliability_specification_path,
        )
        payloads: dict[str, bytes] = {}
        for artifact in acquisition.artifacts:
            payload = self._store.get_bytes(artifact.object_key)
            if (
                len(payload) != artifact.content_length_bytes
                or hashlib.sha256(payload).hexdigest() != artifact.sha256
            ):
                raise CalibrationFeasibilityAuditError(
                    f"stored artifact changed: {artifact.filename}"
                )
            payloads[artifact.filename] = payload

        pam50 = set(specification.input_contract.canonical_gene_symbols)
        aliases = specification.input_contract.historical_aliases
        gse60788 = self._audit_gse60788(acquisition, payloads, pam50, aliases)
        gse130397 = self._audit_gse130397(acquisition, payloads, pam50)
        return CalibrationFeasibilityAuditReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            acquisition_receipt_sha256=sha256(acquisition_receipt_path.read_bytes()),
            reliability_specification_sha256=sha256(
                reliability_specification_path.read_bytes()
            ),
            sources=[gse60788, gse130397],
            decision="feasibility_audit_complete_primary_calibration_not_ready",
            source_identifiers_retained=False,
            molecular_values_retained=False,
            outcomes_accessed=False,
            sources_pooled=False,
            thresholds_estimated=False,
            classifier_executed=False,
            external_publication_authorized=False,
            next_actions=[
                "Freeze source-specific technical-replicate estimands for GSE60788.",
                "Resolve GSE130397 Ensembl-to-symbol mapping under a versioned annotation source.",
                "Do not pool sources or estimate reliability thresholds.",
            ],
        )

    @staticmethod
    def _validate_provenance(
        plan: CalibrationFeasibilityAuditPlan,
        *,
        acquisition_receipt_path: Path,
        reliability_specification_path: Path,
    ) -> None:
        observed = {
            "acquisition receipt": (
                plan.acquisition_receipt_sha256,
                sha256(acquisition_receipt_path.read_bytes()),
            ),
            "reliability specification": (
                plan.reliability_specification_sha256,
                sha256(reliability_specification_path.read_bytes()),
            ),
        }
        changed = [
            label for label, (expected, actual) in observed.items() if expected != actual
        ]
        if changed:
            raise CalibrationFeasibilityAuditError(
                f"feasibility-audit provenance changed: {', '.join(changed)}"
            )

    @staticmethod
    def _audit_gse60788(
        acquisition: CalibrationFeasibilityAcquisitionReceipt,
        payloads: dict[str, bytes],
        pam50: set[str],
        aliases: dict[str, str],
    ) -> SourceFeasibilityProjection:
        filename = "GSE60788_rnaseq_gex_normalized.txt.gz"
        try:
            stream = io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(payloads[filename])))
            reader = csv.reader(stream, delimiter="\t")
            header = next(reader)
        except (KeyError, OSError, StopIteration) as error:
            raise CalibrationFeasibilityAuditError("invalid GSE60788 matrix") from error
        if not header or header[0] != "Gene Symbol":
            raise CalibrationFeasibilityAuditError("unexpected GSE60788 matrix header")
        sample_labels = header[1:]
        primary = sum(bool(re.fullmatch(r"P[0-9]+", label)) for label in sample_labels)
        replicates = sum(
            bool(re.fullmatch(r"P[0-9]+-replicate", label))
            for label in sample_labels
        )
        if primary + replicates != len(sample_labels):
            raise CalibrationFeasibilityAuditError("unrecognized GSE60788 sample label")

        genes: set[str] = set()
        rows = total = nonfinite = negative = integer_like = 0
        minimum = math.inf
        maximum = -math.inf
        for row in reader:
            if len(row) != len(header):
                raise CalibrationFeasibilityAuditError("ragged GSE60788 matrix")
            rows += 1
            genes.add(aliases.get(row[0], row[0]))
            for token in row[1:]:
                value = float(token)
                total += 1
                if not math.isfinite(value):
                    nonfinite += 1
                    continue
                negative += int(value < 0)
                integer_like += int(value.is_integer())
                minimum = min(minimum, value)
                maximum = max(maximum, value)
        covered = pam50 & genes
        return SourceFeasibilityProjection(
            source_id="ncbi-geo-gse60788",
            artifact_count=sum(
                item.source_id == "ncbi-geo-gse60788" for item in acquisition.artifacts
            ),
            sample_count=len(sample_labels),
            primary_or_unlabeled_count=primary,
            replicate_record_count=replicates,
            replicate_group_count=primary,
            feature_row_count=rows,
            identifier_namespace="gene_symbol_with_declared_historical_alias_resolution",
            panel_mapping_status=PanelMappingStatus.VERIFIED_DIRECT_SYMBOLS,
            direct_pam50_gene_count=len(covered),
            missing_direct_pam50_gene_count=len(pam50 - covered),
            total_numeric_value_count=total,
            nonfinite_value_count=nonfinite,
            negative_value_count=negative,
            integer_like_value_count=integer_like,
            observed_minimum=minimum,
            observed_maximum=maximum,
            scale_interpretation=(
                "source-normalized continuous expression; exact transform not inferred"
            ),
            usable_for_source_specific_feasibility=(
                len(covered) == 50 and nonfinite == 0 and replicates == 6
            ),
            usable_for_primary_calibration=False,
        )

    @staticmethod
    def _audit_gse130397(
        acquisition: CalibrationFeasibilityAcquisitionReceipt,
        payloads: dict[str, bytes],
        pam50: set[str],
    ) -> SourceFeasibilityProjection:
        artifacts = [
            item
            for item in acquisition.artifacts
            if item.source_id == "ncbi-geo-gse130397"
            and item.artifact_kind is CalibrationFeasibilityArtifactKind.PROCESSED_EXPRESSION
        ]
        total = nonfinite = negative = integer_like = 0
        minimum = math.inf
        maximum = -math.inf
        feature_rows: int | None = None
        feature_digest: str | None = None
        direct_symbols: set[str] = set()
        primary = replicates = 0
        groups: set[str] = set()
        for artifact in artifacts:
            filename = artifact.filename
            base = re.sub(r"^GSM[0-9]+_", "", filename)
            base = re.sub(r"_readsPerGene\.txt\.gz$", "", base)
            is_reseq = base.endswith("_Reseq")
            triplicate = re.fullmatch(r"(.+_S[12])_(0[123])", base)
            if triplicate:
                group, replicate_number = triplicate.groups()
                groups.add(group)
                primary += int(replicate_number == "01")
                replicates += int(replicate_number != "01")
            else:
                group = base.removesuffix("_Reseq")
                groups.add(group)
                primary += int(not is_reseq)
                replicates += int(is_reseq)

            reader = csv.reader(
                io.TextIOWrapper(
                    gzip.GzipFile(fileobj=io.BytesIO(payloads[filename]))
                ),
                delimiter="\t",
            )
            digest = hashlib.sha256()
            rows = 0
            for row in reader:
                if len(row) != 4:
                    raise CalibrationFeasibilityAuditError("ragged GSE130397 count file")
                rows += 1
                digest.update(row[0].encode("utf-8"))
                digest.update(b"\0")
                if row[0] in pam50:
                    direct_symbols.add(row[0])
                for token in row[1:]:
                    value = float(token)
                    total += 1
                    if not math.isfinite(value):
                        nonfinite += 1
                        continue
                    negative += int(value < 0)
                    integer_like += int(value.is_integer())
                    minimum = min(minimum, value)
                    maximum = max(maximum, value)
            if feature_rows is None:
                feature_rows = rows
                feature_digest = digest.hexdigest()
            elif rows != feature_rows or digest.hexdigest() != feature_digest:
                raise CalibrationFeasibilityAuditError(
                    "GSE130397 feature order differs across files"
                )
        if feature_rows is None:
            raise CalibrationFeasibilityAuditError("GSE130397 has no count files")
        return SourceFeasibilityProjection(
            source_id="ncbi-geo-gse130397",
            artifact_count=sum(
                item.source_id == "ncbi-geo-gse130397" for item in acquisition.artifacts
            ),
            sample_count=len(artifacts),
            primary_or_unlabeled_count=primary,
            replicate_record_count=replicates,
            replicate_group_count=len(groups),
            feature_row_count=feature_rows,
            identifier_namespace="ensembl_gene_identifier_unmapped",
            panel_mapping_status=PanelMappingStatus.UNRESOLVED_IDENTIFIER_MAPPING,
            direct_pam50_gene_count=len(direct_symbols),
            missing_direct_pam50_gene_count=len(pam50 - direct_symbols),
            total_numeric_value_count=total,
            nonfinite_value_count=nonfinite,
            negative_value_count=negative,
            integer_like_value_count=integer_like,
            observed_minimum=minimum,
            observed_maximum=maximum,
            scale_interpretation=(
                "three integer count columns per Ensembl feature; "
                "strandedness choice unresolved"
            ),
            usable_for_source_specific_feasibility=(
                nonfinite == 0 and negative == 0 and integer_like == total
            ),
            usable_for_primary_calibration=False,
        )
