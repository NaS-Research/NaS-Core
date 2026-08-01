"""Pilot-informed pair-count reestimation with explicit compatibility gates."""

from __future__ import annotations

from pathlib import Path

from nas_core.domain.calibration_feasibility_pilot import (
    CalibrationFeasibilityPilotReceipt,
)
from nas_core.domain.calibration_reestimation import (
    CalibrationPairCountReestimationPlan,
    CalibrationPairCountReestimationReceipt,
)
from nas_core.domain.prospective_calibration import (
    CalibrationArmRole,
    ProspectiveCalibrationExperimentDesign,
)
from nas_core.ingestion.gdc import sha256


class CalibrationPairCountReestimationError(RuntimeError):
    """Raised when reestimation inputs violate their frozen lineage."""


class CalibrationPairCountReestimationService:
    def assess(
        self,
        plan: CalibrationPairCountReestimationPlan,
        pilot: CalibrationFeasibilityPilotReceipt,
        prospective_design: ProspectiveCalibrationExperimentDesign,
        *,
        plan_path: Path,
        pilot_receipt_path: Path,
        prospective_design_path: Path,
        planning_bundle_path: Path,
        hypothetical_balanced_result_path: Path,
        code_revision: str,
    ) -> CalibrationPairCountReestimationReceipt:
        declared = (
            (plan.pilot_receipt_sha256, pilot_receipt_path),
            (plan.prospective_design_sha256, prospective_design_path),
            (plan.planning_bundle_sha256, planning_bundle_path),
            (
                plan.hypothetical_balanced_result_sha256,
                hypothetical_balanced_result_path,
            ),
        )
        if any(expected != sha256(path.read_bytes()) for expected, path in declared):
            raise CalibrationPairCountReestimationError("reestimation provenance changed")
        if pilot.study_id != plan.study_id or prospective_design.study_id != plan.study_id:
            raise CalibrationPairCountReestimationError("study identities do not reconcile")
        if pilot.decision != "excluded_pilots_complete_primary_calibration_not_ready":
            raise CalibrationPairCountReestimationError("pilot boundary is not eligible")
        primary_arm = next(
            arm
            for arm in prospective_design.arms
            if arm.role is CalibrationArmRole.PRIMARY_CALIBRATION
        )
        if primary_arm.pair_count is not None or prospective_design.study_execution_authorized:
            raise CalibrationPairCountReestimationError("prospective design is no longer blinded")

        groups = sum(item.eligible_replicate_group_count for item in pilot.source_summaries)
        pairs = sum(item.unordered_pair_comparison_count for item in pilot.source_summaries)
        return CalibrationPairCountReestimationReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            pilot_receipt_sha256=sha256(pilot_receipt_path.read_bytes()),
            independent_group_count=groups,
            within_group_pair_count=pairs,
            estimable_pilot_parameters=[
                "source-specific PAM50 within-group rank agreement",
                "source-specific PAM50 expression-scale absolute error",
                "source-specific exploratory gene-level absolute difference",
            ],
            nonestimable_primary_parameters=[
                "locked PAM50 subtype-label retention probability",
                "locked subtype-score and runner-up-margin paired standard deviation",
                "target-assay operational attrition and rerun fraction",
                "target-assay batch and run clustering design effect",
                "receptor, RNA-quality, score-margin, and placement coverage",
            ],
            compatibility_failures=[
                "Neither public pilot used the still-unselected target assay workflow.",
                "No classifier was executed, so label-retention and score-error "
                "estimands are absent.",
                "GSE60788 and GSE130397 use noncommensurate expression scales.",
                "The public files cannot estimate prospective operational attrition or coverage.",
            ],
            hypothetical_attempted_pair_reference=(
                plan.hypothetical_attempted_pair_reference
            ),
            final_attempted_pair_count=None,
            status="not_estimable_from_excluded_public_pilots",
            primary_calibration_ready=False,
            proxy_substituted=False,
            sources_pooled=False,
            thresholds_selected=False,
            classifier_executed=False,
            outcomes_accessed=False,
            execution_authorized=False,
            interpretation=[
                "The pilots support technical-feasibility planning but do not match "
                "the primary estimands.",
                "Using their RMSE as a subtype-score standard deviation would be an "
                "unjustified proxy substitution.",
                "The prior 185-pair balanced scenario remains hypothetical and is "
                "not a final sample size.",
            ],
            next_actions=[
                "Select and freeze the intended assay and preprocessing bridge.",
                "Obtain a target-matched excluded pilot before final pair-count reestimation.",
                "Preserve the 30-pair excluded prospective pilot as the current "
                "planning target only.",
                "Keep procurement, specimens, thresholds, and execution unauthorized.",
            ],
        )
