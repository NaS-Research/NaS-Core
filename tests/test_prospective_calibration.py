from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.analysis.prospective_calibration import (
    ProspectiveCalibrationDesignError,
    ProspectiveCalibrationDesignService,
)
from nas_core.domain.method_dependency import load_method_route_activation
from nas_core.domain.prospective_calibration import (
    ProspectiveCalibrationExperimentDesign,
    ProspectiveCalibrationFounderDecision,
    ProspectiveCalibrationPlanningActivation,
    load_calibration_contact_revocation,
    load_prospective_calibration_design,
    load_prospective_calibration_founder_decision,
    load_prospective_calibration_planning_activation,
)
from nas_core.domain.technical_calibration import load_technical_calibration_plan

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
DESIGN = STUDY / "protocol" / "prospective_calibration_experiment_design_v0.1.0.yaml"
ACTIVATION = STUDY / "protocol" / "method_route_activation_v1.0.0.yaml"
PLAN = STUDY / "protocol" / "technical_calibration_acquisition_plan_v1.0.0.yaml"
REVOCATION = (
    STUDY
    / "reviews"
    / "FOUNDER_CALIBRATION_INQUIRY_REVOCATION_v1.0.0.yaml"
)
SCHEMA = ROOT / "workflows" / "prospective_calibration_experiment_design.schema.json"
DECISION = (
    STUDY
    / "reviews"
    / "FOUNDER_PROSPECTIVE_CALIBRATION_DESIGN_DECISION_v0.1.0.yaml"
)
PACKET = (
    STUDY
    / "reviews"
    / "FOUNDER_PROSPECTIVE_CALIBRATION_DESIGN_DECISION_PACKET_v0.1.0.md"
)
DECISION_SCHEMA = (
    ROOT / "workflows" / "prospective_calibration_founder_decision.schema.json"
)
ACTIVATION_SCHEMA = (
    ROOT / "workflows" / "prospective_calibration_planning_activation.schema.json"
)
PLANNING_ACTIVATION = (
    STUDY
    / "protocol"
    / "prospective_calibration_planning_activation_v1.0.0.yaml"
)


def _validate(
    *,
    activation_path: Path = ACTIVATION,
) -> ProspectiveCalibrationExperimentDesign:
    return ProspectiveCalibrationDesignService().validate(
        load_prospective_calibration_design(DESIGN),
        load_method_route_activation(activation_path),
        load_technical_calibration_plan(PLAN),
        load_calibration_contact_revocation(REVOCATION),
        activation_path=activation_path,
        plan_path=PLAN,
        revocation_path=REVOCATION,
    )


def test_phase_one_design_is_bound_nonexecuting_and_no_contact() -> None:
    design = _validate()

    assert design.phase == "phase_1_method_calibration"
    assert design.route_id == "ROUTE-C"
    assert len(design.arms) == 3
    assert len(design.estimands) == 5
    assert sum(estimand.primary for estimand in design.estimands) == 1
    assert design.validation_source_ids == ["GEO:GSE96058"]
    assert design.threshold_calibration_source_ids == []
    assert design.external_contact_authorized is False
    assert design.spending_authorized is False
    assert design.source_selected is False
    assert design.molecular_values_accessed is False
    assert design.outcome_data_accessed is False
    assert design.study_execution_authorized is False


def test_design_rejects_contact_spending_or_execution_authority() -> None:
    design = load_prospective_calibration_design(DESIGN)
    payload = design.model_dump(mode="json")
    payload["external_contact_authorized"] = True
    payload["spending_authorized"] = True
    payload["study_execution_authorized"] = True

    with pytest.raises(ValidationError, match="cannot contact, spend"):
        ProspectiveCalibrationExperimentDesign.model_validate(payload)


def test_design_rejects_validation_leakage() -> None:
    design = load_prospective_calibration_design(DESIGN)
    payload = design.model_dump(mode="json")
    payload["threshold_calibration_source_ids"] = ["GEO:GSE96058"]

    with pytest.raises(ValidationError, match="cannot calibrate thresholds"):
        ProspectiveCalibrationExperimentDesign.model_validate(payload)


