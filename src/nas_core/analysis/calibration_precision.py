"""Deterministic expected-precision planning for technical replicate studies."""

from __future__ import annotations

import math
from statistics import NormalDist

from nas_core.domain.calibration_precision import (
    TechnicalReplicatePrecisionDesign,
    TechnicalReplicatePrecisionResult,
)


class CalibrationPrecisionError(RuntimeError):
    """Raised when a requested precision target cannot be met."""


class TechnicalReplicatePrecisionService:
    @staticmethod
    def _wilson_half_width(
        probability: float,
        effective_pairs: float,
        normal_quantile: float,
    ) -> float:
        squared = normal_quantile**2
        denominator = 1.0 + squared / effective_pairs
        variance = (
            probability * (1.0 - probability) / effective_pairs
            + squared / (4.0 * effective_pairs**2)
        )
        return normal_quantile * math.sqrt(variance) / denominator

    def calculate(
        self,
        design: TechnicalReplicatePrecisionDesign,
    ) -> TechnicalReplicatePrecisionResult:
        normal_quantile = NormalDist().inv_cdf(
            0.5 + design.confidence_level / 2.0
        )
        for required_observations in range(
            design.minimum_pair_observations,
            design.maximum_pair_observations + 1,
        ):
            achieved_effective_pairs = (
                required_observations / design.cluster_design_effect
            )
            half_width = self._wilson_half_width(
                design.expected_retention_probability,
                achieved_effective_pairs,
                normal_quantile,
            )
            if half_width <= design.target_interval_half_width:
                return TechnicalReplicatePrecisionResult(
                    scenario_id=design.scenario_id,
                    estimand=design.estimand,
                    method="wilson_expected_interval_precision",
                    expected_retention_probability=(
                        design.expected_retention_probability
                    ),
                    confidence_level=design.confidence_level,
                    target_interval_half_width=design.target_interval_half_width,
                    normal_quantile=normal_quantile,
                    cluster_design_effect=design.cluster_design_effect,
                    required_effective_pair_equivalents=achieved_effective_pairs,
                    required_pair_observations=required_observations,
                    achieved_expected_half_width=half_width,
                    planning_only=True,
                    scientific_parameters_approved=False,
                    source_selected=False,
                    data_accessed=False,
                    execution_authorized=False,
                    interpretation_limits=[
                        "This is expected Wilson-interval precision, not power for "
                        "a treatment, survival, or clinical-utility hypothesis.",
                        "It addresses binary label retention only; it does not establish "
                        "margin, perturbation, calibration, or abstention sufficiency.",
                        "The expected probability, confidence level, precision target, "
                        "and clustering assumption require scientific and statistical review.",
                    ],
                )
        raise CalibrationPrecisionError(
            "precision target is not achievable within the declared search range"
        )
