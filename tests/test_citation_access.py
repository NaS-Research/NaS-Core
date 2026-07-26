from datetime import UTC, datetime
from pathlib import Path

import yaml

from nas_core.domain.appraisal import (
    FullTextAppraisalProgress,
    FullTextInventory,
    FullTextInventoryRecord,
)
from nas_core.domain.citation_access import (
    load_citation_access_check_queue,
    load_repository_access_batch_receipt,
)
from nas_core.ingestion.gdc import HTTPResponse
from nas_core.retrieval.citation_access import (
    CitationAccessCheckQueueService,
    CitationRepositoryAccessService,
)
from nas_core.retrieval.full_text_retrieval import FullTextRetrievalService
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 20, 0, tzinfo=UTC)
ROOT = Path(__file__).parents[1]
CITATION_FULL_TEXT = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
    / "citation-full-text"
)


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


def test_identity_matching_allows_only_bounded_dash_typography() -> None:
    expected = {
        "pmcid": "PMC123",
        "pmid": "456",
        "doi": "10.1/synthetic",
        "title": "Feature-specific mean-variance model.",
    }
    typographic_dash = {
        **expected,
        "title": "Feature–specific mean—variance model",
    }
    lexical_change = {
        **expected,
        "title": "Feature-specific mean-variance classifier",
    }

    assert FullTextRetrievalService._identity_matches(expected, typographic_dash)
    assert not FullTextRetrievalService._identity_matches(expected, lexical_change)


def test_identity_matching_still_requires_exact_primary_identifiers() -> None:
    expected = {
        "pmcid": "PMC123",
        "pmid": "456",
        "doi": "10.1/synthetic",
        "title": "Feature-specific mean-variance model.",
    }

    for field, changed in (
        ("pmcid", "PMC999"),
        ("pmid", "999"),
        ("doi", "10.1/different"),
    ):
        actual = {**expected, field: changed}
        assert not FullTextRetrievalService._identity_matches(expected, actual)


def test_checked_in_repository_batch_and_access_queue_reconcile() -> None:
    batch = load_repository_access_batch_receipt(
        CITATION_FULL_TEXT / "repository-access-batch-v1.0.0.yaml"
    )
    queue = load_citation_access_check_queue(
        CITATION_FULL_TEXT / "access-check-queue-v1.0.0.yaml"
    )

    assert batch.repository_candidate_count == 23
    assert batch.retrieved_count == 13
    assert batch.access_check_required_count == 10
    assert queue.record_count == 16
    assert queue.repository_batch_id == batch.batch_id
    assert sum(item.reason == "no_repository_identifier" for item in queue.records) == 6
    assert queue.final_access_decisions_recorded == 0

    progress = FullTextAppraisalProgress.model_validate(
        yaml.safe_load(
            (
                CITATION_FULL_TEXT.parent
                / "citation_appraisal_progress_v1.0.0.yaml"
            ).read_text(encoding="utf-8")
        )
    )
    assert progress.full_texts_retrieved == 15
    assert progress.appraisals_completed == 3
    assert progress.context_only_count == 3
    assert sum(item.status == "ready_for_appraisal" for item in progress.records) == 12
    assert sum(item.status == "awaiting_full_text" for item in progress.records) == 14
