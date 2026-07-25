from pathlib import Path

import yaml

from nas_core.domain.appraisal import (
    FullTextAccessDecision,
    FullTextAppraisal,
    FullTextAppraisalProgress,
    FullTextInventory,
    FullTextReadOnlyReviewReceipt,
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
            (
                REVISED_FULL_TEXT_ROOT
                / "inventory"
                / "access_inventory_v0.3.2.yaml"
            ).read_text()
        )
    )
    retrievals = [
        FullTextRetrievalReceipt.model_validate(yaml.safe_load(path.read_text()))
        for path in sorted(REVISED_FULL_TEXT_ROOT.glob("*.yaml"))
    ]
    restrictions = [
        FullTextAccessDecision.model_validate(yaml.safe_load(path.read_text()))
        for path in sorted((REVISED_FULL_TEXT_ROOT / "access-decisions").glob("*.yaml"))
    ]
    read_only_receipts = [
        FullTextReadOnlyReviewReceipt.model_validate(yaml.safe_load(path.read_text()))
        for path in sorted(
            (REVISED_FULL_TEXT_ROOT / "read-only-receipts").glob("*.yaml")
        )
    ]

    assert inventory.progress_id == (
        "7b90c37aa7fcab3607b5fde99c6aa97a0a3e440889b0d44727ba4f685863218c"
    )
    assert inventory.provisional_inclusion_count == 30
    assert inventory.repository_candidate_count == 26
    assert inventory.access_check_required_count == 4
    assert len(retrievals) == 19
    assert len(restrictions) == 10
    assert len(read_only_receipts) == 9
    assert {item.screening_id for item in retrievals}.isdisjoint(
        {item.screening_id for item in restrictions}
    )
    assert all(item.license_verified for item in retrievals)
    assert all(not item.durable_full_text_stored for item in restrictions)

    progress = FullTextAppraisalProgress.model_validate(
        yaml.safe_load(
            (
                REVISED_FULL_TEXT_ROOT.parent
                / "revised_appraisal_progress_v0.4.0.yaml"
            ).read_text()
        )
    )
    assert progress.progress_id == inventory.progress_id
    assert progress.provisional_inclusion_count == 30
    assert progress.full_texts_retrieved == 19
    assert progress.read_only_full_texts_reviewed == 9
    assert progress.access_restricted_count == 2
    assert sum(item.status == "ready_for_appraisal" for item in progress.records) == 0
    assert sum(item.status == "awaiting_full_text" for item in progress.records) == 0
    assert progress.appraisals_completed == 28
    assert progress.supporting_count == 15
    assert progress.context_only_count == 13
    completed = [item for item in progress.records if item.status == "completed"]
    assert {item.pmcid for item in completed} == {
        "PMC3275466",
        "PMC3151208",
        "PMC3445863",
        "PMC4008304",
        "PMC4365540",
        "PMC7442834",
        "PMC7761033",
        "PMC9381586",
        "PMC10587090",
        "PMC12501779",
        "PMC2667820",
        "PMC4495301",
        "PMC5939629",
        "PMC6408846",
        "PMC10052604",
        "PMC10147733",
        "PMC12789466",
        "PMC3893734",
        "PMC6538748",
        "PMC10241706",
        "PMC6449178",
        "PMC8138885",
        "PMC7641762",
        "PMC8385191",
        "PMC8974006",
        "PMC10723508",
        None,
    }

    appraisals = [
        FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))
        for path in sorted(REVISED_APPRAISAL_ROOT.glob("*.yaml"))
    ]
    assert {item.screening_id for item in appraisals} == {
        item.screening_id for item in completed
    }
    assert {
        (item.screening_id, item.full_text_sha256) for item in appraisals
    } == {
        (item.screening_id, item.full_text_sha256) for item in completed
    }
    assert all(item.founder_authorized for item in appraisals)
    assert {
        item.pmid: item.evidence_role for item in appraisals
    } == {
        "22196354": "context_only",
        "25849221": "context_only",
        "32826944": "supporting",
        "33255759": "supporting",
        "35974007": "supporting",
        "37857634": "supporting",
        "41064593": "supporting",
        "19204204": "supporting",
        "25788628": "supporting",
        "28062443": "supporting",
        "37008073": "supporting",
        "41390542": "context_only",
        "27130929": "supporting",
        "30849944": "context_only",
        "36892725": "supporting",
        "21718502": "supporting",
        "23046482": "context_only",
        "24625003": "supporting",
        "24490149": "context_only",
        "31138829": "context_only",
        "37209182": "context_only",
        "30591591": "context_only",
        "32789507": "supporting",
        "32997146": "supporting",
        "34387660": "context_only",
        "35361119": "context_only",
        "38105959": "context_only",
        "42172162": "context_only",
    }
