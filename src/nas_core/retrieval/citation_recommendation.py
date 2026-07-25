"""Conservative abstract-informed recommendations for founder citation screening."""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import TypeAdapter, ValidationError

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

ALGORITHM_VERSION = "citation-abstract-advisory-1.0.2"
JSON_MEDIA_TYPE = "application/json"
_ENRICHED = TypeAdapter(list[EnrichedCitationCandidate])
_HTML_TAG = re.compile(r"<[^>]+>")

_DOMAIN = re.compile(
    r"\b(pam[ -]?50|intrinsic subtyp\w*|prosigna|single[- ]sample)\b", re.I
)
_STRONG_METHOD = re.compile(
    r"\b(stabil\w*|reproduc\w*|robust\w*|discordan\w*|concordan\w*|agreement|"
    r"normaliz\w*|preprocess\w*|center\w*|cross[- ]platform|transport\w*|"
    r"uncertain\w*|confidence|margin|ambiguous|abstain\w*|unclassif\w*|"
    r"technical error|measurement error|sample preparation|fixative\w*|"
    r"analytical validation|verification|assay development|classifier comparison)\b",
    re.I,
)
_CLASSIFIER_METHOD = re.compile(
    r"\b(classif\w*|centroid\w*|predictor\w*|subtyp\w*|gene expression|"
    r"transcriptom\w*|microarray)\b",
    re.I,
)
_OUTCOME_OR_TREATMENT = re.compile(
    r"\b(survival|prognos\w*|recurrence|treatment decision|chemotherapy|"
    r"therapy|response|clinical outcome|risk of recurrence)\b",
    re.I,
)
_CLINICAL_OUTCOME_FOCUS = re.compile(
    r"\b(survival|prognos\w*|risk prediction|treatment|chemotherapy|therapy|response)\b",
    re.I,
)
_SUBTYPE_TRANSCRIPTOMIC = re.compile(
    r"\b(subtyp\w*|transcriptom\w*|gene expression|microarray)\b", re.I
)
_DETECTION = re.compile(r"\b(detection|diagnosis|screening)\b", re.I)
_SECONDARY = re.compile(r"\b(review|editorial|commentary|meta-analysis)\b", re.I)
_NONHUMAN = re.compile(r"\b(mouse|mice|murine|xenograft|cell line)\b", re.I)
_HUMAN = re.compile(r"\b(patient\w*|human|tumou?r\w*|cohort\w*|clinical sample)\b", re.I)


class CitationRecommendationError(RuntimeError):
    """Raised when abstract advisory recommendations cannot be verified."""


