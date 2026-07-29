from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.analysis.platform_compatibility import (
    PlatformCompatibilityAuditError,
    PlatformCompatibilityAuditService,
)
from nas_core.domain.calibration_planning import (
    load_phase_one_internal_planning_bundle,
)
from nas_core.domain.field_isolated_metadata import (
    load_field_isolated_metadata_receipt,
)
from nas_core.domain.method_dependency import load_pam50_centroid_candidate
from nas_core.domain.platform_compatibility import (
    PlatformCompatibilityAuditReceipt,
    load_platform_compatibility_audit,
)

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
BUNDLE = STUDY / "protocol" / "phase_one_internal_planning_bundle_v1.0.0.yaml"
METADATA = STUDY / "ingestion" / "field_isolated_metadata_receipt_v1.0.1.yaml"
CANDIDATE = (
    STUDY
    / "protocol"
    / "artifact-candidates"
    / "genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
)
SPECIFICATION = STUDY / "protocol" / "reliability_specification.yaml"
SCHEMA = ROOT / "workflows" / "platform_compatibility_audit.schema.json"
RECEIPT = (
    STUDY
    / "protocol"
    / "platform_compatibility_audit_receipt_v1.0.0.yaml"
)


def _audit() -> PlatformCompatibilityAuditReceipt:
    return PlatformCompatibilityAuditService().audit(
        load_phase_one_internal_planning_bundle(BUNDLE),
        load_field_isolated_metadata_receipt(METADATA),
        load_pam50_centroid_candidate(CANDIDATE),
        bundle_path=BUNDLE,
        metadata_path=METADATA,
        candidate_path=CANDIDATE,
        reliability_specification_path=SPECIFICATION,
        code_revision="c97c262",
        audited_at=datetime(2026, 7, 29, 20, 30, tzinfo=UTC),
    )


def test_platform_audit_is_conservative_and_reconciled() -> None:
    receipt = _audit()

    assert receipt.verified_count == 1
    assert receipt.partial_count == 4
    assert receipt.pending_count == 3
    assert receipt.decision.value == "changes_required"
    assert receipt.findings[0].criterion_id == "PLAT-001"
    assert receipt.findings[0].status.value == "verified"
    assert receipt.findings[1].status.value == "partial"
    assert receipt.findings[2].status.value == "pending"
    assert receipt.molecular_values_parsed is False
    assert receipt.outcome_values_parsed is False
    assert receipt.classifier_executed is False
    assert receipt.source_selected is False
    assert receipt.transformation_locked is False
    assert receipt.reference_locked is False
    assert receipt.study_execution_authorized is False


def test_platform_audit_rejects_incomplete_gene_mapping() -> None:
    metadata = load_field_isolated_metadata_receipt(METADATA)
    changed_coverage = metadata.gse96058_gene_coverage.model_copy(
        update={
            "canonical_genes_present": (
                metadata.gse96058_gene_coverage.canonical_genes_present[:-1]
            ),
            "missing_canonical_genes": ["UBE2T"],
        }
    )
    changed_metadata = metadata.model_copy(
        update={"gse96058_gene_coverage": changed_coverage}
    )

    with pytest.raises(
        PlatformCompatibilityAuditError,
        match="does not verify complete PAM50 mapping",
    ):
        PlatformCompatibilityAuditService().audit(
            load_phase_one_internal_planning_bundle(BUNDLE),
            changed_metadata,
            load_pam50_centroid_candidate(CANDIDATE),
            bundle_path=BUNDLE,
            metadata_path=METADATA,
            candidate_path=CANDIDATE,
            reliability_specification_path=SPECIFICATION,
            code_revision="c97c262",
            audited_at=datetime(2026, 7, 29, 20, 30, tzinfo=UTC),
        )


def test_platform_audit_rejects_false_method_lock() -> None:
    receipt = _audit()
    payload = receipt.model_dump(mode="json")
    payload["decision"] = "pass"
    payload["transformation_locked"] = True
    payload["reference_locked"] = True

    with pytest.raises(ValidationError):
        PlatformCompatibilityAuditReceipt.model_validate(payload)


def test_platform_compatibility_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        PlatformCompatibilityAuditReceipt.model_json_schema()
    )


def test_checked_in_platform_audit_matches_frozen_implementation() -> None:
    receipt = load_platform_compatibility_audit(RECEIPT)
    regenerated = PlatformCompatibilityAuditService().audit(
        load_phase_one_internal_planning_bundle(BUNDLE),
        load_field_isolated_metadata_receipt(METADATA),
        load_pam50_centroid_candidate(CANDIDATE),
        bundle_path=BUNDLE,
        metadata_path=METADATA,
        candidate_path=CANDIDATE,
        reliability_specification_path=SPECIFICATION,
        code_revision=receipt.code_revision,
        audited_at=receipt.audited_at,
    )

    assert receipt == regenerated
    assert receipt.code_revision == "5a19d7e"
