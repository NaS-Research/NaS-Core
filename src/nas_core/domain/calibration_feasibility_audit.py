"""Contracts for source-isolated calibration-feasibility auditing."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationFeasibilityAuditModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PanelMappingStatus(StrEnum):
    VERIFIED_DIRECT_SYMBOLS = "verified_direct_symbols"
    UNRESOLVED_IDENTIFIER_MAPPING = "unresolved_identifier_mapping"


class CalibrationFeasibilityAuditPlan(CalibrationFeasibilityAuditModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    audit_sources_separately: bool
    retain_source_identifiers: bool
    retain_molecular_values: bool
    outcomes_requested: bool
    pooling_authorized: bool
    threshold_estimation_authorized: bool
    classifier_execution_authorized: bool

    @model_validator(mode="after")
    def enforce_source_isolation(self) -> CalibrationFeasibilityAuditPlan:
        if not self.audit_sources_separately:
            raise ValueError("feasibility sources must be audited separately")
        if any(
            (
                self.retain_source_identifiers,
                self.retain_molecular_values,
                self.outcomes_requested,
                self.pooling_authorized,
                self.threshold_estimation_authorized,
                self.classifier_execution_authorized,
            )
        ):
            raise ValueError("audit cannot retain, pool, tune, classify, or access outcomes")
        return self


class SourceFeasibilityProjection(CalibrationFeasibilityAuditModel):
    source_id: str
    artifact_count: int = Field(gt=0)
    sample_count: int = Field(gt=0)
    primary_or_unlabeled_count: int = Field(ge=0)
    replicate_record_count: int = Field(ge=0)
    replicate_group_count: int = Field(ge=0)
    feature_row_count: int = Field(gt=0)
    identifier_namespace: str
    panel_mapping_status: PanelMappingStatus
    direct_pam50_gene_count: int = Field(ge=0, le=50)
    missing_direct_pam50_gene_count: int = Field(ge=0, le=50)
    total_numeric_value_count: int = Field(gt=0)
    nonfinite_value_count: int = Field(ge=0)
    negative_value_count: int = Field(ge=0)
    integer_like_value_count: int = Field(ge=0)
    observed_minimum: float
    observed_maximum: float
    scale_interpretation: str
    usable_for_source_specific_feasibility: bool
    usable_for_primary_calibration: bool


class CalibrationFeasibilityAuditReceipt(CalibrationFeasibilityAuditModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sources: list[SourceFeasibilityProjection] = Field(min_length=2, max_length=2)
    decision: str = Field(
        pattern=r"^feasibility_audit_complete_primary_calibration_not_ready$"
    )
    source_identifiers_retained: bool
    molecular_values_retained: bool
    outcomes_accessed: bool
    sources_pooled: bool
    thresholds_estimated: bool
    classifier_executed: bool
    external_publication_authorized: bool
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_receipt_boundary(self) -> CalibrationFeasibilityAuditReceipt:
        if {source.source_id for source in self.sources} != {
            "ncbi-geo-gse60788",
            "ncbi-geo-gse130397",
        }:
            raise ValueError("receipt requires both feasibility sources")
        if any(source.usable_for_primary_calibration for source in self.sources):
            raise ValueError("excluded feasibility sources cannot become primary calibration")
        if any(
            (
                self.source_identifiers_retained,
                self.molecular_values_retained,
                self.outcomes_accessed,
                self.sources_pooled,
                self.thresholds_estimated,
                self.classifier_executed,
                self.external_publication_authorized,
            )
        ):
            raise ValueError("receipt cannot retain values or claim downstream execution")
        return self


def load_calibration_feasibility_audit_plan(
    path: Path,
) -> CalibrationFeasibilityAuditPlan:
    return CalibrationFeasibilityAuditPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_feasibility_audit_receipt(
    path: Path,
    receipt: CalibrationFeasibilityAuditReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("calibration-feasibility audit receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_calibration_feasibility_audit_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, CalibrationFeasibilityAuditPlan),
        (receipt_path, CalibrationFeasibilityAuditReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
