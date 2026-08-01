"""Contracts for the prospective high-quality RNA analytical-use gate."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RNAQualityGateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProspectiveRNAQualityGatePlan(RNAQualityGateModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    assay_selection_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prospective_design_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    uncalibrated_scoring_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    primary_material: str = Field(
        pattern=r"^purified_total_rna_from_homogenized_primary_breast_tumor$"
    )
    primary_error_scope: str = Field(pattern=r"^post_extraction_analytical_error$")
    selected_chemistry_family: str = Field(pattern=r"^stranded_polya_mrna_whole_transcriptome$")
    rna_input_minimum_ng: float = Field(ge=25.0)
    rna_input_maximum_ng: float = Field(le=1000.0)
    rin_minimum: float = Field(ge=8.0, le=10.0)
    require_dnase_treatment: bool
    require_finite_quantity: bool
    require_fragment_analysis: bool
    require_purity_measurement: bool
    require_same_homogenized_rna: bool
    independent_library_preparation: bool
    degraded_or_ffpe_in_primary_scope: bool
    extraction_repeat_in_primary_scope: bool
    failed_input_action: str = Field(
        pattern=r"^exclude_before_scoring_retain_attempted_denominator$"
    )
    lower_quality_contingency_action: str = Field(pattern=r"^separate_future_amendment_and_bridge$")
    official_documentation_urls: list[str] = Field(min_length=2)
    exact_kit_selected: bool
    exact_instrument_selected: bool
    vendor_selected: bool
    external_contact_authorized: bool
    spending_authorized: bool
    procurement_authorized: bool
    specimen_acquisition_authorized: bool
    study_execution_authorized: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    validation_values_accessed: bool
    unresolved_prerequisites: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_gate(self) -> ProspectiveRNAQualityGatePlan:
        if self.rna_input_minimum_ng > self.rna_input_maximum_ng:
            raise ValueError("RNA input range is reversed")
        if not all(
            (
                self.require_dnase_treatment,
                self.require_finite_quantity,
                self.require_fragment_analysis,
                self.require_purity_measurement,
                self.require_same_homogenized_rna,
                self.independent_library_preparation,
            )
        ):
            raise ValueError("high-quality RNA safeguards cannot be weakened")
        if any(
            (
                self.degraded_or_ffpe_in_primary_scope,
                self.extraction_repeat_in_primary_scope,
                self.exact_kit_selected,
                self.exact_instrument_selected,
                self.vendor_selected,
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
            raise ValueError("RNA gate cannot expand scope or authorize external action")
        return self


class ProspectiveRNAQualityGateReceipt(RNAQualityGateModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependency_hashes_verified: bool
    primary_material_frozen: bool
    post_extraction_scope_frozen: bool
    high_quality_rna_range_frozen: bool
    stranded_polya_family_frozen: bool
    degraded_rna_separate: bool
    failed_inputs_retained: bool
    no_external_action_preserved: bool
    decision: str = Field(pattern=r"^prospective_rna_quality_and_chemistry_gate_frozen$")
    study_execution_authorized: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    validation_values_accessed: bool
    limitations: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_receipt(self) -> ProspectiveRNAQualityGateReceipt:
        if not all(
            (
                self.dependency_hashes_verified,
                self.primary_material_frozen,
                self.post_extraction_scope_frozen,
                self.high_quality_rna_range_frozen,
                self.stranded_polya_family_frozen,
                self.degraded_rna_separate,
                self.failed_inputs_retained,
                self.no_external_action_preserved,
            )
        ):
            raise ValueError("RNA-quality gate safeguards are incomplete")
        if any(
            (
                self.study_execution_authorized,
                self.molecular_values_accessed,
                self.outcomes_accessed,
                self.validation_values_accessed,
            )
        ):
            raise ValueError("RNA-quality receipt cannot execute or access study data")
        return self


def load_prospective_rna_quality_gate_plan(
    path: Path,
) -> ProspectiveRNAQualityGatePlan:
    return ProspectiveRNAQualityGatePlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_prospective_rna_quality_gate_receipt(
    path: Path,
    receipt: ProspectiveRNAQualityGateReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("RNA-quality gate receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_prospective_rna_quality_gate_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, ProspectiveRNAQualityGatePlan),
        (receipt_path, ProspectiveRNAQualityGateReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
