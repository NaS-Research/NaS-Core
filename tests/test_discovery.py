import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.domain.discovery import (
    DataFeasibilitySpecification,
    LiteratureSearchStrategy,
    PhaseZeroPlan,
    load_phase_zero_artifacts,
)

ROOT = Path(__file__).parents[1]
STUDY_ROOT = ROOT / "workflows" / "studies" / "breast_clinical_molecular_discordance"
PLAN_PATH = STUDY_ROOT / "question" / "phase_zero_plan.yaml"
SEARCH_PATH = STUDY_ROOT / "literature" / "search_strategy.yaml"
FEASIBILITY_PATH = STUDY_ROOT / "ingestion" / "data_feasibility.yaml"
PLAN_SCHEMA_PATH = ROOT / "workflows" / "phase_zero_plan.schema.json"
SEARCH_SCHEMA_PATH = ROOT / "workflows" / "literature_search.schema.json"
FEASIBILITY_SCHEMA_PATH = ROOT / "workflows" / "data_feasibility.schema.json"


def test_checked_in_phase_zero_package_is_typed_and_bound() -> None:
    plan, search, feasibility = load_phase_zero_artifacts(
        PLAN_PATH,
        SEARCH_PATH,
        FEASIBILITY_PATH,
    )

    assert plan.study_id == "NAS-BRCA-002"
    assert plan.status == "in_progress"
    assert search.status == "locked"
    assert search.retrieval_authorized is True
    assert plan.authorization is not None
    assert plan.authorization.decision == "approved"
    assert feasibility.outcome_data_access_authorized is False


def test_checked_in_discovery_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA_PATH.read_text()) == PhaseZeroPlan.model_json_schema()
    assert (
        json.loads(SEARCH_SCHEMA_PATH.read_text()) == LiteratureSearchStrategy.model_json_schema()
    )
    assert (
        json.loads(FEASIBILITY_SCHEMA_PATH.read_text())
        == DataFeasibilitySpecification.model_json_schema()
    )


def test_draft_search_cannot_authorize_retrieval() -> None:
    payload = deepcopy(yaml.safe_load(SEARCH_PATH.read_text()))
    payload["status"] = "draft"
    payload["retrieval_authorized"] = True

    with pytest.raises(ValidationError, match="draft search strategy cannot authorize"):
        LiteratureSearchStrategy.model_validate(payload)


def test_draft_feasibility_cannot_authorize_outcome_access() -> None:
    payload = deepcopy(yaml.safe_load(FEASIBILITY_PATH.read_text()))
    payload["status"] = "draft"
    payload["outcome_data_access_authorized"] = True

    with pytest.raises(ValidationError, match="cannot authorize outcome access"):
        DataFeasibilitySpecification.model_validate(payload)


def test_phase_zero_artifacts_must_share_question_version(tmp_path: Path) -> None:
    payload = deepcopy(yaml.safe_load(SEARCH_PATH.read_text()))
    payload["question_version"] = "0.3.0"
    mismatched = tmp_path / "search.yaml"
    mismatched.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="same study question version"):
        load_phase_zero_artifacts(PLAN_PATH, mismatched, FEASIBILITY_PATH)


def test_retrieval_requires_founder_authorization(tmp_path: Path) -> None:
    payload = deepcopy(yaml.safe_load(PLAN_PATH.read_text()))
    payload["authorization"] = None
    unauthorized = tmp_path / "plan.yaml"
    unauthorized.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="requires founder Phase 0 authorization"):
        load_phase_zero_artifacts(unauthorized, SEARCH_PATH, FEASIBILITY_PATH)


def test_phase_zero_never_authorizes_outcome_data_access(tmp_path: Path) -> None:
    payload = deepcopy(yaml.safe_load(FEASIBILITY_PATH.read_text()))
    payload["outcome_data_access_authorized"] = True
    authorized = tmp_path / "feasibility.yaml"
    authorized.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="cannot authorize outcome-bearing data access"):
        load_phase_zero_artifacts(PLAN_PATH, SEARCH_PATH, authorized)
