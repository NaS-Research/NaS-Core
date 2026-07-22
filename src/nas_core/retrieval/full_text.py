"""Verified full-text access inventory derived from founder decisions."""

from __future__ import annotations

from nas_core.domain.appraisal import (
    FullTextAccessStatus,
    FullTextInventory,
    FullTextInventoryRecord,
)
from nas_core.domain.literature import ScreeningProgressReceipt, ScreeningQueueReceipt
from nas_core.retrieval.review import ScreeningReviewService
from nas_core.storage.object_store import ObjectStore


class FullTextInventoryService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._review = ScreeningReviewService(store=store)

    def build(
        self,
        queue_receipt: ScreeningQueueReceipt,
        progress_receipt: ScreeningProgressReceipt,
    ) -> FullTextInventory:
        records = self._review.included_records(
            queue_receipt,
            progress_receipt=progress_receipt,
        )
        inventory_records = [
            FullTextInventoryRecord(
                screening_id=record.screening_id,
                record_key=record.record_key,
                title=record.title,
                publication_year=record.publication_year,
                journal=record.journal,
                pmid=record.pmid,
                pmcid=record.pmcid,
                doi=record.doi,
                bibliographic_open_access_flag=record.is_open_access,
                access_status=(
                    FullTextAccessStatus.REPOSITORY_CANDIDATE
                    if record.pmcid
                    else FullTextAccessStatus.ACCESS_CHECK_REQUIRED
                ),
            )
            for record in records
        ]
        repository_count = sum(
            item.access_status is FullTextAccessStatus.REPOSITORY_CANDIDATE
            for item in inventory_records
        )
        return FullTextInventory(
            study_id=queue_receipt.study_id,
            queue_id=queue_receipt.queue_id,
            progress_id=progress_receipt.progress_id,
            provisional_inclusion_count=len(inventory_records),
            repository_candidate_count=repository_count,
            access_check_required_count=len(inventory_records) - repository_count,
            records=inventory_records,
        )
