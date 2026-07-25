"""Activate a founder-approved evidence-cap amendment and build its appraisal queue."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from nas_core.domain.appraisal import (
    FullTextAccessStatus,
    FullTextInventory,
    FullTextInventoryRecord,
)
from nas_core.domain.citation_reconciliation import (
    CitationInclusionReconciliationReceipt,
)
from nas_core.domain.evidence_amendment import (
    CitationAppraisalQueueRecord,
    CitationAppraisalRoute,
    EvidenceCapAmendmentActivationReceipt,
    EvidenceCapAmendmentApproval,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

JSON_MEDIA_TYPE = "application/json"


class EvidenceCapAmendmentError(RuntimeError):
    """Raised when an evidence-cap amendment cannot be activated safely."""


class EvidenceCapAmendmentActivationService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def activate(
        self,
        approval: EvidenceCapAmendmentApproval,
        reconciliation: CitationInclusionReconciliationReceipt,
        *,
        amendment_path: Path,
        reconciliation_receipt_path: Path,
        code_revision: str,
        activated_at: datetime | None = None,
    ) -> EvidenceCapAmendmentActivationReceipt:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise EvidenceCapAmendmentError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        if sha256(amendment_path.read_bytes()) != approval.amendment_sha256:
            raise EvidenceCapAmendmentError("approved amendment checksum failed")
        if (
            sha256(reconciliation_receipt_path.read_bytes())
            != approval.reconciliation_receipt_sha256
        ):
            raise EvidenceCapAmendmentError(
                "approved reconciliation receipt checksum failed"
            )
        if (
            approval.study_id != reconciliation.study_id
            or approval.reconciliation_id != reconciliation.reconciliation_id
        ):
            raise EvidenceCapAmendmentError(
                "approval and reconciliation identities differ"
            )
        body = self._store.get_bytes(reconciliation.reconciliation_object.object_key)
        if (
            len(body) != reconciliation.reconciliation_object.size_bytes
            or sha256(body) != reconciliation.reconciliation_object.sha256
        ):
            raise EvidenceCapAmendmentError(
                "citation reconciliation object checksum failed"
            )
        rows = self._load_rows(body)
        queue = [self._route(row) for row in rows]
        net_new = [
            row for row in queue if row.route is not CitationAppraisalRoute.REUSE_PRIOR_APPRAISAL
        ]
        prior = len(queue) - len(net_new)
        if (
            len(queue) != reconciliation.confirmed_inclusion_count
            or len(net_new) != reconciliation.net_new_count
            or prior != reconciliation.prior_appraisal_match_count
        ):
            raise EvidenceCapAmendmentError(
                "activation queue does not reconcile with confirmed inclusions"
            )
        timestamp = activated_at or datetime.now(UTC)
        identity = {
            "amendment_sha256": approval.amendment_sha256,
            "approved_at": approval.approved_at.isoformat(),
            "code_revision": code_revision,
            "reconciliation_id": reconciliation.reconciliation_id,
            "study_id": approval.study_id,
        }
        activation_id = sha256(canonical_json(identity))
        queue_body = canonical_json(
            [
                item.model_dump(mode="json", exclude_none=True)
                for item in sorted(queue, key=lambda item: item.record_key)
            ]
        )
        key = (
            f"evidence-review/{approval.study_id}/protocol-{approval.amendment_version}/"
            f"citation-pass-0001-appraisal-queue-{activation_id}.json"
        )
        queue_object = self._store_object(key, queue_body)
        repository = sum(
            item.route is CitationAppraisalRoute.REPOSITORY_CANDIDATE
            for item in queue
        )
        access = sum(
            item.route is CitationAppraisalRoute.ACCESS_CHECK_REQUIRED
            for item in queue
        )
        return EvidenceCapAmendmentActivationReceipt(
            activation_id=activation_id,
            study_id=approval.study_id,
            prior_protocol_version=approval.prior_protocol_version,
            active_protocol_version=approval.amendment_version,
            code_revision=code_revision,
            approved_at=approval.approved_at,
            activated_at=timestamp,
            founder_id=approval.founder_id,
            amendment_sha256=approval.amendment_sha256,
            reconciliation_id=reconciliation.reconciliation_id,
            reconciliation_receipt_sha256=approval.reconciliation_receipt_sha256,
            confirmed_inclusion_count=len(queue),
            repository_candidate_count=repository,
            access_check_required_count=access,
            prior_appraisal_reuse_count=prior,
            net_new_count=len(net_new),
            core_synthesis_maximum=approval.core_synthesis_maximum,
            queue_object=queue_object,
            amendment_checksum_verified=True,
            reconciliation_checksum_verified=True,
            count_invariants_verified=True,
            founder_authorized=True,
            uncapped_saturation_inventory_active=True,
            founder_decisions_changed=0,
            molecular_data_access_authorized=False,
            outcome_data_access_authorized=False,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _load_rows(body: bytes) -> list[dict[str, object]]:
        try:
            rows = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise EvidenceCapAmendmentError(
                "citation reconciliation object is not valid JSON"
            ) from error
        if not isinstance(rows, list) or any(
            not isinstance(row, dict)
            or row.get("disposition") not in {"active_inventory", "prior_appraisal", "net_new"}
            for row in rows
        ):
            raise EvidenceCapAmendmentError(
                "citation reconciliation rows are invalid"
            )
        return rows

    @staticmethod
    def _route(row: dict[str, object]) -> CitationAppraisalQueueRecord:
        disposition = row["disposition"]
        pmcid = row.get("pmcid")
        if disposition == "active_inventory":
            raise EvidenceCapAmendmentError(
                "active-inventory citation cannot enter the new appraisal queue"
            )
        if disposition == "prior_appraisal":
            route = CitationAppraisalRoute.REUSE_PRIOR_APPRAISAL
        elif isinstance(pmcid, str) and pmcid:
            route = CitationAppraisalRoute.REPOSITORY_CANDIDATE
        else:
            route = CitationAppraisalRoute.ACCESS_CHECK_REQUIRED
        return CitationAppraisalQueueRecord(
            record_key=str(row["record_key"]),
            title=str(row["title"]),
            pmid=str(row["pmid"]) if row.get("pmid") else None,
            pmcid=str(pmcid) if pmcid else None,
            doi=str(row["doi"]) if row.get("doi") else None,
            route=route,
            matched_screening_id=(
                str(row["matched_screening_id"])
                if row.get("matched_screening_id")
                else None
            ),
            founder_inclusion_preserved=True,
            scientific_conclusions_drawn=False,
        )

    def _store_object(self, key: str, body: bytes) -> StoredObject:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
        else:
            self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
        stored = self._store.get_bytes(key)
        if stored != body:
            raise EvidenceCapAmendmentError("stored appraisal queue changed")
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )


class CitationAccessInventoryService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def build(
        self,
        activation: EvidenceCapAmendmentActivationReceipt,
    ) -> FullTextInventory:
        body = self._store.get_bytes(activation.queue_object.object_key)
        if (
            len(body) != activation.queue_object.size_bytes
            or sha256(body) != activation.queue_object.sha256
        ):
            raise EvidenceCapAmendmentError("amendment appraisal queue checksum failed")
        try:
            payload = json.loads(body)
            queue = [
                CitationAppraisalQueueRecord.model_validate(row) for row in payload
            ]
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise EvidenceCapAmendmentError(
                "amendment appraisal queue is invalid"
            ) from error
        net_new = [
            row
            for row in queue
            if row.route is not CitationAppraisalRoute.REUSE_PRIOR_APPRAISAL
        ]
        records = [
            FullTextInventoryRecord(
                screening_id=sha256(
                    canonical_json(
                        {
                            "activation_id": activation.activation_id,
                            "record_key": item.record_key,
                        }
                    )
                ),
                record_key=item.record_key,
                title=item.title,
                pmid=item.pmid,
                pmcid=item.pmcid,
                doi=item.doi,
                access_status=(
                    FullTextAccessStatus.REPOSITORY_CANDIDATE
                    if item.route is CitationAppraisalRoute.REPOSITORY_CANDIDATE
                    else FullTextAccessStatus.ACCESS_CHECK_REQUIRED
                ),
            )
            for item in net_new
        ]
        repository_count = sum(
            item.access_status is FullTextAccessStatus.REPOSITORY_CANDIDATE
            for item in records
        )
        if (
            len(records) != activation.net_new_count
            or repository_count != activation.repository_candidate_count
        ):
            raise EvidenceCapAmendmentError(
                "citation access inventory does not reconcile with activation"
            )
        return FullTextInventory(
            inventory_version="1.0.0",
            study_id=activation.study_id,
            queue_id=activation.activation_id,
            progress_id=activation.reconciliation_id,
            provisional_inclusion_count=len(records),
            repository_candidate_count=repository_count,
            access_check_required_count=len(records) - repository_count,
            records=records,
            full_texts_retrieved=0,
            appraisals_completed=0,
            scientific_conclusions_drawn=False,
        )