def test_design_rejects_locked_pair_count_before_founder_review() -> None:
    design = load_prospective_calibration_design(DESIGN)
    payload = design.model_dump(mode="json")
    payload["arms"][1]["pair_count"] = 141

    with pytest.raises(ValidationError, match="cannot silently lock"):
        ProspectiveCalibrationExperimentDesign.model_validate(payload)


def test_design_rejects_changed_route_activation(tmp_path: Path) -> None:
    changed = tmp_path / "activation.yaml"
    payload = yaml.safe_load(ACTIVATION.read_text(encoding="utf-8"))
    payload["activated_at"] = "2026-07-29T00:00:00Z"
    changed.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(
        ProspectiveCalibrationDesignError,
        match="different Route C activation",
    ):
        _validate(activation_path=changed)


def test_checked_in_prospective_calibration_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        ProspectiveCalibrationExperimentDesign.model_json_schema()
    )


def test_founder_decision_activates_internal_planning_only() -> None:
    decision = load_prospective_calibration_founder_decision(DECISION)
    design = load_prospective_calibration_design(DESIGN)

    activation = ProspectiveCalibrationDesignService().activate_planning(
        decision,
        design,
        decision_path=DECISION,
        design_path=DESIGN,
        decision_packet_path=PACKET,
        code_revision="5502f07",
        activated_at=datetime(2026, 7, 29, 18, 1, 3, tzinfo=UTC),
    )

    assert activation.status.value == "internal_planning_active"
    assert activation.unresolved_decision_ids == [
        "CAL-DEC-001",
        "CAL-DEC-002",
        "CAL-DEC-003",
        "CAL-DEC-004",
        "CAL-DEC-005",
        "CAL-DEC-006",
    ]
    assert activation.internal_scientific_planning_authorized is True
    assert activation.internal_statistical_planning_authorized is True
    assert activation.internal_budget_scenario_planning_authorized is True
    assert activation.final_human_review_preserved is True
    assert activation.external_contact_authorized is False
    assert activation.laboratory_quote_authorized is False
    assert activation.spending_authorized is False
    assert activation.data_access_authorized is False
    assert activation.study_execution_authorized is False


def test_planning_decision_rejects_expanded_authority() -> None:
    decision = load_prospective_calibration_founder_decision(DECISION)
    payload = decision.model_dump(mode="json")
    payload["external_contact_authorized"] = True
    payload["spending_authorized"] = True

    with pytest.raises(ValidationError, match="cannot authorize external"):
        ProspectiveCalibrationFounderDecision.model_validate(payload)


def test_planning_activation_rejects_changed_founder_packet(
    tmp_path: Path,
) -> None:
    changed = tmp_path / "packet.md"
    changed.write_bytes(PACKET.read_bytes() + b"\n")

    with pytest.raises(
        ProspectiveCalibrationDesignError,
        match="different founder packet",
    ):
        ProspectiveCalibrationDesignService().activate_planning(
            load_prospective_calibration_founder_decision(DECISION),
            load_prospective_calibration_design(DESIGN),
            decision_path=DECISION,
            design_path=DESIGN,
            decision_packet_path=changed,
            code_revision="5502f07",
            activated_at=datetime(2026, 7, 29, 18, 1, 3, tzinfo=UTC),
        )


def test_checked_in_planning_authorization_schemas_match_runtime_models() -> None:
    assert json.loads(DECISION_SCHEMA.read_text(encoding="utf-8")) == (
        ProspectiveCalibrationFounderDecision.model_json_schema()
    )
    assert json.loads(ACTIVATION_SCHEMA.read_text(encoding="utf-8")) == (
        ProspectiveCalibrationPlanningActivation.model_json_schema()
    )


def test_checked_in_planning_activation_matches_frozen_implementation() -> None:
    activation = load_prospective_calibration_planning_activation(
        PLANNING_ACTIVATION
    )
    regenerated = ProspectiveCalibrationDesignService().activate_planning(
        load_prospective_calibration_founder_decision(DECISION),
        load_prospective_calibration_design(DESIGN),
        decision_path=DECISION,
        design_path=DESIGN,
        decision_packet_path=PACKET,
        code_revision=activation.code_revision,
        activated_at=activation.activated_at,
    )

    assert activation == regenerated
    assert activation.code_revision == "00bfa89"
