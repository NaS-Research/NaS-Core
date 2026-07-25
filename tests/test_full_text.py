from pathlib import Path

import yaml

from nas_core.domain.appraisal import (
    FullTextAccessDecision,
    FullTextAppraisal,
    FullTextAppraisalProgress,
    FullTextInventory,
    FullTextRetrievalReceipt,
    write_full_text_inventory,
)

ROOT = Path(__file__).parents[1]
REVISED_FULL_TEXT_ROOT = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
    / "revised-full-text"
)
REVISED_APPRAISAL_ROOT = REVISED_FULL_TEXT_ROOT.parent / "revised-appraisals"


def test_full_text_inventory_reconciles_access_candidates() -> None:
    inventory = FullTextInventory(
        study_id="NAS-BRCA-002",
        queue_id="a" * 64,
        progress_id="b" * 64,
        provisional_inclusion_count=2,
        repository_candidate_count=1,
        access_check_required_count=1,
        records=[
            {
                "screening_id": "c" * 64,
                "record_key": "pmid:1",
                "title": "Synthetic repository candidate",
                "pmcid": "PMC1",
                "access_status": "repository_candidate",
            },
            {
                "screening_id": "d" * 64,
                "record_key": "pmid:2",
                "title": "Synthetic access-check candidate",
                "access_status": "access_check_required",
            },
        ],
    )

    assert inventory.provisional_inclusion_count == 2
    assert inventory.full_texts_retrieved == 0
    assert inventory.appraisals_completed == 0
    assert inventory.scientific_conclusions_drawn is False


def test_full_text_inventory_writer_is_exclusive(tmp_path) -> None:
    inventory = FullTextInventory(
        study_id="NAS-BRCA-002",
        queue_id="a" * 64,
        progress_id="b" * 64,
        provisional_inclusion_count=1,
        repository_candidate_count=1,
        access_check_required_count=0,
        records=[
            {
                "screening_id": "c" * 64,
                "record_key": "pmid:1",
                "title": "Synthetic repository candidate",
                "pmcid": "PMC1",
                "access_status": "repository_candidate",
            }
        ],
    )
    path = tmp_path / "inventory.yaml"

    write_full_text_inventory(path, inventory)

    assert FullTextInventory.model_validate(yaml.safe_load(path.read_text())) == inventory


def test_checked_in_revised_access_inventory_and_receipts_reconcile() -> None:
    inventory = FullTextInventory.model_validate(
        yaml.safe_load(
            (REVISED_FULL_TEXT_ROOT / "inventory" / "access_inventory.yaml").read_text()
        )
    )
    retrievals = [
        FullTextRetrievalReceipt.model_validate(yaml.safe_load(path.read_text()))
        for path in sorted(REVISED_FULL_TEXT_ROOT.glob("PMC*.yaml"))
    ]
    restrictions = [
        FullTextAccessDecision.model_validate(yaml.safe_load(path.read_text()))
        for path in sorted((REVISED_FULL_TEXT_ROOT / "access-decisions").glob("*.yaml"))
    ]

    assert inventory.provisional_inclusion_count == 13
    assert inventory.repository_candidate_count == 11
    assert inventory.access_check_required_count == 2
    assert len(retrievals) == 7
    assert len(restrictions) == 4
    assert {item.screening_id for item in retrievals}.isdisjoint(
        {item.screening_id for item in restrictions}
    )
    assert all(item.license_verified for item in retrievals)
    assert all(not item.durable_full_text_stored for item in restrictions)

    progress = FullTextAppraisalProgress.model_validate(
        yaml.safe_load(
            (
                REVISED_FULL_TEXT_ROOT.parent / "revised_appraisal_progress.yaml"
            ).read_text()
        )
    )
    assert progress.provisional_inclusion_count == 13
    assert progress.full_texts_retrieved == 7
    assert progress.access_restricted_count == 4
    assert sum(item.status == "awaiting_full_text" for item in progress.records) == 2
    assert progress.appraisals_completed == 1
    assert progress.context_only_count == 1
    completed = [item for item in progress.records if item.status == "completed"]
    assert len(completed) == 1
    assert completed[0].pmcid == "PMC3275466"

    appraisal = FullTextAppraisal.model_validate(
        yaml.safe_load(
            (REVISED_APPRAISAL_ROOT / "PMC3275466-v1.0.0.yaml").read_text()
        )
    )
    assert appraisal.screening_id == completed[0].screening_id
    assert appraisal.full_text_sha256 == completed[0].full_text_sha256
    assert appraisal.evidence_role == "context_only"
    assert appraisal.founder_authorized is True
