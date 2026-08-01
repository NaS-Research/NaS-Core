"""Fail-closed scoring bridge used before technical calibration exists."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import yaml

from nas_core.analysis.reliability import SyntheticSingleSampleReliabilityKernel
from nas_core.domain.retrospective_qc import RetrospectiveProfileQCResult
from nas_core.domain.uncalibrated_scoring import (
    AttemptedDenominatorAccounting,
    UncalibratedProfileScore,
    UncalibratedScoringReceipt,
    UncalibratedScoringSpecification,
    UncalibratedScoringState,
)
from nas_core.ingestion.gdc import sha256


class UncalibratedScoringError(RuntimeError):
    """Raised when a frozen dependency or scoring invariant differs."""


class UncalibratedScoringService:
    def __init__(
        self,
        specification: UncalibratedScoringSpecification,
        *,
        centroids: dict[str, dict[str, float]],
        gene_order: list[str],
    ) -> None:
        self._specification = specification
        self._gene_order = gene_order
        if set(centroids) != set(specification.canonical_subtype_order):
            raise UncalibratedScoringError("centroid subtype set changed")
        if any(set(values) != set(gene_order) for values in centroids.values()):
            raise UncalibratedScoringError("centroid gene set changed")
        self._centroids = centroids

    def score(
        self,
        qc_result: RetrospectiveProfileQCResult,
        centered_profile: tuple[float, ...] | None,
    ) -> UncalibratedProfileScore:
        if not qc_result.valid:
            if centered_profile is not None:
                raise UncalibratedScoringError("QC-failed input cannot have a profile")
            return UncalibratedProfileScore(
                state=UncalibratedScoringState.QC_FAILED,
                scored=False,
                report_action="abstain",
                top_subtype=None,
                top_score=None,
                runner_up_subtype=None,
                runner_up_score=None,
                margin=None,
                reason_codes=[*qc_result.reason_codes, "qc_failed"],
            )
        if centered_profile is None or len(centered_profile) != len(self._gene_order):
            raise UncalibratedScoringError("QC-valid input requires the exact panel")
        sample = np.asarray(centered_profile, dtype=np.float64)
        if not np.isfinite(sample).all() or np.ptp(sample) == 0.0:
            return self._score_failure("invalid_centered_profile")
        scores: list[tuple[str, float]] = []
        for subtype in self._specification.canonical_subtype_order:
            centroid = np.asarray(
                [self._centroids[subtype][gene] for gene in self._gene_order],
                dtype=np.float64,
            )
            score = SyntheticSingleSampleReliabilityKernel._spearman(sample, centroid)
            if score is None or not math.isfinite(score):
                return self._score_failure(f"invalid_score:{subtype}")
            scores.append((subtype, score))
        scores.sort(key=lambda item: (-item[1], item[0]))
        tolerance = self._specification.numerical_tolerance
        if abs(scores[0][1] - scores[1][1]) <= tolerance:
            return self._score_failure("top_score_tie")
        if abs(scores[1][1] - scores[2][1]) <= tolerance:
            return self._score_failure("runner_up_score_tie")
        return UncalibratedProfileScore(
            state=UncalibratedScoringState.UNCALIBRATED,
            scored=True,
            report_action="abstain",
            top_subtype=scores[0][0],
            top_score=scores[0][1],
            runner_up_subtype=scores[1][0],
            runner_up_score=scores[1][1],
            margin=scores[0][1] - scores[1][1],
            reason_codes=["technical_calibration_incomplete"],
        )

    @staticmethod
    def account(results: list[UncalibratedProfileScore]) -> AttemptedDenominatorAccounting:
        qc_failed = sum(item.state is UncalibratedScoringState.QC_FAILED for item in results)
        score_failed = sum(item.state is UncalibratedScoringState.SCORE_FAILED for item in results)
        scored = sum(item.scored for item in results)
        return AttemptedDenominatorAccounting(
            attempted_count=len(results),
            qc_valid_count=len(results) - qc_failed,
            qc_failed_count=qc_failed,
            scored_count=scored,
            score_failed_count=score_failed,
            uncalibrated_count=scored,
            abstained_count=len(results),
            reported_label_count=0,
        )

    @staticmethod
    def _score_failure(reason: str) -> UncalibratedProfileScore:
        return UncalibratedProfileScore(
            state=UncalibratedScoringState.SCORE_FAILED,
            scored=False,
            report_action="abstain",
            top_subtype=None,
            top_score=None,
            runner_up_subtype=None,
            runner_up_score=None,
            margin=None,
            reason_codes=[reason],
        )

    def freeze_receipt(
        self,
        *,
        specification_path: Path,
        processed_input_qc_receipt_path: Path,
        expression_bridge_receipt_path: Path,
        centroid_candidate_path: Path,
        numerical_conformance_receipt_path: Path,
        code_revision: str,
    ) -> UncalibratedScoringReceipt:
        dependencies = (
            (
                processed_input_qc_receipt_path,
                self._specification.processed_input_qc_receipt_sha256,
            ),
            (
                expression_bridge_receipt_path,
                self._specification.expression_bridge_receipt_sha256,
            ),
            (centroid_candidate_path, self._specification.centroid_candidate_sha256),
            (
                numerical_conformance_receipt_path,
                self._specification.numerical_conformance_receipt_sha256,
            ),
        )
        if any(sha256(path.read_bytes()) != expected for path, expected in dependencies):
            raise UncalibratedScoringError("frozen scoring dependency changed")
        return UncalibratedScoringReceipt(
            receipt_version="1.0.0",
            study_id=self._specification.study_id,
            code_revision=code_revision,
            specification_sha256=sha256(specification_path.read_bytes()),
            dependency_hashes_verified=True,
            fixed_spearman_scoring_frozen=True,
            uncalibrated_state_mandatory=True,
            all_attempts_abstain=True,
            denominator_reconciliation_frozen=True,
            reported_label_count=0,
            decision="uncalibrated_scoring_boundary_frozen",
            molecular_values_accessed=False,
            validation_values_accessed=False,
            outcomes_accessed=False,
            study_classifier_executed=False,
            limitations=[
                "A numerical score is not evidence that a subtype label is reliable.",
                "Technical-error calibration and reporting thresholds remain absent.",
                "The freeze exercised only synthetic software fixtures, not study profiles.",
            ],
            next_actions=[
                "Select the future prospective primary-calibration assay in planning only.",
                "Obtain compatible primary-estimand inputs before pair-count reestimation.",
                "Keep all retrospective outputs uncalibrated and abstained until then.",
            ],
        )


def load_centroids(path: Path) -> tuple[list[str], dict[str, dict[str, float]]]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return document["gene_order"], document["centroids"]
