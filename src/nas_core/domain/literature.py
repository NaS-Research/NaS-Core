"""Typed immutable provenance for bibliographic search executions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from nas_core.domain.snapshots import StoredObject


class LiteratureModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LiteratureRequest(LiteratureModel):
    source_id: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    parameters: dict[str, str]


class SourceSearchResult(LiteratureModel):
    source_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    reported_result_count: int = Field(ge=0)
    retrieved_record_count: int = Field(ge=0)
    request_count: int = Field(ge=1)
    raw_objects: list[StoredObject] = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)


class BibliographicRecord(LiteratureModel):
    record_key: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    pmid: str | None = None
    pmcid: str | None = None
    doi: str | None = None
    title: str = Field(min_length=1)
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    publication_year: int | None = Field(default=None, ge=1500, le=2200)
    abstract: str | None = None
    is_open_access: bool | None = None


class LiteratureSearchSnapshot(LiteratureModel):
    schema_version: str = "1.0.0"
    execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    question_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    executed_at: datetime
    contact_email_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    requests: list[LiteratureRequest] = Field(min_length=1)
    source_results: list[SourceSearchResult] = Field(min_length=2)
    normalized_records_object: StoredObject
    unique_record_count: int = Field(ge=0)
    duplicate_record_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


def write_literature_snapshot_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(LiteratureSearchSnapshot.model_json_schema(), indent=2, sort_keys=True)
    path.write_text(f"{payload}\n", encoding="utf-8")
