"""Load and publish schemas for decision-led research program artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel

from nas_core.domain.programs import OncologyProgramCharter, ResearchQuestionIntake


def _load[ProgramArtifact: BaseModel](path: Path, model: type[ProgramArtifact]) -> ProgramArtifact:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return model.model_validate(payload)


def load_program_charter(path: Path) -> OncologyProgramCharter:
    return _load(path, OncologyProgramCharter)


def load_research_question(path: Path) -> ResearchQuestionIntake:
    return _load(path, ResearchQuestionIntake)


def write_model_schema(path: Path, model: type[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
    path.write_text(f"{payload}\n", encoding="utf-8")
