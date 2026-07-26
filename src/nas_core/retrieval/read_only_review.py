"""Ephemeral, no-storage review receipts for lawfully viewable articles."""

from __future__ import annotations

import re
import ssl
from collections.abc import Callable
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import certifi

from nas_core.domain.appraisal import (
    FullTextInventoryRecord,
    FullTextReadOnlyReviewReceipt,
    FullTextReviewAccessMode,
)
from nas_core.ingestion.gdc import (
    HTTPResponse,
    RemoteResponseError,
    canonical_json,
    sha256,
)
from nas_core.retrieval.full_text_retrieval import normalize_article_title

PMC_ARTICLE_URL = "https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
MEDRXIV_HOST = "www.medrxiv.org"
HTML_MEDIA_TYPE = "text/html"
PLAIN_TEXT_MEDIA_TYPE = "text/plain"


class ReadOnlyReviewError(RuntimeError):
    """Raised when an ephemeral article review cannot be identity verified."""


class ReadOnlyReviewTransport(Protocol):
    def get(self, url: str) -> HTTPResponse: ...


class UrllibReadOnlyReviewTransport:
    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> HTTPResponse:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "pmc.ncbi.nlm.nih.gov"
            or not parsed.path.startswith("/articles/PMC")
        ):
            raise ValueError("read-only review URL must be an approved PMC article")
        request = Request(
            url,
            headers={"Accept": HTML_MEDIA_TYPE, "User-Agent": "NaS-Core/0.1"},
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
            raise RemoteResponseError("PMC read-only review request failed") from error


class _CitationMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.metadata: dict[str, str] = {}

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.casefold() != "meta":
            return
        values = {key.casefold(): value or "" for key, value in attrs}
        name = values.get("name", "").casefold()
        if (
            name.startswith("citation_") or name == "dc.rights"
        ) and values.get("content"):
            self.metadata[name] = values["content"].strip()


class UrllibMedrxivReadOnlyReviewTransport:
    """Fetch only exact, reproducible medRxiv plain full-text pages over HTTPS."""

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> HTTPResponse:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != MEDRXIV_HOST
            or not parsed.path.startswith("/content/10.")
            or not parsed.path.endswith(".full.txt")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "read-only review URL must be an exact medRxiv plain full-text page"
            )
        request = Request(
            url,
            headers={"Accept": PLAIN_TEXT_MEDIA_TYPE, "User-Agent": "NaS-Core/0.1"},
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
            raise RemoteResponseError("medRxiv read-only review request failed") from error


class PmcReadOnlyReviewService:
    """Review a PMC page in memory and emit provenance without retaining its text."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport or UrllibReadOnlyReviewTransport()
        self._clock = clock or (lambda: datetime.now(UTC))

    def review(
        self,
        record: FullTextInventoryRecord,
        *,
        study_id: str,
        queue_id: str,
        progress_id: str,
        code_revision: str,
        access_basis: str,
        observed_rights: str,
        rights_url: str,
    ) -> FullTextReadOnlyReviewReceipt:
        if record.pmcid is None:
            raise ReadOnlyReviewError("PMC read-only review requires a verified PMCID")
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ReadOnlyReviewError("code revision is invalid")
        source_url = PMC_ARTICLE_URL.format(pmcid=record.pmcid)
        response = self._transport.get(source_url)
        if response.status_code != 200 or len(response.body) < 10_000:
            raise ReadOnlyReviewError("PMC full-text page is unavailable or incomplete")
        parser = _CitationMetaParser()
        try:
            parser.feed(response.body.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise ReadOnlyReviewError("PMC full-text page is not UTF-8 HTML") from error
        self._verify_identity(record, parser.metadata, source_url)
        accessed_at = self._clock()
        content_sha256 = sha256(response.body)
        review_id = sha256(
            canonical_json(
                {
                    "accessed_at": accessed_at.isoformat(),
                    "code_revision": code_revision,
                    "content_sha256": content_sha256,
                    "screening_id": record.screening_id,
                    "source_url": source_url,
                }
            )
        )
        return FullTextReadOnlyReviewReceipt(
            receipt_version="1.0.0",
            review_id=review_id,
            study_id=study_id,
            queue_id=queue_id,
            progress_id=progress_id,
            screening_id=record.screening_id,
            pmcid=record.pmcid,
            pmid=record.pmid,
            doi=record.doi,
            title=record.title,
            source_url=source_url,
            access_mode=FullTextReviewAccessMode.READ_ONLY_EPHEMERAL,
            access_basis=access_basis,
            observed_rights=observed_rights,
            rights_url=rights_url,
            content_sha256=content_sha256,
            content_size_bytes=len(response.body),
            accessed_at=accessed_at,
            verified_at=self._clock(),
            code_revision=code_revision,
            checksum_verified=True,
            article_identity_verified=True,
            lawful_read_access_verified=True,
            durable_full_text_stored=False,
            redistribution_authorized=False,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _verify_identity(
        record: FullTextInventoryRecord,
        metadata: dict[str, str],
        source_url: str,
    ) -> None:
        if (
            metadata.get("citation_fulltext_html_url") != source_url
            or metadata.get("citation_pmid") != record.pmid
            or metadata.get("citation_doi", "").casefold()
            != (record.doi or "").casefold()
            or normalize_article_title(metadata.get("citation_title"))
            != normalize_article_title(record.title)
        ):
            raise ReadOnlyReviewError("PMC full-text page does not match inventory identity")


class MedrxivReadOnlyReviewService:
    """Review a medRxiv preprint in memory and retain provenance only."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport or UrllibMedrxivReadOnlyReviewTransport()
        self._clock = clock or (lambda: datetime.now(UTC))

    def review(
        self,
        record: FullTextInventoryRecord,
        *,
        source_url: str,
        study_id: str,
        queue_id: str,
        progress_id: str,
        code_revision: str,
        access_basis: str,
        observed_rights: str,
        rights_url: str,
    ) -> FullTextReadOnlyReviewReceipt:
        if record.doi is None:
            raise ReadOnlyReviewError("medRxiv read-only review requires a verified DOI")
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ReadOnlyReviewError("code revision is invalid")
        parsed_url = urlsplit(source_url)
        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname != MEDRXIV_HOST
            or record.doi.casefold() not in parsed_url.path.casefold()
            or not re.search(r"v[0-9]+\.full\.txt$", parsed_url.path)
        ):
            raise ReadOnlyReviewError(
                "medRxiv source URL must bind the inventory DOI to an exact version"
            )
        response = self._transport.get(source_url)
        if response.status_code != 200 or len(response.body) < 10_000:
            raise ReadOnlyReviewError(
                "medRxiv full-text page is unavailable or incomplete"
            )
        try:
            full_text = response.body.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ReadOnlyReviewError(
                "medRxiv plain full text is not UTF-8"
            ) from error
        self._verify_identity_and_rights(record, full_text)
        accessed_at = self._clock()
        content_sha256 = sha256(response.body)
        review_id = sha256(
            canonical_json(
                {
                    "accessed_at": accessed_at.isoformat(),
                    "code_revision": code_revision,
                    "content_sha256": content_sha256,
                    "screening_id": record.screening_id,
                    "source_url": source_url,
                }
            )
        )
        return FullTextReadOnlyReviewReceipt(
            receipt_version="1.0.0",
            review_id=review_id,
            study_id=study_id,
            queue_id=queue_id,
            progress_id=progress_id,
            screening_id=record.screening_id,
            pmcid=record.pmcid,
            pmid=record.pmid,
            doi=record.doi,
            title=record.title,
            source_url=source_url,
            access_mode=FullTextReviewAccessMode.READ_ONLY_EPHEMERAL,
            access_basis=access_basis,
            observed_rights=observed_rights,
            rights_url=rights_url,
            content_sha256=content_sha256,
            content_size_bytes=len(response.body),
            accessed_at=accessed_at,
            verified_at=self._clock(),
            code_revision=code_revision,
            checksum_verified=True,
            article_identity_verified=True,
            lawful_read_access_verified=True,
            durable_full_text_stored=False,
            redistribution_authorized=False,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _verify_identity_and_rights(
        record: FullTextInventoryRecord,
        full_text: str,
    ) -> None:
        first_line = next(
            (line.strip() for line in full_text.splitlines() if line.strip()),
            "",
        )
        if (
            normalize_article_title(first_line)
            != normalize_article_title(record.title)
            or "cc by-nc 4.0" not in full_text.casefold()
        ):
            raise ReadOnlyReviewError(
                "medRxiv full-text page identity or rights do not match inventory"
            )
