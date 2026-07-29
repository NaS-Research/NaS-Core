"""Validate a prospective calibration design against frozen Route C state."""

from pathlib import Path

from nas_core.domain.method_dependency import MethodRouteActivationReceipt
from nas_core.domain.prospective_calibration import (
    CalibrationContactRevocation,
    ProspectiveCalibrationExperimentDesign,
)
from nas_core.domain.technical_calibration import TechnicalCalibrationAcquisitionPlan
from nas_core.ingestion.gdc import sha256


class ProspectiveCalibrationDesignError(RuntimeError):
    """Raised when a prospective design is not bound to governed Route C state."""


class ProspectiveCalibrationDesignService:
    def validate(
        self,
        design: ProspectiveCalibrationExperimentDesign,
        activation: MethodRouteActivationReceipt,
        plan: TechnicalCalibrationAcquisitionPlan,
        revocation: CalibrationContactRevocation,
        *,
        activation_path: Path,
        plan_path: Path,
        revocation_path: Path,
    ) -> ProspectiveCalibrationExperimentDesign:
        identities = {
            (design.study_id, design.question_id, design.question_version),
            (activation.study_id, activation.question_id, activation.question_version),
            (plan.study_id, plan.question_id, plan.question_version),
            (revocation.study_id, revocation.question_id, revocation.question_version),
        }
        if len(identities) != 1:
            raise ProspectiveCalibrationDesignError(
                "prospective design inputs identify different questions"
            )
        if design.route_activation_sha256 != sha256(activation_path.read_bytes()):
            raise ProspectiveCalibrationDesignError(
                "prospective design is bound to a different Route C activation"
            )
        if design.acquisition_plan_sha256 != sha256(plan_path.read_bytes()):
            raise ProspectiveCalibrationDesignError(
                "prospective design is bound to a different acquisition plan"
            )
        if design.contact_revocation_sha256 != sha256(revocation_path.read_bytes()):
            raise ProspectiveCalibrationDesignError(
                "prospective design is bound to a different contact revocation"
            )
        if (
            activation.selected_route_id != "ROUTE-C"
            or not activation.calibration_acquisition_active
            or activation.calibration_source_selected
            or activation.method_execution_authorized
        ):
            raise ProspectiveCalibrationDesignError(
                "prospective design requires an active nonexecuting Route C hold"
            )
        future_source = next(
            (
                source
                for source in plan.source_candidates
                if source.source_id == "CALSRC-004"
            ),
            None,
        )
        if future_source is None or future_source.access_class.value != "not_yet_created":
            raise ProspectiveCalibrationDesignError(
                "acquisition plan does not preserve the future NaS experiment path"
            )
        if revocation.contact_authorized:
            raise ProspectiveCalibrationDesignError(
                "prospective design requires the founder's no-contact boundary"
            )
        return design
