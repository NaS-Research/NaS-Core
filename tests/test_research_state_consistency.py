from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
MANUSCRIPT = STUDY / "manuscript" / "WORKING_MANUSCRIPT.md"
STATUS = ROOT / "PROJECT_STATUS.md"
SYNTHESIS = STUDY / "literature" / "saturated_evidence_synthesis_v1.0.0.yaml"
PROGRESS = STUDY / "literature" / "revised_evidence_review_progress.yaml"


def test_current_narrative_matches_saturated_evidence_state() -> None:
    synthesis = yaml.safe_load(SYNTHESIS.read_text(encoding="utf-8"))
    progress = yaml.safe_load(PROGRESS.read_text(encoding="utf-8"))
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")
    current_text = manuscript + "\n" + status

    assert synthesis["eligible_evidence_count"] == 81
    assert synthesis["completed_appraisal_count"] == 68
    assert synthesis["access_restricted_count"] == 13
    assert synthesis["supporting_count"] == 22
    assert synthesis["context_only_count"] == 46
    assert progress["review_status"] == "complete"
    assert progress["stopping_rule_satisfied"] is True

    for expected in (
        "81 eligible",
        "68 completed appraisals",
        "13 access restrictions",
        "stopping rule is satisfied",
    ):
        assert expected in current_text


def test_current_manuscript_does_not_reintroduce_pre_saturation_claims() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8").split(
        "## Revision log",
        maxsplit=1,
    )[0]

    for stale_claim in (
        "pass 3 awaits founder screening confirmation",
        "founder confirmation pending",
        "Sequential citation chaining remains incomplete",
        "supported, evidence review incomplete",
    ):
        assert stale_claim not in manuscript
