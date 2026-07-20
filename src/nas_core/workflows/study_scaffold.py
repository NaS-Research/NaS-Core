"""Create consistent, Git-safe study workspaces."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from nas_core.domain.programs import StudyRole
from nas_core.domain.studies import (
    PipelineManifest,
    PipelineStage,
    StageRecord,
    StageStatus,
    StudyManifest,
    StudyStatus,
)

STAGE_DETAILS: dict[PipelineStage, tuple[list[str], str]] = {
    PipelineStage.QUESTION: (
        ["question/research_question.yaml"],
        "Question is selected, approved, and marked literature-ready.",
    ),
    PipelineStage.LITERATURE: (
        ["literature/protocol.md", "literature/search_strategy.yaml"],
        "Search protocol is locked before evidence retrieval.",
    ),
    PipelineStage.PROTOCOL: (
        ["protocol/analysis_plan.yaml"],
        "Analysis plan is independently approved, preregistered, and Git-tagged.",
    ),
    PipelineStage.INGESTION: (
        ["ingestion/README.md"],
        "Governed immutable dataset snapshot is verified.",
    ),
    PipelineStage.ANALYSIS: (
        ["analysis/README.md", "tests/README.md"],
        "Deterministic pipeline and synthetic tests pass; run artifacts are frozen.",
    ),
    PipelineStage.EVIDENCE: (
        ["evidence/README.md", "reviews/README.md"],
        "Claims trace to reviewed results or external evidence, including null findings.",
    ),
    PipelineStage.RELEASE: (
        ["release/README.md"],
        "Immutable research release is independently approved.",
    ),
}


def initialize_study(
    root: Path,
    *,
    study_id: str,
    slug: str,
    title: str,
    program_id: str,
    role: StudyRole,
    created_at: datetime | None = None,
) -> Path:
    """Create a standardized study directory without overwriting existing work."""

    timestamp = created_at or datetime.now(UTC)
    manifest = StudyManifest(
        schema_version="1.0.0",
        study_id=study_id,
        slug=slug,
        title=title,
        program_id=program_id,
        role=role,
        status=StudyStatus.PROPOSED,
        created_at=timestamp,
        owner="To be assigned",
        objective="Define the decision-led objective before collecting evidence or data.",
        artifact_namespace=f"studies/{study_id}",
    )
    pipeline = PipelineManifest(
        schema_version="1.0.0",
        study_id=study_id,
        pipeline_version="1.0.0",
        current_stage=PipelineStage.QUESTION,
        stages=[
            StageRecord(
                stage=stage,
                status=(
                    StageStatus.IN_PROGRESS
                    if stage is PipelineStage.QUESTION
                    else StageStatus.NOT_STARTED
                ),
                required_artifacts=details[0],
                completion_gate=details[1],
            )
            for stage, details in STAGE_DETAILS.items()
        ],
    )

    resolved_root = root.expanduser().resolve()
    target = resolved_root / manifest.slug
    if target.exists():
        raise FileExistsError(f"study directory already exists: {target}")

    target.mkdir(parents=True)
    _write_yaml(target / "study.yaml", manifest.model_dump(mode="json"))
    _write_yaml(target / "pipeline.yaml", pipeline.model_dump(mode="json"))
    (target / "README.md").write_text(_study_readme(manifest), encoding="utf-8")

    for stage, (artifacts, gate) in STAGE_DETAILS.items():
        stage_dir = target / stage.value
        stage_dir.mkdir()
        (stage_dir / "README.md").write_text(
            _stage_readme(stage, artifacts, gate), encoding="utf-8"
        )
    (target / "tests").mkdir()
    (target / "tests" / "README.md").write_text(
        "# Synthetic tests\n\nStore study-specific tests and synthetic fixtures here.\n",
        encoding="utf-8",
    )
    (target / "reviews").mkdir()
    (target / "reviews" / "README.md").write_text(
        "# Reviews\n\nRecord review decisions and resolved comments; "
        "never store credentials or PHI.\n",
        encoding="utf-8",
    )
    return target


def load_study_manifests(path: Path) -> tuple[StudyManifest, PipelineManifest]:
    """Validate identity and lifecycle manifests and their shared study ID."""

    study = StudyManifest.model_validate(_read_yaml(path / "study.yaml"))
    pipeline = PipelineManifest.model_validate(_read_yaml(path / "pipeline.yaml"))
    if study.study_id != pipeline.study_id:
        raise ValueError("study and pipeline manifests must use the same study_id")
    if study.slug != path.name:
        raise ValueError("study slug must match the directory name")
    for record in pipeline.stages:
        if record.status is StageStatus.COMPLETE:
            missing = [
                artifact
                for artifact in record.required_artifacts
                if not (path / artifact).is_file()
            ]
            if missing:
                raise ValueError(
                    f"completed stage {record.stage.value} is missing artifacts: "
                    f"{', '.join(missing)}"
                )
    return study, pipeline


def write_study_schemas(study_path: Path, pipeline_path: Path) -> None:
    """Write canonical JSON Schemas for study and lifecycle manifests."""

    for path, model in (
        (study_path, StudyManifest),
        (pipeline_path, PipelineManifest),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        path.write_text(f"{payload}\n", encoding="utf-8")


def _read_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _study_readme(study: StudyManifest) -> str:
    return f"""# {study.study_id}: {study.title}

This directory contains versioned definitions, deterministic code, tests, and
reviews for one NaS study. It must not contain raw data, credentials, PHI,
embeddings, model weights, or generated research artifacts.

## Identity

- Program: `{study.program_id}`
- Role: `{study.role.value}`
- Artifact namespace: `{study.artifact_namespace}`

Update `pipeline.yaml` only when a stage's completion gate is supported by
reviewed artifacts. Large artifacts belong under `NAS_DATA_ROOT`, keyed by the
artifact namespace and immutable snapshot, run, or release identifiers.
"""


def _stage_readme(stage: PipelineStage, artifacts: list[str], gate: str) -> str:
    listed = "\n".join(f"- `{artifact}`" for artifact in artifacts)
    return f"""# {stage.value.replace("_", " ").title()}

Required artifacts:

{listed}

Completion gate: {gate}
"""
