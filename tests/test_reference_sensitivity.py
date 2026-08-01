from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import statistics
from pathlib import Path

import pytest

from nas_core.analysis.reference_sensitivity import (
    GSE81538ReferenceSensitivityService,
    ReferenceSensitivityError,
)
from nas_core.domain.matrix_audit import load_matrix_audit_receipt
from nas_core.domain.method_dependency import load_pam50_centroid_candidate
from nas_core.domain.reference_construction import load_reference_construction_receipt
from nas_core.domain.reference_development import load_reference_development_protocol
from nas_core.domain.reference_metadata import load_reference_metadata_receipt
from nas_core.domain.reference_sensitivity import (
    GSE81538ReferenceSensitivityPlan,
    GSE81538ReferenceSensitivityReceipt,
    load_reference_sensitivity_plan,
)
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "analysis/gse81538_reference_sensitivity_plan_v1.0.0.yaml"
MATRIX_AUDIT = STUDY / "ingestion/gse81538_matrix_audit_receipt_v1.0.0.yaml"
METADATA = STUDY / "ingestion/gse81538_reference_metadata_receipt_v1.0.0.yaml"
CONSTRUCTION = STUDY / "analysis/gse81538_reference_construction_receipt_v1.0.0.yaml"
PROTOCOL = STUDY / "protocol/reference_development_protocol_v1.1.0.yaml"
CANDIDATE = (
    STUDY
    / "protocol/artifact-candidates/genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
)
PLAN_SCHEMA = ROOT / "workflows/gse81538_reference_sensitivity_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/gse81538_reference_sensitivity_receipt.schema.json"


def _fixtures():
    store = InMemoryObjectStore()
    candidate = load_pam50_centroid_candidate(CANDIDATE)
    titles = [f"T{index}" for index in range(1, 101)]
    records = [
        {
            "sample_title": title,
            "geo_accession": f"GSM{index}",
            "er_stratum": "ER-negative" if index <= 50 else "ER-positive",
        }
        for index, title in enumerate(titles, start=1)
    ]
    manifest_bytes = (
        json.dumps({"records": records}, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()

    matrix_text = io.StringIO(newline="")
    writer = csv.writer(matrix_text)
    writer.writerow(["", *titles])
    vectors: dict[str, list[float]] = {}
    for gene_index, gene in enumerate(candidate.gene_order):
        outlier_count = gene_index % 26
        values = [
            float(gene_index + index / 10 * (1 + gene_index / 100))
            for index in range(100 - outlier_count)
        ]
        values.extend([float(1000 + gene_index)] * outlier_count)
        vectors[gene] = values
        writer.writerow([gene, *values])
    matrix_bytes = gzip.compress(matrix_text.getvalue().encode(), mtime=0)

    metadata_lines: list[str] = []
    for index in range(1, 183):
        code = 0 if index <= 50 or 101 <= index <= 132 else 3
        metadata_lines.extend(
            [
                f"^SAMPLE = GSM{index}",
                f"!Sample_geo_accession = GSM{index}",
                f"!Sample_characteristics_ch1 = er consensus: {code}",
            ]
        )
    metadata_bytes = gzip.compress(("\n".join(metadata_lines) + "\n").encode(), mtime=0)

    primary_reference = {
        gene: statistics.median(values) for gene, values in vectors.items()
    }
    reference_bytes = (
        json.dumps(
            {"gene_order": candidate.gene_order, "reference": primary_reference},
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()

    base = load_reference_sensitivity_plan(PLAN).model_dump(mode="json")
    base.update(
        {
            "matrix_object_key": "raw/test/matrix.csv.gz",
            "matrix_sha256": hashlib.sha256(matrix_bytes).hexdigest(),
            "metadata_object_key": "raw/test/family.soft.gz",
            "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
            "selection_manifest_object_key": "derived/test/manifest.json",
            "selection_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "primary_reference_object_key": "derived/test/reference.json",
            "primary_reference_sha256": hashlib.sha256(reference_bytes).hexdigest(),
            "sensitivity_object_key": "derived/test/sensitivity.json",
        }
    )
    plan = GSE81538ReferenceSensitivityPlan.model_validate(base)
    for key, data, content_type in (
        (plan.matrix_object_key, matrix_bytes, "application/gzip"),
        (plan.metadata_object_key, metadata_bytes, "application/gzip"),
        (plan.selection_manifest_object_key, manifest_bytes, "application/json"),
        (plan.primary_reference_object_key, reference_bytes, "application/json"),
    ):
        store.put_bytes(key, data, content_type=content_type)

    matrix_audit = load_matrix_audit_receipt(MATRIX_AUDIT)
    metadata = load_reference_metadata_receipt(METADATA).model_copy(
        update={"manifest_sha256": plan.selection_manifest_sha256}
    )
    construction = load_reference_construction_receipt(CONSTRUCTION).model_copy(
        update={"reference_sha256": plan.primary_reference_sha256}
    )
    protocol = load_reference_development_protocol(PROTOCOL)
    return store, plan, matrix_audit, metadata, construction, protocol, candidate


def test_reference_sensitivity_is_outcome_blind_and_reports_infeasibility() -> None:
    store, plan, matrix_audit, metadata, construction, protocol, candidate = _fixtures()

    receipt = GSE81538ReferenceSensitivityService(store=store).execute(
        plan,
        matrix_audit,
        metadata,
        construction,
        protocol,
        candidate,
        plan_path=PLAN,
        matrix_audit_path=MATRIX_AUDIT,
        metadata_receipt_path=METADATA,
        construction_receipt_path=CONSTRUCTION,
        protocol_path=PROTOCOL,
        candidate_path=CANDIDATE,
        code_revision="abcdef1",
    )

    assert receipt.decision.value == "pass_with_limitation"
    assert receipt.next_er_negative_available == 32
    assert receipt.next_er_positive_available == 50
    assert receipt.exact_alternative_balanced_reference_feasible is False
    assert receipt.vector_maximum_absolute_difference > 0
    assert -1 <= receipt.centered_profile_correlation_minimum <= 1
    assert receipt.outcome_values_accessed is False
    assert receipt.classifier_executed is False
    assert receipt.threshold_tuning_performed is False


def test_reference_sensitivity_rejects_changed_reference() -> None:
    store, plan, matrix_audit, metadata, construction, protocol, candidate = _fixtures()
    changed = plan.model_copy(update={"primary_reference_sha256": "0" * 64})

    with pytest.raises(ReferenceSensitivityError, match="reference"):
        GSE81538ReferenceSensitivityService(store=store).execute(
            changed,
            matrix_audit,
            metadata,
            construction,
            protocol,
            candidate,
            plan_path=PLAN,
            matrix_audit_path=MATRIX_AUDIT,
            metadata_receipt_path=METADATA,
            construction_receipt_path=CONSTRUCTION,
            protocol_path=PROTOCOL,
            candidate_path=CANDIDATE,
            code_revision="abcdef1",
        )


def test_reference_sensitivity_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text()) == (
        GSE81538ReferenceSensitivityPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        GSE81538ReferenceSensitivityReceipt.model_json_schema()
    )
