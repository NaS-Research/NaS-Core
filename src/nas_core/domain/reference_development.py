"""Governed reference-development contracts for NAS-BRCA-002."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReferenceDevelopmentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReferenceDevelopmentRole(StrEnum):
    REFERENCE_DEVELOPMENT_ONLY = "reference_development_only"


class SourceSelectionStatus(StrEnum):
    CANDIDATE = "candidate"
    LOCKED = "locked"


class ReferenceSubsetRule(ReferenceDevelopmentModel):
    eligible_material: str = Field(min_length=1)
    receptor_field: str = Field(min_length=1)
    receptor_strata: list[str] = Field(min_length=2, max_length=2)
    samples_per_stratum: int = Field(gt=0)
    deterministic_ordering: str = Field(min_length=1)
    outcome_fields_permitted: bool
    molecular_values_permitted_during_selection: bool

    @model_validator(mode="after")
    def enforce_outcome_blind_selection(self) -> ReferenceSubsetRule:
        if self.outcome_fields_permitted or self.molecular_values_permitted_during_selection:
            raise ValueError("reference subset selection must be outcome and expression blind")
        if set(self.receptor_strata) != {"ER-positive", "ER-negative"}:
            raise ValueError("reference subset must use the two frozen ER strata")
        return self


class PreprocessingBridgeCandidate(ReferenceDevelopmentModel):
    source_quantity: str = Field(min_length=1)
    source_scale_status: str = Field(min_length=1)
    target_quantity: str = Field(min_length=1)
    target_transform: str = Field(min_length=1)
    pseudocount: float = Field(gt=0)
    gene_identifier: str = Field(min_length=1)
    duplicate_gene_rule: str = Field(min_length=1)
    missing_gene_rule: str = Field(min_length=1)
    reference_statistic: str = Field(min_length=1)
    centering_operation: str = Field(min_length=1)
    unit_audit_required: bool
    transformation_locked: bool

    @model_validator(mode="after")
    def prevent_unverified_transform_lock(self) -> PreprocessingBridgeCandidate:
        if self.unit_audit_required and self.transformation_locked:
            raise ValueError("transformation cannot lock before the unit audit")
        return self


class ReferenceDevelopmentProtocol(ReferenceDevelopmentModel):
    schema_version: str = "1.0.0"
    protocol_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    route_id: str = Field(pattern=r"^ROUTE-C$")
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    source_accession: str = Field(pattern=r"^GSE[0-9]+$")
    intended_role: ReferenceDevelopmentRole
    source_selection_status: SourceSelectionStatus
    source_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    standing_authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    platform_audit_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    numerical_conformance_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    supersedes_protocol_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    reference_input_founder_decision_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    matrix_audit_receipt_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    metadata_acquisition_receipt_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    official_metadata_url: str = Field(pattern=r"^https://")
    proposed_processed_artifact: str = Field(min_length=1)
    expected_public_sample_count: int = Field(gt=0)
    relationship_to_validation: str = Field(min_length=1)
    participant_nonoverlap_status: str = Field(min_length=1)
    subset_rule: ReferenceSubsetRule
    preprocessing_bridge: PreprocessingBridgeCandidate
    required_pre_acquisition_checks: list[str] = Field(min_length=1)
    sensitivity_analyses: list[str] = Field(min_length=1)
    firewalls: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    molecular_values_accessed: bool
    outcome_values_accessed: bool
    source_bytes_stored: bool
    reference_vector_materialized: bool
    classifier_executed: bool
    reference_locked: bool
    study_execution_authorized: bool
    external_publication_authorized: bool

    @model_validator(mode="after")
    def enforce_candidate_boundary(self) -> ReferenceDevelopmentProtocol:
        if self.source_id != "ncbi-geo-gse81538" or self.source_accession != "GSE81538":
            raise ValueError("protocol is restricted to the registered GSE81538 candidate")
        if self.expected_public_sample_count != 405:
            raise ValueError("protocol must preserve the official 405-sample metadata count")
        if self.source_selection_status is SourceSelectionStatus.LOCKED and (
            self.participant_nonoverlap_status != "verified"
            or self.preprocessing_bridge.unit_audit_required
            or not self.preprocessing_bridge.transformation_locked
        ):
            raise ValueError("a locked source requires verified lineage and transformation")
        if any(
            (
                self.molecular_values_accessed,
                self.outcome_values_accessed,
                self.source_bytes_stored,
                self.reference_vector_materialized,
                self.classifier_executed,
                self.reference_locked,
                self.study_execution_authorized,
                self.external_publication_authorized,
            )
        ):
            raise ValueError("candidate protocol cannot claim acquisition, execution, or lock")
        if self.subset_rule.samples_per_stratum != 50:
            raise ValueError("candidate protocol freezes 50 samples per ER stratum")
        amendment_provenance = (
            self.supersedes_protocol_sha256,
            self.reference_input_founder_decision_sha256,
            self.matrix_audit_receipt_sha256,
            self.metadata_acquisition_receipt_sha256,
        )
        if self.protocol_version == "1.0.0":
            if any(amendment_provenance):
                raise ValueError("protocol 1.0.0 cannot claim later amendment evidence")
        else:
            if not all(amendment_provenance):
                raise ValueError("an amended protocol requires complete provenance")
            if (
                self.preprocessing_bridge.unit_audit_required
                or not self.preprocessing_bridge.transformation_locked
            ):
                raise ValueError("amended protocol must preserve the approved input scale")
        return self


def load_reference_development_protocol(path: Path) -> ReferenceDevelopmentProtocol:
    return ReferenceDevelopmentProtocol.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_reference_development_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            ReferenceDevelopmentProtocol.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
