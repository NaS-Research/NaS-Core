"""Governed nonexecuting designs for prospective technical calibration."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProspectiveCalibrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalibrationDesignStatus(StrEnum):
    FOUNDER_REVIEW_REQUIRED = "founder_review_required"


class CalibrationArmRole(StrEnum):
    FEASIBILITY_PILOT = "feasibility_pilot"
    PRIMARY_CALIBRATION = "primary_calibration"
    EXTRACTION_SENSITIVITY = "extraction_sensitivity"


class CalibrationParameterStatus(StrEnum):
    HYPOTHETICAL = "hypothetical"
    REQUIRES_PILOT = "requires_pilot"
    REQUIRES_FOUNDER_REVIEW = "requires_founder_review"


class CalibrationPlanningActivationStatus(StrEnum):
    INTERNAL_PLANNING_ACTIVE = "internal_planning_active"


class TechnicalReplicateArm(ProspectiveCalibrationModel):
    arm_id: str = Field(pattern=r"^CAL-ARM-[0-9]{3}$")
    role: CalibrationArmRole
    purpose: str = Field(min_length=1)
    technical_unit: str = Field(min_length=1)
    independent_steps: list[str] = Field(min_length=1)
    shared_steps: list[str] = Field(min_length=1)
    included_in_threshold_calibration: bool
    specimen_nonoverlap_required: bool
    pair_count: int | None = Field(default=None, ge=2)
    pair_count_status: CalibrationParameterStatus
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_arm(self) -> TechnicalReplicateArm:
        if not self.specimen_nonoverlap_required:
            raise ValueError("every arm must require specimen non-overlap")
        if (
            self.role is CalibrationArmRole.FEASIBILITY_PILOT
            and self.included_in_threshold_calibration
        ):
            raise ValueError("feasibility-pilot data cannot calibrate final thresholds")
        if (
            self.role is CalibrationArmRole.PRIMARY_CALIBRATION
            and not self.included_in_threshold_calibration
        ):
            raise ValueError("the primary calibration arm must calibrate thresholds")
        if self.pair_count is not None:
            raise ValueError(
                "a pre-approval design cannot silently lock a replicate-pair count"
            )
        return self


class CalibrationEstimand(ProspectiveCalibrationModel):
    estimand_id: str = Field(pattern=r"^CAL-EST-[0-9]{3}$")
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    primary: bool
    definition: str = Field(min_length=1)
    multiplicity_family: str = Field(min_length=1)
    parameter_status: CalibrationParameterStatus
    clinical_outcomes_used: bool

    @model_validator(mode="after")
    def validate_estimand(self) -> CalibrationEstimand:
        if self.clinical_outcomes_used:
            raise ValueError("technical calibration cannot use clinical outcomes")
        return self


class CalibrationDecisionItem(ProspectiveCalibrationModel):
    decision_id: str = Field(pattern=r"^CAL-DEC-[0-9]{3}$")
    question: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    status: CalibrationParameterStatus
    founder_decision_required: bool

    @model_validator(mode="after")
    def validate_decision(self) -> CalibrationDecisionItem:
        if not self.founder_decision_required:
            raise ValueError("every material design decision requires founder review")
        if self.status is CalibrationParameterStatus.HYPOTHETICAL:
            raise ValueError("material decisions must remain pending founder or pilot input")
        return self


class ProspectiveCalibrationExperimentDesign(ProspectiveCalibrationModel):
    schema_version: str = "1.0.0"
    design_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    phase: str = Field(pattern=r"^phase_1_method_calibration$")
    route_id: str = Field(pattern=r"^ROUTE-C$")
    design_status: CalibrationDesignStatus
    route_activation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    acquisition_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contact_revocation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    purpose: str = Field(min_length=1)
    design_principles: list[str] = Field(min_length=1)
    specimen_requirements: list[str] = Field(min_length=1)
    assay_workflow: list[str] = Field(min_length=1)
    arms: list[TechnicalReplicateArm] = Field(min_length=2)
    estimands: list[CalibrationEstimand] = Field(min_length=2)
    quality_controls: list[str] = Field(min_length=1)
    statistical_design: list[str] = Field(min_length=1)
    data_firewalls: list[str] = Field(min_length=1)
    acceptance_gates: list[str] = Field(min_length=1)
    no_go_criteria: list[str] = Field(min_length=1)
    unresolved_decisions: list[CalibrationDecisionItem] = Field(min_length=1)
    validation_source_ids: list[str] = Field(min_length=1)
    threshold_calibration_source_ids: list[str]
    external_contact_authorized: bool
    spending_authorized: bool
    procurement_authorized: bool
    specimen_acquisition_authorized: bool
    source_selected: bool
    patient_level_data_accessed: bool
    molecular_values_accessed: bool
    outcome_data_accessed: bool
    threshold_selection_authorized: bool
    study_execution_authorized: bool
    clinical_use_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def validate_nonexecuting_boundary(
        self,
    ) -> ProspectiveCalibrationExperimentDesign:
        arm_ids = [arm.arm_id for arm in self.arms]
        if len(arm_ids) != len(set(arm_ids)):
            raise ValueError("calibration arm IDs must be unique")
        roles = [arm.role for arm in self.arms]
        if roles.count(CalibrationArmRole.FEASIBILITY_PILOT) != 1:
            raise ValueError("design requires exactly one excluded feasibility pilot")
        if roles.count(CalibrationArmRole.PRIMARY_CALIBRATION) != 1:
            raise ValueError("design requires exactly one primary calibration arm")

        estimand_ids = [estimand.estimand_id for estimand in self.estimands]
        if len(estimand_ids) != len(set(estimand_ids)):
            raise ValueError("calibration estimand IDs must be unique")
        if sum(estimand.primary for estimand in self.estimands) != 1:
            raise ValueError("design requires exactly one primary estimand")

        decision_ids = [decision.decision_id for decision in self.unresolved_decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("calibration decision IDs must be unique")

        if "GEO:GSE96058" not in self.validation_source_ids:
            raise ValueError("GSE96058 must remain explicitly reserved for validation")
        if set(self.validation_source_ids) & set(self.threshold_calibration_source_ids):
            raise ValueError("validation sources cannot calibrate thresholds")
        if self.threshold_calibration_source_ids:
            raise ValueError("a planning design cannot select calibration sources")

        if any(
            (
                self.external_contact_authorized,
                self.spending_authorized,
                self.procurement_authorized,
                self.specimen_acquisition_authorized,
                self.source_selected,
                self.patient_level_data_accessed,
                self.molecular_values_accessed,
                self.outcome_data_accessed,
                self.threshold_selection_authorized,
                self.study_execution_authorized,
                self.clinical_use_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError(
                "a Phase 1 design cannot contact, spend, select a source, access data, "
                "or authorize execution"
            )
        return self


class CalibrationContactRevocation(ProspectiveCalibrationModel):
    schema_version: str = "1.0.0"
    revocation_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    question_id: str
    question_version: str
    route_id: str
    superseded_authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    revocation_statement: str
    founder_id: str
    founder_name: str
    reviewer_role: str
    revoked_at: str
    contact_authorized: bool
    revoked_inquiries: list[str]
    transmission_state: dict[str, bool | int]
    preserved_boundaries: dict[str, bool]

    @model_validator(mode="after")
    def validate_revocation(self) -> CalibrationContactRevocation:
        if self.contact_authorized:
            raise ValueError("the contact-revocation artifact must prohibit contact")
        if self.transmission_state.get("sent_message_count") != 0:
            raise ValueError("the contact revocation requires zero sent messages")
        if self.transmission_state.get("external_contact_prohibited") is not True:
            raise ValueError("external contact must remain prohibited")
        return self


def prospective_calibration_confirmation_statement(study_id: str) -> str:
    return (
        f"I approve {study_id} prospective calibration design 0.1.0 "
        "for planning only as written."
    )


class ProspectiveCalibrationFounderDecision(ProspectiveCalibrationModel):
    schema_version: str = "1.0.0"
    decision_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    route_id: str = Field(pattern=r"^ROUTE-C$")
    design_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation_statement: str
    founder_id: str
    founder_name: str
    reviewer_role: str
    confirmed_at: datetime
    planning_only_authorized: bool
    final_human_review_preserved: bool
    external_contact_authorized: bool
    laboratory_quote_authorized: bool
    spending_authorized: bool
    procurement_authorized: bool
    specimen_acquisition_authorized: bool
    data_access_authorized: bool
    threshold_selection_authorized: bool
    study_execution_authorized: bool
    clinical_use_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def validate_decision_boundary(
        self,
    ) -> ProspectiveCalibrationFounderDecision:
        if self.confirmation_statement != prospective_calibration_confirmation_statement(
            self.study_id
        ):
            raise ValueError("founder confirmation statement is not exact")
        if not self.planning_only_authorized:
            raise ValueError("the decision must authorize internal planning")
        if not self.final_human_review_preserved:
            raise ValueError("the founder's final human review must remain preserved")
        if any(
            (
                self.external_contact_authorized,
                self.laboratory_quote_authorized,
                self.spending_authorized,
                self.procurement_authorized,
                self.specimen_acquisition_authorized,
                self.data_access_authorized,
                self.threshold_selection_authorized,
                self.study_execution_authorized,
                self.clinical_use_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError(
                "planning-only approval cannot authorize external or executing actions"
            )
        return self


class ProspectiveCalibrationPlanningActivation(ProspectiveCalibrationModel):
    schema_version: str = "1.0.0"
    activation_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    route_id: str = Field(pattern=r"^ROUTE-C$")
    status: CalibrationPlanningActivationStatus
    design_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    founder_decision_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    activated_at: datetime
    unresolved_decision_ids: list[str] = Field(min_length=1)
    internal_scientific_planning_authorized: bool
    internal_statistical_planning_authorized: bool
    internal_operational_scenario_planning_authorized: bool
    internal_budget_scenario_planning_authorized: bool
    final_human_review_preserved: bool
    external_contact_authorized: bool
    laboratory_quote_authorized: bool
    spending_authorized: bool
    procurement_authorized: bool
    specimen_acquisition_authorized: bool
    source_selected: bool
    data_access_authorized: bool
    threshold_selection_authorized: bool
    study_execution_authorized: bool
    clinical_use_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def validate_activation_boundary(
        self,
    ) -> ProspectiveCalibrationPlanningActivation:
        if len(self.unresolved_decision_ids) != len(
            set(self.unresolved_decision_ids)
        ):
            raise ValueError("unresolved calibration decision IDs must be unique")
        if any(
            not decision_id.startswith("CAL-DEC-")
            for decision_id in self.unresolved_decision_ids
        ):
            raise ValueError("unresolved decisions must use CAL-DEC identifiers")
        if not all(
            (
                self.internal_scientific_planning_authorized,
                self.internal_statistical_planning_authorized,
                self.internal_operational_scenario_planning_authorized,
                self.internal_budget_scenario_planning_authorized,
                self.final_human_review_preserved,
            )
        ):
            raise ValueError("approved internal planning authorities must be preserved")
        if any(
            (
                self.external_contact_authorized,
                self.laboratory_quote_authorized,
                self.spending_authorized,
                self.procurement_authorized,
                self.specimen_acquisition_authorized,
                self.source_selected,
                self.data_access_authorized,
                self.threshold_selection_authorized,
                self.study_execution_authorized,
                self.clinical_use_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError(
                "planning activation cannot authorize external or executing actions"
            )
        return self


def load_prospective_calibration_design(
    path: Path,
) -> ProspectiveCalibrationExperimentDesign:
    return ProspectiveCalibrationExperimentDesign.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_calibration_contact_revocation(path: Path) -> CalibrationContactRevocation:
    return CalibrationContactRevocation.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_prospective_calibration_founder_decision(
    path: Path,
) -> ProspectiveCalibrationFounderDecision:
    return ProspectiveCalibrationFounderDecision.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_prospective_calibration_planning_activation(
    path: Path,
) -> ProspectiveCalibrationPlanningActivation:
    return ProspectiveCalibrationPlanningActivation.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_prospective_calibration_planning_activation(
    path: Path,
    activation: ProspectiveCalibrationPlanningActivation,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            activation.model_dump(mode="json"),
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def write_prospective_calibration_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            ProspectiveCalibrationExperimentDesign.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_prospective_calibration_authorization_schemas(
    decision_path: Path,
    activation_path: Path,
) -> None:
    for path, model in (
        (decision_path, ProspectiveCalibrationFounderDecision),
        (activation_path, ProspectiveCalibrationPlanningActivation),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
