"""Hypothetical multi-objective technical-calibration planning scenarios."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MultiObjectiveCalibrationScenario(CalibrationScenarioModel):
    schema_version: str = "1.0.0"
    scenario_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    scenario_id: str = Field(pattern=r"^HYPOTHETICAL-CAL-[A-Z0-9-]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    planning_activation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    label_retention_probability: float = Field(gt=0.0, lt=1.0)
    label_retention_confidence: float = Field(gt=0.5, lt=1.0)
    label_retention_half_width: float = Field(gt=0.0, lt=0.5)
    continuous_paired_sd: float = Field(gt=0.0)
    continuous_mean_half_width: float = Field(gt=0.0)
    continuous_familywise_confidence: float = Field(gt=0.5, lt=1.0)
    continuous_multiplicity_count: int = Field(ge=1, le=10_000)
    cluster_design_effect: float = Field(ge=1.0, le=20.0)
    expected_attrition_fraction: float = Field(ge=0.0, lt=0.95)
    minimum_attempted_pairs: int = Field(ge=2)
    maximum_attempted_pairs: int = Field(ge=2, le=1_000_000)
    assumptions: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    parameters_are_hypothetical: bool
    scientific_parameters_approved: bool
    source_selected: bool
    data_accessed: bool
    threshold_selection_authorized: bool
    study_execution_authorized: bool

    @model_validator(mode="after")
    def validate_scenario_boundary(self) -> MultiObjectiveCalibrationScenario:
        if self.minimum_attempted_pairs > self.maximum_attempted_pairs:
            raise ValueError("minimum attempted pairs exceed the declared maximum")
        if not self.parameters_are_hypothetical:
            raise ValueError("planning scenarios must remain explicitly hypothetical")
        if any(
            (
                self.scientific_parameters_approved,
                self.source_selected,
                self.data_accessed,
                self.threshold_selection_authorized,
                self.study_execution_authorized,
            )
        ):
            raise ValueError(
                "a hypothetical scenario cannot approve parameters, select a source, "
                "access data, select thresholds, or authorize execution"
            )
        return self


class MultiObjectiveCalibrationScenarioResult(CalibrationScenarioModel):
    schema_version: str = "1.0.0"
    scenario_id: str = Field(pattern=r"^HYPOTHETICAL-CAL-[A-Z0-9-]+$")
    scenario_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    planning_activation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    calculated_at: datetime
    binary_effective_pairs_required: int = Field(ge=2)
    continuous_effective_pairs_required: int = Field(ge=2)
    governing_objective: str = Field(
        pattern=r"^(label_retention|continuous_mean_precision)$"
    )
    governing_effective_pairs: int = Field(ge=2)
    cluster_design_effect: float = Field(ge=1.0, le=20.0)
    expected_attrition_fraction: float = Field(ge=0.0, lt=0.95)
    attempted_pairs_required: int = Field(ge=2)
    attempted_measurements_required: int = Field(ge=4)
    achieved_expected_effective_pairs: float = Field(gt=0.0)
    achieved_binary_half_width: float = Field(gt=0.0, lt=0.5)
    continuous_normal_quantile: float = Field(gt=0.0)
    achieved_continuous_mean_half_width: float = Field(gt=0.0)
    planning_only: bool
    scientific_parameters_approved: bool
    source_selected: bool
    data_accessed: bool
    execution_authorized: bool
    interpretation_limits: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_result_boundary(
        self,
    ) -> MultiObjectiveCalibrationScenarioResult:
        if self.attempted_measurements_required != 2 * self.attempted_pairs_required:
            raise ValueError("each attempted pair must contribute two measurements")
        if self.governing_effective_pairs != max(
            self.binary_effective_pairs_required,
            self.continuous_effective_pairs_required,
        ):
            raise ValueError("governing effective pairs do not match the objectives")
        if (
            not self.planning_only
            or self.scientific_parameters_approved
            or self.source_selected
            or self.data_accessed
            or self.execution_authorized
        ):
            raise ValueError("scenario results must remain planning-only")
        return self


def load_multi_objective_calibration_scenario(
    path: Path,
) -> MultiObjectiveCalibrationScenario:
    return MultiObjectiveCalibrationScenario.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_multi_objective_calibration_scenario_result(
    path: Path,
    result: MultiObjectiveCalibrationScenarioResult,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(result.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_calibration_scenario_schemas(
    scenario_path: Path,
    result_path: Path,
) -> None:
    for path, model in (
        (scenario_path, MultiObjectiveCalibrationScenario),
        (result_path, MultiObjectiveCalibrationScenarioResult),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
