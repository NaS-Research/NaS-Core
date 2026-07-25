"""Build a typed founder decision batch from a checksum-bound review packet."""

from __future__ import annotations

import re
from pathlib import Path

from nas_core.domain.literature import (
    ScreeningDecision,
    ScreeningDecisionBatch,
    ScreeningDecisionInput,
    ScreeningExclusionReason,
    ScreeningProgressReceipt,
    ScreeningQueueReceipt,
    ScreeningQueueRecord,
    ScreeningReviewerRole,
)
from nas_core.domain.screening_confirmation import (
    ScreeningConfirmation,
    ScreeningPacketPreview,
)
from nas_core.ingestion.gdc import sha256
from nas_core.retrieval.review import ScreeningReviewService

_ROW = re.compile(r"^\| (\d+) \| ([^|]+?) \|", flags=re.MULTILINE)
_EXCLUSION_ROW = re.compile(
    r"^\| (\d+) \| ([^|]+?) \| [^|]+? \| ([1-6]) \|",
    flags=re.MULTILINE,
)
_REASON_BY_NUMBER = {
    1: ScreeningExclusionReason.NONHUMAN_OR_NO_PRIMARY_HUMAN_TUMOR_COHORT,
    2: ScreeningExclusionReason.NO_MOLECULAR_INTRINSIC_SUBTYPE_MEASURE,
    3: ScreeningExclusionReason.NO_RELEVANT_DISCORDANCE_STABILITY_OR_CLASSIFIER_METHOD,
    4: ScreeningExclusionReason.REVIEW_EDITORIAL_OR_COMMENTARY_FOR_CITATION_CHAINING_ONLY,
    5: ScreeningExclusionReason.DUPLICATE_OR_SUPERSEDED_REPORT_WITHOUT_DISTINCT_CONTRIBUTION,
    6: ScreeningExclusionReason.OUTSIDE_BREAST_CANCER_SCOPE,
}


class ScreeningConfirmationError(RuntimeError):
    """Raised when a founder confirmation cannot reproduce the reviewed packet."""


class ScreeningConfirmationService:
    def __init__(self, *, review_service: ScreeningReviewService) -> None:
        self._review_service = review_service

    def build_decision_batch(
        self,
        *,
        queue_receipt: ScreeningQueueReceipt,
        progress_receipt: ScreeningProgressReceipt,
        packet_path: Path,
        confirmation: ScreeningConfirmation,
    ) -> ScreeningDecisionBatch:
        packet = packet_path.read_bytes()
        if sha256(packet) != confirmation.packet_sha256:
            raise ScreeningConfirmationError(
                "founder confirmation does not match the current packet checksum"
            )
        if (
            confirmation.queue_id != queue_receipt.queue_id
            or confirmation.expected_previous_progress_id
            != progress_receipt.progress_id
        ):
            raise ScreeningConfirmationError(
                "founder confirmation is bound to a different queue or progress state"
            )

        pending = self._review_service.pending_records(
            queue_receipt,
            progress_receipt=progress_receipt,
        )
        decisions = self._parse_packet(packet, pending)

        return ScreeningDecisionBatch(
            queue_id=queue_receipt.queue_id,
            expected_previous_progress_id=progress_receipt.progress_id,
            reviewer_id=confirmation.reviewer_id,
            reviewer_name=confirmation.reviewer_name,
            reviewer_role=ScreeningReviewerRole.FOUNDER_INTERNAL_REVIEWER,
            decisions=decisions,
        )

    def preview_packet(
        self,
        *,
        queue_receipt: ScreeningQueueReceipt,
        progress_receipt: ScreeningProgressReceipt,
        packet_path: Path,
    ) -> ScreeningPacketPreview:
        packet = packet_path.read_bytes()
        pending = self._review_service.pending_records(
            queue_receipt,
            progress_receipt=progress_receipt,
        )
        decisions = self._parse_packet(packet, pending)
        return ScreeningPacketPreview(
            queue_id=queue_receipt.queue_id,
            based_on_progress_id=progress_receipt.progress_id,
            packet_sha256=sha256(packet),
            pending_record_count=len(pending),
            proposed_include_count=sum(
                item.decision is ScreeningDecision.INCLUDE for item in decisions
            ),
            proposed_exclude_count=sum(
                item.decision is ScreeningDecision.EXCLUDE for item in decisions
            ),
            complete_coverage_verified=True,
            immutable_identity_verified=True,
        )

    def _parse_packet(
        self,
        packet: bytes,
        pending: list[ScreeningQueueRecord],
    ) -> list[ScreeningDecisionInput]:
        text = packet.decode("utf-8")
        try:
            inclusion_text, tail = text.split("## Recommended exclusions", maxsplit=1)
            exclusion_text, _ = tail.split("## Founder confirmation", maxsplit=1)
        except ValueError as error:
            raise ScreeningConfirmationError(
                "screening packet is missing required decision sections"
            ) from error

        included = self._parse_inclusions(inclusion_text)
        excluded = self._parse_exclusions(exclusion_text)
        numbered = [*included, *excluded]
        expected_numbers = list(range(1, len(pending) + 1))
        if sorted(number for number, _, _ in numbered) != expected_numbers:
            raise ScreeningConfirmationError(
                "screening packet must decide every pending record exactly once"
            )

        decisions: list[ScreeningDecisionInput] = []
        for number, displayed_record, reason in sorted(numbered):
            record = pending[number - 1]
            if displayed_record != self._display_identifier(record):
                raise ScreeningConfirmationError(
                    f"packet record {number} does not match immutable queue identity"
                )
            decisions.append(
                ScreeningDecisionInput(
                    screening_id=record.screening_id,
                    decision=(
                        ScreeningDecision.INCLUDE
                        if reason is None
                        else ScreeningDecision.EXCLUDE
                    ),
                    exclusion_reason=reason,
                )
            )

        return decisions

    @staticmethod
    def _parse_inclusions(
        section: str,
    ) -> list[tuple[int, str, ScreeningExclusionReason | None]]:
        return [
            (int(number), record.strip(), None)
            for number, record in _ROW.findall(section)
            if record.strip() not in {"Current record", "#"}
        ]

    @staticmethod
    def _parse_exclusions(
        section: str,
    ) -> list[tuple[int, str, ScreeningExclusionReason | None]]:
        return [
            (int(number), record.strip(), _REASON_BY_NUMBER[int(reason)])
            for number, record, reason in _EXCLUSION_ROW.findall(section)
        ]

    @staticmethod
    def _display_identifier(record: ScreeningQueueRecord) -> str:
        if record.pmid is not None:
            return f"PMID {record.pmid}"
        return record.record_key.rsplit(":", maxsplit=1)[-1]
