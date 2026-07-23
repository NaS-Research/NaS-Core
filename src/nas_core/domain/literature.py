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


class InventoryReconciliationStatus(StrEnum):
    PRIOR_EXACT_MATCH = "prior_exact_match"
    AUTHOR_YEAR_CANDIDATE = "author_year_candidate"
    NEW_CANDIDATE = "new_candidate"


class InventoryReconciliationReceipt(LiteratureModel):
    schema_version: str = "1.0.0"
    reconciliation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    current_queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    prior_queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    artifact_object_key: str = Field(min_length=1)
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_size_bytes: int = Field(ge=1)
    current_record_count: int = Field(ge=1)
    prior_record_count: int = Field(ge=1)
    prior_exact_match_count: int = Field(ge=0)
    author_year_candidate_count: int = Field(ge=0)
    new_candidate_count: int = Field(ge=0)
    verified_at: datetime
    input_checksums_verified: bool
    artifact_checksum_verified: bool
    classification_counts_verified: bool
    prior_decisions_carried_forward: bool
    scientific_conclusions_drawn: bool

    @model_validator(mode="after")
    def validate_reconciliation(self) -> InventoryReconciliationReceipt:
        classified = (
            self.prior_exact_match_count
            + self.author_year_candidate_count
            + self.new_candidate_count
        )
        if classified != self.current_record_count:
            raise ValueError("reconciliation classifications must cover every current record")
        if self.prior_decisions_carried_forward:
            raise ValueError("prior screening decisions cannot carry into a revised question")
        return self


class ScreeningExclusionReason(StrEnum):
    NONHUMAN_OR_NO_PRIMARY_HUMAN_TUMOR_COHORT = "nonhuman_or_no_primary_human_tumor_cohort"
    NO_MOLECULAR_INTRINSIC_SUBTYPE_MEASURE = "no_molecular_intrinsic_subtype_measure"
    NO_RELEVANT_DISCORDANCE_STABILITY_OR_CLASSIFIER_METHOD = (
        "no_relevant_discordance_stability_or_classifier_method"
    )
    REVIEW_EDITORIAL_OR_COMMENTARY_FOR_CITATION_CHAINING_ONLY = (
        "review_editorial_or_commentary_for_citation_chaining_only"
    )
    DUPLICATE_OR_SUPERSEDED_REPORT_WITHOUT_DISTINCT_CONTRIBUTION = (
        "duplicate_or_superseded_report_without_distinct_contribution"
    )
    OUTSIDE_BREAST_CANCER_SCOPE = "outside_breast_cancer_scope"


class ScreeningReviewerRole(StrEnum):
    FOUNDER_INTERNAL_REVIEWER = "founder_internal_reviewer"


