"""Contracts for governed immutable acquisition of one public source artifact."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PublicArtifactModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublicArtifactKind(StrEnum):
    PROCESSED_EXPRESSION_MATRIX = "processed_expression_matrix"
    SAMPLE_METADATA = "sample_metadata"


class PublicArtifactAcquisitionPlan(PublicArtifactModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    source_accession: str = Field(pattern=r"^GSE[0-9]+$")
    artifact_kind: PublicArtifactKind = PublicArtifactKind.PROCESSED_EXPRESSION_MATRIX
    intended_role: str = Field(pattern=r"^reference_development_only$")
    official_url: str = Field(pattern=r"^https://")
    filename: str = Field(min_length=1)
    expected_content_type: str = Field(min_length=1)
    expected_content_length_bytes: int = Field(gt=0)
    object_key: str = Field(pattern=r"^raw/[a-z0-9._/-]+$")
    source_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    standing_authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_protocol_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    storage_readiness_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    outcome_fields_requested: bool
    parse_molecular_values_during_acquisition: bool
    immutable_write_required: bool

    @model_validator(mode="after")
    def enforce_bounded_acquisition(self) -> PublicArtifactAcquisitionPlan:
        if self.source_id != "ncbi-geo-gse81538" or self.source_accession != "GSE81538":
            raise ValueError("acquisition plan is restricted to GSE81538")
        if self.outcome_fields_requested or self.parse_molecular_values_during_acquisition:
            raise ValueError("acquisition cannot request outcomes or parse molecular values")
        if not self.immutable_write_required:
            raise ValueError("public source acquisition must be immutable")
        if not self.official_url.endswith(f"/{self.filename}"):
            raise ValueError("official URL and filename do not reconcile")
        return self


class PublicArtifactAcquisitionReceipt(PublicArtifactModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    source_accession: str = Field(pattern=r"^GSE[0-9]+$")
    artifact_kind: PublicArtifactKind = PublicArtifactKind.PROCESSED_EXPRESSION_MATRIX
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    acquired_at: datetime
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    official_url: str = Field(pattern=r"^https://")
    response_content_type: str = Field(min_length=1)
    response_last_modified: str | None
    content_length_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    object_key: str = Field(pattern=r"^raw/[a-z0-9._/-]+$")
    immutable_object_verified: bool
    source_bytes_stored: bool = True
    molecular_source_bytes_stored: bool
    molecular_values_parsed: bool
    outcome_values_accessed: bool
    classifier_executed: bool
    external_publication_authorized: bool

    @model_validator(mode="after")
    def enforce_receipt_boundary(self) -> PublicArtifactAcquisitionReceipt:
        if not self.immutable_object_verified or not self.source_bytes_stored:
            raise ValueError("receipt requires a verified immutable source object")
        if (
            self.artifact_kind is PublicArtifactKind.PROCESSED_EXPRESSION_MATRIX
            and not self.molecular_source_bytes_stored
        ):
            raise ValueError("a processed matrix receipt must disclose molecular bytes")
        if (
            self.artifact_kind is PublicArtifactKind.SAMPLE_METADATA
            and self.molecular_source_bytes_stored
        ):
            raise ValueError("a sample-metadata receipt cannot claim molecular bytes")
        if any(
            (
                self.molecular_values_parsed,
                self.outcome_values_accessed,
                self.classifier_executed,
                self.external_publication_authorized,
            )
        ):
            raise ValueError("acquisition receipt cannot claim parsing, outcomes, or execution")
        return self


def load_public_artifact_plan(path: Path) -> PublicArtifactAcquisitionPlan:
    return PublicArtifactAcquisitionPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_public_artifact_receipt(path: Path) -> PublicArtifactAcquisitionReceipt:
    return PublicArtifactAcquisitionReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_public_artifact_receipt(
    path: Path,
    receipt: PublicArtifactAcquisitionReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("public artifact receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_public_artifact_schemas(plan_path: Path, receipt_path: Path) -> None:
    for path, model in (
        (plan_path, PublicArtifactAcquisitionPlan),
        (receipt_path, PublicArtifactAcquisitionReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
