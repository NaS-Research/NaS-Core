from datetime import UTC, datetime

from nas_core.domain.appraisal import FullTextInventory, FullTextInventoryRecord
from nas_core.ingestion.gdc import HTTPResponse
from nas_core.retrieval.citation_access import (
    CitationAccessCheckQueueService,
    CitationRepositoryAccessService,
)
from nas_core.retrieval.full_text_retrieval import FullTextRetrievalService
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 20, 0, tzinfo=UTC)


def _xml(*, license_url: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front><article-meta>
    <article-id pub-id-type="pmcid">PMC123</article-id>
    <article-id pub-id-type="pmid">456</article-id>
    <article-id pub-id-type="doi">10.1/synthetic</article-id>
    <title-group><article-title>Synthetic licensed study</article-title></title-group>
    <permissions>
      <copyright-statement>© Synthetic authors 2026</copyright-statement>
      <license xlink:href="{license_url}">
        <license-p>Creative Commons Attribution 4.0 International License</license-p>
      </license>
    </permissions>
  </article-meta></front>
</article>""".encode()


class FakeTransport:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def get(self, url: str) -> HTTPResponse:
        del url
        return HTTPResponse(status_code=200, headers={}, body=self.body)


def _inventory() -> FullTextInventory:
    return FullTextInventory(
        study_id="NAS-BRCA-002",
        queue_id="a" * 64,
        progress_id="b" * 64,
        provisional_inclusion_count=1,
        repository_candidate_count=1,
        access_check_required_count=0,
        records=[
            FullTextInventoryRecord(
                screening_id="c" * 64,
                record_key="MED:456",
                title="Synthetic licensed study.",
                pmid="456",
                pmcid="PMC123",
                doi="10.1/synthetic",
                access_status="repository_candidate",
            )
        ],
    )


def _service(body: bytes) -> CitationRepositoryAccessService:
    return CitationRepositoryAccessService(
        retrieval_service=FullTextRetrievalService(
            store=InMemoryObjectStore(),
            transport=FakeTransport(body),
            clock=lambda: NOW,
        ),
        clock=lambda: NOW,
    )


def test_repository_batch_retrieves_only_verified_cc_by_article() -> None:
    batch, receipts = _service(
        _xml(license_url="https://creativecommons.org/licenses/by/4.0/")
    ).assess(
        _inventory(),
        code_revision="abcdef0",
        receipt_directory="literature/citation-full-text",
    )

    assert batch.repository_candidate_count == 1
    assert batch.retrieved_count == 1
    assert batch.access_check_required_count == 0
    assert len(receipts) == 1
    assert batch.records[0].outcome == "retrieved"
    assert batch.records[0].durable_full_text_stored is True


def test_repository_batch_routes_unapproved_license_without_storage() -> None:
    batch, receipts = _service(
        _xml(license_url="https://creativecommons.org/licenses/by-nc/4.0/")
    ).assess(
        _inventory(),
        code_revision="abcdef0",
        receipt_directory="literature/citation-full-text",
    )

    assert batch.retrieved_count == 0
    assert batch.access_check_required_count == 1
    assert receipts == []
    assert batch.records[0].outcome == "license_not_approved"
    assert batch.records[0].durable_full_text_stored is False

    queue = CitationAccessCheckQueueService().build(
        _inventory(),
        batch,
        code_revision="abcdef0",
    )
    assert queue.record_count == 1
    assert queue.records[0].reason == "license_not_approved"
    assert queue.records[0].final_access_decision_recorded is False
