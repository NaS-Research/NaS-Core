"""Fail-closed import of verified, non-executable PAM50 artifact candidates."""

from __future__ import annotations

import csv
import hashlib
import io
import tarfile
from datetime import datetime
from pathlib import Path

from nas_core.domain.method_dependency import (
    ArtifactCandidateStatus,
    CentroidCandidateImportReceipt,
    MethodDependencyAuditProposal,
    Pam50CentroidCandidateArtifact,
)
from nas_core.domain.reliability import PAM50_HISTORICAL_ALIASES
from nas_core.ingestion.gdc import sha256

_CENTROID_LABELS = {
    "Basal": "Basal-like",
    "Her2": "HER2-enriched",
    "LumA": "Luminal A",
    "LumB": "Luminal B",
    "Normal": "Normal-like",
}


class MethodArtifactImportError(RuntimeError):
    """Raised when a candidate package does not match its governed declaration."""


class Pam50CandidateImportService:
    def parse(
        self,
        audit: MethodDependencyAuditProposal,
        package_path: Path,
        *,
        artifact_id: str,
    ) -> Pam50CentroidCandidateArtifact:
        candidate = next(
            (
                item
                for item in audit.artifact_candidates
                if item.artifact_id == artifact_id
            ),
            None,
        )
        if candidate is None:
            raise MethodArtifactImportError("artifact is absent from the governed audit")
        if candidate.status is not ArtifactCandidateStatus.VERIFIED_CANDIDATE:
            raise MethodArtifactImportError("artifact is not a verified audit candidate")
        if (
            candidate.distribution_sha256 is None
            or candidate.member_path is None
            or candidate.member_sha256 is None
        ):
            raise MethodArtifactImportError("verified candidate hashes are incomplete")
        if sha256(package_path.read_bytes()) != candidate.distribution_sha256:
            raise MethodArtifactImportError("source distribution checksum mismatch")

        with tarfile.open(package_path, mode="r:gz") as archive:
            members = [
                member
                for member in archive.getmembers()
                if member.name == candidate.member_path
            ]
            if len(members) != 1 or not members[0].isfile():
                raise MethodArtifactImportError(
                    "source member must be one unique regular file"
                )
            member = members[0]
            if member.size > 1_000_000:
                raise MethodArtifactImportError("source member exceeds the size boundary")
            source = archive.extractfile(member)
            if source is None:
                raise MethodArtifactImportError("source member could not be extracted")
            member_bytes = source.read()
        if hashlib.sha256(member_bytes).hexdigest() != candidate.member_sha256:
            raise MethodArtifactImportError("source member checksum mismatch")

        return self._parse_member(
            member_bytes,
            artifact_id=artifact_id,
            source_url=candidate.source_url,
            distribution_version=candidate.distribution_version,
            distribution_sha256=candidate.distribution_sha256,
            member_path=candidate.member_path,
            member_sha256=candidate.member_sha256,
            license_id=candidate.license_id,
        )

    @staticmethod
    def _parse_member(
        member_bytes: bytes,
        *,
        artifact_id: str,
        source_url: str,
        distribution_version: str,
        distribution_sha256: str,
        member_path: str,
        member_sha256: str,
        license_id: str,
    ) -> Pam50CentroidCandidateArtifact:
        try:
            text = member_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise MethodArtifactImportError("source member is not UTF-8") from error
        metadata: dict[str, str] = {}
        centroid_vectors: dict[str, list[float]] = {}
        source_notice = ""
        csv_lines: list[str] = []
        for line in text.splitlines():
            if not line.startswith("#"):
                csv_lines.append(line)
                continue
            content = line.removeprefix("#").strip()
            if not source_notice:
                source_notice = content
            if ":" not in content:
                continue
            key, value = (part.strip() for part in content.split(":", maxsplit=1))
            if key.startswith("centroid."):
                label = key.removeprefix("centroid.")
                try:
                    centroid_vectors[label] = [
                        float(item) for item in value.split()
                    ]
                except ValueError as error:
                    raise MethodArtifactImportError(
                        f"centroid {label} contains a nonnumeric coefficient"
                    ) from error
            else:
                metadata[key] = value
        if set(centroid_vectors) != set(_CENTROID_LABELS):
            raise MethodArtifactImportError("source member does not contain five centroids")
        if any(len(values) != 50 for values in centroid_vectors.values()):
            raise MethodArtifactImportError(
                "every source centroid must contain exactly 50 coefficients"
            )
        if metadata.get("method.cor") != "spearman":
            raise MethodArtifactImportError("source member correlation is not Spearman")
        if metadata.get("method.centroids") != "mean":
            raise MethodArtifactImportError("source member centroid method is not mean")
        if metadata.get("std") != "none":
            raise MethodArtifactImportError("source member standardization is not none")

        rows = list(csv.DictReader(io.StringIO("\n".join(csv_lines))))
        if len(rows) != 50 or any(row.get("probe") is None for row in rows):
            raise MethodArtifactImportError(
                "source member must declare exactly 50 ordered probes"
            )
        gene_order = [row["probe"] for row in rows]
        centroids = {
            _CENTROID_LABELS[label]: dict(zip(gene_order, values, strict=True))
            for label, values in centroid_vectors.items()
        }
        return Pam50CentroidCandidateArtifact(
            artifact_version="1.0.0",
            artifact_id=artifact_id,
            source_url=source_url,
            source_distribution_version=distribution_version,
            source_distribution_sha256=distribution_sha256,
            source_member_path=member_path,
            source_member_sha256=member_sha256,
            license_id=license_id,
            source_notice=source_notice,
            method_correlation="spearman",
            method_centroids="mean",
            expression_standardization="none",
            gene_order=gene_order,
            historical_aliases=PAM50_HISTORICAL_ALIASES,
            centroids=centroids,
            candidate_only=True,
            founder_approved=False,
            method_execution_authorized=False,
        )

    @staticmethod
    def receipt(
        audit: MethodDependencyAuditProposal,
        *,
        audit_path: Path,
        candidate: Pam50CentroidCandidateArtifact,
        candidate_path: Path,
        code_revision: str,
        imported_at: datetime,
    ) -> CentroidCandidateImportReceipt:
        candidate_bytes = candidate_path.read_bytes()
        return CentroidCandidateImportReceipt(
            receipt_version="1.0.0",
            study_id=audit.study_id,
            question_id=audit.question_id,
            question_version=audit.question_version,
            method_dependency_audit_sha256=sha256(audit_path.read_bytes()),
            source_distribution_sha256=candidate.source_distribution_sha256,
            source_member_sha256=candidate.source_member_sha256,
            candidate_artifact_path=str(candidate_path),
            candidate_artifact_sha256=sha256(candidate_bytes),
            candidate_artifact_size_bytes=len(candidate_bytes),
            coefficient_count=sum(
                len(values) for values in candidate.centroids.values()
            ),
            gene_count=len(candidate.gene_order),
            subtype_count=len(candidate.centroids),
            code_revision=code_revision,
            imported_at=imported_at,
            candidate_only=True,
            founder_approved=False,
            method_execution_authorized=False,
            molecular_data_accessed=False,
            outcome_data_accessed=False,
        )
