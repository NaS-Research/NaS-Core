import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nas_core.domain.discovery import load_phase_zero_artifacts
from nas_core.domain.literature import LiteratureSearchSnapshot
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import HTTPResponse, canonical_json, sha256
from nas_core.retrieval.literature import LiteratureSearchService, UrllibLiteratureTransport
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows" / "studies" / "breast_clinical_molecular_discordance"
PLAN_PATH = STUDY / "question" / "phase_zero_plan.yaml"
SEARCH_PATH = STUDY / "literature" / "search_strategy.yaml"
FEASIBILITY_PATH = STUDY / "ingestion" / "data_feasibility.yaml"
SCHEMA_PATH = ROOT / "workflows" / "literature_search_snapshot.schema.json"
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


def test_capture_is_governed_deduplicated_and_immutable() -> None:
    plan, strategy, _ = _package()
    transport = FakeLiteratureTransport()
    store = InMemoryObjectStore()
    snapshot = LiteratureSearchService(
        store=store,
        registry=SourceRegistry.from_yaml(ROOT / "data" / "source-registry.yaml"),
        transport=transport,
        clock=lambda: NOW,
        page_size=100,
    ).capture(plan, strategy, contact_email="research@example.org")

    assert snapshot.unique_record_count == 3
    assert snapshot.duplicate_record_count == 1
    assert len(snapshot.source_results) == 2
    assert len(snapshot.requests) == 3
    assert all("email" not in request.parameters for request in snapshot.requests)
    assert all(request[1]["email"] == "research@example.org" for request in transport.requests)
    prefix = f"literature/NAS-BRCA-002/{snapshot.execution_id}"
    assert store.exists(f"{prefix}/manifest.json")
    assert store.exists(f"{prefix}/normalized-records.json")
    normalized = json.loads(store.get_bytes(f"{prefix}/normalized-records.json"))
    stable = next(record for record in normalized if record["pmid"] == "1")
    assert stable["source_ids"] == ["europe-pmc", "pubmed"]
    assert stable["abstract"] == "Synthetic abstract for testing."
    assert stable["is_open_access"] is False

    manifest = json.loads(store.get_bytes(f"{prefix}/manifest.json"))
    unhashed = deepcopy(manifest)
    manifest_hash = unhashed.pop("manifest_sha256")
    assert manifest_hash == sha256(canonical_json(unhashed))


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
