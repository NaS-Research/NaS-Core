"""Contracts for pilot-informed, fail-closed pair-count reestimation."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationReestimationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalibrationPairCountReestimationPlan(CalibrationReestimationModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    pilot_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prospective_design_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    planning_bundle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hypothetical_balanced_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hypothetical_attempted_pair_reference: int = Field(ge=2)
    required_primary_inputs: list[str] = Field(min_length=1)
    permitted_pilot_inputs: list[str] = Field(min_length=1)
    require_target_assay_match: bool
    require_primary_estimand_match: bool
    allow_proxy_substitution: bool
    allow_source_pooling: bool
    allow_threshold_selection: bool
    allow_classifier_execution: bool
    allow_outcome_access: bool
    execution_authorized: bool

    @model_validator(mode="after")
    def enforce_blinded_boundary(self) -> CalibrationPairCountReestimationPlan:
        if not self.require_target_assay_match or not self.require_primary_estimand_match:
            raise ValueError("reestimation must require assay and estimand compatibility")
        if any(
            (
                self.allow_proxy_substitution,
                self.allow_source_pooling,
                self.allow_threshold_selection,
                self.allow_classifier_execution,
                self.allow_outcome_access,
                self.execution_authorized,
            )
        ):
            raise ValueError("blinded reestimation cannot substitute, pool, tune, or execute")
        return self


class CalibrationPairCountReestimationReceipt(CalibrationReestimationModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pilot_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    independent_group_count: int = Field(gt=0)
    within_group_pair_count: int = Field(gt=0)
    estimable_pilot_parameters: list[str] = Field(min_length=1)
    nonestimable_primary_parameters: list[str] = Field(min_length=1)
    compatibility_failures: list[str] = Field(min_length=1)
    hypothetical_attempted_pair_reference: int = Field(ge=2)
    final_attempted_pair_count: int | None
    status: str = Field(
        pattern=r"^not_estimable_from_excluded_public_pilots$"
    )
    primary_calibration_ready: bool
    proxy_substituted: bool
    sources_pooled: bool
    thresholds_selected: bool
    classifier_executed: bool
    outcomes_accessed: bool
    execution_authorized: bool
    interpretation: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_fail_closed_result(self) -> CalibrationPairCountReestimationReceipt:
        if self.final_attempted_pair_count is not None or self.primary_calibration_ready:
            raise ValueError("incompatible pilots cannot produce a final pair count")
        if any(
            (
                self.proxy_substituted,
                self.sources_pooled,
                self.thresholds_selected,
                self.classifier_executed,
                self.outcomes_accessed,
                self.execution_authorized,
            )
        ):
            raise ValueError("fail-closed reestimation crossed a prohibited boundary")
        return self


def load_calibration_pair_count_reestimation_plan(
    path: Path,
) -> CalibrationPairCountReestimationPlan:
    return CalibrationPairCountReestimationPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_pair_count_reestimation_receipt(
    path: Path,
    receipt: CalibrationPairCountReestimationReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("pair-count reestimation receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_calibration_pair_count_reestimation_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, CalibrationPairCountReestimationPlan),
        (receipt_path, CalibrationPairCountReestimationReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
