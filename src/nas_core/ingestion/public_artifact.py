"""Streaming, immutable acquisition of an allowlisted public GEO artifact."""

from __future__ import annotations

import hashlib
import ssl
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, Protocol, cast
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import certifi

from nas_core.domain.public_artifact import (
    PublicArtifactAcquisitionPlan,
    PublicArtifactAcquisitionReceipt,
    PublicArtifactKind,
)
from nas_core.domain.reference_development import ReferenceDevelopmentProtocol
from nas_core.domain.storage_readiness import (
    StorageReadinessDecision,
    StorageReadinessReceipt,
)
from nas_core.governance.classifications import DataClassification
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore

GSE81538_HOST = "ftp.ncbi.nlm.nih.gov"
GSE81538_MATRIX_PATH = (
    "/geo/series/GSE81nnn/GSE81538/suppl/"
    "GSE81538_gene_expression_405_transformed.csv.gz"
)
GSE81538_FAMILY_SOFT_PATH = (
    "/geo/series/GSE81nnn/GSE81538/soft/GSE81538_family.soft.gz"
)
GSE81538_PATHS = {GSE81538_MATRIX_PATH, GSE81538_FAMILY_SOFT_PATH}


class PublicArtifactAcquisitionError(RuntimeError):
    """Raised when governed public-artifact acquisition fails closed."""


@dataclass(frozen=True, slots=True)
class DownloadResult:
    status_code: int
    headers: Mapping[str, str]
    content_length_bytes: int
    sha256: str


class StreamingTransport(Protocol):
    def download(self, url: str, destination: BinaryIO) -> DownloadResult: ...


class UrllibStreamingTransport:
    def __init__(self, *, timeout_seconds: float = 120.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def download(self, url: str, destination: BinaryIO) -> DownloadResult:
        request = Request(
            url,
            headers={"Accept": "application/x-gzip", "User-Agent": "NaS-Core/0.1"},
        )
        digest = hashlib.sha256()
        size = 0
        with urlopen(  # noqa: S310
            request,
            timeout=self._timeout_seconds,
            context=self._ssl_context,
        ) as response:
            while chunk := response.read(1024 * 1024):
                destination.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            return DownloadResult(
                status_code=response.status,
                headers=dict(response.headers.items()),
                content_length_bytes=size,
                sha256=digest.hexdigest(),
            )


class PublicArtifactAcquisitionService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        data_root: Path,
        transport: StreamingTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._data_root = data_root.expanduser().resolve()
        self._working = self._data_root / "working"
        self._transport = transport or UrllibStreamingTransport()
        self._clock = clock or (lambda: datetime.now(UTC))

    def acquire(
        self,
        plan: PublicArtifactAcquisitionPlan,
        registry: SourceRegistry,
        reference_protocol: ReferenceDevelopmentProtocol,
        storage_readiness: StorageReadinessReceipt,
        *,
        plan_path: Path,
        registry_path: Path,
        authorization_path: Path,
        reference_protocol_path: Path,
        storage_readiness_path: Path,
        code_revision: str,
    ) -> PublicArtifactAcquisitionReceipt:
        self._validate_inputs(
            plan,
            registry,
            reference_protocol,
            storage_readiness,
            registry_path=registry_path,
            authorization_path=authorization_path,
            reference_protocol_path=reference_protocol_path,
            storage_readiness_path=storage_readiness_path,
        )
        if Path(storage_readiness.data_root).resolve() != self._data_root:
            raise PublicArtifactAcquisitionError(
                "storage receipt identifies another data root"
            )
        if self._store.exists(plan.object_key):
            raise PublicArtifactAcquisitionError("immutable object already exists")
        self._working.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w+b",
                prefix=f"gse81538-{plan.artifact_kind.value}-",
                suffix=".download",
                dir=self._working,
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                result = self._transport.download(
                    plan.official_url,
                    cast(BinaryIO, temporary),
                )
                temporary.flush()
            self._validate_download(plan, result)
            self._store.put_file(
                plan.object_key,
                temporary_path,
                content_type=plan.expected_content_type,
            )
            if not self._store.exists(plan.object_key):
                raise PublicArtifactAcquisitionError("immutable object was not stored")
            return PublicArtifactAcquisitionReceipt(
                receipt_version="1.0.0",
                study_id=plan.study_id,
                source_id=plan.source_id,
                source_accession=plan.source_accession,
                artifact_kind=plan.artifact_kind,
                code_revision=code_revision,
                acquired_at=self._clock(),
                plan_sha256=sha256(plan_path.read_bytes()),
                official_url=plan.official_url,
                response_content_type=result.headers.get(
                    "Content-Type", plan.expected_content_type
                ),
                response_last_modified=result.headers.get("Last-Modified"),
                content_length_bytes=result.content_length_bytes,
                sha256=result.sha256,
                object_key=plan.object_key,
                immutable_object_verified=True,
                source_bytes_stored=True,
                molecular_source_bytes_stored=(
                    plan.artifact_kind
                    is PublicArtifactKind.PROCESSED_EXPRESSION_MATRIX
                ),
                molecular_values_parsed=False,
                outcome_values_accessed=False,
                classifier_executed=False,
                external_publication_authorized=False,
            )
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _validate_inputs(
        plan: PublicArtifactAcquisitionPlan,
        registry: SourceRegistry,
        reference_protocol: ReferenceDevelopmentProtocol,
        storage_readiness: StorageReadinessReceipt,
        *,
        registry_path: Path,
        authorization_path: Path,
        reference_protocol_path: Path,
        storage_readiness_path: Path,
    ) -> None:
        parsed = urlsplit(plan.official_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != GSE81538_HOST
            or parsed.path not in GSE81538_PATHS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
        ):
            raise PublicArtifactAcquisitionError("source URL is not the allowlisted GEO artifact")
        source = registry.get(plan.source_id)
        if (
            source.classification is not DataClassification.PUBLIC_OPEN
            or source.status.value != "active"
        ):
            raise PublicArtifactAcquisitionError("source must be active public/open")
        if "reference-development" not in source.approved_purposes:
            raise PublicArtifactAcquisitionError("source purpose is not approved")
        if reference_protocol.source_id != plan.source_id:
            raise PublicArtifactAcquisitionError("reference protocol identifies another source")
        if storage_readiness.decision is not StorageReadinessDecision.READY:
            raise PublicArtifactAcquisitionError("governed storage is not ready")
        declared = {
            "source registry": (plan.source_registry_sha256, registry_path),
            "standing authorization": (
                plan.standing_authorization_sha256,
                authorization_path,
            ),
            "reference protocol": (
                plan.reference_protocol_sha256,
                reference_protocol_path,
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
            raise PublicArtifactAcquisitionError(
                f"acquisition provenance changed: {', '.join(changed)}"
            )

    @staticmethod
    def _validate_download(
        plan: PublicArtifactAcquisitionPlan,
        result: DownloadResult,
    ) -> None:
        if result.status_code != 200:
            raise PublicArtifactAcquisitionError(
                f"download returned HTTP {result.status_code}"
            )
        if result.content_length_bytes != plan.expected_content_length_bytes:
            raise PublicArtifactAcquisitionError("downloaded content length changed")
        header_length = result.headers.get("Content-Length")
        if header_length is not None and int(header_length) != result.content_length_bytes:
            raise PublicArtifactAcquisitionError("response Content-Length does not reconcile")
