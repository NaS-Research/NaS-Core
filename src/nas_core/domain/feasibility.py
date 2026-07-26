"""Typed receipts for non-patient source-metadata feasibility audits."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FeasibilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FeasibilityStatus(StrEnum):
    VERIFIED = "verified"
    UNRESOLVED = "unresolved"
    PROHIBITED = "prohibited"


class FeasibilityDecision(StrEnum):
    PASS = "pass"
    CHANGES_REQUESTED = "changes_requested"
    FAIL = "fail"


class MetadataEndpointEvidence(FeasibilityModel):
    source_id: str = Field(min_length=1)
    method: str = Field(pattern=r"^(GET|HEAD|POST)$")
    url: str = Field(pattern=r"^https://")
    request_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    representation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    representation_size_bytes: int = Field(ge=0)
    raw_response_stored: bool
    patient_rows_requested: bool
    outcome_fields_requested: bool

    @model_validator(mode="after")
    def enforce_metadata_only_endpoint(self) -> MetadataEndpointEvidence:
        if self.raw_response_stored:
            raise ValueError("metadata-audit source responses cannot be stored")
        if self.patient_rows_requested:
            raise ValueError("metadata-audit endpoints cannot request patient rows")
        if self.outcome_fields_requested:
            raise ValueError("metadata-audit endpoints cannot request outcome fields")
        return self


class FeasibilityCheck(FeasibilityModel):
    check_id: str = Field(min_length=1)
    status: FeasibilityStatus
    finding: str = Field(min_length=1)
    evidence_source_ids: list[str] = Field(min_length=1)
    limitation: str | None = None

    @model_validator(mode="after")
    def unresolved_checks_explain_limit(self) -> FeasibilityCheck:
        if self.status is not FeasibilityStatus.VERIFIED and not self.limitation:
            raise ValueError("unresolved or prohibited checks require an explicit limitation")
        return self


class GDCMetadataSummary(FeasibilityModel):
    data_release: str = Field(min_length=1)
    api_tag: str = Field(min_length=1)
    case_mapping_field_count: int = Field(ge=1)
    indexed_receptor_field_matches: list[str]
    open_star_counts_file_count: int = Field(ge=0)
    workflow_types: list[str]
    data_formats: list[str]
    access_categories: list[str]


class GEOSupplementaryArtifact(FeasibilityModel):
    artifact_role: str = Field(min_length=1)
    url: str = Field(pattern=r"^https://ftp\.ncbi\.nlm\.nih\.gov/")
    content_length_bytes: int = Field(ge=1)
    last_modified: str = Field(min_length=1)
    content_type: str = Field(min_length=1)


class GEOMetadataSummary(FeasibilityModel):
    accession: str = Field(pattern=r"^GSE[0-9]+$")
    supplementary_artifacts: list[GEOSupplementaryArtifact] = Field(min_length=2)
    family_metadata_endpoint_used: bool
    family_metadata_exclusion_reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def prohibit_family_bundle(self) -> GEOMetadataSummary:
        if self.family_metadata_endpoint_used:
            raise ValueError(
                "GEO family metadata is prohibited because it co-mingles patient fields"
            )
        return self


class MetadataFeasibilityReceipt(FeasibilityModel):
    schema_version: str = Field(pattern=r"^1\.0\.0$")
    audit_version: str = Field(pattern=r"^1\.0\.0$")
    study_id: str = Field(pattern=r"^NAS-BRCA-002$")
    question_id: str = Field(pattern=r"^NAS-RQ-BRCA002$")
    question_version: str = Field(pattern=r"^0\.3\.0$")
    executed_at: str = Field(min_length=1)
    authorization_path: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    metadata_only: bool
    patient_level_data_accessed: bool
    molecular_values_accessed: bool
    outcome_data_accessed: bool
    raw_responses_stored: bool
    endpoints: list[MetadataEndpointEvidence] = Field(min_length=5, max_length=5)
    gdc: GDCMetadataSummary
    geo: GEOMetadataSummary
    checks: list[FeasibilityCheck] = Field(min_length=5)
    decision: FeasibilityDecision
    decision_rationale: str = Field(min_length=1)
    next_authorization_required: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_audit_boundary(self) -> MetadataFeasibilityReceipt:
        if not self.metadata_only:
            raise ValueError("the feasibility receipt must remain metadata-only")
        if (
            self.patient_level_data_accessed
            or self.molecular_values_accessed
            or self.outcome_data_accessed
            or self.raw_responses_stored
        ):
            raise ValueError("the Phase 0 metadata audit cannot access or retain governed values")
        if self.decision is FeasibilityDecision.PASS:
            unresolved = [
                check for check in self.checks if check.status is not FeasibilityStatus.VERIFIED
            ]
            if unresolved:
                raise ValueError("a passing audit cannot contain unresolved or prohibited checks")
        return self


def write_metadata_feasibility_receipt(
    path: Path,
    receipt: MetadataFeasibilityReceipt,
) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite immutable receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        allow_unicode=True,
    )
    path.write_text(payload, encoding="utf-8")


def write_metadata_feasibility_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(MetadataFeasibilityReceipt.model_json_schema(), indent=2, sort_keys=True)
    path.write_text(f"{payload}\n", encoding="utf-8")
