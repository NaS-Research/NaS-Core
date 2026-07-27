"""Typed, non-authoritative claim synthesis over a saturated evidence review."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceSynthesisModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceDirection(StrEnum):
    SUPPORTS = "supports"
    LIMITS_OR_CONTRADICTS = "limits_or_contradicts"
    NULL_OR_NEGATIVE = "null_or_negative"
    CONTEXTUALIZES = "contextualizes"


class ProposedClaimStatus(StrEnum):
    ESTABLISHED = "established"
    PARTLY_ESTABLISHED = "partly_established"
    UNRESOLVED = "unresolved"


class ClaimEvidenceLink(EvidenceSynthesisModel):
    evidence_id: str = Field(pattern=r"^(PMID:[0-9]+|DOI:.+)$")
    direction: EvidenceDirection
    rationale: str = Field(min_length=1)


class ClaimSynthesis(EvidenceSynthesisModel):
    claim_id: str = Field(pattern=r"^CLM-[0-9]{3}$")
    claim: str = Field(min_length=1)
    proposed_status: ProposedClaimStatus
    evidence: list[ClaimEvidenceLink] = Field(min_length=1)
    synthesis: str = Field(min_length=1)
    residual_uncertainty: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_claim(self) -> ClaimSynthesis:
        evidence_ids = [item.evidence_id.casefold() for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("claim synthesis cannot cite one evidence identity twice")
        if (
            self.proposed_status is ProposedClaimStatus.ESTABLISHED
            and not any(
                item.direction is EvidenceDirection.SUPPORTS
                for item in self.evidence
            )
        ):
            raise ValueError("an established proposal requires supporting evidence")
        return self


class SaturatedEvidenceSynthesisProposal(EvidenceSynthesisModel):
    schema_version: str = "1.0.0"
    synthesis_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    progress_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    eligible_evidence_count: int = Field(ge=0)
    completed_appraisal_count: int = Field(ge=0)
    access_restricted_count: int = Field(ge=0)
    anchor_count: int = Field(ge=0)
    supporting_count: int = Field(ge=0)
    context_only_count: int = Field(ge=0)
    claims: list[ClaimSynthesis] = Field(min_length=1)
    assistant_disclosure: str = Field(min_length=1)
    prepared_at: datetime
    founder_decision_recorded: bool = False
    novelty_claim_authorized: bool = False
    scientific_conclusions_authorized: bool = False

    @model_validator(mode="after")
    def validate_boundary(self) -> SaturatedEvidenceSynthesisProposal:
        if (
            self.anchor_count + self.supporting_count + self.context_only_count
            != self.completed_appraisal_count
        ):
            raise ValueError("synthesis evidence-role counts do not reconcile")
        claim_ids = [item.claim_id for item in self.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("synthesis claim IDs must be unique")
        if (
            self.founder_decision_recorded
            or self.novelty_claim_authorized
            or self.scientific_conclusions_authorized
        ):
            raise ValueError(
                "a synthesis proposal cannot authorize founder decisions or conclusions"
            )
        return self


def load_saturated_evidence_synthesis_proposal(
    path: Path,
) -> SaturatedEvidenceSynthesisProposal:
    return SaturatedEvidenceSynthesisProposal.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
