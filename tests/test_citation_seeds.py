import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nas_core.domain.appraisal import (
    FullTextAccessStatus,
    FullTextInventory,
    FullTextInventoryRecord,
)
from nas_core.domain.evidence_amendment import (
    CitationAppraisalQueueRecord,
    CitationAppraisalRoute,
    CitationPassAppraisalQueueReceipt,
    EvidenceCapAmendmentActivationReceipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.citation_seeds import (
    CitationCumulativeSeedError,
    CitationCumulativeSeedService,
)
from nas_core.retrieval.evidence_amendment import (
    CitationAccessInventoryService,
    EvidenceCapAmendmentError,
)
from nas_core.storage.object_store import InMemoryObjectStore

NOW = datetime(2026, 7, 26, 18, 0, tzinfo=UTC)


def _stored(store: InMemoryObjectStore, key: str, payload: object) -> StoredObject:
    body = canonical_json(payload)
    store.put_bytes(key, body, content_type="application/json")
    return StoredObject(
        object_key=key,
        media_type="application/json",
        size_bytes=len(body),
        sha256=sha256(body),
    )


def _inventory() -> FullTextInventory:
    return FullTextInventory(
        study_id="NAS-BRCA-002",
        queue_id="a" * 64,
        progress_id="b" * 64,
        provisional_inclusion_count=2,
        repository_candidate_count=1,
        access_check_required_count=1,
        records=[
            FullTextInventoryRecord(
                screening_id="c" * 64,
                record_key="pmid:1",
                title="Direct method one",
                pmid="1",
                pmcid="PMC1",
                access_status=FullTextAccessStatus.REPOSITORY_CANDIDATE,
            ),
            FullTextInventoryRecord(
                screening_id="d" * 64,
                record_key="pmid:2",
                title="Shared method",
                pmid="2",
                access_status=FullTextAccessStatus.ACCESS_CHECK_REQUIRED,
            ),
        ],
    )


def _activation(
    store: InMemoryObjectStore,
) -> EvidenceCapAmendmentActivationReceipt:
    queue = [
        CitationAppraisalQueueRecord(
            record_key="MED:2",
            title="Shared method.",
            pmid="2",
            route=CitationAppraisalRoute.ACCESS_CHECK_REQUIRED,
            founder_inclusion_preserved=True,
        ),
        CitationAppraisalQueueRecord(
            record_key="PPR:PPR4",
            title="Preprint method four",
            doi="10.1101/example",
            route=CitationAppraisalRoute.ACCESS_CHECK_REQUIRED,
            founder_inclusion_preserved=True,
        ),
        CitationAppraisalQueueRecord(
            record_key="MED:3",
            title="Citation method three",
            pmid="3",
            pmcid="PMC3",
            route=CitationAppraisalRoute.REPOSITORY_CANDIDATE,
            founder_inclusion_preserved=True,
        ),
    ]
    stored = _stored(
        store,
        "activation/queue.json",
        [item.model_dump(mode="json", exclude_none=True) for item in queue],
    )
    return EvidenceCapAmendmentActivationReceipt(
        activation_id="e" * 64,
        study_id="NAS-BRCA-002",
        prior_protocol_version="0.2.4",
        active_protocol_version="0.2.5",
        code_revision="abcdef0",
        approved_at=NOW,
        activated_at=NOW,
        founder_id="founder",
        amendment_sha256="f" * 64,
        reconciliation_id="1" * 64,
        reconciliation_receipt_sha256="2" * 64,
        confirmed_inclusion_count=3,
        repository_candidate_count=1,
        access_check_required_count=2,
        prior_appraisal_reuse_count=0,
        net_new_count=3,
        core_synthesis_maximum=30,
        queue_object=stored,
        amendment_checksum_verified=True,
        reconciliation_checksum_verified=True,
        count_invariants_verified=True,
        founder_authorized=True,
        uncapped_saturation_inventory_active=True,
    )


def _later_queue(
    store: InMemoryObjectStore,
) -> CitationPassAppraisalQueueReceipt:
    queue = [
        CitationAppraisalQueueRecord(
            record_key="MED:3",
            title="Citation method three.",
            pmid="3",
            pmcid="PMC3",
            route=CitationAppraisalRoute.REPOSITORY_CANDIDATE,
            founder_inclusion_preserved=True,
        ),
        CitationAppraisalQueueRecord(
            record_key="MED:5",
            title="Later citation method five",
            pmid="5",
            route=CitationAppraisalRoute.ACCESS_CHECK_REQUIRED,
            founder_inclusion_preserved=True,
        ),
        CitationAppraisalQueueRecord(
            record_key="PPR:PPR6",
            title="Later preprint method six",
            doi="10.1101/later",
            route=CitationAppraisalRoute.ACCESS_CHECK_REQUIRED,
            founder_inclusion_preserved=True,
        ),
    ]
    stored = _stored(
        store,
        "later-pass/queue.json",
        [item.model_dump(mode="json", exclude_none=True) for item in queue],
    )
    return CitationPassAppraisalQueueReceipt(
        queue_id="3" * 64,
        study_id="NAS-BRCA-002",
        pass_number=2,
        code_revision="abcdef0",
        queued_at=NOW,
        founder_id="founder",
        decision_id="4" * 64,
        decision_receipt_sha256="5" * 64,
        reconciliation_id="6" * 64,
        reconciliation_receipt_sha256="7" * 64,
        active_amendment_activation_id="e" * 64,
        active_amendment_receipt_sha256="8" * 64,
        active_protocol_version="0.2.5",
        confirmed_inclusion_count=3,
        repository_candidate_count=1,
        access_check_required_count=2,
        prior_appraisal_reuse_count=0,
        net_new_count=3,
        core_synthesis_maximum=30,
        queue_object=stored,
        decision_ledger_checksum_verified=True,
        reconciliation_checksum_verified=True,
        active_amendment_verified=True,
        count_invariants_verified=True,
        founder_authorized=True,
        uncapped_saturation_inventory_active=True,
    )


def _empty_later_queue(
    store: InMemoryObjectStore,
) -> CitationPassAppraisalQueueReceipt:
    stored = _stored(store, "empty-later-pass/queue.json", [])
    return CitationPassAppraisalQueueReceipt(
        queue_id="9" * 64,
        study_id="NAS-BRCA-002",
        pass_number=3,
        code_revision="abcdef0",
        queued_at=NOW,
        founder_id="founder",
        decision_id="a" * 64,
        decision_receipt_sha256="b" * 64,
        reconciliation_id="c" * 64,
        reconciliation_receipt_sha256="d" * 64,
        active_amendment_activation_id="e" * 64,
        active_amendment_receipt_sha256="f" * 64,
        active_protocol_version="0.2.5",
        confirmed_inclusion_count=0,
        repository_candidate_count=0,
        access_check_required_count=0,
        prior_appraisal_reuse_count=0,
        net_new_count=0,
        core_synthesis_maximum=30,
        queue_object=stored,
        decision_ledger_checksum_verified=True,
        reconciliation_checksum_verified=True,
        active_amendment_verified=True,
        count_invariants_verified=True,
        founder_authorized=True,
        uncapped_saturation_inventory_active=True,
    )


def test_builds_verified_cumulative_seed_set_without_losing_inclusions(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore()
    inventory_path = tmp_path / "inventory.yaml"
    activation_path = tmp_path / "activation.yaml"
    inventory_path.write_bytes(b"direct inventory")
    activation_path.write_bytes(b"activation receipt")
    service = CitationCumulativeSeedService(store=store, clock=lambda: NOW)

    receipt = service.build(
        _inventory(),
        _activation(store),
        direct_inventory_path=inventory_path,
        activation_receipt_path=activation_path,
        next_pass_number=2,
        code_revision="abcdef0",
    )
    seeds = service.load_seeds(receipt)

    assert receipt.direct_inclusion_count == 2
    assert receipt.prior_pass_inclusion_count == 3
    assert receipt.duplicate_identifier_count == 1
    assert receipt.cumulative_seed_count == 4
    assert {seed.evidence_id for seed in seeds} == {
        "PMID:1",
        "PMID:2",
        "PMID:3",
        "PPR:PPR4",
    }
    rows = json.loads(store.get_bytes(receipt.seeds_object.object_key))
    shared = next(row for row in rows if row["pmid"] == "2")
    assert shared["origins"] == ["citation_pass", "direct_search"]
    assert shared["source_record_keys"] == ["MED:2", "pmid:2"]
    preprint = next(row for row in rows if row["evidence_id"] == "PPR:PPR4")
    assert preprint["source"] == "PPR"
    assert preprint["external_id"] == "PPR4"
    assert "pmid" not in preprint


def test_pass_three_preserves_every_inclusion_from_all_prior_passes(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore()
    inventory_path = tmp_path / "inventory.yaml"
    activation_path = tmp_path / "activation.yaml"
    later_queue_path = tmp_path / "pass-0002-queue.yaml"
    inventory_path.write_bytes(b"direct inventory")
    activation_path.write_bytes(b"activation receipt")
    later_queue_path.write_bytes(b"pass 2 queue receipt")
    service = CitationCumulativeSeedService(store=store, clock=lambda: NOW)
    later_queue = _later_queue(store)

    receipt = service.build(
        _inventory(),
        _activation(store),
        direct_inventory_path=inventory_path,
        activation_receipt_path=activation_path,
        prior_pass_queues=[later_queue],
        prior_pass_queue_paths=[later_queue_path],
        next_pass_number=3,
        code_revision="abcdef0",
    )
    seeds = service.load_seeds(receipt)

    assert receipt.seed_set_version == "1.1.0"
    assert receipt.prior_pass_queue_ids == [later_queue.queue_id]
    assert receipt.prior_pass_queue_sha256s == [
        sha256(later_queue_path.read_bytes())
    ]
    assert receipt.direct_inclusion_count == 2
    assert receipt.prior_pass_inclusion_count == 6
    assert receipt.duplicate_identifier_count == 2
    assert receipt.cumulative_seed_count == 6
    assert {seed.evidence_id for seed in seeds} == {
        "PMID:1",
        "PMID:2",
        "PMID:3",
        "PPR:PPR4",
        "PMID:5",
        "PPR:PPR6",
    }


def test_pass_three_rejects_missing_prior_pass_queue(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    inventory_path = tmp_path / "inventory.yaml"
    activation_path = tmp_path / "activation.yaml"
    inventory_path.write_bytes(b"direct inventory")
    activation_path.write_bytes(b"activation receipt")

    with pytest.raises(
        CitationCumulativeSeedError,
        match="one ordered queue for every later prior pass",
    ):
        CitationCumulativeSeedService(store=store, clock=lambda: NOW).build(
            _inventory(),
            _activation(store),
            direct_inventory_path=inventory_path,
            activation_receipt_path=activation_path,
            next_pass_number=3,
            code_revision="abcdef0",
        )


def test_pass_four_preserves_an_empty_prior_pass_in_lineage(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore()
    inventory_path = tmp_path / "inventory.yaml"
    activation_path = tmp_path / "activation.yaml"
    pass_two_path = tmp_path / "pass-0002-queue.yaml"
    pass_three_path = tmp_path / "pass-0003-empty-queue.yaml"
    inventory_path.write_bytes(b"direct inventory")
    activation_path.write_bytes(b"activation receipt")
    pass_two_path.write_bytes(b"pass 2 queue receipt")
    pass_three_path.write_bytes(b"pass 3 empty queue receipt")
    pass_two = _later_queue(store)
    pass_three = _empty_later_queue(store)
    service = CitationCumulativeSeedService(store=store, clock=lambda: NOW)

    receipt = service.build(
        _inventory(),
        _activation(store),
        direct_inventory_path=inventory_path,
        activation_receipt_path=activation_path,
        prior_pass_queues=[pass_two, pass_three],
        prior_pass_queue_paths=[pass_two_path, pass_three_path],
        next_pass_number=4,
        code_revision="abcdef0",
    )

    assert receipt.prior_pass_queue_ids == [
        pass_two.queue_id,
        pass_three.queue_id,
    ]
    assert receipt.prior_pass_inclusion_count == 6
    assert receipt.duplicate_identifier_count == 2
    assert receipt.cumulative_seed_count == 6


def test_empty_later_pass_does_not_create_an_access_inventory() -> None:
    store = InMemoryObjectStore()

    with pytest.raises(
        EvidenceCapAmendmentError,
        match="no net-new inclusions",
    ):
        CitationAccessInventoryService(store=store).build(
            _empty_later_queue(store)
        )


def test_rejects_tampered_activation_queue(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    activation = _activation(store)
    store.put_bytes(
        activation.queue_object.object_key,
        b"[]",
        content_type="application/json",
    )
    inventory_path = tmp_path / "inventory.yaml"
    activation_path = tmp_path / "activation.yaml"
    inventory_path.write_bytes(b"direct inventory")
    activation_path.write_bytes(b"activation receipt")

    with pytest.raises(CitationCumulativeSeedError, match="does not match"):
        CitationCumulativeSeedService(store=store, clock=lambda: NOW).build(
            _inventory(),
            activation,
            direct_inventory_path=inventory_path,
            activation_receipt_path=activation_path,
            next_pass_number=2,
            code_revision="abcdef0",
        )
