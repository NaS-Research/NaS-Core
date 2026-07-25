from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.domain.citation_reconciliation import (
    CitationInclusionReconciliationReceipt,
)
from nas_core.domain.evidence_amendment import (
    APPROVAL_STATEMENT,
    EvidenceCapAmendmentApproval,
    load_evidence_cap_amendment_activation_receipt,
    load_evidence_cap_amendment_approval,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.evidence_amendment import (
    CitationAccessInventoryService,
    EvidenceCapAmendmentActivationService,
    EvidenceCapAmendmentError,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 25, 19, 53, tzinfo=UTC)
ROOT = Path(__file__).parents[1]
LITERATURE = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
)


def _approval(amendment: bytes, reconciliation_receipt: bytes) -> EvidenceCapAmendmentApproval:
    return EvidenceCapAmendmentApproval(
        study_id="NAS-BRCA-002",
        prior_protocol_version="0.2.4",
        amendment_version="0.2.5",
        amendment_sha256=sha256(amendment),
        reconciliation_id="a" * 64,
        reconciliation_receipt_sha256=sha256(reconciliation_receipt),
        approval_statement=APPROVAL_STATEMENT,
        founder_id="test-founder",
        founder_name="Test Founder",
        approved_at=NOW,
        founder_authorized=True,
        uncapped_saturation_inventory_authorized=True,
        core_synthesis_maximum=30,
    )


def _reconciliation(store: InMemoryObjectStore) -> CitationInclusionReconciliationReceipt:
    rows = [
        {
            "record_key": "MED:1",
            "title": "Repository study",
            "pmid": "1",
            "pmcid": "PMC1",
            "disposition": "net_new",
            "matched_identifiers": [],
        },
        {
            "record_key": "MED:2",
            "title": "Access-check study",
            "pmid": "2",
            "disposition": "net_new",
            "matched_identifiers": [],
        },
        {
            "record_key": "MED:3",
            "title": "Prior study",
            "pmid": "3",
            "disposition": "prior_appraisal",
            "matched_identifiers": ["pmid"],
            "matched_screening_id": "b" * 64,
        },
    ]
    body = canonical_json(rows)
    key = "citation-screening/NAS-BRCA-002/pass-0001/reconciliation-test.json"
    store.put_bytes(key, body, content_type="application/json")
    return CitationInclusionReconciliationReceipt(
        reconciliation_id="a" * 64,
        study_id="NAS-BRCA-002",
        pass_number=1,
        decision_id="c" * 64,
        code_revision="abcdef0",
        reconciled_at=NOW,
        confirmed_inclusion_count=3,
        active_inventory_match_count=0,
        prior_appraisal_match_count=1,
        net_new_count=2,
        inventory_record_count=30,
        prior_appraisal_count=1,
        reconciliation_object=StoredObject(
            object_key=key,
            media_type="application/json",
            size_bytes=len(body),
            sha256=sha256(body),
        ),
        decision_ledger_checksum_verified=True,
        exact_identifier_matching_only=True,
        count_invariants_verified=True,
    )


def test_activation_routes_every_inclusion_without_authorizing_data_access(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore()
    amendment = b"approved amendment"
    receipt_bytes = b"reconciliation receipt"
    amendment_path = tmp_path / "amendment.md"
    reconciliation_path = tmp_path / "reconciliation.yaml"
    amendment_path.write_bytes(amendment)
    reconciliation_path.write_bytes(receipt_bytes)

    receipt = EvidenceCapAmendmentActivationService(store=store).activate(
        _approval(amendment, receipt_bytes),
        _reconciliation(store),
        amendment_path=amendment_path,
        reconciliation_receipt_path=reconciliation_path,
        code_revision="abcdef0",
        activated_at=NOW,
    )

    assert receipt.confirmed_inclusion_count == 3
    assert receipt.repository_candidate_count == 1
    assert receipt.access_check_required_count == 1
    assert receipt.prior_appraisal_reuse_count == 1
    assert receipt.net_new_count == 2
    assert receipt.uncapped_saturation_inventory_active is True
    assert receipt.molecular_data_access_authorized is False
    assert receipt.outcome_data_access_authorized is False

    inventory = CitationAccessInventoryService(store=store).build(receipt)
    assert inventory.provisional_inclusion_count == 2
    assert inventory.repository_candidate_count == 1
    assert inventory.access_check_required_count == 1
    assert len({item.screening_id for item in inventory.records}) == 2
    assert all(item.full_text_retrieved is False for item in inventory.records)


def test_approval_rejects_inexact_statement() -> None:
    payload = _approval(b"amendment", b"receipt").model_dump()
    payload["approval_statement"] = "approved"

    with pytest.raises(ValidationError, match="statement is not exact"):
        EvidenceCapAmendmentApproval.model_validate(payload)


def test_activation_rejects_changed_approved_amendment(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    amendment_path = tmp_path / "amendment.md"
    reconciliation_path = tmp_path / "reconciliation.yaml"
    amendment_path.write_bytes(b"changed")
    reconciliation_path.write_bytes(b"receipt")

    with pytest.raises(EvidenceCapAmendmentError, match="amendment checksum"):
        EvidenceCapAmendmentActivationService(store=store).activate(
            _approval(b"approved", b"receipt"),
            _reconciliation(store),
            amendment_path=amendment_path,
            reconciliation_receipt_path=reconciliation_path,
            code_revision="abcdef0",
            activated_at=NOW,
        )


def test_checked_in_amendment_approval_and_activation_are_checksum_bound() -> None:
    approval = load_evidence_cap_amendment_approval(
        LITERATURE / "FOUNDER_EVIDENCE_CAP_AMENDMENT_APPROVAL_v0.2.5.yaml"
    )
    activation = load_evidence_cap_amendment_activation_receipt(
        LITERATURE / "evidence-cap-amendment-activation-v0.2.5.yaml"
    )

    assert approval.amendment_sha256 == sha256(
        (
            LITERATURE
            / "CITATION_CHAIN_EVIDENCE_CAP_AMENDMENT_DRAFT_v0.2.5.md"
        ).read_bytes()
    )
    assert activation.amendment_sha256 == approval.amendment_sha256
    assert activation.reconciliation_id == approval.reconciliation_id
    assert activation.confirmed_inclusion_count == 32
    assert activation.repository_candidate_count == 23
    assert activation.access_check_required_count == 6
    assert activation.prior_appraisal_reuse_count == 3
    assert activation.net_new_count == 29
