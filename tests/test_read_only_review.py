from datetime import UTC, datetime

import pytest

from nas_core.domain.appraisal import FullTextInventoryRecord
from nas_core.ingestion.gdc import HTTPResponse
from nas_core.retrieval.read_only_review import (
    APPROVED_PUBLISHER_PDF_URLS,
    ApprovedPublisherPdfReadOnlyReviewService,
    InstitutionalPdfReadOnlyReviewService,
    MedrxivReadOnlyReviewService,
    PmcReadOnlyReviewService,
    ReadOnlyReviewError,
)

NOW = datetime(2026, 7, 25, 23, 0, tzinfo=UTC)


def _html(
    *,
    title: str = "Synthetic single-sample study",
    pdf_url: str = (
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC123/pdf/synthetic.pdf"
    ),
) -> bytes:
    body = f"""<!doctype html>
<html><head>
<meta name="citation_title" content="{title}">
<meta name="citation_doi" content="10.1/synthetic">
<meta name="citation_pmid" content="456">
<meta name="citation_fulltext_html_url"
 content="https://pmc.ncbi.nlm.nih.gov/articles/PMC123/">
<meta name="citation_pdf_url" content="{pdf_url}">
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


def _medrxiv_html(
    *,
    title: str = "Synthetic® preprint study",
    rights: str = (
        "© 2026, Posted by openRxiv. This pre-print is available under "
        "CC BY-NC 4.0."
    ),
) -> bytes:
    body = f"""{title}
===========================

{"full text " * 1200}

