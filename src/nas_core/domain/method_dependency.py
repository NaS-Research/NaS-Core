"""Governed method-dependency audit contracts for reliability studies."""

from __future__ import annotations

import json
import math
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.reliability import (
    PAM50_HISTORICAL_ALIASES,
    PAM50_HISTORICAL_GENES,
)


class MethodDependencyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArtifactCandidateStatus(StrEnum):
    VERIFIED_CANDIDATE = "verified_candidate"
    INSUFFICIENT = "insufficient"
    UNAVAILABLE = "unavailable"


class DependencyDisposition(StrEnum):
    RESOLVED_CANDIDATE = "resolved_candidate"
    REQUIRES_FOUNDER_CHOICE = "requires_founder_choice"
    BLOCKED_MISSING_ARTIFACT = "blocked_missing_artifact"
    REJECTED = "rejected"


class RouteRecommendation(StrEnum):
    PREFERRED = "preferred"
    ALTERNATIVE = "alternative"
    REJECT = "reject"


class ArtifactCandidate(MethodDependencyModel):
    artifact_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    role: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    distribution_version: str = Field(min_length=1)
    license_id: str = Field(min_length=1)
    distribution_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    member_path: str | None = None
    member_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    status: ArtifactCandidateStatus
    verification_basis: list[str] = Field(min_length=1)
    candidate_only: bool = True

    @model_validator(mode="after")
    def validate_candidate(self) -> ArtifactCandidate:
        if self.status is ArtifactCandidateStatus.VERIFIED_CANDIDATE and (
            self.distribution_sha256 is None
            or self.member_path is None
            or self.member_sha256 is None
        ):
            raise ValueError(
                "a verified artifact candidate requires distribution and member hashes"
            )
        if not self.candidate_only:
            raise ValueError(
                "an audit candidate cannot silently become an approved method artifact"
            )
        return self


class DependencyAssessment(MethodDependencyModel):
    dependency_id: str = Field(pattern=r"^DEP-[0-9]{3}$")
    dependency: str = Field(min_length=1)
    disposition: DependencyDisposition
    evidence_ids: list[str] = Field(min_length=1)
    finding: str = Field(min_length=1)
    required_resolution: str = Field(min_length=1)


class MethodRoute(MethodDependencyModel):
    route_id: str = Field(pattern=r"^ROUTE-[A-Z]$")
    label: str = Field(min_length=1)
    classifier_family: str = Field(min_length=1)
    patient_independent_at_inference: bool
    external_reference_required: bool
    preserves_question_version_0_3_0: bool
    advantages: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    recommendation: RouteRecommendation
    material_scope_change: bool


class MethodDependencyAuditProposal(MethodDependencyModel):
    schema_version: str = "1.0.0"
    audit_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    authorized_synthesis_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    audited_at: datetime
    source_retrieval_notes: list[str] = Field(min_length=1)
    artifact_candidates: list[ArtifactCandidate] = Field(min_length=1)
    dependencies: list[DependencyAssessment] = Field(min_length=1)
    routes: list[MethodRoute] = Field(min_length=2)
    recommended_route_id: str = Field(pattern=r"^ROUTE-[A-Z]$")
    recommendation_rationale: str = Field(min_length=1)
    founder_decision_required: bool
    patient_level_data_accessed: bool
    molecular_values_accessed: bool
    outcome_data_accessed: bool
    method_execution_authorized: bool
    molecular_data_access_authorized: bool
    outcome_data_access_authorized: bool
    clinical_use_authorized: bool
    publication_authorized: bool

    @model_validator(mode="after")
    def validate_audit_boundary(self) -> MethodDependencyAuditProposal:
        dependency_ids = [item.dependency_id for item in self.dependencies]
        if len(dependency_ids) != len(set(dependency_ids)):
            raise ValueError("method dependency IDs must be unique")
        route_ids = [item.route_id for item in self.routes]
        if len(route_ids) != len(set(route_ids)):
            raise ValueError("method route IDs must be unique")
        if self.recommended_route_id not in route_ids:
            raise ValueError("recommended route must exist in the audited route set")
        preferred = [
            item
            for item in self.routes
            if item.recommendation is RouteRecommendation.PREFERRED
        ]
        if len(preferred) != 1 or preferred[0].route_id != self.recommended_route_id:
            raise ValueError("exactly one preferred route must match the recommendation")
        if not self.founder_decision_required:
            raise ValueError("a material method-route audit requires a founder decision")
        if any(
            (
                self.patient_level_data_accessed,
                self.molecular_values_accessed,
                self.outcome_data_accessed,
                self.method_execution_authorized,
                self.molecular_data_access_authorized,
                self.outcome_data_access_authorized,
                self.clinical_use_authorized,
                self.publication_authorized,
            )
        ):
            raise ValueError("a method audit cannot access data or authorize execution")
        return self


