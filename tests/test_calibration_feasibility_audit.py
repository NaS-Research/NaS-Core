from __future__ import annotations

import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from nas_core.analysis.calibration_feasibility_audit import (
    CalibrationFeasibilityAuditService,
)
from nas_core.domain.calibration_feasibility_artifact import (
    CalibrationFeasibilityAcquisitionReceipt,
    CalibrationFeasibilityArtifactKind,
    CalibrationFeasibilityArtifactReceipt,
)
from nas_core.domain.calibration_feasibility_audit import (
    CalibrationFeasibilityAuditPlan,
    CalibrationFeasibilityAuditReceipt,
    PanelMappingStatus,
)
from nas_core.domain.reliability import load_reliability_specification
from nas_core.ingestion.gdc import sha256
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import FileSystemObjectStore

ROOT = Path(__file__).parents[1]
SPECIFICATION = (
    ROOT
    / "workflows/studies/breast_clinical_molecular_discordance/protocol"
    / "reliability_specification.yaml"
)
PLAN_SCHEMA = ROOT / "workflows/calibration_feasibility_audit_plan.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/calibration_feasibility_audit_receipt.schema.json"


def _artifact(
    source_id: str,
    accession: str,
    filename: str,
    object_key: str,
    payload: bytes,
) -> CalibrationFeasibilityArtifactReceipt:
    return CalibrationFeasibilityArtifactReceipt(
        source_id=source_id,
        source_accession=accession,
        file_accession=accession,
        artifact_kind=CalibrationFeasibilityArtifactKind.PROCESSED_EXPRESSION,
        filename=filename,
        official_url="https://www.ncbi.nlm.nih.gov/geo/download/?synthetic=true",
        response_content_type="application/octet-stream",
        response_last_modified=None,
        content_length_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        object_key=object_key,
        immutable_object_verified=True,
    )


def test_source_isolated_audit_preserves_unresolved_mapping(tmp_path: Path) -> None:
    specification = load_reliability_specification(SPECIFICATION)
    genes = specification.input_contract.canonical_gene_symbols
    pilot_payload = gzip.compress(
        ("Gene Symbol\tP1\tP1-replicate\n" + "".join(
            f"{gene}\t1.25\t1.5\n" for gene in genes
        )).encode()
    )
    ffpe_payload = gzip.compress(
        b"Gene\tUnstranded\tfwd\trev\n"
        b"ENSG000001\t1\t2\t3\nENSG000002\t4\t5\t6\n"
    )
    artifacts = [
        _artifact(
            "ncbi-geo-gse60788",
            "GSE60788",
            "GSE60788_rnaseq_gex_normalized.txt.gz",
            "raw/nas-brca-002/ncbi-geo-gse60788/matrix.gz",
            pilot_payload,
        ),
        _artifact(
            "ncbi-geo-gse130397",
            "GSM3737461",
            "GSM3737461_FFPE_RNASeq_OVA_S1_01_readsPerGene.txt.gz",
            "raw/nas-brca-002/ncbi-geo-gse130397/counts.gz",
            ffpe_payload,
        ),
    ]
    acquisition = CalibrationFeasibilityAcquisitionReceipt(
        receipt_version="1.0.0",
        study_id="NAS-BRCA-002",
        code_revision="1234567",
        acquired_at=datetime(2026, 8, 1, tzinfo=UTC),
        plan_sha256="a" * 64,
        artifacts=artifacts,
        all_immutable_objects_verified=True,
        molecular_values_parsed=False,
        outcomes_accessed=False,
        sources_pooled=False,
        thresholds_estimated=False,
        classifier_executed=False,
        external_publication_authorized=False,
    )
    acquisition_path = tmp_path / "acquisition.yaml"
    acquisition_path.write_text(
        yaml.safe_dump(acquisition.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    plan = CalibrationFeasibilityAuditPlan(
        plan_version="1.0.0",
        acquisition_receipt_sha256=sha256(acquisition_path.read_bytes()),
        reliability_specification_sha256=sha256(SPECIFICATION.read_bytes()),
        audit_sources_separately=True,
        retain_source_identifiers=False,
        retain_molecular_values=False,
        outcomes_requested=False,
        pooling_authorized=False,
        threshold_estimation_authorized=False,
        classifier_execution_authorized=False,
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(plan.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    data_root = tmp_path / "data"
    DataLayout(data_root).initialize()
    store = FileSystemObjectStore(data_root)
    for artifact, payload in zip(artifacts, [pilot_payload, ffpe_payload], strict=True):
        store.put_bytes(artifact.object_key, payload, content_type="application/x-gzip")

    receipt = CalibrationFeasibilityAuditService(store=store).execute(
        plan,
        acquisition,
        specification,
        plan_path=plan_path,
        acquisition_receipt_path=acquisition_path,
        reliability_specification_path=SPECIFICATION,
        code_revision="7654321",
    )

    by_source = {source.source_id: source for source in receipt.sources}
    assert by_source["ncbi-geo-gse60788"].direct_pam50_gene_count == 50
    assert by_source["ncbi-geo-gse60788"].replicate_record_count == 1
    assert by_source["ncbi-geo-gse130397"].panel_mapping_status is (
        PanelMappingStatus.UNRESOLVED_IDENTIFIER_MAPPING
    )
    assert by_source["ncbi-geo-gse130397"].integer_like_value_count == 6
    assert receipt.sources_pooled is False
    assert receipt.thresholds_estimated is False


def test_calibration_feasibility_audit_schemas_match_runtime_models() -> None:
    assert json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationFeasibilityAuditPlan.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8")) == (
        CalibrationFeasibilityAuditReceipt.model_json_schema()
    )
