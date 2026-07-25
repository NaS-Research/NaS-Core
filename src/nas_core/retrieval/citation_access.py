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
