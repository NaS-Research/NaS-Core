"""Typed contracts for bounded evidence reviews and citation-chain saturation."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nas_core.domain.citation_saturation import (
    load_citation_pass_closure_receipt,
)


class EvidenceReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETE = "complete"


class CitationPassStatus(StrEnum):
    PLANNED = "planned"
    COMPLETE = "complete"


class CandidateReviewState(StrEnum):
    PENDING_SCREENING = "pending_screening"
    PENDING_REAPPRAISAL = "pending_reappraisal"
    ELIGIBLE = "eligible"
    EXCLUDED = "excluded"
    ACCESS_RESTRICTED = "access_restricted"
    DUPLICATE = "duplicate"


class EvidenceDomain(StrEnum):
    FIXED_SINGLE_SAMPLE_CLASSIFIER = "fixed_single_sample_classifier"
    REFERENCE_AND_CENTERING = "reference_and_centering"
    GENE_MAPPING_AND_TRANSFORMATION = "gene_mapping_and_transformation"
    MARGIN_AND_UNCERTAINTY = "margin_and_uncertainty"
    TECHNICAL_MEASUREMENT_ERROR = "technical_measurement_error"
    PERTURBATION_AND_REPEATABILITY = "perturbation_and_repeatability"
    ABSTENTION_AND_UNCLASSIFIABLE = "abstention_and_unclassifiable"
    EXTERNAL_TRANSPORT = "external_transport"
    IMPLEMENTATION_AND_LICENSING = "implementation_and_licensing"


class PriorityCandidate(EvidenceReviewModel):
    candidate_id: str = Field(pattern=r"^(?:PMID|PMC|DOI):.+$")
    title: str = Field(min_length=1)
    publication_year: int = Field(ge=1990, le=2100)
    pmid: str | None = Field(default=None, pattern=r"^[0-9]+$")
    pmcid: str | None = Field(default=None, pattern=r"^PMC[0-9]+$")
    doi: str | None = Field(default=None, min_length=1)
    evidence_domains: list[EvidenceDomain] = Field(min_length=1)
    review_state: CandidateReviewState
    priority_rationale: str = Field(min_length=1)
    prior_artifact: str | None = None
    founder_decision_recorded: bool

    @model_validator(mode="after")
    def validate_identity_and_authority(self) -> PriorityCandidate:
        if not any((self.pmid, self.pmcid, self.doi)):
            raise ValueError("a priority candidate requires at least one persistent identifier")
        final_states = {
            CandidateReviewState.ELIGIBLE,
            CandidateReviewState.EXCLUDED,
            CandidateReviewState.ACCESS_RESTRICTED,
            CandidateReviewState.DUPLICATE,
        }
        if (self.review_state in final_states) != self.founder_decision_recorded:
            raise ValueError("only a founder decision may assign a final candidate state")
        if (
            self.review_state is CandidateReviewState.PENDING_REAPPRAISAL
            and not self.prior_artifact
        ):
            raise ValueError("pending reappraisal requires the prior appraisal artifact")
        return self


class PriorityEvidenceSet(EvidenceReviewModel):
    schema_version: str = "1.0.0"
    set_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    maximum_final_evidence_count: int = Field(ge=1, le=30)
    selection_rule: str = Field(min_length=1)
    candidates: list[PriorityCandidate] = Field(min_length=1, max_length=30)
    autonomous_screening_decisions_allowed: bool
    scientific_conclusions_drawn: bool

    @model_validator(mode="after")
    def validate_priority_set(self) -> PriorityEvidenceSet:
        identifiers = [item.candidate_id for item in self.candidates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("priority candidate IDs must be unique")
        if self.autonomous_screening_decisions_allowed:
            raise ValueError("AI may prioritize evidence but cannot make screening decisions")
        if self.scientific_conclusions_drawn:
            raise ValueError("a priority set cannot draw scientific conclusions")
        return self


class CitationChainPass(EvidenceReviewModel):
    pass_number: int = Field(ge=1)
    status: CitationPassStatus
    seed_evidence_ids: list[str] = Field(min_length=1)
    backward_source: str = Field(pattern=r"^europe_pmc_references$")
    forward_source: str = Field(pattern=r"^europe_pmc_citations$")
    backward_candidate_count: int = Field(ge=0)
    forward_candidate_count: int = Field(ge=0)
    unique_candidate_count: int = Field(ge=0)
    screened_candidate_count: int = Field(ge=0)
    new_eligible_evidence_ids: list[str]
    completed_at: datetime | None = None
    closure_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    closure_receipt_path: str | None = None

    @model_validator(mode="after")
    def validate_pass(self) -> CitationChainPass:
        if len(self.seed_evidence_ids) != len(set(self.seed_evidence_ids)):
            raise ValueError("citation-pass seed IDs must be unique")
        if len(self.new_eligible_evidence_ids) != len(set(self.new_eligible_evidence_ids)):
            raise ValueError("new eligible evidence IDs must be unique")
        if self.unique_candidate_count > (
            self.backward_candidate_count + self.forward_candidate_count
        ):
            raise ValueError("unique citation candidates cannot exceed directional candidates")
        if self.status is CitationPassStatus.PLANNED:
            if any(
                (
                    self.backward_candidate_count,
                    self.forward_candidate_count,
                    self.unique_candidate_count,
                    self.screened_candidate_count,
                )
            ):
                raise ValueError("a planned citation pass cannot claim candidate counts")
            if (
                self.new_eligible_evidence_ids
                or self.completed_at is not None
                or self.closure_id is not None
                or self.closure_receipt_path is not None
            ):
                raise ValueError("a planned citation pass cannot claim results")
            return self
        if self.screened_candidate_count != self.unique_candidate_count:
            raise ValueError("a complete citation pass must screen every unique candidate")
        if self.completed_at is None:
            raise ValueError("a complete citation pass requires a completion timestamp")
        if self.closure_id is None or self.closure_receipt_path is None:
            raise ValueError("a complete citation pass requires its closure receipt")
        return self


class EvidenceReviewProgress(EvidenceReviewModel):
    schema_version: str = "1.0.0"
    progress_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    protocol_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    review_status: ReviewStatus
    search_strategy_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    priority_set_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    locked_search_executed: bool
    search_execution_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    search_receipt_path: str | None = None
    screening_queue_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    screening_queue_receipt_path: str | None = None
    inventory_reconciliation_id: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    inventory_reconciliation_receipt_path: str | None = None
    deduplication_complete: bool
    screening_progress_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    screening_progress_receipt_path: str | None = None
    primary_screening_complete: bool
    eligible_evidence_count: int = Field(ge=0)
    completed_appraisal_count: int = Field(ge=0)
    access_restricted_count: int = Field(ge=0)
    pending_candidate_count: int = Field(ge=0)
    uncapped_saturation_inventory_active: bool
    core_synthesis_maximum: int = Field(ge=1, le=30)
    amendment_activation_id: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    amendment_activation_receipt_path: str | None = None
    citation_passes: list[CitationChainPass]
    unresolved_claims: list[str] = Field(min_length=1)
    stopping_rule_satisfied: bool
    novelty_claim_authorized: bool
    molecular_data_access_authorized: bool
    outcome_data_access_authorized: bool

    @model_validator(mode="after")
    def validate_progress_and_stopping_rule(self) -> EvidenceReviewProgress:
        pass_numbers = [item.pass_number for item in self.citation_passes]
        if pass_numbers != list(range(1, len(pass_numbers) + 1)):
            raise ValueError("citation passes must be sequential and start at one")
        if len(pass_numbers) != len(set(pass_numbers)):
            raise ValueError("citation-pass numbers must be unique")
        if self.completed_appraisal_count > self.eligible_evidence_count:
            raise ValueError("completed appraisals cannot exceed eligible evidence")
        amendment_bound = (
            self.amendment_activation_id is not None
            and self.amendment_activation_receipt_path is not None
        )
        if self.uncapped_saturation_inventory_active != amendment_bound:
            raise ValueError(
                "uncapped saturation inventory requires an amendment activation receipt"
            )
        if self.uncapped_saturation_inventory_active and self.protocol_version != "0.2.5":
            raise ValueError("active evidence-cap amendment requires protocol 0.2.5")
        if self.locked_search_executed != (
            self.search_execution_id is not None and self.search_receipt_path is not None
        ):
            raise ValueError(
                "search execution state requires both an execution ID and receipt path"
            )
        reconciliation_bound = all(
            (
                self.screening_queue_id is not None,
                self.screening_queue_receipt_path is not None,
                self.inventory_reconciliation_id is not None,
                self.inventory_reconciliation_receipt_path is not None,
            )
        )
        if self.deduplication_complete != reconciliation_bound:
            raise ValueError(
                "deduplication state requires a queue and inventory-reconciliation receipt"
            )
        if (self.screening_progress_id is None) != (
            self.screening_progress_receipt_path is None
        ):
            raise ValueError(
                "screening progress requires both a progress ID and receipt path"
            )
        if self.novelty_claim_authorized and not self.stopping_rule_satisfied:
            raise ValueError("novelty cannot be authorized before the stopping rule is satisfied")
        if self.molecular_data_access_authorized or self.outcome_data_access_authorized:
            raise ValueError("an evidence review cannot authorize molecular or outcome access")

        completed = [
            item for item in self.citation_passes if item.status is CitationPassStatus.COMPLETE
        ]
        last_two_are_zero = (
            len(completed) >= 2
            and completed[-2].pass_number + 1 == completed[-1].pass_number
            and not completed[-2].new_eligible_evidence_ids
            and not completed[-1].new_eligible_evidence_ids
        )
        prerequisites = (
            self.locked_search_executed
            and self.deduplication_complete
            and self.primary_screening_complete
            and self.pending_candidate_count == 0
            and self.completed_appraisal_count + self.access_restricted_count
            == self.eligible_evidence_count
            and len(completed) == len(self.citation_passes)
            and last_two_are_zero
        )
        if self.stopping_rule_satisfied != prerequisites:
            raise ValueError("stopping-rule claim does not match the audited review state")
        if (self.review_status is ReviewStatus.COMPLETE) != self.stopping_rule_satisfied:
            raise ValueError("only a stopping-rule-satisfied review may be complete")
        return self


def load_priority_evidence_set(path: Path) -> PriorityEvidenceSet:
    return PriorityEvidenceSet.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_evidence_review_progress(path: Path) -> EvidenceReviewProgress:
    progress = EvidenceReviewProgress.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
    for citation_pass in progress.citation_passes:
        if citation_pass.status is not CitationPassStatus.COMPLETE:
            continue
        assert citation_pass.closure_receipt_path is not None
        closure_path = Path(citation_pass.closure_receipt_path)
        if not closure_path.is_absolute():
            candidates = (
                path.parent / closure_path,
                path.parent.parent / closure_path,
            )
            closure_path = next(
                (candidate for candidate in candidates if candidate.is_file()),
                candidates[-1],
            )
        closure = load_citation_pass_closure_receipt(closure_path)
        expected = (
            closure.study_id,
            closure.pass_number,
            closure.seed_evidence_ids,
            closure.backward_candidate_count,
            closure.forward_candidate_count,
            closure.unique_candidate_count,
            closure.unique_candidate_count,
            closure.new_eligible_evidence_ids,
            closure.closed_at,
            closure.closure_id,
        )
        observed = (
            progress.study_id,
            citation_pass.pass_number,
            citation_pass.seed_evidence_ids,
            citation_pass.backward_candidate_count,
            citation_pass.forward_candidate_count,
            citation_pass.unique_candidate_count,
            citation_pass.screened_candidate_count,
            citation_pass.new_eligible_evidence_ids,
            citation_pass.completed_at,
            citation_pass.closure_id,
        )
        if observed != expected:
            raise ValueError(
                f"citation pass {citation_pass.pass_number} does not match its closure"
            )
    return progress


def write_evidence_review_schemas(priority_path: Path, progress_path: Path) -> None:
    for path, model in (
        (priority_path, PriorityEvidenceSet),
        (progress_path, EvidenceReviewProgress),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        path.write_text(f"{payload}\n", encoding="utf-8")
