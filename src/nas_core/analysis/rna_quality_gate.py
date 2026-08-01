"""Freeze a nonexecuting prospective RNA-quality and chemistry gate."""

from pathlib import Path

from nas_core.domain.rna_quality_gate import (
    ProspectiveRNAQualityGatePlan,
    ProspectiveRNAQualityGateReceipt,
)
from nas_core.ingestion.gdc import sha256


class ProspectiveRNAQualityGateError(RuntimeError):
    """Raised when a frozen RNA-quality dependency differs."""


class ProspectiveRNAQualityGateService:
    def freeze(
        self,
        plan: ProspectiveRNAQualityGatePlan,
        *,
        plan_path: Path,
        assay_selection_receipt_path: Path,
        prospective_design_path: Path,
        uncalibrated_scoring_receipt_path: Path,
        code_revision: str,
    ) -> ProspectiveRNAQualityGateReceipt:
        dependencies = (
            (assay_selection_receipt_path, plan.assay_selection_receipt_sha256),
            (prospective_design_path, plan.prospective_design_sha256),
            (uncalibrated_scoring_receipt_path, plan.uncalibrated_scoring_receipt_sha256),
        )
        if any(sha256(path.read_bytes()) != expected for path, expected in dependencies):
            raise ProspectiveRNAQualityGateError("frozen RNA-quality dependency changed")
        return ProspectiveRNAQualityGateReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            dependency_hashes_verified=True,
            primary_material_frozen=True,
            post_extraction_scope_frozen=True,
            high_quality_rna_range_frozen=True,
            stranded_polya_family_frozen=True,
            degraded_rna_separate=True,
            failed_inputs_retained=True,
            no_external_action_preserved=True,
            decision="prospective_rna_quality_and_chemistry_gate_frozen",
            study_execution_authorized=False,
            molecular_values_accessed=False,
            outcomes_accessed=False,
            validation_values_accessed=False,
            limitations=[
                "The primary calibration claim is limited to post-extraction error.",
                "RIN below 8 or degraded/FFPE RNA is outside the frozen primary range.",
                "The range is a planning boundary, not evidence of assay performance.",
            ],
            next_actions=[
                "Identify a lawful source of target-matched high-quality RNA without contact.",
                "Prepare a checksum-bound excluded-pilot acquisition and randomization plan.",
                "Require separate authority before quotes, specimens, spending, or execution.",
            ],
        )
