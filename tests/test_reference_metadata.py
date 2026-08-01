from __future__ import annotations

import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.matrix_audit import load_matrix_audit_receipt
from nas_core.domain.public_artifact import load_public_artifact_receipt
from nas_core.domain.reference_development import load_reference_development_protocol
from nas_core.domain.reference_input import load_reference_input_founder_decision
from nas_core.domain.reference_metadata import (
    GSE81538ReferenceMetadataPlan,
    GSE81538ReferenceMetadataReceipt,
    ReferenceMetadataDecision,
    load_reference_metadata_plan,
    load_reference_metadata_receipt,
)
from nas_core.ingestion.gdc import sha256
from nas_core.ingestion.reference_metadata import (
    GSE81538ReferenceMetadataService,
    ReferenceMetadataError,
)
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import FileSystemObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
EXECUTED_RECEIPT = STUDY / "ingestion/gse81538_reference_metadata_receipt_v1.0.0.yaml"
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PLAN = STUDY / "ingestion/gse81538_reference_metadata_plan_v1.0.0.yaml"
ACQUISITION = STUDY / "ingestion/gse81538_family_soft_acquisition_receipt_v1.0.0.yaml"
MATRIX_AUDIT = STUDY / "ingestion/gse81538_matrix_audit_receipt_v1.0.0.yaml"
DECISION = STUDY / "reviews/FOUNDER_REFERENCE_INPUT_DECISION_v1.1.0.yaml"
PROTOCOL = STUDY / "protocol/reference_development_protocol_v1.1.0.yaml"
PLAN_SCHEMA = ROOT / "workflows/gse81538_reference_metadata_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/gse81538_reference_metadata_receipt.schema.json"
NOW = datetime(2026, 8, 1, 17, 0, tzinfo=UTC)


def _soft_bytes(*, duplicate_title: bool = False) -> bytes:
    codes = [*([0] * 50), 1, 2, *([3] * 50)]
    lines = ["^SERIES = GSE81538"]
    for index, code in enumerate(codes, start=1):
        title = "T1" if duplicate_title and index == 2 else f"T{index}"
        lines.extend(
            (
                f"^SAMPLE = GSM{1000 + index}",
                f"!Sample_title = {title}",
                f"!Sample_geo_accession = GSM{1000 + index}",
                "!Sample_characteristics_ch1 = survival months: 999",
                "!Sample_characteristics_ch1 = treatment: prohibited fixture",
                f"!Sample_characteristics_ch1 = er consensus: {code}",
            )
        )
    return gzip.compress(("\n".join(lines) + "\n").encode("utf-8"), mtime=0)


