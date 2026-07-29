"""Governed Phase 1 planning under standing founder autonomy."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationPlanningModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def standing_autonomy_statement() -> str:
    return (
        "I authorize Codex to autonomously complete NaS-Core and NAS-BRCA-002 "
        "through preparation of the final human-review package. Codex may make "
        "and document reasonable, reversible scientific, statistical, engineering, "
        "and project-management decisions; use approved public/open data; run "
        "analyses; update the manuscript and project records; test; commit; and "
        "push to main. Do not request routine founder approvals. Stop only before "
        "spending or procurement, credentials or paid access, external contact, "
        "controlled data, PHI or specimen acquisition, destructive or irreversible "
        "actions, clinical use, external publication or submission, or a material "
        "change to the study’s purpose or intended claim. Preserve my final human "
        "review."
    )


class StandingAutonomyAuthorization(CalibrationPlanningModel):
    schema_version: str = "1.0.0"
    authorization_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    project_id: str = Field(pattern=r"^NaS-Core$")
    authorization_statement: str
    founder_id: str
    founder_name: str
    authorized_at: datetime
    delegated_internal_actions: list[str] = Field(min_length=1)
    stop_conditions: list[str] = Field(min_length=1)
    routine_founder_approvals_required: bool
    final_human_review_preserved: bool
    external_contact_authorized: bool
    spending_authorized: bool
    controlled_data_authorized: bool
    phi_authorized: bool
    specimen_acquisition_authorized: bool
    clinical_use_authorized: bool
    external_publication_authorized: bool
    external_submission_authorized: bool

    @model_validator(mode="after")
    def validate_delegation(self) -> StandingAutonomyAuthorization:
        if self.authorization_statement != standing_autonomy_statement():
            raise ValueError("standing autonomy statement is not exact")
        if self.routine_founder_approvals_required:
            raise ValueError("standing autonomy must remove routine founder approvals")
        if not self.final_human_review_preserved:
            raise ValueError("final human review must remain preserved")
        required_actions = {
            "reversible_scientific_decisions",
            "reversible_statistical_decisions",
            "engineering_implementation",
            "project_management",
            "approved_public_open_data_use",
            "analysis_execution",
            "manuscript_and_project_record_updates",
            "testing",
            "commit_and_push_main",
        }
        if not required_actions.issubset(self.delegated_internal_actions):
            raise ValueError("standing autonomy is missing delegated internal actions")
        required_stops = {
            "spending_or_procurement",
            "credentials_or_paid_access",
            "external_contact",
            "controlled_data_phi_or_specimen_acquisition",
            "destructive_or_irreversible_actions",
            "clinical_use",
            "external_publication_or_submission",
            "material_change_to_purpose_or_intended_claim",
        }
        if not required_stops.issubset(self.stop_conditions):
            raise ValueError("standing autonomy is missing required stop conditions")
        if any(
            (
                self.external_contact_authorized,
                self.spending_authorized,
                self.controlled_data_authorized,
                self.phi_authorized,
                self.specimen_acquisition_authorized,
                self.clinical_use_authorized,
                self.external_publication_authorized,
                self.external_submission_authorized,
            )
        ):
            raise ValueError("standing autonomy cannot authorize a stop-condition action")
        return self


class PlanningStatus(StrEnum):
    INTERNALLY_FROZEN_PENDING_EVIDENCE = "internally_frozen_pending_evidence"


class CompatibilityCriterion(CalibrationPlanningModel):
    criterion_id: str = Field(pattern=r"^PLAT-[0-9]{3}$")
    requirement: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    evidence_required: list[str] = Field(min_length=1)
    status: str = Field(pattern=r"^pending_external_or_experimental_evidence$")


class PlatformCompatibilityPlan(CalibrationPlanningModel):
    intended_platform_family: str = Field(pattern=r"^bulk_rna_sequencing$")
    exact_instrument_selected: bool
    exact_kit_selected: bool
    exact_chemistry_selected: bool
    vendor_selected: bool
    primary_repeat_architecture: str
    extraction_sensitivity_separate: bool
    compatibility_criteria: list[CompatibilityCriterion] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unselected_platform(self) -> PlatformCompatibilityPlan:
        if any(
            (
                self.exact_instrument_selected,
                self.exact_kit_selected,
                self.exact_chemistry_selected,
                self.vendor_selected,
            )
        ):
            raise ValueError("internal compatibility planning cannot select a vendor stack")
        if not self.extraction_sensitivity_separate:
            raise ValueError("extraction sensitivity must remain a separate arm")
        return self


class ExcludedPilotPlan(CalibrationPlanningModel):
    attempted_pairs: int = Field(ge=20, le=60)
    independent_biological_sources_target: int = Field(ge=20, le=60)
    measurements_per_pair: int = Field(ge=2, le=2)
    permanently_excluded_from_primary_calibration: bool
    permanently_excluded_from_external_validation: bool
    outcomes_prohibited: bool
    permitted_estimates: list[str] = Field(min_length=1)
    final_pair_count_approved: bool
    blinded_reestimation_required: bool
    interpretation: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_pilot_firewall(self) -> ExcludedPilotPlan:
        if self.independent_biological_sources_target > self.attempted_pairs:
            raise ValueError("independent source target cannot exceed attempted pairs")
        if not all(
            (
                self.permanently_excluded_from_primary_calibration,
                self.permanently_excluded_from_external_validation,
                self.outcomes_prohibited,
                self.blinded_reestimation_required,
            )
        ):
            raise ValueError("the feasibility pilot must remain excluded and blinded")
        if self.final_pair_count_approved:
            raise ValueError("the pilot plan cannot preapprove a final pair count")
        return self


class CoverageDimension(CalibrationPlanningModel):
    dimension_id: str = Field(pattern=r"^COV-[0-9]{3}$")
    name: str
    categories: list[str] = Field(min_length=2)
    minimum_per_category: int | None = Field(default=None, ge=2)
    outcome_derived: bool
    applied_marginally_not_cartesian: bool

    @model_validator(mode="after")
    def validate_coverage(self) -> CoverageDimension:
        if self.outcome_derived:
            raise ValueError("technical coverage cannot be outcome-derived")
        if not self.applied_marginally_not_cartesian:
            raise ValueError("small-pilot coverage must use marginal quotas")
        return self


class MultiplicityFamily(CalibrationPlanningModel):
    family_id: str = Field(pattern=r"^MULT-[0-9]{3}$")
    role: str = Field(pattern=r"^(primary|confirmatory|descriptive|exploratory)$")
    endpoints: list[str] = Field(min_length=1)
    method: str
    error_rate: float | None = Field(default=None, gt=0.0, lt=1.0)
    supports_primary_claim: bool


class SymbolicCostVariable(CalibrationPlanningModel):
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    definition: str
    unit: str
    numeric_value: float | None = None

    @model_validator(mode="after")
    def validate_symbolic_only(self) -> SymbolicCostVariable:
        if self.numeric_value is not None:
            raise ValueError("symbolic budget variables cannot contain prices or quantities")
        return self


class SymbolicBudgetPlan(CalibrationPlanningModel):
    formula: str
    variables: list[SymbolicCostVariable] = Field(min_length=1)
    currency_selected: bool
    laboratory_quote_obtained: bool
    total_cost_calculated: bool

    @model_validator(mode="after")
    def validate_symbolic_budget(self) -> SymbolicBudgetPlan:
        if any(
            (
                self.currency_selected,
                self.laboratory_quote_obtained,
                self.total_cost_calculated,
            )
        ):
            raise ValueError("the budget model must remain symbolic")
        return self


class PhaseOneInternalPlanningBundle(CalibrationPlanningModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    route_id: str = Field(pattern=r"^ROUTE-C$")
    status: PlanningStatus
    autonomy_authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    planning_decision_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    planning_activation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    platform_compatibility: PlatformCompatibilityPlan
    excluded_pilot: ExcludedPilotPlan
    coverage: list[CoverageDimension] = Field(min_length=1)
    multiplicity: list[MultiplicityFamily] = Field(min_length=1)
    symbolic_budget: SymbolicBudgetPlan
    retained_denominators: list[str] = Field(min_length=1)
    planning_assumptions: list[str] = Field(min_length=1)
    evidence_needed_to_close: list[str] = Field(min_length=1)
    final_human_review_preserved: bool
    data_accessed: bool
    source_selected: bool
    threshold_selected: bool
    final_primary_pair_count_approved: bool
    external_contact_authorized: bool
    spending_authorized: bool
    specimen_acquisition_authorized: bool
    study_execution_authorized: bool
    clinical_use_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def validate_nonexecuting_plan(self) -> PhaseOneInternalPlanningBundle:
        primary = [family for family in self.multiplicity if family.role == "primary"]
        if len(primary) != 1 or len(primary[0].endpoints) != 1:
            raise ValueError("the plan requires one unambiguous primary endpoint")
        if primary[0].method != "single_primary_no_adjustment":
            raise ValueError("the single primary endpoint must not imply hidden multiplicity")
        if not self.final_human_review_preserved:
            raise ValueError("final human review must remain preserved")
        if any(
            (
                self.data_accessed,
                self.source_selected,
                self.threshold_selected,
                self.final_primary_pair_count_approved,
                self.external_contact_authorized,
                self.spending_authorized,
                self.specimen_acquisition_authorized,
                self.study_execution_authorized,
                self.clinical_use_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError("internal planning cannot authorize or claim execution")
        return self


def load_standing_autonomy_authorization(
    path: Path,
) -> StandingAutonomyAuthorization:
    return StandingAutonomyAuthorization.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_phase_one_internal_planning_bundle(
    path: Path,
) -> PhaseOneInternalPlanningBundle:
    return PhaseOneInternalPlanningBundle.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_planning_schemas(
    authorization_path: Path,
    bundle_path: Path,
) -> None:
    for path, model in (
        (authorization_path, StandingAutonomyAuthorization),
        (bundle_path, PhaseOneInternalPlanningBundle),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
