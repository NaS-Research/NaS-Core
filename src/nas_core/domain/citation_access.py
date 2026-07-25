"""Typed batch-access accounting for citation-derived repository candidates."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CitationAccessModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RepositoryAccessOutcome(StrEnum):
    RETRIEVED = "retrieved"
    FULL_TEXT_UNAVAILABLE = "full_text_unavailable"
    LICENSE_NOT_APPROVED = "license_not_approved"
    IDENTITY_MISMATCH = "identity_mismatch"
    METADATA_INVALID = "metadata_invalid"
    REMOTE_ERROR = "remote_error"


class RepositoryAccessAssessmentRecord(CitationAccessModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_key: str = Field(pattern=r"^[A-Z]+:.+$")
    pmcid: str = Field(pattern=r"^PMC[0-9]+$")
    title: str = Field(min_length=1)
    outcome: RepositoryAccessOutcome
    retrieval_receipt_path: str | None = Field(default=None, min_length=1)
    reason: str | None = Field(default=None, min_length=1)
    durable_full_text_stored: bool
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_outcome(self) -> RepositoryAccessAssessmentRecord:
        if self.outcome is RepositoryAccessOutcome.RETRIEVED:
            if self.retrieval_receipt_path is None or self.reason is not None:
                raise ValueError("retrieved record requires only a retrieval receipt")
            if not self.durable_full_text_stored:
                raise ValueError("retrieved record must acknowledge durable licensed storage")
        else:
            if self.retrieval_receipt_path is not None or self.reason is None:
                raise ValueError("failed access check requires only an explicit reason")
            if self.durable_full_text_stored:
                raise ValueError("failed access check cannot claim durable storage")
        if self.scientific_conclusions_drawn:
            raise ValueError("access assessment cannot draw scientific conclusions")
        return self


class RepositoryAccessBatchReceipt(CitationAccessModel):
    schema_version: str = "1.0.0"
    batch_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    inventory_queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    inventory_progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    assessed_at: datetime
    repository_candidate_count: int = Field(ge=1)
    retrieved_count: int = Field(ge=0)
    access_check_required_count: int = Field(ge=0)
    records: list[RepositoryAccessAssessmentRecord] = Field(min_length=1)
    complete_coverage_verified: bool
    identity_and_license_fail_closed: bool
    founder_decisions_changed: int = Field(default=0, ge=0)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_batch(self) -> RepositoryAccessBatchReceipt:
        if len(self.records) != self.repository_candidate_count:
            raise ValueError("repository access batch does not cover every candidate")
        if len({item.screening_id for item in self.records}) != len(self.records):
            raise ValueError("repository access batch contains duplicate records")
        retrieved = sum(
            item.outcome is RepositoryAccessOutcome.RETRIEVED for item in self.records
        )
        if retrieved != self.retrieved_count:
            raise ValueError("repository retrieval count does not reconcile")
        if len(self.records) - retrieved != self.access_check_required_count:
            raise ValueError("repository access-check count does not reconcile")
        if not self.complete_coverage_verified or not self.identity_and_license_fail_closed:
            raise ValueError("repository access batch requires verified safeguards")
        if self.founder_decisions_changed or self.scientific_conclusions_drawn:
            raise ValueError("access accounting cannot change decisions or conclude")
        return self


def load_repository_access_batch_receipt(path: Path) -> RepositoryAccessBatchReceipt:
    return RepositoryAccessBatchReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_repository_access_batch_receipt(
    path: Path,
    receipt: RepositoryAccessBatchReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)
