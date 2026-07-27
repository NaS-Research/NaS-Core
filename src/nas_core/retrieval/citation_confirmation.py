"""Verify founder authority and freeze a complete citation-pass decision ledger."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from nas_core.domain.citation_chain import CitationFounderPacketReceipt
from nas_core.domain.citation_confirmation import (
    CitationDecisionLedgerReceipt,
    CitationFounderConfirmation,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

JSON_MEDIA_TYPE = "application/json"


class CitationConfirmationError(RuntimeError):
    """Raised when combined founder confirmation cannot reproduce both packets."""


class CitationDecisionConfirmationService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def confirm(
        self,
        first_packet: CitationFounderPacketReceipt,
        second_packet: CitationFounderPacketReceipt,
        confirmation: CitationFounderConfirmation,
        *,
        first_packet_path: Path,
        first_appendix_path: Path,
        second_packet_path: Path,
        second_appendix_path: Path,
        code_revision: str,
    ) -> CitationDecisionLedgerReceipt:
        self._validate_identities(
            first_packet, second_packet, confirmation, code_revision
        )
        assert confirmation.second_packet_sha256 is not None
        assert confirmation.second_appendix_sha256 is not None
        self._verify_file(
            first_packet_path,
            first_packet.packet_sha256,
            confirmation.first_packet_sha256,
        )
        self._verify_file(
            first_appendix_path,
            first_packet.appendix_sha256,
            confirmation.first_appendix_sha256,
        )
        self._verify_file(
            second_packet_path,
            second_packet.packet_sha256,
            confirmation.second_packet_sha256,
        )
        self._verify_file(
            second_appendix_path,
            second_packet.appendix_sha256,
            confirmation.second_appendix_sha256,
        )
        first_rows = self._read_appendix(first_appendix_path)
        second_rows = self._read_appendix(second_appendix_path)
        first_decided = [
            row for row in first_rows if row["recommendation"] != "unclear"
        ]
        first_unclear_keys = {
            row["record_key"]
            for row in first_rows
            if row["recommendation"] == "unclear"
        }
        second_keys = {row["record_key"] for row in second_rows}
        if first_unclear_keys != second_keys:
            raise CitationConfirmationError(
                "second packet does not exactly adjudicate the first packet's unclear set"
            )
        combined = first_decided + second_rows
        record_keys = [row["record_key"] for row in combined]
        if (
            len(combined) != first_packet.candidate_count
            or len(record_keys) != len(set(record_keys))
            or any(row["recommendation"] not in {"include", "exclude"} for row in combined)
            or any(row["founder_decision_recorded"] != "false" for row in combined)
        ):
            raise CitationConfirmationError(
                "combined citation decisions do not provide unique complete coverage"
            )
        ledger_rows = [
            {
                "record_key": row["record_key"],
                "rank": int(row["rank"]),
                "title": row["title"],
                "pmid": row["pmid"] or None,
                "pmcid": row["pmcid"] or None,
                "doi": row["doi"] or None,
                "decision": row["recommendation"],
                "exclusion_reason": row["exclusion_reason"] or None,
                "reviewer_id": confirmation.founder_id,
                "reviewer_name": confirmation.founder_name,
                "reviewer_role": confirmation.reviewer_role,
                "decided_at": confirmation.confirmed_at.isoformat(),
                "founder_authorized": True,
                "ai_decision": False,
            }
            for row in sorted(combined, key=lambda item: int(item["rank"]))
        ]
        identity = {
            "code_revision": code_revision,
            "confirmed_at": confirmation.confirmed_at.isoformat(),
            "first_appendix_sha256": confirmation.first_appendix_sha256,
            "founder_id": confirmation.founder_id,
            "second_appendix_sha256": confirmation.second_appendix_sha256,
            "study_id": confirmation.study_id,
        }
        decision_id = sha256(canonical_json(identity))
        ledger_body = canonical_json(ledger_rows)
        key = (
            f"citation-screening/{confirmation.study_id}/"
            f"pass-{confirmation.pass_number:04d}/decisions-{decision_id}.json"
        )
        ledger_object = self._store_object(key, ledger_body)
        included = sum(row["decision"] == "include" for row in ledger_rows)
        excluded = len(ledger_rows) - included
        return CitationDecisionLedgerReceipt(
            decision_id=decision_id,
            study_id=confirmation.study_id,
            pass_number=confirmation.pass_number,
            code_revision=code_revision,
            confirmed_at=confirmation.confirmed_at,
            founder_id=confirmation.founder_id,
            founder_name=confirmation.founder_name,
            first_packet_sha256=confirmation.first_packet_sha256,
            first_appendix_sha256=confirmation.first_appendix_sha256,
            second_packet_sha256=confirmation.second_packet_sha256,
            second_appendix_sha256=confirmation.second_appendix_sha256,
            candidate_count=len(ledger_rows),
            included_count=included,
            excluded_count=excluded,
            unclear_count=0,
            ledger_object=ledger_object,
            packet_checksums_verified=True,
            appendix_checksums_verified=True,
            record_coverage_verified=True,
            founder_authorized=True,
            founder_role_conflict_disclosed=True,
            ai_decisions_recorded=0,
            scientific_conclusions_drawn=False,
        )

    def confirm_single(
        self,
        packet: CitationFounderPacketReceipt,
        confirmation: CitationFounderConfirmation,
        *,
        packet_path: Path,
        appendix_path: Path,
        code_revision: str,
    ) -> CitationDecisionLedgerReceipt:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationConfirmationError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        if (
            (packet.study_id, packet.pass_number)
            != (confirmation.study_id, confirmation.pass_number)
            or confirmation.first_packet_sha256 != packet.packet_sha256
            or confirmation.first_appendix_sha256 != packet.appendix_sha256
            or confirmation.second_packet_sha256 is not None
            or confirmation.second_appendix_sha256 is not None
        ):
            raise CitationConfirmationError(
                "single-packet confirmation identity or checksums differ"
            )
        if packet.pending_adjudication_count:
            raise CitationConfirmationError(
                "single-packet confirmation cannot authorize pending adjudication"
            )
        self._verify_file(
            packet_path,
            packet.packet_sha256,
            confirmation.first_packet_sha256,
        )
        self._verify_file(
            appendix_path,
            packet.appendix_sha256,
            confirmation.first_appendix_sha256,
        )
        rows = self._read_appendix(
            appendix_path,
            allow_empty=packet.candidate_count == 0,
        )
        record_keys = [row["record_key"] for row in rows]
        if (
            len(rows) != packet.candidate_count
            or len(rows) != packet.proposed_decision_count
            or len(record_keys) != len(set(record_keys))
            or any(row["recommendation"] not in {"include", "exclude"} for row in rows)
            or any(row["founder_decision_recorded"] != "false" for row in rows)
        ):
            raise CitationConfirmationError(
                "single citation packet does not provide unique complete coverage"
            )
        ledger_rows = self._ledger_rows(rows, confirmation)
        identity = {
            "code_revision": code_revision,
            "confirmed_at": confirmation.confirmed_at.isoformat(),
            "first_appendix_sha256": confirmation.first_appendix_sha256,
            "founder_id": confirmation.founder_id,
            "second_appendix_sha256": None,
            "study_id": confirmation.study_id,
        }
        decision_id = sha256(canonical_json(identity))
        ledger_body = canonical_json(ledger_rows)
        key = (
            f"citation-screening/{confirmation.study_id}/"
            f"pass-{confirmation.pass_number:04d}/decisions-{decision_id}.json"
        )
        ledger_object = self._store_object(key, ledger_body)
        included = sum(row["decision"] == "include" for row in ledger_rows)
        return CitationDecisionLedgerReceipt(
            decision_id=decision_id,
            study_id=confirmation.study_id,
            pass_number=confirmation.pass_number,
            code_revision=code_revision,
            confirmed_at=confirmation.confirmed_at,
            founder_id=confirmation.founder_id,
            founder_name=confirmation.founder_name,
            first_packet_sha256=confirmation.first_packet_sha256,
            first_appendix_sha256=confirmation.first_appendix_sha256,
            candidate_count=len(ledger_rows),
            included_count=included,
            excluded_count=len(ledger_rows) - included,
            unclear_count=0,
            ledger_object=ledger_object,
            packet_checksums_verified=True,
            appendix_checksums_verified=True,
            record_coverage_verified=True,
            founder_authorized=True,
            founder_role_conflict_disclosed=True,
            ai_decisions_recorded=0,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _ledger_rows(
        rows: list[dict[str, str]],
        confirmation: CitationFounderConfirmation,
    ) -> list[dict[str, object]]:
        return [
            {
                "record_key": row["record_key"],
                "rank": int(row["rank"]),
                "title": row["title"],
                "pmid": row["pmid"] or None,
                "pmcid": row["pmcid"] or None,
                "doi": row["doi"] or None,
                "decision": row["recommendation"],
                "exclusion_reason": row["exclusion_reason"] or None,
                "reviewer_id": confirmation.founder_id,
                "reviewer_name": confirmation.founder_name,
                "reviewer_role": confirmation.reviewer_role,
                "decided_at": confirmation.confirmed_at.isoformat(),
                "founder_authorized": True,
                "ai_decision": False,
            }
            for row in sorted(rows, key=lambda item: int(item["rank"]))
        ]

    @staticmethod
    def _validate_identities(
        first: CitationFounderPacketReceipt,
        second: CitationFounderPacketReceipt,
        confirmation: CitationFounderConfirmation,
        code_revision: str,
    ) -> None:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationConfirmationError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        identities = {
            (first.study_id, first.pass_number),
            (second.study_id, second.pass_number),
            (confirmation.study_id, confirmation.pass_number),
        }
        if len(identities) != 1:
            raise CitationConfirmationError(
                "citation packet and confirmation identities differ"
            )
        expected = (
            first.packet_sha256,
            first.appendix_sha256,
            second.packet_sha256,
            second.appendix_sha256,
        )
        supplied = (
            confirmation.first_packet_sha256,
            confirmation.first_appendix_sha256,
            confirmation.second_packet_sha256,
            confirmation.second_appendix_sha256,
        )
        if supplied != expected:
            raise CitationConfirmationError(
                "citation confirmation is bound to different packet checksums"
            )
        if first.pending_adjudication_count != second.candidate_count:
            raise CitationConfirmationError(
                "second packet count does not match first-packet adjudication hold"
            )
        if second.pending_adjudication_count:
            raise CitationConfirmationError("second packet still contains pending records")

    @staticmethod
    def _verify_file(path: Path, *expected_hashes: str) -> None:
        if not path.is_file():
            raise CitationConfirmationError(f"citation confirmation file is missing: {path}")
        actual = sha256(path.read_bytes())
        if any(actual != expected for expected in expected_hashes):
            raise CitationConfirmationError(
                f"citation confirmation checksum failed: {path}"
            )

    @staticmethod
    def _read_appendix(
        path: Path,
        *,
        allow_empty: bool = False,
    ) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            rows = list(reader)
            fieldnames = set(reader.fieldnames or [])
        required = {
            "rank",
            "record_key",
            "pmid",
            "pmcid",
            "doi",
            "recommendation",
            "exclusion_reason",
            "title",
            "founder_decision_recorded",
        }
        if (
            fieldnames < required
            or (not rows and not allow_empty)
            or any(set(row) < required for row in rows)
        ):
            raise CitationConfirmationError("citation appendix columns are invalid")
        return rows

    def _store_object(self, key: str, body: bytes) -> StoredObject:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
        else:
            self._store.put_bytes(key, body, content_type=JSON_MEDIA_TYPE)
        stored = self._store.get_bytes(key)
        try:
            json.loads(stored)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CitationConfirmationError("stored citation decision ledger is invalid") from error
        if stored != body:
            raise CitationConfirmationError("stored citation decision ledger changed")
        return StoredObject(
            object_key=key,
            media_type=JSON_MEDIA_TYPE,
            size_bytes=len(body),
            sha256=sha256(body),
        )
