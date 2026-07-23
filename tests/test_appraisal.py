from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from nas_core.domain.appraisal import AppraisalDomainName, FullTextAppraisal


def _payload(*, role: str = "anchor", validation: str = "low") -> dict[str, object]:
    domains = [
        {
            "domain": domain,
            "judgment": validation if domain == "validation_and_transportability" else "low",
            "rationale": "Synthetic test rationale.",
            "evidence_locations": ["Methods, p. 4"],
        }
        for domain in AppraisalDomainName
    ]
    return {
        "appraisal_version": "1.0.0",
        "study_id": "NAS-BRCA-002",
        "screening_id": "a" * 64,
        "title": "Synthetic appraisal fixture",
        "pmid": "00000000",
        "full_text_source_url": "https://example.org/synthetic",
        "full_text_sha256": "b" * 64,
        "access_basis": "Synthetic test fixture; no copyrighted content.",
        "study_design": "prediction_model",
        "eligibility": "eligible",
        "domains": domains,
        "evidence_role": role,
        "key_strengths": ["Independent validation"],
        "key_limitations": [],
        "conflicts_and_funding": "None declared in synthetic fixture.",
        "reviewer_id": "dalron-j-robertson",
        "reviewer_name": "Dalron J. Robertson",
        "review_method": "founder_only",
        "founder_authorized": True,
        "assessed_at": datetime(2026, 7, 22, tzinfo=UTC),
    }


def test_anchor_appraisal_requires_complete_low_risk_core_domains() -> None:
    appraisal = FullTextAppraisal.model_validate(_payload())

    assert appraisal.evidence_role == "anchor"
    assert len(appraisal.domains) == 7
    assert appraisal.scientific_conclusions_drawn is False


def test_anchor_rejects_unclear_validation() -> None:
    with pytest.raises(ValidationError, match="anchor studies require low-risk"):
        FullTextAppraisal.model_validate(_payload(validation="some_concerns"))


def test_supporting_rejects_high_risk_domain() -> None:
    payload = _payload(role="supporting")
    payload["domains"][0]["judgment"] = "high"  # type: ignore[index]

    with pytest.raises(ValidationError, match="context-only"):
        FullTextAppraisal.model_validate(payload)


def test_appraisal_requires_each_domain_once() -> None:
    payload = _payload()
    payload["domains"] = payload["domains"][:-1]  # type: ignore[index]

    with pytest.raises(ValidationError, match="at least 7 items"):
        FullTextAppraisal.model_validate(payload)


def test_ai_assisted_appraisal_requires_disclosure() -> None:
    payload = _payload()
    payload["review_method"] = "founder_with_ai_assistance"

    with pytest.raises(ValidationError, match="assistant disclosure"):
        FullTextAppraisal.model_validate(payload)


def test_locked_appraisal_requires_founder_authorization() -> None:
    payload = _payload()
    payload["founder_authorized"] = False

    with pytest.raises(ValidationError, match="founder authorization"):
        FullTextAppraisal.model_validate(payload)
