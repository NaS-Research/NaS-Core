from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.analysis.calibration_precision import (
    CalibrationPrecisionError,
    TechnicalReplicatePrecisionService,
)
from nas_core.domain.calibration_precision import (
    TechnicalReplicatePrecisionDesign,
    TechnicalReplicatePrecisionResult,
    load_technical_replicate_precision_design,
)

ROOT = Path(__file__).parents[1]
SCENARIO = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "protocol"
    / "technical_calibration_precision_scenario_HYPOTHETICAL.yaml"
)
DESIGN_SCHEMA = ROOT / "workflows" / "calibration_precision_design.schema.json"
RESULT_SCHEMA = ROOT / "workflows" / "calibration_precision_result.schema.json"


def test_hypothetical_precision_scenario_is_deterministic_and_nondecisional() -> None:
    design = load_technical_replicate_precision_design(SCENARIO)

    result = TechnicalReplicatePrecisionService().calculate(design)

    assert result.required_pair_observations > 2
    assert result.required_effective_pair_equivalents == pytest.approx(
        result.required_pair_observations
    )
    assert (
        result.achieved_expected_half_width
        <= design.target_interval_half_width
    )
    previous_half_width = TechnicalReplicatePrecisionService._wilson_half_width(
        design.expected_retention_probability,
        result.required_pair_observations - 1,
        result.normal_quantile,
    )
    assert previous_half_width > design.target_interval_half_width
    assert result.planning_only is True
    assert result.scientific_parameters_approved is False
    assert result.source_selected is False
    assert result.data_accessed is False
    assert result.execution_authorized is False


def test_cluster_design_effect_inflates_observed_pair_requirement() -> None:
    design = load_technical_replicate_precision_design(SCENARIO)
    baseline = TechnicalReplicatePrecisionService().calculate(design)
    clustered = TechnicalReplicatePrecisionService().calculate(
        design.model_copy(update={"cluster_design_effect": 2.0})
    )

    assert clustered.required_pair_observations == (
        baseline.required_pair_observations * 2
    )
    assert clustered.required_effective_pair_equivalents == pytest.approx(
        baseline.required_effective_pair_equivalents
    )


def test_precision_design_rejects_nonhypothetical_or_authorized_state() -> None:
    design = load_technical_replicate_precision_design(SCENARIO)
    payload = design.model_dump(mode="json")
    payload["parameters_are_hypothetical"] = False
    payload["study_execution_authorized"] = True

    with pytest.raises(ValidationError, match="hypothetical"):
        TechnicalReplicatePrecisionDesign.model_validate(payload)


def test_unreachable_precision_target_fails_closed() -> None:
    design = load_technical_replicate_precision_design(SCENARIO).model_copy(
        update={
            "target_interval_half_width": 0.001,
            "maximum_pair_observations": 10,
        }
    )

    with pytest.raises(CalibrationPrecisionError, match="not achievable"):
        TechnicalReplicatePrecisionService().calculate(design)


def test_checked_in_precision_schemas_match_runtime_models() -> None:
    assert json.loads(DESIGN_SCHEMA.read_text(encoding="utf-8")) == (
        TechnicalReplicatePrecisionDesign.model_json_schema()
    )
    assert json.loads(RESULT_SCHEMA.read_text(encoding="utf-8")) == (
        TechnicalReplicatePrecisionResult.model_json_schema()
    )
