"""Append-only founder review for immutable literature-screening queues."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import ValidationError

from nas_core.domain.literature import (
    ScreeningDecision,
    ScreeningDecisionBatch,
    ScreeningDecisionEvent,
    ScreeningProgressManifest,
    ScreeningProgressReceipt,
    ScreeningProgressSummary,
    ScreeningQueueReceipt,
    ScreeningQueueRecord,
    ScreeningReviewBatch,
    ScreeningReviewerRole,
    ScreeningStatus,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "literature-founder-review-1.0.0"
JSON_MEDIA_TYPE = "application/json"
JSONL_MEDIA_TYPE = "application/x-ndjson"


class ScreeningReviewError(RuntimeError):
    """Raised when queue, decision-chain, or review invariants fail."""


class ScreeningReviewService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def next_batch(
        self,
        queue_receipt: ScreeningQueueReceipt,
        *,
        progress_receipt: ScreeningProgressReceipt | None = None,
        batch_size: int = 20,
        include_unclear: bool = False,
    ) -> ScreeningReviewBatch:
        if not 1 <= batch_size <= 100:
            raise ScreeningReviewError("batch size must be between 1 and 100")
        queue = self._load_queue(queue_receipt)
        events = self._load_prior_events(queue_receipt, progress_receipt)
        current = self._current_events(events)
        available = [
            record
            for record in queue
            if record.screening_id not in current
            or (
                include_unclear
                and current[record.screening_id].decision is ScreeningDecision.UNCLEAR
            )
        ]
        return ScreeningReviewBatch(
            queue_id=queue_receipt.queue_id,
            based_on_progress_id=(progress_receipt.progress_id if progress_receipt else None),
            available_record_count=len(available),
            records=available[:batch_size],
        )

    def record_batch(
        self,
        queue_receipt: ScreeningQueueReceipt,
        batch: ScreeningDecisionBatch,
        *,
        code_revision: str,
        progress_receipt: ScreeningProgressReceipt | None = None,
    ) -> ScreeningProgressManifest:
        self._validate_submission(queue_receipt, batch, code_revision, progress_receipt)
        queue = self._load_queue(queue_receipt)
        queue_by_id = {record.screening_id: record for record in queue}
        prior_events = self._load_prior_events(queue_receipt, progress_receipt)
        current = self._current_events(prior_events)
        created_at = self._clock()
        batch_identity = {
            "created_at": created_at.isoformat(),
            "decisions": [item.model_dump(mode="json") for item in batch.decisions],
            "expected_previous_progress_id": batch.expected_previous_progress_id,
            "queue_id": batch.queue_id,
            "reviewer_id": batch.reviewer_id,
        }
        batch_id = sha256(canonical_json(batch_identity))
        added_events: list[ScreeningDecisionEvent] = []
        for item in batch.decisions:
            record = queue_by_id.get(item.screening_id)
            if record is None:
                raise ScreeningReviewError(f"unknown screening ID: {item.screening_id}")
            previous = current.get(item.screening_id)
            if previous is None and item.supersedes_event_id is not None:
                raise ScreeningReviewError("an initial decision cannot supersede an event")
            if previous is not None and item.supersedes_event_id != previous.event_id:
                raise ScreeningReviewError(
                    "an existing decision requires its current event ID and a change reason"
                )
            event = ScreeningDecisionEvent(
                event_id="0" * 64,
                batch_id=batch_id,
                change_reason=item.change_reason,
                decided_at=created_at,
                decision=item.decision,
                exclusion_reason=item.exclusion_reason,
                queue_id=queue_receipt.queue_id,
                record_key=record.record_key,
                reviewer_id=batch.reviewer_id,
                reviewer_name=batch.reviewer_name,
                reviewer_role=batch.reviewer_role,
                screening_id=item.screening_id,
                supersedes_event_id=item.supersedes_event_id,
            )
            event = event.model_copy(update={"event_id": self._event_id(event)})
            added_events.append(event)
            current[item.screening_id] = event

        events = [*prior_events, *added_events]
        summary = self._summary(queue, events)
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "batch_id": batch_id,
            "code_revision": code_revision,
            "previous_progress_id": batch.expected_previous_progress_id,
            "queue_id": queue_receipt.queue_id,
        }
        progress_id = sha256(canonical_json(identity))
        prefix = f"literature-screening-review/{queue_receipt.queue_id}/{progress_id}"
        decisions_body = b"".join(
            canonical_json(event.model_dump(mode="json", exclude_none=True)) + b"\n"
            for event in events
        )
        summary_body = canonical_json(summary.model_dump(mode="json"))
        artifacts: list[StoredObject] = []
        for name, body, media_type in (
            ("decision-events.jsonl", decisions_body, JSONL_MEDIA_TYPE),
            ("progress-summary.json", summary_body, JSON_MEDIA_TYPE),
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
        manifest = ScreeningProgressManifest(
            progress_id=progress_id,
            previous_progress_id=batch.expected_previous_progress_id,
            queue_id=queue_receipt.queue_id,
            batch_id=batch_id,
            algorithm_version=ALGORITHM_VERSION,
            code_revision=code_revision,
            created_at=created_at,
            reviewer_id=batch.reviewer_id,
            reviewer_name=batch.reviewer_name,
            reviewer_role=batch.reviewer_role,
            queue_object_key=queue_receipt.queue_object_key,
            queue_sha256=queue_receipt.queue_sha256,
            artifacts=artifacts,
            summary=summary,
            added_event_count=len(added_events),
            ai_decisions_recorded=0,
            scientific_conclusions_drawn=False,
        )
        unhashed = canonical_json(manifest.model_dump(mode="json", exclude_none=True))
        manifest = manifest.model_copy(update={"manifest_sha256": sha256(unhashed)})
        self._put_immutable(
            self.manifest_object_key(manifest),
            canonical_json(manifest.model_dump(mode="json", exclude_none=True)),
            content_type=JSON_MEDIA_TYPE,
        )
        return manifest

    def validate_batch(
        self,
        queue_receipt: ScreeningQueueReceipt,
        batch: ScreeningDecisionBatch,
        *,
        code_revision: str,
        progress_receipt: ScreeningProgressReceipt | None = None,
    ) -> None:
        """Validate submission binding without reading protected queue records."""

        self._validate_submission(queue_receipt, batch, code_revision, progress_receipt)

    def verify(
        self,
        queue_receipt: ScreeningQueueReceipt,
        manifest: ScreeningProgressManifest,
    ) -> ScreeningProgressReceipt:
        self._load_queue(queue_receipt)
        if manifest.queue_id != queue_receipt.queue_id:
            raise ScreeningReviewError("progress manifest does not belong to the queue")
        manifest_key = self.manifest_object_key(manifest)
        stored_manifest = self._store.get_bytes(manifest_key)
        try:
            reloaded = ScreeningProgressManifest.model_validate(json.loads(stored_manifest))
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise ScreeningReviewError("stored progress manifest is invalid") from error
        if reloaded != manifest:
            raise ScreeningReviewError(
                "stored progress manifest differs from the supplied manifest"
            )
        expected_manifest_hash = sha256(
            canonical_json(
                manifest.model_copy(update={"manifest_sha256": None}).model_dump(
                    mode="json", exclude_none=True
                )
            )
        )
        if manifest.manifest_sha256 != expected_manifest_hash:
            raise ScreeningReviewError("progress manifest checksum is invalid")
        decisions_object = self._artifact(manifest, "decision-events.jsonl")
        summary_object = self._artifact(manifest, "progress-summary.json")
        decisions_body = self._verified_object(decisions_object)
        summary_body = self._verified_object(summary_object)
        events = self._parse_events(decisions_body)
        self._validate_event_chain(events, queue_receipt.queue_id)
        added_events = [event for event in events if event.batch_id == manifest.batch_id]
        if len(added_events) != manifest.added_event_count:
            raise ScreeningReviewError("manifest added-event count does not match its ledger")
        if any(
            event.reviewer_id != manifest.reviewer_id
            or event.reviewer_name != manifest.reviewer_name
            or event.reviewer_role is not manifest.reviewer_role
            for event in added_events
        ):
            raise ScreeningReviewError("batch event reviewer does not match its manifest")
        if manifest.ai_decisions_recorded or manifest.scientific_conclusions_drawn:
            raise ScreeningReviewError("progress manifest violates the human screening boundary")
        queue = self._load_queue(queue_receipt)
        derived_summary = self._summary(queue, events)
        try:
            stored_summary = ScreeningProgressSummary.model_validate(json.loads(summary_body))
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise ScreeningReviewError("stored progress summary is invalid") from error
        if stored_summary != derived_summary or manifest.summary != derived_summary:
            raise ScreeningReviewError("progress counts do not reconcile with decision events")
        status = self._status(derived_summary)
        return ScreeningProgressReceipt(
            progress_id=manifest.progress_id,
            previous_progress_id=manifest.previous_progress_id,
            queue_id=manifest.queue_id,
            batch_id=manifest.batch_id,
            algorithm_version=manifest.algorithm_version,
            code_revision=manifest.code_revision,
            created_at=manifest.created_at,
            manifest_object_key=manifest_key,
            manifest_sha256=expected_manifest_hash,
            decisions_object_key=decisions_object.object_key,
            decisions_sha256=decisions_object.sha256,
            decisions_size_bytes=decisions_object.size_bytes,
            summary_object_key=summary_object.object_key,
            summary_sha256=summary_object.sha256,
            summary_size_bytes=summary_object.size_bytes,
            summary=derived_summary,
            verified_at=self._clock(),
            manifest_checksum_verified=True,
            artifact_checksums_verified=True,
            event_chain_verified=True,
            count_invariants_verified=True,
            screening_status=status,
            ai_decisions_recorded=manifest.ai_decisions_recorded,
            scientific_conclusions_drawn=manifest.scientific_conclusions_drawn,
        )

    @staticmethod
    def manifest_object_key(manifest: ScreeningProgressManifest) -> str:
        return (
            f"literature-screening-review/{manifest.queue_id}/{manifest.progress_id}/manifest.json"
        )

    @staticmethod
    def _validate_submission(
        queue_receipt: ScreeningQueueReceipt,
        batch: ScreeningDecisionBatch,
        code_revision: str,
        progress_receipt: ScreeningProgressReceipt | None,
    ) -> None:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ScreeningReviewError("code revision must be a 7-to-40 character Git SHA")
        if batch.queue_id != queue_receipt.queue_id:
            raise ScreeningReviewError("decision batch does not belong to the queue")
        actual_previous = progress_receipt.progress_id if progress_receipt else None
        if batch.expected_previous_progress_id != actual_previous:
            raise ScreeningReviewError(
                "decision batch was prepared against a different progress state"
            )
        if batch.reviewer_role is not ScreeningReviewerRole.FOUNDER_INTERNAL_REVIEWER:
            raise ScreeningReviewError(
                "only the founder internal-review role may decide this queue"
            )

    def _load_queue(self, receipt: ScreeningQueueReceipt) -> list[ScreeningQueueRecord]:
        if not all(
            (
                receipt.manifest_checksum_verified,
                receipt.artifact_checksums_verified,
                receipt.record_count_verified,
            )
        ):
            raise ScreeningReviewError("review requires a verified screening queue receipt")
        if receipt.scientific_conclusions_drawn:
            raise ScreeningReviewError("queue receipt contains premature scientific conclusions")
        if receipt.screening_status is not ScreeningStatus.NOT_STARTED:
            raise ScreeningReviewError("the immutable source queue must remain not started")
        body = self._store.get_bytes(receipt.queue_object_key)
        if len(body) != receipt.queue_size_bytes or sha256(body) != receipt.queue_sha256:
            raise ScreeningReviewError("screening queue does not match its verified receipt")
        records: list[ScreeningQueueRecord] = []
        try:
            for line in body.splitlines():
                records.append(ScreeningQueueRecord.model_validate(json.loads(line)))
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise ScreeningReviewError("screening queue contains invalid records") from error
        if len(records) != receipt.summary.input_record_count:
            raise ScreeningReviewError("screening queue record count does not match its receipt")
        identifiers = [record.screening_id for record in records]
        if len(identifiers) != len(set(identifiers)):
            raise ScreeningReviewError("screening queue contains duplicate screening IDs")
        if any(record.decision is not ScreeningDecision.PENDING for record in records):
            raise ScreeningReviewError("the source queue must remain undecided")
        return records

    def _load_prior_events(
        self,
        queue_receipt: ScreeningQueueReceipt,
        receipt: ScreeningProgressReceipt | None,
    ) -> list[ScreeningDecisionEvent]:
        if receipt is None:
            return []
        if receipt.queue_id != queue_receipt.queue_id:
            raise ScreeningReviewError("progress receipt does not belong to the queue")
        if not all(
            (
                receipt.manifest_checksum_verified,
                receipt.artifact_checksums_verified,
                receipt.event_chain_verified,
                receipt.count_invariants_verified,
            )
        ):
            raise ScreeningReviewError("review continuation requires a verified progress receipt")
        if receipt.ai_decisions_recorded or receipt.scientific_conclusions_drawn:
            raise ScreeningReviewError("progress receipt violates the human screening boundary")
        body = self._store.get_bytes(receipt.decisions_object_key)
        if len(body) != receipt.decisions_size_bytes or sha256(body) != receipt.decisions_sha256:
            raise ScreeningReviewError("decision ledger does not match its progress receipt")
        events = self._parse_events(body)
        self._validate_event_chain(events, queue_receipt.queue_id)
        derived_summary = self._summary(self._load_queue(queue_receipt), events)
        if derived_summary != receipt.summary:
            raise ScreeningReviewError("progress receipt counts do not match its decision ledger")
        if receipt.screening_status is not self._status(derived_summary):
            raise ScreeningReviewError("progress receipt status does not match its decision ledger")
        return events

    @staticmethod
    def _parse_events(body: bytes) -> list[ScreeningDecisionEvent]:
        try:
            return [
                ScreeningDecisionEvent.model_validate(json.loads(line))
                for line in body.splitlines()
            ]
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise ScreeningReviewError("decision ledger contains invalid events") from error

    @staticmethod
    def _validate_event_chain(events: list[ScreeningDecisionEvent], queue_id: str) -> None:
        seen_ids: set[str] = set()
        current_by_record: dict[str, ScreeningDecisionEvent] = {}
        for event in events:
            if event.queue_id != queue_id:
                raise ScreeningReviewError("decision event belongs to another queue")
            if event.event_id in seen_ids:
                raise ScreeningReviewError("decision ledger contains a duplicate event ID")
            if event.event_id != ScreeningReviewService._event_id(event):
                raise ScreeningReviewError("decision event checksum is invalid")
            previous = current_by_record.get(event.screening_id)
            if previous is None and event.supersedes_event_id is not None:
                raise ScreeningReviewError("decision chain begins with a superseding event")
            if previous is not None and event.supersedes_event_id != previous.event_id:
                raise ScreeningReviewError("decision event does not supersede the current event")
            seen_ids.add(event.event_id)
            current_by_record[event.screening_id] = event

    @staticmethod
    def _current_events(events: list[ScreeningDecisionEvent]) -> dict[str, ScreeningDecisionEvent]:
        current: dict[str, ScreeningDecisionEvent] = {}
        for event in events:
            current[event.screening_id] = event
        return current

    @classmethod
    def _summary(
        cls,
        queue: list[ScreeningQueueRecord],
        events: list[ScreeningDecisionEvent],
    ) -> ScreeningProgressSummary:
        queue_by_id = {record.screening_id: record for record in queue}
        current = cls._current_events(events)
        if not set(current).issubset(queue_by_id):
            raise ScreeningReviewError("decision ledger references records outside the queue")
        if any(
            event.record_key != queue_by_id[event.screening_id].record_key
            for event in current.values()
        ):
            raise ScreeningReviewError("decision ledger record key does not match the queue")
        included = sum(event.decision is ScreeningDecision.INCLUDE for event in current.values())
        excluded = sum(event.decision is ScreeningDecision.EXCLUDE for event in current.values())
        unclear = sum(event.decision is ScreeningDecision.UNCLEAR for event in current.values())
        decided = len(current)
        total = len(queue)
        return ScreeningProgressSummary(
            total_record_count=total,
            decided_record_count=decided,
            pending_record_count=total - decided,
            included_record_count=included,
            excluded_record_count=excluded,
            unclear_record_count=unclear,
            decision_event_count=len(events),
            completion_percent=round((decided / total) * 100, 2),
        )

    @staticmethod
    def _status(summary: ScreeningProgressSummary) -> ScreeningStatus:
        if summary.decided_record_count == 0:
            return ScreeningStatus.NOT_STARTED
        if summary.pending_record_count == 0 and summary.unclear_record_count == 0:
            return ScreeningStatus.COMPLETE
        return ScreeningStatus.IN_PROGRESS

    @staticmethod
    def _event_id(event: ScreeningDecisionEvent) -> str:
        payload = event.model_dump(mode="json", exclude={"event_id"}, exclude_none=True)
        return sha256(canonical_json(payload))

    @staticmethod
    def _artifact(manifest: ScreeningProgressManifest, suffix: str) -> StoredObject:
        matches = [item for item in manifest.artifacts if item.object_key.endswith(suffix)]
        if len(matches) != 1:
            raise ScreeningReviewError(f"progress manifest must contain one {suffix} artifact")
        return matches[0]

    def _verified_object(self, artifact: StoredObject) -> bytes:
        body = self._store.get_bytes(artifact.object_key)
        if len(body) != artifact.size_bytes or sha256(body) != artifact.sha256:
            raise ScreeningReviewError(
                f"stored artifact failed verification: {artifact.object_key}"
            )
        return body

    def _put_immutable(self, key: str, body: bytes, *, content_type: str) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
            return
        self._store.put_bytes(key, body, content_type=content_type)
