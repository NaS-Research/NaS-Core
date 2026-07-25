"""Policy-bound second-stage advisory adjudication of unclear citation records."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from nas_core.domain.advisory import AdvisoryConfidence
from nas_core.domain.citation_chain import (
    CitationEnrichmentReceipt,
    CitationRecommendationReceipt,
    CitationScreeningRecommendation,
    EnrichedCitationCandidate,
)
from nas_core.domain.literature import ScreeningDecision, ScreeningExclusionReason
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "citation-unclear-adjudication-1.0.0"
JSON_MEDIA_TYPE = "application/json"
_RECOMMENDATIONS = TypeAdapter(list[CitationScreeningRecommendation])
_ENRICHED = TypeAdapter(list[EnrichedCitationCandidate])
_SECONDARY = re.compile(
    r"\b(review|guideline|recommendation|editorial|comment|perspective|"
    r"consensus|ready to use|ready for clinical|introducing|clinical practice)\b",
    re.I,
)
_NONHUMAN = re.compile(r"\b(canine|mouse|mice|murine|xenograft)\b", re.I)


class CitationAdjudicationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    policy_version: str = Field(min_length=1)
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    based_on_recommendation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    include_record_keys: list[str]
    rationale: str = Field(min_length=1)
    founder_confirmation_required: bool = True
    autonomous_decisions_allowed: bool = False

    @model_validator(mode="after")
    def validate_policy(self) -> CitationAdjudicationPolicy:
        if len(self.include_record_keys) != len(set(self.include_record_keys)):
            raise ValueError("adjudication include keys must be unique")
        if not self.founder_confirmation_required or self.autonomous_decisions_allowed:
            raise ValueError("adjudication policy must preserve founder authority")
        return self


class CitationUnclearAdjudicationService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def adjudicate(
        self,
        prior_receipt: CitationRecommendationReceipt,
        enrichment_receipt: CitationEnrichmentReceipt,
        policy: CitationAdjudicationPolicy,
        *,
        code_revision: str,
    ) -> CitationRecommendationReceipt:
        self._validate_inputs(
            prior_receipt, enrichment_receipt, policy, code_revision
        )
        prior = self._load_prior(prior_receipt)
        enriched = self._load_enriched(enrichment_receipt)
        unresolved = [
            item for item in prior if item.recommendation is ScreeningDecision.UNCLEAR
        ]
        enriched_by_key = {item.record_key: item for item in enriched}
        unresolved_keys = {item.record_key for item in unresolved}
        include_keys = set(policy.include_record_keys)
        unknown = include_keys - unresolved_keys
        if unknown:
            raise ValueError(
                f"adjudication policy includes records outside unresolved set: {sorted(unknown)}"
            )

        recommendations = [
            self._recommend(
                previous,
                enriched_by_key[previous.record_key],
                include=previous.record_key in include_keys,
            )
            for previous in unresolved
        ]
        recommendations.sort(key=lambda item: item.rank)
        created_at = self._clock()
        policy_hash = sha256(canonical_json(policy.model_dump(mode="json")))
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "code_revision": code_revision,
            "created_at": created_at.isoformat(),
            "policy_sha256": policy_hash,
            "prior_recommendation_id": prior_receipt.recommendation_id,
        }
        recommendation_id = sha256(canonical_json(identity))
        key = (
            f"citation-screening/{prior_receipt.study_id}/"
            f"pass-{prior_receipt.pass_number:04d}/"
            f"adjudication-{recommendation_id}.json"
        )
        body = canonical_json(
            [item.model_dump(mode="json", exclude_none=True) for item in recommendations]
        )
        stored = self._store_object(key, body)
        return CitationRecommendationReceipt(
            recommendation_id=recommendation_id,
            study_id=prior_receipt.study_id,
            pass_number=prior_receipt.pass_number,
            enrichment_id=enrichment_receipt.enrichment_id,
            algorithm_version=f"{ALGORITHM_VERSION}+policy-{policy.policy_version}",
            code_revision=code_revision,
            created_at=created_at,
            verified_at=self._clock(),
            candidate_count=len(recommendations),
            include_recommendation_count=sum(
                item.recommendation is ScreeningDecision.INCLUDE
                for item in recommendations
            ),
            exclude_recommendation_count=sum(
                item.recommendation is ScreeningDecision.EXCLUDE
                for item in recommendations
            ),
            unclear_recommendation_count=0,
            high_confidence_count=sum(
                item.confidence is AdvisoryConfidence.HIGH
                for item in recommendations
            ),
            abstract_unavailable_count=sum(
                not item.abstract_available for item in recommendations
            ),
            recommendations_object=stored,
            input_checksum_verified=True,
            output_checksum_verified=True,
            record_coverage_verified=len(
                {item.record_key for item in recommendations}
            )
            == len(unresolved),
        )

    @staticmethod
    def _recommend(
        previous: CitationScreeningRecommendation,
        enriched: EnrichedCitationCandidate,
        *,
        include: bool,
    ) -> CitationScreeningRecommendation:
        if include:
            return previous.model_copy(
                update={
                    "recommendation": ScreeningDecision.INCLUDE,
                    "confidence": (
                        AdvisoryConfidence.HIGH
                        if enriched.abstract is not None
                        else AdvisoryConfidence.MODERATE
                    ),
                    "exclusion_reason": None,
                    "rationale": (
                        "Second-stage review identifies a direct classifier, assay, "
                        "platform, specimen, normalization, or implementation-comparison "
                        "contribution relevant to the locked reliability question."
                    ),
                    "matched_signals": [
                        *previous.matched_signals,
                        "second_stage_direct_method",
                    ],
                }
            )
        if _SECONDARY.search(enriched.title):
            reason = (
                ScreeningExclusionReason.REVIEW_EDITORIAL_OR_COMMENTARY_FOR_CITATION_CHAINING_ONLY
            )
            rationale = (
                "Second-stage review identifies secondary, guideline, commentary, "
                "or perspective literature retained only for citation chaining."
            )
            confidence = AdvisoryConfidence.HIGH
        elif _NONHUMAN.search(enriched.title):
            reason = (
                ScreeningExclusionReason.NONHUMAN_OR_NO_PRIMARY_HUMAN_TUMOR_COHORT
            )
            rationale = (
                "Second-stage review identifies a nonhuman study outside the primary "
                "human-tumor evidence requirement."
            )
            confidence = AdvisoryConfidence.HIGH
        else:
            reason = (
                ScreeningExclusionReason.NO_RELEVANT_DISCORDANCE_STABILITY_OR_CLASSIFIER_METHOD
            )
            rationale = (
                "Second-stage review finds outcome, treatment, biomarker, taxonomy, "
                "or general molecular content without a direct contribution to the "
                "locked classifier reliability, uncertainty, preprocessing, or "
                "transport question."
            )
            confidence = (
                AdvisoryConfidence.MODERATE
                if enriched.abstract is not None
                else AdvisoryConfidence.LOW
            )
        return previous.model_copy(
            update={
                "recommendation": ScreeningDecision.EXCLUDE,
                "confidence": confidence,
                "exclusion_reason": reason,
                "rationale": rationale,
                "matched_signals": [
                    *previous.matched_signals,
                    "second_stage_not_direct",
                ],
            }
        )

    def _load_prior(
        self, receipt: CitationRecommendationReceipt
    ) -> list[CitationScreeningRecommendation]:
        body = self._verified_body(receipt.recommendations_object)
        try:
            recommendations = _RECOMMENDATIONS.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise ValueError("prior citation recommendations are invalid") from error
        if len(recommendations) != receipt.candidate_count:
            raise ValueError("prior citation recommendation count does not reconcile")
        return recommendations

    def _load_enriched(
        self, receipt: CitationEnrichmentReceipt
    ) -> list[EnrichedCitationCandidate]:
        body = self._verified_body(receipt.enriched_candidates_object)
        try:
            records = _ENRICHED.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise ValueError("enriched citation inventory is invalid") from error
        if len(records) != receipt.requested_candidate_count:
            raise ValueError("enriched citation count does not reconcile")
        return records

    @staticmethod
    def _validate_inputs(
        prior: CitationRecommendationReceipt,
        enrichment: CitationEnrichmentReceipt,
        policy: CitationAdjudicationPolicy,
        code_revision: str,
    ) -> None:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise ValueError("code revision must be a 7-to-40 character Git SHA")
        if (
            prior.study_id != enrichment.study_id
            or prior.study_id != policy.study_id
            or prior.pass_number != enrichment.pass_number
            or prior.pass_number != policy.pass_number
            or prior.enrichment_id != enrichment.enrichment_id
            or prior.recommendation_id != policy.based_on_recommendation_id
        ):
            raise ValueError("citation adjudication inputs identify different passes")
        if prior.unclear_recommendation_count == 0:
            raise ValueError("citation adjudication requires unresolved recommendations")

    def _verified_body(self, stored: StoredObject) -> bytes:
        body = self._store.get_bytes(stored.object_key)
        if len(body) != stored.size_bytes or sha256(body) != stored.sha256:
            raise ValueError("citation adjudication input checksum is invalid")
        return body

    def _store_object(self, key: str, body: bytes) -> StoredObject:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
        else:
            self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )


def load_citation_adjudication_policy(path: Path) -> CitationAdjudicationPolicy:
    return CitationAdjudicationPolicy.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
