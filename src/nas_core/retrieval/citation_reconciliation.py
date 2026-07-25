"""Reconcile confirmed citation inclusions against governed evidence identities."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime

from nas_core.domain.appraisal import FullTextAppraisal, FullTextInventory
from nas_core.domain.citation_confirmation import CitationDecisionLedgerReceipt
from nas_core.domain.citation_reconciliation import (
    CitationInclusionDisposition,
    CitationInclusionReconciliationReceipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

JSON_MEDIA_TYPE = "application/json"


class CitationReconciliationError(RuntimeError):
    """Raised when confirmed citation inclusions cannot be reconciled safely."""


class CitationInclusionReconciliationService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def reconcile(
        self,
        decision: CitationDecisionLedgerReceipt,
        inventory: FullTextInventory,
        appraisals: list[FullTextAppraisal],
        *,
        code_revision: str,
        reconciled_at: datetime | None = None,
    ) -> CitationInclusionReconciliationReceipt:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationReconciliationError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        if decision.study_id != inventory.study_id or any(
            appraisal.study_id != decision.study_id for appraisal in appraisals
        ):
            raise CitationReconciliationError(
                "decision, inventory, and appraisal study identities differ"
            )
        ledger_body = self._store.get_bytes(decision.ledger_object.object_key)
        if (
            len(ledger_body) != decision.ledger_object.size_bytes
            or sha256(ledger_body) != decision.ledger_object.sha256
        ):
            raise CitationReconciliationError("citation decision ledger checksum failed")
        ledger = self._load_ledger(ledger_body)
        included = [row for row in ledger if row["decision"] == "include"]
        if len(included) != decision.included_count:
            raise CitationReconciliationError(
                "citation ledger inclusion count does not match its receipt"
            )

        inventory_index = self._build_inventory_index(inventory)
        appraisal_index = self._build_appraisal_index(appraisals)
        rows: list[dict[str, object]] = []
        for citation in included:
            identifiers = self._identifiers(citation)
            inventory_matches = self._matches(identifiers, inventory_index)
            appraisal_matches = self._matches(identifiers, appraisal_index)
            if len(inventory_matches) > 1 or len(appraisal_matches) > 1:
                raise CitationReconciliationError(
                    f"citation identifiers resolve to conflicting records: "
                    f"{citation['record_key']}"
                )
            base: dict[str, object] = {
                "record_key": citation["record_key"],
                "title": citation["title"],
                "pmid": citation.get("pmid"),
                "pmcid": citation.get("pmcid"),
                "doi": citation.get("doi"),
            }
            if inventory_matches:
                match = next(iter(inventory_matches.values()))
                base.update(
                    disposition=CitationInclusionDisposition.ACTIVE_INVENTORY,
                    matched_identifiers=self._matching_identifier_names(
                        identifiers, match["identifiers"]
                    ),
                    matched_screening_id=match["screening_id"],
                    matched_record_key=match["record_key"],
                )
            elif appraisal_matches:
                match = next(iter(appraisal_matches.values()))
                base.update(
                    disposition=CitationInclusionDisposition.PRIOR_APPRAISAL,
                    matched_identifiers=self._matching_identifier_names(
                        identifiers, match["identifiers"]
                    ),
                    matched_screening_id=match["screening_id"],
                    matched_record_key=None,
                )
            else:
                base.update(
                    disposition=CitationInclusionDisposition.NET_NEW,
                    matched_identifiers=[],
                    matched_screening_id=None,
                    matched_record_key=None,
                )
            rows.append(base)

        normalized_rows = [
            {
                key: (value.value if isinstance(value, CitationInclusionDisposition) else value)
                for key, value in row.items()
                if value is not None
            }
            for row in sorted(rows, key=lambda item: str(item["record_key"]))
        ]
        timestamp = reconciled_at or datetime.now(UTC)
        identity = {
            "code_revision": code_revision,
            "decision_id": decision.decision_id,
            "inventory_queue_id": inventory.queue_id,
            "prior_appraisal_screening_ids": sorted(
                {appraisal.screening_id for appraisal in appraisals}
            ),
            "reconciled_at": timestamp.isoformat(),
            "study_id": decision.study_id,
        }
        reconciliation_id = sha256(canonical_json(identity))
        artifact = canonical_json(normalized_rows)
        key = (
            f"citation-screening/{decision.study_id}/"
            f"pass-{decision.pass_number:04d}/"
            f"inclusion-reconciliation-{reconciliation_id}.json"
        )
        stored = self._store_object(key, artifact)
        active = sum(
            row["disposition"] is CitationInclusionDisposition.ACTIVE_INVENTORY
            for row in rows
        )
        prior = sum(
            row["disposition"] is CitationInclusionDisposition.PRIOR_APPRAISAL
            for row in rows
        )
        net_new = len(rows) - active - prior
        return CitationInclusionReconciliationReceipt(
            reconciliation_id=reconciliation_id,
            study_id=decision.study_id,
            pass_number=decision.pass_number,
            decision_id=decision.decision_id,
            code_revision=code_revision,
            reconciled_at=timestamp,
            confirmed_inclusion_count=len(rows),
            active_inventory_match_count=active,
            prior_appraisal_match_count=prior,
            net_new_count=net_new,
            inventory_record_count=len(inventory.records),
            prior_appraisal_count=len({item.screening_id for item in appraisals}),
            reconciliation_object=stored,
            decision_ledger_checksum_verified=True,
            exact_identifier_matching_only=True,
            count_invariants_verified=True,
            founder_decisions_changed=0,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _load_ledger(body: bytes) -> list[dict[str, object]]:
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CitationReconciliationError(
                "citation decision ledger is not valid JSON"
            ) from error
        if not isinstance(payload, list) or any(
            not isinstance(row, dict)
            or row.get("decision") not in {"include", "exclude"}
            or not isinstance(row.get("record_key"), str)
            or not isinstance(row.get("title"), str)
            for row in payload
        ):
            raise CitationReconciliationError("citation decision ledger rows are invalid")
        return payload

    @classmethod
    def _build_inventory_index(
        cls, inventory: FullTextInventory
    ) -> dict[str, dict[str, object]]:
        return cls._build_index(
            [
                {
                    "screening_id": item.screening_id,
                    "record_key": item.record_key,
                    "identifiers": cls._identifiers(item.model_dump()),
                    "assessed_at": "",
                }
                for item in inventory.records
            ]
        )

    @classmethod
    def _build_appraisal_index(
        cls, appraisals: list[FullTextAppraisal]
    ) -> dict[str, dict[str, object]]:
        unique = {item.screening_id: item for item in appraisals}
        return cls._build_index(
            [
                {
                    "screening_id": item.screening_id,
                    "record_key": None,
                    "identifiers": cls._identifiers(item.model_dump()),
                    "assessed_at": item.assessed_at.isoformat(),
                }
                for item in unique.values()
            ]
        )

    @staticmethod
    def _build_index(
        records: list[dict[str, object]],
    ) -> dict[str, dict[str, object]]:
        index: dict[str, dict[str, object]] = {}
        for record in records:
            identifiers = record["identifiers"]
            assert isinstance(identifiers, dict)
            for value in identifiers.values():
                existing = index.get(value)
                if existing is None or str(record["assessed_at"]) > str(
                    existing["assessed_at"]
                ):
                    index[value] = record
        return index

    @staticmethod
    def _identifiers(record: dict[str, object]) -> dict[str, str]:
        identifiers: dict[str, str] = {}
        pmid = record.get("pmid")
        pmcid = record.get("pmcid")
        doi = record.get("doi")
        if isinstance(pmid, str) and pmid.strip():
            identifiers["pmid"] = f"pmid:{pmid.strip()}"
        if isinstance(pmcid, str) and pmcid.strip():
            identifiers["pmcid"] = f"pmcid:{pmcid.strip().upper()}"
        if isinstance(doi, str) and doi.strip():
            normalized = doi.strip().lower()
            for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
                if normalized.startswith(prefix):
                    normalized = normalized[len(prefix) :]
            identifiers["doi"] = f"doi:{normalized}"
        return identifiers

    @staticmethod
    def _matches(
        identifiers: dict[str, str],
        index: dict[str, dict[str, object]],
    ) -> dict[str, dict[str, object]]:
        return {
            str(match["screening_id"]): match
            for value in identifiers.values()
            if (match := index.get(value)) is not None
        }

    @staticmethod
    def _matching_identifier_names(
        candidate: dict[str, str],
        existing: object,
    ) -> list[str]:
        assert isinstance(existing, dict)
        return sorted(
            name
            for name, value in candidate.items()
            if existing.get(name) == value
        )

    def _store_object(self, key: str, body: bytes) -> StoredObject:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
        else:
            self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
        stored = self._store.get_bytes(key)
        if stored != body:
            raise CitationReconciliationError("stored reconciliation artifact changed")
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )
