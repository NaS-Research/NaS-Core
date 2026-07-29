"""Read-only preflight for a marker-validated NaS data root."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from nas_core.domain.storage_readiness import (
    StorageReadinessDecision,
    StorageReadinessReceipt,
)
from nas_core.ingestion.gdc import sha256
from nas_core.storage.layout import DataLayout


class StorageReadinessService:
    def inspect(
        self,
        data_root: Path,
        *,
        minimum_required_bytes: int,
        code_revision: str,
        checked_at: datetime,
    ) -> StorageReadinessReceipt:
        layout = DataLayout(data_root)
        layout.validate()
        root = data_root.expanduser().resolve()
        marker = root / DataLayout.MARKER_FILE
        marker_payload = json.loads(marker.read_text(encoding="utf-8"))
        filesystem = os.statvfs(root)
        available_bytes = filesystem.f_bavail * filesystem.f_frsize
        mount_read_only = bool(filesystem.f_flag & os.ST_RDONLY)
        write_access = os.access(root, os.W_OK)

        blockers: list[str] = []
        if mount_read_only:
            blockers.append("filesystem mount is read-only")
        if not write_access:
            blockers.append("operating system reports no write access")
        if available_bytes < minimum_required_bytes:
            blockers.append("available capacity is below the declared minimum")

        return StorageReadinessReceipt(
            receipt_version="1.0.0",
            code_revision=code_revision,
            checked_at=checked_at,
            data_root=str(root),
            marker_sha256=sha256(marker.read_bytes()),
            layout_schema_version=int(marker_payload["schema_version"]),
            required_directories_present=list(DataLayout.REQUIRED_DIRECTORIES),
            available_bytes=available_bytes,
            minimum_required_bytes=minimum_required_bytes,
            mount_read_only=mount_read_only,
            operating_system_write_access=write_access,
            write_probe_performed=False,
            decision=(
                StorageReadinessDecision.BLOCKED
                if blockers
                else StorageReadinessDecision.READY
            ),
            blockers=blockers,
            limitations=[
                "The check uses filesystem flags and access metadata without a write probe.",
                "A ready result does not verify future availability, backup, or media health.",
                "No source artifact, participant row, or molecular value is accessed.",
            ],
            source_bytes_written=False,
            biomedical_data_accessed=False,
        )
