"""License-enforced immutable full-text retrieval from Europe PMC."""

from __future__ import annotations

import json
import re
import ssl
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import certifi
from pydantic import ValidationError

from nas_core.domain.appraisal import (
    FullTextInventoryRecord,
    FullTextLicense,
    FullTextRetrievalManifest,
    FullTextRetrievalReceipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import (
    HTTPResponse,
    ImmutableObjectConflictError,
    RemoteResponseError,
    canonical_json,
    sha256,
)
from nas_core.storage.object_store import ObjectStore

EUROPE_PMC_FULL_TEXT_URL = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
)
XML_MEDIA_TYPE = "application/xml"
JSON_MEDIA_TYPE = "application/json"
CC_BY_4_URLS = {
    "http://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/licenses/by/4.0/",
}


class FullTextRetrievalError(RuntimeError):
    """Raised when identity, license, transport, or artifact verification fails."""


class FullTextTransport(Protocol):
    def get(self, url: str) -> HTTPResponse: ...


class UrllibFullTextTransport:
    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> HTTPResponse:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "www.ebi.ac.uk":
            raise ValueError("full-text URL must use the approved Europe PMC HTTPS host")
        request = Request(
            url,
            headers={"Accept": XML_MEDIA_TYPE, "User-Agent": "NaS-Core/0.1"},
        )
        try:
            with urlopen(  # noqa: S310
                request,
                timeout=self._timeout_seconds,
                context=self._ssl_context,
            ) as response:
                return HTTPResponse(
                    status_code=response.status,
                    headers=dict(response.headers.items()),
                    body=response.read(),
                )
        except HTTPError as error:
            return HTTPResponse(
                status_code=error.code,
                headers=dict(error.headers.items()),
                body=error.read(),
            )
        except (TimeoutError, URLError) as error:
            raise RemoteResponseError("Europe PMC full-text request failed") from error


class FullTextRetrievalService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        transport: FullTextTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._transport = transport or UrllibFullTextTransport()
        self._clock = clock or (lambda: datetime.now(UTC))

    def retrieve(
        self,
        record: FullTextInventoryRecord,
        *,
        study_id: str,
        queue_id: str,
        progress_id: str,
        code_revision: str,
    ) -> FullTextRetrievalManifest:
        if record.pmcid is None:
            raise FullTextRetrievalError("full-text retrieval requires a verified PMCID")
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise FullTextRetrievalError("code revision must be a 7-to-40 character Git SHA")
        source_url = EUROPE_PMC_FULL_TEXT_URL.format(pmcid=record.pmcid)
        response = self._transport.get(source_url)
        if response.status_code != 200 or not response.body:
            raise RemoteResponseError(
                f"Europe PMC full-text request failed with status {response.status_code}"
            )
        identity, license_record = self._parse_article(response.body)
        self._validate_identity(record, identity)
        retrieved_at = self._clock()
        retrieval_identity = {
            "code_revision": code_revision,
            "full_text_sha256": sha256(response.body),
            "progress_id": progress_id,
            "retrieved_at": retrieved_at.isoformat(),
            "screening_id": record.screening_id,
            "source_url": source_url,
        }
        retrieval_id = sha256(canonical_json(retrieval_identity))
        prefix = f"full-text/{study_id}/{record.screening_id}/{retrieval_id}"
        full_text_key = f"{prefix}/article.xml"
        self._put_immutable(full_text_key, response.body, content_type=XML_MEDIA_TYPE)
        full_text_object = StoredObject(
            object_key=full_text_key,
            media_type=XML_MEDIA_TYPE,
            size_bytes=len(response.body),
            sha256=sha256(response.body),
            record_ids=[record.pmcid],
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
        body = self._store.get_bytes(manifest.full_text_object.object_key)
        if (
            len(body) != manifest.full_text_object.size_bytes
            or sha256(body) != manifest.full_text_object.sha256
        ):
            raise FullTextRetrievalError("stored full text failed size or checksum verification")
        identity, license_record = self._parse_article(body)
        expected_identity = {
            "pmcid": manifest.pmcid,
            "pmid": manifest.pmid,
            "doi": manifest.doi,
            "title": manifest.title,
        }
        if not self._identity_matches(expected_identity, identity):
            raise FullTextRetrievalError("stored full text does not match manifest identity")
        if license_record != manifest.license:
            raise FullTextRetrievalError("stored full-text license differs from manifest")
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
    def _parse_article(body: bytes) -> tuple[dict[str, str | None], FullTextLicense]:
        try:
            root = ElementTree.fromstring(body)
        except ElementTree.ParseError as error:
            raise FullTextRetrievalError("full-text response is not valid XML") from error

        def article_id(kind: str) -> str | None:
            node = root.find(f".//article-id[@pub-id-type='{kind}']")
            return node.text.strip() if node is not None and node.text else None

        title_node = root.find(".//article-title")
        title = "".join(title_node.itertext()).strip() if title_node is not None else ""
        license_node = root.find(".//permissions/license")
        copyright_node = root.find(".//permissions/copyright-statement")
        if license_node is None or copyright_node is None:
            raise FullTextRetrievalError("article lacks explicit license metadata")
        license_url = license_node.attrib.get(
            "{http://www.w3.org/1999/xlink}href",
            "",
        )
        if not license_url:
            link = license_node.find(".//ext-link")
            if link is not None:
                license_url = link.attrib.get(
                    "{http://www.w3.org/1999/xlink}href",
                    "",
                )
        license_text = " ".join("".join(license_node.itertext()).split())
        if license_url not in CC_BY_4_URLS or "Attribution 4.0" not in license_text:
            raise FullTextRetrievalError("article license is not in the approved CC BY 4.0 set")
        copyright_text = " ".join("".join(copyright_node.itertext()).split())
        identity = {
            "pmcid": article_id("pmcid"),
            "pmid": article_id("pmid"),
            "doi": article_id("doi"),
            "title": title,
        }
        if identity["pmcid"] is None or not title:
            raise FullTextRetrievalError("article identity metadata is incomplete")
        return identity, FullTextLicense(
            name="Creative Commons Attribution 4.0 International",
            spdx_identifier="CC-BY-4.0",
            url="https://creativecommons.org/licenses/by/4.0/",
            copyright_statement=copyright_text,
        )

    @staticmethod
    def _validate_identity(
        record: FullTextInventoryRecord,
        identity: dict[str, str | None],
    ) -> None:
        expected = {
            "pmcid": record.pmcid,
            "pmid": record.pmid,
            "doi": record.doi,
            "title": record.title,
        }
        if not FullTextRetrievalService._identity_matches(expected, identity):
            raise FullTextRetrievalError("retrieved article does not match inventory identity")

    @staticmethod
    def _identity_matches(
        expected: dict[str, str | None],
        actual: dict[str, str | None],
    ) -> bool:
        for field in ("pmcid", "pmid", "doi"):
            if expected[field] != actual[field]:
                return False
        expected_title = " ".join((expected["title"] or "").split()).removesuffix(".")
        actual_title = " ".join((actual["title"] or "").split()).removesuffix(".")
        return bool(expected_title) and expected_title == actual_title

    def _put_immutable(self, key: str, body: bytes, *, content_type: str) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
            return
        self._store.put_bytes(key, body, content_type=content_type)
