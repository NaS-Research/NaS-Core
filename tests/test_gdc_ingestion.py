import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.research import AnalysisPlan
from nas_core.domain.snapshots import DatasetSnapshot
from nas_core.ingestion.gdc import (
    GDC_API_ROOT,
    GDCSnapshotService,
    HTTPResponse,
    ProtocolNotLockedError,
    RemoteResponseError,
    build_case_query,
    canonical_json,
    sha256,
)
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
PLAN_PATH = ROOT / "workflows" / "tcga_brca_stage_survival" / "analysis_plan.yaml"
SCHEMA_PATH = ROOT / "workflows" / "dataset_snapshot.schema.json"
NOW = datetime(2026, 7, 20, 18, 0, tzinfo=UTC)


class FakeTransport:
    def __init__(self, pages: list[dict[str, object]]) -> None:
        self.pages = pages
        self.requests: list[tuple[str, dict[str, object] | None]] = []

    def get(self, url: str) -> HTTPResponse:
        self.requests.append((url, None))
        return HTTPResponse(
            status_code=200,
            headers={},
            body=canonical_json(
                {
                    "status": "OK",
                    "tag": "8.5.0",
                    "version": 1,
                    "commit": "a" * 40,
                }
            ),
        )

    def post_json(self, url: str, payload: dict[str, object]) -> HTTPResponse:
        self.requests.append((url, payload))
        page = self.pages.pop(0)
        return HTTPResponse(status_code=200, headers={}, body=canonical_json(page))


def _plan(*, approved: bool) -> AnalysisPlan:
    payload = yaml.safe_load(PLAN_PATH.read_text(encoding="utf-8"))
    if approved:
        payload["status"] = "preregistered"
        payload["reviews"][0] = {
            "reviewer": "Synthetic Reviewer",
            "role": "Independent scientific reviewer",
            "decision": "approved",
            "reviewed_at": "2026-07-20T17:00:00Z",
            "notes": "Synthetic approval used only by automated tests.",
        }
    return AnalysisPlan.model_validate(payload)


def _page(ids: list[str], *, total: int) -> dict[str, object]:
    return {
        "data": {
            "hits": [{"case_id": record_id} for record_id in ids],
            "pagination": {"count": len(ids), "total": total},
        },
        "warnings": {},
    }


def test_case_query_is_deterministic_and_project_scoped() -> None:
    query = build_case_query(_plan(approved=False), page_size=500)

    assert query["sort"] == "case_id:asc"
    assert query["from"] == 0
    assert query["size"] == 500
    assert query["filters"] == {
        "op": "in",
        "content": {"field": "project.project_id", "value": ["TCGA-BRCA"]},
    }
    assert "demographic.vital_status" in str(query["fields"])


def test_checked_in_snapshot_schema_matches_runtime_model() -> None:
    checked_in_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert checked_in_schema == DatasetSnapshot.model_json_schema()


def test_pending_plan_blocks_network_and_storage() -> None:
    transport = FakeTransport([])
    store = InMemoryObjectStore()

    with pytest.raises(ProtocolNotLockedError, match="preregistration is required"):
        GDCSnapshotService(store=store, transport=transport).capture_cases(
            _plan(approved=False), data_release="45.0"
        )

    assert transport.requests == []


def test_capture_paginates_and_writes_immutable_provenance() -> None:
    transport = FakeTransport([_page(["case-1", "case-2"], total=3), _page(["case-3"], total=3)])
    store = InMemoryObjectStore()
    service = GDCSnapshotService(
        store=store,
        transport=transport,
        clock=lambda: NOW,
        page_size=2,
    )

    snapshot = service.capture_cases(_plan(approved=True), data_release="45.0")

    assert snapshot.record_count == 3
    assert snapshot.release.data_release == "45.0"
    assert snapshot.release.api_tag == "8.5.0"
    assert snapshot.classification.value == "public_open"
    assert len(snapshot.requests) == 2
    assert snapshot.requests[1].body["from"] == 2
    assert transport.requests[0] == (f"{GDC_API_ROOT}/status", None)

    prefix = f"raw/gdc-tcga-open/NAS-BRCA-001/{snapshot.snapshot_id}"
    assert store.exists(f"{prefix}/pages/00001.json")
    assert store.exists(f"{prefix}/pages/00002.json")
    assert store.exists(f"{prefix}/gdc-status.json")
    assert store.exists(f"{prefix}/manifest.json")

    manifest = json.loads(store.get_bytes(f"{prefix}/manifest.json"))
    assert manifest["manifest_sha256"] == snapshot.manifest_sha256
    unhashed = deepcopy(manifest)
    unhashed.pop("manifest_sha256")
    assert snapshot.manifest_sha256 == sha256(canonical_json(unhashed))


def test_capture_rejects_duplicate_case_ids_across_pages() -> None:
    transport = FakeTransport([_page(["case-1"], total=2), _page(["case-1"], total=2)])

    with pytest.raises(RemoteResponseError, match="duplicate case IDs"):
        GDCSnapshotService(
            store=InMemoryObjectStore(),
            transport=transport,
            clock=lambda: NOW,
            page_size=1,
        ).capture_cases(_plan(approved=True), data_release="45.0")
