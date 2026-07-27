import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

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
REVISED_SCREENING_PROTOCOL_PATH = (
    STUDY_ROOT / "literature" / "REVISED_SCREENING_PROTOCOL.md"
)
PRIORITY_PACKET_PATH = (
    STUDY_ROOT / "literature" / "FOUNDER_PRIORITY_SCREENING_PACKET_v1.0.0.md"
)


def load_progress_payload() -> dict[str, Any]:
    payload = yaml.safe_load(PROGRESS_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def load_priority_payload() -> dict[str, Any]:
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
        "closure_id": f"{number:064x}",
        "closure_receipt_path": f"literature/citation-chain/pass-{number:04d}-closure.yaml",
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
    assert all(item.founder_decision_recorded for item in priority.candidates)
    assert all(item.review_state == "eligible" for item in priority.candidates)
    assert search.status == "locked"
    assert search.retrieval_authorized is True
    assert progress.review_status == "active"
    assert progress.protocol_version == "0.2.5"
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
    assert (
        progress.screening_progress_id
        == "7b90c37aa7fcab3607b5fde99c6aa97a0a3e440889b0d44727ba4f685863218c"
    )
    assert progress.screening_progress_receipt_path == (
        "literature/revised-screening-progress/batch-0002.yaml"
    )
    assert progress.primary_screening_complete is True
    assert progress.eligible_evidence_count == 80
    assert progress.completed_appraisal_count == 68
    assert progress.access_restricted_count == 12
    assert progress.pending_candidate_count == 0
    assert progress.uncapped_saturation_inventory_active is True
    assert progress.core_synthesis_maximum == 30
    assert len(progress.citation_passes) == 4
    assert len(progress.citation_passes[0].new_eligible_evidence_ids) == 32
    assert (
        progress.citation_passes[0].closure_id
        == "3f7037cada1872601b75a79a1d13a831c7f7a57c5543038a3e0e3c5803cd9676"
    )
    assert len(progress.citation_passes[1].new_eligible_evidence_ids) == 9
    assert (
        progress.citation_passes[1].closure_id
        == "995b8b3f93410642ef508366eccad225e3c3c8003867e1988d3cb89513f6f9a7"
    )
    assert len(progress.citation_passes[2].new_eligible_evidence_ids) == 7
    assert (
        progress.citation_passes[2].closure_id
        == "08fcf9c6fa1fec051fd33ed2daee0cc8aa119dff855f921735dab97eff4a33d9"
    )
    assert len(progress.citation_passes[3].new_eligible_evidence_ids) == 2
    assert (
        progress.citation_passes[3].closure_id
        == "7880f29b90aed61ba21c0f8c73515ae03423c1b3cacd20caf2265e7c98d5a1ff"
    )
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


def test_founder_priority_packet_is_complete_and_nondecisional() -> None:
    protocol = REVISED_SCREENING_PROTOCOL_PATH.read_text(encoding="utf-8")
    packet = PRIORITY_PACKET_PATH.read_text(encoding="utf-8")

    assert "Version: `1.1.0`" in protocol
    assert "af08a334…8a2a3" in protocol
    assert "Each of the 100 records" in protocol
    assert "Status: **Founder confirmed; append-only batch recorded**" in packet
    assert "records 13 inclusions and 87 pending records" in packet
    assert set(re.findall(r"^\| (\d{8}) \|", packet, flags=re.MULTILINE)) == {
        "19204204",
        "28062443",
        "22196354",
        "25479802",
        "33255759",
        "35974007",
        "37008073",
        "32826944",
        "37857634",
        "41064593",
        "41390542",
        "25788628",
        "25849221",
    }


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
    candidates = payload["candidates"]
    candidates[0]["founder_decision_recorded"] = False

    with pytest.raises(ValidationError, match="founder decision"):
        PriorityEvidenceSet.model_validate(payload)


def test_reappraisal_candidate_requires_prior_artifact() -> None:
    payload = load_priority_payload()
    candidates = payload["candidates"]
    candidate = candidates[0]
    candidate["review_state"] = "pending_reappraisal"
    candidate["founder_decision_recorded"] = False
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


def test_complete_pass_requires_closure_receipt() -> None:
    payload = load_progress_payload()
    invalid_pass = complete_pass(1)
    invalid_pass["closure_id"] = None
    invalid_pass["closure_receipt_path"] = None
    payload["citation_passes"] = [invalid_pass]

    with pytest.raises(ValidationError, match="requires its closure receipt"):
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


def test_partial_screening_progress_requires_id_and_receipt() -> None:
    payload = load_progress_payload()
    payload["screening_progress_receipt_path"] = None

    with pytest.raises(ValidationError, match="both a progress ID and receipt path"):
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


def test_trailing_planned_pass_prevents_stopping_rule() -> None:
    payload = load_progress_payload()
    planned = complete_pass(3)
    planned.update(
        {
            "status": "planned",
            "backward_candidate_count": 0,
            "forward_candidate_count": 0,
            "unique_candidate_count": 0,
            "screened_candidate_count": 0,
            "new_eligible_evidence_ids": [],
            "completed_at": None,
            "closure_id": None,
            "closure_receipt_path": None,
        }
    )
    payload.update(
        {
            "review_status": "complete",
            "eligible_evidence_count": 13,
            "completed_appraisal_count": 12,
            "access_restricted_count": 1,
            "pending_candidate_count": 0,
            "citation_passes": [complete_pass(1), complete_pass(2), planned],
            "stopping_rule_satisfied": True,
        }
    )

    with pytest.raises(ValidationError, match="does not match the audited review state"):
        EvidenceReviewProgress.model_validate(payload)


def test_loader_rejects_progress_that_disagrees_with_closure(tmp_path: Path) -> None:
    progress_payload = load_progress_payload()
    progress_payload["citation_passes"][0]["backward_candidate_count"] = 980
    for citation_pass in progress_payload["citation_passes"]:
        pass_number = citation_pass["pass_number"]
        citation_pass["closure_receipt_path"] = str(
            STUDY_ROOT
            / "literature"
            / "citation-chain"
            / f"pass-{pass_number:04d}-closure.yaml"
        )
    mismatched_path = tmp_path / "progress.yaml"
    mismatched_path.write_text(
        yaml.safe_dump(progress_payload, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match its closure"):
        load_evidence_review_progress(mismatched_path)


def test_priority_and_progress_versions_must_match(tmp_path: Path) -> None:
    progress_payload = load_progress_payload()
    progress_payload["priority_set_version"] = "9.9.9"
    for citation_pass in progress_payload["citation_passes"]:
        pass_number = citation_pass["pass_number"]
        citation_pass["closure_receipt_path"] = str(
            STUDY_ROOT
            / "literature"
            / "citation-chain"
            / f"pass-{pass_number:04d}-closure.yaml"
        )
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
    copied["pending_candidate_count"] = 30

    assert payload["pending_candidate_count"] == 0
