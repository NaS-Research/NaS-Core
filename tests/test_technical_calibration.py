from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.analysis.technical_calibration import (
    TechnicalCalibrationPlanError,
    TechnicalCalibrationPlanService,
)
from nas_core.domain.method_dependency import (
    MethodDependencyAuditProposal,
    Pam50CentroidCandidateArtifact,
    load_method_dependency_audit,
    load_pam50_centroid_candidate,
)
from nas_core.domain.technical_calibration import (
    CalibrationSourceDisposition,
    TechnicalCalibrationAcquisitionPlan,
    load_technical_calibration_plan,
)

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
PLAN = STUDY / "protocol" / "technical_calibration_acquisition_plan_v1.0.0.yaml"
AUDIT = STUDY / "protocol" / "method_dependency_audit_proposal_v1.0.0.yaml"
CANDIDATE = (
    STUDY
    / "protocol"
    / "artifact-candidates"
    / "genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
)
SCHEMA = ROOT / "workflows" / "technical_calibration_acquisition_plan.schema.json"


def _artifacts() -> tuple[
    TechnicalCalibrationAcquisitionPlan,
    MethodDependencyAuditProposal,
    Pam50CentroidCandidateArtifact,
]:
    return (
        load_technical_calibration_plan(PLAN),
        load_method_dependency_audit(AUDIT),
        load_pam50_centroid_candidate(CANDIDATE),
    )


def test_checked_in_calibration_plan_is_bound_and_nonexecuting() -> None:
    plan, audit, candidate = _artifacts()

    validated = TechnicalCalibrationPlanService().validate(
        plan,
        audit,
        candidate,
        audit_path=AUDIT,
        candidate_path=CANDIDATE,
    )

    assert validated.selected_source_id is None
    assert validated.founder_route_selected is False
    assert len(validated.source_candidates) == 4
    assert not any(
        source.candidate_for_threshold_calibration
        for source in validated.source_candidates
    )
    assert validated.patient_level_data_accessed is False
    assert validated.molecular_values_accessed is False
    assert validated.outcome_data_accessed is False
    assert validated.threshold_selection_authorized is False
    assert validated.method_execution_authorized is False


def test_external_validation_source_cannot_calibrate_itself() -> None:
    plan, _, _ = _artifacts()
    source = plan.source_candidates[0].model_copy(
        update={
            "disposition": CalibrationSourceDisposition.RESERVED_EXTERNAL_VALIDATION,
            "independent_from_external_validation": True,
            "candidate_for_threshold_calibration": True,
        }
    )
    payload = plan.model_dump(mode="json")
    payload["source_candidates"][0] = source.model_dump(mode="json")

    with pytest.raises(ValidationError, match="external-validation source"):
        TechnicalCalibrationAcquisitionPlan.model_validate(payload)


def test_plan_cannot_select_source_before_founder_route() -> None:
    plan, _, _ = _artifacts()
    payload = plan.model_dump(mode="json")
    source = payload["source_candidates"][2]
    for field in (
        "independent_from_classifier_training",
        "independent_from_external_validation",
        "paired_measurements_reported",
        "participant_level_molecular_values_available",
        "stable_pair_identifiers_available",
        "full_classifier_panel_confirmed",
        "lawful_access_verified",
    ):
        source[field] = True
    source["candidate_for_threshold_calibration"] = True
    payload["selected_source_id"] = source["source_id"]

    with pytest.raises(ValidationError, match="before the founder route"):
        TechnicalCalibrationAcquisitionPlan.model_validate(payload)


def test_plan_rejects_candidate_checksum_drift(tmp_path: Path) -> None:
    plan, audit, candidate = _artifacts()
    changed = tmp_path / "candidate.yaml"
    changed.write_bytes(CANDIDATE.read_bytes() + b"\n")

    with pytest.raises(TechnicalCalibrationPlanError, match="different centroid"):
        TechnicalCalibrationPlanService().validate(
            plan,
            audit,
            candidate,
            audit_path=AUDIT,
            candidate_path=changed,
        )


def test_checked_in_calibration_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        TechnicalCalibrationAcquisitionPlan.model_json_schema()
    )
