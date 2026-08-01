"""Contracts for authoritative GSE130397 annotation and strandedness resolution."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationAnnotationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalibrationAnnotationResolutionPlan(CalibrationAnnotationModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    feasibility_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    lineage_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_family_soft_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    family_soft_url: str = Field(pattern=r"^https://ftp\.ncbi\.nlm\.nih\.gov/")
    candidate_annotation_url: str = Field(pattern=r"^https://ftp\.ensembl\.org/")
    candidate_annotation_length_bytes: int = Field(gt=0)
    retain_sample_identifiers: bool
    retain_processing_rows: bool
    molecular_values_requested: bool
    outcomes_requested: bool

    @model_validator(mode="after")
    def enforce_metadata_only(self) -> CalibrationAnnotationResolutionPlan:
        if any(
            (
                self.retain_sample_identifiers,
                self.retain_processing_rows,
                self.molecular_values_requested,
                self.outcomes_requested,
            )
        ):
            raise ValueError("annotation resolution is aggregate metadata only")
        return self


class CalibrationAnnotationResolutionReceipt(CalibrationAnnotationModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    family_soft_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    family_soft_size_bytes: int = Field(gt=0)
    sample_count: int = Field(gt=0)
    grch38_release_84_count: int = Field(ge=0)
    star_gene_counts_count: int = Field(ge=0)
    access_library_count: int = Field(ge=0)
    access_reverse_directive_count: int = Field(ge=0)
    ovation_library_count: int = Field(ge=0)
    ovation_forward_directive_count: int = Field(ge=0)
    genome_build: str = Field(pattern=r"^GRCh38$")
    ensembl_release: int = Field(ge=84, le=84)
    access_count_column: str = Field(pattern=r"^rev$")
    ovation_count_column: str = Field(pattern=r"^fwd$")
    annotation_url: str = Field(pattern=r"^https://ftp\.ensembl\.org/")
    annotation_expected_length_bytes: int = Field(gt=0)
    resolution_complete: bool
    sample_identifiers_retained: bool
    processing_rows_retained: bool
    molecular_values_parsed: bool
    outcomes_accessed: bool
    raw_metadata_stored: bool

    @model_validator(mode="after")
    def validate_resolution(self) -> CalibrationAnnotationResolutionReceipt:
        if not self.resolution_complete:
            raise ValueError("annotation resolution receipt must be complete")
        if self.sample_count != 21 or self.access_library_count + self.ovation_library_count != 21:
            raise ValueError("GSE130397 library counts must reconcile to 21")
        if (
            self.grch38_release_84_count != self.sample_count
            or self.star_gene_counts_count != self.sample_count
            or self.access_reverse_directive_count != self.access_library_count
            or self.ovation_forward_directive_count != self.ovation_library_count
        ):
            raise ValueError("processing directives must reconcile for every sample")
        if any(
            (
                self.sample_identifiers_retained,
                self.processing_rows_retained,
                self.molecular_values_parsed,
                self.outcomes_accessed,
                self.raw_metadata_stored,
            )
        ):
            raise ValueError("resolution receipt cannot retain source rows or values")
        return self


class CalibrationAnnotationAcquisitionPlan(CalibrationAnnotationModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    source_id: str = Field(pattern=r"^ensembl-grch38-release-84$")
    official_url: str = Field(
        pattern=r"^https://ftp\.ensembl\.org/pub/release-84/gtf/homo_sapiens/"
    )
    filename: str = Field(pattern=r"^Homo_sapiens\.GRCh38\.84\.gtf\.gz$")
    expected_content_length_bytes: int = Field(gt=0)
    expected_content_type: str
    object_key: str = Field(pattern=r"^raw/nas-brca-002/annotation/")
    source_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    annotation_resolution_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    storage_readiness_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parse_during_acquisition: bool
    molecular_values_requested: bool
    outcomes_requested: bool
    export_authorized: bool
    publication_authorized: bool
    immutable_write_required: bool

    @model_validator(mode="after")
    def enforce_internal_acquisition(self) -> CalibrationAnnotationAcquisitionPlan:
        if not self.official_url.endswith(self.filename):
            raise ValueError("annotation URL and filename do not reconcile")
        if any(
            (
                self.parse_during_acquisition,
                self.molecular_values_requested,
                self.outcomes_requested,
                self.export_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError("annotation acquisition is internal and nonanalytical")
        if not self.immutable_write_required:
            raise ValueError("annotation acquisition must be immutable")
        return self


class CalibrationAnnotationAcquisitionReceipt(CalibrationAnnotationModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    source_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    acquired_at: datetime
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    official_url: str
    response_content_type: str
    response_last_modified: str | None
    content_length_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    object_key: str
    immutable_object_verified: bool
    source_bytes_stored: bool
    annotation_rows_parsed: bool
    molecular_values_parsed: bool
    outcomes_accessed: bool
    export_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def enforce_acquisition_receipt(self) -> CalibrationAnnotationAcquisitionReceipt:
        if not self.immutable_object_verified or not self.source_bytes_stored:
            raise ValueError("annotation object must be immutably stored")
        if any(
            (
                self.annotation_rows_parsed,
                self.molecular_values_parsed,
                self.outcomes_accessed,
                self.export_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError("annotation acquisition cannot claim analysis or release")
        return self


class CalibrationAnnotationMappingPlan(CalibrationAnnotationModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    annotation_acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    feasibility_acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    feasibility_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mapping_object_key: str = Field(pattern=r"^derived/nas-brca-002/")
    retain_participant_identifiers: bool
    retain_molecular_values: bool
    outcomes_requested: bool
    classifier_execution_authorized: bool
    threshold_estimation_authorized: bool

    @model_validator(mode="after")
    def enforce_mapping_boundary(self) -> CalibrationAnnotationMappingPlan:
        if any(
            (
                self.retain_participant_identifiers,
                self.retain_molecular_values,
                self.outcomes_requested,
                self.classifier_execution_authorized,
                self.threshold_estimation_authorized,
            )
        ):
            raise ValueError("annotation mapping cannot access downstream analysis")
        return self


class CalibrationAnnotationMappingReceipt(CalibrationAnnotationModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    annotation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    annotation_gene_row_count: int = Field(gt=0)
    unique_annotation_gene_id_count: int = Field(gt=0)
    conflicting_annotation_gene_id_count: int = Field(ge=0)
    source_feature_count: int = Field(gt=0)
    mapped_source_feature_count: int = Field(ge=0)
    unmapped_source_feature_count: int = Field(ge=0)
    pam50_required_gene_count: int = Field(ge=50, le=50)
    pam50_uniquely_mapped_gene_count: int = Field(ge=0, le=50)
    pam50_present_in_source_count: int = Field(ge=0, le=50)
    pam50_missing_from_source_count: int = Field(ge=0, le=50)
    mapping_object_key: str
    mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mapping_object_verified: bool
    mapping_complete: bool
    participant_identifiers_retained: bool
    molecular_values_parsed: bool
    outcomes_accessed: bool
    classifier_executed: bool
    thresholds_estimated: bool
    export_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def validate_mapping_receipt(self) -> CalibrationAnnotationMappingReceipt:
        if (
            self.mapped_source_feature_count + self.unmapped_source_feature_count
            != self.source_feature_count
        ):
            raise ValueError("source feature mapping counts must reconcile")
        if (
            self.pam50_present_in_source_count
            + self.pam50_missing_from_source_count
            != 50
        ):
            raise ValueError("PAM50 source coverage must reconcile")
        if self.mapping_complete != (
            self.pam50_uniquely_mapped_gene_count == 50
            and self.pam50_present_in_source_count == 50
            and self.conflicting_annotation_gene_id_count == 0
            and self.mapping_object_verified
        ):
            raise ValueError("mapping completion flag does not reconcile")
        if any(
            (
                self.participant_identifiers_retained,
                self.molecular_values_parsed,
                self.outcomes_accessed,
                self.classifier_executed,
                self.thresholds_estimated,
                self.export_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError("mapping receipt cannot claim downstream use or release")
        return self


def load_calibration_annotation_resolution_plan(
    path: Path,
) -> CalibrationAnnotationResolutionPlan:
    return CalibrationAnnotationResolutionPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_calibration_annotation_acquisition_plan(
    path: Path,
) -> CalibrationAnnotationAcquisitionPlan:
    return CalibrationAnnotationAcquisitionPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_calibration_annotation_acquisition_receipt(
    path: Path,
) -> CalibrationAnnotationAcquisitionReceipt:
    return CalibrationAnnotationAcquisitionReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_calibration_annotation_mapping_plan(
    path: Path,
) -> CalibrationAnnotationMappingPlan:
    return CalibrationAnnotationMappingPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_annotation_resolution_receipt(
    path: Path,
    receipt: CalibrationAnnotationResolutionReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("annotation-resolution receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_calibration_annotation_acquisition_receipt(
    path: Path,
    receipt: CalibrationAnnotationAcquisitionReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("annotation-acquisition receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_calibration_annotation_mapping_receipt(
    path: Path,
    receipt: CalibrationAnnotationMappingReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("annotation-mapping receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_calibration_annotation_resolution_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, CalibrationAnnotationResolutionPlan),
        (receipt_path, CalibrationAnnotationResolutionReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def write_calibration_annotation_acquisition_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, CalibrationAnnotationAcquisitionPlan),
        (receipt_path, CalibrationAnnotationAcquisitionReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def write_calibration_annotation_mapping_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, CalibrationAnnotationMappingPlan),
        (receipt_path, CalibrationAnnotationMappingReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
