"""Deterministic full-text retrieval and appraisal progress reconciliation."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from nas_core.domain.appraisal import (
    AppraisalCompletionStatus,
    EvidenceRole,
    FullTextAccessDecision,
    FullTextAppraisal,
    FullTextAppraisalProgress,
    FullTextAppraisalProgressRecord,
    FullTextDuplicateDecision,
    FullTextInventory,
    FullTextInventoryRecord,
    FullTextReadOnlyReviewReceipt,
    FullTextRetrievalReceipt,
    load_full_text_access_decision,
    load_full_text_appraisal,
    load_full_text_duplicate_decision,
    load_full_text_read_only_review_receipt,
    load_full_text_retrieval_receipt,
)
from nas_core.retrieval.full_text_retrieval import normalize_article_title


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
        read_only_review_receipt_paths: Sequence[Path] = (),
        appraisal_source_receipt_paths: Sequence[Path] = (),
        access_decision_paths: Sequence[Path] = (),
        duplicate_decision_paths: Sequence[Path] = (),
    ) -> FullTextAppraisalProgress:
        inventory_by_id = {item.screening_id: item for item in inventory.records}
        receipts = self._load_unique_receipts(retrieval_receipt_paths)
        read_only_receipts = self._load_unique_read_only_receipts(
            read_only_review_receipt_paths
        )
        appraisal_source_receipts = self._load_unique_appraisal_source_receipts(
            appraisal_source_receipt_paths
        )
        appraisals = self._load_unique_appraisals(appraisal_paths)
        access_decisions = self._load_unique_access_decisions(access_decision_paths)
        duplicate_decisions = self._load_unique_duplicate_decisions(
            duplicate_decision_paths
        )
        unknown = (
            set(receipts)
            | set(read_only_receipts)
            | set(appraisal_source_receipts)
            | set(appraisals)
            | set(access_decisions)
            | set(duplicate_decisions)
        ) - set(inventory_by_id)
        if unknown:
            raise AppraisalProgressError("artifact exists outside current founder inclusions")

        progress_records: list[FullTextAppraisalProgressRecord] = []
        for screening_id, item in inventory_by_id.items():
            receipt = receipts.get(screening_id)
            read_only_receipt = read_only_receipts.get(screening_id)
            appraisal_source_receipt = appraisal_source_receipts.get(screening_id)
            appraisal = appraisals.get(screening_id)
            access_decision = access_decisions.get(screening_id)
            duplicate_decision = duplicate_decisions.get(screening_id)
            if receipt is not None and read_only_receipt is not None:
                raise AppraisalProgressError(
                    "record cannot have both durable and read-only full-text receipts"
                )
            if duplicate_decision is not None and any(
                value is not None
                for value in (receipt, read_only_receipt, access_decision)
            ):
                raise AppraisalProgressError(
                    "record cannot combine duplicate resolution with access or review state"
                )
            if receipt is not None and access_decision is not None:
                raise AppraisalProgressError(
                    "record cannot be both access-restricted and durably retrieved"
                )
            if receipt is None and read_only_receipt is None and appraisal is not None:
                raise AppraisalProgressError("appraisal lacks a verified full-text receipt")
            if appraisal_source_receipt is not None and appraisal is None:
                raise AppraisalProgressError(
                    "appraisal-source receipt requires a completed appraisal"
                )
            if receipt is not None:
                self._verify_receipt(inventory, item.title, receipt)
            if read_only_receipt is not None:
                self._verify_read_only_receipt(
                    inventory, item.title, item.pmcid, read_only_receipt
                )
            if appraisal_source_receipt is not None:
                self._verify_read_only_receipt(
                    inventory,
                    item.title,
                    item.pmcid,
                    appraisal_source_receipt,
                )
            appraisal_receipt = appraisal_source_receipt or read_only_receipt
            source_title = (
                appraisal_receipt.title
                if appraisal_receipt is not None
                else receipt.title
                if receipt is not None
                else None
            )
            source_url = (
                appraisal_receipt.source_url
                if appraisal_receipt is not None
                else receipt.source_url
                if receipt is not None
                else None
            )
            source_sha256 = (
                appraisal_receipt.content_sha256
                if appraisal_receipt is not None
                else receipt.full_text_sha256
                if receipt is not None
                else None
            )
            if (
                appraisal is not None
                and (
                    appraisal.study_id != inventory.study_id
                    or normalize_article_title(appraisal.title)
                    != normalize_article_title(source_title)
                    or appraisal.pmid != item.pmid
                    or (appraisal.doi or "").casefold()
                    != (item.doi or "").casefold()
                    or appraisal.full_text_source_url != source_url
                    or appraisal.full_text_sha256 != source_sha256
                )
            ):
                raise AppraisalProgressError(
                    "appraisal identity does not match verified full-text receipt "
                    f"for {screening_id}"
                )
            access_source_sha256 = (
                receipt.full_text_sha256
                if receipt is not None
                else read_only_receipt.content_sha256
                if read_only_receipt is not None
                else None
            )
            status = AppraisalCompletionStatus.AWAITING_FULL_TEXT
            if access_decision is not None and read_only_receipt is None:
                self._verify_access_decision(inventory, item, access_decision)
                status = AppraisalCompletionStatus.ACCESS_RESTRICTED
            elif access_decision is not None:
                self._verify_access_decision(inventory, item, access_decision)
            if duplicate_decision is not None:
                self._verify_duplicate_decision(
                    inventory, item.title, inventory_by_id, duplicate_decision
                )
                status = AppraisalCompletionStatus.DUPLICATE_RESOLVED
            if receipt is not None or read_only_receipt is not None:
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
                    read_only_review_id=(
                        read_only_receipt.review_id if read_only_receipt else None
                    ),
                    full_text_sha256=access_source_sha256,
                    appraisal_source_review_id=(
                        appraisal_source_receipt.review_id
                        if appraisal_source_receipt
                        else None
                    ),
                    appraisal_source_sha256=(
                        appraisal_source_receipt.content_sha256
                        if appraisal_source_receipt
                        else None
                    ),
                    appraisal_version=appraisal.appraisal_version if appraisal else None,
                    evidence_role=appraisal.evidence_role if appraisal else None,
                    observed_license=(
                        access_decision.observed_license
                        if access_decision and read_only_receipt is None
                        else None
                    ),
                    canonical_screening_id=(
                        duplicate_decision.canonical_screening_id
                        if duplicate_decision
                        else None
                    ),
                    duplicate_relationship=(
                        duplicate_decision.relationship if duplicate_decision else None
                    ),
                )
            )

        return FullTextAppraisalProgress(
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            generated_at=self._clock(),
            provisional_inclusion_count=len(progress_records),
            full_texts_retrieved=len(receipts),
            read_only_full_texts_reviewed=len(read_only_receipts),
            appraisals_completed=len(appraisals),
            access_restricted_count=len(set(access_decisions) - set(read_only_receipts)),
            duplicate_resolved_count=len(duplicate_decisions),
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
    def _load_unique_read_only_receipts(
        paths: Sequence[Path],
    ) -> dict[str, FullTextReadOnlyReviewReceipt]:
        receipts: dict[str, FullTextReadOnlyReviewReceipt] = {}
        for path in paths:
            receipt = load_full_text_read_only_review_receipt(path)
            if receipt.screening_id in receipts:
                raise AppraisalProgressError("duplicate read-only review receipt")
            receipts[receipt.screening_id] = receipt
        return receipts

    @staticmethod
    def _load_unique_appraisal_source_receipts(
        paths: Sequence[Path],
    ) -> dict[str, FullTextReadOnlyReviewReceipt]:
        receipts: dict[str, FullTextReadOnlyReviewReceipt] = {}
        for path in paths:
            receipt = load_full_text_read_only_review_receipt(path)
            if receipt.screening_id in receipts:
                raise AppraisalProgressError("duplicate appraisal-source receipt")
            receipts[receipt.screening_id] = receipt
        return receipts

    @staticmethod
    def _load_unique_access_decisions(
        paths: Sequence[Path],
    ) -> dict[str, FullTextAccessDecision]:
        decisions: dict[str, FullTextAccessDecision] = {}
        for path in paths:
            decision = load_full_text_access_decision(path)
            if decision.screening_id in decisions:
                raise AppraisalProgressError("duplicate full-text access decision")
            decisions[decision.screening_id] = decision
        return decisions

    @staticmethod
    def _load_unique_duplicate_decisions(
        paths: Sequence[Path],
    ) -> dict[str, FullTextDuplicateDecision]:
        decisions: dict[str, FullTextDuplicateDecision] = {}
        for path in paths:
            decision = load_full_text_duplicate_decision(path)
            if decision.screening_id in decisions:
                raise AppraisalProgressError("duplicate full-text duplicate decision")
            decisions[decision.screening_id] = decision
        return decisions

    @staticmethod
    def _verify_access_decision(
        inventory: FullTextInventory,
        inventory_record: FullTextInventoryRecord,
        decision: FullTextAccessDecision,
    ) -> None:
        expected_title = inventory_record.title
        expected_pmcid = inventory_record.pmcid
        expected_pmid = inventory_record.pmid
        expected_doi = inventory_record.doi
        if (
            decision.study_id != inventory.study_id
            or decision.title != expected_title
            or (
                decision.pmcid is not None
                and decision.pmcid != expected_pmcid
            )
            or (
                decision.pmid is not None
                and decision.pmid != expected_pmid
            )
            or (
                decision.doi is not None
                and decision.doi.casefold() != (expected_doi or "").casefold()
            )
            or decision.durable_full_text_stored
            or decision.scientific_conclusions_drawn
        ):
            raise AppraisalProgressError("access decision failed progress reconciliation")

    @staticmethod
    def _verify_duplicate_decision(
        inventory: FullTextInventory,
        expected_title: str,
        inventory_by_id: Mapping[str, object],
        decision: FullTextDuplicateDecision,
    ) -> None:
        if (
            decision.study_id != inventory.study_id
            or decision.title != expected_title
            or decision.canonical_screening_id not in inventory_by_id
            or not decision.founder_authorized
            or decision.scientific_conclusions_drawn
        ):
            raise AppraisalProgressError("duplicate decision failed progress reconciliation")

    @staticmethod
    def _verify_receipt(
        inventory: FullTextInventory,
        expected_title: str,
        receipt: FullTextRetrievalReceipt,
    ) -> None:
        # A retrieval remains valid when later append-only screening batches advance
        # the progress ID, provided the exact record is still a current inclusion.
        # Membership and title are checked against the current inventory before this
        # method; the receipt retains the checkpoint that originally authorized it.
        if (
            receipt.study_id != inventory.study_id
            or receipt.queue_id != inventory.queue_id
            or receipt.title != expected_title
            or not receipt.manifest_checksum_verified
            or not receipt.full_text_checksum_verified
            or not receipt.article_identity_verified
            or not receipt.license_verified
            or receipt.scientific_conclusions_drawn
        ):
            raise AppraisalProgressError("full-text receipt failed progress reconciliation")

    @staticmethod
    def _verify_read_only_receipt(
        inventory: FullTextInventory,
        expected_title: str,
        expected_pmcid: str | None,
        receipt: FullTextReadOnlyReviewReceipt,
    ) -> None:
        # Read-only receipts are likewise durable provenance for their original
        # screening checkpoint. Current-inclusion membership, identity, access, and
        # checksum constraints still fail closed.
        if (
            receipt.study_id != inventory.study_id
            or receipt.queue_id != inventory.queue_id
            or receipt.title != expected_title
            or receipt.pmcid != expected_pmcid
            or not receipt.checksum_verified
            or not receipt.article_identity_verified
            or not receipt.lawful_read_access_verified
            or receipt.durable_full_text_stored
            or receipt.redistribution_authorized
            or receipt.scientific_conclusions_drawn
        ):
            raise AppraisalProgressError(
                "read-only review receipt failed progress reconciliation"
            )

    @staticmethod
    def _role_count(
        records: Sequence[FullTextAppraisalProgressRecord], role: EvidenceRole
    ) -> int:
        return sum(item.evidence_role is role for item in records)
