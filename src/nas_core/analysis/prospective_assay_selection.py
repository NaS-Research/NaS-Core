"""Validate a planning-only assay-family selection against frozen dependencies."""

from pathlib import Path

from nas_core.domain.prospective_assay_selection import (
    ProspectiveAssaySelectionPlan,
    ProspectiveAssaySelectionReceipt,
)
from nas_core.ingestion.gdc import sha256


class ProspectiveAssaySelectionError(RuntimeError):
    """Raised when an assay selection is not bound to the frozen research state."""


class ProspectiveAssaySelectionService:
    def freeze(
        self,
        plan: ProspectiveAssaySelectionPlan,
        *,
        plan_path: Path,
        prospective_design_path: Path,
        planning_bundle_path: Path,
        planning_activation_path: Path,
        retrospective_bridge_receipt_path: Path,
        uncalibrated_scoring_receipt_path: Path,
        code_revision: str,
    ) -> ProspectiveAssaySelectionReceipt:
        dependencies = (
            (prospective_design_path, plan.prospective_design_sha256),
            (planning_bundle_path, plan.planning_bundle_sha256),
            (planning_activation_path, plan.planning_activation_sha256),
            (retrospective_bridge_receipt_path, plan.retrospective_bridge_receipt_sha256),
            (uncalibrated_scoring_receipt_path, plan.uncalibrated_scoring_receipt_sha256),
        )
        if any(sha256(path.read_bytes()) != expected for path, expected in dependencies):
            raise ProspectiveAssaySelectionError("frozen assay-selection dependency changed")
        return ProspectiveAssaySelectionReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            dependency_hashes_verified=True,
            candidate_count=len(plan.candidates),
            selected_candidate_id=plan.selected_candidate_id,
            selected_platform_family=plan.selected_platform_family,
            selection_scope=plan.selection_scope,
            exact_chemistry_unresolved=True,
            exact_instrument_unresolved=True,
            platform_conformance_required=True,
            no_external_action_preserved=True,
            decision="prospective_assay_family_selected_for_planning",
            study_execution_authorized=False,
            molecular_values_accessed=False,
            outcomes_accessed=False,
            validation_values_accessed=False,
            limitations=[
                "Platform-family selection is not analytical validation or procurement approval.",
                "Exact chemistry depends on a prespecified RNA-quality and specimen-use range.",
                "Any degraded-RNA contingency requires its own fixed-reference conformance bridge.",
            ],
            next_actions=[
                "Freeze minimum RNA input, integrity, purity, and specimen-format ranges.",
                "Define a performance-blind chemistry-selection gate for high-quality "
                "versus degraded RNA.",
                "Keep contact, quotes, procurement, specimens, and execution "
                "separately prohibited.",
            ],
        )
