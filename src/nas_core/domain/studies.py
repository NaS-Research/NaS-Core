"""Typed identity and lifecycle models for standardized NaS studies."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.programs import StudyRole


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StudyStatus(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    RETIRED = "retired"


class PipelineStage(StrEnum):
    QUESTION = "question"
    LITERATURE = "literature"
    PROTOCOL = "protocol"
    INGESTION = "ingestion"
    ANALYSIS = "analysis"
    EVIDENCE = "evidence"
    RELEASE = "release"


class StageStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETE = "complete"


class StudyManifest(StrictModel):
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    slug: str = Field(pattern=r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
    title: str = Field(min_length=1)
    program_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    role: StudyRole
    status: StudyStatus
    created_at: datetime
    owner: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    artifact_namespace: str = Field(pattern=r"^studies/NAS-[A-Z0-9]+-[0-9]{3}$")

    @model_validator(mode="after")
    def validate_namespace(self) -> StudyManifest:
        if self.artifact_namespace != f"studies/{self.study_id}":
            raise ValueError("artifact namespace must be derived from study_id")
        return self


class StageRecord(StrictModel):
    stage: PipelineStage
    status: StageStatus
    required_artifacts: list[str] = Field(min_length=1)
    completion_gate: str = Field(min_length=1)


class PipelineManifest(StrictModel):
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    pipeline_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    current_stage: PipelineStage
    stages: list[StageRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_stage_sequence(self) -> PipelineManifest:
        expected = list(PipelineStage)
        actual = [record.stage for record in self.stages]
        if actual != expected:
            raise ValueError("pipeline stages must appear once in canonical order")

        active = [
            record.stage for record in self.stages if record.status is StageStatus.IN_PROGRESS
        ]
        if active != [self.current_stage]:
            raise ValueError("exactly the current stage must be in progress")

        for record in self.stages:
            for artifact in record.required_artifacts:
                path = PurePosixPath(artifact)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("required artifact paths must remain inside the study")
        return self
