"""Checksum-bound closure contracts for citation-pass saturation accounting."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CitationSaturationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CitationPassClosureReceipt(CitationSaturationModel):
    schema_version: str = "1.0.0"
    closure_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    closed_at: datetime
    citation_execution_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    screening_preparation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    reconciliation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    screening_preparation_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reconciliation_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    queue_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    access_inventory_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    appraisal_progress_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    prior_appraisal_sha256s: list[str] = Field(default_factory=list)
    seed_evidence_ids: list[str] = Field(min_length=1)
    backward_candidate_count: int = Field(ge=0)
    forward_candidate_count: int = Field(ge=0)
    unique_candidate_count: int = Field(ge=0)
    already_screened_count: int = Field(ge=0)
    duplicate_candidate_count: int = Field(ge=0)
    founder_screened_candidate_count: int = Field(ge=0)
    included_count: int = Field(ge=0)
    excluded_count: int = Field(ge=0)
    prior_appraisal_reuse_count: int = Field(ge=0)
    prior_appraisal_excluded_count: int = Field(ge=0)
    net_new_count: int = Field(ge=0)
    appraisals_completed_count: int = Field(ge=0)
    access_restricted_count: int = Field(ge=0)
    duplicate_resolved_count: int = Field(ge=0)
    appraisal_excluded_count: int = Field(ge=0)
    new_eligible_evidence_ids: list[str]
    input_receipt_checksums_verified: bool
    retrieval_complete: bool
    deduplication_complete: bool
    founder_screening_complete: bool
    appraisal_accounting_complete: bool
    founder_authorized: bool
    ai_decisions_recorded: int = Field(default=0, ge=0)
    molecular_data_access_authorized: bool = False
    outcome_data_access_authorized: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_closure(self) -> CitationPassClosureReceipt:
        if len(self.seed_evidence_ids) != len(set(self.seed_evidence_ids)):
            raise ValueError("citation-pass closure seed IDs must be unique")
        if len(self.new_eligible_evidence_ids) != len(
            set(self.new_eligible_evidence_ids)
        ):
            raise ValueError("citation-pass eligible evidence IDs must be unique")
        if self.unique_candidate_count > (
            self.backward_candidate_count + self.forward_candidate_count
        ):
            raise ValueError("citation-pass closure directional counts do not reconcile")
        if (
            self.already_screened_count
            + self.duplicate_candidate_count
            + self.founder_screened_candidate_count
            != self.unique_candidate_count
        ):
            raise ValueError("citation-pass closure screening counts do not reconcile")
        if (
            self.included_count + self.excluded_count
            != self.founder_screened_candidate_count
        ):
            raise ValueError("citation-pass closure founder decisions do not reconcile")
        if (
            self.prior_appraisal_reuse_count + self.net_new_count
            != self.included_count
        ):
            raise ValueError("citation-pass closure inclusion routing does not reconcile")
        if self.prior_appraisal_excluded_count > self.prior_appraisal_reuse_count:
            raise ValueError("citation-pass prior excluded count is impossible")
        if len(self.prior_appraisal_sha256s) != self.prior_appraisal_reuse_count:
            raise ValueError("citation-pass prior appraisal checksums do not reconcile")
        if any(
            re.fullmatch(r"[a-f0-9]{64}", value) is None
            for value in self.prior_appraisal_sha256s
        ):
            raise ValueError("citation-pass prior appraisal checksum is invalid")
        has_access_accounting = (
            self.access_inventory_sha256 is not None
            and self.appraisal_progress_sha256 is not None
        )
        if has_access_accounting != (self.net_new_count > 0):
            raise ValueError(
                "citation-pass net-new records require inventory and progress checksums"
            )
        accounted_net_new = (
            self.appraisals_completed_count
            + self.access_restricted_count
            + self.duplicate_resolved_count
        )
        if accounted_net_new != self.net_new_count:
            raise ValueError("citation-pass closure appraisal counts do not reconcile")
        eligible_count = (
            self.prior_appraisal_reuse_count
            - self.prior_appraisal_excluded_count
            + self.appraisals_completed_count
            - self.appraisal_excluded_count
            + self.access_restricted_count
        )
        if eligible_count != len(self.new_eligible_evidence_ids):
            raise ValueError("citation-pass eligible evidence count does not reconcile")
        if not all(
            (
                self.input_receipt_checksums_verified,
                self.retrieval_complete,
                self.deduplication_complete,
                self.founder_screening_complete,
                self.appraisal_accounting_complete,
                self.founder_authorized,
            )
        ):
            raise ValueError("citation-pass closure requires complete verified inputs")
        if (
            self.ai_decisions_recorded
            or self.molecular_data_access_authorized
            or self.outcome_data_access_authorized
            or self.scientific_conclusions_drawn
        ):
            raise ValueError(
                "citation-pass closure cannot record AI decisions, data access, or conclusions"
            )
        return self


def load_citation_pass_closure_receipt(path: Path) -> CitationPassClosureReceipt:
    return CitationPassClosureReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_citation_pass_closure_receipt(
    path: Path,
    receipt: CitationPassClosureReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)
