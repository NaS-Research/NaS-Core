from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

import pytest
import yaml

from nas_core.domain.public_artifact import (
    PublicArtifactAcquisitionPlan,
    PublicArtifactAcquisitionReceipt,
    load_public_artifact_plan,
)
from nas_core.domain.reference_development import load_reference_development_protocol
from nas_core.domain.storage_readiness import load_storage_readiness_receipt
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import sha256
from nas_core.ingestion.public_artifact import (
    DownloadResult,
    PublicArtifactAcquisitionError,
    PublicArtifactAcquisitionService,
)
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import FileSystemObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "ingestion/gse81538_acquisition_plan_v1.0.0.yaml"
REGISTRY = ROOT / "data/source-registry.yaml"
AUTHORIZATION = STUDY / "reviews/FOUNDER_STANDING_AUTONOMY_AUTHORIZATION_v1.0.0.yaml"
REFERENCE = STUDY / "protocol/reference_development_protocol_v1.0.0.yaml"
READINESS = STUDY / "ingestion/storage_readiness_receipt_v1.1.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/public_artifact_acquisition_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/public_artifact_acquisition_receipt.schema.json"
PAYLOAD = b"synthetic-gzip-fixture"
NOW = datetime(2026, 8, 1, 16, 0, tzinfo=UTC)


class FakeStreamingTransport:
    def __init__(self, payload: bytes = PAYLOAD) -> None:
        self.payload = payload
        self.calls: list[str] = []

    def download(self, url: str, destination: BinaryIO) -> DownloadResult:
        self.calls.append(url)
        destination.write(self.payload)
        return DownloadResult(
            status_code=200,
            headers={
                "Content-Type": "application/x-gzip",
                "Content-Length": str(len(self.payload)),
                "Last-Modified": "Tue, 17 May 2016 20:45:49 GMT",
            },
            content_length_bytes=len(self.payload),
            sha256=hashlib.sha256(self.payload).hexdigest(),
        )


def _fixture_plan(readiness_path: Path) -> PublicArtifactAcquisitionPlan:
    plan = load_public_artifact_plan(PLAN)
    return plan.model_copy(
        update={
            "expected_content_length_bytes": len(PAYLOAD),
            "storage_readiness_receipt_sha256": sha256(readiness_path.read_bytes()),
        }
    )


def _service(
    tmp_path: Path,
    transport: FakeStreamingTransport,
) -> tuple[
    PublicArtifactAcquisitionService,
    FileSystemObjectStore,
    Path,
]:
    data_root = tmp_path / "nas-data"
    DataLayout(data_root).initialize()
    readiness = load_storage_readiness_receipt(READINESS).model_copy(
        update={"data_root": str(data_root.resolve())}
    )
    readiness_path = tmp_path / "readiness.yaml"
    readiness_path.write_text(
        yaml.safe_dump(readiness.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    store = FileSystemObjectStore(data_root)
    return (
        PublicArtifactAcquisitionService(
            store=store,
            data_root=data_root,
            transport=transport,
            clock=lambda: NOW,
        ),
        store,
        readiness_path,
    )


def _acquire(
    service: PublicArtifactAcquisitionService,
    plan: PublicArtifactAcquisitionPlan,
    readiness_path: Path,
) -> PublicArtifactAcquisitionReceipt:
    return service.acquire(
        plan,
        SourceRegistry.from_yaml(REGISTRY),
        load_reference_development_protocol(REFERENCE),
        load_storage_readiness_receipt(readiness_path),
        plan_path=PLAN,
        registry_path=REGISTRY,
        authorization_path=AUTHORIZATION,
        reference_protocol_path=REFERENCE,
        storage_readiness_path=readiness_path,
        code_revision="a881b71",
    )


def test_public_artifact_acquisition_streams_and_freezes_checksum(tmp_path: Path) -> None:
    transport = FakeStreamingTransport()
    service, store, readiness_path = _service(tmp_path, transport)
    plan = _fixture_plan(readiness_path)

    receipt = _acquire(service, plan, readiness_path)

    assert transport.calls == [plan.official_url]
    assert store.get_bytes(plan.object_key) == PAYLOAD
    assert receipt.sha256 == hashlib.sha256(PAYLOAD).hexdigest()
    assert receipt.content_length_bytes == len(PAYLOAD)
    assert receipt.molecular_source_bytes_stored is True
    assert receipt.molecular_values_parsed is False
    assert receipt.outcome_values_accessed is False


def test_public_artifact_acquisition_rejects_changed_size(tmp_path: Path) -> None:
    transport = FakeStreamingTransport(b"wrong-size")
    service, store, readiness_path = _service(tmp_path, transport)
    plan = _fixture_plan(readiness_path)

    with pytest.raises(PublicArtifactAcquisitionError, match="content length changed"):
        _acquire(service, plan, readiness_path)

    assert not store.exists(plan.object_key)


def test_public_artifact_acquisition_never_overwrites(tmp_path: Path) -> None:
    transport = FakeStreamingTransport()
    service, _, readiness_path = _service(tmp_path, transport)
    plan = _fixture_plan(readiness_path)
    _acquire(service, plan, readiness_path)

    with pytest.raises(PublicArtifactAcquisitionError, match="already exists"):
        _acquire(service, plan, readiness_path)


def test_public_artifact_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")) == (
        PublicArtifactAcquisitionPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8")) == (
        PublicArtifactAcquisitionReceipt.model_json_schema()
    )
