"""Machine-verifiable research completion and final-review contracts."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResearchCompletionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResearchPhaseStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    AWAITING_FINAL_HUMAN_REVIEW = "awaiting_final_human_review"


class CompletionEvidence(ResearchCompletionModel):
    artifact_path: str = Field(
        min_length=1,
        pattern=r"^[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)*$",
    )
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    proves: str = Field(min_length=1)


class ResearchPhaseRecord(ResearchCompletionModel):
    phase_number: int = Field(ge=0, le=6)
    name: str = Field(min_length=1)
    status: ResearchPhaseStatus
    completion_gate: str = Field(min_length=1)
    evidence: list[CompletionEvidence]
    open_requirements: list[str]

    @model_validator(mode="after")
    def validate_phase_state(self) -> ResearchPhaseRecord:
        if self.status is ResearchPhaseStatus.COMPLETE:
            if not self.evidence:
                raise ValueError("a complete phase requires completion evidence")
            if self.open_requirements:
                raise ValueError("a complete phase cannot retain open requirements")
        elif not self.open_requirements:
            raise ValueError("an incomplete phase must declare open requirements")
        return self


class StudyCompletionAudit(ResearchCompletionModel):
    schema_version: str = "1.0.0"
    audit_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    pipeline_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    current_phase: int = Field(ge=0, le=6)
    phases: list[ResearchPhaseRecord] = Field(min_length=7, max_length=7)
    ready_for_final_human_review: bool
    final_human_review_preserved: bool
    final_human_review_completed: bool
    scientific_conclusion_authorized: bool
    external_publication_authorized: bool
    external_submission_authorized: bool

    @model_validator(mode="after")
    def validate_completion_claim(self) -> StudyCompletionAudit:
        phase_numbers = [phase.phase_number for phase in self.phases]
        if phase_numbers != list(range(7)):
            raise ValueError("completion phases must appear once in order 0 through 6")

        active = [
            phase.phase_number
            for phase in self.phases
            if phase.status is ResearchPhaseStatus.IN_PROGRESS
        ]
        awaiting = [
            phase.phase_number
            for phase in self.phases
            if phase.status is ResearchPhaseStatus.AWAITING_FINAL_HUMAN_REVIEW
        ]
        if self.ready_for_final_human_review:
            if active:
                raise ValueError("final-review readiness cannot retain an active phase")
            if awaiting != [6] or self.current_phase != 6:
                raise ValueError(
                    "final-review readiness requires Phase 6 awaiting human review"
                )
            if any(
                phase.status is not ResearchPhaseStatus.COMPLETE
                for phase in self.phases[:6]
            ):
                raise ValueError("Phases 0 through 5 must be complete before final review")
        else:
            if active != [self.current_phase]:
                raise ValueError(
                    "exactly the declared current phase must be in progress"
                )
            if awaiting:
                raise ValueError(
                    "an incomplete study cannot await final human review"
                )

        if not self.final_human_review_preserved:
            raise ValueError("the founder's final human review must be preserved")
        if self.final_human_review_completed and not self.ready_for_final_human_review:
            raise ValueError("final review cannot complete before readiness")
        if (
            self.external_publication_authorized
            or self.external_submission_authorized
        ) and not self.final_human_review_completed:
            raise ValueError(
                "publication or submission requires completed final human review"
            )
        if self.scientific_conclusion_authorized and not (
            self.ready_for_final_human_review or self.final_human_review_completed
        ):
            raise ValueError(
                "a scientific conclusion requires a review-ready research release"
            )
        return self


def load_study_completion_audit(path: Path) -> StudyCompletionAudit:
    return StudyCompletionAudit.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_study_completion_audit_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            StudyCompletionAudit.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
