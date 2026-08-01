"""Field-isolated authoritative annotation resolution for GSE130397."""

from __future__ import annotations

import gzip
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, cast

from nas_core.domain.calibration_annotation import (
    CalibrationAnnotationResolutionPlan,
    CalibrationAnnotationResolutionReceipt,
)
from nas_core.ingestion.calibration_lineage import CalibrationLineageTransport
from nas_core.ingestion.field_isolated_metadata import (
    DigestingReader,
    UrllibFieldIsolatedMetadataTransport,
)
from nas_core.ingestion.gdc import sha256


class CalibrationAnnotationResolutionError(RuntimeError):
    """Raised when official processing metadata do not reconcile."""


@dataclass(slots=True)
class _SampleProcessing:
    title: str | None = None
    processing: list[str] = field(default_factory=list)


class CalibrationAnnotationResolutionService:
    def __init__(self, transport: CalibrationLineageTransport | None = None) -> None:
        self._transport = transport or UrllibFieldIsolatedMetadataTransport()

    def execute(
        self,
        plan: CalibrationAnnotationResolutionPlan,
        *,
        plan_path: Path,
        feasibility_audit_receipt_path: Path,
        lineage_receipt_path: Path,
        code_revision: str,
    ) -> CalibrationAnnotationResolutionReceipt:
        changed = [
            label
            for label, expected, path in (
                (
                    "feasibility audit",
                    plan.feasibility_audit_receipt_sha256,
                    feasibility_audit_receipt_path,
                ),
                ("lineage receipt", plan.lineage_receipt_sha256, lineage_receipt_path),
            )
            if expected != sha256(path.read_bytes())
        ]
        if changed:
            raise CalibrationAnnotationResolutionError(
                f"annotation-resolution provenance changed: {', '.join(changed)}"
            )
        with self._transport.open_get(plan.family_soft_url) as response:
            if response.status_code != 200:
                raise CalibrationAnnotationResolutionError(
                    f"family SOFT returned HTTP {response.status_code}"
                )
            reader = DigestingReader(response.stream)
            samples = self._parse(reader)
            reader.drain()
        if reader.hexdigest() != plan.expected_family_soft_sha256:
            raise CalibrationAnnotationResolutionError("family SOFT checksum changed")

        access = [sample for sample in samples if sample.title and "_ACC_" in sample.title]
        ovation = [sample for sample in samples if sample.title and "_OVA_" in sample.title]
        grch38 = sum(
            any("GRCh38, release 84" in line for line in sample.processing)
            for sample in samples
        )
        gene_counts = sum(
            any("GeneCounts module in STAR" in line for line in sample.processing)
            for sample in samples
        )
        access_reverse = sum(
            any("reverse strand counts used for Access" in line for line in sample.processing)
            for sample in access
        )
        ovation_forward = sum(
            any(
                "forward strand counts used for Nugen-Ovation" in line
                for line in sample.processing
            )
            for sample in ovation
        )
        return CalibrationAnnotationResolutionReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            family_soft_sha256=reader.hexdigest(),
            family_soft_size_bytes=reader.size,
            sample_count=len(samples),
            grch38_release_84_count=grch38,
            star_gene_counts_count=gene_counts,
            access_library_count=len(access),
            access_reverse_directive_count=access_reverse,
            ovation_library_count=len(ovation),
            ovation_forward_directive_count=ovation_forward,
            genome_build="GRCh38",
            ensembl_release=84,
            access_count_column="rev",
            ovation_count_column="fwd",
            annotation_url=plan.candidate_annotation_url,
            annotation_expected_length_bytes=plan.candidate_annotation_length_bytes,
            resolution_complete=True,
            sample_identifiers_retained=False,
            processing_rows_retained=False,
            molecular_values_parsed=False,
            outcomes_accessed=False,
            raw_metadata_stored=False,
        )

    @staticmethod
    def _parse(reader: DigestingReader) -> list[_SampleProcessing]:
        samples: list[_SampleProcessing] = []
        current: _SampleProcessing | None = None
        with gzip.GzipFile(fileobj=cast(BinaryIO, reader), mode="rb") as decoded:
            for raw_line in decoded:
                if raw_line.startswith(b"^SAMPLE = "):
                    if current is not None:
                        samples.append(current)
                    current = _SampleProcessing()
                elif current is not None and raw_line.startswith(b"!Sample_title = "):
                    current.title = raw_line.removeprefix(b"!Sample_title = ").decode().strip()
                elif current is not None and raw_line.startswith(b"!Sample_data_processing = "):
                    current.processing.append(
                        raw_line.removeprefix(b"!Sample_data_processing = ").decode().strip()
                    )
        if current is not None:
            samples.append(current)
        if any(sample.title is None for sample in samples):
            raise CalibrationAnnotationResolutionError("sample title is missing")
        return samples
