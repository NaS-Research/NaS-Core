"""Governed acquisition contracts for independent technical calibration data."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TechnicalCalibrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalibrationSourceDisposition(StrEnum):
    RESERVED_EXTERNAL_VALIDATION = "reserved_external_validation"
    PARTICIPANT_LEVEL_DATA_UNAVAILABLE = "participant_level_data_unavailable"
    REQUIRES_DUE_DILIGENCE = "requires_due_diligence"
    FUTURE_NAS_EXPERIMENT = "future_nas_experiment"


class CalibrationAccessClass(StrEnum):
    PUBLIC_OPEN = "public_open"
    LICENSED = "licensed"
    CONTROLLED = "controlled"
    NOT_YET_CREATED = "not_yet_created"


class CalibrationSourceCandidate(TechnicalCalibrationModel):
    source_id: str = Field(pattern=r"^CALSRC-[0-9]{3}$")
    label: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    assay_or_platform: str = Field(min_length=1)
    access_class: CalibrationAccessClass
    disposition: CalibrationSourceDisposition
    independent_from_classifier_training: bool
    independent_from_external_validation: bool
    paired_measurements_reported: bool
    participant_level_molecular_values_available: bool
    stable_pair_identifiers_available: bool
    full_classifier_panel_confirmed: bool
    lawful_access_verified: bool
    candidate_for_threshold_calibration: bool
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_candidate_boundary(self) -> CalibrationSourceCandidate:
        requirements = (
            self.independent_from_classifier_training,
            self.independent_from_external_validation,
            self.paired_measurements_reported,
            self.participant_level_molecular_values_available,
            self.stable_pair_identifiers_available,
            self.full_classifier_panel_confirmed,
            self.lawful_access_verified,
        )
        if self.candidate_for_threshold_calibration and not all(requirements):
            raise ValueError(
                "a threshold-calibration candidate must satisfy every hard source requirement"
            )
        if (
            self.disposition
            is CalibrationSourceDisposition.RESERVED_EXTERNAL_VALIDATION
            and (
                self.independent_from_external_validation
                or self.candidate_for_threshold_calibration
            )
        ):
            raise ValueError(
                "an external-validation source cannot calibrate its own reliability rule"
            )
        if (
            self.access_class is CalibrationAccessClass.NOT_YET_CREATED
            and (
                self.participant_level_molecular_values_available
                or self.lawful_access_verified
            )
        ):
            raise ValueError("a future experiment cannot claim existing accessible data")
        return self


class CalibrationAcceptanceCriterion(TechnicalCalibrationModel):
    criterion_id: str = Field(pattern=r"^CAL-[0-9]{3}$")
    requirement: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    mandatory: bool = True
    resolution_status: str = Field(pattern=r"^(unresolved|satisfied)$")


class TechnicalCalibrationAcquisitionPlan(TechnicalCalibrationModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    method_dependency_audit_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    purpose: str = Field(min_length=1)
    prohibited_uses: list[str] = Field(min_length=1)
    acceptance_criteria: list[CalibrationAcceptanceCriterion] = Field(min_length=1)
    source_candidates: list[CalibrationSourceCandidate] = Field(min_length=1)
    selected_source_id: str | None
    founder_route_selected: bool
    power_analysis_required_before_minimum_pair_count: bool
    next_actions: list[str] = Field(min_length=1)
    patient_level_data_accessed: bool
    molecular_values_accessed: bool
    outcome_data_accessed: bool
    threshold_selection_authorized: bool
    method_execution_authorized: bool
    clinical_use_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def validate_plan_boundary(self) -> TechnicalCalibrationAcquisitionPlan:
        source_ids = [source.source_id for source in self.source_candidates]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("calibration source IDs must be unique")
        criterion_ids = [
            criterion.criterion_id for criterion in self.acceptance_criteria
        ]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("calibration criterion IDs must be unique")
        eligible_ids = {
            source.source_id
            for source in self.source_candidates
            if source.candidate_for_threshold_calibration
        }
        if self.selected_source_id is not None:
            if self.selected_source_id not in eligible_ids:
                raise ValueError("selected calibration source is not fully eligible")
            if not self.founder_route_selected:
                raise ValueError(
                    "a calibration source cannot be selected before the founder route"
                )
        if self.founder_route_selected and self.selected_source_id is None:
            raise ValueError(
                "a selected founder route requires an eligible calibration source"
            )
        if not self.power_analysis_required_before_minimum_pair_count:
            raise ValueError(
                "minimum replicate-pair count must be justified by a power analysis"
            )
        if any(
            (
                self.patient_level_data_accessed,
                self.molecular_values_accessed,
                self.outcome_data_accessed,
                self.threshold_selection_authorized,
                self.method_execution_authorized,
                self.clinical_use_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError(
                "an acquisition plan cannot access data or authorize analysis"
            )
        return self


def load_technical_calibration_plan(
    path: Path,
) -> TechnicalCalibrationAcquisitionPlan:
    return TechnicalCalibrationAcquisitionPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_technical_calibration_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            TechnicalCalibrationAcquisitionPlan.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
