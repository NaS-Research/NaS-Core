"""Typed statistical results and immutable survival-run manifests."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.research import ReviewDecision, ReviewRecord


class SurvivalModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalysisStatus(StrEnum):
    COMPLETE = "complete"
    NOT_INTERPRETABLE = "not_interpretable"
    SKIPPED = "skipped"
    FAILED = "failed"


class QualificationDecision(StrEnum):
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"


class ResultsGateStatus(StrEnum):
    PENDING_FOUNDER_REVIEW = "pending_founder_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"


class AnalysisArtifact(SurvivalModel):
    object_key: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class GroupSummary(SurvivalModel):
    group: str
    participants: int = Field(ge=0)
    events: int = Field(ge=0)
    censored: int = Field(ge=0)
    mean_age_years: float
    median_age_years: float
    median_follow_up_days: float


class CoefficientEstimate(SurvivalModel):
    term: str
    coefficient: float
    hazard_ratio: float = Field(gt=0)
    confidence_interval_lower: float = Field(gt=0)
    confidence_interval_upper: float = Field(gt=0)
    standard_error: float = Field(ge=0)
    z: float
    p_value: float = Field(ge=0, le=1)
    adjusted_p_value: float | None = Field(default=None, ge=0, le=1)


class ModelResult(SurvivalModel):
    analysis_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    status: AnalysisStatus
    participants: int = Field(ge=0)
    events: int = Field(ge=0)
    formula: str
    concordance_index: float | None = None
    log_likelihood: float | None = None
    coefficients: list[CoefficientEstimate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PHDiagnostic(SurvivalModel):
    term: str
    test_statistic: float
    p_value: float = Field(ge=0, le=1)
    assumption_violated: bool


class LogRankResult(SurvivalModel):
    test_statistic: float
    p_value: float = Field(ge=0, le=1)


class RiskTableRow(SurvivalModel):
    time_days: float = Field(ge=0)
    early_at_risk: int = Field(ge=0)
    advanced_at_risk: int = Field(ge=0)


class EditionDistribution(SurvivalModel):
    edition: str
    stage_group: str
    participants: int = Field(ge=0)


class InfluenceObservation(SurvivalModel):
    case_id: str
    term: str
    delta_beta_absolute: float = Field(ge=0)


class SurvivalAnalysisSummary(SurvivalModel):
    schema_version: str = "1.0.0"
    study_id: str
    protocol_version: str
    cohort_build_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    participant_count: int = Field(ge=0)
    event_count: int = Field(ge=0)
    groups: list[GroupSummary] = Field(min_length=2)
    log_rank: LogRankResult
    primary_model: ModelResult
    secondary_models: list[ModelResult]
    sensitivity_models: list[ModelResult]
    ph_diagnostics: list[PHDiagnostic]
    influential_observations: list[InfluenceObservation]
    ajcc_edition_distribution: list[EditionDistribution]
    risk_table: list[RiskTableRow]
    scientific_reproduction: str
    qualification_decision: QualificationDecision
    qualification_reasons: list[str] = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)
    generated_by_deterministic_code: bool = True

    @model_validator(mode="after")
    def validate_counts(self) -> SurvivalAnalysisSummary:
        if sum(group.participants for group in self.groups) != self.participant_count:
            raise ValueError("group participants do not equal analysis participants")
        if sum(group.events for group in self.groups) != self.event_count:
            raise ValueError("group events do not equal analysis events")
        return self


class SurvivalRunManifest(SurvivalModel):
    schema_version: str = "1.0.0"
    run_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str
    protocol_version: str
    protocol_tag: str
    cohort_build_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    cohort_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str
    code_revision: str = Field(min_length=7)
    executed_at: datetime
    random_seed: int
    parameters: dict[str, object]
    environment: dict[str, str]
    artifacts: list[AnalysisArtifact] = Field(min_length=1)
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class RunVerification(SurvivalModel):
    verified_at: datetime
    manifest_payload_checksum: Literal["passed"]
    artifact_sizes: Literal["passed"]
    artifact_checksums: Literal["passed"]
    participant_partition: Literal["passed"]
    event_partition: Literal["passed"]
    sensitivity_branch_completeness: Literal["passed"]
    typed_result_validation: Literal["passed"]
    figure_rendering: Literal["passed"]
    figure_layout: Literal["passed", "failed"]


class PrimaryResultSnapshot(SurvivalModel):
    participants: int = Field(ge=0)
    events: int = Field(ge=0)
    early_participants: int = Field(ge=0)
    early_events: int = Field(ge=0)
    advanced_participants: int = Field(ge=0)
    advanced_events: int = Field(ge=0)
    hazard_ratio: float = Field(gt=0)
    confidence_interval_lower: float = Field(gt=0)
    confidence_interval_upper: float = Field(gt=0)
    p_value: float = Field(ge=0, le=1)
    ph_test_p_value: float = Field(ge=0, le=1)
    ph_assumption_violated: bool


class SurvivalRunReceipt(SurvivalModel):
    schema_version: str = "1.0.0"
    study_id: str
    protocol_version: str
    protocol_tag: str
    cohort_build_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    cohort_tag: str
    run_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str
    code_revision: str = Field(min_length=7)
    executed_at: datetime
    manifest_object_key: str
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifacts: list[AnalysisArtifact] = Field(min_length=1)
    verification: RunVerification
    primary_result: PrimaryResultSnapshot
    scientific_reproduction: str
    qualification_decision: QualificationDecision
    sensitivity_statuses: dict[str, AnalysisStatus]
    material_findings: list[str] = Field(min_length=1)
    results_gate_status: ResultsGateStatus
    reviews: list[ReviewRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_gate(self) -> SurvivalRunReceipt:
        if (
            self.primary_result.early_participants + self.primary_result.advanced_participants
            != self.primary_result.participants
        ):
            raise ValueError("exposure-group participants do not equal primary participants")
        if (
            self.primary_result.early_events + self.primary_result.advanced_events
            != self.primary_result.events
        ):
            raise ValueError("exposure-group events do not equal primary events")
        if set(self.sensitivity_statuses) != {"S1", "S2", "S3", "S4", "S5"}:
            raise ValueError("run receipt must record all five sensitivity branches")
        if self.results_gate_status is ResultsGateStatus.APPROVED:
            required = [review for review in self.reviews if review.required_for_gate]
            if not required or any(
                review.decision is not ReviewDecision.APPROVED for review in required
            ):
                raise ValueError("an approved results gate requires all gate reviews approved")
        return self


def load_survival_run_receipt(path: Path) -> SurvivalRunReceipt:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SurvivalRunReceipt.model_validate(payload)


def write_survival_schemas(summary_path: Path, manifest_path: Path, receipt_path: Path) -> None:
    for path, model in (
        (summary_path, SurvivalAnalysisSummary),
        (manifest_path, SurvivalRunManifest),
        (receipt_path, SurvivalRunReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        path.write_text(f"{payload}\n", encoding="utf-8")
