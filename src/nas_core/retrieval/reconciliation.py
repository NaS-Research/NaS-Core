"""Deterministic reconciliation of a revised evidence queue against prior inventory."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import ValidationError

from nas_core.domain.literature import (
    InventoryReconciliationReceipt,
    InventoryReconciliationStatus,
    ScreeningDecision,
    ScreeningQueueReceipt,
    ScreeningQueueRecord,
)
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "literature-inventory-reconciliation-1.0.0"
JSONL_MEDIA_TYPE = "application/x-ndjson"


class InventoryReconciliationError(RuntimeError):
    """Raised when queue inputs or reconciliation invariants fail."""


class InventoryReconciliationService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def reconcile(
        self,
        current: ScreeningQueueReceipt,
        prior: ScreeningQueueReceipt,
        *,
        code_revision: str,
    ) -> InventoryReconciliationReceipt:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise InventoryReconciliationError("code revision must be a Git SHA")
        if current.study_id != prior.study_id:
            raise InventoryReconciliationError("queue receipts must belong to one study")
        if current.queue_id == prior.queue_id:
            raise InventoryReconciliationError("current and prior queues must differ")
        current_rows = self._load_verified_queue(current)
        prior_rows = self._load_verified_queue(prior)

        identifier_index: dict[tuple[str, str], set[str]] = defaultdict(set)
        title_index: dict[str, set[str]] = defaultdict(set)
        author_year_index: dict[tuple[str, int], set[str]] = defaultdict(set)
        prior_by_id = {row.screening_id: row for row in prior_rows}
        for row in prior_rows:
            for signal in self._identifiers(row):
                identifier_index[signal].add(row.screening_id)
            title_index[self._normalize_text(row.title)].add(row.screening_id)
            author_year = self._author_year(row)
            if author_year is not None:
                author_year_index[author_year].add(row.screening_id)

        reconciliation_rows: list[dict[str, object]] = []
        counts = {status: 0 for status in InventoryReconciliationStatus}
        for row in current_rows:
            matches: set[str] = set()
            signals: list[str] = []
            for signal in self._identifiers(row):
                found = identifier_index.get(signal, set())
                if found:
                    matches.update(found)
                    signals.append(f"{signal[0]}:{signal[1]}")
            normalized_title = self._normalize_text(row.title)
            title_matches = title_index.get(normalized_title, set())
            if title_matches:
                matches.update(title_matches)
                signals.append(f"title_sha256:{sha256(normalized_title.encode())}")

            author_year_matches: set[str] = set()
            author_year = self._author_year(row)
            if author_year is not None:
                author_year_matches = author_year_index.get(author_year, set())

            if matches:
                status = InventoryReconciliationStatus.PRIOR_EXACT_MATCH
                prior_matches = sorted(matches)
            elif author_year_matches:
                assert author_year is not None
                status = InventoryReconciliationStatus.AUTHOR_YEAR_CANDIDATE
                prior_matches = sorted(author_year_matches)
                signals.append(f"author_year:{author_year[0]}:{author_year[1]}")
            else:
                status = InventoryReconciliationStatus.NEW_CANDIDATE
                prior_matches = []
            counts[status] += 1
            reconciliation_rows.append(
                {
                    "current_screening_id": row.screening_id,
                    "current_record_key": row.record_key,
                    "status": status.value,
                    "matching_signals": sorted(set(signals)),
                    "prior_screening_ids": prior_matches,
                    "prior_record_keys": sorted(
                        prior_by_id[item].record_key for item in prior_matches
                    ),
                    "prior_decision_carried_forward": False,
                }
            )

        created_at = self._clock()
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "code_revision": code_revision,
            "created_at": created_at.isoformat(),
            "current_queue_id": current.queue_id,
            "prior_queue_id": prior.queue_id,
            "study_id": current.study_id,
        }
        reconciliation_id = sha256(canonical_json(identity))
        object_key = (
            f"literature-reconciliation/{current.study_id}/{reconciliation_id}/"
            "inventory-reconciliation.jsonl"
        )
        artifact = b"".join(canonical_json(item) + b"\n" for item in reconciliation_rows)
        if self._store.exists(object_key):
            if self._store.get_bytes(object_key) != artifact:
                raise ImmutableObjectConflictError(f"immutable object conflict: {object_key}")
        else:
            self._store.put_bytes(object_key, artifact, content_type=JSONL_MEDIA_TYPE)
        if sha256(self._store.get_bytes(object_key)) != sha256(artifact):
            raise InventoryReconciliationError("stored reconciliation checksum failed")

        return InventoryReconciliationReceipt(
            reconciliation_id=reconciliation_id,
            study_id=current.study_id,
            current_queue_id=current.queue_id,
            prior_queue_id=prior.queue_id,
            algorithm_version=ALGORITHM_VERSION,
            code_revision=code_revision,
            created_at=created_at,
            artifact_object_key=object_key,
            artifact_sha256=sha256(artifact),
            artifact_size_bytes=len(artifact),
            current_record_count=len(current_rows),
            prior_record_count=len(prior_rows),
            prior_exact_match_count=counts[
                InventoryReconciliationStatus.PRIOR_EXACT_MATCH
            ],
            author_year_candidate_count=counts[
                InventoryReconciliationStatus.AUTHOR_YEAR_CANDIDATE
            ],
            new_candidate_count=counts[InventoryReconciliationStatus.NEW_CANDIDATE],
            verified_at=self._clock(),
            input_checksums_verified=True,
            artifact_checksum_verified=True,
            classification_counts_verified=True,
            prior_decisions_carried_forward=False,
            scientific_conclusions_drawn=False,
        )

    def _load_verified_queue(
        self,
        receipt: ScreeningQueueReceipt,
    ) -> list[ScreeningQueueRecord]:
        if not all(
            (
                receipt.manifest_checksum_verified,
                receipt.artifact_checksums_verified,
                receipt.record_count_verified,
            )
        ):
            raise InventoryReconciliationError("reconciliation requires verified queue receipts")
        body = self._store.get_bytes(receipt.queue_object_key)
        if sha256(body) != receipt.queue_sha256 or len(body) != receipt.queue_size_bytes:
            raise InventoryReconciliationError("queue artifact does not match its receipt")
        try:
            rows = [
                ScreeningQueueRecord.model_validate_json(line)
                for line in body.splitlines()
                if line
            ]
        except (ValidationError, ValueError) as error:
            raise InventoryReconciliationError("queue contains invalid records") from error
        if (
            len(rows) != receipt.summary.input_record_count
            or len({row.screening_id for row in rows}) != len(rows)
            or any(row.decision is not ScreeningDecision.PENDING for row in rows)
        ):
            raise InventoryReconciliationError("queue invariants failed")
        return rows

    @staticmethod
    def _identifiers(row: ScreeningQueueRecord) -> set[tuple[str, str]]:
        values: set[tuple[str, str]] = set()
        if row.pmid:
            values.add(("pmid", row.pmid.strip().lower()))
        if row.pmcid:
            values.add(("pmcid", row.pmcid.strip().lower()))
        if row.doi:
            doi = row.doi.strip().lower()
            doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
            values.add(("doi", doi))
        return values

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).casefold()
        return " ".join(re.findall(r"[a-z0-9]+", normalized))

    @classmethod
    def _author_year(cls, row: ScreeningQueueRecord) -> tuple[str, int] | None:
        if not row.authors or row.publication_year is None:
            return None
        first_author = cls._normalize_text(row.authors[0])
        surname = first_author.split()[0] if first_author else ""
        return (surname, row.publication_year) if surname else None
