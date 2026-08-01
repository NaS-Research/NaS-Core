from __future__ import annotations

import gzip
import hashlib
import json
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

import yaml

from nas_core.domain.calibration_annotation import (
    CalibrationAnnotationAcquisitionPlan,
    CalibrationAnnotationAcquisitionReceipt,
    CalibrationAnnotationResolutionPlan,
    CalibrationAnnotationResolutionReceipt,
)
from nas_core.ingestion.calibration_annotation import (
    CalibrationAnnotationResolutionService,
)
from nas_core.ingestion.field_isolated_metadata import StreamingResponse

ROOT = Path(__file__).parents[1]
PLAN_SCHEMA = ROOT / "workflows/calibration_annotation_resolution_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/calibration_annotation_resolution_receipt.schema.json"
ACQUISITION_PLAN_SCHEMA = ROOT / "workflows/calibration_annotation_acquisition_plan.schema.json"
ACQUISITION_RECEIPT_SCHEMA = (
    ROOT / "workflows/calibration_annotation_acquisition_receipt.schema.json"
)


def _sample(title: str) -> str:
    processing = [
        "STAR version 2.5.2b was used to align reads to human reference genome GRCh38, release 84",
        "GeneCounts module in STAR was used to quantify genes",
    ]
    if "_ACC_" in title:
        processing.append("reverse strand counts used for Access samples (files contain _ACC_)")
    else:
        processing.append(
            "forward strand counts used for Nugen-Ovation samples (files contain _OVA_)"
        )
    lines = [f"^SAMPLE = GSM{title}", f"!Sample_title = {title}"]
    lines.extend(f"!Sample_data_processing = {line}" for line in processing)
    return "\n".join(lines) + "\n"


class FakeTransport:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    @contextmanager
    def open_get(self, url: str):  # type: ignore[no-untyped-def]
        del url
        yield StreamingResponse(200, {}, BytesIO(self.payload))


def test_resolution_reconciles_every_library_directive(tmp_path: Path) -> None:
    titles = [f"FFPE-RNA-Seq_ACC_S1_{i:02d}" for i in range(1, 16)]
    titles += [f"FFPE-RNA-Seq_OVA_S1_{i:02d}" for i in range(1, 7)]
    payload = gzip.compress("".join(_sample(title) for title in titles).encode())
    feasibility_path = tmp_path / "feasibility.yaml"
    lineage_path = tmp_path / "lineage.yaml"
    feasibility_path.write_text("fixture: feasibility\n", encoding="utf-8")
    lineage_path.write_text("fixture: lineage\n", encoding="utf-8")
    plan = CalibrationAnnotationResolutionPlan(
        plan_version="1.0.0",
        feasibility_audit_receipt_sha256=hashlib.sha256(
            feasibility_path.read_bytes()
        ).hexdigest(),
        lineage_receipt_sha256=hashlib.sha256(lineage_path.read_bytes()).hexdigest(),
        expected_family_soft_sha256=hashlib.sha256(payload).hexdigest(),
        family_soft_url="https://ftp.ncbi.nlm.nih.gov/family.soft.gz",
        candidate_annotation_url=(
            "https://ftp.ensembl.org/pub/release-84/gtf/homo_sapiens/"
            "Homo_sapiens.GRCh38.84.gtf.gz"
        ),
        candidate_annotation_length_bytes=45686368,
        retain_sample_identifiers=False,
        retain_processing_rows=False,
        molecular_values_requested=False,
        outcomes_requested=False,
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(plan.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )

    receipt = CalibrationAnnotationResolutionService(FakeTransport(payload)).execute(
        plan,
        plan_path=plan_path,
        feasibility_audit_receipt_path=feasibility_path,
        lineage_receipt_path=lineage_path,
        code_revision="1234567",
    )

    assert receipt.sample_count == 21
    assert receipt.access_library_count == 15
    assert receipt.access_reverse_directive_count == 15
    assert receipt.ovation_library_count == 6
    assert receipt.ovation_forward_directive_count == 6
    assert receipt.sample_identifiers_retained is False


def test_calibration_annotation_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationAnnotationResolutionPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationAnnotationResolutionReceipt.model_json_schema()
    )


def test_annotation_acquisition_contract_prohibits_release() -> None:
    plan = CalibrationAnnotationAcquisitionPlan(
        plan_version="1.0.0",
        source_id="ensembl-grch38-release-84",
        official_url=(
            "https://ftp.ensembl.org/pub/release-84/gtf/homo_sapiens/"
            "Homo_sapiens.GRCh38.84.gtf.gz"
        ),
        filename="Homo_sapiens.GRCh38.84.gtf.gz",
        expected_content_length_bytes=45686368,
        expected_content_type="application/x-gzip",
        object_key="raw/nas-brca-002/annotation/homo_sapiens.grch38.84.gtf.gz",
        source_registry_sha256="a" * 64,
        annotation_resolution_receipt_sha256="b" * 64,
        storage_readiness_receipt_sha256="c" * 64,
        parse_during_acquisition=False,
        molecular_values_requested=False,
        outcomes_requested=False,
        export_authorized=False,
        publication_authorized=False,
        immutable_write_required=True,
    )

    assert plan.export_authorized is False
    assert json.loads(ACQUISITION_PLAN_SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationAnnotationAcquisitionPlan.model_json_schema()
    )
    assert json.loads(ACQUISITION_RECEIPT_SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationAnnotationAcquisitionReceipt.model_json_schema()
    )
