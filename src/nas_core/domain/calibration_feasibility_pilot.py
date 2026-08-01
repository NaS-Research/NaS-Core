"""Contracts for excluded source-specific technical-replicate pilots."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationPilotModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalibrationFeasibilityPilotPlan(CalibrationPilotModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = "NAS-BRCA-002"
    feasibility_acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    feasibility_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    annotation_resolution_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    annotation_mapping_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    annotation_mapping_object_key: str = Field(pattern=r"^derived/nas-brca-002/")
    annotation_mapping_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    gse60788_transform: str = Field(pattern=r"^unchanged_source_normalized_values$")
    gse130397_transform: str = Field(pattern=r"^log2_cpm_plus_1$")
    gse130397_library_size_scope: str = Field(pattern=r"^all_60675_features$")
    gse130397_access_count_column: str = Field(pattern=r"^rev$")
    gse130397_ovation_count_column: str = Field(pattern=r"^fwd$")
    panel: str = Field(pattern=r"^PAM50_historical_50$")
    pair_metrics: list[str] = Field(min_length=4, max_length=4)
    group_aggregation: str = Field(pattern=r"^median_of_all_unordered_within_group_pairs$")
    source_summary: str = Field(pattern=r"^median_across_independent_replicate_groups$")
    bootstrap_unit: str = Field(pattern=r"^replicate_group$")
    bootstrap_replicates: int = Field(ge=10000, le=10000)
    random_seed: int = Field(ge=0)
    details_object_key: str = Field(pattern=r"^derived/nas-brca-002/")
    pool_sources: bool
    infer_reliability_threshold: bool
    execute_classifier: bool
    access_outcomes: bool
    retain_source_identifiers: bool
    retain_molecular_values_in_git: bool
    export_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def enforce_excluded_pilot(self) -> CalibrationFeasibilityPilotPlan:
        if self.pair_metrics != ["spearman", "pearson", "mae", "rmse"]:
            raise ValueError("pair metrics and order must be prespecified")
        if any(
            (
                self.pool_sources,
                self.infer_reliability_threshold,
                self.execute_classifier,
                self.access_outcomes,
                self.retain_source_identifiers,
                self.retain_molecular_values_in_git,
                self.export_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError("excluded pilot cannot pool, tune, classify, retain, or release")
        return self


class SourcePilotSummary(CalibrationPilotModel):
    source_id: str = Field(pattern=r"^ncbi-geo-gse(60788|130397)$")
    eligible_replicate_group_count: int = Field(gt=0)
    unordered_pair_comparison_count: int = Field(gt=0)
    panel_gene_count: int = Field(ge=50, le=50)
    analysis_scale: str
    median_group_spearman: float = Field(ge=-1, le=1)
    bootstrap_spearman_ci_lower: float = Field(ge=-1, le=1)
    bootstrap_spearman_ci_upper: float = Field(ge=-1, le=1)
    minimum_group_spearman: float = Field(ge=-1, le=1)
    maximum_group_spearman: float = Field(ge=-1, le=1)
    median_group_pearson: float = Field(ge=-1, le=1)
    median_group_mae: float = Field(ge=0)
    median_group_rmse: float = Field(ge=0)
    bootstrap_rmse_ci_lower: float = Field(ge=0)
    bootstrap_rmse_ci_upper: float = Field(ge=0)
    median_gene_absolute_difference: float = Field(ge=0)
    maximum_gene_absolute_difference: float = Field(ge=0)
    highest_difference_genes: list[str] = Field(min_length=5, max_length=5)
    inferential_claim_authorized: bool
    primary_calibration_eligible: bool

    @model_validator(mode="after")
    def enforce_descriptive_summary(self) -> SourcePilotSummary:
        if self.bootstrap_spearman_ci_lower > self.bootstrap_spearman_ci_upper:
            raise ValueError("Spearman interval is reversed")
        if self.bootstrap_rmse_ci_lower > self.bootstrap_rmse_ci_upper:
            raise ValueError("RMSE interval is reversed")
        if self.inferential_claim_authorized or self.primary_calibration_eligible:
            raise ValueError("excluded source summary cannot authorize inference")
        return self


class CalibrationFeasibilityPilotReceipt(CalibrationPilotModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_summaries: list[SourcePilotSummary] = Field(min_length=2, max_length=2)
    details_object_key: str
    details_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    details_object_verified: bool
    decision: str = Field(
        pattern=r"^excluded_pilots_complete_primary_calibration_not_ready$"
    )
    sources_pooled: bool
    thresholds_estimated: bool
    classifier_executed: bool
    outcomes_accessed: bool
    source_identifiers_retained: bool
    molecular_values_retained_in_git: bool
    external_export_authorized: bool
    external_publication_authorized: bool
    limitations: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_pilot_receipt(self) -> CalibrationFeasibilityPilotReceipt:
        if {item.source_id for item in self.source_summaries} != {
            "ncbi-geo-gse60788",
            "ncbi-geo-gse130397",
        }:
            raise ValueError("pilot receipt requires both separate sources")
        if not self.details_object_verified:
            raise ValueError("external pilot details must be verified")
        if any(
            (
                self.sources_pooled,
                self.thresholds_estimated,
                self.classifier_executed,
                self.outcomes_accessed,
                self.source_identifiers_retained,
                self.molecular_values_retained_in_git,
                self.external_export_authorized,
                self.external_publication_authorized,
            )
        ):
            raise ValueError("pilot receipt cannot claim prohibited use or release")
        return self


def load_calibration_feasibility_pilot_plan(
    path: Path,
) -> CalibrationFeasibilityPilotPlan:
    return CalibrationFeasibilityPilotPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_feasibility_pilot_receipt(
    path: Path,
    receipt: CalibrationFeasibilityPilotReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("calibration-pilot receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def load_calibration_feasibility_pilot_receipt(
    path: Path,
) -> CalibrationFeasibilityPilotReceipt:
    return CalibrationFeasibilityPilotReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_feasibility_pilot_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, CalibrationFeasibilityPilotPlan),
        (receipt_path, CalibrationFeasibilityPilotReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
