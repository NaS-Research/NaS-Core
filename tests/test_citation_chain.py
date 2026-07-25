import json
from datetime import UTC, datetime

import pytest

from nas_core.domain.citation_chain import CitationSeed
from nas_core.ingestion.gdc import HTTPResponse
from nas_core.retrieval.citation_chain import (
    CitationChainError,
    CitationChainRetrievalService,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 16, 0, tzinfo=UTC)


class FakeCitationTransport:
    def get(self, url: str, parameters: dict[str, str]) -> HTTPResponse:
        del parameters
        if url.endswith("/references"):
            payload = {
                "hitCount": 2,
                "referenceList": {
                    "reference": [
                        {
                            "id": "111",
                            "source": "MED",
                            "title": "A relevant prior method.",
                            "authorString": "One A.",
                            "journalAbbreviation": "Journal",
                            "pubYear": 2020,
                        },
                        {
                            "id": "222",
                            "source": "MED",
                            "title": "A duplicated linked method.",
                            "authorString": "Two B.",
                            "journalAbbreviation": "Journal",
                            "pubYear": 2021,
                        },
                    ]
                },
            }
        else:
            payload = {
                "hitCount": 2,
                "citationList": {
                    "citation": [
                        {
                            "id": "222",
                            "source": "MED",
                            "title": "A duplicated linked method.",
                            "authorString": "Two B.",
                            "journalAbbreviation": "Journal",
                            "pubYear": 2021,
                        },
                        {
                            "id": "456",
                            "source": "MED",
                            "title": "The seed must not become a candidate.",
                            "pubYear": 2022,
                        },
                    ]
                },
            }
        return HTTPResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=json.dumps(payload).encode(),
        )


def _seed() -> CitationSeed:
    return CitationSeed(
        evidence_id="PMID:456",
        pmid="456",
        title="Synthetic seed",
    )


def test_retrieves_deduplicates_and_verifies_both_citation_directions() -> None:
    store = InMemoryObjectStore()
    service = CitationChainRetrievalService(
        store=store,
        transport=FakeCitationTransport(),
        clock=lambda: NOW,
    )

    snapshot = service.retrieve(
        [_seed()],
        study_id="NAS-BRCA-002",
        pass_number=1,
        code_revision="f9f1f46",
    )
    receipt = service.verify(snapshot)

    assert receipt.backward_candidate_count == 2
    assert receipt.forward_candidate_count == 2
    assert receipt.unique_candidate_count == 2
    assert receipt.endpoint_request_count == 2
    assert receipt.manifest_checksum_verified is True
    assert receipt.object_checksums_verified is True
    candidates = json.loads(store.get_bytes(receipt.candidates_object.object_key))
    by_key = {item["record_key"]: item for item in candidates}
    assert set(by_key) == {"MED:111", "MED:222"}
    assert set(by_key["MED:222"]["directions"]) == {"backward", "forward"}


def test_verification_detects_tampered_candidate_object() -> None:
    store = InMemoryObjectStore()
    service = CitationChainRetrievalService(
        store=store,
        transport=FakeCitationTransport(),
        clock=lambda: NOW,
    )
    snapshot = service.retrieve(
        [_seed()],
        study_id="NAS-BRCA-002",
        pass_number=1,
        code_revision="f9f1f46",
    )
    store.put_bytes(
        snapshot.candidates_object.object_key,
        b"[]",
        content_type="application/json",
    )

    with pytest.raises(CitationChainError, match="checksum or size"):
        service.verify(snapshot)
