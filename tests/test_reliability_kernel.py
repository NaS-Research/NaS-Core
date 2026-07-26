from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import yaml
from pydantic import ValidationError
from scipy.stats import spearmanr

from nas_core.analysis.reliability import SyntheticSingleSampleReliabilityKernel
from nas_core.cli import main
from nas_core.domain.reliability import (
    PAM50_HISTORICAL_ALIASES,
    ReliabilityMethodInputs,
    SingleSampleExpression,
    SyntheticTechnicalErrorPanel,
    load_reliability_specification,
)

ROOT = Path(__file__).parents[1]
SPECIFICATION_PATH = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "protocol"
    / "reliability_specification.yaml"
)


def _method() -> ReliabilityMethodInputs:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    genes = specification.input_contract.canonical_gene_symbols
    base = np.arange(1, 51, dtype=float)
    permutations = {
        "Luminal A": base,
        "Luminal B": base[::-1],
        "HER2-enriched": np.roll(base, 11),
        "Basal-like": np.roll(base[::-1], 17),
        "Normal-like": np.concatenate((base[::2], base[1::2])),
    }
    return ReliabilityMethodInputs(
        method_version="0.1.0",
        gene_order=genes,
        reference_values={gene: 0.0 for gene in genes},
        centroids={
            subtype: dict(zip(genes, values, strict=True))
            for subtype, values in permutations.items()
        },
        margin_threshold=0.0,
        label_retention_threshold=1.0,
        numerical_tolerance=1e-12,
    )


def _sample(method: ReliabilityMethodInputs) -> SingleSampleExpression:
    return SingleSampleExpression(
        sample_id="SYNTHETIC-001",
        expression_values=deepcopy(method.centroids["Luminal A"]),
    )


def _technical_panel(
    method: ReliabilityMethodInputs,
    vectors: list[dict[str, float]],
) -> SyntheticTechnicalErrorPanel:
    return SyntheticTechnicalErrorPanel(
        panel_version="0.1.0",
        gene_order=method.gene_order,
        random_seed=20260726,
        generation_description="Deterministic synthetic vectors for software tests only.",
        perturbation_vectors=vectors,
    )


def test_synthetic_kernel_scores_one_sample_deterministically() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    sample = _sample(method)
    kernel = SyntheticSingleSampleReliabilityKernel()

    first = kernel.score(specification, method, sample)
    second = kernel.score(specification, method, sample)

    assert first == second
    assert first.canonical_subtype == "Luminal A"
    assert first.reliability_state == "reliable"
    assert first.report_action == "report_label"
    assert first.valid_perturbation_count == 50
    assert first.canonical_label_retention_fraction == 1.0
    assert len(first.perturbation_families) == 1
    assert first.perturbation_families[0].kind == "leave_one_gene_out"
    assert first.provenance["execution_scope"] == "synthetic_method_validation_only"


def test_internal_spearman_matches_independent_library_with_ties() -> None:
    left = np.asarray([1.0, 2.0, 2.0, 4.0, 5.0])
    right = np.asarray([5.0, 1.0, 1.0, 3.0, 2.0])
    expected = float(spearmanr(left, right).statistic)

    observed = SyntheticSingleSampleReliabilityKernel._spearman(left, right)

    assert observed == pytest.approx(expected, abs=1e-15)


def test_expression_key_order_does_not_change_result_or_input_hash() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    sample = _sample(method)
    reversed_sample = SingleSampleExpression(
        sample_id=sample.sample_id,
        expression_values=dict(reversed(list(sample.expression_values.items()))),
    )
    kernel = SyntheticSingleSampleReliabilityKernel()

    first = kernel.score(specification, method, sample)
    second = kernel.score(specification, method, reversed_sample)

    assert first == second


def test_missing_gene_fails_closed_without_scoring() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    values = deepcopy(method.centroids["Luminal A"])
    values.pop(method.gene_order[0])

    result = SyntheticSingleSampleReliabilityKernel().score(
        specification,
        method,
        SingleSampleExpression(
            sample_id="SYNTHETIC-MISSING",
            expression_values=values,
        ),
    )

    assert result.data_quality_state == "insufficient_gene_coverage"
    assert result.reliability_state == "insufficient_data"
    assert result.report_action == "abstain"
    assert result.canonical_subtype is None
    assert result.reason_codes[0].startswith("missing_genes:")


def test_kernel_input_contract_rejects_non_synthetic_sample_identity() -> None:
    method = _method()

    with pytest.raises(ValidationError, match="SYNTHETIC"):
        SingleSampleExpression(
            sample_id="TCGA-REAL-PATIENT",
            expression_values=method.centroids["Luminal A"],
        )


def test_historical_alias_is_accepted_but_alias_collision_abstains() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    canonical_gene = next(iter(PAM50_HISTORICAL_ALIASES.values()))
    alias = next(
        key
        for key, value in PAM50_HISTORICAL_ALIASES.items()
        if value == canonical_gene
    )
    aliased_values = deepcopy(method.centroids["Luminal A"])
    aliased_values[alias] = aliased_values.pop(canonical_gene)
    kernel = SyntheticSingleSampleReliabilityKernel()

    accepted = kernel.score(
        specification,
        method,
        SingleSampleExpression(
            sample_id="SYNTHETIC-ALIAS",
            expression_values=aliased_values,
        ),
    )
    colliding_values = deepcopy(method.centroids["Luminal A"])
    colliding_values[alias] = colliding_values[canonical_gene]
    rejected = kernel.score(
        specification,
        method,
        SingleSampleExpression(
            sample_id="SYNTHETIC-COLLISION",
            expression_values=colliding_values,
        ),
    )

    assert accepted.data_quality_state == "valid"
    assert accepted.canonical_subtype == "Luminal A"
    assert rejected.data_quality_state == "ambiguous_gene_mapping"
    assert rejected.report_action == "abstain"


