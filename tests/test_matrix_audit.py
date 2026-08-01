from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.matrix_audit import (
    GSE81538MatrixAuditPlan,
    GSE81538MatrixAuditReceipt,
    MatrixAuditDecision,
    load_matrix_audit_plan,
)
from nas_core.domain.method_dependency import load_pam50_centroid_candidate
from nas_core.domain.public_artifact import (
    load_public_artifact_receipt,
)
from nas_core.ingestion.gdc import sha256
from nas_core.ingestion.matrix_audit import (
    GSE81538MatrixAuditService,
    MatrixAuditError,
)
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import FileSystemObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "ingestion/gse81538_matrix_audit_plan_v1.0.0.yaml"
ACQUISITION = STUDY / "ingestion/gse81538_acquisition_receipt_v1.0.0.yaml"
CANDIDATE = STUDY / "protocol/artifact-candidates/genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
REFERENCE = STUDY / "protocol/reference_development_protocol_v1.0.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/gse81538_matrix_audit_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/gse81538_matrix_audit_receipt.schema.json"
NOW = datetime(2026, 8, 1, 18, 0, tzinfo=UTC)


def _matrix_bytes(*, wrong_header: bool = False, missing_panel: bool = False) -> bytes:
    candidate = load_pam50_centroid_candidate(CANDIDATE)
    reverse_aliases = {
        canonical: historical for historical, canonical in candidate.historical_aliases.items()
    }
    genes = [reverse_aliases.get(gene, gene) for gene in candidate.gene_order]
    if missing_panel:
        genes[-1] = "SYNTHETIC_NON_PANEL_GENE"
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["", "T1", "T2" if not wrong_header else "X2", "T3"])
    for index, gene in enumerate(genes):
        values = ["-3.321928094887362", str(index / 10), str(index / 10 + 0.5)]
        writer.writerow([gene, *values])
    return gzip.compress(output.getvalue().encode("utf-8"), mtime=0)


def _audit_fixture(
    tmp_path: Path,
    *,
    wrong_header: bool = False,
    missing_panel: bool = False,
) -> tuple[
    GSE81538MatrixAuditService,
    GSE81538MatrixAuditPlan,
    Path,
    Path,
]:
    payload = _matrix_bytes(wrong_header=wrong_header, missing_panel=missing_panel)
    data_root = tmp_path / "NaS-Core-Data"
    DataLayout(data_root).initialize()
    store = FileSystemObjectStore(data_root)
    base_plan = load_matrix_audit_plan(PLAN)
    store.put_bytes(base_plan.object_key, payload, content_type="application/gzip")

    acquisition = load_public_artifact_receipt(ACQUISITION).model_copy(
        update={
            "content_length_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
    acquisition_path = tmp_path / "acquisition.yaml"
    acquisition_path.write_text(
        yaml.safe_dump(acquisition.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    plan = base_plan.model_copy(
        update={
            "acquisition_receipt_sha256": sha256(acquisition_path.read_bytes()),
            "expected_compressed_sha256": hashlib.sha256(payload).hexdigest(),
            "expected_compressed_bytes": len(payload),
            "expected_gene_rows": 50,
            "expected_sample_columns": 3,
        }
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(plan.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return GSE81538MatrixAuditService(store=store), plan, plan_path, acquisition_path


def _execute(
    service: GSE81538MatrixAuditService,
    plan: GSE81538MatrixAuditPlan,
    plan_path: Path,
    acquisition_path: Path,
) -> GSE81538MatrixAuditReceipt:
    return service.audit(
        plan,
        load_public_artifact_receipt(acquisition_path),
        load_pam50_centroid_candidate(CANDIDATE),
        plan_path=plan_path,
        acquisition_path=acquisition_path,
        candidate_path=CANDIDATE,
        reference_protocol_path=REFERENCE,
        code_revision="abcdef1",
        audited_at=NOW,
    )


def test_matrix_audit_streams_complete_panel_without_outcomes(tmp_path: Path) -> None:
    service, plan, plan_path, acquisition_path = _audit_fixture(tmp_path)

    receipt = _execute(service, plan, plan_path, acquisition_path)

    assert receipt.decision is MatrixAuditDecision.PASS
    assert receipt.gene_row_count == 50
    assert receipt.sample_column_count == 3
    assert receipt.total_measurement_count == 150
    assert receipt.finite_measurement_count == 150
    assert receipt.zero_floor_count == 50
    assert receipt.resolved_pam50_gene_count == 50
    assert receipt.historical_aliases_applied == {
        "CDCA1": "NUF2",
        "KNTC2": "NDC80",
        "ORC6L": "ORC6",
    }
    assert receipt.outcome_values_accessed is False
    assert receipt.sample_rows_retained is False
    assert receipt.classifier_executed is False
    assert receipt.reference_vector_materialized is False


def test_matrix_audit_fails_closed_on_changed_header(tmp_path: Path) -> None:
    service, plan, plan_path, acquisition_path = _audit_fixture(tmp_path, wrong_header=True)

    receipt = _execute(service, plan, plan_path, acquisition_path)

    assert receipt.decision is MatrixAuditDecision.CHANGES_REQUIRED
    assert receipt.sample_header_sequence_verified is False


def test_matrix_audit_fails_closed_on_missing_panel_gene(tmp_path: Path) -> None:
    service, plan, plan_path, acquisition_path = _audit_fixture(tmp_path, missing_panel=True)

    receipt = _execute(service, plan, plan_path, acquisition_path)

    assert receipt.decision is MatrixAuditDecision.CHANGES_REQUIRED
    assert receipt.resolved_pam50_gene_count == 49
    assert receipt.missing_pam50_genes == ["UBE2T"]


def test_matrix_audit_rejects_changed_provenance(tmp_path: Path) -> None:
    service, plan, plan_path, acquisition_path = _audit_fixture(tmp_path)
    changed = plan.model_copy(update={"reference_protocol_sha256": "0" * 64})

    with pytest.raises(MatrixAuditError, match="reference protocol"):
        _execute(service, changed, plan_path, acquisition_path)


def test_matrix_audit_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")) == (
        GSE81538MatrixAuditPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8")) == (
        GSE81538MatrixAuditReceipt.model_json_schema()
    )
