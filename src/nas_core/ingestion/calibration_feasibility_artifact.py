"""Atomic governed acquisition for excluded public calibration-feasibility files."""

from __future__ import annotations

import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, cast

from nas_core.domain.calibration_feasibility_artifact import (
    CalibrationFeasibilityAcquisitionPlan,
    CalibrationFeasibilityAcquisitionReceipt,
    CalibrationFeasibilityArtifact,
    CalibrationFeasibilityArtifactReceipt,
)
from nas_core.domain.storage_readiness import StorageReadinessDecision, StorageReadinessReceipt
from nas_core.governance.classifications import DataClassification
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import sha256
from nas_core.ingestion.public_artifact import (
    DownloadResult,
    StreamingTransport,
    UrllibStreamingTransport,
)
from nas_core.storage.object_store import ObjectStore


class CalibrationFeasibilityAcquisitionError(RuntimeError):
    """Raised when feasibility acquisition cannot preserve its frozen boundary."""


class CalibrationFeasibilityAcquisitionService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        data_root: Path,
        transport: StreamingTransport | None = None,
        request_interval_seconds: float = 0.4,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self._store = store
        self._data_root = data_root.expanduser().resolve()
        self._working = self._data_root / "working"
        self._transport = transport or UrllibStreamingTransport()
        self._request_interval_seconds = request_interval_seconds
        self._sleep = sleeper or time.sleep

    def acquire(
        self,
        plan: CalibrationFeasibilityAcquisitionPlan,
        registry: SourceRegistry,
        storage_readiness: StorageReadinessReceipt,
        *,
        plan_path: Path,
        registry_path: Path,
        authorization_path: Path,
        calibration_readiness_path: Path,
        storage_readiness_path: Path,
        code_revision: str,
    ) -> CalibrationFeasibilityAcquisitionReceipt:
        self._validate_inputs(
            plan,
            registry,
            storage_readiness,
            registry_path=registry_path,
            authorization_path=authorization_path,
            calibration_readiness_path=calibration_readiness_path,
            storage_readiness_path=storage_readiness_path,
        )
        self._working.mkdir(parents=True, exist_ok=True)
        staged: list[
            tuple[Path, CalibrationFeasibilityArtifact, DownloadResult]
        ] = []
        try:
            for artifact in plan.artifacts:
                if self._store.exists(artifact.object_key):
                    raise CalibrationFeasibilityAcquisitionError(
                        f"immutable object already exists: {artifact.object_key}"
                    )
                with tempfile.NamedTemporaryFile(
                    mode="w+b",
                    prefix="calibration-feasibility-",
                    suffix=".download",
                    dir=self._working,
                    delete=False,
                ) as temporary:
                    path = Path(temporary.name)
                    result = self._transport.download(
                        artifact.official_url,
                        cast(BinaryIO, temporary),
                    )
                    temporary.flush()
                staged.append((path, artifact, result))
                self._sleep(self._request_interval_seconds)
                if result.status_code != 200:
                    raise CalibrationFeasibilityAcquisitionError(
                        f"download returned HTTP {result.status_code}"
                    )
                if result.content_length_bytes != artifact.expected_content_length_bytes:
                    raise CalibrationFeasibilityAcquisitionError(
                        f"content length changed for {artifact.filename}"
                    )
                header_length = result.headers.get("Content-Length")
                if (
                    header_length is not None
                    and int(header_length) != artifact.expected_content_length_bytes
                ):
                    raise CalibrationFeasibilityAcquisitionError(
                        f"response Content-Length changed for {artifact.filename}"
                    )
            receipts: list[CalibrationFeasibilityArtifactReceipt] = []
            for path, artifact, result in staged:
                self._store.put_file(
                    artifact.object_key,
                    path,
                    content_type=artifact.expected_content_type,
                )
                if not self._store.exists(artifact.object_key):
                    raise CalibrationFeasibilityAcquisitionError("stored object is missing")
                receipts.append(
                    CalibrationFeasibilityArtifactReceipt(
                        source_id=artifact.source_id,
                        source_accession=artifact.source_accession,
                        file_accession=artifact.file_accession,
                        artifact_kind=artifact.artifact_kind,
                        filename=artifact.filename,
                        official_url=artifact.official_url,
                        response_content_type=result.headers.get(
                            "Content-Type", artifact.expected_content_type
                        ),
                        response_last_modified=result.headers.get("Last-Modified"),
                        content_length_bytes=result.content_length_bytes,
                        sha256=result.sha256,
                        object_key=artifact.object_key,
                        immutable_object_verified=True,
                    )
                )
            return CalibrationFeasibilityAcquisitionReceipt(
                receipt_version="1.0.0",
                study_id=plan.study_id,
                code_revision=code_revision,
                acquired_at=datetime.now(UTC),
                plan_sha256=sha256(plan_path.read_bytes()),
                artifacts=receipts,
                all_immutable_objects_verified=True,
                molecular_values_parsed=False,
                outcomes_accessed=False,
                sources_pooled=False,
                thresholds_estimated=False,
                classifier_executed=False,
                external_publication_authorized=False,
            )
        finally:
            for path, _, _ in staged:
                path.unlink(missing_ok=True)

    def _validate_inputs(
        self,
        plan: CalibrationFeasibilityAcquisitionPlan,
        registry: SourceRegistry,
        storage_readiness: StorageReadinessReceipt,
        *,
        registry_path: Path,
        authorization_path: Path,
        calibration_readiness_path: Path,
        storage_readiness_path: Path,
    ) -> None:
        if storage_readiness.decision is not StorageReadinessDecision.READY:
            raise CalibrationFeasibilityAcquisitionError("governed storage is not ready")
        if Path(storage_readiness.data_root).resolve() != self._data_root:
            raise CalibrationFeasibilityAcquisitionError("storage receipt identifies another root")
        for source_id in {item.source_id for item in plan.artifacts}:
            source = registry.get(source_id)
            if (
                source.classification is not DataClassification.PUBLIC_OPEN
                or source.status.value != "active"
                or "calibration-feasibility" not in source.approved_purposes
            ):
                raise CalibrationFeasibilityAcquisitionError(
                    f"source is not approved for feasibility: {source_id}"
                )
        declared = {
            "source registry": (plan.source_registry_sha256, registry_path),
            "standing authorization": (
                plan.standing_authorization_sha256,
                authorization_path,
            ),
            "calibration readiness": (
                plan.calibration_readiness_receipt_sha256,
                calibration_readiness_path,
            ),
            "storage readiness": (
                plan.storage_readiness_receipt_sha256,
                storage_readiness_path,
            ),
        }
        changed = [
            label
            for label, (expected, path) in declared.items()
            if expected != sha256(path.read_bytes())
        ]
        if changed:
            raise CalibrationFeasibilityAcquisitionError(
                f"acquisition provenance changed: {', '.join(changed)}"
            )
