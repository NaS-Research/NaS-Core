"""Checksum-bound activation of founder-selected method routes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nas_core.domain.method_dependency import (
    MethodDependencyAuditProposal,
    MethodRouteActivationReceipt,
    MethodRouteActivationStatus,
    MethodRouteFounderDecision,
    Pam50CentroidCandidateArtifact,
)
from nas_core.domain.technical_calibration import (
    TechnicalCalibrationAcquisitionPlan,
)
from nas_core.ingestion.gdc import sha256


class MethodRouteActivationError(RuntimeError):
    """Raised when route activation is not bound to the reviewed artifacts."""


class MethodRouteActivationService:
    def activate(
        self,
        decision: MethodRouteFounderDecision,
        audit: MethodDependencyAuditProposal,
        candidate: Pam50CentroidCandidateArtifact,
        calibration_plan: TechnicalCalibrationAcquisitionPlan,
        *,
        decision_path: Path,
        audit_path: Path,
        decision_packet_path: Path,
        candidate_path: Path,
        calibration_plan_path: Path,
        code_revision: str,
        activated_at: datetime,
    ) -> MethodRouteActivationReceipt:
        identities = {
            (decision.study_id, decision.question_id, decision.question_version),
            (audit.study_id, audit.question_id, audit.question_version),
            (
                calibration_plan.study_id,
                calibration_plan.question_id,
                calibration_plan.question_version,
            ),
        }
        if len(identities) != 1:
            raise MethodRouteActivationError(
                "method-route artifacts identify different governed questions"
            )
        if decision.method_dependency_audit_sha256 != sha256(
            audit_path.read_bytes()
        ):
            raise MethodRouteActivationError(
                "founder decision is bound to a different method audit"
            )
        if decision.decision_packet_sha256 != sha256(
            decision_packet_path.read_bytes()
        ):
            raise MethodRouteActivationError(
                "founder decision is bound to a different review packet"
            )
        if not any(
            route.route_id == decision.selected_route_id for route in audit.routes
        ):
            raise MethodRouteActivationError(
                "founder-selected route is absent from the method audit"
            )
        if decision.selected_route_id != "ROUTE-C":
            raise MethodRouteActivationError(
                "this activation revision implements the approved Route C boundary"
            )
        if sha256(candidate_path.read_bytes()) != (
            calibration_plan.centroid_candidate_sha256
        ):
            raise MethodRouteActivationError(
                "calibration plan is bound to a different centroid candidate"
            )
        if calibration_plan.method_dependency_audit_sha256 != sha256(
            audit_path.read_bytes()
        ):
            raise MethodRouteActivationError(
                "calibration plan is bound to a different method audit"
            )
        if (
            not candidate.candidate_only
            or candidate.founder_approved
            or candidate.method_execution_authorized
        ):
            raise MethodRouteActivationError(
                "Route C requires a staged non-executable centroid candidate"
            )
        return MethodRouteActivationReceipt(
            activation_version="1.0.0",
            study_id=decision.study_id,
            question_id=decision.question_id,
            question_version=decision.question_version,
            selected_route_id=decision.selected_route_id,
            activation_status=(
                MethodRouteActivationStatus.INDEPENDENT_CALIBRATION_HOLD
            ),
            method_dependency_audit_sha256=sha256(audit_path.read_bytes()),
            founder_decision_sha256=sha256(decision_path.read_bytes()),
            centroid_candidate_sha256=sha256(candidate_path.read_bytes()),
            calibration_acquisition_plan_sha256=sha256(
                calibration_plan_path.read_bytes()
            ),
            code_revision=code_revision,
            activated_at=activated_at,
            question_preserved=True,
            centroid_candidate_staged=True,
            calibration_acquisition_active=True,
            founder_route_selected=True,
            calibration_source_selected=False,
            method_locked=False,
            fixed_reference_resolved=False,
            technical_calibration_resolved=False,
            thresholds_resolved=False,
            patient_level_data_accessed=False,
            molecular_values_accessed=False,
            outcome_data_accessed=False,
            method_execution_authorized=False,
            clinical_use_authorized=False,
            publication_authorized=False,
            next_required_actions=[
                "Resolve a lawful independent technical-calibration source.",
                "Resolve the fixed platform-matched centering reference.",
                "Approve calibration estimands, precision targets, and multiplicity.",
                "Freeze cross-language numerical conformance tolerances.",
                "Complete independent scientific, molecular, and statistical review.",
            ],
        )
