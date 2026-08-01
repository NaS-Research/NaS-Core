"""Freeze a no-contact prospective-pilot source landscape audit."""

from pathlib import Path

from nas_core.domain.pilot_source_landscape import (
    PilotSourceDisposition,
    PilotSourceLandscapePlan,
    PilotSourceLandscapeReceipt,
)
from nas_core.ingestion.gdc import sha256


class PilotSourceLandscapeError(RuntimeError):
    """Raised when a source-audit dependency differs."""


class PilotSourceLandscapeService:
    def freeze(
        self,
        plan: PilotSourceLandscapePlan,
        *,
        plan_path: Path,
        pilot_receipt_path: Path,
        rna_quality_gate_receipt_path: Path,
        code_revision: str,
    ) -> PilotSourceLandscapeReceipt:
        if sha256(pilot_receipt_path.read_bytes()) != plan.pilot_receipt_sha256:
            raise PilotSourceLandscapeError("excluded-pilot receipt changed")
        if (
            sha256(rna_quality_gate_receipt_path.read_bytes())
            != plan.rna_quality_gate_receipt_sha256
        ):
            raise PilotSourceLandscapeError("RNA-quality gate receipt changed")
        counts = {
            state: sum(item.disposition is state for item in plan.candidates)
            for state in PilotSourceDisposition
        }
        return PilotSourceLandscapeReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            dependency_hashes_verified=True,
            candidate_count=len(plan.candidates),
            verified_eligible_count=counts[PilotSourceDisposition.VERIFIED_ELIGIBLE],
            unresolved_count=counts[PilotSourceDisposition.UNRESOLVED],
            ineligible_count=counts[PilotSourceDisposition.INELIGIBLE],
            selected_source_id=None,
            no_contact_preserved=True,
            decision="no_verified_source_external_due_diligence_required",
            external_action_authorized=False,
            study_execution_authorized=False,
            molecular_values_accessed=False,
            outcomes_accessed=False,
            validation_values_accessed=False,
            limitations=[
                "Public catalogs do not prove 30 independent RIN-at-least-8 RNA sources.",
                "Same-homogenate aliquots and nonoverlap require provider due diligence.",
                "Application, pricing, shipping, and lawful-use terms require external action.",
            ],
            next_actions=[
                "Present unresolved routes for founder review of external due diligence.",
                "Require separate authority before any inquiry, application, quote, or purchase.",
                "Do not select a source until every frozen eligibility field is documented.",
            ],
        )
