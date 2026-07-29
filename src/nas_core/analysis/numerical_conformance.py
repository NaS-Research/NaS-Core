"""Independent pure-Python numerical reference for synthetic PAM50 conformance."""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from nas_core.analysis.reliability import (
    KERNEL_VERSION,
    SyntheticSingleSampleReliabilityKernel,
)
from nas_core.domain.method_dependency import Pam50CentroidCandidateArtifact
from nas_core.domain.numerical_conformance import (
    NumericalConformanceCaseResult,
    NumericalConformancePlan,
    NumericalConformanceReceipt,
)
from nas_core.domain.reliability import (
    ReliabilityMethodInputs,
    SingleSampleExpression,
    SingleSampleReliabilitySpecification,
)
from nas_core.ingestion.gdc import sha256


class NumericalConformanceError(RuntimeError):
    """Raised when the frozen numerical-conformance suite cannot execute."""


@dataclass(frozen=True)
class _ReferenceCall:
    label: str | None
    runner_up: str | None
    top_score: float | None
    runner_up_score: float | None
    margin: float | None
    reason: str


class NumericalConformanceService:
    def execute(
        self,
        plan: NumericalConformancePlan,
        candidate: Pam50CentroidCandidateArtifact,
        specification: SingleSampleReliabilitySpecification,
        *,
        plan_path: Path,
        candidate_path: Path,
        reliability_specification_path: Path,
        code_revision: str,
        executed_at: datetime,
    ) -> NumericalConformanceReceipt:
        if (
            plan.study_id,
            plan.question_id,
            plan.question_version,
        ) != (
            specification.study_id,
            specification.question_id,
            specification.question_version,
        ):
            raise NumericalConformanceError(
                "conformance plan and reliability specification identify different states"
            )
        if plan.centroid_candidate_sha256 != sha256(candidate_path.read_bytes()):
            raise NumericalConformanceError(
                "conformance plan is bound to a different centroid candidate"
            )

        base_method = ReliabilityMethodInputs(
            method_version="0.1.0",
            gene_order=candidate.gene_order,
            reference_values={gene: 0.0 for gene in candidate.gene_order},
            centroids=candidate.centroids,
            margin_threshold=0.0,
            label_retention_threshold=0.0,
            numerical_tolerance=plan.absolute_score_tolerance,
        )
        cases: list[tuple[str, ReliabilityMethodInputs, SingleSampleExpression]] = []
        subtype_case_ids = {
            "Luminal A": "CONF-ARCHETYPE-LUMINAL-A",
            "Luminal B": "CONF-ARCHETYPE-LUMINAL-B",
            "HER2-enriched": "CONF-ARCHETYPE-HER2-ENRICHED",
            "Basal-like": "CONF-ARCHETYPE-BASAL-LIKE",
            "Normal-like": "CONF-ARCHETYPE-NORMAL-LIKE",
        }
        for subtype, case_id in subtype_case_ids.items():
            cases.append(
                (
                    case_id,
                    base_method,
                    SingleSampleExpression(
                        sample_id=f"SYNTHETIC-{case_id}",
                        expression_values=deepcopy(candidate.centroids[subtype]),
                    ),
                )
            )
        tied_values = {
            gene: round(candidate.centroids["Luminal A"][gene], 1)
            for gene in candidate.gene_order
        }
        cases.append(
            (
                "CONF-TIED-INPUT-RANKS",
                base_method,
                SingleSampleExpression(
                    sample_id="SYNTHETIC-CONF-TIED-INPUT-RANKS",
                    expression_values=tied_values,
                ),
            )
        )
        top_tie_payload = base_method.model_dump(mode="python")
        top_tie_payload["centroids"]["Luminal B"] = deepcopy(
            top_tie_payload["centroids"]["Luminal A"]
        )
        cases.append(
            (
                "CONF-TOP-SCORE-TIE",
                ReliabilityMethodInputs.model_validate(top_tie_payload),
                SingleSampleExpression(
                    sample_id="SYNTHETIC-CONF-TOP-SCORE-TIE",
                    expression_values=deepcopy(candidate.centroids["Luminal A"]),
                ),
            )
        )
        runner_tie_payload = base_method.model_dump(mode="python")
        luminal_a_vector = [
            candidate.centroids["Luminal A"][gene]
            for gene in candidate.gene_order
        ]
        baseline_reference = self._reference_score(luminal_a_vector, base_method)
        if baseline_reference.label is None or baseline_reference.runner_up is None:
            raise NumericalConformanceError(
                "baseline archetype cannot define a runner-up tie fixture"
            )
        duplicate_subtype = next(
            subtype
            for subtype in base_method.centroids
            if subtype not in {
                baseline_reference.label,
                baseline_reference.runner_up,
            }
        )
        runner_tie_payload["centroids"][duplicate_subtype] = deepcopy(
            runner_tie_payload["centroids"][baseline_reference.runner_up]
        )
        cases.append(
            (
                "CONF-RUNNER-UP-SCORE-TIE",
                ReliabilityMethodInputs.model_validate(runner_tie_payload),
                SingleSampleExpression(
                    sample_id="SYNTHETIC-CONF-RUNNER-UP-SCORE-TIE",
                    expression_values=deepcopy(candidate.centroids["Luminal A"]),
                ),
            )
        )
        if [case_id for case_id, _, _ in cases] != plan.required_case_ids:
            raise NumericalConformanceError(
                "generated conformance cases do not match the frozen plan"
            )

        results = [
            self._run_case(
                case_id,
                method,
                sample,
                specification,
                score_tolerance=plan.absolute_score_tolerance,
                margin_tolerance=plan.absolute_margin_tolerance,
            )
            for case_id, method, sample in cases
        ]
        passed = sum(result.passed for result in results)
        return NumericalConformanceReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            question_id=plan.question_id,
            question_version=plan.question_version,
            code_revision=code_revision,
            executed_at=executed_at,
            plan_sha256=sha256(plan_path.read_bytes()),
            candidate_sha256=sha256(candidate_path.read_bytes()),
            reliability_specification_sha256=sha256(
                reliability_specification_path.read_bytes()
            ),
            production_kernel_version=KERNEL_VERSION,
            reference_implementation="pure_python_no_numpy_no_scipy",
            absolute_score_tolerance=plan.absolute_score_tolerance,
            absolute_margin_tolerance=plan.absolute_margin_tolerance,
            cases=results,
            passed_count=passed,
            failed_count=len(results) - passed,
            overall_passed=passed == len(results),
            limitations=[
                "The suite uses synthetic vectors and verifies software arithmetic only.",
                "Centroid-archetype fixtures do not represent patient or assay distributions.",
                "Passing conformance does not establish analytical validity or transportability.",
                "Threshold calibration and clinical outcomes are outside this suite.",
            ],
            synthetic_only=True,
            molecular_values_accessed=False,
            outcomes_accessed=False,
            analytical_validity_claimed=False,
            method_lock_authorized=False,
            study_execution_authorized=False,
        )

    def _run_case(
        self,
        case_id: str,
        method: ReliabilityMethodInputs,
        sample: SingleSampleExpression,
        specification: SingleSampleReliabilitySpecification,
        *,
        score_tolerance: float,
        margin_tolerance: float,
    ) -> NumericalConformanceCaseResult:
        production = SyntheticSingleSampleReliabilityKernel().score(
            specification,
            method,
            sample,
        )
        centered = [
            sample.expression_values[gene] - method.reference_values[gene]
            for gene in method.gene_order
        ]
        reference = self._reference_score(centered, method)
        production_reason = (
            production.reason_codes[0]
            if production.canonical_subtype is None
            else "scored"
        )
        score_diff = self._difference(production.top_score, reference.top_score)
        runner_diff = self._difference(
            production.runner_up_score,
            reference.runner_up_score,
        )
        margin_diff = self._difference(production.margin, reference.margin)
        tolerance_passed = all(
            difference is None or difference <= tolerance
            for difference, tolerance in (
                (score_diff, score_tolerance),
                (runner_diff, score_tolerance),
                (margin_diff, margin_tolerance),
            )
        )
        labels_match = production.canonical_subtype == reference.label
        ranks_match = production.runner_up_subtype == reference.runner_up
        reasons_match = production_reason == reference.reason
        return NumericalConformanceCaseResult(
            case_id=case_id,
            production_label=production.canonical_subtype,
            reference_label=reference.label,
            production_runner_up=production.runner_up_subtype,
            reference_runner_up=reference.runner_up,
            top_score_absolute_difference=score_diff,
            runner_up_score_absolute_difference=runner_diff,
            margin_absolute_difference=margin_diff,
            production_reason=production_reason,
            reference_reason=reference.reason,
            labels_match=labels_match,
            ranks_match=ranks_match,
            reasons_match=reasons_match,
            tolerance_passed=tolerance_passed,
            passed=labels_match and ranks_match and reasons_match and tolerance_passed,
        )

    @classmethod
    def _reference_score(
        cls,
        sample: list[float],
        method: ReliabilityMethodInputs,
    ) -> _ReferenceCall:
        scores = []
        for subtype, values in method.centroids.items():
            centroid = [values[gene] for gene in method.gene_order]
            score = cls._pure_spearman(sample, centroid)
            if score is None:
                return _ReferenceCall(
                    None,
                    None,
                    None,
                    None,
                    None,
                    f"invalid_score:{subtype}",
                )
            scores.append((subtype, score))
        scores.sort(key=lambda item: (-item[1], item[0]))
        if abs(scores[0][1] - scores[1][1]) <= method.numerical_tolerance:
            return _ReferenceCall(
                None,
                None,
                None,
                None,
                None,
                "top_score_tie",
            )
        if abs(scores[1][1] - scores[2][1]) <= method.numerical_tolerance:
            return _ReferenceCall(
                None,
                None,
                None,
                None,
                None,
                "runner_up_score_tie",
            )
        return _ReferenceCall(
            label=scores[0][0],
            runner_up=scores[1][0],
            top_score=scores[0][1],
            runner_up_score=scores[1][1],
            margin=scores[0][1] - scores[1][1],
            reason="scored",
        )

    @classmethod
    def _pure_spearman(
        cls,
        left: list[float],
        right: list[float],
    ) -> float | None:
        left_ranks = cls._pure_average_ranks(left)
        right_ranks = cls._pure_average_ranks(right)
        left_mean = math.fsum(left_ranks) / len(left_ranks)
        right_mean = math.fsum(right_ranks) / len(right_ranks)
        left_centered = [value - left_mean for value in left_ranks]
        right_centered = [value - right_mean for value in right_ranks]
        numerator = math.fsum(
            left_value * right_value
            for left_value, right_value in zip(
                left_centered,
                right_centered,
                strict=True,
            )
        )
        denominator = math.sqrt(
            math.fsum(value * value for value in left_centered)
            * math.fsum(value * value for value in right_centered)
        )
        if denominator == 0.0:
            return None
        result = numerator / denominator
        return result if math.isfinite(result) else None

    @staticmethod
    def _pure_average_ranks(values: list[float]) -> list[float]:
        ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
        ranks = [0.0] * len(values)
        start = 0
        while start < len(ordered):
            end = start + 1
            while end < len(ordered) and ordered[end][1] == ordered[start][1]:
                end += 1
            average = (start + end - 1) / 2.0 + 1.0
            for original_index, _ in ordered[start:end]:
                ranks[original_index] = average
            start = end
        return ranks

    @staticmethod
    def _difference(left: float | None, right: float | None) -> float | None:
        if left is None or right is None:
            if left is right:
                return None
            return math.inf
        return abs(left - right)
