"""Founder authorization and queue contracts for evidence-cap amendments."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.snapshots import StoredObject

APPROVAL_STATEMENT = "I approve evidence-cap amendment 0.2.5 as written."


class EvidenceAmendmentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceCapAmendmentApproval(EvidenceAmendmentModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    prior_protocol_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    amendment_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    amendment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reconciliation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    reconciliation_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_statement: str
    founder_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    founder_name: str = Field(min_length=1)
    approved_at: datetime
    founder_authorized: bool
    uncapped_saturation_inventory_authorized: bool
    core_synthesis_maximum: int = Field(ge=1, le=30)
    molecular_data_access_authorized: bool = False
    outcome_data_access_authorized: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_authorization(self) -> EvidenceCapAmendmentApproval:
        if self.approval_statement != APPROVAL_STATEMENT:
            raise ValueError("evidence-cap approval statement is not exact")
        if self.prior_protocol_version != "0.2.4" or self.amendment_version != "0.2.5":
            raise ValueError("evidence-cap approval is bound to protocol 0.2.5")
        if not self.founder_authorized:
            raise ValueError("evidence-cap amendment requires founder authorization")
        if not self.uncapped_saturation_inventory_authorized:
            raise ValueError("approval must authorize the uncapped saturation inventory")
        if (
            self.molecular_data_access_authorized
            or self.outcome_data_access_authorized
            or self.scientific_conclusions_drawn
        ):
            raise ValueError(
                "evidence-cap approval cannot authorize data access or conclusions"
            )
        return self


class CitationAppraisalRoute(StrEnum):
    REPOSITORY_CANDIDATE = "repository_candidate"
    ACCESS_CHECK_REQUIRED = "access_check_required"
    REUSE_PRIOR_APPRAISAL = "reuse_prior_appraisal"


class CitationAppraisalQueueRecord(EvidenceAmendmentModel):
    record_key: str = Field(pattern=r"^[A-Z]+:.+$")
    title: str = Field(min_length=1)
    pmid: str | None = Field(default=None, pattern=r"^[0-9]+$")
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    doi: str | None = Field(default=None, min_length=1)
    route: CitationAppraisalRoute
    matched_screening_id: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    founder_inclusion_preserved: bool
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_route(self) -> CitationAppraisalQueueRecord:
        if self.route is CitationAppraisalRoute.REPOSITORY_CANDIDATE and not self.pmcid:
            raise ValueError("repository candidate requires a PMCID")
        if self.route is CitationAppraisalRoute.REUSE_PRIOR_APPRAISAL:
            if self.matched_screening_id is None:
                raise ValueError("prior-appraisal route requires a screening ID")
        elif self.matched_screening_id is not None:
            raise ValueError("net-new queue record cannot reference a prior appraisal")
        if not self.founder_inclusion_preserved or self.scientific_conclusions_drawn:
            raise ValueError("queue routing cannot alter founder decisions or draw conclusions")
        return self


class EvidenceCapAmendmentActivationReceipt(EvidenceAmendmentModel):
    schema_version: str = "1.0.0"
    activation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    prior_protocol_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    active_protocol_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    approved_at: datetime
    activated_at: datetime
    founder_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    amendment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reconciliation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    reconciliation_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_inclusion_count: int = Field(ge=1)
    repository_candidate_count: int = Field(ge=0)
    access_check_required_count: int = Field(ge=0)
    prior_appraisal_reuse_count: int = Field(ge=0)
    net_new_count: int = Field(ge=0)
    core_synthesis_maximum: int = Field(ge=1, le=30)
    queue_object: StoredObject
    amendment_checksum_verified: bool
    reconciliation_checksum_verified: bool
    count_invariants_verified: bool
    founder_authorized: bool
    uncapped_saturation_inventory_active: bool
    founder_decisions_changed: int = Field(default=0, ge=0)
    molecular_data_access_authorized: bool = False
    outcome_data_access_authorized: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_activation(self) -> EvidenceCapAmendmentActivationReceipt:
        if (
            self.repository_candidate_count
            + self.access_check_required_count
            != self.net_new_count
        ):
            raise ValueError("net-new access routes do not reconcile")
        if (
            self.net_new_count + self.prior_appraisal_reuse_count
            != self.confirmed_inclusion_count
        ):
            raise ValueError("activation queue does not cover every confirmed inclusion")
        if not all(
            (
                self.amendment_checksum_verified,
                self.reconciliation_checksum_verified,
                self.count_invariants_verified,
                self.founder_authorized,
                self.uncapped_saturation_inventory_active,
            )
        ):
            raise ValueError("evidence-cap activation requires verified authority")
        if (
            self.founder_decisions_changed
            or self.molecular_data_access_authorized
            or self.outcome_data_access_authorized
            or self.scientific_conclusions_drawn
        ):
            raise ValueError(
                "evidence-cap activation cannot change decisions, access data, or conclude"
            )
        return self


class CitationPassAppraisalQueueReceipt(EvidenceAmendmentModel):
    """Route a later founder-confirmed citation pass under the active amendment."""

    schema_version: str = "1.0.0"
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pass_number: int = Field(ge=2)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    queued_at: datetime
    founder_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    decision_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reconciliation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    reconciliation_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    active_amendment_activation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    active_amendment_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    active_protocol_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    confirmed_inclusion_count: int = Field(ge=1)
    repository_candidate_count: int = Field(ge=0)
    access_check_required_count: int = Field(ge=0)
    prior_appraisal_reuse_count: int = Field(ge=0)
    net_new_count: int = Field(ge=0)
    core_synthesis_maximum: int = Field(ge=1, le=30)
    queue_object: StoredObject
    decision_ledger_checksum_verified: bool
    reconciliation_checksum_verified: bool
    active_amendment_verified: bool
    count_invariants_verified: bool
    founder_authorized: bool
    uncapped_saturation_inventory_active: bool
    founder_decisions_changed: int = Field(default=0, ge=0)
    molecular_data_access_authorized: bool = False
    outcome_data_access_authorized: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_queue(self) -> CitationPassAppraisalQueueReceipt:
        if (
            self.repository_candidate_count
            + self.access_check_required_count
            != self.net_new_count
        ):
            raise ValueError("later-pass net-new access routes do not reconcile")
        if (
            self.net_new_count + self.prior_appraisal_reuse_count
            != self.confirmed_inclusion_count
        ):
            raise ValueError("later-pass queue does not cover every inclusion")
        if not all(
            (
                self.decision_ledger_checksum_verified,
                self.reconciliation_checksum_verified,
                self.active_amendment_verified,
                self.count_invariants_verified,
                self.founder_authorized,
                self.uncapped_saturation_inventory_active,
            )
        ):
            raise ValueError("later-pass queue requires verified founder authority")
        if (
            self.founder_decisions_changed
            or self.molecular_data_access_authorized
            or self.outcome_data_access_authorized
            or self.scientific_conclusions_drawn
        ):
            raise ValueError(
                "later-pass routing cannot change decisions, access data, or conclude"
            )
        return self


def load_evidence_cap_amendment_approval(
    path: Path,
) -> EvidenceCapAmendmentApproval:
    return EvidenceCapAmendmentApproval.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_evidence_cap_amendment_activation_receipt(
    path: Path,
) -> EvidenceCapAmendmentActivationReceipt:
    return EvidenceCapAmendmentActivationReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_evidence_cap_amendment_activation_receipt(
    path: Path,
    receipt: EvidenceCapAmendmentActivationReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_pass_appraisal_queue_receipt(
    path: Path,
) -> CitationPassAppraisalQueueReceipt:
    return CitationPassAppraisalQueueReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_citation_pass_appraisal_queue_receipt(
    path: Path,
    receipt: CitationPassAppraisalQueueReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def load_citation_access_queue_receipt(
    path: Path,
) -> EvidenceCapAmendmentActivationReceipt | CitationPassAppraisalQueueReceipt:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "pass_number" in payload:
        return CitationPassAppraisalQueueReceipt.model_validate(payload)
    return EvidenceCapAmendmentActivationReceipt.model_validate(payload)
