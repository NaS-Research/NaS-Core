"""Governed contracts for performance-blind, uncalibrated retrospective scoring."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class UncalibratedScoringModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UncalibratedScoringState(StrEnum):
    UNCALIBRATED = "uncalibrated"
    SCORE_FAILED = "score_failed"
    QC_FAILED = "qc_failed"


class UncalibratedScoringSpecification(UncalibratedScoringModel):
    schema_version: str = "1.0.0"
    specification_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    processed_input_qc_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expression_bridge_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    numerical_conformance_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    canonical_subtype_order: list[str] = Field(min_length=5, max_length=5)
    correlation_metric: str = Field(pattern=r"^spearman$")
    numerical_tolerance: float = Field(gt=0.0, le=1e-6)
    technical_calibration_complete: bool
    threshold_selection_allowed: bool
    reported_label_allowed: bool
    outcome_access_authorized: bool
    validation_access_authorized: bool
    valid_score_state: str = Field(pattern=r"^uncalibrated$")
    valid_score_action: str = Field(pattern=r"^abstain$")
    valid_score_reason: str = Field(pattern=r"^technical_calibration_incomplete$")

    @model_validator(mode="after")
    def enforce_uncalibrated_boundary(self) -> UncalibratedScoringSpecification:
        if len(set(self.canonical_subtype_order)) != 5:
            raise ValueError("canonical subtype order must contain five unique labels")
        if any(
            (
                self.technical_calibration_complete,
                self.threshold_selection_allowed,
                self.reported_label_allowed,
                self.outcome_access_authorized,
                self.validation_access_authorized,
            )
        ):
            raise ValueError("uncalibrated scoring cannot cross calibration firewalls")
        return self


class UncalibratedProfileScore(UncalibratedScoringModel):
    state: UncalibratedScoringState
    scored: bool
    report_action: str = Field(pattern=r"^abstain$")
    top_subtype: str | None
    top_score: float | None
    runner_up_subtype: str | None
    runner_up_score: float | None
    margin: float | None
    reason_codes: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def reconcile_score(self) -> UncalibratedProfileScore:
        values = (
            self.top_subtype,
            self.top_score,
            self.runner_up_subtype,
            self.runner_up_score,
            self.margin,
        )
        if self.scored != (self.state is UncalibratedScoringState.UNCALIBRATED):
            raise ValueError("only uncalibrated results may contain a score")
        if self.scored != all(value is not None for value in values):
            raise ValueError("score fields must be all present or all absent")
        if self.scored and "technical_calibration_incomplete" not in self.reason_codes:
            raise ValueError("scored profiles must declare incomplete calibration")
        return self


class AttemptedDenominatorAccounting(UncalibratedScoringModel):
    attempted_count: int = Field(ge=0)
    qc_valid_count: int = Field(ge=0)
    qc_failed_count: int = Field(ge=0)
    scored_count: int = Field(ge=0)
    score_failed_count: int = Field(ge=0)
    uncalibrated_count: int = Field(ge=0)
    abstained_count: int = Field(ge=0)
    reported_label_count: int = Field(ge=0, le=0)

    @model_validator(mode="after")
    def reconcile_counts(self) -> AttemptedDenominatorAccounting:
        if self.attempted_count != self.qc_valid_count + self.qc_failed_count:
            raise ValueError("attempted count must equal QC-valid plus QC-failed")
        if self.qc_valid_count != self.scored_count + self.score_failed_count:
            raise ValueError("QC-valid count must equal scored plus score-failed")
        if self.scored_count != self.uncalibrated_count:
            raise ValueError("every score must remain uncalibrated")
        if self.abstained_count != self.attempted_count:
            raise ValueError("every attempted profile must abstain before calibration")
        return self


class UncalibratedScoringReceipt(UncalibratedScoringModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependency_hashes_verified: bool
    fixed_spearman_scoring_frozen: bool
    uncalibrated_state_mandatory: bool
    all_attempts_abstain: bool
    denominator_reconciliation_frozen: bool
    reported_label_count: int = Field(ge=0, le=0)
    decision: str = Field(pattern=r"^uncalibrated_scoring_boundary_frozen$")
    molecular_values_accessed: bool
    validation_values_accessed: bool
    outcomes_accessed: bool
    study_classifier_executed: bool
    limitations: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_freeze(self) -> UncalibratedScoringReceipt:
        if not all(
            (
                self.dependency_hashes_verified,
                self.fixed_spearman_scoring_frozen,
                self.uncalibrated_state_mandatory,
                self.all_attempts_abstain,
                self.denominator_reconciliation_frozen,
            )
        ):
            raise ValueError("all uncalibrated scoring safeguards must be frozen")
        if any(
            (
                self.molecular_values_accessed,
                self.validation_values_accessed,
                self.outcomes_accessed,
                self.study_classifier_executed,
            )
        ):
            raise ValueError("boundary freeze cannot access study data or execute")
        return self


def load_uncalibrated_scoring_specification(
    path: Path,
) -> UncalibratedScoringSpecification:
    return UncalibratedScoringSpecification.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_uncalibrated_scoring_receipt(
    path: Path,
    receipt: UncalibratedScoringReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("uncalibrated scoring receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_uncalibrated_scoring_schemas(
    specification_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (specification_path, UncalibratedScoringSpecification),
        (receipt_path, UncalibratedScoringReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
