"""Typed contracts for AI-assisted literature screening without decision authority."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.literature import ScreeningDecision, ScreeningExclusionReason
from nas_core.domain.snapshots import StoredObject


class AdvisoryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdvisoryConfidence(StrEnum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class AdvisoryCriterion(StrEnum):
    PRIMARY_HUMAN_BREAST_TUMOR = "primary_human_breast_tumor"
    MOLECULAR_INTRINSIC_SUBTYPE = "molecular_intrinsic_subtype"
    CLINICAL_MOLECULAR_DISCORDANCE = "clinical_molecular_discordance"
    CLASSIFICATION_STABILITY_OR_UNCERTAINTY = "classification_stability_or_uncertainty"
    CLASSIFIER_OR_NORMALIZATION_METHOD = "classifier_or_normalization_method"
    RELEVANT_CORRELATE_OUTCOME_OR_VALIDATION = "relevant_correlate_outcome_or_validation"
    CITATION_CHAINING_ONLY = "citation_chaining_only"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class AIAdvisoryRecommendation(AdvisoryModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    recommendation: ScreeningDecision
    confidence: AdvisoryConfidence
    matched_criteria: list[AdvisoryCriterion] = Field(min_length=1)
    exclusion_reason: ScreeningExclusionReason | None = None
    evidence_sentence_ids: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=800)
    human_review_required: bool

    @model_validator(mode="after")
    def validate_advisory_boundary(self) -> AIAdvisoryRecommendation:
        if self.recommendation is ScreeningDecision.PENDING:
            raise ValueError("AI must recommend include, exclude, or unclear")
        if self.recommendation is ScreeningDecision.EXCLUDE and self.exclusion_reason is None:
            raise ValueError("an AI exclusion recommendation requires one protocol reason")
        if self.recommendation is not ScreeningDecision.EXCLUDE and self.exclusion_reason:
            raise ValueError("only an AI exclusion recommendation may have an exclusion reason")
        if not self.human_review_required:
            raise ValueError("all AI screening recommendations require human review")
        if len(self.evidence_sentence_ids) != len(set(self.evidence_sentence_ids)):
            raise ValueError("evidence sentence IDs must be unique")
        return self


class AIAdvisoryBatchOutput(AdvisoryModel):
    recommendations: list[AIAdvisoryRecommendation] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_unique_records(self) -> AIAdvisoryBatchOutput:
        identifiers = [item.screening_id for item in self.recommendations]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("AI output may recommend each record only once")
        return self


class AIAdvisoryPolicy(AdvisoryModel):
    schema_version: str = "1.0.0"
    policy_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: str = Field(pattern=r"^implementation_locked$")
    provider: str = Field(pattern=r"^openai$")
    model: str = Field(min_length=1)
    reasoning_effort: str = Field(pattern=r"^(low|medium|high|xhigh|max)$")
    max_records_per_call: int = Field(ge=1, le=20)
    prompt_path: str = Field(min_length=1)
    permitted_data_classes: list[str] = Field(min_length=1, max_length=1)
    provider_store_enabled: bool
    live_execution_authorized: bool
    standard_abuse_monitoring_acknowledged: bool
    zero_data_retention_required: bool
    autonomous_decisions_allowed: bool
    human_review_required: bool
    calibration_required_before_routing: bool

    @model_validator(mode="after")
    def validate_governance(self) -> AIAdvisoryPolicy:
        if self.autonomous_decisions_allowed or not self.human_review_required:
            raise ValueError("this policy permits advisory output only")
        if not self.calibration_required_before_routing:
            raise ValueError("calibration is required before AI-based routing")
        if self.permitted_data_classes != ["public_open"]:
            raise ValueError("AI screening currently permits only public/open records")
        if self.provider_store_enabled:
            raise ValueError("provider response storage must remain disabled")
        retention_path = (
            self.standard_abuse_monitoring_acknowledged or self.zero_data_retention_required
        )
        if self.live_execution_authorized and not retention_path:
            raise ValueError("live execution requires an approved provider-retention path")
        return self


class AIModelCall(AdvisoryModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    response_id: str = Field(min_length=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class AIAdvisorySummary(AdvisoryModel):
    requested_record_count: int = Field(ge=1)
    recommendation_count: int = Field(ge=1)
    include_count: int = Field(ge=0)
    exclude_count: int = Field(ge=0)
    unclear_count: int = Field(ge=0)
    high_confidence_count: int = Field(ge=0)
    moderate_confidence_count: int = Field(ge=0)
    low_confidence_count: int = Field(ge=0)
    human_decisions_recorded: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_counts(self) -> AIAdvisorySummary:
        if (
            self.include_count + self.exclude_count + self.unclear_count
            != self.recommendation_count
        ):
            raise ValueError("recommendation counts do not reconcile")
        confidence_total = (
            self.high_confidence_count + self.moderate_confidence_count + self.low_confidence_count
        )
        if confidence_total != self.recommendation_count:
            raise ValueError("confidence counts do not reconcile")
        if self.requested_record_count != self.recommendation_count:
            raise ValueError("every requested record requires one recommendation")
        if self.human_decisions_recorded:
            raise ValueError("an AI advisory run cannot record human decisions")
        return self


class AIAdvisoryManifest(AdvisoryModel):
    schema_version: str = "1.0.0"
    advisory_run_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    based_on_progress_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    policy_version: str = Field(min_length=1)
    policy_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prompt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    model_call: AIModelCall
    artifacts: list[StoredObject] = Field(min_length=3, max_length=3)
    summary: AIAdvisorySummary
    autonomous_decisions_allowed: bool
    final_decisions_recorded: int = Field(ge=0)
    scientific_conclusions_drawn: bool
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_boundary(self) -> AIAdvisoryManifest:
        if (
            self.autonomous_decisions_allowed
            or self.final_decisions_recorded
            or self.scientific_conclusions_drawn
        ):
            raise ValueError("AI advisory manifests cannot record decisions or conclusions")
        return self


class AIAdvisoryReceipt(AdvisoryModel):
    schema_version: str = "1.0.0"
    advisory_run_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    based_on_progress_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    policy_version: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    manifest_object_key: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    summary: AIAdvisorySummary
    verified_at: datetime
    manifest_checksum_verified: bool
    artifact_checksums_verified: bool
    evidence_references_verified: bool
    count_invariants_verified: bool
    calibration_status: str = Field(pattern=r"^required$")
    autonomous_decisions_allowed: bool
    final_decisions_recorded: int = Field(ge=0)
    scientific_conclusions_drawn: bool


def load_ai_advisory_policy(path: Path) -> AIAdvisoryPolicy:
    return AIAdvisoryPolicy.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def write_ai_advisory_receipt(path: Path, receipt: AIAdvisoryReceipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_ai_advisory_schemas(
    output_path: Path,
    manifest_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (output_path, AIAdvisoryBatchOutput),
        (manifest_path, AIAdvisoryManifest),
        (receipt_path, AIAdvisoryReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        path.write_text(f"{payload}\n", encoding="utf-8")
