"""Contracts for fail-closed retrospective processed-expression QC."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetrospectiveQCModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RetrospectiveSourceRole(StrEnum):
    TCGA_DISCOVERY = "tcga_discovery"
    GSE96058_VALIDATION = "gse96058_validation"


class RetrospectiveQCState(StrEnum):
    VALID = "valid"
    SCHEMA_MISMATCH = "schema_mismatch"
    DUPLICATE_MAPPING = "duplicate_mapping"
    INSUFFICIENT_GENE_COVERAGE = "insufficient_gene_coverage"
    NONFINITE_INPUT = "nonfinite_input"
    NEGATIVE_FPKM = "negative_fpkm"
    BELOW_DECLARED_FLOOR = "below_declared_floor"
    CONSTANT_CENTERED_PROFILE = "constant_centered_profile"


class RetrospectiveProcessedInputQCSpecification(RetrospectiveQCModel):
    schema_version: str = "1.0.0"
    specification_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    bridge_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_object_key: str = Field(pattern=r"^derived/nas-brca-002/")
    reference_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    canonical_gene_symbols: list[str] = Field(min_length=50, max_length=50)
    historical_aliases: dict[str, str]
    required_gene_count: int = Field(ge=50, le=50)
    tcga_input_scale: str = Field(pattern=r"^fpkm_unstranded$")
    tcga_minimum_value: float = Field(ge=0, le=0)
    tcga_log2_offset: float = Field(gt=0)
    validation_input_scale: str = Field(pattern=r"^log2_fpkm_plus_0_1$")
    validation_declared_floor: float
    floor_absolute_tolerance: float = Field(gt=0, le=1e-9)
    require_exact_panel_only: bool
    require_unique_mapping: bool
    require_all_finite: bool
    imputation_allowed: bool
    cohort_centering_allowed: bool
    invalid_profile_action: str = Field(pattern=r"^abstain$")
    source_reacquisition_allowed_for_checksum_or_schema_failure: bool
    scientific_qc_rerun_allowed: bool
    validation_adaptation_allowed: bool
    classifier_execution_authorized: bool
    outcome_access_authorized: bool

    @model_validator(mode="after")
    def enforce_fail_closed_qc(self) -> RetrospectiveProcessedInputQCSpecification:
        if len(set(self.canonical_gene_symbols)) != 50:
            raise ValueError("canonical panel must contain 50 unique genes")
        if not all(
            (
                self.require_exact_panel_only,
                self.require_unique_mapping,
                self.require_all_finite,
                self.source_reacquisition_allowed_for_checksum_or_schema_failure,
            )
        ):
            raise ValueError("processed-input QC requirements cannot be weakened")
        if any(
            (
                self.imputation_allowed,
                self.cohort_centering_allowed,
                self.scientific_qc_rerun_allowed,
                self.validation_adaptation_allowed,
                self.classifier_execution_authorized,
                self.outcome_access_authorized,
            )
        ):
            raise ValueError("QC cannot impute, adapt, rerun scientific failure, or execute")
        return self


class RetrospectiveProfileQCResult(RetrospectiveQCModel):
    source_role: RetrospectiveSourceRole
    state: RetrospectiveQCState
    valid: bool
    canonical_gene_count: int = Field(ge=0, le=50)
    reason_codes: list[str]
    report_action: str = Field(pattern=r"^(continue_to_locked_scoring|abstain)$")

    @model_validator(mode="after")
    def reconcile_state(self) -> RetrospectiveProfileQCResult:
        if self.valid != (self.state is RetrospectiveQCState.VALID):
            raise ValueError("valid flag and QC state disagree")
        if self.valid != (self.report_action == "continue_to_locked_scoring"):
            raise ValueError("only valid profiles may continue to scoring")
        return self


class RetrospectiveProcessedInputQCReceipt(RetrospectiveQCModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bridge_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_object_verified: bool
    canonical_gene_count: int = Field(ge=50, le=50)
    historical_alias_count: int = Field(ge=3, le=3)
    failure_state_count: int = Field(ge=7, le=7)
    discovery_rule_frozen: bool
    validation_rule_frozen: bool
    imputation_prohibited: bool
    cohort_centering_prohibited: bool
    scientific_failure_rerun_prohibited: bool
    invalid_profiles_abstain: bool
    decision: str = Field(pattern=r"^retrospective_processed_input_qc_frozen$")
    molecular_values_accessed: bool
    validation_values_accessed: bool
    classifier_executed: bool
    outcomes_accessed: bool
    limitations: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_qc_freeze(self) -> RetrospectiveProcessedInputQCReceipt:
        if not all(
            (
                self.reference_object_verified,
                self.discovery_rule_frozen,
                self.validation_rule_frozen,
                self.imputation_prohibited,
                self.cohort_centering_prohibited,
                self.scientific_failure_rerun_prohibited,
                self.invalid_profiles_abstain,
            )
        ):
            raise ValueError("all processed-input QC safeguards must be frozen")
        if any(
            (
                self.molecular_values_accessed,
                self.validation_values_accessed,
                self.classifier_executed,
                self.outcomes_accessed,
            )
        ):
            raise ValueError("QC freeze cannot access study values or execute")
        return self


def load_retrospective_processed_input_qc_specification(
    path: Path,
) -> RetrospectiveProcessedInputQCSpecification:
    return RetrospectiveProcessedInputQCSpecification.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_retrospective_processed_input_qc_receipt(
    path: Path,
    receipt: RetrospectiveProcessedInputQCReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("retrospective QC receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_retrospective_processed_input_qc_schemas(
    specification_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (specification_path, RetrospectiveProcessedInputQCSpecification),
        (receipt_path, RetrospectiveProcessedInputQCReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
