import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.domain.research import AnalysisPlan, PlanStatus
from nas_core.governance.exceptions import PolicyDeniedError
from nas_core.governance.registry import SourceRegistry
from nas_core.workflows.analysis_plan import load_analysis_plan

ROOT = Path(__file__).parents[1]
PLAN_PATH = ROOT / "workflows" / "tcga_brca_stage_survival" / "analysis_plan.yaml"
REGISTRY_PATH = ROOT / "data" / "source-registry.yaml"
SCHEMA_PATH = ROOT / "workflows" / "analysis_plan.schema.json"


def _payload() -> dict:
    return yaml.safe_load(PLAN_PATH.read_text(encoding="utf-8"))


def test_first_study_plan_is_typed_and_governed() -> None:
    plan = load_analysis_plan(PLAN_PATH, registry=SourceRegistry.from_yaml(REGISTRY_PATH))

    assert plan.study_id == "NAS-BRCA-001"
    assert plan.status is PlanStatus.PENDING_REVIEW
    assert plan.governance.source_id == "gdc-tcga-open"
    assert len([hypothesis for hypothesis in plan.hypotheses if hypothesis.primary]) == 1


def test_checked_in_schema_matches_runtime_model() -> None:
    checked_in_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert checked_in_schema == AnalysisPlan.model_json_schema()


def test_plan_rejects_multiple_primary_hypotheses() -> None:
    payload = _payload()
    second = deepcopy(payload["hypotheses"][0])
    second["hypothesis_id"] = "H2"
    payload["hypotheses"].append(second)

    with pytest.raises(ValidationError, match="exactly one primary confirmatory"):
        AnalysisPlan.model_validate(payload)


def test_plan_cannot_be_preregistered_without_approval() -> None:
    payload = _payload()
    payload["status"] = "preregistered"

    with pytest.raises(ValidationError, match="requires an approved review"):
        AnalysisPlan.model_validate(payload)


def test_plan_rejects_an_unapproved_research_purpose(tmp_path: Path) -> None:
    payload = _payload()
    payload["governance"]["purpose"] = "commercial-model-training"
    invalid_plan = tmp_path / "analysis_plan.yaml"
    invalid_plan.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(PolicyDeniedError, match="not approved"):
        load_analysis_plan(invalid_plan, registry=SourceRegistry.from_yaml(REGISTRY_PATH))
