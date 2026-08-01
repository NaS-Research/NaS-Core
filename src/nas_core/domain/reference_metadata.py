"""Contracts for field-isolated GSE81538 reference-metadata selection."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReferenceMetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReferenceMetadataDecision(StrEnum):
    PASS = "pass"


class GSE81538ReferenceMetadataPlan(ReferenceMetadataModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_id: str = Field(pattern=r"^ncbi-geo-gse81538$")
    source_accession: str = Field(pattern=r"^GSE81538$")
    metadata_object_key: str = Field(pattern=r"^raw/[a-z0-9._/-]+$")
    metadata_acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    founder_decision_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_protocol_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_metadata_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_metadata_bytes: int = Field(gt=0)
    expected_sample_count: int = Field(gt=0)
    expected_title_prefix: str = Field(pattern=r"^T$")
    permitted_sample_fields: list[str] = Field(min_length=3, max_length=3)
    er_consensus_field: str = Field(pattern=r"^er consensus$")
    er_negative_consensus_code: int = Field(ge=0, le=3)
    er_positive_consensus_code: int = Field(ge=0, le=3)
    excluded_er_consensus_codes: list[int] = Field(min_length=2, max_length=2)
    samples_per_stratum: int = Field(gt=0)
    deterministic_ordering: str = Field(pattern=r"^lexicographic_geo_accession$")
    manifest_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    primary_source_url: str = Field(pattern=r"^https://")
    outcome_fields_permitted: bool
    expression_values_permitted: bool
    validation_data_permitted: bool
    generative_ai_processing_permitted: bool

    @model_validator(mode="after")
    def enforce_field_isolation(self) -> GSE81538ReferenceMetadataPlan:
        if self.permitted_sample_fields != [
            "!Sample_title",
            "!Sample_geo_accession",
            "er consensus",
        ]:
            raise ValueError("reference metadata fields must match the frozen projection")
        if self.er_negative_consensus_code != 0 or self.er_positive_consensus_code != 3:
            raise ValueError("approved ER strata require codes 0 and 3")
        if self.excluded_er_consensus_codes != [1, 2]:
            raise ValueError("approved ER consensus codes 1 and 2 must be excluded")
        if any(
            (
                self.outcome_fields_permitted,
                self.expression_values_permitted,
                self.validation_data_permitted,
                self.generative_ai_processing_permitted,
            )
        ):
            raise ValueError("reference metadata selection must remain field isolated")
        return self


class GSE81538ReferenceMetadataReceipt(ReferenceMetadataModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    source_id: str = Field(pattern=r"^ncbi-geo-gse81538$")
    source_accession: str = Field(pattern=r"^GSE81538$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    audited_at: datetime
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    metadata_acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    founder_decision_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_protocol_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    metadata_object_sha256_verified: bool
    metadata_bytes: int = Field(gt=0)
    parsed_sample_fields: list[str] = Field(min_length=3, max_length=3)
    sample_record_count: int = Field(gt=0)
    unique_accession_count: int = Field(gt=0)
    unique_title_count: int = Field(gt=0)
    exact_title_sequence_verified: bool
    matrix_title_linkage_verified: bool
    er_consensus_counts: dict[int, int]
    er_negative_eligible_count: int = Field(ge=0)
    er_positive_eligible_count: int = Field(ge=0)
    ambiguous_excluded_count: int = Field(ge=0)
    selected_negative_count: int = Field(ge=0)
    selected_positive_count: int = Field(ge=0)
    manifest_object_key: str = Field(pattern=r"^derived/[a-z0-9._/-]+$")
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    manifest_bytes: int = Field(gt=0)
    manifest_record_count: int = Field(gt=0)
    manifest_immutable_verified: bool
    relationship_to_validation: str = Field(min_length=1)
    er_codebook_status: str = Field(pattern=r"^founder_approved_conservative_inference$")
    decision: ReferenceMetadataDecision
    limitations: list[str] = Field(min_length=1)
    participant_identifiers_stored_external: bool
    participant_identifiers_retained_in_git: bool
    outcome_values_accessed: bool
    expression_values_accessed: bool
    validation_data_accessed: bool
    classifier_executed: bool
    generative_ai_received_participant_data: bool

    @model_validator(mode="after")
    def reconcile_receipt(self) -> GSE81538ReferenceMetadataReceipt:
        if not all(
            (
                self.metadata_object_sha256_verified,
                self.exact_title_sequence_verified,
                self.matrix_title_linkage_verified,
                self.manifest_immutable_verified,
                self.participant_identifiers_stored_external,
            )
        ):
            raise ValueError("a passing metadata receipt requires all integrity gates")
        if self.unique_accession_count != self.sample_record_count:
            raise ValueError("all sample accessions must be unique")
        if self.unique_title_count != self.sample_record_count:
            raise ValueError("all sample titles must be unique")
        if sum(self.er_consensus_counts.values()) != self.sample_record_count:
            raise ValueError("ER consensus counts must reconcile to sample records")
        if (
            self.er_negative_eligible_count
            + self.er_positive_eligible_count
            + self.ambiguous_excluded_count
            != self.sample_record_count
        ):
            raise ValueError("ER eligibility counts must reconcile")
        if self.manifest_record_count != (
            self.selected_negative_count + self.selected_positive_count
        ):
            raise ValueError("selection counts must reconcile to the manifest")
        if any(
            (
                self.participant_identifiers_retained_in_git,
                self.outcome_values_accessed,
                self.expression_values_accessed,
                self.validation_data_accessed,
                self.classifier_executed,
                self.generative_ai_received_participant_data,
            )
        ):
            raise ValueError("metadata selection exceeded its field-isolated boundary")
        return self


def load_reference_metadata_plan(path: Path) -> GSE81538ReferenceMetadataPlan:
    return GSE81538ReferenceMetadataPlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_reference_metadata_receipt(
    path: Path,
    receipt: GSE81538ReferenceMetadataReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("reference metadata receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_reference_metadata_schemas(plan_path: Path, receipt_path: Path) -> None:
    for path, model in (
        (plan_path, GSE81538ReferenceMetadataPlan),
        (receipt_path, GSE81538ReferenceMetadataReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
