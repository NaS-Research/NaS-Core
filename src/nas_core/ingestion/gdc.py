"""Governed GDC clinical-data ingestion with immutable snapshot manifests."""

from __future__ import annotations

import hashlib
import json
import ssl
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, cast
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import certifi

from nas_core.domain.research import AnalysisPlan, PlanStatus
from nas_core.domain.snapshots import (
    DatasetSnapshot,
    ReleaseRecord,
    RequestRecord,
    StoredObject,
)
from nas_core.storage.object_store import ObjectStore

GDC_API_ROOT = "https://api.gdc.cancer.gov"
JSON_MEDIA_TYPE = "application/json"
HTML_MEDIA_TYPE = "text/html"
GDC_RELEASE_NOTES_HOSTS = frozenset({"docs.gdc.cancer.gov", "gdc.cancer.gov"})


class ProtocolNotLockedError(PermissionError):
    """Raised when outcome-bearing ingestion is attempted before approval."""


class RemoteResponseError(RuntimeError):
    """Raised when a GDC response is unsuccessful or structurally invalid."""


class ImmutableObjectConflictError(RuntimeError):
    """Raised when an existing immutable object has different bytes."""


@dataclass(frozen=True, slots=True)
class HTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class HTTPTransport(Protocol):
    def get(self, url: str) -> HTTPResponse: ...

    def post_json(self, url: str, payload: dict[str, object]) -> HTTPResponse: ...


class UrllibTransport:
    """Minimal standard-library transport for the public GDC API."""

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> HTTPResponse:
        request = Request(url, headers={"Accept": JSON_MEDIA_TYPE, "User-Agent": "NaS-Core/0.1"})
        return self._send(request)

    def post_json(self, url: str, payload: dict[str, object]) -> HTTPResponse:
        request = Request(
            url,
            data=canonical_json(payload),
            method="POST",
            headers={
                "Accept": JSON_MEDIA_TYPE,
                "Content-Type": JSON_MEDIA_TYPE,
                "User-Agent": "NaS-Core/0.1",
            },
        )
        return self._send(request)

    def _send(self, request: Request) -> HTTPResponse:
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


