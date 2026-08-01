from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from nas_core.analysis.retrospective_bridge import (
    RetrospectiveExpressionBridgeError,
    RetrospectiveExpressionBridgeService,
)
from nas_core.domain.retrospective_bridge import (
    RetrospectiveExpressionBridgePlan,
    RetrospectiveExpressionBridgeReceipt,
    load_retrospective_expression_bridge_plan,
)
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "protocol/retrospective_expression_bridge_plan_v1.0.0.yaml"
CANDIDATE = STUDY / "protocol/artifact-candidates/genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
IMPORT = STUDY / "protocol/artifact-candidates/genefu_2.44.0_pam50_import_receipt_v1.0.0.yaml"
REFERENCE = STUDY / "analysis/gse81538_reference_construction_receipt_v1.0.0.yaml"
MATRIX_AUDIT = STUDY / "ingestion/gse81538_matrix_audit_receipt_v1.0.0.yaml"
METADATA = STUDY / "ingestion/field_isolated_metadata_receipt_v1.0.1.yaml"
CONFORMANCE = STUDY / "protocol/numerical_conformance_receipt_v1.0.0.yaml"
SPECIFICATION = STUDY / "protocol/reliability_specification.yaml"
PLAN_SCHEMA = ROOT / "workflows/retrospective_expression_bridge_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/retrospective_expression_bridge_receipt.schema.json"


def _execute(plan: RetrospectiveExpressionBridgePlan) -> RetrospectiveExpressionBridgeReceipt:
    genes = yaml.safe_load(CANDIDATE.read_text())["gene_order"]
    payload = json.dumps({"reference": {gene: 0.0 for gene in genes}}).encode()
    synthetic = plan.model_copy(
        update={"reference_sha256": hashlib.sha256(payload).hexdigest()}
    )
    store = InMemoryObjectStore()
    store.put_bytes(synthetic.reference_object_key, payload, content_type="application/json")
    return RetrospectiveExpressionBridgeService(store=store).freeze(
        synthetic,
        plan_path=PLAN,
        centroid_candidate_path=CANDIDATE,
        centroid_import_receipt_path=IMPORT,
        reference_construction_receipt_path=REFERENCE,
        matrix_audit_receipt_path=MATRIX_AUDIT,
        metadata_receipt_path=METADATA,
        numerical_conformance_receipt_path=CONFORMANCE,
        reliability_specification_path=SPECIFICATION,
        code_revision="bfe9289",
    )


def test_retrospective_bridge_freezes_without_execution_or_adaptation() -> None:
    receipt = _execute(load_retrospective_expression_bridge_plan(PLAN))
    assert receipt.decision == "retrospective_research_bridge_frozen"
    assert receipt.reference_gene_count == 50
    assert receipt.centroid_gene_count == 50
    assert receipt.centroid_subtype_count == 5
    assert receipt.tcga_input_field == "fpkm_unstranded"
    assert receipt.tcga_transform == "log2_fpkm_plus_0_1"
    assert receipt.gse96058_transform == "consume_unchanged"
    assert receipt.performance_blind_validation_bridge_frozen is True
    assert receipt.prospective_primary_assay_selected is False
    assert receipt.classifier_executed is False
    assert receipt.outcomes_accessed is False


def test_retrospective_bridge_rejects_changed_evidence(tmp_path: Path) -> None:
    changed = tmp_path / "candidate.yaml"
    changed.write_text("changed: true\n", encoding="utf-8")
    plan = load_retrospective_expression_bridge_plan(PLAN)
    genes = yaml.safe_load(CANDIDATE.read_text())["gene_order"]
    payload = json.dumps({"reference": {gene: 0.0 for gene in genes}}).encode()
    plan = plan.model_copy(update={"reference_sha256": hashlib.sha256(payload).hexdigest()})
    store = InMemoryObjectStore()
    store.put_bytes(plan.reference_object_key, payload, content_type="application/json")
    with pytest.raises(RetrospectiveExpressionBridgeError, match="evidence"):
        RetrospectiveExpressionBridgeService(store=store).freeze(
            plan,
            plan_path=PLAN,
            centroid_candidate_path=changed,
            centroid_import_receipt_path=IMPORT,
            reference_construction_receipt_path=REFERENCE,
            matrix_audit_receipt_path=MATRIX_AUDIT,
            metadata_receipt_path=METADATA,
            numerical_conformance_receipt_path=CONFORMANCE,
            reliability_specification_path=SPECIFICATION,
            code_revision="bfe9289",
        )


def test_bridge_plan_rejects_validation_adaptation() -> None:
    plan = load_retrospective_expression_bridge_plan(PLAN)
    with pytest.raises(ValueError, match="cannot adapt"):
        RetrospectiveExpressionBridgePlan.model_validate(
            {**plan.model_dump(), "validation_adaptation_allowed": True}
        )


def test_retrospective_bridge_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text()) == (
        RetrospectiveExpressionBridgePlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        RetrospectiveExpressionBridgeReceipt.model_json_schema()
    )
