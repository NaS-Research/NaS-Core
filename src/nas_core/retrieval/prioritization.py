"""Transparent, zero-cost prioritization for human literature screening."""

from __future__ import annotations

import re
from dataclasses import dataclass

from nas_core.domain.literature import (
    ScreeningPriorityBatch,
    ScreeningPriorityRecord,
    ScreeningPriorityTier,
    ScreeningProgressReceipt,
    ScreeningQueueReceipt,
    ScreeningQueueRecord,
)
from nas_core.retrieval.review import ScreeningReviewService
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "literature-deterministic-priority-1.0.0"


@dataclass(frozen=True)
class Signal:
    name: str
    pattern: re.Pattern[str]
    weight: int


POSITIVE_SIGNALS = (
    Signal(
        "pam50_or_intrinsic_subtype",
        re.compile(r"\b(pam[ -]?50|intrinsic subtype)\b", re.I),
        4,
    ),
    Signal(
        "stability_or_robustness",
        re.compile(r"\b(stabilit|reproducib|robust|perturb|sensitivity analysis)\w*", re.I),
        5,
    ),
    Signal(
        "classification_uncertainty",
        re.compile(
            r"\b(uncertain|confidence|margin|entropy|probabilit|second[- ]best|abstain)\w*",
            re.I,
        ),
        5,
    ),
    Signal("clinical_molecular_discordance", re.compile(r"\b(discordan|concordan)\w*", re.I), 4),
    Signal(
        "preprocessing_or_centering",
        re.compile(r"\b(preprocess|normaliz|centering|batch effect)\w*", re.I),
        3,
    ),
    Signal(
        "external_or_independent_validation",
        re.compile(r"\b(external|independent|validation|replication)\w*", re.I),
        3,
    ),
    Signal(
        "human_cohort",
        re.compile(r"\b(patient|human|tumou?r|cohort|clinical sample)\w*", re.I),
        2,
    ),
    Signal(
        "classifier_methods",
        re.compile(r"\b(classifier|algorithm|centroid|implementation)\w*", re.I),
        2,
    ),
    Signal("outcomes", re.compile(r"\b(survival|prognos|outcome|recurrence)\w*", re.I), 1),
)

CAUTION_SIGNALS = (
    Signal(
        "secondary_literature",
        re.compile(r"\b(review|meta-analysis|editorial|commentary)\b", re.I),
        -4,
    ),
    Signal(
        "nonhuman_or_cell_line_focus",
        re.compile(r"\b(xenograft|murine|mouse|mice|cell line)\w*", re.I),
        -3,
    ),
)


class DeterministicPrioritizationService:
    """Rank pending records for review without making eligibility or quality decisions."""

    def __init__(self, *, store: ObjectStore) -> None:
        self._review = ScreeningReviewService(store=store)

    def rank(
        self,
        queue_receipt: ScreeningQueueReceipt,
        *,
        progress_receipt: ScreeningProgressReceipt | None = None,
        limit: int = 30,
    ) -> ScreeningPriorityBatch:
        if not 1 <= limit <= 100:
            raise ValueError("priority display limit must be between 1 and 100")
        available = self._review.pending_records(
            queue_receipt,
            progress_receipt=progress_receipt,
        )
        scored = [self._score(record) for record in available]
        scored.sort(
            key=lambda item: (
                -item[0],
                -(item[3].publication_year or 0),
                item[3].screening_id,
            )
        )
        tiers = [self._tier(score) for score, _, _, _ in scored]
        records = [
            ScreeningPriorityRecord(
                rank=index,
                score=score,
                tier=self._tier(score),
                positive_signals=positive,
                caution_signals=cautions,
                record=record,
            )
            for index, (score, positive, cautions, record) in enumerate(scored[:limit], start=1)
        ]
        return ScreeningPriorityBatch(
            algorithm_version=ALGORITHM_VERSION,
            queue_id=queue_receipt.queue_id,
            based_on_progress_id=(progress_receipt.progress_id if progress_receipt else None),
            available_record_count=len(scored),
            core_record_count=tiers.count(ScreeningPriorityTier.CORE),
            supporting_record_count=tiers.count(ScreeningPriorityTier.SUPPORTING),
            context_record_count=tiers.count(ScreeningPriorityTier.CONTEXT),
            records=records,
            final_decisions_recorded=0,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _score(
        record: ScreeningQueueRecord,
    ) -> tuple[int, list[str], list[str], ScreeningQueueRecord]:
        text = f"{record.title}\n{record.abstract or ''}"
        positive = [signal.name for signal in POSITIVE_SIGNALS if signal.pattern.search(text)]
        cautions = [signal.name for signal in CAUTION_SIGNALS if signal.pattern.search(text)]
        score = sum(
            signal.weight
            for signal in (*POSITIVE_SIGNALS, *CAUTION_SIGNALS)
            if signal.pattern.search(text)
        )
        return score, positive, cautions, record

    @staticmethod
    def _tier(score: int) -> ScreeningPriorityTier:
        if score >= 17:
            return ScreeningPriorityTier.CORE
        if score >= 12:
            return ScreeningPriorityTier.SUPPORTING
        return ScreeningPriorityTier.CONTEXT
