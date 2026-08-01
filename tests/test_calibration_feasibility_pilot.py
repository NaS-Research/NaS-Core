from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from nas_core.analysis.calibration_feasibility_pilot import (
    CalibrationFeasibilityPilotError,
    bootstrap_median_interval,
    calculate_pair_metrics,
    summarize_group,
)
from nas_core.domain.calibration_feasibility_pilot import (
    CalibrationFeasibilityPilotPlan,
    CalibrationFeasibilityPilotReceipt,
    load_calibration_feasibility_pilot_plan,
)

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "analysis/calibration_feasibility_pilot_plan_v1.0.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/calibration_feasibility_pilot_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/calibration_feasibility_pilot_receipt.schema.json"


def test_pair_metrics_are_exact_for_identical_profiles() -> None:
    profile = np.arange(50, dtype=float)
    metrics = calculate_pair_metrics(profile, profile.copy())
    assert metrics.spearman == pytest.approx(1.0)
    assert metrics.pearson == pytest.approx(1.0)
    assert metrics.mae == 0.0
    assert metrics.rmse == 0.0


def test_pair_metrics_reject_constant_profiles() -> None:
    with pytest.raises(CalibrationFeasibilityPilotError, match="constant"):
        calculate_pair_metrics(np.ones(50), np.arange(50, dtype=float))


def test_group_summary_uses_all_unordered_pairs() -> None:
    genes = [f"G{index:02d}" for index in range(50)]
    profiles = [
        {gene: float(index + offset) for index, gene in enumerate(genes)}
        for offset in (0, 1, 3)
    ]
    summary = summarize_group("group-test", profiles, genes)
    assert summary.pair_count == 3
    assert summary.spearman == pytest.approx(1.0)
    assert summary.pearson == pytest.approx(1.0)
    assert summary.mae == pytest.approx(2.0)
    assert summary.rmse == pytest.approx(2.0)
    assert set(summary.gene_absolute_differences) == set(genes)


def test_bootstrap_interval_is_deterministic_and_group_resampled() -> None:
    first = bootstrap_median_interval(
        [0.1, 0.2, 0.8, 0.9],
        replicates=10_000,
        random_seed=20260801,
    )
    second = bootstrap_median_interval(
        [0.1, 0.2, 0.8, 0.9],
        replicates=10_000,
        random_seed=20260801,
    )
    assert first == second
    assert first[0] <= 0.5 <= first[1]


def test_frozen_pilot_plan_enforces_firewall() -> None:
    plan = load_calibration_feasibility_pilot_plan(PLAN)
    assert plan.bootstrap_replicates == 10_000
    assert plan.random_seed == 20260801
    assert plan.pool_sources is False
    assert plan.infer_reliability_threshold is False
    assert plan.execute_classifier is False
    assert plan.access_outcomes is False


def test_pilot_schemas_match_runtime_models() -> None:
    assert (
        json.loads(PLAN_SCHEMA.read_text())
        == CalibrationFeasibilityPilotPlan.model_json_schema()
    )
    assert (
        json.loads(RECEIPT_SCHEMA.read_text())
        == CalibrationFeasibilityPilotReceipt.model_json_schema()
    )
