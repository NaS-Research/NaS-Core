"""Checksum-bound founder packet generation for citation-chain screening."""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from nas_core.domain.citation_chain import (
    CitationFounderPacketReceipt,
    CitationRecommendationReceipt,
    CitationScreeningRecommendation,
)
from nas_core.domain.literature import ScreeningDecision
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore

_RECOMMENDATIONS = TypeAdapter(list[CitationScreeningRecommendation])


class CitationPacketError(RuntimeError):
    """Raised when a founder packet cannot reproduce its advisory ledger."""


class CitationFounderPacketService:
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
        receipt: CitationRecommendationReceipt,
        *,
        packet_path: Path,
        appendix_path: Path,
    ) -> CitationFounderPacketReceipt:
        body = self._store.get_bytes(receipt.recommendations_object.object_key)
        if (
            len(body) != receipt.recommendations_object.size_bytes
            or sha256(body) != receipt.recommendations_object.sha256
        ):
            raise CitationPacketError("recommendation ledger does not match its receipt")
        try:
            recommendations = _RECOMMENDATIONS.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationPacketError("recommendation ledger is invalid") from error
        if (
            len(recommendations) != receipt.candidate_count
            or len({item.record_key for item in recommendations})
            != len(recommendations)
        ):
            raise CitationPacketError("recommendation ledger coverage is invalid")

        appendix_body = self._appendix(recommendations)
        appendix_hash = sha256(appendix_body)
        packet_body = self._packet(
            receipt,
            recommendations,
            appendix_path=appendix_path,
            appendix_sha256=appendix_hash,
        )
        self._write_exclusive(appendix_path, appendix_body)
        self._write_exclusive(packet_path, packet_body)
        proposed = [
            item
            for item in recommendations
            if item.recommendation is not ScreeningDecision.UNCLEAR
        ]
        pending = len(recommendations) - len(proposed)
        packet_hash = sha256(packet_body)
        created_at = self._clock()
        packet_id = sha256(
            (
                f"{receipt.recommendation_id}|{packet_hash}|{appendix_hash}|"
                f"{created_at.isoformat()}"
            ).encode()
        )
        return CitationFounderPacketReceipt(
            packet_id=packet_id,
            study_id=receipt.study_id,
            pass_number=receipt.pass_number,
            recommendation_id=receipt.recommendation_id,
            created_at=created_at,
            candidate_count=len(recommendations),
            proposed_decision_count=len(proposed),
            pending_adjudication_count=pending,
            include_recommendation_count=receipt.include_recommendation_count,
            exclude_recommendation_count=receipt.exclude_recommendation_count,
            packet_path=str(packet_path),
            packet_sha256=packet_hash,
            appendix_path=str(appendix_path),
            appendix_sha256=appendix_hash,
            recommendation_checksum_verified=True,
            packet_coverage_verified=True,
            founder_confirmation_required=True,
        )

    @staticmethod
    def _appendix(recommendations: list[CitationScreeningRecommendation]) -> bytes:
        destination = io.StringIO(newline="")
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(
            (
                "rank",
                "record_key",
                "pmid",
                "pmcid",
                "doi",
                "priority_tier",
                "recommendation",
                "confidence",
                "exclusion_reason",
                "abstract_available",
                "title",
                "rationale",
                "matched_signals",
                "founder_decision_recorded",
            )
        )
        for item in sorted(recommendations, key=lambda value: value.rank):
            writer.writerow(
                (
                    item.rank,
                    item.record_key,
                    item.pmid or "",
                    item.pmcid or "",
                    item.doi or "",
                    item.priority_tier.value,
                    item.recommendation.value,
                    item.confidence.value,
                    item.exclusion_reason.value if item.exclusion_reason else "",
                    str(item.abstract_available).lower(),
                    item.title,
                    item.rationale,
                    "|".join(item.matched_signals),
                    "false",
                )
            )
        return destination.getvalue().encode("utf-8")

    @staticmethod
    def _packet(
        receipt: CitationRecommendationReceipt,
        recommendations: list[CitationScreeningRecommendation],
        *,
        appendix_path: Path,
        appendix_sha256: str,
    ) -> bytes:
        included = [
            item
            for item in recommendations
            if item.recommendation is ScreeningDecision.INCLUDE
        ]
        unclear = [
            item
            for item in recommendations
            if item.recommendation is ScreeningDecision.UNCLEAR
        ]
        reason_counts = Counter(
            item.exclusion_reason.value
            for item in recommendations
            if item.exclusion_reason is not None
        )
        lines = [
            "# Founder Citation Screening Packet — Pass 1",
            "",
            "**Advisory only—founder confirmation required.**",
            "",
            "No recommendation in this packet is a final screening decision. "
            "The complete row-level appendix is checksum-bound and records "
            "`founder_decision_recorded=false` for every candidate.",
            "",
            "## Provenance",
            "",
            f"- Recommendation ID: `{receipt.recommendation_id}`",
            f"- Candidate count: {receipt.candidate_count}",
            f"- Proposed decisions: {len(included) + receipt.exclude_recommendation_count}",
            f"- Pending individual adjudication: {len(unclear)}",
            f"- Appendix: `{appendix_path.name}`",
            f"- Appendix SHA-256: `{appendix_sha256}`",
            "",
            "## High-confidence inclusion recommendations",
            "",
            "| Rank | Record | Title |",
            "|---:|---|---|",
        ]
        lines.extend(
            f"| {item.rank} | `{item.record_key}` | {item.title.replace('|', '&#124;')} |"
            for item in included
        )
        lines.extend(
            [
                "",
                "## Exclusion recommendation summary",
                "",
                f"- Total: {receipt.exclude_recommendation_count}",
            ]
        )
        lines.extend(
            f"- `{reason}`: {count}" for reason, count in sorted(reason_counts.items())
        )
        lines.extend(
            [
                "",
                "Every exclusion title, rationale, confidence, protocol reason, and "
                "signal is present in the checksum-bound CSV appendix.",
                "",
                "## Records requiring individual adjudication",
                "",
                "| Rank | Record | Abstract | Title |",
                "|---:|---|:---:|---|",
            ]
        )
        lines.extend(
            f"| {item.rank} | `{item.record_key}` | "
            f"{'yes' if item.abstract_available else 'no'} | "
            f"{item.title.replace('|', '&#124;')} |"
            for item in unclear
        )
        lines.extend(
            [
                "",
                "## Confirmation boundary",
                "",
                "A founder confirmation may authorize the proposed include/exclude "
                "recommendations, but it cannot convert the unclear records into final "
                "decisions. Those records require a separate adjudication packet.",
                "",
                "Exact confirmation statement:",
                "",
                "`I confirm the proposed citation pass 1 decisions in the checksum-bound packet.`",
                "",
            ]
        )
        return "\n".join(lines).encode("utf-8")

    @staticmethod
    def _write_exclusive(path: Path, body: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as destination:
            destination.write(body)
