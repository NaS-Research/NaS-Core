"""Ephemeral, no-storage review receipts for lawfully viewable articles."""

from __future__ import annotations

import re
import ssl
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

import certifi

from nas_core.domain.appraisal import (
    FullTextContentRepresentation,
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
from nas_core.retrieval.licensed_pdf import LicensedPdfImportService

PMC_ARTICLE_URL = "https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
MEDRXIV_HOST = "www.medrxiv.org"
HTML_MEDIA_TYPE = "text/html"
PLAIN_TEXT_MEDIA_TYPE = "text/plain"
PDF_MEDIA_TYPE = "application/pdf"
XML_MEDIA_TYPE = "application/xml"
PMC_OAI_ARTICLE_URL = (
    "https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/"
    "?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:{pmc_numeric_id}"
    "&metadataPrefix=pmc"
)
APPROVED_PUBLISHER_HTML_URLS = {
    "10.1093/jnci/djr545": (
        "https://oup.silverchair-cdn.com/article-minimal/979947"
    ),
    "10.21203/rs.3.rs-3290125/v1": (
        "https://www.researchsquare.com/article/rs-3290125/v1"
    ),
}
INSTITUTIONAL_PDF_URLS = {
    "10.1007/s12094-013-1088-z": (
        "https://unclineberger.org/peroulab/wp-content/uploads/sites/1008/"
        "2013/10/July-16.pdf"
    ),
}
APPROVED_PUBLISHER_PDF_URLS = {
    "10.4143/crt.2018.342": (
        "https://www.e-crt.org/upload/pdf/crt-2018-342.pdf"
    ),
    "10.1007/s10549-023-06886-3": (
        "https://link.springer.com/content/pdf/"
        "10.1007/s10549-023-06886-3.pdf"
    ),
}
UNC_REFERER = "https://unclineberger.org/peroulab/publications/"
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)


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


class _CanonicalPublisherHtmlParser(_CitationMetaParser):
    """Extract citation identity and visible text from an allowlisted article page."""

    def __init__(self) -> None:
        super().__init__()
        self._suppressed_depth = 0
        self.text_parts: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        super().handle_starttag(tag, attrs)
        if tag.casefold() in {"script", "style", "noscript", "template"}:
            self._suppressed_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if (
            tag.casefold() in {"script", "style", "noscript", "template"}
            and self._suppressed_depth
        ):
            self._suppressed_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._suppressed_depth and data.strip():
            self.text_parts.append(data)

    def canonical_representation(self) -> tuple[bytes, str]:
        text = " ".join(" ".join(self.text_parts).split())
        canonical = canonical_json(
            {
                "citation_doi": self.metadata.get("citation_doi", ""),
                "citation_pmid": self.metadata.get("citation_pmid", ""),
                "citation_title": self.metadata.get("citation_title", ""),
                "text": text,
            }
        )
        return canonical, text


