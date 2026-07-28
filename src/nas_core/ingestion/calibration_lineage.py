"""Transient GEO title projections for calibration-source lineage assessment."""

from __future__ import annotations

import gzip
import re
from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Protocol, cast

from nas_core.domain.calibration_lineage import (
    CalibrationLineageArtifact,
    CalibrationLineageAuditReceipt,
    CalibrationLineageSummary,
)
from nas_core.domain.method_dependency import (
    MethodRouteActivationReceipt,
    MethodRouteActivationStatus,
)
from nas_core.ingestion.field_isolated_metadata import (
    DigestingReader,
    StreamingResponse,
    UrllibFieldIsolatedMetadataTransport,
)
from nas_core.ingestion.gdc import sha256

GSE60788_SOFT_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE60nnn/GSE60788/soft/"
    "GSE60788_family.soft.gz"
)
GSE96058_SOFT_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96058/soft/"
    "GSE96058_family.soft.gz"
)
GSE130397_SOFT_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE130nnn/GSE130397/soft/"
    "GSE130397_family.soft.gz"
)
CALIBRATION_LINEAGE_URLS: Mapping[str, str] = {
    "GEO:GSE60788": GSE60788_SOFT_URL,
    "GEO:GSE96058": GSE96058_SOFT_URL,
    "GEO:GSE130397": GSE130397_SOFT_URL,
}
_GSM = re.compile(r"^GSM[0-9]+$")
_GSE60788_PRIMARY = re.compile(r"^(P[0-9]+)$")
_GSE60788_REPLICATE = re.compile(r"^(P[0-9]+)-replicate$")
_GSE96058_PRIMARY = re.compile(r"^(F[0-9]+)$")
_GSE96058_REPLICATE = re.compile(r"^(F[0-9]+)repl$")
_GSE130397_TRIPLICATE = re.compile(
    r"^(FFPE-RNA-Seq_(?:OVA|ACC)_S[12])_(0[123])$"
)
_GSE130397_RESEQUENCE = re.compile(r"^(FFPE-RNA-Seq_ACC_ER_S0[1-6])_Reseq$")


class CalibrationLineageError(RuntimeError):
    """Raised when a GEO representation violates the lineage projection."""


class CalibrationLineageTransport(Protocol):
    def open_get(self, url: str) -> AbstractContextManager[StreamingResponse]: ...


@dataclass(slots=True)
class _Projection:
    accessions: set[str]
    titles: set[str]
    primary_or_unlabeled_count: int
    replicate_count: int
    linked_count: int
    groups: set[str]
    unrecognized_count: int


