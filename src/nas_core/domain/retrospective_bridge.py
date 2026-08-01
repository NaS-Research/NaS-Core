"""Contracts for the performance-blind retrospective RNA-seq bridge."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetrospectiveBridgeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RetrospectiveExpressionBridgePlan(RetrospectiveBridgeModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_import_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_construction_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    metadata_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    numerical_conformance_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    official_gdc_pipeline_url: str = Field(
        pattern=r"^https://docs\.gdc\.cancer\.gov/"
    )
    official_gse96058_metadata_url: str = Field(
        pattern=r"^https://www\.ncbi\.nlm\.nih\.gov/geo/query/acc\.cgi\?acc=GSM[0-9]+$"
    )
    panel: str = Field(pattern=r"^PAM50_historical_50$")
    required_gene_count: int = Field(ge=50, le=50)
    tcga_source: str = Field(pattern=r"^GDC_TCGA_BRCA_STAR_Counts$")
    tcga_input_field: str = Field(pattern=r"^fpkm_unstranded$")
    tcga_transform: str = Field(pattern=r"^log2_fpkm_plus_0_1$")
    gse96058_input_representation: str = Field(
        pattern=r"^source_supplied_log2_fpkm_plus_0_1$"
    )
    gse96058_transform: str = Field(pattern=r"^consume_unchanged$")
    reference_object_key: str = Field(pattern=r"^derived/nas-brca-002/")
    reference_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centering_operation: str = Field(pattern=r"^subtract_fixed_reference_gene_wise$")
    scoring_operation: str = Field(pattern=r"^spearman_to_five_fixed_centroids$")
    numerical_precision: str = Field(pattern=r"^IEEE_754_binary64$")
    duplicate_mapping_action: str = Field(pattern=r"^abstain$")
    missing_gene_action: str = Field(pattern=r"^abstain$")
    nonfinite_value_action: str = Field(pattern=r"^abstain$")
    test_cohort_centering_allowed: bool
    validation_adaptation_allowed: bool
    outcome_guided_tuning_allowed: bool
    classifier_execution_authorized: bool
    validation_molecular_access_authorized: bool
    outcome_access_authorized: bool
    prospective_assay_selected: bool
    external_publication_authorized: bool

    @model_validator(mode="after")
    def enforce_performance_blind_bridge(self) -> RetrospectiveExpressionBridgePlan:
        if any(
            (
                self.test_cohort_centering_allowed,
                self.validation_adaptation_allowed,
                self.outcome_guided_tuning_allowed,
                self.classifier_execution_authorized,
                self.validation_molecular_access_authorized,
                self.outcome_access_authorized,
                self.prospective_assay_selected,
                self.external_publication_authorized,
            )
        ):
            raise ValueError("bridge planning cannot adapt, execute, access, or publish")
        return self


class RetrospectiveExpressionBridgeReceipt(RetrospectiveBridgeModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_hashes_verified: bool
    reference_object_verified: bool
    reference_gene_count: int = Field(ge=50, le=50)
    centroid_gene_count: int = Field(ge=50, le=50)
    centroid_subtype_count: int = Field(ge=5, le=5)
    tcga_input_field: str
    tcga_transform: str
    gse96058_transform: str
    centering_operation: str
    scoring_operation: str
    decision: str = Field(pattern=r"^retrospective_research_bridge_frozen$")
    reference_locked_for_retrospective_bridge: bool
    centroids_locked_for_retrospective_bridge: bool
    performance_blind_validation_bridge_frozen: bool
    prospective_primary_assay_selected: bool
    primary_calibration_ready: bool
    classifier_executed: bool
    validation_molecular_values_accessed: bool
    outcomes_accessed: bool
    external_publication_authorized: bool
    limitations: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_research_only_receipt(self) -> RetrospectiveExpressionBridgeReceipt:
        if not all(
            (
                self.evidence_hashes_verified,
                self.reference_object_verified,
                self.reference_locked_for_retrospective_bridge,
                self.centroids_locked_for_retrospective_bridge,
                self.performance_blind_validation_bridge_frozen,
            )
        ):
            raise ValueError("retrospective bridge evidence must be completely verified")
        if any(
            (
                self.prospective_primary_assay_selected,
                self.primary_calibration_ready,
                self.classifier_executed,
                self.validation_molecular_values_accessed,
                self.outcomes_accessed,
                self.external_publication_authorized,
            )
        ):
            raise ValueError("retrospective bridge cannot claim calibration or execution")
        return self


def load_retrospective_expression_bridge_plan(
    path: Path,
) -> RetrospectiveExpressionBridgePlan:
    return RetrospectiveExpressionBridgePlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_retrospective_expression_bridge_receipt(
    path: Path,
    receipt: RetrospectiveExpressionBridgeReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("retrospective bridge receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_retrospective_expression_bridge_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, RetrospectiveExpressionBridgePlan),
        (receipt_path, RetrospectiveExpressionBridgeReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
