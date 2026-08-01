"""Machine-verifiable readiness decision for technical calibration paths."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationReadinessModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalibrationReadinessDecision(StrEnum):
    FEASIBILITY_ONLY = "public_feasibility_only_primary_calibration_not_ready"


class CalibrationPathDisposition(StrEnum):
    FEASIBILITY_AUTHORIZED = "public_feasibility_authorized"
    RESERVED_VALIDATION = "reserved_external_validation"
    CONTROLLED_UNAVAILABLE = "controlled_unavailable_contact_prohibited"
    PROSPECTIVE_STOP = "prospective_experiment_requires_stop_condition_review"


class CalibrationPathAssessment(CalibrationReadinessModel):
    source_id: str = Field(pattern=r"^(GEO:GSE[0-9]+|PMC:PMC[0-9]+|NAS:PROSPECTIVE)$")
    disposition: CalibrationPathDisposition
    public_open: bool
    expected_replicate_record_count: int | None = Field(default=None, ge=0)
    feasibility_molecular_acquisition_authorized: bool
    threshold_calibration_authorized: bool
    primary_calibration_eligible: bool
    external_contact_required: bool
    spending_or_specimens_required: bool
    reasons: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_disposition(self) -> CalibrationPathAssessment:
        if self.feasibility_molecular_acquisition_authorized and (
            not self.public_open
            or self.threshold_calibration_authorized
            or self.primary_calibration_eligible
        ):
            raise ValueError("public feasibility access cannot imply calibration eligibility")
        if self.threshold_calibration_authorized or self.primary_calibration_eligible:
            raise ValueError("no current path is eligible for primary threshold calibration")
        if self.disposition is CalibrationPathDisposition.RESERVED_VALIDATION and (
            self.feasibility_molecular_acquisition_authorized
        ):
            raise ValueError("GSE96058 must remain inaccessible during calibration")
        return self


class TechnicalCalibrationReadinessReceipt(CalibrationReadinessModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    assessed_at: datetime
    standing_authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    acquisition_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_scout_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    lineage_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prospective_design_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    internal_planning_bundle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contact_revocation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_construction_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_sensitivity_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: CalibrationReadinessDecision
    path_assessments: list[CalibrationPathAssessment] = Field(min_length=5, max_length=5)
    public_feasibility_source_ids: list[str] = Field(min_length=2, max_length=2)
    primary_calibration_source_id: str | None
    primary_calibration_ready: bool
    reference_dependency_ready: bool
    exact_alternative_reference_sensitivity_estimable: bool
    feasibility_acquisition_next: bool
    feasibility_analysis_permitted_estimands: list[str] = Field(min_length=1)
    prohibited_uses: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)
    final_human_review_preserved: bool
    external_contact_authorized: bool
    spending_authorized: bool
    controlled_data_authorized: bool
    specimen_acquisition_authorized: bool
    gse96058_molecular_access_authorized: bool
    outcome_access_authorized: bool
    threshold_selection_authorized: bool
    classifier_execution_authorized: bool
    clinical_use_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def enforce_readiness_boundary(self) -> TechnicalCalibrationReadinessReceipt:
        source_ids = [item.source_id for item in self.path_assessments]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("calibration readiness paths must be unique")
        if set(self.public_feasibility_source_ids) != {"GEO:GSE60788", "GEO:GSE130397"}:
            raise ValueError("only the two reviewed public sources may enter feasibility")
        authorized = {
            item.source_id
            for item in self.path_assessments
            if item.feasibility_molecular_acquisition_authorized
        }
        if authorized != set(self.public_feasibility_source_ids):
            raise ValueError("feasibility authorization does not reconcile")
        if self.primary_calibration_source_id is not None or self.primary_calibration_ready:
            raise ValueError("no primary calibration source is ready")
        if not all(
            (
                self.reference_dependency_ready,
                self.feasibility_acquisition_next,
                self.final_human_review_preserved,
            )
        ):
            raise ValueError("readiness receipt must preserve completed and next gates")
        if any(
            (
                self.external_contact_authorized,
                self.spending_authorized,
                self.controlled_data_authorized,
                self.specimen_acquisition_authorized,
                self.gse96058_molecular_access_authorized,
                self.outcome_access_authorized,
                self.threshold_selection_authorized,
                self.classifier_execution_authorized,
                self.clinical_use_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError("readiness receipt crossed a standing stop condition")
        return self


def load_calibration_readiness_receipt(
    path: Path,
) -> TechnicalCalibrationReadinessReceipt:
    return TechnicalCalibrationReadinessReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_readiness_receipt(
    path: Path,
    receipt: TechnicalCalibrationReadinessReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("calibration readiness receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_calibration_readiness_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            TechnicalCalibrationReadinessReceipt.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
