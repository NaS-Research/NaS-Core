from datetime import UTC, datetime
from pathlib import Path

import pytest

from nas_core.domain.appraisal import FullTextInventoryRecord, FullTextLicense
from nas_core.retrieval.full_text_retrieval import FullTextRetrievalError
from nas_core.retrieval.licensed_pdf import LicensedPdfImportService
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 15, 0, tzinfo=UTC)
TEXT = """
Synthetic Licensed Publisher Study
DOI 10.1/synthetic
This work is licensed under a Creative Commons Attribution 4.0 International
License. https://creativecommons.org/licenses/by/4.0/
""" + ("Methods and results for a synthetic test fixture only. " * 20)


class FixturePdfImportService(LicensedPdfImportService):
    @staticmethod
    def _parse_pdf(body: bytes) -> dict[str, str]:
        if not body.startswith(b"%PDF-") or b"%%EOF" not in body[-2048:]:
            raise FullTextRetrievalError("publisher full text is not a complete PDF")
        return {"text": TEXT}


def _record() -> FullTextInventoryRecord:
    return FullTextInventoryRecord(
        screening_id="a" * 64,
        record_key="pmid:456",
        title="Synthetic Licensed Publisher Study.",
        pmid="456",
        doi="10.1/synthetic",
        access_status="access_check_required",
    )


def _license() -> FullTextLicense:
    return FullTextLicense(
        name="Creative Commons Attribution 4.0 International",
        spdx_identifier="CC-BY-4.0",
        url="https://creativecommons.org/licenses/by/4.0/",
        copyright_statement="© Synthetic authors 2026",
    )


def test_imports_and_independently_verifies_publisher_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "article.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nsynthetic\n%%EOF")
    store = InMemoryObjectStore()
    service = FixturePdfImportService(store=store, clock=lambda: NOW)

    manifest = service.import_pdf(
        _record(),
        pdf_path=pdf_path,
        source_url="https://publisher.example/article.pdf",
        license_record=_license(),
        study_id="NAS-BRCA-002",
        queue_id="b" * 64,
        progress_id="c" * 64,
        code_revision="f9f1f46",
    )
    receipt = service.verify(manifest)

    assert receipt.pmcid is None
    assert receipt.full_text_object_key.endswith("/article.pdf")
    assert receipt.full_text_checksum_verified is True
    assert receipt.article_identity_verified is True
    assert receipt.license_verified is True
    assert receipt.scientific_conclusions_drawn is False


def test_rejects_non_pdf_before_storage(tmp_path: Path) -> None:
    pdf_path = tmp_path / "article.pdf"
    pdf_path.write_bytes(b"not a PDF")
    service = FixturePdfImportService(
        store=InMemoryObjectStore(),
        clock=lambda: NOW,
    )

    with pytest.raises(FullTextRetrievalError, match="not a complete PDF"):
        service.import_pdf(
            _record(),
            pdf_path=pdf_path,
            source_url="https://publisher.example/article.pdf",
            license_record=_license(),
            study_id="NAS-BRCA-002",
            queue_id="b" * 64,
            progress_id="c" * 64,
            code_revision="f9f1f46",
        )


def test_rejects_license_not_printed_in_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "article.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nsynthetic\n%%EOF")

    class MissingLicenseService(FixturePdfImportService):
        @staticmethod
        def _parse_pdf(body: bytes) -> dict[str, str]:
            del body
            return {"text": TEXT.replace("Creative Commons Attribution 4.0 International", "Other")}

    with pytest.raises(FullTextRetrievalError, match="lacks the declared"):
        MissingLicenseService(store=InMemoryObjectStore()).import_pdf(
            _record(),
            pdf_path=pdf_path,
            source_url="https://publisher.example/article.pdf",
            license_record=_license(),
            study_id="NAS-BRCA-002",
            queue_id="b" * 64,
            progress_id="c" * 64,
            code_revision="f9f1f46",
        )
