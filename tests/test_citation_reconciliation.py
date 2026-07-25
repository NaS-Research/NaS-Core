from datetime import UTC, datetime

import pytest

from nas_core.domain.appraisal import (
    FullTextAppraisal,
    FullTextInventory,
    FullTextInventoryRecord,
)
from nas_core.domain.citation_confirmation import CitationDecisionLedgerReceipt
from nas_core.domain.citation_reconciliation import CitationInclusionDisposition
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.citation_reconciliation import (
    CitationInclusionReconciliationService,
    CitationReconciliationError,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 16, 0, tzinfo=UTC)


def _inventory() -> FullTextInventory:
    return FullTextInventory(
        inventory_version="1.0.0",
        study_id="NAS-BRCA-002",
        queue_id="a" * 64,
        progress_id="b" * 64,
        provisional_inclusion_count=1,
        repository_candidate_count=1,
        access_check_required_count=0,
        records=[
            FullTextInventoryRecord(
                screening_id="c" * 64,
                record_key="MED:1",
                title="Active study",
                pmid="1",
                access_status="repository_candidate",
            )
        ],
    )


def _appraisal() -> FullTextAppraisal:
    return FullTextAppraisal.model_validate(
        {
            "schema_version": "1.0.0",
            "appraisal_version": "1.0.0",
            "study_id": "NAS-BRCA-002",
            "screening_id": "d" * 64,
            "title": "Prior study",
            "pmid": "2",
            "doi": "10.1/prior",
            "full_text_source_url": "https://example.test/prior",
            "full_text_sha256": "e" * 64,
            "access_basis": "Test fixture",
            "study_design": "other",
            "eligibility": "eligible",
            "domains": [
                {
                    "domain": name,
                    "judgment": "some_concerns",
                    "rationale": "Test rationale",
                    "evidence_locations": ["Test section"],
                }
                for name in (
                    "population_selection",
                    "specimen_and_measurement",
                    "classifier_implementation",
                    "reference_comparator",
                    "analysis_and_statistics",
                    "validation_and_transportability",
                    "reporting_and_reproducibility",
                )
            ],
            "evidence_role": "context_only",
            "key_strengths": [],
            "key_limitations": [],
            "conflicts_and_funding": "Not assessed in fixture",
            "reviewer_id": "test-reviewer",
            "reviewer_name": "Test Reviewer",
            "review_method": "founder_only",
            "founder_authorized": True,
            "assessed_at": NOW,
        }
    )


def _decision(store: InMemoryObjectStore) -> CitationDecisionLedgerReceipt:
    rows = [
        {
            "record_key": "MED:1",
            "title": "Active study",
            "pmid": "1",
            "pmcid": None,
            "doi": None,
            "decision": "include",
        },
        {
            "record_key": "MED:2",
            "title": "Prior study",
            "pmid": "2",
            "pmcid": None,
            "doi": "https://doi.org/10.1/PRIOR",
            "decision": "include",
        },
        {
            "record_key": "MED:3",
            "title": "New study",
            "pmid": "3",
            "pmcid": None,
            "doi": None,
            "decision": "include",
        },
        {
            "record_key": "MED:4",
            "title": "Excluded study",
            "pmid": "4",
            "pmcid": None,
            "doi": None,
            "decision": "exclude",
        },
    ]
    body = canonical_json(rows)
    key = "citation-screening/NAS-BRCA-002/pass-0001/decisions-test.json"
    store.put_bytes(key, body, content_type="application/json")
    return CitationDecisionLedgerReceipt(
        decision_id="f" * 64,
        study_id="NAS-BRCA-002",
        pass_number=1,
        code_revision="abcdef0",
        confirmed_at=NOW,
        founder_id="test-founder",
        founder_name="Test Founder",
        first_packet_sha256="1" * 64,
        first_appendix_sha256="2" * 64,
        second_packet_sha256="3" * 64,
        second_appendix_sha256="4" * 64,
        candidate_count=4,
        included_count=3,
        excluded_count=1,
        unclear_count=0,
        ledger_object=StoredObject(
            object_key=key,
            media_type="application/json",
            size_bytes=len(body),
            sha256=sha256(body),
        ),
        packet_checksums_verified=True,
        appendix_checksums_verified=True,
        record_coverage_verified=True,
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )


def test_reconciliation_routes_every_confirmed_inclusion_without_changing_it() -> None:
    store = InMemoryObjectStore()
    receipt = CitationInclusionReconciliationService(store=store).reconcile(
        _decision(store),
        _inventory(),
        [_appraisal()],
        code_revision="abcdef0",
        reconciled_at=NOW,
    )

    assert receipt.confirmed_inclusion_count == 3
    assert receipt.active_inventory_match_count == 1
    assert receipt.prior_appraisal_match_count == 1
    assert receipt.net_new_count == 1
    assert receipt.founder_decisions_changed == 0
    rows = __import__("json").loads(
        store.get_bytes(receipt.reconciliation_object.object_key)
    )
    assert {row["disposition"] for row in rows} == {
        disposition.value for disposition in CitationInclusionDisposition
    }


def test_reconciliation_rejects_tampered_decision_ledger() -> None:
    store = InMemoryObjectStore()
    decision = _decision(store)
    store._objects[decision.ledger_object.object_key] = b"[]"  # noqa: SLF001

    with pytest.raises(CitationReconciliationError, match="checksum failed"):
        CitationInclusionReconciliationService(store=store).reconcile(
            decision,
            _inventory(),
            [_appraisal()],
            code_revision="abcdef0",
            reconciled_at=NOW,
        )
