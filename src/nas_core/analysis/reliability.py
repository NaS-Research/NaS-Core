"""Synthetic-only deterministic kernel for the single-sample reliability contract."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Final

import numpy as np

from nas_core.domain.reliability import (
    DataQualityState,
    ReliabilityMethodInputs,
    ReliabilityState,
    ReportAction,
    SingleSampleExpression,
    SingleSampleReliabilityResult,
    SingleSampleReliabilitySpecification,
)

KERNEL_VERSION: Final = "pam50-synthetic-reliability-0.1.0"
LOGO_RUN_COUNT: Final = 50
SYNTHETIC_LIMITATION: Final = (
    "Synthetic method-validation output only; no patient, molecular, outcome, "
    "biological-truth, diagnostic, prognostic, or treatment inference is authorized."
)


class ReliabilityKernelError(RuntimeError):
    """Raised when the synthetic method kernel cannot safely execute."""


@dataclass(frozen=True)
class _ScoredCall:
    canonical_subtype: str
    top_score: float
    runner_up_subtype: str
    runner_up_score: float
    margin: float


@dataclass(frozen=True)
class _ScoreAttempt:
    call: _ScoredCall | None
    failure_reason: str | None


class SyntheticSingleSampleReliabilityKernel:
    """Exercise the declared scoring and abstention logic on synthetic fixtures only."""

    def score(
        self,
        specification: SingleSampleReliabilitySpecification,
        method: ReliabilityMethodInputs,
        sample: SingleSampleExpression,
    ) -> SingleSampleReliabilityResult:
        input_hash = self._input_hash(sample)
        provenance = {
            "execution_scope": "synthetic_method_validation_only",
            "kernel_version": KERNEL_VERSION,
            "method_version": method.method_version,
            "question_id": specification.question_id,
            "question_version": specification.question_version,
            "specification_version": specification.specification_version,
            "study_id": specification.study_id,
        }

        method_issue = self._validate_numeric_method(method)
        if method_issue is not None:
            return self._failed_result(
                sample=sample,
                method=method,
                input_hash=input_hash,
                quality=DataQualityState.INVALID_CENTROID,
                reason=method_issue,
                provenance=provenance,
            )

        normalized, quality, reason = self._normalize_sample(
            specification,
            sample,
        )
        if normalized is None:
            return self._failed_result(
                sample=sample,
                method=method,
                input_hash=input_hash,
                quality=quality,
                reason=reason,
                provenance=provenance,
            )

        centered = np.asarray(
            [
                normalized[gene] - method.reference_values[gene]
                for gene in method.gene_order
            ],
            dtype=float,
        )
        if not np.isfinite(centered).all():
            return self._failed_result(
                sample=sample,
                method=method,
                input_hash=input_hash,
                quality=DataQualityState.INVALID_TRANSFORMATION,
                reason="invalid_transformation",
                provenance=provenance,
            )

        canonical_attempt = self._score_vectors(
            centered,
            method,
            retained_indices=np.arange(LOGO_RUN_COUNT),
        )
        canonical = canonical_attempt.call
        if canonical is None:
            return SingleSampleReliabilityResult(
                sample_id=sample.sample_id,
                method_version=method.method_version,
                input_artifact_sha256=input_hash,
                data_quality_state=DataQualityState.VALID,
                canonical_subtype=None,
                top_score=None,
                runner_up_subtype=None,
                runner_up_score=None,
                margin=None,
                valid_perturbation_count=0,
                total_perturbation_count=0,
                valid_perturbation_fraction=None,
                canonical_label_retention_fraction=None,
                reliability_state=ReliabilityState.UNCLASSIFIABLE,
                report_action=ReportAction.ABSTAIN,
                reason_codes=[
                    canonical_attempt.failure_reason or "canonical_score_invalid"
                ],
                provenance=provenance,
                limitations=[SYNTHETIC_LIMITATION],
            )

        valid_runs = 0
        retained_label_runs = 0
        for omitted_index in range(LOGO_RUN_COUNT):
            retained_indices = np.delete(np.arange(LOGO_RUN_COUNT), omitted_index)
            perturbation = self._score_vectors(
                centered,
                method,
                retained_indices=retained_indices,
            ).call
            if perturbation is None:
                continue
            valid_runs += 1
            if perturbation.canonical_subtype == canonical.canonical_subtype:
                retained_label_runs += 1

        valid_fraction = valid_runs / LOGO_RUN_COUNT
        retention_fraction = (
            retained_label_runs / valid_runs if valid_runs else None
        )
        reasons: list[str] = []
        if valid_runs != LOGO_RUN_COUNT:
            state = ReliabilityState.UNCLASSIFIABLE
            action = ReportAction.ABSTAIN
            reasons.append("invalid_logo_run")
        elif retention_fraction is None:
            state = ReliabilityState.UNCLASSIFIABLE
            action = ReportAction.ABSTAIN
            reasons.append("no_valid_logo_runs")
        else:
            if canonical.margin < method.margin_threshold:
                reasons.append("margin_below_threshold")
            if retention_fraction < method.label_retention_threshold:
                reasons.append("label_retention_below_threshold")
            if reasons:
                state = ReliabilityState.UNSTABLE
                action = ReportAction.ABSTAIN
            else:
                state = ReliabilityState.RELIABLE
                action = ReportAction.REPORT_LABEL
                reasons.append("synthetic_rules_passed")

        return SingleSampleReliabilityResult(
            sample_id=sample.sample_id,
            method_version=method.method_version,
            input_artifact_sha256=input_hash,
            data_quality_state=DataQualityState.VALID,
            canonical_subtype=canonical.canonical_subtype,
            top_score=canonical.top_score,
            runner_up_subtype=canonical.runner_up_subtype,
            runner_up_score=canonical.runner_up_score,
            margin=canonical.margin,
            valid_perturbation_count=valid_runs,
            total_perturbation_count=LOGO_RUN_COUNT,
            valid_perturbation_fraction=valid_fraction,
            canonical_label_retention_fraction=retention_fraction,
            reliability_state=state,
            report_action=action,
            reason_codes=reasons,
            provenance=provenance,
            limitations=[SYNTHETIC_LIMITATION],
        )

    @staticmethod
    def _input_hash(sample: SingleSampleExpression) -> str:
        hashable_values: dict[str, float | str] = {}
        for gene, value in sample.expression_values.items():
            if math.isnan(value):
                hashable_values[gene] = "NaN"
            elif value == math.inf:
                hashable_values[gene] = "Infinity"
            elif value == -math.inf:
                hashable_values[gene] = "-Infinity"
            else:
                hashable_values[gene] = value
        body = json.dumps(
            {
                "expression_values": hashable_values,
                "sample_id": sample.sample_id,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    @staticmethod
    def _validate_numeric_method(method: ReliabilityMethodInputs) -> str | None:
        reference = np.asarray(
            [method.reference_values[gene] for gene in method.gene_order],
            dtype=float,
        )
        if not np.isfinite(reference).all():
            return "nonfinite_reference"
        for subtype, values in method.centroids.items():
            centroid = np.asarray([values[gene] for gene in method.gene_order], dtype=float)
            if not np.isfinite(centroid).all():
                return f"nonfinite_centroid:{subtype}"
            if np.ptp(centroid) <= method.numerical_tolerance:
                return f"constant_centroid:{subtype}"
        return None

    @staticmethod
    def _normalize_sample(
        specification: SingleSampleReliabilitySpecification,
        sample: SingleSampleExpression,
    ) -> tuple[dict[str, float] | None, DataQualityState, str]:
        required = set(specification.input_contract.canonical_gene_symbols)
        aliases = specification.input_contract.historical_aliases
        normalized: dict[str, float] = {}
        for supplied_gene, value in sample.expression_values.items():
            canonical_gene = aliases.get(supplied_gene, supplied_gene)
            if canonical_gene not in required:
                continue
            if canonical_gene in normalized:
                return (
                    None,
                    DataQualityState.AMBIGUOUS_GENE_MAPPING,
                    f"duplicate_mapping:{canonical_gene}",
                )
            normalized[canonical_gene] = value
        missing = sorted(required - set(normalized))
        if missing:
            return (
                None,
                DataQualityState.INSUFFICIENT_GENE_COVERAGE,
                f"missing_genes:{','.join(missing)}",
            )
        if any(not math.isfinite(value) for value in normalized.values()):
            return None, DataQualityState.NONFINITE_INPUT, "nonfinite_input"
        return normalized, DataQualityState.VALID, "valid"

    @classmethod
    def _score_vectors(
        cls,
        centered_sample: np.ndarray,
        method: ReliabilityMethodInputs,
        *,
        retained_indices: np.ndarray,
    ) -> _ScoreAttempt:
        sample_values = centered_sample[retained_indices]
        scores: list[tuple[str, float]] = []
        for subtype, centroid_values in method.centroids.items():
            centroid = np.asarray(
                [centroid_values[gene] for gene in method.gene_order],
                dtype=float,
            )[retained_indices]
            score = cls._spearman(sample_values, centroid)
            if score is None:
                return _ScoreAttempt(
                    call=None,
                    failure_reason=f"invalid_score:{subtype}",
                )
            scores.append((subtype, score))
        scores.sort(key=lambda item: (-item[1], item[0]))
        if len(scores) != 5:
            raise ReliabilityKernelError("the synthetic scorer requires five centroids")
        if abs(scores[0][1] - scores[1][1]) <= method.numerical_tolerance:
            return _ScoreAttempt(call=None, failure_reason="top_score_tie")
        if abs(scores[1][1] - scores[2][1]) <= method.numerical_tolerance:
            return _ScoreAttempt(call=None, failure_reason="runner_up_score_tie")
        return _ScoreAttempt(
            call=_ScoredCall(
                canonical_subtype=scores[0][0],
                top_score=scores[0][1],
                runner_up_subtype=scores[1][0],
                runner_up_score=scores[1][1],
                margin=scores[0][1] - scores[1][1],
            ),
            failure_reason=None,
        )

    @classmethod
    def _spearman(cls, left: np.ndarray, right: np.ndarray) -> float | None:
        left_ranks = cls._average_ranks(left)
        right_ranks = cls._average_ranks(right)
        left_centered = left_ranks - left_ranks.mean()
        right_centered = right_ranks - right_ranks.mean()
        denominator = float(
            np.linalg.norm(left_centered) * np.linalg.norm(right_centered)
        )
        if denominator == 0.0:
            return None
        score = float(np.dot(left_centered, right_centered) / denominator)
        return score if math.isfinite(score) else None

    @staticmethod
    def _average_ranks(values: np.ndarray) -> np.ndarray:
        order = np.argsort(values, kind="mergesort")
        ranks = np.empty(len(values), dtype=float)
        start = 0
        while start < len(values):
            end = start + 1
            while end < len(values) and values[order[end]] == values[order[start]]:
                end += 1
            average_rank = (start + end - 1) / 2.0 + 1.0
            ranks[order[start:end]] = average_rank
            start = end
        return ranks

    @staticmethod
    def _failed_result(
        *,
        sample: SingleSampleExpression,
        method: ReliabilityMethodInputs,
        input_hash: str,
        quality: DataQualityState,
        reason: str,
        provenance: dict[str, str],
    ) -> SingleSampleReliabilityResult:
        return SingleSampleReliabilityResult(
            sample_id=sample.sample_id,
            method_version=method.method_version,
            input_artifact_sha256=input_hash,
            data_quality_state=quality,
            canonical_subtype=None,
            top_score=None,
            runner_up_subtype=None,
            runner_up_score=None,
            margin=None,
            valid_perturbation_count=0,
            total_perturbation_count=0,
            valid_perturbation_fraction=None,
            canonical_label_retention_fraction=None,
            reliability_state=ReliabilityState.INSUFFICIENT_DATA,
            report_action=ReportAction.ABSTAIN,
            reason_codes=[reason],
            provenance=provenance,
            limitations=[SYNTHETIC_LIMITATION],
        )
