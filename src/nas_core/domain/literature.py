"""Typed immutable provenance for bibliographic search executions."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class ScreeningStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class SourceSearchReceipt(LiteratureModel):
    source_id: str = Field(min_length=1)
    reported_result_count: int = Field(ge=0)
    retrieved_record_count: int = Field(ge=0)
    request_count: int = Field(ge=1)
    raw_object_count: int = Field(ge=1)


class LiteratureSearchReceipt(LiteratureModel):
    schema_version: str = "1.0.0"
    execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    question_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    executed_at: datetime
    source_results: list[SourceSearchReceipt] = Field(min_length=2)
    unique_record_count: int = Field(ge=0)
    duplicate_record_count: int = Field(ge=0)
    manifest_object_key: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalized_records_object_key: str = Field(min_length=1)
    normalized_records_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalized_records_size_bytes: int = Field(ge=0)
    verified_at: datetime
    manifest_checksum_verified: bool
    object_checksums_verified: bool
    object_sizes_verified: bool
    record_count_invariants_verified: bool
    verified_object_count: int = Field(ge=1)
    screening_status: ScreeningStatus
    scientific_conclusions_drawn: bool
    outcome_data_accessed: bool


class ScreeningDecision(StrEnum):
    PENDING = "pending"
    INCLUDE = "include"
    EXCLUDE = "exclude"
    UNCLEAR = "unclear"


class ScreeningQueueRecord(LiteratureModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
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
    decision: ScreeningDecision = ScreeningDecision.PENDING
    exclusion_reason: str | None = None
    reviewer: str | None = None
    decided_at: datetime | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> ScreeningQueueRecord:
        if self.decision is ScreeningDecision.PENDING:
            if any((self.exclusion_reason, self.reviewer, self.decided_at)):
                raise ValueError("pending screening records cannot contain adjudication")
        elif self.reviewer is None or self.decided_at is None:
            raise ValueError("a screening decision requires reviewer and timestamp")
        if self.decision is ScreeningDecision.EXCLUDE and not self.exclusion_reason:
            raise ValueError("an exclusion requires one reason")
        if self.decision is not ScreeningDecision.EXCLUDE and self.exclusion_reason:
            raise ValueError("only excluded records may contain an exclusion reason")
        return self


class ScreeningQueueSummary(LiteratureModel):
    input_record_count: int = Field(ge=0)
    pending_record_count: int = Field(ge=0)
    records_with_abstract: int = Field(ge=0)
    records_without_abstract: int = Field(ge=0)
    records_with_doi: int = Field(ge=0)
    records_with_pmid: int = Field(ge=0)
    earliest_publication_year: int | None = None
    latest_publication_year: int | None = None


class ScreeningQueueManifest(LiteratureModel):
    schema_version: str = "1.0.0"
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    question_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    search_execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    input_object_key: str = Field(min_length=1)
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifacts: list[StoredObject] = Field(min_length=2)
    summary: ScreeningQueueSummary
    human_decisions_recorded: int = Field(ge=0)
    ai_decisions_recorded: int = Field(ge=0)
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class ScreeningQueueReceipt(LiteratureModel):
    schema_version: str = "1.0.0"
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    search_execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    manifest_object_key: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    queue_object_key: str = Field(min_length=1)
    queue_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    queue_size_bytes: int = Field(ge=0)
    summary: ScreeningQueueSummary
    verified_at: datetime
    manifest_checksum_verified: bool
    artifact_checksums_verified: bool
    record_count_verified: bool
    screening_status: ScreeningStatus
    scientific_conclusions_drawn: bool


def load_literature_search_receipt(path: Path) -> LiteratureSearchReceipt:
    return LiteratureSearchReceipt.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def write_literature_schemas(
    snapshot_path: Path,
    receipt_path: Path,
    screening_manifest_path: Path,
    screening_receipt_path: Path,
) -> None:
    for path, model in (
        (snapshot_path, LiteratureSearchSnapshot),
        (receipt_path, LiteratureSearchReceipt),
        (screening_manifest_path, ScreeningQueueManifest),
        (screening_receipt_path, ScreeningQueueReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        path.write_text(f"{payload}\n", encoding="utf-8")