def canonicalize_pmc_oai_article(body: bytes) -> tuple[bytes, str, dict[str, str]]:
    """Return stable article XML, visible text, and identity from an OAI envelope."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError as error:
        raise ReadOnlyReviewError("PMC OAI response is not valid XML") from error
    articles = [
        element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "article"
    ]
    if len(articles) != 1:
        raise ReadOnlyReviewError("PMC OAI response must contain exactly one article")
    article = articles[0]
    article_xml = ET.tostring(article, encoding="unicode")
    canonical_text = ET.canonicalize(article_xml, strip_text=True)
    if not isinstance(canonical_text, str):
        raise ReadOnlyReviewError("PMC OAI article canonicalization failed")
    visible_text = " ".join(" ".join(article.itertext()).split())
    identity: dict[str, str] = {}
    for element in article.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        # Inline JATS markup may split one word across adjacent text nodes, as in
        # ``<underline>Pur</underline>ity``. Identity extraction must concatenate
        # those nodes before normalizing whitespace or exact titles fail closed.
        value = " ".join("".join(element.itertext()).split())
        if local_name == "article-id":
            id_type = element.attrib.get("pub-id-type", "").casefold()
            if id_type in {"pmcid", "pmid", "doi"} and value:
                identity[id_type] = value
        elif local_name == "article-title" and "title" not in identity and value:
            identity["title"] = value
    return canonical_text.encode("utf-8"), visible_text, identity


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


class UrllibInstitutionalPdfReadOnlyReviewTransport:
    """Fetch only explicitly approved institutional author-copy PDFs."""

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> HTTPResponse:
        if url not in INSTITUTIONAL_PDF_URLS.values():
            raise ValueError(
                "read-only review URL must be an approved institutional PDF"
            )
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "unclineberger.org"
            or not parsed.path.endswith(".pdf")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "institutional PDF URL failed exact HTTPS host/path validation"
            )
        request = Request(
            url,
            headers={
                "Accept": PDF_MEDIA_TYPE,
                "Referer": UNC_REFERER,
                "User-Agent": BROWSER_USER_AGENT,
            },
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
            raise RemoteResponseError(
                "institutional PDF read-only review request failed"
            ) from error


class UrllibApprovedPublisherPdfReadOnlyReviewTransport:
    """Fetch only explicitly approved official publisher/repository PDFs."""

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> HTTPResponse:
        if url not in APPROVED_PUBLISHER_PDF_URLS.values():
            raise ValueError(
                "read-only review URL must be an approved publisher PDF"
            )
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname
            not in {"dash.harvard.edu", "www.e-crt.org", "link.springer.com"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "publisher PDF URL failed exact HTTPS host/path validation"
            )
        request = Request(
            url,
            headers={"Accept": PDF_MEDIA_TYPE, "User-Agent": BROWSER_USER_AGENT},
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
            raise RemoteResponseError(
                "publisher PDF read-only review request failed"
            ) from error


class UrllibPmcOaiReadOnlyReviewTransport:
    """Fetch one exact PMC OAI article record over HTTPS."""

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> HTTPResponse:
        parsed = urlsplit(url)
        query = parse_qs(parsed.query, strict_parsing=True)
        identifiers = query.get("identifier", [])
        if (
            parsed.scheme != "https"
            or parsed.hostname != "pmc.ncbi.nlm.nih.gov"
            or parsed.path != "/api/oai/v1/mh/"
            or query.get("verb") != ["GetRecord"]
            or query.get("metadataPrefix") != ["pmc"]
            or len(identifiers) != 1
            or not re.fullmatch(
                r"oai:pubmedcentral\.nih\.gov:[0-9]+", identifiers[0]
            )
            or parsed.fragment
        ):
            raise ValueError("PMC OAI URL failed exact record validation")
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
            raise RemoteResponseError("PMC OAI review request failed") from error


class UrllibApprovedPublisherHtmlReadOnlyReviewTransport:
    """Fetch one explicitly approved official publisher HTML representation."""

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> HTTPResponse:
        if url not in APPROVED_PUBLISHER_HTML_URLS.values():
            raise ValueError("read-only review URL must be an approved publisher page")
        parsed = urlsplit(url)
        approved_location = (
            parsed.hostname == "oup.silverchair-cdn.com"
            and parsed.path.startswith("/article-minimal/")
        ) or (
            parsed.hostname == "www.researchsquare.com"
            and parsed.path == "/article/rs-3290125/v1"
        )
        if (
            parsed.scheme != "https"
            or not approved_location
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("publisher HTML URL failed exact HTTPS validation")
        request = Request(
            url,
            headers={"Accept": HTML_MEDIA_TYPE, "User-Agent": BROWSER_USER_AGENT},
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
            raise RemoteResponseError(
                "publisher HTML read-only review request failed"
            ) from error


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
        parser = _CanonicalPublisherHtmlParser()
        try:
            parser.feed(response.body.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise ReadOnlyReviewError("PMC full-text page is not UTF-8 HTML") from error
        self._verify_identity(record, parser.metadata, source_url)
        canonical_bytes, _ = parser.canonical_representation()
        accessed_at = self._clock()
        content_sha256 = sha256(canonical_bytes)
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
            content_representation=(
                FullTextContentRepresentation.CANONICAL_PMC_HTML_V1
            ),
            access_basis=access_basis,
            observed_rights=observed_rights,
            rights_url=rights_url,
            content_sha256=content_sha256,
            content_size_bytes=len(canonical_bytes),
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


class InstitutionalPdfReadOnlyReviewService:
    """Review one approved institutional author-copy PDF without retaining it."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
        pdf_parser: Callable[[bytes], dict[str, str]] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = (
            transport or UrllibInstitutionalPdfReadOnlyReviewTransport()
        )
        self._pdf_parser = pdf_parser or LicensedPdfImportService._parse_pdf  # noqa: SLF001
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
        normalized_doi = (record.doi or "").casefold()
        source_url = INSTITUTIONAL_PDF_URLS.get(normalized_doi)
        if source_url is None:
            raise ReadOnlyReviewError(
                "institutional PDF review requires an approved DOI-to-URL binding"
            )
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ReadOnlyReviewError("code revision is invalid")
        response = self._transport.get(source_url)
        if (
            response.status_code != 200
            or len(response.body) < 10_000
            or not response.body.startswith(b"%PDF-")
            or b"%%EOF" not in response.body[-2048:]
        ):
            raise ReadOnlyReviewError(
                "institutional full-text PDF is unavailable or incomplete"
            )
        try:
            identity = self._pdf_parser(response.body)
        except RuntimeError as error:
            raise ReadOnlyReviewError(
                "institutional full-text PDF failed parsing"
            ) from error
        self._verify_identity(record, identity.get("text", ""))
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
        text: str,
    ) -> None:
        normalized_text = re.sub(r"[^a-z0-9]+", "", text.casefold())
        normalized_title = re.sub(r"[^a-z0-9]+", "", record.title.casefold())
        normalized_doi = (record.doi or "").casefold()
        if (
            not normalized_title
            or normalized_title not in normalized_text
            or not normalized_doi
            or normalized_doi not in text.casefold()
        ):
            raise ReadOnlyReviewError(
                "institutional PDF identity does not match inventory"
            )


