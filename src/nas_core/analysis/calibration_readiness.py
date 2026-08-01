"""Reconcile technical-calibration evidence into a fail-closed path decision."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from nas_core.domain.calibration_lineage import CalibrationLineageAuditReceipt
from nas_core.domain.calibration_planning import (
    PhaseOneInternalPlanningBundle,
    StandingAutonomyAuthorization,
)
from nas_core.domain.calibration_readiness import (
    CalibrationPathAssessment,
    CalibrationPathDisposition,
    CalibrationReadinessDecision,
    TechnicalCalibrationReadinessReceipt,
)
from nas_core.domain.prospective_calibration import (
    CalibrationContactRevocation,
    ProspectiveCalibrationExperimentDesign,
)
from nas_core.domain.reference_construction import GSE81538ReferenceConstructionReceipt
from nas_core.domain.reference_sensitivity import GSE81538ReferenceSensitivityReceipt
from nas_core.domain.technical_calibration import (
    TechnicalCalibrationAcquisitionPlan,
    TechnicalCalibrationSourceScoutReceipt,
)
from nas_core.ingestion.gdc import sha256


class CalibrationReadinessError(RuntimeError):
    """Raised when calibration evidence or governance no longer reconciles."""


class TechnicalCalibrationReadinessService:
    def assess(
        self,
        authorization: StandingAutonomyAuthorization,
        acquisition: TechnicalCalibrationAcquisitionPlan,
        scout: TechnicalCalibrationSourceScoutReceipt,
        lineage: CalibrationLineageAuditReceipt,
        design: ProspectiveCalibrationExperimentDesign,
        planning: PhaseOneInternalPlanningBundle,
        revocation: CalibrationContactRevocation,
        reference: GSE81538ReferenceConstructionReceipt,
        sensitivity: GSE81538ReferenceSensitivityReceipt,
        *,
        authorization_path: Path,
        acquisition_path: Path,
        scout_path: Path,
        lineage_path: Path,
        design_path: Path,
        planning_path: Path,
        revocation_path: Path,
        reference_path: Path,
        sensitivity_path: Path,
        code_revision: str,
        assessed_at: datetime | None = None,
    ) -> TechnicalCalibrationReadinessReceipt:
        self._validate_inputs(
            authorization,
            acquisition,
            scout,
            lineage,
            design,
            planning,
            revocation,
            reference,
            sensitivity,
        )
        paths = [
            CalibrationPathAssessment(
                source_id="GEO:GSE60788",
                disposition=CalibrationPathDisposition.FEASIBILITY_AUTHORIZED,
                public_open=True,
                expected_replicate_record_count=6,
                feasibility_molecular_acquisition_authorized=True,
                threshold_calibration_authorized=False,
                primary_calibration_eligible=False,
                external_contact_required=False,
                spending_or_specimens_required=False,
                reasons=[
                    "Public processed RNA-seq values and stable replicate labels exist.",
                    "Six replicate records are inadequate for primary threshold calibration.",
                    "SCAN-B relationship to GSE96058 leaves biological independence unresolved.",
                ],
            ),
            CalibrationPathAssessment(
                source_id="GEO:GSE130397",
                disposition=CalibrationPathDisposition.FEASIBILITY_AUTHORIZED,
                public_open=True,
                expected_replicate_record_count=11,
                feasibility_molecular_acquisition_authorized=True,
                threshold_calibration_authorized=False,
                primary_calibration_eligible=False,
                external_contact_required=False,
                spending_or_specimens_required=False,
                reasons=[
                    "Public library-method replicate files exist.",
                    "The source contains too few biological specimens for primary calibration.",
                    "FFPE library-method variation cannot represent the full intended-use range.",
                ],
            ),
            CalibrationPathAssessment(
                source_id="GEO:GSE96058",
                disposition=CalibrationPathDisposition.RESERVED_VALIDATION,
                public_open=True,
                expected_replicate_record_count=136,
                feasibility_molecular_acquisition_authorized=False,
                threshold_calibration_authorized=False,
                primary_calibration_eligible=False,
                external_contact_required=False,
                spending_or_specimens_required=False,
                reasons=[
                    "GSE96058 is the frozen unchanged external-validation source.",
                    "Using it now would leak validation information into calibration.",
                ],
            ),
            CalibrationPathAssessment(
                source_id="PMC:PMC10147733",
                disposition=CalibrationPathDisposition.CONTROLLED_UNAVAILABLE,
                public_open=False,
                expected_replicate_record_count=144,
                feasibility_molecular_acquisition_authorized=False,
                threshold_calibration_authorized=False,
                primary_calibration_eligible=False,
                external_contact_required=True,
                spending_or_specimens_required=False,
                reasons=[
                    "Participant-level paired molecular values are not public.",
                    "Founder revocation prohibits the required external inquiry.",
                    "The NanoString platform is not automatically transferable to RNA-seq.",
                ],
            ),
            CalibrationPathAssessment(
                source_id="NAS:PROSPECTIVE",
                disposition=CalibrationPathDisposition.PROSPECTIVE_STOP,
                public_open=False,
                expected_replicate_record_count=None,
                feasibility_molecular_acquisition_authorized=False,
                threshold_calibration_authorized=False,
                primary_calibration_eligible=False,
                external_contact_required=True,
                spending_or_specimens_required=True,
                reasons=[
                    "The prospective design is scientifically prepared but nonexecuting.",
                    "Laboratory, spending, and specimen actions are standing stop conditions.",
                    "Pilot estimates and a blinded final pair-count reestimation remain required.",
                ],
            ),
        ]
        return TechnicalCalibrationReadinessReceipt(
            receipt_version="1.0.0",
            study_id=planning.study_id,
            question_id=planning.question_id,
            question_version=planning.question_version,
            code_revision=code_revision,
            assessed_at=assessed_at or datetime.now(UTC),
            standing_authorization_sha256=sha256(authorization_path.read_bytes()),
            acquisition_plan_sha256=sha256(acquisition_path.read_bytes()),
            source_scout_sha256=sha256(scout_path.read_bytes()),
            lineage_receipt_sha256=sha256(lineage_path.read_bytes()),
            prospective_design_sha256=sha256(design_path.read_bytes()),
            internal_planning_bundle_sha256=sha256(planning_path.read_bytes()),
            contact_revocation_sha256=sha256(revocation_path.read_bytes()),
            reference_construction_receipt_sha256=sha256(reference_path.read_bytes()),
            reference_sensitivity_receipt_sha256=sha256(sensitivity_path.read_bytes()),
            decision=CalibrationReadinessDecision.FEASIBILITY_ONLY,
            path_assessments=paths,
            public_feasibility_source_ids=["GEO:GSE60788", "GEO:GSE130397"],
            primary_calibration_source_id=None,
            primary_calibration_ready=False,
            reference_dependency_ready=True,
            exact_alternative_reference_sensitivity_estimable=False,
            feasibility_acquisition_next=True,
            feasibility_analysis_permitted_estimands=[
                "PAM50 panel completeness and identifier mapping",
                "Declared replicate-pair lineage and denominator reconciliation",
                "Gene-level paired differences as feasibility variance components",
                "Assay missingness, invalidity, and processing metadata completeness",
            ],
            prohibited_uses=[
                "Do not pool these small heterogeneous sources into a threshold distribution.",
                "Do not select reliability, margin, retention, or abstention thresholds.",
                "Do not access GSE96058 molecular values or any clinical outcome.",
                "Do not execute the classifier or make patient-level claims.",
                "Do not contact external parties or initiate spending or specimen work.",
            ],
            next_actions=[
                "Register exact public artifacts for feasibility-only roles.",
                "Acquire and checksum official GSE60788 processed expression artifacts.",
                "Acquire and inventory the official GSE130397 public archive.",
                "Audit panel coverage, replicate lineage, scale, and lawful-use metadata.",
                "Keep all pilot findings excluded from final threshold calibration.",
            ],
            final_human_review_preserved=True,
            external_contact_authorized=False,
            spending_authorized=False,
            controlled_data_authorized=False,
            specimen_acquisition_authorized=False,
            gse96058_molecular_access_authorized=False,
            outcome_access_authorized=False,
            threshold_selection_authorized=False,
            classifier_execution_authorized=False,
            clinical_use_authorized=False,
            publication_authorized=False,
        )

    @staticmethod
    def _validate_inputs(
        authorization: StandingAutonomyAuthorization,
        acquisition: TechnicalCalibrationAcquisitionPlan,
        scout: TechnicalCalibrationSourceScoutReceipt,
        lineage: CalibrationLineageAuditReceipt,
        design: ProspectiveCalibrationExperimentDesign,
        planning: PhaseOneInternalPlanningBundle,
        revocation: CalibrationContactRevocation,
        reference: GSE81538ReferenceConstructionReceipt,
        sensitivity: GSE81538ReferenceSensitivityReceipt,
    ) -> None:
        if "approved_public_open_data_use" not in authorization.delegated_internal_actions:
            raise CalibrationReadinessError("public/open feasibility use is not authorized")
        if acquisition.selected_source_id is not None or scout.source_selected:
            raise CalibrationReadinessError("a calibration source was selected prematurely")
        if not lineage.metadata_lineage_feasibility_established:
            raise CalibrationReadinessError("metadata lineage feasibility is unresolved")
        if design.source_selected or planning.source_selected:
            raise CalibrationReadinessError("planning artifacts selected a source")
        if revocation.contact_authorized or not revocation.transmission_state.get(
            "external_contact_prohibited"
        ):
            raise CalibrationReadinessError("external-contact revocation is not active")
        if reference.decision.value != "pass" or sensitivity.decision.value != (
            "pass_with_limitation"
        ):
            raise CalibrationReadinessError("reference dependency is incomplete")
        if reference.reference_locked or sensitivity.reference_locked:
            raise CalibrationReadinessError("candidate reference was prematurely locked")
