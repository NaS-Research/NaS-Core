from __future__ import annotations

import json
from pathlib import Path

import pytest

from nas_core.analysis.prospective_assay_selection import (
    ProspectiveAssaySelectionError,
    ProspectiveAssaySelectionService,
)
from nas_core.domain.prospective_assay_selection import (
    ProspectiveAssaySelectionPlan,
    ProspectiveAssaySelectionReceipt,
    load_prospective_assay_selection_plan,
)

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "protocol/prospective_assay_selection_plan_v1.0.0.yaml"
DESIGN = STUDY / "protocol/prospective_calibration_experiment_design_v0.1.0.yaml"
BUNDLE = STUDY / "protocol/phase_one_internal_planning_bundle_v1.0.0.yaml"
ACTIVATION = STUDY / "protocol/prospective_calibration_planning_activation_v1.0.0.yaml"
BRIDGE = STUDY / "protocol/retrospective_expression_bridge_receipt_v1.0.0.yaml"
SCORING = STUDY / "protocol/uncalibrated_scoring_receipt_v1.0.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/prospective_assay_selection_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/prospective_assay_selection_receipt.schema.json"


def _freeze(plan: ProspectiveAssaySelectionPlan) -> ProspectiveAssaySelectionReceipt:
    return ProspectiveAssaySelectionService().freeze(
        plan,
        plan_path=PLAN,
        prospective_design_path=DESIGN,
        planning_bundle_path=BUNDLE,
        planning_activation_path=ACTIVATION,
        retrospective_bridge_receipt_path=BRIDGE,
        uncalibrated_scoring_receipt_path=SCORING,
        code_revision="1d192e8",
    )


def test_selected_family_is_whole_transcriptome_rna_seq_planning_only() -> None:
    plan = load_prospective_assay_selection_plan(PLAN)
    receipt = _freeze(plan)
    assert receipt.selected_candidate_id == "ASSAY-001"
    assert receipt.selection_scope == "planning_only_platform_family"
    assert receipt.exact_chemistry_unresolved is True
    assert receipt.study_execution_authorized is False
    assert receipt.molecular_values_accessed is False


def test_plan_rejects_procurement_or_execution_authority() -> None:
    plan = load_prospective_assay_selection_plan(PLAN)
    with pytest.raises(ValueError, match="cannot authorize procurement"):
        ProspectiveAssaySelectionPlan.model_validate(
            {**plan.model_dump(), "spending_authorized": True}
        )


def test_plan_requires_exactly_one_selected_family() -> None:
    plan = load_prospective_assay_selection_plan(PLAN)
    payload = plan.model_dump(mode="json")
    payload["candidates"][1]["disposition"] = "selected_family"
    with pytest.raises(ValueError, match="exactly one assay family"):
        ProspectiveAssaySelectionPlan.model_validate(payload)


def test_changed_dependency_fails_closed(tmp_path: Path) -> None:
    plan = load_prospective_assay_selection_plan(PLAN)
    changed = tmp_path / "changed.yaml"
    changed.write_text("changed: true\n", encoding="utf-8")
    with pytest.raises(ProspectiveAssaySelectionError, match="dependency changed"):
        ProspectiveAssaySelectionService().freeze(
            plan,
            plan_path=PLAN,
            prospective_design_path=changed,
            planning_bundle_path=BUNDLE,
            planning_activation_path=ACTIVATION,
            retrospective_bridge_receipt_path=BRIDGE,
            uncalibrated_scoring_receipt_path=SCORING,
            code_revision="1d192e8",
        )


def test_assay_selection_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text()) == (
        ProspectiveAssaySelectionPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        ProspectiveAssaySelectionReceipt.model_json_schema()
    )
