"""Typed program and research-question models for decision-led NaS research."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProgramModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProgramStatus(StrEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    RETIRED = "retired"


class ProgramStage(StrEnum):
    PLATFORM_QUALIFICATION = "platform_qualification"
    DISCOVERY = "discovery"
    EXTERNAL_VALIDATION = "external_validation"
    TRANSLATION = "translation"
    DEPLOYMENT = "deployment"


class StudyRole(StrEnum):
    QUALIFICATION = "qualification"
    DISCOVERY = "discovery"
    VALIDATION = "validation"
    TRANSLATION = "translation"


class QuestionStatus(StrEnum):
    PROPOSED = "proposed"
    SCREENED = "screened"
    SELECTED = "selected"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"


class LiteratureStatus(StrEnum):
    NOT_READY = "not_ready"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class ReviewDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class ProgramStudy(ProgramModel):
    study_id: str = Field(min_length=1)
    role: StudyRole
    title: str = Field(min_length=1)
    status: str = Field(min_length=1)
    purpose: str = Field(min_length=1)


class StageGate(ProgramModel):
    from_stage: ProgramStage
    to_stage: ProgramStage
    requirements: list[str] = Field(min_length=1)


class OncologyProgramCharter(ProgramModel):
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    program_id: str = Field(pattern=r"^NAS-ONC-[0-9]{3}$")
    charter_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    title: str = Field(min_length=1)
    status: ProgramStatus
    created_at: datetime
    mission: str = Field(min_length=1)
    therapeutic_area: str = Field(min_length=1)
    initial_learning_domain: str = Field(min_length=1)
    current_stage: ProgramStage
    intended_research_users: list[str] = Field(min_length=1)
    candidate_decision_domains: list[str] = Field(min_length=1)
    product_wedge_status: str = Field(min_length=1)
    operating_principles: list[str] = Field(min_length=1)
    stage_gates: list[StageGate] = Field(min_length=1)
    studies: list[ProgramStudy] = Field(min_length=1)
    governance_boundaries: list[str] = Field(min_length=1)
    program_success_criteria: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_program(self) -> OncologyProgramCharter:
        study_ids = [study.study_id for study in self.studies]
        if len(study_ids) != len(set(study_ids)):
            raise ValueError("program studies must have unique study IDs")
        if self.current_stage is ProgramStage.PLATFORM_QUALIFICATION and not any(
            study.role is StudyRole.QUALIFICATION for study in self.studies
        ):
            raise ValueError("platform qualification requires a qualification study")
        return self


class DecisionContext(ProgramModel):
    intended_user: str = Field(min_length=1)
    decision_to_support: str = Field(min_length=1)
    current_workflow: str = Field(min_length=1)
    unmet_need: str = Field(min_length=1)
    desired_action_change: str = Field(min_length=1)
    meaningful_outcome: str = Field(min_length=1)


class ScientificQuestion(ProgramModel):
    population: str = Field(min_length=1)
    exposure_or_intervention: str = Field(min_length=1)
    comparator: str = Field(min_length=1)
    outcomes: list[str] = Field(min_length=1)
    time_horizon: str = Field(min_length=1)
    estimand: str = Field(min_length=1)


class DataFeasibility(ProgramModel):
    required_modalities: list[str] = Field(min_length=1)
    available_sources: list[str] = Field(default_factory=list)
    missing_sources: list[str] = Field(default_factory=list)
    requires_real_world_data: bool
    public_data_role: str = Field(min_length=1)
    known_data_limitations: list[str] = Field(min_length=1)


class ValidationPath(ProgramModel):
    internal_validation: str = Field(min_length=1)
    external_validation: str = Field(min_length=1)
    biological_or_clinical_validation: str = Field(min_length=1)
    deployment_evaluation: str = Field(min_length=1)


class SelectionScores(ProgramModel):
    decision_impact: int = Field(ge=0, le=5)
    unmet_need: int = Field(ge=0, le=5)
    scientific_testability: int = Field(ge=0, le=5)
    data_feasibility: int = Field(ge=0, le=5)
    validation_feasibility: int = Field(ge=0, le=5)
    differentiation: int = Field(ge=0, le=5)
    translation_path: int = Field(ge=0, le=5)
    governance_feasibility: int = Field(ge=0, le=5)

    @property
    def total(self) -> int:
        return sum(
            (
                self.decision_impact,
                self.unmet_need,
                self.scientific_testability,
                self.data_feasibility,
                self.validation_feasibility,
                self.differentiation,
                self.translation_path,
                self.governance_feasibility,
            )
        )


class QuestionReview(ProgramModel):
    reviewer: str = Field(min_length=1)
    role: str = Field(min_length=1)
    decision: ReviewDecision
    reviewed_at: datetime | None = None
    rationale: str = Field(min_length=1)


class ResearchQuestionIntake(ProgramModel):
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    program_id: str = Field(pattern=r"^NAS-ONC-[0-9]{3}$")
    title: str = Field(min_length=1)
    status: QuestionStatus
    study_role: StudyRole
    created_at: datetime
    decision_context: DecisionContext
    scientific_question: ScientificQuestion
    precision_medicine_rationale: list[str] = Field(min_length=1)
    evidence_needed: list[str] = Field(min_length=1)
    data_feasibility: DataFeasibility
    analysis_families: list[str] = Field(min_length=1)
    validation_path: ValidationPath
    proposed_system_output: str = Field(min_length=1)
    scientific_success_criteria: list[str] = Field(min_length=1)
    decision_success_criteria: list[str] = Field(min_length=1)
    product_success_criteria: list[str] = Field(min_length=1)
    selection_scores: SelectionScores
    literature_status: LiteratureStatus
    reviews: list[QuestionReview] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_selection_and_literature_gates(self) -> ResearchQuestionIntake:
        all_approved = all(
            review.decision is ReviewDecision.APPROVED for review in self.reviews
        )
        if self.status is QuestionStatus.SELECTED and not all_approved:
            raise ValueError("a selected research question requires all recorded reviews approved")
        if self.literature_status is not LiteratureStatus.NOT_READY and (
            self.status is not QuestionStatus.SELECTED or not all_approved
        ):
            raise ValueError(
                "literature work requires a selected research question with all reviews approved"
            )
        if self.study_role is StudyRole.VALIDATION and not self.data_feasibility.available_sources:
            raise ValueError("a validation question requires an available data source")
        return self
