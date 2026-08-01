"""Field-isolated processed-expression matrix audit contracts."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MatrixAuditModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MatrixAuditDecision(StrEnum):
    PASS = "pass"
    CHANGES_REQUIRED = "changes_required"


class GSE81538MatrixAuditPlan(MatrixAuditModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_id: str = Field(pattern=r"^ncbi-geo-gse81538$")
    source_accession: str = Field(pattern=r"^GSE81538$")
    object_key: str = Field(pattern=r"^raw/[a-z0-9._/-]+$")
    acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_protocol_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_compressed_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_compressed_bytes: int = Field(gt=0)
    expected_gene_rows: int = Field(gt=0)
    expected_sample_columns: int = Field(gt=0)
    sample_column_prefix: str = Field(pattern=r"^T$")
    declared_quantity: str = Field(pattern=r"^FPKM$")
    declared_transform: str = Field(pattern=r"^log2\(FPKM \+ 0\.1\)$")
    expected_zero_floor: float
    floor_absolute_tolerance: float = Field(gt=0)
    official_processing_statement_url: str = Field(pattern=r"^https://")
    outcome_fields_permitted: bool
    classifier_execution_permitted: bool

    @model_validator(mode="after")
    def enforce_field_isolation(self) -> GSE81538MatrixAuditPlan:
        if self.outcome_fields_permitted or self.classifier_execution_permitted:
            raise ValueError("matrix audit cannot access outcomes or execute classifier")
        return self


class GSE81538MatrixAuditReceipt(MatrixAuditModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    source_id: str = Field(pattern=r"^ncbi-geo-gse81538$")
    source_accession: str = Field(pattern=r"^GSE81538$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    audited_at: datetime
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    object_sha256_verified: bool
    compressed_bytes: int = Field(gt=0)
    expected_gene_row_count: int = Field(gt=0)
    gene_row_count: int = Field(gt=0)
    unique_gene_identifier_count: int = Field(gt=0)
    duplicate_gene_identifier_count: int = Field(ge=0)
    expected_sample_column_count: int = Field(gt=0)
    sample_column_count: int = Field(gt=0)
    sample_header_sequence_verified: bool
    total_measurement_count: int = Field(gt=0)
    finite_measurement_count: int = Field(ge=0)
    missing_measurement_count: int = Field(ge=0)
    nonfinite_measurement_count: int = Field(ge=0)
    minimum_value: float
    maximum_value: float
    expected_zero_floor: float
    zero_floor_count: int = Field(ge=0)
    values_below_expected_floor: int = Field(ge=0)
    official_transform_declared: str = Field(pattern=r"^log2\(FPKM \+ 0\.1\)$")
    observed_floor_matches_declared_transform: bool
    input_scale_verified: bool
    required_pam50_gene_count: int = Field(gt=0)
    resolved_pam50_gene_count: int = Field(ge=0)
    missing_pam50_genes: list[str]
    duplicate_pam50_mappings: list[str]
    historical_aliases_applied: dict[str, str]
    decision: MatrixAuditDecision
    limitations: list[str] = Field(min_length=1)
    molecular_values_parsed: bool
    sample_rows_retained: bool
    outcome_values_accessed: bool
    classifier_executed: bool
    reference_vector_materialized: bool
    reference_locked: bool

    @model_validator(mode="after")
    def reconcile_audit(self) -> GSE81538MatrixAuditReceipt:
        passed = all(
            (
                self.object_sha256_verified,
                self.gene_row_count == self.expected_gene_row_count,
                self.sample_header_sequence_verified,
                self.sample_column_count == self.expected_sample_column_count,
                self.finite_measurement_count == self.total_measurement_count,
                self.missing_measurement_count == 0,
                self.nonfinite_measurement_count == 0,
                self.duplicate_gene_identifier_count == 0,
                self.observed_floor_matches_declared_transform,
                self.input_scale_verified,
                self.resolved_pam50_gene_count == self.required_pam50_gene_count,
                not self.missing_pam50_genes,
                not self.duplicate_pam50_mappings,
            )
        )
        expected = MatrixAuditDecision.PASS if passed else MatrixAuditDecision.CHANGES_REQUIRED
        if self.decision is not expected:
            raise ValueError("matrix-audit decision does not reconcile")
        if not self.molecular_values_parsed:
            raise ValueError("matrix audit must disclose molecular-value parsing")
        if any(
            (
                self.sample_rows_retained,
                self.outcome_values_accessed,
                self.classifier_executed,
                self.reference_vector_materialized,
                self.reference_locked,
            )
        ):
            raise ValueError("matrix audit cannot retain rows, outcomes, or method results")
        return self


def load_matrix_audit_plan(path: Path) -> GSE81538MatrixAuditPlan:
    return GSE81538MatrixAuditPlan.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_matrix_audit_receipt(path: Path) -> GSE81538MatrixAuditReceipt:
    return GSE81538MatrixAuditReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_matrix_audit_receipt(path: Path, receipt: GSE81538MatrixAuditReceipt) -> None:
    if path.exists():
        raise FileExistsError("matrix audit receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_matrix_audit_schemas(plan_path: Path, receipt_path: Path) -> None:
    for path, model in (
        (plan_path, GSE81538MatrixAuditPlan),
        (receipt_path, GSE81538MatrixAuditReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
