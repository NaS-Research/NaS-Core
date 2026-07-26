import csv
import io
from datetime import UTC, datetime
from pathlib import Path

from nas_core.domain.advisory import AdvisoryConfidence
from nas_core.domain.citation_chain import (
    CitationPriorityTier,
    CitationRecommendationReceipt,
    CitationScreeningRecommendation,
)
from nas_core.domain.literature import ScreeningDecision, ScreeningExclusionReason
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.citation_packet import CitationFounderPacketService
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 22, 0, tzinfo=UTC)


def _recommendation(
    rank: int,
    decision: ScreeningDecision,
) -> CitationScreeningRecommendation:
    return CitationScreeningRecommendation(
        record_key=f"MED:{rank}",
        title=f"Record {rank}",
        rank=rank,
        priority_tier=CitationPriorityTier.DIRECT,
        recommendation=decision,
        confidence=(
            AdvisoryConfidence.HIGH
            if decision is not ScreeningDecision.UNCLEAR
            else AdvisoryConfidence.LOW
        ),
        exclusion_reason=(
            ScreeningExclusionReason.NO_RELEVANT_DISCORDANCE_STABILITY_OR_CLASSIFIER_METHOD
            if decision is ScreeningDecision.EXCLUDE
            else None
        ),
        rationale="Synthetic advisory rationale.",
        matched_signals=[],
        abstract_available=decision is not ScreeningDecision.UNCLEAR,
    )


def test_packet_covers_all_records_and_preserves_advisory_boundary(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore()
    recommendations = [
        _recommendation(1, ScreeningDecision.INCLUDE),
        _recommendation(2, ScreeningDecision.EXCLUDE),
        _recommendation(3, ScreeningDecision.UNCLEAR),
    ]
    body = canonical_json(
        [item.model_dump(mode="json", exclude_none=True) for item in recommendations]
    )
    store.put_bytes("recommendations.json", body, content_type="application/json")
    stored = StoredObject(
        object_key="recommendations.json",
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )
    receipt = CitationRecommendationReceipt(
        recommendation_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=1,
        enrichment_id="b" * 64,
        algorithm_version="citation-abstract-advisory-1.0.2",
        code_revision="9ffd151",
        created_at=NOW,
        verified_at=NOW,
        candidate_count=3,
        include_recommendation_count=1,
        exclude_recommendation_count=1,
        unclear_recommendation_count=1,
        high_confidence_count=2,
        abstract_unavailable_count=1,
        recommendations_object=stored,
        input_checksum_verified=True,
        output_checksum_verified=True,
        record_coverage_verified=True,
    )
    packet_path = tmp_path / "packet.md"
    appendix_path = tmp_path / "appendix.csv"
    service = CitationFounderPacketService(store=store, clock=lambda: NOW)

    packet = service.build(
        receipt,
        packet_path=packet_path,
        appendix_path=appendix_path,
    )

    assert packet.candidate_count == 3
    assert packet.proposed_decision_count == 2
    assert packet.pending_adjudication_count == 1
    assert packet.final_screening_decisions_recorded == 0
    text = packet_path.read_text(encoding="utf-8")
    assert "# Founder Citation Screening Packet — Pass 1" in text
    assert "Advisory only—founder confirmation required" in text
    assert "cannot convert the unclear records into final decisions" in text
    rows = list(csv.DictReader(io.StringIO(appendix_path.read_text())))
    assert len(rows) == 3
    assert all(row["founder_decision_recorded"] == "false" for row in rows)


def test_packet_heading_uses_receipt_pass_number(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    recommendations = [_recommendation(1, ScreeningDecision.INCLUDE)]
    body = canonical_json(
        [item.model_dump(mode="json", exclude_none=True) for item in recommendations]
    )
    store.put_bytes("recommendations.json", body, content_type="application/json")
    stored = StoredObject(
        object_key="recommendations.json",
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )
    receipt = CitationRecommendationReceipt(
        recommendation_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=2,
        enrichment_id="b" * 64,
        algorithm_version="citation-abstract-advisory-1.0.2",
        code_revision="9ffd151",
        created_at=NOW,
        verified_at=NOW,
        candidate_count=1,
        include_recommendation_count=1,
        exclude_recommendation_count=0,
        unclear_recommendation_count=0,
        high_confidence_count=1,
        abstract_unavailable_count=0,
        recommendations_object=stored,
        input_checksum_verified=True,
        output_checksum_verified=True,
        record_coverage_verified=True,
    )
    packet_path = tmp_path / "packet.md"
    service = CitationFounderPacketService(store=store, clock=lambda: NOW)

    service.build(
        receipt,
        packet_path=packet_path,
        appendix_path=tmp_path / "appendix.csv",
    )

    text = packet_path.read_text(encoding="utf-8")
    assert "# Founder Citation Screening Packet — Pass 2" in text
    assert "citation pass 2 decisions" in text