class ApprovedPublisherPdfReadOnlyReviewService:
    """Review an approved publisher/repository PDF without retaining it."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
        pdf_parser: Callable[[bytes], dict[str, str]] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = (
            transport or UrllibApprovedPublisherPdfReadOnlyReviewTransport()
        )
        self._pdf_parser = pdf_parser or LicensedPdfImportService._parse_pdf  # noqa: SLF001
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
        source_url = APPROVED_PUBLISHER_PDF_URLS.get(
            (record.doi or "").casefold()
        )
        if source_url is None:
            raise ReadOnlyReviewError(
                "publisher PDF review requires an approved DOI-to-URL binding"
            )
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ReadOnlyReviewError("code revision is invalid")
        response = self._transport.get(source_url)
        if (
            response.status_code != 200
            or len(response.body) < 10_000
            or not response.body.startswith(b"%PDF-")
            or b"%%EOF" not in response.body[-2048:]
        ):
            raise ReadOnlyReviewError(
                "publisher full-text PDF is unavailable or incomplete"
            )
        try:
            source_text = self._pdf_parser(response.body).get("text", "")
        except RuntimeError as error:
            raise ReadOnlyReviewError(
                "publisher full-text PDF failed parsing"
            ) from error
        InstitutionalPdfReadOnlyReviewService._verify_identity(  # noqa: SLF001
            record, source_text
        )
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


class PmcOaiReadOnlyReviewService:
    """Hash a canonical PMC article subtree while retaining no article content."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport or UrllibPmcOaiReadOnlyReviewTransport()
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
            raise ReadOnlyReviewError("PMC OAI review requires a verified PMCID")
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ReadOnlyReviewError("code revision is invalid")
        source_url = PMC_OAI_ARTICLE_URL.format(
            pmc_numeric_id=record.pmcid.removeprefix("PMC")
        )
        response = self._transport.get(source_url)
        if response.status_code != 200 or not 10_000 <= len(response.body) <= 20_000_000:
            raise ReadOnlyReviewError("PMC OAI article is unavailable or incomplete")
        canonical_bytes, _, identity = canonicalize_pmc_oai_article(response.body)
        self._verify_identity(record, identity)
        accessed_at = self._clock()
        content_sha256 = sha256(canonical_bytes)
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
            content_representation=(
                FullTextContentRepresentation.CANONICAL_PMC_OAI_ARTICLE_XML_V1
            ),
            access_basis=access_basis,
            observed_rights=observed_rights,
            rights_url=rights_url,
            content_sha256=content_sha256,
            content_size_bytes=len(canonical_bytes),
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
        identity: dict[str, str],
    ) -> None:
        if (
            identity.get("pmcid", "").casefold() != (record.pmcid or "").casefold()
            or identity.get("pmid") != record.pmid
            or identity.get("doi", "").casefold() != (record.doi or "").casefold()
            or normalize_article_title(identity.get("title"))
            != normalize_article_title(record.title)
        ):
            raise ReadOnlyReviewError(
                "PMC OAI article identity does not match inventory"
            )


