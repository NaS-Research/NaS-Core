"""Founder authority and receipt contracts for citation-pass screening decisions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.snapshots import StoredObject

CONFIRMATION_STATEMENT = "I confirm both checksum-bound citation pass 1 packets as written."


class CitationConfirmationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CitationFounderConfirmation(CitationConfirmationModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    first_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    first_appendix_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    second_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    second_appendix_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation_statement: str
    founder_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    founder_name: str = Field(min_length=1)
    reviewer_role: str = Field(pattern=r"^founder_internal_reviewer$")
    confirmed_at: datetime
    founder_authorized: bool
    founder_role_conflict_disclosed: bool

    @model_validator(mode="after")
    def validate_authority(self) -> CitationFounderConfirmation:
        if self.confirmation_statement != CONFIRMATION_STATEMENT:
            raise ValueError("citation confirmation statement is not exact")
        if not self.founder_authorized:
            raise ValueError("citation confirmation requires founder authorization")
        if not self.founder_role_conflict_disclosed:
            raise ValueError("citation confirmation requires founder-role disclosure")
        return self


class CitationDecisionLedgerReceipt(CitationConfirmationModel):
    schema_version: str = "1.0.0"
    decision_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    confirmed_at: datetime
    founder_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    founder_name: str = Field(min_length=1)
    first_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    first_appendix_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    second_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    second_appendix_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_count: int = Field(ge=1)
    included_count: int = Field(ge=0)
    excluded_count: int = Field(ge=0)
    unclear_count: int = Field(ge=0)
    ledger_object: StoredObject
    packet_checksums_verified: bool
    appendix_checksums_verified: bool
    record_coverage_verified: bool
    founder_authorized: bool
    founder_role_conflict_disclosed: bool
    ai_decisions_recorded: int = Field(default=0, ge=0)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_receipt(self) -> CitationDecisionLedgerReceipt:
        if self.included_count + self.excluded_count + self.unclear_count != self.candidate_count:
            raise ValueError("citation decision counts do not reconcile")
        if self.unclear_count:
            raise ValueError("completed citation decision ledger cannot contain unclear records")
        if not all(
            (
                self.packet_checksums_verified,
                self.appendix_checksums_verified,
                self.record_coverage_verified,
                self.founder_authorized,
                self.founder_role_conflict_disclosed,
            )
        ):
            raise ValueError("citation decision ledger requires verified founder authority")
        if self.ai_decisions_recorded or self.scientific_conclusions_drawn:
            raise ValueError("citation decision ledger cannot record AI decisions or conclusions")
        return self


def load_citation_founder_confirmation(path: Path) -> CitationFounderConfirmation:
    return CitationFounderConfirmation.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_citation_decision_ledger_receipt(
    path: Path,
    receipt: CitationDecisionLedgerReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)
