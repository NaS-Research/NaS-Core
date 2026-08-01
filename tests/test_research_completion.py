from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.domain.research_completion import (
    StudyCompletionAudit,
    load_study_completion_audit,
)
from nas_core.workflows.research_completion import (
    StudyCompletionAuditError,
    StudyCompletionAuditService,
)
from nas_core.workflows.study_scaffold import load_study_manifests

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
AUDIT = STUDY / "reviews" / "RESEARCH_COMPLETION_AUDIT_v1.21.0.yaml"
PIPELINE = STUDY / "pipeline.yaml"
SCHEMA = ROOT / "workflows" / "research_completion_audit.schema.json"


def test_checked_in_completion_audit_proves_current_incomplete_state() -> None:
    audit = load_study_completion_audit(AUDIT)

    validated = StudyCompletionAuditService().validate(
        audit,
        study_root=STUDY,
        pipeline_path=PIPELINE,
    )

    assert validated.current_phase == 1
    assert validated.phases[0].status.value == "complete"
    assert validated.phases[1].status.value == "in_progress"
    assert all(
        phase.status.value == "not_started" for phase in validated.phases[2:]
    )
    assert validated.ready_for_final_human_review is False
    assert validated.final_human_review_preserved is True
    assert validated.final_human_review_completed is False
    assert validated.scientific_conclusion_authorized is False
    assert validated.external_publication_authorized is False
    assert validated.external_submission_authorized is False
    assert validated.phases[1].open_requirements[0].startswith("Complete a no-contact")


def test_study_lifecycle_manifest_records_phase_one_protocol_work() -> None:
    study, pipeline = load_study_manifests(STUDY)

    assert study.status.value == "active"
    assert pipeline.pipeline_version == "1.1.0"
    assert pipeline.current_stage.value == "protocol"
    assert pipeline.stages[0].status.value == "complete"
    assert pipeline.stages[1].status.value == "complete"
    assert pipeline.stages[2].status.value == "in_progress"


def test_completion_audit_rejects_premature_final_review_claim() -> None:
    audit = load_study_completion_audit(AUDIT)
    payload = audit.model_dump(mode="json")
    payload["ready_for_final_human_review"] = True

    with pytest.raises(ValidationError, match="cannot retain an active phase"):
        StudyCompletionAudit.model_validate(payload)


def test_completion_audit_rejects_publication_before_final_review() -> None:
    audit = load_study_completion_audit(AUDIT)
    payload = audit.model_dump(mode="json")
    payload["external_publication_authorized"] = True

    with pytest.raises(ValidationError, match="requires completed final human review"):
        StudyCompletionAudit.model_validate(payload)


def test_completion_audit_rejects_changed_evidence(tmp_path: Path) -> None:
    copied_root = tmp_path / "study"
    copied_root.mkdir()
    question_dir = copied_root / "question"
    question_dir.mkdir()
    question = question_dir / "research_question.yaml"
    question.write_text("changed: true\n", encoding="utf-8")

    audit = load_study_completion_audit(AUDIT)
    payload = audit.model_dump(mode="json")
    payload["phases"][0]["evidence"] = [payload["phases"][0]["evidence"][0]]
    for phase in payload["phases"][1:]:
        phase["evidence"] = []
    reduced = StudyCompletionAudit.model_validate(payload)

    with pytest.raises(StudyCompletionAuditError, match="completion evidence changed"):
        StudyCompletionAuditService().validate(
            reduced,
            study_root=copied_root,
            pipeline_path=PIPELINE,
        )


def test_checked_in_completion_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        StudyCompletionAudit.model_json_schema()
    )