class CitationRecommendationService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def recommend(
        self,
        enrichment: CitationEnrichmentReceipt,
        *,
        code_revision: str,
    ) -> CitationRecommendationReceipt:
        self._validate_input(enrichment, code_revision)
        body = self._verified_body(enrichment.enriched_candidates_object)
        try:
            candidates = _ENRICHED.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationRecommendationError(
                "enriched citation candidates are invalid"
            ) from error
        if len(candidates) != enrichment.requested_candidate_count:
            raise CitationRecommendationError(
                "enriched citation candidate count does not reconcile"
            )
        recommendations = [self._recommend(item) for item in candidates]
        recommendations.sort(key=lambda item: item.rank)
        created_at = self._clock()
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "code_revision": code_revision,
            "created_at": created_at.isoformat(),
            "enrichment_id": enrichment.enrichment_id,
            "study_id": enrichment.study_id,
        }
        recommendation_id = sha256(canonical_json(identity))
        key = (
            f"citation-screening/{enrichment.study_id}/"
            f"pass-{enrichment.pass_number:04d}/recommendations-{recommendation_id}.json"
        )
        recommendation_body = canonical_json(
            [item.model_dump(mode="json", exclude_none=True) for item in recommendations]
        )
        recommendation_object = self._store_object(key, recommendation_body)
        return CitationRecommendationReceipt(
            recommendation_id=recommendation_id,
            study_id=enrichment.study_id,
            pass_number=enrichment.pass_number,
            enrichment_id=enrichment.enrichment_id,
            algorithm_version=ALGORITHM_VERSION,
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
            unclear_recommendation_count=sum(
                item.recommendation is ScreeningDecision.UNCLEAR
                for item in recommendations
            ),
            high_confidence_count=sum(
                item.confidence is AdvisoryConfidence.HIGH
                for item in recommendations
            ),
            abstract_unavailable_count=sum(
                not item.abstract_available for item in recommendations
            ),
            recommendations_object=recommendation_object,
            input_checksum_verified=True,
            output_checksum_verified=True,
            record_coverage_verified=len(
                {item.record_key for item in recommendations}
            )
            == len(recommendations),
        )

    @classmethod
    def _recommend(
        cls, candidate: EnrichedCitationCandidate
    ) -> CitationScreeningRecommendation:
        title = cls._clean(candidate.title)
        abstract = cls._clean(candidate.abstract or "")
        combined = f"{title}\n{abstract}"
        signals = cls._signals(title, combined)

        if candidate.abstract is None:
            return cls._result(
                candidate,
                ScreeningDecision.UNCLEAR,
                AdvisoryConfidence.LOW,
                "No abstract is available; founder title-level adjudication is required.",
                signals,
            )
        if _SECONDARY.search(title):
            return cls._result(
                candidate,
                ScreeningDecision.EXCLUDE,
                AdvisoryConfidence.HIGH,
                "The title identifies secondary literature retained only for citation chaining.",
                signals,
                ScreeningExclusionReason.REVIEW_EDITORIAL_OR_COMMENTARY_FOR_CITATION_CHAINING_ONLY,
            )
        if _NONHUMAN.search(title) and not _HUMAN.search(combined):
            return cls._result(
                candidate,
                ScreeningDecision.EXCLUDE,
                AdvisoryConfidence.HIGH,
                "The record is nonhuman or cell-line focused without a primary human tumor cohort.",
                signals,
                ScreeningExclusionReason.NONHUMAN_OR_NO_PRIMARY_HUMAN_TUMOR_COHORT,
            )

        title_domain = bool(_DOMAIN.search(title))
        title_method = bool(_STRONG_METHOD.search(title))
        combined_domain = bool(_DOMAIN.search(combined))
        combined_method = bool(_STRONG_METHOD.search(combined))
        classifier_method = bool(_CLASSIFIER_METHOD.search(combined))
        outcome_title = bool(_OUTCOME_OR_TREATMENT.search(title))
        clinical_outcome_focus = bool(_CLINICAL_OUTCOME_FOCUS.search(title))

        if (
            title_domain
            and title_method
            and classifier_method
            and not clinical_outcome_focus
        ):
            return cls._result(
                candidate,
                ScreeningDecision.INCLUDE,
                AdvisoryConfidence.HIGH,
                "The title directly joins the locked classifier domain to a reliability, "
                "assay, preprocessing, uncertainty, or transport method.",
                signals,
            )
        if (
            re.search(r"\bsingle[- ]sample\b", title, re.I)
            and classifier_method
            and combined_method
            and _SUBTYPE_TRANSCRIPTOMIC.search(combined)
            and not _DETECTION.search(title)
            and not clinical_outcome_focus
        ):
            return cls._result(
                candidate,
                ScreeningDecision.INCLUDE,
                AdvisoryConfidence.HIGH,
                "The record directly evaluates a single-sample transcriptomic classifier "
                "or preprocessing method relevant to patient-independent execution.",
                signals,
            )
        if title_domain and outcome_title and not title_method:
            return cls._result(
                candidate,
                ScreeningDecision.EXCLUDE,
                AdvisoryConfidence.HIGH,
                "The record uses a relevant subtype or assay for prognosis, treatment, or "
                "outcome association without a qualifying reliability-method focus.",
                signals,
                ScreeningExclusionReason.NO_RELEVANT_DISCORDANCE_STABILITY_OR_CLASSIFIER_METHOD,
            )
        if combined_domain and combined_method and classifier_method:
            return cls._result(
                candidate,
                ScreeningDecision.UNCLEAR,
                AdvisoryConfidence.MODERATE,
                "The abstract contains relevant classifier and reliability signals, but "
                "direct eligibility is not unambiguous from deterministic rules.",
                signals,
            )
        return cls._result(
            candidate,
            ScreeningDecision.EXCLUDE,
            AdvisoryConfidence.MODERATE,
            "The title and abstract do not jointly establish a qualifying single-sample "
            "classifier reliability, uncertainty, preprocessing, or transport method.",
            signals,
            ScreeningExclusionReason.NO_RELEVANT_DISCORDANCE_STABILITY_OR_CLASSIFIER_METHOD,
        )

    @staticmethod
    def _signals(title: str, combined: str) -> list[str]:
        checks = (
            ("domain_in_title", _DOMAIN.search(title)),
            ("domain_in_record", _DOMAIN.search(combined)),
            ("strong_method_in_title", _STRONG_METHOD.search(title)),
            ("strong_method_in_record", _STRONG_METHOD.search(combined)),
            ("classifier_method", _CLASSIFIER_METHOD.search(combined)),
            ("outcome_or_treatment_in_title", _OUTCOME_OR_TREATMENT.search(title)),
            ("secondary_literature_in_title", _SECONDARY.search(title)),
            ("nonhuman_in_title", _NONHUMAN.search(title)),
        )
        return [name for name, match in checks if match]

    @staticmethod
    def _result(
        candidate: EnrichedCitationCandidate,
        decision: ScreeningDecision,
        confidence: AdvisoryConfidence,
        rationale: str,
        signals: list[str],
        exclusion_reason: ScreeningExclusionReason | None = None,
    ) -> CitationScreeningRecommendation:
        return CitationScreeningRecommendation(
            record_key=candidate.record_key,
            title=candidate.title,
            pmid=candidate.pmid,
            pmcid=candidate.pmcid,
            doi=candidate.doi,
            rank=candidate.rank,
            priority_tier=candidate.tier,
            recommendation=decision,
            confidence=confidence,
            exclusion_reason=exclusion_reason,
            rationale=rationale,
            matched_signals=signals,
            abstract_available=candidate.abstract is not None,
            founder_decision_recorded=False,
        )

    @staticmethod
    def _clean(value: str) -> str:
        return " ".join(html.unescape(_HTML_TAG.sub(" ", value)).split())

    @staticmethod
    def _validate_input(
        enrichment: CitationEnrichmentReceipt,
        code_revision: str,
    ) -> None:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationRecommendationError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        if enrichment.selection_scope.value != "all_candidates":
            raise CitationRecommendationError(
                "citation recommendations require full-scope enrichment"
            )
        if not all(
            (
                enrichment.input_checksum_verified,
                enrichment.output_checksums_verified,
                enrichment.record_coverage_verified,
            )
        ):
            raise CitationRecommendationError(
                "citation recommendations require verified enrichment"
            )
        if (
            enrichment.final_screening_decisions_recorded
            or enrichment.scientific_conclusions_drawn
        ):
            raise CitationRecommendationError(
                "citation enrichment exceeds the advisory boundary"
            )

    def _verified_body(self, stored: StoredObject) -> bytes:
        body = self._store.get_bytes(stored.object_key)
        if len(body) != stored.size_bytes or sha256(body) != stored.sha256:
            raise CitationRecommendationError(
                "enriched citation candidates do not match their receipt"
            )
        return body

    def _store_object(self, key: str, body: bytes) -> StoredObject:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
        else:
            self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
        stored = self._store.get_bytes(key)
        if stored != body:
            raise CitationRecommendationError("stored recommendation object changed")
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )
