import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.domain.programs import (
    OncologyProgramCharter,
    ProgramStage,
    ResearchQuestionIntake,
)
from nas_core.workflows.program import load_program_charter, load_research_question

ROOT = Path(__file__).parents[1]
CHARTER_PATH = ROOT / "workflows" / "oncology" / "program_charter.yaml"
QUESTION_PATH = ROOT / "workflows" / "templates" / "research_question_intake.yaml"
DISCOVERY_QUESTION_PATH = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "question"
    / "research_question.yaml"
)
CHARTER_SCHEMA_PATH = ROOT / "workflows" / "program_charter.schema.json"
QUESTION_SCHEMA_PATH = ROOT / "workflows" / "research_question.schema.json"


def _question_payload() -> dict:
    return yaml.safe_load(QUESTION_PATH.read_text(encoding="utf-8"))


def test_oncology_charter_identifies_qualification_stage() -> None:
    charter = load_program_charter(CHARTER_PATH)

    assert charter.program_id == "NAS-ONC-001"
    assert charter.current_stage is ProgramStage.PLATFORM_QUALIFICATION
    assert charter.studies[0].study_id == "NAS-BRCA-001"
    assert charter.studies[0].role.value == "qualification"


def test_research_question_template_is_valid_but_not_literature_ready() -> None:
    question = load_research_question(QUESTION_PATH)

    assert question.status.value == "proposed"
    assert question.literature_status.value == "not_ready"
    assert question.selection_scores.total == 0


def test_proposed_discovery_question_is_valid_but_not_literature_ready() -> None:
    question = load_research_question(DISCOVERY_QUESTION_PATH)

    assert question.question_id == "NAS-RQ-BRCA002"
    assert question.status.value == "proposed"
    assert question.literature_status.value == "not_ready"
    assert question.selection_scores.total == 30


def test_selected_question_requires_approval() -> None:
    payload = _question_payload()
    payload["status"] = "selected"

    with pytest.raises(ValidationError, match="requires an approved review"):
        ResearchQuestionIntake.model_validate(payload)


def test_literature_cannot_start_before_question_selection() -> None:
    payload = _question_payload()
    payload["literature_status"] = "ready"

    with pytest.raises(ValidationError, match="literature work requires"):
        ResearchQuestionIntake.model_validate(payload)


def test_approved_selected_question_can_become_literature_ready() -> None:
    payload = deepcopy(_question_payload())
    payload["status"] = "selected"
    payload["literature_status"] = "ready"
    payload["reviews"][0] = {
        "reviewer": "Synthetic Reviewer",
        "role": "Scientific and product reviewer",
        "decision": "approved",
        "reviewed_at": "2026-07-20T16:00:00Z",
        "rationale": "Synthetic approval used only by automated tests.",
    }

    question = ResearchQuestionIntake.model_validate(payload)

    assert question.status.value == "selected"
    assert question.literature_status.value == "ready"


def test_checked_in_program_schemas_match_runtime_models() -> None:
    charter_schema = json.loads(CHARTER_SCHEMA_PATH.read_text(encoding="utf-8"))
    question_schema = json.loads(QUESTION_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert charter_schema == OncologyProgramCharter.model_json_schema()
    assert question_schema == ResearchQuestionIntake.model_json_schema()
