import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.analysis.cohort import CohortBuildError, CohortBuildService, canonical_json, sha256
from nas_core.domain.cohorts import (
    CohortBuildManifest,
    CohortQASummary,
    SnapshotReceipt,
)
from nas_core.domain.research import AnalysisPlan
from nas_core.domain.snapshots import DatasetSnapshot, ReleaseRecord, StoredObject
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
PLAN_PATH = (
    ROOT / "workflows" / "studies" / "tcga_brca_stage_survival" / "protocol" / "analysis_plan.yaml"
)
RECEIPT_PATH = (
    ROOT
    / "workflows"
    / "studies"
    / "tcga_brca_stage_survival"
    / "ingestion"
    / "snapshot_receipt.yaml"
)
QA_SCHEMA_PATH = ROOT / "workflows" / "cohort_qa.schema.json"
MANIFEST_SCHEMA_PATH = ROOT / "workflows" / "cohort_build.schema.json"
NOW = datetime(2026, 7, 21, 20, 0, tzinfo=UTC)
SNAPSHOT_ID = "b" * 64
CODE_REVISION = "a" * 40


def _plan(*, approved: bool = True) -> AnalysisPlan:
    payload = yaml.safe_load(PLAN_PATH.read_text(encoding="utf-8"))
    if not approved:
        payload["status"] = "pending_review"
        payload["reviews"][0]["decision"] = "pending"
        payload["reviews"][0]["reviewed_at"] = None
    return AnalysisPlan.model_validate(payload)


def _diagnosis(
    diagnosis_id: str,
    *,
    primary: bool = True,
    stage: str = "Stage IIA",
    age_days: int = 20_000,
    days_to_diagnosis: int | None = 0,
    days_to_last_follow_up: int | None = 1_000,
) -> dict[str, object]:
    return {
        "diagnosis_id": diagnosis_id,
        "diagnosis_is_primary_disease": primary,
        "ajcc_pathologic_stage": stage,
        "ajcc_staging_system_edition": "7th",
        "age_at_diagnosis": age_days,
        "days_to_diagnosis": days_to_diagnosis,
        "days_to_last_follow_up": days_to_last_follow_up,
    }


def _case(
    case_id: str,
    *,
    diagnoses: list[dict[str, object]] | None = None,
    index_date: str = "Diagnosis",
    vital_status: str = "Alive",
    days_to_death: int | None = None,
    follow_up_days: int | None = 1_200,
) -> dict[str, object]:
    demographic: dict[str, object] = {"vital_status": vital_status}
    if days_to_death is not None:
        demographic["days_to_death"] = days_to_death
    follow_ups = (
        [{"follow_up_id": f"fu-{case_id}", "days_to_follow_up": follow_up_days}]
        if follow_up_days is not None
        else []
    )
    return {
        "case_id": case_id,
        "submitter_id": f"submitter-{case_id}",
        "index_date": index_date,
        "demographic": demographic,
        "diagnoses": diagnoses if diagnoses is not None else [_diagnosis(f"dx-{case_id}")],
        "follow_ups": follow_ups,
    }


