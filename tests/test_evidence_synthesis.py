from pathlib import Path

import pytest

from nas_core.domain.appraisal import FullTextAppraisal, load_full_text_appraisal
from nas_core.domain.evidence_review import load_evidence_review_progress
from nas_core.domain.evidence_synthesis import (
    EvidenceDirection,
    load_saturated_evidence_synthesis_proposal,
)
from nas_core.retrieval.evidence_synthesis import (
    EvidenceSynthesisError,
    SaturatedEvidenceSynthesisService,
)

ROOT = Path(__file__).parents[1]
LITERATURE = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
)
PROGRESS = LITERATURE / "revised_evidence_review_progress.yaml"
PROPOSAL = LITERATURE / "saturated_evidence_synthesis_proposal_v1.0.0.yaml"
REUSED = (
    LITERATURE / "appraisals" / "PMC3413822-v1.0.0.yaml",
    LITERATURE / "appraisals" / "PMC5001207-v1.0.0.yaml",
    LITERATURE / "appraisals" / "PMC1468408-v1.0.0.yaml",
)


def _appraisals() -> list[FullTextAppraisal]:
    paths = [
        *sorted((LITERATURE / "revised-appraisals").glob("*.yaml")),
        *sorted((LITERATURE / "citation-appraisals").glob("*.yaml")),
        *REUSED,
    ]
    return [load_full_text_appraisal(path) for path in paths]


def test_checked_in_synthesis_is_bound_to_all_saturated_appraisals() -> None:
    proposal = SaturatedEvidenceSynthesisService().validate(
        load_saturated_evidence_synthesis_proposal(PROPOSAL),
        load_evidence_review_progress(PROGRESS),
        _appraisals(),
        progress_path=PROGRESS,
    )

    assert proposal.completed_appraisal_count == 68
    assert proposal.supporting_count == 22
    assert proposal.context_only_count == 46
    assert len(proposal.claims) == 8
    assert proposal.novelty_claim_authorized is False
    assert proposal.scientific_conclusions_authorized is False


def test_synthesis_rejects_context_only_evidence_as_supporting() -> None:
    proposal = load_saturated_evidence_synthesis_proposal(PROPOSAL)
    context_link = proposal.claims[4].evidence[0].model_copy(
        update={
            "evidence_id": "PMID:22196354",
            "direction": EvidenceDirection.SUPPORTS,
        }
    )
    changed_claim = proposal.claims[4].model_copy(
        update={"evidence": [context_link, *proposal.claims[4].evidence[1:]]}
    )
    changed = proposal.model_copy(
        update={"claims": [*proposal.claims[:4], changed_claim, *proposal.claims[5:]]}
    )

    with pytest.raises(EvidenceSynthesisError, match="context-only"):
        SaturatedEvidenceSynthesisService().validate(
            changed,
            load_evidence_review_progress(PROGRESS),
            _appraisals(),
            progress_path=PROGRESS,
        )


def test_synthesis_rejects_missing_appraisal_coverage() -> None:
    with pytest.raises(EvidenceSynthesisError, match="every completed appraisal"):
        SaturatedEvidenceSynthesisService().validate(
            load_saturated_evidence_synthesis_proposal(PROPOSAL),
            load_evidence_review_progress(PROGRESS),
            _appraisals()[:-1],
            progress_path=PROGRESS,
        )
