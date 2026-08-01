from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

import pytest

from nas_core.analysis.reference_construction import (
    GSE81538ReferenceConstructionService,
    ReferenceConstructionError,
)
from nas_core.domain.matrix_audit import load_matrix_audit_receipt
from nas_core.domain.method_dependency import load_pam50_centroid_candidate
from nas_core.domain.reference_construction import (
    GSE81538ReferenceConstructionPlan,
    GSE81538ReferenceConstructionReceipt,
    load_reference_construction_plan,
)
from nas_core.domain.reference_development import load_reference_development_protocol
from nas_core.domain.reference_metadata import load_reference_metadata_receipt
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "analysis/gse81538_reference_construction_plan_v1.0.0.yaml"
MATRIX_AUDIT = STUDY / "ingestion/gse81538_matrix_audit_receipt_v1.0.0.yaml"
METADATA = STUDY / "ingestion/gse81538_reference_metadata_receipt_v1.0.0.yaml"
PROTOCOL = STUDY / "protocol/reference_development_protocol_v1.1.0.yaml"
CANDIDATE = (
    STUDY
    / "protocol/artifact-candidates/genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
)
PLAN_SCHEMA = ROOT / "workflows/gse81538_reference_construction_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/gse81538_reference_construction_receipt.schema.json"


def _fixtures() -> tuple[
    InMemoryObjectStore,
    GSE81538ReferenceConstructionPlan,
    object,
    object,
    object,
    object,
]:
    store = InMemoryObjectStore()
    candidate = load_pam50_centroid_candidate(CANDIDATE)
    titles = [f"T{index}" for index in range(1, 101)]
    manifest = {
        "records": [
            {
                "sample_title": title,
                "geo_accession": f"GSM{index}",
                "er_stratum": "ER-negative" if index <= 50 else "ER-positive",
            }
            for index, title in enumerate(titles, start=1)
        ]
    }
    manifest_bytes = (
        json.dumps(manifest, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()
    matrix_text = io.StringIO(newline="")
    writer = csv.writer(matrix_text)
    writer.writerow(["", *titles])
    for gene_index, gene in enumerate(candidate.gene_order):
        writer.writerow([gene, *[gene_index + index / 10 for index in range(100)]])
    matrix_bytes = gzip.compress(matrix_text.getvalue().encode(), mtime=0)

    base = load_reference_construction_plan(PLAN).model_dump(mode="json")
    base.update(
        {
            "matrix_object_key": "raw/test/matrix.csv.gz",
            "matrix_sha256": hashlib.sha256(matrix_bytes).hexdigest(),
            "matrix_bytes": len(matrix_bytes),
            "selection_manifest_object_key": "derived/test/manifest.json",
            "selection_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "reference_object_key": "derived/test/reference.json",
        }
    )
    plan = GSE81538ReferenceConstructionPlan.model_validate(base)
    store.put_bytes(plan.matrix_object_key, matrix_bytes, content_type="application/gzip")
    store.put_bytes(
        plan.selection_manifest_object_key,
        manifest_bytes,
        content_type="application/json",
    )
    matrix_audit = load_matrix_audit_receipt(MATRIX_AUDIT)
    metadata = load_reference_metadata_receipt(METADATA).model_copy(
        update={"manifest_sha256": plan.selection_manifest_sha256}
    )
    protocol = load_reference_development_protocol(PROTOCOL)
    return store, plan, matrix_audit, metadata, protocol, candidate


def test_reference_construction_is_deterministic_and_outcome_blind() -> None:
    store, plan, matrix_audit, metadata, protocol, candidate = _fixtures()

    receipt = GSE81538ReferenceConstructionService(store=store).construct(
        plan,
        matrix_audit,
        metadata,
        protocol,
        candidate,
        plan_path=PLAN,
        matrix_audit_path=MATRIX_AUDIT,
        metadata_receipt_path=METADATA,
        protocol_path=PROTOCOL,
        candidate_path=CANDIDATE,
        code_revision="abcdef1",
    )

    artifact = json.loads(store.get_bytes(plan.reference_object_key))
    assert receipt.decision.value == "pass"
    assert receipt.parsed_measurement_count == 5000
    assert receipt.reference_gene_count == 50
    assert artifact["reference"][candidate.gene_order[0]] == pytest.approx(4.95)
    assert artifact["reference"][candidate.gene_order[-1]] == pytest.approx(53.95)
    assert receipt.participant_identifiers_retained_in_git is False
    assert receipt.outcome_values_accessed is False
    assert receipt.classifier_executed is False


def test_reference_construction_rejects_changed_manifest() -> None:
    store, plan, matrix_audit, metadata, protocol, candidate = _fixtures()
    changed = plan.model_copy(update={"selection_manifest_sha256": "0" * 64})

    with pytest.raises(ReferenceConstructionError, match="manifest"):
        GSE81538ReferenceConstructionService(store=store).construct(
            changed,
            matrix_audit,
            metadata,
            protocol,
            candidate,
            plan_path=PLAN,
            matrix_audit_path=MATRIX_AUDIT,
            metadata_receipt_path=METADATA,
            protocol_path=PROTOCOL,
            candidate_path=CANDIDATE,
            code_revision="abcdef1",
        )


def test_reference_construction_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text()) == (
        GSE81538ReferenceConstructionPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        GSE81538ReferenceConstructionReceipt.model_json_schema()
    )
