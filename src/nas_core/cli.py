import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from nas_core.ai.gateway import OpenAIScreeningGateway
from nas_core.ai.screening import AIAdvisoryScreeningService
from nas_core.analysis.cohort import CohortBuildService
from nas_core.analysis.survival import SurvivalAnalysisService
from nas_core.config import get_settings
from nas_core.domain.advisory import (
    load_ai_advisory_policy,
    write_ai_advisory_receipt,
    write_ai_advisory_schemas,
)
from nas_core.domain.appraisal import (
    FullTextLicense,
    load_full_text_access_decision,
    load_full_text_appraisal,
    load_full_text_appraisal_batch_confirmation,
    load_full_text_appraisal_proposal,
    load_full_text_inventory,
    load_full_text_read_only_review_receipt,
    write_full_text_appraisal,
    write_full_text_appraisal_progress,
    write_full_text_appraisal_proposal,
    write_full_text_inventory,
    write_full_text_read_only_review_receipt,
    write_full_text_retrieval_receipt,
)
from nas_core.domain.citation_access import (
    load_repository_access_batch_receipt,
    write_citation_access_check_queue,
    write_repository_access_batch_receipt,
)
from nas_core.domain.citation_chain import (
    CitationSeed,
    load_citation_chain_receipt,
    load_citation_enrichment_receipt,
    load_citation_founder_packet_receipt,
    load_citation_prioritization_receipt,
    load_citation_recommendation_receipt,
    load_citation_screening_preparation_receipt,
    write_citation_chain_receipt,
    write_citation_enrichment_receipt,
    write_citation_founder_packet_receipt,
    write_citation_prioritization_receipt,
    write_citation_recommendation_receipt,
    write_citation_screening_preparation_receipt,
)
from nas_core.domain.citation_confirmation import (
    load_citation_decision_ledger_receipt,
    load_citation_founder_confirmation,
    write_citation_decision_ledger_receipt,
)
from nas_core.domain.citation_reconciliation import (
    load_citation_inclusion_reconciliation_receipt,
    write_citation_inclusion_reconciliation_receipt,
)
from nas_core.domain.cohorts import (
    load_cohort_receipt,
    load_snapshot_receipt,
    write_cohort_schemas,
)
from nas_core.domain.discovery import load_phase_zero_artifacts, write_discovery_schemas
from nas_core.domain.evidence_amendment import (
    load_evidence_cap_amendment_activation_receipt,
    load_evidence_cap_amendment_approval,
    write_evidence_cap_amendment_activation_receipt,
)
from nas_core.domain.evidence_review import (
    load_evidence_review_progress,
    load_priority_evidence_set,
    write_evidence_review_schemas,
)
from nas_core.domain.literature import (
    load_literature_search_receipt,
    load_screening_decision_batch,
    load_screening_progress_receipt,
    load_screening_queue_receipt,
    write_inventory_reconciliation_receipt,
    write_inventory_reconciliation_schema,
    write_literature_schemas,
    write_literature_search_receipt,
    write_screening_decision_batch,
    write_screening_progress_receipt,
    write_screening_queue_receipt,
    write_screening_review_schemas,
)
from nas_core.domain.programs import OncologyProgramCharter, ResearchQuestionIntake, StudyRole
from nas_core.domain.reliability import (
    load_reliability_specification,
    write_reliability_schema,
)
from nas_core.domain.screening_confirmation import load_screening_confirmation
from nas_core.domain.snapshots import write_dataset_snapshot_schema
from nas_core.domain.survival import write_survival_schemas
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import GDCSnapshotService, build_case_query
from nas_core.retrieval.appraisal_confirmation import AppraisalConfirmationService
from nas_core.retrieval.appraisal_progress import FullTextAppraisalProgressService
from nas_core.retrieval.citation_access import (
    CitationAccessCheckQueueService,
    CitationRepositoryAccessService,
)
from nas_core.retrieval.citation_adjudication import (
    CitationUnclearAdjudicationService,
    load_citation_adjudication_policy,
)
from nas_core.retrieval.citation_chain import CitationChainRetrievalService
from nas_core.retrieval.citation_confirmation import CitationDecisionConfirmationService
from nas_core.retrieval.citation_enrichment import CitationEnrichmentService
from nas_core.retrieval.citation_packet import CitationFounderPacketService
from nas_core.retrieval.citation_prioritization import CitationPrioritizationService
from nas_core.retrieval.citation_recommendation import CitationRecommendationService
from nas_core.retrieval.citation_reconciliation import (
    CitationInclusionReconciliationService,
)
from nas_core.retrieval.citation_screening import CitationScreeningPreparationService
from nas_core.retrieval.ephemeral_appraisal import (
    ApprovedPublisherPdfAppraisalProposalService,
    InstitutionalPdfAppraisalProposalService,
)
from nas_core.retrieval.evidence_amendment import (
    CitationAccessInventoryService,
    EvidenceCapAmendmentActivationService,
)
from nas_core.retrieval.full_text import FullTextInventoryService
from nas_core.retrieval.full_text_retrieval import FullTextRetrievalService
from nas_core.retrieval.licensed_pdf import LicensedPdfImportService
from nas_core.retrieval.literature import (
    LiteratureSearchService,
    LiteratureSearchVerificationService,
)
from nas_core.retrieval.prioritization import DeterministicPrioritizationService
from nas_core.retrieval.read_only_review import (
    ApprovedPublisherPdfReadOnlyReviewService,
    InstitutionalPdfReadOnlyReviewService,
    MedrxivReadOnlyReviewService,
    PmcReadOnlyReviewService,
)
from nas_core.retrieval.reconciliation import InventoryReconciliationService
from nas_core.retrieval.review import ScreeningReviewService
from nas_core.retrieval.screening import ScreeningQueueService
from nas_core.retrieval.screening_confirmation import ScreeningConfirmationService
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import get_object_store
from nas_core.workflows.analysis_plan import load_analysis_plan, write_analysis_plan_schema
from nas_core.workflows.program import (
    load_program_charter,
    load_research_question,
    write_model_schema,
)
from nas_core.workflows.study_scaffold import (
    initialize_study,
    load_study_manifests,
    write_study_schemas,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nas-core")
    commands = parser.add_subparsers(dest="command", required=True)

    storage = commands.add_parser("storage", help="Manage the NaS Core data root")
    storage_commands = storage.add_subparsers(dest="storage_command", required=True)
    storage_commands.add_parser("init", help="Create and validate the data-root layout")
    storage_commands.add_parser("check", help="Validate the existing data-root layout")

    plan = commands.add_parser("plan", help="Manage versioned research analysis plans")
    plan_commands = plan.add_subparsers(dest="plan_command", required=True)
    validate = plan_commands.add_parser("validate", help="Validate a plan and its governance")
    validate.add_argument("path", type=Path, help="Path to analysis_plan.yaml")
    validate.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    schema = plan_commands.add_parser("schema", help="Write the canonical plan JSON Schema")
    schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    ingest = commands.add_parser("ingest", help="Create governed dataset snapshots")
    ingest_commands = ingest.add_subparsers(dest="ingest_command", required=True)
    gdc = ingest_commands.add_parser("gdc-plan", help="Prepare or execute a GDC plan")
    gdc.add_argument("path", type=Path, help="Path to analysis_plan.yaml")
    gdc.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    gdc.add_argument("--data-release", help="Exact GDC data release, for example 45.0")
    gdc.add_argument(
        "--release-notes-url",
        help="Official GDC release-notes URL that identifies the declared Data Release",
    )
    gdc.add_argument(
        "--execute",
        action="store_true",
        help="Fetch and persist data; requires a preregistered plan",
    )
    snapshot_schema = ingest_commands.add_parser(
        "schema", help="Write the canonical dataset-snapshot JSON Schema"
    )
    snapshot_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    cohort = commands.add_parser("cohort", help="Build governed analysis-ready cohorts")
    cohort_commands = cohort.add_subparsers(dest="cohort_command", required=True)
    cohort_build = cohort_commands.add_parser("build", help="Prepare or execute cohort build")
    cohort_build.add_argument("plan", type=Path, help="Path to analysis_plan.yaml")
    cohort_build.add_argument("receipt", type=Path, help="Path to snapshot_receipt.yaml")
    cohort_build.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    cohort_build.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    cohort_build.add_argument(
        "--execute",
        action="store_true",
        help="Read the frozen snapshot and persist cohort artifacts",
    )
    cohort_schema = cohort_commands.add_parser("schema", help="Write cohort JSON Schemas")
    cohort_schema.add_argument("qa_path", type=Path, help="Output path for QA schema")
    cohort_schema.add_argument("manifest_path", type=Path, help="Output path for manifest schema")
    cohort_schema.add_argument("receipt_path", type=Path, help="Output path for receipt schema")

    analysis = commands.add_parser("analysis", help="Run governed statistical analyses")
    analysis_commands = analysis.add_subparsers(dest="analysis_command", required=True)
    survival = analysis_commands.add_parser("survival", help="Prepare or execute survival models")
    survival.add_argument("plan", type=Path, help="Path to analysis_plan.yaml")
    survival.add_argument("receipt", type=Path, help="Path to cohort_build_receipt.yaml")
    survival.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    survival.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    survival.add_argument(
        "--execute",
        action="store_true",
        help="Read the approved cohort and persist statistical artifacts",
    )
    survival_schema = analysis_commands.add_parser(
        "schema", help="Write survival result JSON Schemas"
    )
    survival_schema.add_argument("summary_path", type=Path, help="Output path for result schema")
    survival_schema.add_argument("manifest_path", type=Path, help="Output path for run schema")
    survival_schema.add_argument("receipt_path", type=Path, help="Output path for receipt schema")

    discovery = commands.add_parser("discovery", help="Manage discovery-study Phase 0 audits")
    discovery_commands = discovery.add_subparsers(dest="discovery_command", required=True)
    discovery_validate = discovery_commands.add_parser(
        "validate", help="Validate a Phase 0 novelty and feasibility package"
    )
    discovery_validate.add_argument("plan", type=Path, help="Path to phase_zero_plan.yaml")
    discovery_validate.add_argument("search", type=Path, help="Path to search_strategy.yaml")
    discovery_validate.add_argument("feasibility", type=Path, help="Path to data_feasibility.yaml")
    discovery_schema = discovery_commands.add_parser(
        "schema", help="Write Phase 0 discovery JSON Schemas"
    )
    discovery_schema.add_argument("plan_path", type=Path, help="Output path for plan schema")
    discovery_schema.add_argument("search_path", type=Path, help="Output path for search schema")
    discovery_schema.add_argument(
        "feasibility_path", type=Path, help="Output path for feasibility schema"
    )

    reliability = commands.add_parser(
        "reliability", help="Manage single-sample classifier reliability specifications"
    )
    reliability_commands = reliability.add_subparsers(
        dest="reliability_command", required=True
    )
    reliability_validate = reliability_commands.add_parser(
        "validate", help="Validate a governed reliability specification"
    )
    reliability_validate.add_argument(
        "path", type=Path, help="Path to reliability_specification.yaml"
    )
    reliability_schema = reliability_commands.add_parser(
        "schema", help="Write the canonical reliability JSON Schema"
    )
    reliability_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    evidence_review = commands.add_parser(
        "evidence-review", help="Manage bounded evidence reviews and citation-chain saturation"
    )
    evidence_review_commands = evidence_review.add_subparsers(
        dest="evidence_review_command", required=True
    )
    evidence_review_validate = evidence_review_commands.add_parser(
        "validate", help="Validate priority evidence and review-progress artifacts"
    )
    evidence_review_validate.add_argument("priority_path", type=Path)
    evidence_review_validate.add_argument("progress_path", type=Path)
    evidence_review_schema = evidence_review_commands.add_parser(
        "schema", help="Write evidence-review JSON Schemas"
    )
    evidence_review_schema.add_argument("priority_path", type=Path)
    evidence_review_schema.add_argument("progress_path", type=Path)
    citation_retrieve = evidence_review_commands.add_parser(
        "citation-retrieve",
        help="Retrieve and verify one backward-plus-forward Europe PMC citation pass",
    )
    citation_retrieve.add_argument("inventory_path", type=Path)
    citation_retrieve.add_argument("--pass-number", required=True, type=int)
    citation_retrieve.add_argument("--code-revision", required=True)
    citation_retrieve.add_argument("--receipt-output", required=True, type=Path)
    citation_retrieve.add_argument(
        "--execute", action="store_true", help="Contact Europe PMC and persist the pass"
    )
    citation_prepare = evidence_review_commands.add_parser(
        "citation-screening-prepare",
        help="Deduplicate a verified citation pass before founder screening",
    )
    citation_prepare.add_argument("citation_receipt", type=Path)
    citation_prepare.add_argument("prior_search_receipt", type=Path)
    citation_prepare.add_argument("--code-revision", required=True)
    citation_prepare.add_argument("--receipt-output", required=True, type=Path)
    citation_prepare.add_argument(
        "--execute",
        action="store_true",
        help="Persist the verified deduplication inventory and screening candidate set",
    )
    citation_prioritize = evidence_review_commands.add_parser(
        "citation-prioritize",
        help="Rank every unscreened citation candidate using transparent title signals",
    )
    citation_prioritize.add_argument("preparation_receipt", type=Path)
    citation_prioritize.add_argument("--code-revision", required=True)
    citation_prioritize.add_argument("--receipt-output", required=True, type=Path)
    citation_prioritize.add_argument(
        "--execute",
        action="store_true",
        help="Persist the complete advisory ranking without screening decisions",
    )
    citation_enrich = evidence_review_commands.add_parser(
        "citation-enrich",
        help="Retrieve Europe PMC abstracts for direct and supporting citation candidates",
    )
    citation_enrich.add_argument("prioritization_receipt", type=Path)
    citation_enrich.add_argument("--code-revision", required=True)
    citation_enrich.add_argument("--receipt-output", required=True, type=Path)
    citation_enrich.add_argument(
        "--include-context",
        action="store_true",
        help="Enrich every retained candidate, including the title-only context tier",
    )
    citation_enrich.add_argument(
        "--execute",
        action="store_true",
        help="Contact Europe PMC and persist verified enrichment artifacts",
    )
    citation_recommend = evidence_review_commands.add_parser(
        "citation-recommend",
        help="Create conservative abstract-informed advisory screening recommendations",
    )
    citation_recommend.add_argument("enrichment_receipt", type=Path)
    citation_recommend.add_argument("--code-revision", required=True)
    citation_recommend.add_argument("--receipt-output", required=True, type=Path)
    citation_recommend.add_argument(
        "--execute",
        action="store_true",
        help="Persist recommendations covering every enriched citation candidate",
    )
    citation_packet = evidence_review_commands.add_parser(
        "citation-packet",
        help="Freeze a checksum-bound founder packet and complete row-level appendix",
    )
    citation_packet.add_argument("recommendation_receipt", type=Path)
    citation_packet.add_argument("--packet-output", required=True, type=Path)
    citation_packet.add_argument("--appendix-output", required=True, type=Path)
    citation_packet.add_argument("--receipt-output", required=True, type=Path)
    citation_adjudicate = evidence_review_commands.add_parser(
        "citation-adjudicate",
        help="Apply a versioned advisory policy to unresolved citation records",
    )
    citation_adjudicate.add_argument("recommendation_receipt", type=Path)
    citation_adjudicate.add_argument("enrichment_receipt", type=Path)
    citation_adjudicate.add_argument("policy", type=Path)
    citation_adjudicate.add_argument("--code-revision", required=True)
    citation_adjudicate.add_argument("--receipt-output", required=True, type=Path)
    citation_adjudicate.add_argument(
        "--execute",
        action="store_true",
        help="Persist complete second-stage advisory recommendations",
    )
    citation_confirm = evidence_review_commands.add_parser(
        "citation-confirm",
        help="Verify founder authority and freeze the complete citation decision ledger",
    )
    citation_confirm.add_argument("first_packet_receipt", type=Path)
    citation_confirm.add_argument("first_packet", type=Path)
    citation_confirm.add_argument("first_appendix", type=Path)
    citation_confirm.add_argument("second_packet_receipt", type=Path)
    citation_confirm.add_argument("second_packet", type=Path)
    citation_confirm.add_argument("second_appendix", type=Path)
    citation_confirm.add_argument("confirmation", type=Path)
    citation_confirm.add_argument("--code-revision", required=True)
    citation_confirm.add_argument("--receipt-output", required=True, type=Path)
    citation_confirm.add_argument(
        "--execute",
        action="store_true",
        help="Persist final founder decisions after exact confirmation",
    )
    citation_reconcile = evidence_review_commands.add_parser(
        "citation-reconcile",
        help="Reconcile confirmed inclusions against inventory and prior appraisals",
    )
    citation_reconcile.add_argument("decision_receipt", type=Path)
    citation_reconcile.add_argument("inventory", type=Path)
    citation_reconcile.add_argument(
        "--appraisal-dir",
        required=True,
        action="append",
        type=Path,
        help="Directory containing prior full-text appraisal YAML files; repeatable",
    )
    citation_reconcile.add_argument("--code-revision", required=True)
    citation_reconcile.add_argument("--receipt-output", required=True, type=Path)
    citation_reconcile.add_argument(
        "--execute",
        action="store_true",
        help="Persist the checksum-verified inclusion reconciliation",
    )
    activate_cap = evidence_review_commands.add_parser(
        "activate-cap-amendment",
        help="Activate a checksum-bound founder-approved evidence-cap amendment",
    )
    activate_cap.add_argument("approval", type=Path)
    activate_cap.add_argument("amendment", type=Path)
    activate_cap.add_argument("reconciliation_receipt", type=Path)
    activate_cap.add_argument("--code-revision", required=True)
    activate_cap.add_argument("--receipt-output", required=True, type=Path)
    activate_cap.add_argument(
        "--execute",
        action="store_true",
        help="Persist the governed citation appraisal queue and activation receipt",
    )

    literature = commands.add_parser("literature", help="Capture governed evidence searches")
    literature_commands = literature.add_subparsers(dest="literature_command", required=True)
    literature_search = literature_commands.add_parser(
        "search", help="Prepare or execute a locked bibliographic search"
    )
    literature_search.add_argument("plan", type=Path, help="Path to phase_zero_plan.yaml")
    literature_search.add_argument("search", type=Path, help="Path to search_strategy.yaml")
    literature_search.add_argument("feasibility", type=Path, help="Path to data_feasibility.yaml")
    literature_search.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    literature_search.add_argument(
        "--contact-email", help="Valid API contact email; hashed in the manifest"
    )
    literature_search.add_argument(
        "--execute", action="store_true", help="Contact APIs and persist immutable search exports"
    )
    literature_search.add_argument(
        "--count-only",
        action="store_true",
        help="Contact each API once for result counts without storing records",
    )
    literature_schema = literature_commands.add_parser(
        "schema", help="Write the literature-search snapshot JSON Schema"
    )
    literature_schema.add_argument("snapshot_path", type=Path, help="Snapshot schema output path")
    literature_schema.add_argument("receipt_path", type=Path, help="Receipt schema output path")
    literature_schema.add_argument(
        "screening_manifest_path", type=Path, help="Screening manifest schema output path"
    )
    literature_schema.add_argument(
        "screening_receipt_path", type=Path, help="Screening receipt schema output path"
    )
    literature_verify = literature_commands.add_parser(
        "search-verify", help="Verify a stored search and write a minimal receipt"
    )
    literature_verify.add_argument("study_id")
    literature_verify.add_argument("execution_id")
    literature_verify.add_argument("output_path", type=Path)
    screening_build = literature_commands.add_parser(
        "screening-build", help="Prepare or create an immutable human screening queue"
    )
    screening_build.add_argument("receipt", type=Path, help="Verified search_receipt.yaml")
    screening_build.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    screening_build.add_argument(
        "--execute", action="store_true", help="Read verified records and persist the queue"
    )
    screening_verify = literature_commands.add_parser(
        "screening-verify", help="Independently verify a stored screening queue"
    )
    screening_verify.add_argument("study_id")
    screening_verify.add_argument("search_execution_id")
    screening_verify.add_argument("queue_id")
    screening_verify.add_argument("output_path", type=Path)
    screening_reconcile = literature_commands.add_parser(
        "screening-reconcile",
        help="Reconcile a revised queue against a prior inventory without carrying decisions",
    )
    screening_reconcile.add_argument("current_receipt", type=Path)
    screening_reconcile.add_argument("prior_receipt", type=Path)
    screening_reconcile.add_argument("--code-revision", required=True)
    screening_reconcile.add_argument("--receipt-output", type=Path)
    screening_reconcile.add_argument("--execute", action="store_true")
    reconciliation_schema = literature_commands.add_parser(
        "screening-reconciliation-schema",
        help="Write the inventory-reconciliation receipt JSON Schema",
    )
    reconciliation_schema.add_argument("output_path", type=Path)
    screening_next = literature_commands.add_parser(
        "screening-next", help="Display the next resumable founder-review batch"
    )
    screening_next.add_argument("receipt", type=Path, help="Verified screening_queue_receipt.yaml")
    screening_next.add_argument(
        "--progress-receipt", type=Path, help="Latest verified screening progress receipt"
    )
    screening_next.add_argument("--batch-size", type=int, default=20, help="Records to display")
    screening_next.add_argument(
        "--include-unclear",
        action="store_true",
        help="Include records whose latest decision is unclear for adjudication",
    )
    screening_prioritize = literature_commands.add_parser(
        "screening-prioritize",
        help="Rank pending records with transparent zero-cost rules",
    )
    screening_prioritize.add_argument(
        "receipt", type=Path, help="Verified screening_queue_receipt.yaml"
    )
    screening_prioritize.add_argument(
        "--progress-receipt", type=Path, help="Latest verified screening progress receipt"
    )
    screening_prioritize.add_argument(
        "--limit", type=int, default=30, help="Highest-priority records to display"
    )
    screening_record = literature_commands.add_parser(
        "screening-record", help="Record and verify one immutable founder-review batch"
    )
    screening_record.add_argument(
        "receipt", type=Path, help="Verified screening_queue_receipt.yaml"
    )
    screening_record.add_argument(
        "decisions", type=Path, help="Typed screening decision batch YAML"
    )
    screening_record.add_argument(
        "--previous-progress-receipt", type=Path, help="Latest verified progress receipt"
    )
    screening_record.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    screening_record.add_argument(
        "--receipt-output", type=Path, help="New path for the verified aggregate progress receipt"
    )
    screening_record.add_argument(
        "--execute", action="store_true", help="Persist decision events and verify progress"
    )
    screening_confirm = literature_commands.add_parser(
        "screening-confirm",
        help="Build a founder decision batch from an exact checksum-bound review packet",
    )
    screening_confirm.add_argument(
        "receipt", type=Path, help="Verified screening_queue_receipt.yaml"
    )
    screening_confirm.add_argument(
        "progress_receipt", type=Path, help="Latest verified screening progress receipt"
    )
    screening_confirm.add_argument("packet", type=Path, help="Founder review packet Markdown")
    screening_confirm.add_argument(
        "confirmation", type=Path, help="Explicit founder confirmation YAML"
    )
    screening_confirm.add_argument("output_path", type=Path, help="New decision-batch YAML")
    screening_confirm_preview = literature_commands.add_parser(
        "screening-confirm-preview",
        help="Verify a review packet against immutable pending records without authorizing it",
    )
    screening_confirm_preview.add_argument(
        "receipt", type=Path, help="Verified screening_queue_receipt.yaml"
    )
    screening_confirm_preview.add_argument(
        "progress_receipt", type=Path, help="Latest verified screening progress receipt"
    )
    screening_confirm_preview.add_argument(
        "packet", type=Path, help="Founder review packet Markdown"
    )
    screening_review_schema = literature_commands.add_parser(
        "screening-review-schema", help="Write founder-review JSON Schemas"
    )
    screening_review_schema.add_argument(
        "decision_batch_path", type=Path, help="Decision-batch schema output path"
    )
    screening_review_schema.add_argument(
        "progress_manifest_path", type=Path, help="Progress-manifest schema output path"
    )
    screening_review_schema.add_argument(
        "progress_receipt_path", type=Path, help="Progress-receipt schema output path"
    )
    screening_ai = literature_commands.add_parser(
        "screening-ai", help="Run governed AI advisory screening without final decisions"
    )
    screening_ai.add_argument("receipt", type=Path, help="Verified screening queue receipt")
    screening_ai.add_argument("policy", type=Path, help="Locked AI screening policy YAML")
    screening_ai.add_argument(
        "--progress-receipt", type=Path, help="Latest verified founder progress receipt"
    )
    screening_ai.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    screening_ai.add_argument(
        "--receipt-output", type=Path, help="New path for the aggregate AI advisory receipt"
    )
    screening_ai.add_argument(
        "--execute", action="store_true", help="Send pending records to the configured provider"
    )
    screening_ai_schema = literature_commands.add_parser(
        "screening-ai-schema", help="Write AI advisory screening JSON Schemas"
    )
    screening_ai_schema.add_argument("output_path", type=Path)
    screening_ai_schema.add_argument("manifest_path", type=Path)
    screening_ai_schema.add_argument("receipt_path", type=Path)
    appraisal_validate = literature_commands.add_parser(
        "appraisal-validate",
        help="Validate one full-text eligibility and quality appraisal",
    )
    appraisal_validate.add_argument("path", type=Path, help="Full-text appraisal YAML")
    read_only_validate = literature_commands.add_parser(
        "read-only-receipt-validate",
        help="Validate a governed ephemeral full-text review receipt",
    )
    read_only_validate.add_argument("path", type=Path, help="Read-only review receipt YAML")
    appraisal_progress = literature_commands.add_parser(
        "appraisal-progress",
        help="Reconcile founder inclusions, verified full texts, and completed appraisals",
    )
    appraisal_progress.add_argument("receipt", type=Path, help="Screening queue receipt")
    appraisal_progress.add_argument(
        "progress_receipt", type=Path, help="Latest founder progress receipt"
    )
    appraisal_progress.add_argument(
        "full_text_receipt_dir", type=Path, help="Directory of verified full-text receipts"
    )
    appraisal_progress.add_argument(
        "appraisal_dir", type=Path, help="Directory of completed appraisal YAML files"
    )
    appraisal_progress.add_argument("output_path", type=Path)
    full_text_inventory = literature_commands.add_parser(
        "full-text-inventory",
        help="Build a verified access inventory from founder-included records",
    )
    full_text_inventory.add_argument(
        "receipt", type=Path, help="Verified screening queue receipt"
    )
    full_text_inventory.add_argument(
        "progress_receipt", type=Path, help="Latest verified founder progress receipt"
    )
    full_text_inventory.add_argument(
        "--output-path",
        type=Path,
        help="New path for the typed access inventory YAML",
    )
    citation_access_inventory = literature_commands.add_parser(
        "citation-access-inventory",
        help="Build the net-new access inventory from an activated citation queue",
    )
    citation_access_inventory.add_argument("activation_receipt", type=Path)
    citation_access_inventory.add_argument("--output-path", required=True, type=Path)
    citation_full_text_batch = literature_commands.add_parser(
        "citation-full-text-batch",
        help="Retrieve licensed repository candidates and account for every failure",
    )
    citation_full_text_batch.add_argument("inventory", type=Path)
    citation_full_text_batch.add_argument("--code-revision", required=True)
    citation_full_text_batch.add_argument("--receipt-dir", required=True, type=Path)
    citation_full_text_batch.add_argument(
        "--batch-receipt-output", required=True, type=Path
    )
    citation_full_text_batch.add_argument(
        "--execute",
        action="store_true",
        help="Contact Europe PMC and store only identity-verified CC BY full texts",
    )
    citation_access_checks = literature_commands.add_parser(
        "citation-access-check-queue",
        help="Combine non-repository records and repository failures for access review",
    )
    citation_access_checks.add_argument("inventory", type=Path)
    citation_access_checks.add_argument("repository_batch", type=Path)
    citation_access_checks.add_argument("--code-revision", required=True)
    citation_access_checks.add_argument("--output-path", required=True, type=Path)
    citation_appraisal_progress = literature_commands.add_parser(
        "citation-appraisal-progress",
        help="Reconcile citation access inventory, retrievals, and appraisals",
    )
    citation_appraisal_progress.add_argument("inventory", type=Path)
    citation_appraisal_progress.add_argument("retrieval_dir", type=Path)
    citation_appraisal_progress.add_argument("appraisal_dir", type=Path)
    citation_appraisal_progress.add_argument(
        "--read-only-receipt-dir",
        type=Path,
        help="Directory containing governed ephemeral-review receipts",
    )
    citation_appraisal_progress.add_argument(
        "--access-decision-dir",
        type=Path,
        help="Directory containing final restricted-access decisions",
    )
    citation_appraisal_progress.add_argument(
        "--duplicate-decision-dir",
        type=Path,
        help="Directory containing founder-authorized duplicate decisions",
    )
    citation_appraisal_progress.add_argument("--output-path", required=True, type=Path)
    citation_appraisal_authorize = literature_commands.add_parser(
        "citation-appraisal-authorize",
        help="Derive locked appraisals from one exact founder-confirmed batch",
    )
    citation_appraisal_authorize.add_argument("confirmation", type=Path)
    citation_appraisal_authorize.add_argument("packet", type=Path)
    citation_appraisal_authorize.add_argument("proposal_dir", type=Path)
    citation_appraisal_authorize.add_argument("output_dir", type=Path)
    citation_read_only_review = literature_commands.add_parser(
        "citation-pmc-read-only-review",
        help="Review a PMC article ephemerally and emit a no-storage receipt",
    )
    citation_read_only_review.add_argument("inventory", type=Path)
    citation_read_only_review.add_argument("screening_id")
    citation_read_only_review.add_argument("--code-revision", required=True)
    citation_read_only_review.add_argument("--access-basis", required=True)
    citation_read_only_review.add_argument("--observed-rights", required=True)
    citation_read_only_review.add_argument("--rights-url", required=True)
    citation_read_only_review.add_argument(
        "--receipt-output", required=True, type=Path
    )
    citation_read_only_review.add_argument(
        "--execute",
        action="store_true",
        help="Read the PMC page in memory; never persist article content",
    )
    citation_medrxiv_read_only_review = literature_commands.add_parser(
        "citation-medrxiv-read-only-review",
        help="Review an exact medRxiv preprint version and emit a no-storage receipt",
    )
    citation_medrxiv_read_only_review.add_argument("inventory", type=Path)
    citation_medrxiv_read_only_review.add_argument("screening_id")
    citation_medrxiv_read_only_review.add_argument("--source-url", required=True)
    citation_medrxiv_read_only_review.add_argument("--code-revision", required=True)
    citation_medrxiv_read_only_review.add_argument("--access-basis", required=True)
    citation_medrxiv_read_only_review.add_argument("--observed-rights", required=True)
    citation_medrxiv_read_only_review.add_argument("--rights-url", required=True)
    citation_medrxiv_read_only_review.add_argument(
        "--receipt-output", required=True, type=Path
    )
    citation_medrxiv_read_only_review.add_argument(
        "--execute",
        action="store_true",
        help="Read the medRxiv page in memory; never persist article content",
    )
    citation_institutional_pdf_review = literature_commands.add_parser(
        "citation-institutional-pdf-read-only-review",
        help="Review an approved institutional author-copy PDF without storing it",
    )
    citation_institutional_pdf_review.add_argument("inventory", type=Path)
    citation_institutional_pdf_review.add_argument("screening_id")
    citation_institutional_pdf_review.add_argument("--code-revision", required=True)
    citation_institutional_pdf_review.add_argument("--access-basis", required=True)
    citation_institutional_pdf_review.add_argument("--observed-rights", required=True)
    citation_institutional_pdf_review.add_argument("--rights-url", required=True)
    citation_institutional_pdf_review.add_argument(
        "--receipt-output", required=True, type=Path
    )
    citation_institutional_pdf_review.add_argument(
        "--execute",
        action="store_true",
        help="Read the PDF in memory; never persist article content",
    )
    citation_institutional_pdf_proposal = literature_commands.add_parser(
        "citation-institutional-pdf-appraisal-propose",
        help="Verify a bounded structured proposal against an ephemeral PDF",
    )
    citation_institutional_pdf_proposal.add_argument("inventory", type=Path)
    citation_institutional_pdf_proposal.add_argument("screening_id")
    citation_institutional_pdf_proposal.add_argument("review_receipt", type=Path)
    citation_institutional_pdf_proposal.add_argument("draft", type=Path)
    citation_institutional_pdf_proposal.add_argument(
        "--proposal-output", required=True, type=Path
    )
    citation_institutional_pdf_proposal.add_argument(
        "--execute",
        action="store_true",
        help="Verify the draft against PDF bytes in memory and retain only the proposal",
    )
    citation_publisher_pdf_review = literature_commands.add_parser(
        "citation-publisher-pdf-read-only-review",
        help="Review an approved publisher/repository PDF without storing it",
    )
    citation_publisher_pdf_review.add_argument("inventory", type=Path)
    citation_publisher_pdf_review.add_argument("screening_id")
    citation_publisher_pdf_review.add_argument("--code-revision", required=True)
    citation_publisher_pdf_review.add_argument("--access-basis", required=True)
    citation_publisher_pdf_review.add_argument("--observed-rights", required=True)
    citation_publisher_pdf_review.add_argument("--rights-url", required=True)
    citation_publisher_pdf_review.add_argument(
        "--receipt-output", required=True, type=Path
    )
    citation_publisher_pdf_review.add_argument(
        "--execute",
        action="store_true",
        help="Read the PDF in memory; never persist article content",
    )
    citation_publisher_pdf_proposal = literature_commands.add_parser(
        "citation-publisher-pdf-appraisal-propose",
        help="Verify a bounded proposal against an approved ephemeral PDF",
    )
    citation_publisher_pdf_proposal.add_argument("inventory", type=Path)
    citation_publisher_pdf_proposal.add_argument("screening_id")
    citation_publisher_pdf_proposal.add_argument("review_receipt", type=Path)
    citation_publisher_pdf_proposal.add_argument("draft", type=Path)
    citation_publisher_pdf_proposal.add_argument(
        "--proposal-output", required=True, type=Path
    )
    citation_publisher_pdf_proposal.add_argument(
        "--execute",
        action="store_true",
        help="Verify the draft against PDF bytes and retain only the proposal",
    )
    full_text_fetch = literature_commands.add_parser(
        "full-text-fetch",
        help="Retrieve and verify one explicitly licensed Europe PMC full text",
    )
    full_text_fetch.add_argument("receipt", type=Path, help="Verified screening queue receipt")
    full_text_fetch.add_argument(
        "progress_receipt", type=Path, help="Latest verified founder progress receipt"
    )
    full_text_fetch.add_argument("screening_id", help="Founder-included screening ID")
    full_text_fetch.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    full_text_fetch.add_argument(
        "--receipt-output", type=Path, help="New path for the verified aggregate receipt"
    )
    full_text_fetch.add_argument(
        "--access-decision-dir",
        type=Path,
        help="Directory of prior restricted-access decisions that must not be retried",
    )
    full_text_fetch.add_argument(
        "--execute", action="store_true", help="Contact Europe PMC and persist licensed XML"
    )
    full_text_import_pdf = literature_commands.add_parser(
        "full-text-import-pdf",
        help="Import and verify one explicitly licensed publisher PDF",
    )
    full_text_import_pdf.add_argument(
        "receipt", type=Path, help="Verified screening queue receipt"
    )
    full_text_import_pdf.add_argument(
        "progress_receipt", type=Path, help="Latest verified founder progress receipt"
    )
    full_text_import_pdf.add_argument("screening_id", help="Founder-included screening ID")
    full_text_import_pdf.add_argument("pdf_path", type=Path, help="Downloaded publisher PDF")
    full_text_import_pdf.add_argument("--source-url", required=True)
    full_text_import_pdf.add_argument("--license-name", required=True)
    full_text_import_pdf.add_argument("--license-spdx", required=True)
    full_text_import_pdf.add_argument("--license-url", required=True)
    full_text_import_pdf.add_argument("--copyright-statement", required=True)
    full_text_import_pdf.add_argument(
        "--code-revision", required=True, help="Exact Git commit SHA"
    )
    full_text_import_pdf.add_argument(
        "--receipt-output", required=True, type=Path, help="New verified receipt path"
    )
    full_text_import_pdf.add_argument(
        "--execute", action="store_true", help="Verify and persist the licensed PDF"
    )

    program = commands.add_parser("program", help="Manage research program charters")
    program_commands = program.add_subparsers(dest="program_command", required=True)
    program_validate = program_commands.add_parser("validate", help="Validate a program charter")
    program_validate.add_argument("path", type=Path, help="Path to program_charter.yaml")
    program_schema = program_commands.add_parser("schema", help="Write the program JSON Schema")
    program_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    question = commands.add_parser("question", help="Manage decision-led research questions")
    question_commands = question.add_subparsers(dest="question_command", required=True)
    question_validate = question_commands.add_parser(
        "validate", help="Validate a research-question intake"
    )
    question_validate.add_argument("path", type=Path, help="Path to research_question.yaml")
    question_schema = question_commands.add_parser(
        "schema", help="Write the research-question JSON Schema"
    )
    question_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    study = commands.add_parser("study", help="Create and validate standardized study workspaces")
    study_commands = study.add_subparsers(dest="study_command", required=True)
    study_init = study_commands.add_parser("init", help="Create a new study scaffold")
    study_init.add_argument("study_id", help="Permanent study ID, for example NAS-BRCA-002")
    study_init.add_argument("--slug", required=True, help="Lowercase underscore directory slug")
    study_init.add_argument("--title", required=True, help="Human-readable study title")
    study_init.add_argument("--program-id", required=True, help="Owning program ID")
    study_init.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in StudyRole],
        help="Study's role in the research program",
    )
    study_init.add_argument(
        "--root",
        type=Path,
        default=Path("workflows/studies"),
        help="Directory that contains standardized study workspaces",
    )
    study_validate = study_commands.add_parser("validate", help="Validate a study workspace")
    study_validate.add_argument("path", type=Path, help="Path to a study workspace")
    study_schema = study_commands.add_parser("schema", help="Write canonical study schemas")
    study_schema.add_argument("study_path", type=Path, help="Output path for study schema")
    study_schema.add_argument("pipeline_path", type=Path, help="Output path for pipeline schema")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "storage" and args.storage_command == "init":
        layout = DataLayout(get_settings().data_root)
        layout.initialize()
        print(f"Initialized NaS Core data root: {layout.root}")
        return 0

    if args.command == "storage" and args.storage_command == "check":
        layout = DataLayout(get_settings().data_root)
        layout.validate()
        print(f"NaS Core data root is valid: {layout.root}")
        return 0

    if args.command == "plan" and args.plan_command == "validate":
        plan = load_analysis_plan(args.path, registry=SourceRegistry.from_yaml(args.registry))
        print(
            f"Analysis plan is valid: {plan.study_id} "
            f"v{plan.protocol_version} ({plan.status.value})"
        )
        return 0

    if args.command == "plan" and args.plan_command == "schema":
        write_analysis_plan_schema(args.path)
        print(f"Wrote analysis-plan schema: {args.path}")
        return 0

    if args.command == "ingest" and args.ingest_command == "gdc-plan":
        plan = load_analysis_plan(args.path, registry=SourceRegistry.from_yaml(args.registry))
        if not args.execute:
            print(json.dumps(build_case_query(plan, page_size=500), indent=2))
            print("Dry run only; no data was requested or stored.")
            return 0
        if not args.data_release:
            raise SystemExit("--data-release is required with --execute")
        if not args.release_notes_url:
            raise SystemExit("--release-notes-url is required with --execute")
        snapshot = GDCSnapshotService(store=get_object_store()).capture_cases(
            plan,
            data_release=args.data_release,
            release_notes_url=args.release_notes_url,
        )
        print(
            f"Created immutable snapshot {snapshot.snapshot_id} "
            f"with {snapshot.record_count} records"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "schema":
        write_dataset_snapshot_schema(args.path)
        print(f"Wrote dataset-snapshot schema: {args.path}")
        return 0

    if args.command == "cohort" and args.cohort_command == "build":
        plan = load_analysis_plan(args.plan, registry=SourceRegistry.from_yaml(args.registry))
        receipt = load_snapshot_receipt(args.receipt)
        if not args.execute:
            print(
                f"Cohort build ready: {plan.study_id} protocol {plan.protocol_version}, "
                f"snapshot {receipt.snapshot_id}, code {args.code_revision}"
            )
            print("Dry run only; no snapshot records were read and no artifacts were stored.")
            return 0
        manifest = CohortBuildService(store=get_object_store()).build(
            plan,
            receipt,
            code_revision=args.code_revision,
        )
        print(
            f"Created immutable cohort build {manifest.build_id}: "
            f"{manifest.included_case_count} included, "
            f"{manifest.excluded_case_count} excluded"
        )
        return 0

    if args.command == "cohort" and args.cohort_command == "schema":
        write_cohort_schemas(args.qa_path, args.manifest_path, args.receipt_path)
        print(f"Wrote cohort schemas: {args.qa_path}, {args.manifest_path}, {args.receipt_path}")
        return 0

    if args.command == "analysis" and args.analysis_command == "survival":
        plan = load_analysis_plan(args.plan, registry=SourceRegistry.from_yaml(args.registry))
        cohort_receipt = load_cohort_receipt(args.receipt)
        if not args.execute:
            print(
                f"Survival analysis ready: {plan.study_id} protocol {plan.protocol_version}, "
                f"cohort {cohort_receipt.build_id}, gate {cohort_receipt.qa_gate_status.value}, "
                f"code {args.code_revision}"
            )
            print("Dry run only; no cohort rows were read and no models were fitted.")
            return 0
        run_manifest = SurvivalAnalysisService(store=get_object_store()).run(
            plan,
            cohort_receipt,
            code_revision=args.code_revision,
        )
        print(f"Created immutable survival run {run_manifest.run_id}")
        return 0

    if args.command == "analysis" and args.analysis_command == "schema":
        write_survival_schemas(args.summary_path, args.manifest_path, args.receipt_path)
        print(
            "Wrote survival schemas: "
            f"{args.summary_path}, {args.manifest_path}, {args.receipt_path}"
        )
        return 0

    if args.command == "discovery" and args.discovery_command == "validate":
        phase_zero, search, feasibility = load_phase_zero_artifacts(
            args.plan,
            args.search,
            args.feasibility,
        )
        print(
            f"Phase 0 package is valid: {phase_zero.study_id} "
            f"question {phase_zero.question_id} v{phase_zero.question_version}; "
            f"search {search.status.value}; feasibility {feasibility.status.value}"
        )
        return 0

    if args.command == "discovery" and args.discovery_command == "schema":
        write_discovery_schemas(args.plan_path, args.search_path, args.feasibility_path)
        print(
            "Wrote discovery schemas: "
            f"{args.plan_path}, {args.search_path}, {args.feasibility_path}"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "validate":
        specification = load_reliability_specification(args.path)
        print(
            f"Reliability specification is valid: {specification.study_id} "
            f"question {specification.question_version}, "
            f"method {specification.specification_version} ({specification.status.value}); "
            f"execution authorized: {specification.execution_authorized}"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "schema":
        write_reliability_schema(args.path)
        print(f"Wrote reliability schema: {args.path}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "validate":
        priority = load_priority_evidence_set(args.priority_path)
        review_progress = load_evidence_review_progress(args.progress_path)
        priority_identity = (
            priority.study_id,
            priority.question_id,
            priority.question_version,
            priority.set_version,
        )
        progress_identity = (
            review_progress.study_id,
            review_progress.question_id,
            review_progress.question_version,
            review_progress.priority_set_version,
        )
        if priority_identity != progress_identity:
            raise ValueError("priority set and evidence-review progress must identify one version")
        print(
            f"Evidence review is valid: {review_progress.study_id} "
            f"question {review_progress.question_version}; "
            f"{len(priority.candidates)} priority records, "
            f"{review_progress.pending_candidate_count} pending, "
            f"stopping rule satisfied: {review_progress.stopping_rule_satisfied}"
        )
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "schema":
        write_evidence_review_schemas(args.priority_path, args.progress_path)
        print(
            f"Wrote evidence-review schemas: {args.priority_path}, {args.progress_path}"
        )
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-retrieve"
    ):
        inventory = load_full_text_inventory(args.inventory_path)
        seeds = [
            CitationSeed(
                evidence_id=f"PMID:{record.pmid}",
                pmid=record.pmid,
                title=record.title,
            )
            for record in inventory.records
            if record.pmid is not None
        ]
        if len(seeds) != inventory.provisional_inclusion_count:
            raise SystemExit("every included citation seed requires a PMID")
        if not args.execute:
            print(
                f"Citation pass {args.pass_number} ready: {len(seeds)} seeds, "
                f"code {args.code_revision}"
            )
            print("Dry run only; Europe PMC was not contacted and nothing was stored.")
            return 0
        service = CitationChainRetrievalService(store=get_object_store())
        citation_snapshot = service.retrieve(
            seeds,
            study_id=inventory.study_id,
            pass_number=args.pass_number,
            code_revision=args.code_revision,
        )
        citation_receipt = service.verify(citation_snapshot)
        write_citation_chain_receipt(args.receipt_output, citation_receipt)
        print(
            f"Retrieved citation pass {citation_receipt.pass_number}: "
            f"{citation_receipt.backward_candidate_count} backward links, "
            f"{citation_receipt.forward_candidate_count} forward links, "
            f"{citation_receipt.unique_candidate_count} unique non-seed candidates"
        )
        print(f"Wrote verified citation receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-screening-prepare"
    ):
        citation_receipt = load_citation_chain_receipt(args.citation_receipt)
        prior_search_receipt = load_literature_search_receipt(
            args.prior_search_receipt
        )
        if not args.execute:
            print(
                f"Citation screening preparation ready: pass "
                f"{citation_receipt.pass_number}, "
                f"{citation_receipt.unique_candidate_count} candidates"
            )
            print("Dry run only; no deduplication artifacts were stored.")
            return 0
        preparation_service = CitationScreeningPreparationService(
            store=get_object_store()
        )
        preparation = preparation_service.prepare(
            citation_receipt,
            prior_search_receipt,
            code_revision=args.code_revision,
        )
        write_citation_screening_preparation_receipt(
            args.receipt_output, preparation
        )
        print(
            f"Prepared citation screening pass {preparation.pass_number}: "
            f"{preparation.already_screened_count} already screened, "
            f"{preparation.duplicate_candidate_count} duplicate candidates, "
            f"{preparation.requires_screening_count} requiring founder screening"
        )
        print(f"Wrote verified preparation receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-prioritize"
    ):
        preparation = load_citation_screening_preparation_receipt(
            args.preparation_receipt
        )
        if not args.execute:
            print(
                f"Citation prioritization ready: "
                f"{preparation.requires_screening_count} candidates"
            )
            print("Dry run only; no ranking artifact was stored.")
            return 0
        prioritization_service = CitationPrioritizationService(
            store=get_object_store()
        )
        prioritization = prioritization_service.prioritize(
            preparation,
            code_revision=args.code_revision,
        )
        write_citation_prioritization_receipt(
            args.receipt_output, prioritization
        )
        print(
            f"Prioritized citation pass {prioritization.pass_number}: "
            f"{prioritization.direct_priority_count} direct, "
            f"{prioritization.supporting_priority_count} supporting, "
            f"{prioritization.context_priority_count} context"
        )
        print("Advisory ranking only; zero final screening decisions were recorded.")
        print(f"Wrote verified prioritization receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-enrich"
    ):
        prioritization = load_citation_prioritization_receipt(
            args.prioritization_receipt
        )
        requested = (
            prioritization.candidate_count
            if args.include_context
            else (
                prioritization.direct_priority_count
                + prioritization.supporting_priority_count
            )
        )
        if not args.execute:
            print(
                f"Citation enrichment ready: {requested} direct/supporting candidates"
            )
            print("Dry run only; Europe PMC was not contacted.")
            return 0
        enrichment_service = CitationEnrichmentService(store=get_object_store())
        enrichment = enrichment_service.enrich(
            prioritization,
            code_revision=args.code_revision,
            include_context=args.include_context,
        )
        write_citation_enrichment_receipt(args.receipt_output, enrichment)
        print(
            f"Enriched citation pass {enrichment.pass_number}: "
            f"{enrichment.metadata_match_count}/{enrichment.requested_candidate_count} "
            f"metadata matches, {enrichment.abstract_count} abstracts, "
            f"{enrichment.unresolved_metadata_count} unresolved"
        )
        print("Metadata only; zero final screening decisions were recorded.")
        print(f"Wrote verified enrichment receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-recommend"
    ):
        enrichment = load_citation_enrichment_receipt(args.enrichment_receipt)
        if not args.execute:
            print(
                f"Citation recommendation pass ready: "
                f"{enrichment.requested_candidate_count} candidates"
            )
            print("Dry run only; no recommendations or decisions were stored.")
            return 0
        recommendation_service = CitationRecommendationService(
            store=get_object_store()
        )
        recommendations = recommendation_service.recommend(
            enrichment,
            code_revision=args.code_revision,
        )
        write_citation_recommendation_receipt(
            args.receipt_output, recommendations
        )
        print(
            f"Recommended citation pass {recommendations.pass_number}: "
            f"{recommendations.include_recommendation_count} include, "
            f"{recommendations.exclude_recommendation_count} exclude, "
            f"{recommendations.unclear_recommendation_count} unclear"
        )
        print("Advisory only; zero founder decisions were recorded.")
        print(f"Wrote verified recommendation receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-packet"
    ):
        recommendation_receipt = load_citation_recommendation_receipt(
            args.recommendation_receipt
        )
        packet_service = CitationFounderPacketService(store=get_object_store())
        packet = packet_service.build(
            recommendation_receipt,
            packet_path=args.packet_output,
            appendix_path=args.appendix_output,
        )
        write_citation_founder_packet_receipt(args.receipt_output, packet)
        print(
            f"Built citation founder packet: {packet.proposed_decision_count} "
            f"proposed decisions, {packet.pending_adjudication_count} pending"
        )
        print(f"Packet SHA-256: {packet.packet_sha256}")
        print(f"Appendix SHA-256: {packet.appendix_sha256}")
        print("Advisory only; explicit founder confirmation is still required.")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-adjudicate"
    ):
        prior_recommendations = load_citation_recommendation_receipt(
            args.recommendation_receipt
        )
        enrichment = load_citation_enrichment_receipt(args.enrichment_receipt)
        policy = load_citation_adjudication_policy(args.policy)
        if not args.execute:
            print(
                f"Citation adjudication ready: "
                f"{prior_recommendations.unclear_recommendation_count} unresolved records"
            )
            print("Dry run only; no recommendations or decisions were stored.")
            return 0
        adjudication_service = CitationUnclearAdjudicationService(
            store=get_object_store()
        )
        adjudication = adjudication_service.adjudicate(
            prior_recommendations,
            enrichment,
            policy,
            code_revision=args.code_revision,
        )
        write_citation_recommendation_receipt(args.receipt_output, adjudication)
        print(
            f"Adjudicated citation pass {adjudication.pass_number}: "
            f"{adjudication.include_recommendation_count} include, "
            f"{adjudication.exclude_recommendation_count} exclude, "
            f"{adjudication.unclear_recommendation_count} unclear"
        )
        print("Advisory only; zero founder decisions were recorded.")
        print(f"Wrote verified adjudication receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-confirm"
    ):
        first_packet = load_citation_founder_packet_receipt(
            args.first_packet_receipt
        )
        second_packet = load_citation_founder_packet_receipt(
            args.second_packet_receipt
        )
        citation_confirmation = load_citation_founder_confirmation(args.confirmation)
        if not args.execute:
            print(
                f"Citation confirmation ready: "
                f"{first_packet.proposed_decision_count + second_packet.proposed_decision_count} "
                f"decisions bound to founder {citation_confirmation.founder_name}"
            )
            print("Dry run only; no final decision ledger was stored.")
            return 0
        confirmation_service = CitationDecisionConfirmationService(
            store=get_object_store()
        )
        decision_receipt = confirmation_service.confirm(
            first_packet,
            second_packet,
            citation_confirmation,
            first_packet_path=args.first_packet,
            first_appendix_path=args.first_appendix,
            second_packet_path=args.second_packet,
            second_appendix_path=args.second_appendix,
            code_revision=args.code_revision,
        )
        write_citation_decision_ledger_receipt(
            args.receipt_output, decision_receipt
        )
        print(
            f"Confirmed citation pass {decision_receipt.pass_number}: "
            f"{decision_receipt.included_count} include, "
            f"{decision_receipt.excluded_count} exclude, "
            f"{decision_receipt.unclear_count} unclear"
        )
        print(f"Wrote final founder decision receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-reconcile"
    ):
        citation_decision = load_citation_decision_ledger_receipt(
            args.decision_receipt
        )
        citation_inventory = load_full_text_inventory(args.inventory)
        appraisal_paths = sorted(
            {
                path
                for directory in args.appraisal_dir
                for path in directory.glob("*.yaml")
            }
        )
        appraisals = [load_full_text_appraisal(path) for path in appraisal_paths]
        if not args.execute:
            print(
                f"Citation reconciliation ready: "
                f"{citation_decision.included_count} confirmed inclusions against "
                f"{len(citation_inventory.records)} active records and "
                f"{len({item.screening_id for item in appraisals})} prior appraisals"
            )
            print("Dry run only; no reconciliation artifact was stored.")
            return 0
        reconciliation_service = CitationInclusionReconciliationService(
            store=get_object_store()
        )
        reconciliation = reconciliation_service.reconcile(
            citation_decision,
            citation_inventory,
            appraisals,
            code_revision=args.code_revision,
        )
        write_citation_inclusion_reconciliation_receipt(
            args.receipt_output, reconciliation
        )
        print(
            f"Reconciled citation pass {reconciliation.pass_number}: "
            f"{reconciliation.active_inventory_match_count} active inventory, "
            f"{reconciliation.prior_appraisal_match_count} prior appraisal, "
            f"{reconciliation.net_new_count} net new"
        )
        print(f"Wrote reconciliation receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "activate-cap-amendment"
    ):
        amendment_approval = load_evidence_cap_amendment_approval(args.approval)
        inclusion_reconciliation = load_citation_inclusion_reconciliation_receipt(
            args.reconciliation_receipt
        )
        if not args.execute:
            print(
                f"Evidence-cap amendment {amendment_approval.amendment_version} "
                f"ready for activation by founder {amendment_approval.founder_name}"
            )
            print("Dry run only; no appraisal queue was stored.")
            return 0
        amendment_service = EvidenceCapAmendmentActivationService(
            store=get_object_store()
        )
        activation = amendment_service.activate(
            amendment_approval,
            inclusion_reconciliation,
            amendment_path=args.amendment,
            reconciliation_receipt_path=args.reconciliation_receipt,
            code_revision=args.code_revision,
        )
        write_evidence_cap_amendment_activation_receipt(
            args.receipt_output, activation
        )
        print(
            f"Activated evidence protocol {activation.active_protocol_version}: "
            f"{activation.repository_candidate_count} repository candidates, "
            f"{activation.access_check_required_count} access checks, "
            f"{activation.prior_appraisal_reuse_count} prior appraisals"
        )
        print(f"Wrote amendment activation receipt: {args.receipt_output}")
        return 0

    if args.command == "literature" and args.literature_command == "search":
        phase_zero, search, _ = load_phase_zero_artifacts(
            args.plan,
            args.search,
            args.feasibility,
        )
        if args.execute and args.count_only:
            raise SystemExit("choose either --execute or --count-only")
        if not args.execute and not args.count_only:
            for source in search.sources:
                print(f"{source.source_id}: {source.query}")
            print("Dry run only; no literature API was contacted and nothing was stored.")
            return 0
        if not args.contact_email:
            raise SystemExit("--contact-email is required with --execute or --count-only")
        literature_service = LiteratureSearchService(
            store=get_object_store(),
            registry=SourceRegistry.from_yaml(args.registry),
        )
        if args.count_only:
            counts = literature_service.preview_counts(
                phase_zero,
                search,
                contact_email=args.contact_email,
            )
            print(json.dumps(counts, indent=2, sort_keys=True))
            print("Count preview only; no literature records or manifests were stored.")
            return 0
        literature_snapshot = literature_service.capture(
            phase_zero,
            search,
            contact_email=args.contact_email,
        )
        print(
            f"Created immutable literature search {literature_snapshot.execution_id}: "
            f"{literature_snapshot.unique_record_count} unique records, "
            f"{literature_snapshot.duplicate_record_count} duplicates"
        )
        return 0

    if args.command == "literature" and args.literature_command == "schema":
        write_literature_schemas(
            args.snapshot_path,
            args.receipt_path,
            args.screening_manifest_path,
            args.screening_receipt_path,
        )
        print(
            "Wrote literature schemas: "
            f"{args.snapshot_path}, {args.receipt_path}, "
            f"{args.screening_manifest_path}, {args.screening_receipt_path}"
        )
        return 0

    if args.command == "literature" and args.literature_command == "search-verify":
        search_receipt = LiteratureSearchVerificationService(store=get_object_store()).verify(
            args.study_id,
            args.execution_id,
        )
        write_literature_search_receipt(args.output_path, search_receipt)
        print(
            f"Verified literature search {search_receipt.execution_id}: "
            f"{search_receipt.unique_record_count} unique records; receipt {args.output_path}"
        )
        return 0

    if args.command == "literature" and args.literature_command == "screening-build":
        screening_receipt = load_literature_search_receipt(args.receipt)
        if not args.execute:
            print(
                f"Screening queue ready: {screening_receipt.study_id}, "
                f"search {screening_receipt.execution_id}, "
                f"{screening_receipt.unique_record_count} records, code {args.code_revision}"
            )
            print("Dry run only; no literature records were read and no queue was stored.")
            return 0
        queue = ScreeningQueueService(store=get_object_store()).build(
            screening_receipt,
            code_revision=args.code_revision,
        )
        print(
            f"Created immutable screening queue {queue.queue_id}: "
            f"{queue.summary.pending_record_count} pending human decisions"
        )
        return 0

    if args.command == "literature" and args.literature_command == "screening-verify":
        queue_receipt = ScreeningQueueService(store=get_object_store()).verify(
            args.study_id,
            args.search_execution_id,
            args.queue_id,
        )
        write_screening_queue_receipt(args.output_path, queue_receipt)
        print(
            f"Verified screening queue {queue_receipt.queue_id}: "
            f"{queue_receipt.summary.pending_record_count} pending records; "
            f"receipt {args.output_path}"
        )
        return 0

    if args.command == "literature" and args.literature_command == "screening-reconcile":
        current_receipt = load_screening_queue_receipt(args.current_receipt)
        prior_receipt = load_screening_queue_receipt(args.prior_receipt)
        if not args.execute:
            print(
                f"Inventory reconciliation ready: current {current_receipt.queue_id}, "
                f"prior {prior_receipt.queue_id}, code {args.code_revision}"
            )
            print("Dry run only; no queue records were read and no artifact was stored.")
            return 0
        if args.receipt_output is None:
            raise SystemExit("--receipt-output is required with --execute")
        reconciliation_receipt = InventoryReconciliationService(
            store=get_object_store()
        ).reconcile(
            current_receipt,
            prior_receipt,
            code_revision=args.code_revision,
        )
        write_inventory_reconciliation_receipt(
            args.receipt_output,
            reconciliation_receipt,
        )
        print(
            f"Reconciled inventory {reconciliation_receipt.reconciliation_id}: "
            f"{reconciliation_receipt.prior_exact_match_count} exact prior matches, "
            f"{reconciliation_receipt.author_year_candidate_count} author-year candidates, "
            f"{reconciliation_receipt.new_candidate_count} new candidates"
        )
        print(f"Wrote verified aggregate receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "screening-reconciliation-schema"
    ):
        write_inventory_reconciliation_schema(args.output_path)
        print(f"Wrote inventory-reconciliation schema: {args.output_path}")
        return 0

    if args.command == "literature" and args.literature_command == "screening-next":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = (
            load_screening_progress_receipt(args.progress_receipt)
            if args.progress_receipt
            else None
        )
        review_batch = ScreeningReviewService(store=get_object_store()).next_batch(
            queue_receipt,
            progress_receipt=progress_receipt,
            batch_size=args.batch_size,
            include_unclear=args.include_unclear,
        )
        print(json.dumps(review_batch.model_dump(mode="json", exclude_none=True), indent=2))
        return 0

    if args.command == "literature" and args.literature_command == "screening-prioritize":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = (
            load_screening_progress_receipt(args.progress_receipt)
            if args.progress_receipt
            else None
        )
        priority_batch = DeterministicPrioritizationService(store=get_object_store()).rank(
            queue_receipt,
            progress_receipt=progress_receipt,
            limit=args.limit,
        )
        print(json.dumps(priority_batch.model_dump(mode="json", exclude_none=True), indent=2))
        return 0

    if args.command == "literature" and args.literature_command == "screening-record":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        decision_batch = load_screening_decision_batch(args.decisions)
        progress_receipt = (
            load_screening_progress_receipt(args.previous_progress_receipt)
            if args.previous_progress_receipt
            else None
        )
        review_service = ScreeningReviewService(store=get_object_store())
        if not args.execute:
            review_service.validate_batch(
                queue_receipt,
                decision_batch,
                code_revision=args.code_revision,
                progress_receipt=progress_receipt,
            )
            print(
                f"Review batch is valid: {len(decision_batch.decisions)} founder decisions "
                f"for queue {decision_batch.queue_id}, code {args.code_revision}"
            )
            print("Dry run only; no queue records were read and no decisions were stored.")
            return 0
        if args.receipt_output is None:
            raise SystemExit("--receipt-output is required with --execute")
        progress = review_service.record_batch(
            queue_receipt,
            decision_batch,
            code_revision=args.code_revision,
            progress_receipt=progress_receipt,
        )
        verified_receipt = review_service.verify(queue_receipt, progress)
        write_screening_progress_receipt(args.receipt_output, verified_receipt)
        print(
            f"Recorded immutable screening progress {progress.progress_id}: "
            f"{progress.summary.decided_record_count}/"
            f"{progress.summary.total_record_count} records decided"
        )
        print(f"Wrote verified aggregate receipt: {args.receipt_output}")
        return 0

    if args.command == "literature" and args.literature_command == "screening-confirm":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = load_screening_progress_receipt(args.progress_receipt)
        confirmation = load_screening_confirmation(args.confirmation)
        batch = ScreeningConfirmationService(
            review_service=ScreeningReviewService(store=get_object_store())
        ).build_decision_batch(
            queue_receipt=queue_receipt,
            progress_receipt=progress_receipt,
            packet_path=args.packet,
            confirmation=confirmation,
        )
        write_screening_decision_batch(args.output_path, batch)
        print(
            f"Built founder decision batch for {len(batch.decisions)} records from "
            f"packet {confirmation.packet_sha256}"
        )
        print("No decisions were stored; use screening-record to validate and execute.")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "screening-confirm-preview"
    ):
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = load_screening_progress_receipt(args.progress_receipt)
        preview = ScreeningConfirmationService(
            review_service=ScreeningReviewService(store=get_object_store())
        ).preview_packet(
            queue_receipt=queue_receipt,
            progress_receipt=progress_receipt,
            packet_path=args.packet,
        )
        print(json.dumps(preview.model_dump(mode="json"), indent=2))
        return 0

    if args.command == "literature" and args.literature_command == "screening-review-schema":
        write_screening_review_schemas(
            args.decision_batch_path,
            args.progress_manifest_path,
            args.progress_receipt_path,
        )
        print(
            "Wrote screening-review schemas: "
            f"{args.decision_batch_path}, {args.progress_manifest_path}, "
            f"{args.progress_receipt_path}"
        )
        return 0

    if args.command == "literature" and args.literature_command == "screening-ai":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        ai_policy = load_ai_advisory_policy(args.policy)
        ai_prompt = Path(ai_policy.prompt_path).read_text(encoding="utf-8")
        progress_receipt = (
            load_screening_progress_receipt(args.progress_receipt)
            if args.progress_receipt
            else None
        )
        if not args.execute:
            print(
                f"AI advisory screening ready: queue {queue_receipt.queue_id}, "
                f"policy {ai_policy.policy_version}, {ai_policy.model}, "
                f"up to {ai_policy.max_records_per_call} records"
            )
            print("Dry run only; no queue records were read and no provider was contacted.")
            return 0
        if args.receipt_output is None:
            raise SystemExit("--receipt-output is required with --execute")
        settings = get_settings()
        gateway = OpenAIScreeningGateway(
            api_key=settings.openai_api_key,
            model=ai_policy.model,
            reasoning_effort=ai_policy.reasoning_effort,
        )
        ai_service = AIAdvisoryScreeningService(
            store=get_object_store(settings),
            gateway=gateway,
        )
        advisory_manifest = ai_service.run(
            queue_receipt,
            ai_policy,
            prompt_text=ai_prompt,
            code_revision=args.code_revision,
            progress_receipt=progress_receipt,
        )
        verified = ai_service.verify(advisory_manifest)
        write_ai_advisory_receipt(args.receipt_output, verified)
        print(
            f"Created verified AI advisory run {advisory_manifest.advisory_run_id}: "
            f"{advisory_manifest.summary.recommendation_count} recommendations, "
            "zero final decisions"
        )
        return 0

    if args.command == "literature" and args.literature_command == "appraisal-validate":
        appraisal = load_full_text_appraisal(args.path)
        print(
            f"Full-text appraisal is valid: {appraisal.study_id}, "
            f"{appraisal.screening_id}, {appraisal.evidence_role}"
        )
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "read-only-receipt-validate"
    ):
        read_only_receipt = load_full_text_read_only_review_receipt(args.path)
        print(
            f"Read-only review receipt is valid: {read_only_receipt.study_id}, "
            f"{read_only_receipt.screening_id}, {read_only_receipt.access_mode}"
        )
        return 0

    if args.command == "literature" and args.literature_command == "appraisal-progress":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = load_screening_progress_receipt(args.progress_receipt)
        inventory = FullTextInventoryService(store=get_object_store()).build(
            queue_receipt,
            progress_receipt,
        )
        appraisal_progress = FullTextAppraisalProgressService().build(
            inventory,
            retrieval_receipt_paths=sorted(args.full_text_receipt_dir.glob("*.yaml")),
            read_only_review_receipt_paths=sorted(
                (args.full_text_receipt_dir / "read-only-receipts").glob("*.yaml")
            ),
            appraisal_paths=sorted(args.appraisal_dir.glob("*.yaml")),
            access_decision_paths=sorted(
                (args.full_text_receipt_dir / "access-decisions").glob("*.yaml")
            ),
            duplicate_decision_paths=sorted(
                (args.full_text_receipt_dir / "duplicate-decisions").glob("*.yaml")
            ),
        )
        write_full_text_appraisal_progress(args.output_path, appraisal_progress)
        print(
            f"Appraisal progress: {appraisal_progress.appraisals_completed}/"
            f"{appraisal_progress.provisional_inclusion_count} completed; "
            f"{appraisal_progress.full_texts_retrieved} full texts retrieved; "
            f"{appraisal_progress.read_only_full_texts_reviewed} reviewed read-only; "
            f"{appraisal_progress.access_restricted_count} access restricted; "
            f"{appraisal_progress.duplicate_resolved_count} duplicates resolved"
        )
        print(f"Wrote reconciled progress: {args.output_path}")
        return 0

    if args.command == "literature" and args.literature_command == "full-text-inventory":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = load_screening_progress_receipt(args.progress_receipt)
        inventory = FullTextInventoryService(store=get_object_store()).build(
            queue_receipt,
            progress_receipt,
        )
        if args.output_path is not None:
            write_full_text_inventory(args.output_path, inventory)
            print(f"Wrote verified access inventory: {args.output_path}")
        print(json.dumps(inventory.model_dump(mode="json", exclude_none=True), indent=2))
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-access-inventory"
    ):
        activation_receipt = load_evidence_cap_amendment_activation_receipt(
            args.activation_receipt
        )
        inventory = CitationAccessInventoryService(store=get_object_store()).build(
            activation_receipt
        )
        write_full_text_inventory(args.output_path, inventory)
        print(
            f"Wrote citation access inventory: {inventory.provisional_inclusion_count} "
            f"net-new records, {inventory.repository_candidate_count} repository "
            f"candidates, {inventory.access_check_required_count} access checks"
        )
        print(f"Inventory path: {args.output_path}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-full-text-batch"
    ):
        inventory = load_full_text_inventory(args.inventory)
        if not args.execute:
            print(
                f"Citation full-text batch ready: "
                f"{inventory.repository_candidate_count} repository candidates, "
                f"code {args.code_revision}"
            )
            print("Dry run only; Europe PMC was not contacted and nothing was stored.")
            return 0
        citation_access_service = CitationRepositoryAccessService(
            retrieval_service=FullTextRetrievalService(store=get_object_store())
        )
        repository_access_batch, citation_retrieval_receipts = (
            citation_access_service.assess(
            inventory,
            code_revision=args.code_revision,
            receipt_directory=str(args.receipt_dir),
            )
        )
        args.receipt_dir.mkdir(parents=True, exist_ok=True)
        for citation_retrieval_receipt in citation_retrieval_receipts:
            write_full_text_retrieval_receipt(
                args.receipt_dir / f"{citation_retrieval_receipt.pmcid}.yaml",
                citation_retrieval_receipt,
            )
        write_repository_access_batch_receipt(
            args.batch_receipt_output, repository_access_batch
        )
        print(
            f"Assessed {repository_access_batch.repository_candidate_count} "
            f"repository candidates: {repository_access_batch.retrieved_count} "
            f"licensed full texts retrieved, "
            f"{repository_access_batch.access_check_required_count} "
            "routed to access checks"
        )
        print(f"Wrote repository access batch: {args.batch_receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-access-check-queue"
    ):
        inventory = load_full_text_inventory(args.inventory)
        repository_batch = load_repository_access_batch_receipt(
            args.repository_batch
        )
        access_queue = CitationAccessCheckQueueService().build(
            inventory,
            repository_batch,
            code_revision=args.code_revision,
        )
        write_citation_access_check_queue(args.output_path, access_queue)
        print(
            f"Wrote citation access-check queue: {access_queue.record_count} "
            "records pending governed resolution"
        )
        print(f"Access-check queue path: {args.output_path}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-appraisal-progress"
    ):
        inventory = load_full_text_inventory(args.inventory)
        citation_appraisal_progress = FullTextAppraisalProgressService().build(
            inventory,
            retrieval_receipt_paths=sorted(args.retrieval_dir.glob("*.yaml")),
            appraisal_paths=sorted(args.appraisal_dir.glob("*.yaml")),
            read_only_review_receipt_paths=(
                sorted(args.read_only_receipt_dir.glob("*.yaml"))
                if args.read_only_receipt_dir is not None
                else ()
            ),
            access_decision_paths=(
                sorted(args.access_decision_dir.glob("*.yaml"))
                if args.access_decision_dir is not None
                else ()
            ),
            duplicate_decision_paths=(
                sorted(args.duplicate_decision_dir.glob("*.yaml"))
                if args.duplicate_decision_dir is not None
                else ()
            ),
        )
        write_full_text_appraisal_progress(
            args.output_path, citation_appraisal_progress
        )
        ready = sum(
            item.status == "ready_for_appraisal"
            for item in citation_appraisal_progress.records
        )
        awaiting = sum(
            item.status == "awaiting_full_text"
            for item in citation_appraisal_progress.records
        )
        print(
            f"Wrote citation appraisal progress: {ready} ready for appraisal, "
            f"{awaiting} awaiting full text, "
            f"{citation_appraisal_progress.appraisals_completed} completed"
        )
        print(f"Progress path: {args.output_path}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-appraisal-authorize"
    ):
        appraisal_confirmation = load_full_text_appraisal_batch_confirmation(
            args.confirmation
        )
        proposal_paths = sorted(args.proposal_dir.glob("*.yaml"))
        appraisals = AppraisalConfirmationService().authorize(
            confirmation=appraisal_confirmation,
            packet_path=args.packet,
            proposal_paths=proposal_paths,
        )
        by_screening_id = {
            item.screening_id: item for item in appraisal_confirmation.proposals
        }
        for appraisal in appraisals:
            reference = by_screening_id[appraisal.screening_id]
            write_full_text_appraisal(
                args.output_dir / reference.filename,
                appraisal,
            )
        print(
            f"Authorized and wrote {len(appraisals)} locked appraisals "
            f"from batch {appraisal_confirmation.batch_number:04d}"
        )
        print(f"Appraisal directory: {args.output_dir}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-pmc-read-only-review"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [
            item for item in inventory.records if item.screening_id == args.screening_id
        ]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        if not args.execute:
            print(
                f"PMC read-only review ready: {matches[0].pmcid}, "
                f"screening {matches[0].screening_id}, code {args.code_revision}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        review_receipt = PmcReadOnlyReviewService().review(
            matches[0],
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            code_revision=args.code_revision,
            access_basis=args.access_basis,
            observed_rights=args.observed_rights,
            rights_url=args.rights_url,
        )
        write_full_text_read_only_review_receipt(
            args.receipt_output, review_receipt
        )
        print(
            f"Reviewed {review_receipt.pmcid} ephemerally: "
            f"{review_receipt.content_size_bytes} bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-medrxiv-read-only-review"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [
            item for item in inventory.records if item.screening_id == args.screening_id
        ]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        if not args.execute:
            print(
                f"medRxiv read-only review ready: {matches[0].doi}, "
                f"screening {matches[0].screening_id}, code {args.code_revision}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        review_receipt = MedrxivReadOnlyReviewService().review(
            matches[0],
            source_url=args.source_url,
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            code_revision=args.code_revision,
            access_basis=args.access_basis,
            observed_rights=args.observed_rights,
            rights_url=args.rights_url,
        )
        write_full_text_read_only_review_receipt(
            args.receipt_output, review_receipt
        )
        print(
            f"Reviewed medRxiv DOI {review_receipt.doi} ephemerally: "
            f"{review_receipt.content_size_bytes} bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command
        == "citation-institutional-pdf-read-only-review"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [
            item for item in inventory.records if item.screening_id == args.screening_id
        ]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        if not args.execute:
            print(
                f"Institutional PDF read-only review ready: {matches[0].doi}, "
                f"screening {matches[0].screening_id}, code {args.code_revision}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        review_receipt = InstitutionalPdfReadOnlyReviewService().review(
            matches[0],
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            code_revision=args.code_revision,
            access_basis=args.access_basis,
            observed_rights=args.observed_rights,
            rights_url=args.rights_url,
        )
        write_full_text_read_only_review_receipt(
            args.receipt_output, review_receipt
        )
        print(
            f"Reviewed institutional PDF DOI {review_receipt.doi} ephemerally: "
            f"{review_receipt.content_size_bytes} bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command
        == "citation-publisher-pdf-read-only-review"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [
            item for item in inventory.records if item.screening_id == args.screening_id
        ]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        if not args.execute:
            print(
                f"Publisher PDF read-only review ready: {matches[0].doi}, "
                f"screening {matches[0].screening_id}, code {args.code_revision}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        review_receipt = ApprovedPublisherPdfReadOnlyReviewService().review(
            matches[0],
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            code_revision=args.code_revision,
            access_basis=args.access_basis,
            observed_rights=args.observed_rights,
            rights_url=args.rights_url,
        )
        write_full_text_read_only_review_receipt(
            args.receipt_output, review_receipt
        )
        print(
            f"Reviewed publisher PDF DOI {review_receipt.doi} ephemerally: "
            f"{review_receipt.content_size_bytes} bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command
        == "citation-institutional-pdf-appraisal-propose"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [
            item for item in inventory.records if item.screening_id == args.screening_id
        ]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        review_receipt = load_full_text_read_only_review_receipt(
            args.review_receipt
        )
        draft = load_full_text_appraisal_proposal(args.draft)
        if not args.execute:
            print(
                f"Institutional PDF proposal verification ready: {matches[0].doi}, "
                f"screening {matches[0].screening_id}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        proposal = InstitutionalPdfAppraisalProposalService().validate(
            record=matches[0],
            receipt=review_receipt,
            proposal=draft,
        )
        write_full_text_appraisal_proposal(args.proposal_output, proposal)
        print(
            f"Verified structured proposal for DOI {proposal.doi} against "
            f"{review_receipt.content_size_bytes} ephemeral bytes; "
            "zero article bytes stored"
        )
        print(f"Wrote non-authoritative proposal: {args.proposal_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command
        == "citation-publisher-pdf-appraisal-propose"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [
            item for item in inventory.records if item.screening_id == args.screening_id
        ]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        review_receipt = load_full_text_read_only_review_receipt(
            args.review_receipt
        )
        draft = load_full_text_appraisal_proposal(args.draft)
        if not args.execute:
            print(
                f"Publisher PDF proposal verification ready: {matches[0].doi}, "
                f"screening {matches[0].screening_id}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        proposal = ApprovedPublisherPdfAppraisalProposalService().validate(
            record=matches[0],
            receipt=review_receipt,
            proposal=draft,
        )
        write_full_text_appraisal_proposal(args.proposal_output, proposal)
        print(
            f"Verified structured proposal for DOI {proposal.doi} against "
            f"{review_receipt.content_size_bytes} ephemeral bytes; "
            "zero article bytes stored"
        )
        print(f"Wrote non-authoritative proposal: {args.proposal_output}")
        return 0

    if args.command == "literature" and args.literature_command == "full-text-fetch":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = load_screening_progress_receipt(args.progress_receipt)
        inventory = FullTextInventoryService(store=get_object_store()).build(
            queue_receipt,
            progress_receipt,
        )
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not a current founder inclusion")
        if args.access_decision_dir is not None:
            decisions = [
                load_full_text_access_decision(path)
                for path in sorted(args.access_decision_dir.glob("*.yaml"))
            ]
            if any(item.screening_id == args.screening_id for item in decisions):
                raise SystemExit(
                    "full-text retrieval blocked by a recorded restricted-access decision"
                )
        if not args.execute:
            print(
                f"Full-text retrieval ready: {matches[0].pmcid}, "
                f"screening {matches[0].screening_id}, code {args.code_revision}"
            )
            print("Dry run only; Europe PMC was not contacted and nothing was stored.")
            return 0
        if args.receipt_output is None:
            raise SystemExit("--receipt-output is required with --execute")
        retrieval_service = FullTextRetrievalService(store=get_object_store())
        retrieval_manifest = retrieval_service.retrieve(
            matches[0],
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            code_revision=args.code_revision,
        )
        retrieval_receipt = retrieval_service.verify(retrieval_manifest)
        write_full_text_retrieval_receipt(args.receipt_output, retrieval_receipt)
        print(
            f"Retrieved and verified {retrieval_receipt.pmcid}: "
            f"{retrieval_receipt.full_text_size_bytes} bytes, "
            f"{retrieval_receipt.license.spdx_identifier}, "
            f"{retrieval_receipt.full_text_sha256}"
        )
        print(f"Wrote verified aggregate receipt: {args.receipt_output}")
        return 0

    if args.command == "literature" and args.literature_command == "full-text-import-pdf":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = load_screening_progress_receipt(args.progress_receipt)
        inventory = FullTextInventoryService(store=get_object_store()).build(
            queue_receipt,
            progress_receipt,
        )
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not a current founder inclusion")
        if not args.execute:
            print(
                f"Publisher-PDF import ready: {args.pdf_path}, "
                f"screening {matches[0].screening_id}, code {args.code_revision}"
            )
            print("Dry run only; the PDF was not read or stored.")
            return 0
        license_record = FullTextLicense(
            name=args.license_name,
            spdx_identifier=args.license_spdx,
            url=args.license_url,
            copyright_statement=args.copyright_statement,
        )
        import_service = LicensedPdfImportService(store=get_object_store())
        pdf_manifest = import_service.import_pdf(
            matches[0],
            pdf_path=args.pdf_path,
            source_url=args.source_url,
            license_record=license_record,
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            code_revision=args.code_revision,
        )
        retrieval_receipt = import_service.verify(pdf_manifest)
        write_full_text_retrieval_receipt(args.receipt_output, retrieval_receipt)
        print(
            f"Imported and verified publisher PDF: "
            f"{retrieval_receipt.full_text_size_bytes} bytes, "
            f"{retrieval_receipt.license.spdx_identifier}, "
            f"{retrieval_receipt.full_text_sha256}"
        )
        print(f"Wrote verified aggregate receipt: {args.receipt_output}")
        return 0

    if args.command == "literature" and args.literature_command == "screening-ai-schema":
        write_ai_advisory_schemas(args.output_path, args.manifest_path, args.receipt_path)
        print(
            f"Wrote AI advisory schemas: {args.output_path}, "
            f"{args.manifest_path}, {args.receipt_path}"
        )
        return 0

    if args.command == "program" and args.program_command == "validate":
        program = load_program_charter(args.path)
        print(
            f"Program charter is valid: {program.program_id} "
            f"v{program.charter_version} ({program.current_stage.value})"
        )
        return 0

    if args.command == "program" and args.program_command == "schema":
        write_model_schema(args.path, OncologyProgramCharter)
        print(f"Wrote program-charter schema: {args.path}")
        return 0

    if args.command == "question" and args.question_command == "validate":
        question = load_research_question(args.path)
        print(
            f"Research question is valid: {question.question_id} "
            f"({question.status.value}; score {question.selection_scores.total}/40)"
        )
        return 0

    if args.command == "question" and args.question_command == "schema":
        write_model_schema(args.path, ResearchQuestionIntake)
        print(f"Wrote research-question schema: {args.path}")
        return 0

    if args.command == "study" and args.study_command == "init":
        path = initialize_study(
            args.root,
            study_id=args.study_id,
            slug=args.slug,
            title=args.title,
            program_id=args.program_id,
            role=StudyRole(args.role),
        )
        print(f"Created standardized study workspace: {path}")
        return 0

    if args.command == "study" and args.study_command == "validate":
        study, pipeline = load_study_manifests(args.path)
        print(
            f"Study workspace is valid: {study.study_id} "
            f"({study.status.value}; stage {pipeline.current_stage.value})"
        )
        return 0

    if args.command == "study" and args.study_command == "schema":
        write_study_schemas(args.study_path, args.pipeline_path)
        print(f"Wrote study schemas: {args.study_path}, {args.pipeline_path}")
        return 0

    raise AssertionError("Unreachable command")
