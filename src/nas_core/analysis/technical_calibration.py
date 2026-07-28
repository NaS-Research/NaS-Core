"""Validate technical-calibration plans against frozen method artifacts."""

from pathlib import Path

from nas_core.domain.method_dependency import (
    MethodDependencyAuditProposal,
    Pam50CentroidCandidateArtifact,
)
from nas_core.domain.technical_calibration import (
    TechnicalCalibrationAcquisitionPlan,
)
from nas_core.ingestion.gdc import sha256


class TechnicalCalibrationPlanError(RuntimeError):
    """Raised when an acquisition plan is not bound to the governed method state."""


class TechnicalCalibrationPlanService:
    def validate(
        self,
        plan: TechnicalCalibrationAcquisitionPlan,
        audit: MethodDependencyAuditProposal,
        candidate: Pam50CentroidCandidateArtifact,
        *,
        audit_path: Path,
        candidate_path: Path,
    ) -> TechnicalCalibrationAcquisitionPlan:
        identities = {
            (plan.study_id, plan.question_id, plan.question_version),
            (audit.study_id, audit.question_id, audit.question_version),
        }
        if len(identities) != 1:
            raise TechnicalCalibrationPlanError(
                "calibration plan and method audit identify different questions"
            )
        if plan.method_dependency_audit_sha256 != sha256(audit_path.read_bytes()):
            raise TechnicalCalibrationPlanError(
                "calibration plan is bound to a different method audit"
            )
        if plan.centroid_candidate_sha256 != sha256(candidate_path.read_bytes()):
            raise TechnicalCalibrationPlanError(
                "calibration plan is bound to a different centroid candidate"
            )
        audited = next(
            (
                item
                for item in audit.artifact_candidates
                if item.artifact_id == candidate.artifact_id
            ),
            None,
        )
        if audited is None:
            raise TechnicalCalibrationPlanError(
                "centroid candidate is absent from the method audit"
            )
        if (
            audited.distribution_sha256 != candidate.source_distribution_sha256
            or audited.member_sha256 != candidate.source_member_sha256
        ):
            raise TechnicalCalibrationPlanError(
                "centroid candidate source hashes do not match the method audit"
            )
        if (
            not candidate.candidate_only
            or candidate.founder_approved
            or candidate.method_execution_authorized
        ):
            raise TechnicalCalibrationPlanError(
                "calibration planning requires a non-executable candidate"
            )
        return plan