class CalibrationLineageAuditService:
    def __init__(
        self,
        transport: CalibrationLineageTransport | None = None,
    ) -> None:
        self._transport = transport or UrllibFieldIsolatedMetadataTransport()

    def execute(
        self,
        *,
        route_activation: MethodRouteActivationReceipt,
        route_activation_path: Path,
        code_revision: str,
        executed_at: datetime,
    ) -> CalibrationLineageAuditReceipt:
        if (
            route_activation.selected_route_id != "ROUTE-C"
            or route_activation.activation_status
            is not MethodRouteActivationStatus.INDEPENDENT_CALIBRATION_HOLD
            or not route_activation.calibration_acquisition_active
            or route_activation.method_execution_authorized
        ):
            raise CalibrationLineageError(
                "lineage audit requires the active nonexecuting Route C boundary"
            )
        artifacts: list[CalibrationLineageArtifact] = []
        summaries: list[CalibrationLineageSummary] = []
        projections: dict[str, _Projection] = {}
        for source_id, url in CALIBRATION_LINEAGE_URLS.items():
            artifact, summary, projection = self._project(source_id, url)
            artifacts.append(artifact)
            summaries.append(summary)
            projections[source_id] = projection

        pilot = projections["GEO:GSE60788"]
        validation = projections["GEO:GSE96058"]
        accession_overlap = len(pilot.accessions & validation.accessions)
        title_overlap = len(pilot.titles & validation.titles)
        return CalibrationLineageAuditReceipt(
            audit_version="1.0.0",
            study_id="NAS-BRCA-002",
            question_id="NAS-RQ-BRCA002",
            question_version="0.3.0",
            route_activation_sha256=sha256(route_activation_path.read_bytes()),
            code_revision=code_revision,
            executed_at=executed_at,
            artifacts=artifacts,
            summaries=summaries,
            gse60788_gse96058_accession_overlap_count=accession_overlap,
            gse60788_gse96058_title_overlap_count=title_overlap,
            biological_sample_nonoverlap_established=False,
            metadata_lineage_feasibility_established=True,
            prohibited_fields_transiently_transferred=True,
            patient_level_records_retained=False,
            sample_identifiers_retained=False,
            molecular_values_parsed=False,
            outcome_values_parsed=False,
            raw_artifacts_stored=False,
            calibration_source_selected=False,
            method_execution_authorized=False,
            limitations=[
                "Disjoint GEO accessions and public titles do not prove that biological "
                "specimens or source RNA never overlap.",
                "Title patterns classify declared replicate records but do not prove "
                "same-RNA, library reconstruction, or resequencing lineage.",
                "No expression matrix, molecular value, outcome, or patient row was parsed.",
            ],
            next_required_actions=[
                "Obtain authoritative confirmation of GSE60788 and GSE96058 biological "
                "sample nonoverlap.",
                "Confirm the laboratory lineage of every candidate technical pair.",
                "Perform a separately governed gene-panel audit before source eligibility.",
            ],
        )

    def _project(
        self,
        source_id: str,
        url: str,
    ) -> tuple[
        CalibrationLineageArtifact,
        CalibrationLineageSummary,
        _Projection,
    ]:
        with self._transport.open_get(url) as response:
            if response.status_code != 200:
                raise CalibrationLineageError(
                    f"{source_id} returned HTTP {response.status_code}"
                )
            reader = DigestingReader(response.stream)
            projection = self._parse_soft(source_id, reader)
            reader.drain()
        count = len(projection.accessions)
        if count == 0 or len(projection.titles) != count:
            raise CalibrationLineageError(
                f"{source_id} must contain one unique title for every sample"
            )
        artifact = CalibrationLineageArtifact(
            source_id=source_id,
            url=url,
            representation_sha256=reader.hexdigest(),
            representation_size_bytes=reader.size,
            parser_name="geo_family_soft_title_projection_v1",
            raw_artifact_stored=False,
            sample_rows_retained=False,
            molecular_values_parsed=False,
            outcome_values_parsed=False,
        )
        summary = CalibrationLineageSummary(
            source_id=source_id,
            sample_record_count=count,
            primary_or_unlabeled_record_count=(
                projection.primary_or_unlabeled_count
            ),
            replicate_labeled_record_count=projection.replicate_count,
            linked_replicate_record_count=projection.linked_count,
            unique_replicate_group_count=len(projection.groups),
            unrecognized_title_count=projection.unrecognized_count,
            transient_title_count=count,
            sample_titles_retained=False,
        )
        return artifact, summary, projection

    @staticmethod
    def _parse_soft(source_id: str, stream: DigestingReader) -> _Projection:
        accessions: set[str] = set()
        titles: set[str] = set()
        current_accession: str | None = None
        primary_or_unlabeled_count = 0
        replicate_count = 0
        linked_count = 0
        groups: set[str] = set()
        unrecognized_count = 0
        with gzip.GzipFile(fileobj=cast(BinaryIO, stream), mode="rb") as decoded:
            for raw_line in decoded:
                if raw_line.startswith(b"^SAMPLE = "):
                    accession = raw_line.removeprefix(b"^SAMPLE = ").decode().strip()
                    if not _GSM.fullmatch(accession) or accession in accessions:
                        raise CalibrationLineageError(
                            f"{source_id} contains an invalid or duplicate accession"
                        )
                    accessions.add(accession)
                    current_accession = accession
                elif raw_line.startswith(b"!Sample_title = "):
                    if current_accession is None:
                        raise CalibrationLineageError(
                            f"{source_id} title precedes its sample accession"
                        )
                    title = raw_line.removeprefix(b"!Sample_title = ").decode().strip()
                    if not title or title in titles:
                        raise CalibrationLineageError(
                            f"{source_id} contains an empty or duplicate title"
                        )
                    titles.add(title)
                    classification = _classify_title(source_id, title)
                    if classification is None:
                        primary_or_unlabeled_count += 1
                        unrecognized_count += 1
                    elif classification[0] == "primary":
                        primary_or_unlabeled_count += 1
                        groups.add(classification[1])
                    else:
                        replicate_count += 1
                        groups.add(classification[1])
                        linked_count += 1
                    current_accession = None
        return _Projection(
            accessions=accessions,
            titles=titles,
            primary_or_unlabeled_count=primary_or_unlabeled_count,
            replicate_count=replicate_count,
            linked_count=linked_count,
            groups=groups,
            unrecognized_count=unrecognized_count,
        )


def _classify_title(source_id: str, title: str) -> tuple[str, str] | None:
    patterns = {
        "GEO:GSE60788": (_GSE60788_PRIMARY, _GSE60788_REPLICATE),
        "GEO:GSE96058": (_GSE96058_PRIMARY, _GSE96058_REPLICATE),
    }
    if source_id in patterns:
        primary, replicate = patterns[source_id]
        if match := primary.fullmatch(title):
            return "primary", match.group(1)
        if match := replicate.fullmatch(title):
            return "replicate", match.group(1)
        return None
    if source_id == "GEO:GSE130397":
        if match := _GSE130397_TRIPLICATE.fullmatch(title):
            state = "primary" if match.group(2) == "01" else "replicate"
            return state, match.group(1)
        if match := _GSE130397_RESEQUENCE.fullmatch(title):
            return "replicate", match.group(1)
        if title.startswith("FFPE-RNA-Seq_ACC_ER_S"):
            return "primary", title
    return None
