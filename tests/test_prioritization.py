from nas_core.domain.literature import ScreeningQueueRecord
from nas_core.retrieval.prioritization import DeterministicPrioritizationService


def _record(identifier: str, title: str, abstract: str) -> ScreeningQueueRecord:
    return ScreeningQueueRecord(
        screening_id=identifier * 64,
        record_key=f"synthetic:{identifier}",
        source_ids=["synthetic"],
        title=title,
        abstract=abstract,
        publication_year=2025,
    )


def test_priority_score_favors_direct_stability_and_validation_evidence() -> None:
    core = _record(
        "a",
        "PAM50 classification stability in breast tumors",
        (
            "A human patient cohort evaluated classifier uncertainty, normalization, "
            "discordance, and external validation."
        ),
    )
    context = _record(
        "b",
        "Breast cancer overview",
        "A review of clinical outcomes in breast cancer.",
    )

    core_score, core_signals, core_cautions, _ = DeterministicPrioritizationService._score(core)
    context_score, _, context_cautions, _ = DeterministicPrioritizationService._score(context)

    assert core_score >= 12
    assert core_score > context_score
    assert "stability_or_robustness" in core_signals
    assert core_cautions == []
    assert "secondary_literature" in context_cautions


def test_priority_tiers_do_not_create_screening_decisions() -> None:
    record = _record(
        "c",
        "PAM50 discordance and classifier confidence",
        "Human tumor cohort validation and survival outcomes.",
    )
    score, _, _, unchanged = DeterministicPrioritizationService._score(record)

    assert DeterministicPrioritizationService._tier(score) == "core"
    assert unchanged.decision == "pending"
    assert unchanged.reviewer is None
