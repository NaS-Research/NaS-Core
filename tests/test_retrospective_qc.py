from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

from nas_core.analysis.retrospective_qc import RetrospectiveProcessedInputQCService
from nas_core.domain.retrospective_qc import (
    RetrospectiveProcessedInputQCReceipt,
    RetrospectiveProcessedInputQCSpecification,
    RetrospectiveQCState,
    RetrospectiveSourceRole,
    load_retrospective_processed_input_qc_specification,
)
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
SPECIFICATION = STUDY / "protocol/retrospective_processed_input_qc_specification_v1.0.0.yaml"
BRIDGE = STUDY / "protocol/retrospective_expression_bridge_receipt_v1.0.0.yaml"
RELIABILITY = STUDY / "protocol/reliability_specification.yaml"
SPECIFICATION_SCHEMA = ROOT / "workflows/retrospective_processed_input_qc_specification.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/retrospective_processed_input_qc_receipt.schema.json"


def _service() -> tuple[
    RetrospectiveProcessedInputQCService,
    RetrospectiveProcessedInputQCSpecification,
]:
    specification = load_retrospective_processed_input_qc_specification(SPECIFICATION)
    payload = json.dumps(
        {"reference": {gene: 0.0 for gene in specification.canonical_gene_symbols}}
    ).encode()
    specification = specification.model_copy(
        update={"reference_sha256": hashlib.sha256(payload).hexdigest()}
    )
    store = InMemoryObjectStore()
    store.put_bytes(specification.reference_object_key, payload, content_type="application/json")
    return RetrospectiveProcessedInputQCService(specification, store=store), specification


def _profile(specification: RetrospectiveProcessedInputQCSpecification) -> dict[str, float]:
    return {
        gene: float(index + 1)
        for index, gene in enumerate(specification.canonical_gene_symbols)
    }


def test_valid_tcga_profile_is_transformed_centered_and_allowed_to_score() -> None:
    service, specification = _service()
    result, centered = service.evaluate(
        RetrospectiveSourceRole.TCGA_DISCOVERY,
        _profile(specification),
    )
    assert result.state is RetrospectiveQCState.VALID
    assert result.report_action == "continue_to_locked_scoring"
    assert centered is not None and len(centered) == 50
    assert centered[0] == pytest.approx(math.log2(1.1))


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("missing", RetrospectiveQCState.INSUFFICIENT_GENE_COVERAGE),
        ("extra", RetrospectiveQCState.SCHEMA_MISMATCH),
        ("duplicate_alias", RetrospectiveQCState.DUPLICATE_MAPPING),
        ("nonfinite", RetrospectiveQCState.NONFINITE_INPUT),
        ("negative", RetrospectiveQCState.NEGATIVE_FPKM),
        ("constant", RetrospectiveQCState.CONSTANT_CENTERED_PROFILE),
    ],
)
def test_tcga_profile_failures_abstain(
    mutation: str,
    expected: RetrospectiveQCState,
) -> None:
    service, specification = _service()
    values = _profile(specification)
    if mutation == "missing":
        values.pop("ACTR3B")
    elif mutation == "extra":
        values["NOT_PAM50"] = 1.0
    elif mutation == "duplicate_alias":
        values["CDCA1"] = values["NUF2"]
    elif mutation == "nonfinite":
        values["ACTR3B"] = math.nan
    elif mutation == "negative":
        values["ACTR3B"] = -0.01
    else:
        values = {gene: 0.0 for gene in specification.canonical_gene_symbols}
    result, centered = service.evaluate(
        RetrospectiveSourceRole.TCGA_DISCOVERY,
        values,
    )
    assert result.state is expected
    assert result.report_action == "abstain"
    assert centered is None


def test_validation_below_declared_floor_abstains() -> None:
    service, specification = _service()
    values = _profile(specification)
    values["ACTR3B"] = specification.validation_declared_floor - 0.01
    result, centered = service.evaluate(
        RetrospectiveSourceRole.GSE96058_VALIDATION,
        values,
    )
    assert result.state is RetrospectiveQCState.BELOW_DECLARED_FLOOR
    assert centered is None


def test_qc_freeze_receipt_preserves_zero_access_and_execution() -> None:
    service, _specification = _service()
    receipt = service.freeze_receipt(
        specification_path=SPECIFICATION,
        bridge_receipt_path=BRIDGE,
        reliability_specification_path=RELIABILITY,
        code_revision="669df84",
    )
    assert receipt.decision == "retrospective_processed_input_qc_frozen"
    assert receipt.failure_state_count == 7
    assert receipt.imputation_prohibited is True
    assert receipt.scientific_failure_rerun_prohibited is True
    assert receipt.classifier_executed is False
    assert receipt.outcomes_accessed is False


def test_qc_specification_rejects_scientific_failure_rerun() -> None:
    specification = load_retrospective_processed_input_qc_specification(SPECIFICATION)
    with pytest.raises(ValueError, match="cannot impute"):
        RetrospectiveProcessedInputQCSpecification.model_validate(
            {**specification.model_dump(), "scientific_qc_rerun_allowed": True}
        )


def test_retrospective_qc_schemas_match_runtime_models() -> None:
    assert json.loads(SPECIFICATION_SCHEMA.read_text()) == (
        RetrospectiveProcessedInputQCSpecification.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        RetrospectiveProcessedInputQCReceipt.model_json_schema()
    )
