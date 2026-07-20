import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.domain.programs import StudyRole
from nas_core.domain.studies import PipelineManifest, PipelineStage, StageStatus, StudyManifest
from nas_core.workflows.study_scaffold import initialize_study, load_study_manifests

ROOT = Path(__file__).parents[1]
STUDY_SCHEMA_PATH = ROOT / "workflows" / "study.schema.json"
PIPELINE_SCHEMA_PATH = ROOT / "workflows" / "pipeline.schema.json"


def _initialize(root: Path) -> Path:
    return initialize_study(
        root,
        study_id="NAS-BRCA-002",
        slug="example_biomarker_study",
        title="Synthetic biomarker study",
        program_id="NAS-ONC-001",
        role=StudyRole.DISCOVERY,
        created_at=datetime(2026, 7, 20, 18, 0, tzinfo=UTC),
    )


def test_initialize_study_creates_canonical_workspace(tmp_path: Path) -> None:
    path = _initialize(tmp_path / "studies")

    study, pipeline = load_study_manifests(path)

    assert study.study_id == "NAS-BRCA-002"
    assert study.artifact_namespace == "studies/NAS-BRCA-002"
    assert pipeline.current_stage is PipelineStage.QUESTION
    assert pipeline.stages[0].status is StageStatus.IN_PROGRESS
    assert all(stage.status is StageStatus.NOT_STARTED for stage in pipeline.stages[1:])
    assert [stage.stage for stage in pipeline.stages] == list(PipelineStage)
    for directory in (*PipelineStage, "tests", "reviews"):
        name = directory.value if isinstance(directory, PipelineStage) else directory
        assert (path / name / "README.md").is_file()


def test_initialize_study_never_overwrites_an_existing_workspace(tmp_path: Path) -> None:
    root = tmp_path / "studies"
    path = _initialize(root)
    marker = path / "README.md"
    original = marker.read_text(encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        _initialize(root)

    assert marker.read_text(encoding="utf-8") == original


def test_initialize_study_rejects_unsafe_or_noncanonical_slug(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="slug"):
        initialize_study(
            tmp_path / "studies",
            study_id="NAS-BRCA-002",
            slug="../outside",
            title="Synthetic biomarker study",
            program_id="NAS-ONC-001",
            role=StudyRole.DISCOVERY,
        )


def test_validate_rejects_mismatched_directory_slug(tmp_path: Path) -> None:
    path = _initialize(tmp_path / "studies")
    moved = path.with_name("wrong_slug")
    path.rename(moved)

    with pytest.raises(ValueError, match="directory name"):
        load_study_manifests(moved)


def test_checked_in_study_schemas_match_runtime_models() -> None:
    study_schema = json.loads(STUDY_SCHEMA_PATH.read_text(encoding="utf-8"))
    pipeline_schema = json.loads(PIPELINE_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert study_schema == StudyManifest.model_json_schema()
    assert pipeline_schema == PipelineManifest.model_json_schema()
