import json
from datetime import UTC, datetime

import pytest

from nas_core.domain.citation_chain import (
    CitationCandidate,
    CitationChainReceipt,
    CitationDirection,
)
from nas_core.domain.citation_confirmation import (
    CitationDecisionLedgerReceipt,
    CitationDecisionLedgerRecord,
)
from nas_core.domain.literature import (
    BibliographicRecord,
    LiteratureSearchReceipt,
    ScreeningStatus,
    SourceSearchReceipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.citation_screening import (
    CitationScreeningPreparationError,
    CitationScreeningPreparationService,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 18, 0, tzinfo=UTC)


def _stored(store: InMemoryObjectStore, key: str, payload: object) -> StoredObject:
    body = canonical_json(payload)
    store.put_bytes(key, body, content_type="application/json")
    return StoredObject(
        object_key=key,
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )


def _citation_receipt(
    store: InMemoryObjectStore,
    candidates: list[CitationCandidate],
    *,
    pass_number: int = 1,
) -> CitationChainReceipt:
    candidate_object = _stored(
        store,
        "citation/candidates.json",
        [item.model_dump(mode="json") for item in candidates],
    )
    raw_object = _stored(store, "citation/raw.json", [])
    return CitationChainReceipt(
        execution_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=pass_number,
        code_revision="f9f1f46",
        retrieved_at=NOW,
        verified_at=NOW,
        seed_evidence_ids=["PMID:1"],
        backward_candidate_count=len(candidates),
        forward_candidate_count=0,
        unique_candidate_count=len(candidates),
        endpoint_request_count=2,
        manifest_object_key="citation/manifest.json",
        manifest_sha256="b" * 64,
        raw_responses_object=raw_object,
        candidates_object=candidate_object,
        manifest_checksum_verified=True,
        object_checksums_verified=True,
        endpoint_counts_verified=True,
        candidate_count_verified=True,
    )


def _prior_receipt(
    store: InMemoryObjectStore, records: list[BibliographicRecord]
) -> LiteratureSearchReceipt:
    body = canonical_json([item.model_dump(mode="json") for item in records])
    store.put_bytes("prior/records.json", body, content_type="application/json")
    source = SourceSearchReceipt(
        source_id="pubmed",
        reported_result_count=len(records),
        retrieved_record_count=len(records),
        request_count=1,
        raw_object_count=1,
    )
    return LiteratureSearchReceipt(
        execution_id="c" * 64,
        study_id="NAS-BRCA-002",
        question_id="NAS-RQ-BRCA002",
        question_version="0.3.0",
        strategy_version="0.2.4",
        executed_at=NOW,
        source_results=[source, source.model_copy(update={"source_id": "europe-pmc"})],
        unique_record_count=len(records),
        duplicate_record_count=0,
        manifest_object_key="prior/manifest.json",
        manifest_sha256="d" * 64,
        normalized_records_object_key="prior/records.json",
        normalized_records_sha256=sha256(body),
        normalized_records_size_bytes=len(body),
        verified_at=NOW,
        manifest_checksum_verified=True,
        object_checksums_verified=True,
        object_sizes_verified=True,
        record_count_invariants_verified=True,
        verified_object_count=3,
        screening_status=ScreeningStatus.COMPLETE,
        scientific_conclusions_drawn=False,
        outcome_data_accessed=False,
    )


def _candidate(
    key: str, source: str, external_id: str, title: str
) -> CitationCandidate:
    return CitationCandidate(
        record_key=key,
        source=source,
        external_id=external_id,
        title=title,
        directions=[CitationDirection.FORWARD],
        seed_evidence_ids=["PMID:1"],
    )


def _decision_receipt(
    store: InMemoryObjectStore,
    records: list[CitationDecisionLedgerRecord],
    *,
    pass_number: int = 1,
) -> CitationDecisionLedgerReceipt:
    stored = _stored(
        store,
        f"prior/decisions-{pass_number}.json",
        [item.model_dump(mode="json", exclude_none=True) for item in records],
    )
    included = sum(record.decision.value == "include" for record in records)
    return CitationDecisionLedgerReceipt(
        decision_id=("e" if pass_number == 1 else "9") * 64,
        study_id="NAS-BRCA-002",
        pass_number=pass_number,
        code_revision="abcdef0",
        confirmed_at=NOW,
        founder_id="founder",
        founder_name="Founder",
        first_packet_sha256="f" * 64,
        first_appendix_sha256="1" * 64,
        second_packet_sha256="2" * 64,
        second_appendix_sha256="3" * 64,
        candidate_count=len(records),
        included_count=included,
        excluded_count=len(records) - included,
        unclear_count=0,
        ledger_object=stored,
        packet_checksums_verified=True,
        appendix_checksums_verified=True,
        record_coverage_verified=True,
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )


def test_preparation_deduplicates_prior_and_cross_source_records() -> None:
    store = InMemoryObjectStore()
    candidates = [
        _candidate("MED:10", "MED", "10", "Previously screened paper."),
        _candidate("MED:20", "MED", "20", "A new method"),
        _candidate("PPR:PPR20", "PPR", "PPR20", "A new method."),
        _candidate("MED:30", "MED", "30", "Another new method"),
    ]
    prior = [
        BibliographicRecord(
            record_key="pubmed:10",
            source_ids=["pubmed"],
            pmid="10",
            title="Previously screened paper",
        )
    ]
    service = CitationScreeningPreparationService(store=store, clock=lambda: NOW)

    receipt = service.prepare(
        _citation_receipt(store, candidates),
        _prior_receipt(store, prior),
        code_revision="f9f1f46",
    )

    assert receipt.input_candidate_count == 4
    assert receipt.already_screened_count == 1
    assert receipt.duplicate_candidate_count == 1
    assert receipt.requires_screening_count == 2
    screening = json.loads(
        store.get_bytes(receipt.screening_candidates_object.object_key)
    )
    assert {item["record_key"] for item in screening} == {"MED:20", "MED:30"}
    assert receipt.final_screening_decisions_recorded == 0


def test_preparation_rejects_tampered_citation_candidates() -> None:
    store = InMemoryObjectStore()
    candidates = [_candidate("MED:20", "MED", "20", "A new method")]
    citation = _citation_receipt(store, candidates)
    store.put_bytes(
        citation.candidates_object.object_key,
        b"[]",
        content_type="application/json",
    )
    service = CitationScreeningPreparationService(store=store, clock=lambda: NOW)

    with pytest.raises(CitationScreeningPreparationError, match="does not match"):
        service.prepare(
            citation,
            _prior_receipt(store, []),
            code_revision="f9f1f46",
        )


def test_pass_two_deduplicates_every_prior_founder_decision() -> None:
    store = InMemoryObjectStore()
    prior_record = CitationDecisionLedgerRecord(
        record_key="MED:20",
        rank=1,
        title="A prior citation method",
        pmid="20",
        decision="include",
        reviewer_id="founder",
        reviewer_name="Founder",
        reviewer_role="founder_internal_reviewer",
        decided_at=NOW,
        founder_authorized=True,
        ai_decision=False,
    )
    candidates = [
        _candidate("MED:20", "MED", "20", "A prior citation method"),
        _candidate("MED:30", "MED", "30", "A newly linked method"),
    ]
    service = CitationScreeningPreparationService(store=store, clock=lambda: NOW)

    receipt = service.prepare(
        _citation_receipt(store, candidates, pass_number=2),
        _prior_receipt(store, []),
        code_revision="f9f1f46",
        prior_decision_receipts=[_decision_receipt(store, [prior_record])],
    )

    assert receipt.prior_decision_ids == ["e" * 64]
    assert receipt.already_screened_count == 1
    assert receipt.requires_screening_count == 1
    screening = json.loads(
        store.get_bytes(receipt.screening_candidates_object.object_key)
    )
    assert [item["record_key"] for item in screening] == ["MED:30"]


def test_pass_two_requires_complete_prior_decision_history() -> None:
    store = InMemoryObjectStore()
    service = CitationScreeningPreparationService(store=store, clock=lambda: NOW)

    with pytest.raises(
        CitationScreeningPreparationError,
        match="one decision ledger for every prior pass",
    ):
        service.prepare(
            _citation_receipt(
                store,
                [_candidate("MED:30", "MED", "30", "A newly linked method")],
                pass_number=2,
            ),
            _prior_receipt(store, []),
            code_revision="f9f1f46",
        )


def test_pass_three_deduplicates_both_prior_founder_ledgers() -> None:
    store = InMemoryObjectStore()
    pass_one = CitationDecisionLedgerRecord(
        record_key="MED:20",
        rank=1,
        title="Pass one method",
        pmid="20",
        decision="include",
        reviewer_id="founder",
        reviewer_name="Founder",
        reviewer_role="founder_internal_reviewer",
        decided_at=NOW,
        founder_authorized=True,
        ai_decision=False,
    )
    pass_two = pass_one.model_copy(
        update={
            "record_key": "MED:30",
            "title": "Pass two method",
            "pmid": "30",
        }
    )
    candidates = [
        _candidate("MED:20", "MED", "20", "Pass one method"),
        _candidate("MED:30", "MED", "30", "Pass two method"),
        _candidate("MED:40", "MED", "40", "Pass three new method"),
    ]

    receipt = CitationScreeningPreparationService(
        store=store, clock=lambda: NOW
    ).prepare(
        _citation_receipt(store, candidates, pass_number=3),
        _prior_receipt(store, []),
        code_revision="f9f1f46",
        prior_decision_receipts=[
            _decision_receipt(store, [pass_one], pass_number=1),
            _decision_receipt(store, [pass_two], pass_number=2),
        ],
    )

    assert receipt.prior_decision_ids == ["e" * 64, "9" * 64]
    assert receipt.already_screened_count == 2
    assert receipt.requires_screening_count == 1
    screening = json.loads(
        store.get_bytes(receipt.screening_candidates_object.object_key)
    )
    assert [item["record_key"] for item in screening] == ["MED:40"]
