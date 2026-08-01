from __future__ import annotations

import json
from pathlib import Path

import pytest

from nas_core.analysis.pilot_source_landscape import (
    PilotSourceLandscapeError,
    PilotSourceLandscapeService,
)
from nas_core.domain.pilot_source_landscape import (
    PilotSourceLandscapePlan,
    PilotSourceLandscapeReceipt,
    load_pilot_source_landscape_plan,
)

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "protocol/pilot_source_landscape_plan_v1.0.0.yaml"
PILOT = STUDY / "protocol/excluded_prospective_pilot_receipt_v1.0.0.yaml"
RNA_GATE = STUDY / "protocol/prospective_rna_quality_gate_receipt_v1.0.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/pilot_source_landscape_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/pilot_source_landscape_receipt.schema.json"


def _freeze(plan: PilotSourceLandscapePlan) -> PilotSourceLandscapeReceipt:
    return PilotSourceLandscapeService().freeze(
        plan,
        plan_path=PLAN,
        pilot_receipt_path=PILOT,
        rna_quality_gate_receipt_path=RNA_GATE,
        code_revision="e0d3202",
    )


def test_landscape_has_no_verified_or_selected_source() -> None:
    receipt = _freeze(load_pilot_source_landscape_plan(PLAN))
    assert receipt.candidate_count == 6
    assert receipt.verified_eligible_count == 0
    assert receipt.unresolved_count == 5
    assert receipt.ineligible_count == 1
    assert receipt.selected_source_id is None
    assert receipt.external_action_authorized is False


def test_landscape_cannot_select_source_or_authorize_contact() -> None:
    plan = load_pilot_source_landscape_plan(PLAN)
    with pytest.raises(ValueError, match="cannot select"):
        PilotSourceLandscapePlan.model_validate(
            {**plan.model_dump(), "selected_source_id": "PILOTSRC-001"}
        )
    with pytest.raises(ValueError, match="cannot authorize"):
        PilotSourceLandscapePlan.model_validate(
            {**plan.model_dump(), "external_contact_authorized": True}
        )


def test_unproven_candidate_cannot_be_marked_eligible() -> None:
    plan = load_pilot_source_landscape_plan(PLAN)
    payload = plan.model_dump(mode="json")
    payload["candidates"][0]["disposition"] = "verified_eligible"
    with pytest.raises(ValueError, match="satisfy every"):
        PilotSourceLandscapePlan.model_validate(payload)


def test_changed_pilot_receipt_fails_closed(tmp_path: Path) -> None:
    plan = load_pilot_source_landscape_plan(PLAN)
    changed = tmp_path / "changed.yaml"
    changed.write_text("changed: true\n", encoding="utf-8")
    with pytest.raises(PilotSourceLandscapeError, match="pilot receipt changed"):
        PilotSourceLandscapeService().freeze(
            plan,
            plan_path=PLAN,
            pilot_receipt_path=changed,
            rna_quality_gate_receipt_path=RNA_GATE,
            code_revision="e0d3202",
        )


def test_source_landscape_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text()) == (PilotSourceLandscapePlan.model_json_schema())
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        PilotSourceLandscapeReceipt.model_json_schema()
    )
