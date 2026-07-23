import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.discovery import load_phase_zero_artifacts
from nas_core.domain.literature import LiteratureSearchReceipt, LiteratureSearchSnapshot
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import HTTPResponse, canonical_json, sha256
from nas_core.retrieval.literature import (
    LiteratureSearchService,
    LiteratureSearchVerificationService,
    LiteratureVerificationError,
    UrllibLiteratureTransport,
    pubmed_summary_batches,
)
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows" / "studies" / "breast_clinical_molecular_discordance"
PLAN_PATH = STUDY / "question" / "phase_zero_plan.yaml"
SEARCH_PATH = STUDY / "literature" / "search_strategy.yaml"
FEASIBILITY_PATH = STUDY / "ingestion" / "data_feasibility.yaml"
SCHEMA_PATH = ROOT / "workflows" / "literature_search_snapshot.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "workflows" / "literature_search_receipt.schema.json"
REVISED_SEARCH_RECEIPT_PATH = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
    / "search_receipt_v0.3.1.yaml"
)
RECEIPT_PATH = STUDY / "literature" / "search_receipt.yaml"
NOW = datetime(2026, 7, 22, 19, 0, tzinfo=UTC)


class FakeLiteratureTransport:
    def __init__(self) -> None:
        self.requests: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, parameters: dict[str, str]) -> HTTPResponse:
        self.requests.append((url, parameters))
        if url.endswith("esearch.fcgi"):
            payload: object = {"esearchresult": {"count": "2", "idlist": ["1", "2"]}}
        elif url.endswith("esummary.fcgi"):
            payload = {
                "result": {
                    "uids": ["1", "2"],
                    "1": {
                        "title": "Stable PAM50 classification",
                        "authors": [{"name": "One A"}],
                        "fulljournalname": "Journal One",
                        "pubdate": "2024",
                        "articleids": [{"idtype": "doi", "value": "10.1/stable"}],
                    },
                    "2": {
                        "title": "Uncertain breast subtypes",
                        "authors": [{"name": "Two B"}],
                        "fulljournalname": "Journal Two",
                        "pubdate": "2023",
                        "articleids": [],
                    },
                }
            }
        elif url.endswith("efetch.fcgi"):
            articles = "".join(
                f"<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID><Article>"
                f"<Abstract><AbstractText Label='BACKGROUND'>Synthetic abstract {pmid}."
                "</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle>"
                for pmid in parameters["id"].split(",")
            )
            return HTTPResponse(
                status_code=200,
                headers={},
                body=f"<PubmedArticleSet>{articles}</PubmedArticleSet>".encode(),
            )
        else:
            payload = {
                "hitCount": 2,
                "nextCursorMark": "done",
                "resultList": {
                    "result": [
                        {
                            "source": "MED",
                            "id": "1",
                            "pmid": "1",
                            "doi": "10.1/stable",
                            "title": "Stable PAM50 classification",
                            "authorString": "One A",
                            "journalTitle": "Journal One",
                            "pubYear": "2024",
                            "abstractText": "Synthetic abstract for testing.",
                            "isOpenAccess": "N",
                        },
                        {
                            "source": "MED",
                            "id": "3",
                            "pmid": "3",
                            "title": "Classifier perturbation study",
                            "authorString": "Three C",
                            "journalTitle": "Journal Three",
                            "pubYear": "2022",
                            "isOpenAccess": "Y",
                        },
                    ]
                },
            }
        return HTTPResponse(status_code=200, headers={}, body=canonical_json(payload))


def _package():
    return load_phase_zero_artifacts(PLAN_PATH, SEARCH_PATH, FEASIBILITY_PATH)


def test_checked_in_literature_snapshot_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA_PATH.read_text()) == LiteratureSearchSnapshot.model_json_schema()
    assert (
        json.loads(RECEIPT_SCHEMA_PATH.read_text()) == LiteratureSearchReceipt.model_json_schema()
    )


def test_checked_in_revised_search_receipt_has_complete_priority_corpus() -> None:
    receipt = LiteratureSearchReceipt.model_validate(
        yaml.safe_load(REVISED_SEARCH_RECEIPT_PATH.read_text())
    )

    assert receipt.strategy_version == "0.2.4"
    assert receipt.unique_record_count == 100
    assert receipt.duplicate_record_count == 55
    assert receipt.record_count_invariants_verified is True
    assert receipt.scientific_conclusions_drawn is False
    assert receipt.outcome_data_accessed is False


def test_checked_in_search_receipt_is_typed_and_nonconclusive() -> None:
    receipt = LiteratureSearchReceipt.model_validate(yaml.safe_load(RECEIPT_PATH.read_text()))

    assert receipt.unique_record_count == 457
    assert receipt.duplicate_record_count == 57
    assert receipt.screening_status == "not_started"
    assert receipt.scientific_conclusions_drawn is False
    assert receipt.outcome_data_accessed is False


