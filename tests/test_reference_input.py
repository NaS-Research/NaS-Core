from __future__ import annotations

import json
from pathlib import Path

from nas_core.domain.reference_input import (
    ReferenceInputFounderDecision,
    load_reference_input_founder_decision,
)
from nas_core.ingestion.gdc import sha256

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
DECISION = STUDY / "reviews/FOUNDER_REFERENCE_INPUT_DECISION_v1.1.0.yaml"
PACKET = STUDY / "reviews/REFERENCE_INPUT_DECISION_PACKET_v1.0.0.md"
MATRIX_AUDIT = STUDY / "ingestion/gse81538_matrix_audit_receipt_v1.0.0.yaml"
METADATA_ACQUISITION = (
    STUDY / "ingestion/gse81538_family_soft_acquisition_receipt_v1.0.0.yaml"
)
SCHEMA = ROOT / "workflows/reference_input_founder_decision.schema.json"


def test_reference_input_decision_is_exact_and_bounded() -> None:
    decision = load_reference_input_founder_decision(DECISION)

    assert decision.decision_packet_sha256 == sha256(PACKET.read_bytes())
    assert decision.matrix_audit_receipt_sha256 == sha256(MATRIX_AUDIT.read_bytes())
    assert decision.metadata_acquisition_receipt_sha256 == sha256(
        METADATA_ACQUISITION.read_bytes()
    )
    assert decision.stored_input_representation == "log2(FPKM + 0.1)"
    assert decision.additional_transformation == "none"
    assert decision.er_negative_consensus_code == 0
    assert decision.er_positive_consensus_code == 3
    assert decision.excluded_er_consensus_codes == [1, 2]
    assert decision.outcome_blind_reference_construction_authorized is True
    assert decision.outcome_access_authorized is False
    assert decision.validation_data_access_authorized is False
    assert decision.classifier_execution_authorized is False
    assert decision.final_human_review_preserved is True


def test_reference_input_decision_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        ReferenceInputFounderDecision.model_json_schema()
    )
