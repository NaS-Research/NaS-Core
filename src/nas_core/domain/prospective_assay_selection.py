"""Contracts for a nonexecuting prospective primary-calibration assay selection."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AssaySelectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssayCandidateDisposition(StrEnum):
    SELECTED_FAMILY = "selected_family"
    CONDITIONAL_CONTINGENCY = "conditional_contingency"
    NOT_SELECTED_PRIMARY = "not_selected_primary"


class ProspectiveAssayCandidate(AssaySelectionModel):
    candidate_id: str = Field(pattern=r"^ASSAY-[0-9]{3}$")
    assay_family: str = Field(min_length=1)
    measurement_scope: str = Field(min_length=1)
    repeat_architecture_compatible: bool
    full_pam50_panel_feasible: bool
    high_quality_rna_compatible: bool
    degraded_or_ffpe_compatible: bool
    fixed_reference_bridge_status: str = Field(
        pattern=r"^(requires_platform_conformance|materially_different_measurement_family)$"
    )
    disposition: AssayCandidateDisposition
    rationale: list[str] = Field(min_length=1)
    official_documentation_urls: list[str] = Field(min_length=1)


class ProspectiveAssaySelectionPlan(AssaySelectionModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    prospective_design_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    planning_bundle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    planning_activation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    retrospective_bridge_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    uncalibrated_scoring_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    intended_use: str = Field(min_length=1)
    primary_repeat_architecture: str = Field(min_length=1)
    candidates: list[ProspectiveAssayCandidate] = Field(min_length=3)
    selected_candidate_id: str
    selected_platform_family: str
    selection_scope: str = Field(pattern=r"^planning_only_platform_family$")
    exact_library_chemistry_selected: bool
    exact_instrument_selected: bool
    vendor_selected: bool
    procurement_authorized: bool
    spending_authorized: bool
    specimen_acquisition_authorized: bool
    study_execution_authorized: bool
    external_contact_authorized: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    validation_values_accessed: bool
    threshold_selection_authorized: bool
    unresolved_prerequisites: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_planning_boundary(self) -> ProspectiveAssaySelectionPlan:
        ids = [item.candidate_id for item in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("assay candidate IDs must be unique")
        selected = [
            item
            for item in self.candidates
            if item.disposition is AssayCandidateDisposition.SELECTED_FAMILY
        ]
        if len(selected) != 1 or selected[0].candidate_id != self.selected_candidate_id:
            raise ValueError("exactly one assay family must be selected")
        if not selected[0].repeat_architecture_compatible:
            raise ValueError("selected family must support the fixed repeat architecture")
        if not selected[0].full_pam50_panel_feasible:
            raise ValueError("selected family must support the full PAM50 panel")
        if any(
            (
                self.exact_library_chemistry_selected,
                self.exact_instrument_selected,
                self.vendor_selected,
                self.procurement_authorized,
                self.spending_authorized,
                self.specimen_acquisition_authorized,
                self.study_execution_authorized,
                self.external_contact_authorized,
                self.molecular_values_accessed,
                self.outcomes_accessed,
                self.validation_values_accessed,
                self.threshold_selection_authorized,
            )
        ):
            raise ValueError("planning selection cannot authorize procurement or execution")
        return self


class ProspectiveAssaySelectionReceipt(AssaySelectionModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependency_hashes_verified: bool
    candidate_count: int = Field(ge=3)
    selected_candidate_id: str
    selected_platform_family: str
    selection_scope: str = Field(pattern=r"^planning_only_platform_family$")
    exact_chemistry_unresolved: bool
    exact_instrument_unresolved: bool
    platform_conformance_required: bool
    no_external_action_preserved: bool
    decision: str = Field(pattern=r"^prospective_assay_family_selected_for_planning$")
    study_execution_authorized: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    validation_values_accessed: bool
    limitations: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_receipt(self) -> ProspectiveAssaySelectionReceipt:
        if not all(
            (
                self.dependency_hashes_verified,
                self.exact_chemistry_unresolved,
                self.exact_instrument_unresolved,
                self.platform_conformance_required,
                self.no_external_action_preserved,
            )
        ):
            raise ValueError("assay-family selection safeguards are incomplete")
        if any(
            (
                self.study_execution_authorized,
                self.molecular_values_accessed,
                self.outcomes_accessed,
                self.validation_values_accessed,
            )
        ):
            raise ValueError("assay-family receipt cannot execute or access study data")
        return self


def load_prospective_assay_selection_plan(
    path: Path,
) -> ProspectiveAssaySelectionPlan:
    return ProspectiveAssaySelectionPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_prospective_assay_selection_receipt(
    path: Path,
    receipt: ProspectiveAssaySelectionReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("prospective assay-selection receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_prospective_assay_selection_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, ProspectiveAssaySelectionPlan),
        (receipt_path, ProspectiveAssaySelectionReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
