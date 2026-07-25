"""Typed provenance contracts for citation-chain retrieval passes."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.advisory import AdvisoryConfidence
from nas_core.domain.literature import ScreeningDecision, ScreeningExclusionReason
from nas_core.domain.snapshots import StoredObject


class CitationChainModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CitationDirection(StrEnum):
    BACKWARD = "backward"
    FORWARD = "forward"


class CitationSeed(CitationChainModel):
    evidence_id: str = Field(pattern=r"^PMID:[0-9]+$")
    pmid: str = Field(pattern=r"^[0-9]+$")
    title: str = Field(min_length=1)


class CitationEndpointResult(CitationChainModel):
    seed_evidence_id: str = Field(pattern=r"^PMID:[0-9]+$")
    direction: CitationDirection
    endpoint_url: str = Field(min_length=1)
    reported_result_count: int = Field(ge=0)
    retrieved_result_count: int = Field(ge=0)
    request_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_counts(self) -> CitationEndpointResult:
        if self.reported_result_count != self.retrieved_result_count:
            raise ValueError("citation endpoint result count does not reconcile")
        return self


class CitationCandidate(CitationChainModel):
    record_key: str = Field(pattern=r"^[A-Z]+:.+$")
    source: str = Field(pattern=r"^[A-Z]+$")
    external_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    author_string: str | None = None
    journal: str | None = None
    publication_year: int | None = Field(default=None, ge=1800, le=2100)
    directions: list[CitationDirection] = Field(min_length=1, max_length=2)
    seed_evidence_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_candidate(self) -> CitationCandidate:
        if len(self.directions) != len(set(self.directions)):
            raise ValueError("citation candidate directions must be unique")
        if len(self.seed_evidence_ids) != len(set(self.seed_evidence_ids)):
            raise ValueError("citation candidate seeds must be unique")
        return self


class CitationScreeningDisposition(StrEnum):
    ALREADY_SCREENED = "already_screened"
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    REQUIRES_SCREENING = "requires_screening"


class CitationScreeningInventoryRecord(CitationChainModel):
    record_key: str = Field(pattern=r"^[A-Z]+:.+$")
    canonical_record_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    normalized_title: str = Field(min_length=1)
    disposition: CitationScreeningDisposition
    matched_prior_record_key: str | None = Field(default=None, min_length=1)
    duplicate_of_record_key: str | None = Field(default=None, min_length=1)
    directions: list[CitationDirection] = Field(min_length=1, max_length=2)
    seed_evidence_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_disposition(self) -> CitationScreeningInventoryRecord:
        if self.disposition is CitationScreeningDisposition.ALREADY_SCREENED:
            if self.matched_prior_record_key is None or self.duplicate_of_record_key is not None:
                raise ValueError("already-screened records require one prior-record match")
        elif self.disposition is CitationScreeningDisposition.DUPLICATE_CANDIDATE:
            if self.duplicate_of_record_key is None or self.matched_prior_record_key is not None:
                raise ValueError("duplicate candidates require one canonical candidate")
        elif self.matched_prior_record_key is not None or self.duplicate_of_record_key is not None:
            raise ValueError("screening candidates cannot contain a duplicate match")
        return self


class CitationScreeningPreparationReceipt(CitationChainModel):
    schema_version: str = "1.0.0"
    preparation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    citation_execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    prior_search_execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    verified_at: datetime
    input_candidate_count: int = Field(ge=0)
    already_screened_count: int = Field(ge=0)
    duplicate_candidate_count: int = Field(ge=0)
    requires_screening_count: int = Field(ge=0)
    inventory_object: StoredObject
    screening_candidates_object: StoredObject
    input_checksums_verified: bool
    output_checksums_verified: bool
    count_invariants_verified: bool
    final_screening_decisions_recorded: int = Field(default=0, ge=0)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_preparation(self) -> CitationScreeningPreparationReceipt:
        total = (
            self.already_screened_count
            + self.duplicate_candidate_count
            + self.requires_screening_count
        )
        if total != self.input_candidate_count:
            raise ValueError("citation-screening dispositions must cover every candidate")
        if not all(
            (
                self.input_checksums_verified,
                self.output_checksums_verified,
                self.count_invariants_verified,
            )
        ):
            raise ValueError("citation-screening preparation requires verified invariants")
        if self.final_screening_decisions_recorded or self.scientific_conclusions_drawn:
            raise ValueError("citation-screening preparation cannot make final decisions")
        return self


class CitationPriorityTier(StrEnum):
    DIRECT = "direct"
    SUPPORTING = "supporting"
    CONTEXT = "context"


class CitationPriorityRecord(CitationChainModel):
    rank: int = Field(ge=1)
    score: int
    tier: CitationPriorityTier
    positive_signals: list[str]
    caution_signals: list[str]
    candidate: CitationCandidate


class CitationPrioritizationReceipt(CitationChainModel):
    schema_version: str = "1.0.0"
    prioritization_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    preparation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    verified_at: datetime
    candidate_count: int = Field(ge=0)
    direct_priority_count: int = Field(ge=0)
    supporting_priority_count: int = Field(ge=0)
    context_priority_count: int = Field(ge=0)
    ranking_object: StoredObject
    input_checksum_verified: bool
    output_checksum_verified: bool
    rank_invariants_verified: bool
    final_screening_decisions_recorded: int = Field(default=0, ge=0)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_prioritization(self) -> CitationPrioritizationReceipt:
        if (
            self.direct_priority_count
            + self.supporting_priority_count
            + self.context_priority_count
            != self.candidate_count
        ):
            raise ValueError("citation priority tiers must cover every candidate")
        if not all(
            (
                self.input_checksum_verified,
                self.output_checksum_verified,
                self.rank_invariants_verified,
            )
        ):
            raise ValueError("citation prioritization requires verified invariants")
        if self.final_screening_decisions_recorded or self.scientific_conclusions_drawn:
            raise ValueError("citation prioritization cannot make final decisions")
        return self


class EnrichedCitationCandidate(CitationChainModel):
    record_key: str = Field(pattern=r"^[A-Z]+:.+$")
    source: str = Field(pattern=r"^[A-Z]+$")
    external_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    author_string: str | None = None
    journal: str | None = None
    publication_year: int | None = Field(default=None, ge=1800, le=2100)
    pmid: str | None = None
    pmcid: str | None = None
    doi: str | None = None
    abstract: str | None = None
    is_open_access: bool | None = None
    rank: int = Field(ge=1)
    score: int
    tier: CitationPriorityTier
    positive_signals: list[str]
    caution_signals: list[str]
    metadata_match_found: bool
    directions: list[CitationDirection] = Field(min_length=1, max_length=2)
    seed_evidence_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_enrichment(self) -> EnrichedCitationCandidate:
        if not self.metadata_match_found and any(
            (self.pmid, self.pmcid, self.doi, self.abstract, self.is_open_access)
        ):
            raise ValueError("unmatched citation candidates cannot claim enriched metadata")
        return self


class CitationEnrichmentScope(StrEnum):
    DIRECT_AND_SUPPORTING = "direct_and_supporting"
    ALL_CANDIDATES = "all_candidates"


class CitationEnrichmentReceipt(CitationChainModel):
    schema_version: str = "1.0.0"
    enrichment_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    prioritization_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    selection_scope: CitationEnrichmentScope
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    verified_at: datetime
    requested_candidate_count: int = Field(ge=0)
    metadata_match_count: int = Field(ge=0)
    abstract_count: int = Field(ge=0)
    unresolved_metadata_count: int = Field(ge=0)
    request_count: int = Field(ge=0)
    raw_responses_object: StoredObject
    enriched_candidates_object: StoredObject
    input_checksum_verified: bool
    output_checksums_verified: bool
    record_coverage_verified: bool
    final_screening_decisions_recorded: int = Field(default=0, ge=0)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_enrichment(self) -> CitationEnrichmentReceipt:
        if (
            self.metadata_match_count + self.unresolved_metadata_count
            != self.requested_candidate_count
        ):
            raise ValueError("citation enrichment must account for every requested record")
        if self.abstract_count > self.metadata_match_count:
            raise ValueError("citation abstracts cannot exceed metadata matches")
        if not all(
            (
                self.input_checksum_verified,
                self.output_checksums_verified,
                self.record_coverage_verified,
            )
        ):
            raise ValueError("citation enrichment requires verified invariants")
        if self.final_screening_decisions_recorded or self.scientific_conclusions_drawn:
            raise ValueError("citation enrichment cannot make final decisions")
        return self


class CitationScreeningRecommendation(CitationChainModel):
    record_key: str = Field(pattern=r"^[A-Z]+:.+$")
    title: str = Field(min_length=1)
    pmid: str | None = None
    pmcid: str | None = None
    doi: str | None = None
    rank: int = Field(ge=1)
    priority_tier: CitationPriorityTier
    recommendation: ScreeningDecision
    confidence: AdvisoryConfidence
    exclusion_reason: ScreeningExclusionReason | None = None
    rationale: str = Field(min_length=1)
    matched_signals: list[str]
    abstract_available: bool
    founder_decision_recorded: bool = False

    @model_validator(mode="after")
    def validate_recommendation(self) -> CitationScreeningRecommendation:
        if self.recommendation is ScreeningDecision.PENDING:
            raise ValueError("citation advisory recommendations cannot be pending")
        if (
            self.recommendation is ScreeningDecision.EXCLUDE
        ) != (self.exclusion_reason is not None):
            raise ValueError("only exclusion recommendations require an exclusion reason")
        if self.founder_decision_recorded:
            raise ValueError("advisory recommendation cannot claim a founder decision")
        return self


class CitationRecommendationReceipt(CitationChainModel):
    schema_version: str = "1.0.0"
    recommendation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    enrichment_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    verified_at: datetime
    candidate_count: int = Field(ge=0)
    include_recommendation_count: int = Field(ge=0)
    exclude_recommendation_count: int = Field(ge=0)
    unclear_recommendation_count: int = Field(ge=0)
    high_confidence_count: int = Field(ge=0)
    abstract_unavailable_count: int = Field(ge=0)
    recommendations_object: StoredObject
    input_checksum_verified: bool
    output_checksum_verified: bool
    record_coverage_verified: bool
    final_screening_decisions_recorded: int = Field(default=0, ge=0)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_recommendations(self) -> CitationRecommendationReceipt:
        if (
            self.include_recommendation_count
            + self.exclude_recommendation_count
            + self.unclear_recommendation_count
            != self.candidate_count
        ):
            raise ValueError("citation recommendations must cover every candidate")
        if not all(
            (
                self.input_checksum_verified,
                self.output_checksum_verified,
                self.record_coverage_verified,
            )
        ):
            raise ValueError("citation recommendations require verified invariants")
        if self.final_screening_decisions_recorded or self.scientific_conclusions_drawn:
            raise ValueError("citation recommendations cannot make final decisions")
        return self


class CitationFounderPacketReceipt(CitationChainModel):
    schema_version: str = "1.0.0"
    packet_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    recommendation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    created_at: datetime
    candidate_count: int = Field(ge=0)
    proposed_decision_count: int = Field(ge=0)
    pending_adjudication_count: int = Field(ge=0)
    include_recommendation_count: int = Field(ge=0)
    exclude_recommendation_count: int = Field(ge=0)
    packet_path: str = Field(min_length=1)
    packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    appendix_path: str = Field(min_length=1)
    appendix_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    recommendation_checksum_verified: bool
    packet_coverage_verified: bool
    founder_confirmation_required: bool = True
    final_screening_decisions_recorded: int = Field(default=0, ge=0)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_packet(self) -> CitationFounderPacketReceipt:
        if (
            self.proposed_decision_count + self.pending_adjudication_count
            != self.candidate_count
        ):
            raise ValueError("citation packet must account for every candidate")
        if (
            self.include_recommendation_count + self.exclude_recommendation_count
            != self.proposed_decision_count
        ):
            raise ValueError("citation packet proposed decisions do not reconcile")
        if not (
            self.recommendation_checksum_verified
            and self.packet_coverage_verified
            and self.founder_confirmation_required
        ):
            raise ValueError("citation packet requires verified advisory boundaries")
        if self.final_screening_decisions_recorded or self.scientific_conclusions_drawn:
            raise ValueError("citation packet cannot make final decisions")
        return self


class CitationChainSnapshot(CitationChainModel):
    schema_version: str = "1.0.0"
    execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    retrieved_at: datetime
    seeds: list[CitationSeed] = Field(min_length=1)
    endpoint_results: list[CitationEndpointResult] = Field(min_length=2)
    backward_candidate_count: int = Field(ge=0)
    forward_candidate_count: int = Field(ge=0)
    unique_candidate_count: int = Field(ge=0)
    raw_responses_object: StoredObject
    candidates_object: StoredObject
    scientific_conclusions_drawn: bool = False
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_snapshot(self) -> CitationChainSnapshot:
        if len({item.evidence_id for item in self.seeds}) != len(self.seeds):
            raise ValueError("citation-chain seeds must be unique")
        expected_endpoints = len(self.seeds) * 2
        if len(self.endpoint_results) != expected_endpoints:
            raise ValueError("every citation seed requires both directional endpoint results")
        pairs = {(item.seed_evidence_id, item.direction) for item in self.endpoint_results}
        if len(pairs) != expected_endpoints:
            raise ValueError("citation endpoint seed-direction pairs must be unique")
        seed_ids = {item.evidence_id for item in self.seeds}
        if any(item.seed_evidence_id not in seed_ids for item in self.endpoint_results):
            raise ValueError("citation endpoint result references an unknown seed")
        backward = sum(
            item.retrieved_result_count
            for item in self.endpoint_results
            if item.direction is CitationDirection.BACKWARD
        )
        forward = sum(
            item.retrieved_result_count
            for item in self.endpoint_results
            if item.direction is CitationDirection.FORWARD
        )
        if (
            backward != self.backward_candidate_count
            or forward != self.forward_candidate_count
        ):
            raise ValueError("citation directional counts do not reconcile")
        if self.unique_candidate_count > backward + forward:
            raise ValueError("unique citation candidates exceed directional retrievals")
        if self.scientific_conclusions_drawn:
            raise ValueError("citation retrieval cannot draw scientific conclusions")
        return self


class CitationChainReceipt(CitationChainModel):
    schema_version: str = "1.0.0"
    execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    retrieved_at: datetime
    verified_at: datetime
    seed_evidence_ids: list[str] = Field(min_length=1)
    backward_candidate_count: int = Field(ge=0)
    forward_candidate_count: int = Field(ge=0)
    unique_candidate_count: int = Field(ge=0)
    endpoint_request_count: int = Field(ge=2)
    manifest_object_key: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    raw_responses_object: StoredObject
    candidates_object: StoredObject
    manifest_checksum_verified: bool
    object_checksums_verified: bool
    endpoint_counts_verified: bool
    candidate_count_verified: bool
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_receipt(self) -> CitationChainReceipt:
        if len(self.seed_evidence_ids) != len(set(self.seed_evidence_ids)):
            raise ValueError("citation receipt seeds must be unique")
        if not all(
            (
                self.manifest_checksum_verified,
                self.object_checksums_verified,
                self.endpoint_counts_verified,
                self.candidate_count_verified,
            )
        ):
            raise ValueError("citation receipt requires all verification flags")
        if self.scientific_conclusions_drawn:
            raise ValueError("citation receipt cannot draw scientific conclusions")
        return self


def write_citation_chain_receipt(path: Path, receipt: CitationChainReceipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_chain_receipt(path: Path) -> CitationChainReceipt:
    return CitationChainReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_citation_screening_preparation_receipt(
    path: Path,
    receipt: CitationScreeningPreparationReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_screening_preparation_receipt(
    path: Path,
) -> CitationScreeningPreparationReceipt:
    return CitationScreeningPreparationReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_citation_prioritization_receipt(
    path: Path,
    receipt: CitationPrioritizationReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_prioritization_receipt(path: Path) -> CitationPrioritizationReceipt:
    return CitationPrioritizationReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_citation_enrichment_receipt(
    path: Path,
    receipt: CitationEnrichmentReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_enrichment_receipt(path: Path) -> CitationEnrichmentReceipt:
    return CitationEnrichmentReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_citation_recommendation_receipt(
    path: Path,
    receipt: CitationRecommendationReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_recommendation_receipt(path: Path) -> CitationRecommendationReceipt:
    return CitationRecommendationReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_citation_founder_packet_receipt(
    path: Path,
    receipt: CitationFounderPacketReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_founder_packet_receipt(path: Path) -> CitationFounderPacketReceipt:
    return CitationFounderPacketReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
