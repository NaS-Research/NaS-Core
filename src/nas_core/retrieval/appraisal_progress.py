"""Deterministic full-text retrieval and appraisal progress reconciliation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from nas_core.domain.appraisal import (
    AppraisalCompletionStatus,
    EvidenceRole,
    FullTextAppraisal,
    FullTextAppraisalProgress,
    FullTextAppraisalProgressRecord,
    FullTextInventory,
    FullTextRetrievalReceipt,
    load_full_text_appraisal,
    load_full_text_retrieval_receipt,
)


class AppraisalProgressError(RuntimeError):
    """Raised when receipts and appraisals do not form one coherent state."""


class FullTextAppraisalProgressService:
    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))

    def build(
        self,
        inventory: FullTextInventory,
        *,
        retrieval_receipt_paths: Sequence[Path],
        appraisal_paths: Sequence[Path],
    ) -> FullTextAppraisalProgress:
        inventory_by_id = {item.screening_id: item for item in inventory.records}
        receipts = self._load_unique_receipts(retrieval_receipt_paths)
        appraisals = self._load_unique_appraisals(appraisal_paths)
        unknown = (set(receipts) | set(appraisals)) - set(inventory_by_id)
        if unknown:
            raise AppraisalProgressError("artifact exists outside current founder inclusions")

        progress_records: list[FullTextAppraisalProgressRecord] = []
        for screening_id, item in inventory_by_id.items():
            receipt = receipts.get(screening_id)
            appraisal = appraisals.get(screening_id)
            if receipt is None and appraisal is not None:
                raise AppraisalProgressError("appraisal lacks a verified full-text receipt")
            if receipt is not None:
                self._verify_receipt(inventory, item.title, receipt)
            if (
                appraisal is not None
                and receipt is not None
                and (
                    appraisal.study_id != inventory.study_id
                    or appraisal.title != receipt.title
                    or appraisal.full_text_source_url != receipt.source_url
                    or appraisal.full_text_sha256 != receipt.full_text_sha256
                )
            ):
                raise AppraisalProgressError(
                    "appraisal identity does not match verified full-text receipt"
                )
            status = AppraisalCompletionStatus.AWAITING_FULL_TEXT
            if receipt is not None:
                status = AppraisalCompletionStatus.READY_FOR_APPRAISAL
            if appraisal is not None:
                status = AppraisalCompletionStatus.COMPLETED
            progress_records.append(
                FullTextAppraisalProgressRecord(
                    screening_id=screening_id,
                    title=item.title,
                    pmcid=item.pmcid,
                    status=status,
                    retrieval_id=receipt.retrieval_id if receipt else None,
                    full_text_sha256=receipt.full_text_sha256 if receipt else None,
                    appraisal_version=appraisal.appraisal_version if appraisal else None,
                    evidence_role=appraisal.evidence_role if appraisal else None,
                )
            )

        return FullTextAppraisalProgress(
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            generated_at=self._clock(),
            provisional_inclusion_count=len(progress_records),
            full_texts_retrieved=len(receipts),
            appraisals_completed=len(appraisals),
            anchor_count=self._role_count(progress_records, EvidenceRole.ANCHOR),
            supporting_count=self._role_count(progress_records, EvidenceRole.SUPPORTING),
            context_only_count=self._role_count(progress_records, EvidenceRole.CONTEXT_ONLY),
            excluded_count=self._role_count(progress_records, EvidenceRole.EXCLUDED),
            records=progress_records,
        )

    @staticmethod
    def _load_unique_receipts(
        paths: Sequence[Path],
    ) -> dict[str, FullTextRetrievalReceipt]:
        receipts: dict[str, FullTextRetrievalReceipt] = {}
        for path in paths:
            receipt = load_full_text_retrieval_receipt(path)
            if receipt.screening_id in receipts:
                raise AppraisalProgressError("duplicate full-text retrieval receipt")
            receipts[receipt.screening_id] = receipt
        return receipts

    @staticmethod
    def _load_unique_appraisals(paths: Sequence[Path]) -> dict[str, FullTextAppraisal]:
        appraisals: dict[str, FullTextAppraisal] = {}
        for path in paths:
            appraisal = load_full_text_appraisal(path)
            if appraisal.screening_id in appraisals:
                raise AppraisalProgressError("duplicate completed appraisal")
            appraisals[appraisal.screening_id] = appraisal
        return appraisals

    @staticmethod
    def _verify_receipt(
        inventory: FullTextInventory,
        expected_title: str,
        receipt: FullTextRetrievalReceipt,
    ) -> None:
        if (
            receipt.study_id != inventory.study_id
            or receipt.queue_id != inventory.queue_id
            or receipt.progress_id != inventory.progress_id
            or receipt.title != expected_title
            or not receipt.manifest_checksum_verified
            or not receipt.full_text_checksum_verified
            or not receipt.article_identity_verified
            or not receipt.license_verified
            or receipt.scientific_conclusions_drawn
        ):
            raise AppraisalProgressError("full-text receipt failed progress reconciliation")

    @staticmethod
    def _role_count(
        records: Sequence[FullTextAppraisalProgressRecord], role: EvidenceRole
    ) -> int:
        return sum(item.evidence_role is role for item in records)
