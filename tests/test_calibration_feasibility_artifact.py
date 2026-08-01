from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import BinaryIO

import pytest
import yaml

from nas_core.domain.calibration_feasibility_artifact import (
    CalibrationFeasibilityAcquisitionPlan,
    CalibrationFeasibilityAcquisitionReceipt,
    CalibrationFeasibilityArtifact,
    CalibrationFeasibilityArtifactKind,
)
from nas_core.domain.storage_readiness import load_storage_readiness_receipt
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.calibration_feasibility_artifact import (
    CalibrationFeasibilityAcquisitionError,
    CalibrationFeasibilityAcquisitionService,
)
from nas_core.ingestion.gdc import sha256
from nas_core.ingestion.public_artifact import DownloadResult
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import FileSystemObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
REGISTRY = STUDY / "ingestion/calibration_feasibility_source_registry_v1.0.0.yaml"
AUTHORIZATION = STUDY / "reviews/FOUNDER_STANDING_AUTONOMY_AUTHORIZATION_v1.0.0.yaml"
CALIBRATION_READINESS = STUDY / "protocol/technical_calibration_readiness_receipt_v1.0.0.yaml"
STORAGE_READINESS = STUDY / "ingestion/storage_readiness_receipt_v1.1.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/calibration_feasibility_acquisition_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/calibration_feasibility_acquisition_receipt.schema.json"


class FakeTransport:
    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads

    def download(self, url: str, destination: BinaryIO) -> DownloadResult:
        payload = self.payloads[url]
        destination.write(payload)
        return DownloadResult(
            status_code=200,
            headers={"Content-Type": "application/octet-stream"},
            content_length_bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
        )


def _artifact(
    source: str,
    accession: str,
    file_accession: str,
    payload: bytes,
) -> CalibrationFeasibilityArtifact:
    filename = f"{file_accession}_expression.txt.gz"
    return CalibrationFeasibilityArtifact(
        source_id=source,
        source_accession=accession,
        file_accession=file_accession,
        artifact_kind=CalibrationFeasibilityArtifactKind.PROCESSED_EXPRESSION,
        filename=filename,
        official_url=(
            "https://www.ncbi.nlm.nih.gov/geo/download/"
            f"?acc={file_accession}&format=file&file={filename}"
        ),
        expected_content_length_bytes=len(payload),
        expected_content_type="application/octet-stream",
        object_key=f"raw/nas-brca-002/{source}/{filename.lower()}",
    )


def _setup(
    tmp_path: Path,
) -> tuple[
    CalibrationFeasibilityAcquisitionPlan,
    Path,
    Path,
    dict[str, bytes],
]:
    payloads = {"GSE60788": b"pilot", "GSM3737461": b"ffpe"}
    artifacts = [
        _artifact("ncbi-geo-gse60788", "GSE60788", "GSE60788", payloads["GSE60788"]),
        _artifact("ncbi-geo-gse130397", "GSE130397", "GSM3737461", payloads["GSM3737461"]),
    ]
    data_root = tmp_path / "data"
    DataLayout(data_root).initialize()
    readiness = load_storage_readiness_receipt(STORAGE_READINESS).model_copy(
        update={"data_root": str(data_root.resolve())}
    )
    readiness_path = tmp_path / "storage-readiness.yaml"
    readiness_path.write_text(
        yaml.safe_dump(readiness.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    plan = CalibrationFeasibilityAcquisitionPlan(
        plan_version="1.0.0",
        study_id="NAS-BRCA-002",
        question_id="NAS-RQ-BRCA002",
        question_version="0.3.0",
        intended_role="excluded_public_calibration_feasibility_only",
        source_registry_sha256=sha256(REGISTRY.read_bytes()),
        standing_authorization_sha256=sha256(AUTHORIZATION.read_bytes()),
        calibration_readiness_receipt_sha256=sha256(CALIBRATION_READINESS.read_bytes()),
        storage_readiness_receipt_sha256=sha256(readiness_path.read_bytes()),
        artifacts=artifacts,
        parse_during_acquisition=False,
        outcome_fields_requested=False,
        pooling_authorized=False,
        threshold_estimation_authorized=False,
        classifier_execution_authorized=False,
        immutable_write_required=True,
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(plan.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    transport_payloads = {
        artifact.official_url: payloads[artifact.file_accession]
        for artifact in artifacts
    }
    return plan, plan_path, readiness_path, transport_payloads


def test_acquisition_stages_and_freezes_all_artifacts(tmp_path: Path) -> None:
    plan, plan_path, readiness_path, payloads = _setup(tmp_path)
    data_root = Path(load_storage_readiness_receipt(readiness_path).data_root)
    store = FileSystemObjectStore(data_root)
    receipt = CalibrationFeasibilityAcquisitionService(
        store=store,
        data_root=data_root,
        transport=FakeTransport(payloads),
        request_interval_seconds=0,
        sleeper=lambda _: None,
    ).acquire(
        plan,
        SourceRegistry.from_yaml(REGISTRY),
        load_storage_readiness_receipt(readiness_path),
        plan_path=plan_path,
        registry_path=REGISTRY,
        authorization_path=AUTHORIZATION,
        calibration_readiness_path=CALIBRATION_READINESS,
        storage_readiness_path=readiness_path,
        code_revision="1234567",
    )

    assert len(receipt.artifacts) == 2
    assert receipt.all_immutable_objects_verified is True
    assert receipt.sources_pooled is False
    assert all(store.exists(item.object_key) for item in plan.artifacts)


def test_acquisition_rejects_changed_length_before_any_write(tmp_path: Path) -> None:
    plan, plan_path, readiness_path, payloads = _setup(tmp_path)
    first = plan.artifacts[0]
    bad = plan.model_copy(
        update={
            "artifacts": [
                first.model_copy(update={"expected_content_length_bytes": 999}),
                plan.artifacts[1],
            ]
        }
    )
    data_root = Path(load_storage_readiness_receipt(readiness_path).data_root)
    store = FileSystemObjectStore(data_root)

    with pytest.raises(CalibrationFeasibilityAcquisitionError, match="content length changed"):
        CalibrationFeasibilityAcquisitionService(
            store=store,
            data_root=data_root,
            transport=FakeTransport(payloads),
            request_interval_seconds=0,
            sleeper=lambda _: None,
        ).acquire(
            bad,
            SourceRegistry.from_yaml(REGISTRY),
            load_storage_readiness_receipt(readiness_path),
            plan_path=plan_path,
            registry_path=REGISTRY,
            authorization_path=AUTHORIZATION,
            calibration_readiness_path=CALIBRATION_READINESS,
            storage_readiness_path=readiness_path,
            code_revision="1234567",
        )

    assert not any(store.exists(item.object_key) for item in plan.artifacts)


def test_calibration_feasibility_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationFeasibilityAcquisitionPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationFeasibilityAcquisitionReceipt.model_json_schema()
    )
