import json
from datetime import UTC, datetime

import pytest

from nas_core.domain.advisory import AdvisoryConfidence
from nas_core.domain.citation_chain import (
    CitationDirection,
    CitationEnrichmentReceipt,
    CitationEnrichmentScope,
    CitationPriorityTier,
    CitationRecommendationReceipt,
    CitationScreeningRecommendation,
    EnrichedCitationCandidate,
)
from nas_core.domain.literature import ScreeningDecision
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.citation_adjudication import (
    CitationAdjudicationPolicy,
    CitationUnclearAdjudicationService,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 23, 0, tzinfo=UTC)


def _stored(store: InMemoryObjectStore, key: str, payload: object) -> StoredObject:
    body = canonical_json(payload)
    store.put_bytes(key, body, content_type="application/json")
    return StoredObject(
        object_key=key,
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )


def _inputs(
    store: InMemoryObjectStore,
) -> tuple[CitationRecommendationReceipt, CitationEnrichmentReceipt]:
    enriched = [
        EnrichedCitationCandidate(
            record_key=f"MED:{index}",
            source="MED",
            external_id=str(index),
            title=title,
            abstract=abstract,
            rank=index,
            score=6,
            tier=CitationPriorityTier.SUPPORTING,
            positive_signals=[],
            caution_signals=[],
            metadata_match_found=True,
            directions=[CitationDirection.FORWARD],
            seed_evidence_ids=["PMID:9"],
        )
        for index, (title, abstract) in enumerate(
            (
                ("Cross-platform PAM50 comparison", "A human classifier method."),
                ("A treatment outcome study", "A patient survival association."),
            ),
            start=1,
        )
    ]
    prior = [
        CitationScreeningRecommendation(
            record_key=item.record_key,
            title=item.title,
            rank=item.rank,
            priority_tier=item.tier,
            recommendation=ScreeningDecision.UNCLEAR,
            confidence=AdvisoryConfidence.MODERATE,
            rationale="Requires second-stage review.",
            matched_signals=[],
            abstract_available=True,
        )
        for item in enriched
    ]
    enriched_object = _stored(
        store,
        "enriched.json",
        [item.model_dump(mode="json", exclude_none=True) for item in enriched],
    )
    prior_object = _stored(
        store,
        "prior.json",
        [item.model_dump(mode="json", exclude_none=True) for item in prior],
    )
    enrichment = CitationEnrichmentReceipt(
        enrichment_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=1,
        prioritization_id="b" * 64,
        selection_scope=CitationEnrichmentScope.ALL_CANDIDATES,
        code_revision="a86b9ba",
        created_at=NOW,
        verified_at=NOW,
        requested_candidate_count=2,
        metadata_match_count=2,
        abstract_count=2,
        unresolved_metadata_count=0,
        request_count=1,
        raw_responses_object=enriched_object.model_copy(update={"object_key": "raw.json"}),
        enriched_candidates_object=enriched_object,
        input_checksum_verified=True,
        output_checksums_verified=True,
        record_coverage_verified=True,
    )
    recommendations = CitationRecommendationReceipt(
        recommendation_id="c" * 64,
        study_id="NAS-BRCA-002",
        pass_number=1,
        enrichment_id=enrichment.enrichment_id,
        algorithm_version="citation-abstract-advisory-1.0.2",
        code_revision="a86b9ba",
        created_at=NOW,
        verified_at=NOW,
        candidate_count=2,
        include_recommendation_count=0,
        exclude_recommendation_count=0,
        unclear_recommendation_count=2,
        high_confidence_count=0,
        abstract_unavailable_count=0,
        recommendations_object=prior_object,
        input_checksum_verified=True,
        output_checksum_verified=True,
        record_coverage_verified=True,
    )
    return recommendations, enrichment


def test_adjudication_covers_every_unclear_record_without_founder_decisions() -> None:
    store = InMemoryObjectStore()
    prior, enrichment = _inputs(store)
    policy = CitationAdjudicationPolicy(
        policy_version="1.0.0",
        study_id="NAS-BRCA-002",
        pass_number=1,
        based_on_recommendation_id=prior.recommendation_id,
        include_record_keys=["MED:1"],
        rationale="Synthetic policy for test coverage.",
    )
    service = CitationUnclearAdjudicationService(store=store, clock=lambda: NOW)

    receipt = service.adjudicate(
        prior, enrichment, policy, code_revision="a86b9ba"
    )

    assert receipt.candidate_count == 2
    assert receipt.include_recommendation_count == 1
    assert receipt.exclude_recommendation_count == 1
    assert receipt.unclear_recommendation_count == 0
    assert receipt.final_screening_decisions_recorded == 0
    rows = json.loads(store.get_bytes(receipt.recommendations_object.object_key))
    assert {row["recommendation"] for row in rows} == {"include", "exclude"}


def test_adjudication_rejects_policy_keys_outside_unresolved_set() -> None:
    store = InMemoryObjectStore()
    prior, enrichment = _inputs(store)
    policy = CitationAdjudicationPolicy(
        policy_version="1.0.0",
        study_id="NAS-BRCA-002",
        pass_number=1,
        based_on_recommendation_id=prior.recommendation_id,
        include_record_keys=["MED:999"],
        rationale="Synthetic invalid policy.",
    )
    service = CitationUnclearAdjudicationService(store=store, clock=lambda: NOW)

    with pytest.raises(ValueError, match="outside unresolved"):
        service.adjudicate(prior, enrichment, policy, code_revision="a86b9ba")
