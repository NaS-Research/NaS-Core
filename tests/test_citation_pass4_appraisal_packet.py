import hashlib
from pathlib import Path

import yaml

from nas_core.domain.appraisal import FullTextAppraisalProposal

ROOT = Path(__file__).parents[1]
LITERATURE = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
)
PROPOSAL_DIR = LITERATURE / "citation-appraisal-proposals" / "batch-0011"
PACKET = LITERATURE / "FOUNDER_CITATION_APPRAISAL_BATCH_0011_v1.0.0.md"
PROGRESS = (
    LITERATURE / "citation-pass-0004-full-text" / "appraisal-progress-v1.0.0.yaml"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pass4_appraisal_packet_binds_both_proposals() -> None:
    paths = sorted(PROPOSAL_DIR.glob("*.yaml"))
    proposals = [
        FullTextAppraisalProposal.model_validate(yaml.safe_load(path.read_text()))
        for path in paths
    ]
    packet = PACKET.read_text(encoding="utf-8")

    assert [path.stem for path in paths] == [
        "PMC5947827-v1.0.0",
        "PMC9604175-v1.0.0",
    ]
    assert all(item.proposed_evidence_role == "context_only" for item in proposals)
    assert all(item.founder_decision_recorded is False for item in proposals)
    for path in paths:
        assert _sha256(path) in packet
    assert "`I confirm citation appraisal batch 0011 as written.`" in packet


def test_pass4_progress_accounts_for_both_readable_inclusions() -> None:
    progress = yaml.safe_load(PROGRESS.read_text(encoding="utf-8"))

    assert progress["provisional_inclusion_count"] == 2
    assert progress["full_texts_retrieved"] == 1
    assert progress["read_only_full_texts_reviewed"] == 1
    assert progress["appraisals_completed"] == 1
    assert progress["access_restricted_count"] == 0
    assert sum(
        item["status"] == "ready_for_appraisal" for item in progress["records"]
    ) == 1
    assert sum(item["status"] == "completed" for item in progress["records"]) == 1
    assert progress["scientific_conclusions_drawn"] is False


def test_batch_0012_corrects_only_the_mismatched_doi() -> None:
    correction = (
        LITERATURE
        / "citation-appraisal-proposals"
        / "batch-0012"
        / "PMC9604175-v1.0.1.yaml"
    )
    proposal = FullTextAppraisalProposal.model_validate(
        yaml.safe_load(correction.read_text())
    )
    packet = (
        LITERATURE / "FOUNDER_CITATION_APPRAISAL_BATCH_0012_v1.0.0.md"
    ).read_text(encoding="utf-8")

    assert proposal.doi == "10.3390/ijms232012707"
    assert proposal.full_text_sha256 == (
        "7ef0ce57c28959daa8be1624c22fe0595c16dbcb4f404f0afa353eb5331ed142"
    )
    assert proposal.proposed_evidence_role == "context_only"
    assert _sha256(correction) in packet
    assert "`I confirm citation appraisal batch 0012 as written.`" in packet
