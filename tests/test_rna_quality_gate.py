from __future__ import annotations

import json
from pathlib import Path

import pytest

from nas_core.analysis.rna_quality_gate import (
    ProspectiveRNAQualityGateError,
    ProspectiveRNAQualityGateService,
)
from nas_core.domain.rna_quality_gate import (
    ProspectiveRNAQualityGatePlan,
    ProspectiveRNAQualityGateReceipt,
    load_prospective_rna_quality_gate_plan,
)

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "protocol/prospective_rna_quality_gate_plan_v1.0.0.yaml"
ASSAY = STUDY / "protocol/prospective_assay_selection_receipt_v1.0.0.yaml"
DESIGN = STUDY / "protocol/prospective_calibration_experiment_design_v0.1.0.yaml"
SCORING = STUDY / "protocol/uncalibrated_scoring_receipt_v1.0.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/prospective_rna_quality_gate_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/prospective_rna_quality_gate_receipt.schema.json"


def _freeze(plan: ProspectiveRNAQualityGatePlan) -> ProspectiveRNAQualityGateReceipt:
    return ProspectiveRNAQualityGateService().freeze(
        plan,
        plan_path=PLAN,
        assay_selection_receipt_path=ASSAY,
        prospective_design_path=DESIGN,
        uncalibrated_scoring_receipt_path=SCORING,
        code_revision="bc456d7",
    )


def test_high_quality_post_extraction_gate_is_frozen_without_execution() -> None:
    plan = load_prospective_rna_quality_gate_plan(PLAN)
    receipt = _freeze(plan)
    assert plan.rin_minimum == 8.0
    assert plan.selected_chemistry_family == "stranded_polya_mrna_whole_transcriptome"
    assert receipt.degraded_rna_separate is True
    assert receipt.study_execution_authorized is False


def test_degraded_rna_cannot_enter_primary_scope_silently() -> None:
    plan = load_prospective_rna_quality_gate_plan(PLAN)
    with pytest.raises(ValueError, match="cannot expand scope"):
        ProspectiveRNAQualityGatePlan.model_validate(
            {**plan.model_dump(), "degraded_or_ffpe_in_primary_scope": True}
        )


def test_rna_safeguards_cannot_be_weakened() -> None:
    plan = load_prospective_rna_quality_gate_plan(PLAN)
    with pytest.raises(ValueError, match="cannot be weakened"):
        ProspectiveRNAQualityGatePlan.model_validate(
            {**plan.model_dump(), "require_fragment_analysis": False}
        )


def test_changed_assay_selection_fails_closed(tmp_path: Path) -> None:
    plan = load_prospective_rna_quality_gate_plan(PLAN)
    changed = tmp_path / "changed.yaml"
    changed.write_text("changed: true\n", encoding="utf-8")
    with pytest.raises(ProspectiveRNAQualityGateError, match="dependency changed"):
        ProspectiveRNAQualityGateService().freeze(
            plan,
            plan_path=PLAN,
            assay_selection_receipt_path=changed,
            prospective_design_path=DESIGN,
            uncalibrated_scoring_receipt_path=SCORING,
            code_revision="bc456d7",
        )


def test_rna_quality_gate_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text()) == (
        ProspectiveRNAQualityGatePlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        ProspectiveRNAQualityGateReceipt.model_json_schema()
    )
