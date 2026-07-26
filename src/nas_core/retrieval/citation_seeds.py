"""Build and verify the cumulative founder-included seed set for citation chaining."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from nas_core.domain.appraisal import FullTextInventory
from nas_core.domain.citation_chain import (
    CitationCumulativeSeedReceipt,
    CitationCumulativeSeedRecord,
    CitationSeed,
    CitationSeedOrigin,
)
from nas_core.domain.evidence_amendment import (
    CitationAppraisalQueueRecord,
    EvidenceCapAmendmentActivationReceipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

JSON_MEDIA_TYPE = "application/json"
_QUEUE = TypeAdapter(list[CitationAppraisalQueueRecord])
_SEEDS = TypeAdapter(list[CitationCumulativeSeedRecord])


class CitationCumulativeSeedError(RuntimeError):
    """Raised when cumulative citation seeds cannot be proven from locked inputs."""


class CitationCumulativeSeedService:
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
        direct_inventory: FullTextInventory,
        activation: EvidenceCapAmendmentActivationReceipt,
        *,
        direct_inventory_path: Path,
        activation_receipt_path: Path,
        next_pass_number: int,
        code_revision: str,
    ) -> CitationCumulativeSeedReceipt:
        self._validate_inputs(
            direct_inventory,
            activation,
            next_pass_number=next_pass_number,
            code_revision=code_revision,
        )
        direct_sha = sha256(direct_inventory_path.read_bytes())
        activation_sha = sha256(activation_receipt_path.read_bytes())
        queue = self._load_queue(activation)

        by_pmid: dict[str, CitationCumulativeSeedRecord] = {}
        duplicate_count = 0
        for direct_record in direct_inventory.records:
            if direct_record.pmid is None:
                raise CitationCumulativeSeedError(
                    "every direct founder inclusion requires a PMID"
                )
            by_pmid[direct_record.pmid] = CitationCumulativeSeedRecord(
                evidence_id=f"PMID:{direct_record.pmid}",
                pmid=direct_record.pmid,
                title=direct_record.title,
                origins=[CitationSeedOrigin.DIRECT_SEARCH],
                source_record_keys=[direct_record.record_key],
                founder_inclusion_preserved=True,
            )
        for queue_record in queue:
            if queue_record.pmid is None:
                raise CitationCumulativeSeedError(
                    "every prior-pass founder inclusion requires a PMID"
                )
            prior = by_pmid.get(queue_record.pmid)
            if prior is None:
                by_pmid[queue_record.pmid] = CitationCumulativeSeedRecord(
                    evidence_id=f"PMID:{queue_record.pmid}",
                    pmid=queue_record.pmid,
                    title=queue_record.title,
                    origins=[CitationSeedOrigin.CITATION_PASS],
                    source_record_keys=[queue_record.record_key],
                    founder_inclusion_preserved=True,
                )
                continue
            duplicate_count += 1
            if self._normalized_title(prior.title) != self._normalized_title(
                queue_record.title
            ):
                raise CitationCumulativeSeedError(
                    "duplicate cumulative PMID has conflicting titles"
                )
            by_pmid[queue_record.pmid] = prior.model_copy(
                update={
                    "origins": sorted(
                        {*prior.origins, CitationSeedOrigin.CITATION_PASS}
                    ),
                    "source_record_keys": sorted(
                        {*prior.source_record_keys, queue_record.record_key}
                    ),
                }
            )

        records = sorted(by_pmid.values(), key=lambda item: int(item.pmid))
        seed_body = canonical_json(
            [item.model_dump(mode="json", exclude_none=True) for item in records]
        )
        identity = {
            "activation_id": activation.activation_id,
            "activation_receipt_sha256": activation_sha,
            "code_revision": code_revision,
            "direct_inventory_sha256": direct_sha,
            "next_pass_number": next_pass_number,
            "study_id": direct_inventory.study_id,
        }
        seed_set_id = sha256(canonical_json(identity))
        key = (
            f"citation-chain/{direct_inventory.study_id}/"
            f"pass-{next_pass_number:04d}/seed-set-{seed_set_id}.json"
        )
        stored = self._store_object(key, seed_body)
        created_at = self._clock()
        return CitationCumulativeSeedReceipt(
            seed_set_id=seed_set_id,
            study_id=direct_inventory.study_id,
            next_pass_number=next_pass_number,
            code_revision=code_revision,
            created_at=created_at,
            verified_at=self._clock(),
            direct_inventory_sha256=direct_sha,
            amendment_activation_sha256=activation_sha,
            amendment_activation_id=activation.activation_id,
            direct_inclusion_count=len(direct_inventory.records),
            prior_pass_inclusion_count=len(queue),
            duplicate_pmid_count=duplicate_count,
            cumulative_seed_count=len(records),
            seeds_object=stored,
            input_checksums_verified=True,
            output_checksum_verified=True,
            exact_pmid_deduplication=True,
            all_founder_inclusions_preserved=True,
            molecular_data_access_authorized=False,
            outcome_data_access_authorized=False,
            scientific_conclusions_drawn=False,
        )

    def load_seeds(
        self,
        receipt: CitationCumulativeSeedReceipt,
    ) -> list[CitationSeed]:
        body = self._verified_body(receipt.seeds_object)
        try:
            records = _SEEDS.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationCumulativeSeedError(
                "cumulative citation seed object is invalid"
            ) from error
        if len(records) != receipt.cumulative_seed_count:
            raise CitationCumulativeSeedError(
                "cumulative citation seed count does not match its receipt"
            )
        evidence_ids = [item.evidence_id for item in records]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise CitationCumulativeSeedError(
                "cumulative citation seed object contains duplicate PMIDs"
            )
        return [
            CitationSeed(
                evidence_id=item.evidence_id,
                pmid=item.pmid,
                title=item.title,
            )
            for item in records
        ]

    def _load_queue(
        self,
        activation: EvidenceCapAmendmentActivationReceipt,
    ) -> list[CitationAppraisalQueueRecord]:
        body = self._verified_body(activation.queue_object)
        try:
            queue = _QUEUE.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationCumulativeSeedError(
                "evidence-cap activation queue is invalid"
            ) from error
        if len(queue) != activation.confirmed_inclusion_count:
            raise CitationCumulativeSeedError(
                "evidence-cap queue does not cover every confirmed inclusion"
            )
        return queue

    def _verified_body(self, stored: StoredObject) -> bytes:
        body = self._store.get_bytes(stored.object_key)
        if len(body) != stored.size_bytes or sha256(body) != stored.sha256:
            raise CitationCumulativeSeedError(
                "cumulative citation input does not match its receipt"
            )
        return body

    def _store_object(self, key: str, body: bytes) -> StoredObject:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
        else:
            self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
        stored = self._store.get_bytes(key)
        if stored != body:
            raise CitationCumulativeSeedError("stored cumulative seed object changed")
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
            record_ids=[item.evidence_id for item in _SEEDS.validate_json(body)],
        )

    @staticmethod
    def _normalized_title(value: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))

    @staticmethod
    def _validate_inputs(
        direct_inventory: FullTextInventory,
        activation: EvidenceCapAmendmentActivationReceipt,
        *,
        next_pass_number: int,
        code_revision: str,
    ) -> None:
        if direct_inventory.study_id != activation.study_id:
            raise CitationCumulativeSeedError(
                "direct inventory and amendment activation identify different studies"
            )
        if next_pass_number != 2:
            raise CitationCumulativeSeedError(
                "this cumulative seed builder is bound to citation pass 2"
            )
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationCumulativeSeedError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        if not (
            activation.founder_authorized
            and activation.uncapped_saturation_inventory_active
            and activation.count_invariants_verified
        ):
            raise CitationCumulativeSeedError(
                "cumulative seeds require an active founder-authorized uncapped inventory"
            )
