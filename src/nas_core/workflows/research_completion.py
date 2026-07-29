"""Validate study-completion evidence against the repository."""

from pathlib import Path

from nas_core.domain.research_completion import StudyCompletionAudit
from nas_core.ingestion.gdc import sha256


class StudyCompletionAuditError(RuntimeError):
    """Raised when completion evidence is absent or does not match frozen bytes."""


class StudyCompletionAuditService:
    def validate(
        self,
        audit: StudyCompletionAudit,
        *,
        study_root: Path,
        pipeline_path: Path,
    ) -> StudyCompletionAudit:
        if audit.pipeline_manifest_sha256 != sha256(pipeline_path.read_bytes()):
            raise StudyCompletionAuditError(
                "completion audit is bound to a different pipeline manifest"
            )
        for phase in audit.phases:
            for item in phase.evidence:
                artifact_path = study_root / item.artifact_path
                try:
                    artifact_path.resolve().relative_to(study_root.resolve())
                except ValueError as exc:
                    raise StudyCompletionAuditError(
                        "completion evidence escapes the study root"
                    ) from exc
                if not artifact_path.is_file():
                    raise StudyCompletionAuditError(
                        f"completion evidence is missing: {item.artifact_path}"
                    )
                if item.sha256 != sha256(artifact_path.read_bytes()):
                    raise StudyCompletionAuditError(
                        f"completion evidence changed: {item.artifact_path}"
                    )
        return audit
