"""Contracts for a nonexecuting excluded prospective calibration pilot."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProspectivePilotModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExcludedProspectivePilotPlan(ProspectivePilotModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    rna_quality_gate_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    planning_bundle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prospective_design_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    attempted_pair_target: int = Field(ge=30, le=30)
    independent_biological_source_target: int = Field(ge=30, le=30)
    measurements_per_pair: int = Field(ge=2, le=2)
    pilot_role: str = Field(pattern=r"^excluded_feasibility_pilot$")
    pair_unit: str = Field(pattern=r"^same_homogenized_rna_independent_libraries$")
    immutable_identifier_levels: list[str] = Field(min_length=5)
    randomization_factors: list[str] = Field(min_length=3)
    blinding_requirements: list[str] = Field(min_length=2)
    control_requirements: list[str] = Field(min_length=2)
    retained_denominators: list[str] = Field(min_length=8)
    permitted_estimates: list[str] = Field(min_length=5)
    prohibited_uses: list[str] = Field(min_length=5)
    nonoverlap_populations: list[str] = Field(min_length=4)
    raw_object_key_prefix: str = Field(pattern=r"^raw/nas-brca-002/prospective-pilot/")
    derived_object_key_prefix: str = Field(pattern=r"^derived/nas-brca-002/prospective-pilot/")
    checksums_required: bool
    atomic_manifest_publish_required: bool
    pilot_specimens_permanently_excluded_from_primary: bool
    pilot_specimens_permanently_excluded_from_validation: bool
    final_pair_count_authorized: bool
    threshold_selection_authorized: bool
    external_contact_authorized: bool
    spending_authorized: bool
    procurement_authorized: bool
    specimen_acquisition_authorized: bool
    study_execution_authorized: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    validation_values_accessed: bool

    @model_validator(mode="after")
    def enforce_excluded_pilot(self) -> ExcludedProspectivePilotPlan:
        if len(set(self.immutable_identifier_levels)) != len(self.immutable_identifier_levels):
            raise ValueError("pilot identifier levels must be unique")
        if not all(
            (
                self.checksums_required,
                self.atomic_manifest_publish_required,
                self.pilot_specimens_permanently_excluded_from_primary,
                self.pilot_specimens_permanently_excluded_from_validation,
            )
        ):
            raise ValueError("pilot provenance and exclusion safeguards are mandatory")
        if any(
            (
                self.final_pair_count_authorized,
                self.threshold_selection_authorized,
                self.external_contact_authorized,
                self.spending_authorized,
                self.procurement_authorized,
                self.specimen_acquisition_authorized,
                self.study_execution_authorized,
                self.molecular_values_accessed,
                self.outcomes_accessed,
                self.validation_values_accessed,
            )
        ):
            raise ValueError("pilot plan cannot authorize external action or inference")
        return self


class ExcludedProspectivePilotPlanReceipt(ProspectivePilotModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependency_hashes_verified: bool
    attempted_pair_target: int = Field(ge=30, le=30)
    planned_measurement_count: int = Field(ge=60, le=60)
    independent_source_target: int = Field(ge=30, le=30)
    randomization_frozen: bool
    lineage_frozen: bool
    denominator_accounting_frozen: bool
    immutable_storage_contract_frozen: bool
    permanent_exclusion_frozen: bool
    no_external_action_preserved: bool
    decision: str = Field(pattern=r"^excluded_prospective_pilot_plan_frozen$")
    study_execution_authorized: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    validation_values_accessed: bool
    limitations: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_receipt(self) -> ExcludedProspectivePilotPlanReceipt:
        if not all(
            (
                self.dependency_hashes_verified,
                self.randomization_frozen,
                self.lineage_frozen,
                self.denominator_accounting_frozen,
                self.immutable_storage_contract_frozen,
                self.permanent_exclusion_frozen,
                self.no_external_action_preserved,
            )
        ):
            raise ValueError("excluded-pilot planning safeguards are incomplete")
        if any(
            (
                self.study_execution_authorized,
                self.molecular_values_accessed,
                self.outcomes_accessed,
                self.validation_values_accessed,
            )
        ):
            raise ValueError("pilot-plan receipt cannot execute or access study data")
        return self


def load_excluded_prospective_pilot_plan(path: Path) -> ExcludedProspectivePilotPlan:
    return ExcludedProspectivePilotPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_excluded_prospective_pilot_plan_receipt(
    path: Path,
    receipt: ExcludedProspectivePilotPlanReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("prospective pilot receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_excluded_prospective_pilot_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, ExcludedProspectivePilotPlan),
        (receipt_path, ExcludedProspectivePilotPlanReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
