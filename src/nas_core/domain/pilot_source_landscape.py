"""Contracts for a no-contact prospective-pilot source landscape audit."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PilotSourceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PilotSourceDisposition(StrEnum):
    VERIFIED_ELIGIBLE = "verified_eligible"
    UNRESOLVED = "unresolved"
    INELIGIBLE = "ineligible"


class PilotSourceCandidate(PilotSourceModel):
    source_id: str = Field(pattern=r"^PILOTSRC-[0-9]{3}$")
    provider: str = Field(min_length=1)
    provider_class: str = Field(
        pattern=r"^(public_biospecimen_network|commercial_supplier|data_repository)$"
    )
    public_urls: list[str] = Field(min_length=1)
    publicly_described_material: str = Field(min_length=1)
    primary_breast_tumor_material_publicly_supported: bool
    purified_total_rna_publicly_supported: bool
    thirty_independent_sources_publicly_confirmed: bool
    rin_at_least_8_publicly_confirmed: bool
    same_homogenized_rna_aliquots_publicly_confirmed: bool
    lawful_research_use_process_publicly_described: bool
    nonoverlap_can_be_verified_without_identifiers: bool
    application_or_contact_required: bool
    spending_or_purchase_required: bool
    disposition: PilotSourceDisposition
    blockers: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_eligibility(self) -> PilotSourceCandidate:
        eligibility = (
            self.primary_breast_tumor_material_publicly_supported,
            self.purified_total_rna_publicly_supported,
            self.thirty_independent_sources_publicly_confirmed,
            self.rin_at_least_8_publicly_confirmed,
            self.same_homogenized_rna_aliquots_publicly_confirmed,
            self.lawful_research_use_process_publicly_described,
            self.nonoverlap_can_be_verified_without_identifiers,
        )
        if self.disposition is PilotSourceDisposition.VERIFIED_ELIGIBLE and not all(eligibility):
            raise ValueError("verified source must satisfy every public-evidence criterion")
        return self


class PilotSourceLandscapePlan(PilotSourceModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    pilot_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    rna_quality_gate_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    audit_date: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    candidates: list[PilotSourceCandidate] = Field(min_length=5)
    selected_source_id: str | None
    source_selection_authorized: bool
    external_contact_authorized: bool
    application_submission_authorized: bool
    spending_authorized: bool
    procurement_authorized: bool
    specimen_acquisition_authorized: bool
    study_execution_authorized: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    validation_values_accessed: bool

    @model_validator(mode="after")
    def enforce_no_contact_audit(self) -> PilotSourceLandscapePlan:
        ids = [item.source_id for item in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("pilot source IDs must be unique")
        if self.selected_source_id is not None:
            raise ValueError("no-contact landscape cannot select a source")
        if any(
            (
                self.source_selection_authorized,
                self.external_contact_authorized,
                self.application_submission_authorized,
                self.spending_authorized,
                self.procurement_authorized,
                self.specimen_acquisition_authorized,
                self.study_execution_authorized,
                self.molecular_values_accessed,
                self.outcomes_accessed,
                self.validation_values_accessed,
            )
        ):
            raise ValueError("landscape audit cannot authorize external action or access")
        return self


class PilotSourceLandscapeReceipt(PilotSourceModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependency_hashes_verified: bool
    candidate_count: int = Field(ge=5)
    verified_eligible_count: int = Field(ge=0)
    unresolved_count: int = Field(ge=0)
    ineligible_count: int = Field(ge=0)
    selected_source_id: str | None
    no_contact_preserved: bool
    decision: str = Field(pattern=r"^no_verified_source_external_due_diligence_required$")
    external_action_authorized: bool
    study_execution_authorized: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    validation_values_accessed: bool
    limitations: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def reconcile_receipt(self) -> PilotSourceLandscapeReceipt:
        if (
            self.candidate_count
            != self.verified_eligible_count + self.unresolved_count + self.ineligible_count
        ):
            raise ValueError("source landscape counts do not reconcile")
        if self.verified_eligible_count != 0 or self.selected_source_id is not None:
            raise ValueError("current public evidence does not verify a source")
        if not self.dependency_hashes_verified or not self.no_contact_preserved:
            raise ValueError("source landscape safeguards are incomplete")
        if any(
            (
                self.external_action_authorized,
                self.study_execution_authorized,
                self.molecular_values_accessed,
                self.outcomes_accessed,
                self.validation_values_accessed,
            )
        ):
            raise ValueError("source landscape receipt cannot authorize action or access")
        return self


def load_pilot_source_landscape_plan(path: Path) -> PilotSourceLandscapePlan:
    return PilotSourceLandscapePlan.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def write_pilot_source_landscape_receipt(
    path: Path,
    receipt: PilotSourceLandscapeReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("pilot source landscape receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_pilot_source_landscape_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, PilotSourceLandscapePlan),
        (receipt_path, PilotSourceLandscapeReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
