"""Validate method-dependency audits against governed study artifacts."""

from pathlib import Path

from nas_core.domain.evidence_synthesis import AuthorizedSaturatedEvidenceSynthesis
from nas_core.domain.method_dependency import MethodDependencyAuditProposal
from nas_core.domain.reliability import SingleSampleReliabilitySpecification
from nas_core.ingestion.gdc import sha256


class MethodDependencyAuditError(RuntimeError):
    """Raised when a method audit is not bound to the active governed state."""


class MethodDependencyAuditService:
    def validate(
        self,
        proposal: MethodDependencyAuditProposal,
        synthesis: AuthorizedSaturatedEvidenceSynthesis,
        specification: SingleSampleReliabilitySpecification,
        *,
        synthesis_path: Path,
        specification_path: Path,
    ) -> MethodDependencyAuditProposal:
        identities = {
            (proposal.study_id, proposal.question_id, proposal.question_version),
            (synthesis.study_id, synthesis.question_id, synthesis.question_version),
            (
                specification.study_id,
                specification.question_id,
                specification.question_version,
            ),
        }
        if len(identities) != 1:
            raise MethodDependencyAuditError(
                "method audit artifacts do not identify one governed question"
            )
        if (
            not synthesis.working_synthesis_authorized
            or synthesis.novelty_claim_authorized
            or synthesis.molecular_data_access_authorized
            or synthesis.outcome_data_access_authorized
        ):
            raise MethodDependencyAuditError(
                "method audit requires a narrow founder-authorized working synthesis"
            )
        if (
            specification.status.value != "draft"
            or specification.execution_authorized
            or specification.molecular_data_access_authorized
            or specification.outcome_data_access_authorized
        ):
            raise MethodDependencyAuditError(
                "method audit requires a nonexecuting draft reliability specification"
            )
        if proposal.authorized_synthesis_sha256 != sha256(
            synthesis_path.read_bytes()
        ):
            raise MethodDependencyAuditError(
                "method audit is bound to a different authorized synthesis"
            )
        if proposal.reliability_specification_sha256 != sha256(
            specification_path.read_bytes()
        ):
            raise MethodDependencyAuditError(
                "method audit is bound to a different reliability specification"
            )
        return proposal
