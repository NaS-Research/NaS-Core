"""Typed cohort-build receipts, QA summaries, and immutable manifests."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.research import ReviewDecision, ReviewRecord


class CohortModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CohortExclusionReason(StrEnum):
    INVALID_INDEX_DATE = "invalid_index_date"
    NO_PRIMARY_DIAGNOSIS = "no_primary_diagnosis"
    INVALID_PATHOLOGIC_STAGE = "invalid_pathologic_stage"
    MISSING_DIAGNOSIS_ID = "missing_diagnosis_id"
    MISSING_OR_INVALID_AGE = "missing_or_invalid_age"
    UNDERAGE = "underage"
    INVALID_VITAL_STATUS = "invalid_vital_status"
    INVALID_SURVIVAL_TIME = "invalid_survival_time"


class SnapshotVerification(CohortModel):
    verified_at: datetime
    manifest_payload_checksum: Literal["passed"]
    stored_object_checksums: Literal["passed"]
    verified_object_count: int = Field(ge=1)
    duplicate_case_check: Literal["passed"]
    pagination_count_check: Literal["passed"]
    outcome_analysis_performed: Literal[False]


class SnapshotReceipt(CohortModel):
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
    protocol_tag: str = Field(min_length=1)
    ingestion_code_revision: str = Field(min_length=7)
    source_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    data_release: str = Field(min_length=1)
    api_tag: str = Field(min_length=1)
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    retrieved_at: datetime
    record_count: int = Field(ge=0)
    page_count: int = Field(ge=1)
    warning_count: int = Field(ge=0)
    manifest_object_key: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    release_notes_url: str = Field(min_length=1)
    release_notes_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    verification: SnapshotVerification


class SelectionDescriptives(CohortModel):
    case_count: int = Field(ge=0)
    age_available_count: int = Field(ge=0)
    mean_age_years: float | None = None
    median_age_years: float | None = None
    vital_alive_count: int = Field(ge=0)
    vital_dead_count: int = Field(ge=0)
    vital_other_or_missing_count: int = Field(ge=0)


class CohortQASummary(CohortModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(min_length=1)
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_case_count: int = Field(ge=0)
    included_case_count: int = Field(ge=0)
    excluded_case_count: int = Field(ge=0)
    exclusion_counts: dict[str, int]
    missingness_counts: dict[str, int]
    stage_normalization_counts: dict[str, int]
    included_descriptives: SelectionDescriptives
    excluded_descriptives: SelectionDescriptives
    outcome_analysis_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_counts(self) -> CohortQASummary:
        if self.included_case_count + self.excluded_case_count != self.input_case_count:
            raise ValueError("included and excluded counts must equal the input count")
        if sum(self.exclusion_counts.values()) != self.excluded_case_count:
            raise ValueError("exclusion counts must equal the excluded count")
        return self


class CohortArtifact(CohortModel):
    object_key: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class CohortBuildManifest(CohortModel):
    schema_version: str = "1.0.0"
    build_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
    protocol_tag: str = Field(min_length=1)
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(min_length=7)
    built_at: datetime
    input_case_count: int = Field(ge=0)
    included_case_count: int = Field(ge=0)
    excluded_case_count: int = Field(ge=0)
    artifacts: list[CohortArtifact] = Field(min_length=3)
    outcome_analysis_performed: Literal[False] = False
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class CohortGateStatus(StrEnum):
    PENDING_FOUNDER_REVIEW = "pending_founder_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"


class CohortVerification(CohortModel):
    verified_at: datetime
    manifest_payload_checksum: Literal["passed"]
    artifact_checksums: Literal["passed"]
    case_partition_unique: Literal["passed"]
    case_partition_disjoint: Literal["passed"]
    case_partition_complete: Literal["passed"]
    requested_field_missingness_complete: Literal["passed"]
    outcome_analysis_performed: Literal[False]


class CohortBuildReceipt(CohortModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
    protocol_tag: str = Field(min_length=1)
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    build_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(min_length=7)
    built_at: datetime
    input_case_count: int = Field(ge=0)
    included_case_count: int = Field(ge=0)
    excluded_case_count: int = Field(ge=0)
    exclusion_counts: dict[str, int]
    manifest_object_key: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifacts: list[CohortArtifact] = Field(min_length=3)
    verification: CohortVerification
    qa_gate_status: CohortGateStatus
    reviews: list[ReviewRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_gate(self) -> CohortBuildReceipt:
        if self.included_case_count + self.excluded_case_count != self.input_case_count:
            raise ValueError("cohort receipt counts do not equal the input count")
        if sum(self.exclusion_counts.values()) != self.excluded_case_count:
            raise ValueError("cohort receipt exclusions do not equal the excluded count")
        if self.qa_gate_status is CohortGateStatus.APPROVED:
            required = [review for review in self.reviews if review.required_for_gate]
            if not required or any(
                review.decision is not ReviewDecision.APPROVED for review in required
            ):
                raise ValueError("an approved cohort gate requires all gate reviews approved")
        return self


def load_snapshot_receipt(path: Path) -> SnapshotReceipt:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SnapshotReceipt.model_validate(payload)


def load_cohort_receipt(path: Path) -> CohortBuildReceipt:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return CohortBuildReceipt.model_validate(payload)


def write_cohort_schemas(qa_path: Path, manifest_path: Path, receipt_path: Path) -> None:
    for path, model in (
        (qa_path, CohortQASummary),
        (manifest_path, CohortBuildManifest),
        (receipt_path, CohortBuildReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        path.write_text(f"{payload}\n", encoding="utf-8")
