import hashlib
from pathlib import Path

import yaml

from nas_core.domain.appraisal import (
    FullTextAppraisalProposal,
    load_full_text_appraisal_batch_confirmation,
)

ROOT = Path(__file__).parents[1]
LITERATURE = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
)
PROPOSAL_DIR = LITERATURE / "citation-appraisal-proposals" / "batch-0010"
PACKET = LITERATURE / "FOUNDER_CITATION_APPRAISAL_BATCH_0010_v1.0.0.md"
CONFIRMATION = (
    LITERATURE
    / "FOUNDER_CITATION_APPRAISAL_BATCH_0010_CONFIRMATION_v1.0.0.yaml"
)
PROGRESS = (
    LITERATURE
    / "citation-pass-0003-full-text"
    / "appraisal-progress-v1.0.0.yaml"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pass3_appraisal_packet_binds_all_non_authoritative_proposals() -> None:
    paths = sorted(PROPOSAL_DIR.glob("*.yaml"))
    proposals = [
        FullTextAppraisalProposal.model_validate(yaml.safe_load(path.read_text()))
        for path in paths
    ]
    packet = PACKET.read_text(encoding="utf-8")

    assert [path.stem for path in paths] == [
        "PMC12764145-v1.0.0",
        "PMC3273349-v1.0.0",
        "PMC3733243-v1.0.0",
        "PMC7746197-v1.0.0",
        "PMC7873419-v1.0.0",
    ]
    assert all(item.proposed_evidence_role == "context_only" for item in proposals)
    assert all(item.founder_decision_recorded is False for item in proposals)
    assert all(item.scientific_conclusions_drawn is False for item in proposals)
    for path in paths:
        assert _sha256(path) in packet
    assert "`I confirm citation appraisal batch 0010 as written.`" in packet


def test_pass3_access_and_appraisal_progress_accounts_for_every_inclusion() -> None:
    progress = yaml.safe_load(PROGRESS.read_text(encoding="utf-8"))

    assert progress["provisional_inclusion_count"] == 7
    assert progress["full_texts_retrieved"] == 3
    assert progress["read_only_full_texts_reviewed"] == 2
    assert progress["access_restricted_count"] == 2
    assert progress["appraisals_completed"] == 5
    assert sum(
        item["status"] == "completed" for item in progress["records"]
    ) == 5
    assert sum(
        item["status"] == "access_restricted" for item in progress["records"]
    ) == 2
    assert progress["scientific_conclusions_drawn"] is False


def test_batch_0010_confirmation_is_bound_to_the_exact_packet() -> None:
    confirmation = load_full_text_appraisal_batch_confirmation(CONFIRMATION)

    assert confirmation.batch_number == 10
    assert confirmation.packet_sha256 == _sha256(PACKET)
    assert confirmation.proposal_count == 5
    assert confirmation.confirmation_statement == (
        "I confirm citation appraisal batch 0010 as written."
    )
    assert confirmation.founder_authorized is True
    assert confirmation.founder_role_conflict_disclosed is True
