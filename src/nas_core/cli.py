import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from nas_core.ai.gateway import OpenAIScreeningGateway
from nas_core.ai.screening import AIAdvisoryScreeningService
from nas_core.analysis.calibration_annotation_mapping import (
    CalibrationAnnotationMappingService,
)
from nas_core.analysis.calibration_feasibility_audit import (
    CalibrationFeasibilityAuditService,
)
from nas_core.analysis.calibration_feasibility_pilot import (
    CalibrationFeasibilityPilotService,
)
from nas_core.analysis.calibration_planning import CalibrationPlanningService
from nas_core.analysis.calibration_precision import (
    TechnicalReplicatePrecisionService,
)
from nas_core.analysis.calibration_readiness import TechnicalCalibrationReadinessService
from nas_core.analysis.calibration_scenario import (
    MultiObjectiveCalibrationScenarioService,
)
from nas_core.analysis.cohort import CohortBuildService
from nas_core.analysis.method_artifact import Pam50CandidateImportService
from nas_core.analysis.method_dependency import MethodDependencyAuditService
from nas_core.analysis.method_route import MethodRouteActivationService
from nas_core.analysis.numerical_conformance import NumericalConformanceService
from nas_core.analysis.platform_compatibility import (
    PlatformCompatibilityAuditService,
)
from nas_core.analysis.prospective_calibration import (
    ProspectiveCalibrationDesignService,
)
from nas_core.analysis.reference_construction import GSE81538ReferenceConstructionService
from nas_core.analysis.reference_development import (
    ReferenceDevelopmentProtocolService,
)
from nas_core.analysis.reference_sensitivity import GSE81538ReferenceSensitivityService
from nas_core.analysis.reliability import SyntheticSingleSampleReliabilityKernel
from nas_core.analysis.survival import SurvivalAnalysisService
from nas_core.analysis.technical_calibration import TechnicalCalibrationPlanService
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
    load_full_text_appraisal_progress,
    load_full_text_appraisal_proposal,
    load_full_text_inventory,
    load_full_text_read_only_review_receipt,
    load_publication_version_link_decision,
    write_full_text_appraisal,
    write_full_text_appraisal_progress,
    write_full_text_appraisal_proposal,
    write_full_text_inventory,
    write_full_text_read_only_review_receipt,
    write_full_text_retrieval_receipt,
    write_publication_version_link_decision,
    write_publication_version_reconciliation_receipt,
)
from nas_core.domain.calibration_annotation import (
    load_calibration_annotation_acquisition_plan,
    load_calibration_annotation_acquisition_receipt,
    load_calibration_annotation_mapping_plan,
    load_calibration_annotation_resolution_plan,
    write_calibration_annotation_acquisition_receipt,
    write_calibration_annotation_acquisition_schemas,
    write_calibration_annotation_mapping_receipt,
    write_calibration_annotation_mapping_schemas,
    write_calibration_annotation_resolution_receipt,
    write_calibration_annotation_resolution_schemas,
)
from nas_core.domain.calibration_feasibility_artifact import (
    load_calibration_feasibility_acquisition_plan,
    load_calibration_feasibility_acquisition_receipt,
    write_calibration_feasibility_acquisition_receipt,
    write_calibration_feasibility_acquisition_schemas,
)
from nas_core.domain.calibration_feasibility_audit import (
    load_calibration_feasibility_audit_plan,
    write_calibration_feasibility_audit_receipt,
    write_calibration_feasibility_audit_schemas,
)
from nas_core.domain.calibration_feasibility_pilot import (
    load_calibration_feasibility_pilot_plan,
    write_calibration_feasibility_pilot_receipt,
    write_calibration_feasibility_pilot_schemas,
)
from nas_core.domain.calibration_lineage import (
    load_calibration_lineage_receipt,
    write_calibration_lineage_receipt,
    write_calibration_lineage_schema,
)
from nas_core.domain.calibration_planning import (
    load_phase_one_internal_planning_bundle,
    load_standing_autonomy_authorization,
    write_calibration_planning_schemas,
)
from nas_core.domain.calibration_precision import (
    load_technical_replicate_precision_design,
    write_calibration_precision_schemas,
)
from nas_core.domain.calibration_readiness import (
    write_calibration_readiness_receipt,
    write_calibration_readiness_schema,
)
from nas_core.domain.calibration_scenario import (
    load_multi_objective_calibration_scenario,
    write_calibration_scenario_schemas,
    write_multi_objective_calibration_scenario_result,
)
from nas_core.domain.citation_access import (
    load_repository_access_batch_receipt,
    write_citation_access_check_queue,
    write_repository_access_batch_receipt,
)
from nas_core.domain.citation_chain import (
    CitationSeed,
    load_citation_chain_receipt,
    load_citation_cumulative_seed_receipt,
    load_citation_enrichment_receipt,
    load_citation_founder_packet_receipt,
    load_citation_prioritization_receipt,
    load_citation_recommendation_receipt,
    load_citation_screening_preparation_receipt,
    write_citation_chain_receipt,
    write_citation_cumulative_seed_receipt,
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
from nas_core.domain.citation_saturation import (
    write_citation_pass_closure_receipt,
)
from nas_core.domain.cohorts import (
    load_cohort_receipt,
    load_snapshot_receipt,
    write_cohort_schemas,
)
from nas_core.domain.discovery import load_phase_zero_artifacts, write_discovery_schemas
from nas_core.domain.evidence_amendment import (
    load_citation_access_queue_receipt,
    load_citation_pass_appraisal_queue_receipt,
    load_evidence_cap_amendment_activation_receipt,
    load_evidence_cap_amendment_approval,
    write_citation_pass_appraisal_queue_receipt,
    write_evidence_cap_amendment_activation_receipt,
)
from nas_core.domain.evidence_review import (
    load_evidence_review_progress,
    load_priority_evidence_set,
    write_evidence_review_schemas,
)
from nas_core.domain.evidence_synthesis import (
    load_authorized_saturated_evidence_synthesis,
    load_evidence_synthesis_founder_confirmation,
    load_saturated_evidence_synthesis_proposal,
    write_authorized_saturated_evidence_synthesis,
)
from nas_core.domain.feasibility import (
    write_metadata_feasibility_receipt,
    write_metadata_feasibility_schema,
)
from nas_core.domain.field_isolated_metadata import (
    load_field_isolated_metadata_authorization,
    load_field_isolated_metadata_receipt,
    write_field_isolated_metadata_receipt,
    write_field_isolated_metadata_schema,
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
from nas_core.domain.matrix_audit import (
    load_matrix_audit_plan,
    load_matrix_audit_receipt,
    write_matrix_audit_receipt,
    write_matrix_audit_schemas,
)
from nas_core.domain.method_dependency import (
    load_method_dependency_audit,
    load_method_route_activation,
    load_method_route_founder_decision,
    load_pam50_centroid_candidate,
    write_centroid_candidate_import_receipt,
    write_centroid_candidate_schemas,
    write_method_dependency_audit_schema,
    write_method_route_activation,
    write_method_route_schemas,
    write_pam50_centroid_candidate,
)
from nas_core.domain.numerical_conformance import (
    load_numerical_conformance_plan,
    write_numerical_conformance_receipt,
    write_numerical_conformance_schemas,
)
from nas_core.domain.platform_compatibility import (
    write_platform_compatibility_audit,
    write_platform_compatibility_schema,
)
from nas_core.domain.programs import OncologyProgramCharter, ResearchQuestionIntake, StudyRole
from nas_core.domain.prospective_calibration import (
    load_calibration_contact_revocation,
    load_prospective_calibration_design,
    load_prospective_calibration_founder_decision,
    load_prospective_calibration_planning_activation,
    write_prospective_calibration_authorization_schemas,
    write_prospective_calibration_planning_activation,
    write_prospective_calibration_schema,
)
from nas_core.domain.public_artifact import (
    load_public_artifact_plan,
    load_public_artifact_receipt,
    write_public_artifact_receipt,
    write_public_artifact_schemas,
)
from nas_core.domain.reference_construction import (
    load_reference_construction_plan,
    load_reference_construction_receipt,
    write_reference_construction_receipt,
    write_reference_construction_schemas,
)
from nas_core.domain.reference_development import (
    load_reference_development_protocol,
    write_reference_development_schema,
)
from nas_core.domain.reference_input import load_reference_input_founder_decision
from nas_core.domain.reference_metadata import (
    load_reference_metadata_plan,
    load_reference_metadata_receipt,
    write_reference_metadata_receipt,
    write_reference_metadata_schemas,
)
from nas_core.domain.reference_sensitivity import (
    load_reference_sensitivity_plan,
    load_reference_sensitivity_receipt,
    write_reference_sensitivity_receipt,
    write_reference_sensitivity_schemas,
)
from nas_core.domain.reliability import (
    load_reliability_method_inputs,
    load_reliability_specification,
    load_single_sample_expression,
    load_synthetic_expression_batch,
    load_synthetic_technical_error_panel,
    write_reliability_schema,
)
from nas_core.domain.research_completion import (
    load_study_completion_audit,
    write_study_completion_audit_schema,
)
from nas_core.domain.screening_confirmation import load_screening_confirmation
from nas_core.domain.snapshots import write_dataset_snapshot_schema
from nas_core.domain.storage_readiness import (
    load_storage_readiness_receipt,
    write_storage_readiness_receipt,
    write_storage_readiness_schema,
)
from nas_core.domain.survival import write_survival_schemas
from nas_core.domain.technical_calibration import (
    load_technical_calibration_plan,
    load_technical_calibration_scout,
    write_technical_calibration_schema,
    write_technical_calibration_scout_schema,
)
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.calibration_annotation import (
    CalibrationAnnotationAcquisitionService,
    CalibrationAnnotationResolutionService,
)
from nas_core.ingestion.calibration_feasibility_artifact import (
    CalibrationFeasibilityAcquisitionService,
)
from nas_core.ingestion.calibration_lineage import (
    CALIBRATION_LINEAGE_URLS,
    CalibrationLineageAuditService,
)
from nas_core.ingestion.field_isolated_metadata import (
    GDC_FILES_URL as FIELD_ISOLATED_GDC_FILES_URL,
)
from nas_core.ingestion.field_isolated_metadata import (
    GEO_EXPRESSION_URL as FIELD_ISOLATED_GEO_EXPRESSION_URL,
)
from nas_core.ingestion.field_isolated_metadata import (
    GEO_FAMILY_SOFT_URL as FIELD_ISOLATED_GEO_FAMILY_SOFT_URL,
)
from nas_core.ingestion.field_isolated_metadata import (
    FieldIsolatedMetadataAuditService,
    build_gdc_clinical_manifest_query,
    build_gdc_star_manifest_query,
)
from nas_core.ingestion.gdc import GDCSnapshotService, build_case_query
from nas_core.ingestion.matrix_audit import GSE81538MatrixAuditService
from nas_core.ingestion.metadata_feasibility import (
    ALLOWED_URLS as METADATA_AUDIT_URLS,
)
from nas_core.ingestion.metadata_feasibility import MetadataFeasibilityAuditService
from nas_core.ingestion.public_artifact import PublicArtifactAcquisitionService
from nas_core.ingestion.reference_metadata import GSE81538ReferenceMetadataService
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
from nas_core.retrieval.citation_saturation import CitationPassClosureService
from nas_core.retrieval.citation_screening import CitationScreeningPreparationService
from nas_core.retrieval.citation_seeds import CitationCumulativeSeedService
from nas_core.retrieval.ephemeral_appraisal import (
    ApprovedPublisherHtmlAppraisalProposalService,
    ApprovedPublisherPdfAppraisalProposalService,
    InstitutionalPdfAppraisalProposalService,
    PmcHtmlAppraisalProposalService,
    PmcOaiAppraisalProposalService,
)
from nas_core.retrieval.evidence_amendment import (
    CitationAccessInventoryService,
    CitationPassAppraisalQueueService,
    EvidenceCapAmendmentActivationService,
)
from nas_core.retrieval.evidence_synthesis import (
    SaturatedEvidenceSynthesisService,
)
from nas_core.retrieval.full_text import FullTextInventoryService
from nas_core.retrieval.full_text_retrieval import FullTextRetrievalService
from nas_core.retrieval.licensed_pdf import LicensedPdfImportService
from nas_core.retrieval.literature import (
    LiteratureSearchService,
    LiteratureSearchVerificationService,
)
from nas_core.retrieval.prioritization import DeterministicPrioritizationService
from nas_core.retrieval.publication_versions import (
    PublicationVersionReconciliationService,
)
from nas_core.retrieval.read_only_review import (
    ApprovedPublisherHtmlReadOnlyReviewService,
    ApprovedPublisherPdfReadOnlyReviewService,
    InstitutionalPdfReadOnlyReviewService,
    MedrxivReadOnlyReviewService,
    PmcOaiReadOnlyReviewService,
    PmcReadOnlyReviewService,
)
from nas_core.retrieval.reconciliation import InventoryReconciliationService
from nas_core.retrieval.review import ScreeningReviewService
from nas_core.retrieval.screening import ScreeningQueueService
from nas_core.retrieval.screening_confirmation import ScreeningConfirmationService
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import FileSystemObjectStore, get_object_store
from nas_core.storage.readiness import StorageReadinessService
from nas_core.workflows.analysis_plan import load_analysis_plan, write_analysis_plan_schema
from nas_core.workflows.program import (
    load_program_charter,
    load_research_question,
    write_model_schema,
)
from nas_core.workflows.research_completion import StudyCompletionAuditService
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
    storage_preflight = storage_commands.add_parser(
        "preflight",
        help="Inspect governed storage readiness without writing a probe",
    )
    storage_preflight.add_argument("--data-root", type=Path)
    storage_preflight.add_argument(
        "--minimum-required-bytes",
        type=int,
        required=True,
    )
    storage_preflight.add_argument("--code-revision", required=True)
    storage_preflight.add_argument("--output-path", type=Path)
    storage_preflight.add_argument(
        "--execute",
        action="store_true",
        help="Persist the non-mutating storage-readiness receipt",
    )
    storage_preflight_schema = storage_commands.add_parser(
        "preflight-schema",
        help="Write the storage-readiness receipt JSON Schema",
    )
    storage_preflight_schema.add_argument("path", type=Path)

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
    public_artifact = ingest_commands.add_parser(
        "public-artifact",
        help="Acquire one checksum-bound allowlisted public source artifact",
    )
    public_artifact.add_argument("plan_path", type=Path)
    public_artifact.add_argument("reference_protocol_path", type=Path)
    public_artifact.add_argument("storage_readiness_path", type=Path)
    public_artifact.add_argument("authorization_path", type=Path)
    public_artifact.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
    )
    public_artifact.add_argument("--data-root", type=Path, required=True)
    public_artifact.add_argument("--code-revision", required=True)
    public_artifact.add_argument("--output-path", type=Path)
    public_artifact.add_argument(
        "--execute",
        action="store_true",
        help="Download and immutably store the allowlisted public artifact",
    )
    public_artifact_schema = ingest_commands.add_parser(
        "public-artifact-schema",
        help="Write public-artifact acquisition plan and receipt JSON Schemas",
    )
    public_artifact_schema.add_argument("plan_path", type=Path)
    public_artifact_schema.add_argument("receipt_path", type=Path)
    calibration_feasibility = ingest_commands.add_parser(
        "calibration-feasibility",
        help="Acquire the checksum-bound excluded public calibration-feasibility set",
    )
    calibration_feasibility.add_argument("plan_path", type=Path)
    calibration_feasibility.add_argument("storage_readiness_path", type=Path)
    calibration_feasibility.add_argument("authorization_path", type=Path)
    calibration_feasibility.add_argument("calibration_readiness_path", type=Path)
    calibration_feasibility.add_argument(
        "--registry",
        type=Path,
        required=True,
    )
    calibration_feasibility.add_argument("--data-root", type=Path, required=True)
    calibration_feasibility.add_argument("--code-revision", required=True)
    calibration_feasibility.add_argument("--output-path", type=Path)
    calibration_feasibility.add_argument("--execute", action="store_true")
    calibration_feasibility_schema = ingest_commands.add_parser(
        "calibration-feasibility-schema",
        help="Write calibration-feasibility acquisition JSON Schemas",
    )
    calibration_feasibility_schema.add_argument("plan_path", type=Path)
    calibration_feasibility_schema.add_argument("receipt_path", type=Path)
    calibration_feasibility_audit = ingest_commands.add_parser(
        "calibration-feasibility-audit",
        help="Audit acquired public calibration-feasibility artifacts source by source",
    )
    calibration_feasibility_audit.add_argument("plan_path", type=Path)
    calibration_feasibility_audit.add_argument("acquisition_receipt_path", type=Path)
    calibration_feasibility_audit.add_argument("reliability_specification_path", type=Path)
    calibration_feasibility_audit.add_argument("--data-root", type=Path, required=True)
    calibration_feasibility_audit.add_argument("--code-revision", required=True)
    calibration_feasibility_audit.add_argument("--output-path", type=Path)
    calibration_feasibility_audit.add_argument("--execute", action="store_true")
    calibration_feasibility_audit_schema = ingest_commands.add_parser(
        "calibration-feasibility-audit-schema",
        help="Write calibration-feasibility audit JSON Schemas",
    )
    calibration_feasibility_audit_schema.add_argument("plan_path", type=Path)
    calibration_feasibility_audit_schema.add_argument("receipt_path", type=Path)
    calibration_feasibility_pilot = ingest_commands.add_parser(
        "calibration-feasibility-pilot",
        help="Run frozen source-isolated technical-replicate feasibility pilots",
    )
    calibration_feasibility_pilot.add_argument("plan_path", type=Path)
    calibration_feasibility_pilot.add_argument("acquisition_receipt_path", type=Path)
    calibration_feasibility_pilot.add_argument("feasibility_audit_receipt_path", type=Path)
    calibration_feasibility_pilot.add_argument(
        "annotation_resolution_receipt_path", type=Path
    )
    calibration_feasibility_pilot.add_argument(
        "annotation_mapping_receipt_path", type=Path
    )
    calibration_feasibility_pilot.add_argument(
        "reliability_specification_path", type=Path
    )
    calibration_feasibility_pilot.add_argument("--data-root", type=Path, required=True)
    calibration_feasibility_pilot.add_argument("--code-revision", required=True)
    calibration_feasibility_pilot.add_argument("--output-path", type=Path)
    calibration_feasibility_pilot.add_argument("--execute", action="store_true")
    calibration_feasibility_pilot_schema = ingest_commands.add_parser(
        "calibration-feasibility-pilot-schema",
        help="Write calibration-feasibility pilot JSON Schemas",
    )
    calibration_feasibility_pilot_schema.add_argument("plan_path", type=Path)
    calibration_feasibility_pilot_schema.add_argument("receipt_path", type=Path)
    calibration_annotation = ingest_commands.add_parser(
        "calibration-annotation-resolve",
        help="Resolve GSE130397 annotation and strandedness from official metadata",
    )
    calibration_annotation.add_argument("plan_path", type=Path)
    calibration_annotation.add_argument("feasibility_audit_receipt_path", type=Path)
    calibration_annotation.add_argument("lineage_receipt_path", type=Path)
    calibration_annotation.add_argument("--code-revision", required=True)
    calibration_annotation.add_argument("--output-path", type=Path)
    calibration_annotation.add_argument("--execute", action="store_true")
    calibration_annotation_schema = ingest_commands.add_parser(
        "calibration-annotation-resolve-schema",
        help="Write calibration annotation-resolution JSON Schemas",
    )
    calibration_annotation_schema.add_argument("plan_path", type=Path)
    calibration_annotation_schema.add_argument("receipt_path", type=Path)
    annotation_acquisition = ingest_commands.add_parser(
        "calibration-annotation-acquire",
        help="Acquire the frozen Ensembl annotation artifact",
    )
    annotation_acquisition.add_argument("plan_path", type=Path)
    annotation_acquisition.add_argument("annotation_resolution_path", type=Path)
    annotation_acquisition.add_argument("storage_readiness_path", type=Path)
    annotation_acquisition.add_argument("--registry", type=Path, required=True)
    annotation_acquisition.add_argument("--data-root", type=Path, required=True)
    annotation_acquisition.add_argument("--code-revision", required=True)
    annotation_acquisition.add_argument("--output-path", type=Path)
    annotation_acquisition.add_argument("--execute", action="store_true")
    annotation_acquisition_schema = ingest_commands.add_parser(
        "calibration-annotation-acquire-schema",
        help="Write annotation-acquisition JSON Schemas",
    )
    annotation_acquisition_schema.add_argument("plan_path", type=Path)
    annotation_acquisition_schema.add_argument("receipt_path", type=Path)
    annotation_mapping = ingest_commands.add_parser(
        "calibration-annotation-map",
        help="Map GSE130397 Ensembl-84 features to the historical PAM50 panel",
    )
    annotation_mapping.add_argument("plan_path", type=Path)
    annotation_mapping.add_argument("annotation_receipt_path", type=Path)
    annotation_mapping.add_argument("feasibility_receipt_path", type=Path)
    annotation_mapping.add_argument("feasibility_audit_receipt_path", type=Path)
    annotation_mapping.add_argument("reliability_specification_path", type=Path)
    annotation_mapping.add_argument("--data-root", type=Path, required=True)
    annotation_mapping.add_argument("--code-revision", required=True)
    annotation_mapping.add_argument("--output-path", type=Path)
    annotation_mapping.add_argument("--execute", action="store_true")
    annotation_mapping_schema = ingest_commands.add_parser(
        "calibration-annotation-map-schema",
        help="Write annotation-mapping JSON Schemas",
    )
    annotation_mapping_schema.add_argument("plan_path", type=Path)
    annotation_mapping_schema.add_argument("receipt_path", type=Path)
    matrix_audit = ingest_commands.add_parser(
        "matrix-audit",
        help="Audit the governed GSE81538 processed matrix without outcomes",
    )
    matrix_audit.add_argument("plan_path", type=Path)
    matrix_audit.add_argument("acquisition_receipt_path", type=Path)
    matrix_audit.add_argument("centroid_candidate_path", type=Path)
    matrix_audit.add_argument("reference_protocol_path", type=Path)
    matrix_audit.add_argument("--data-root", type=Path, required=True)
    matrix_audit.add_argument("--code-revision", required=True)
    matrix_audit.add_argument("--output-path", type=Path)
    matrix_audit.add_argument(
        "--execute",
        action="store_true",
        help="Stream and audit the stored matrix; never reads outcomes",
    )
    matrix_audit_schema = ingest_commands.add_parser(
        "matrix-audit-schema",
        help="Write GSE81538 matrix-audit plan and receipt JSON Schemas",
    )
    matrix_audit_schema.add_argument("plan_path", type=Path)
    matrix_audit_schema.add_argument("receipt_path", type=Path)
    reference_metadata = ingest_commands.add_parser(
        "reference-metadata",
        help="Select the field-isolated GSE81538 ER-balanced reference manifest",
    )
    reference_metadata.add_argument("plan_path", type=Path)
    reference_metadata.add_argument("acquisition_receipt_path", type=Path)
    reference_metadata.add_argument("matrix_audit_receipt_path", type=Path)
    reference_metadata.add_argument("founder_decision_path", type=Path)
    reference_metadata.add_argument("reference_protocol_path", type=Path)
    reference_metadata.add_argument("--data-root", type=Path, required=True)
    reference_metadata.add_argument("--code-revision", required=True)
    reference_metadata.add_argument("--output-path", type=Path)
    reference_metadata.add_argument(
        "--execute",
        action="store_true",
        help="Parse only approved metadata and freeze the external manifest",
    )
    reference_metadata_schema = ingest_commands.add_parser(
        "reference-metadata-schema",
        help="Write GSE81538 reference-metadata plan and receipt JSON Schemas",
    )
    reference_metadata_schema.add_argument("plan_path", type=Path)
    reference_metadata_schema.add_argument("receipt_path", type=Path)
    reference_construction = ingest_commands.add_parser(
        "reference-construct",
        help="Construct the outcome-blind GSE81538 50-gene median reference",
    )
    reference_construction.add_argument("plan_path", type=Path)
    reference_construction.add_argument("matrix_audit_receipt_path", type=Path)
    reference_construction.add_argument("reference_metadata_receipt_path", type=Path)
    reference_construction.add_argument("reference_protocol_path", type=Path)
    reference_construction.add_argument("centroid_candidate_path", type=Path)
    reference_construction.add_argument("--data-root", type=Path, required=True)
    reference_construction.add_argument("--code-revision", required=True)
    reference_construction.add_argument("--output-path", type=Path)
    reference_construction.add_argument(
        "--execute",
        action="store_true",
        help="Parse only selected PAM50 values and freeze the external reference",
    )
    reference_construction_schema = ingest_commands.add_parser(
        "reference-construct-schema",
        help="Write GSE81538 reference-construction plan and receipt JSON Schemas",
    )
    reference_construction_schema.add_argument("plan_path", type=Path)
    reference_construction_schema.add_argument("receipt_path", type=Path)
    reference_sensitivity = ingest_commands.add_parser(
        "reference-sensitivity",
        help="Run outcome-blind GSE81538 fixed-reference sensitivities",
    )
    reference_sensitivity.add_argument("plan_path", type=Path)
    reference_sensitivity.add_argument("matrix_audit_receipt_path", type=Path)
    reference_sensitivity.add_argument("reference_metadata_receipt_path", type=Path)
    reference_sensitivity.add_argument("construction_receipt_path", type=Path)
    reference_sensitivity.add_argument("reference_protocol_path", type=Path)
    reference_sensitivity.add_argument("centroid_candidate_path", type=Path)
    reference_sensitivity.add_argument("--data-root", type=Path, required=True)
    reference_sensitivity.add_argument("--code-revision", required=True)
    reference_sensitivity.add_argument("--output-path", type=Path)
    reference_sensitivity.add_argument(
        "--execute",
        action="store_true",
        help="Freeze outcome-blind reference diagnostics outside Git",
    )
    reference_sensitivity_schema = ingest_commands.add_parser(
        "reference-sensitivity-schema",
        help="Write reference-sensitivity plan and receipt JSON Schemas",
    )
    reference_sensitivity_schema.add_argument("plan_path", type=Path)
    reference_sensitivity_schema.add_argument("receipt_path", type=Path)

    feasibility = commands.add_parser(
        "feasibility",
        help="Run governed source-metadata feasibility audits",
    )
    feasibility_commands = feasibility.add_subparsers(
        dest="feasibility_command",
        required=True,
    )
    metadata_audit = feasibility_commands.add_parser(
        "metadata-audit",
        help="Audit TCGA-BRCA and GSE96058 source metadata without patient rows",
    )
    metadata_audit.add_argument(
        "--authorization",
        type=Path,
        required=True,
        help="Founder Phase 0 authorization artifact",
    )
    metadata_audit.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Immutable YAML receipt path",
    )
    metadata_audit.add_argument(
        "--execute",
        action="store_true",
        help="Execute five allowlisted source-level requests and write the receipt",
    )
    metadata_schema = feasibility_commands.add_parser(
        "schema",
        help="Write the canonical metadata-feasibility receipt JSON Schema",
    )
    metadata_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")
    field_isolated = feasibility_commands.add_parser(
        "field-isolated-metadata",
        help="Verify receptor completeness and PAM50 gene coverage without retention",
    )
    field_isolated.add_argument(
        "--authorization",
        type=Path,
        required=True,
        help="Founder field-isolated authorization confirmation YAML",
    )
    field_isolated.add_argument(
        "--packet",
        type=Path,
        required=True,
        help="Checksum-bound founder field-isolated review packet",
    )
    field_isolated.add_argument(
        "--prior-receipt",
        type=Path,
        help="Immutable audit 1.0.0 receipt required by amendment 1.0.1",
    )
    field_isolated.add_argument(
        "--software-revision",
        required=True,
        help="Exact 40-character Git revision containing the executed projection code",
    )
    field_isolated.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Immutable YAML receipt path",
    )
    field_isolated.add_argument(
        "--execute",
        action="store_true",
        help="Execute the allowlisted transient projections and write the receipt",
    )
    field_isolated_schema = feasibility_commands.add_parser(
        "field-isolated-schema",
        help="Write the canonical field-isolated metadata receipt JSON Schema",
    )
    field_isolated_schema.add_argument(
        "path",
        type=Path,
        help="Output path for the JSON Schema",
    )

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
    reliability_commands = reliability.add_subparsers(dest="reliability_command", required=True)
    reliability_validate = reliability_commands.add_parser(
        "validate", help="Validate a governed reliability specification"
    )
    reliability_validate.add_argument(
        "path", type=Path, help="Path to reliability_specification.yaml"
    )
    reliability_audit_validate = reliability_commands.add_parser(
        "audit-validate",
        help="Validate a method-dependency audit against governed study artifacts",
    )
    reliability_audit_validate.add_argument("audit_path", type=Path)
    reliability_audit_validate.add_argument("synthesis_path", type=Path)
    reliability_audit_validate.add_argument("specification_path", type=Path)
    reliability_audit_schema = reliability_commands.add_parser(
        "audit-schema",
        help="Write the method-dependency audit JSON Schema",
    )
    reliability_audit_schema.add_argument("path", type=Path)
    reliability_artifact_import = reliability_commands.add_parser(
        "artifact-import-candidate",
        help="Import a checksum-bound non-executable PAM50 centroid candidate",
    )
    reliability_artifact_import.add_argument("audit_path", type=Path)
    reliability_artifact_import.add_argument("package_path", type=Path)
    reliability_artifact_import.add_argument("--artifact-id", required=True)
    reliability_artifact_import.add_argument("--output-path", required=True, type=Path)
    reliability_artifact_import.add_argument("--receipt-path", required=True, type=Path)
    reliability_artifact_import.add_argument("--code-revision", required=True)
    reliability_artifact_import.add_argument(
        "--candidate-only",
        action="store_true",
        required=True,
        help="Acknowledge that import cannot approve or execute the method",
    )
    reliability_artifact_import.add_argument(
        "--execute",
        action="store_true",
        help="Persist the candidate artifact and import receipt",
    )
    reliability_artifact_schema = reliability_commands.add_parser(
        "artifact-schema",
        help="Write PAM50 candidate and import-receipt JSON Schemas",
    )
    reliability_artifact_schema.add_argument("candidate_path", type=Path)
    reliability_artifact_schema.add_argument("receipt_path", type=Path)
    reliability_route_activate = reliability_commands.add_parser(
        "route-activate",
        help="Activate a checksum-bound founder-selected method route",
    )
    reliability_route_activate.add_argument("decision_path", type=Path)
    reliability_route_activate.add_argument("audit_path", type=Path)
    reliability_route_activate.add_argument("decision_packet_path", type=Path)
    reliability_route_activate.add_argument("candidate_path", type=Path)
    reliability_route_activate.add_argument("calibration_plan_path", type=Path)
    reliability_route_activate.add_argument("--output-path", required=True, type=Path)
    reliability_route_activate.add_argument("--code-revision", required=True)
    reliability_route_activate.add_argument(
        "--execute",
        action="store_true",
        help="Persist the route activation receipt",
    )
    reliability_route_schema = reliability_commands.add_parser(
        "route-schema",
        help="Write method-route founder-decision and activation schemas",
    )
    reliability_route_schema.add_argument("decision_path", type=Path)
    reliability_route_schema.add_argument("activation_path", type=Path)
    reliability_calibration_validate = reliability_commands.add_parser(
        "calibration-plan-validate",
        help="Validate a technical-calibration acquisition plan",
    )
    reliability_calibration_validate.add_argument("plan_path", type=Path)
    reliability_calibration_validate.add_argument("audit_path", type=Path)
    reliability_calibration_validate.add_argument("candidate_path", type=Path)
    reliability_calibration_schema = reliability_commands.add_parser(
        "calibration-plan-schema",
        help="Write the technical-calibration acquisition-plan JSON Schema",
    )
    reliability_calibration_schema.add_argument("path", type=Path)
    reliability_calibration_scout_validate = reliability_commands.add_parser(
        "calibration-scout-validate",
        help="Validate a metadata-only calibration-source scout receipt",
    )
    reliability_calibration_scout_validate.add_argument("receipt_path", type=Path)
    reliability_calibration_scout_validate.add_argument("plan_path", type=Path)
    reliability_calibration_scout_schema = reliability_commands.add_parser(
        "calibration-scout-schema",
        help="Write the calibration-source scout-receipt JSON Schema",
    )
    reliability_calibration_scout_schema.add_argument("path", type=Path)
    reliability_calibration_lineage = reliability_commands.add_parser(
        "calibration-lineage-audit",
        help="Run a field-isolated GEO calibration-source lineage audit",
    )
    reliability_calibration_lineage.add_argument(
        "route_activation_path",
        type=Path,
    )
    reliability_calibration_lineage.add_argument(
        "--output-path",
        required=True,
        type=Path,
    )
    reliability_calibration_lineage.add_argument("--code-revision", required=True)
    reliability_calibration_lineage.add_argument(
        "--execute",
        action="store_true",
        help="Fetch official GEO metadata and persist only the aggregate receipt",
    )
    reliability_calibration_lineage_schema = reliability_commands.add_parser(
        "calibration-lineage-schema",
        help="Write the calibration lineage audit-receipt JSON Schema",
    )
    reliability_calibration_lineage_schema.add_argument("path", type=Path)
    reliability_calibration_precision = reliability_commands.add_parser(
        "calibration-precision-design",
        help="Calculate a hypothetical technical-replicate precision scenario",
    )
    reliability_calibration_precision.add_argument("design_path", type=Path)
    reliability_calibration_precision.add_argument(
        "--hypothetical-only",
        action="store_true",
        required=True,
        help="Acknowledge that the calculation cannot select a source or authorize a study",
    )
    reliability_calibration_precision_schema = reliability_commands.add_parser(
        "calibration-precision-schema",
        help="Write technical-replicate precision design and result schemas",
    )
    reliability_calibration_precision_schema.add_argument("design_path", type=Path)
    reliability_calibration_precision_schema.add_argument("result_path", type=Path)
    reliability_calibration_scenario = reliability_commands.add_parser(
        "calibration-scenario",
        help="Calculate a hypothetical multi-objective calibration scenario",
    )
    reliability_calibration_scenario.add_argument("scenario_path", type=Path)
    reliability_calibration_scenario.add_argument("planning_activation_path", type=Path)
    reliability_calibration_scenario.add_argument("--code-revision", required=True)
    reliability_calibration_scenario.add_argument("--output-path", type=Path)
    reliability_calibration_scenario.add_argument(
        "--execute",
        action="store_true",
        help="Persist the hypothetical planning result",
    )
    reliability_calibration_scenario.add_argument(
        "--hypothetical-only",
        action="store_true",
        required=True,
        help="Acknowledge that the result is not an approved sample size",
    )
    reliability_calibration_scenario_schema = reliability_commands.add_parser(
        "calibration-scenario-schema",
        help="Write multi-objective calibration scenario and result schemas",
    )
    reliability_calibration_scenario_schema.add_argument("scenario_path", type=Path)
    reliability_calibration_scenario_schema.add_argument("result_path", type=Path)
    reliability_calibration_planning = reliability_commands.add_parser(
        "calibration-planning-validate",
        help="Validate the standing-autonomy Phase 1 planning bundle",
    )
    reliability_calibration_planning.add_argument("bundle_path", type=Path)
    reliability_calibration_planning.add_argument("authorization_path", type=Path)
    reliability_calibration_planning.add_argument("planning_decision_path", type=Path)
    reliability_calibration_planning.add_argument("planning_activation_path", type=Path)
    reliability_calibration_planning_schema = reliability_commands.add_parser(
        "calibration-planning-schema",
        help="Write standing-autonomy and Phase 1 planning JSON Schemas",
    )
    reliability_calibration_planning_schema.add_argument(
        "authorization_schema_path",
        type=Path,
    )
    reliability_calibration_planning_schema.add_argument(
        "bundle_schema_path",
        type=Path,
    )
    reliability_calibration_readiness = reliability_commands.add_parser(
        "calibration-readiness",
        help="Reconcile technical-calibration paths and authorize public feasibility only",
    )
    reliability_calibration_readiness.add_argument("authorization_path", type=Path)
    reliability_calibration_readiness.add_argument("acquisition_plan_path", type=Path)
    reliability_calibration_readiness.add_argument("source_scout_path", type=Path)
    reliability_calibration_readiness.add_argument("lineage_receipt_path", type=Path)
    reliability_calibration_readiness.add_argument("prospective_design_path", type=Path)
    reliability_calibration_readiness.add_argument("planning_bundle_path", type=Path)
    reliability_calibration_readiness.add_argument("contact_revocation_path", type=Path)
    reliability_calibration_readiness.add_argument("reference_receipt_path", type=Path)
    reliability_calibration_readiness.add_argument("sensitivity_receipt_path", type=Path)
    reliability_calibration_readiness.add_argument("--code-revision", required=True)
    reliability_calibration_readiness.add_argument("--output-path", type=Path)
    reliability_calibration_readiness.add_argument(
        "--execute",
        action="store_true",
        help="Persist the internal readiness receipt",
    )
    reliability_calibration_readiness_schema = reliability_commands.add_parser(
        "calibration-readiness-schema",
        help="Write the technical-calibration readiness JSON Schema",
    )
    reliability_calibration_readiness_schema.add_argument("path", type=Path)
    reliability_platform_compatibility = reliability_commands.add_parser(
        "platform-compatibility-audit",
        help="Audit platform compatibility from existing governed evidence",
    )
    reliability_platform_compatibility.add_argument("bundle_path", type=Path)
    reliability_platform_compatibility.add_argument("metadata_receipt_path", type=Path)
    reliability_platform_compatibility.add_argument("centroid_candidate_path", type=Path)
    reliability_platform_compatibility.add_argument(
        "reliability_specification_path",
        type=Path,
    )
    reliability_platform_compatibility.add_argument("--code-revision", required=True)
    reliability_platform_compatibility.add_argument("--output-path", type=Path)
    reliability_platform_compatibility.add_argument(
        "--execute",
        action="store_true",
        help="Persist the immutable platform audit receipt",
    )
    reliability_platform_compatibility_schema = reliability_commands.add_parser(
        "platform-compatibility-schema",
        help="Write the platform-compatibility audit JSON Schema",
    )
    reliability_platform_compatibility_schema.add_argument("path", type=Path)
    reliability_numerical_conformance = reliability_commands.add_parser(
        "numerical-conformance",
        help="Run the independent synthetic numerical-conformance suite",
    )
    reliability_numerical_conformance.add_argument("plan_path", type=Path)
    reliability_numerical_conformance.add_argument("centroid_candidate_path", type=Path)
    reliability_numerical_conformance.add_argument(
        "reliability_specification_path",
        type=Path,
    )
    reliability_numerical_conformance.add_argument("--code-revision", required=True)
    reliability_numerical_conformance.add_argument("--output-path", type=Path)
    reliability_numerical_conformance.add_argument(
        "--execute",
        action="store_true",
        help="Persist the immutable numerical-conformance receipt",
    )
    reliability_numerical_conformance_schema = reliability_commands.add_parser(
        "numerical-conformance-schema",
        help="Write numerical-conformance plan and receipt JSON Schemas",
    )
    reliability_numerical_conformance_schema.add_argument("plan_path", type=Path)
    reliability_numerical_conformance_schema.add_argument("receipt_path", type=Path)
    reliability_reference_development = reliability_commands.add_parser(
        "reference-development-validate",
        help="Validate the outcome-blind platform-reference development protocol",
    )
    reliability_reference_development.add_argument("protocol_path", type=Path)
    reliability_reference_development.add_argument("authorization_path", type=Path)
    reliability_reference_development.add_argument("platform_audit_path", type=Path)
    reliability_reference_development.add_argument(
        "numerical_conformance_path",
        type=Path,
    )
    reliability_reference_development.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
    )
    reliability_reference_development_schema = reliability_commands.add_parser(
        "reference-development-schema",
        help="Write the reference-development protocol JSON Schema",
    )
    reliability_reference_development_schema.add_argument("path", type=Path)
    reliability_prospective_calibration = reliability_commands.add_parser(
        "prospective-calibration-validate",
        help="Validate a nonexecuting prospective Route C calibration design",
    )
    reliability_prospective_calibration.add_argument("design_path", type=Path)
    reliability_prospective_calibration.add_argument("route_activation_path", type=Path)
    reliability_prospective_calibration.add_argument("acquisition_plan_path", type=Path)
    reliability_prospective_calibration.add_argument("contact_revocation_path", type=Path)
    reliability_prospective_calibration_schema = reliability_commands.add_parser(
        "prospective-calibration-schema",
        help="Write the prospective calibration experiment-design JSON Schema",
    )
    reliability_prospective_calibration_schema.add_argument("path", type=Path)
    reliability_prospective_calibration_activate = reliability_commands.add_parser(
        "prospective-calibration-activate",
        help="Activate founder-approved internal prospective-calibration planning",
    )
    reliability_prospective_calibration_activate.add_argument(
        "decision_path",
        type=Path,
    )
    reliability_prospective_calibration_activate.add_argument(
        "design_path",
        type=Path,
    )
    reliability_prospective_calibration_activate.add_argument(
        "decision_packet_path",
        type=Path,
    )
    reliability_prospective_calibration_activate.add_argument(
        "--output-path",
        required=True,
        type=Path,
    )
    reliability_prospective_calibration_activate.add_argument(
        "--code-revision",
        required=True,
    )
    reliability_prospective_calibration_activate.add_argument(
        "--execute",
        action="store_true",
        help="Persist the planning activation receipt",
    )
    reliability_prospective_authorization_schema = reliability_commands.add_parser(
        "prospective-calibration-authorization-schema",
        help="Write founder-decision and planning-activation JSON Schemas",
    )
    reliability_prospective_authorization_schema.add_argument(
        "decision_path",
        type=Path,
    )
    reliability_prospective_authorization_schema.add_argument(
        "activation_path",
        type=Path,
    )
    reliability_schema = reliability_commands.add_parser(
        "schema", help="Write the canonical reliability JSON Schema"
    )
    reliability_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")
    reliability_synthetic_score = reliability_commands.add_parser(
        "synthetic-score",
        help="Exercise the single-sample reliability kernel on a synthetic fixture",
    )
    reliability_synthetic_score.add_argument("specification_path", type=Path)
    reliability_synthetic_score.add_argument("method_path", type=Path)
    reliability_synthetic_score.add_argument("sample_path", type=Path)
    reliability_synthetic_score.add_argument(
        "--technical-error-panel",
        type=Path,
        help="Optional explicit synthetic technical-error perturbation panel",
    )
    reliability_synthetic_score.add_argument(
        "--synthetic-only",
        action="store_true",
        required=True,
        help="Acknowledge that the input is synthetic and the result has no scientific use",
    )
    reliability_synthetic_batch_score = reliability_commands.add_parser(
        "synthetic-batch-score",
        help="Prove independent single-sample execution within a synthetic batch",
    )
    reliability_synthetic_batch_score.add_argument("specification_path", type=Path)
    reliability_synthetic_batch_score.add_argument("method_path", type=Path)
    reliability_synthetic_batch_score.add_argument("batch_path", type=Path)
    reliability_synthetic_batch_score.add_argument(
        "--technical-error-panel",
        type=Path,
        help="Optional explicit synthetic technical-error perturbation panel",
    )
    reliability_synthetic_batch_score.add_argument(
        "--synthetic-only",
        action="store_true",
        required=True,
        help="Acknowledge that every batch input is synthetic and non-scientific",
    )

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
    citation_retrieve.add_argument("inventory_path", type=Path, nargs="?")
    citation_retrieve.add_argument(
        "--seed-receipt",
        type=Path,
        help="Verified cumulative seed receipt for citation pass 2 or later",
    )
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
    citation_prepare.add_argument(
        "--prior-decision-receipt",
        action="append",
        default=[],
        type=Path,
        help="Completed founder decision ledger for a prior citation pass; repeatable",
    )
    citation_prepare.add_argument("--code-revision", required=True)
    citation_prepare.add_argument("--receipt-output", required=True, type=Path)
    citation_prepare.add_argument(
        "--execute",
        action="store_true",
        help="Persist the verified deduplication inventory and screening candidate set",
    )
    citation_seed_build = evidence_review_commands.add_parser(
        "citation-seed-build",
        help="Build the cumulative founder-included seed set for the next citation pass",
    )
    citation_seed_build.add_argument("direct_inventory", type=Path)
    citation_seed_build.add_argument("amendment_activation", type=Path)
    citation_seed_build.add_argument(
        "--prior-pass-queue-receipt",
        action="append",
        default=[],
        type=Path,
        help=(
            "Founder-authorized appraisal queue for citation pass 2+; "
            "repeat once per pass in ascending pass order"
        ),
    )
    citation_seed_build.add_argument("--next-pass-number", required=True, type=int)
    citation_seed_build.add_argument("--code-revision", required=True)
    citation_seed_build.add_argument("--receipt-output", required=True, type=Path)
    citation_seed_build.add_argument(
        "--execute",
        action="store_true",
        help="Verify inputs and persist the immutable cumulative seed object",
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
    citation_confirm_single = evidence_review_commands.add_parser(
        "citation-confirm-single",
        help="Freeze a complete founder decision ledger from one zero-pending packet",
    )
    citation_confirm_single.add_argument("packet_receipt", type=Path)
    citation_confirm_single.add_argument("packet", type=Path)
    citation_confirm_single.add_argument("appendix", type=Path)
    citation_confirm_single.add_argument("confirmation", type=Path)
    citation_confirm_single.add_argument("--code-revision", required=True)
    citation_confirm_single.add_argument("--receipt-output", required=True, type=Path)
    citation_confirm_single.add_argument(
        "--execute",
        action="store_true",
        help="Persist final founder decisions after exact single-packet confirmation",
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
    citation_route = evidence_review_commands.add_parser(
        "citation-route-inclusions",
        help="Route a later citation pass under the active uncapped amendment",
    )
    citation_route.add_argument("decision_receipt", type=Path)
    citation_route.add_argument("reconciliation_receipt", type=Path)
    citation_route.add_argument("active_amendment_receipt", type=Path)
    citation_route.add_argument("--code-revision", required=True)
    citation_route.add_argument("--receipt-output", required=True, type=Path)
    citation_route.add_argument(
        "--execute",
        action="store_true",
        help="Persist the later-pass appraisal queue and routing receipt",
    )
    citation_close = evidence_review_commands.add_parser(
        "citation-close-pass",
        help="Derive complete citation-pass saturation accounting from receipts",
    )
    citation_close.add_argument("citation_receipt", type=Path)
    citation_close.add_argument("preparation_receipt", type=Path)
    citation_close.add_argument("decision_receipt", type=Path)
    citation_close.add_argument("reconciliation_receipt", type=Path)
    citation_close.add_argument("queue_receipt", type=Path)
    citation_close.add_argument("--access-inventory", type=Path)
    citation_close.add_argument("--appraisal-progress", type=Path)
    citation_close.add_argument(
        "--prior-appraisal",
        action="append",
        default=[],
        type=Path,
        help="Locked appraisal reused by this citation pass; repeatable",
    )
    citation_close.add_argument("--code-revision", required=True)
    citation_close.add_argument("--receipt-output", required=True, type=Path)
    citation_close.add_argument(
        "--execute",
        action="store_true",
        help="Write the verified citation-pass closure receipt",
    )
    synthesis_validate = evidence_review_commands.add_parser(
        "synthesis-validate",
        help="Validate a non-authoritative claim synthesis against saturated evidence",
    )
    synthesis_validate.add_argument("progress", type=Path)
    synthesis_validate.add_argument("proposal", type=Path)
    synthesis_validate.add_argument(
        "--appraisal-dir",
        action="append",
        default=[],
        type=Path,
        help="Directory of locked appraisals; repeatable",
    )
    synthesis_validate.add_argument(
        "--appraisal",
        action="append",
        default=[],
        type=Path,
        help="Individual locked appraisal reused by the active review; repeatable",
    )
    synthesis_authorize = evidence_review_commands.add_parser(
        "synthesis-authorize",
        help="Authorize a checksum-bound saturated evidence synthesis",
    )
    synthesis_authorize.add_argument("progress", type=Path)
    synthesis_authorize.add_argument("proposal", type=Path)
    synthesis_authorize.add_argument("confirmation", type=Path)
    synthesis_authorize.add_argument(
        "--appraisal-dir",
        action="append",
        default=[],
        type=Path,
        help="Directory of locked appraisals; repeatable",
    )
    synthesis_authorize.add_argument(
        "--appraisal",
        action="append",
        default=[],
        type=Path,
        help="Individual locked appraisal reused by the active review; repeatable",
    )
    synthesis_authorize.add_argument("--output-path", required=True, type=Path)
    synthesis_authorize.add_argument(
        "--execute",
        action="store_true",
        help="Persist the founder-authorized working synthesis",
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
    full_text_inventory.add_argument("receipt", type=Path, help="Verified screening queue receipt")
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
    citation_full_text_batch.add_argument("--batch-receipt-output", required=True, type=Path)
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
        "--appraisal-source-receipt-dir",
        action="append",
        type=Path,
        help=(
            "Directory containing a verified delayed-appraisal source receipt; "
            "repeat for additional batches"
        ),
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
    citation_appraisal_authorize.add_argument(
        "--version-link-proposal-dir",
        type=Path,
        help="Directory containing checksum-confirmed publication-version proposals",
    )
    citation_appraisal_authorize.add_argument(
        "--version-link-output-dir",
        type=Path,
        help="Directory for founder-authorized publication-version decisions",
    )
    citation_version_reconcile = literature_commands.add_parser(
        "citation-publication-version-reconcile",
        help="Count appraised publication families without double-counting versions",
    )
    citation_version_reconcile.add_argument(
        "--appraisal-dir",
        action="append",
        required=True,
        type=Path,
        help="Appraisal directory; repeat for each evidence workspace",
    )
    citation_version_reconcile.add_argument(
        "--version-link-dir",
        required=True,
        type=Path,
        help="Directory containing founder-authorized publication-version links",
    )
    citation_version_reconcile.add_argument(
        "--output-path",
        required=True,
        type=Path,
    )
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
    citation_read_only_review.add_argument("--receipt-output", required=True, type=Path)
    citation_read_only_review.add_argument(
        "--execute",
        action="store_true",
        help="Read the PMC page in memory; never persist article content",
    )
    citation_pmc_oai_review = literature_commands.add_parser(
        "citation-pmc-oai-read-only-review",
        help="Review canonical PMC OAI article XML without storing it",
    )
    citation_pmc_oai_review.add_argument("inventory", type=Path)
    citation_pmc_oai_review.add_argument("screening_id")
    citation_pmc_oai_review.add_argument("--code-revision", required=True)
    citation_pmc_oai_review.add_argument("--access-basis", required=True)
    citation_pmc_oai_review.add_argument("--observed-rights", required=True)
    citation_pmc_oai_review.add_argument("--rights-url", required=True)
    citation_pmc_oai_review.add_argument("--receipt-output", required=True, type=Path)
    citation_pmc_oai_review.add_argument(
        "--execute",
        action="store_true",
        help="Canonicalize article XML in memory; never persist article content",
    )
    citation_pmc_oai_proposal = literature_commands.add_parser(
        "citation-pmc-oai-appraisal-propose",
        help="Verify a bounded proposal against canonical PMC OAI article XML",
    )
    citation_pmc_oai_proposal.add_argument("inventory", type=Path)
    citation_pmc_oai_proposal.add_argument("screening_id")
    citation_pmc_oai_proposal.add_argument("review_receipt", type=Path)
    citation_pmc_oai_proposal.add_argument("draft", type=Path)
    citation_pmc_oai_proposal.add_argument("--proposal-output", required=True, type=Path)
    citation_pmc_oai_proposal.add_argument(
        "--execute",
        action="store_true",
        help="Verify canonical XML in memory and retain only the proposal",
    )
    citation_pmc_html_proposal = literature_commands.add_parser(
        "citation-pmc-html-appraisal-propose",
        help="Verify a bounded proposal against an exact PMC HTML article",
    )
    citation_pmc_html_proposal.add_argument("inventory", type=Path)
    citation_pmc_html_proposal.add_argument("screening_id")
    citation_pmc_html_proposal.add_argument("review_receipt", type=Path)
    citation_pmc_html_proposal.add_argument("draft", type=Path)
    citation_pmc_html_proposal.add_argument("--proposal-output", required=True, type=Path)
    citation_pmc_html_proposal.add_argument(
        "--execute",
        action="store_true",
        help="Verify PMC HTML in memory and retain only the proposal",
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
    citation_medrxiv_read_only_review.add_argument("--receipt-output", required=True, type=Path)
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
    citation_institutional_pdf_review.add_argument("--receipt-output", required=True, type=Path)
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
    citation_institutional_pdf_proposal.add_argument("--proposal-output", required=True, type=Path)
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
    citation_publisher_pdf_review.add_argument("--receipt-output", required=True, type=Path)
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
    citation_publisher_pdf_proposal.add_argument("--proposal-output", required=True, type=Path)
    citation_publisher_pdf_proposal.add_argument(
        "--execute",
        action="store_true",
        help="Verify the draft against PDF bytes and retain only the proposal",
    )
    citation_publisher_html_review = literature_commands.add_parser(
        "citation-publisher-html-read-only-review",
        help="Review canonical allowlisted publisher HTML without storing it",
    )
    citation_publisher_html_review.add_argument("inventory", type=Path)
    citation_publisher_html_review.add_argument("screening_id")
    citation_publisher_html_review.add_argument("--code-revision", required=True)
    citation_publisher_html_review.add_argument("--access-basis", required=True)
    citation_publisher_html_review.add_argument("--observed-rights", required=True)
    citation_publisher_html_review.add_argument("--rights-url", required=True)
    citation_publisher_html_review.add_argument("--receipt-output", required=True, type=Path)
    citation_publisher_html_review.add_argument(
        "--execute",
        action="store_true",
        help="Canonicalize publisher HTML in memory; never persist article content",
    )
    citation_publisher_html_proposal = literature_commands.add_parser(
        "citation-publisher-html-appraisal-propose",
        help="Verify a bounded proposal against canonical allowlisted publisher HTML",
    )
    citation_publisher_html_proposal.add_argument("inventory", type=Path)
    citation_publisher_html_proposal.add_argument("screening_id")
    citation_publisher_html_proposal.add_argument("review_receipt", type=Path)
    citation_publisher_html_proposal.add_argument("draft", type=Path)
    citation_publisher_html_proposal.add_argument("--proposal-output", required=True, type=Path)
    citation_publisher_html_proposal.add_argument(
        "--execute",
        action="store_true",
        help="Verify canonical HTML in memory and retain only the proposal",
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
    full_text_import_pdf.add_argument("receipt", type=Path, help="Verified screening queue receipt")
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
    full_text_import_pdf.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
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
    study_completion_validate = study_commands.add_parser(
        "completion-validate",
        help="Validate a phase-by-phase research completion audit",
    )
    study_completion_validate.add_argument("audit_path", type=Path)
    study_completion_validate.add_argument("study_root", type=Path)
    study_completion_validate.add_argument("pipeline_path", type=Path)
    study_completion_schema = study_commands.add_parser(
        "completion-schema",
        help="Write the research completion-audit JSON Schema",
    )
    study_completion_schema.add_argument("path", type=Path)
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

    if args.command == "storage" and args.storage_command == "preflight":
        preflight_root = args.data_root or get_settings().data_root
        storage_receipt = StorageReadinessService().inspect(
            preflight_root,
            minimum_required_bytes=args.minimum_required_bytes,
            code_revision=args.code_revision,
            checked_at=datetime.now(UTC),
        )
        if not args.execute:
            print(
                "Storage preflight completed: "
                f"decision={storage_receipt.decision.value}; "
                f"available_bytes={storage_receipt.available_bytes}; "
                f"blockers={len(storage_receipt.blockers)}"
            )
            print("Dry run only; no readiness receipt was written.")
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        write_storage_readiness_receipt(args.output_path, storage_receipt)
        print(f"Wrote storage readiness receipt: {args.output_path}")
        return 0

    if args.command == "storage" and args.storage_command == "preflight-schema":
        write_storage_readiness_schema(args.path)
        print(f"Wrote storage readiness schema: {args.path}")
        return 0

    if args.command == "plan" and args.plan_command == "validate":
        plan = load_analysis_plan(args.path, registry=SourceRegistry.from_yaml(args.registry))
        print(
            f"Analysis plan is valid: {plan.study_id} "
            f"v{plan.protocol_version} ({plan.status.value})"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "audit-schema":
        write_method_dependency_audit_schema(args.path)
        print(f"Wrote method dependency audit schema: {args.path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "artifact-import-candidate":
        artifact_audit = load_method_dependency_audit(args.audit_path)
        artifact_service = Pam50CandidateImportService()
        centroid_candidate = artifact_service.parse(
            artifact_audit,
            args.package_path,
            artifact_id=args.artifact_id,
        )
        if not args.execute:
            print(
                f"PAM50 candidate verified: {centroid_candidate.artifact_id}, "
                f"{len(centroid_candidate.centroids)} subtypes, "
                f"{len(centroid_candidate.gene_order)} genes, "
                "zero execution authorization"
            )
            print("Dry run only; no candidate artifact or receipt was written.")
            return 0
        if args.output_path.exists() or args.receipt_path.exists():
            raise FileExistsError("candidate output and receipt paths must both be new")
        write_pam50_centroid_candidate(args.output_path, centroid_candidate)
        import_receipt = artifact_service.receipt(
            artifact_audit,
            audit_path=args.audit_path,
            candidate=centroid_candidate,
            candidate_path=args.output_path,
            code_revision=args.code_revision,
            imported_at=datetime.now(UTC),
        )
        write_centroid_candidate_import_receipt(
            args.receipt_path,
            import_receipt,
        )
        print(f"Imported non-executable PAM50 candidate: {args.output_path}")
        print(f"Wrote candidate import receipt: {args.receipt_path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "artifact-schema":
        write_centroid_candidate_schemas(
            args.candidate_path,
            args.receipt_path,
        )
        print(f"Wrote centroid candidate schemas: {args.candidate_path}, {args.receipt_path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "route-activate":
        route_decision = load_method_route_founder_decision(args.decision_path)
        route_audit = load_method_dependency_audit(args.audit_path)
        route_candidate = load_pam50_centroid_candidate(args.candidate_path)
        route_calibration_plan = load_technical_calibration_plan(args.calibration_plan_path)
        route_activation = MethodRouteActivationService().activate(
            route_decision,
            route_audit,
            route_candidate,
            route_calibration_plan,
            decision_path=args.decision_path,
            audit_path=args.audit_path,
            decision_packet_path=args.decision_packet_path,
            candidate_path=args.candidate_path,
            calibration_plan_path=args.calibration_plan_path,
            code_revision=args.code_revision,
            activated_at=datetime.now(UTC),
        )
        if not args.execute:
            print(
                f"Method route verified: {route_activation.selected_route_id}; "
                f"status={route_activation.activation_status.value}; "
                "zero data access or execution authorization"
            )
            print("Dry run only; no route activation receipt was written.")
            return 0
        if args.output_path.exists():
            raise FileExistsError("route activation output path must be new")
        write_method_route_activation(args.output_path, route_activation)
        print(f"Activated governed method route: {args.output_path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "route-schema":
        write_method_route_schemas(
            args.decision_path,
            args.activation_path,
        )
        print(f"Wrote method route schemas: {args.decision_path}, {args.activation_path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-plan-validate":
        calibration_plan = load_technical_calibration_plan(args.plan_path)
        calibration_audit = load_method_dependency_audit(args.audit_path)
        calibration_candidate = load_pam50_centroid_candidate(args.candidate_path)
        TechnicalCalibrationPlanService().validate(
            calibration_plan,
            calibration_audit,
            calibration_candidate,
            audit_path=args.audit_path,
            candidate_path=args.candidate_path,
        )
        print(
            "Technical-calibration acquisition plan is valid: "
            f"{calibration_plan.study_id} v{calibration_plan.plan_version}; "
            f"{len(calibration_plan.source_candidates)} sources; "
            "zero data access or execution authorization"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-plan-schema":
        write_technical_calibration_schema(args.path)
        print(f"Wrote technical-calibration schema: {args.path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-scout-validate":
        calibration_scout = load_technical_calibration_scout(args.receipt_path)
        calibration_plan = load_technical_calibration_plan(args.plan_path)
        TechnicalCalibrationPlanService().validate_scout(
            calibration_scout,
            calibration_plan,
            plan_path=args.plan_path,
        )
        print(
            "Technical-calibration scout receipt is valid: "
            f"{len(calibration_scout.findings)} new findings; "
            "zero data access, source selection, or external contact"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-scout-schema":
        write_technical_calibration_scout_schema(args.path)
        print(f"Wrote technical-calibration scout schema: {args.path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-lineage-audit":
        if not args.execute:
            print(json.dumps(CALIBRATION_LINEAGE_URLS, indent=2, sort_keys=True))
            print("Dry run only; no metadata was fetched or stored.")
            return 0
        if args.output_path.exists():
            raise FileExistsError("calibration lineage output path must be new")
        lineage_activation = load_method_route_activation(args.route_activation_path)
        lineage_receipt = CalibrationLineageAuditService().execute(
            route_activation=lineage_activation,
            route_activation_path=args.route_activation_path,
            code_revision=args.code_revision,
            executed_at=datetime.now(UTC),
        )
        write_calibration_lineage_receipt(
            args.output_path,
            lineage_receipt,
        )
        print(f"Wrote calibration lineage audit receipt: {args.output_path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-lineage-schema":
        write_calibration_lineage_schema(args.path)
        print(f"Wrote calibration lineage audit schema: {args.path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-precision-design":
        precision_design = load_technical_replicate_precision_design(args.design_path)
        precision_result = TechnicalReplicatePrecisionService().calculate(precision_design)
        print(precision_result.model_dump_json(indent=2))
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-precision-schema":
        write_calibration_precision_schemas(
            args.design_path,
            args.result_path,
        )
        print(f"Wrote calibration precision schemas: {args.design_path}, {args.result_path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-scenario":
        calibration_scenario = load_multi_objective_calibration_scenario(args.scenario_path)
        calibration_planning_activation = load_prospective_calibration_planning_activation(
            args.planning_activation_path
        )
        calibration_scenario_result = MultiObjectiveCalibrationScenarioService().calculate(
            calibration_scenario,
            calibration_planning_activation,
            scenario_path=args.scenario_path,
            activation_path=args.planning_activation_path,
            code_revision=args.code_revision,
            calculated_at=datetime.now(UTC),
        )
        if args.execute:
            if args.output_path is None:
                raise SystemExit("--output-path is required with --execute")
            if args.output_path.exists():
                raise FileExistsError("calibration scenario output path must be new")
            write_multi_objective_calibration_scenario_result(
                args.output_path,
                calibration_scenario_result,
            )
            print(f"Wrote hypothetical calibration scenario result: {args.output_path}")
            return 0
        print(calibration_scenario_result.model_dump_json(indent=2))
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-scenario-schema":
        write_calibration_scenario_schemas(
            args.scenario_path,
            args.result_path,
        )
        print(f"Wrote calibration scenario schemas: {args.scenario_path}, {args.result_path}")
        return 0

    if (
        args.command == "reliability"
        and args.reliability_command == "calibration-planning-validate"
    ):
        phase_one_bundle = load_phase_one_internal_planning_bundle(args.bundle_path)
        standing_authorization = load_standing_autonomy_authorization(args.authorization_path)
        CalibrationPlanningService().validate(
            phase_one_bundle,
            standing_authorization,
            authorization_path=args.authorization_path,
            planning_decision_path=args.planning_decision_path,
            planning_activation_path=args.planning_activation_path,
        )
        print(
            "Phase 1 internal planning bundle is valid: "
            f"{phase_one_bundle.study_id} v{phase_one_bundle.plan_version}; "
            f"pilot={phase_one_bundle.excluded_pilot.attempted_pairs} pairs; "
            "zero external or executing authority"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-planning-schema":
        write_calibration_planning_schemas(
            args.authorization_schema_path,
            args.bundle_schema_path,
        )
        print(
            "Wrote calibration planning schemas: "
            f"{args.authorization_schema_path}, {args.bundle_schema_path}"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-readiness":
        readiness_receipt = TechnicalCalibrationReadinessService().assess(
            load_standing_autonomy_authorization(args.authorization_path),
            load_technical_calibration_plan(args.acquisition_plan_path),
            load_technical_calibration_scout(args.source_scout_path),
            load_calibration_lineage_receipt(args.lineage_receipt_path),
            load_prospective_calibration_design(args.prospective_design_path),
            load_phase_one_internal_planning_bundle(args.planning_bundle_path),
            load_calibration_contact_revocation(args.contact_revocation_path),
            load_reference_construction_receipt(args.reference_receipt_path),
            load_reference_sensitivity_receipt(args.sensitivity_receipt_path),
            authorization_path=args.authorization_path,
            acquisition_path=args.acquisition_plan_path,
            scout_path=args.source_scout_path,
            lineage_path=args.lineage_receipt_path,
            design_path=args.prospective_design_path,
            planning_path=args.planning_bundle_path,
            revocation_path=args.contact_revocation_path,
            reference_path=args.reference_receipt_path,
            sensitivity_path=args.sensitivity_receipt_path,
            code_revision=args.code_revision,
        )
        if not args.execute:
            print(
                "Technical calibration readiness assessed: "
                f"{readiness_receipt.decision.value}; "
                f"public_feasibility={len(readiness_receipt.public_feasibility_source_ids)}; "
                "dry run only"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        write_calibration_readiness_receipt(args.output_path, readiness_receipt)
        print(
            "Wrote technical calibration readiness: "
            f"{readiness_receipt.decision.value}; "
            f"primary_ready={readiness_receipt.primary_calibration_ready}"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "calibration-readiness-schema":
        write_calibration_readiness_schema(args.path)
        print(f"Wrote technical-calibration readiness schema: {args.path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "platform-compatibility-audit":
        platform_bundle = load_phase_one_internal_planning_bundle(args.bundle_path)
        platform_metadata = load_field_isolated_metadata_receipt(args.metadata_receipt_path)
        platform_candidate = load_pam50_centroid_candidate(args.centroid_candidate_path)
        platform_audit = PlatformCompatibilityAuditService().audit(
            platform_bundle,
            platform_metadata,
            platform_candidate,
            bundle_path=args.bundle_path,
            metadata_path=args.metadata_receipt_path,
            candidate_path=args.centroid_candidate_path,
            reliability_specification_path=args.reliability_specification_path,
            code_revision=args.code_revision,
            audited_at=datetime.now(UTC),
        )
        if not args.execute:
            print(
                "Platform compatibility audit completed: "
                f"verified={platform_audit.verified_count}; "
                f"partial={platform_audit.partial_count}; "
                f"pending={platform_audit.pending_count}; "
                f"decision={platform_audit.decision.value}"
            )
            print("Dry run only; no audit receipt was written.")
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        write_platform_compatibility_audit(args.output_path, platform_audit)
        print(f"Wrote platform compatibility audit: {args.output_path}")
        return 0

    if (
        args.command == "reliability"
        and args.reliability_command == "platform-compatibility-schema"
    ):
        write_platform_compatibility_schema(args.path)
        print(f"Wrote platform compatibility schema: {args.path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "numerical-conformance":
        conformance_plan = load_numerical_conformance_plan(args.plan_path)
        conformance_candidate = load_pam50_centroid_candidate(args.centroid_candidate_path)
        conformance_specification = load_reliability_specification(
            args.reliability_specification_path
        )
        conformance_receipt = NumericalConformanceService().execute(
            conformance_plan,
            conformance_candidate,
            conformance_specification,
            plan_path=args.plan_path,
            candidate_path=args.centroid_candidate_path,
            reliability_specification_path=args.reliability_specification_path,
            code_revision=args.code_revision,
            executed_at=datetime.now(UTC),
        )
        if not args.execute:
            print(
                "Numerical conformance completed: "
                f"passed={conformance_receipt.passed_count}; "
                f"failed={conformance_receipt.failed_count}; "
                f"overall={conformance_receipt.overall_passed}"
            )
            print("Dry run only; no conformance receipt was written.")
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        write_numerical_conformance_receipt(
            args.output_path,
            conformance_receipt,
        )
        print(f"Wrote numerical conformance receipt: {args.output_path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "numerical-conformance-schema":
        write_numerical_conformance_schemas(
            args.plan_path,
            args.receipt_path,
        )
        print(f"Wrote numerical conformance schemas: {args.plan_path}, {args.receipt_path}")
        return 0

    if (
        args.command == "reliability"
        and args.reliability_command == "reference-development-validate"
    ):
        reference_protocol = load_reference_development_protocol(args.protocol_path)
        ReferenceDevelopmentProtocolService().validate(
            reference_protocol,
            SourceRegistry.from_yaml(args.registry),
            registry_path=args.registry,
            standing_authorization_path=args.authorization_path,
            platform_audit_path=args.platform_audit_path,
            numerical_conformance_path=args.numerical_conformance_path,
        )
        print(
            "Reference-development protocol is valid: "
            f"{reference_protocol.source_accession}; "
            f"status={reference_protocol.source_selection_status.value}; "
            "zero molecular, outcome, or classifier execution"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "reference-development-schema":
        write_reference_development_schema(args.path)
        print(f"Wrote reference-development schema: {args.path}")
        return 0

    if (
        args.command == "reliability"
        and args.reliability_command == "prospective-calibration-validate"
    ):
        prospective_design = load_prospective_calibration_design(args.design_path)
        prospective_activation = load_method_route_activation(args.route_activation_path)
        prospective_plan = load_technical_calibration_plan(args.acquisition_plan_path)
        prospective_revocation = load_calibration_contact_revocation(args.contact_revocation_path)
        ProspectiveCalibrationDesignService().validate(
            prospective_design,
            prospective_activation,
            prospective_plan,
            prospective_revocation,
            activation_path=args.route_activation_path,
            plan_path=args.acquisition_plan_path,
            revocation_path=args.contact_revocation_path,
        )
        print(
            "Prospective calibration experiment design is valid: "
            f"{prospective_design.study_id} v{prospective_design.design_version}; "
            f"{len(prospective_design.arms)} arms; "
            f"{len(prospective_design.estimands)} estimands; "
            "zero contact, spending, data access, or execution authorization"
        )
        return 0

    if (
        args.command == "reliability"
        and args.reliability_command == "prospective-calibration-schema"
    ):
        write_prospective_calibration_schema(args.path)
        print(f"Wrote prospective calibration design schema: {args.path}")
        return 0

    if (
        args.command == "reliability"
        and args.reliability_command == "prospective-calibration-activate"
    ):
        planning_decision = load_prospective_calibration_founder_decision(args.decision_path)
        planning_design = load_prospective_calibration_design(args.design_path)
        planning_activation = ProspectiveCalibrationDesignService().activate_planning(
            planning_decision,
            planning_design,
            decision_path=args.decision_path,
            design_path=args.design_path,
            decision_packet_path=args.decision_packet_path,
            code_revision=args.code_revision,
            activated_at=datetime.now(UTC),
        )
        if not args.execute:
            print(
                "Prospective calibration planning approval verified: "
                f"{planning_activation.study_id}; "
                f"{len(planning_activation.unresolved_decision_ids)} decisions; "
                "zero external or executing authority"
            )
            print("Dry run only; no activation receipt was written.")
            return 0
        if args.output_path.exists():
            raise FileExistsError("planning activation output path must be new")
        write_prospective_calibration_planning_activation(
            args.output_path,
            planning_activation,
        )
        print(f"Activated internal calibration planning: {args.output_path}")
        return 0

    if (
        args.command == "reliability"
        and args.reliability_command == "prospective-calibration-authorization-schema"
    ):
        write_prospective_calibration_authorization_schemas(
            args.decision_path,
            args.activation_path,
        )
        print(
            "Wrote prospective calibration authorization schemas: "
            f"{args.decision_path}, {args.activation_path}"
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

    if args.command == "ingest" and args.ingest_command == "public-artifact":
        artifact_plan = load_public_artifact_plan(args.plan_path)
        if not args.execute:
            print(
                "Public artifact plan is valid: "
                f"{artifact_plan.source_accession}; "
                f"bytes={artifact_plan.expected_content_length_bytes}; "
                "dry run only"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        artifact_receipt = PublicArtifactAcquisitionService(
            store=FileSystemObjectStore(args.data_root),
            data_root=args.data_root,
        ).acquire(
            artifact_plan,
            SourceRegistry.from_yaml(args.registry),
            load_reference_development_protocol(args.reference_protocol_path),
            load_storage_readiness_receipt(args.storage_readiness_path),
            plan_path=args.plan_path,
            registry_path=args.registry,
            authorization_path=args.authorization_path,
            reference_protocol_path=args.reference_protocol_path,
            storage_readiness_path=args.storage_readiness_path,
            code_revision=args.code_revision,
        )
        write_public_artifact_receipt(args.output_path, artifact_receipt)
        print(
            "Stored public artifact: "
            f"{artifact_receipt.object_key}; "
            f"sha256={artifact_receipt.sha256}"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "public-artifact-schema":
        write_public_artifact_schemas(args.plan_path, args.receipt_path)
        print(f"Wrote public-artifact schemas: {args.plan_path}, {args.receipt_path}")
        return 0

    if args.command == "ingest" and args.ingest_command == "calibration-feasibility":
        feasibility_plan = load_calibration_feasibility_acquisition_plan(args.plan_path)
        if not args.execute:
            expected_bytes = sum(
                item.expected_content_length_bytes
                for item in feasibility_plan.artifacts
            )
            print(
                "Calibration-feasibility plan is valid: "
                f"artifacts={len(feasibility_plan.artifacts)}; "
                f"bytes={expected_bytes}; "
                "dry run only"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        feasibility_receipt = CalibrationFeasibilityAcquisitionService(
            store=FileSystemObjectStore(args.data_root),
            data_root=args.data_root,
        ).acquire(
            feasibility_plan,
            SourceRegistry.from_yaml(args.registry),
            load_storage_readiness_receipt(args.storage_readiness_path),
            plan_path=args.plan_path,
            registry_path=args.registry,
            authorization_path=args.authorization_path,
            calibration_readiness_path=args.calibration_readiness_path,
            storage_readiness_path=args.storage_readiness_path,
            code_revision=args.code_revision,
        )
        write_calibration_feasibility_acquisition_receipt(
            args.output_path,
            feasibility_receipt,
        )
        print(
            "Stored calibration-feasibility artifact set: "
            f"artifacts={len(feasibility_receipt.artifacts)}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-feasibility-schema"
    ):
        write_calibration_feasibility_acquisition_schemas(
            args.plan_path,
            args.receipt_path,
        )
        print(
            "Wrote calibration-feasibility schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-feasibility-audit"
    ):
        feasibility_audit_plan = load_calibration_feasibility_audit_plan(args.plan_path)
        if not args.execute:
            print(
                "Calibration-feasibility audit plan is valid; "
                "source-isolated dry run only"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        feasibility_audit_receipt = CalibrationFeasibilityAuditService(
            store=FileSystemObjectStore(args.data_root)
        ).execute(
            feasibility_audit_plan,
            load_calibration_feasibility_acquisition_receipt(
                args.acquisition_receipt_path
            ),
            load_reliability_specification(args.reliability_specification_path),
            plan_path=args.plan_path,
            acquisition_receipt_path=args.acquisition_receipt_path,
            reliability_specification_path=args.reliability_specification_path,
            code_revision=args.code_revision,
        )
        write_calibration_feasibility_audit_receipt(
            args.output_path,
            feasibility_audit_receipt,
        )
        print(
            "Wrote calibration-feasibility audit: "
            f"{feasibility_audit_receipt.decision}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-feasibility-audit-schema"
    ):
        write_calibration_feasibility_audit_schemas(
            args.plan_path,
            args.receipt_path,
        )
        print(
            "Wrote calibration-feasibility audit schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-feasibility-pilot"
    ):
        pilot_plan = load_calibration_feasibility_pilot_plan(args.plan_path)
        if not args.execute:
            print("Calibration-feasibility pilot plan is valid; dry run")
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        pilot_receipt = CalibrationFeasibilityPilotService(
            store=FileSystemObjectStore(args.data_root)
        ).execute(
            pilot_plan,
            load_calibration_feasibility_acquisition_receipt(
                args.acquisition_receipt_path
            ),
            load_reliability_specification(args.reliability_specification_path),
            plan_path=args.plan_path,
            acquisition_receipt_path=args.acquisition_receipt_path,
            feasibility_audit_receipt_path=args.feasibility_audit_receipt_path,
            annotation_resolution_receipt_path=(
                args.annotation_resolution_receipt_path
            ),
            annotation_mapping_receipt_path=args.annotation_mapping_receipt_path,
            reliability_specification_path=args.reliability_specification_path,
            code_revision=args.code_revision,
        )
        write_calibration_feasibility_pilot_receipt(
            args.output_path,
            pilot_receipt,
        )
        print(
            "Wrote source-isolated calibration-feasibility pilot: "
            f"{pilot_receipt.decision}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-feasibility-pilot-schema"
    ):
        write_calibration_feasibility_pilot_schemas(
            args.plan_path,
            args.receipt_path,
        )
        print(
            "Wrote calibration-feasibility pilot schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-annotation-resolve"
    ):
        annotation_plan = load_calibration_annotation_resolution_plan(args.plan_path)
        if not args.execute:
            print(
                "Calibration annotation-resolution plan is valid; "
                "metadata-only dry run"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        annotation_receipt = CalibrationAnnotationResolutionService().execute(
            annotation_plan,
            plan_path=args.plan_path,
            feasibility_audit_receipt_path=args.feasibility_audit_receipt_path,
            lineage_receipt_path=args.lineage_receipt_path,
            code_revision=args.code_revision,
        )
        write_calibration_annotation_resolution_receipt(
            args.output_path,
            annotation_receipt,
        )
        print(
            "Resolved calibration annotation: "
            f"GRCh38/Ensembl {annotation_receipt.ensembl_release}; "
            f"samples={annotation_receipt.sample_count}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-annotation-resolve-schema"
    ):
        write_calibration_annotation_resolution_schemas(
            args.plan_path,
            args.receipt_path,
        )
        print(
            "Wrote calibration annotation-resolution schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-annotation-acquire"
    ):
        annotation_acquisition_plan = load_calibration_annotation_acquisition_plan(
            args.plan_path
        )
        if not args.execute:
            print(
                "Calibration annotation-acquisition plan is valid: "
                f"bytes={annotation_acquisition_plan.expected_content_length_bytes}; "
                "dry run"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        annotation_acquisition_receipt = CalibrationAnnotationAcquisitionService(
            store=FileSystemObjectStore(args.data_root),
            data_root=args.data_root,
        ).acquire(
            annotation_acquisition_plan,
            SourceRegistry.from_yaml(args.registry),
            load_storage_readiness_receipt(args.storage_readiness_path),
            plan_path=args.plan_path,
            registry_path=args.registry,
            annotation_resolution_path=args.annotation_resolution_path,
            storage_readiness_path=args.storage_readiness_path,
            code_revision=args.code_revision,
        )
        write_calibration_annotation_acquisition_receipt(
            args.output_path,
            annotation_acquisition_receipt,
        )
        print(
            "Stored calibration annotation: "
            f"sha256={annotation_acquisition_receipt.sha256}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-annotation-acquire-schema"
    ):
        write_calibration_annotation_acquisition_schemas(
            args.plan_path,
            args.receipt_path,
        )
        print(
            "Wrote annotation-acquisition schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-annotation-map"
    ):
        mapping_plan = load_calibration_annotation_mapping_plan(args.plan_path)
        if not args.execute:
            print("Calibration annotation-mapping plan is valid; dry run")
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        mapping_receipt = CalibrationAnnotationMappingService(
            store=FileSystemObjectStore(args.data_root)
        ).execute(
            mapping_plan,
            load_calibration_annotation_acquisition_receipt(
                args.annotation_receipt_path
            ),
            load_calibration_feasibility_acquisition_receipt(
                args.feasibility_receipt_path
            ),
            load_reliability_specification(args.reliability_specification_path),
            plan_path=args.plan_path,
            annotation_receipt_path=args.annotation_receipt_path,
            feasibility_receipt_path=args.feasibility_receipt_path,
            feasibility_audit_receipt_path=args.feasibility_audit_receipt_path,
            reliability_specification_path=args.reliability_specification_path,
            code_revision=args.code_revision,
        )
        write_calibration_annotation_mapping_receipt(
            args.output_path,
            mapping_receipt,
        )
        print(
            "Mapped calibration annotation: "
            f"PAM50={mapping_receipt.pam50_present_in_source_count}/50; "
            f"complete={mapping_receipt.mapping_complete}"
        )
        return 0

    if (
        args.command == "ingest"
        and args.ingest_command == "calibration-annotation-map-schema"
    ):
        write_calibration_annotation_mapping_schemas(
            args.plan_path,
            args.receipt_path,
        )
        print(
            "Wrote annotation-mapping schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "matrix-audit":
        audit_plan = load_matrix_audit_plan(args.plan_path)
        if not args.execute:
            print(
                "GSE81538 matrix-audit plan is valid: "
                f"rows={audit_plan.expected_gene_rows}; "
                f"samples={audit_plan.expected_sample_columns}; dry run only"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        audit_receipt = GSE81538MatrixAuditService(
            store=FileSystemObjectStore(args.data_root)
        ).audit(
            audit_plan,
            load_public_artifact_receipt(args.acquisition_receipt_path),
            load_pam50_centroid_candidate(args.centroid_candidate_path),
            plan_path=args.plan_path,
            acquisition_path=args.acquisition_receipt_path,
            candidate_path=args.centroid_candidate_path,
            reference_protocol_path=args.reference_protocol_path,
            code_revision=args.code_revision,
        )
        write_matrix_audit_receipt(args.output_path, audit_receipt)
        print(
            "Wrote GSE81538 matrix audit: "
            f"{audit_receipt.decision.value}; "
            f"measurements={audit_receipt.total_measurement_count}; "
            f"PAM50={audit_receipt.resolved_pam50_gene_count}/"
            f"{audit_receipt.required_pam50_gene_count}"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "matrix-audit-schema":
        write_matrix_audit_schemas(args.plan_path, args.receipt_path)
        print(f"Wrote GSE81538 matrix-audit schemas: {args.plan_path}, {args.receipt_path}")
        return 0

    if args.command == "ingest" and args.ingest_command == "reference-metadata":
        metadata_plan = load_reference_metadata_plan(args.plan_path)
        if not args.execute:
            print(
                "GSE81538 reference-metadata plan is valid: "
                f"samples={metadata_plan.expected_sample_count}; "
                f"per_stratum={metadata_plan.samples_per_stratum}; dry run only"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        reference_metadata_receipt = GSE81538ReferenceMetadataService(
            store=FileSystemObjectStore(args.data_root)
        ).select(
            metadata_plan,
            load_public_artifact_receipt(args.acquisition_receipt_path),
            load_matrix_audit_receipt(args.matrix_audit_receipt_path),
            load_reference_input_founder_decision(args.founder_decision_path),
            load_reference_development_protocol(args.reference_protocol_path),
            plan_path=args.plan_path,
            acquisition_path=args.acquisition_receipt_path,
            matrix_audit_path=args.matrix_audit_receipt_path,
            founder_decision_path=args.founder_decision_path,
            protocol_path=args.reference_protocol_path,
            code_revision=args.code_revision,
        )
        write_reference_metadata_receipt(args.output_path, reference_metadata_receipt)
        print(
            "Wrote GSE81538 reference metadata selection: "
            f"{reference_metadata_receipt.decision.value}; "
            f"manifest_records={reference_metadata_receipt.manifest_record_count}; "
            f"manifest_sha256={reference_metadata_receipt.manifest_sha256}"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "reference-metadata-schema":
        write_reference_metadata_schemas(args.plan_path, args.receipt_path)
        print(
            "Wrote GSE81538 reference-metadata schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "reference-construct":
        construction_plan = load_reference_construction_plan(args.plan_path)
        if not args.execute:
            print(
                "GSE81538 reference-construction plan is valid: "
                f"samples={construction_plan.expected_sample_count}; "
                f"genes={construction_plan.expected_gene_count}; dry run only"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        construction_receipt = GSE81538ReferenceConstructionService(
            store=FileSystemObjectStore(args.data_root)
        ).construct(
            construction_plan,
            load_matrix_audit_receipt(args.matrix_audit_receipt_path),
            load_reference_metadata_receipt(args.reference_metadata_receipt_path),
            load_reference_development_protocol(args.reference_protocol_path),
            load_pam50_centroid_candidate(args.centroid_candidate_path),
            plan_path=args.plan_path,
            matrix_audit_path=args.matrix_audit_receipt_path,
            metadata_receipt_path=args.reference_metadata_receipt_path,
            protocol_path=args.reference_protocol_path,
            candidate_path=args.centroid_candidate_path,
            code_revision=args.code_revision,
        )
        write_reference_construction_receipt(args.output_path, construction_receipt)
        print(
            "Wrote GSE81538 fixed reference: "
            f"{construction_receipt.decision.value}; "
            f"genes={construction_receipt.reference_gene_count}; "
            f"reference_sha256={construction_receipt.reference_sha256}"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "reference-construct-schema":
        write_reference_construction_schemas(args.plan_path, args.receipt_path)
        print(
            "Wrote GSE81538 reference-construction schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "reference-sensitivity":
        sensitivity_plan = load_reference_sensitivity_plan(args.plan_path)
        if not args.execute:
            print(
                "GSE81538 reference-sensitivity plan is valid: "
                f"samples={sensitivity_plan.expected_sample_count}; "
                f"genes={sensitivity_plan.expected_gene_count}; dry run only"
            )
            return 0
        if args.output_path is None:
            raise ValueError("--output-path is required with --execute")
        sensitivity_receipt = GSE81538ReferenceSensitivityService(
            store=FileSystemObjectStore(args.data_root)
        ).execute(
            sensitivity_plan,
            load_matrix_audit_receipt(args.matrix_audit_receipt_path),
            load_reference_metadata_receipt(args.reference_metadata_receipt_path),
            load_reference_construction_receipt(args.construction_receipt_path),
            load_reference_development_protocol(args.reference_protocol_path),
            load_pam50_centroid_candidate(args.centroid_candidate_path),
            plan_path=args.plan_path,
            matrix_audit_path=args.matrix_audit_receipt_path,
            metadata_receipt_path=args.reference_metadata_receipt_path,
            construction_receipt_path=args.construction_receipt_path,
            protocol_path=args.reference_protocol_path,
            candidate_path=args.centroid_candidate_path,
            code_revision=args.code_revision,
        )
        write_reference_sensitivity_receipt(args.output_path, sensitivity_receipt)
        print(
            "Wrote GSE81538 reference sensitivity: "
            f"{sensitivity_receipt.decision.value}; "
            f"spearman={sensitivity_receipt.vector_spearman_correlation:.6f}; "
            f"sensitivity_sha256={sensitivity_receipt.sensitivity_sha256}"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "reference-sensitivity-schema":
        write_reference_sensitivity_schemas(args.plan_path, args.receipt_path)
        print(
            "Wrote GSE81538 reference-sensitivity schemas: "
            f"{args.plan_path}, {args.receipt_path}"
        )
        return 0

    if args.command == "feasibility" and args.feasibility_command == "metadata-audit":
        if not args.execute:
            print(json.dumps(sorted(METADATA_AUDIT_URLS), indent=2))
            print("Dry run only; no endpoint was contacted and no artifact was written.")
            return 0
        authorization_bytes = args.authorization.read_bytes()
        metadata_receipt = MetadataFeasibilityAuditService().execute(
            authorization_path=str(args.authorization),
            authorization_bytes=authorization_bytes,
        )
        write_metadata_feasibility_receipt(args.output, metadata_receipt)
        print(
            f"Wrote metadata feasibility audit {metadata_receipt.audit_version}: "
            f"{metadata_receipt.decision.value}"
        )
        return 0

    if args.command == "feasibility" and args.feasibility_command == "schema":
        write_metadata_feasibility_schema(args.path)
        print(f"Wrote metadata-feasibility schema: {args.path}")
        return 0

    if args.command == "feasibility" and args.feasibility_command == "field-isolated-metadata":
        if not args.execute:
            print(
                json.dumps(
                    {
                        "gdc_manifest_url": FIELD_ISOLATED_GDC_FILES_URL,
                        "gdc_clinical_query": build_gdc_clinical_manifest_query(),
                        "gdc_star_query": build_gdc_star_manifest_query(),
                        "geo_expression_url": FIELD_ISOLATED_GEO_EXPRESSION_URL,
                        "geo_family_url": FIELD_ISOLATED_GEO_FAMILY_SOFT_URL,
                    },
                    indent=2,
                )
            )
            print("Dry run only; no endpoint was contacted and no artifact was written.")
            return 0
        authorization_bytes = args.authorization.read_bytes()
        packet_bytes = args.packet.read_bytes()
        field_prior_receipt_bytes = (
            args.prior_receipt.read_bytes() if args.prior_receipt is not None else None
        )
        field_prior_receipt = (
            load_field_isolated_metadata_receipt(args.prior_receipt)
            if args.prior_receipt is not None
            else None
        )
        field_authorization = load_field_isolated_metadata_authorization(args.authorization)
        field_isolated_receipt = FieldIsolatedMetadataAuditService().execute(
            authorization=field_authorization,
            authorization_path=str(args.authorization),
            authorization_bytes=authorization_bytes,
            packet_path=str(args.packet),
            packet_bytes=packet_bytes,
            software_revision=args.software_revision,
            prior_receipt=field_prior_receipt,
            prior_receipt_path=(
                str(args.prior_receipt) if args.prior_receipt is not None else None
            ),
            prior_receipt_bytes=field_prior_receipt_bytes,
        )
        write_field_isolated_metadata_receipt(args.output, field_isolated_receipt)
        print(
            f"Wrote field-isolated metadata audit "
            f"{field_isolated_receipt.audit_version}: "
            f"{field_isolated_receipt.decision.value}"
        )
        return 0

    if args.command == "feasibility" and args.feasibility_command == "field-isolated-schema":
        write_field_isolated_metadata_schema(args.path)
        print(f"Wrote field-isolated metadata schema: {args.path}")
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

    if args.command == "reliability" and args.reliability_command == "audit-validate":
        method_audit = load_method_dependency_audit(args.audit_path)
        audit_synthesis = load_authorized_saturated_evidence_synthesis(args.synthesis_path)
        audit_specification = load_reliability_specification(args.specification_path)
        validated_audit = MethodDependencyAuditService().validate(
            method_audit,
            audit_synthesis,
            audit_specification,
            synthesis_path=args.synthesis_path,
            specification_path=args.specification_path,
        )
        print(
            f"Method dependency audit is valid: {validated_audit.study_id}, "
            f"{len(validated_audit.dependencies)} dependencies, "
            f"recommended {validated_audit.recommended_route_id}; "
            "founder decision required"
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "schema":
        write_reliability_schema(args.path)
        print(f"Wrote reliability schema: {args.path}")
        return 0

    if args.command == "reliability" and args.reliability_command == "synthetic-score":
        specification = load_reliability_specification(args.specification_path)
        method = load_reliability_method_inputs(args.method_path)
        sample = load_single_sample_expression(args.sample_path)
        technical_error_panel = (
            load_synthetic_technical_error_panel(args.technical_error_panel)
            if args.technical_error_panel is not None
            else None
        )
        synthetic_result = SyntheticSingleSampleReliabilityKernel().score(
            specification,
            method,
            sample,
            technical_error_panel,
        )
        print(
            json.dumps(
                synthetic_result.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "reliability" and args.reliability_command == "synthetic-batch-score":
        specification = load_reliability_specification(args.specification_path)
        method = load_reliability_method_inputs(args.method_path)
        synthetic_batch = load_synthetic_expression_batch(args.batch_path)
        technical_error_panel = (
            load_synthetic_technical_error_panel(args.technical_error_panel)
            if args.technical_error_panel is not None
            else None
        )
        synthetic_batch_result = SyntheticSingleSampleReliabilityKernel().score_batch(
            specification,
            method,
            synthetic_batch,
            technical_error_panel,
        )
        print(
            json.dumps(
                synthetic_batch_result.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            )
        )
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
        print(f"Wrote evidence-review schemas: {args.priority_path}, {args.progress_path}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "citation-seed-build":
        direct_inventory = load_full_text_inventory(args.direct_inventory)
        amendment_activation = load_evidence_cap_amendment_activation_receipt(
            args.amendment_activation
        )
        prior_pass_queues = [
            load_citation_pass_appraisal_queue_receipt(path)
            for path in args.prior_pass_queue_receipt
        ]
        prior_pass_inclusion_count = amendment_activation.confirmed_inclusion_count + sum(
            queue.confirmed_inclusion_count for queue in prior_pass_queues
        )
        if not args.execute:
            print(
                f"Cumulative citation seed set ready: "
                f"{direct_inventory.provisional_inclusion_count} direct and "
                f"{prior_pass_inclusion_count} prior-pass inclusions "
                f"for pass {args.next_pass_number}"
            )
            print("Dry run only; no cumulative seed object was stored.")
            return 0
        seed_service = CitationCumulativeSeedService(store=get_object_store())
        cumulative_seeds = seed_service.build(
            direct_inventory,
            amendment_activation,
            direct_inventory_path=args.direct_inventory,
            activation_receipt_path=args.amendment_activation,
            prior_pass_queues=prior_pass_queues,
            prior_pass_queue_paths=args.prior_pass_queue_receipt,
            next_pass_number=args.next_pass_number,
            code_revision=args.code_revision,
        )
        write_citation_cumulative_seed_receipt(
            args.receipt_output,
            cumulative_seeds,
        )
        print(
            f"Built citation pass {cumulative_seeds.next_pass_number} seed set: "
            f"{cumulative_seeds.cumulative_seed_count} unique persistent identifiers from "
            f"{cumulative_seeds.direct_inclusion_count} direct and "
            f"{cumulative_seeds.prior_pass_inclusion_count} prior-pass inclusions"
        )
        print(f"Wrote cumulative seed receipt: {args.receipt_output}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "citation-retrieve":
        if (args.inventory_path is None) == (args.seed_receipt is None):
            raise SystemExit("provide exactly one inventory_path or --seed-receipt")
        if args.seed_receipt is not None:
            cumulative_receipt = load_citation_cumulative_seed_receipt(args.seed_receipt)
            if cumulative_receipt.next_pass_number != args.pass_number:
                raise SystemExit("cumulative seed receipt is bound to a different citation pass")
            seeds = CitationCumulativeSeedService(store=get_object_store()).load_seeds(
                cumulative_receipt
            )
            study_id = cumulative_receipt.study_id
        else:
            inventory = load_full_text_inventory(args.inventory_path)
            seeds = [
                CitationSeed(
                    evidence_id=f"PMID:{record.pmid}",
                    source="MED",
                    external_id=record.pmid,
                    pmid=record.pmid,
                    title=record.title,
                )
                for record in inventory.records
                if record.pmid is not None
            ]
            if len(seeds) != inventory.provisional_inclusion_count:
                raise SystemExit("every included citation seed requires a PMID")
            study_id = inventory.study_id
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
            study_id=study_id,
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
        prior_search_receipt = load_literature_search_receipt(args.prior_search_receipt)
        prior_decision_receipts = [
            load_citation_decision_ledger_receipt(path) for path in args.prior_decision_receipt
        ]
        if not args.execute:
            print(
                f"Citation screening preparation ready: pass "
                f"{citation_receipt.pass_number}, "
                f"{citation_receipt.unique_candidate_count} candidates"
            )
            print("Dry run only; no deduplication artifacts were stored.")
            return 0
        preparation_service = CitationScreeningPreparationService(store=get_object_store())
        preparation = preparation_service.prepare(
            citation_receipt,
            prior_search_receipt,
            code_revision=args.code_revision,
            prior_decision_receipts=prior_decision_receipts,
        )
        write_citation_screening_preparation_receipt(args.receipt_output, preparation)
        print(
            f"Prepared citation screening pass {preparation.pass_number}: "
            f"{preparation.already_screened_count} already screened, "
            f"{preparation.duplicate_candidate_count} duplicate candidates, "
            f"{preparation.requires_screening_count} requiring founder screening"
        )
        print(f"Wrote verified preparation receipt: {args.receipt_output}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "citation-prioritize":
        preparation = load_citation_screening_preparation_receipt(args.preparation_receipt)
        if not args.execute:
            print(
                f"Citation prioritization ready: {preparation.requires_screening_count} candidates"
            )
            print("Dry run only; no ranking artifact was stored.")
            return 0
        prioritization_service = CitationPrioritizationService(store=get_object_store())
        prioritization = prioritization_service.prioritize(
            preparation,
            code_revision=args.code_revision,
        )
        write_citation_prioritization_receipt(args.receipt_output, prioritization)
        print(
            f"Prioritized citation pass {prioritization.pass_number}: "
            f"{prioritization.direct_priority_count} direct, "
            f"{prioritization.supporting_priority_count} supporting, "
            f"{prioritization.context_priority_count} context"
        )
        print("Advisory ranking only; zero final screening decisions were recorded.")
        print(f"Wrote verified prioritization receipt: {args.receipt_output}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "citation-enrich":
        prioritization = load_citation_prioritization_receipt(args.prioritization_receipt)
        requested = (
            prioritization.candidate_count
            if args.include_context
            else (prioritization.direct_priority_count + prioritization.supporting_priority_count)
        )
        if not args.execute:
            print(f"Citation enrichment ready: {requested} direct/supporting candidates")
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

    if args.command == "evidence-review" and args.evidence_review_command == "citation-recommend":
        enrichment = load_citation_enrichment_receipt(args.enrichment_receipt)
        if not args.execute:
            print(
                f"Citation recommendation pass ready: "
                f"{enrichment.requested_candidate_count} candidates"
            )
            print("Dry run only; no recommendations or decisions were stored.")
            return 0
        recommendation_service = CitationRecommendationService(store=get_object_store())
        recommendations = recommendation_service.recommend(
            enrichment,
            code_revision=args.code_revision,
        )
        write_citation_recommendation_receipt(args.receipt_output, recommendations)
        print(
            f"Recommended citation pass {recommendations.pass_number}: "
            f"{recommendations.include_recommendation_count} include, "
            f"{recommendations.exclude_recommendation_count} exclude, "
            f"{recommendations.unclear_recommendation_count} unclear"
        )
        print("Advisory only; zero founder decisions were recorded.")
        print(f"Wrote verified recommendation receipt: {args.receipt_output}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "citation-packet":
        recommendation_receipt = load_citation_recommendation_receipt(args.recommendation_receipt)
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

    if args.command == "evidence-review" and args.evidence_review_command == "citation-adjudicate":
        prior_recommendations = load_citation_recommendation_receipt(args.recommendation_receipt)
        enrichment = load_citation_enrichment_receipt(args.enrichment_receipt)
        policy = load_citation_adjudication_policy(args.policy)
        if not args.execute:
            print(
                f"Citation adjudication ready: "
                f"{prior_recommendations.unclear_recommendation_count} unresolved records"
            )
            print("Dry run only; no recommendations or decisions were stored.")
            return 0
        adjudication_service = CitationUnclearAdjudicationService(store=get_object_store())
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

    if args.command == "evidence-review" and args.evidence_review_command == "citation-confirm":
        first_packet = load_citation_founder_packet_receipt(args.first_packet_receipt)
        second_packet = load_citation_founder_packet_receipt(args.second_packet_receipt)
        citation_confirmation = load_citation_founder_confirmation(args.confirmation)
        if not args.execute:
            print(
                f"Citation confirmation ready: "
                f"{first_packet.proposed_decision_count + second_packet.proposed_decision_count} "
                f"decisions bound to founder {citation_confirmation.founder_name}"
            )
            print("Dry run only; no final decision ledger was stored.")
            return 0
        confirmation_service = CitationDecisionConfirmationService(store=get_object_store())
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
        write_citation_decision_ledger_receipt(args.receipt_output, decision_receipt)
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
        and args.evidence_review_command == "citation-confirm-single"
    ):
        packet = load_citation_founder_packet_receipt(args.packet_receipt)
        citation_confirmation = load_citation_founder_confirmation(args.confirmation)
        if not args.execute:
            print(
                f"Single citation packet confirmation ready: "
                f"{packet.proposed_decision_count} decisions bound to founder "
                f"{citation_confirmation.founder_name}"
            )
            print("Dry run only; no final decision ledger was stored.")
            return 0
        decision_receipt = CitationDecisionConfirmationService(
            store=get_object_store()
        ).confirm_single(
            packet,
            citation_confirmation,
            packet_path=args.packet,
            appendix_path=args.appendix,
            code_revision=args.code_revision,
        )
        write_citation_decision_ledger_receipt(args.receipt_output, decision_receipt)
        print(
            f"Confirmed citation pass {decision_receipt.pass_number}: "
            f"{decision_receipt.included_count} include, "
            f"{decision_receipt.excluded_count} exclude, "
            f"{decision_receipt.unclear_count} unclear"
        )
        print(f"Wrote final founder decision receipt: {args.receipt_output}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "citation-reconcile":
        citation_decision = load_citation_decision_ledger_receipt(args.decision_receipt)
        citation_inventory = load_full_text_inventory(args.inventory)
        appraisal_paths = sorted(
            {path for directory in args.appraisal_dir for path in directory.glob("*.yaml")}
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
        reconciliation_service = CitationInclusionReconciliationService(store=get_object_store())
        reconciliation = reconciliation_service.reconcile(
            citation_decision,
            citation_inventory,
            appraisals,
            code_revision=args.code_revision,
        )
        write_citation_inclusion_reconciliation_receipt(args.receipt_output, reconciliation)
        print(
            f"Reconciled citation pass {reconciliation.pass_number}: "
            f"{reconciliation.active_inventory_match_count} active inventory, "
            f"{reconciliation.prior_appraisal_match_count} prior appraisal, "
            f"{reconciliation.net_new_count} net new"
        )
        print(f"Wrote reconciliation receipt: {args.receipt_output}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "citation-close-pass":
        citation_receipt = load_citation_chain_receipt(args.citation_receipt)
        preparation_receipt = load_citation_screening_preparation_receipt(args.preparation_receipt)
        decision_receipt = load_citation_decision_ledger_receipt(args.decision_receipt)
        closure_reconciliation = load_citation_inclusion_reconciliation_receipt(
            args.reconciliation_receipt
        )
        closure_queue = load_citation_access_queue_receipt(args.queue_receipt)
        access_inventory = (
            load_full_text_inventory(args.access_inventory)
            if args.access_inventory is not None
            else None
        )
        appraisal_progress = (
            load_full_text_appraisal_progress(args.appraisal_progress)
            if args.appraisal_progress is not None
            else None
        )
        closure = CitationPassClosureService(store=get_object_store()).close(
            citation_receipt,
            preparation_receipt,
            decision_receipt,
            closure_reconciliation,
            closure_queue,
            citation_receipt_path=args.citation_receipt,
            preparation_receipt_path=args.preparation_receipt,
            decision_receipt_path=args.decision_receipt,
            reconciliation_receipt_path=args.reconciliation_receipt,
            queue_receipt_path=args.queue_receipt,
            code_revision=args.code_revision,
            access_inventory=access_inventory,
            access_inventory_path=args.access_inventory,
            appraisal_progress=appraisal_progress,
            appraisal_progress_path=args.appraisal_progress,
            prior_appraisal_paths=args.prior_appraisal,
        )
        if not args.execute:
            print(
                f"Citation pass {closure.pass_number} closure verified: "
                f"{len(closure.new_eligible_evidence_ids)} new eligible, "
                f"{closure.appraisals_completed_count} appraised, "
                f"{closure.access_restricted_count} restricted"
            )
            print("Dry run only; no closure receipt was written.")
            return 0
        write_citation_pass_closure_receipt(args.receipt_output, closure)
        print(
            f"Closed citation pass {closure.pass_number}: "
            f"{len(closure.new_eligible_evidence_ids)} new eligible evidence records"
        )
        print(f"Wrote citation-pass closure receipt: {args.receipt_output}")
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "synthesis-validate":
        synthesis_progress = load_evidence_review_progress(args.progress)
        synthesis_proposal = load_saturated_evidence_synthesis_proposal(args.proposal)
        appraisal_paths = sorted(
            {
                *args.appraisal,
                *(path for directory in args.appraisal_dir for path in directory.glob("*.yaml")),
            }
        )
        synthesis_appraisals = [load_full_text_appraisal(path) for path in appraisal_paths]
        validated = SaturatedEvidenceSynthesisService().validate(
            synthesis_proposal,
            synthesis_progress,
            synthesis_appraisals,
            progress_path=args.progress,
        )
        print(
            f"Evidence synthesis proposal is valid: {validated.study_id}, "
            f"{len(validated.claims)} claims, "
            f"{validated.completed_appraisal_count} appraisals, "
            "zero authorized conclusions"
        )
        return 0

    if args.command == "evidence-review" and args.evidence_review_command == "synthesis-authorize":
        authorization_progress = load_evidence_review_progress(args.progress)
        authorization_proposal = load_saturated_evidence_synthesis_proposal(args.proposal)
        authorization_confirmation = load_evidence_synthesis_founder_confirmation(args.confirmation)
        authorization_appraisal_paths = sorted(
            {
                *args.appraisal,
                *(path for directory in args.appraisal_dir for path in directory.glob("*.yaml")),
            }
        )
        authorization_appraisals = [
            load_full_text_appraisal(path) for path in authorization_appraisal_paths
        ]
        authorized_synthesis = SaturatedEvidenceSynthesisService().authorize(
            authorization_proposal,
            authorization_confirmation,
            authorization_progress,
            authorization_appraisals,
            proposal_path=args.proposal,
            progress_path=args.progress,
        )
        if not args.execute:
            print(
                f"Synthesis authorization verified: "
                f"{authorized_synthesis.study_id}, "
                f"{len(authorized_synthesis.claims)} working claims"
            )
            print("Dry run only; no authorized synthesis was written.")
            return 0
        write_authorized_saturated_evidence_synthesis(
            args.output_path,
            authorized_synthesis,
        )
        print(f"Authorized saturated evidence synthesis: {authorized_synthesis.study_id}")
        print(f"Wrote authorized synthesis: {args.output_path}")
        return 0

    if (
        args.command == "evidence-review"
        and args.evidence_review_command == "citation-route-inclusions"
    ):
        citation_decision = load_citation_decision_ledger_receipt(args.decision_receipt)
        citation_reconciliation = load_citation_inclusion_reconciliation_receipt(
            args.reconciliation_receipt
        )
        active_amendment = load_evidence_cap_amendment_activation_receipt(
            args.active_amendment_receipt
        )
        if not args.execute:
            print(
                f"Citation pass {citation_decision.pass_number} routing ready: "
                f"{citation_reconciliation.confirmed_inclusion_count} inclusions "
                f"under active protocol {active_amendment.active_protocol_version}"
            )
            print("Dry run only; no appraisal queue was stored.")
            return 0
        queue_service = CitationPassAppraisalQueueService(store=get_object_store())
        appraisal_queue = queue_service.build(
            citation_decision,
            citation_reconciliation,
            active_amendment,
            decision_receipt_path=args.decision_receipt,
            reconciliation_receipt_path=args.reconciliation_receipt,
            active_amendment_receipt_path=args.active_amendment_receipt,
            code_revision=args.code_revision,
        )
        write_citation_pass_appraisal_queue_receipt(args.receipt_output, appraisal_queue)
        print(
            f"Routed citation pass {appraisal_queue.pass_number}: "
            f"{appraisal_queue.repository_candidate_count} repository candidates, "
            f"{appraisal_queue.access_check_required_count} access checks, "
            f"{appraisal_queue.prior_appraisal_reuse_count} prior appraisal reuses"
        )
        print(f"Wrote later-pass queue receipt: {args.receipt_output}")
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
        amendment_service = EvidenceCapAmendmentActivationService(store=get_object_store())
        activation = amendment_service.activate(
            amendment_approval,
            inclusion_reconciliation,
            amendment_path=args.amendment,
            reconciliation_receipt_path=args.reconciliation_receipt,
            code_revision=args.code_revision,
        )
        write_evidence_cap_amendment_activation_receipt(args.receipt_output, activation)
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
        reconciliation_receipt = InventoryReconciliationService(store=get_object_store()).reconcile(
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

    if args.command == "literature" and args.literature_command == "screening-confirm-preview":
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

    if args.command == "literature" and args.literature_command == "read-only-receipt-validate":
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

    if args.command == "literature" and args.literature_command == "citation-access-inventory":
        activation_receipt = load_citation_access_queue_receipt(args.activation_receipt)
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

    if args.command == "literature" and args.literature_command == "citation-full-text-batch":
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
        repository_access_batch, citation_retrieval_receipts = citation_access_service.assess(
            inventory,
            code_revision=args.code_revision,
            receipt_directory=str(args.receipt_dir),
        )
        args.receipt_dir.mkdir(parents=True, exist_ok=True)
        for citation_retrieval_receipt in citation_retrieval_receipts:
            write_full_text_retrieval_receipt(
                args.receipt_dir / f"{citation_retrieval_receipt.pmcid}.yaml",
                citation_retrieval_receipt,
            )
        write_repository_access_batch_receipt(args.batch_receipt_output, repository_access_batch)
        print(
            f"Assessed {repository_access_batch.repository_candidate_count} "
            f"repository candidates: {repository_access_batch.retrieved_count} "
            f"licensed full texts retrieved, "
            f"{repository_access_batch.access_check_required_count} "
            "routed to access checks"
        )
        print(f"Wrote repository access batch: {args.batch_receipt_output}")
        return 0

    if args.command == "literature" and args.literature_command == "citation-access-check-queue":
        inventory = load_full_text_inventory(args.inventory)
        repository_batch = load_repository_access_batch_receipt(args.repository_batch)
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

    if args.command == "literature" and args.literature_command == "citation-appraisal-progress":
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
            appraisal_source_receipt_paths=(
                sorted(
                    path
                    for directory in args.appraisal_source_receipt_dir
                    for path in directory.glob("*.yaml")
                )
                if args.appraisal_source_receipt_dir is not None
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
        write_full_text_appraisal_progress(args.output_path, citation_appraisal_progress)
        ready = sum(
            item.status == "ready_for_appraisal" for item in citation_appraisal_progress.records
        )
        awaiting = sum(
            item.status == "awaiting_full_text" for item in citation_appraisal_progress.records
        )
        print(
            f"Wrote citation appraisal progress: {ready} ready for appraisal, "
            f"{awaiting} awaiting full text, "
            f"{citation_appraisal_progress.appraisals_completed} completed"
        )
        print(f"Progress path: {args.output_path}")
        return 0

    if args.command == "literature" and args.literature_command == "citation-appraisal-authorize":
        appraisal_confirmation = load_full_text_appraisal_batch_confirmation(args.confirmation)
        proposal_paths = sorted(args.proposal_dir.glob("*.yaml"))
        if (args.version_link_proposal_dir is None) != (args.version_link_output_dir is None):
            raise SystemExit(
                "version-link proposal and output directories must be supplied together"
            )
        version_link_proposal_paths = (
            sorted(args.version_link_proposal_dir.glob("*.yaml"))
            if args.version_link_proposal_dir is not None
            else []
        )
        authorization = AppraisalConfirmationService().authorize_bundle(
            confirmation=appraisal_confirmation,
            packet_path=args.packet,
            proposal_paths=proposal_paths,
            version_link_proposal_paths=version_link_proposal_paths,
        )
        by_screening_id = {item.screening_id: item for item in appraisal_confirmation.proposals}
        for appraisal in authorization.appraisals:
            reference = by_screening_id[appraisal.screening_id]
            write_full_text_appraisal(
                args.output_dir / reference.filename,
                appraisal,
            )
        by_version_pair = {
            (item.earlier_screening_id, item.canonical_screening_id): item
            for item in appraisal_confirmation.version_links
        }
        for version_link in authorization.version_links:
            version_reference = by_version_pair[
                (
                    version_link.earlier.screening_id,
                    version_link.canonical.screening_id,
                )
            ]
            if args.version_link_output_dir is None:
                raise SystemExit("confirmed version links require an output directory")
            write_publication_version_link_decision(
                args.version_link_output_dir / version_reference.filename,
                version_link,
            )
        print(
            f"Authorized and wrote {len(authorization.appraisals)} locked appraisals "
            f"and {len(authorization.version_links)} publication-version links "
            f"from batch {appraisal_confirmation.batch_number:04d}"
        )
        print(f"Appraisal directory: {args.output_dir}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-publication-version-reconcile"
    ):
        appraisal_paths = sorted(
            path for directory in args.appraisal_dir for path in directory.glob("*.yaml")
        )
        version_link_paths = sorted(args.version_link_dir.glob("*.yaml"))
        version_receipt = PublicationVersionReconciliationService().build(
            appraisals=[load_full_text_appraisal(path) for path in appraisal_paths],
            version_links=[
                load_publication_version_link_decision(path) for path in version_link_paths
            ],
        )
        write_publication_version_reconciliation_receipt(
            args.output_path,
            version_receipt,
        )
        print(
            f"Reconciled {version_receipt.appraisal_count} appraisals into "
            f"{version_receipt.unique_study_count} unique studies"
        )
        print(f"Version reconciliation: {args.output_path}")
        return 0

    if args.command == "literature" and args.literature_command == "citation-pmc-read-only-review":
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
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
        write_full_text_read_only_review_receipt(args.receipt_output, review_receipt)
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
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
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
        write_full_text_read_only_review_receipt(args.receipt_output, review_receipt)
        print(
            f"Reviewed medRxiv DOI {review_receipt.doi} ephemerally: "
            f"{review_receipt.content_size_bytes} bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-pmc-oai-read-only-review"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        if not args.execute:
            print(
                f"PMC OAI review ready: {matches[0].pmcid}, "
                f"screening {matches[0].screening_id}, code {args.code_revision}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        review_receipt = PmcOaiReadOnlyReviewService().review(
            matches[0],
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            code_revision=args.code_revision,
            access_basis=args.access_basis,
            observed_rights=args.observed_rights,
            rights_url=args.rights_url,
        )
        write_full_text_read_only_review_receipt(args.receipt_output, review_receipt)
        print(
            f"Reviewed {review_receipt.pmcid} canonical OAI article ephemerally: "
            f"{review_receipt.content_size_bytes} canonical bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-institutional-pdf-read-only-review"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
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
        write_full_text_read_only_review_receipt(args.receipt_output, review_receipt)
        print(
            f"Reviewed institutional PDF DOI {review_receipt.doi} ephemerally: "
            f"{review_receipt.content_size_bytes} bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-publisher-pdf-read-only-review"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
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
        write_full_text_read_only_review_receipt(args.receipt_output, review_receipt)
        print(
            f"Reviewed publisher PDF DOI {review_receipt.doi} ephemerally: "
            f"{review_receipt.content_size_bytes} bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-institutional-pdf-appraisal-propose"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        review_receipt = load_full_text_read_only_review_receipt(args.review_receipt)
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
        and args.literature_command == "citation-pmc-oai-appraisal-propose"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        review_receipt = load_full_text_read_only_review_receipt(args.review_receipt)
        draft = load_full_text_appraisal_proposal(args.draft)
        if not args.execute:
            print(
                f"PMC OAI proposal verification ready: {matches[0].pmcid}, "
                f"screening {matches[0].screening_id}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        proposal = PmcOaiAppraisalProposalService().validate(
            record=matches[0],
            receipt=review_receipt,
            proposal=draft,
        )
        write_full_text_appraisal_proposal(args.proposal_output, proposal)
        print(
            f"Verified structured proposal for {proposal.pmid} against "
            f"{review_receipt.content_size_bytes} canonical ephemeral bytes; "
            "zero article bytes stored"
        )
        print(f"Wrote non-authoritative proposal: {args.proposal_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-pmc-html-appraisal-propose"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        review_receipt = load_full_text_read_only_review_receipt(args.review_receipt)
        draft = load_full_text_appraisal_proposal(args.draft)
        if not args.execute:
            print(
                f"PMC HTML proposal verification ready: {matches[0].pmcid}, "
                f"screening {matches[0].screening_id}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        proposal = PmcHtmlAppraisalProposalService().validate(
            record=matches[0],
            receipt=review_receipt,
            proposal=draft,
        )
        write_full_text_appraisal_proposal(args.proposal_output, proposal)
        print(
            f"Verified structured proposal for {proposal.pmid} against "
            f"{review_receipt.content_size_bytes} ephemeral HTML bytes; "
            "zero article bytes stored"
        )
        print(f"Wrote non-authoritative proposal: {args.proposal_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-publisher-pdf-appraisal-propose"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        review_receipt = load_full_text_read_only_review_receipt(args.review_receipt)
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

    if (
        args.command == "literature"
        and args.literature_command == "citation-publisher-html-read-only-review"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        if not args.execute:
            print(
                f"Publisher HTML review ready: {matches[0].doi}, "
                f"screening {matches[0].screening_id}, code {args.code_revision}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        review_receipt = ApprovedPublisherHtmlReadOnlyReviewService().review(
            matches[0],
            study_id=inventory.study_id,
            queue_id=inventory.queue_id,
            progress_id=inventory.progress_id,
            code_revision=args.code_revision,
            access_basis=args.access_basis,
            observed_rights=args.observed_rights,
            rights_url=args.rights_url,
        )
        write_full_text_read_only_review_receipt(args.receipt_output, review_receipt)
        print(
            f"Reviewed publisher HTML DOI {review_receipt.doi} ephemerally: "
            f"{review_receipt.content_size_bytes} canonical bytes hashed, "
            "zero article bytes stored"
        )
        print(f"Wrote verified no-storage receipt: {args.receipt_output}")
        return 0

    if (
        args.command == "literature"
        and args.literature_command == "citation-publisher-html-appraisal-propose"
    ):
        inventory = load_full_text_inventory(args.inventory)
        matches = [item for item in inventory.records if item.screening_id == args.screening_id]
        if len(matches) != 1:
            raise SystemExit("screening ID is not in the citation access inventory")
        review_receipt = load_full_text_read_only_review_receipt(args.review_receipt)
        draft = load_full_text_appraisal_proposal(args.draft)
        if not args.execute:
            print(
                f"Publisher HTML proposal verification ready: {matches[0].doi}, "
                f"screening {matches[0].screening_id}"
            )
            print("Dry run only; no article content was requested or stored.")
            return 0
        proposal = ApprovedPublisherHtmlAppraisalProposalService().validate(
            record=matches[0],
            receipt=review_receipt,
            proposal=draft,
        )
        write_full_text_appraisal_proposal(args.proposal_output, proposal)
        print(
            f"Verified structured proposal for DOI {proposal.doi} against "
            f"{review_receipt.content_size_bytes} canonical ephemeral bytes; "
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

    if args.command == "study" and args.study_command == "completion-validate":
        completion_audit = load_study_completion_audit(args.audit_path)
        StudyCompletionAuditService().validate(
            completion_audit,
            study_root=args.study_root,
            pipeline_path=args.pipeline_path,
        )
        print(
            "Research completion audit is valid: "
            f"{completion_audit.study_id}; "
            f"current phase={completion_audit.current_phase}; "
            f"final-review-ready={completion_audit.ready_for_final_human_review}"
        )
        return 0

    if args.command == "study" and args.study_command == "completion-schema":
        write_study_completion_audit_schema(args.path)
        print(f"Wrote research completion-audit schema: {args.path}")
        return 0

    raise AssertionError("Unreachable command")
