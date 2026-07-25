"""Typed contracts for reconciling founder-confirmed citation inclusions."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.snapshots import StoredObject


class CitationReconciliationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CitationInclusionDisposition(StrEnum):
    ACTIVE_INVENTORY = "active_inventory"
    PRIOR_APPRAISAL = "prior_appraisal"
    NET_NEW = "net_new"


class CitationInclusionReconciliationRecord(CitationReconciliationModel):
    record_key: str = Field(pattern=r"^[A-Z]+:.+$")
    title: str = Field(min_length=1)
    pmid: str | None = Field(default=None, pattern=r"^[0-9]+$")
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    doi: str | None = Field(default=None, min_length=1)
    disposition: CitationInclusionDisposition
    matched_identifiers: list[str]
    matched_screening_id: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    matched_record_key: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_disposition(self) -> CitationInclusionReconciliationRecord:
        if self.disposition is CitationInclusionDisposition.NET_NEW:
            if (
                self.matched_identifiers
                or self.matched_screening_id is not None
                or self.matched_record_key is not None
            ):
                raise ValueError("net-new citation cannot contain an existing-record match")
        elif not self.matched_identifiers or self.matched_screening_id is None:
            raise ValueError("reused citation requires an exact identifier match")
        if (
            self.disposition is CitationInclusionDisposition.ACTIVE_INVENTORY
            and self.matched_record_key is None
        ):
            raise ValueError("active-inventory match requires its record key")
        if (
            self.disposition is CitationInclusionDisposition.PRIOR_APPRAISAL
            and self.matched_record_key is not None
        ):
            raise ValueError("prior-appraisal match cannot claim an inventory record key")
        return self


class CitationInclusionReconciliationReceipt(CitationReconciliationModel):
    schema_version: str = "1.0.0"
    reconciliation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=1)
    decision_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    reconciled_at: datetime
    confirmed_inclusion_count: int = Field(ge=0)
    active_inventory_match_count: int = Field(ge=0)
    prior_appraisal_match_count: int = Field(ge=0)
    net_new_count: int = Field(ge=0)
    inventory_record_count: int = Field(ge=1)
    prior_appraisal_count: int = Field(ge=0)
    reconciliation_object: StoredObject
    decision_ledger_checksum_verified: bool
    exact_identifier_matching_only: bool
    count_invariants_verified: bool
    founder_decisions_changed: int = Field(default=0, ge=0)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_receipt(self) -> CitationInclusionReconciliationReceipt:
        routed = (
            self.active_inventory_match_count
            + self.prior_appraisal_match_count
            + self.net_new_count
        )
        if routed != self.confirmed_inclusion_count:
            raise ValueError("citation reconciliation counts do not reconcile")
        if not all(
            (
                self.decision_ledger_checksum_verified,
                self.exact_identifier_matching_only,
                self.count_invariants_verified,
            )
        ):
            raise ValueError("citation reconciliation requires verified invariants")
        if self.founder_decisions_changed or self.scientific_conclusions_drawn:
            raise ValueError(
                "citation reconciliation cannot change decisions or draw conclusions"
            )
        return self


def write_citation_inclusion_reconciliation_receipt(
    path: Path,
    receipt: CitationInclusionReconciliationReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_inclusion_reconciliation_receipt(
    path: Path,
) -> CitationInclusionReconciliationReceipt:
    return CitationInclusionReconciliationReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
