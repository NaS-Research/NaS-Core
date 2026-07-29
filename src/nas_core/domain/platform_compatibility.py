"""Platform-compatibility audit contracts for Phase 1 method lock."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlatformCompatibilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompatibilityFindingStatus(StrEnum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    PENDING = "pending"


class PlatformAuditDecision(StrEnum):
    PASS = "pass"
    CHANGES_REQUIRED = "changes_required"


class PlatformCompatibilityFinding(PlatformCompatibilityModel):
    criterion_id: str = Field(pattern=r"^PLAT-[0-9]{3}$")
    status: CompatibilityFindingStatus
    finding: str = Field(min_length=1)
    evidence_paths: list[str] = Field(min_length=1)
    remaining_requirement: str | None = None

    @model_validator(mode="after")
    def require_open_work_for_nonverified(
        self,
    ) -> PlatformCompatibilityFinding:
        if (
            self.status is not CompatibilityFindingStatus.VERIFIED
            and not self.remaining_requirement
        ):
            raise ValueError("partial or pending findings require remaining work")
        if (
            self.status is CompatibilityFindingStatus.VERIFIED
            and self.remaining_requirement is not None
        ):
            raise ValueError("verified findings cannot retain a requirement")
        return self


class PlatformCompatibilityAuditReceipt(PlatformCompatibilityModel):
    schema_version: str = "1.0.0"
    audit_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    route_id: str = Field(pattern=r"^ROUTE-C$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    audited_at: datetime
    planning_bundle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    metadata_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: list[PlatformCompatibilityFinding] = Field(min_length=8, max_length=8)
    verified_count: int = Field(ge=0, le=8)
    partial_count: int = Field(ge=0, le=8)
    pending_count: int = Field(ge=0, le=8)
    decision: PlatformAuditDecision
    decision_rationale: str = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    molecular_values_parsed: bool
    outcome_values_parsed: bool
    raw_artifacts_stored: bool
    classifier_executed: bool
    source_selected: bool
    transformation_locked: bool
    reference_locked: bool
    platform_stack_selected: bool
    study_execution_authorized: bool

    @model_validator(mode="after")
    def validate_audit_state(self) -> PlatformCompatibilityAuditReceipt:
        ids = [finding.criterion_id for finding in self.findings]
        if ids != [f"PLAT-{index:03d}" for index in range(1, 9)]:
            raise ValueError("platform findings must appear once in PLAT-001–008 order")
        observed = {
            CompatibilityFindingStatus.VERIFIED: 0,
            CompatibilityFindingStatus.PARTIAL: 0,
            CompatibilityFindingStatus.PENDING: 0,
        }
        for finding in self.findings:
            observed[finding.status] += 1
        if (
            self.verified_count,
            self.partial_count,
            self.pending_count,
        ) != (
            observed[CompatibilityFindingStatus.VERIFIED],
            observed[CompatibilityFindingStatus.PARTIAL],
            observed[CompatibilityFindingStatus.PENDING],
        ):
            raise ValueError("platform finding counts do not reconcile")
        if self.decision is PlatformAuditDecision.PASS and (
            self.partial_count or self.pending_count
        ):
            raise ValueError("a passing platform audit cannot retain open findings")
        if self.decision is PlatformAuditDecision.CHANGES_REQUIRED and not (
            self.partial_count or self.pending_count
        ):
            raise ValueError("changes_required requires at least one open finding")
        if any(
            (
                self.molecular_values_parsed,
                self.outcome_values_parsed,
                self.raw_artifacts_stored,
                self.classifier_executed,
                self.source_selected,
                self.transformation_locked,
                self.reference_locked,
                self.platform_stack_selected,
                self.study_execution_authorized,
            )
        ):
            raise ValueError("metadata-only platform audit cannot claim method lock")
        return self


def load_platform_compatibility_audit(
    path: Path,
) -> PlatformCompatibilityAuditReceipt:
    return PlatformCompatibilityAuditReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_platform_compatibility_audit(
    path: Path,
    receipt: PlatformCompatibilityAuditReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("platform compatibility receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_platform_compatibility_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            PlatformCompatibilityAuditReceipt.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
