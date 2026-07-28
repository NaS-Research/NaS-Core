import hashlib
import io
import tarfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.analysis.method_artifact import (
    MethodArtifactImportError,
    Pam50CandidateImportService,
)
from nas_core.domain.method_dependency import (
    MethodDependencyAuditProposal,
    Pam50CentroidCandidateArtifact,
    load_method_dependency_audit,
)
from nas_core.domain.reliability import PAM50_HISTORICAL_GENES

ROOT = Path(__file__).parents[1]
AUDIT = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "protocol"
    / "method_dependency_audit_proposal_v1.0.0.yaml"
)
MEMBER_PATH = "genefu/inst/extdata/pam50_model.csv"


def _member_bytes() -> bytes:
    genes = sorted(PAM50_HISTORICAL_GENES)
    lines = [
        "# Test fixture. All rights reserved.",
        "# method.cor: spearman",
        "# method.centroids: mean",
        "# std: none",
        "# rescale.q: 0.05",
        "# mins: 5",
    ]
    for offset, label in enumerate(("Basal", "Her2", "LumA", "LumB", "Normal")):
        values = " ".join(
            str((index + 1 + offset) / 100) for index in range(50)
        )
        lines.append(f"# centroid.{label}: {values}")
    lines.extend(
        [
            '"probe","probe.centroids","EntrezGene.ID"',
            *[f'"{gene}","{gene}","{index + 1}"' for index, gene in enumerate(genes)],
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def _package(tmp_path: Path) -> tuple[Path, bytes]:
    member_bytes = _member_bytes()
    package = tmp_path / "genefu.tar.gz"
    with tarfile.open(package, mode="w:gz") as archive:
        info = tarfile.TarInfo(MEMBER_PATH)
        info.size = len(member_bytes)
        info.mtime = 0
        archive.addfile(info, io.BytesIO(member_bytes))
    return package, member_bytes


def _audit_for_package(
    package: Path,
    member_bytes: bytes,
) -> MethodDependencyAuditProposal:
    audit = load_method_dependency_audit(AUDIT)
    candidate = audit.artifact_candidates[0].model_copy(
        update={
            "distribution_sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
            "member_sha256": hashlib.sha256(member_bytes).hexdigest(),
            "member_path": MEMBER_PATH,
        }
    )
    return audit.model_copy(
        update={
            "artifact_candidates": [
                candidate,
                *audit.artifact_candidates[1:],
            ]
        }
    )


def test_importer_parses_exact_panel_and_remains_nonexecuting(
    tmp_path: Path,
) -> None:
    package, member_bytes = _package(tmp_path)
    audit = _audit_for_package(package, member_bytes)

    artifact = Pam50CandidateImportService().parse(
        audit,
        package,
        artifact_id="genefu-2-44-0-pam50-model",
    )

    assert len(artifact.gene_order) == 50
    assert len(artifact.centroids) == 5
    assert sum(len(values) for values in artifact.centroids.values()) == 250
    assert artifact.candidate_only is True
    assert artifact.founder_approved is False
    assert artifact.method_execution_authorized is False


def test_importer_rejects_distribution_checksum_drift(tmp_path: Path) -> None:
    package, member_bytes = _package(tmp_path)
    audit = _audit_for_package(package, member_bytes)
    package.write_bytes(package.read_bytes() + b"drift")

    with pytest.raises(MethodArtifactImportError, match="distribution checksum"):
        Pam50CandidateImportService().parse(
            audit,
            package,
            artifact_id="genefu-2-44-0-pam50-model",
        )


def test_importer_rejects_nonverified_candidate(tmp_path: Path) -> None:
    package, member_bytes = _package(tmp_path)
    audit = _audit_for_package(package, member_bytes)
    candidate = audit.artifact_candidates[0].model_copy(
        update={"status": "insufficient"}
    )
    changed = audit.model_copy(
        update={
            "artifact_candidates": [
                candidate,
                *audit.artifact_candidates[1:],
            ]
        }
    )

    with pytest.raises(MethodArtifactImportError, match="not a verified"):
        Pam50CandidateImportService().parse(
            changed,
            package,
            artifact_id="genefu-2-44-0-pam50-model",
        )


def test_candidate_model_cannot_record_founder_approval() -> None:
    payload = {
        "artifact_version": "1.0.0",
        "artifact_id": "candidate",
        "source_url": "https://example.invalid",
        "source_distribution_version": "test",
        "source_distribution_sha256": "0" * 64,
        "source_member_path": MEMBER_PATH,
        "source_member_sha256": "1" * 64,
        "license_id": "test",
        "source_notice": "test",
        "method_correlation": "spearman",
        "method_centroids": "mean",
        "expression_standardization": "none",
        "gene_order": sorted(PAM50_HISTORICAL_GENES),
        "historical_aliases": {
            "CDCA1": "NUF2",
            "KNTC2": "NDC80",
            "ORC6L": "ORC6",
        },
        "centroids": {
            label: {gene: 0.0 for gene in PAM50_HISTORICAL_GENES}
            for label in (
                "Luminal A",
                "Luminal B",
                "HER2-enriched",
                "Basal-like",
                "Normal-like",
            )
        },
        "candidate_only": True,
        "founder_approved": True,
        "method_execution_authorized": False,
    }

    with pytest.raises(ValidationError, match="cannot record founder approval"):
        Pam50CentroidCandidateArtifact.model_validate(payload)
