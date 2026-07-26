"""Fail-closed transient projections for the authorized Phase 0 metadata audit."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import ssl
import time
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from http.client import RemoteDisconnected
from typing import BinaryIO, Protocol, cast
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import certifi

from nas_core.domain.field_isolated_metadata import (
    FieldIsolatedMetadataAuthorization,
    FieldIsolatedMetadataReceipt,
    FieldIsolationCheck,
    FieldIsolationDecision,
    FieldIsolationStatus,
    GeneCoverageSummary,
    ReceptorCompletenessSummary,
    ReplicateSummary,
    SourceArtifactEvidence,
)
from nas_core.domain.reliability import (
    PAM50_HISTORICAL_ALIASES,
    PAM50_HISTORICAL_GENES,
)
from nas_core.ingestion.gdc import canonical_json, sha256

GDC_FILES_URL = "https://api.gdc.cancer.gov/files"
GDC_DATA_PREFIX = "https://api.gdc.cancer.gov/data/"
TCGA_CLINICAL_PATIENT_FILENAME = "nationwidechildrens.org_clinical_patient_brca.txt"
GEO_EXPRESSION_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96058/suppl/"
    "GSE96058_gene_expression_3273_samples_and_136_replicates_transformed.csv.gz"
)
GEO_FAMILY_SOFT_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96058/soft/"
    "GSE96058_family.soft.gz"
)
AUTHORIZATION_STATEMENT = "I authorize field-isolated metadata audit 1.0.0 as written."
AMENDMENT_AUTHORIZATION_STATEMENT = (
    "I authorize field-isolated metadata audit amendment 1.0.1 as written."
)
MAX_MANIFEST_BYTES = 5_000_000
MAX_LINE_BYTES = 4_000_000
MAX_ARTIFACT_BYTES = 2_000_000_000
GDC_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
GSM_ACCESSION = re.compile(r"^GSM[0-9]+$")
GEO_SAMPLE_TITLE = re.compile(r"^F[0-9]+(?:repl)?$")

TCGA_RECORD_FIELDS = frozenset({"bcr_patient_uuid", "bcr_patient_barcode"})
TCGA_RECEPTOR_FIELDS = {
    "breast_carcinoma_estrogen_receptor_status": "er",
    "breast_carcinoma_progesterone_receptor_status": "pr",
    "lab_proc_her2_neu_immunohistochemistry_receptor_status": "her2",
    "lab_procedure_her2_neu_in_situ_hybrid_outcome_type": "her2",
}
GEO_RECEPTOR_FIELDS = {
    "er status": "er",
    "estrogen receptor status": "er",
    "pgr status": "pr",
    "pr status": "pr",
    "progesterone receptor status": "pr",
    "her2 status": "her2",
    "her2 receptor status": "her2",
}
GEO_REPLICATE_FIELDS = frozenset(
    {
        "primary sample",
        "replicate",
        "replicate of",
        "sample group",
        "sample type",
        "technical replicate",
        "technical replicate of",
    }
)
MISSING_STATUS_VALUES = frozenset(
    {
        "",
        "NA",
        "N/A",
        "NOT AVAILABLE",
        "NOT APPLICABLE",
        "NOT EVALUATED",
        "NOT REPORTED",
        "UNKNOWN",
    }
)
KNOWN_STATUS_VALUES = {
    "POSITIVE": "positive",
    "NEGATIVE": "negative",
    "INDETERMINATE": "indeterminate",
    "EQUIVOCAL": "equivocal",
    "BORDERLINE": "borderline",
    "DISCREPANCY": "discrepancy",
}


class FieldIsolatedMetadataError(RuntimeError):
    """Raised when a remote representation violates the projection contract."""


@dataclass(slots=True)
class ManifestResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(slots=True)
class StreamingResponse:
    status_code: int
    headers: Mapping[str, str]
    stream: BinaryIO


class FieldIsolatedMetadataTransport(Protocol):
    def post_json(self, url: str, payload: dict[str, object]) -> ManifestResponse: ...

    def open_get(self, url: str) -> AbstractContextManager[StreamingResponse]: ...


class ByteReader(Protocol):
    def read(self, size: int = -1) -> bytes: ...

    def readline(self, size: int = -1) -> bytes: ...


class ReceptorProjection(Protocol):
    er: str | None
    pr: str | None
    her2: str | None


class UrllibFieldIsolatedMetadataTransport:
    def __init__(
        self,
        *,
        timeout_seconds: float = 120.0,
        open_attempts: int = 4,
        retry_delay_seconds: float = 0.5,
    ) -> None:
        if open_attempts < 1:
            raise ValueError("open_attempts must be at least one")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative")
        self._timeout_seconds = timeout_seconds
        self._open_attempts = open_attempts
        self._retry_delay_seconds = retry_delay_seconds
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def post_json(self, url: str, payload: dict[str, object]) -> ManifestResponse:
        request = Request(
            url,
            data=canonical_json(payload),
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "NaS-Core/0.1",
            },
        )
        with urlopen(  # noqa: S310
            request,
            timeout=self._timeout_seconds,
            context=self._ssl_context,
        ) as response:
            body = response.read(MAX_MANIFEST_BYTES + 1)
            return ManifestResponse(
                status_code=response.status,
                headers={
                    key.casefold(): value for key, value in response.headers.items()
                },
                body=body,
            )

    @contextmanager
    def open_get(self, url: str) -> Iterator[StreamingResponse]:
        request = Request(
            url,
            headers={
                "Accept": "application/octet-stream",
                "User-Agent": "NaS-Core/0.1",
            },
        )
        response = None
        for attempt in range(1, self._open_attempts + 1):
            try:
                response = urlopen(  # noqa: S310
                    request,
                    timeout=self._timeout_seconds,
                    context=self._ssl_context,
                )
                break
            except (RemoteDisconnected, TimeoutError, URLError):
                if attempt == self._open_attempts:
                    raise
                time.sleep(self._retry_delay_seconds * attempt)
        if response is None:
            raise AssertionError("bounded response-open attempts were exhausted")
        with response:
            yield StreamingResponse(
                status_code=response.status,
                headers={
                    key.casefold(): value for key, value in response.headers.items()
                },
                stream=cast(BinaryIO, response),
            )


@dataclass(frozen=True, slots=True)
class GDCFileRecord:
    file_id: str
    file_name: str
    file_size: int
    md5sum: str
    data_format: str


@dataclass(slots=True)
class ReceptorRecord:
    er: str | None = None
    pr: str | None = None
    her2: str | None = None


@dataclass(slots=True)
class GeoSampleRecord:
    er: str | None = None
    pr: str | None = None
    her2: str | None = None
    replicate_state: str = "unclassified"
    replicate_linked: bool = False
    title: str | None = None


class DigestingReader:
    def __init__(self, stream: BinaryIO) -> None:
        self._stream = stream
        self._digest = hashlib.sha256()
        self._md5 = hashlib.md5(usedforsecurity=False)
        self.size = 0

    def read(self, size: int = -1) -> bytes:
        data = self._stream.read(size)
        return self._record(data)

    def readline(self, size: int = -1) -> bytes:
        data = self._stream.readline(size)
        return self._record(data)

    def _record(self, data: bytes) -> bytes:
        if data:
            self._digest.update(data)
            self._md5.update(data)
            self.size += len(data)
            if self.size > MAX_ARTIFACT_BYTES:
                raise FieldIsolatedMetadataError("source artifact exceeds bounded transfer size")
        return data

    def hexdigest(self) -> str:
        return self._digest.hexdigest()

    def md5_hexdigest(self) -> str:
        return self._md5.hexdigest()

    def drain(self) -> None:
        while self.read(1024 * 1024):
            pass


def build_gdc_clinical_manifest_query() -> dict[str, object]:
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
                    "content": {"field": "data_category", "value": ["Clinical"]},
                },
                {
                    "op": "in",
                    "content": {
                        "field": "data_type",
                        "value": ["Clinical Supplement"],
                    },
                },
                {
                    "op": "in",
                    "content": {"field": "data_format", "value": ["BCR Biotab"]},
                },
                {
                    "op": "in",
                    "content": {"field": "access", "value": ["open"]},
                },
                {
                    "op": "in",
                    "content": {
                        "field": "file_name",
                        "value": [TCGA_CLINICAL_PATIENT_FILENAME],
                    },
                },
            ],
        },
        "fields": "file_id,file_name,file_size,md5sum,data_format",
        "format": "JSON",
        "from": 0,
        "size": 200,
        "sort": "file_id:asc",
    }


def build_gdc_star_manifest_query() -> dict[str, object]:
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
        "fields": "file_id,file_name,file_size,md5sum,data_format",
        "format": "JSON",
        "from": 0,
        "size": 1,
        "sort": "file_id:asc",
    }


class FieldIsolatedMetadataAuditService:
    def __init__(
        self,
        *,
        transport: FieldIsolatedMetadataTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport or UrllibFieldIsolatedMetadataTransport()
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(
        self,
        *,
        authorization: FieldIsolatedMetadataAuthorization,
        authorization_path: str,
        authorization_bytes: bytes,
        packet_path: str,
        packet_bytes: bytes,
        software_revision: str,
        prior_receipt: FieldIsolatedMetadataReceipt | None = None,
        prior_receipt_path: str | None = None,
        prior_receipt_bytes: bytes | None = None,
    ) -> FieldIsolatedMetadataReceipt:
        self._verify_authorization(
            authorization=authorization,
            authorization_bytes=authorization_bytes,
            packet_bytes=packet_bytes,
            prior_receipt=prior_receipt,
            prior_receipt_bytes=prior_receipt_bytes,
        )

        clinical_files = self._manifest(
            build_gdc_clinical_manifest_query(),
            context="TCGA clinical supplement",
        )
        star_files = self._manifest(
            build_gdc_star_manifest_query(),
            context="TCGA STAR-count",
        )
        if len(star_files) != 1:
            raise FieldIsolatedMetadataError(
                "the deterministic STAR manifest must return exactly one file"
            )
        if (
            len(clinical_files) != 1
            or clinical_files[0].file_name != TCGA_CLINICAL_PATIENT_FILENAME
        ):
            raise FieldIsolatedMetadataError(
                "the clinical manifest must return exactly the registered patient table"
            )

        tcga_records: dict[str, ReceptorRecord] = {}
        artifacts: list[SourceArtifactEvidence] = []
        for record in clinical_files:
            artifact, parsed_records = self._project_tcga_clinical(record)
            artifacts.append(artifact)
            for record_id, projected in parsed_records.items():
                target = tcga_records.setdefault(record_id, ReceptorRecord())
                target.er = target.er or projected.er
                target.pr = target.pr or projected.pr
                target.her2 = target.her2 or projected.her2

        star_artifact, star_identifiers = self._project_tcga_gene_names(star_files[0])
        artifacts.append(star_artifact)
        geo_expression_artifact, geo_identifiers = self._project_geo_gene_names()
        artifacts.append(geo_expression_artifact)
        geo_family_artifact, geo_samples = self._project_geo_family(
            audit_version=authorization.audit_version
        )
        artifacts.append(geo_family_artifact)
        if prior_receipt is not None:
            self._verify_representation_continuity(
                prior_receipt=prior_receipt,
                artifacts=artifacts,
            )

        tcga_gene_coverage = self._gene_coverage("tcga-star-counts", star_identifiers)
        geo_gene_coverage = self._gene_coverage("gse96058-expression", geo_identifiers)
        tcga_receptors = self._receptor_summary("tcga-clinical", tcga_records.values())
        geo_receptors = self._receptor_summary("gse96058-family", geo_samples.values())
        geo_replicates = self._replicate_summary(geo_samples.values())
        checks = self._checks(
            tcga_gene_coverage=tcga_gene_coverage,
            geo_gene_coverage=geo_gene_coverage,
            tcga_receptors=tcga_receptors,
            geo_receptors=geo_receptors,
            geo_replicates=geo_replicates,
        )
        decision = (
            FieldIsolationDecision.PASS
            if all(check.status is FieldIsolationStatus.VERIFIED for check in checks)
            else FieldIsolationDecision.CHANGES_REQUESTED
        )
        return FieldIsolatedMetadataReceipt(
            schema_version="1.0.0",
            audit_version=authorization.audit_version,
            study_id="NAS-BRCA-002",
            question_id="NAS-RQ-BRCA002",
            question_version="0.3.0",
            executed_at=self._clock().isoformat(),
            software_revision=software_revision,
            authorization_path=authorization_path,
            authorization_sha256=sha256(authorization_bytes),
            authorization_packet_path=packet_path,
            authorization_packet_sha256=sha256(packet_bytes),
            prior_receipt_path=prior_receipt_path,
            prior_receipt_sha256=(
                sha256(prior_receipt_bytes)
                if prior_receipt_bytes is not None
                else None
            ),
            transient_field_isolated_access=True,
            prohibited_fields_transiently_transferred=True,
            patient_level_records_retained=False,
            molecular_values_parsed=False,
            outcome_values_parsed=False,
            raw_artifacts_stored=False,
            cohort_constructed=False,
            classifier_executed=False,
            artifacts=artifacts,
            tcga_gene_coverage=tcga_gene_coverage,
            gse96058_gene_coverage=geo_gene_coverage,
            tcga_receptor_completeness=tcga_receptors,
            gse96058_receptor_completeness=geo_receptors,
            gse96058_replicates=geo_replicates,
            checks=checks,
            decision=decision,
            decision_rationale=(
                "All five bounded input-feasibility checks passed."
                if decision is FieldIsolationDecision.PASS
                else "At least one bounded input-feasibility check remains unresolved; "
                "molecular and outcome execution remain prohibited."
            ),
            limitations=[
                "Gene presence does not establish assay equivalence, numerical "
                "compatibility, or a valid cross-platform transformation.",
                "Receptor completeness does not establish diagnostic correctness or "
                "clinical utility.",
                "The audit parsed only founder-authorized fields and did not construct "
                "an analytical cohort.",
            ],
            next_authorization_required=(
                [
                    "Resolve every nonverified field-isolation check and execute a "
                    "new versioned audit."
                ]
                if decision is not FieldIsolationDecision.PASS
                else [
                    "Lock the exact centroids, external reference, platform "
                    "transformations, technical-error model, and reliability thresholds.",
                    "Complete founder scientific, molecular/pathology, and statistical "
                    "reviews before any preregistration or molecular execution.",
                ]
            ),
        )

    @staticmethod
    def _verify_authorization(
        *,
        authorization: FieldIsolatedMetadataAuthorization,
        authorization_bytes: bytes,
        packet_bytes: bytes,
        prior_receipt: FieldIsolatedMetadataReceipt | None,
        prior_receipt_bytes: bytes | None,
    ) -> None:
        loaded = FieldIsolatedMetadataAuthorization.model_validate(
            json.loads(json.dumps(authorization.model_dump(mode="json")))
        )
        expected_statement = {
            "1.0.0": AUTHORIZATION_STATEMENT,
            "1.0.1": AMENDMENT_AUTHORIZATION_STATEMENT,
        }[loaded.audit_version]
        if loaded.authorization_statement != expected_statement:
            raise PermissionError("exact field-isolated authorization is missing")
        if sha256(packet_bytes) != loaded.packet_sha256:
            raise PermissionError("authorization packet checksum mismatch")
        if sha256(authorization_bytes) == sha256(packet_bytes):
            raise PermissionError("confirmation must be separate from its review packet")
        if loaded.audit_version == "1.0.1":
            if prior_receipt is None or prior_receipt_bytes is None:
                raise PermissionError("audit 1.0.1 requires its immutable prior receipt")
            if prior_receipt.audit_version != "1.0.0":
                raise PermissionError("audit 1.0.1 prior receipt has the wrong version")
            if sha256(prior_receipt_bytes) != loaded.prior_receipt_sha256:
                raise PermissionError("audit 1.0.1 prior receipt checksum mismatch")
        elif prior_receipt is not None or prior_receipt_bytes is not None:
            raise PermissionError("audit 1.0.0 cannot receive a prior receipt")

    @staticmethod
    def _verify_representation_continuity(
        *,
        prior_receipt: FieldIsolatedMetadataReceipt,
        artifacts: list[SourceArtifactEvidence],
    ) -> None:
        prior = {
            artifact.source_id: artifact.representation_sha256
            for artifact in prior_receipt.artifacts
        }
        current = {
            artifact.source_id: artifact.representation_sha256
            for artifact in artifacts
        }
        if current != prior:
            changed = sorted(
                source_id
                for source_id in set(prior) | set(current)
                if prior.get(source_id) != current.get(source_id)
            )
            raise FieldIsolatedMetadataError(
                "audit 1.0.1 source representations changed: "
                + ", ".join(changed)
            )

    def _manifest(
        self,
        query: dict[str, object],
        *,
        context: str,
    ) -> list[GDCFileRecord]:
        self._validate_url(GDC_FILES_URL)
        response = self._transport.post_json(GDC_FILES_URL, query)
        if not 200 <= response.status_code < 300:
            raise FieldIsolatedMetadataError(
                f"{context} manifest failed with HTTP {response.status_code}"
            )
        if len(response.body) > MAX_MANIFEST_BYTES:
            raise FieldIsolatedMetadataError(f"{context} manifest exceeds size limit")
        try:
            payload = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FieldIsolatedMetadataError(f"{context} manifest is invalid JSON") from error
        if not isinstance(payload, dict):
            raise FieldIsolatedMetadataError(f"{context} manifest must be an object")
        data = payload.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("hits"), list):
            raise FieldIsolatedMetadataError(f"{context} manifest is missing hits")
        records: list[GDCFileRecord] = []
        for item in data["hits"]:
            if not isinstance(item, dict):
                raise FieldIsolatedMetadataError(f"{context} manifest hit is invalid")
            try:
                record = GDCFileRecord(
                    file_id=str(item["file_id"]),
                    file_name=str(item["file_name"]),
                    file_size=int(item["file_size"]),
                    md5sum=str(item["md5sum"]).casefold(),
                    data_format=str(item["data_format"]),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise FieldIsolatedMetadataError(
                    f"{context} manifest hit is incomplete"
                ) from error
            if not GDC_UUID.fullmatch(record.file_id):
                raise FieldIsolatedMetadataError(f"{context} contains an invalid file UUID")
            if (
                record.file_size < 1
                or record.file_size > MAX_ARTIFACT_BYTES
                or not re.fullmatch(r"[a-f0-9]{32}", record.md5sum)
            ):
                raise FieldIsolatedMetadataError(
                    f"{context} contains invalid size or checksum metadata"
                )
            records.append(record)
        if not records:
            raise FieldIsolatedMetadataError(f"{context} manifest returned no files")
        return sorted(records, key=lambda item: item.file_id)

    def _project_tcga_clinical(
        self,
        record: GDCFileRecord,
    ) -> tuple[SourceArtifactEvidence, dict[str, ReceptorRecord]]:
        url = f"{GDC_DATA_PREFIX}{record.file_id}"
        self._validate_url(url, expected_file_id=record.file_id)
        with self._transport.open_get(url) as response:
            self._checked_stream(response, context="TCGA clinical supplement")
            digest = DigestingReader(response.stream)
            records: dict[str, ReceptorRecord] = {}
            permitted: set[str] = set()
            rejected: set[str] = set()
            self._parse_clinical_table(
                digest,
                records=records,
                permitted=permitted,
                rejected=rejected,
            )
            digest.drain()
        if not records:
            raise FieldIsolatedMetadataError(
                "TCGA clinical table contained no permitted receptor records"
            )
        return (
            self._artifact(
                source_id=f"tcga-clinical-{record.file_id}",
                role="TCGA-BRCA receptor-field completeness",
                url=url,
                record=record,
                digest=digest,
                parser_name="tcga-bcr-biotab-plain-field-projection-v1",
                permitted=permitted,
                rejected=rejected,
            ),
            records,
        )

    def _project_tcga_gene_names(
        self,
        record: GDCFileRecord,
    ) -> tuple[SourceArtifactEvidence, list[str]]:
        url = f"{GDC_DATA_PREFIX}{record.file_id}"
        self._validate_url(url, expected_file_id=record.file_id)
        with self._transport.open_get(url) as response:
            self._checked_stream(response, context="TCGA STAR-count file")
            digest = DigestingReader(response.stream)
            identifiers = self._parse_delimited_gene_column(
                digest,
                delimiter=b"\t",
                column_index=1,
                expected_header="gene_name",
                compressed=record.file_name.endswith(".gz"),
            )
            digest.drain()
        return (
            self._artifact(
                source_id="tcga-star-counts",
                role="TCGA-BRCA gene-identifier coverage",
                url=url,
                record=record,
                digest=digest,
                parser_name="gene-name-only-tsv-projection-v1",
                permitted={"gene_name"},
                rejected={"expression_value_columns"},
            ),
            identifiers,
        )

    def _project_geo_gene_names(self) -> tuple[SourceArtifactEvidence, list[str]]:
        self._validate_url(GEO_EXPRESSION_URL)
        with self._transport.open_get(GEO_EXPRESSION_URL) as response:
            self._checked_stream(response, context="GSE96058 expression artifact")
            digest = DigestingReader(response.stream)
            identifiers = self._parse_delimited_gene_column(
                digest,
                delimiter=b",",
                column_index=0,
                expected_header=None,
                compressed=True,
            )
            digest.drain()
        artifact = SourceArtifactEvidence(
            source_id="gse96058-expression",
            role="GSE96058 gene-identifier coverage",
            url=GEO_EXPRESSION_URL,
            filename=GEO_EXPRESSION_URL.rsplit("/", 1)[-1],
            representation_sha256=digest.hexdigest(),
            representation_size_bytes=digest.size,
            parser_name="gene-identifier-only-csv-projection-v1",
            raw_artifact_stored=False,
            permitted_field_names=["gene_identifier"],
            rejected_field_names=["expression_value_columns"],
        )
        return artifact, identifiers

    def _project_geo_family(
        self,
        *,
        audit_version: str,
    ) -> tuple[SourceArtifactEvidence, dict[str, GeoSampleRecord]]:
        self._validate_url(GEO_FAMILY_SOFT_URL)
        with self._transport.open_get(GEO_FAMILY_SOFT_URL) as response:
            self._checked_stream(response, context="GSE96058 family metadata")
            digest = DigestingReader(response.stream)
            samples, permitted, rejected = self._parse_geo_family(
                digest,
                audit_version=audit_version,
            )
            digest.drain()
        return (
            SourceArtifactEvidence(
                source_id="gse96058-family",
                role="GSE96058 receptor and technical-replicate completeness",
                url=GEO_FAMILY_SOFT_URL,
                filename=GEO_FAMILY_SOFT_URL.rsplit("/", 1)[-1],
                representation_sha256=digest.hexdigest(),
                representation_size_bytes=digest.size,
                parser_name=(
                    "geo-soft-sample-title-projection-v2"
                    if audit_version == "1.0.1"
                    else "geo-soft-field-allowlist-projection-v1"
                ),
                raw_artifact_stored=False,
                permitted_field_names=sorted(permitted),
                rejected_field_names=sorted(rejected),
            ),
            samples,
        )

    @staticmethod
    def _parse_clinical_table(
        source: ByteReader,
        *,
        records: dict[str, ReceptorRecord],
        permitted: set[str],
        rejected: set[str],
    ) -> None:
        header: list[str] | None = None
        selected: dict[int, str] = {}
        for raw_line in FieldIsolatedMetadataAuditService._bounded_lines(source):
            fields = raw_line.rstrip(b"\r\n").split(b"\t")
            decoded_header = [
                field.decode("utf-8", errors="strict").strip().casefold()
                for field in fields
            ]
            if header is None and any(
                field in TCGA_RECEPTOR_FIELDS for field in decoded_header
            ):
                header = decoded_header
                for index, field in enumerate(header):
                    if field in TCGA_RECORD_FIELDS or field in TCGA_RECEPTOR_FIELDS:
                        selected[index] = field
                        permitted.add(field)
                    elif field:
                        rejected.add(field)
                continue
            if header is None:
                continue
            values = {
                field: (
                    fields[index].decode("utf-8", errors="strict").strip()
                    if index < len(fields)
                    else ""
                )
                for index, field in selected.items()
            }
            record_id = next(
                (
                    values[field]
                    for field in ("bcr_patient_uuid", "bcr_patient_barcode")
                    if values.get(field)
                ),
                "",
            )
            if not record_id:
                continue
            record = records.setdefault(record_id, ReceptorRecord())
            for field, receptor in TCGA_RECEPTOR_FIELDS.items():
                if field in values and values[field]:
                    normalized = FieldIsolatedMetadataAuditService._status(values[field])
                    if normalized is not None:
                        setattr(record, receptor, getattr(record, receptor) or normalized)

    @staticmethod
    def _parse_delimited_gene_column(
        digest: DigestingReader,
        *,
        delimiter: bytes,
        column_index: int,
        expected_header: str | None,
        compressed: bool,
    ) -> list[str]:
        stream: ByteReader
        gzip_stream: gzip.GzipFile | None = None
        if compressed:
            gzip_stream = gzip.GzipFile(fileobj=cast(BinaryIO, digest), mode="rb")
            stream = cast(ByteReader, gzip_stream)
        else:
            stream = digest
        identifiers: list[str] = []
        header_seen = expected_header is None
        try:
            for raw_line in FieldIsolatedMetadataAuditService._bounded_lines(stream):
                fields = raw_line.rstrip(b"\r\n").split(delimiter, column_index + 1)
                if len(fields) <= column_index:
                    continue
                value = (
                    fields[column_index]
                    .strip()
                    .strip(b'"')
                    .decode("utf-8-sig", errors="strict")
                )
                if not header_seen:
                    if value.casefold() != expected_header:
                        continue
                    header_seen = True
                    continue
                if not value or value.casefold() in {
                    "gene",
                    "gene_id",
                    "gene_name",
                    "symbol",
                }:
                    continue
                if value.startswith("N_"):
                    continue
                identifiers.append(value)
        finally:
            if gzip_stream is not None:
                gzip_stream.close()
        if not header_seen or not identifiers:
            raise FieldIsolatedMetadataError("gene-identifier projection returned no genes")
        return identifiers

    @staticmethod
    def _parse_geo_family(
        digest: DigestingReader,
        *,
        audit_version: str,
    ) -> tuple[dict[str, GeoSampleRecord], set[str], set[str]]:
        samples: dict[str, GeoSampleRecord] = {}
        permitted = {"sample accession"}
        rejected: set[str] = set()
        current_accession: str | None = None
        with gzip.GzipFile(fileobj=cast(BinaryIO, digest), mode="rb") as source:
            for raw_line in FieldIsolatedMetadataAuditService._bounded_lines(
                cast(ByteReader, source)
            ):
                if raw_line.startswith(b"^SAMPLE = "):
                    accession = raw_line.split(b"=", 1)[1].strip().decode("ascii")
                    if not GSM_ACCESSION.fullmatch(accession):
                        raise FieldIsolatedMetadataError(
                            "GEO family contains an invalid sample accession"
                        )
                    current_accession = accession
                    samples.setdefault(accession, GeoSampleRecord())
                    continue
                if raw_line.startswith(b"!Sample_title = "):
                    if audit_version != "1.0.1":
                        continue
                    if current_accession is None:
                        raise FieldIsolatedMetadataError(
                            "GEO sample title appeared outside a sample record"
                        )
                    title = raw_line.split(b"=", 1)[1].strip().decode("ascii")
                    if GEO_SAMPLE_TITLE.fullmatch(title) is None:
                        raise FieldIsolatedMetadataError(
                            "GEO sample title violates the approved F<number>[repl] contract"
                        )
                    samples[current_accession].title = title
                    permitted.add("sample title")
                    continue
                if not raw_line.startswith(b"!Sample_characteristics_ch1 = "):
                    continue
                payload = raw_line.split(b"=", 1)[1].strip()
                if b":" not in payload:
                    rejected.add("unkeyed sample characteristic")
                    continue
                key_bytes, value_bytes = payload.split(b":", 1)
                key = key_bytes.decode("utf-8", errors="strict").strip().casefold()
                if current_accession is None:
                    raise FieldIsolatedMetadataError(
                        "GEO characteristic appeared outside a sample record"
                    )
                if key in GEO_RECEPTOR_FIELDS:
                    permitted.add(key)
                    status = FieldIsolatedMetadataAuditService._geo_status(
                        value_bytes.decode("utf-8", errors="strict"),
                        audit_version=audit_version,
                    )
                    if status is not None:
                        setattr(
                            samples[current_accession],
                            GEO_RECEPTOR_FIELDS[key],
                            status,
                        )
                elif key in GEO_REPLICATE_FIELDS:
                    permitted.add(key)
                    value = value_bytes.decode("utf-8", errors="strict").strip()
                    FieldIsolatedMetadataAuditService._project_replicate_value(
                        samples[current_accession],
                        key,
                        value,
                    )
                else:
                    rejected.add(key)
        if not samples:
            raise FieldIsolatedMetadataError("GEO family projection returned no samples")
        if audit_version == "1.0.1":
            FieldIsolatedMetadataAuditService._classify_geo_titles(samples)
        return samples, permitted, rejected

    @staticmethod
    def _classify_geo_titles(samples: dict[str, GeoSampleRecord]) -> None:
        titles = [record.title for record in samples.values()]
        if any(title is None for title in titles):
            raise FieldIsolatedMetadataError(
                "audit 1.0.1 requires exactly one approved title per GEO sample"
            )
        materialized_titles = [title for title in titles if title is not None]
        if len(materialized_titles) != len(set(materialized_titles)):
            raise FieldIsolatedMetadataError("GEO sample titles must be unique")
        primary_titles = {
            title for title in materialized_titles if not title.endswith("repl")
        }
        for record in samples.values():
            if record.title is None:
                raise AssertionError("title completeness was checked above")
            if record.title.endswith("repl"):
                record.replicate_state = "technical_replicate"
                record.replicate_linked = record.title.removesuffix("repl") in primary_titles
            else:
                record.replicate_state = "primary"
                record.replicate_linked = False

    @staticmethod
    def _project_replicate_value(
        record: GeoSampleRecord,
        key: str,
        value: str,
    ) -> None:
        folded = value.casefold()
        if "replicate" in key or "replicate" in folded:
            record.replicate_state = "technical_replicate"
            record.replicate_linked = bool(re.search(r"GSM[0-9]+", value))
        elif (
            "primary" in key or "primary" in folded
        ) and record.replicate_state == "unclassified":
            record.replicate_state = "primary"

    @staticmethod
    def _status(value: str) -> str | None:
        normalized = re.sub(r"[\[\]_-]+", " ", value).strip().upper()
        normalized = re.sub(r"\s+", " ", normalized)
        if normalized in MISSING_STATUS_VALUES:
            return None
        return KNOWN_STATUS_VALUES.get(normalized, "other")

    @staticmethod
    def _geo_status(value: str, *, audit_version: str) -> str | None:
        if audit_version == "1.0.0":
            return FieldIsolatedMetadataAuditService._status(value)
        normalized = value.strip().upper()
        mapping = {"1": "positive", "0": "negative", "NA": None}
        if normalized not in mapping:
            raise FieldIsolatedMetadataError(
                "GSE96058 receptor category violates the approved 0/1/NA contract"
            )
        return mapping[normalized]

    @staticmethod
    def _bounded_lines(stream: ByteReader) -> Iterator[bytes]:
        while True:
            line = stream.readline(MAX_LINE_BYTES + 1)
            if not line:
                return
            if len(line) > MAX_LINE_BYTES:
                raise FieldIsolatedMetadataError(
                    "source line exceeds the bounded parser limit"
                )
            yield line

    @staticmethod
    def _gene_coverage(
        source_id: str,
        identifiers: list[str],
    ) -> GeneCoverageSummary:
        normalized = [identifier.strip().upper() for identifier in identifiers]
        counts = Counter(normalized)
        present: set[str] = set()
        alias_resolutions: dict[str, str] = {}
        canonical_mapping_counts: Counter[str] = Counter()
        for identifier in normalized:
            canonical = (
                identifier
                if identifier in PAM50_HISTORICAL_GENES
                else PAM50_HISTORICAL_ALIASES.get(identifier)
            )
            if canonical is None:
                continue
            present.add(canonical)
            canonical_mapping_counts[canonical] += 1
            if identifier in PAM50_HISTORICAL_ALIASES:
                alias_resolutions[identifier] = canonical
        return GeneCoverageSummary(
            source_id=source_id,
            required_gene_count=len(PAM50_HISTORICAL_GENES),
            observed_identifier_count=len(normalized),
            unique_identifier_count=len(counts),
            canonical_genes_present=sorted(present),
            alias_resolutions=dict(sorted(alias_resolutions.items())),
            missing_canonical_genes=sorted(PAM50_HISTORICAL_GENES - present),
            duplicate_canonical_mappings=sorted(
                gene for gene, count in canonical_mapping_counts.items() if count > 1
            ),
            unmapped_identifier_count=sum(
                count
                for identifier, count in counts.items()
                if identifier not in PAM50_HISTORICAL_GENES
                and identifier not in PAM50_HISTORICAL_ALIASES
            ),
            expression_values_parsed=False,
        )

    @staticmethod
    def _receptor_summary(
        source_id: str,
        records: Iterable[ReceptorProjection],
    ) -> ReceptorCompletenessSummary:
        materialized = list(records)
        er = Counter(record.er for record in materialized if record.er is not None)
        pr = Counter(record.pr for record in materialized if record.pr is not None)
        her2 = Counter(record.her2 for record in materialized if record.her2 is not None)
        return ReceptorCompletenessSummary(
            source_id=source_id,
            record_count=len(materialized),
            er_present_count=sum(er.values()),
            pr_present_count=sum(pr.values()),
            her2_present_count=sum(her2.values()),
            all_three_present_count=sum(
                record.er is not None
                and record.pr is not None
                and record.her2 is not None
                for record in materialized
            ),
            er_category_counts=dict(sorted(er.items())),
            pr_category_counts=dict(sorted(pr.items())),
            her2_category_counts=dict(sorted(her2.items())),
        )

    @staticmethod
    def _replicate_summary(records: Iterable[GeoSampleRecord]) -> ReplicateSummary:
        materialized = list(records)
        states = Counter(record.replicate_state for record in materialized)
        return ReplicateSummary(
            source_id="gse96058-family",
            sample_record_count=len(materialized),
            primary_record_count=states["primary"],
            technical_replicate_count=states["technical_replicate"],
            linked_technical_replicate_count=sum(
                record.replicate_state == "technical_replicate"
                and record.replicate_linked
                for record in materialized
            ),
            unclassified_record_count=states["unclassified"],
        )

    @staticmethod
    def _checks(
        *,
        tcga_gene_coverage: GeneCoverageSummary,
        geo_gene_coverage: GeneCoverageSummary,
        tcga_receptors: ReceptorCompletenessSummary,
        geo_receptors: ReceptorCompletenessSummary,
        geo_replicates: ReplicateSummary,
    ) -> list[FieldIsolationCheck]:
        def coverage_check(
            check_id: str,
            summary: GeneCoverageSummary,
        ) -> FieldIsolationCheck:
            complete = (
                not summary.missing_canonical_genes
                and not summary.duplicate_canonical_mappings
            )
            return FieldIsolationCheck(
                check_id=check_id,
                status=(
                    FieldIsolationStatus.VERIFIED
                    if complete
                    else FieldIsolationStatus.UNRESOLVED
                ),
                finding=(
                    f"Resolved {len(summary.canonical_genes_present)} of "
                    f"{summary.required_gene_count} required PAM50 genes with "
                    f"{len(summary.duplicate_canonical_mappings)} ambiguous duplicates."
                ),
                evidence_source_ids=[summary.source_id],
                limitation=(
                    None
                    if complete
                    else "Missing or duplicate canonical mappings prevent a locked "
                    "no-imputation input contract."
                ),
            )

        def receptor_check(
            check_id: str,
            summary: ReceptorCompletenessSummary,
        ) -> FieldIsolationCheck:
            verified = (
                summary.er_present_count > 0
                and summary.pr_present_count > 0
                and summary.her2_present_count > 0
            )
            return FieldIsolationCheck(
                check_id=check_id,
                status=(
                    FieldIsolationStatus.VERIFIED
                    if verified
                    else FieldIsolationStatus.UNRESOLVED
                ),
                finding=(
                    f"Among {summary.record_count} records, ER/PR/HER2 are present for "
                    f"{summary.er_present_count}/{summary.pr_present_count}/"
                    f"{summary.her2_present_count}; all three are present for "
                    f"{summary.all_three_present_count}."
                ),
                evidence_source_ids=[summary.source_id],
                limitation=(
                    None
                    if verified
                    else "At least one required receptor field was not located in the "
                    "approved projection."
                ),
            )

        replicate_verified = (
            geo_replicates.technical_replicate_count > 0
            and geo_replicates.primary_record_count > 0
            and geo_replicates.unclassified_record_count == 0
            and geo_replicates.linked_technical_replicate_count
            == geo_replicates.technical_replicate_count
        )
        return [
            coverage_check("tcga-pam50-gene-coverage", tcga_gene_coverage),
            coverage_check("gse96058-pam50-gene-coverage", geo_gene_coverage),
            receptor_check("tcga-receptor-completeness", tcga_receptors),
            receptor_check("gse96058-receptor-completeness", geo_receptors),
            FieldIsolationCheck(
                check_id="gse96058-primary-replicate-linkage",
                status=(
                    FieldIsolationStatus.VERIFIED
                    if replicate_verified
                    else FieldIsolationStatus.UNRESOLVED
                ),
                finding=(
                    f"Classified {geo_replicates.primary_record_count} primary and "
                    f"{geo_replicates.technical_replicate_count} technical-replicate "
                    f"records; {geo_replicates.linked_technical_replicate_count} "
                    "technical replicates have an explicit primary link and "
                    f"{geo_replicates.unclassified_record_count} records are unclassified."
                ),
                evidence_source_ids=["gse96058-family"],
                limitation=(
                    None
                    if replicate_verified
                    else "The approved GEO fields do not completely identify and link "
                    "primary and technical-replicate records."
                ),
            ),
        ]

    @staticmethod
    def _artifact(
        *,
        source_id: str,
        role: str,
        url: str,
        record: GDCFileRecord,
        digest: DigestingReader,
        parser_name: str,
        permitted: set[str],
        rejected: set[str],
    ) -> SourceArtifactEvidence:
        if digest.size != record.file_size:
            raise FieldIsolatedMetadataError(
                f"downloaded size mismatch for GDC file {record.file_id}"
            )
        if digest.md5_hexdigest() != record.md5sum:
            raise FieldIsolatedMetadataError(
                f"downloaded MD5 mismatch for GDC file {record.file_id}"
            )
        return SourceArtifactEvidence(
            source_id=source_id,
            role=role,
            url=url,
            file_id=record.file_id,
            filename=record.file_name,
            declared_md5=record.md5sum,
            representation_sha256=digest.hexdigest(),
            representation_size_bytes=digest.size,
            parser_name=parser_name,
            raw_artifact_stored=False,
            permitted_field_names=sorted(permitted),
            rejected_field_names=sorted(rejected),
        )

    @staticmethod
    def _checked_stream(
        response: StreamingResponse,
        *,
        context: str,
    ) -> None:
        if not 200 <= response.status_code < 300:
            raise FieldIsolatedMetadataError(
                f"{context} failed with HTTP {response.status_code}"
            )

    @staticmethod
    def _validate_url(url: str, *, expected_file_id: str | None = None) -> None:
        parsed = urlsplit(url)
        fixed = {GDC_FILES_URL, GEO_EXPRESSION_URL, GEO_FAMILY_SOFT_URL}
        dynamic_valid = (
            expected_file_id is not None
            and GDC_UUID.fullmatch(expected_file_id) is not None
            and url == f"{GDC_DATA_PREFIX}{expected_file_id}"
        )
        if (
            (url not in fixed and not dynamic_valid)
            or parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
        ):
            raise ValueError("field-isolated metadata URL is not exactly allowlisted")
