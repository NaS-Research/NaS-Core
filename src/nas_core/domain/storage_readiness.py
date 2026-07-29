"""Non-mutating governed storage-readiness evidence."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StorageReadinessModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StorageReadinessDecision(StrEnum):
    READY = "ready"
    BLOCKED = "blocked"


class StorageReadinessReceipt(StorageReadinessModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    checked_at: datetime
    data_root: str = Field(min_length=1)
    marker_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    layout_schema_version: int = Field(ge=1)
    required_directories_present: list[str] = Field(min_length=1)
    available_bytes: int = Field(ge=0)
    minimum_required_bytes: int = Field(gt=0)
    mount_read_only: bool
    operating_system_write_access: bool
    write_probe_performed: bool
    decision: StorageReadinessDecision
    blockers: list[str]
    limitations: list[str] = Field(min_length=1)
    source_bytes_written: bool
    biomedical_data_accessed: bool

    @model_validator(mode="after")
    def reconcile_decision(self) -> StorageReadinessReceipt:
        should_block = (
            self.mount_read_only
            or not self.operating_system_write_access
            or self.available_bytes < self.minimum_required_bytes
        )
        expected = (
            StorageReadinessDecision.BLOCKED
            if should_block
            else StorageReadinessDecision.READY
        )
        if self.decision is not expected:
            raise ValueError("storage decision does not reconcile with observations")
        if (self.decision is StorageReadinessDecision.BLOCKED) != bool(self.blockers):
            raise ValueError("blocked storage requires blockers and ready storage cannot have them")
        if self.write_probe_performed:
            raise ValueError("storage readiness must remain non-mutating")
        if self.source_bytes_written or self.biomedical_data_accessed:
            raise ValueError("storage readiness cannot write or access biomedical data")
        return self


def load_storage_readiness_receipt(path: Path) -> StorageReadinessReceipt:
    return StorageReadinessReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_storage_readiness_receipt(
    path: Path,
    receipt: StorageReadinessReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("storage readiness receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_storage_readiness_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(StorageReadinessReceipt.model_json_schema(), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
