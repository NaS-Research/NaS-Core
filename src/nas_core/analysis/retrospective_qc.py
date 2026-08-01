"""Executable fail-closed QC for retrospective processed-expression profiles."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from nas_core.domain.retrospective_qc import (
    RetrospectiveProcessedInputQCReceipt,
    RetrospectiveProcessedInputQCSpecification,
    RetrospectiveProfileQCResult,
    RetrospectiveQCState,
    RetrospectiveSourceRole,
)
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore


class RetrospectiveProcessedInputQCError(RuntimeError):
    """Raised when the QC specification or fixed reference changed."""


class RetrospectiveProcessedInputQCService:
    def __init__(
        self,
        specification: RetrospectiveProcessedInputQCSpecification,
        *,
        store: ObjectStore,
    ) -> None:
        self._specification = specification
        payload = store.get_bytes(specification.reference_object_key)
        if hashlib.sha256(payload).hexdigest() != specification.reference_sha256:
            raise RetrospectiveProcessedInputQCError("fixed reference object changed")
        document = json.loads(payload)
        reference = document.get("reference")
        if not isinstance(reference, dict) or set(reference) != set(
            specification.canonical_gene_symbols
        ):
            raise RetrospectiveProcessedInputQCError("fixed reference panel differs")
        self._reference = {gene: float(value) for gene, value in reference.items()}

    def evaluate(
        self,
        source_role: RetrospectiveSourceRole,
        gene_values: dict[str, float],
    ) -> tuple[RetrospectiveProfileQCResult, tuple[float, ...] | None]:
        canonical: dict[str, float] = {}
        for supplied_gene, value in gene_values.items():
            gene = self._specification.historical_aliases.get(
                supplied_gene,
                supplied_gene,
            )
            if gene in canonical:
                return self._failure(
                    source_role,
                    RetrospectiveQCState.DUPLICATE_MAPPING,
                    len(canonical),
                )
            canonical[gene] = value
        required = set(self._specification.canonical_gene_symbols)
        observed = set(canonical)
        if observed - required:
            return self._failure(
                source_role,
                RetrospectiveQCState.SCHEMA_MISMATCH,
                len(observed & required),
            )
        if observed != required:
            return self._failure(
                source_role,
                RetrospectiveQCState.INSUFFICIENT_GENE_COVERAGE,
                len(observed & required),
            )
        ordered = [canonical[gene] for gene in self._specification.canonical_gene_symbols]
        if not all(math.isfinite(value) for value in ordered):
            return self._failure(
                source_role,
                RetrospectiveQCState.NONFINITE_INPUT,
                50,
            )
        if source_role is RetrospectiveSourceRole.TCGA_DISCOVERY:
            if any(value < self._specification.tcga_minimum_value for value in ordered):
                return self._failure(
                    source_role,
                    RetrospectiveQCState.NEGATIVE_FPKM,
                    50,
                )
            transformed = [
                math.log2(value + self._specification.tcga_log2_offset)
                for value in ordered
            ]
        else:
            floor = (
                self._specification.validation_declared_floor
                - self._specification.floor_absolute_tolerance
            )
            if any(value < floor for value in ordered):
                return self._failure(
                    source_role,
                    RetrospectiveQCState.BELOW_DECLARED_FLOOR,
                    50,
                )
            transformed = ordered
        centered = tuple(
            value - self._reference[gene]
            for gene, value in zip(
                self._specification.canonical_gene_symbols,
                transformed,
                strict=True,
            )
        )
        if len(set(centered)) < 2:
            return self._failure(
                source_role,
                RetrospectiveQCState.CONSTANT_CENTERED_PROFILE,
                50,
            )
        return (
            RetrospectiveProfileQCResult(
                source_role=source_role,
                state=RetrospectiveQCState.VALID,
                valid=True,
                canonical_gene_count=50,
                reason_codes=[],
                report_action="continue_to_locked_scoring",
            ),
            centered,
        )

    @staticmethod
    def _failure(
        source_role: RetrospectiveSourceRole,
        state: RetrospectiveQCState,
        canonical_gene_count: int,
    ) -> tuple[RetrospectiveProfileQCResult, None]:
        return (
            RetrospectiveProfileQCResult(
                source_role=source_role,
                state=state,
                valid=False,
                canonical_gene_count=min(canonical_gene_count, 50),
                reason_codes=[state.value],
                report_action="abstain",
            ),
            None,
        )

    def freeze_receipt(
        self,
        *,
        specification_path: Path,
        bridge_receipt_path: Path,
        reliability_specification_path: Path,
        code_revision: str,
    ) -> RetrospectiveProcessedInputQCReceipt:
        if self._specification.bridge_receipt_sha256 != sha256(
            bridge_receipt_path.read_bytes()
        ):
            raise RetrospectiveProcessedInputQCError("bridge receipt changed")
        if self._specification.reliability_specification_sha256 != sha256(
            reliability_specification_path.read_bytes()
        ):
            raise RetrospectiveProcessedInputQCError("reliability specification changed")
        return RetrospectiveProcessedInputQCReceipt(
            receipt_version="1.0.0",
            study_id=self._specification.study_id,
            code_revision=code_revision,
            specification_sha256=sha256(specification_path.read_bytes()),
            bridge_receipt_sha256=sha256(bridge_receipt_path.read_bytes()),
            reference_object_verified=True,
            canonical_gene_count=50,
            historical_alias_count=len(self._specification.historical_aliases),
            failure_state_count=7,
            discovery_rule_frozen=True,
            validation_rule_frozen=True,
            imputation_prohibited=True,
            cohort_centering_prohibited=True,
            scientific_failure_rerun_prohibited=True,
            invalid_profiles_abstain=True,
            decision="retrospective_processed_input_qc_frozen",
            molecular_values_accessed=False,
            validation_values_accessed=False,
            classifier_executed=False,
            outcomes_accessed=False,
            limitations=[
                "These rules govern processed expression and do not replace laboratory assay QC.",
                "Upstream GDC and SCAN-B pipeline QC fields require separate manifest auditing.",
                "A valid profile may proceed to locked scoring but cannot be called "
                "reliable before calibration.",
            ],
            next_actions=[
                "Integrate these states into discovery ingestion and "
                "attempted-denominator accounting.",
                "Freeze the uncalibrated scoring state before any discovery molecular access.",
                "Keep validation molecular access prohibited until preregistration.",
            ],
        )
