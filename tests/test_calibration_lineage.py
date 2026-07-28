from __future__ import annotations

import gzip
import io
import json
from contextlib import AbstractContextManager, nullcontext
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nas_core.domain.calibration_lineage import (
    CalibrationLineageAuditReceipt,
)
from nas_core.domain.method_dependency import load_method_route_activation
from nas_core.ingestion.calibration_lineage import (
    CALIBRATION_LINEAGE_URLS,
    GSE60788_SOFT_URL,
    GSE96058_SOFT_URL,
    GSE130397_SOFT_URL,
    CalibrationLineageAuditService,
    CalibrationLineageError,
)
from nas_core.ingestion.field_isolated_metadata import StreamingResponse
from nas_core.ingestion.gdc import sha256

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
ACTIVATION = STUDY / "protocol" / "method_route_activation_v1.0.0.yaml"
SCHEMA = ROOT / "workflows" / "calibration_lineage_audit_receipt.schema.json"
REAL_RECEIPT = (
    STUDY / "ingestion" / "calibration_lineage_receipt_v1.0.0.yaml"
)
NOW = datetime(2026, 7, 28, 21, 0, tzinfo=UTC)


def _soft(records: list[tuple[str, str]]) -> bytes:
    text = "".join(
        f"^SAMPLE = {accession}\n"
        f"!Sample_title = {title}\n"
        "!Sample_characteristics_ch1 = overall survival: PROHIBITED\n"
        for accession, title in records
    )
    return gzip.compress(text.encode(), mtime=0)


class FakeTransport:
    def __init__(self, *, duplicate_title: bool = False) -> None:
        title = "P1" if duplicate_title else "P2"
        self.payloads = {
            GSE60788_SOFT_URL: _soft(
                [
                    ("GSM1000001", "P1"),
                    ("GSM1000002", "P1-replicate"),
                    ("GSM1000003", title),
                ]
            ),
            GSE96058_SOFT_URL: _soft(
                [
                    ("GSM2000001", "F1"),
                    ("GSM2000002", "F1repl"),
                    ("GSM2000003", "F2"),
                ]
            ),
            GSE130397_SOFT_URL: _soft(
                [
                    ("GSM3000001", "FFPE-RNA-Seq_OVA_S1_01"),
                    ("GSM3000002", "FFPE-RNA-Seq_OVA_S1_02"),
                    ("GSM3000003", "FFPE-RNA-Seq_OVA_S1_03"),
                    ("GSM3000004", "FFPE-RNA-Seq_ACC_ER_S01"),
                    ("GSM3000005", "FFPE-RNA-Seq_ACC_ER_S01_Reseq"),
                ]
            ),
        }

    def open_get(self, url: str) -> AbstractContextManager[StreamingResponse]:
        return nullcontext(
            StreamingResponse(200, {}, io.BytesIO(self.payloads[url]))
        )


def test_lineage_audit_retains_aggregates_only() -> None:
    receipt = CalibrationLineageAuditService(FakeTransport()).execute(
        route_activation=load_method_route_activation(ACTIVATION),
        route_activation_path=ACTIVATION,
        code_revision="0ee2112",
        executed_at=NOW,
    )

    assert receipt.route_activation_sha256 == sha256(ACTIVATION.read_bytes())
    assert len(receipt.artifacts) == 3
    assert set(CALIBRATION_LINEAGE_URLS) == {
        artifact.source_id for artifact in receipt.artifacts
    }
    by_source = {summary.source_id: summary for summary in receipt.summaries}
    assert by_source["GEO:GSE60788"].sample_record_count == 3
    assert by_source["GEO:GSE60788"].replicate_labeled_record_count == 1
    assert by_source["GEO:GSE60788"].linked_replicate_record_count == 1
    assert by_source["GEO:GSE96058"].replicate_labeled_record_count == 1
    assert by_source["GEO:GSE130397"].replicate_labeled_record_count == 3
    assert by_source["GEO:GSE130397"].unique_replicate_group_count == 2
    assert receipt.gse60788_gse96058_accession_overlap_count == 0
    assert receipt.gse60788_gse96058_title_overlap_count == 0
    assert receipt.biological_sample_nonoverlap_established is False
    assert receipt.patient_level_records_retained is False
    assert receipt.sample_identifiers_retained is False
    assert receipt.molecular_values_parsed is False
    assert receipt.outcome_values_parsed is False
    assert receipt.raw_artifacts_stored is False


def test_lineage_audit_rejects_duplicate_titles() -> None:
    with pytest.raises(CalibrationLineageError, match="duplicate title"):
        CalibrationLineageAuditService(
            FakeTransport(duplicate_title=True)
        ).execute(
            route_activation=load_method_route_activation(ACTIVATION),
            route_activation_path=ACTIVATION,
            code_revision="0ee2112",
            executed_at=NOW,
        )


def test_checked_in_lineage_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationLineageAuditReceipt.model_json_schema()
    )


def test_checked_in_lineage_receipt_records_only_verified_aggregates() -> None:
    from nas_core.domain.calibration_lineage import (
        load_calibration_lineage_receipt,
    )

    receipt = load_calibration_lineage_receipt(REAL_RECEIPT)
    by_source = {summary.source_id: summary for summary in receipt.summaries}

    assert receipt.code_revision == "d256342"
    assert by_source["GEO:GSE60788"].sample_record_count == 55
    assert by_source["GEO:GSE60788"].replicate_labeled_record_count == 6
    assert by_source["GEO:GSE96058"].sample_record_count == 3409
    assert by_source["GEO:GSE96058"].replicate_labeled_record_count == 136
    assert by_source["GEO:GSE130397"].sample_record_count == 21
    assert by_source["GEO:GSE130397"].replicate_labeled_record_count == 11
    assert receipt.gse60788_gse96058_accession_overlap_count == 0
    assert receipt.gse60788_gse96058_title_overlap_count == 0
    assert receipt.biological_sample_nonoverlap_established is False
    assert receipt.sample_identifiers_retained is False
    assert receipt.molecular_values_parsed is False
    assert receipt.outcome_values_parsed is False
