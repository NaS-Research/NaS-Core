"""Immutable backward and forward citation retrieval from Europe PMC."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import ValidationError

from nas_core.domain.citation_chain import (
    CitationCandidate,
    CitationChainReceipt,
    CitationChainSnapshot,
    CitationDirection,
    CitationEndpointResult,
    CitationSeed,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import (
    ImmutableObjectConflictError,
    RemoteResponseError,
    canonical_json,
    sha256,
)
from nas_core.retrieval.literature import (
    EUROPE_PMC_SEARCH_URL,
    LiteratureTransport,
    UrllibLiteratureTransport,
)
from nas_core.storage.object_store import ObjectStore

EUROPE_PMC_ROOT = EUROPE_PMC_SEARCH_URL.removesuffix("/search")
JSON_MEDIA_TYPE = "application/json"
PAGE_SIZE = 1000


class CitationChainError(RuntimeError):
    """Raised when citation transport, identity, or provenance verification fails."""


class CitationChainRetrievalService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        transport: LiteratureTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._transport = transport or UrllibLiteratureTransport()
        self._clock = clock or (lambda: datetime.now(UTC))

    def retrieve(
        self,
        seeds: list[CitationSeed],
        *,
        study_id: str,
        pass_number: int,
        code_revision: str,
    ) -> CitationChainSnapshot:
        self._validate_request(seeds, code_revision)
        retrieved_at = self._clock()
        endpoint_results: list[CitationEndpointResult] = []
        raw_responses: list[dict[str, object]] = []
        candidates: dict[str, dict[str, object]] = {}
        seed_identities = {
            (item.source, item.external_id)
            for item in seeds
        }

        for seed in seeds:
            for direction in CitationDirection:
                result, responses = self._retrieve_endpoint(seed, direction)
                endpoint_results.append(result)
                raw_responses.extend(
                    {
                        "seed_evidence_id": seed.evidence_id,
                        "direction": direction.value,
                        "page": page,
                        "payload": response,
                    }
                    for page, response in enumerate(responses, start=1)
                )
                for response in responses:
                    for item in self._response_records(response, direction):
                        external_id = str(item.get("id", "")).strip()
                        source = str(item.get("source", "")).strip().upper()
                        title = " ".join(str(item.get("title", "")).split())
                        if not external_id or not source or not title:
                            continue
                        if (source, external_id) in seed_identities:
                            continue
                        record_key = f"{source}:{external_id}"
                        candidate = candidates.setdefault(
                            record_key,
                            {
                                "record_key": record_key,
                                "source": source,
                                "external_id": external_id,
                                "title": title,
                                "author_string": (
                                    str(item.get("authorString", "")).strip() or None
                                ),
                                "journal": (
                                    str(item.get("journalAbbreviation", "")).strip() or None
                                ),
                                "publication_year": item.get("pubYear"),
                                "directions": [],
                                "seed_evidence_ids": [],
                            },
                        )
                        directions = candidate["directions"]
                        seed_ids = candidate["seed_evidence_ids"]
                        assert isinstance(directions, list)
                        assert isinstance(seed_ids, list)
                        if direction.value not in directions:
                            directions.append(direction.value)
                        if seed.evidence_id not in seed_ids:
                            seed_ids.append(seed.evidence_id)

        normalized_candidates = [
            CitationCandidate.model_validate(candidate)
            for candidate in sorted(candidates.values(), key=lambda item: str(item["record_key"]))
        ]
        endpoint_results.sort(key=lambda item: (item.seed_evidence_id, item.direction.value))
        raw_body = canonical_json(raw_responses)
        candidate_body = canonical_json(
            [item.model_dump(mode="json", exclude_none=True) for item in normalized_candidates]
        )
        backward_count = sum(
            item.retrieved_result_count
            for item in endpoint_results
            if item.direction is CitationDirection.BACKWARD
        )
        forward_count = sum(
            item.retrieved_result_count
            for item in endpoint_results
            if item.direction is CitationDirection.FORWARD
        )
        execution_identity = {
            "code_revision": code_revision,
            "pass_number": pass_number,
            "retrieved_at": retrieved_at.isoformat(),
            "seed_evidence_ids": sorted(item.evidence_id for item in seeds),
            "study_id": study_id,
        }
        execution_id = sha256(canonical_json(execution_identity))
        prefix = f"citation-chain/{study_id}/pass-{pass_number:04d}/{execution_id}"
        raw_object = self._store_object(
            f"{prefix}/raw-responses.json",
            raw_body,
            record_ids=[item.evidence_id for item in seeds],
        )
        candidates_object = self._store_object(
            f"{prefix}/candidates.json",
            candidate_body,
            # Candidate identities live in the checksummed external payload. Keeping
            # thousands of IDs out of the Git-safe receipt is an explicit boundary.
            record_ids=[],
        )
        snapshot = CitationChainSnapshot(
            execution_id=execution_id,
            study_id=study_id,
            pass_number=pass_number,
            code_revision=code_revision,
            retrieved_at=retrieved_at,
            seeds=sorted(seeds, key=lambda item: item.evidence_id),
            endpoint_results=endpoint_results,
            backward_candidate_count=backward_count,
            forward_candidate_count=forward_count,
            unique_candidate_count=len(normalized_candidates),
            raw_responses_object=raw_object,
            candidates_object=candidates_object,
        )
        manifest_hash = sha256(
            canonical_json(snapshot.model_dump(mode="json", exclude_none=True))
        )
        snapshot = snapshot.model_copy(update={"manifest_sha256": manifest_hash})
        self._put_immutable(
            self.manifest_object_key(snapshot),
            canonical_json(snapshot.model_dump(mode="json", exclude_none=True)),
        )
        return snapshot

    def verify(self, snapshot: CitationChainSnapshot) -> CitationChainReceipt:
        manifest_key = self.manifest_object_key(snapshot)
        manifest_body = self._store.get_bytes(manifest_key)
        try:
            reloaded = CitationChainSnapshot.model_validate(json.loads(manifest_body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationChainError("stored citation manifest is invalid") from error
        if reloaded != snapshot:
            raise CitationChainError("stored citation manifest differs from supplied manifest")
        expected_hash = sha256(
            canonical_json(
                snapshot.model_copy(update={"manifest_sha256": None}).model_dump(
                    mode="json", exclude_none=True
                )
            )
        )
        if snapshot.manifest_sha256 != expected_hash:
            raise CitationChainError("citation manifest checksum is invalid")

        raw_body = self._store.get_bytes(snapshot.raw_responses_object.object_key)
        candidate_body = self._store.get_bytes(snapshot.candidates_object.object_key)
        objects = {
            snapshot.raw_responses_object.object_key: (
                snapshot.raw_responses_object,
                raw_body,
            ),
            snapshot.candidates_object.object_key: (
                snapshot.candidates_object,
                candidate_body,
            ),
        }
        if any(
            len(body) != stored.size_bytes or sha256(body) != stored.sha256
            for stored, body in objects.values()
        ):
            raise CitationChainError("citation object checksum or size is invalid")
        try:
            candidates = [
                CitationCandidate.model_validate(item)
                for item in json.loads(candidate_body)
            ]
            raw_responses = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationChainError("stored citation objects are invalid") from error
        if not isinstance(raw_responses, list):
            raise CitationChainError("stored raw citation responses are invalid")
        if len(candidates) != snapshot.unique_candidate_count:
            raise CitationChainError("stored citation candidate count is invalid")

        endpoint_request_count = sum(item.request_count for item in snapshot.endpoint_results)
        if endpoint_request_count != len(raw_responses):
            raise CitationChainError("citation endpoint request count is invalid")
        return CitationChainReceipt(
            execution_id=snapshot.execution_id,
            study_id=snapshot.study_id,
            pass_number=snapshot.pass_number,
            code_revision=snapshot.code_revision,
            retrieved_at=snapshot.retrieved_at,
            verified_at=self._clock(),
            seed_evidence_ids=[item.evidence_id for item in snapshot.seeds],
            backward_candidate_count=snapshot.backward_candidate_count,
            forward_candidate_count=snapshot.forward_candidate_count,
            unique_candidate_count=snapshot.unique_candidate_count,
            endpoint_request_count=endpoint_request_count,
            manifest_object_key=manifest_key,
            manifest_sha256=expected_hash,
            raw_responses_object=snapshot.raw_responses_object,
            candidates_object=snapshot.candidates_object,
            manifest_checksum_verified=True,
            object_checksums_verified=True,
            endpoint_counts_verified=True,
            candidate_count_verified=True,
        )

    def _retrieve_endpoint(
        self,
        seed: CitationSeed,
        direction: CitationDirection,
    ) -> tuple[CitationEndpointResult, list[dict[str, object]]]:
        endpoint = (
            f"{EUROPE_PMC_ROOT}/{seed.source}/{seed.external_id}/"
            f"{self._endpoint_name(direction)}"
        )
        first = self._request_page(endpoint, page=1)
        hit_count = self._hit_count(first)
        responses = [first]
        page_count = max(1, math.ceil(hit_count / PAGE_SIZE))
        for page in range(2, page_count + 1):
            responses.append(self._request_page(endpoint, page=page))
        retrieved_count = sum(
            len(self._response_records(response, direction)) for response in responses
        )
        return (
            CitationEndpointResult(
                seed_evidence_id=seed.evidence_id,
                direction=direction,
                endpoint_url=endpoint,
                reported_result_count=hit_count,
                retrieved_result_count=retrieved_count,
                request_count=len(responses),
            ),
            responses,
        )

    def _request_page(self, endpoint: str, *, page: int) -> dict[str, object]:
        response = self._transport.get(
            endpoint,
            {"format": "json", "page": str(page), "pageSize": str(PAGE_SIZE)},
        )
        if response.status_code != 200 or not response.body:
            raise RemoteResponseError(
                f"Europe PMC citation request failed with status {response.status_code}"
            )
        try:
            payload = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CitationChainError("Europe PMC citation response is invalid JSON") from error
        if not isinstance(payload, dict):
            raise CitationChainError("Europe PMC citation response is not an object")
        return payload

    @staticmethod
    def _hit_count(payload: dict[str, object]) -> int:
        value = payload.get("hitCount")
        if not isinstance(value, int) or value < 0:
            raise CitationChainError("Europe PMC citation response lacks a valid hit count")
        return value

    @staticmethod
    def _response_records(
        payload: dict[str, object],
        direction: CitationDirection,
    ) -> list[dict[str, object]]:
        list_key = "referenceList" if direction is CitationDirection.BACKWARD else "citationList"
        item_key = "reference" if direction is CitationDirection.BACKWARD else "citation"
        container = payload.get(list_key, {})
        if container is None:
            return []
        if not isinstance(container, dict):
            raise CitationChainError("Europe PMC citation list is invalid")
        records = container.get(item_key, [])
        if records is None:
            return []
        if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
            raise CitationChainError("Europe PMC citation records are invalid")
        return records

    @staticmethod
    def _endpoint_name(direction: CitationDirection) -> str:
        return "references" if direction is CitationDirection.BACKWARD else "citations"

    @staticmethod
    def _validate_request(seeds: list[CitationSeed], code_revision: str) -> None:
        if not seeds or len({item.evidence_id for item in seeds}) != len(seeds):
            raise CitationChainError("citation retrieval requires unique seeds")
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationChainError("code revision must be a 7-to-40 character Git SHA")

    @staticmethod
    def manifest_object_key(snapshot: CitationChainSnapshot) -> str:
        return (
            f"citation-chain/{snapshot.study_id}/pass-{snapshot.pass_number:04d}/"
            f"{snapshot.execution_id}/manifest.json"
        )

    def _store_object(
        self,
        key: str,
        body: bytes,
        *,
        record_ids: list[str],
    ) -> StoredObject:
        self._put_immutable(key, body)
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
            record_ids=record_ids,
        )

    def _put_immutable(self, key: str, body: bytes) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
            return
        self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
