from __future__ import annotations

import json
from pathlib import Path

import pytest

from nas_core.analysis.calibration_readiness import (
    CalibrationReadinessError,
    TechnicalCalibrationReadinessService,
)
from nas_core.domain.calibration_lineage import load_calibration_lineage_receipt
from nas_core.domain.calibration_planning import (
    load_phase_one_internal_planning_bundle,
    load_standing_autonomy_authorization,
)
from nas_core.domain.calibration_readiness import TechnicalCalibrationReadinessReceipt
from nas_core.domain.prospective_calibration import (
    load_calibration_contact_revocation,
    load_prospective_calibration_design,
)
from nas_core.domain.reference_construction import load_reference_construction_receipt
from nas_core.domain.reference_sensitivity import load_reference_sensitivity_receipt
from nas_core.domain.technical_calibration import (
    load_technical_calibration_plan,
    load_technical_calibration_scout,
)

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
AUTHORIZATION = STUDY / "reviews/FOUNDER_STANDING_AUTONOMY_AUTHORIZATION_v1.0.0.yaml"
ACQUISITION = STUDY / "protocol/technical_calibration_acquisition_plan_v1.0.0.yaml"
SCOUT = STUDY / "protocol/technical_calibration_source_scout_v1.0.0.yaml"
LINEAGE = STUDY / "ingestion/calibration_lineage_receipt_v1.0.0.yaml"
DESIGN = STUDY / "protocol/prospective_calibration_experiment_design_v0.1.0.yaml"
PLANNING = STUDY / "protocol/phase_one_internal_planning_bundle_v1.0.0.yaml"
REVOCATION = STUDY / "reviews/FOUNDER_CALIBRATION_INQUIRY_REVOCATION_v1.0.0.yaml"
REFERENCE = STUDY / "analysis/gse81538_reference_construction_receipt_v1.0.0.yaml"
SENSITIVITY = STUDY / "analysis/gse81538_reference_sensitivity_receipt_v1.0.0.yaml"
SCHEMA = ROOT / "workflows/technical_calibration_readiness.schema.json"


def _assess(authorization=None) -> TechnicalCalibrationReadinessReceipt:
    return TechnicalCalibrationReadinessService().assess(
        authorization or load_standing_autonomy_authorization(AUTHORIZATION),
        load_technical_calibration_plan(ACQUISITION),
        load_technical_calibration_scout(SCOUT),
        load_calibration_lineage_receipt(LINEAGE),
        load_prospective_calibration_design(DESIGN),
        load_phase_one_internal_planning_bundle(PLANNING),
        load_calibration_contact_revocation(REVOCATION),
        load_reference_construction_receipt(REFERENCE),
        load_reference_sensitivity_receipt(SENSITIVITY),
        authorization_path=AUTHORIZATION,
        acquisition_path=ACQUISITION,
        scout_path=SCOUT,
        lineage_path=LINEAGE,
        design_path=DESIGN,
        planning_path=PLANNING,
        revocation_path=REVOCATION,
        reference_path=REFERENCE,
        sensitivity_path=SENSITIVITY,
        code_revision="abcdef1",
    )


def test_readiness_authorizes_only_two_public_feasibility_sources() -> None:
    receipt = _assess()

    assert receipt.decision.value == (
        "public_feasibility_only_primary_calibration_not_ready"
    )
    assert set(receipt.public_feasibility_source_ids) == {
        "GEO:GSE60788",
        "GEO:GSE130397",
    }
    assert receipt.primary_calibration_ready is False
    assert receipt.primary_calibration_source_id is None
    assert receipt.gse96058_molecular_access_authorized is False
    assert receipt.external_contact_authorized is False
    assert receipt.threshold_selection_authorized is False


def test_readiness_rejects_missing_public_data_delegation() -> None:
    authorization = load_standing_autonomy_authorization(AUTHORIZATION)
    changed = authorization.model_copy(
        update={
            "delegated_internal_actions": [
                item
                for item in authorization.delegated_internal_actions
                if item != "approved_public_open_data_use"
            ]
        }
    )

    with pytest.raises(CalibrationReadinessError, match="public/open"):
        _assess(changed)


def test_calibration_readiness_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text()) == (
        TechnicalCalibrationReadinessReceipt.model_json_schema()
    )
