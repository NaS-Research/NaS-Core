"""Batched Europe PMC metadata enrichment for prioritized citation candidates."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import TypeAdapter, ValidationError

from nas_core.domain.citation_chain import (
    CitationEnrichmentReceipt,
    CitationEnrichmentScope,
    CitationPrioritizationReceipt,
    CitationPriorityRecord,
    CitationPriorityTier,
    EnrichedCitationCandidate,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import (
    ImmutableObjectConflictError,
    RemoteResponseError,
    canonical_json,
    sha256,
)
from nas_core.retrieval.literature import (
    EUROPE_PMC_SEARCH_URL,
    LiteratureTransport,
    UrllibLiteratureTransport,
)
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "citation-metadata-enrichment-1.1.0"
JSON_MEDIA_TYPE = "application/json"
BATCH_SIZE = 50
_RANKINGS = TypeAdapter(list[CitationPriorityRecord])


class CitationEnrichmentError(RuntimeError):
    """Raised when citation metadata enrichment or verification fails."""


class CitationEnrichmentService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        transport: LiteratureTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._transport = transport or UrllibLiteratureTransport()
        self._clock = clock or (lambda: datetime.now(UTC))

    def enrich(
        self,
        prioritization: CitationPrioritizationReceipt,
        *,
        code_revision: str,
        include_context: bool = False,
    ) -> CitationEnrichmentReceipt:
        self._validate_input(prioritization, code_revision)
        ranking_body = self._verified_body(prioritization.ranking_object)
        try:
            ranking = _RANKINGS.validate_python(json.loads(ranking_body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationEnrichmentError("citation ranking is invalid") from error
        if len(ranking) != prioritization.candidate_count:
            raise CitationEnrichmentError("citation ranking count does not reconcile")
        selected = (
            ranking
            if include_context
            else [
                item
                for item in ranking
                if item.tier is not CitationPriorityTier.CONTEXT
            ]
        )
        selection_scope = (
            CitationEnrichmentScope.ALL_CANDIDATES
            if include_context
            else CitationEnrichmentScope.DIRECT_AND_SUPPORTING
        )

        by_source: dict[str, list[CitationPriorityRecord]] = defaultdict(list)
        for item in selected:
            by_source[item.candidate.source].append(item)
        raw_responses: list[dict[str, object]] = []
        matches: dict[str, dict[str, object]] = {}
        request_count = 0
        for source in sorted(by_source):
            source_records = sorted(
                by_source[source], key=lambda item: item.candidate.external_id
            )
            for start in range(0, len(source_records), BATCH_SIZE):
                batch = source_records[start : start + BATCH_SIZE]
                payload = self._request_batch(source, batch)
                request_count += 1
                raw_responses.append(
                    {
                        "source": source,
                        "requested_record_keys": [
                            item.candidate.record_key for item in batch
                        ],
                        "payload": payload,
                    }
                )
                for result in self._results(payload):
                    result_source = str(result.get("source", "")).strip().upper()
                    external_id = str(result.get("id", "")).strip()
                    if result_source and external_id:
                        matches[f"{result_source}:{external_id}"] = result

        enriched = [
            self._enriched_record(item, matches.get(item.candidate.record_key))
            for item in selected
        ]
        created_at = self._clock()
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "code_revision": code_revision,
            "created_at": created_at.isoformat(),
            "prioritization_id": prioritization.prioritization_id,
            "selection_scope": selection_scope.value,
            "study_id": prioritization.study_id,
        }
        enrichment_id = sha256(canonical_json(identity))
        prefix = (
            f"citation-screening/{prioritization.study_id}/"
            f"pass-{prioritization.pass_number:04d}/enrichment-{enrichment_id}"
        )
        raw_body = canonical_json(raw_responses)
        enriched_body = canonical_json(
            [item.model_dump(mode="json", exclude_none=True) for item in enriched]
        )
        raw_object = self._store_object(f"{prefix}/raw-responses.json", raw_body)
        enriched_object = self._store_object(
            f"{prefix}/enriched-candidates.json", enriched_body
        )
        matched = sum(item.metadata_match_found for item in enriched)
        abstracts = sum(item.abstract is not None for item in enriched)
        return CitationEnrichmentReceipt(
            enrichment_id=enrichment_id,
            study_id=prioritization.study_id,
            pass_number=prioritization.pass_number,
            prioritization_id=prioritization.prioritization_id,
            selection_scope=selection_scope,
            code_revision=code_revision,
            created_at=created_at,
            verified_at=self._clock(),
            requested_candidate_count=len(enriched),
            metadata_match_count=matched,
            abstract_count=abstracts,
            unresolved_metadata_count=len(enriched) - matched,
            request_count=request_count,
            raw_responses_object=raw_object,
            enriched_candidates_object=enriched_object,
            input_checksum_verified=True,
            output_checksums_verified=True,
            record_coverage_verified=len({item.record_key for item in enriched})
            == len(enriched),
        )

    def _request_batch(
        self,
        source: str,
        batch: list[CitationPriorityRecord],
    ) -> dict[str, object]:
        external_ids = [item.candidate.external_id for item in batch]
        if any(not re.fullmatch(r"[A-Za-z0-9._-]+", item) for item in external_ids):
            raise CitationEnrichmentError("citation external ID is unsafe for query")
        clauses = " OR ".join(f'EXT_ID:"{item}"' for item in external_ids)
        query = f"SRC:{source} AND ({clauses})"
        response = self._transport.get(
            EUROPE_PMC_SEARCH_URL,
            {
                "query": query,
                "format": "json",
                "resultType": "core",
                "pageSize": str(BATCH_SIZE),
            },
        )
        if response.status_code != 200 or not response.body:
            raise RemoteResponseError(
                f"Europe PMC enrichment failed with status {response.status_code}"
            )
        try:
            payload = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CitationEnrichmentError(
                "Europe PMC enrichment returned invalid JSON"
            ) from error
        if not isinstance(payload, dict):
            raise CitationEnrichmentError(
                "Europe PMC enrichment response is not an object"
            )
        return payload

    @staticmethod
    def _results(payload: dict[str, object]) -> list[dict[str, object]]:
        result_list = payload.get("resultList", {})
        if not isinstance(result_list, dict):
            raise CitationEnrichmentError("Europe PMC result list is invalid")
        results = result_list.get("result", [])
        if results is None:
            return []
        if not isinstance(results, list) or any(
            not isinstance(item, dict) for item in results
        ):
            raise CitationEnrichmentError("Europe PMC results are invalid")
        return results

    @staticmethod
    def _enriched_record(
        ranked: CitationPriorityRecord,
        result: dict[str, object] | None,
    ) -> EnrichedCitationCandidate:
        candidate = ranked.candidate
        if result is None:
            return EnrichedCitationCandidate(
                **candidate.model_dump(),
                rank=ranked.rank,
                score=ranked.score,
                tier=ranked.tier,
                positive_signals=ranked.positive_signals,
                caution_signals=ranked.caution_signals,
                metadata_match_found=False,
            )
        abstract = str(result.get("abstractText", "")).strip() or None
        return EnrichedCitationCandidate(
            **candidate.model_dump(
                exclude={"title", "author_string", "journal", "publication_year"}
            ),
            title=str(result.get("title", "")).strip() or candidate.title,
            author_string=(
                str(result.get("authorString", "")).strip() or candidate.author_string
            ),
            journal=(
                str(result.get("journalTitle", "")).strip()
                or str(result.get("journalAbbreviation", "")).strip()
                or candidate.journal
            ),
            publication_year=CitationEnrichmentService._publication_year(
                result.get("pubYear"), candidate.publication_year
            ),
            pmid=str(result.get("pmid", "")).strip() or None,
            pmcid=str(result.get("pmcid", "")).strip() or None,
            doi=str(result.get("doi", "")).strip() or None,
            abstract=abstract,
            is_open_access=(
                str(result.get("isOpenAccess", "")).strip().upper() == "Y"
                if result.get("isOpenAccess") is not None
                else None
            ),
            rank=ranked.rank,
            score=ranked.score,
            tier=ranked.tier,
            positive_signals=ranked.positive_signals,
            caution_signals=ranked.caution_signals,
            metadata_match_found=True,
        )

    @staticmethod
    def _publication_year(value: object, fallback: int | None) -> int | None:
        if value is None or value == "":
            return fallback
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise CitationEnrichmentError("Europe PMC publication year is invalid")

    @staticmethod
    def _validate_input(
        prioritization: CitationPrioritizationReceipt,
        code_revision: str,
    ) -> None:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationEnrichmentError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        if not all(
            (
                prioritization.input_checksum_verified,
                prioritization.output_checksum_verified,
                prioritization.rank_invariants_verified,
            )
        ):
            raise CitationEnrichmentError(
                "citation enrichment requires verified prioritization"
            )
        if (
            prioritization.final_screening_decisions_recorded
            or prioritization.scientific_conclusions_drawn
        ):
            raise CitationEnrichmentError(
                "citation prioritization exceeds the advisory boundary"
            )

    def _verified_body(self, stored: StoredObject) -> bytes:
        body = self._store.get_bytes(stored.object_key)
        if len(body) != stored.size_bytes or sha256(body) != stored.sha256:
            raise CitationEnrichmentError("citation ranking does not match its receipt")
        return body

    def _store_object(self, key: str, body: bytes) -> StoredObject:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
        else:
            self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
        stored = self._store.get_bytes(key)
        if stored != body:
            raise CitationEnrichmentError("stored enrichment object changed")
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )
