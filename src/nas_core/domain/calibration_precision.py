"""Nondecisional precision-planning contracts for technical replicate studies."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationPrecisionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TechnicalReplicatePrecisionDesign(CalibrationPrecisionModel):
    schema_version: str = "1.0.0"
    design_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    scenario_id: str = Field(pattern=r"^SYNTHETIC-CAL-[A-Z0-9-]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    estimand: str = Field(pattern=r"^technical_label_retention_probability$")
    expected_retention_probability: float = Field(gt=0.0, lt=1.0)
    confidence_level: float = Field(gt=0.5, lt=1.0)
    target_interval_half_width: float = Field(gt=0.0, lt=0.5)
    cluster_design_effect: float = Field(ge=1.0, le=20.0)
    minimum_pair_observations: int = Field(ge=2)
    maximum_pair_observations: int = Field(ge=2, le=1_000_000)
    assumptions: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    parameters_are_hypothetical: bool
    source_selected: bool
    patient_level_data_accessed: bool
    molecular_values_accessed: bool
    outcome_data_accessed: bool
    threshold_selection_authorized: bool
    study_execution_authorized: bool

    @model_validator(mode="after")
    def validate_nondecisional_boundary(
        self,
    ) -> TechnicalReplicatePrecisionDesign:
        if self.minimum_pair_observations > self.maximum_pair_observations:
            raise ValueError("minimum pair observations exceed the search maximum")
        if not self.parameters_are_hypothetical:
            raise ValueError(
                "route-neutral precision scenarios must remain explicitly hypothetical"
            )
        if any(
            (
                self.source_selected,
                self.patient_level_data_accessed,
                self.molecular_values_accessed,
                self.outcome_data_accessed,
                self.threshold_selection_authorized,
                self.study_execution_authorized,
            )
        ):
            raise ValueError(
                "a hypothetical precision design cannot select a source, access data, "
                "or authorize thresholds or execution"
            )
        return self


class TechnicalReplicatePrecisionResult(CalibrationPrecisionModel):
    schema_version: str = "1.0.0"
    scenario_id: str = Field(pattern=r"^SYNTHETIC-CAL-[A-Z0-9-]+$")
    estimand: str = Field(pattern=r"^technical_label_retention_probability$")
    method: str = Field(pattern=r"^wilson_expected_interval_precision$")
    expected_retention_probability: float = Field(gt=0.0, lt=1.0)
    confidence_level: float = Field(gt=0.5, lt=1.0)
    target_interval_half_width: float = Field(gt=0.0, lt=0.5)
    normal_quantile: float = Field(gt=0.0)
    cluster_design_effect: float = Field(ge=1.0, le=20.0)
    required_effective_pair_equivalents: float = Field(gt=0.0)
    required_pair_observations: int = Field(ge=2)
    achieved_expected_half_width: float = Field(gt=0.0, lt=0.5)
    planning_only: bool
    scientific_parameters_approved: bool
    source_selected: bool
    data_accessed: bool
    execution_authorized: bool
    interpretation_limits: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_result_boundary(self) -> TechnicalReplicatePrecisionResult:
        if self.required_pair_observations < self.required_effective_pair_equivalents:
            raise ValueError("design-effect inflation cannot reduce pair observations")
        if (
            not self.planning_only
            or self.scientific_parameters_approved
            or self.source_selected
            or self.data_accessed
            or self.execution_authorized
        ):
            raise ValueError(
                "a precision result must remain nondecisional and nonexecuting"
            )
        return self


def load_technical_replicate_precision_design(
    path: Path,
) -> TechnicalReplicatePrecisionDesign:
    return TechnicalReplicatePrecisionDesign.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_precision_schemas(
    design_path: Path,
    result_path: Path,
) -> None:
    for path, model in (
        (design_path, TechnicalReplicatePrecisionDesign),
        (result_path, TechnicalReplicatePrecisionResult),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
