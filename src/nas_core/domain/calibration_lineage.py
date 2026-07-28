"""Typed receipts for field-isolated calibration-source lineage audits."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationLineageModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalibrationLineageArtifact(CalibrationLineageModel):
    source_id: str = Field(pattern=r"^GEO:GSE[0-9]+$")
    url: str = Field(pattern=r"^https://")
    representation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    representation_size_bytes: int = Field(gt=0)
    parser_name: str = Field(pattern=r"^geo_family_soft_title_projection_v1$")
    raw_artifact_stored: bool
    sample_rows_retained: bool
    molecular_values_parsed: bool
    outcome_values_parsed: bool

    @model_validator(mode="after")
    def validate_artifact_boundary(self) -> CalibrationLineageArtifact:
        if any(
            (
                self.raw_artifact_stored,
                self.sample_rows_retained,
                self.molecular_values_parsed,
                self.outcome_values_parsed,
            )
        ):
            raise ValueError(
                "lineage artifacts cannot retain rows or parse molecular or outcome values"
            )
        return self


class CalibrationLineageSummary(CalibrationLineageModel):
    source_id: str = Field(pattern=r"^GEO:GSE[0-9]+$")
    sample_record_count: int = Field(gt=0)
    primary_or_unlabeled_record_count: int = Field(ge=0)
    replicate_labeled_record_count: int = Field(ge=0)
    linked_replicate_record_count: int = Field(ge=0)
    unique_replicate_group_count: int = Field(ge=0)
    unrecognized_title_count: int = Field(ge=0)
    transient_title_count: int = Field(gt=0)
    sample_titles_retained: bool

    @model_validator(mode="after")
    def validate_counts(self) -> CalibrationLineageSummary:
        if (
            self.primary_or_unlabeled_record_count
            + self.replicate_labeled_record_count
            != self.sample_record_count
        ):
            raise ValueError("lineage record classes must partition sample records")
        if self.linked_replicate_record_count > self.replicate_labeled_record_count:
            raise ValueError("linked replicate count exceeds labeled replicates")
        if self.transient_title_count != self.sample_record_count:
            raise ValueError("every sample record must contribute one transient title")
        if self.sample_titles_retained:
            raise ValueError("field-isolated lineage receipts cannot retain titles")
        return self


class CalibrationLineageAuditReceipt(CalibrationLineageModel):
    schema_version: str = "1.0.0"
    audit_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    route_activation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    executed_at: datetime
    artifacts: list[CalibrationLineageArtifact] = Field(min_length=3, max_length=3)
    summaries: list[CalibrationLineageSummary] = Field(min_length=3, max_length=3)
    gse60788_gse96058_accession_overlap_count: int = Field(ge=0)
    gse60788_gse96058_title_overlap_count: int = Field(ge=0)
    biological_sample_nonoverlap_established: bool
    metadata_lineage_feasibility_established: bool
    prohibited_fields_transiently_transferred: bool
    patient_level_records_retained: bool
    sample_identifiers_retained: bool
    molecular_values_parsed: bool
    outcome_values_parsed: bool
    raw_artifacts_stored: bool
    calibration_source_selected: bool
    method_execution_authorized: bool
    limitations: list[str] = Field(min_length=1)
    next_required_actions: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_receipt_boundary(self) -> CalibrationLineageAuditReceipt:
        artifact_ids = [item.source_id for item in self.artifacts]
        summary_ids = [item.source_id for item in self.summaries]
        if len(set(artifact_ids)) != 3 or set(artifact_ids) != set(summary_ids):
            raise ValueError("lineage receipt requires three matching unique sources")
        if self.biological_sample_nonoverlap_established:
            raise ValueError(
                "public accession and title comparison cannot establish biological nonoverlap"
            )
        if any(
            (
                self.patient_level_records_retained,
                self.sample_identifiers_retained,
                self.molecular_values_parsed,
                self.outcome_values_parsed,
                self.raw_artifacts_stored,
                self.calibration_source_selected,
                self.method_execution_authorized,
            )
        ):
            raise ValueError(
                "metadata lineage audit cannot retain records, select a source, "
                "or authorize execution"
            )
        return self


def load_calibration_lineage_receipt(
    path: Path,
) -> CalibrationLineageAuditReceipt:
    return CalibrationLineageAuditReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_lineage_receipt(
    path: Path,
    receipt: CalibrationLineageAuditReceipt,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json"),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_calibration_lineage_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            CalibrationLineageAuditReceipt.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
