"""Fail-closed validation for an outcome-blind reference-development protocol."""

from pathlib import Path

from nas_core.domain.datasets import SourceStatus
from nas_core.domain.reference_development import ReferenceDevelopmentProtocol
from nas_core.governance.classifications import DataClassification
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import sha256


class ReferenceDevelopmentProtocolError(RuntimeError):
    """Raised when reference-development provenance or governance is inconsistent."""


class ReferenceDevelopmentProtocolService:
    def validate(
        self,
        protocol: ReferenceDevelopmentProtocol,
        registry: SourceRegistry,
        *,
        registry_path: Path,
        standing_authorization_path: Path,
        platform_audit_path: Path,
        numerical_conformance_path: Path,
    ) -> None:
        source = registry.get(protocol.source_id)
        if source.status is not SourceStatus.ACTIVE:
            raise ReferenceDevelopmentProtocolError(
                "reference-development source must be active"
            )
        if source.classification is not DataClassification.PUBLIC_OPEN:
            raise ReferenceDevelopmentProtocolError(
                "reference-development source must be public/open"
            )
        if "reference-development" not in source.approved_purposes:
            raise ReferenceDevelopmentProtocolError(
                "source is not approved for reference development"
            )
        if source.ai_processing_allowed:
            raise ReferenceDevelopmentProtocolError(
                "participant molecular data must remain outside generative AI"
            )

        expected_hashes = {
            "source registry": (
                protocol.source_registry_sha256,
                sha256(registry_path.read_bytes()),
            ),
            "standing authorization": (
                protocol.standing_authorization_sha256,
                sha256(standing_authorization_path.read_bytes()),
            ),
            "platform audit": (
                protocol.platform_audit_sha256,
                sha256(platform_audit_path.read_bytes()),
            ),
            "numerical conformance": (
                protocol.numerical_conformance_sha256,
                sha256(numerical_conformance_path.read_bytes()),
            ),
        }
        changed = [
            label for label, (declared, observed) in expected_hashes.items() if declared != observed
        ]
        if changed:
            raise ReferenceDevelopmentProtocolError(
                f"reference protocol provenance changed: {', '.join(changed)}"
            )
