import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.cli import main
from nas_core.domain.discovery import LiteratureSearchStrategy
from nas_core.domain.evidence_review import (
    EvidenceReviewProgress,
    PriorityEvidenceSet,
    load_evidence_review_progress,
    load_priority_evidence_set,
)

ROOT = Path(__file__).parents[1]
STUDY_ROOT = ROOT / "workflows" / "studies" / "breast_clinical_molecular_discordance"
PRIORITY_PATH = STUDY_ROOT / "literature" / "revised_priority_evidence.yaml"
PROGRESS_PATH = STUDY_ROOT / "literature" / "revised_evidence_review_progress.yaml"
SEARCH_PATH = STUDY_ROOT / "literature" / "search_strategy_v0.3.0.yaml"
PRIORITY_SCHEMA_PATH = ROOT / "workflows" / "priority_evidence_set.schema.json"
PROGRESS_SCHEMA_PATH = ROOT / "workflows" / "evidence_review_progress.schema.json"


def load_progress_payload() -> dict[str, object]:
    payload = yaml.safe_load(PROGRESS_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def load_priority_payload() -> dict[str, object]:
    payload = yaml.safe_load(PRIORITY_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def complete_pass(number: int, *, new_ids: list[str] | None = None) -> dict[str, object]:
    return {
        "pass_number": number,
        "status": "complete",
        "seed_evidence_ids": ["PMID:1", "PMID:2"],
        "backward_source": "europe_pmc_references",
        "forward_source": "europe_pmc_citations",
        "backward_candidate_count": 5,
        "forward_candidate_count": 4,
        "unique_candidate_count": 7,
        "screened_candidate_count": 7,
        "new_eligible_evidence_ids": new_ids or [],
        "completed_at": f"2026-07-{23 + number:02d}T12:00:00Z",
    }


def test_checked_in_revised_review_artifacts_are_valid_and_search_executed() -> None:
    priority = load_priority_evidence_set(PRIORITY_PATH)
    progress = load_evidence_review_progress(PROGRESS_PATH)
    search = LiteratureSearchStrategy.model_validate(
        yaml.safe_load(SEARCH_PATH.read_text(encoding="utf-8"))
    )

    assert priority.question_version == "0.3.0"
    assert len(priority.candidates) == 13
    assert priority.maximum_final_evidence_count == 30
    assert all(not item.founder_decision_recorded for item in priority.candidates)
    assert search.status == "locked"
    assert search.retrieval_authorized is True
    assert progress.review_status == "active"
    assert progress.locked_search_executed is True
    assert (
        progress.search_execution_id
        == "a2500aba7ae0277cdd0c572553b74d53622b2d9c8bf011b87bb55fe4f2f1ea9f"
    )
    assert progress.search_receipt_path == "literature/search_receipt_v0.3.1.yaml"
    assert progress.deduplication_complete is True
    assert (
        progress.screening_queue_id
        == "af08a33445641feba853fb292c92b17dd4020cecbae42158a64b430e5278a2a3"
    )
    assert progress.pending_candidate_count == 100
    assert progress.stopping_rule_satisfied is False
    assert progress.novelty_claim_authorized is False
    assert progress.molecular_data_access_authorized is False
    assert progress.outcome_data_access_authorized is False


def test_checked_in_evidence_review_schemas_match_runtime_models() -> None:
    assert json.loads(PRIORITY_SCHEMA_PATH.read_text(encoding="utf-8")) == (
        PriorityEvidenceSet.model_json_schema()
    )
    assert json.loads(PROGRESS_SCHEMA_PATH.read_text(encoding="utf-8")) == (
        EvidenceReviewProgress.model_json_schema()
    )


def test_cli_validates_bound_evidence_review_artifacts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(
        ["evidence-review", "validate", str(PRIORITY_PATH), str(PROGRESS_PATH)]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "13 priority records" in output
    assert "stopping rule satisfied: False" in output


def test_priority_set_cannot_make_autonomous_decisions() -> None:
    payload = load_priority_payload()
    payload["autonomous_screening_decisions_allowed"] = True

    with pytest.raises(ValidationError, match="cannot make screening decisions"):
        PriorityEvidenceSet.model_validate(payload)


def test_final_candidate_state_requires_founder_decision() -> None:
    payload = load_priority_payload()
    candidates = payload["candidates"]  # type: ignore[assignment]
    candidates[0]["review_state"] = "eligible"  # type: ignore[index]

    with pytest.raises(ValidationError, match="founder decision"):
        PriorityEvidenceSet.model_validate(payload)


def test_reappraisal_candidate_requires_prior_artifact() -> None:
    payload = load_priority_payload()
    candidates = payload["candidates"]  # type: ignore[assignment]
    candidate = next(  # type: ignore[call-overload]
        item for item in candidates if item["review_state"] == "pending_reappraisal"
    )
    candidate["prior_artifact"] = None

    with pytest.raises(ValidationError, match="requires the prior appraisal"):
        PriorityEvidenceSet.model_validate(payload)


def test_complete_pass_must_screen_every_unique_candidate() -> None:
    payload = load_progress_payload()
    invalid_pass = complete_pass(1)
    invalid_pass["screened_candidate_count"] = 6
    payload["citation_passes"] = [invalid_pass]

    with pytest.raises(ValidationError, match="screen every unique candidate"):
        EvidenceReviewProgress.model_validate(payload)


def test_false_stopping_rule_claim_is_rejected() -> None:
    payload = load_progress_payload()
    payload["stopping_rule_satisfied"] = True
    payload["review_status"] = "complete"

    with pytest.raises(ValidationError, match="does not match the audited review state"):
        EvidenceReviewProgress.model_validate(payload)


def test_search_execution_requires_id_and_receipt_path() -> None:
    payload = load_progress_payload()
    payload["search_receipt_path"] = None

    with pytest.raises(ValidationError, match="both an execution ID and receipt path"):
        EvidenceReviewProgress.model_validate(payload)


def test_deduplication_requires_queue_and_reconciliation_receipts() -> None:
    payload = load_progress_payload()
    payload["inventory_reconciliation_receipt_path"] = None

    with pytest.raises(ValidationError, match="queue and inventory-reconciliation"):
        EvidenceReviewProgress.model_validate(payload)


def test_two_consecutive_zero_yield_passes_can_satisfy_stopping_rule() -> None:
    payload = load_progress_payload()
    payload.update(
        {
            "review_status": "complete",
            "locked_search_executed": True,
            "deduplication_complete": True,
            "primary_screening_complete": True,
            "eligible_evidence_count": 13,
            "completed_appraisal_count": 12,
            "access_restricted_count": 1,
            "pending_candidate_count": 0,
            "citation_passes": [complete_pass(1), complete_pass(2)],
            "stopping_rule_satisfied": True,
        }
    )

    progress = EvidenceReviewProgress.model_validate(payload)
    assert progress.review_status == "complete"
    assert progress.stopping_rule_satisfied is True


def test_new_eligible_study_resets_two_pass_saturation() -> None:
    payload = load_progress_payload()
    payload.update(
        {
            "locked_search_executed": True,
            "deduplication_complete": True,
            "primary_screening_complete": True,
            "eligible_evidence_count": 13,
            "completed_appraisal_count": 12,
            "access_restricted_count": 1,
            "pending_candidate_count": 0,
            "citation_passes": [
                complete_pass(1),
                complete_pass(2, new_ids=["PMID:NEW"]),
            ],
        }
    )

    progress = EvidenceReviewProgress.model_validate(payload)
    assert progress.stopping_rule_satisfied is False


def test_priority_and_progress_versions_must_match(tmp_path: Path) -> None:
    progress_payload = load_progress_payload()
    progress_payload["priority_set_version"] = "9.9.9"
    mismatched_path = tmp_path / "progress.yaml"
    mismatched_path.write_text(
        yaml.safe_dump(progress_payload, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must identify one version"):
        main(
            [
                "evidence-review",
                "validate",
                str(PRIORITY_PATH),
                str(mismatched_path),
            ]
        )


def test_progress_payload_copy_is_independent() -> None:
    payload = load_progress_payload()
    copied = deepcopy(payload)
    copied["pending_candidate_count"] = 0

    assert payload["pending_candidate_count"] == 100
