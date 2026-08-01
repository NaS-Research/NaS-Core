"""Contracts for authoritative GSE130397 annotation and strandedness resolution."""

from __future__ import annotations

import json
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


def load_calibration_annotation_resolution_plan(
    path: Path,
) -> CalibrationAnnotationResolutionPlan:
    return CalibrationAnnotationResolutionPlan.model_validate(
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
