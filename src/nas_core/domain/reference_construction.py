"""Contracts for outcome-blind construction of the GSE81538 fixed reference."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReferenceConstructionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReferenceConstructionDecision(StrEnum):
    PASS = "pass"


class GSE81538ReferenceConstructionPlan(ReferenceConstructionModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_accession: str = Field(pattern=r"^GSE81538$")
    matrix_object_key: str = Field(pattern=r"^raw/[a-z0-9._/-]+$")
    matrix_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_bytes: int = Field(gt=0)
    matrix_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_metadata_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_protocol_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selection_manifest_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    selection_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    expected_sample_count: int = Field(gt=0)
    expected_gene_count: int = Field(gt=0)
    input_scale: str = Field(pattern=r"^log2\(FPKM \+ 0\.1\)$")
    additional_transform: str = Field(pattern=r"^none$")
    reference_statistic: str = Field(pattern=r"^gene_wise_median$")
    outcome_fields_permitted: bool
    validation_data_permitted: bool
    classifier_execution_permitted: bool
    generative_ai_processing_permitted: bool

    @model_validator(mode="after")
    def enforce_outcome_blind_construction(self) -> GSE81538ReferenceConstructionPlan:
        if self.expected_sample_count != 100 or self.expected_gene_count != 50:
            raise ValueError("fixed reference requires 100 samples and 50 genes")
        if any(
            (
                self.outcome_fields_permitted,
                self.validation_data_permitted,
                self.classifier_execution_permitted,
                self.generative_ai_processing_permitted,
            )
        ):
            raise ValueError("reference construction exceeded the approved boundary")
        return self


class GSE81538ReferenceConstructionReceipt(ReferenceConstructionModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    source_accession: str = Field(pattern=r"^GSE81538$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    constructed_at: datetime
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_metadata_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_protocol_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_object_sha256_verified: bool
    selection_manifest_sha256_verified: bool
    selected_sample_count: int = Field(gt=0)
    selected_er_negative_count: int = Field(ge=0)
    selected_er_positive_count: int = Field(ge=0)
    retained_gene_count: int = Field(gt=0)
    parsed_measurement_count: int = Field(gt=0)
    finite_measurement_count: int = Field(ge=0)
    input_scale: str = Field(pattern=r"^log2\(FPKM \+ 0\.1\)$")
    additional_transform_applied: bool
    reference_statistic: str = Field(pattern=r"^gene_wise_median$")
    reference_minimum: float
    reference_maximum: float
    reference_mean: float
    reference_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    reference_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_bytes: int = Field(gt=0)
    reference_gene_count: int = Field(gt=0)
    reference_immutable_verified: bool
    decision: ReferenceConstructionDecision
    limitations: list[str] = Field(min_length=1)
    participant_identifiers_retained_in_git: bool
    reference_values_retained_in_git: bool
    molecular_values_parsed: bool
    outcome_values_accessed: bool
    validation_data_accessed: bool
    classifier_executed: bool
    generative_ai_received_participant_data: bool
    reference_locked: bool

    @model_validator(mode="after")
    def reconcile_receipt(self) -> GSE81538ReferenceConstructionReceipt:
        if not all(
            (
                self.matrix_object_sha256_verified,
                self.selection_manifest_sha256_verified,
                self.reference_immutable_verified,
                self.molecular_values_parsed,
            )
        ):
            raise ValueError("passing construction requires all integrity gates")
        if self.selected_sample_count != 100 or self.reference_gene_count != 50:
            raise ValueError("constructed reference has changed dimensions")
        if self.selected_er_negative_count + self.selected_er_positive_count != 100:
            raise ValueError("reference strata do not reconcile")
        if self.parsed_measurement_count != self.finite_measurement_count:
            raise ValueError("reference input contains nonfinite measurements")
        if self.parsed_measurement_count != self.selected_sample_count * self.retained_gene_count:
            raise ValueError("reference measurements do not reconcile")
        if self.additional_transform_applied or self.reference_locked:
            raise ValueError("construction cannot transform input or lock the reference")
        if any(
            (
                self.participant_identifiers_retained_in_git,
                self.reference_values_retained_in_git,
                self.outcome_values_accessed,
                self.validation_data_accessed,
                self.classifier_executed,
                self.generative_ai_received_participant_data,
            )
        ):
            raise ValueError("reference construction exceeded its boundary")
        return self


def load_reference_construction_plan(path: Path) -> GSE81538ReferenceConstructionPlan:
    return GSE81538ReferenceConstructionPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_reference_construction_receipt(
    path: Path,
) -> GSE81538ReferenceConstructionReceipt:
    return GSE81538ReferenceConstructionReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_reference_construction_receipt(
    path: Path,
    receipt: GSE81538ReferenceConstructionReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("reference construction receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_reference_construction_schemas(plan_path: Path, receipt_path: Path) -> None:
    for path, model in (
        (plan_path, GSE81538ReferenceConstructionPlan),
        (receipt_path, GSE81538ReferenceConstructionReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
