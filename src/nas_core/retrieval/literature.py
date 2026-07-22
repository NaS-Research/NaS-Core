"""Governed, reproducible PubMed and Europe PMC search capture."""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

import certifi

from nas_core.domain.discovery import LiteratureSearchStrategy, PhaseZeroPlan
from nas_core.domain.literature import (
    BibliographicRecord,
    LiteratureRequest,
    LiteratureSearchSnapshot,
    SourceSearchResult,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.governance.policy import DataAction, GovernancePolicy
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import (
    HTTPResponse,
    ImmutableObjectConflictError,
    RemoteResponseError,
    canonical_json,
    sha256,
)
from nas_core.storage.object_store import ObjectStore

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EUROPE_PMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ALLOWED_HOSTS = frozenset({"eutils.ncbi.nlm.nih.gov", "www.ebi.ac.uk"})
JSON_MEDIA_TYPE = "application/json"
PUBMED_SUMMARY_BATCH_SIZE = 100
EUROPE_PMC_PAGE_SIZE = 100


def pubmed_summary_batches(ids: list[str]) -> list[list[str]]:
    """Bound GET request size so PMID lists do not exceed server URI limits."""

    return [
        ids[start : start + PUBMED_SUMMARY_BATCH_SIZE]
        for start in range(0, len(ids), PUBMED_SUMMARY_BATCH_SIZE)
    ]


class LiteratureTransport(Protocol):
    def get(self, url: str, parameters: Mapping[str, str]) -> HTTPResponse: ...


class UrllibLiteratureTransport:
    def __init__(
        self,
        *,
        timeout_seconds: float = 60.0,
        minimum_request_interval_seconds: float = 0.34,
        maximum_attempts: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        if minimum_request_interval_seconds < 0.34:
            raise ValueError("NCBI-compatible request interval must be at least 0.34 seconds")
        if maximum_attempts < 1:
            raise ValueError("maximum_attempts must be positive")
        self._timeout_seconds = timeout_seconds
        self._minimum_request_interval_seconds = minimum_request_interval_seconds
        self._maximum_attempts = maximum_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())
        self._last_request_at: float | None = None

    def get(self, url: str, parameters: Mapping[str, str]) -> HTTPResponse:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError("literature API URL must use an approved HTTPS host")
        request = Request(
            f"{url}?{urlencode(parameters)}",
            headers={"Accept": JSON_MEDIA_TYPE, "User-Agent": "NaS-Core/0.1"},
        )
        for attempt in range(self._maximum_attempts):
            self._pace_request()
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
                if error.code not in {429, 500, 502, 503, 504}:
                    return HTTPResponse(
                        status_code=error.code,
                        headers=dict(error.headers.items()),
                        body=error.read(),
                    )
                last_error: Exception = error
            except (TimeoutError, URLError) as error:
                last_error = error
            if attempt + 1 < self._maximum_attempts:
                time.sleep(self._retry_backoff_seconds * (2**attempt))
        raise RemoteResponseError(
            f"literature API request failed after {self._maximum_attempts} attempts"
        ) from last_error

    def _pace_request(self) -> None:
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            time.sleep(max(0.0, self._minimum_request_interval_seconds - elapsed))
        self._last_request_at = time.monotonic()


@dataclass(frozen=True, slots=True)
class _CapturedSource:
    result: SourceSearchResult
    requests: list[LiteratureRequest]
    raw_bodies: list[bytes]
    records: list[BibliographicRecord]


class LiteratureSearchService:
    """Capture authorized searches and store immutable raw and normalized records."""

    def __init__(
        self,
        *,
        store: ObjectStore,
        registry: SourceRegistry,
        transport: LiteratureTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        page_size: int = 500,
        maximum_source_records: int = 5000,
    ) -> None:
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000")
        if maximum_source_records < 1:
            raise ValueError("maximum_source_records must be positive")
        self._store = store
        self._registry = registry
        self._transport = transport or UrllibLiteratureTransport()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._page_size = page_size
        self._maximum_source_records = maximum_source_records

    def capture(
        self,
        plan: PhaseZeroPlan,
        strategy: LiteratureSearchStrategy,
        *,
        contact_email: str,
    ) -> LiteratureSearchSnapshot:
        self._authorize(plan, strategy, contact_email)
        executed_at = self._clock()
        source_queries = self._source_queries(strategy)
        pubmed = self._capture_pubmed(source_queries["pubmed"], contact_email)
        europe = self._capture_europe_pmc(source_queries["europe-pmc"], contact_email)
        captured = [pubmed, europe]
        records, duplicate_count = self._deduplicate(
            [record for source in captured for record in source.records]
        )

        identity = {
            "study_id": plan.study_id,
            "question_id": plan.question_id,
            "question_version": plan.question_version,
            "strategy_version": strategy.strategy_version,
            "executed_at": executed_at.isoformat(),
            "requests": [
                request.model_dump(mode="json")
                for source in captured
                for request in source.requests
            ],
            "raw_sha256": [sha256(body) for source in captured for body in source.raw_bodies],
        }
        execution_id = sha256(canonical_json(identity))
        prefix = f"literature/{plan.study_id}/{execution_id}"

        source_results: list[SourceSearchResult] = []
        raw_index = 0
        for captured_source in captured:
            objects: list[StoredObject] = []
            for body in captured_source.raw_bodies:
                raw_index += 1
                key = f"{prefix}/raw/{raw_index:05d}.json"
                self._put_immutable(key, body)
                objects.append(self._stored_object(key, body))
            source_results.append(
                captured_source.result.model_copy(update={"raw_objects": objects})
            )

        normalized_bytes = canonical_json(
            [record.model_dump(mode="json", exclude_none=True) for record in records]
        )
        normalized_key = f"{prefix}/normalized-records.json"
        self._put_immutable(normalized_key, normalized_bytes)
        normalized_object = self._stored_object(normalized_key, normalized_bytes)
        requests = [request for source in captured for request in source.requests]
        snapshot = LiteratureSearchSnapshot(
            execution_id=execution_id,
            study_id=plan.study_id,
            question_id=plan.question_id,
            question_version=plan.question_version,
            strategy_version=strategy.strategy_version,
            executed_at=executed_at,
            contact_email_sha256=hashlib.sha256(contact_email.encode()).hexdigest(),
            requests=requests,
            source_results=source_results,
            normalized_records_object=normalized_object,
            unique_record_count=len(records),
            duplicate_record_count=duplicate_count,
        )
        unhashed = canonical_json(snapshot.model_dump(mode="json", exclude_none=True))
        snapshot = snapshot.model_copy(update={"manifest_sha256": sha256(unhashed)})
        manifest_bytes = canonical_json(snapshot.model_dump(mode="json", exclude_none=True))
        self._put_immutable(f"{prefix}/manifest.json", manifest_bytes)
        return snapshot

    def preview_counts(
        self,
        plan: PhaseZeroPlan,
        strategy: LiteratureSearchStrategy,
        *,
        contact_email: str,
    ) -> dict[str, int]:
        """Contact each source once to assess corpus size without storing records."""

        self._authorize(plan, strategy, contact_email)
        queries = self._source_queries(strategy)
        pubmed_params = {
            "db": "pubmed",
            "term": queries["pubmed"],
            "retmode": "json",
            "retmax": "0",
            "tool": "nas_core",
            "email": contact_email,
        }
        pubmed_payload = self._json(
            self._checked(self._transport.get(PUBMED_SEARCH_URL, pubmed_params), "PubMed").body,
            "PubMed count preview",
        )
        search_result = pubmed_payload.get("esearchresult")
        if not isinstance(search_result, dict):
            raise RemoteResponseError("PubMed count preview is missing esearchresult")
        try:
            pubmed_count = int(str(search_result["count"]))
        except (KeyError, TypeError, ValueError) as error:
            raise RemoteResponseError("PubMed count preview has an invalid count") from error

        europe_params = {
            "query": queries["europe-pmc"],
            "format": "json",
            "resultType": "idlist",
            "pageSize": "1",
            "cursorMark": "*",
            "email": contact_email,
        }
        europe_payload = self._json(
            self._checked(
                self._transport.get(EUROPE_PMC_SEARCH_URL, europe_params), "Europe PMC"
            ).body,
            "Europe PMC count preview",
        )
        europe_count = europe_payload.get("hitCount")
        if not isinstance(europe_count, int):
            raise RemoteResponseError("Europe PMC count preview has an invalid hitCount")
        return {"pubmed": pubmed_count, "europe-pmc": europe_count}

    def _authorize(
        self,
        plan: PhaseZeroPlan,
        strategy: LiteratureSearchStrategy,
        contact_email: str,
    ) -> None:
        if not strategy.retrieval_authorized or strategy.status.value != "locked":
            raise PermissionError("a locked, retrieval-authorized search strategy is required")
        if plan.authorization is None or plan.authorization.decision.value != "approved":
            raise PermissionError("founder Phase 0 authorization is required")
        if "@" not in contact_email or contact_email.startswith("@"):
            raise ValueError("a valid contact email is required by the literature APIs")

        for source in strategy.sources:
            registration = self._registry.get(source.source_id)
            policy = GovernancePolicy()
            policy.authorize(
                registration,
                DataAction.INGEST,
                actor_role="researcher",
                purpose="evidence-synthesis",
            )
            policy.authorize(
                registration,
                DataAction.STORE,
                actor_role="researcher",
                purpose="evidence-synthesis",
            )

    @staticmethod
    def _source_queries(strategy: LiteratureSearchStrategy) -> dict[str, str]:
        source_queries = {source.source_id: source.query for source in strategy.sources}
        if set(source_queries) != {"pubmed", "europe-pmc"}:
            raise ValueError("the current literature runner requires PubMed and Europe PMC")
        return source_queries

    def _capture_pubmed(self, query: str, contact_email: str) -> _CapturedSource:
        requests: list[LiteratureRequest] = []
        bodies: list[bytes] = []
        ids: list[str] = []
        total: int | None = None
        offset = 0
        while total is None or offset < total:
            params = {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": str(self._page_size),
                "retstart": str(offset),
                "sort": "pub date",
                "tool": "nas_core",
                "email": contact_email,
            }
            response = self._checked(self._transport.get(PUBMED_SEARCH_URL, params), "PubMed")
            payload = self._json(response.body, "PubMed search")
            result = payload.get("esearchresult")
            if not isinstance(result, dict):
                raise RemoteResponseError("PubMed response is missing esearchresult")
            try:
                page_ids = [str(value) for value in cast(list[object], result["idlist"])]
                page_total = int(str(result["count"]))
            except (KeyError, TypeError, ValueError) as error:
                raise RemoteResponseError("PubMed response has invalid count or IDs") from error
            if page_total > 9999:
                raise RemoteResponseError("PubMed search exceeds 9,999 records; partition by date")
            if page_total > self._maximum_source_records:
                raise RemoteResponseError(
                    f"PubMed search returned {page_total} records; refine the locked strategy"
                )
            total = page_total if total is None else total
            if page_total != total:
                raise RemoteResponseError("PubMed result count changed during retrieval")
            requests.append(self._request("pubmed", PUBMED_SEARCH_URL, params))
            bodies.append(response.body)
            ids.extend(page_ids)
            if not page_ids:
                break
            offset += len(page_ids)

        records: list[BibliographicRecord] = []
        for batch in pubmed_summary_batches(ids):
            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "json",
                "version": "2.0",
                "tool": "nas_core",
                "email": contact_email,
            }
            response = self._checked(self._transport.get(PUBMED_SUMMARY_URL, params), "PubMed")
            payload = self._json(response.body, "PubMed summary")
            records.extend(self._parse_pubmed_summaries(payload, batch))
            requests.append(self._request("pubmed", PUBMED_SUMMARY_URL, params))
            bodies.append(response.body)
        result = SourceSearchResult(
            source_id="pubmed",
            query=query,
            reported_result_count=total or 0,
            retrieved_record_count=len(records),
            request_count=len(requests),
            raw_objects=[self._placeholder_object()],
        )
        return _CapturedSource(result, requests, bodies, records)

    def _capture_europe_pmc(self, query: str, contact_email: str) -> _CapturedSource:
        requests: list[LiteratureRequest] = []
        bodies: list[bytes] = []
        records: list[BibliographicRecord] = []
        cursor = "*"
        total: int | None = None
        while total is None or len(records) < total:
            params = {
                "query": query,
                "format": "json",
                "resultType": "core",
                "pageSize": str(min(self._page_size, EUROPE_PMC_PAGE_SIZE)),
                "cursorMark": cursor,
                "email": contact_email,
            }
            response = self._checked(
                self._transport.get(EUROPE_PMC_SEARCH_URL, params), "Europe PMC"
            )
            payload = self._json(response.body, "Europe PMC search")
            hit_count = payload.get("hitCount")
            result_list = payload.get("resultList")
            if not isinstance(hit_count, int) or not isinstance(result_list, dict):
                raise RemoteResponseError("Europe PMC response is missing hitCount or resultList")
            page = result_list.get("result")
            if not isinstance(page, list):
                raise RemoteResponseError("Europe PMC response has an invalid result page")
            total = hit_count if total is None else total
            if hit_count > self._maximum_source_records:
                raise RemoteResponseError(
                    f"Europe PMC search returned {hit_count} records; refine the locked strategy"
                )
            if hit_count != total:
                raise RemoteResponseError("Europe PMC result count changed during retrieval")
            page_records = [
                self._parse_europe_record(item) for item in page if isinstance(item, dict)
            ]
            requests.append(self._request("europe-pmc", EUROPE_PMC_SEARCH_URL, params))
            bodies.append(response.body)
            records.extend(page_records)
            if not page:
                break
            next_cursor = payload.get("nextCursorMark")
            if not isinstance(next_cursor, str) or next_cursor == cursor:
                if len(records) < total:
                    raise RemoteResponseError("Europe PMC pagination did not advance")
                break
            cursor = next_cursor
        result = SourceSearchResult(
            source_id="europe-pmc",
            query=query,
            reported_result_count=total or 0,
            retrieved_record_count=len(records),
            request_count=len(requests),
            raw_objects=[self._placeholder_object()],
        )
        return _CapturedSource(result, requests, bodies, records)

    @staticmethod
    def _parse_pubmed_summaries(
        payload: dict[str, object], expected_ids: list[str]
    ) -> list[BibliographicRecord]:
        result = payload.get("result")
        if not isinstance(result, dict):
            raise RemoteResponseError("PubMed summary response is missing result")
        records: list[BibliographicRecord] = []
        for pmid in expected_ids:
            item = result.get(pmid)
            if not isinstance(item, dict):
                raise RemoteResponseError(f"PubMed summary is missing PMID {pmid}")
            title = str(item.get("title", "")).strip()
            if not title:
                raise RemoteResponseError(f"PubMed summary PMID {pmid} has no title")
            article_ids = item.get("articleids", [])
            doi = None
            pmcid = None
            if isinstance(article_ids, list):
                for identifier in article_ids:
                    if not isinstance(identifier, dict):
                        continue
                    if identifier.get("idtype") == "doi":
                        doi = str(identifier.get("value", "")) or None
                    if identifier.get("idtype") == "pmc":
                        pmcid = str(identifier.get("value", "")) or None
            raw_authors = item.get("authors", [])
            authors = (
                [
                    str(author.get("name"))
                    for author in raw_authors
                    if isinstance(author, dict) and author.get("name")
                ]
                if isinstance(raw_authors, list)
                else []
            )
            records.append(
                BibliographicRecord(
                    record_key=f"pmid:{pmid}",
                    source_ids=["pubmed"],
                    pmid=pmid,
                    pmcid=pmcid,
                    doi=doi,
                    title=title,
                    authors=authors,
                    journal=str(item.get("fulljournalname") or item.get("source") or "") or None,
                    publication_year=LiteratureSearchService._year(item.get("pubdate")),
                )
            )
        return records

    @staticmethod
    def _parse_europe_record(item: dict[str, object]) -> BibliographicRecord:
        title = str(item.get("title", "")).strip()
        if not title:
            raise RemoteResponseError("Europe PMC record has no title")
        pmid = str(item.get("pmid", "")) or None
        pmcid = str(item.get("pmcid", "")) or None
        doi = str(item.get("doi", "")) or None
        source_id = str(item.get("source", "MED"))
        external_id = str(item.get("id", ""))
        key = f"pmid:{pmid}" if pmid else f"europe-pmc:{source_id}:{external_id}"
        author_string = str(item.get("authorString", "")).strip()
        return BibliographicRecord(
            record_key=key,
            source_ids=["europe-pmc"],
            pmid=pmid,
            pmcid=pmcid,
            doi=doi,
            title=title,
            authors=[value.strip() for value in author_string.split(",") if value.strip()],
            journal=str(item.get("journalTitle", "")) or None,
            publication_year=LiteratureSearchService._year(
                item.get("pubYear") or item.get("firstPublicationDate")
            ),
            abstract=str(item.get("abstractText", "")) or None,
            is_open_access=LiteratureSearchService._boolean(item.get("isOpenAccess")),
        )

    @staticmethod
    def _deduplicate(
        records: list[BibliographicRecord],
    ) -> tuple[list[BibliographicRecord], int]:
        merged: dict[str, BibliographicRecord] = {}
        for record in records:
            key = LiteratureSearchService._dedupe_key(record)
            existing = merged.get(key)
            if existing is None:
                merged[key] = record
                continue
            existing_payload = existing.model_dump()
            incoming = record.model_dump()
            for field in ("pmid", "pmcid", "doi", "journal", "publication_year", "abstract"):
                if existing_payload[field] is None and incoming[field] is not None:
                    existing_payload[field] = incoming[field]
            existing_payload["authors"] = existing.authors or record.authors
            existing_payload["source_ids"] = sorted(set(existing.source_ids + record.source_ids))
            if existing.is_open_access is None:
                existing_payload["is_open_access"] = record.is_open_access
            merged[key] = BibliographicRecord.model_validate(existing_payload)
        output = sorted(merged.values(), key=lambda record: record.record_key)
        return output, len(records) - len(output)

    @staticmethod
    def _dedupe_key(record: BibliographicRecord) -> str:
        if record.doi:
            return f"doi:{record.doi.casefold().removeprefix('https://doi.org/')}"
        if record.pmid:
            return f"pmid:{record.pmid}"
        normalized_title = re.sub(r"[^a-z0-9]+", "", record.title.casefold())
        return f"title:{normalized_title}"

    @staticmethod
    def _year(value: object) -> int | None:
        match = re.search(r"\b(1[5-9]\d{2}|20\d{2}|21\d{2})\b", str(value or ""))
        return int(match.group(1)) if match else None

    @staticmethod
    def _boolean(value: object) -> bool | None:
        if value in (True, "Y", "y", "true", "True", 1):
            return True
        if value in (False, "N", "n", "false", "False", 0):
            return False
        return None

    @staticmethod
    def _request(source_id: str, endpoint: str, parameters: dict[str, str]) -> LiteratureRequest:
        redacted = {key: value for key, value in parameters.items() if key != "email"}
        return LiteratureRequest(source_id=source_id, endpoint=endpoint, parameters=redacted)

    @staticmethod
    def _checked(response: HTTPResponse, source: str) -> HTTPResponse:
        if not 200 <= response.status_code < 300:
            raise RemoteResponseError(f"{source} request failed with HTTP {response.status_code}")
        return response

    @staticmethod
    def _json(body: bytes, context: str) -> dict[str, object]:
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RemoteResponseError(f"{context} response is not valid JSON") from error
        if not isinstance(payload, dict):
            raise RemoteResponseError(f"{context} response must be a JSON object")
        return cast(dict[str, object], payload)

    @staticmethod
    def _placeholder_object() -> StoredObject:
        return StoredObject(
            object_key="pending", media_type=JSON_MEDIA_TYPE, size_bytes=0, sha256="0" * 64
        )

    @staticmethod
    def _stored_object(key: str, body: bytes) -> StoredObject:
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )

    def _put_immutable(self, key: str, body: bytes) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
            return
        self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
