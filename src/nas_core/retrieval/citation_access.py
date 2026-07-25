"""Batch retrieval and fail-closed access accounting for citation full texts."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime

from nas_core.domain.appraisal import (
    FullTextAccessStatus,
    FullTextInventory,
    FullTextInventoryRecord,
    FullTextRetrievalReceipt,
)
from nas_core.domain.citation_access import (
    CitationAccessCheckQueue,
    CitationAccessCheckReason,
    CitationAccessCheckRecord,
    RepositoryAccessAssessmentRecord,
    RepositoryAccessBatchReceipt,
    RepositoryAccessOutcome,
)
from nas_core.ingestion.gdc import RemoteResponseError, canonical_json, sha256
from nas_core.retrieval.full_text_retrieval import (
    FullTextRetrievalError,
    FullTextRetrievalService,
)


class CitationRepositoryAccessService:
    def __init__(
        self,
        *,
        retrieval_service: FullTextRetrievalService,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._retrieval = retrieval_service
        self._clock = clock or (lambda: datetime.now(UTC))

    def assess(
        self,
        inventory: FullTextInventory,
        *,
        code_revision: str,
        receipt_directory: str,
    ) -> tuple[RepositoryAccessBatchReceipt, list[FullTextRetrievalReceipt]]:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ValueError("code revision must be a 7-to-40 character Git SHA")
        candidates = [
            item
            for item in inventory.records
            if item.access_status is FullTextAccessStatus.REPOSITORY_CANDIDATE
        ]
        assessments: list[RepositoryAccessAssessmentRecord] = []
        receipts: list[FullTextRetrievalReceipt] = []
        for record in candidates:
            assert record.pmcid is not None
            try:
                manifest = self._retrieval.retrieve(
                    record,
                    study_id=inventory.study_id,
                    queue_id=inventory.queue_id,
                    progress_id=inventory.progress_id,
                    code_revision=code_revision,
                )
                receipt = self._retrieval.verify(manifest)
            except RemoteResponseError as error:
                outcome = self._remote_outcome(str(error))
                assessments.append(
                    self._failure_record(record, outcome, str(error))
                )
                continue
            except FullTextRetrievalError as error:
                assessments.append(
                    self._failure_record(
                        record,
                        self._retrieval_outcome(str(error)),
                        str(error),
                    )
                )
                continue
            receipts.append(receipt)
            assessments.append(
                RepositoryAccessAssessmentRecord(
                    screening_id=record.screening_id,
                    record_key=record.record_key,
                    pmcid=record.pmcid,
                    title=record.title,
                    outcome=RepositoryAccessOutcome.RETRIEVED,
                    retrieval_receipt_path=(
                        f"{receipt_directory.rstrip('/')}/{record.pmcid}.yaml"
                    ),
                    durable_full_text_stored=True,
                    scientific_conclusions_drawn=False,
                )
            )
        assessed_at = self._clock()
        identity = {
            "assessed_at": assessed_at.isoformat(),
            "code_revision": code_revision,
            "inventory_progress_id": inventory.progress_id,
            "inventory_queue_id": inventory.queue_id,
            "outcomes": [
                {
                    "outcome": item.outcome,
                    "screening_id": item.screening_id,
                }
                for item in assessments
            ],
            "study_id": inventory.study_id,
        }
        retrieved_count = len(receipts)
        return (
            RepositoryAccessBatchReceipt(
                batch_id=sha256(canonical_json(identity)),
                study_id=inventory.study_id,
                inventory_queue_id=inventory.queue_id,
                inventory_progress_id=inventory.progress_id,
                code_revision=code_revision,
                assessed_at=assessed_at,
                repository_candidate_count=len(candidates),
                retrieved_count=retrieved_count,
                access_check_required_count=len(candidates) - retrieved_count,
                records=assessments,
                complete_coverage_verified=True,
                identity_and_license_fail_closed=True,
                founder_decisions_changed=0,
                scientific_conclusions_drawn=False,
            ),
            receipts,
        )

    @staticmethod
    def _failure_record(
        record: FullTextInventoryRecord,
        outcome: RepositoryAccessOutcome,
        reason: str,
    ) -> RepositoryAccessAssessmentRecord:
        assert record.pmcid is not None
        return RepositoryAccessAssessmentRecord(
            screening_id=record.screening_id,
            record_key=record.record_key,
            pmcid=record.pmcid,
            title=record.title,
            outcome=outcome,
            reason=reason,
            durable_full_text_stored=False,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _remote_outcome(reason: str) -> RepositoryAccessOutcome:
        if "status 404" in reason or "status 410" in reason:
            return RepositoryAccessOutcome.FULL_TEXT_UNAVAILABLE
        return RepositoryAccessOutcome.REMOTE_ERROR

    @staticmethod
    def _retrieval_outcome(reason: str) -> RepositoryAccessOutcome:
        lowered = reason.casefold()
        if "license" in lowered:
            return RepositoryAccessOutcome.LICENSE_NOT_APPROVED
        if "identity" in lowered or "does not match" in lowered:
            return RepositoryAccessOutcome.IDENTITY_MISMATCH
        return RepositoryAccessOutcome.METADATA_INVALID


class CitationAccessCheckQueueService:
    _REASON_MAP = {
        RepositoryAccessOutcome.FULL_TEXT_UNAVAILABLE: (
            CitationAccessCheckReason.FULL_TEXT_UNAVAILABLE
        ),
        RepositoryAccessOutcome.LICENSE_NOT_APPROVED: (
            CitationAccessCheckReason.LICENSE_NOT_APPROVED
        ),
        RepositoryAccessOutcome.IDENTITY_MISMATCH: (
            CitationAccessCheckReason.IDENTITY_MISMATCH
        ),
        RepositoryAccessOutcome.METADATA_INVALID: (
            CitationAccessCheckReason.METADATA_INVALID
        ),
        RepositoryAccessOutcome.REMOTE_ERROR: CitationAccessCheckReason.REMOTE_ERROR,
    }

    def build(
        self,
        inventory: FullTextInventory,
        batch: RepositoryAccessBatchReceipt,
        *,
        code_revision: str,
    ) -> CitationAccessCheckQueue:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ValueError("code revision must be a 7-to-40 character Git SHA")
        if (
            inventory.study_id != batch.study_id
            or inventory.queue_id != batch.inventory_queue_id
            or inventory.progress_id != batch.inventory_progress_id
        ):
            raise ValueError("inventory and repository access batch identities differ")
        by_screening_id = {item.screening_id: item for item in inventory.records}
        records = [
            CitationAccessCheckRecord(
                screening_id=item.screening_id,
                record_key=item.record_key,
                title=item.title,
                pmid=item.pmid,
                doi=item.doi,
                reason=CitationAccessCheckReason.NO_REPOSITORY_IDENTIFIER,
                durable_full_text_stored=False,
                final_access_decision_recorded=False,
                scientific_conclusions_drawn=False,
            )
            for item in inventory.records
            if item.access_status is FullTextAccessStatus.ACCESS_CHECK_REQUIRED
        ]
        for assessment in batch.records:
            if assessment.outcome is RepositoryAccessOutcome.RETRIEVED:
                continue
            inventory_record = by_screening_id.get(assessment.screening_id)
            if inventory_record is None:
                raise ValueError("repository access batch references an unknown record")
            records.append(
                CitationAccessCheckRecord(
                    screening_id=inventory_record.screening_id,
                    record_key=inventory_record.record_key,
                    title=inventory_record.title,
                    pmid=inventory_record.pmid,
                    pmcid=inventory_record.pmcid,
                    doi=inventory_record.doi,
                    reason=self._REASON_MAP[assessment.outcome],
                    prior_repository_detail=assessment.reason,
                    durable_full_text_stored=False,
                    final_access_decision_recorded=False,
                    scientific_conclusions_drawn=False,
                )
            )
        expected = (
            inventory.access_check_required_count + batch.access_check_required_count
        )
        if len(records) != expected:
            raise ValueError("access-check queue count does not reconcile")
        queue_id = sha256(
            canonical_json(
                {
                    "code_revision": code_revision,
                    "inventory_queue_id": inventory.queue_id,
                    "repository_batch_id": batch.batch_id,
                    "study_id": inventory.study_id,
                }
            )
        )
        return CitationAccessCheckQueue(
            queue_version="1.0.0",
            queue_id=queue_id,
            study_id=inventory.study_id,
            code_revision=code_revision,
            inventory_queue_id=inventory.queue_id,
            repository_batch_id=batch.batch_id,
            record_count=len(records),
            records=sorted(records, key=lambda item: item.record_key),
            complete_coverage_verified=True,
            final_access_decisions_recorded=0,
            scientific_conclusions_drawn=False,
        )