def _fixture(
    tmp_path: Path,
    *,
    duplicate_title: bool = False,
) -> tuple[
    GSE81538ReferenceMetadataService,
    FileSystemObjectStore,
    GSE81538ReferenceMetadataPlan,
    Path,
    Path,
    Path,
]:
    payload = _soft_bytes(duplicate_title=duplicate_title)
    data_root = tmp_path / "NaS-Core-Data"
    DataLayout(data_root).initialize()
    store = FileSystemObjectStore(data_root)
    base_plan = load_reference_metadata_plan(PLAN)
    store.put_bytes(base_plan.metadata_object_key, payload, content_type="application/gzip")

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
    matrix_audit = load_matrix_audit_receipt(MATRIX_AUDIT).model_copy(
        update={
            "expected_sample_column_count": 102,
            "sample_column_count": 102,
        }
    )
    matrix_audit_path = tmp_path / "matrix-audit.yaml"
    matrix_audit_path.write_text(
        yaml.safe_dump(matrix_audit.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    plan = base_plan.model_copy(
        update={
            "metadata_acquisition_receipt_sha256": sha256(
                acquisition_path.read_bytes()
            ),
            "matrix_audit_receipt_sha256": sha256(matrix_audit_path.read_bytes()),
            "expected_metadata_sha256": hashlib.sha256(payload).hexdigest(),
            "expected_metadata_bytes": len(payload),
            "expected_sample_count": 102,
        }
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(plan.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return (
        GSE81538ReferenceMetadataService(store=store),
        store,
        plan,
        plan_path,
        acquisition_path,
        matrix_audit_path,
    )


def _execute(
    service: GSE81538ReferenceMetadataService,
    plan: GSE81538ReferenceMetadataPlan,
    plan_path: Path,
    acquisition_path: Path,
    matrix_audit_path: Path,
) -> GSE81538ReferenceMetadataReceipt:
    return service.select(
        plan,
        load_public_artifact_receipt(acquisition_path),
        load_matrix_audit_receipt(matrix_audit_path),
        load_reference_input_founder_decision(DECISION),
        load_reference_development_protocol(PROTOCOL),
        plan_path=plan_path,
        acquisition_path=acquisition_path,
        matrix_audit_path=matrix_audit_path,
        founder_decision_path=DECISION,
        protocol_path=PROTOCOL,
        code_revision="abcdef1",
        audited_at=NOW,
    )


def test_reference_metadata_selects_external_manifest_without_outcomes(
    tmp_path: Path,
) -> None:
    service, store, plan, plan_path, acquisition_path, matrix_audit_path = _fixture(
        tmp_path
    )

    receipt = _execute(
        service,
        plan,
        plan_path,
        acquisition_path,
        matrix_audit_path,
    )

    assert receipt.decision is ReferenceMetadataDecision.PASS
    assert receipt.er_consensus_counts == {0: 50, 1: 1, 2: 1, 3: 50}
    assert receipt.ambiguous_excluded_count == 2
    assert receipt.manifest_record_count == 100
    assert receipt.participant_identifiers_retained_in_git is False
    assert receipt.outcome_values_accessed is False
    assert receipt.expression_values_accessed is False
    manifest = json.loads(store.get_bytes(plan.manifest_object_key))
    assert [record["er_stratum"] for record in manifest["records"][:50]] == [
        "ER-negative"
    ] * 50
    assert [record["er_stratum"] for record in manifest["records"][50:]] == [
        "ER-positive"
    ] * 50
    assert all("survival" not in record for record in manifest["records"])
    receipt_text = yaml.safe_dump(receipt.model_dump(mode="json"))
    assert "GSM1001" not in receipt_text


def test_reference_metadata_rejects_duplicate_title(tmp_path: Path) -> None:
    service, _, plan, plan_path, acquisition_path, matrix_audit_path = _fixture(
        tmp_path,
        duplicate_title=True,
    )

    with pytest.raises(ReferenceMetadataError, match="duplicate sample titles"):
        _execute(
            service,
            plan,
            plan_path,
            acquisition_path,
            matrix_audit_path,
        )


def test_reference_metadata_rejects_changed_founder_decision(tmp_path: Path) -> None:
    service, _, plan, plan_path, acquisition_path, matrix_audit_path = _fixture(
        tmp_path
    )
    changed = plan.model_copy(update={"founder_decision_sha256": "0" * 64})

    with pytest.raises(ReferenceMetadataError, match="founder decision"):
        _execute(
            service,
            changed,
            plan_path,
            acquisition_path,
            matrix_audit_path,
        )


def test_reference_metadata_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")) == (
        GSE81538ReferenceMetadataPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8")) == (
        GSE81538ReferenceMetadataReceipt.model_json_schema()
    )


def test_executed_reference_metadata_receipt_is_valid_and_field_isolated() -> None:
    receipt = load_reference_metadata_receipt(EXECUTED_RECEIPT)

    assert receipt.decision.value == "pass"
    assert receipt.sample_record_count == 405
    assert receipt.er_consensus_counts == {0: 82, 1: 8, 2: 11, 3: 304}
    assert receipt.selected_negative_count == 50
    assert receipt.selected_positive_count == 50
    assert receipt.participant_identifiers_retained_in_git is False
    assert receipt.expression_values_accessed is False
    assert receipt.outcome_values_accessed is False
