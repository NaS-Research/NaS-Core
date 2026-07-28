from pathlib import Path

import pytest

from nas_core.domain.appraisal import FullTextAppraisal, load_full_text_appraisal
from nas_core.domain.evidence_review import load_evidence_review_progress
from nas_core.domain.evidence_synthesis import (
    EvidenceDirection,
    EvidenceSynthesisFounderConfirmation,
    evidence_synthesis_confirmation_statement,
    load_authorized_saturated_evidence_synthesis,
    load_evidence_synthesis_founder_confirmation,
    load_saturated_evidence_synthesis_proposal,
)
from nas_core.ingestion.gdc import sha256
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
CONFIRMATION = (
    LITERATURE
    / "FOUNDER_SATURATED_EVIDENCE_SYNTHESIS_CONFIRMATION_v1.0.0.yaml"
)
AUTHORIZED = LITERATURE / "saturated_evidence_synthesis_v1.0.0.yaml"
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


def test_checked_in_founder_authorization_is_checksum_bound_and_narrow() -> None:
    confirmation = load_evidence_synthesis_founder_confirmation(CONFIRMATION)
    authorized = load_authorized_saturated_evidence_synthesis(AUTHORIZED)

    assert confirmation.proposal_sha256 == sha256(PROPOSAL.read_bytes())
    assert confirmation.progress_sha256 == sha256(PROGRESS.read_bytes())
    assert authorized.proposal_sha256 == confirmation.proposal_sha256
    assert authorized.confirmation_statement == confirmation.confirmation_statement
    assert authorized.working_synthesis_authorized is True
    assert authorized.novelty_claim_authorized is False
    assert authorized.molecular_data_access_authorized is False
    assert authorized.outcome_data_access_authorized is False
    assert authorized.clinical_claims_authorized is False
    assert authorized.publication_authorized is False


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


def test_founder_confirmation_authorizes_only_working_synthesis() -> None:
    proposal = load_saturated_evidence_synthesis_proposal(PROPOSAL)
    confirmation = EvidenceSynthesisFounderConfirmation(
        study_id=proposal.study_id,
        synthesis_version=proposal.synthesis_version,
        proposal_sha256=sha256(PROPOSAL.read_bytes()),
        progress_sha256=proposal.progress_sha256,
        confirmation_statement=evidence_synthesis_confirmation_statement(
            proposal.synthesis_version
        ),
        founder_id="dalron-j-robertson",
        founder_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        confirmed_at="2026-07-28T00:00:00-05:00",
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )

    authorized = SaturatedEvidenceSynthesisService().authorize(
        proposal,
        confirmation,
        load_evidence_review_progress(PROGRESS),
        _appraisals(),
        proposal_path=PROPOSAL,
        progress_path=PROGRESS,
    )

    assert authorized.working_synthesis_authorized is True
    assert authorized.novelty_claim_authorized is False
    assert authorized.molecular_data_access_authorized is False
    assert authorized.outcome_data_access_authorized is False
    assert authorized.clinical_claims_authorized is False
    assert authorized.publication_authorized is False


def test_synthesis_authorization_rejects_wrong_proposal_checksum() -> None:
    proposal = load_saturated_evidence_synthesis_proposal(PROPOSAL)
    confirmation = EvidenceSynthesisFounderConfirmation(
        study_id=proposal.study_id,
        synthesis_version=proposal.synthesis_version,
        proposal_sha256="0" * 64,
        progress_sha256=proposal.progress_sha256,
        confirmation_statement=evidence_synthesis_confirmation_statement(
            proposal.synthesis_version
        ),
        founder_id="dalron-j-robertson",
        founder_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        confirmed_at="2026-07-28T00:00:00-05:00",
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )

    with pytest.raises(EvidenceSynthesisError, match="different synthesis"):
        SaturatedEvidenceSynthesisService().authorize(
            proposal,
            confirmation,
            load_evidence_review_progress(PROGRESS),
            _appraisals(),
            proposal_path=PROPOSAL,
            progress_path=PROGRESS,
        )
