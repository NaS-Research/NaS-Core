"""Deterministic hypothetical multi-objective calibration planning."""

from __future__ import annotations

import math
from pathlib import Path
from statistics import NormalDist

from nas_core.analysis.calibration_precision import TechnicalReplicatePrecisionService
from nas_core.domain.calibration_scenario import (
    MultiObjectiveCalibrationScenario,
    MultiObjectiveCalibrationScenarioResult,
)
from nas_core.domain.prospective_calibration import (
    CalibrationPlanningActivationStatus,
    ProspectiveCalibrationPlanningActivation,
)
from nas_core.ingestion.gdc import sha256


class CalibrationScenarioError(RuntimeError):
    """Raised when a hypothetical planning scenario cannot meet its objectives."""


class MultiObjectiveCalibrationScenarioService:
    @staticmethod
    def _binary_effective_pairs(
        scenario: MultiObjectiveCalibrationScenario,
    ) -> int:
        quantile = NormalDist().inv_cdf(
            0.5 + scenario.label_retention_confidence / 2.0
        )
        for pairs in range(2, scenario.maximum_attempted_pairs + 1):
            half_width = TechnicalReplicatePrecisionService._wilson_half_width(
                scenario.label_retention_probability,
                pairs,
                quantile,
            )
            if half_width <= scenario.label_retention_half_width:
                return pairs
        raise CalibrationScenarioError(
            "binary precision target exceeds the declared search range"
        )

    @staticmethod
    def _continuous_requirements(
        scenario: MultiObjectiveCalibrationScenario,
    ) -> tuple[int, float]:
        alpha = 1.0 - scenario.continuous_familywise_confidence
        quantile = NormalDist().inv_cdf(
            1.0 - alpha / (2.0 * scenario.continuous_multiplicity_count)
        )
        effective_pairs = max(
            2,
            math.ceil(
                (
                    quantile
                    * scenario.continuous_paired_sd
                    / scenario.continuous_mean_half_width
                )
                ** 2
            ),
        )
        return effective_pairs, quantile

    def calculate(
        self,
        scenario: MultiObjectiveCalibrationScenario,
        activation: ProspectiveCalibrationPlanningActivation,
        *,
        activation_path: Path,
    ) -> MultiObjectiveCalibrationScenarioResult:
        if scenario.study_id != activation.study_id:
            raise CalibrationScenarioError(
                "scenario and planning activation identify different studies"
            )
        if scenario.planning_activation_sha256 != sha256(
            activation_path.read_bytes()
        ):
            raise CalibrationScenarioError(
                "scenario is bound to a different planning activation"
            )
        if (
            activation.status
            is not CalibrationPlanningActivationStatus.INTERNAL_PLANNING_ACTIVE
            or not activation.internal_statistical_planning_authorized
            or activation.study_execution_authorized
        ):
            raise CalibrationScenarioError(
                "scenario requires active, nonexecuting statistical planning"
            )
        binary_pairs = self._binary_effective_pairs(scenario)
        continuous_pairs, continuous_quantile = self._continuous_requirements(
            scenario
        )
        governing_pairs = max(binary_pairs, continuous_pairs)
        governing_objective = (
            "label_retention"
            if binary_pairs >= continuous_pairs
            else "continuous_mean_precision"
        )
        attempted_pairs = max(
            scenario.minimum_attempted_pairs,
            math.ceil(
                governing_pairs
                * scenario.cluster_design_effect
                / (1.0 - scenario.expected_attrition_fraction)
            ),
        )
        if attempted_pairs > scenario.maximum_attempted_pairs:
            raise CalibrationScenarioError(
                "attrition- and clustering-inflated target exceeds the declared maximum"
            )
        achieved_effective_pairs = (
            attempted_pairs
            * (1.0 - scenario.expected_attrition_fraction)
            / scenario.cluster_design_effect
        )
        binary_quantile = NormalDist().inv_cdf(
            0.5 + scenario.label_retention_confidence / 2.0
        )
        achieved_binary_half_width = (
            TechnicalReplicatePrecisionService._wilson_half_width(
                scenario.label_retention_probability,
                achieved_effective_pairs,
                binary_quantile,
            )
        )
        achieved_continuous_half_width = (
            continuous_quantile
            * scenario.continuous_paired_sd
            / math.sqrt(achieved_effective_pairs)
        )
        return MultiObjectiveCalibrationScenarioResult(
            scenario_id=scenario.scenario_id,
            binary_effective_pairs_required=binary_pairs,
            continuous_effective_pairs_required=continuous_pairs,
            governing_objective=governing_objective,
            governing_effective_pairs=governing_pairs,
            cluster_design_effect=scenario.cluster_design_effect,
            expected_attrition_fraction=scenario.expected_attrition_fraction,
            attempted_pairs_required=attempted_pairs,
            attempted_measurements_required=2 * attempted_pairs,
            achieved_expected_effective_pairs=achieved_effective_pairs,
            achieved_binary_half_width=achieved_binary_half_width,
            continuous_normal_quantile=continuous_quantile,
            achieved_continuous_mean_half_width=(
                achieved_continuous_half_width
            ),
            planning_only=True,
            scientific_parameters_approved=False,
            source_selected=False,
            data_accessed=False,
            execution_authorized=False,
            interpretation_limits=[
                "Every probability, variance, precision, multiplicity, attrition, "
                "and clustering input is hypothetical.",
                "Attempted pairs are an operational scenario, not an approved sample size.",
                "The calculation does not establish subtype, margin-stratum, missingness, "
                "clinical-utility, or budget sufficiency.",
                "Pilot, founder, molecular, statistical, governance, and operational "
                "review remain required.",
            ],
        )
