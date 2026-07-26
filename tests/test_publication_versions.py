from datetime import UTC, datetime

import pytest

from nas_core.domain.appraisal import (
    AppraisalDomainName,
    FullTextAppraisal,
    PublicationVersionLinkDecision,
)
from nas_core.retrieval.publication_versions import (
    PublicationVersionReconciliationError,
    PublicationVersionReconciliationService,
)

NOW = datetime(2026, 7, 26, tzinfo=UTC)


def _appraisal(
    *,
    screening_id: str,
    title: str,
    pmid: str,
    doi: str,
) -> FullTextAppraisal:
    return FullTextAppraisal(
        appraisal_version="1.0.0",
        study_id="NAS-BRCA-002",
        screening_id=screening_id,
        title=title,
        pmid=pmid,
        doi=doi,
        full_text_source_url="https://example.org/article",
        full_text_sha256="f" * 64,
        access_basis="Synthetic test source.",
        study_design="prediction_model",
        eligibility="eligible",
        domains=[
            {
                "domain": domain,
                "judgment": "some_concerns",
                "rationale": "Synthetic rationale.",
                "evidence_locations": ["Methods"],
            }
            for domain in AppraisalDomainName
        ],
        evidence_role="context_only",
        key_strengths=[],
        key_limitations=[],
        conflicts_and_funding="Synthetic fixture.",
        reviewer_id="dalron-j-robertson",
        reviewer_name="Dalron J. Robertson",
        review_method="founder_only",
        founder_authorized=True,
        assessed_at=NOW,
    )


def _version_link() -> PublicationVersionLinkDecision:
    return PublicationVersionLinkDecision(
        decision_version="1.0.0",
        study_id="NAS-BRCA-002",
        relationship="preprint_of",
        earlier={
            "screening_id": "a" * 64,
            "title": "A preprint.",
            "publication_stage": "preprint",
            "pmid": "1",
            "doi": "10.1/preprint",
        },
        canonical={
            "screening_id": "b" * 64,
            "title": "A version of record.",
            "publication_stage": "version_of_record",
            "pmid": "2",
            "doi": "10.1/version",
        },
        matching_evidence=[
            "Same cohort.",
            "Same authors.",
            "Same analysis.",
        ],
        rationale="The peer-reviewed report supersedes its preprint.",
        reviewer_id="dalron-j-robertson",
        reviewer_name="Dalron J. Robertson",
        review_method="founder_with_ai_assistance",
        assistant_disclosure="AI proposed the link; founder authorized it.",
        founder_authorized=True,
        decided_at=NOW,
    )


def test_reconciliation_counts_publication_versions_once() -> None:
    receipt = PublicationVersionReconciliationService(clock=lambda: NOW).build(
        appraisals=[
            _appraisal(
                screening_id="a" * 64,
                title="A preprint.",
                pmid="1",
                doi="10.1/preprint",
            ),
            _appraisal(
                screening_id="b" * 64,
                title="A version of record.",
                pmid="2",
                doi="10.1/version",
            ),
            _appraisal(
                screening_id="c" * 64,
                title="An independent study.",
                pmid="3",
                doi="10.1/independent",
            ),
        ],
        version_links=[_version_link()],
    )

    assert receipt.appraisal_count == 3
    assert receipt.version_link_count == 1
    assert receipt.unique_study_count == 2
    linked = next(family for family in receipt.families if len(family.members) == 2)
    assert linked.canonical_screening_id == "b" * 64
    assert sum(member.canonical for member in linked.members) == 1


def test_reconciliation_rejects_unappraised_version() -> None:
    with pytest.raises(
        PublicationVersionReconciliationError,
        match="unappraised record",
    ):
        PublicationVersionReconciliationService().build(
            appraisals=[
                _appraisal(
                    screening_id="b" * 64,
                    title="A version of record.",
                    pmid="2",
                    doi="10.1/version",
                )
            ],
            version_links=[_version_link()],
        )


def test_reconciliation_rejects_identifier_drift() -> None:
    with pytest.raises(
        PublicationVersionReconciliationError,
        match="DOI does not match",
    ):
        PublicationVersionReconciliationService().build(
            appraisals=[
                _appraisal(
                    screening_id="a" * 64,
                    title="A preprint.",
                    pmid="1",
                    doi="10.1/changed",
                ),
                _appraisal(
                    screening_id="b" * 64,
                    title="A version of record.",
                    pmid="2",
                    doi="10.1/version",
                ),
            ],
            version_links=[_version_link()],
        )
