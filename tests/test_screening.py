import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.domain.literature import (
    BibliographicRecord,
    LiteratureSearchReceipt,
    ScreeningQueueManifest,
    ScreeningQueueReceipt,
    ScreeningQueueRecord,
)
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.screening import (
    ALGORITHM_VERSION,
    ScreeningQueueError,
    ScreeningQueueService,
)
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows" / "studies" / "breast_clinical_molecular_discordance"
SEARCH_RECEIPT = STUDY / "literature" / "search_receipt.yaml"
MANIFEST_SCHEMA = ROOT / "workflows" / "screening_queue_manifest.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows" / "screening_queue_receipt.schema.json"
QUEUE_RECEIPT = STUDY / "literature" / "screening_queue_receipt.yaml"
NOW = datetime(2026, 7, 22, 20, 0, tzinfo=UTC)


def _records() -> list[BibliographicRecord]:
    return [
        BibliographicRecord(
            record_key="pmid:1",
            source_ids=["pubmed"],
            pmid="1",
            doi="10.1/one",
            title="Synthetic classification study",
            authors=["Researcher A"],
            journal="Synthetic Journal",
            publication_year=2024,
            abstract="Synthetic abstract used only for testing.",
        ),
        BibliographicRecord(
            record_key="pmid:2",
            source_ids=["pubmed", "europe-pmc"],
            pmid="2",
            title="Synthetic study without abstract",
            publication_year=2023,
        ),
    ]


def _fixture() -> tuple[InMemoryObjectStore, LiteratureSearchReceipt]:
    records = _records()
    body = canonical_json([record.model_dump(mode="json", exclude_none=True) for record in records])
    key = "literature/NAS-BRCA-002/synthetic/normalized-records.json"
    store = InMemoryObjectStore()
    store.put_bytes(key, body, content_type="application/json")
    payload = yaml.safe_load(SEARCH_RECEIPT.read_text())
    payload.update(
        {
            "unique_record_count": len(records),
            "normalized_records_object_key": key,
            "normalized_records_sha256": sha256(body),
            "normalized_records_size_bytes": len(body),
        }
    )
    return store, LiteratureSearchReceipt.model_validate(payload)


def test_checked_in_screening_schemas_match_runtime_models() -> None:
    assert json.loads(MANIFEST_SCHEMA.read_text()) == ScreeningQueueManifest.model_json_schema()
    assert json.loads(RECEIPT_SCHEMA.read_text()) == ScreeningQueueReceipt.model_json_schema()


def test_checked_in_queue_receipt_is_pending_and_nonconclusive() -> None:
    receipt = ScreeningQueueReceipt.model_validate(yaml.safe_load(QUEUE_RECEIPT.read_text()))

    assert receipt.summary.input_record_count == 457
    assert receipt.summary.records_with_abstract == 457
    assert receipt.summary.records_without_abstract == 0
    assert receipt.summary.pending_record_count == 457
    assert receipt.screening_status == "not_started"
    assert receipt.scientific_conclusions_drawn is False


def test_build_creates_pending_human_queue_without_decisions() -> None:
    store, receipt = _fixture()
    manifest = ScreeningQueueService(store=store, clock=lambda: NOW).build(
        receipt,
        code_revision="d459191",
    )

    assert manifest.algorithm_version == ALGORITHM_VERSION
    assert manifest.summary.input_record_count == 2
    assert manifest.summary.pending_record_count == 2
    assert manifest.summary.records_with_abstract == 1
    assert manifest.summary.records_without_abstract == 1
    assert manifest.human_decisions_recorded == 0
    assert manifest.ai_decisions_recorded == 0
    queue_object = next(
        artifact for artifact in manifest.artifacts if artifact.object_key.endswith(".jsonl")
    )
    rows = [json.loads(line) for line in store.get_bytes(queue_object.object_key).splitlines()]
    assert len(rows) == 2
    assert {row["decision"] for row in rows} == {"pending"}
    assert all("reviewer" not in row for row in rows)


def test_verify_reloads_queue_and_recomputes_invariants() -> None:
    store, receipt = _fixture()
    service = ScreeningQueueService(store=store, clock=lambda: NOW)
    manifest = service.build(receipt, code_revision="d459191")

    verified = service.verify(
        manifest.study_id,
        manifest.search_execution_id,
        manifest.queue_id,
    )

    assert verified.queue_id == manifest.queue_id
    assert verified.summary.input_record_count == 2
    assert verified.summary.pending_record_count == 2
    assert verified.manifest_checksum_verified is True
    assert verified.artifact_checksums_verified is True
    assert verified.record_count_verified is True
    assert verified.scientific_conclusions_drawn is False


def test_verify_rejects_corrupted_queue_artifact() -> None:
    store, receipt = _fixture()
    service = ScreeningQueueService(store=store, clock=lambda: NOW)
    manifest = service.build(receipt, code_revision="d459191")
    queue_object = next(
        artifact for artifact in manifest.artifacts if artifact.object_key.endswith(".jsonl")
    )
    store.put_bytes(queue_object.object_key, b"corrupted", content_type="application/x-ndjson")

    with pytest.raises(ScreeningQueueError, match="artifact verification failed"):
        service.verify(
            manifest.study_id,
            manifest.search_execution_id,
            manifest.queue_id,
        )


def test_build_rejects_tampered_normalized_records() -> None:
    store, receipt = _fixture()
    receipt = receipt.model_copy(
        update={"normalized_records_size_bytes": receipt.normalized_records_size_bytes + 1}
    )

    with pytest.raises(ScreeningQueueError, match="size does not match"):
        ScreeningQueueService(store=store).build(receipt, code_revision="d459191")


def test_exclusion_requires_human_provenance_and_reason() -> None:
    with pytest.raises(ValidationError, match="requires reviewer and timestamp"):
        ScreeningQueueRecord(
            screening_id="a" * 64,
            record_key="pmid:1",
            source_ids=["pubmed"],
            title="Synthetic",
            decision="exclude",
            exclusion_reason="Wrong population",
        )