def test_capture_is_governed_deduplicated_and_immutable() -> None:
    plan, strategy, _ = _package()
    transport = FakeLiteratureTransport()
    store = InMemoryObjectStore()
    snapshot = LiteratureSearchService(
        store=store,
        registry=SourceRegistry.from_yaml(ROOT / "data" / "source-registry.yaml"),
        transport=transport,
        clock=lambda: NOW,
        page_size=500,
    ).capture(plan, strategy, contact_email="research@example.org")

    assert snapshot.unique_record_count == 3
    assert snapshot.duplicate_record_count == 1
    assert len(snapshot.source_results) == 2
    assert len(snapshot.requests) == 4
    assert all("email" not in request.parameters for request in snapshot.requests)
    assert all(request[1]["email"] == "research@example.org" for request in transport.requests)
    europe_request = next(request for request in transport.requests if "europepmc" in request[0])
    assert europe_request[1]["pageSize"] == "100"
    prefix = f"literature/NAS-BRCA-002/{snapshot.execution_id}"
    assert store.exists(f"{prefix}/manifest.json")
    assert store.exists(f"{prefix}/normalized-records.json")
    normalized = json.loads(store.get_bytes(f"{prefix}/normalized-records.json"))
    stable = next(record for record in normalized if record["pmid"] == "1")
    assert stable["source_ids"] == ["europe-pmc", "pubmed"]
    assert stable["abstract"] == "BACKGROUND: Synthetic abstract 1."
    assert stable["is_open_access"] is False

    manifest = json.loads(store.get_bytes(f"{prefix}/manifest.json"))
    unhashed = deepcopy(manifest)
    manifest_hash = unhashed.pop("manifest_sha256")
    assert manifest_hash == sha256(canonical_json(unhashed))


def test_stored_search_is_independently_verified_into_minimal_receipt() -> None:
    plan, strategy, _ = _package()
    store = InMemoryObjectStore()
    snapshot = LiteratureSearchService(
        store=store,
        registry=SourceRegistry.from_yaml(ROOT / "data" / "source-registry.yaml"),
        transport=FakeLiteratureTransport(),
        clock=lambda: NOW,
    ).capture(plan, strategy, contact_email="research@example.org")

    receipt = LiteratureSearchVerificationService(
        store=store,
        clock=lambda: NOW,
    ).verify(plan.study_id, snapshot.execution_id)

    assert receipt.execution_id == snapshot.execution_id
    assert receipt.unique_record_count == 3
    assert receipt.duplicate_record_count == 1
    assert receipt.verified_object_count == 6
    assert receipt.manifest_checksum_verified is True
    assert receipt.object_checksums_verified is True
    assert receipt.object_sizes_verified is True
    assert receipt.record_count_invariants_verified is True
    assert receipt.screening_status == "not_started"
    assert receipt.scientific_conclusions_drawn is False
    assert receipt.outcome_data_accessed is False


def test_search_verification_rejects_corrupt_normalized_records() -> None:
    plan, strategy, _ = _package()
    store = InMemoryObjectStore()
    snapshot = LiteratureSearchService(
        store=store,
        registry=SourceRegistry.from_yaml(ROOT / "data" / "source-registry.yaml"),
        transport=FakeLiteratureTransport(),
        clock=lambda: NOW,
    ).capture(plan, strategy, contact_email="research@example.org")
    store.put_bytes(
        snapshot.normalized_records_object.object_key,
        b"corrupt",
        content_type="application/json",
    )

    with pytest.raises(LiteratureVerificationError, match="checksum"):
        LiteratureSearchVerificationService(store=store).verify(
            plan.study_id,
            snapshot.execution_id,
        )


def test_count_preview_contacts_each_source_once_and_stores_nothing() -> None:
    plan, strategy, _ = _package()
    candidate = strategy.model_copy(
        update={"status": "draft", "retrieval_authorized": False}
    )
    transport = FakeLiteratureTransport()
    store = InMemoryObjectStore()
    counts = LiteratureSearchService(
        store=store,
        registry=SourceRegistry.from_yaml(ROOT / "data" / "source-registry.yaml"),
        transport=transport,
    ).preview_counts(plan, candidate, contact_email="research@example.org")

    assert counts == {"pubmed": 2, "europe-pmc": 2}
    assert len(transport.requests) == 2
    assert not store.exists("literature")


def test_count_preview_rejects_retrieval_authorized_strategy_before_network() -> None:
    plan, strategy, _ = _package()
    transport = FakeLiteratureTransport()

    with pytest.raises(PermissionError, match="non-retrieval candidate strategy"):
        LiteratureSearchService(
            store=InMemoryObjectStore(),
            registry=SourceRegistry.from_yaml(ROOT / "data" / "source-registry.yaml"),
            transport=transport,
        ).preview_counts(plan, strategy, contact_email="research@example.org")

    assert transport.requests == []


def test_capture_blocks_unlocked_search_before_network() -> None:
    plan, strategy, _ = _package()
    transport = FakeLiteratureTransport()
    unlocked = strategy.model_copy(update={"status": "draft", "retrieval_authorized": False})

    with pytest.raises(PermissionError, match="locked, retrieval-authorized"):
        LiteratureSearchService(
            store=InMemoryObjectStore(),
            registry=SourceRegistry.from_yaml(ROOT / "data" / "source-registry.yaml"),
            transport=transport,
        ).capture(plan, unlocked, contact_email="research@example.org")

    assert transport.requests == []


def test_capture_requires_contact_email_before_network() -> None:
    plan, strategy, _ = _package()
    transport = FakeLiteratureTransport()

    with pytest.raises(ValueError, match="valid contact email"):
        LiteratureSearchService(
            store=InMemoryObjectStore(),
            registry=SourceRegistry.from_yaml(ROOT / "data" / "source-registry.yaml"),
            transport=transport,
        ).capture(plan, strategy, contact_email="invalid")

    assert transport.requests == []


def test_default_transport_rejects_noncompliant_request_rate() -> None:
    with pytest.raises(ValueError, match="at least 0.34 seconds"):
        UrllibLiteratureTransport(minimum_request_interval_seconds=0.1)


def test_pubmed_summary_batches_prevent_oversized_get_requests() -> None:
    batches = pubmed_summary_batches([str(value) for value in range(250)])

    assert [len(batch) for batch in batches] == [100, 100, 50]
