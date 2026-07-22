from nas_core.domain.appraisal import FullTextInventory


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
