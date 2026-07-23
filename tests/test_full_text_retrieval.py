from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.appraisal import FullTextInventoryRecord, FullTextRetrievalReceipt
from nas_core.ingestion.gdc import HTTPResponse
from nas_core.retrieval.full_text_retrieval import (
    FullTextRetrievalError,
    FullTextRetrievalService,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 22, 23, 0, tzinfo=UTC)
ROOT = Path(__file__).parents[1]
REAL_RECEIPT = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
    / "full-text"
    / "PMC10587090.yaml"
)
SECOND_RECEIPT = REAL_RECEIPT.with_name("PMC3275466.yaml")


def _xml(
    *,
    license_url: str = "https://creativecommons.org/licenses/by/4.0/",
    license_text: str = "Creative Commons Attribution 4.0 International License",
) -> bytes:
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
        <license-p>{license_text}</license-p>
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
        title="Synthetic licensed study.",
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


def test_retrieves_legacy_cc_by_2_full_text() -> None:
    service = FullTextRetrievalService(
        store=InMemoryObjectStore(),
        transport=FakeTransport(
            _xml(
                license_url="http://creativecommons.org/licenses/by/2.0",
                license_text="Creative Commons Attribution License 2.0",
            )
        ),
        clock=lambda: NOW,
    )

    receipt = service.verify(
        service.retrieve(
            _record(),
            study_id="NAS-BRCA-002",
            queue_id="b" * 64,
            progress_id="c" * 64,
            code_revision="f9f1f46",
        )
    )

    assert receipt.license.spdx_identifier == "CC-BY-2.0"
    assert receipt.license.url == "https://creativecommons.org/licenses/by/2.0/"


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


def test_rejects_substantive_article_identity_mismatch() -> None:
    service = FullTextRetrievalService(
        store=InMemoryObjectStore(),
        transport=FakeTransport(_xml()),
        clock=lambda: NOW,
    )

    with pytest.raises(FullTextRetrievalError, match="does not match inventory identity"):
        service.retrieve(
            _record().model_copy(update={"title": "A different study"}),
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


def test_first_checked_in_full_text_receipt_is_verified_and_non_conclusive() -> None:
    receipt = FullTextRetrievalReceipt.model_validate(yaml.safe_load(REAL_RECEIPT.read_text()))

    assert receipt.pmcid == "PMC10587090"
    assert receipt.code_revision == "42d9752"
    assert receipt.license.spdx_identifier == "CC-BY-4.0"
    assert receipt.full_text_sha256 == (
        "2ca3db6fae40accbc47d98f6b0ff4aedbdb976d8cdde7cda059d6abbf4520e2a"
    )
    assert receipt.manifest_checksum_verified is True
    assert receipt.full_text_checksum_verified is True
    assert receipt.article_identity_verified is True
    assert receipt.license_verified is True
    assert receipt.scientific_conclusions_drawn is False


def test_second_checked_in_full_text_receipt_is_verified_and_non_conclusive() -> None:
    receipt = FullTextRetrievalReceipt.model_validate(
        yaml.safe_load(SECOND_RECEIPT.read_text())
    )

    assert receipt.pmcid == "PMC3275466"
    assert receipt.code_revision == "967b94c"
    assert receipt.license.spdx_identifier == "CC-BY-2.0"
    assert receipt.full_text_sha256 == (
        "a09221f7fa1a951709ad348c5e376b963abb4291e47897d2ac8238866fb2481e"
    )
    assert receipt.manifest_checksum_verified is True
    assert receipt.full_text_checksum_verified is True
    assert receipt.article_identity_verified is True
    assert receipt.license_verified is True
    assert receipt.scientific_conclusions_drawn is False
