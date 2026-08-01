from __future__ import annotations

import json
from pathlib import Path

import pytest

from nas_core.analysis.prospective_pilot import (
    ExcludedProspectivePilotPlanError,
    ExcludedProspectivePilotPlanService,
)
from nas_core.domain.prospective_pilot import (
    ExcludedProspectivePilotPlan,
    ExcludedProspectivePilotPlanReceipt,
    load_excluded_prospective_pilot_plan,
)

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "protocol/excluded_prospective_pilot_plan_v1.0.0.yaml"
RNA_GATE = STUDY / "protocol/prospective_rna_quality_gate_receipt_v1.0.0.yaml"
BUNDLE = STUDY / "protocol/phase_one_internal_planning_bundle_v1.0.0.yaml"
DESIGN = STUDY / "protocol/prospective_calibration_experiment_design_v0.1.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/excluded_prospective_pilot_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/excluded_prospective_pilot_receipt.schema.json"


def _freeze(plan: ExcludedProspectivePilotPlan) -> ExcludedProspectivePilotPlanReceipt:
    return ExcludedProspectivePilotPlanService().freeze(
        plan,
        plan_path=PLAN,
        rna_quality_gate_receipt_path=RNA_GATE,
        planning_bundle_path=BUNDLE,
        prospective_design_path=DESIGN,
        code_revision="41412e7",
    )


def test_excluded_pilot_freezes_30_pairs_and_60_measurements() -> None:
    plan = load_excluded_prospective_pilot_plan(PLAN)
    receipt = _freeze(plan)
    assert receipt.attempted_pair_target == 30
    assert receipt.planned_measurement_count == 60
    assert receipt.independent_source_target == 30
    assert receipt.permanent_exclusion_frozen is True
    assert receipt.study_execution_authorized is False


def test_pilot_cannot_select_final_thresholds() -> None:
    plan = load_excluded_prospective_pilot_plan(PLAN)
    with pytest.raises(ValueError, match="cannot authorize"):
        ExcludedProspectivePilotPlan.model_validate(
            {**plan.model_dump(), "threshold_selection_authorized": True}
        )


def test_pilot_exclusion_cannot_be_weakened() -> None:
    plan = load_excluded_prospective_pilot_plan(PLAN)
    with pytest.raises(ValueError, match="safeguards are mandatory"):
        ExcludedProspectivePilotPlan.model_validate(
            {
                **plan.model_dump(),
                "pilot_specimens_permanently_excluded_from_primary": False,
            }
        )


def test_changed_rna_gate_fails_closed(tmp_path: Path) -> None:
    plan = load_excluded_prospective_pilot_plan(PLAN)
    changed = tmp_path / "changed.yaml"
    changed.write_text("changed: true\n", encoding="utf-8")
    with pytest.raises(ExcludedProspectivePilotPlanError, match="dependency changed"):
        ExcludedProspectivePilotPlanService().freeze(
            plan,
            plan_path=PLAN,
            rna_quality_gate_receipt_path=changed,
            planning_bundle_path=BUNDLE,
            prospective_design_path=DESIGN,
            code_revision="41412e7",
        )


def test_prospective_pilot_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text()) == (ExcludedProspectivePilotPlan.model_json_schema())
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        ExcludedProspectivePilotPlanReceipt.model_json_schema()
    )