{rights}
"""
    return body.encode()


def _medrxiv_record() -> FullTextInventoryRecord:
    return FullTextInventoryRecord(
        screening_id="d" * 64,
        record_key="PPR:PPR123",
        title="Synthetic  <sup>®</sup>  preprint study.",
        doi="10.1234/2026.01.01.12345678",
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


def test_medrxiv_review_emits_verified_no_storage_receipt() -> None:
    service = MedrxivReadOnlyReviewService(
        transport=FakeTransport(_medrxiv_html()),
        clock=lambda: NOW,
    )

    receipt = service.review(
        _medrxiv_record(),
        source_url=(
            "https://www.medrxiv.org/content/"
            "10.1234/2026.01.01.12345678v2.full.txt"
        ),
        study_id="NAS-BRCA-002",
        queue_id="b" * 64,
        progress_id="c" * 64,
        code_revision="abcdef1",
        access_basis="Lawfully viewable medRxiv preprint; ephemeral review only.",
        observed_rights="CC BY-NC 4.0; durable storage not approved.",
        rights_url="https://creativecommons.org/licenses/by-nc/4.0/",
    )

    assert receipt.pmcid is None
    assert receipt.doi == "10.1234/2026.01.01.12345678"
    assert receipt.checksum_verified
    assert receipt.article_identity_verified
    assert receipt.lawful_read_access_verified
    assert receipt.durable_full_text_stored is False
    assert receipt.redistribution_authorized is False


@pytest.mark.parametrize(
    ("source_url", "body", "error"),
    [
        (
            "https://example.org/content/10.1234/2026.01.01.12345678v2.full.txt",
            _medrxiv_html(),
            "source URL",
        ),
        (
            "https://www.medrxiv.org/content/10.1234/differentv2.full.txt",
            _medrxiv_html(),
            "source URL",
        ),
        (
            "https://www.medrxiv.org/content/"
            "10.1234/2026.01.01.12345678v2.full.txt",
            _medrxiv_html(rights="All rights reserved."),
            "identity or rights",
        ),
    ],
)
def test_medrxiv_review_rejects_invalid_source_or_rights(
    source_url: str,
    body: bytes,
    error: str,
) -> None:
    service = MedrxivReadOnlyReviewService(
        transport=FakeTransport(body),
        clock=lambda: NOW,
    )

    with pytest.raises(ReadOnlyReviewError, match=error):
        service.review(
            _medrxiv_record(),
            source_url=source_url,
            study_id="NAS-BRCA-002",
            queue_id="b" * 64,
            progress_id="c" * 64,
            code_revision="abcdef1",
            access_basis="Lawfully viewable medRxiv preprint; ephemeral review only.",
            observed_rights="CC BY-NC 4.0; durable storage not approved.",
            rights_url="https://creativecommons.org/licenses/by-nc/4.0/",
        )


def _institutional_record() -> FullTextInventoryRecord:
    return FullTextInventoryRecord(
        screening_id="e" * 64,
        record_key="MED:23907291",
        title=(
            "Assignment of tumor subtype by genomic testing and pathologic-based "
            "approximations: implications on patient's management and therapy "
            "selection."
        ),
        pmid="23907291",
        doi="10.1007/s12094-013-1088-z",
        access_status="access_check_required",
    )


def _institutional_pdf_text() -> str:
    return (
        "Assignment of tumor subtype by genomic testing and pathologic-based "
        "approximations: implications on patient's management and therapy selection. "
        "DOI 10.1007/s12094-013-1088-z "
        + ("Methods and results. " * 100)
    )


def test_institutional_pdf_review_emits_verified_no_storage_receipt() -> None:
    body = b"%PDF-1.7\n" + (b"synthetic " * 1200) + b"\n%%EOF"
    service = InstitutionalPdfReadOnlyReviewService(
        transport=FakeTransport(body),
        pdf_parser=lambda value: {"text": _institutional_pdf_text()},
        clock=lambda: NOW,
    )

    receipt = service.review(
        _institutional_record(),
        study_id="NAS-BRCA-002",
        queue_id="b" * 64,
        progress_id="c" * 64,
        code_revision="abcdef1",
        access_basis="Public institutional author copy; ephemeral review only.",
        observed_rights="Publisher copyright; no reuse license verified.",
        rights_url="https://link.springer.com/article/10.1007/s12094-013-1088-z",
    )

    assert receipt.pmid == "23907291"
    assert receipt.doi == "10.1007/s12094-013-1088-z"
    assert receipt.content_size_bytes == len(body)
    assert receipt.checksum_verified
    assert receipt.article_identity_verified
    assert receipt.lawful_read_access_verified
    assert receipt.durable_full_text_stored is False


def test_institutional_pdf_review_rejects_wrong_identity() -> None:
    body = b"%PDF-1.7\n" + (b"synthetic " * 1200) + b"\n%%EOF"
    service = InstitutionalPdfReadOnlyReviewService(
        transport=FakeTransport(body),
        pdf_parser=lambda value: {
            "text": "Different title. DOI 10.1007/s12094-013-1088-z"
        },
        clock=lambda: NOW,
    )

    with pytest.raises(ReadOnlyReviewError, match="identity"):
        service.review(
            _institutional_record(),
            study_id="NAS-BRCA-002",
            queue_id="b" * 64,
            progress_id="c" * 64,
            code_revision="abcdef1",
            access_basis="Public institutional author copy; ephemeral review only.",
            observed_rights="Publisher copyright; no reuse license verified.",
            rights_url="https://link.springer.com/article/10.1007/s12094-013-1088-z",
        )


def _publisher_record() -> FullTextInventoryRecord:
    return FullTextInventoryRecord(
        screening_id="f" * 64,
        record_key="MED:22262870",
        title="A three-gene model to robustly identify breast cancer molecular subtypes.",
        pmid="22262870",
        pmcid="PMC3283537",
        doi="10.1093/jnci/djr545",
        access_status="access_check_required",
    )


def _publisher_pdf_text() -> str:
    return (
        "A three-gene model to robustly identify breast cancer molecular subtypes. "
        "DOI 10.1093/jnci/djr545 "
        + ("Methods and results. " * 100)
    )


def test_publisher_pdf_review_emits_verified_no_storage_receipt() -> None:
    body = b"%PDF-1.7\n" + (b"synthetic " * 1200) + b"\n%%EOF"
    service = ApprovedPublisherPdfReadOnlyReviewService(
        transport=FakeTransport(body),
        pdf_parser=lambda value: {"text": _publisher_pdf_text()},
        clock=lambda: NOW,
    )

    receipt = service.review(
        _publisher_record(),
        study_id="NAS-BRCA-002",
        queue_id="b" * 64,
        progress_id="c" * 64,
        code_revision="abcdef1",
        access_basis="Official repository PDF; zero article bytes retained.",
        observed_rights="CC BY-NC 3.0.",
        rights_url="https://creativecommons.org/licenses/by-nc/3.0/",
    )

    assert receipt.source_url == APPROVED_PUBLISHER_PDF_URLS[
        "10.1093/jnci/djr545"
    ]
    assert receipt.content_size_bytes == len(body)
    assert receipt.checksum_verified
    assert receipt.article_identity_verified
    assert receipt.durable_full_text_stored is False


def test_publisher_pdf_review_rejects_unapproved_doi() -> None:
    service = ApprovedPublisherPdfReadOnlyReviewService(
        transport=FakeTransport(b"unused"),
        pdf_parser=lambda value: {"text": _publisher_pdf_text()},
        clock=lambda: NOW,
    )

    with pytest.raises(ReadOnlyReviewError, match="approved DOI"):
        service.review(
            _record(),
            study_id="NAS-BRCA-002",
            queue_id="b" * 64,
            progress_id="c" * 64,
            code_revision="abcdef1",
            access_basis="Ephemeral review only.",
            observed_rights="All rights reserved.",
            rights_url="https://example.org/rights",
        )
