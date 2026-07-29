from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.analysis.calibration_planning import (
    CalibrationPlanningError,
    CalibrationPlanningService,
)
from nas_core.domain.calibration_planning import (
    PhaseOneInternalPlanningBundle,
    StandingAutonomyAuthorization,
    load_phase_one_internal_planning_bundle,
    load_standing_autonomy_authorization,
)

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
AUTHORIZATION = (
    STUDY
    / "reviews"
    / "FOUNDER_STANDING_AUTONOMY_AUTHORIZATION_v1.0.0.yaml"
)
DECISION = (
    STUDY
    / "reviews"
    / "FOUNDER_PHASE1_SCIENTIFIC_STATISTICAL_PLANNING_DECISION_v0.1.0.yaml"
)
ACTIVATION = (
    STUDY
    / "protocol"
    / "prospective_calibration_planning_activation_v1.0.0.yaml"
)
BUNDLE = STUDY / "protocol" / "phase_one_internal_planning_bundle_v1.0.0.yaml"
AUTHORIZATION_SCHEMA = ROOT / "workflows" / "standing_autonomy_authorization.schema.json"
BUNDLE_SCHEMA = ROOT / "workflows" / "phase_one_internal_planning_bundle.schema.json"


def _validate() -> PhaseOneInternalPlanningBundle:
    bundle = load_phase_one_internal_planning_bundle(BUNDLE)
    return CalibrationPlanningService().validate(
        bundle,
        load_standing_autonomy_authorization(AUTHORIZATION),
        authorization_path=AUTHORIZATION,
        planning_decision_path=DECISION,
        planning_activation_path=ACTIVATION,
    )


def test_standing_autonomy_preserves_required_stops_and_final_review() -> None:
    authorization = load_standing_autonomy_authorization(AUTHORIZATION)

    assert authorization.routine_founder_approvals_required is False
    assert authorization.final_human_review_preserved is True
    assert authorization.external_contact_authorized is False
    assert authorization.spending_authorized is False
    assert authorization.controlled_data_authorized is False
    assert authorization.phi_authorized is False
    assert authorization.specimen_acquisition_authorized is False
    assert authorization.clinical_use_authorized is False
    assert authorization.external_publication_authorized is False
    assert authorization.external_submission_authorized is False


def test_phase_one_bundle_is_bound_and_nonexecuting() -> None:
    bundle = _validate()

    assert bundle.status.value == "internally_frozen_pending_evidence"
    assert bundle.platform_compatibility.intended_platform_family == (
        "bulk_rna_sequencing"
    )
    assert bundle.excluded_pilot.attempted_pairs == 30
    assert bundle.excluded_pilot.final_pair_count_approved is False
    assert len(bundle.platform_compatibility.compatibility_criteria) == 8
    assert len(bundle.coverage) == 4
    assert len(bundle.multiplicity) == 4
    assert all(
        variable.numeric_value is None
        for variable in bundle.symbolic_budget.variables
    )
    assert bundle.data_accessed is False
    assert bundle.source_selected is False
    assert bundle.threshold_selected is False
    assert bundle.study_execution_authorized is False
    assert bundle.publication_authorized is False


def test_standing_autonomy_rejects_external_authority() -> None:
    authorization = load_standing_autonomy_authorization(AUTHORIZATION)
    payload = authorization.model_dump(mode="json")
    payload["external_contact_authorized"] = True
    payload["spending_authorized"] = True

    with pytest.raises(ValidationError, match="stop-condition action"):
        StandingAutonomyAuthorization.model_validate(payload)


def test_phase_one_bundle_rejects_pilot_leakage_or_final_pair_count() -> None:
    bundle = load_phase_one_internal_planning_bundle(BUNDLE)
    payload = bundle.model_dump(mode="json")
    payload["excluded_pilot"]["permanently_excluded_from_primary_calibration"] = False
    payload["final_primary_pair_count_approved"] = True

    with pytest.raises(ValidationError):
        PhaseOneInternalPlanningBundle.model_validate(payload)


def test_phase_one_bundle_rejects_changed_authorization(tmp_path: Path) -> None:
    changed = tmp_path / "authorization.yaml"
    changed.write_bytes(AUTHORIZATION.read_bytes() + b"\n")

    with pytest.raises(
        CalibrationPlanningError,
        match="different autonomy authorization",
    ):
        CalibrationPlanningService().validate(
            load_phase_one_internal_planning_bundle(BUNDLE),
            load_standing_autonomy_authorization(changed),
            authorization_path=changed,
            planning_decision_path=DECISION,
            planning_activation_path=ACTIVATION,
        )


def test_checked_in_calibration_planning_schemas_match_models() -> None:
    assert json.loads(AUTHORIZATION_SCHEMA.read_text(encoding="utf-8")) == (
        StandingAutonomyAuthorization.model_json_schema()
    )
    assert json.loads(BUNDLE_SCHEMA.read_text(encoding="utf-8")) == (
        PhaseOneInternalPlanningBundle.model_json_schema()
    )
