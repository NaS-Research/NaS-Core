"""Deterministic Ensembl-84 mapping for the GSE130397 PAM50 panel."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
from pathlib import Path

from nas_core.domain.calibration_annotation import (
    CalibrationAnnotationAcquisitionReceipt,
    CalibrationAnnotationMappingPlan,
    CalibrationAnnotationMappingReceipt,
)
from nas_core.domain.calibration_feasibility_artifact import (
    CalibrationFeasibilityAcquisitionReceipt,
    CalibrationFeasibilityArtifactKind,
)
from nas_core.domain.reliability import SingleSampleReliabilitySpecification
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore

_GENE_ID = re.compile(r'(?:^|;\s*)gene_id "([^"]+)";')
_GENE_NAME = re.compile(r'(?:^|;\s*)gene_name "([^"]+)";')


class CalibrationAnnotationMappingError(RuntimeError):
    """Raised when Ensembl annotation cannot produce a unique bounded mapping."""


class CalibrationAnnotationMappingService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def execute(
        self,
        plan: CalibrationAnnotationMappingPlan,
        annotation: CalibrationAnnotationAcquisitionReceipt,
        feasibility: CalibrationFeasibilityAcquisitionReceipt,
        specification: SingleSampleReliabilitySpecification,
        *,
        plan_path: Path,
        annotation_receipt_path: Path,
        feasibility_receipt_path: Path,
        feasibility_audit_receipt_path: Path,
        reliability_specification_path: Path,
        code_revision: str,
    ) -> CalibrationAnnotationMappingReceipt:
        self._validate_provenance(
            plan,
            annotation_receipt_path=annotation_receipt_path,
            feasibility_receipt_path=feasibility_receipt_path,
            feasibility_audit_receipt_path=feasibility_audit_receipt_path,
            reliability_specification_path=reliability_specification_path,
        )
        annotation_bytes = self._store.get_bytes(annotation.object_key)
        if (
            len(annotation_bytes) != annotation.content_length_bytes
            or hashlib.sha256(annotation_bytes).hexdigest() != annotation.sha256
        ):
            raise CalibrationAnnotationMappingError("stored annotation changed")
        gene_rows, gene_to_name, conflicts = self._parse_gtf(annotation_bytes)
        source_features = self._source_features(feasibility)
        canonical = set(specification.input_contract.canonical_gene_symbols)
        aliases = specification.input_contract.historical_aliases

        name_to_ids: dict[str, set[str]] = {}
        for gene_id, name in gene_to_name.items():
            resolved = aliases.get(name, name)
            if resolved in canonical:
                name_to_ids.setdefault(resolved, set()).add(gene_id)
        unique_map = {
            name: next(iter(ids))
            for name, ids in name_to_ids.items()
            if len(ids) == 1
        }
        present = {
            name: gene_id
            for name, gene_id in unique_map.items()
            if gene_id in source_features
        }
        mapping_payload = json.dumps(
            {
                "schema_version": "1.0.0",
                "source": "Ensembl release 84 GRCh38",
                "panel": "PAM50_historical_50",
                "gene_to_ensembl_id": dict(sorted(present.items())),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if self._store.exists(plan.mapping_object_key):
            raise CalibrationAnnotationMappingError("immutable mapping already exists")
        self._store.put_bytes(
            plan.mapping_object_key,
            mapping_payload,
            content_type="application/json",
        )
        mapping_sha = hashlib.sha256(mapping_payload).hexdigest()
        mapped_features = source_features & set(gene_to_name)
        return CalibrationAnnotationMappingReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            annotation_sha256=annotation.sha256,
            annotation_gene_row_count=gene_rows,
            unique_annotation_gene_id_count=len(gene_to_name),
            conflicting_annotation_gene_id_count=conflicts,
            source_feature_count=len(source_features),
            mapped_source_feature_count=len(mapped_features),
            unmapped_source_feature_count=len(source_features - mapped_features),
            pam50_required_gene_count=50,
            pam50_uniquely_mapped_gene_count=len(unique_map),
            pam50_present_in_source_count=len(present),
            pam50_missing_from_source_count=50 - len(present),
            mapping_object_key=plan.mapping_object_key,
            mapping_sha256=mapping_sha,
            mapping_object_verified=(
                self._store.exists(plan.mapping_object_key)
                and hashlib.sha256(
                    self._store.get_bytes(plan.mapping_object_key)
                ).hexdigest()
                == mapping_sha
            ),
            mapping_complete=(
                len(unique_map) == 50
                and len(present) == 50
                and conflicts == 0
            ),
            participant_identifiers_retained=False,
            molecular_values_parsed=False,
            outcomes_accessed=False,
            classifier_executed=False,
            thresholds_estimated=False,
            export_authorized=False,
            publication_authorized=False,
        )

    @staticmethod
    def _parse_gtf(payload: bytes) -> tuple[int, dict[str, str], int]:
        gene_to_name: dict[str, str] = {}
        conflicts: set[str] = set()
        rows = 0
        with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as decoded:
            for raw_line in decoded:
                if raw_line.startswith(b"#"):
                    continue
                fields = raw_line.decode("utf-8").rstrip("\n").split("\t")
                if len(fields) != 9 or fields[2] != "gene":
                    continue
                rows += 1
                gene_id_match = _GENE_ID.search(fields[8])
                gene_name_match = _GENE_NAME.search(fields[8])
                if gene_id_match is None or gene_name_match is None:
                    raise CalibrationAnnotationMappingError("GTF gene row lacks identifiers")
                gene_id = gene_id_match.group(1).split(".", 1)[0]
                gene_name = gene_name_match.group(1)
                previous = gene_to_name.setdefault(gene_id, gene_name)
                if previous != gene_name:
                    conflicts.add(gene_id)
        return rows, gene_to_name, len(conflicts)

    def _source_features(
        self,
        feasibility: CalibrationFeasibilityAcquisitionReceipt,
    ) -> set[str]:
        artifact = next(
            (
                item
                for item in feasibility.artifacts
                if item.source_id == "ncbi-geo-gse130397"
                and item.artifact_kind
                is CalibrationFeasibilityArtifactKind.PROCESSED_EXPRESSION
            ),
            None,
        )
        if artifact is None:
            raise CalibrationAnnotationMappingError("GSE130397 count artifact is missing")
        payload = self._store.get_bytes(artifact.object_key)
        if hashlib.sha256(payload).hexdigest() != artifact.sha256:
            raise CalibrationAnnotationMappingError("GSE130397 count artifact changed")
        reader = csv.reader(
            io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(payload))),
            delimiter="\t",
        )
        if next(reader, None) != ["Gene", "Unstranded", "fwd", "rev"]:
            raise CalibrationAnnotationMappingError("unexpected GSE130397 header")
        return {row[0].split(".", 1)[0] for row in reader}

    @staticmethod
    def _validate_provenance(
        plan: CalibrationAnnotationMappingPlan,
        *,
        annotation_receipt_path: Path,
        feasibility_receipt_path: Path,
        feasibility_audit_receipt_path: Path,
        reliability_specification_path: Path,
    ) -> None:
        declared = (
            (plan.annotation_acquisition_receipt_sha256, annotation_receipt_path),
            (plan.feasibility_acquisition_receipt_sha256, feasibility_receipt_path),
            (plan.feasibility_audit_receipt_sha256, feasibility_audit_receipt_path),
            (plan.reliability_specification_sha256, reliability_specification_path),
        )
        if any(expected != sha256(path.read_bytes()) for expected, path in declared):
            raise CalibrationAnnotationMappingError("annotation-mapping provenance changed")
