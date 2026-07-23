from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.domain.appraisal import FullTextInventory
from nas_core.retrieval.appraisal_progress import (
    AppraisalProgressError,
    FullTextAppraisalProgressService,
)


def _inventory() -> FullTextInventory:
    return FullTextInventory.model_validate(
        {
            "study_id": "NAS-BRCA-002",
            "queue_id": "a" * 64,
            "progress_id": "b" * 64,
            "provisional_inclusion_count": 2,
            "repository_candidate_count": 2,
            "access_check_required_count": 0,
            "records": [
                {
                    "screening_id": "c" * 64,
                    "record_key": "pmid:1",
                    "title": "One",
                    "pmcid": "PMC1",
                    "access_status": "repository_candidate",
                },
                {
                    "screening_id": "d" * 64,
                    "record_key": "pmid:2",
                    "title": "Two",
                    "pmcid": "PMC2",
                    "access_status": "repository_candidate",
                },
            ],
        }
    )


def _write_yaml(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def _receipt_payload() -> dict[str, object]:
    return {
        "retrieval_id": "e" * 64,
        "study_id": "NAS-BRCA-002",
        "queue_id": "a" * 64,
        "progress_id": "b" * 64,
        "screening_id": "c" * 64,
        "pmcid": "PMC1",
        "title": "One",
        "source_url": "https://example.org/one.xml",
        "retrieved_at": "2026-07-22T00:00:00Z",
        "code_revision": "abcdef1",
        "license": {
            "name": "Creative Commons Attribution 4.0 International",
            "spdx_identifier": "CC-BY-4.0",
            "url": "https://creativecommons.org/licenses/by/4.0/",
            "copyright_statement": "Synthetic",
        },
        "manifest_object_key": "manifest.json",
        "manifest_sha256": "f" * 64,
        "full_text_object_key": "article.xml",
        "full_text_sha256": "1" * 64,
        "full_text_size_bytes": 10,
        "verified_at": "2026-07-22T00:00:01Z",
        "manifest_checksum_verified": True,
        "full_text_checksum_verified": True,
        "article_identity_verified": True,
        "license_verified": True,
    }


def _appraisal_payload() -> dict[str, object]:
    domains = [
        {
            "domain": name,
            "judgment": "some_concerns",
            "rationale": "Synthetic rationale.",
            "evidence_locations": ["Methods"],
        }
        for name in (
            "population_selection",
            "specimen_and_measurement",
            "classifier_implementation",
            "reference_comparator",
            "analysis_and_statistics",
            "validation_and_transportability",
            "reporting_and_reproducibility",
        )
    ]
    return {
        "appraisal_version": "1.0.0",
        "study_id": "NAS-BRCA-002",
        "screening_id": "c" * 64,
        "title": "One",
        "full_text_source_url": "https://example.org/one.xml",
        "full_text_sha256": "1" * 64,
        "access_basis": "Synthetic CC BY fixture.",
        "study_design": "classifier_comparison",
        "eligibility": "eligible",
        "domains": domains,
        "evidence_role": "supporting",
        "key_strengths": [],
        "key_limitations": [],
        "conflicts_and_funding": "Synthetic.",
        "reviewer_id": "dalron-j-robertson",
        "reviewer_name": "Dalron J. Robertson",
        "review_method": "founder_only",
        "founder_authorized": True,
        "assessed_at": "2026-07-22T00:00:00Z",
    }


def _access_decision_payload() -> dict[str, object]:
    return {
        "decision_version": "1.0.0",
        "study_id": "NAS-BRCA-002",
        "screening_id": "d" * 64,
        "pmcid": "PMC2",
        "title": "Two",
        "source_url": "https://example.org/two.xml",
        "observed_license": "CC-BY-NC-4.0",
        "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
        "outcome": "restricted",
        "policy_reason": "Commercial reuse is not authorized.",
        "checked_at": "2026-07-22T00:00:00Z",
    }


def _duplicate_decision_payload() -> dict[str, object]:
    return {
        "decision_version": "1.0.0",
        "study_id": "NAS-BRCA-002",
        "screening_id": "d" * 64,
        "title": "Two",
        "relationship": "preprint_of",
        "canonical_screening_id": "c" * 64,
        "canonical_title": "One",
        "matching_identifiers": ["doi:10.1/preprint", "doi:10.1/version"],
        "rationale": "Synthetic preprint and version-of-record pair.",
        "reviewer_id": "dalron-j-robertson",
        "reviewer_name": "Dalron J. Robertson",
        "founder_authorized": True,
        "decided_at": "2026-07-23T00:00:00Z",
    }


def test_progress_reconciles_retrieval_and_appraisal(tmp_path: Path) -> None:
    receipt = _write_yaml(tmp_path / "receipt.yaml", _receipt_payload())
    appraisal = _write_yaml(tmp_path / "appraisal.yaml", _appraisal_payload())
    progress = FullTextAppraisalProgressService(
        clock=lambda: datetime(2026, 7, 22, tzinfo=UTC)
    ).build(
        _inventory(),
        retrieval_receipt_paths=[receipt],
        appraisal_paths=[appraisal],
    )

    assert progress.full_texts_retrieved == 1
    assert progress.appraisals_completed == 1
    assert progress.supporting_count == 1
    assert [item.status for item in progress.records] == [
        "completed",
        "awaiting_full_text",
    ]


def test_progress_rejects_appraisal_without_receipt(tmp_path: Path) -> None:
    appraisal = _write_yaml(tmp_path / "appraisal.yaml", _appraisal_payload())

    with pytest.raises(AppraisalProgressError, match="lacks a verified"):
        FullTextAppraisalProgressService().build(
            _inventory(), retrieval_receipt_paths=[], appraisal_paths=[appraisal]
        )


def test_progress_records_restricted_access_without_claiming_retrieval(
    tmp_path: Path,
) -> None:
    decision = _write_yaml(tmp_path / "decision.yaml", _access_decision_payload())

    progress = FullTextAppraisalProgressService().build(
        _inventory(),
        retrieval_receipt_paths=[],
        appraisal_paths=[],
        access_decision_paths=[decision],
    )

    assert progress.full_texts_retrieved == 0
    assert progress.access_restricted_count == 1
    assert progress.records[1].status == "access_restricted"
    assert progress.records[1].observed_license == "CC-BY-NC-4.0"


def test_progress_rejects_restricted_and_retrieved_conflict(tmp_path: Path) -> None:
    receipt_payload = _receipt_payload()
    receipt_payload["screening_id"] = "d" * 64
    receipt_payload["pmcid"] = "PMC2"
    receipt_payload["title"] = "Two"
    receipt = _write_yaml(tmp_path / "receipt.yaml", receipt_payload)
    decision = _write_yaml(tmp_path / "decision.yaml", _access_decision_payload())

    with pytest.raises(AppraisalProgressError, match="both access-restricted"):
        FullTextAppraisalProgressService().build(
            _inventory(),
            retrieval_receipt_paths=[receipt],
            appraisal_paths=[],
            access_decision_paths=[decision],
        )


def test_progress_resolves_preprint_without_double_counting_evidence(
    tmp_path: Path,
) -> None:
    receipt = _write_yaml(tmp_path / "receipt.yaml", _receipt_payload())
    appraisal = _write_yaml(tmp_path / "appraisal.yaml", _appraisal_payload())
    duplicate = _write_yaml(tmp_path / "duplicate.yaml", _duplicate_decision_payload())

    progress = FullTextAppraisalProgressService().build(
        _inventory(),
        retrieval_receipt_paths=[receipt],
        appraisal_paths=[appraisal],
        duplicate_decision_paths=[duplicate],
    )

    assert progress.appraisals_completed == 1
    assert progress.duplicate_resolved_count == 1
    assert progress.records[1].status == "duplicate_resolved"
    assert progress.records[1].canonical_screening_id == "c" * 64
