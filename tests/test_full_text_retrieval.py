from datetime import UTC, datetime

import pytest

from nas_core.domain.appraisal import FullTextInventoryRecord
from nas_core.ingestion.gdc import HTTPResponse
from nas_core.retrieval.full_text_retrieval import (
    FullTextRetrievalError,
    FullTextRetrievalService,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 22, 23, 0, tzinfo=UTC)


def _xml(*, license_url: str = "https://creativecommons.org/licenses/by/4.0/") -> bytes:
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
  <body><sec><title>Methods</title><p>Synthetic fixture only.</p></sec></body>
</article>""".encode()


class FakeTransport:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def get(self, url: str) -> HTTPResponse:
        del url
        return HTTPResponse(status_code=200, headers={}, body=self.body)


def _record() -> FullTextInventoryRecord:
    return FullTextInventoryRecord(
        screening_id="a" * 64,
        record_key="pmid:456",
        title="Synthetic licensed study",
        pmid="456",
        pmcid="PMC123",
        doi="10.1/synthetic",
        access_status="repository_candidate",
    )


def test_retrieves_and_independently_verifies_cc_by_full_text() -> None:
    store = InMemoryObjectStore()
    service = FullTextRetrievalService(
        store=store,
        transport=FakeTransport(_xml()),
        clock=lambda: NOW,
    )

    manifest = service.retrieve(
        _record(),
        study_id="NAS-BRCA-002",
        queue_id="b" * 64,
        progress_id="c" * 64,
        code_revision="f9f1f46",
    )
    receipt = service.verify(manifest)

    assert receipt.license.spdx_identifier == "CC-BY-4.0"
    assert receipt.full_text_checksum_verified is True
    assert receipt.article_identity_verified is True
    assert receipt.license_verified is True
    assert receipt.scientific_conclusions_drawn is False


def test_rejects_article_without_approved_license() -> None:
    service = FullTextRetrievalService(
        store=InMemoryObjectStore(),
        transport=FakeTransport(_xml(license_url="https://example.org/restricted")),
        clock=lambda: NOW,
    )

    with pytest.raises(FullTextRetrievalError, match="not in the approved"):
        service.retrieve(
            _record(),
            study_id="NAS-BRCA-002",
            queue_id="b" * 64,
            progress_id="c" * 64,
            code_revision="f9f1f46",
        )


def test_verification_detects_tampered_full_text() -> None:
    store = InMemoryObjectStore()
    service = FullTextRetrievalService(
        store=store,
        transport=FakeTransport(_xml()),
        clock=lambda: NOW,
    )
    manifest = service.retrieve(
        _record(),
        study_id="NAS-BRCA-002",
        queue_id="b" * 64,
        progress_id="c" * 64,
        code_revision="f9f1f46",
    )
    store.put_bytes(
        manifest.full_text_object.object_key,
        b"tampered",
        content_type="application/xml",
    )

    with pytest.raises(FullTextRetrievalError, match="checksum"):
        service.verify(manifest)