class ScreeningDecisionInput(LiteratureModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: ScreeningDecision
    exclusion_reason: ScreeningExclusionReason | None = None
    supersedes_event_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    change_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_input(self) -> ScreeningDecisionInput:
        if self.decision is ScreeningDecision.PENDING:
            raise ValueError("pending is not a review decision")
        if self.decision is ScreeningDecision.EXCLUDE and self.exclusion_reason is None:
            raise ValueError("an exclusion requires one protocol reason")
        if self.decision is not ScreeningDecision.EXCLUDE and self.exclusion_reason is not None:
            raise ValueError("only an exclusion may have an exclusion reason")
        if (self.supersedes_event_id is None) != (self.change_reason is None):
            raise ValueError("a superseding decision requires an event ID and change reason")
        return self


class ScreeningDecisionBatch(LiteratureModel):
    schema_version: str = "1.0.0"
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_previous_progress_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    reviewer_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reviewer_name: str = Field(min_length=1)
    reviewer_role: ScreeningReviewerRole
    decisions: list[ScreeningDecisionInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_unique_records(self) -> ScreeningDecisionBatch:
        identifiers = [item.screening_id for item in self.decisions]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("a batch may decide each screening record only once")
        return self


class ScreeningDecisionEvent(LiteratureModel):
    schema_version: str = "1.0.0"
    event_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    batch_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_key: str = Field(min_length=1)
    decision: ScreeningDecision
    exclusion_reason: ScreeningExclusionReason | None = None
    reviewer_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reviewer_name: str = Field(min_length=1)
    reviewer_role: ScreeningReviewerRole
    decided_at: datetime
    supersedes_event_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    change_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_event(self) -> ScreeningDecisionEvent:
        ScreeningDecisionInput(
            screening_id=self.screening_id,
            decision=self.decision,
            exclusion_reason=self.exclusion_reason,
            supersedes_event_id=self.supersedes_event_id,
            change_reason=self.change_reason,
        )
        return self


class ScreeningProgressSummary(LiteratureModel):
    total_record_count: int = Field(ge=1)
    decided_record_count: int = Field(ge=0)
    pending_record_count: int = Field(ge=0)
    included_record_count: int = Field(ge=0)
    excluded_record_count: int = Field(ge=0)
    unclear_record_count: int = Field(ge=0)
    decision_event_count: int = Field(ge=0)
    completion_percent: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_counts(self) -> ScreeningProgressSummary:
        decisions = (
            self.included_record_count + self.excluded_record_count + self.unclear_record_count
        )
        if decisions != self.decided_record_count:
            raise ValueError("decision category counts do not reconcile")
        if self.decided_record_count + self.pending_record_count != self.total_record_count:
            raise ValueError("decided and pending counts do not reconcile")
        if self.decision_event_count < self.decided_record_count:
            raise ValueError("event count cannot be smaller than decided record count")
        return self


class ScreeningProgressManifest(LiteratureModel):
    schema_version: str = "1.0.0"
    progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    previous_progress_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    batch_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    reviewer_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reviewer_name: str = Field(min_length=1)
    reviewer_role: ScreeningReviewerRole
    queue_object_key: str = Field(min_length=1)
    queue_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifacts: list[StoredObject] = Field(min_length=2, max_length=2)
    summary: ScreeningProgressSummary
    added_event_count: int = Field(ge=1, le=100)
    ai_decisions_recorded: int = Field(ge=0)
    scientific_conclusions_drawn: bool
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class ScreeningProgressReceipt(LiteratureModel):
    schema_version: str = "1.0.0"
    progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    previous_progress_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    batch_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    algorithm_version: str = Field(min_length=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    created_at: datetime
    manifest_object_key: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decisions_object_key: str = Field(min_length=1)
    decisions_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decisions_size_bytes: int = Field(ge=1)
    summary_object_key: str = Field(min_length=1)
    summary_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    summary_size_bytes: int = Field(ge=1)
    summary: ScreeningProgressSummary
    verified_at: datetime
    manifest_checksum_verified: bool
    artifact_checksums_verified: bool
    event_chain_verified: bool
    count_invariants_verified: bool
    screening_status: ScreeningStatus
    ai_decisions_recorded: int = Field(ge=0)
    scientific_conclusions_drawn: bool


class ScreeningReviewBatch(LiteratureModel):
    schema_version: str = "1.0.0"
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    based_on_progress_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    available_record_count: int = Field(ge=0)
    records: list[ScreeningQueueRecord]


class ScreeningPriorityTier(StrEnum):
    CORE = "core"
    SUPPORTING = "supporting"
    CONTEXT = "context"


class ScreeningPriorityRecord(LiteratureModel):
    rank: int = Field(ge=1)
    score: int
    tier: ScreeningPriorityTier
    positive_signals: list[str]
    caution_signals: list[str]
    record: ScreeningQueueRecord


class ScreeningPriorityBatch(LiteratureModel):
    schema_version: str = "1.0.0"
    algorithm_version: str = Field(min_length=1)
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    based_on_progress_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    available_record_count: int = Field(ge=0)
    core_record_count: int = Field(ge=0)
    supporting_record_count: int = Field(ge=0)
    context_record_count: int = Field(ge=0)
    records: list[ScreeningPriorityRecord]
    final_decisions_recorded: int = Field(ge=0)
    scientific_conclusions_drawn: bool


def load_literature_search_receipt(path: Path) -> LiteratureSearchReceipt:
    return LiteratureSearchReceipt.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def write_literature_search_receipt(path: Path, receipt: LiteratureSearchReceipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_screening_queue_receipt(path: Path) -> ScreeningQueueReceipt:
    return ScreeningQueueReceipt.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def write_screening_queue_receipt(path: Path, receipt: ScreeningQueueReceipt) -> None:
    _write_exclusive_yaml(path, receipt)


def load_inventory_reconciliation_receipt(path: Path) -> InventoryReconciliationReceipt:
    return InventoryReconciliationReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_inventory_reconciliation_receipt(
    path: Path,
    receipt: InventoryReconciliationReceipt,
) -> None:
    _write_exclusive_yaml(path, receipt)


def load_screening_progress_receipt(path: Path) -> ScreeningProgressReceipt:
    return ScreeningProgressReceipt.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_screening_decision_batch(path: Path) -> ScreeningDecisionBatch:
    return ScreeningDecisionBatch.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def write_screening_progress_receipt(path: Path, receipt: ScreeningProgressReceipt) -> None:
    _write_exclusive_yaml(path, receipt)


def _write_exclusive_yaml(path: Path, model: LiteratureModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        model.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_screening_review_schemas(
    decision_batch_path: Path,
    progress_manifest_path: Path,
    progress_receipt_path: Path,
) -> None:
    for path, model in (
        (decision_batch_path, ScreeningDecisionBatch),
        (progress_manifest_path, ScreeningProgressManifest),
        (progress_receipt_path, ScreeningProgressReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        path.write_text(f"{payload}\n", encoding="utf-8")


def write_inventory_reconciliation_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        InventoryReconciliationReceipt.model_json_schema(),
        indent=2,
        sort_keys=True,
    )
    path.write_text(f"{payload}\n", encoding="utf-8")


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
