"""Immutable human-review queue construction from verified literature snapshots."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import TypeAdapter, ValidationError

from nas_core.domain.literature import (
    BibliographicRecord,
    LiteratureSearchReceipt,
    ScreeningDecision,
    ScreeningQueueManifest,
    ScreeningQueueReceipt,
    ScreeningQueueRecord,
    ScreeningQueueSummary,
    ScreeningStatus,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "literature-screening-queue-1.0.0"
JSON_MEDIA_TYPE = "application/json"
JSONL_MEDIA_TYPE = "application/x-ndjson"
_RECORDS = TypeAdapter(list[BibliographicRecord])


class ScreeningQueueError(RuntimeError):
    """Raised when verified search inputs or queue invariants fail."""


class ScreeningQueueService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def build(
        self,
        receipt: LiteratureSearchReceipt,
        *,
        code_revision: str,
    ) -> ScreeningQueueManifest:
        self._validate_receipt(receipt, code_revision)
        records = self._load_records(receipt)
        queue_records = [self._queue_record(receipt.execution_id, record) for record in records]
        summary = self._summary(queue_records)
        created_at = self._clock()
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "code_revision": code_revision,
            "created_at": created_at.isoformat(),
            "input_sha256": receipt.normalized_records_sha256,
            "search_execution_id": receipt.execution_id,
            "study_id": receipt.study_id,
        }
        queue_id = sha256(canonical_json(identity))
        prefix = f"literature-screening/{receipt.study_id}/{receipt.execution_id}/{queue_id}"

        queue_bytes = b"".join(
            canonical_json(record.model_dump(mode="json", exclude_none=True)) + b"\n"
            for record in queue_records
        )
        summary_bytes = canonical_json(summary.model_dump(mode="json", exclude_none=True))
        artifacts: list[StoredObject] = []
        for name, body, media_type in (
            ("title-abstract-queue.jsonl", queue_bytes, JSONL_MEDIA_TYPE),
            ("queue-summary.json", summary_bytes, JSON_MEDIA_TYPE),
        ):
            key = f"{prefix}/{name}"
            self._put_immutable(key, body, content_type=media_type)
            artifacts.append(
                StoredObject(
                    object_key=key,
                    media_type=media_type,
                    size_bytes=len(body),
                    sha256=sha256(body),
                )
            )

        manifest = ScreeningQueueManifest(
            queue_id=queue_id,
            study_id=receipt.study_id,
            question_id=receipt.question_id,
            question_version=receipt.question_version,
            strategy_version=receipt.strategy_version,
            search_execution_id=receipt.execution_id,
            algorithm_version=ALGORITHM_VERSION,
            code_revision=code_revision,
            created_at=created_at,
            input_object_key=receipt.normalized_records_object_key,
            input_sha256=receipt.normalized_records_sha256,
            artifacts=artifacts,
            summary=summary,
            human_decisions_recorded=0,
            ai_decisions_recorded=0,
        )
        unhashed = canonical_json(manifest.model_dump(mode="json", exclude_none=True))
        manifest = manifest.model_copy(update={"manifest_sha256": sha256(unhashed)})
        self._put_immutable(
            f"{prefix}/manifest.json",
            canonical_json(manifest.model_dump(mode="json", exclude_none=True)),
            content_type=JSON_MEDIA_TYPE,
        )
        return manifest

    def verify(
        self,
        study_id: str,
        search_execution_id: str,
        queue_id: str,
    ) -> ScreeningQueueReceipt:
        for label, value in (
            ("search execution ID", search_execution_id),
            ("queue ID", queue_id),
        ):
            if not re.fullmatch(r"[a-f0-9]{64}", value):
                raise ScreeningQueueError(f"{label} must be a SHA-256")
        if not re.fullmatch(r"NAS-[A-Z0-9]+-[0-9]{3}", study_id):
            raise ScreeningQueueError("study ID is invalid")

        prefix = f"literature-screening/{study_id}/{search_execution_id}/{queue_id}"
        manifest_key = f"{prefix}/manifest.json"
        if not self._store.exists(manifest_key):
            raise ScreeningQueueError("screening queue manifest does not exist")
        try:
            manifest = ScreeningQueueManifest.model_validate_json(
                self._store.get_bytes(manifest_key)
            )
        except (ValidationError, ValueError) as error:
            raise ScreeningQueueError("screening queue manifest is invalid") from error
        if (
            manifest.study_id != study_id
            or manifest.search_execution_id != search_execution_id
            or manifest.queue_id != queue_id
        ):
            raise ScreeningQueueError("screening queue manifest identity does not match its key")

        payload = manifest.model_dump(mode="json", exclude_none=True)
        declared_manifest_sha256 = payload.pop("manifest_sha256", None)
        if (
            declared_manifest_sha256 is None
            or sha256(canonical_json(payload)) != declared_manifest_sha256
        ):
            raise ScreeningQueueError("screening queue manifest checksum verification failed")
        if len(manifest.artifacts) != 2:
            raise ScreeningQueueError("screening queue must contain exactly two artifacts")

        bodies: dict[str, bytes] = {}
        for artifact in manifest.artifacts:
            if not self._store.exists(artifact.object_key):
                raise ScreeningQueueError("one or more screening queue artifacts are missing")
            body = self._store.get_bytes(artifact.object_key)
            if sha256(body) != artifact.sha256 or len(body) != artifact.size_bytes:
                raise ScreeningQueueError("screening queue artifact verification failed")
            bodies[artifact.object_key] = body

        queue_artifact = next(
            (
                item
                for item in manifest.artifacts
                if item.object_key.endswith("/title-abstract-queue.jsonl")
            ),
            None,
        )
        summary_artifact = next(
            (
                item
                for item in manifest.artifacts
                if item.object_key.endswith("/queue-summary.json")
            ),
            None,
        )
        if queue_artifact is None or summary_artifact is None:
            raise ScreeningQueueError("screening queue artifact roles are invalid")
        try:
            rows = [
                ScreeningQueueRecord.model_validate_json(line)
                for line in bodies[queue_artifact.object_key].splitlines()
                if line
            ]
            stored_summary = ScreeningQueueSummary.model_validate_json(
                bodies[summary_artifact.object_key]
            )
        except (ValidationError, ValueError) as error:
            raise ScreeningQueueError("screening queue artifacts are invalid") from error

        screening_ids = [row.screening_id for row in rows]
        expected_ids = [
            sha256(
                canonical_json(
                    {
                        "execution_id": search_execution_id,
                        "record_key": row.record_key,
                    }
                )
            )
            for row in rows
        ]
        recalculated_summary = self._summary(rows)
        if (
            screening_ids != expected_ids
            or len(screening_ids) != len(set(screening_ids))
            or any(row.decision is not ScreeningDecision.PENDING for row in rows)
            or stored_summary != recalculated_summary
            or manifest.summary != recalculated_summary
            or manifest.human_decisions_recorded != 0
            or manifest.ai_decisions_recorded != 0
        ):
            raise ScreeningQueueError("screening queue record-count verification failed")

        return ScreeningQueueReceipt(
            queue_id=manifest.queue_id,
            study_id=manifest.study_id,
            search_execution_id=manifest.search_execution_id,
            algorithm_version=manifest.algorithm_version,
            code_revision=manifest.code_revision,
            created_at=manifest.created_at,
            manifest_object_key=manifest_key,
            manifest_sha256=declared_manifest_sha256,
            queue_object_key=queue_artifact.object_key,
            queue_sha256=queue_artifact.sha256,
            queue_size_bytes=queue_artifact.size_bytes,
            summary=manifest.summary,
            verified_at=self._clock(),
            manifest_checksum_verified=True,
            artifact_checksums_verified=True,
            record_count_verified=True,
            screening_status=ScreeningStatus.NOT_STARTED,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _validate_receipt(receipt: LiteratureSearchReceipt, code_revision: str) -> None:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ScreeningQueueError("code revision must be a 7-to-40 character Git SHA")
        if not all(
            (
                receipt.manifest_checksum_verified,
                receipt.object_checksums_verified,
                receipt.object_sizes_verified,
                receipt.record_count_invariants_verified,
            )
        ):
            raise ScreeningQueueError("screening requires an independently verified search receipt")
        if receipt.scientific_conclusions_drawn or receipt.outcome_data_accessed:
            raise ScreeningQueueError("search receipt violates the Phase 0 screening boundary")

    def _load_records(self, receipt: LiteratureSearchReceipt) -> list[BibliographicRecord]:
        body = self._store.get_bytes(receipt.normalized_records_object_key)
        if len(body) != receipt.normalized_records_size_bytes:
            raise ScreeningQueueError("normalized record size does not match the receipt")
        if sha256(body) != receipt.normalized_records_sha256:
            raise ScreeningQueueError("normalized record checksum does not match the receipt")
        try:
            records = _RECORDS.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise ScreeningQueueError(
                "normalized records are not valid bibliographic data"
            ) from error
        if len(records) != receipt.unique_record_count:
            raise ScreeningQueueError("normalized record count does not match the receipt")
        keys = [record.record_key for record in records]
        if len(keys) != len(set(keys)):
            raise ScreeningQueueError("normalized records contain duplicate record keys")
        return sorted(records, key=lambda record: record.record_key)

    @staticmethod
    def _queue_record(
        execution_id: str,
        record: BibliographicRecord,
    ) -> ScreeningQueueRecord:
        screening_id = sha256(
            canonical_json({"execution_id": execution_id, "record_key": record.record_key})
        )
        return ScreeningQueueRecord(
            screening_id=screening_id,
            **record.model_dump(),
            decision=ScreeningDecision.PENDING,
        )

    @staticmethod
    def _summary(records: list[ScreeningQueueRecord]) -> ScreeningQueueSummary:
        years = [record.publication_year for record in records if record.publication_year]
        with_abstract = sum(record.abstract is not None for record in records)
        return ScreeningQueueSummary(
            input_record_count=len(records),
            pending_record_count=len(records),
            records_with_abstract=with_abstract,
            records_without_abstract=len(records) - with_abstract,
            records_with_doi=sum(record.doi is not None for record in records),
            records_with_pmid=sum(record.pmid is not None for record in records),
            earliest_publication_year=min(years, default=None),
            latest_publication_year=max(years, default=None),
        )

    def _put_immutable(self, key: str, body: bytes, *, content_type: str) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
            return
        self._store.put_bytes(key, body, content_type=content_type)
