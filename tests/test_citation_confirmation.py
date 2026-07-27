from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.domain.citation_chain import load_citation_founder_packet_receipt
from nas_core.domain.citation_confirmation import (
    CONFIRMATION_STATEMENT,
    CitationFounderConfirmation,
    citation_confirmation_statement,
    single_citation_confirmation_statement,
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
PASS6_PACKET = LITERATURE / "FOUNDER_CITATION_PASS_0006_REVIEW_v1.0.0.md"
PASS6_APPENDIX = LITERATURE / "FOUNDER_CITATION_PASS_0006_APPENDIX_v1.0.0.csv"
PASS6_RECEIPT = LITERATURE / "citation-chain" / "pass-0006-founder-packet.yaml"


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


def test_confirmation_statement_is_bound_to_pass_number() -> None:
    payload = _confirmation().model_dump()
    payload["pass_number"] = 2
    payload["confirmation_statement"] = citation_confirmation_statement(2)

    confirmation = CitationFounderConfirmation.model_validate(payload)

    assert confirmation.confirmation_statement == (
        "I confirm both checksum-bound citation pass 2 packets as written."
    )


def test_single_packet_confirmation_freezes_zero_pending_ledger() -> None:
    packet = load_citation_founder_packet_receipt(PASS6_RECEIPT)
    confirmation = CitationFounderConfirmation(
        study_id="NAS-BRCA-002",
        pass_number=6,
        first_packet_sha256=packet.packet_sha256,
        first_appendix_sha256=packet.appendix_sha256,
        confirmation_statement=single_citation_confirmation_statement(6),
        founder_id="dalron-j-robertson",
        founder_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        confirmed_at=NOW,
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )

    receipt = CitationDecisionConfirmationService(
        store=InMemoryObjectStore()
    ).confirm_single(
        packet,
        confirmation,
        packet_path=PASS6_PACKET,
        appendix_path=PASS6_APPENDIX,
        code_revision="15374c5",
    )

    assert receipt.candidate_count == 38
    assert receipt.included_count == 0
    assert receipt.excluded_count == 38
    assert receipt.second_packet_sha256 is None


def test_single_packet_confirmation_rejects_pending_records() -> None:
    packet = load_citation_founder_packet_receipt(FIRST_RECEIPT)
    confirmation = _confirmation().model_copy(
        update={
            "second_packet_sha256": None,
            "second_appendix_sha256": None,
            "confirmation_statement": single_citation_confirmation_statement(1),
        }
    )

    with pytest.raises(CitationConfirmationError, match="pending adjudication"):
        CitationDecisionConfirmationService(
            store=InMemoryObjectStore()
        ).confirm_single(
            packet,
            confirmation,
            packet_path=FIRST_PACKET,
            appendix_path=FIRST_APPENDIX,
            code_revision="15374c5",
        )


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
