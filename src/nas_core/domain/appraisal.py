"""Typed full-text eligibility and methodological appraisal contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.snapshots import StoredObject


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
    READY_FOR_APPRAISAL = "ready_for_appraisal"
    COMPLETED = "completed"


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
    pmcid: str = Field(pattern=r"^PMC[0-9]+$")
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
    pmcid: str = Field(pattern=r"^PMC[0-9]+$")
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


class FullTextAppraisalProgressRecord(AppraisalModel):
    screening_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    title: str = Field(min_length=1)
    pmcid: str | None = None
    status: AppraisalCompletionStatus
    retrieval_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    full_text_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    appraisal_version: str | None = Field(
        default=None, pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$"
    )
    evidence_role: EvidenceRole | None = None

    @model_validator(mode="after")
    def validate_state(self) -> FullTextAppraisalProgressRecord:
        retrieval_fields = (self.retrieval_id, self.full_text_sha256)
        appraisal_fields = (self.appraisal_version, self.evidence_role)
        if self.status is AppraisalCompletionStatus.AWAITING_FULL_TEXT:
            if any(value is not None for value in (*retrieval_fields, *appraisal_fields)):
                raise ValueError("awaiting-full-text record cannot contain downstream state")
        elif self.status is AppraisalCompletionStatus.READY_FOR_APPRAISAL:
            if any(value is None for value in retrieval_fields) or any(
                value is not None for value in appraisal_fields
            ):
                raise ValueError("ready record requires retrieval state only")
        elif any(value is None for value in (*retrieval_fields, *appraisal_fields)):
            raise ValueError("completed record requires retrieval and appraisal state")
        return self


class FullTextAppraisalProgress(AppraisalModel):
    schema_version: str = "1.0.0"
    study_id: str = Field(min_length=1)
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    generated_at: datetime
    provisional_inclusion_count: int = Field(ge=1)
    full_texts_retrieved: int = Field(ge=0)
    appraisals_completed: int = Field(ge=0)
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
        retrieved = sum(
            item.status is not AppraisalCompletionStatus.AWAITING_FULL_TEXT
            for item in self.records
        )
        completed = sum(
            item.status is AppraisalCompletionStatus.COMPLETED for item in self.records
        )
        if retrieved != self.full_texts_retrieved or completed != self.appraisals_completed:
            raise ValueError("appraisal-progress completion counts do not reconcile")
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


def load_full_text_retrieval_receipt(path: Path) -> FullTextRetrievalReceipt:
    return FullTextRetrievalReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


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
