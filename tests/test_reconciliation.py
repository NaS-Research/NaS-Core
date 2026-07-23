import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nas_core.domain.literature import (
    BibliographicRecord,
    InventoryReconciliationReceipt,
    LiteratureSearchReceipt,
    ScreeningQueueReceipt,
)
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.reconciliation import (
    InventoryReconciliationError,
    InventoryReconciliationService,
)
from nas_core.retrieval.screening import ScreeningQueueService
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "workflows" / "inventory_reconciliation_receipt.schema.json"
NOW = datetime(2026, 7, 23, 20, 0, tzinfo=UTC)


def _queue(
    store: InMemoryObjectStore,
    records: list[BibliographicRecord],
    *,
    execution: str,
    revision: str,
) -> ScreeningQueueReceipt:
    body = canonical_json(
        [record.model_dump(mode="json", exclude_none=True) for record in records]
    )
    key = f"literature/NAS-BRCA-002/{execution}/normalized-records.json"
    store.put_bytes(key, body, content_type="application/json")
    search = LiteratureSearchReceipt(
        execution_id=execution,
        study_id="NAS-BRCA-002",
        question_id="NAS-RQ-BRCA002",
        question_version="0.3.0",
        strategy_version="0.2.3",
        executed_at=NOW,
        source_results=[
            {
                "source_id": "pubmed",
                "reported_result_count": len(records),
                "retrieved_record_count": len(records),
                "request_count": 1,
                "raw_object_count": 1,
            },
            {
                "source_id": "europe-pmc",
                "reported_result_count": 0,
                "retrieved_record_count": 0,
                "request_count": 1,
                "raw_object_count": 1,
            },
        ],
        unique_record_count=len(records),
        duplicate_record_count=0,
        manifest_object_key=f"literature/NAS-BRCA-002/{execution}/manifest.json",
        manifest_sha256="a" * 64,
        normalized_records_object_key=key,
        normalized_records_sha256=sha256(body),
        normalized_records_size_bytes=len(body),
        verified_at=NOW,
        manifest_checksum_verified=True,
        object_checksums_verified=True,
        object_sizes_verified=True,
        record_count_invariants_verified=True,
        verified_object_count=3,
        screening_status="not_started",
        scientific_conclusions_drawn=False,
        outcome_data_accessed=False,
    )
    service = ScreeningQueueService(store=store, clock=lambda: NOW)
    manifest = service.build(search, code_revision=revision)
    return service.verify(
        manifest.study_id,
        manifest.search_execution_id,
        manifest.queue_id,
    )


def test_reconciliation_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA_PATH.read_text()) == (
        InventoryReconciliationReceipt.model_json_schema()
    )


def test_reconcile_classifies_exact_candidate_and_new_without_decisions() -> None:
    store = InMemoryObjectStore()
    prior = _queue(
        store,
        [
            BibliographicRecord(
                record_key="pmid:1",
                source_ids=["pubmed"],
                pmid="1",
                title="Exact prior study",
                authors=["Smith J"],
                publication_year=2024,
            ),
            BibliographicRecord(
                record_key="pmid:2",
                source_ids=["pubmed"],
                pmid="2",
                title="Different title",
                authors=["Jones A"],
                publication_year=2023,
            ),
        ],
        execution="1" * 64,
        revision="1234567",
    )
    current = _queue(
        store,
        [
            BibliographicRecord(
                record_key="pmid:1",
                source_ids=["pubmed"],
                pmid="1",
                title="Exact prior study",
                authors=["Smith J"],
                publication_year=2024,
            ),
            BibliographicRecord(
                record_key="pmid:3",
                source_ids=["pubmed"],
                pmid="3",
                title="New title by Jones",
                authors=["Jones B"],
                publication_year=2023,
            ),
            BibliographicRecord(
                record_key="pmid:4",
                source_ids=["pubmed"],
                pmid="4",
                title="Entirely new",
                authors=["Ng C"],
                publication_year=2025,
            ),
        ],
        execution="2" * 64,
        revision="1234567",
    )

    receipt = InventoryReconciliationService(
        store=store,
        clock=lambda: NOW,
    ).reconcile(current, prior, code_revision="abcdef0")

    assert receipt.current_record_count == 3
    assert receipt.prior_exact_match_count == 1
    assert receipt.author_year_candidate_count == 1
    assert receipt.new_candidate_count == 1
    assert receipt.prior_decisions_carried_forward is False
    rows = [
        json.loads(line)
        for line in store.get_bytes(receipt.artifact_object_key).splitlines()
    ]
    assert {row["status"] for row in rows} == {
        "prior_exact_match",
        "author_year_candidate",
        "new_candidate",
    }
    assert all(row["prior_decision_carried_forward"] is False for row in rows)


def test_reconciliation_rejects_unverified_queue_receipt() -> None:
    store = InMemoryObjectStore()
    prior = _queue(
        store,
        [
            BibliographicRecord(
                record_key="pmid:1",
                source_ids=["pubmed"],
                pmid="1",
                title="Prior",
            )
        ],
        execution="1" * 64,
        revision="1234567",
    )
    current = prior.model_copy(
        update={
            "queue_id": "f" * 64,
            "artifact_checksums_verified": False,
        }
    )

    with pytest.raises(InventoryReconciliationError, match="verified queue receipts"):
        InventoryReconciliationService(store=store).reconcile(
            current,
            prior,
            code_revision="abcdef0",
        )
