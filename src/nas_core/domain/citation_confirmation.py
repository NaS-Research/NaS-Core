"""Founder authority and receipt contracts for citation-pass screening decisions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.literature import ScreeningDecision, ScreeningExclusionReason
from nas_core.domain.snapshots import StoredObject

CONFIRMATION_STATEMENT = "I confirm both checksum-bound citation pass 1 packets as written."


def citation_confirmation_statement(pass_number: int) -> str:
    return (
        f"I confirm both checksum-bound citation pass {pass_number} "
        "packets as written."
    )


def single_citation_confirmation_statement(pass_number: int) -> str:
    return (
        f"I confirm the proposed citation pass {pass_number} decisions "
        "in the checksum-bound packet."
    )


class CitationConfirmationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CitationFounderConfirmation(CitationConfirmationModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    first_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    first_appendix_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    second_packet_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    second_appendix_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    confirmation_statement: str
    founder_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    founder_name: str = Field(min_length=1)
    reviewer_role: str = Field(pattern=r"^founder_internal_reviewer$")
    confirmed_at: datetime
    founder_authorized: bool
    founder_role_conflict_disclosed: bool

    @model_validator(mode="after")
    def validate_authority(self) -> CitationFounderConfirmation:
        second_packet_present = self.second_packet_sha256 is not None
        second_appendix_present = self.second_appendix_sha256 is not None
        if second_packet_present != second_appendix_present:
            raise ValueError(
                "citation confirmation requires both or neither second-packet hashes"
            )
        expected_statement = (
            citation_confirmation_statement(self.pass_number)
            if second_packet_present
            else single_citation_confirmation_statement(self.pass_number)
        )
        if self.confirmation_statement != expected_statement:
            raise ValueError("citation confirmation statement is not exact")
        if not self.founder_authorized:
            raise ValueError("citation confirmation requires founder authorization")
        if not self.founder_role_conflict_disclosed:
            raise ValueError("citation confirmation requires founder-role disclosure")
        return self


class CitationDecisionLedgerRecord(CitationConfirmationModel):
    record_key: str = Field(pattern=r"^[A-Z]+:.+$")
    rank: int = Field(ge=1)
    title: str = Field(min_length=1)
    pmid: str | None = Field(default=None, pattern=r"^[0-9]+$")
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    doi: str | None = Field(default=None, min_length=1)
    decision: ScreeningDecision
    exclusion_reason: ScreeningExclusionReason | None = None
    reviewer_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reviewer_name: str = Field(min_length=1)
    reviewer_role: str = Field(pattern=r"^founder_internal_reviewer$")
    decided_at: datetime
    founder_authorized: bool
    ai_decision: bool

    @model_validator(mode="after")
    def validate_decision(self) -> CitationDecisionLedgerRecord:
        if self.decision not in {ScreeningDecision.INCLUDE, ScreeningDecision.EXCLUDE}:
            raise ValueError("citation decision ledger cannot contain pending or unclear")
        if (self.decision is ScreeningDecision.EXCLUDE) != (
            self.exclusion_reason is not None
        ):
            raise ValueError("only excluded citation decisions require an exclusion reason")
        if not self.founder_authorized or self.ai_decision:
            raise ValueError("citation ledger requires founder, not AI, decisions")
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
    second_packet_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    second_appendix_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    candidate_count: int = Field(ge=0)
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
        if (self.second_packet_sha256 is None) != (
            self.second_appendix_sha256 is None
        ):
            raise ValueError(
                "citation decision ledger requires both or neither second-packet hashes"
            )
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


def load_citation_decision_ledger_receipt(
    path: Path,
) -> CitationDecisionLedgerReceipt:
    return CitationDecisionLedgerReceipt.model_validate(
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
