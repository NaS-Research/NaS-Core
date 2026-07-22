import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from nas_core.domain.literature import (
    BibliographicRecord,
    LiteratureSearchReceipt,
    ScreeningDecisionBatch,
    ScreeningProgressManifest,
    ScreeningProgressReceipt,
    ScreeningQueueReceipt,
)
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.review import (
    ALGORITHM_VERSION,
    ScreeningReviewError,
    ScreeningReviewService,
)
from nas_core.retrieval.screening import ScreeningQueueService
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows" / "studies" / "breast_clinical_molecular_discordance"
SEARCH_RECEIPT = STUDY / "literature" / "search_receipt.yaml"
DECISION_SCHEMA = ROOT / "workflows" / "screening_decision_batch.schema.json"
PROGRESS_MANIFEST_SCHEMA = ROOT / "workflows" / "screening_progress_manifest.schema.json"
PROGRESS_RECEIPT_SCHEMA = ROOT / "workflows" / "screening_progress_receipt.schema.json"
FIRST_PROGRESS_RECEIPT = STUDY / "literature" / "screening-progress" / "batch-0001.yaml"
SECOND_PROGRESS_RECEIPT = STUDY / "literature" / "screening-progress" / "batch-0002.yaml"
NOW = datetime(2026, 7, 22, 21, 0, tzinfo=UTC)


def _fixture() -> tuple[InMemoryObjectStore, ScreeningQueueReceipt, list[str]]:
    records = [
        BibliographicRecord(
            record_key=f"pmid:{index}",
            source_ids=["pubmed"],
            pmid=str(index),
            title=f"Synthetic screening record {index}",
            abstract=f"Synthetic abstract {index} used only in tests.",
            publication_year=2024,
        )
        for index in range(1, 5)
    ]
    normalized = canonical_json(
        [record.model_dump(mode="json", exclude_none=True) for record in records]
    )
    normalized_key = "literature/NAS-BRCA-002/synthetic-review/normalized-records.json"
    store = InMemoryObjectStore()
    store.put_bytes(normalized_key, normalized, content_type="application/json")
    search_payload = yaml.safe_load(SEARCH_RECEIPT.read_text())
    search_payload.update(
        {
            "unique_record_count": len(records),
            "normalized_records_object_key": normalized_key,
            "normalized_records_sha256": sha256(normalized),
            "normalized_records_size_bytes": len(normalized),
        }
    )
    search_receipt = LiteratureSearchReceipt.model_validate(search_payload)
    queue_manifest = ScreeningQueueService(store=store, clock=lambda: NOW).build(
        search_receipt,
        code_revision="3f10788",
    )
    queue_object = next(
        item for item in queue_manifest.artifacts if item.object_key.endswith(".jsonl")
    )
    queue_receipt = ScreeningQueueReceipt(
        queue_id=queue_manifest.queue_id,
        study_id=queue_manifest.study_id,
        search_execution_id=queue_manifest.search_execution_id,
        algorithm_version=queue_manifest.algorithm_version,
        code_revision=queue_manifest.code_revision,
        created_at=queue_manifest.created_at,
        manifest_object_key=(
            f"literature-screening/{queue_manifest.study_id}/"
            f"{queue_manifest.search_execution_id}/{queue_manifest.queue_id}/manifest.json"
        ),
        manifest_sha256=queue_manifest.manifest_sha256 or "",
        queue_object_key=queue_object.object_key,
        queue_sha256=queue_object.sha256,
        queue_size_bytes=queue_object.size_bytes,
        summary=queue_manifest.summary,
        verified_at=NOW,
        manifest_checksum_verified=True,
        artifact_checksums_verified=True,
        record_count_verified=True,
        screening_status="not_started",
        scientific_conclusions_drawn=False,
    )
    queue_rows = [
        json.loads(line) for line in store.get_bytes(queue_object.object_key).splitlines()
    ]
    return store, queue_receipt, [row["screening_id"] for row in queue_rows]


def _batch(
    queue_id: str,
    decisions: list[dict[str, object]],
    *,
    previous: str | None = None,
) -> ScreeningDecisionBatch:
    return ScreeningDecisionBatch(
        queue_id=queue_id,
        expected_previous_progress_id=previous,
        reviewer_id="dalron-j-robertson",
        reviewer_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        decisions=decisions,
    )


def test_checked_in_review_schemas_match_runtime_models() -> None:
    assert json.loads(DECISION_SCHEMA.read_text()) == ScreeningDecisionBatch.model_json_schema()
    assert (
        json.loads(PROGRESS_MANIFEST_SCHEMA.read_text())
        == ScreeningProgressManifest.model_json_schema()
    )


def test_first_checked_in_progress_receipt_records_only_founder_inclusions() -> None:
    receipt = ScreeningProgressReceipt.model_validate(
        yaml.safe_load(FIRST_PROGRESS_RECEIPT.read_text())
    )

    assert receipt.summary.total_record_count == 457
    assert receipt.summary.decided_record_count == 5
    assert receipt.summary.included_record_count == 5
    assert receipt.summary.pending_record_count == 452
    assert receipt.summary.excluded_record_count == 0
    assert receipt.summary.unclear_record_count == 0
    assert receipt.ai_decisions_recorded == 0
    assert receipt.scientific_conclusions_drawn is False
    assert (
        json.loads(PROGRESS_RECEIPT_SCHEMA.read_text())
        == ScreeningProgressReceipt.model_json_schema()
    )