def _fixture() -> tuple[InMemoryObjectStore, SnapshotReceipt, list[dict[str, object]]]:
    cases = [
        _case(
            "case-early",
            diagnoses=[
                _diagnosis("dx-false", primary=False, stage="Stage IV"),
                _diagnosis("dx-later", stage="Stage IIA", days_to_diagnosis=5),
                _diagnosis("dx-chosen", stage="Stage IA", days_to_diagnosis=0),
            ],
        ),
        _case(
            "case-advanced",
            diagnoses=[_diagnosis("dx-advanced", stage="Stage IIIB")],
            vital_status="Dead",
            days_to_death=700,
        ),
        _case("excluded-index", index_date="Enrollment"),
        _case("excluded-primary", diagnoses=[_diagnosis("dx", primary=False)]),
        _case("excluded-stage", diagnoses=[_diagnosis("dx", stage="Not Reported")]),
        _case("excluded-underage", diagnoses=[_diagnosis("dx", age_days=1_000)]),
        _case("excluded-vital", vital_status="Unknown"),
        _case(
            "excluded-survival",
            follow_up_days=None,
            diagnoses=[_diagnosis("dx", days_to_last_follow_up=None)],
        ),
    ]
    page_body = canonical_json(
        {
            "data": {
                "hits": cases,
                "pagination": {"count": len(cases), "total": len(cases)},
            },
            "warnings": {},
        }
    )
    page_key = f"raw/gdc/NAS-BRCA-001/{SNAPSHOT_ID}/pages/00001.json"
    page = StoredObject(
        object_key=page_key,
        media_type="application/json",
        size_bytes=len(page_body),
        sha256=sha256(page_body),
        record_ids=[str(case["case_id"]) for case in cases],
    )
    snapshot = DatasetSnapshot(
        schema_version="1.0.0",
        snapshot_id=SNAPSHOT_ID,
        study_id="NAS-BRCA-001",
        protocol_version="1.1.0",
        source_id="gdc-tcga-open",
        project_id="TCGA-BRCA",
        classification="public_open",
        purpose="oncology-research",
        retrieved_at=NOW,
        release=ReleaseRecord(
            data_release="45.0",
            release_notes_url="https://docs.gdc.cancer.gov/releases",
            release_notes_retrieved_at=NOW,
            release_notes_sha256="c" * 64,
            api_status="OK",
            api_tag="8.5.0",
            api_version="1",
            api_commit="d" * 40,
            status_response_sha256="e" * 64,
        ),
        requests=[
            {
                "method": "POST",
                "url": "https://api.gdc.cancer.gov/cases",
                "body": {"from": 0},
            }
        ],
        objects=[page],
        record_count=len(cases),
        warnings=[],
    )
    snapshot_hash = sha256(canonical_json(snapshot.model_dump(mode="json", exclude_none=True)))
    snapshot = snapshot.model_copy(update={"manifest_sha256": snapshot_hash})
    manifest_key = f"raw/gdc/NAS-BRCA-001/{SNAPSHOT_ID}/manifest.json"
    store = InMemoryObjectStore()
    store.put_bytes(page_key, page_body, content_type="application/json")
    store.put_bytes(
        manifest_key,
        canonical_json(snapshot.model_dump(mode="json", exclude_none=True)),
        content_type="application/json",
    )
    receipt = SnapshotReceipt(
        schema_version="1.0.0",
        study_id="NAS-BRCA-001",
        protocol_version="1.1.0",
        protocol_tag="NAS-BRCA-001-protocol-v1.1.0",
        ingestion_code_revision="f" * 40,
        source_id="gdc-tcga-open",
        project_id="TCGA-BRCA",
        classification="public_open",
        data_release="45.0",
        api_tag="8.5.0",
        snapshot_id=SNAPSHOT_ID,
        retrieved_at=NOW,
        record_count=len(cases),
        page_count=1,
        warning_count=0,
        manifest_object_key=manifest_key,
        manifest_sha256=snapshot_hash,
        release_notes_url="https://docs.gdc.cancer.gov/releases",
        release_notes_sha256="c" * 64,
        verification={
            "verified_at": NOW,
            "manifest_payload_checksum": "passed",
            "stored_object_checksums": "passed",
            "verified_object_count": 1,
            "duplicate_case_check": "passed",
            "pagination_count_check": "passed",
            "outcome_analysis_performed": False,
        },
    )
    return store, receipt, cases


def test_checked_in_receipt_and_schemas_are_typed() -> None:
    receipt = SnapshotReceipt.model_validate(yaml.safe_load(RECEIPT_PATH.read_text()))

    assert receipt.study_id == "NAS-BRCA-001"
    assert json.loads(QA_SCHEMA_PATH.read_text()) == CohortQASummary.model_json_schema()
    assert json.loads(MANIFEST_SCHEMA_PATH.read_text()) == CohortBuildManifest.model_json_schema()


def test_build_creates_cohort_exclusions_and_nonoutcome_qa() -> None:
    store, receipt, _ = _fixture()

    manifest = CohortBuildService(store=store, clock=lambda: NOW).build(
        _plan(), receipt, code_revision=CODE_REVISION
    )

    assert manifest.included_case_count == 2
    assert manifest.excluded_case_count == 6
    artifacts = {
        artifact.object_key.rsplit("/", 1)[-1]: artifact for artifact in manifest.artifacts
    }
    cohort_rows = list(
        csv.DictReader(io.StringIO(store.get_bytes(artifacts["cohort.csv"].object_key).decode()))
    )
    assert [row["case_id"] for row in cohort_rows] == ["case-advanced", "case-early"]
    assert cohort_rows[1]["diagnosis_id"] == "dx-chosen"
    assert cohort_rows[1]["pathologic_stage"] == "I"

    qa = json.loads(store.get_bytes(artifacts["qa-summary.json"].object_key))
    assert qa["included_case_count"] == 2
    assert sum(qa["exclusion_counts"].values()) == 6
    assert set(qa["missingness_counts"]) == set(_plan().data_requirements[0].fields)
    assert qa["included_descriptives"]["case_count"] == 2
    assert qa["excluded_descriptives"]["case_count"] == 6
    assert qa["outcome_analysis_performed"] is False
    assert "hazard" not in json.dumps(qa).casefold()


def test_build_rejects_tampered_snapshot_page() -> None:
    store, receipt, _ = _fixture()
    manifest = json.loads(store.get_bytes(receipt.manifest_object_key))
    page_key = manifest["objects"][0]["object_key"]
    store.put_bytes(page_key, b"{}", content_type="application/json")

    with pytest.raises(CohortBuildError, match="page checksum mismatch"):
        CohortBuildService(store=store, clock=lambda: NOW).build(
            _plan(), receipt, code_revision=CODE_REVISION
        )


def test_build_rejects_unapproved_plan_before_reading_snapshot() -> None:
    store, receipt, _ = _fixture()

    with pytest.raises(CohortBuildError, match="preregistered plan"):
        CohortBuildService(store=store, clock=lambda: NOW).build(
            _plan(approved=False), receipt, code_revision=CODE_REVISION
        )