class Pam50CentroidCandidateArtifact(MethodDependencyModel):
    schema_version: str = "1.0.0"
    artifact_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    artifact_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    source_url: str = Field(min_length=1)
    source_distribution_version: str = Field(min_length=1)
    source_distribution_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_member_path: str = Field(min_length=1)
    source_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    license_id: str = Field(min_length=1)
    source_notice: str = Field(min_length=1)
    method_correlation: str = Field(pattern=r"^spearman$")
    method_centroids: str = Field(pattern=r"^mean$")
    expression_standardization: str = Field(pattern=r"^none$")
    gene_order: list[str] = Field(min_length=50, max_length=50)
    historical_aliases: dict[str, str]
    centroids: dict[str, dict[str, float]]
    candidate_only: bool
    founder_approved: bool
    method_execution_authorized: bool

    @model_validator(mode="after")
    def validate_centroid_candidate(self) -> Pam50CentroidCandidateArtifact:
        if len(self.gene_order) != len(set(self.gene_order)):
            raise ValueError("PAM50 candidate gene order must be unique")
        if set(self.gene_order) != PAM50_HISTORICAL_GENES:
            raise ValueError("PAM50 candidate must contain the historical 50-gene panel")
        if self.historical_aliases != PAM50_HISTORICAL_ALIASES:
            raise ValueError("PAM50 candidate aliases must match the governed mapping")
        expected = {
            "Luminal A",
            "Luminal B",
            "HER2-enriched",
            "Basal-like",
            "Normal-like",
        }
        if set(self.centroids) != expected:
            raise ValueError("PAM50 candidate must contain exactly five governed subtypes")
        for values in self.centroids.values():
            if set(values) != PAM50_HISTORICAL_GENES:
                raise ValueError("each PAM50 centroid must contain exactly 50 genes")
            if any(not math.isfinite(value) for value in values.values()):
                raise ValueError("PAM50 centroid coefficients must be finite")
        if not self.candidate_only or self.founder_approved:
            raise ValueError("an imported candidate cannot record founder approval")
        if self.method_execution_authorized:
            raise ValueError("a centroid candidate cannot authorize method execution")
        return self


class CentroidCandidateImportReceipt(MethodDependencyModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    method_dependency_audit_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_distribution_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_artifact_path: str = Field(min_length=1)
    candidate_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_artifact_size_bytes: int = Field(gt=0)
    coefficient_count: int = Field(ge=250, le=250)
    gene_count: int = Field(ge=50, le=50)
    subtype_count: int = Field(ge=5, le=5)
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    imported_at: datetime
    candidate_only: bool
    founder_approved: bool
    method_execution_authorized: bool
    molecular_data_accessed: bool
    outcome_data_accessed: bool

    @model_validator(mode="after")
    def validate_receipt_boundary(self) -> CentroidCandidateImportReceipt:
        if (
            not self.candidate_only
            or self.founder_approved
            or self.method_execution_authorized
            or self.molecular_data_accessed
            or self.outcome_data_accessed
        ):
            raise ValueError("candidate import receipt cannot authorize or access study data")
        return self


def load_method_dependency_audit(path: Path) -> MethodDependencyAuditProposal:
    return MethodDependencyAuditProposal.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_pam50_centroid_candidate(
    path: Path,
) -> Pam50CentroidCandidateArtifact:
    return Pam50CentroidCandidateArtifact.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_centroid_candidate_import_receipt(
    path: Path,
) -> CentroidCandidateImportReceipt:
    return CentroidCandidateImportReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_pam50_centroid_candidate(
    path: Path,
    artifact: Pam50CentroidCandidateArtifact,
) -> None:
    _write_yaml_exclusive(path, artifact)


def write_centroid_candidate_import_receipt(
    path: Path,
    receipt: CentroidCandidateImportReceipt,
) -> None:
    _write_yaml_exclusive(path, receipt)


def _write_yaml_exclusive(path: Path, model: MethodDependencyModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        model.model_dump(mode="json"),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_method_dependency_audit_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            MethodDependencyAuditProposal.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_centroid_candidate_schemas(
    candidate_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (candidate_path, Pam50CentroidCandidateArtifact),
        (receipt_path, CentroidCandidateImportReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
