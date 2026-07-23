import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.cli import main
from nas_core.domain.reliability import (
    SingleSampleReliabilitySpecification,
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
SCHEMA_PATH = ROOT / "workflows" / "reliability_specification.schema.json"


def load_payload() -> dict[str, object]:
    payload = yaml.safe_load(SPECIFICATION_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_checked_in_reliability_specification_is_valid_and_nonexecuting() -> None:
    specification = load_reliability_specification(SPECIFICATION_PATH)

    assert specification.study_id == "NAS-BRCA-002"
    assert specification.question_version == "0.3.0"
    assert specification.status == "draft"
    assert specification.execution_authorized is False
    assert specification.molecular_data_access_authorized is False
    assert specification.outcome_data_access_authorized is False
    assert specification.clinical_use_authorized is False
    assert len(specification.input_contract.canonical_gene_symbols) == 50
    assert len(specification.outputs.required_fields) == 18


def test_checked_in_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA_PATH.read_text(encoding="utf-8")) == (
        SingleSampleReliabilitySpecification.model_json_schema()
    )


def test_cli_validates_checked_in_specification(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["reliability", "validate", str(SPECIFICATION_PATH)])

    assert result == 0
    assert "execution authorized: False" in capsys.readouterr().out


def test_pam50_panel_must_be_exact_and_aliases_explicit() -> None:
    payload = load_payload()
    genes = payload["input_contract"]["canonical_gene_symbols"]  # type: ignore[index]
    genes[-1] = "NOT_A_PAM50_GENE"  # type: ignore[index]

    with pytest.raises(ValidationError, match="historical PAM50 50-gene panel"):
        SingleSampleReliabilitySpecification.model_validate(payload)


def test_draft_cannot_authorize_molecular_execution() -> None:
    payload = load_payload()
    payload["execution_authorized"] = True
    payload["molecular_data_access_authorized"] = True

    with pytest.raises(ValidationError, match="draft specification cannot authorize"):
        SingleSampleReliabilitySpecification.model_validate(payload)


def test_locked_specification_rejects_unresolved_dependencies() -> None:
    payload = load_payload()
    payload["status"] = "locked"
    payload["execution_authorized"] = True
    payload["molecular_data_access_authorized"] = True

    with pytest.raises(ValidationError, match="every dependency to be approved"):
        SingleSampleReliabilitySpecification.model_validate(payload)


def test_non_reliable_state_cannot_report_a_subtype() -> None:
    payload = load_payload()
    outputs = payload["outputs"]  # type: ignore[assignment]
    outputs["state_actions"]["unstable"] = "report_label"  # type: ignore[index]

    with pytest.raises(ValidationError, match="non-reliable state must abstain"):
        SingleSampleReliabilitySpecification.model_validate(payload)


def test_thresholds_cannot_be_tuned_on_outcomes_or_validation() -> None:
    payload = load_payload()
    thresholds = payload["thresholds"]  # type: ignore[assignment]
    thresholds[0]["outcome_guided_selection_allowed"] = True  # type: ignore[index]

    with pytest.raises(ValidationError, match="cannot be selected using outcomes"):
        SingleSampleReliabilitySpecification.model_validate(payload)


def test_minimum_perturbation_panel_requires_both_families() -> None:
    payload = load_payload()
    perturbations = payload["perturbations"]  # type: ignore[assignment]
    perturbations[1] = deepcopy(perturbations[0])  # type: ignore[index]
    perturbations[1]["perturbation_id"] = "logo-50-copy"  # type: ignore[index]

    with pytest.raises(ValidationError, match="requires both declared families"):
        SingleSampleReliabilitySpecification.model_validate(payload)


def test_canonical_scoring_cannot_depend_on_test_cohort_or_outcomes() -> None:
    payload = load_payload()
    classifier = payload["classifier"]  # type: ignore[assignment]
    classifier["outcome_guided_tuning_allowed"] = True  # type: ignore[index]

    with pytest.raises(ValidationError, match="cannot depend on test cohorts or outcomes"):
        SingleSampleReliabilitySpecification.model_validate(payload)
