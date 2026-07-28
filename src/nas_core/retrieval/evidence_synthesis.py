"""Validate a claim-level proposal against saturated progress and locked appraisals."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from nas_core.domain.appraisal import EvidenceRole, FullTextAppraisal
from nas_core.domain.evidence_review import EvidenceReviewProgress
from nas_core.domain.evidence_synthesis import (
    AuthorizedSaturatedEvidenceSynthesis,
    EvidenceDirection,
    EvidenceSynthesisFounderConfirmation,
    SaturatedEvidenceSynthesisProposal,
)
from nas_core.ingestion.gdc import sha256


class EvidenceSynthesisError(RuntimeError):
    """Raised when a synthesis proposal is not bound to locked evidence."""


class SaturatedEvidenceSynthesisService:
    def validate(
        self,
        proposal: SaturatedEvidenceSynthesisProposal,
        progress: EvidenceReviewProgress,
        appraisals: Sequence[FullTextAppraisal],
        *,
        progress_path: Path,
    ) -> SaturatedEvidenceSynthesisProposal:
        if (
            progress.study_id != proposal.study_id
            or progress.question_id != proposal.question_id
            or progress.question_version != proposal.question_version
            or not progress.stopping_rule_satisfied
            or progress.review_status.value != "complete"
            or progress.pending_candidate_count
        ):
            raise EvidenceSynthesisError(
                "claim synthesis requires the matching saturated evidence review"
            )
        if proposal.progress_sha256 != sha256(progress_path.read_bytes()):
            raise EvidenceSynthesisError(
                "claim synthesis is bound to a different progress receipt"
            )
        if (
            proposal.eligible_evidence_count != progress.eligible_evidence_count
            or proposal.completed_appraisal_count
            != progress.completed_appraisal_count
            or proposal.access_restricted_count
            != progress.access_restricted_count
        ):
            raise EvidenceSynthesisError(
                "claim synthesis aggregate counts do not match progress"
            )
        if len(appraisals) != progress.completed_appraisal_count:
            raise EvidenceSynthesisError(
                "claim synthesis must receive every completed appraisal exactly once"
            )
        screening_ids = [item.screening_id for item in appraisals]
        if len(screening_ids) != len(set(screening_ids)):
            raise EvidenceSynthesisError(
                "claim synthesis appraisal set contains duplicate screening identities"
            )
        if any(
            item.study_id != progress.study_id
            or not item.founder_authorized
            or item.scientific_conclusions_drawn
            for item in appraisals
        ):
            raise EvidenceSynthesisError(
                "claim synthesis appraisal set is not fully locked and nonconclusive"
            )
        role_counts = {
            role: sum(item.evidence_role is role for item in appraisals)
            for role in (
                EvidenceRole.ANCHOR,
                EvidenceRole.SUPPORTING,
                EvidenceRole.CONTEXT_ONLY,
            )
        }
        if (
            proposal.anchor_count != role_counts[EvidenceRole.ANCHOR]
            or proposal.supporting_count != role_counts[EvidenceRole.SUPPORTING]
            or proposal.context_only_count
            != role_counts[EvidenceRole.CONTEXT_ONLY]
        ):
            raise EvidenceSynthesisError(
                "claim synthesis evidence-role counts do not match appraisals"
            )
        by_evidence_id: dict[str, FullTextAppraisal] = {}
        for appraisal in appraisals:
            identifier = (
                f"PMID:{appraisal.pmid}"
                if appraisal.pmid is not None
                else f"DOI:{appraisal.doi}"
            )
            normalized = identifier.casefold()
            if normalized in by_evidence_id:
                raise EvidenceSynthesisError(
                    "claim synthesis appraisal set contains duplicate evidence identities"
                )
            by_evidence_id[normalized] = appraisal
        for claim in proposal.claims:
            for link in claim.evidence:
                linked_appraisal = by_evidence_id.get(
                    link.evidence_id.casefold()
                )
                if linked_appraisal is None:
                    raise EvidenceSynthesisError(
                        f"claim {claim.claim_id} cites evidence outside locked appraisals"
                    )
                if (
                    link.direction is EvidenceDirection.SUPPORTS
                    and linked_appraisal.evidence_role
                    is not EvidenceRole.SUPPORTING
                ):
                    raise EvidenceSynthesisError(
                        f"claim {claim.claim_id} treats context-only evidence as supporting"
                    )
        return proposal

    def authorize(
        self,
        proposal: SaturatedEvidenceSynthesisProposal,
        confirmation: EvidenceSynthesisFounderConfirmation,
        progress: EvidenceReviewProgress,
        appraisals: Sequence[FullTextAppraisal],
        *,
        proposal_path: Path,
        progress_path: Path,
    ) -> AuthorizedSaturatedEvidenceSynthesis:
        validated = self.validate(
            proposal,
            progress,
            appraisals,
            progress_path=progress_path,
        )
        proposal_sha256 = sha256(proposal_path.read_bytes())
        if (
            confirmation.study_id != validated.study_id
            or confirmation.synthesis_version != validated.synthesis_version
            or confirmation.proposal_sha256 != proposal_sha256
            or confirmation.progress_sha256 != validated.progress_sha256
        ):
            raise EvidenceSynthesisError(
                "founder confirmation is bound to a different synthesis proposal"
            )
        return AuthorizedSaturatedEvidenceSynthesis(
            synthesis_version=validated.synthesis_version,
            study_id=validated.study_id,
            question_id=validated.question_id,
            question_version=validated.question_version,
            proposal_sha256=proposal_sha256,
            progress_sha256=validated.progress_sha256,
            eligible_evidence_count=validated.eligible_evidence_count,
            completed_appraisal_count=validated.completed_appraisal_count,
            access_restricted_count=validated.access_restricted_count,
            anchor_count=validated.anchor_count,
            supporting_count=validated.supporting_count,
            context_only_count=validated.context_only_count,
            claims=validated.claims,
            assistant_disclosure=validated.assistant_disclosure,
            confirmation_statement=confirmation.confirmation_statement,
            founder_id=confirmation.founder_id,
            founder_name=confirmation.founder_name,
            reviewer_role=confirmation.reviewer_role,
            authorized_at=confirmation.confirmed_at,
            working_synthesis_authorized=True,
            novelty_claim_authorized=False,
            molecular_data_access_authorized=False,
            outcome_data_access_authorized=False,
            clinical_claims_authorized=False,
            publication_authorized=False,
        )
