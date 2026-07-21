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

    with pytest.raises(ValidationError, match="requires all gate reviews approved"):
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
        "review_type": "internal_self_review",
        "required_for_gate": True,
        "decision": "approved",
        "reviewed_at": "2026-07-20T16:00:00Z",
        "rationale": "Synthetic approval used only by automated tests.",
    }

    question = ResearchQuestionIntake.model_validate(payload)

    assert question.status.value == "selected"
    assert question.literature_status.value == "ready"


def test_selected_question_requires_every_recorded_review_approved() -> None:
    payload = deepcopy(_question_payload())
    payload["status"] = "selected"
    payload["reviews"][0] = {
        "reviewer": "Synthetic Scientific Reviewer",
        "role": "Scientific reviewer",
        "review_type": "internal_self_review",
        "required_for_gate": True,
        "decision": "approved",
        "reviewed_at": "2026-07-20T16:00:00Z",
        "rationale": "Synthetic approval used only by automated tests.",
    }
    payload["reviews"].append(
        {
            "reviewer": "Synthetic Statistical Reviewer",
            "role": "Biostatistical reviewer",
            "review_type": "independent_human_review",
            "required_for_gate": True,
            "decision": "pending",
            "reviewed_at": None,
            "rationale": "Synthetic pending review used only by automated tests.",
        }
    )

    with pytest.raises(ValidationError, match="requires all gate reviews approved"):
        ResearchQuestionIntake.model_validate(payload)


def test_ai_review_cannot_authorize_question_selection() -> None:
    payload = deepcopy(_question_payload())
    payload["status"] = "selected"
    payload["reviews"] = [
        {
            "reviewer": "Synthetic AI Reviewer",
            "role": "AI-assisted reviewer",
            "review_type": "ai_assisted_internal_review",
            "required_for_gate": True,
            "decision": "approved",
            "reviewed_at": "2026-07-20T16:00:00Z",
            "rationale": "Synthetic AI review used only by automated tests.",
        }
    ]

    with pytest.raises(ValidationError, match="AI-assisted review cannot"):
        ResearchQuestionIntake.model_validate(payload)


def test_nonrequired_ai_advice_does_not_block_founder_approval() -> None:
    payload = deepcopy(_question_payload())
    payload["status"] = "selected"
    payload["literature_status"] = "ready"
    payload["reviews"][0] = {
        "reviewer": "Synthetic Founder",
        "role": "Founder and study lead",
        "review_type": "internal_self_review",
        "required_for_gate": True,
        "decision": "approved",
        "reviewed_at": "2026-07-20T16:00:00Z",
        "rationale": "Synthetic founder approval used only by automated tests.",
    }
    payload["reviews"][1] = {
        "reviewer": "Synthetic AI Reviewer",
        "role": "AI-assisted reviewer",
        "review_type": "ai_assisted_internal_review",
        "required_for_gate": False,
        "decision": "advisory_complete",
        "reviewed_at": "2026-07-20T15:00:00Z",
        "rationale": "Synthetic advisory review used only by automated tests.",
    }

    question = ResearchQuestionIntake.model_validate(payload)

    assert question.status.value == "selected"
    assert question.literature_status.value == "ready"


def test_human_review_cannot_use_ai_advisory_decision() -> None:
    payload = deepcopy(_question_payload())
    payload["reviews"][0]["decision"] = "advisory_complete"
    payload["reviews"][0]["reviewed_at"] = "2026-07-20T16:00:00Z"

    with pytest.raises(ValidationError, match="only AI-assisted review"):
        ResearchQuestionIntake.model_validate(payload)


def test_checked_in_program_schemas_match_runtime_models() -> None:
    charter_schema = json.loads(CHARTER_SCHEMA_PATH.read_text(encoding="utf-8"))
    question_schema = json.loads(QUESTION_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert charter_schema == OncologyProgramCharter.model_json_schema()
    assert question_schema == ResearchQuestionIntake.model_json_schema()