def test_second_checked_in_progress_receipt_records_approved_founder_batch() -> None:
    receipt = ScreeningProgressReceipt.model_validate(
        yaml.safe_load(SECOND_PROGRESS_RECEIPT.read_text())
    )

    assert receipt.previous_progress_id == (
        "1529a64b2b7ce3e623215863824a4a0a7a5e2838a9988995366b4332f22683f1"
    )
    assert receipt.summary.total_record_count == 457
    assert receipt.summary.decided_record_count == 15
    assert receipt.summary.included_record_count == 12
    assert receipt.summary.excluded_record_count == 3
    assert receipt.summary.pending_record_count == 442
    assert receipt.summary.unclear_record_count == 0
    assert receipt.ai_decisions_recorded == 0
    assert receipt.scientific_conclusions_drawn is False


def test_records_verifies_and_resumes_founder_review() -> None:
    store, queue_receipt, identifiers = _fixture()
    service = ScreeningReviewService(store=store, clock=lambda: NOW + timedelta(minutes=1))
    initial = service.next_batch(queue_receipt, batch_size=2)

    assert initial.available_record_count == 4
    assert [record.screening_id for record in initial.records] == identifiers[:2]

    manifest = service.record_batch(
        queue_receipt,
        _batch(
            queue_receipt.queue_id,
            [
                {"screening_id": identifiers[0], "decision": "include"},
                {
                    "screening_id": identifiers[1],
                    "decision": "exclude",
                    "exclusion_reason": "outside_breast_cancer_scope",
                },
            ],
        ),
        code_revision="982321f",
    )
    receipt = service.verify(queue_receipt, manifest)

    assert manifest.algorithm_version == ALGORITHM_VERSION
    assert receipt.summary.decided_record_count == 2
    assert receipt.summary.pending_record_count == 2
    assert receipt.summary.included_record_count == 1
    assert receipt.summary.excluded_record_count == 1
    assert receipt.summary.decision_event_count == 2
    assert receipt.screening_status == "in_progress"
    assert receipt.ai_decisions_recorded == 0
    assert receipt.scientific_conclusions_drawn is False
    resumed = service.next_batch(queue_receipt, progress_receipt=receipt, batch_size=10)
    assert [record.screening_id for record in resumed.records] == identifiers[2:]


def test_rejects_stale_progress_and_duplicate_decision() -> None:
    store, queue_receipt, identifiers = _fixture()
    service = ScreeningReviewService(store=store, clock=lambda: NOW)
    first = service.record_batch(
        queue_receipt,
        _batch(queue_receipt.queue_id, [{"screening_id": identifiers[0], "decision": "include"}]),
        code_revision="982321f",
    )
    receipt = service.verify(queue_receipt, first)

    with pytest.raises(ScreeningReviewError, match="different progress state"):
        service.record_batch(
            queue_receipt,
            _batch(
                queue_receipt.queue_id, [{"screening_id": identifiers[1], "decision": "include"}]
            ),
            code_revision="982321f",
            progress_receipt=receipt,
        )

    with pytest.raises(ScreeningReviewError, match="requires its current event ID"):
        service.record_batch(
            queue_receipt,
            _batch(
                queue_receipt.queue_id,
                [
                    {
                        "screening_id": identifiers[0],
                        "decision": "exclude",
                        "exclusion_reason": "outside_breast_cancer_scope",
                    }
                ],
                previous=receipt.progress_id,
            ),
            code_revision="982321f",
            progress_receipt=receipt,
        )


def test_unclear_decision_can_be_adjudicated_with_explicit_supersession() -> None:
    store, queue_receipt, identifiers = _fixture()
    first_service = ScreeningReviewService(store=store, clock=lambda: NOW)
    first = first_service.record_batch(
        queue_receipt,
        _batch(queue_receipt.queue_id, [{"screening_id": identifiers[0], "decision": "unclear"}]),
        code_revision="982321f",
    )
    first_receipt = first_service.verify(queue_receipt, first)
    event = json.loads(store.get_bytes(first_receipt.decisions_object_key).splitlines()[0])

    second_service = ScreeningReviewService(
        store=store,
        clock=lambda: NOW + timedelta(minutes=5),
    )
    second = second_service.record_batch(
        queue_receipt,
        _batch(
            queue_receipt.queue_id,
            [
                {
                    "screening_id": identifiers[0],
                    "decision": "include",
                    "supersedes_event_id": event["event_id"],
                    "change_reason": "Assay method clarified during founder adjudication.",
                }
            ],
            previous=first_receipt.progress_id,
        ),
        code_revision="982321f",
        progress_receipt=first_receipt,
    )
    second_receipt = second_service.verify(queue_receipt, second)

    assert second_receipt.summary.decided_record_count == 1
    assert second_receipt.summary.included_record_count == 1
    assert second_receipt.summary.unclear_record_count == 0
    assert second_receipt.summary.decision_event_count == 2


def test_rejects_tampered_decision_ledger() -> None:
    store, queue_receipt, identifiers = _fixture()
    service = ScreeningReviewService(store=store, clock=lambda: NOW)
    manifest = service.record_batch(
        queue_receipt,
        _batch(queue_receipt.queue_id, [{"screening_id": identifiers[0], "decision": "include"}]),
        code_revision="982321f",
    )
    decisions = next(item for item in manifest.artifacts if item.object_key.endswith(".jsonl"))
    store.put_bytes(decisions.object_key, b"tampered\n", content_type="application/x-ndjson")

    with pytest.raises(ScreeningReviewError, match="failed verification"):
        service.verify(queue_receipt, manifest)