def canonical_json(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_release_notes_url(url: str) -> str:
    """Allow release evidence only from official HTTPS GDC hosts."""

    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in GDC_RELEASE_NOTES_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise ValueError("release notes URL must use HTTPS on an official GDC host")
    return url


def build_case_query(plan: AnalysisPlan, *, page_size: int, offset: int = 0) -> dict[str, object]:
    """Build the exact deterministic GDC cases request from a reviewed protocol."""

    requirement = plan.data_requirements[0]
    return {
        "filters": {
            "op": "in",
            "content": {
                "field": "project.project_id",
                "value": [requirement.project_id],
            },
        },
        "format": "JSON",
        "fields": ",".join(requirement.fields),
        "from": offset,
        "size": page_size,
        "sort": "case_id:asc",
    }


class GDCSnapshotService:
    """Fetch GDC pages and persist raw bytes plus a content-addressed manifest."""

    def __init__(
        self,
        *,
        store: ObjectStore,
        transport: HTTPTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        page_size: int = 500,
    ) -> None:
        if page_size < 1:
            raise ValueError("page_size must be positive")
        self._store = store
        self._transport = transport or UrllibTransport()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._page_size = page_size

    def capture_cases(
        self,
        plan: AnalysisPlan,
        *,
        data_release: str,
        release_notes_url: str,
    ) -> DatasetSnapshot:
        if plan.status is not PlanStatus.PREREGISTERED:
            raise ProtocolNotLockedError(
                f"study {plan.study_id} is {plan.status.value}; preregistration is required"
            )
        if not data_release.strip():
            raise ValueError("the exact GDC data release is required")
        release_notes_url = validate_release_notes_url(release_notes_url)

        retrieved_at = self._clock()
        status_response = self._checked(self._transport.get(f"{GDC_API_ROOT}/status"))
        status_payload = self._json_object(status_response.body, context="GDC status")
        release_notes_response = self._checked(self._transport.get(release_notes_url))
        self._validate_release_reference(data_release, release_notes_response.body)
        release = self._release_record(
            data_release,
            status_payload,
            status_response.body,
            release_notes_url=release_notes_url,
            release_notes_body=release_notes_response.body,
            retrieved_at=retrieved_at,
        )

        requests: list[RequestRecord] = []
        page_bodies: list[bytes] = []
        page_record_ids: list[list[str]] = []
        warnings: list[str] = []
        offset = 0
        expected_total: int | None = None

        while expected_total is None or offset < expected_total:
            request_payload = build_case_query(plan, page_size=self._page_size, offset=offset)
            response = self._checked(
                self._transport.post_json(plan.data_requirements[0].endpoint, request_payload)
            )
            payload = self._json_object(response.body, context="GDC cases")
            hits, total, response_warnings = self._parse_page(payload)
            if expected_total is None:
                expected_total = total
            elif total != expected_total:
                raise RemoteResponseError("GDC result total changed during paginated retrieval")

            requests.append(
                RequestRecord(
                    method="POST",
                    url=plan.data_requirements[0].endpoint,
                    body=request_payload,
                )
            )
            page_bodies.append(response.body)
            page_record_ids.append(self._record_ids(hits))
            warnings.extend(response_warnings)

            count = len(hits)
            if count == 0 and offset < total:
                raise RemoteResponseError("GDC returned an empty page before the expected total")
            offset += count

        record_ids = [record_id for page in page_record_ids for record_id in page]
        if len(record_ids) != len(set(record_ids)):
            raise RemoteResponseError("GDC returned duplicate case IDs across pages")
        if expected_total != len(record_ids):
            raise RemoteResponseError("retrieved case count does not match GDC pagination total")

        identity_payload = {
            "study_id": plan.study_id,
            "protocol_version": plan.protocol_version,
            "source_id": plan.governance.source_id,
            "data_release": data_release,
            "release_notes_url": release_notes_url,
            "release_notes_sha256": sha256(release_notes_response.body),
            "retrieved_at": retrieved_at.isoformat(),
            "requests": [request.model_dump(mode="json") for request in requests],
            "page_sha256": [sha256(body) for body in page_bodies],
        }
        snapshot_id = sha256(canonical_json(identity_payload))
        prefix = f"raw/{plan.governance.source_id}/{plan.study_id}/{snapshot_id}"

        objects: list[StoredObject] = []
        for index, (body, ids) in enumerate(
            zip(page_bodies, page_record_ids, strict=True), start=1
        ):
            key = f"{prefix}/pages/{index:05d}.json"
            self._put_immutable(key, body, content_type=JSON_MEDIA_TYPE)
            objects.append(
                StoredObject(
                    object_key=key,
                    media_type=JSON_MEDIA_TYPE,
                    size_bytes=len(body),
                    sha256=sha256(body),
                    record_ids=ids,
                )
            )

        status_key = f"{prefix}/gdc-status.json"
        self._put_immutable(status_key, status_response.body, content_type=JSON_MEDIA_TYPE)
        objects.append(
            StoredObject(
                object_key=status_key,
                media_type=JSON_MEDIA_TYPE,
                size_bytes=len(status_response.body),
                sha256=sha256(status_response.body),
            )
        )

        release_notes_key = f"{prefix}/gdc-data-release-notes.html"
        self._put_immutable(
            release_notes_key,
            release_notes_response.body,
            content_type=HTML_MEDIA_TYPE,
        )
        objects.append(
            StoredObject(
                object_key=release_notes_key,
                media_type=HTML_MEDIA_TYPE,
                size_bytes=len(release_notes_response.body),
                sha256=sha256(release_notes_response.body),
            )
        )

        manifest = DatasetSnapshot(
            schema_version="1.0.0",
            snapshot_id=snapshot_id,
            study_id=plan.study_id,
            protocol_version=plan.protocol_version,
            source_id=plan.governance.source_id,
            project_id=plan.data_requirements[0].project_id,
            classification=plan.governance.classification,
            purpose=plan.governance.purpose,
            retrieved_at=retrieved_at,
            release=release,
            requests=requests,
            objects=objects,
            record_count=len(record_ids),
            warnings=warnings,
        )
        manifest_bytes = canonical_json(manifest.model_dump(mode="json", exclude_none=True))
        manifest_hash = sha256(manifest_bytes)
        manifest = manifest.model_copy(update={"manifest_sha256": manifest_hash})
        final_manifest_bytes = canonical_json(manifest.model_dump(mode="json", exclude_none=True))
        self._put_immutable(
            f"{prefix}/manifest.json", final_manifest_bytes, content_type=JSON_MEDIA_TYPE
        )
        return manifest

    def _put_immutable(self, key: str, data: bytes, *, content_type: str) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != data:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
            return
        self._store.put_bytes(key, data, content_type=content_type)

    @staticmethod
    def _checked(response: HTTPResponse) -> HTTPResponse:
        if not 200 <= response.status_code < 300:
            raise RemoteResponseError(f"GDC request failed with HTTP {response.status_code}")
        return response

    @staticmethod
    def _json_object(body: bytes, *, context: str) -> dict[str, object]:
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RemoteResponseError(f"{context} response is not valid JSON") from error
        if not isinstance(payload, dict):
            raise RemoteResponseError(f"{context} response must be a JSON object")
        return cast(dict[str, object], payload)

    @staticmethod
    def _release_record(
        data_release: str,
        status: dict[str, object],
        status_body: bytes,
        *,
        release_notes_url: str,
        release_notes_body: bytes,
        retrieved_at: datetime,
    ) -> ReleaseRecord:
        required = ("status", "tag", "version", "commit")
        if any(field not in status for field in required):
            raise RemoteResponseError("GDC status response is missing release provenance")
        return ReleaseRecord(
            data_release=data_release,
            release_notes_url=release_notes_url,
            release_notes_retrieved_at=retrieved_at,
            release_notes_sha256=sha256(release_notes_body),
            api_status=str(status["status"]),
            api_tag=str(status["tag"]),
            api_version=str(status["version"]),
            api_commit=str(status["commit"]),
            status_response_sha256=sha256(status_body),
        )

    @staticmethod
    def _validate_release_reference(data_release: str, body: bytes) -> None:
        try:
            text = body.decode("utf-8").casefold()
        except UnicodeDecodeError as error:
            raise RemoteResponseError("GDC release notes are not valid UTF-8") from error
        expected = (f"data release {data_release}".casefold(), f"v{data_release}".casefold())
        if not any(identifier in text for identifier in expected):
            raise RemoteResponseError(
                f"GDC release notes do not identify Data Release {data_release}"
            )

    @staticmethod
    def _parse_page(
        payload: dict[str, object],
    ) -> tuple[list[dict[str, object]], int, list[str]]:
        data = payload.get("data")
        if not isinstance(data, dict):
            raise RemoteResponseError("GDC cases response is missing data")
        hits = data.get("hits")
        pagination = data.get("pagination")
        if not isinstance(hits, list) or not isinstance(pagination, dict):
            raise RemoteResponseError("GDC cases response is missing hits or pagination")
        total = pagination.get("total")
        if not isinstance(total, int) or total < 0:
            raise RemoteResponseError("GDC cases response has an invalid total")
        typed_hits: list[dict[str, object]] = []
        for hit in hits:
            if not isinstance(hit, dict):
                raise RemoteResponseError("GDC cases response contains a non-object hit")
            typed_hits.append(cast(dict[str, object], hit))
        raw_warnings = payload.get("warnings", {})
        warnings = [] if raw_warnings in ({}, None) else [json.dumps(raw_warnings, sort_keys=True)]
        return typed_hits, total, warnings

    @staticmethod
    def _record_ids(hits: list[dict[str, object]]) -> list[str]:
        ids: list[str] = []
        for hit in hits:
            record_id = hit.get("case_id") or hit.get("id")
            if not isinstance(record_id, str) or not record_id:
                raise RemoteResponseError("GDC case hit is missing case_id")
            ids.append(record_id)
        return ids