class ApprovedPublisherHtmlReadOnlyReviewService:
    """Hash a canonical allowlisted publisher article page without retaining it."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = (
            transport or UrllibApprovedPublisherHtmlReadOnlyReviewTransport()
        )
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
        source_url = APPROVED_PUBLISHER_HTML_URLS.get(
            (record.doi or "").casefold()
        )
        if source_url is None:
            raise ReadOnlyReviewError(
                "publisher HTML review requires an approved DOI-to-URL binding"
            )
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ReadOnlyReviewError("code revision is invalid")
        response = self._transport.get(source_url)
        if response.status_code != 200 or not 10_000 <= len(response.body) <= 20_000_000:
            raise ReadOnlyReviewError(
                "publisher full-text HTML is unavailable or incomplete"
            )
        parser = _CanonicalPublisherHtmlParser()
        try:
            parser.feed(response.body.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise ReadOnlyReviewError(
                "publisher full-text HTML is not UTF-8"
            ) from error
        canonical_bytes, source_text = parser.canonical_representation()
        self._verify_identity(record, parser.metadata, source_text)
        accessed_at = self._clock()
        content_sha256 = sha256(canonical_bytes)
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
            content_representation=(
                FullTextContentRepresentation.CANONICAL_PUBLISHER_HTML_V1
            ),
            access_basis=access_basis,
            observed_rights=observed_rights,
            rights_url=rights_url,
            content_sha256=content_sha256,
            content_size_bytes=len(canonical_bytes),
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
        source_text: str,
    ) -> None:
        normalized_source = re.sub(r"[^a-z0-9]+", "", source_text.casefold())
        normalized_title = re.sub(r"[^a-z0-9]+", "", record.title.casefold())
        normalized_doi = (record.doi or "").casefold()
        metadata_title = metadata.get("citation_title")
        metadata_doi = metadata.get("citation_doi")
        metadata_pmid = metadata.get("citation_pmid")
        if (
            (metadata_title is not None and normalize_article_title(metadata_title)
             != normalize_article_title(record.title))
            or (metadata_doi is not None and metadata_doi.casefold() != normalized_doi)
            or (metadata_pmid is not None and metadata_pmid != record.pmid)
            or not normalized_title
            or normalized_title not in normalized_source
            or not normalized_doi
            or (
                metadata_doi is None
                and normalized_doi not in source_text.casefold()
            )
        ):
            raise ReadOnlyReviewError(
                "publisher HTML identity does not match inventory"
            )
