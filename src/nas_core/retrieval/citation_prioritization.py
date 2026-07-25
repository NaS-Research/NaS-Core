"""Transparent title-only prioritization for citation-chain founder screening."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import TypeAdapter, ValidationError

from nas_core.domain.citation_chain import (
    CitationCandidate,
    CitationPrioritizationReceipt,
    CitationPriorityRecord,
    CitationPriorityTier,
    CitationScreeningPreparationReceipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "citation-title-priority-1.0.1"
JSON_MEDIA_TYPE = "application/json"
_CANDIDATES = TypeAdapter(list[CitationCandidate])


@dataclass(frozen=True)
class TitleSignal:
    name: str
    pattern: re.Pattern[str]
    weight: int


POSITIVE_SIGNALS = (
    TitleSignal(
        "pam50_intrinsic_or_prosigna",
        re.compile(r"\b(pam[ -]?50|intrinsic subtyp\w*|prosigna)\b", re.I),
        8,
    ),
    TitleSignal("single_sample", re.compile(r"\bsingle[- ]sample\b", re.I), 6),
    TitleSignal(
        "classifier_or_subtyping_method",
        re.compile(r"\b(classif\w*|centroid\w*|molecular subtyp\w*|predictor)\b", re.I),
        4,
    ),
    TitleSignal(
        "preprocessing_or_transport",
        re.compile(
            r"\b(normaliz\w*|preprocess\w*|center\w*|cross[- ]platform|"
            r"transport\w*|assay|rna[- ]?seq|nanostring)\b",
            re.I,
        ),
        4,
    ),
    TitleSignal(
        "reliability_or_agreement",
        re.compile(
            r"\b(stabil\w*|reproduc\w*|robust\w*|discordan\w*|concordan\w*|"
            r"agreement)\b",
            re.I,
        ),
        5,
    ),
    TitleSignal(
        "patient_level_uncertainty",
        re.compile(
            r"\b(uncertain\w*|confidence|margin|ambiguous|abstain\w*|"
            r"unclassif\w*|not assigned)\b",
            re.I,
        ),
        6,
    ),
    TitleSignal("breast_cancer", re.compile(r"\bbreast\b", re.I), 3),
    TitleSignal(
        "human_evaluation",
        re.compile(r"\b(patient\w*|tumou?r\w*|cohort\w*|clinical)\b", re.I),
        1,
    ),
)

CAUTION_SIGNALS = (
    TitleSignal(
        "secondary_literature",
        re.compile(r"\b(review|editorial|commentary|meta-analysis)\b", re.I),
        -3,
    ),
    TitleSignal(
        "nonhuman_or_cell_line",
        re.compile(r"\b(mouse|mice|murine|xenograft|cell line)\b", re.I),
        -3,
    ),
)


class CitationPrioritizationError(RuntimeError):
    """Raised when citation-title prioritization cannot be independently verified."""


class CitationPrioritizationService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def prioritize(
        self,
        preparation: CitationScreeningPreparationReceipt,
        *,
        code_revision: str,
    ) -> CitationPrioritizationReceipt:
        self._validate_input(preparation, code_revision)
        body = self._verified_body(preparation.screening_candidates_object)
        try:
            candidates = _CANDIDATES.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationPrioritizationError(
                "citation screening candidates are invalid"
            ) from error
        if len(candidates) != preparation.requires_screening_count:
            raise CitationPrioritizationError(
                "citation screening candidate count does not reconcile"
            )

        scored = [self._score(candidate) for candidate in candidates]
        scored.sort(
            key=lambda item: (
                -item[0],
                -(item[3].publication_year or 0),
                item[3].record_key,
            )
        )
        ranked = [
            CitationPriorityRecord(
                rank=rank,
                score=score,
                tier=self._tier(score),
                positive_signals=positive,
                caution_signals=cautions,
                candidate=candidate,
            )
            for rank, (score, positive, cautions, candidate) in enumerate(
                scored, start=1
            )
        ]
        created_at = self._clock()
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "code_revision": code_revision,
            "created_at": created_at.isoformat(),
            "preparation_id": preparation.preparation_id,
            "study_id": preparation.study_id,
        }
        prioritization_id = sha256(canonical_json(identity))
        key = (
            f"citation-screening/{preparation.study_id}/"
            f"pass-{preparation.pass_number:04d}/{preparation.preparation_id}/"
            f"priority-{prioritization_id}.json"
        )
        ranking_body = canonical_json(
            [item.model_dump(mode="json", exclude_none=True) for item in ranked]
        )
        ranking_object = self._store_object(key, ranking_body)
        tiers = [item.tier for item in ranked]
        return CitationPrioritizationReceipt(
            prioritization_id=prioritization_id,
            study_id=preparation.study_id,
            pass_number=preparation.pass_number,
            preparation_id=preparation.preparation_id,
            algorithm_version=ALGORITHM_VERSION,
            code_revision=code_revision,
            created_at=created_at,
            verified_at=self._clock(),
            candidate_count=len(ranked),
            direct_priority_count=tiers.count(CitationPriorityTier.DIRECT),
            supporting_priority_count=tiers.count(CitationPriorityTier.SUPPORTING),
            context_priority_count=tiers.count(CitationPriorityTier.CONTEXT),
            ranking_object=ranking_object,
            input_checksum_verified=True,
            output_checksum_verified=True,
            rank_invariants_verified=[item.rank for item in ranked]
            == list(range(1, len(ranked) + 1)),
        )

    @staticmethod
    def _score(
        candidate: CitationCandidate,
    ) -> tuple[int, list[str], list[str], CitationCandidate]:
        positive = [
            signal.name
            for signal in POSITIVE_SIGNALS
            if signal.pattern.search(candidate.title)
        ]
        cautions = [
            signal.name
            for signal in CAUTION_SIGNALS
            if signal.pattern.search(candidate.title)
        ]
        score = sum(
            signal.weight
            for signal in (*POSITIVE_SIGNALS, *CAUTION_SIGNALS)
            if signal.pattern.search(candidate.title)
        )
        return score, positive, cautions, candidate

    @staticmethod
    def _tier(score: int) -> CitationPriorityTier:
        if score >= 12:
            return CitationPriorityTier.DIRECT
        if score >= 6:
            return CitationPriorityTier.SUPPORTING
        return CitationPriorityTier.CONTEXT

    @staticmethod
    def _validate_input(
        preparation: CitationScreeningPreparationReceipt,
        code_revision: str,
    ) -> None:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationPrioritizationError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        if not all(
            (
                preparation.input_checksums_verified,
                preparation.output_checksums_verified,
                preparation.count_invariants_verified,
            )
        ):
            raise CitationPrioritizationError(
                "citation prioritization requires verified preparation"
            )
        if (
            preparation.final_screening_decisions_recorded
            or preparation.scientific_conclusions_drawn
        ):
            raise CitationPrioritizationError(
                "citation preparation exceeds the advisory boundary"
            )

    def _verified_body(self, stored: StoredObject) -> bytes:
        body = self._store.get_bytes(stored.object_key)
        if len(body) != stored.size_bytes or sha256(body) != stored.sha256:
            raise CitationPrioritizationError(
                "citation screening candidates do not match their receipt"
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
            raise CitationPrioritizationError("stored prioritization object changed")
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )
