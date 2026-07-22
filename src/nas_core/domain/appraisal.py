"""Typed full-text eligibility and methodological appraisal contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class FullTextAccessStatus(StrEnum):
    REPOSITORY_CANDIDATE = "repository_candidate"
    ACCESS_CHECK_REQUIRED = "access_check_required"


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


def load_full_text_appraisal(path: Path) -> FullTextAppraisal:
    return FullTextAppraisal.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
