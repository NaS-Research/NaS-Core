from datetime import UTC, datetime

from nas_core.domain.citation_chain import (
    CitationDirection,
    CitationEnrichmentReceipt,
    CitationEnrichmentScope,
    CitationPriorityTier,
    EnrichedCitationCandidate,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.citation_recommendation import CitationRecommendationService
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 21, 0, tzinfo=UTC)


def _candidate(
    key: str,
    title: str,
    abstract: str | None,
    rank: int,
) -> EnrichedCitationCandidate:
    source, external_id = key.split(":", maxsplit=1)
    return EnrichedCitationCandidate(
        record_key=key,
        source=source,
        external_id=external_id,
        title=title,
        abstract=abstract,
        rank=rank,
        score=12,
        tier=CitationPriorityTier.DIRECT,
        positive_signals=[],
        caution_signals=[],
        metadata_match_found=True,
        directions=[CitationDirection.FORWARD],
        seed_evidence_ids=["PMID:9"],
    )


def _receipt(
    store: InMemoryObjectStore,
    candidates: list[EnrichedCitationCandidate],
) -> CitationEnrichmentReceipt:
    body = canonical_json(
        [item.model_dump(mode="json", exclude_none=True) for item in candidates]
    )
    store.put_bytes("enriched.json", body, content_type="application/json")
    stored = StoredObject(
        object_key="enriched.json",
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )
    return CitationEnrichmentReceipt(
        enrichment_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=1,
        prioritization_id="b" * 64,
        selection_scope=CitationEnrichmentScope.ALL_CANDIDATES,
        code_revision="9ffd151",
        created_at=NOW,
        verified_at=NOW,
        requested_candidate_count=len(candidates),
        metadata_match_count=len(candidates),
        abstract_count=sum(item.abstract is not None for item in candidates),
        unresolved_metadata_count=0,
        request_count=1,
        raw_responses_object=stored.model_copy(update={"object_key": "raw.json"}),
        enriched_candidates_object=stored,
        input_checksum_verified=True,
        output_checksums_verified=True,
        record_coverage_verified=True,
    )


def test_recommendations_cover_include_exclude_and_unclear_without_decisions() -> None:
    store = InMemoryObjectStore()
    candidates = [
        _candidate(
            "MED:1",
            "PAM50 cross-platform classifier concordance in breast cancer",
            "We evaluated gene expression classifier agreement in a human cohort.",
            1,
        ),
        _candidate(
            "MED:2",
            "PAM50 survival after chemotherapy",
            "A prognostic outcome association in patients.",
            2,
        ),
        _candidate("MED:3", "Potential single-sample method", None, 3),
        _candidate(
            "MED:4",
            "Sample Preparation Approach Influences PAM50 Risk of Recurrence Score",
            "We tested gene expression assay reproducibility in patient tumors.",
            4,
        ),
        _candidate(
            "MED:5",
            "A single-sample serum classifier for pan-cancer detection",
            "A diagnostic miRNA screening classifier.",
            5,
        ),
        _candidate(
            "MED:6",
            "A single-sample microarray normalization method",
            "The method normalizes one microarray for personalized workflows.",
            6,
        ),
    ]
    service = CitationRecommendationService(store=store, clock=lambda: NOW)

    receipt = service.recommend(
        _receipt(store, candidates), code_revision="9ffd151"
    )

    assert receipt.candidate_count == 6
    assert receipt.include_recommendation_count == 3
    assert receipt.exclude_recommendation_count == 2
    assert receipt.unclear_recommendation_count == 1
    assert receipt.final_screening_decisions_recorded == 0
