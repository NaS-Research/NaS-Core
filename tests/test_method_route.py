from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.analysis.method_route import (
    MethodRouteActivationError,
    MethodRouteActivationService,
)
from nas_core.domain.method_dependency import (
    MethodRouteActivationReceipt,
    MethodRouteFounderDecision,
    load_method_dependency_audit,
    load_method_route_activation,
    load_method_route_founder_decision,
    load_pam50_centroid_candidate,
)
from nas_core.domain.technical_calibration import (
    load_technical_calibration_plan,
)

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
AUDIT = STUDY / "protocol" / "method_dependency_audit_proposal_v1.0.0.yaml"
PACKET = STUDY / "reviews" / "FOUNDER_METHOD_DEPENDENCY_DECISION_PACKET_v1.0.0.md"
DECISION = STUDY / "reviews" / "FOUNDER_METHOD_ROUTE_DECISION_v1.0.0.yaml"
CANDIDATE = (
    STUDY
    / "protocol"
    / "artifact-candidates"
    / "genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
)
CALIBRATION_PLAN = (
    STUDY
    / "protocol"
    / "technical_calibration_acquisition_plan_v1.0.0.yaml"
)
DECISION_SCHEMA = ROOT / "workflows" / "method_route_founder_decision.schema.json"
ACTIVATION_SCHEMA = ROOT / "workflows" / "method_route_activation.schema.json"
ACTIVATION = STUDY / "protocol" / "method_route_activation_v1.0.0.yaml"


def _activate(
    *,
    decision_path: Path = DECISION,
    packet_path: Path = PACKET,
) -> MethodRouteActivationReceipt:
    return MethodRouteActivationService().activate(
        load_method_route_founder_decision(decision_path),
        load_method_dependency_audit(AUDIT),
        load_pam50_centroid_candidate(CANDIDATE),
        load_technical_calibration_plan(CALIBRATION_PLAN),
        decision_path=decision_path,
        audit_path=AUDIT,
        decision_packet_path=packet_path,
        candidate_path=CANDIDATE,
        calibration_plan_path=CALIBRATION_PLAN,
        code_revision="74b3f2a",
        activated_at=datetime(2026, 7, 28, 20, 39, 8, tzinfo=UTC),
    )


def test_route_c_decision_activates_hold_without_data_authority() -> None:
    activation = _activate()

    assert activation.selected_route_id == "ROUTE-C"
    assert activation.activation_status.value == "independent_calibration_hold"
    assert activation.question_preserved is True
    assert activation.centroid_candidate_staged is True
    assert activation.calibration_acquisition_active is True
    assert activation.founder_route_selected is True
    assert activation.calibration_source_selected is False
    assert activation.method_locked is False
    assert activation.molecular_values_accessed is False
    assert activation.outcome_data_accessed is False
    assert activation.method_execution_authorized is False


def test_route_activation_rejects_changed_founder_packet(tmp_path: Path) -> None:
    changed = tmp_path / "packet.md"
    changed.write_bytes(PACKET.read_bytes() + b"\n")

    with pytest.raises(MethodRouteActivationError, match="different review packet"):
        _activate(packet_path=changed)


def test_route_activation_rejects_non_route_c_decision(tmp_path: Path) -> None:
    decision = load_method_route_founder_decision(DECISION)
    payload = decision.model_dump(mode="json")
    payload["selected_route_id"] = "ROUTE-A"
    payload["confirmation_statement"] = (
        "I approve NAS-BRCA-002 method dependency Route A as written."
    )
    changed = tmp_path / "decision.yaml"
    changed.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(MethodRouteActivationError, match="approved Route C"):
        _activate(decision_path=changed)


def test_checked_in_route_schemas_match_runtime_models() -> None:
    assert json.loads(DECISION_SCHEMA.read_text(encoding="utf-8")) == (
        MethodRouteFounderDecision.model_json_schema()
    )
    assert json.loads(ACTIVATION_SCHEMA.read_text(encoding="utf-8")) == (
        MethodRouteActivationReceipt.model_json_schema()
    )


def test_checked_in_route_c_activation_matches_frozen_implementation() -> None:
    activation = load_method_route_activation(ACTIVATION)
    regenerated = _activate()

    assert activation.model_copy(update={"activated_at": regenerated.activated_at}) == (
        regenerated
    )
    assert activation.code_revision == "74b3f2a"
    assert activation.founder_decision_sha256 == (
        "01ffbe13e464e3c3f9ce8b623be60ee5f6bb8f27511b107ed71cc14a8bd1b747"
    )
