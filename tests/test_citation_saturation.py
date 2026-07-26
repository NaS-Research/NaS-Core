from datetime import UTC, datetime
from pathlib import Path

import pytest

from nas_core.domain.appraisal import (
    AppraisalCompletionStatus,
    EvidenceRole,
    FullTextAccessStatus,
    FullTextAppraisalProgress,
    FullTextAppraisalProgressRecord,
    FullTextInventory,
    FullTextInventoryRecord,
    write_full_text_appraisal_progress,
    write_full_text_inventory,
)
from nas_core.domain.citation_chain import (
    CitationChainReceipt,
    CitationScreeningPreparationReceipt,
    write_citation_chain_receipt,
    write_citation_screening_preparation_receipt,
)
from nas_core.domain.citation_confirmation import (
    CitationDecisionLedgerReceipt,
    CitationDecisionLedgerRecord,
    write_citation_decision_ledger_receipt,
)
from nas_core.domain.citation_reconciliation import (
    CitationInclusionReconciliationReceipt,
    CitationInclusionReconciliationRecord,
    write_citation_inclusion_reconciliation_receipt,
)
from nas_core.domain.evidence_amendment import (
    CitationAppraisalQueueRecord,
    CitationAppraisalRoute,
    CitationPassAppraisalQueueReceipt,
    write_citation_pass_appraisal_queue_receipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.citation_saturation import (
    CitationPassClosureError,
    CitationPassClosureService,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 26, 20, 0, tzinfo=UTC)
SCREENING_ID = "1" * 64


def _stored(
    store: InMemoryObjectStore,
    key: str,
    payload: object,
) -> StoredObject:
    body = canonical_json(payload)
    store.put_bytes(key, body, content_type="application/json")
    return StoredObject(
        object_key=key,
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )


def _citation(store: InMemoryObjectStore) -> CitationChainReceipt:
    return CitationChainReceipt(
        execution_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=2,
        code_revision="abcdef0",
        retrieved_at=NOW,
        verified_at=NOW,
        seed_evidence_ids=["PMID:1"],
        backward_candidate_count=1,
        forward_candidate_count=1,
        unique_candidate_count=2,
        endpoint_request_count=2,
        manifest_object_key="citation/manifest.json",
        manifest_sha256="b" * 64,
        raw_responses_object=_stored(store, "citation/raw.json", []),
        candidates_object=_stored(store, "citation/candidates.json", [{}, {}]),
        manifest_checksum_verified=True,
        object_checksums_verified=True,
        endpoint_counts_verified=True,
        candidate_count_verified=True,
    )


def _preparation(store: InMemoryObjectStore) -> CitationScreeningPreparationReceipt:
    return CitationScreeningPreparationReceipt(
        preparation_id="c" * 64,
        study_id="NAS-BRCA-002",
        pass_number=2,
        citation_execution_id="a" * 64,
        prior_search_execution_id="d" * 64,
        prior_decision_ids=["e" * 64],
        code_revision="abcdef0",
        created_at=NOW,
        verified_at=NOW,
        input_candidate_count=2,
        already_screened_count=0,
        duplicate_candidate_count=0,
        requires_screening_count=2,
        inventory_object=_stored(store, "screening/inventory.json", [{}, {}]),
        screening_candidates_object=_stored(
            store, "screening/candidates.json", [{}, {}]
        ),
        input_checksums_verified=True,
        prior_decision_checksums_verified=True,
        output_checksums_verified=True,
        count_invariants_verified=True,
    )


def _decision(
    store: InMemoryObjectStore,
    *,
    include: bool = True,
) -> CitationDecisionLedgerReceipt:
    records = [
        CitationDecisionLedgerRecord(
            record_key="MED:3",
            rank=1,
            title="Included method" if include else "Excluded method",
            pmid="3",
            decision="include" if include else "exclude",
            exclusion_reason=(
                None
                if include
                else "no_relevant_discordance_stability_or_classifier_method"
            ),
            reviewer_id="founder",
            reviewer_name="Founder",
            reviewer_role="founder_internal_reviewer",
            decided_at=NOW,
            founder_authorized=True,
            ai_decision=False,
        ),
        CitationDecisionLedgerRecord(
            record_key="MED:4",
            rank=2,
            title="Excluded method two",
            pmid="4",
            decision="exclude",
            exclusion_reason=(
                "no_relevant_discordance_stability_or_classifier_method"
            ),
            reviewer_id="founder",
            reviewer_name="Founder",
            reviewer_role="founder_internal_reviewer",
            decided_at=NOW,
            founder_authorized=True,
            ai_decision=False,
        ),
    ]
    ledger = _stored(
        store,
        "decisions/ledger.json",
        [record.model_dump(mode="json", exclude_none=True) for record in records],
    )
    included = int(include)
    return CitationDecisionLedgerReceipt(
        decision_id="f" * 64,
        study_id="NAS-BRCA-002",
        pass_number=2,
        code_revision="abcdef0",
        confirmed_at=NOW,
        founder_id="founder",
        founder_name="Founder",
        first_packet_sha256="2" * 64,
        first_appendix_sha256="3" * 64,
        second_packet_sha256="4" * 64,
        second_appendix_sha256="5" * 64,
        candidate_count=2,
        included_count=included,
        excluded_count=2 - included,
        unclear_count=0,
        ledger_object=ledger,
        packet_checksums_verified=True,
        appendix_checksums_verified=True,
        record_coverage_verified=True,
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )


def _reconciliation(
    store: InMemoryObjectStore,
    *,
    include: bool = True,
) -> CitationInclusionReconciliationReceipt:
    rows = (
        [
            CitationInclusionReconciliationRecord(
                record_key="MED:3",
                title="Included method",
                pmid="3",
                disposition="net_new",
                matched_identifiers=[],
            )
        ]
        if include
        else []
    )
    stored = _stored(
        store,
        "reconciliation/rows.json",
        [row.model_dump(mode="json", exclude_none=True) for row in rows],
    )
    count = int(include)
    return CitationInclusionReconciliationReceipt(
        reconciliation_id="6" * 64,
        study_id="NAS-BRCA-002",
        pass_number=2,
        decision_id="f" * 64,
        code_revision="abcdef0",
        reconciled_at=NOW,
        confirmed_inclusion_count=count,
        active_inventory_match_count=0,
        prior_appraisal_match_count=0,
        net_new_count=count,
        inventory_record_count=30,
        prior_appraisal_count=1,
        reconciliation_object=stored,
        decision_ledger_checksum_verified=True,
        exact_identifier_matching_only=True,
        count_invariants_verified=True,
    )


def _queue(
    store: InMemoryObjectStore,
    *,
    include: bool = True,
) -> CitationPassAppraisalQueueReceipt:
    records = (
        [
            CitationAppraisalQueueRecord(
                record_key="MED:3",
                title="Included method",
                pmid="3",
                pmcid="PMC3",
                route=CitationAppraisalRoute.REPOSITORY_CANDIDATE,
                founder_inclusion_preserved=True,
            )
        ]
        if include
        else []
    )
    stored = _stored(
        store,
        "queue/rows.json",
        [record.model_dump(mode="json", exclude_none=True) for record in records],
    )
    count = int(include)
    return CitationPassAppraisalQueueReceipt(
        queue_id="7" * 64,
        study_id="NAS-BRCA-002",
        pass_number=2,
        code_revision="abcdef0",
        queued_at=NOW,
        founder_id="founder",
        decision_id="f" * 64,
        decision_receipt_sha256="8" * 64,
        reconciliation_id="6" * 64,
        reconciliation_receipt_sha256="9" * 64,
        active_amendment_activation_id="0" * 64,
        active_amendment_receipt_sha256="a" * 64,
        active_protocol_version="0.2.5",
        confirmed_inclusion_count=count,
        repository_candidate_count=count,
        access_check_required_count=0,
        prior_appraisal_reuse_count=0,
        net_new_count=count,
        core_synthesis_maximum=30,
        queue_object=stored,
        decision_ledger_checksum_verified=True,
        reconciliation_checksum_verified=True,
        active_amendment_verified=True,
        count_invariants_verified=True,
        founder_authorized=True,
        uncapped_saturation_inventory_active=True,
    )


def _inventory_and_progress(
    *,
    status: AppraisalCompletionStatus = AppraisalCompletionStatus.COMPLETED,
) -> tuple[FullTextInventory, FullTextAppraisalProgress]:
    inventory = FullTextInventory(
        study_id="NAS-BRCA-002",
        queue_id="7" * 64,
        progress_id="6" * 64,
        provisional_inclusion_count=1,
        repository_candidate_count=1,
        access_check_required_count=0,
        records=[
            FullTextInventoryRecord(
                screening_id=SCREENING_ID,
                record_key="MED:3",
                title="Included method",
                pmid="3",
                pmcid="PMC3",
                access_status=FullTextAccessStatus.REPOSITORY_CANDIDATE,
            )
        ],
    )
    completed = status is AppraisalCompletionStatus.COMPLETED
    ready = status is AppraisalCompletionStatus.READY_FOR_APPRAISAL
    progress_record = FullTextAppraisalProgressRecord(
        screening_id=SCREENING_ID,
        title="Included method",
        pmcid="PMC3",
        status=status,
        retrieval_id="b" * 64 if completed or ready else None,
        full_text_sha256="c" * 64 if completed or ready else None,
        appraisal_version="1.0.0" if completed else None,
        evidence_role=EvidenceRole.SUPPORTING if completed else None,
    )
    progress = FullTextAppraisalProgress(
        study_id="NAS-BRCA-002",
        queue_id="7" * 64,
        progress_id="6" * 64,
        generated_at=NOW,
        provisional_inclusion_count=1,
        full_texts_retrieved=1 if completed or ready else 0,
        appraisals_completed=1 if completed else 0,
        access_restricted_count=0,
        duplicate_resolved_count=0,
        anchor_count=0,
        supporting_count=1 if completed else 0,
        context_only_count=0,
        excluded_count=0,
        records=[progress_record],
    )
    return inventory, progress


def _write_inputs(
    tmp_path: Path,
    citation: CitationChainReceipt,
    preparation: CitationScreeningPreparationReceipt,
    decision: CitationDecisionLedgerReceipt,
    reconciliation: CitationInclusionReconciliationReceipt,
    queue: CitationPassAppraisalQueueReceipt,
) -> dict[str, Path]:
    paths = {
        "citation": tmp_path / "citation.yaml",
        "preparation": tmp_path / "preparation.yaml",
        "decision": tmp_path / "decision.yaml",
        "reconciliation": tmp_path / "reconciliation.yaml",
        "queue": tmp_path / "queue.yaml",
    }
    write_citation_chain_receipt(paths["citation"], citation)
    write_citation_screening_preparation_receipt(
        paths["preparation"], preparation
    )
    write_citation_decision_ledger_receipt(paths["decision"], decision)
    write_citation_inclusion_reconciliation_receipt(
        paths["reconciliation"], reconciliation
    )
    write_citation_pass_appraisal_queue_receipt(paths["queue"], queue)
    return paths


def test_closure_derives_new_eligible_evidence_from_complete_receipts(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore()
    citation = _citation(store)
    preparation = _preparation(store)
    decision = _decision(store)
    reconciliation = _reconciliation(store)
    queue = _queue(store)
    inventory, progress = _inventory_and_progress()
    paths = _write_inputs(
        tmp_path, citation, preparation, decision, reconciliation, queue
    )
    inventory_path = tmp_path / "inventory.yaml"
    progress_path = tmp_path / "progress.yaml"
    write_full_text_inventory(inventory_path, inventory)
    write_full_text_appraisal_progress(progress_path, progress)

    closure = CitationPassClosureService(store=store).close(
        citation,
        preparation,
        decision,
        reconciliation,
        queue,
        citation_receipt_path=paths["citation"],
        preparation_receipt_path=paths["preparation"],
        decision_receipt_path=paths["decision"],
        reconciliation_receipt_path=paths["reconciliation"],
        queue_receipt_path=paths["queue"],
        access_inventory=inventory,
        access_inventory_path=inventory_path,
        appraisal_progress=progress,
        appraisal_progress_path=progress_path,
        code_revision="abcdef0",
        closed_at=NOW,
    )

    assert closure.unique_candidate_count == 2
    assert closure.founder_screened_candidate_count == 2
    assert closure.included_count == 1
    assert closure.appraisals_completed_count == 1
    assert closure.new_eligible_evidence_ids == ["PMID:3"]
    assert closure.appraisal_accounting_complete is True


def test_closure_rejects_unfinished_appraisal_work(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    citation = _citation(store)
    preparation = _preparation(store)
    decision = _decision(store)
    reconciliation = _reconciliation(store)
    queue = _queue(store)
    inventory, progress = _inventory_and_progress(
        status=AppraisalCompletionStatus.READY_FOR_APPRAISAL
    )
    paths = _write_inputs(
        tmp_path, citation, preparation, decision, reconciliation, queue
    )
    inventory_path = tmp_path / "inventory.yaml"
    progress_path = tmp_path / "progress.yaml"
    write_full_text_inventory(inventory_path, inventory)
    write_full_text_appraisal_progress(progress_path, progress)

    with pytest.raises(
        CitationPassClosureError,
        match="unresolved records",
    ):
        CitationPassClosureService(store=store).close(
            citation,
            preparation,
            decision,
            reconciliation,
            queue,
            citation_receipt_path=paths["citation"],
            preparation_receipt_path=paths["preparation"],
            decision_receipt_path=paths["decision"],
            reconciliation_receipt_path=paths["reconciliation"],
            queue_receipt_path=paths["queue"],
            access_inventory=inventory,
            access_inventory_path=inventory_path,
            appraisal_progress=progress,
            appraisal_progress_path=progress_path,
            code_revision="abcdef0",
            closed_at=NOW,
        )


def test_zero_yield_pass_closes_without_access_artifacts(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    citation = _citation(store)
    preparation = _preparation(store)
    decision = _decision(store, include=False)
    reconciliation = _reconciliation(store, include=False)
    queue = _queue(store, include=False)
    paths = _write_inputs(
        tmp_path, citation, preparation, decision, reconciliation, queue
    )

    closure = CitationPassClosureService(store=store).close(
        citation,
        preparation,
        decision,
        reconciliation,
        queue,
        citation_receipt_path=paths["citation"],
        preparation_receipt_path=paths["preparation"],
        decision_receipt_path=paths["decision"],
        reconciliation_receipt_path=paths["reconciliation"],
        queue_receipt_path=paths["queue"],
        code_revision="abcdef0",
        closed_at=NOW,
    )

    assert closure.included_count == 0
    assert closure.net_new_count == 0
    assert closure.new_eligible_evidence_ids == []
    assert closure.access_inventory_sha256 is None
    assert closure.appraisal_progress_sha256 is None
