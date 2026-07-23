import csv
import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.domain.discovery import (
    DataFeasibilityAssessment,
    DataFeasibilitySpecification,
    LiteratureSearchStrategy,
    NoveltyMemorandum,
    PhaseZeroGateDecision,
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
NOVELTY_PATH = STUDY_ROOT / "literature" / "novelty_memorandum.yaml"
SOURCE_ASSESSMENT_PATH = STUDY_ROOT / "ingestion" / "source_feasibility_assessment.yaml"
GATE_DECISION_PATH = STUDY_ROOT / "reviews" / "FOUNDER_PHASE_ZERO_GATE_DECISION_v0.2.0.yaml"
EVIDENCE_MATRIX_PATH = STUDY_ROOT / "literature" / "evidence_matrix.csv"
REVISED_PLAN_PATH = STUDY_ROOT / "question" / "phase_zero_plan_v0.3.0.yaml"
REVISED_SEARCH_PATH = STUDY_ROOT / "literature" / "search_strategy_v0.3.0.yaml"
REVISED_FEASIBILITY_PATH = STUDY_ROOT / "ingestion" / "data_feasibility_v0.3.0.yaml"


def test_checked_in_phase_zero_package_is_typed_and_bound() -> None:
    plan, search, feasibility = load_phase_zero_artifacts(
        PLAN_PATH,
        SEARCH_PATH,
        FEASIBILITY_PATH,
    )

    assert plan.study_id == "NAS-BRCA-002"
    assert plan.status == "changes_requested"
    assert search.status == "locked"
    assert search.retrieval_authorized is True
    assert plan.authorization is not None
    assert plan.authorization.decision == "approved"
    assert feasibility.outcome_data_access_authorized is False
    assert feasibility.status == "complete"


def test_checked_in_revised_phase_zero_package_is_authorized_and_bound() -> None:
    plan, search, feasibility = load_phase_zero_artifacts(
        REVISED_PLAN_PATH,
        REVISED_SEARCH_PATH,
        REVISED_FEASIBILITY_PATH,
    )

    assert plan.study_id == "NAS-BRCA-002"
    assert plan.question_version == "0.3.0"
    assert plan.status == "in_progress"
    assert plan.authorization is not None
    assert plan.authorization.decision == "approved"
    assert search.status == "locked"
    assert search.strategy_version == "0.2.4"
    assert search.retrieval_authorized is True
    assert feasibility.status == "draft"
    assert feasibility.discovery_source_id == "gdc-tcga-open"
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


def test_checked_in_phase_zero_outputs_preserve_no_go_boundary() -> None:
    novelty = NoveltyMemorandum.model_validate(
        yaml.safe_load(NOVELTY_PATH.read_text())
    )
    feasibility = DataFeasibilityAssessment.model_validate(
        yaml.safe_load(SOURCE_ASSESSMENT_PATH.read_text())
    )
    decision = PhaseZeroGateDecision.model_validate(
        yaml.safe_load(GATE_DECISION_PATH.read_text())
    )

    assert novelty.evidence_review.review_disposition == "terminated_by_no_go"
    assert novelty.novelty_claim_authorized is False
    assert feasibility.metadata_only is True
    assert feasibility.outcome_data_accessed is False
    assert decision.decision == "change"
    assert decision.preregistration_authorized is False
    assert decision.outcome_data_access_authorized is False


def test_change_decision_cannot_authorize_preregistration() -> None:
    payload = yaml.safe_load(GATE_DECISION_PATH.read_text())
    payload["preregistration_authorized"] = True

    with pytest.raises(ValidationError, match="only a go"):
        PhaseZeroGateDecision.model_validate(payload)


def test_evidence_matrix_contains_each_completed_appraisal_once() -> None:
    with EVIDENCE_MATRIX_PATH.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))

    assert len(rows) == 8
    assert {row["citation_id"] for row in rows} == {
        "PMC10587090",
        "PMC1468408",
        "PMC3275466",
        "PMC3413822",
        "PMC4166472",
        "PMC5001207",
        "PMC7376512",
        "PMC7442834",
    }
    assert all(row["screening_status"].startswith("included_") for row in rows)
