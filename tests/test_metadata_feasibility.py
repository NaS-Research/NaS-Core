import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.feasibility import (
    FeasibilityDecision,
    FeasibilityStatus,
    MetadataFeasibilityReceipt,
    write_metadata_feasibility_receipt,
)
from nas_core.ingestion.gdc import canonical_json
from nas_core.ingestion.metadata_feasibility import (
    AUTHORIZATION_SENTENCE,
    GDC_CASE_MAPPING_URL,
    GDC_FILES_URL,
    GDC_STATUS_URL,
    GEO_EXPRESSION_URL,
    GEO_GTF_URL,
    MetadataAuditError,
    MetadataFeasibilityAuditService,
    MetadataHTTPResponse,
    build_gdc_file_aggregation,
)

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "workflows" / "metadata_feasibility_receipt.schema.json"
REAL_RECEIPT_PATH = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "ingestion"
    / "metadata_feasibility_receipt_v1.0.0.yaml"
)
REAL_AUTHORIZATION_PATH = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "reviews"
    / "FOUNDER_PHASE_ZERO_AUTHORIZATION_v0.3.0.md"
)
NOW = datetime(2026, 7, 25, 20, 0, tzinfo=UTC)
AUTHORIZATION = f"""
# Synthetic founder authorization

- {AUTHORIZATION_SENTENCE}

## Work not authorized

- Molecular expression, clinical outcome, or patient-level biomedical data retrieval.
""".encode()


class FakeTransport:
    def __init__(self, *, row_bearing_files: bool = False) -> None:
        self.row_bearing_files = row_bearing_files
        self.requests: list[tuple[str, str, dict[str, object] | None]] = []

    def get(self, url: str) -> MetadataHTTPResponse:
        self.requests.append(("GET", url, None))
        if url == GDC_STATUS_URL:
            return _json_response(
                {
                    "status": "OK",
                    "tag": "8.5.0",
                    "version": 1,
                    "commit": "a" * 40,
                    "data_release": "Data Release 45.0 - December 04, 2025",
                }
            )
        if url == GDC_CASE_MAPPING_URL:
            return _json_response(
                {
                    "_mapping": {
                        "cases.case_id": {"description": "UNRETAINED-SENTINEL"},
                        "cases.samples.sample_type": {"type": "keyword"},
                    }
                }
            )
        raise AssertionError(f"unexpected GET: {url}")

    def head(self, url: str) -> MetadataHTTPResponse:
        self.requests.append(("HEAD", url, None))
        sizes = {GEO_GTF_URL: "20971520", GEO_EXPRESSION_URL: "591396864"}
        return MetadataHTTPResponse(
            status_code=200,
            headers={
                "content-length": sizes[url],
                "last-modified": "Thu, 14 Sep 2017 16:40:00 GMT",
                "content-type": "application/x-gzip",
                "etag": '"synthetic"',
            },
            body=b"",
        )

    def post_json(
        self,
        url: str,
        payload: dict[str, object],
    ) -> MetadataHTTPResponse:
        self.requests.append(("POST", url, payload))
        hits: list[dict[str, str]] = (
            [{"case_id": "PROHIBITED-PATIENT-ROW"}] if self.row_bearing_files else []
        )
        count = len(hits)
        return _json_response(
            {
                "data": {
                    "hits": hits,
                    "aggregations": {
                        "data_type": {
                            "buckets": [
                                {"key": "Gene Expression Quantification", "doc_count": 1231}
                            ]
                        },
                        "analysis.workflow_type": {
                            "buckets": [{"key": "STAR - Counts", "doc_count": 1231}]
                        },
                        "data_format": {"buckets": [{"key": "tsv", "doc_count": 1231}]},
                        "access": {"buckets": [{"key": "open", "doc_count": 1231}]},
                    },
                    "pagination": {
                        "count": count,
                        "total": 1231,
                        "size": 0,
                        "from": 0,
                    },
                },
                "warnings": {"private": "UNRETAINED-SENTINEL"},
            }
        )


def _json_response(payload: object) -> MetadataHTTPResponse:
    return MetadataHTTPResponse(status_code=200, headers={}, body=canonical_json(payload))


def _execute(*, transport: FakeTransport | None = None) -> MetadataFeasibilityReceipt:
    return MetadataFeasibilityAuditService(
        transport=transport or FakeTransport(),
        clock=lambda: NOW,
    ).execute(
        authorization_path="reviews/FOUNDER_PHASE_ZERO_AUTHORIZATION_v0.3.0.md",
        authorization_bytes=AUTHORIZATION,
    )


