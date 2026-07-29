"""Independent numerical-conformance contracts for the PAM50 kernel."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class NumericalConformanceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NumericalConformancePlan(NumericalConformanceModel):
    schema_version: str = "1.0.0"
    plan_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    platform_audit_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    centroid_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    absolute_score_tolerance: float = Field(gt=0.0, le=1e-10)
    absolute_margin_tolerance: float = Field(gt=0.0, le=1e-10)
    required_case_ids: list[str] = Field(min_length=8, max_length=8)
    independent_reference_implementation: str = Field(
        pattern=r"^pure_python_no_numpy_no_scipy$"
    )
    synthetic_only: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    method_lock_authorized: bool

    @model_validator(mode="after")
    def validate_plan(self) -> NumericalConformancePlan:
        expected = [
            "CONF-ARCHETYPE-LUMINAL-A",
            "CONF-ARCHETYPE-LUMINAL-B",
            "CONF-ARCHETYPE-HER2-ENRICHED",
            "CONF-ARCHETYPE-BASAL-LIKE",
            "CONF-ARCHETYPE-NORMAL-LIKE",
            "CONF-TIED-INPUT-RANKS",
            "CONF-TOP-SCORE-TIE",
            "CONF-RUNNER-UP-SCORE-TIE",
        ]
        if self.required_case_ids != expected:
            raise ValueError("conformance cases must use the frozen ordered suite")
        if (
            not self.synthetic_only
            or self.molecular_values_accessed
            or self.outcomes_accessed
            or self.method_lock_authorized
        ):
            raise ValueError("conformance planning must remain synthetic and nonlocking")
        return self


class NumericalConformanceCaseResult(NumericalConformanceModel):
    case_id: str = Field(pattern=r"^CONF-[A-Z0-9-]+$")
    production_label: str | None
    reference_label: str | None
    production_runner_up: str | None
    reference_runner_up: str | None
    top_score_absolute_difference: float | None = Field(default=None, ge=0.0)
    runner_up_score_absolute_difference: float | None = Field(default=None, ge=0.0)
    margin_absolute_difference: float | None = Field(default=None, ge=0.0)
    production_reason: str
    reference_reason: str
    labels_match: bool
    ranks_match: bool
    reasons_match: bool
    tolerance_passed: bool
    passed: bool

    @model_validator(mode="after")
    def validate_case(self) -> NumericalConformanceCaseResult:
        expected_pass = (
            self.labels_match
            and self.ranks_match
            and self.reasons_match
            and self.tolerance_passed
        )
        if self.passed != expected_pass:
            raise ValueError("conformance case pass state does not reconcile")
        return self


class NumericalConformanceReceipt(NumericalConformanceModel):
    schema_version: str = "1.0.0"
    receipt_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    code_revision: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    executed_at: datetime
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reliability_specification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    production_kernel_version: str
    reference_implementation: str
    absolute_score_tolerance: float = Field(gt=0.0, le=1e-10)
    absolute_margin_tolerance: float = Field(gt=0.0, le=1e-10)
    cases: list[NumericalConformanceCaseResult] = Field(min_length=8, max_length=8)
    passed_count: int = Field(ge=0, le=8)
    failed_count: int = Field(ge=0, le=8)
    overall_passed: bool
    limitations: list[str] = Field(min_length=1)
    synthetic_only: bool
    molecular_values_accessed: bool
    outcomes_accessed: bool
    analytical_validity_claimed: bool
    method_lock_authorized: bool
    study_execution_authorized: bool

    @model_validator(mode="after")
    def validate_receipt(self) -> NumericalConformanceReceipt:
        observed_passes = sum(case.passed for case in self.cases)
        if (self.passed_count, self.failed_count) != (
            observed_passes,
            len(self.cases) - observed_passes,
        ):
            raise ValueError("conformance receipt counts do not reconcile")
        if self.overall_passed != (self.failed_count == 0):
            raise ValueError("overall conformance state does not reconcile")
        if (
            not self.synthetic_only
            or self.molecular_values_accessed
            or self.outcomes_accessed
            or self.analytical_validity_claimed
            or self.method_lock_authorized
            or self.study_execution_authorized
        ):
            raise ValueError("numerical conformance cannot claim analytical execution")
        return self


def load_numerical_conformance_plan(path: Path) -> NumericalConformancePlan:
    return NumericalConformancePlan.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_numerical_conformance_receipt(
    path: Path,
) -> NumericalConformanceReceipt:
    return NumericalConformanceReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_numerical_conformance_receipt(
    path: Path,
    receipt: NumericalConformanceReceipt,
) -> None:
    if path.exists():
        raise FileExistsError("numerical conformance receipt path must be new")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(receipt.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_numerical_conformance_schemas(
    plan_path: Path,
    receipt_path: Path,
) -> None:
    for path, model in (
        (plan_path, NumericalConformancePlan),
        (receipt_path, NumericalConformanceReceipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
