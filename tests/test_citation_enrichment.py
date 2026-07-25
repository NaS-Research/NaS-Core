import json
from datetime import UTC, datetime

import pytest

from nas_core.domain.citation_chain import (
    CitationCandidate,
    CitationDirection,
    CitationPrioritizationReceipt,
    CitationPriorityRecord,
    CitationPriorityTier,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import HTTPResponse, canonical_json, sha256
from nas_core.retrieval.citation_enrichment import (
    CitationEnrichmentError,
    CitationEnrichmentService,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 20, 0, tzinfo=UTC)


class FakeTransport:
    def get(self, url: str, parameters: dict[str, str]) -> HTTPResponse:
        del url
        assert "SRC:MED" in parameters["query"]
        payload = {
            "hitCount": 1,
            "resultList": {
                "result": [
                    {
                        "id": "1",
                        "source": "MED",
                        "pmid": "1",
                        "pmcid": "PMC1",
                        "doi": "10.1/example",
                        "title": "PAM50 single-sample classifier stability.",
                        "authorString": "One A",
                        "journalTitle": "Methods",
                        "pubYear": 2024,
                        "abstractText": "A complete abstract.",
                        "isOpenAccess": "Y",
                    }
                ]
            },
        }
        return HTTPResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=json.dumps(payload).encode(),
        )


def _ranked(key: str, tier: CitationPriorityTier, rank: int) -> CitationPriorityRecord:
    source, external_id = key.split(":", maxsplit=1)
    return CitationPriorityRecord(
        rank=rank,
        score=20 if tier is CitationPriorityTier.DIRECT else 0,
        tier=tier,
        positive_signals=[],
        caution_signals=[],
        candidate=CitationCandidate(
            record_key=key,
            source=source,
            external_id=external_id,
            title="Original title",
            directions=[CitationDirection.FORWARD],
            seed_evidence_ids=["PMID:9"],
        ),
    )


def _receipt(
    store: InMemoryObjectStore,
    ranking: list[CitationPriorityRecord],
) -> CitationPrioritizationReceipt:
    body = canonical_json(
        [item.model_dump(mode="json", exclude_none=True) for item in ranking]
    )
    store.put_bytes("ranking.json", body, content_type="application/json")
    stored = StoredObject(
        object_key="ranking.json",
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )
    return CitationPrioritizationReceipt(
        prioritization_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=1,
        preparation_id="b" * 64,
        algorithm_version="citation-title-priority-1.0.1",
        code_revision="8981d9f",
        created_at=NOW,
        verified_at=NOW,
        candidate_count=len(ranking),
        direct_priority_count=sum(
            item.tier is CitationPriorityTier.DIRECT for item in ranking
        ),
        supporting_priority_count=sum(
            item.tier is CitationPriorityTier.SUPPORTING for item in ranking
        ),
        context_priority_count=sum(
            item.tier is CitationPriorityTier.CONTEXT for item in ranking
        ),
        ranking_object=stored,
        input_checksum_verified=True,
        output_checksum_verified=True,
        rank_invariants_verified=True,
    )


def test_enriches_noncontext_records_and_preserves_unresolved_matches() -> None:
    store = InMemoryObjectStore()
    ranking = [
        _ranked("MED:1", CitationPriorityTier.DIRECT, 1),
        _ranked("MED:2", CitationPriorityTier.SUPPORTING, 2),
        _ranked("MED:3", CitationPriorityTier.CONTEXT, 3),
    ]
    service = CitationEnrichmentService(
        store=store,
        transport=FakeTransport(),
        clock=lambda: NOW,
    )

    receipt = service.enrich(_receipt(store, ranking), code_revision="8981d9f")

    assert receipt.requested_candidate_count == 2
    assert receipt.selection_scope.value == "direct_and_supporting"
    assert receipt.metadata_match_count == 1
    assert receipt.abstract_count == 1
    assert receipt.unresolved_metadata_count == 1
    assert receipt.final_screening_decisions_recorded == 0
    enriched = json.loads(store.get_bytes(receipt.enriched_candidates_object.object_key))
    assert {item["record_key"] for item in enriched} == {"MED:1", "MED:2"}
    assert next(item for item in enriched if item["record_key"] == "MED:1")[
        "abstract"
    ] == "A complete abstract."


def test_full_scope_enrichment_includes_context_records() -> None:
    store = InMemoryObjectStore()
    ranking = [
        _ranked("MED:1", CitationPriorityTier.DIRECT, 1),
        _ranked("MED:3", CitationPriorityTier.CONTEXT, 2),
    ]
    service = CitationEnrichmentService(
        store=store,
        transport=FakeTransport(),
        clock=lambda: NOW,
    )

    receipt = service.enrich(
        _receipt(store, ranking),
        code_revision="8981d9f",
        include_context=True,
    )

    assert receipt.selection_scope.value == "all_candidates"
    assert receipt.requested_candidate_count == 2


def test_enrichment_rejects_tampered_ranking() -> None:
    store = InMemoryObjectStore()
    receipt = _receipt(
        store, [_ranked("MED:1", CitationPriorityTier.DIRECT, 1)]
    )
    store.put_bytes("ranking.json", b"[]", content_type="application/json")
    service = CitationEnrichmentService(
        store=store,
        transport=FakeTransport(),
        clock=lambda: NOW,
    )

    with pytest.raises(CitationEnrichmentError, match="does not match"):
        service.enrich(receipt, code_revision="8981d9f")
