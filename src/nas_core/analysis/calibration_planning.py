"""Provenance validation for standing-autonomy Phase 1 plans."""

from pathlib import Path

from nas_core.domain.calibration_planning import (
    PhaseOneInternalPlanningBundle,
    StandingAutonomyAuthorization,
)
from nas_core.ingestion.gdc import sha256


class CalibrationPlanningError(RuntimeError):
    """Raised when a Phase 1 planning artifact has stale provenance."""


class CalibrationPlanningService:
    def validate(
        self,
        bundle: PhaseOneInternalPlanningBundle,
        authorization: StandingAutonomyAuthorization,
        *,
        authorization_path: Path,
        planning_decision_path: Path,
        planning_activation_path: Path,
    ) -> PhaseOneInternalPlanningBundle:
        if bundle.study_id != authorization.study_id:
            raise CalibrationPlanningError(
                "standing authorization and planning bundle identify different studies"
            )
        expected_hashes = {
            "autonomy authorization": (
                bundle.autonomy_authorization_sha256,
                sha256(authorization_path.read_bytes()),
            ),
            "planning decision": (
                bundle.planning_decision_sha256,
                sha256(planning_decision_path.read_bytes()),
            ),
            "planning activation": (
                bundle.planning_activation_sha256,
                sha256(planning_activation_path.read_bytes()),
            ),
        }
        for label, (declared, observed) in expected_hashes.items():
            if declared != observed:
                raise CalibrationPlanningError(
                    f"Phase 1 bundle is bound to a different {label}"
                )
        return bundle
