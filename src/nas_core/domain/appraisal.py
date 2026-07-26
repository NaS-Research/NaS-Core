"""Typed full-text eligibility and methodological appraisal contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.snapshots import StoredObject


def appraisal_batch_confirmation_statement(batch_number: int) -> str:
    """Return the exact founder statement for one numbered appraisal batch."""
    if not 1 <= batch_number <= 9999:
        raise ValueError("appraisal batch number must be between 1 and 9999")
    return f"I confirm citation appraisal batch {batch_number:04d} as written."


APPRAISAL_BATCH_CONFIRMATION_STATEMENT = appraisal_batch_confirmation_statement(1)


class AppraisalModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StudyDesign(StrEnum):
    PREDICTION_MODEL = "prediction_model"
    CLASSIFIER_COMPARISON = "classifier_comparison"
    ANALYTICAL_VALIDATION = "analytical_validation"
    OBSERVATIONAL_CONCORDANCE = "observational_concordance"
    OUTCOME_ASSOCIATION = "outcome_association"
    METHODS_NORMALIZATION = "methods_normalization"
    OTHER = "other"


class AppraisalDomainName(StrEnum):
    POPULATION_SELECTION = "population_selection"
    SPECIMEN_AND_MEASUREMENT = "specimen_and_measurement"
    CLASSIFIER_IMPLEMENTATION = "classifier_implementation"
    REFERENCE_COMPARATOR = "reference_comparator"
    ANALYSIS_AND_STATISTICS = "analysis_and_statistics"
    VALIDATION_AND_TRANSPORTABILITY = "validation_and_transportability"
    REPORTING_AND_REPRODUCIBILITY = "reporting_and_reproducibility"


class RiskJudgment(StrEnum):
    LOW = "low"
    SOME_CONCERNS = "some_concerns"
    HIGH = "high"
    UNCLEAR = "unclear"
    NOT_APPLICABLE = "not_applicable"


class FullTextEligibility(StrEnum):
    ELIGIBLE = "eligible"
    EXCLUDE = "exclude"


class EvidenceRole(StrEnum):
    ANCHOR = "anchor"
    SUPPORTING = "supporting"
    CONTEXT_ONLY = "context_only"
    EXCLUDED = "excluded"


class AppraisalReviewMethod(StrEnum):
    FOUNDER_ONLY = "founder_only"
    FOUNDER_WITH_AI_ASSISTANCE = "founder_with_ai_assistance"


class FullTextAccessStatus(StrEnum):
    REPOSITORY_CANDIDATE = "repository_candidate"
    ACCESS_CHECK_REQUIRED = "access_check_required"


class AppraisalCompletionStatus(StrEnum):
    AWAITING_FULL_TEXT = "awaiting_full_text"
    ACCESS_RESTRICTED = "access_restricted"
    DUPLICATE_RESOLVED = "duplicate_resolved"
    READY_FOR_APPRAISAL = "ready_for_appraisal"
    COMPLETED = "completed"


class FullTextAccessOutcome(StrEnum):
    RESTRICTED = "restricted"


class FullTextReviewAccessMode(StrEnum):
    READ_ONLY_EPHEMERAL = "read_only_ephemeral"


class FullTextContentRepresentation(StrEnum):
    RAW_SOURCE_BYTES = "raw_source_bytes"
    CANONICAL_PMC_OAI_ARTICLE_XML_V1 = "canonical_pmc_oai_article_xml_v1"
    CANONICAL_PUBLISHER_HTML_V1 = "canonical_publisher_html_v1"


class DuplicateRelationship(StrEnum):
    PREPRINT_OF = "preprint_of"
    DUPLICATE_REPORT = "duplicate_report"


class PublicationStage(StrEnum):
    PREPRINT = "preprint"
    VERSION_OF_RECORD = "version_of_record"


class PublicationVersionIdentity(AppraisalModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    title: str = Field(min_length=1)
    publication_stage: PublicationStage
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    pmid: str | None = Field(default=None, pattern=r"^[0-9]+$")
    doi: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_identity(self) -> PublicationVersionIdentity:
        if not any((self.pmcid, self.pmid, self.doi)):
            raise ValueError("publication version identity requires one identifier")
        return self


class PublicationVersionLinkProposal(AppraisalModel):
    """Non-authoritative same-study link proposed for founder review."""

    schema_version: str = "1.0.0"
    proposal_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    relationship: DuplicateRelationship
    earlier: PublicationVersionIdentity
    canonical: PublicationVersionIdentity
    matching_evidence: list[str] = Field(min_length=3)
    rationale: str = Field(min_length=1)
    assistant_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    assistant_disclosure: str = Field(min_length=1)
    proposed_at: datetime
    founder_decision_recorded: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_proposal(self) -> PublicationVersionLinkProposal:
        if self.relationship is not DuplicateRelationship.PREPRINT_OF:
            raise ValueError("publication version proposal must use preprint_of")
        if self.earlier.screening_id == self.canonical.screening_id:
            raise ValueError("publication version proposal requires distinct records")
        if (
            self.earlier.publication_stage is not PublicationStage.PREPRINT
            or self.canonical.publication_stage
            is not PublicationStage.VERSION_OF_RECORD
        ):
            raise ValueError(
                "publication version proposal must link preprint to version of record"
            )
        if self.founder_decision_recorded:
            raise ValueError("publication version proposal cannot record founder decision")
        if self.scientific_conclusions_drawn:
            raise ValueError("publication version proposal cannot draw conclusions")
        return self


class PublicationVersionLinkDecision(AppraisalModel):
    """Founder-authorized same-study link used to prevent evidence double counting."""

    schema_version: str = "1.0.0"
    decision_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    relationship: DuplicateRelationship
    earlier: PublicationVersionIdentity
    canonical: PublicationVersionIdentity
    matching_evidence: list[str] = Field(min_length=3)
    rationale: str = Field(min_length=1)
    reviewer_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reviewer_name: str = Field(min_length=1)
    review_method: AppraisalReviewMethod
    assistant_disclosure: str | None = Field(default=None, min_length=1)
    founder_authorized: bool
    decided_at: datetime
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_decision(self) -> PublicationVersionLinkDecision:
        proposal = PublicationVersionLinkProposal(
            proposal_version=self.decision_version,
            study_id=self.study_id,
            relationship=self.relationship,
            earlier=self.earlier,
            canonical=self.canonical,
            matching_evidence=self.matching_evidence,
            rationale=self.rationale,
            assistant_id="validation-only",
            assistant_disclosure="Validation-only reconstruction.",
            proposed_at=self.decided_at,
        )
        if proposal.scientific_conclusions_drawn:
            raise ValueError("publication version decision cannot draw conclusions")
        if not self.founder_authorized:
            raise ValueError("publication version decision requires founder authorization")
        if (
            self.review_method is AppraisalReviewMethod.FOUNDER_WITH_AI_ASSISTANCE
            and self.assistant_disclosure is None
        ):
            raise ValueError("AI-assisted version decision requires disclosure")
        if (
            self.review_method is AppraisalReviewMethod.FOUNDER_ONLY
            and self.assistant_disclosure is not None
        ):
            raise ValueError("founder-only version decision cannot contain AI disclosure")
        if self.scientific_conclusions_drawn:
            raise ValueError("publication version decision cannot draw conclusions")
        return self


class FullTextDuplicateDecision(AppraisalModel):
    schema_version: str = "1.0.0"
    decision_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    title: str = Field(min_length=1)
    relationship: DuplicateRelationship
    canonical_screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    canonical_title: str = Field(min_length=1)
    matching_identifiers: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    reviewer_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reviewer_name: str = Field(min_length=1)
    founder_authorized: bool
    decided_at: datetime
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_decision(self) -> FullTextDuplicateDecision:
        if self.screening_id == self.canonical_screening_id:
            raise ValueError("duplicate decision must reference a different canonical record")
        if not self.founder_authorized:
            raise ValueError("duplicate resolution requires founder authorization")
        if self.scientific_conclusions_drawn:
            raise ValueError("duplicate resolution cannot draw scientific conclusions")
        return self


class FullTextAccessDecision(AppraisalModel):
    schema_version: str = "1.0.0"
    decision_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    pmid: str | None = Field(default=None, pattern=r"^[0-9]+$")
    doi: str | None = Field(default=None, min_length=1)
    title: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    observed_license: str = Field(min_length=1)
    license_url: str = Field(min_length=1)
    outcome: FullTextAccessOutcome
    policy_reason: str = Field(min_length=1)
    checked_at: datetime
    durable_full_text_stored: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_decision(self) -> FullTextAccessDecision:
        if not any((self.pmcid, self.pmid, self.doi)):
            raise ValueError("access decision requires PMCID, PMID, or DOI")
        if self.durable_full_text_stored:
            raise ValueError("restricted access decision cannot claim durable storage")
        if self.scientific_conclusions_drawn:
            raise ValueError("access decision cannot draw scientific conclusions")
        return self


class FullTextInventoryRecord(AppraisalModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    publication_year: int | None = None
    journal: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    doi: str | None = None
    bibliographic_open_access_flag: bool | None = None
    access_status: FullTextAccessStatus
    full_text_retrieved: bool = False
    full_text_appraised: bool = False


class FullTextInventory(AppraisalModel):
    schema_version: str = "1.0.0"
    inventory_version: str = "1.0.0"
    study_id: str = Field(min_length=1)
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    provisional_inclusion_count: int = Field(ge=1)
    repository_candidate_count: int = Field(ge=0)
    access_check_required_count: int = Field(ge=0)
    records: list[FullTextInventoryRecord] = Field(min_length=1)
    full_texts_retrieved: int = 0
    appraisals_completed: int = 0
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_counts(self) -> FullTextInventory:
        if len(self.records) != self.provisional_inclusion_count:
            raise ValueError("inventory record count does not match provisional inclusions")
        repository = sum(
            item.access_status is FullTextAccessStatus.REPOSITORY_CANDIDATE
            for item in self.records
        )
        if repository != self.repository_candidate_count:
            raise ValueError("repository-candidate count does not reconcile")
        if len(self.records) - repository != self.access_check_required_count:
            raise ValueError("access-check count does not reconcile")
        if self.full_texts_retrieved or self.appraisals_completed:
            raise ValueError("initial access inventory cannot claim completed downstream work")
        if self.scientific_conclusions_drawn:
            raise ValueError("an access inventory cannot draw scientific conclusions")
        return self


class FullTextLicense(AppraisalModel):
    name: str = Field(min_length=1)
    spdx_identifier: str = Field(pattern=r"^CC-BY-(?:2\.0|2\.5|3\.0|4\.0)$")
    url: str = Field(min_length=1)
    copyright_statement: str = Field(min_length=1)


class FullTextRetrievalManifest(AppraisalModel):
    schema_version: str = "1.0.0"
    retrieval_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    pmid: str | None = None
    doi: str | None = None
    title: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    retrieved_at: datetime
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    license: FullTextLicense
    full_text_object: StoredObject
    scientific_conclusions_drawn: bool = False
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class FullTextRetrievalReceipt(AppraisalModel):
    schema_version: str = "1.0.0"
    retrieval_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    title: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    retrieved_at: datetime
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    license: FullTextLicense
    manifest_object_key: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    full_text_object_key: str = Field(min_length=1)
    full_text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    full_text_size_bytes: int = Field(ge=1)
    verified_at: datetime
    manifest_checksum_verified: bool
    full_text_checksum_verified: bool
    article_identity_verified: bool
    license_verified: bool
    scientific_conclusions_drawn: bool = False


class FullTextReadOnlyReviewReceipt(AppraisalModel):
    """Receipt for lawful review when durable full-text storage is not authorized."""

    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    review_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    study_id: str = Field(min_length=1)
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    pmid: str | None = Field(default=None, pattern=r"^[0-9]+$")
    doi: str | None = None
    title: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    access_mode: FullTextReviewAccessMode
    content_representation: FullTextContentRepresentation = (
        FullTextContentRepresentation.RAW_SOURCE_BYTES
    )
    access_basis: str = Field(min_length=1)
    observed_rights: str = Field(min_length=1)
    rights_url: str | None = Field(default=None, min_length=1)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_size_bytes: int = Field(ge=1)
    accessed_at: datetime
    verified_at: datetime
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    checksum_verified: bool
    article_identity_verified: bool
    lawful_read_access_verified: bool
    durable_full_text_stored: bool = False
    redistribution_authorized: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_receipt(self) -> FullTextReadOnlyReviewReceipt:
        if not (
            self.checksum_verified
            and self.article_identity_verified
            and self.lawful_read_access_verified
        ):
            raise ValueError("read-only review receipt requires all verification flags")
        if self.durable_full_text_stored:
            raise ValueError("read-only review receipt cannot claim durable storage")
        if self.redistribution_authorized:
            raise ValueError("read-only review receipt cannot authorize redistribution")
        if self.scientific_conclusions_drawn:
            raise ValueError("read-only review receipt cannot draw scientific conclusions")
        return self


class AppraisalDomain(AppraisalModel):
    domain: AppraisalDomainName
    judgment: RiskJudgment
    rationale: str = Field(min_length=1)
    evidence_locations: list[str] = Field(min_length=1)


class FullTextAppraisal(AppraisalModel):
    schema_version: str = "1.0.0"
    appraisal_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    title: str = Field(min_length=1)
    pmid: str | None = None
    doi: str | None = None
    full_text_source_url: str = Field(min_length=1)
    full_text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    access_basis: str = Field(min_length=1)
    study_design: StudyDesign
    eligibility: FullTextEligibility
    full_text_exclusion_reason: str | None = Field(default=None, min_length=1)
    domains: list[AppraisalDomain] = Field(min_length=7, max_length=7)
    evidence_role: EvidenceRole
    key_strengths: list[str]
    key_limitations: list[str]
    conflicts_and_funding: str = Field(min_length=1)
    reviewer_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reviewer_name: str = Field(min_length=1)
    review_method: AppraisalReviewMethod
    assistant_disclosure: str | None = Field(default=None, min_length=1)
    founder_authorized: bool
    assessed_at: datetime
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_appraisal(self) -> FullTextAppraisal:
        names = [item.domain for item in self.domains]
        if len(set(names)) != len(AppraisalDomainName) or set(names) != set(
            AppraisalDomainName
        ):
            raise ValueError("each required appraisal domain must appear exactly once")
        if self.scientific_conclusions_drawn:
            raise ValueError("an appraisal cannot itself record a scientific conclusion")
        if not self.founder_authorized:
            raise ValueError("a locked appraisal requires explicit founder authorization")
        if (
            self.review_method is AppraisalReviewMethod.FOUNDER_WITH_AI_ASSISTANCE
            and self.assistant_disclosure is None
        ):
            raise ValueError("AI-assisted appraisal requires an assistant disclosure")
        if (
            self.review_method is AppraisalReviewMethod.FOUNDER_ONLY
            and self.assistant_disclosure is not None
        ):
            raise ValueError("founder-only appraisal cannot contain an AI disclosure")
        if self.eligibility is FullTextEligibility.EXCLUDE:
            if self.evidence_role is not EvidenceRole.EXCLUDED:
                raise ValueError("a full-text exclusion must have the excluded evidence role")
            if self.full_text_exclusion_reason is None:
                raise ValueError("a full-text exclusion requires one explicit reason")
        else:
            if self.evidence_role is EvidenceRole.EXCLUDED:
                raise ValueError("an eligible study cannot have the excluded evidence role")
            if self.full_text_exclusion_reason is not None:
                raise ValueError("an eligible study cannot have a full-text exclusion reason")
        judgments = {item.domain: item.judgment for item in self.domains}
        if self.evidence_role is EvidenceRole.ANCHOR:
            if any(
                value in {RiskJudgment.HIGH, RiskJudgment.UNCLEAR}
                for value in judgments.values()
            ):
                raise ValueError("an anchor study cannot contain high or unclear risk domains")
            required_low = {
                AppraisalDomainName.ANALYSIS_AND_STATISTICS,
                AppraisalDomainName.VALIDATION_AND_TRANSPORTABILITY,
            }
            if any(judgments[name] is not RiskJudgment.LOW for name in required_low):
                raise ValueError("anchor studies require low-risk analysis and validation")
        if self.evidence_role is EvidenceRole.SUPPORTING and any(
            value is RiskJudgment.HIGH for value in judgments.values()
        ):
            raise ValueError("a study with a high-risk domain must be context-only or excluded")
        return self


class FullTextAppraisalProposal(AppraisalModel):
    """AI-assisted appraisal draft that cannot be mistaken for locked evidence."""

    schema_version: str = "1.0.0"
    proposal_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    title: str = Field(min_length=1)
    pmid: str | None = None
    doi: str | None = None
    full_text_source_url: str = Field(min_length=1)
    full_text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    access_basis: str = Field(min_length=1)
    study_design: StudyDesign
    eligibility: FullTextEligibility
    full_text_exclusion_reason: str | None = Field(default=None, min_length=1)
    domains: list[AppraisalDomain] = Field(min_length=7, max_length=7)
    proposed_evidence_role: EvidenceRole
    key_strengths: list[str]
    key_limitations: list[str]
    conflicts_and_funding: str = Field(min_length=1)
    assistant_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    assistant_disclosure: str = Field(min_length=1)
    proposed_at: datetime
    founder_decision_recorded: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_proposal(self) -> FullTextAppraisalProposal:
        names = [item.domain for item in self.domains]
        if len(set(names)) != len(AppraisalDomainName) or set(names) != set(
            AppraisalDomainName
        ):
            raise ValueError("each required appraisal domain must appear exactly once")
        if self.founder_decision_recorded:
            raise ValueError("an appraisal proposal cannot record a founder decision")
        if self.scientific_conclusions_drawn:
            raise ValueError("an appraisal proposal cannot draw a scientific conclusion")
        if self.eligibility is FullTextEligibility.EXCLUDE:
            if self.proposed_evidence_role is not EvidenceRole.EXCLUDED:
                raise ValueError("a proposed exclusion must have the excluded evidence role")
            if self.full_text_exclusion_reason is None:
                raise ValueError("a proposed exclusion requires one explicit reason")
        else:
            if self.proposed_evidence_role is EvidenceRole.EXCLUDED:
                raise ValueError("an eligible proposal cannot use the excluded evidence role")
            if self.full_text_exclusion_reason is not None:
                raise ValueError("an eligible proposal cannot have an exclusion reason")
        judgments = {item.domain: item.judgment for item in self.domains}
        if self.proposed_evidence_role is EvidenceRole.ANCHOR:
            if any(
                value in {RiskJudgment.HIGH, RiskJudgment.UNCLEAR}
                for value in judgments.values()
            ):
                raise ValueError("a proposed anchor cannot contain high or unclear domains")
            required_low = {
                AppraisalDomainName.ANALYSIS_AND_STATISTICS,
                AppraisalDomainName.VALIDATION_AND_TRANSPORTABILITY,
            }
            if any(judgments[name] is not RiskJudgment.LOW for name in required_low):
                raise ValueError("proposed anchors require low-risk analysis and validation")
        if self.proposed_evidence_role is EvidenceRole.SUPPORTING and any(
            value is RiskJudgment.HIGH for value in judgments.values()
        ):
            raise ValueError(
                "a proposal with a high-risk domain must be context-only or excluded"
            )
        return self


class FullTextAppraisalProposalReference(AppraisalModel):
    filename: str = Field(
        pattern=r"^(?:PMC|PMID|PPR)[0-9]+-v[0-9]+\.[0-9]+\.[0-9]+\.yaml$"
    )
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class PublicationVersionLinkProposalReference(AppraisalModel):
    filename: str = Field(
        pattern=(
            r"^PMC[0-9]+-to-PMC[0-9]+"
            r"-v[0-9]+\.[0-9]+\.[0-9]+\.yaml$"
        )
    )
    earlier_screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    canonical_screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class FullTextAppraisalBatchConfirmation(AppraisalModel):
    schema_version: str = "1.0.0"
    confirmation_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    batch_number: int = Field(ge=1, le=9999)
    packet_filename: str = Field(
        pattern=(
            r"^FOUNDER_CITATION_APPRAISAL_BATCH_[0-9]{4}"
            r"_v[0-9]+\.[0-9]+\.[0-9]+\.md$"
        )
    )
    packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    proposal_count: int = Field(ge=1)
    proposals: list[FullTextAppraisalProposalReference] = Field(min_length=1)
    version_link_count: int = Field(default=0, ge=0)
    version_links: list[PublicationVersionLinkProposalReference] = Field(
        default_factory=list
    )
    confirmation_statement: str
    founder_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    founder_name: str = Field(min_length=1)
    reviewer_role: str = Field(min_length=1)
    confirmed_at: datetime
    founder_authorized: bool
    founder_role_conflict_disclosed: bool

    @model_validator(mode="after")
    def validate_confirmation(self) -> FullTextAppraisalBatchConfirmation:
        expected_statement = appraisal_batch_confirmation_statement(
            self.batch_number
        )
        if self.confirmation_statement != expected_statement:
            raise ValueError("appraisal confirmation statement is not exact")
        expected_packet_prefix = (
            f"FOUNDER_CITATION_APPRAISAL_BATCH_{self.batch_number:04d}_"
        )
        if not self.packet_filename.startswith(expected_packet_prefix):
            raise ValueError("appraisal packet filename does not match batch number")
        if not self.founder_authorized:
            raise ValueError("appraisal confirmation requires founder authorization")
        if not self.founder_role_conflict_disclosed:
            raise ValueError("founder reviewer-role conflict must be disclosed")
        if len(self.proposals) != self.proposal_count:
            raise ValueError("appraisal confirmation proposal count does not reconcile")
        if len({item.filename for item in self.proposals}) != len(self.proposals):
            raise ValueError("appraisal confirmation filenames must be unique")
        if len({item.screening_id for item in self.proposals}) != len(self.proposals):
            raise ValueError("appraisal confirmation screening IDs must be unique")
        if len({item.sha256 for item in self.proposals}) != len(self.proposals):
            raise ValueError("appraisal confirmation proposal checksums must be unique")
        if len(self.version_links) != self.version_link_count:
            raise ValueError("appraisal confirmation version-link count does not reconcile")
        if len({item.filename for item in self.version_links}) != len(
            self.version_links
        ):
            raise ValueError("appraisal confirmation version-link filenames must be unique")
        linked_ids = [
            screening_id
            for item in self.version_links
            for screening_id in (
                item.earlier_screening_id,
                item.canonical_screening_id,
            )
        ]
        if len(set(linked_ids)) != len(linked_ids):
            raise ValueError("appraisal confirmation version-link records must be unique")
        if len({item.sha256 for item in self.version_links}) != len(
            self.version_links
        ):
            raise ValueError("appraisal confirmation version-link checksums must be unique")
        return self


class EvidenceStudyFamilyMember(AppraisalModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    title: str = Field(min_length=1)
    publication_stage: PublicationStage | None = None
    canonical: bool


class EvidenceStudyFamily(AppraisalModel):
    canonical_screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    canonical_title: str = Field(min_length=1)
    members: list[EvidenceStudyFamilyMember] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_family(self) -> EvidenceStudyFamily:
        if len({item.screening_id for item in self.members}) != len(self.members):
            raise ValueError("evidence family members must be unique")
        canonical = [item for item in self.members if item.canonical]
        if len(canonical) != 1:
            raise ValueError("evidence family requires exactly one canonical member")
        if (
            canonical[0].screening_id != self.canonical_screening_id
            or canonical[0].title != self.canonical_title
        ):
            raise ValueError("evidence family canonical identity does not reconcile")
        return self


class PublicationVersionReconciliationReceipt(AppraisalModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(min_length=1)
    generated_at: datetime
    appraisal_count: int = Field(ge=1)
    version_link_count: int = Field(ge=0)
    unique_study_count: int = Field(ge=1)
    families: list[EvidenceStudyFamily] = Field(min_length=1)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_receipt(self) -> PublicationVersionReconciliationReceipt:
        members = [item for family in self.families for item in family.members]
        if len(members) != self.appraisal_count:
            raise ValueError("version reconciliation appraisal count does not reconcile")
        if len({item.screening_id for item in members}) != len(members):
            raise ValueError("version reconciliation appraisals must appear exactly once")
        if len(self.families) != self.unique_study_count:
            raise ValueError("version reconciliation unique-study count does not reconcile")
        if self.appraisal_count - self.version_link_count != self.unique_study_count:
            raise ValueError("version reconciliation link count does not reconcile")
        linked_families = sum(len(family.members) > 1 for family in self.families)
        if linked_families != self.version_link_count:
            raise ValueError("version reconciliation linked families do not reconcile")
        if self.scientific_conclusions_drawn:
            raise ValueError("version reconciliation cannot draw scientific conclusions")
        return self


class FullTextAppraisalProgressRecord(AppraisalModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    title: str = Field(min_length=1)
    pmcid: str | None = None
    status: AppraisalCompletionStatus
    retrieval_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    read_only_review_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    full_text_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    appraisal_source_review_id: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    appraisal_source_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    appraisal_version: str | None = Field(
        default=None, pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$"
    )
    evidence_role: EvidenceRole | None = None
    observed_license: str | None = None
    canonical_screening_id: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    duplicate_relationship: DuplicateRelationship | None = None

    @model_validator(mode="after")
    def validate_state(self) -> FullTextAppraisalProgressRecord:
        source_ids = (self.retrieval_id, self.read_only_review_id)
        source_fields = (*source_ids, self.full_text_sha256)
        appraisal_source_fields = (
            self.appraisal_source_review_id,
            self.appraisal_source_sha256,
        )
        appraisal_fields = (self.appraisal_version, self.evidence_role)
        duplicate_fields = (self.canonical_screening_id, self.duplicate_relationship)
        source_is_complete = (
            sum(value is not None for value in source_ids) == 1
            and self.full_text_sha256 is not None
        )
        appraisal_source_is_complete = all(
            value is not None for value in appraisal_source_fields
        )
        if any(value is not None for value in appraisal_source_fields) and not (
            appraisal_source_is_complete
        ):
            raise ValueError(
                "appraisal source requires both review ID and checksum"
            )
        if self.status is AppraisalCompletionStatus.AWAITING_FULL_TEXT:
            if any(
                value is not None
                for value in (
                    *source_fields,
                    *appraisal_source_fields,
                    *appraisal_fields,
                    *duplicate_fields,
                    self.observed_license,
                )
            ):
                raise ValueError("awaiting-full-text record cannot contain downstream state")
        elif self.status is AppraisalCompletionStatus.ACCESS_RESTRICTED:
            if any(
                value is not None
                for value in (
                    *source_fields,
                    *appraisal_source_fields,
                    *appraisal_fields,
                    *duplicate_fields,
                )
            ):
                raise ValueError("restricted record cannot contain retrieval or appraisal state")
            if self.observed_license is None:
                raise ValueError("restricted record requires its observed license")
        elif self.status is AppraisalCompletionStatus.DUPLICATE_RESOLVED:
            if any(
                value is not None
                for value in (
                    *source_fields,
                    *appraisal_source_fields,
                    *appraisal_fields,
                    self.observed_license,
                )
            ) or any(value is None for value in duplicate_fields):
                raise ValueError(
                    "duplicate-resolved record requires only canonical relationship state"
                )
        elif self.status is AppraisalCompletionStatus.READY_FOR_APPRAISAL:
            if not source_is_complete or any(
                value is not None
                for value in (
                    *appraisal_source_fields,
                    *appraisal_fields,
                    *duplicate_fields,
                )
            ) or self.observed_license is not None:
                raise ValueError("ready record requires exactly one verified source state")
        elif (
            not source_is_complete
            or any(value is None for value in appraisal_fields)
            or self.observed_license is not None
            or any(value is not None for value in duplicate_fields)
        ):
            raise ValueError(
                "completed record requires exactly one verified source and appraisal state"
            )
        return self


class FullTextAppraisalProgress(AppraisalModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(min_length=1)
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    generated_at: datetime
    provisional_inclusion_count: int = Field(ge=1)
    full_texts_retrieved: int = Field(ge=0)
    read_only_full_texts_reviewed: int = Field(default=0, ge=0)
    appraisals_completed: int = Field(ge=0)
    access_restricted_count: int = Field(ge=0)
    duplicate_resolved_count: int = Field(ge=0)
    anchor_count: int = Field(ge=0)
    supporting_count: int = Field(ge=0)
    context_only_count: int = Field(ge=0)
    excluded_count: int = Field(ge=0)
    records: list[FullTextAppraisalProgressRecord] = Field(min_length=1)
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_progress(self) -> FullTextAppraisalProgress:
        if len(self.records) != self.provisional_inclusion_count:
            raise ValueError("appraisal-progress record count does not reconcile")
        if len({item.screening_id for item in self.records}) != len(self.records):
            raise ValueError("appraisal-progress screening IDs must be unique")
        retrieved = sum(item.retrieval_id is not None for item in self.records)
        read_only = sum(item.read_only_review_id is not None for item in self.records)
        completed = sum(
            item.status is AppraisalCompletionStatus.COMPLETED for item in self.records
        )
        if (
            retrieved != self.full_texts_retrieved
            or read_only != self.read_only_full_texts_reviewed
            or completed != self.appraisals_completed
        ):
            raise ValueError("appraisal-progress completion counts do not reconcile")
        restricted = sum(
            item.status is AppraisalCompletionStatus.ACCESS_RESTRICTED
            for item in self.records
        )
        if restricted != self.access_restricted_count:
            raise ValueError("appraisal-progress restricted count does not reconcile")
        duplicates = sum(
            item.status is AppraisalCompletionStatus.DUPLICATE_RESOLVED
            for item in self.records
        )
        if duplicates != self.duplicate_resolved_count:
            raise ValueError("appraisal-progress duplicate count does not reconcile")
        roles = {
            EvidenceRole.ANCHOR: self.anchor_count,
            EvidenceRole.SUPPORTING: self.supporting_count,
            EvidenceRole.CONTEXT_ONLY: self.context_only_count,
            EvidenceRole.EXCLUDED: self.excluded_count,
        }
        for role, expected in roles.items():
            if sum(item.evidence_role is role for item in self.records) != expected:
                raise ValueError(f"appraisal-progress {role} count does not reconcile")
        if sum(roles.values()) != self.appraisals_completed:
            raise ValueError("appraisal-progress role counts do not match completed count")
        if self.scientific_conclusions_drawn:
            raise ValueError("appraisal progress cannot draw scientific conclusions")
        return self


def load_full_text_appraisal(path: Path) -> FullTextAppraisal:
    return FullTextAppraisal.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_full_text_appraisal_proposal(path: Path) -> FullTextAppraisalProposal:
    return FullTextAppraisalProposal.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_publication_version_link_proposal(
    path: Path,
) -> PublicationVersionLinkProposal:
    return PublicationVersionLinkProposal.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_publication_version_link_decision(
    path: Path,
) -> PublicationVersionLinkDecision:
    return PublicationVersionLinkDecision.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_full_text_appraisal_batch_confirmation(
    path: Path,
) -> FullTextAppraisalBatchConfirmation:
    return FullTextAppraisalBatchConfirmation.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_full_text_inventory(path: Path) -> FullTextInventory:
    return FullTextInventory.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_full_text_appraisal_progress(
    path: Path,
) -> FullTextAppraisalProgress:
    return FullTextAppraisalProgress.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_full_text_retrieval_receipt(path: Path) -> FullTextRetrievalReceipt:
    return FullTextRetrievalReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_full_text_read_only_review_receipt(
    path: Path,
) -> FullTextReadOnlyReviewReceipt:
    return FullTextReadOnlyReviewReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_full_text_access_decision(path: Path) -> FullTextAccessDecision:
    return FullTextAccessDecision.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_full_text_duplicate_decision(path: Path) -> FullTextDuplicateDecision:
    return FullTextDuplicateDecision.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_full_text_inventory(path: Path, inventory: FullTextInventory) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        inventory.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_full_text_appraisal(path: Path, appraisal: FullTextAppraisal) -> None:
    """Write one founder-authorized appraisal without overwriting prior evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        appraisal.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_full_text_appraisal_proposal(
    path: Path, proposal: FullTextAppraisalProposal
) -> None:
    """Write one non-authoritative proposal without overwriting prior review."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        proposal.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_publication_version_link_proposal(
    path: Path, proposal: PublicationVersionLinkProposal
) -> None:
    """Write one non-authoritative publication link without overwriting review."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        proposal.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_publication_version_link_decision(
    path: Path, decision: PublicationVersionLinkDecision
) -> None:
    """Write one founder-authorized publication link without overwriting evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        decision.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_publication_version_reconciliation_receipt(
    path: Path, receipt: PublicationVersionReconciliationReceipt
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_full_text_appraisal_progress(
    path: Path, progress: FullTextAppraisalProgress
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            progress.model_dump(mode="json", exclude_none=True),
            sort_keys=False,
            width=100,
        ),
        encoding="utf-8",
    )


def write_full_text_retrieval_receipt(path: Path, receipt: FullTextRetrievalReceipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)


def write_full_text_read_only_review_receipt(
    path: Path, receipt: FullTextReadOnlyReviewReceipt
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        width=100,
    )
    with path.open("x", encoding="utf-8") as destination:
        destination.write(payload)
