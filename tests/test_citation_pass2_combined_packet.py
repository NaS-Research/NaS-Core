import csv
import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.appraisal import (
    load_full_text_appraisal,
    load_full_text_inventory,
)
from nas_core.domain.citation_chain import load_citation_founder_packet_receipt
from nas_core.domain.citation_confirmation import (
    CitationDecisionLedgerReceipt,
    CitationFounderConfirmation,
    write_citation_decision_ledger_receipt,
)
from nas_core.domain.citation_reconciliation import (
    CitationInclusionReconciliationReceipt,
    write_citation_inclusion_reconciliation_receipt,
)
from nas_core.domain.evidence_amendment import (
    load_citation_access_queue_receipt,
    load_evidence_cap_amendment_activation_receipt,
    write_citation_pass_appraisal_queue_receipt,
    write_evidence_cap_amendment_activation_receipt,
)
from nas_core.retrieval.citation_confirmation import (
    CitationDecisionConfirmationService,
)
from nas_core.retrieval.citation_reconciliation import (
    CitationInclusionReconciliationService,
)
from nas_core.retrieval.evidence_amendment import (
    CitationAccessInventoryService,
    CitationPassAppraisalQueueService,
    EvidenceCapAmendmentError,
)
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
LITERATURE = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
)
FIRST_APPENDIX = LITERATURE / "FOUNDER_CITATION_PASS_0002_APPENDIX_v1.0.0.csv"
FIRST_PACKET = LITERATURE / "FOUNDER_CITATION_PASS_0002_PACKET_v1.0.0.md"
SECOND_APPENDIX = (
    LITERATURE / "FOUNDER_CITATION_PASS_0002_ADJUDICATION_APPENDIX_v1.0.0.csv"
)
SECOND_PACKET = (
    LITERATURE / "FOUNDER_CITATION_PASS_0002_ADJUDICATION_PACKET_v1.0.0.md"
)
COMBINED_REVIEW = LITERATURE / "FOUNDER_CITATION_PASS_0002_COMBINED_REVIEW_v1.0.0.md"
FIRST_RECEIPT = LITERATURE / "citation-chain" / "pass-0002-founder-packet.yaml"
SECOND_RECEIPT = (
    LITERATURE / "citation-chain" / "pass-0002-adjudication-packet.yaml"
)
INVENTORY = (
    LITERATURE
    / "revised-full-text"
    / "inventory"
    / "access_inventory_v0.3.2.yaml"
)
APPRAISAL_DIRS = (
    LITERATURE / "revised-appraisals",
    LITERATURE / "citation-appraisals",
)
ACTIVE_AMENDMENT = (
    LITERATURE / "evidence-cap-amendment-activation-v0.2.5.yaml"
)
NOW = datetime(2026, 7, 26, 19, 0, tzinfo=UTC)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _simulate_confirmation(
    store: InMemoryObjectStore,
) -> CitationDecisionLedgerReceipt:
    first = load_citation_founder_packet_receipt(FIRST_RECEIPT)
    second = load_citation_founder_packet_receipt(SECOND_RECEIPT)
    confirmation = CitationFounderConfirmation(
        study_id="NAS-BRCA-002",
        pass_number=2,
        first_packet_sha256=first.packet_sha256,
        first_appendix_sha256=first.appendix_sha256,
        second_packet_sha256=second.packet_sha256,
        second_appendix_sha256=second.appendix_sha256,
        confirmation_statement=(
            "I confirm both checksum-bound citation pass 2 packets as written."
        ),
        founder_id="dalron-j-robertson",
        founder_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        confirmed_at=NOW,
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )
    return CitationDecisionConfirmationService(store=store).confirm(
        first,
        second,
        confirmation,
        first_packet_path=FIRST_PACKET,
        first_appendix_path=FIRST_APPENDIX,
        second_packet_path=SECOND_PACKET,
        second_appendix_path=SECOND_APPENDIX,
        code_revision="64a6c2f",
    )


def _simulate_reconciliation(
    store: InMemoryObjectStore,
    decision: CitationDecisionLedgerReceipt,
) -> CitationInclusionReconciliationReceipt:
    inventory = load_full_text_inventory(INVENTORY)
    appraisal_paths = sorted(
        path for directory in APPRAISAL_DIRS for path in directory.glob("*.yaml")
    )
    appraisals = [load_full_text_appraisal(path) for path in appraisal_paths]
    return CitationInclusionReconciliationService(store=store).reconcile(
        decision,
        inventory,
        appraisals,
        code_revision="64a6c2f",
        reconciled_at=NOW,
    )


def test_pass2_combined_packet_covers_every_candidate_once() -> None:
    first = _rows(FIRST_APPENDIX)
    second = _rows(SECOND_APPENDIX)
    first_decided = [row for row in first if row["recommendation"] != "unclear"]

    assert len(first) == 2479
    assert len(first_decided) == 2379
    assert len(second) == 100
    combined = first_decided + second
    assert len(combined) == 2479
    assert len({row["record_key"] for row in combined}) == 2479
    assert sum(row["recommendation"] == "include" for row in combined) == 9
    assert sum(row["recommendation"] == "exclude" for row in combined) == 2470
    assert all(row["recommendation"] != "unclear" for row in combined)
    assert all(row["founder_decision_recorded"] == "false" for row in combined)