def test_nonfinite_sample_and_centroid_fail_closed() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    sample_values = deepcopy(method.centroids["Luminal A"])
    sample_values[method.gene_order[0]] = float("nan")
    sample_result = SyntheticSingleSampleReliabilityKernel().score(
        specification,
        method,
        SingleSampleExpression(
            sample_id="SYNTHETIC-NONFINITE",
            expression_values=sample_values,
        ),
    )
    method_payload = method.model_dump(mode="python")
    method_payload["centroids"]["Luminal A"][method.gene_order[0]] = float("inf")
    invalid_method = ReliabilityMethodInputs.model_validate(method_payload)
    method_result = SyntheticSingleSampleReliabilityKernel().score(
        specification,
        invalid_method,
        _sample(method),
    )

    assert sample_result.data_quality_state == "nonfinite_input"
    assert sample_result.report_action == "abstain"
    assert method_result.data_quality_state == "invalid_centroid"
    assert method_result.report_action == "abstain"


def test_canonical_tie_is_unclassifiable_and_abstains() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    method_payload = method.model_dump(mode="python")
    method_payload["centroids"]["Luminal B"] = deepcopy(
        method_payload["centroids"]["Luminal A"]
    )
    tied_method = ReliabilityMethodInputs.model_validate(method_payload)

    result = SyntheticSingleSampleReliabilityKernel().score(
        specification,
        tied_method,
        _sample(method),
    )

    assert result.data_quality_state == "valid"
    assert result.reliability_state == "unclassifiable"
    assert result.report_action == "abstain"
    assert result.canonical_subtype is None
    assert result.reason_codes == ["top_score_tie"]


def test_prespecified_threshold_can_force_unstable_abstention() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    method_payload = method.model_dump(mode="python")
    method_payload["margin_threshold"] = 1.0
    strict_method = ReliabilityMethodInputs.model_validate(method_payload)

    result = SyntheticSingleSampleReliabilityKernel().score(
        specification,
        strict_method,
        _sample(method),
    )

    assert result.canonical_subtype == "Luminal A"
    assert result.reliability_state == "unstable"
    assert result.report_action == "abstain"
    assert "margin_below_threshold" in result.reason_codes


def test_combined_panel_reports_each_perturbation_family() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    zero_vector = {gene: 0.0 for gene in method.gene_order}
    panel = _technical_panel(method, [zero_vector, zero_vector, zero_vector])

    result = SyntheticSingleSampleReliabilityKernel().score(
        specification,
        method,
        _sample(method),
        panel,
    )

    assert result.reliability_state == "reliable"
    assert result.total_perturbation_count == 53
    assert result.valid_perturbation_count == 53
    assert len(result.perturbation_families) == 2
    assert result.perturbation_families[1].kind == "technical_measurement_error"
    assert result.perturbation_families[1].canonical_label_retention_fraction == 1.0
    assert "technical_error_panel_sha256" in result.provenance


def test_synthetic_technical_error_label_change_triggers_instability() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    luminal_a = method.centroids["Luminal A"]
    luminal_b = method.centroids["Luminal B"]
    label_changing_vector = {
        gene: luminal_b[gene] - luminal_a[gene] for gene in method.gene_order
    }
    panel = _technical_panel(method, [label_changing_vector])

    result = SyntheticSingleSampleReliabilityKernel().score(
        specification,
        method,
        _sample(method),
        panel,
    )

    assert result.canonical_subtype == "Luminal A"
    assert result.reliability_state == "unstable"
    assert result.report_action == "abstain"
    assert result.total_perturbation_count == 51
    assert result.canonical_label_retention_fraction == pytest.approx(50 / 51)
    assert "label_retention_below_threshold" in result.reason_codes


def test_invalid_technical_error_run_is_preserved_and_abstains() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)
    method = _method()
    invalid_vector = {gene: 0.0 for gene in method.gene_order}
    invalid_vector[method.gene_order[0]] = float("nan")
    panel = _technical_panel(method, [invalid_vector])

    result = SyntheticSingleSampleReliabilityKernel().score(
        specification,
        method,
        _sample(method),
        panel,
    )

    assert result.data_quality_state == "valid"
    assert result.reliability_state == "unclassifiable"
    assert result.report_action == "abstain"
    assert result.total_perturbation_count == 51
    assert result.valid_perturbation_count == 50
    assert result.perturbation_families[1].valid_count == 0
    assert result.reason_codes == ["invalid_technical_error_run"]


def test_cli_scores_only_an_explicitly_synthetic_fixture(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    method = _method()
    sample = _sample(method)
    method_path = tmp_path / "method.yaml"
    sample_path = tmp_path / "sample.yaml"
    panel_path = tmp_path / "technical-panel.yaml"
    zero_vector = {gene: 0.0 for gene in method.gene_order}
    panel = _technical_panel(method, [zero_vector, zero_vector, zero_vector])
    method_path.write_text(
        yaml.safe_dump(method.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    sample_path.write_text(
        yaml.safe_dump(sample.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    panel_path.write_text(
        yaml.safe_dump(panel.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )

    result = main(
        [
            "reliability",
            "synthetic-score",
            str(SPECIFICATION_PATH),
            str(method_path),
            str(sample_path),
            "--technical-error-panel",
            str(panel_path),
            "--synthetic-only",
        ]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert '"execution_scope": "synthetic_method_validation_only"' in output
    assert '"canonical_subtype": "Luminal A"' in output
    assert '"total_perturbation_count": 53' in output
