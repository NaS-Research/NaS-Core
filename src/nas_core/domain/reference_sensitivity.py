"""Contracts for outcome-blind GSE81538 reference sensitivity diagnostics."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReferenceSensitivityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReferenceSensitivityDecision(StrEnum):
    PASS_WITH_LIMITATION = "pass_with_limitation"


class GSE81538ReferenceSensitivityPlan(ReferenceSensitivityModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_accession: str = Field(pattern=r"^GSE81538$")
    matrix_object_key: str = Field(pattern=r"^raw/[a-z0-9._/-]+$")
    matrix_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    metadata_object_key: str = Field(pattern=r"^raw/[a-z0-9._/-]+$")
    metadata_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selection_manifest_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    selection_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    primary_reference_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    primary_reference_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_metadata_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_construction_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_protocol_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sensitivity_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    expected_sample_count: int = Field(gt=0)
    expected_gene_count: int = Field(gt=0)
    trimmed_mean_fraction_each_tail: float = Field(gt=0, lt=0.5)
    alternative_target_per_stratum: int = Field(gt=0)
    input_scale: str = Field(pattern=r"^log2\(FPKM \+ 0\.1\)$")
    outcome_fields_permitted: bool
    validation_data_permitted: bool
    classifier_execution_permitted: bool
    generative_ai_processing_permitted: bool

    @model_validator(mode="after")
    def enforce_boundary(self) -> GSE81538ReferenceSensitivityPlan:
        if self.expected_sample_count != 100 or self.expected_gene_count != 50:
            raise ValueError("reference sensitivity requires the frozen 100-by-50 panel")
        if self.trimmed_mean_fraction_each_tail != 0.2:
            raise ValueError("the prespecified trimmed mean removes 20% per tail")
        if self.alternative_target_per_stratum != 50:
            raise ValueError("alternative-reference target is 50 per ER stratum")
        if any(
            (
                self.outcome_fields_permitted,
                self.validation_data_permitted,
                self.classifier_execution_permitted,
                self.generative_ai_processing_permitted,
            )
        ):
            raise ValueError("reference sensitivity exceeded its firewall")
        return self


class GSE81538ReferenceSensitivityReceipt(ReferenceSensitivityModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    source_accession: str = Field(pattern=r"^GSE81538$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    executed_at: datetime
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_metadata_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_construction_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_protocol_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    all_object_checksums_verified: bool
    primary_sample_count: int = Field(gt=0)
    primary_gene_count: int = Field(gt=0)
    parsed_measurement_count: int = Field(gt=0)
    trimmed_mean_fraction_each_tail: float = Field(gt=0, lt=0.5)
    trimmed_observations_per_gene: int = Field(gt=0)
    vector_pearson_correlation: float = Field(ge=-1, le=1)
    vector_spearman_correlation: float = Field(ge=-1, le=1)
    vector_mean_absolute_difference: float = Field(ge=0)
    vector_maximum_absolute_difference: float = Field(ge=0)
    vector_root_mean_square_difference: float = Field(ge=0)
    centered_profile_correlation_minimum: float = Field(ge=-1, le=1)
    centered_profile_correlation_median: float = Field(ge=-1, le=1)
    centered_profile_correlation_mean: float = Field(ge=-1, le=1)
    next_er_negative_available: int = Field(ge=0)
    next_er_positive_available: int = Field(ge=0)
    alternative_target_per_stratum: int = Field(gt=0)
    exact_alternative_balanced_reference_feasible: bool
    exact_alternative_reference_constructed: bool
    sensitivity_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    sensitivity_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sensitivity_bytes: int = Field(gt=0)
    sensitivity_immutable_verified: bool
    decision: ReferenceSensitivityDecision
    limitations: list[str] = Field(min_length=1)
    participant_identifiers_retained_in_git: bool
    reference_values_retained_in_git: bool
    molecular_values_parsed: bool
    outcome_values_accessed: bool
    validation_data_accessed: bool
    classifier_executed: bool
    generative_ai_received_participant_data: bool
    threshold_tuning_performed: bool
    reference_locked: bool

    @model_validator(mode="after")
    def reconcile(self) -> GSE81538ReferenceSensitivityReceipt:
        if not all((self.all_object_checksums_verified, self.sensitivity_immutable_verified)):
            raise ValueError("sensitivity integrity gates must pass")
        if self.primary_sample_count != 100 or self.primary_gene_count != 50:
            raise ValueError("primary reference dimensions changed")
        if self.parsed_measurement_count != 5000:
            raise ValueError("sensitivity must parse exactly 5,000 measurements")
        feasible = min(
            self.next_er_negative_available,
            self.next_er_positive_available,
        ) >= self.alternative_target_per_stratum
        if self.exact_alternative_balanced_reference_feasible != feasible:
            raise ValueError("alternative-reference feasibility does not reconcile")
        if self.exact_alternative_reference_constructed:
            raise ValueError("this outcome-blind panel must not silently change the subset")
        if any(
            (
                self.participant_identifiers_retained_in_git,
                self.reference_values_retained_in_git,
                self.outcome_values_accessed,
                self.validation_data_accessed,
                self.classifier_executed,
                self.generative_ai_received_participant_data,
                self.threshold_tuning_performed,
                self.reference_locked,
            )
        ):
            raise ValueError("sensitivity execution exceeded its boundary")
        return self


def load_reference_sensitivity_plan(path: Path) -> GSE81538ReferenceSensitivityPlan:
    return GSE81538ReferenceSensitivityPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_reference_sensitivity_receipt(path: Path) -> GSE81538ReferenceSensitivityReceipt:
    return GSE81538ReferenceSensitivityReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_reference_sensitivity_receipt(
    path: Path,
    receipt: GSE81538ReferenceSensitivityReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("reference sensitivity receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_reference_sensitivity_schemas(plan_path: Path, receipt_path: Path) -> None:
    for path, model in (
        (plan_path, GSE81538ReferenceSensitivityPlan),
        (receipt_path, GSE81538ReferenceSensitivityReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
