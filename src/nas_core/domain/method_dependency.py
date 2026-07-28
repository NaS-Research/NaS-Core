"""Governed method-dependency audit contracts for reliability studies."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


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


def load_method_dependency_audit(path: Path) -> MethodDependencyAuditProposal:
    return MethodDependencyAuditProposal.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


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