def test_file_aggregation_is_zero_row_and_project_scoped() -> None:
    payload = build_gdc_file_aggregation()

    assert payload["size"] == 0
    assert payload["from"] == 0
    assert "TCGA-BRCA" in str(payload["filters"])
    assert "STAR - Counts" in str(payload["filters"])
    assert "open" in str(payload["filters"])
    assert "vital_status" not in str(payload)
    assert "days_to_death" not in str(payload)


def test_metadata_audit_retains_only_source_level_derivatives() -> None:
    transport = FakeTransport()
    receipt = _execute(transport=transport)

    assert receipt.decision is FeasibilityDecision.CHANGES_REQUESTED
    assert receipt.metadata_only is True
    assert receipt.patient_level_data_accessed is False
    assert receipt.molecular_values_accessed is False
    assert receipt.outcome_data_accessed is False
    assert receipt.raw_responses_stored is False
    assert len(receipt.endpoints) == 5
    assert receipt.gdc.open_star_counts_file_count == 1231
    assert receipt.gdc.indexed_receptor_field_matches == []
    assert receipt.geo.family_metadata_endpoint_used is False
    assert len(receipt.geo.supplementary_artifacts) == 2
    assert [request[:2] for request in transport.requests] == [
        ("GET", GDC_STATUS_URL),
        ("GET", GDC_CASE_MAPPING_URL),
        ("POST", GDC_FILES_URL),
        ("HEAD", GEO_GTF_URL),
        ("HEAD", GEO_EXPRESSION_URL),
    ]
    serialized = json.dumps(receipt.model_dump(mode="json"))
    assert "UNRETAINED-SENTINEL" not in serialized
    assert "PROHIBITED-PATIENT-ROW" not in serialized


def test_metadata_audit_preserves_unresolved_and_prohibited_gates() -> None:
    receipt = _execute()
    checks = {check.check_id: check for check in receipt.checks}

    assert checks["tcga-open-star-counts"].status is FeasibilityStatus.VERIFIED
    assert checks["gse96058-processed-artifacts"].status is FeasibilityStatus.VERIFIED
    assert checks["tcga-indexed-receptor-fields"].status is FeasibilityStatus.UNRESOLVED
    assert checks["tcga-pam50-gene-coverage"].status is FeasibilityStatus.UNRESOLVED
    assert checks["gse96058-pam50-gene-coverage"].status is FeasibilityStatus.UNRESOLVED
    assert (
        checks["gse96058-receptor-and-replicate-completeness"].status
        is FeasibilityStatus.PROHIBITED
    )


def test_metadata_audit_rejects_row_bearing_aggregation() -> None:
    with pytest.raises(MetadataAuditError, match="zero rows"):
        _execute(transport=FakeTransport(row_bearing_files=True))


def test_metadata_audit_requires_exact_founder_scope() -> None:
    with pytest.raises(PermissionError, match="does not permit"):
        MetadataFeasibilityAuditService(transport=FakeTransport()).execute(
            authorization_path="authorization.md",
            authorization_bytes=b"not authorized",
        )


def test_receipt_writer_is_immutable(tmp_path: Path) -> None:
    output = tmp_path / "metadata_feasibility.yaml"
    receipt = _execute()

    write_metadata_feasibility_receipt(output, receipt)
    loaded = MetadataFeasibilityReceipt.model_validate(
        yaml.safe_load(output.read_text(encoding="utf-8"))
    )
    assert loaded == receipt

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_metadata_feasibility_receipt(output, receipt)


def test_checked_in_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA_PATH.read_text(encoding="utf-8")) == (
        MetadataFeasibilityReceipt.model_json_schema()
    )


def test_real_metadata_receipt_is_valid_and_bound_to_authorization() -> None:
    receipt = MetadataFeasibilityReceipt.model_validate(
        yaml.safe_load(REAL_RECEIPT_PATH.read_text(encoding="utf-8"))
    )

    assert receipt.authorization_sha256 == hashlib.sha256(
        REAL_AUTHORIZATION_PATH.read_bytes()
    ).hexdigest()
    assert receipt.decision is FeasibilityDecision.CHANGES_REQUESTED
    assert receipt.gdc.open_star_counts_file_count == 1231
    assert receipt.gdc.indexed_receptor_field_matches == []
    assert all(not endpoint.raw_response_stored for endpoint in receipt.endpoints)
