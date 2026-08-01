"""Contracts for excluded public calibration-feasibility artifacts."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationFeasibilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalibrationFeasibilityArtifactKind(StrEnum):
    PROCESSED_EXPRESSION = "processed_expression"
    FEATURE_MAP = "feature_map"
    FILE_INVENTORY = "file_inventory"


class CalibrationFeasibilityArtifact(CalibrationFeasibilityModel):
    source_id: str = Field(pattern=r"^ncbi-geo-gse(60788|130397)$")
    source_accession: str = Field(pattern=r"^GSE(60788|130397)$")
    file_accession: str = Field(pattern=r"^(GSE|GSM)[0-9]+$")
    artifact_kind: CalibrationFeasibilityArtifactKind
    filename: str = Field(min_length=1)
    official_url: str = Field(pattern=r"^https://www\.ncbi\.nlm\.nih\.gov/geo/download/\?")
    expected_content_length_bytes: int = Field(gt=0)
    expected_content_type: str = Field(min_length=1)
    object_key: str = Field(pattern=r"^raw/nas-brca-002/[a-z0-9._/-]+$")

    @model_validator(mode="after")
    def reconcile_identity(self) -> CalibrationFeasibilityArtifact:
        expected_source = f"ncbi-geo-{self.source_accession.lower()}"
        if self.source_id != expected_source:
            raise ValueError("source id and accession do not reconcile")
        parsed = urlsplit(self.official_url)
        query = parse_qs(parsed.query)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "www.ncbi.nlm.nih.gov"
            or parsed.path != "/geo/download/"
            or query.get("acc") != [self.file_accession]
            or query.get("format") != ["file"]
            or query.get("file") != [self.filename]
        ):
            raise ValueError("official URL does not identify the declared GEO artifact")
        if self.filename.lower() not in self.object_key:
            raise ValueError("object key does not preserve the source filename")
        return self


class CalibrationFeasibilityAcquisitionPlan(CalibrationFeasibilityModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    intended_role: str = Field(pattern=r"^excluded_public_calibration_feasibility_only$")
    source_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    standing_authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_readiness_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    storage_readiness_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifacts: list[CalibrationFeasibilityArtifact] = Field(min_length=1)
    parse_during_acquisition: bool
    outcome_fields_requested: bool
    pooling_authorized: bool
    threshold_estimation_authorized: bool
    classifier_execution_authorized: bool
    immutable_write_required: bool

    @model_validator(mode="after")
    def enforce_firewall(self) -> CalibrationFeasibilityAcquisitionPlan:
        if any(
            (
                self.parse_during_acquisition,
                self.outcome_fields_requested,
                self.pooling_authorized,
                self.threshold_estimation_authorized,
                self.classifier_execution_authorized,
            )
        ):
            raise ValueError("feasibility acquisition cannot parse, pool, tune, or execute")
        if not self.immutable_write_required:
            raise ValueError("feasibility artifacts require immutable storage")
        identities = {(item.source_id, item.filename) for item in self.artifacts}
        if len(identities) != len(self.artifacts):
            raise ValueError("artifact identities must be unique")
        if {item.source_id for item in self.artifacts} != {
            "ncbi-geo-gse60788",
            "ncbi-geo-gse130397",
        }:
            raise ValueError("both approved feasibility sources are required")
        return self


class CalibrationFeasibilityArtifactReceipt(CalibrationFeasibilityModel):
    source_id: str
    source_accession: str
    file_accession: str
    artifact_kind: CalibrationFeasibilityArtifactKind
    filename: str
    official_url: str
    response_content_type: str
    response_last_modified: str | None
    content_length_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    object_key: str
    immutable_object_verified: bool


class CalibrationFeasibilityAcquisitionReceipt(CalibrationFeasibilityModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    acquired_at: datetime
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifacts: list[CalibrationFeasibilityArtifactReceipt] = Field(min_length=1)
    all_immutable_objects_verified: bool
    molecular_values_parsed: bool
    outcomes_accessed: bool
    sources_pooled: bool
    thresholds_estimated: bool
    classifier_executed: bool
    external_publication_authorized: bool

    @model_validator(mode="after")
    def enforce_receipt_firewall(self) -> CalibrationFeasibilityAcquisitionReceipt:
        if not self.all_immutable_objects_verified or not all(
            item.immutable_object_verified for item in self.artifacts
        ):
            raise ValueError("every source artifact must be verified")
        if any(
            (
                self.molecular_values_parsed,
                self.outcomes_accessed,
                self.sources_pooled,
                self.thresholds_estimated,
                self.classifier_executed,
                self.external_publication_authorized,
            )
        ):
            raise ValueError("acquisition receipt cannot claim analysis or publication")
        return self


def load_calibration_feasibility_acquisition_plan(
    path: Path,
) -> CalibrationFeasibilityAcquisitionPlan:
    return CalibrationFeasibilityAcquisitionPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_calibration_feasibility_acquisition_receipt(
    path: Path,
    receipt: CalibrationFeasibilityAcquisitionReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("calibration-feasibility receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_calibration_feasibility_acquisition_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, CalibrationFeasibilityAcquisitionPlan),
        (receipt_path, CalibrationFeasibilityAcquisitionReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
