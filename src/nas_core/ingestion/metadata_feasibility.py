"""Governed source-level metadata audit for NAS-BRCA-002."""

from __future__ import annotations

import json
import ssl
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, cast
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import certifi

from nas_core.domain.feasibility import (
    FeasibilityCheck,
    FeasibilityDecision,
    FeasibilityStatus,
    GDCMetadataSummary,
    GEOMetadataSummary,
    GEOSupplementaryArtifact,
    MetadataEndpointEvidence,
    MetadataFeasibilityReceipt,
)
from nas_core.ingestion.gdc import canonical_json, sha256

GDC_STATUS_URL = "https://api.gdc.cancer.gov/status"
GDC_CASE_MAPPING_URL = "https://api.gdc.cancer.gov/cases/_mapping"
GDC_FILES_URL = "https://api.gdc.cancer.gov/files"
GEO_GTF_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96058/suppl/"
    "GSE96058_UCSC_hg38_knownGenes_22sep2014.gtf.gz"
)
GEO_EXPRESSION_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96058/suppl/"
    "GSE96058_gene_expression_3273_samples_and_136_replicates_transformed.csv.gz"
)
ALLOWED_URLS = frozenset(
    {
        GDC_STATUS_URL,
        GDC_CASE_MAPPING_URL,
        GDC_FILES_URL,
        GEO_GTF_URL,
        GEO_EXPRESSION_URL,
    }
)
MAX_JSON_BYTES = 2_000_000
RECEPTOR_TOKENS = ("estrogen", "progesterone", "her2", "receptor")
AUTHORIZATION_SENTENCE = "Conduct non-outcome source and metadata feasibility checks."


class MetadataAuditError(RuntimeError):
    """Raised when a source-level metadata response violates the audit contract."""


@dataclass(frozen=True, slots=True)
class MetadataHTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class MetadataHTTPTransport(Protocol):
    def get(self, url: str) -> MetadataHTTPResponse: ...

    def head(self, url: str) -> MetadataHTTPResponse: ...

    def post_json(self, url: str, payload: dict[str, object]) -> MetadataHTTPResponse: ...


class MetadataUrllibTransport:
    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def get(self, url: str) -> MetadataHTTPResponse:
        return self._send(Request(url, headers=self._headers("application/json")))

    def head(self, url: str) -> MetadataHTTPResponse:
        return self._send(
            Request(url, method="HEAD", headers=self._headers("application/octet-stream"))
        )

    def post_json(self, url: str, payload: dict[str, object]) -> MetadataHTTPResponse:
        return self._send(
            Request(
                url,
                data=canonical_json(payload),
                method="POST",
                headers={
                    **self._headers("application/json"),
                    "Content-Type": "application/json",
                },
            )
        )

    @staticmethod
    def _headers(accept: str) -> dict[str, str]:
        return {"Accept": accept, "User-Agent": "NaS-Core/0.1"}

    def _send(self, request: Request) -> MetadataHTTPResponse:
        with urlopen(  # noqa: S310
            request,
            timeout=self._timeout_seconds,
            context=self._ssl_context,
        ) as response:
            return MetadataHTTPResponse(
                status_code=response.status,
                headers={key.casefold(): value for key, value in response.headers.items()},
                body=response.read(),
            )


def build_gdc_file_aggregation() -> dict[str, object]:
    return {
        "filters": {
            "op": "and",
            "content": [
                {
                    "op": "in",
                    "content": {
                        "field": "cases.project.project_id",
                        "value": ["TCGA-BRCA"],
                    },
                },
                {
                    "op": "in",
                    "content": {
                        "field": "data_type",
                        "value": ["Gene Expression Quantification"],
                    },
                },
                {
                    "op": "in",
                    "content": {
                        "field": "analysis.workflow_type",
                        "value": ["STAR - Counts"],
                    },
                },
                {
                    "op": "in",
                    "content": {"field": "access", "value": ["open"]},
                },
            ],
        },
        "facets": "data_type,analysis.workflow_type,data_format,access",
        "format": "JSON",
        "from": 0,
        "size": 0,
    }