def test_pass2_review_binds_both_verified_packet_pairs() -> None:
    text = COMBINED_REVIEW.read_text(encoding="utf-8")
    first_receipt = yaml.safe_load(FIRST_RECEIPT.read_text(encoding="utf-8"))
    second_receipt = yaml.safe_load(SECOND_RECEIPT.read_text(encoding="utf-8"))

    assert first_receipt["appendix_sha256"] == _sha256(FIRST_APPENDIX)
    assert first_receipt["packet_sha256"] == _sha256(FIRST_PACKET)
    assert second_receipt["appendix_sha256"] == _sha256(SECOND_APPENDIX)
    assert second_receipt["packet_sha256"] == _sha256(SECOND_PACKET)
    for receipt in (first_receipt, second_receipt):
        assert receipt["packet_sha256"] in text
        assert receipt["appendix_sha256"] in text
        assert receipt["final_screening_decisions_recorded"] == 0
    assert "# Founder Citation Screening Packet — Pass 2" in FIRST_PACKET.read_text()
    assert "# Founder Citation Screening Packet — Pass 2" in SECOND_PACKET.read_text()
    assert "Unique candidate records: 2,479" in text
    assert "Proposed includes: 9" in text
    assert "Proposed excludes: 2,470" in text
    assert (
        "`I confirm both checksum-bound citation pass 2 packets as written.`"
        in text
    )


def test_pass2_confirmation_path_reproduces_ledger_without_external_persistence() -> None:
    store = InMemoryObjectStore()

    receipt = _simulate_confirmation(store)

    assert receipt.pass_number == 2
    assert receipt.candidate_count == 2479
    assert receipt.included_count == 9
    assert receipt.excluded_count == 2470
    assert receipt.unclear_count == 0
    assert receipt.ai_decisions_recorded == 0
    assert receipt.scientific_conclusions_drawn is False
    assert store.exists(receipt.ledger_object.object_key)


def test_pass2_proposed_inclusions_reconcile_against_all_locked_evidence() -> None:
    store = InMemoryObjectStore()
    decision = _simulate_confirmation(store)
    receipt = _simulate_reconciliation(store, decision)

    assert receipt.confirmed_inclusion_count == 9
    assert receipt.active_inventory_match_count == 0
    assert receipt.prior_appraisal_match_count == 0
    assert receipt.net_new_count == 9
    assert receipt.founder_decisions_changed == 0


def test_pass2_net_new_inclusions_route_under_active_uncapped_amendment(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore()
    decision = _simulate_confirmation(store)
    reconciliation = _simulate_reconciliation(store, decision)
    decision_path = tmp_path / "decision.yaml"
    reconciliation_path = tmp_path / "reconciliation.yaml"
    write_citation_decision_ledger_receipt(decision_path, decision)
    write_citation_inclusion_reconciliation_receipt(
        reconciliation_path, reconciliation
    )
    active_amendment = load_evidence_cap_amendment_activation_receipt(
        ACTIVE_AMENDMENT
    )

    queue = CitationPassAppraisalQueueService(store=store).build(
        decision,
        reconciliation,
        active_amendment,
        decision_receipt_path=decision_path,
        reconciliation_receipt_path=reconciliation_path,
        active_amendment_receipt_path=ACTIVE_AMENDMENT,
        code_revision="64a6c2f",
        queued_at=NOW,
    )

    assert queue.pass_number == 2
    assert queue.confirmed_inclusion_count == 9
    assert queue.repository_candidate_count == 4
    assert queue.access_check_required_count == 5
    assert queue.prior_appraisal_reuse_count == 0
    assert queue.net_new_count == 9
    assert "citation-pass-0002-appraisal-queue" in queue.queue_object.object_key
    assert queue.founder_decisions_changed == 0
    assert queue.molecular_data_access_authorized is False
    assert queue.outcome_data_access_authorized is False

    queue_path = tmp_path / "pass-0002-appraisal-queue.yaml"
    write_citation_pass_appraisal_queue_receipt(queue_path, queue)
    loaded_queue = load_citation_access_queue_receipt(queue_path)
    assert loaded_queue == queue

    inventory = CitationAccessInventoryService(store=store).build(loaded_queue)
    assert inventory.provisional_inclusion_count == 9
    assert inventory.repository_candidate_count == 4
    assert inventory.access_check_required_count == 5
    assert all(record.full_text_retrieved is False for record in inventory.records)


def test_pass2_routing_rejects_a_different_active_protocol(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore()
    decision = _simulate_confirmation(store)
    reconciliation = _simulate_reconciliation(store, decision)
    decision_path = tmp_path / "decision.yaml"
    reconciliation_path = tmp_path / "reconciliation.yaml"
    write_citation_decision_ledger_receipt(decision_path, decision)
    write_citation_inclusion_reconciliation_receipt(
        reconciliation_path, reconciliation
    )
    changed_amendment = load_evidence_cap_amendment_activation_receipt(
        ACTIVE_AMENDMENT
    ).model_copy(update={"active_protocol_version": "0.2.6"})
    changed_amendment_path = tmp_path / "changed-amendment.yaml"
    write_evidence_cap_amendment_activation_receipt(
        changed_amendment_path, changed_amendment
    )

    with pytest.raises(
        EvidenceCapAmendmentError,
        match="active protocol 0.2.5",
    ):
        CitationPassAppraisalQueueService(store=store).build(
            decision,
            reconciliation,
            changed_amendment,
            decision_receipt_path=decision_path,
            reconciliation_receipt_path=reconciliation_path,
            active_amendment_receipt_path=changed_amendment_path,
            code_revision="64a6c2f",
            queued_at=NOW,
        )
