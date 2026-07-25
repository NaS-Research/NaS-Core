from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.domain.citation_chain import load_citation_founder_packet_receipt
from nas_core.domain.citation_confirmation import (
    CONFIRMATION_STATEMENT,
    CitationFounderConfirmation,
)
from nas_core.retrieval.citation_confirmation import (
    CitationConfirmationError,
    CitationDecisionConfirmationService,
)
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
LITERATURE = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
)
FIRST_PACKET = LITERATURE / "FOUNDER_CITATION_PASS_0001_PACKET_v1.0.0.md"
FIRST_APPENDIX = LITERATURE / "FOUNDER_CITATION_PASS_0001_APPENDIX_v1.0.0.csv"
FIRST_RECEIPT = LITERATURE / "citation-chain" / "pass-0001-founder-packet.yaml"
SECOND_PACKET = (
    LITERATURE / "FOUNDER_CITATION_PASS_0001_ADJUDICATION_PACKET_v1.0.0.md"
)
SECOND_APPENDIX = (
    LITERATURE / "FOUNDER_CITATION_PASS_0001_ADJUDICATION_APPENDIX_v1.0.0.csv"
)
SECOND_RECEIPT = (
    LITERATURE / "citation-chain" / "pass-0001-adjudication-packet.yaml"
)
NOW = datetime(2026, 7, 25, 23, 30, tzinfo=UTC)


def _confirmation() -> CitationFounderConfirmation:
    first = load_citation_founder_packet_receipt(FIRST_RECEIPT)
    second = load_citation_founder_packet_receipt(SECOND_RECEIPT)
    return CitationFounderConfirmation(
        study_id="NAS-BRCA-002",
        pass_number=1,
        first_packet_sha256=first.packet_sha256,
        first_appendix_sha256=first.appendix_sha256,
        second_packet_sha256=second.packet_sha256,
        second_appendix_sha256=second.appendix_sha256,
        confirmation_statement=CONFIRMATION_STATEMENT,
        founder_id="dalron-j-robertson",
        founder_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        confirmed_at=NOW,
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )


def test_combined_confirmation_freezes_complete_founder_decision_ledger() -> None:
    store = InMemoryObjectStore()
    service = CitationDecisionConfirmationService(store=store)

    receipt = service.confirm(
        load_citation_founder_packet_receipt(FIRST_RECEIPT),
        load_citation_founder_packet_receipt(SECOND_RECEIPT),
        _confirmation(),
        first_packet_path=FIRST_PACKET,
        first_appendix_path=FIRST_APPENDIX,
        second_packet_path=SECOND_PACKET,
        second_appendix_path=SECOND_APPENDIX,
        code_revision="3789e84",
    )

    assert receipt.candidate_count == 4495
    assert receipt.included_count == 32
    assert receipt.excluded_count == 4463
    assert receipt.unclear_count == 0
    assert receipt.ai_decisions_recorded == 0
    assert receipt.founder_authorized is True
    assert store.exists(receipt.ledger_object.object_key)


def test_confirmation_contract_rejects_standing_authorization_alone() -> None:
    payload = _confirmation().model_dump()
    payload["founder_authorized"] = False

    with pytest.raises(ValidationError, match="founder authorization"):
        CitationFounderConfirmation.model_validate(payload)


def test_confirmation_rejects_tampered_packet_bytes(tmp_path: Path) -> None:
    tampered = tmp_path / "packet.md"
    tampered.write_text("tampered", encoding="utf-8")
    service = CitationDecisionConfirmationService(store=InMemoryObjectStore())

    with pytest.raises(CitationConfirmationError, match="checksum failed"):
        service.confirm(
            load_citation_founder_packet_receipt(FIRST_RECEIPT),
            load_citation_founder_packet_receipt(SECOND_RECEIPT),
            _confirmation(),
            first_packet_path=tampered,
            first_appendix_path=FIRST_APPENDIX,
            second_packet_path=SECOND_PACKET,
            second_appendix_path=SECOND_APPENDIX,
            code_revision="3789e84",
        )
