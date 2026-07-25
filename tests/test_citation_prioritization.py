import json
from datetime import UTC, datetime

import pytest

from nas_core.domain.citation_chain import (
    CitationCandidate,
    CitationDirection,
    CitationScreeningPreparationReceipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.citation_prioritization import (
    CitationPrioritizationError,
    CitationPrioritizationService,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 19, 0, tzinfo=UTC)


def _candidate(key: str, title: str, year: int) -> CitationCandidate:
    source, external_id = key.split(":", maxsplit=1)
    return CitationCandidate(
        record_key=key,
        source=source,
        external_id=external_id,
        title=title,
        publication_year=year,
        directions=[CitationDirection.FORWARD],
        seed_evidence_ids=["PMID:1"],
    )


def _preparation(
    store: InMemoryObjectStore, candidates: list[CitationCandidate]
) -> CitationScreeningPreparationReceipt:
    body = canonical_json(
        [item.model_dump(mode="json", exclude_none=True) for item in candidates]
    )
    store.put_bytes("screening/candidates.json", body, content_type="application/json")
    stored = StoredObject(
        object_key="screening/candidates.json",
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )
    return CitationScreeningPreparationReceipt(
        preparation_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=1,
        citation_execution_id="b" * 64,
        prior_search_execution_id="c" * 64,
        code_revision="8981d9f",
        created_at=NOW,
        verified_at=NOW,
        input_candidate_count=len(candidates),
        already_screened_count=0,
        duplicate_candidate_count=0,
        requires_screening_count=len(candidates),
        inventory_object=stored.model_copy(update={"object_key": "unused.json"}),
        screening_candidates_object=stored,
        input_checksums_verified=True,
        output_checksums_verified=True,
        count_invariants_verified=True,
    )


def test_prioritization_ranks_all_records_without_decisions() -> None:
    store = InMemoryObjectStore()
    candidates = [
        _candidate("MED:1", "PAM50 single-sample classifier stability in breast cancer", 2020),
        _candidate("MED:2", "Molecular subtyping of breast tumors", 2024),
        _candidate("MED:3", "Single sample scoring of molecular phenotypes", 2018),
        _candidate("MED:4", "A general oncology outcome report", 2025),
    ]
    service = CitationPrioritizationService(store=store, clock=lambda: NOW)

    receipt = service.prioritize(
        _preparation(store, candidates), code_revision="8981d9f"
    )

    assert receipt.candidate_count == 4
    assert receipt.direct_priority_count == 1
    assert receipt.supporting_priority_count == 2
    assert receipt.context_priority_count == 1
    assert receipt.final_screening_decisions_recorded == 0
    ranked = json.loads(store.get_bytes(receipt.ranking_object.object_key))
    assert [item["rank"] for item in ranked] == [1, 2, 3, 4]
    assert ranked[0]["candidate"]["record_key"] == "MED:1"


def test_prioritization_rejects_tampered_candidate_object() -> None:
    store = InMemoryObjectStore()
    preparation = _preparation(
        store, [_candidate("MED:1", "PAM50 classifier", 2020)]
    )
    store.put_bytes(
        preparation.screening_candidates_object.object_key,
        b"[]",
        content_type="application/json",
    )
    service = CitationPrioritizationService(store=store, clock=lambda: NOW)

    with pytest.raises(CitationPrioritizationError, match="do not match"):
        service.prioritize(preparation, code_revision="8981d9f")
