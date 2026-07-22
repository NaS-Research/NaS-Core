"""Typed preselection novelty and feasibility artifacts for discovery studies."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class DiscoveryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DraftStatus(StrEnum):
    DRAFT = "draft"
    LOCKED = "locked"
    COMPLETE = "complete"


class AuditStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    READY_FOR_FOUNDER_DECISION = "ready_for_founder_decision"
    PASSED = "passed"
    CHANGES_REQUESTED = "changes_requested"
    ON_HOLD = "on_hold"
    FAILED = "failed"


class SourceAssessmentStatus(StrEnum):
    UNASSESSED = "unassessed"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuthorizationDecision(StrEnum):
    APPROVED = "approved"
    REVOKED = "revoked"


class AuthorizedActivity(StrEnum):
    LITERATURE_RETRIEVAL = "literature_retrieval"
    SOURCE_FEASIBILITY_ASSESSMENT = "source_feasibility_assessment"
    NON_OUTCOME_METADATA_QUERIES = "non_outcome_metadata_queries"


class PhaseZeroAuthorization(DiscoveryModel):
    reviewer: str = Field(min_length=1)
    role: str = Field(min_length=1)
    review_type: str = Field(pattern=r"^internal_self_review$")
    decision: AuthorizationDecision
    authorized_at: datetime
    authorized_activities: list[AuthorizedActivity] = Field(min_length=1)
    prohibited_activities: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    conflict_disclosure: str = Field(min_length=1)


class CandidateContribution(DiscoveryModel):
    established_knowledge: list[str] = Field(min_length=1)
    unresolved_problem: str = Field(min_length=1)
    proposed_contribution: str = Field(min_length=1)
    falsification_condition: str = Field(min_length=1)
    value_if_null: str = Field(min_length=1)


class PhaseZeroPlan(DiscoveryModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    status: AuditStatus
    objective: str = Field(min_length=1)
    candidate_thesis: str = Field(min_length=1)
    contribution: CandidateContribution
    novelty_questions: list[str] = Field(min_length=1)
    data_questions: list[str] = Field(min_length=1)
    external_validation_questions: list[str] = Field(min_length=1)
    hard_pass_gates: list[str] = Field(min_length=1)
    no_go_criteria: list[str] = Field(min_length=1)
    deliverables: list[str] = Field(min_length=1)
    prohibited_actions: list[str] = Field(min_length=1)
    authorization: PhaseZeroAuthorization | None = None


class SearchSource(DiscoveryModel):
    source_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    official_url: HttpUrl
    query: str = Field(min_length=1)
    purpose: str = Field(min_length=1)


class LiteratureSearchStrategy(DiscoveryModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    strategy_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    status: DraftStatus
    objective: str = Field(min_length=1)
    sources: list[SearchSource] = Field(min_length=2)
    date_range: str = Field(min_length=1)
    languages: list[str] = Field(min_length=1)
    inclusion_criteria: list[str] = Field(min_length=1)
    exclusion_criteria: list[str] = Field(min_length=1)
    screening_process: list[str] = Field(min_length=1)
    extraction_fields: list[str] = Field(min_length=1)
    synthesis_plan: list[str] = Field(min_length=1)
    stopping_rule: str = Field(min_length=1)
    retrieval_authorized: bool = False

    @model_validator(mode="after")
    def validate_lock(self) -> LiteratureSearchStrategy:
        if self.status is DraftStatus.DRAFT and self.retrieval_authorized:
            raise ValueError("a draft search strategy cannot authorize retrieval")
        return self


class VariableRequirement(DiscoveryModel):
    domain: str = Field(min_length=1)
    concepts: list[str] = Field(min_length=1)
    purpose: str = Field(min_length=1)
    required_for_primary_analysis: bool
    maximum_missing_fraction: float | None = Field(default=None, ge=0, le=1)


class CandidateDataSource(DiscoveryModel):
    candidate_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    intended_role: str = Field(min_length=1)
    authoritative_url: HttpUrl
    assessment_status: SourceAssessmentStatus
    source_registry_status: str = Field(min_length=1)
    access_and_license_questions: list[str] = Field(min_length=1)
    compatibility_questions: list[str] = Field(min_length=1)
    independence_questions: list[str] = Field(min_length=1)


class DataFeasibilitySpecification(DiscoveryModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    specification_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    status: DraftStatus
    discovery_source_id: str = Field(min_length=1)
    discovery_source_registry_status: str = Field(min_length=1)
    variable_requirements: list[VariableRequirement] = Field(min_length=1)
    candidate_validation_sources: list[CandidateDataSource] = Field(min_length=1)
    compatibility_gates: list[str] = Field(min_length=1)
    minimum_feasibility_outputs: list[str] = Field(min_length=1)
    outcome_data_access_authorized: bool = False

    @model_validator(mode="after")
    def validate_authority(self) -> DataFeasibilitySpecification:
        if self.status is DraftStatus.DRAFT and self.outcome_data_access_authorized:
            raise ValueError("a draft feasibility specification cannot authorize outcome access")
        return self


def load_phase_zero_artifacts(
    plan_path: Path,
    search_path: Path,
    feasibility_path: Path,
) -> tuple[PhaseZeroPlan, LiteratureSearchStrategy, DataFeasibilitySpecification]:
    plan = PhaseZeroPlan.model_validate(_read_yaml(plan_path))
    search = LiteratureSearchStrategy.model_validate(_read_yaml(search_path))
    feasibility = DataFeasibilitySpecification.model_validate(_read_yaml(feasibility_path))
    identities = {
        (plan.study_id, plan.question_id, plan.question_version),
        (search.study_id, search.question_id, search.question_version),
        (feasibility.study_id, feasibility.question_id, feasibility.question_version),
    }
    if len(identities) != 1:
        raise ValueError("Phase 0 artifacts must identify the same study question version")
    authorization = plan.authorization
    if search.retrieval_authorized:
        if search.status is not DraftStatus.LOCKED:
            raise ValueError("literature retrieval requires a locked search strategy")
        if authorization is None or authorization.decision is not AuthorizationDecision.APPROVED:
            raise ValueError("literature retrieval requires founder Phase 0 authorization")
        if AuthorizedActivity.LITERATURE_RETRIEVAL not in authorization.authorized_activities:
            raise ValueError("founder authorization does not include literature retrieval")
    if feasibility.status is DraftStatus.LOCKED:
        if authorization is None or authorization.decision is not AuthorizationDecision.APPROVED:
            raise ValueError("locked feasibility work requires founder Phase 0 authorization")
        if (
            AuthorizedActivity.SOURCE_FEASIBILITY_ASSESSMENT
            not in authorization.authorized_activities
        ):
            raise ValueError("founder authorization does not include source feasibility")
    if feasibility.outcome_data_access_authorized:
        raise ValueError("Phase 0 cannot authorize outcome-bearing data access")
    return plan, search, feasibility


def write_discovery_schemas(plan_path: Path, search_path: Path, feasibility_path: Path) -> None:
    for path, model in (
        (plan_path, PhaseZeroPlan),
        (search_path, LiteratureSearchStrategy),
        (feasibility_path, DataFeasibilitySpecification),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        path.write_text(f"{payload}\n", encoding="utf-8")


def _read_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
