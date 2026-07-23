from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.domain.appraisal import AppraisalDomainName, FullTextAppraisal

ROOT = Path(__file__).parents[1]
REAL_APPRAISAL_DIR = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
    / "appraisals"
)


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


def test_second_real_appraisal_is_context_only_and_non_conclusive() -> None:
    path = REAL_APPRAISAL_DIR / "PMC3275466-v1.0.0.yaml"
    appraisal = FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))
    judgments = {item.domain: item.judgment for item in appraisal.domains}

    assert appraisal.pmid == "22196354"
    assert appraisal.doi == "10.1186/2043-9113-1-37"
    assert appraisal.evidence_role == "context_only"
    assert judgments[AppraisalDomainName.ANALYSIS_AND_STATISTICS] == "high"
    assert judgments[AppraisalDomainName.VALIDATION_AND_TRANSPORTABILITY] == "high"
    assert appraisal.scientific_conclusions_drawn is False


def test_cross_platform_real_appraisal_records_classifier_risk() -> None:
    path = REAL_APPRAISAL_DIR / "PMC1468408-v1.0.0.yaml"
    appraisal = FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))
    judgments = {item.domain: item.judgment for item in appraisal.domains}

    assert appraisal.pmid == "16643655"
    assert appraisal.doi == "10.1186/1471-2164-7-96"
    assert appraisal.evidence_role == "context_only"
    assert judgments[AppraisalDomainName.CLASSIFIER_IMPLEMENTATION] == "high"
    assert judgments[AppraisalDomainName.ANALYSIS_AND_STATISTICS] == "high"
    assert appraisal.scientific_conclusions_drawn is False


def test_large_multicohort_appraisal_is_supporting_and_non_conclusive() -> None:
    path = REAL_APPRAISAL_DIR / "PMC4166472-v1.0.0.yaml"
    appraisal = FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))
    judgments = {item.domain: item.judgment for item in appraisal.domains}

    assert appraisal.pmid == "25164602"
    assert appraisal.doi == "10.1186/s13059-014-0431-1"
    assert appraisal.evidence_role == "supporting"
    assert all(judgment != "high" for judgment in judgments.values())
    assert judgments[AppraisalDomainName.REPORTING_AND_REPRODUCIBILITY] == "low"
    assert appraisal.scientific_conclusions_drawn is False


def test_rnaseq_pam50_appraisal_is_supporting_and_non_conclusive() -> None:
    path = REAL_APPRAISAL_DIR / "PMC7442834-v1.0.0.yaml"
    appraisal = FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))
    judgments = {item.domain: item.judgment for item in appraisal.domains}

    assert appraisal.pmid == "32826944"
    assert appraisal.doi == "10.1038/s41598-020-70832-2"
    assert appraisal.evidence_role == "supporting"
    assert all(judgment != "high" for judgment in judgments.values())
    assert judgments[AppraisalDomainName.REPORTING_AND_REPRODUCIBILITY] == "low"
    assert appraisal.scientific_conclusions_drawn is False


def test_three_gene_comparison_appraisal_is_context_only() -> None:
    path = REAL_APPRAISAL_DIR / "PMC3413822-v1.0.0.yaml"
    appraisal = FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))

    assert appraisal.pmid == "22752290"
    assert appraisal.doi == "10.1007/s10549-012-2143-0"
    assert appraisal.evidence_role == "context_only"
    assert appraisal.scientific_conclusions_drawn is False
