from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.analysis.numerical_conformance import NumericalConformanceService
from nas_core.domain.method_dependency import load_pam50_centroid_candidate
from nas_core.domain.numerical_conformance import (
    NumericalConformancePlan,
    NumericalConformanceReceipt,
    load_numerical_conformance_plan,
)
from nas_core.domain.reliability import load_reliability_specification

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
PLAN = STUDY / "protocol" / "numerical_conformance_plan_v1.0.0.yaml"
CANDIDATE = (
    STUDY
    / "protocol"
    / "artifact-candidates"
    / "genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
)
SPECIFICATION = STUDY / "protocol" / "reliability_specification.yaml"
PLAN_SCHEMA = ROOT / "workflows" / "numerical_conformance_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows" / "numerical_conformance_receipt.schema.json"


def _execute() -> NumericalConformanceReceipt:
    return NumericalConformanceService().execute(
        load_numerical_conformance_plan(PLAN),
        load_pam50_centroid_candidate(CANDIDATE),
        load_reliability_specification(SPECIFICATION),
        plan_path=PLAN,
        candidate_path=CANDIDATE,
        reliability_specification_path=SPECIFICATION,
        code_revision="42c91df",
        executed_at=datetime(2026, 7, 29, 20, 45, tzinfo=UTC),
    )


def test_independent_reference_conforms_on_frozen_suite() -> None:
    receipt = _execute()

    assert receipt.passed_count == 8
    assert receipt.failed_count == 0
    assert receipt.overall_passed is True
    assert receipt.reference_implementation == "pure_python_no_numpy_no_scipy"
    assert max(
        difference
        for case in receipt.cases
        for difference in (
            case.top_score_absolute_difference,
            case.runner_up_score_absolute_difference,
            case.margin_absolute_difference,
        )
        if difference is not None
    ) <= 1e-12
    assert receipt.cases[-2].production_reason == "top_score_tie"
    assert receipt.cases[-1].production_reason == "runner_up_score_tie"
    assert receipt.synthetic_only is True
    assert receipt.molecular_values_accessed is False
    assert receipt.outcomes_accessed is False
    assert receipt.analytical_validity_claimed is False
    assert receipt.method_lock_authorized is False


def test_conformance_plan_rejects_expanded_scope() -> None:
    plan = load_numerical_conformance_plan(PLAN)
    payload = plan.model_dump(mode="json")
    payload["molecular_values_accessed"] = True
    payload["method_lock_authorized"] = True

    with pytest.raises(ValidationError, match="synthetic and nonlocking"):
        NumericalConformancePlan.model_validate(payload)


def test_conformance_receipt_rejects_false_pass_count() -> None:
    receipt = _execute()
    payload = receipt.model_dump(mode="json")
    payload["passed_count"] = 7
    payload["failed_count"] = 1

    with pytest.raises(ValidationError, match="counts do not reconcile"):
        NumericalConformanceReceipt.model_validate(payload)


def test_numerical_conformance_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")) == (
        NumericalConformancePlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8")) == (
        NumericalConformanceReceipt.model_json_schema()
    )
