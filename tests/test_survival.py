import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.analysis.survival import SurvivalAnalysisError, SurvivalAnalysisService
from nas_core.domain.cohorts import (
    CohortArtifact,
    CohortBuildManifest,
    CohortBuildReceipt,
    CohortVerification,
)
from nas_core.domain.research import AnalysisPlan, ReviewRecord
from nas_core.domain.survival import SurvivalAnalysisSummary, SurvivalRunManifest
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
PLAN_PATH = (
    ROOT / "workflows" / "studies" / "tcga_brca_stage_survival" / "protocol" / "analysis_plan.yaml"
)
SUMMARY_SCHEMA_PATH = ROOT / "workflows" / "survival_analysis.schema.json"
RUN_SCHEMA_PATH = ROOT / "workflows" / "survival_run.schema.json"
NOW = datetime(2026, 7, 22, 2, 0, tzinfo=UTC)
BUILD_ID = "b" * 64
MANIFEST_KEY = f"analysis-ready/gdc/NAS-BRCA-001/snapshot/{BUILD_ID}/manifest.json"
CODE_REVISION = "c" * 40


def _plan() -> AnalysisPlan:
    return AnalysisPlan.model_validate(yaml.safe_load(PLAN_PATH.read_text(encoding="utf-8")))


def _cohort_csv(*, small_event_group: bool = False, invalid_exposure: bool = False) -> bytes:
    output = io.StringIO(newline="")
    fieldnames = [
        "case_id",
        "submitter_id",
        "diagnosis_id",
        "pathologic_stage",
        "advanced_pathologic_stage",
        "ajcc_staging_system_edition",
        "age_at_diagnosis_days",
        "age_at_diagnosis_years",
        "vital_status",
        "duration_days",
        "event",
        "survival_time_source",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for advanced in (0, 1):
        for index in range(40):
            event_limit = (
                5 if small_event_group and advanced == 0 else (15 if advanced == 0 else 25)
            )
            event = int(index < event_limit)
            duration = (1250 + index * 45) if advanced == 0 else (450 + index * 32)
            if not event:
                duration += 1500
            stage = ("I", "II")[index % 2] if advanced == 0 else ("III", "IV")[index % 2]
            exposure = 0 if invalid_exposure and stage in {"III", "IV"} else advanced
            age = 42 + (index % 22) + advanced * 2
            writer.writerow(
                {
                    "case_id": f"case-{advanced}-{index:02d}",
                    "submitter_id": f"submitter-{advanced}-{index:02d}",
                    "diagnosis_id": f"dx-{advanced}-{index:02d}",
                    "pathologic_stage": stage,
                    "advanced_pathologic_stage": exposure,
                    "ajcc_staging_system_edition": "7th" if index < 32 else "8th",
                    "age_at_diagnosis_days": age * 365.25,
                    "age_at_diagnosis_years": age,
                    "vital_status": "dead" if event else "alive",
                    "duration_days": duration,
                    "event": event,
                    "survival_time_source": "synthetic",
                }
            )
    return output.getvalue().encode("utf-8")


def _fixture(
    *,
    approved: bool = True,
    small_event_group: bool = False,
    invalid_exposure: bool = False,
) -> tuple[InMemoryObjectStore, CohortBuildReceipt]:
    store = InMemoryObjectStore()
    prefix = f"analysis-ready/gdc/NAS-BRCA-001/snapshot/{BUILD_ID}"
    payloads = {
        f"{prefix}/cohort.csv": (
            "text/csv",
            _cohort_csv(small_event_group=small_event_group, invalid_exposure=invalid_exposure),
        ),
        f"{prefix}/exclusions.csv": ("text/csv", b"case_id,reason\n"),
        f"{prefix}/qa-summary.json": ("application/json", b"{}"),
    }
    artifacts: list[CohortArtifact] = []
    for key, (media_type, body) in payloads.items():
        store.put_bytes(key, body, content_type=media_type)
        artifacts.append(
            CohortArtifact(
                object_key=key,
                media_type=media_type,
                size_bytes=len(body),
                sha256=sha256(body),
            )
        )
    manifest = CohortBuildManifest(
        build_id=BUILD_ID,
        study_id="NAS-BRCA-001",
        protocol_version="1.1.0",
        protocol_tag="NAS-BRCA-001-protocol-v1.1.0",
        snapshot_id="a" * 64,
        snapshot_manifest_sha256="d" * 64,
        algorithm_version="synthetic-cohort-1.0.0",
        code_revision="e" * 40,
        built_at=NOW,
        input_case_count=80,
        included_case_count=80,
        excluded_case_count=0,
        artifacts=artifacts,
    )
    manifest_hash = sha256(canonical_json(manifest.model_dump(mode="json", exclude_none=True)))
    manifest = manifest.model_copy(update={"manifest_sha256": manifest_hash})
    store.put_bytes(
        MANIFEST_KEY,
        canonical_json(manifest.model_dump(mode="json", exclude_none=True)),
        content_type="application/json",
    )
    decision = "approved" if approved else "pending"
    reviewed_at = NOW if approved else None
    review = ReviewRecord.model_validate(
        {
            "reviewer": "Synthetic Founder",
            "role": "Founder and internal reviewer",
            "review_type": "internal_self_review",
            "required_for_gate": True,
            "decision": decision,
            "reviewed_at": reviewed_at,
            "notes": "Synthetic gate record for deterministic tests.",
        }
    )
    receipt = CohortBuildReceipt(
        study_id="NAS-BRCA-001",
        protocol_version="1.1.0",
        protocol_tag="NAS-BRCA-001-protocol-v1.1.0",
        snapshot_id="a" * 64,
        build_id=BUILD_ID,
        algorithm_version="synthetic-cohort-1.0.0",
        code_revision="e" * 40,
        built_at=NOW,
        input_case_count=80,
        included_case_count=80,
        excluded_case_count=0,
        exclusion_counts={},
        manifest_object_key=MANIFEST_KEY,
        manifest_sha256=manifest_hash,
        artifacts=artifacts,
        verification=CohortVerification(
            verified_at=NOW,
            manifest_payload_checksum="passed",
            artifact_checksums="passed",
            case_partition_unique="passed",
            case_partition_disjoint="passed",
            case_partition_complete="passed",
            requested_field_missingness_complete="passed",
            outcome_analysis_performed=False,
        ),
        qa_gate_status="approved" if approved else "pending_founder_review",
        reviews=[review],
    )
    return store, receipt


def test_checked_in_survival_schemas_match_typed_models() -> None:
    assert (
        json.loads(SUMMARY_SCHEMA_PATH.read_text()) == SurvivalAnalysisSummary.model_json_schema()
    )
    assert json.loads(RUN_SCHEMA_PATH.read_text()) == SurvivalRunManifest.model_json_schema()


def test_survival_run_generates_typed_immutable_artifacts() -> None:
    store, receipt = _fixture()
    manifest = SurvivalAnalysisService(store=store, clock=lambda: NOW).run(
        _plan(), receipt, code_revision=CODE_REVISION
    )

    assert len(manifest.artifacts) == 5
    assert manifest.cohort_build_id == BUILD_ID
    assert manifest.manifest_sha256 is not None
    summary_key = next(
        item.object_key
        for item in manifest.artifacts
        if item.object_key.endswith("analysis-summary.json")
    )
    summary = SurvivalAnalysisSummary.model_validate_json(store.get_bytes(summary_key))
    assert summary.participant_count == 80
    assert summary.event_count == 40
    assert summary.primary_model.analysis_id == "H1"
    assert {model.analysis_id for model in summary.sensitivity_models} == {
        "S1",
        "S2",
        "S3",
        "S4",
        "S5",
    }
    assert summary.generated_by_deterministic_code is True


def test_survival_run_is_byte_deterministic_for_same_identity_and_clock() -> None:
    store, receipt = _fixture()
    service = SurvivalAnalysisService(store=store, clock=lambda: NOW)
    first = service.run(_plan(), receipt, code_revision=CODE_REVISION)
    first_bytes = {
        artifact.object_key: store.get_bytes(artifact.object_key) for artifact in first.artifacts
    }

    second = service.run(_plan(), receipt, code_revision=CODE_REVISION)

    assert second == first
    assert {
        artifact.object_key: store.get_bytes(artifact.object_key) for artifact in second.artifacts
    } == first_bytes


def test_survival_run_abstains_when_group_has_too_few_events() -> None:
    store, receipt = _fixture(small_event_group=True)
    manifest = SurvivalAnalysisService(store=store, clock=lambda: NOW).run(
        _plan(), receipt, code_revision=CODE_REVISION
    )
    summary_key = next(
        item.object_key
        for item in manifest.artifacts
        if item.object_key.endswith("analysis-summary.json")
    )
    summary = SurvivalAnalysisSummary.model_validate_json(store.get_bytes(summary_key))

    assert summary.primary_model.status == "not_interpretable"
    assert summary.qualification_decision == "fail"


def test_survival_run_rejects_unapproved_gate() -> None:
    store, receipt = _fixture(approved=False)

    with pytest.raises(SurvivalAnalysisError, match="approved cohort QA gate"):
        SurvivalAnalysisService(store=store).run(_plan(), receipt, code_revision=CODE_REVISION)


def test_survival_run_rejects_tampered_artifact() -> None:
    store, receipt = _fixture()
    cohort_key = next(
        item.object_key for item in receipt.artifacts if item.object_key.endswith("cohort.csv")
    )
    store.put_bytes(cohort_key, b"tampered", content_type="text/csv")

    with pytest.raises(SurvivalAnalysisError, match="checksum mismatch"):
        SurvivalAnalysisService(store=store).run(_plan(), receipt, code_revision=CODE_REVISION)


def test_survival_run_rejects_inconsistent_exposure() -> None:
    store, receipt = _fixture(invalid_exposure=True)

    with pytest.raises(SurvivalAnalysisError, match="exposure is inconsistent"):
        SurvivalAnalysisService(store=store).run(_plan(), receipt, code_revision=CODE_REVISION)