class MetadataFeasibilityAuditService:
    def __init__(
        self,
        *,
        transport: MetadataHTTPTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport or MetadataUrllibTransport()
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(
        self, *, authorization_path: str, authorization_bytes: bytes
    ) -> MetadataFeasibilityReceipt:
        authorization_text = authorization_bytes.decode("utf-8")
        if AUTHORIZATION_SENTENCE not in authorization_text:
            raise PermissionError(
                "founder authorization does not permit metadata feasibility checks"
            )
        if (
            "Molecular expression, clinical outcome, or patient-level biomedical data retrieval."
            not in authorization_text
        ):
            raise PermissionError(
                "founder authorization must preserve the patient-data prohibition"
            )

        status = self._checked(self._transport.get(GDC_STATUS_URL), url=GDC_STATUS_URL)
        mapping = self._checked(
            self._transport.get(GDC_CASE_MAPPING_URL),
            url=GDC_CASE_MAPPING_URL,
        )
        file_request = build_gdc_file_aggregation()
        files = self._checked(
            self._transport.post_json(GDC_FILES_URL, file_request),
            url=GDC_FILES_URL,
        )
        gtf = self._checked(self._transport.head(GEO_GTF_URL), url=GEO_GTF_URL)
        expression = self._checked(
            self._transport.head(GEO_EXPRESSION_URL),
            url=GEO_EXPRESSION_URL,
        )

        status_payload = self._json(status.body, context="GDC status")
        mapping_payload = self._json(mapping.body, context="GDC case mapping")
        files_payload = self._json(files.body, context="GDC file aggregation")
        mapping_fields = self._mapping_fields(mapping_payload)
        receptor_fields = sorted(
            field
            for field in mapping_fields
            if any(token in field.casefold() for token in RECEPTOR_TOKENS)
        )
        file_total, workflow_types, formats, access = self._file_aggregation(files_payload)
        executed_at = self._clock().isoformat()

        endpoints = [
            self._body_evidence("gdc-status", "GET", GDC_STATUS_URL, status.body),
            self._body_evidence(
                "gdc-case-mapping",
                "GET",
                GDC_CASE_MAPPING_URL,
                mapping.body,
            ),
            self._body_evidence(
                "gdc-file-aggregation",
                "POST",
                GDC_FILES_URL,
                files.body,
                request=file_request,
            ),
            self._head_evidence("geo-gse96058-gtf", GEO_GTF_URL, gtf),
            self._head_evidence("geo-gse96058-expression", GEO_EXPRESSION_URL, expression),
        ]
        checks = [
            FeasibilityCheck(
                check_id="tcga-indexed-receptor-fields",
                status=(
                    FeasibilityStatus.VERIFIED if receptor_fields else FeasibilityStatus.UNRESOLVED
                ),
                finding=(
                    f"Found {len(receptor_fields)} receptor-related fields in the current "
                    "GDC case mapping."
                    if receptor_fields
                    else "The current GDC case mapping exposes no indexed ER, PR, HER2, "
                    "estrogen-, progesterone-, or receptor-named fields."
                ),
                evidence_source_ids=["gdc-case-mapping"],
                limitation=(
                    None
                    if receptor_fields
                    else "Completeness cannot be estimated without a separately authorized, "
                    "field-limited clinical-supplement route."
                ),
            ),
            FeasibilityCheck(
                check_id="tcga-open-star-counts",
                status=FeasibilityStatus.VERIFIED,
                finding=(
                    f"GDC reports {file_total} open TCGA-BRCA STAR - Counts gene-expression "
                    "files through a zero-row aggregate query."
                ),
                evidence_source_ids=["gdc-status", "gdc-file-aggregation"],
            ),
            FeasibilityCheck(
                check_id="tcga-pam50-gene-coverage",
                status=FeasibilityStatus.UNRESOLVED,
                finding=(
                    "Source-level GDC metadata confirms the workflow but does not "
                    "enumerate expression-table genes."
                ),
                evidence_source_ids=["gdc-file-aggregation"],
                limitation=(
                    "Exact PAM50 coverage requires a separately authorized schema-only "
                    "inspection of one frozen open file or its authoritative annotation."
                ),
            ),
            FeasibilityCheck(
                check_id="gse96058-processed-artifacts",
                status=FeasibilityStatus.VERIFIED,
                finding=(
                    "NCBI GEO serves both the declared hg38 annotation and processed "
                    "3,273-sample plus 136-replicate expression artifacts."
                ),
                evidence_source_ids=["geo-gse96058-gtf", "geo-gse96058-expression"],
            ),
            FeasibilityCheck(
                check_id="gse96058-pam50-gene-coverage",
                status=FeasibilityStatus.UNRESOLVED,
                finding=(
                    "HEAD-only source metadata proves artifact availability but cannot "
                    "prove row-level PAM50 coverage or alias resolution."
                ),
                evidence_source_ids=["geo-gse96058-gtf", "geo-gse96058-expression"],
                limitation=(
                    "Exact coverage requires a separately authorized gene-identifier-only "
                    "projection that discards every expression value."
                ),
            ),
            FeasibilityCheck(
                check_id="gse96058-receptor-and-replicate-completeness",
                status=FeasibilityStatus.PROHIBITED,
                finding=(
                    "The GEO family metadata bundle co-mingles receptor and replicate "
                    "annotations with patient-level treatment and survival fields, so it "
                    "was excluded from this executable audit."
                ),
                evidence_source_ids=["geo-gse96058-expression"],
                limitation=(
                    "A reviewed field-isolation procedure and explicit patient-level "
                    "metadata authorization are required before retrieving the family bundle."
                ),
            ),
        ]

        return MetadataFeasibilityReceipt(
            schema_version="1.0.0",
            audit_version="1.0.0",
            study_id="NAS-BRCA-002",
            question_id="NAS-RQ-BRCA002",
            question_version="0.3.0",
            executed_at=executed_at,
            authorization_path=authorization_path,
            authorization_sha256=sha256(authorization_bytes),
            metadata_only=True,
            patient_level_data_accessed=False,
            molecular_values_accessed=False,
            outcome_data_accessed=False,
            raw_responses_stored=False,
            endpoints=endpoints,
            gdc=GDCMetadataSummary(
                data_release=str(status_payload.get("data_release", "")),
                api_tag=str(status_payload.get("tag", "")),
                case_mapping_field_count=len(mapping_fields),
                indexed_receptor_field_matches=receptor_fields,
                open_star_counts_file_count=file_total,
                workflow_types=workflow_types,
                data_formats=formats,
                access_categories=access,
            ),
            geo=GEOMetadataSummary(
                accession="GSE96058",
                supplementary_artifacts=[
                    self._geo_artifact("hg38 gene annotation", GEO_GTF_URL, gtf),
                    self._geo_artifact(
                        "processed gene-expression matrix",
                        GEO_EXPRESSION_URL,
                        expression,
                    ),
                ],
                family_metadata_endpoint_used=False,
                family_metadata_exclusion_reason=(
                    "Not requested: the bundle contains patient-level treatment and survival "
                    "fields outside the founder-authorized source-metadata boundary."
                ),
            ),
            checks=checks,
            decision=FeasibilityDecision.CHANGES_REQUESTED,
            decision_rationale=(
                "Source availability and the open GDC STAR - Counts workflow are verified, "
                "but receptor completeness and exact PAM50 gene coverage cannot be established "
                "without a narrower, separately authorized field/schema inspection."
            ),
            next_authorization_required=[
                "Field-limited TCGA clinical-supplement inspection retaining only "
                "aggregate ER, PR, and HER2 completeness counts.",
                "Gene-identifier-only inspection of one frozen GDC STAR - Counts artifact "
                "with every expression value discarded.",
                "Gene-identifier-only inspection of the GSE96058 processed matrix with "
                "every expression value discarded.",
                "Field-isolated GSE96058 receptor and replicate audit that rejects "
                "treatment and survival fields before derivation.",
            ],
        )

    @staticmethod
    def _checked(response: MetadataHTTPResponse, *, url: str) -> MetadataHTTPResponse:
        MetadataFeasibilityAuditService._validate_url(url)
        if not 200 <= response.status_code < 300:
            raise MetadataAuditError(f"metadata request failed with HTTP {response.status_code}")
        if len(response.body) > MAX_JSON_BYTES:
            raise MetadataAuditError("metadata response exceeds the bounded in-memory limit")
        return response

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlsplit(url)
        if (
            url not in ALLOWED_URLS
            or parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
        ):
            raise ValueError("metadata audit URL is not exactly allowlisted")

    @staticmethod
    def _json(body: bytes, *, context: str) -> dict[str, object]:
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise MetadataAuditError(f"{context} response is not valid JSON") from error
        if not isinstance(payload, dict):
            raise MetadataAuditError(f"{context} response must be a JSON object")
        return cast(dict[str, object], payload)

    @staticmethod
    def _mapping_fields(payload: dict[str, object]) -> list[str]:
        mapping = payload.get("_mapping")
        if not isinstance(mapping, dict) or not mapping:
            raise MetadataAuditError("GDC case mapping is missing _mapping fields")
        if any(not isinstance(field, str) for field in mapping):
            raise MetadataAuditError("GDC case mapping contains a non-string field")
        return sorted(cast(dict[str, object], mapping))

    @staticmethod
    def _file_aggregation(
        payload: dict[str, object],
    ) -> tuple[int, list[str], list[str], list[str]]:
        data = payload.get("data")
        if not isinstance(data, dict):
            raise MetadataAuditError("GDC file aggregation is missing data")
        hits = data.get("hits")
        pagination = data.get("pagination")
        aggregations = data.get("aggregations")
        if hits != [] or not isinstance(pagination, dict) or not isinstance(aggregations, dict):
            raise MetadataAuditError(
                "GDC file aggregation must return zero rows and aggregate metadata"
            )
        if pagination.get("count") != 0 or pagination.get("size") != 0:
            raise MetadataAuditError("GDC file aggregation returned row-bearing pagination")
        total = pagination.get("total")
        if not isinstance(total, int) or total < 1:
            raise MetadataAuditError("GDC file aggregation has an invalid total")

        def bucket_keys(name: str) -> list[str]:
            aggregation = aggregations.get(name)
            if not isinstance(aggregation, dict):
                raise MetadataAuditError(f"GDC aggregation is missing {name}")
            buckets = aggregation.get("buckets")
            if not isinstance(buckets, list):
                raise MetadataAuditError(f"GDC aggregation {name} has invalid buckets")
            keys: list[str] = []
            for bucket in buckets:
                if not isinstance(bucket, dict) or not isinstance(bucket.get("key"), str):
                    raise MetadataAuditError(f"GDC aggregation {name} has an invalid bucket")
                keys.append(cast(str, bucket["key"]))
            return sorted(keys)

        return (
            total,
            bucket_keys("analysis.workflow_type"),
            bucket_keys("data_format"),
            bucket_keys("access"),
        )

    @staticmethod
    def _body_evidence(
        source_id: str,
        method: str,
        url: str,
        body: bytes,
        *,
        request: dict[str, object] | None = None,
    ) -> MetadataEndpointEvidence:
        return MetadataEndpointEvidence(
            source_id=source_id,
            method=method,
            url=url,
            request_sha256=None if request is None else sha256(canonical_json(request)),
            representation_sha256=sha256(body),
            representation_size_bytes=len(body),
            raw_response_stored=False,
            patient_rows_requested=False,
            outcome_fields_requested=False,
        )

    @staticmethod
    def _head_representation(response: MetadataHTTPResponse) -> bytes:
        selected = {
            key: response.headers.get(key, "")
            for key in ("content-length", "content-type", "etag", "last-modified")
        }
        return canonical_json(selected)

    @classmethod
    def _head_evidence(
        cls,
        source_id: str,
        url: str,
        response: MetadataHTTPResponse,
    ) -> MetadataEndpointEvidence:
        representation = cls._head_representation(response)
        return MetadataEndpointEvidence(
            source_id=source_id,
            method="HEAD",
            url=url,
            representation_sha256=sha256(representation),
            representation_size_bytes=len(representation),
            raw_response_stored=False,
            patient_rows_requested=False,
            outcome_fields_requested=False,
        )

    @staticmethod
    def _geo_artifact(
        role: str,
        url: str,
        response: MetadataHTTPResponse,
    ) -> GEOSupplementaryArtifact:
        try:
            content_length = int(response.headers["content-length"])
            last_modified = response.headers["last-modified"]
            content_type = response.headers["content-type"]
        except (KeyError, ValueError) as error:
            raise MetadataAuditError(
                "GEO HEAD response lacks required artifact metadata"
            ) from error
        return GEOSupplementaryArtifact(
            artifact_role=role,
            url=url,
            content_length_bytes=content_length,
            last_modified=last_modified,
            content_type=content_type,
        )
