from __future__ import annotations

import json
from pathlib import Path

import pytest

from nas_core.analysis.calibration_reestimation import (
    CalibrationPairCountReestimationError,
    CalibrationPairCountReestimationService,
)
from nas_core.domain.calibration_feasibility_pilot import (
    load_calibration_feasibility_pilot_receipt,
)
from nas_core.domain.calibration_reestimation import (
    CalibrationPairCountReestimationPlan,
    CalibrationPairCountReestimationReceipt,
    load_calibration_pair_count_reestimation_plan,
)
from nas_core.domain.prospective_calibration import (
    load_prospective_calibration_design,
)

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "analysis/calibration_pair_count_reestimation_plan_v1.0.0.yaml"
PILOT = STUDY / "analysis/calibration_feasibility_pilot_receipt_v1.0.0.yaml"
DESIGN = STUDY / "protocol/prospective_calibration_experiment_design_v0.1.0.yaml"
BUNDLE = STUDY / "protocol/phase_one_internal_planning_bundle_v1.0.0.yaml"
BALANCED = STUDY / "protocol/calibration-scenarios/HYPOTHETICAL_BALANCED_RESULT.yaml"
PLAN_SCHEMA = ROOT / "workflows/calibration_pair_count_reestimation_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/calibration_pair_count_reestimation_receipt.schema.json"


def _assess(plan: CalibrationPairCountReestimationPlan) -> CalibrationPairCountReestimationReceipt:
    return CalibrationPairCountReestimationService().assess(
        plan,
        load_calibration_feasibility_pilot_receipt(PILOT),
        load_prospective_calibration_design(DESIGN),
        plan_path=PLAN,
        pilot_receipt_path=PILOT,
        prospective_design_path=DESIGN,
        planning_bundle_path=BUNDLE,
        hypothetical_balanced_result_path=BALANCED,
        code_revision="fca7016",
    )


def test_checked_in_reestimation_fails_closed_without_proxy_substitution() -> None:
    receipt = _assess(load_calibration_pair_count_reestimation_plan(PLAN))
    assert receipt.independent_group_count == 13
    assert receipt.within_group_pair_count == 21
    assert receipt.final_attempted_pair_count is None
    assert receipt.status == "not_estimable_from_excluded_public_pilots"
    assert receipt.hypothetical_attempted_pair_reference == 185
    assert receipt.proxy_substituted is False
    assert receipt.sources_pooled is False
    assert receipt.classifier_executed is False
    assert receipt.outcomes_accessed is False


def test_reestimation_rejects_changed_pilot_lineage(tmp_path: Path) -> None:
    changed = tmp_path / "pilot.yaml"
    changed.write_text("changed: true\n", encoding="utf-8")
    plan = load_calibration_pair_count_reestimation_plan(PLAN)
    with pytest.raises(CalibrationPairCountReestimationError, match="provenance"):
        CalibrationPairCountReestimationService().assess(
            plan,
            load_calibration_feasibility_pilot_receipt(PILOT),
            load_prospective_calibration_design(DESIGN),
            plan_path=PLAN,
            pilot_receipt_path=changed,
            prospective_design_path=DESIGN,
            planning_bundle_path=BUNDLE,
            hypothetical_balanced_result_path=BALANCED,
            code_revision="fca7016",
        )


def test_reestimation_plan_rejects_proxy_substitution() -> None:
    plan = load_calibration_pair_count_reestimation_plan(PLAN)
    with pytest.raises(ValueError, match="cannot substitute"):
        CalibrationPairCountReestimationPlan.model_validate(
            {**plan.model_dump(), "allow_proxy_substitution": True}
        )


def test_reestimation_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text()) == (
        CalibrationPairCountReestimationPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        CalibrationPairCountReestimationReceipt.model_json_schema()
    )
