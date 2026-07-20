"""Immutable dataset snapshot and provenance models."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from nas_core.governance.classifications import DataClassification


class SnapshotModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RequestRecord(SnapshotModel):
    method: str = Field(pattern=r"^(GET|POST)$")
    url: str = Field(min_length=1)
    body: dict[str, object]


class ReleaseRecord(SnapshotModel):
    data_release: str = Field(min_length=1)
    api_status: str = Field(min_length=1)
    api_tag: str = Field(min_length=1)
    api_version: str = Field(min_length=1)
    api_commit: str = Field(min_length=1)
    status_response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class StoredObject(SnapshotModel):
    object_key: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_ids: list[str] = Field(default_factory=list)
    file_ids: list[str] = Field(default_factory=list)


class DatasetSnapshot(SnapshotModel):
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    classification: DataClassification
    purpose: str = Field(min_length=1)
    retrieved_at: datetime
    release: ReleaseRecord
    requests: list[RequestRecord] = Field(min_length=1)
    objects: list[StoredObject] = Field(min_length=1)
    record_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


def write_dataset_snapshot_schema(path: Path) -> None:
    """Write the canonical JSON Schema produced by the snapshot model."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(DatasetSnapshot.model_json_schema(), indent=2, sort_keys=True)
    path.write_text(f"{payload}\n", encoding="utf-8")
