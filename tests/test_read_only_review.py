from datetime import UTC, datetime

import pytest

from nas_core.domain.appraisal import FullTextInventoryRecord
from nas_core.ingestion.gdc import HTTPResponse
from nas_core.retrieval.read_only_review import (
    PmcReadOnlyReviewService,
    ReadOnlyReviewError,
)

NOW = datetime(2026, 7, 25, 23, 0, tzinfo=UTC)


def _html(*, title: str = "Synthetic single-sample study") -> bytes:
    body = f"""<!doctype html>
<html><head>
<meta name="citation_title" content="{title}">
<meta name="citation_doi" content="10.1/synthetic">
<meta name="citation_pmid" content="456">
<meta name="citation_fulltext_html_url"
 content="https://pmc.ncbi.nlm.nih.gov/articles/PMC123/">
</head><body><main><article>{"full text " * 1200}</article></main></body></html>"""
    return body.encode()


class FakeTransport:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def get(self, url: str) -> HTTPResponse:
        del url
        return HTTPResponse(status_code=200, headers={}, body=self.body)


def _record() -> FullTextInventoryRecord:
    return FullTextInventoryRecord(
        screening_id="a" * 64,
        record_key="MED:456",
        title="Synthetic single-sample study.",
        pmid="456",
        pmcid="PMC123",
        doi="10.1/synthetic",
        access_status="repository_candidate",
    )


def test_pmc_review_emits_verified_no_storage_receipt() -> None:
    service = PmcReadOnlyReviewService(
        transport=FakeTransport(_html()),
        clock=lambda: NOW,
    )

    receipt = service.review(
        _record(),
        study_id="NAS-BRCA-002",
        queue_id="b" * 64,
        progress_id="c" * 64,
        code_revision="abcdef1",
        access_basis="Lawfully viewable PMC article; ephemeral review only.",
        observed_rights="All rights reserved.",
        rights_url="https://pmc.ncbi.nlm.nih.gov/about/copyright/",
    )

    assert receipt.pmcid == "PMC123"
    assert receipt.checksum_verified
    assert receipt.article_identity_verified
    assert receipt.lawful_read_access_verified
    assert receipt.durable_full_text_stored is False
    assert receipt.redistribution_authorized is False


def test_pmc_review_rejects_lexically_different_title() -> None:
    service = PmcReadOnlyReviewService(
        transport=FakeTransport(_html(title="Different study")),
        clock=lambda: NOW,
    )

    with pytest.raises(ReadOnlyReviewError, match="identity"):
        service.review(
            _record(),
            study_id="NAS-BRCA-002",
            queue_id="b" * 64,
            progress_id="c" * 64,
            code_revision="abcdef1",
            access_basis="Lawfully viewable PMC article; ephemeral review only.",
            observed_rights="All rights reserved.",
            rights_url="https://pmc.ncbi.nlm.nih.gov/about/copyright/",
        )
