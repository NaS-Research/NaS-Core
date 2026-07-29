from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.analysis.calibration_scenario import (
    CalibrationScenarioError,
    MultiObjectiveCalibrationScenarioService,
)
from nas_core.domain.calibration_scenario import (
    MultiObjectiveCalibrationScenario,
    MultiObjectiveCalibrationScenarioResult,
    load_multi_objective_calibration_scenario,
    load_multi_objective_calibration_scenario_result,
)
from nas_core.domain.prospective_calibration import (
    load_prospective_calibration_planning_activation,
)

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
SCENARIOS = STUDY / "protocol" / "calibration-scenarios"
ACTIVATION = (
    STUDY
    / "protocol"
    / "prospective_calibration_planning_activation_v1.0.0.yaml"
)
SCENARIO_SCHEMA = (
    ROOT / "workflows" / "calibration_multiobjective_scenario.schema.json"
)
RESULT_SCHEMA = (
    ROOT / "workflows" / "calibration_multiobjective_scenario_result.schema.json"
)


def _calculate(name: str) -> MultiObjectiveCalibrationScenarioResult:
    scenario_path = SCENARIOS / name
    scenario = load_multi_objective_calibration_scenario(scenario_path)
    activation = load_prospective_calibration_planning_activation(ACTIVATION)
    return MultiObjectiveCalibrationScenarioService().calculate(
        scenario,
        activation,
        scenario_path=scenario_path,
        activation_path=ACTIVATION,
        code_revision="dfc9e56",
        calculated_at=datetime(2026, 7, 29, 18, 30, tzinfo=UTC),
    )


def test_three_scenarios_are_deterministic_and_increasing() -> None:
    lean = _calculate("HYPOTHETICAL_LEAN.yaml")
    balanced = _calculate("HYPOTHETICAL_BALANCED.yaml")
    high = _calculate("HYPOTHETICAL_HIGH_PRECISION.yaml")

    assert lean.attempted_pairs_required == 82
    assert balanced.attempted_pairs_required == 185
    assert high.attempted_pairs_required == 945
    assert lean.attempted_pairs_required < balanced.attempted_pairs_required
    assert balanced.attempted_pairs_required < high.attempted_pairs_required
    for result in (lean, balanced, high):
        assert result.attempted_measurements_required == (
            2 * result.attempted_pairs_required
        )
        assert result.planning_only is True
        assert result.scientific_parameters_approved is False
        assert result.source_selected is False
        assert result.data_accessed is False
        assert result.execution_authorized is False


def test_balanced_scenario_is_governed_by_continuous_precision() -> None:
    result = _calculate("HYPOTHETICAL_BALANCED.yaml")

    assert result.binary_effective_pairs_required == 141
    assert result.continuous_effective_pairs_required == 166
    assert result.governing_objective == "continuous_mean_precision"
    assert result.achieved_binary_half_width <= 0.05
    assert result.achieved_continuous_mean_half_width <= 0.05


def test_scenario_rejects_approved_or_executing_state() -> None:
    scenario = load_multi_objective_calibration_scenario(
        SCENARIOS / "HYPOTHETICAL_BALANCED.yaml"
    )
    payload = scenario.model_dump(mode="json")
    payload["scientific_parameters_approved"] = True
    payload["study_execution_authorized"] = True

    with pytest.raises(ValidationError, match="cannot approve parameters"):
        MultiObjectiveCalibrationScenario.model_validate(payload)


def test_scenario_rejects_changed_planning_activation(tmp_path: Path) -> None:
    changed = tmp_path / "activation.yaml"
    changed.write_bytes(ACTIVATION.read_bytes() + b"\n")
    scenario = load_multi_objective_calibration_scenario(
        SCENARIOS / "HYPOTHETICAL_BALANCED.yaml"
    )

    with pytest.raises(
        CalibrationScenarioError,
        match="different planning activation",
    ):
        MultiObjectiveCalibrationScenarioService().calculate(
            scenario,
            load_prospective_calibration_planning_activation(changed),
            scenario_path=SCENARIOS / "HYPOTHETICAL_BALANCED.yaml",
            activation_path=changed,
            code_revision="dfc9e56",
            calculated_at=datetime(2026, 7, 29, 18, 30, tzinfo=UTC),
        )


def test_unattainable_inflated_scenario_fails_closed() -> None:
    scenario = load_multi_objective_calibration_scenario(
        SCENARIOS / "HYPOTHETICAL_HIGH_PRECISION.yaml"
    ).model_copy(update={"maximum_attempted_pairs": 100})

    with pytest.raises(CalibrationScenarioError, match="search range"):
        MultiObjectiveCalibrationScenarioService().calculate(
            scenario,
            load_prospective_calibration_planning_activation(ACTIVATION),
            scenario_path=SCENARIOS / "HYPOTHETICAL_HIGH_PRECISION.yaml",
            activation_path=ACTIVATION,
            code_revision="dfc9e56",
            calculated_at=datetime(2026, 7, 29, 18, 30, tzinfo=UTC),
        )


def test_checked_in_calibration_scenario_schemas_match_runtime_models() -> None:
    assert json.loads(SCENARIO_SCHEMA.read_text(encoding="utf-8")) == (
        MultiObjectiveCalibrationScenario.model_json_schema()
    )
    assert json.loads(RESULT_SCHEMA.read_text(encoding="utf-8")) == (
        MultiObjectiveCalibrationScenarioResult.model_json_schema()
    )


@pytest.mark.parametrize(
    "scenario_name",
    [
        "HYPOTHETICAL_LEAN",
        "HYPOTHETICAL_BALANCED",
        "HYPOTHETICAL_HIGH_PRECISION",
    ],
)
def test_checked_in_scenario_results_match_frozen_implementation(
    scenario_name: str,
) -> None:
    scenario_path = SCENARIOS / f"{scenario_name}.yaml"
    result = load_multi_objective_calibration_scenario_result(
        SCENARIOS / f"{scenario_name}_RESULT.yaml"
    )
    regenerated = MultiObjectiveCalibrationScenarioService().calculate(
        load_multi_objective_calibration_scenario(scenario_path),
        load_prospective_calibration_planning_activation(ACTIVATION),
        scenario_path=scenario_path,
        activation_path=ACTIVATION,
        code_revision=result.code_revision,
        calculated_at=result.calculated_at,
    )

    assert result == regenerated
    assert result.code_revision == "2a51d0b"
