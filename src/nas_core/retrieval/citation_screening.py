"""Verified deduplication boundary between citation retrieval and founder screening."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import TypeAdapter, ValidationError

from nas_core.domain.citation_chain import (
    CitationCandidate,
    CitationChainReceipt,
    CitationScreeningDisposition,
    CitationScreeningInventoryRecord,
    CitationScreeningPreparationReceipt,
)
from nas_core.domain.literature import BibliographicRecord, LiteratureSearchReceipt
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "citation-screening-preparation-1.0.0"
JSON_MEDIA_TYPE = "application/json"
_CANDIDATES = TypeAdapter(list[CitationCandidate])
_PRIOR_RECORDS = TypeAdapter(list[BibliographicRecord])


class CitationScreeningPreparationError(RuntimeError):
    """Raised when citation-screening inputs or deduplication invariants fail."""


class CitationScreeningPreparationService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def prepare(
        self,
        citation_receipt: CitationChainReceipt,
        prior_receipt: LiteratureSearchReceipt,
        *,
        code_revision: str,
    ) -> CitationScreeningPreparationReceipt:
        self._validate_inputs(citation_receipt, prior_receipt, code_revision)
        candidates = self._load_candidates(citation_receipt)
        prior_records = self._load_prior_records(prior_receipt)
        prior_by_pmid = {
            record.pmid: record.record_key for record in prior_records if record.pmid
        }
        prior_by_title = {
            self.normalize_title(record.title): record.record_key for record in prior_records
        }

        records: list[CitationScreeningInventoryRecord] = []
        canonical_by_title: dict[str, str] = {}
        for candidate in sorted(candidates, key=self._candidate_sort_key):
            normalized_title = self.normalize_title(candidate.title)
            prior_key = (
                prior_by_pmid.get(candidate.external_id)
                if candidate.source == "MED"
                else None
            ) or prior_by_title.get(normalized_title)
            if prior_key:
                disposition = CitationScreeningDisposition.ALREADY_SCREENED
                canonical_key = prior_key
                duplicate_key = None
            elif normalized_title in canonical_by_title:
                disposition = CitationScreeningDisposition.DUPLICATE_CANDIDATE
                canonical_key = canonical_by_title[normalized_title]
                duplicate_key = canonical_key
            else:
                disposition = CitationScreeningDisposition.REQUIRES_SCREENING
                canonical_key = candidate.record_key
                duplicate_key = None
                canonical_by_title[normalized_title] = canonical_key
            records.append(
                CitationScreeningInventoryRecord(
                    record_key=candidate.record_key,
                    canonical_record_key=canonical_key,
                    title=candidate.title,
                    normalized_title=normalized_title,
                    disposition=disposition,
                    matched_prior_record_key=prior_key,
                    duplicate_of_record_key=duplicate_key,
                    directions=candidate.directions,
                    seed_evidence_ids=candidate.seed_evidence_ids,
                )
            )

        records.sort(key=lambda item: item.record_key)
        required_keys = {
            item.record_key
            for item in records
            if item.disposition is CitationScreeningDisposition.REQUIRES_SCREENING
        }
        screening_candidates = [
            candidate.model_dump(mode="json", exclude_none=True)
            for candidate in sorted(candidates, key=lambda item: item.record_key)
            if candidate.record_key in required_keys
        ]
        created_at = self._clock()
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "citation_execution_id": citation_receipt.execution_id,
            "code_revision": code_revision,
            "created_at": created_at.isoformat(),
            "prior_search_execution_id": prior_receipt.execution_id,
            "study_id": citation_receipt.study_id,
        }
        preparation_id = sha256(canonical_json(identity))
        prefix = (
            f"citation-screening/{citation_receipt.study_id}/"
            f"pass-{citation_receipt.pass_number:04d}/{preparation_id}"
        )
        inventory_body = canonical_json(
            [item.model_dump(mode="json", exclude_none=True) for item in records]
        )
        candidates_body = canonical_json(screening_candidates)
        inventory_object = self._store_object(
            f"{prefix}/deduplication-inventory.json", inventory_body
        )
        screening_object = self._store_object(
            f"{prefix}/screening-candidates.json", candidates_body
        )
        counts = {
            disposition: sum(item.disposition is disposition for item in records)
            for disposition in CitationScreeningDisposition
        }
        return CitationScreeningPreparationReceipt(
            preparation_id=preparation_id,
            study_id=citation_receipt.study_id,
            pass_number=citation_receipt.pass_number,
            citation_execution_id=citation_receipt.execution_id,
            prior_search_execution_id=prior_receipt.execution_id,
            code_revision=code_revision,
            created_at=created_at,
            verified_at=self._clock(),
            input_candidate_count=len(candidates),
            already_screened_count=counts[CitationScreeningDisposition.ALREADY_SCREENED],
            duplicate_candidate_count=counts[
                CitationScreeningDisposition.DUPLICATE_CANDIDATE
            ],
            requires_screening_count=counts[
                CitationScreeningDisposition.REQUIRES_SCREENING
            ],
            inventory_object=inventory_object,
            screening_candidates_object=screening_object,
            input_checksums_verified=True,
            output_checksums_verified=True,
            count_invariants_verified=True,
        )

    @staticmethod
    def normalize_title(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).casefold()
        tokens = re.findall(r"[a-z0-9]+", normalized)
        if not tokens:
            raise CitationScreeningPreparationError("citation candidate has no usable title")
        return " ".join(tokens)

    @staticmethod
    def _candidate_sort_key(candidate: CitationCandidate) -> tuple[str, int, str]:
        # Prefer the published MED identity over a same-title preprint identity.
        source_priority = 0 if candidate.source == "MED" else 1
        return (
            CitationScreeningPreparationService.normalize_title(candidate.title),
            source_priority,
            candidate.record_key,
        )

    def _load_candidates(
        self, receipt: CitationChainReceipt
    ) -> list[CitationCandidate]:
        body = self._verified_body(receipt.candidates_object)
        try:
            candidates = _CANDIDATES.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationScreeningPreparationError(
                "citation candidates are invalid"
            ) from error
        if len(candidates) != receipt.unique_candidate_count:
            raise CitationScreeningPreparationError(
                "citation candidate count does not match its receipt"
            )
        return candidates

    def _load_prior_records(
        self, receipt: LiteratureSearchReceipt
    ) -> list[BibliographicRecord]:
        body = self._store.get_bytes(receipt.normalized_records_object_key)
        if (
            len(body) != receipt.normalized_records_size_bytes
            or sha256(body) != receipt.normalized_records_sha256
        ):
            raise CitationScreeningPreparationError(
                "prior search inventory does not match its receipt"
            )
        try:
            records = _PRIOR_RECORDS.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationScreeningPreparationError(
                "prior search inventory is invalid"
            ) from error
        if len(records) != receipt.unique_record_count:
            raise CitationScreeningPreparationError(
                "prior search inventory count does not reconcile"
            )
        return records

    def _verified_body(self, stored: StoredObject) -> bytes:
        body = self._store.get_bytes(stored.object_key)
        if len(body) != stored.size_bytes or sha256(body) != stored.sha256:
            raise CitationScreeningPreparationError(
                "citation candidate object does not match its receipt"
            )
        return body

    @staticmethod
    def _validate_inputs(
        citation_receipt: CitationChainReceipt,
        prior_receipt: LiteratureSearchReceipt,
        code_revision: str,
    ) -> None:
        if citation_receipt.study_id != prior_receipt.study_id:
            raise CitationScreeningPreparationError(
                "citation and prior-search receipts identify different studies"
            )
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationScreeningPreparationError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        citation_flags = (
            citation_receipt.manifest_checksum_verified,
            citation_receipt.object_checksums_verified,
            citation_receipt.endpoint_counts_verified,
            citation_receipt.candidate_count_verified,
        )
        prior_flags = (
            prior_receipt.manifest_checksum_verified,
            prior_receipt.object_checksums_verified,
            prior_receipt.object_sizes_verified,
            prior_receipt.record_count_invariants_verified,
        )
        if not all((*citation_flags, *prior_flags)):
            raise CitationScreeningPreparationError(
                "citation screening requires verified input receipts"
            )

    def _store_object(self, key: str, body: bytes) -> StoredObject:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
        else:
            self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
        stored = self._store.get_bytes(key)
        if stored != body:
            raise CitationScreeningPreparationError("stored screening object changed")
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )
