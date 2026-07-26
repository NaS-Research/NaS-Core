from __future__ import annotations

import gzip
import hashlib
import io
import json
from contextlib import AbstractContextManager, nullcontext
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.field_isolated_metadata import (
    FieldIsolatedMetadataAuthorization,
    FieldIsolatedMetadataReceipt,
    FieldIsolationDecision,
    write_field_isolated_metadata_receipt,
)
from nas_core.domain.reliability import PAM50_HISTORICAL_GENES
from nas_core.ingestion.field_isolated_metadata import (
    AUTHORIZATION_STATEMENT,
    GDC_FILES_URL,
    GEO_EXPRESSION_URL,
    GEO_FAMILY_SOFT_URL,
    TCGA_CLINICAL_PATIENT_FILENAME,
    FieldIsolatedMetadataAuditService,
    FieldIsolatedMetadataError,
    ManifestResponse,
    StreamingResponse,
    build_gdc_clinical_manifest_query,
    build_gdc_star_manifest_query,
)
from nas_core.ingestion.gdc import canonical_json

NOW = datetime(2026, 7, 26, 14, 30, tzinfo=UTC)
SOFTWARE_REVISION = "a" * 40
PACKET = b"frozen field-isolated metadata packet"
CLINICAL_ID = "11111111-1111-4111-8111-111111111111"
STAR_ID = "22222222-2222-4222-8222-222222222222"
ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "workflows" / "field_isolated_metadata_receipt.schema.json"
STUDY_ROOT = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
REAL_PACKET_PATH = (
    STUDY_ROOT
    / "reviews"
    / "FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md"
)
REAL_AUTHORIZATION_PATH = (
    STUDY_ROOT
    / "reviews"
    / "FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_CONFIRMATION_v1.0.0.yaml"
)


def _clinical_table() -> bytes:
    header = (
        "bcr_patient_uuid\tbreast_carcinoma_estrogen_receptor_status\t"
        "breast_carcinoma_progesterone_receptor_status\t"
        "lab_proc_her2_neu_immunohistochemistry_receptor_status\t"
        "days_to_death\n"
    )
    return (
        header
        + "patient-one\tPositive\tNegative\tEquivocal\tPROHIBITED-OUTCOME\n"
        + "patient-two\tNegative\tPositive\tNegative\tPROHIBITED-OUTCOME\n"
    ).encode()


def _star_counts(*, omit_gene: str | None = None) -> bytes:
    genes = sorted(PAM50_HISTORICAL_GENES - ({omit_gene} if omit_gene else set()))
    rows = ["gene_id\tgene_name\tgene_type\tunstranded"]
    rows.extend(
        f"ENSG{index:011d}.1\t{gene}\tprotein_coding\tPROHIBITED-{index}"
        for index, gene in enumerate(genes, start=1)
    )
    return f"{'\n'.join(rows)}\n".encode()


def _geo_expression() -> bytes:
    rows = ["gene,PRIMARY,REPLICATE"]
    rows.extend(
        f"{gene},PROHIBITED-EXPRESSION,PROHIBITED-EXPRESSION"
        for gene in sorted(PAM50_HISTORICAL_GENES)
    )
    return gzip.compress(f"{'\n'.join(rows)}\n".encode(), mtime=0)


def _geo_family() -> bytes:
    payload = """^SAMPLE = GSM1000001
!Sample_characteristics_ch1 = er status: Positive
!Sample_characteristics_ch1 = pgr status: Negative
!Sample_characteristics_ch1 = her2 status: Negative
!Sample_characteristics_ch1 = sample group: Primary
!Sample_characteristics_ch1 = overall survival days: PROHIBITED-OUTCOME
!Sample_characteristics_ch1 = pam50 subtype: PROHIBITED-LABEL
^SAMPLE = GSM1000002
!Sample_characteristics_ch1 = er status: Positive
!Sample_characteristics_ch1 = pgr status: Negative
!Sample_characteristics_ch1 = her2 status: Negative
!Sample_characteristics_ch1 = technical replicate of: GSM1000001
!Sample_characteristics_ch1 = chemo treated: PROHIBITED-TREATMENT
"""
    return gzip.compress(payload.encode(), mtime=0)


class FakeTransport:
    def __init__(self, *, missing_tcga_gene: str | None = None) -> None:
        self.clinical = _clinical_table()
        self.star = _star_counts(omit_gene=missing_tcga_gene)
        self.geo_expression = _geo_expression()
        self.geo_family = _geo_family()
        self.requests: list[tuple[str, str]] = []

    def post_json(
        self,
        url: str,
        payload: dict[str, object],
    ) -> ManifestResponse:
        self.requests.append(("POST", url))
        text = json.dumps(payload)
        if "BCR Biotab" in text:
            hits = [
                self._record(
                    CLINICAL_ID,
                    TCGA_CLINICAL_PATIENT_FILENAME,
                    self.clinical,
                    "BCR Biotab",
                )
            ]
        else:
            hits = [self._record(STAR_ID, "star_counts.tsv", self.star, "TSV")]
        return ManifestResponse(200, {}, canonical_json({"data": {"hits": hits}}))

    def open_get(self, url: str) -> AbstractContextManager[StreamingResponse]:
        self.requests.append(("GET", url))
        if url.endswith(CLINICAL_ID):
            body = self.clinical
        elif url.endswith(STAR_ID):
            body = self.star
        elif url == GEO_EXPRESSION_URL:
            body = self.geo_expression
        elif url == GEO_FAMILY_SOFT_URL:
            body = self.geo_family
        else:
            raise AssertionError(f"unexpected URL: {url}")
        return nullcontext(StreamingResponse(200, {}, io.BytesIO(body)))

    @staticmethod
    def _record(
        file_id: str,
        filename: str,
        body: bytes,
        data_format: str,
    ) -> dict[str, object]:
        return {
            "file_id": file_id,
            "file_name": filename,
            "file_size": len(body),
            "md5sum": hashlib.md5(body, usedforsecurity=False).hexdigest(),
            "data_format": data_format,
        }


def _authorization() -> tuple[FieldIsolatedMetadataAuthorization, bytes]:
    payload = {
        "schema_version": "1.0.0",
        "study_id": "NAS-BRCA-002",
        "question_id": "NAS-RQ-BRCA002",
        "question_version": "0.3.0",
        "audit_version": "1.0.0",
        "packet_filename": "FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md",
        "packet_sha256": hashlib.sha256(PACKET).hexdigest(),
        "authorization_statement": AUTHORIZATION_STATEMENT,
        "founder_id": "founder",
        "founder_name": "Founder",
        "founder_role": "Founder and internal reviewer",
        "authorized_at": NOW.isoformat(),
        "founder_authorized": True,
        "transient_field_isolated_access_authorized": True,
        "patient_level_data_retention_authorized": False,
        "molecular_value_analysis_authorized": False,
        "outcome_data_access_authorized": False,
        "cohort_construction_authorized": False,
        "classifier_execution_authorized": False,
        "scientific_conclusions_authorized": False,
        "ai_assistance_disclosure": "Synthetic test authorization.",
    }
    encoded = yaml.safe_dump(payload, sort_keys=False).encode()
    return FieldIsolatedMetadataAuthorization.model_validate(payload), encoded


def _execute(
    *,
    transport: FakeTransport | None = None,
    packet: bytes = PACKET,
) -> FieldIsolatedMetadataReceipt:
    authorization, authorization_bytes = _authorization()
    return FieldIsolatedMetadataAuditService(
        transport=transport or FakeTransport(),
        clock=lambda: NOW,
    ).execute(
        authorization=authorization,
        authorization_path="confirmation.yaml",
        authorization_bytes=authorization_bytes,
        packet_path="authorization.md",
        packet_bytes=packet,
        software_revision=SOFTWARE_REVISION,
    )


def test_queries_are_project_scoped_and_field_limited() -> None:
    clinical = json.dumps(build_gdc_clinical_manifest_query())
    star = json.dumps(build_gdc_star_manifest_query())

    assert "TCGA-BRCA" in clinical
    assert "BCR Biotab" in clinical
    assert "Clinical Supplement" in clinical
    assert TCGA_CLINICAL_PATIENT_FILENAME in clinical
    assert "TCGA-BRCA" in star
    assert "STAR - Counts" in star
    assert '"size": 1' in star
    for forbidden in ("vital_status", "days_to_death", "submitter_id"):
        assert forbidden not in clinical
        assert forbidden not in star


def test_field_isolation_passes_without_retaining_prohibited_values() -> None:
    transport = FakeTransport()
    receipt = _execute(transport=transport)

    assert receipt.decision is FieldIsolationDecision.PASS
    assert len(receipt.artifacts) == 4
    assert receipt.tcga_gene_coverage.missing_canonical_genes == []
    assert receipt.gse96058_gene_coverage.missing_canonical_genes == []
    assert receipt.tcga_receptor_completeness.record_count == 2
    assert receipt.tcga_receptor_completeness.all_three_present_count == 2
    assert receipt.gse96058_receptor_completeness.record_count == 2
    assert receipt.gse96058_replicates.primary_record_count == 1
    assert receipt.gse96058_replicates.technical_replicate_count == 1
    assert receipt.gse96058_replicates.linked_technical_replicate_count == 1
    assert receipt.patient_level_records_retained is False
    assert receipt.molecular_values_parsed is False
    assert receipt.outcome_values_parsed is False
    assert receipt.raw_artifacts_stored is False
    assert receipt.cohort_constructed is False
    assert receipt.classifier_executed is False
    serialized = json.dumps(receipt.model_dump(mode="json"))
    for prohibited in (
        "PROHIBITED-OUTCOME",
        "PROHIBITED-EXPRESSION",
        "PROHIBITED-LABEL",
        "PROHIBITED-TREATMENT",
        "patient-one",
        "GSM1000001",
    ):
        assert prohibited not in serialized
    assert [request[0] for request in transport.requests] == [
        "POST",
        "POST",
        "GET",
        "GET",
        "GET",
        "GET",
    ]
    assert transport.requests[0][1] == GDC_FILES_URL


def test_missing_pam50_gene_fails_closed_to_changes_requested() -> None:
    receipt = _execute(transport=FakeTransport(missing_tcga_gene="ACTR3B"))
    checks = {check.check_id: check for check in receipt.checks}

    assert receipt.decision is FieldIsolationDecision.CHANGES_REQUESTED
    assert receipt.tcga_gene_coverage.missing_canonical_genes == ["ACTR3B"]
    assert checks["tcga-pam50-gene-coverage"].status.value == "unresolved"
    assert receipt.next_authorization_required


def test_packet_checksum_mismatch_blocks_before_network() -> None:
    transport = FakeTransport()
    with pytest.raises(PermissionError, match="checksum mismatch"):
        _execute(transport=transport, packet=b"changed")
    assert transport.requests == []


def test_gdc_checksum_mismatch_fails_closed() -> None:
    class CorruptTransport(FakeTransport):
        def open_get(self, url: str) -> AbstractContextManager[StreamingResponse]:
            response = super().open_get(url)
            if url.endswith(STAR_ID):
                return nullcontext(StreamingResponse(200, {}, io.BytesIO(b"corrupt")))
            return response

    with pytest.raises(FieldIsolatedMetadataError, match="gene-identifier projection"):
        _execute(transport=CorruptTransport())


def test_receipt_writer_is_immutable(tmp_path: Path) -> None:
    receipt = _execute()
    output = tmp_path / "field_isolated_metadata_receipt.yaml"

    write_field_isolated_metadata_receipt(output, receipt)
    loaded = FieldIsolatedMetadataReceipt.model_validate(
        yaml.safe_load(output.read_text(encoding="utf-8"))
    )
    assert loaded == receipt
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_field_isolated_metadata_receipt(output, receipt)


def test_checked_in_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA_PATH.read_text(encoding="utf-8")) == (
        FieldIsolatedMetadataReceipt.model_json_schema()
    )


def test_real_authorization_is_exact_and_packet_bound() -> None:
    authorization = FieldIsolatedMetadataAuthorization.model_validate(
        yaml.safe_load(REAL_AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    )

    assert authorization.authorization_statement == AUTHORIZATION_STATEMENT
    assert authorization.packet_sha256 == hashlib.sha256(
        REAL_PACKET_PATH.read_bytes()
    ).hexdigest()
    assert authorization.founder_authorized is True
    assert authorization.transient_field_isolated_access_authorized is True
    assert authorization.patient_level_data_retention_authorized is False
    assert authorization.molecular_value_analysis_authorized is False
    assert authorization.outcome_data_access_authorized is False
