"""Repository-evidence-only platform compatibility audit."""

from datetime import datetime
from pathlib import Path

from nas_core.domain.calibration_planning import PhaseOneInternalPlanningBundle
from nas_core.domain.field_isolated_metadata import FieldIsolatedMetadataReceipt
from nas_core.domain.method_dependency import Pam50CentroidCandidateArtifact
from nas_core.domain.platform_compatibility import (
    CompatibilityFindingStatus,
    PlatformAuditDecision,
    PlatformCompatibilityAuditReceipt,
    PlatformCompatibilityFinding,
)
from nas_core.ingestion.gdc import sha256


class PlatformCompatibilityAuditError(RuntimeError):
    """Raised when governed platform-audit inputs are inconsistent."""


class PlatformCompatibilityAuditService:
    def audit(
        self,
        bundle: PhaseOneInternalPlanningBundle,
        metadata: FieldIsolatedMetadataReceipt,
        candidate: Pam50CentroidCandidateArtifact,
        *,
        bundle_path: Path,
        metadata_path: Path,
        candidate_path: Path,
        reliability_specification_path: Path,
        code_revision: str,
        audited_at: datetime,
    ) -> PlatformCompatibilityAuditReceipt:
        identities = {
            (bundle.study_id, bundle.question_id, bundle.question_version),
            (metadata.study_id, metadata.question_id, metadata.question_version),
        }
        if len(identities) != 1:
            raise PlatformCompatibilityAuditError(
                "platform audit inputs identify different research states"
            )
        if len(candidate.gene_order) != 50:
            raise PlatformCompatibilityAuditError(
                "centroid candidate does not contain the governed panel"
            )
        coverage = metadata.gse96058_gene_coverage
        gene_mapping_verified = (
            coverage.required_gene_count == 50
            and len(coverage.canonical_genes_present) == 50
            and not coverage.missing_canonical_genes
            and not coverage.duplicate_canonical_mappings
            and set(candidate.gene_order) == set(coverage.canonical_genes_present)
        )
        if not gene_mapping_verified:
            raise PlatformCompatibilityAuditError(
                "existing evidence does not verify complete PAM50 mapping"
            )

        protocol_path = (
            "protocol/phase_one_internal_planning_bundle_v1.0.0.yaml"
        )
        metadata_evidence = "ingestion/field_isolated_metadata_receipt_v1.0.1.yaml"
        candidate_evidence = (
            "protocol/artifact-candidates/"
            "genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
        )
        reliability_evidence = "protocol/reliability_specification.yaml"
        findings = [
            PlatformCompatibilityFinding(
                criterion_id="PLAT-001",
                status=CompatibilityFindingStatus.VERIFIED,
                finding=(
                    "Existing metadata projections resolve all 50 governed PAM50 "
                    "genes in GSE96058 with zero missing or duplicate canonical "
                    "mappings, and the centroid candidate uses the same panel."
                ),
                evidence_paths=[metadata_evidence, candidate_evidence],
            ),
            PlatformCompatibilityFinding(
                criterion_id="PLAT-002",
                status=CompatibilityFindingStatus.PARTIAL,
                finding=(
                    "A deterministic scoring kernel and governed candidate exist, "
                    "but the assay-specific alignment, quantification, transformation, "
                    "and normalization bridge remains unresolved."
                ),
                evidence_paths=[candidate_evidence, reliability_evidence],
                remaining_requirement=(
                    "Freeze container, reference build, input unit, transformation, "
                    "normalization, and precision before molecular access."
                ),
            ),
            PlatformCompatibilityFinding(
                criterion_id="PLAT-003",
                status=CompatibilityFindingStatus.PENDING,
                finding=(
                    "The historical centroid candidate is verified as an artifact, "
                    "but no independently justified platform-matched reference or "
                    "centering operation is locked."
                ),
                evidence_paths=[candidate_evidence, reliability_evidence],
                remaining_requirement=(
                    "Select and validate a lawful platform-matched fixed reference "
                    "without consulting discovery outcomes or validation performance."
                ),
            ),
            PlatformCompatibilityFinding(
                criterion_id="PLAT-004",
                status=CompatibilityFindingStatus.PARTIAL,
                finding=(
                    "GSE96058 is public processed RNA-seq with complete PAM50 gene "
                    "coverage and remains validation-only; the performance-blind "
                    "transformation bridge is not yet frozen."
                ),
                evidence_paths=[metadata_evidence, protocol_path],
                remaining_requirement=(
                    "Declare the processed-input transformation and validation "
                    "firewall before accessing validation molecular values."
                ),
            ),
            PlatformCompatibilityFinding(
                criterion_id="PLAT-005",
                status=CompatibilityFindingStatus.PENDING,
                finding=(
                    "Required QC domains and denominator rules are specified, but "
                    "no selected assay workflow supplies evidence-backed cutoffs."
                ),
                evidence_paths=[protocol_path],
                remaining_requirement=(
                    "Bind evidence-backed input, integrity, purity, complexity, "
                    "mapping, depth, completeness, failure, and rerun criteria."
                ),
            ),
            PlatformCompatibilityFinding(
                criterion_id="PLAT-006",
                status=CompatibilityFindingStatus.PARTIAL,
                finding=(
                    "Existing metadata links 136 GSE96058 technical replicates, and "
                    "the future design specifies blocked randomization, but prospective "
                    "batch and run lineage do not yet exist."
                ),
                evidence_paths=[metadata_evidence, protocol_path],
                remaining_requirement=(
                    "Materialize and validate the randomization and pair-lineage "
                    "manifest before any prospective execution."
                ),
            ),
            PlatformCompatibilityFinding(
                criterion_id="PLAT-007",
                status=CompatibilityFindingStatus.PARTIAL,
                finding=(
                    "Synthetic deterministic conformance tests exist for the Python "
                    "kernel, but no independent implementation or frozen tolerance "
                    "receipt has been completed."
                ),
                evidence_paths=[reliability_evidence],
                remaining_requirement=(
                    "Implement an independent reference calculation and freeze exact "
                    "score, margin, rank, label, and abstention tolerances."
                ),
            ),
            PlatformCompatibilityFinding(
                criterion_id="PLAT-008",
                status=CompatibilityFindingStatus.PENDING,
                finding=(
                    "The repository defines governed object-storage abstractions, but "
                    "no prospective calibration artifact manifest or retention receipt "
                    "exists."
                ),
                evidence_paths=[protocol_path],
                remaining_requirement=(
                    "Validate the storage marker and freeze retention, destruction, "
                    "object-manifest, and checksum procedures before data acquisition."
                ),
            ),
        ]
        return PlatformCompatibilityAuditReceipt(
            audit_version="1.0.0",
            study_id=bundle.study_id,
            question_id=bundle.question_id,
            question_version=bundle.question_version,
            route_id=bundle.route_id,
            code_revision=code_revision,
            audited_at=audited_at,
            planning_bundle_sha256=sha256(bundle_path.read_bytes()),
            metadata_receipt_sha256=sha256(metadata_path.read_bytes()),
            centroid_candidate_sha256=sha256(candidate_path.read_bytes()),
            reliability_specification_sha256=sha256(
                reliability_specification_path.read_bytes()
            ),
            findings=findings,
            verified_count=1,
            partial_count=4,
            pending_count=3,
            decision=PlatformAuditDecision.CHANGES_REQUIRED,
            decision_rationale=(
                "Complete gene mapping is verified, but the transformation, fixed "
                "reference, assay QC, prospective lineage, independent numerical "
                "conformance, and storage evidence are not complete."
            ),
            limitations=[
                "The audit reuses repository evidence and accesses no molecular values.",
                "Gene presence does not establish numerical or analytical compatibility.",
                "GSE96058 performance and clinical outcomes were not inspected.",
                "The audit does not select a platform stack, source, reference, or threshold.",
            ],
            molecular_values_parsed=False,
            outcome_values_parsed=False,
            raw_artifacts_stored=False,
            classifier_executed=False,
            source_selected=False,
            transformation_locked=False,
            reference_locked=False,
            platform_stack_selected=False,
            study_execution_authorized=False,
        )
