"""Freeze the excluded prospective-pilot plan without external action."""

from pathlib import Path

from nas_core.domain.prospective_pilot import (
    ExcludedProspectivePilotPlan,
    ExcludedProspectivePilotPlanReceipt,
)
from nas_core.ingestion.gdc import sha256


class ExcludedProspectivePilotPlanError(RuntimeError):
    """Raised when an excluded-pilot dependency differs."""


class ExcludedProspectivePilotPlanService:
    def freeze(
        self,
        plan: ExcludedProspectivePilotPlan,
        *,
        plan_path: Path,
        rna_quality_gate_receipt_path: Path,
        planning_bundle_path: Path,
        prospective_design_path: Path,
        code_revision: str,
    ) -> ExcludedProspectivePilotPlanReceipt:
        dependencies = (
            (rna_quality_gate_receipt_path, plan.rna_quality_gate_receipt_sha256),
            (planning_bundle_path, plan.planning_bundle_sha256),
            (prospective_design_path, plan.prospective_design_sha256),
        )
        if any(sha256(path.read_bytes()) != expected for path, expected in dependencies):
            raise ExcludedProspectivePilotPlanError("frozen prospective-pilot dependency changed")
        return ExcludedProspectivePilotPlanReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            dependency_hashes_verified=True,
            attempted_pair_target=plan.attempted_pair_target,
            planned_measurement_count=(plan.attempted_pair_target * plan.measurements_per_pair),
            independent_source_target=plan.independent_biological_source_target,
            randomization_frozen=True,
            lineage_frozen=True,
            denominator_accounting_frozen=True,
            immutable_storage_contract_frozen=True,
            permanent_exclusion_frozen=True,
            no_external_action_preserved=True,
            decision="excluded_prospective_pilot_plan_frozen",
            study_execution_authorized=False,
            molecular_values_accessed=False,
            outcomes_accessed=False,
            validation_values_accessed=False,
            limitations=[
                "Thirty pairs are a feasibility target, not a final sample size.",
                "Pilot estimates cannot establish the final reliability claim.",
                "A lawful target-matched RNA source and execution authority remain absent.",
            ],
            next_actions=[
                "Perform a no-contact lawful-source landscape audit.",
                "Freeze source eligibility and nonoverlap evidence before any inquiry.",
                "Stop before contact, quotes, specimens, spending, or execution.",
            ],
        )
