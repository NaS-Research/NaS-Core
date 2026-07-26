from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
MANUSCRIPT_ROOT = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "manuscript"
)


def test_living_manuscript_preserves_traceability_and_claim_boundaries() -> None:
    manuscript = (MANUSCRIPT_ROOT / "WORKING_MANUSCRIPT.md").read_text(
        encoding="utf-8"
    )
    normalized_manuscript = " ".join(manuscript.split())
    rules = (MANUSCRIPT_ROOT / "README.md").read_text(encoding="utf-8")

    for heading in (
        "## Abstract",
        "## Introduction",
        "## Methods",
        "## Results",
        "## Discussion",
        "## Limitations",
        "## Conclusions",
        "## References",
        "## Evidence-to-text ledger",
        "## Revision log",
    ):
        assert heading in manuscript
    assert "no molecular values or outcome dataset used or retained" in normalized_manuscript
    assert "During pre-gate endpoint characterization" in manuscript
    assert "It supersedes its already appraised preprint" in manuscript
    assert "### Publication-version reconciliation" in manuscript
    assert "preserves 53 appraisal reports and counts 52 unique studies" in (
        normalized_manuscript
    )
    assert "citation-publication-version-reconciliation-v1.0.0.yaml" in manuscript
    assert "No scientific or clinical conclusion is authorized" in manuscript
    assert "revised-appraisals/PMC3275466-v1.0.0.yaml" in manuscript
    assert "revised-appraisals/PMC4365540-v1.0.0.yaml" in manuscript
    assert (
        "| Results—NaS analysis | NaS-generated result | none | prohibited placeholder |"
        in manuscript
    )
    assert "Update the manuscript after each material evidence appraisal" in rules
    assert "Only a frozen research release" in rules
