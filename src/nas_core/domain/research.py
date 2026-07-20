"""Typed research protocol models for reproducible NaS studies."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.governance.classifications import DataClassification


class StrictModel(BaseModel):
    """Base model that rejects undocumented protocol fields."""

    model_config = ConfigDict(extra="forbid")


class PlanStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PREREGISTERED = "preregistered"
    AMENDED = "amended"
    RETIRED = "retired"


class AnalysisMode(StrEnum):
    CONFIRMATORY = "confirmatory"
    EXPLORATORY = "exploratory"


class ReviewDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class DataRequirement(StrictModel):
    source_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    fields: list[str] = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)


class GovernanceBinding(StrictModel):
    source_id: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    actor_role: str = Field(min_length=1)
    classification: DataClassification


class Hypothesis(StrictModel):
    hypothesis_id: str = Field(pattern=r"^H[0-9]+$")
    mode: AnalysisMode
    primary: bool = False
    statement: str = Field(min_length=1)
    null_hypothesis: str = Field(min_length=1)
    alternative_hypothesis: str = Field(min_length=1)


class CohortDefinition(StrictModel):
    unit_of_analysis: str = Field(min_length=1)
    population: str = Field(min_length=1)
    inclusion_criteria: list[str] = Field(min_length=1)
    exclusion_criteria: list[str] = Field(min_length=1)
    record_selection: list[str] = Field(min_length=1)


class EndpointDefinition(StrictModel):
    name: str = Field(min_length=1)
    event: str = Field(min_length=1)
    time_origin: str = Field(min_length=1)
    time_calculation: list[str] = Field(min_length=1)
    censoring: str = Field(min_length=1)


class VariableDefinition(StrictModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    coding: str = Field(min_length=1)


class StatisticalModel(StrictModel):
    name: str = Field(min_length=1)
    method: str = Field(min_length=1)
    outcome: str = Field(min_length=1)
    exposure: str = Field(min_length=1)
    covariates: list[str] = Field(default_factory=list)
    estimand: str = Field(min_length=1)
    alpha: float = Field(gt=0, lt=1)
    diagnostics: list[str] = Field(min_length=1)


class SensitivityAnalysis(StrictModel):
    analysis_id: str = Field(pattern=r"^S[0-9]+$")
    description: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class MissingDataPlan(StrictModel):
    primary_strategy: str = Field(min_length=1)
    reporting: list[str] = Field(min_length=1)
    sensitivity_strategy: str = Field(min_length=1)


class MultiplicityPlan(StrictModel):
    primary_family: str = Field(min_length=1)
    primary_adjustment: str = Field(min_length=1)
    secondary_adjustment: str = Field(min_length=1)


class ReviewRecord(StrictModel):
    reviewer: str = Field(min_length=1)
    role: str = Field(min_length=1)
    decision: ReviewDecision
    reviewed_at: datetime | None = None
    notes: str = Field(min_length=1)


class AnalysisPlan(StrictModel):
    """Pre-specified study protocol with validation invariants."""

    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    protocol_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    title: str = Field(min_length=1)
    status: PlanStatus
    created_at: datetime
    objective: str = Field(min_length=1)
    design: str = Field(min_length=1)
    governance: GovernanceBinding
    data_requirements: list[DataRequirement] = Field(min_length=1)
    hypotheses: list[Hypothesis] = Field(min_length=1)
    cohort: CohortDefinition
    endpoint: EndpointDefinition
    variables: list[VariableDefinition] = Field(min_length=1)
    primary_model: StatisticalModel
    secondary_analyses: list[str] = Field(default_factory=list)
    sensitivity_analyses: list[SensitivityAnalysis] = Field(min_length=1)
    missing_data: MissingDataPlan
    multiplicity: MultiplicityPlan
    required_outputs: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    reviews: list[ReviewRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_protocol_invariants(self) -> AnalysisPlan:
        primary_confirmatory = [
            hypothesis
            for hypothesis in self.hypotheses
            if hypothesis.primary and hypothesis.mode is AnalysisMode.CONFIRMATORY
        ]
        if len(primary_confirmatory) != 1:
            raise ValueError("exactly one primary confirmatory hypothesis is required")

        primary_ids = [
            hypothesis.hypothesis_id for hypothesis in self.hypotheses if hypothesis.primary
        ]
        if len(primary_ids) != 1:
            raise ValueError("exactly one hypothesis must be marked primary")

        requirement_sources = {requirement.source_id for requirement in self.data_requirements}
        if requirement_sources != {self.governance.source_id}:
            raise ValueError("all data requirements must use the governed source")

        variable_names = {variable.name for variable in self.variables}
        referenced_variables = {
            self.primary_model.outcome,
            self.primary_model.exposure,
            *self.primary_model.covariates,
        }
        missing_variables = referenced_variables - variable_names
        if missing_variables:
            missing = ", ".join(sorted(missing_variables))
            raise ValueError(f"primary model references undefined variables: {missing}")

        if self.primary_model.outcome != self.endpoint.name:
            raise ValueError("primary model outcome must match the defined endpoint")

        if self.status in {PlanStatus.PREREGISTERED, PlanStatus.AMENDED}:
            approved = any(review.decision is ReviewDecision.APPROVED for review in self.reviews)
            if not approved:
                raise ValueError("a preregistered or amended plan requires an approved review")

        return self
