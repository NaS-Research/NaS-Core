"""Governed import and verification of explicitly licensed publisher PDFs."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import ValidationError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from nas_core.domain.appraisal import (
    FullTextAccessStatus,
    FullTextInventoryRecord,
    FullTextLicense,
    FullTextRetrievalManifest,
    FullTextRetrievalReceipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import (
    ImmutableObjectConflictError,
    canonical_json,
    sha256,
)
from nas_core.retrieval.full_text_retrieval import FullTextRetrievalError
from nas_core.storage.object_store import ObjectStore

PDF_MEDIA_TYPE = "application/pdf"
JSON_MEDIA_TYPE = "application/json"
APPROVED_PDF_LICENSES = {
    "CC-BY-2.0": "https://creativecommons.org/licenses/by/2.0/",
    "CC-BY-2.5": "https://creativecommons.org/licenses/by/2.5/",
    "CC-BY-3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
}


class LicensedPdfImportService:
    """Import a local publisher PDF only after deterministic identity/license checks."""

    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def import_pdf(
        self,
        record: FullTextInventoryRecord,
        *,
        pdf_path: Path,
        source_url: str,
        license_record: FullTextLicense,
        study_id: str,
        queue_id: str,
        progress_id: str,
        code_revision: str,
    ) -> FullTextRetrievalManifest:
        self._validate_request(source_url, license_record, code_revision)
        body = pdf_path.read_bytes()
        identity = self._parse_pdf(body)
        self._validate_identity(record, identity)
        self._validate_license(identity["text"], license_record)

        retrieved_at = self._clock()
        retrieval_identity = {
            "code_revision": code_revision,
            "full_text_sha256": sha256(body),
            "progress_id": progress_id,
            "retrieved_at": retrieved_at.isoformat(),
            "screening_id": record.screening_id,
            "source_url": source_url,
        }
        retrieval_id = sha256(canonical_json(retrieval_identity))
        prefix = f"full-text/{study_id}/{record.screening_id}/{retrieval_id}"
        full_text_key = f"{prefix}/article.pdf"
        self._put_immutable(full_text_key, body, content_type=PDF_MEDIA_TYPE)
        record_ids = [
            value
            for value in (record.pmcid, record.pmid, record.doi)
            if value is not None
        ]
        full_text_object = StoredObject(
            object_key=full_text_key,
            media_type=PDF_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
            record_ids=record_ids,
        )
        manifest = FullTextRetrievalManifest(
            retrieval_id=retrieval_id,
            study_id=study_id,
            queue_id=queue_id,
            progress_id=progress_id,
            screening_id=record.screening_id,
            pmcid=record.pmcid,
            pmid=record.pmid,
            doi=record.doi,
            title=record.title,
            source_url=source_url,
            retrieved_at=retrieved_at,
            code_revision=code_revision,
            license=license_record,
            full_text_object=full_text_object,
        )
        manifest_hash = sha256(
            canonical_json(manifest.model_dump(mode="json", exclude_none=True))
        )
        manifest = manifest.model_copy(update={"manifest_sha256": manifest_hash})
        self._put_immutable(
            self.manifest_object_key(manifest),
            canonical_json(manifest.model_dump(mode="json", exclude_none=True)),
            content_type=JSON_MEDIA_TYPE,
        )
        return manifest

    def verify(self, manifest: FullTextRetrievalManifest) -> FullTextRetrievalReceipt:
        manifest_key = self.manifest_object_key(manifest)
        stored_manifest = self._store.get_bytes(manifest_key)
        try:
            reloaded = FullTextRetrievalManifest.model_validate(json.loads(stored_manifest))
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise FullTextRetrievalError("stored full-text manifest is invalid") from error
        if reloaded != manifest:
            raise FullTextRetrievalError("stored full-text manifest differs from supplied manifest")

        expected_hash = sha256(
            canonical_json(
                manifest.model_copy(update={"manifest_sha256": None}).model_dump(
                    mode="json", exclude_none=True
                )
            )
        )
        if manifest.manifest_sha256 != expected_hash:
            raise FullTextRetrievalError("full-text manifest checksum is invalid")
        if manifest.full_text_object.media_type != PDF_MEDIA_TYPE:
            raise FullTextRetrievalError("publisher full text is not recorded as a PDF")

        body = self._store.get_bytes(manifest.full_text_object.object_key)
        if (
            len(body) != manifest.full_text_object.size_bytes
            or sha256(body) != manifest.full_text_object.sha256
        ):
            raise FullTextRetrievalError("stored full text failed size or checksum verification")
        identity = self._parse_pdf(body)
        expected = FullTextInventoryRecord(
            screening_id=manifest.screening_id,
            record_key=(
                f"pmcid:{manifest.pmcid}"
                if manifest.pmcid
                else f"pmid:{manifest.pmid}"
            ),
            title=manifest.title,
            pmcid=manifest.pmcid,
            pmid=manifest.pmid,
            doi=manifest.doi,
            access_status=FullTextAccessStatus.ACCESS_CHECK_REQUIRED,
        )
        self._validate_identity(expected, identity)
        self._validate_license(identity["text"], manifest.license)
        if manifest.scientific_conclusions_drawn:
            raise FullTextRetrievalError("retrieval manifest contains a scientific conclusion")

        return FullTextRetrievalReceipt(
            retrieval_id=manifest.retrieval_id,
            study_id=manifest.study_id,
            queue_id=manifest.queue_id,
            progress_id=manifest.progress_id,
            screening_id=manifest.screening_id,
            pmcid=manifest.pmcid,
            title=manifest.title,
            source_url=manifest.source_url,
            retrieved_at=manifest.retrieved_at,
            code_revision=manifest.code_revision,
            license=manifest.license,
            manifest_object_key=manifest_key,
            manifest_sha256=expected_hash,
            full_text_object_key=manifest.full_text_object.object_key,
            full_text_sha256=manifest.full_text_object.sha256,
            full_text_size_bytes=manifest.full_text_object.size_bytes,
            verified_at=self._clock(),
            manifest_checksum_verified=True,
            full_text_checksum_verified=True,
            article_identity_verified=True,
            license_verified=True,
        )

    @staticmethod
    def manifest_object_key(manifest: FullTextRetrievalManifest) -> str:
        return (
            f"full-text/{manifest.study_id}/{manifest.screening_id}/"
            f"{manifest.retrieval_id}/manifest.json"
        )

    @staticmethod
    def _validate_request(
        source_url: str,
        license_record: FullTextLicense,
        code_revision: str,
    ) -> None:
        parsed = urlsplit(source_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise FullTextRetrievalError("publisher source URL must use HTTPS")
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise FullTextRetrievalError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        expected_url = APPROVED_PDF_LICENSES.get(license_record.spdx_identifier)
        normalized_url = license_record.url.replace("http://", "https://").rstrip("/") + "/"
        if expected_url is None or normalized_url != expected_url:
            raise FullTextRetrievalError("publisher PDF license is not an approved CC BY license")

    @staticmethod
    def _parse_pdf(body: bytes) -> dict[str, str]:
        if not body.startswith(b"%PDF-") or b"%%EOF" not in body[-2048:]:
            raise FullTextRetrievalError("publisher full text is not a complete PDF")
        try:
            reader = PdfReader(BytesIO(body), strict=True)
            if reader.is_encrypted:
                raise FullTextRetrievalError("encrypted publisher PDFs are not accepted")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except (PdfReadError, OSError, ValueError) as error:
            raise FullTextRetrievalError("publisher full text failed PDF parsing") from error
        if not reader.pages or len(text.strip()) < 500:
            raise FullTextRetrievalError("publisher PDF contains insufficient extractable text")
        return {"text": text}

    @staticmethod
    def _validate_identity(
        record: FullTextInventoryRecord,
        identity: dict[str, str],
    ) -> None:
        normalized_text = LicensedPdfImportService._normalize(identity["text"])
        normalized_title = LicensedPdfImportService._normalize(record.title)
        if not normalized_title or normalized_title not in normalized_text:
            raise FullTextRetrievalError("publisher PDF title does not match inventory identity")
        if record.doi:
            doi = record.doi.casefold().removeprefix("https://doi.org/")
            if doi not in identity["text"].casefold():
                raise FullTextRetrievalError("publisher PDF DOI does not match inventory identity")

    @staticmethod
    def _validate_license(text: str, license_record: FullTextLicense) -> None:
        normalized_text = text.casefold().replace("http://", "https://")
        expected_url = license_record.url.replace("http://", "https://").rstrip("/") + "/"
        license_version = license_record.spdx_identifier.removeprefix("CC-BY-")
        expected_phrase = f"creative commons attribution {license_version}"
        if (
            expected_url.casefold() not in normalized_text
            or expected_phrase not in normalized_text
        ):
            raise FullTextRetrievalError("publisher PDF lacks the declared CC BY license")

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.casefold())

    def _put_immutable(self, key: str, body: bytes, *, content_type: str) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
            return
        self._store.put_bytes(key, body, content_type=content_type)
