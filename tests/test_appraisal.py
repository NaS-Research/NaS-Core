import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.domain.appraisal import (
    APPRAISAL_BATCH_CONFIRMATION_STATEMENT,
    AppraisalDomainName,
    FullTextAppraisal,
    FullTextAppraisalBatchConfirmation,
    FullTextAppraisalProposal,
    appraisal_batch_confirmation_statement,
    load_full_text_appraisal_batch_confirmation,
    write_full_text_appraisal,
)
from nas_core.retrieval.appraisal_confirmation import (
    AppraisalConfirmationError,
    AppraisalConfirmationService,
)

ROOT = Path(__file__).parents[1]
REAL_APPRAISAL_DIR = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
    / "appraisals"
)
PROPOSAL_ROOT = REAL_APPRAISAL_DIR.parent / "citation-appraisal-proposals"
PROPOSAL_DIR = PROPOSAL_ROOT / "batch-0001"
APPRAISAL_PACKET = (
    REAL_APPRAISAL_DIR.parent / "FOUNDER_CITATION_APPRAISAL_BATCH_0001_v1.0.0.md"
)
APPRAISAL_CONFIRMATION = (
    REAL_APPRAISAL_DIR.parent
    / "FOUNDER_CITATION_APPRAISAL_BATCH_0001_CONFIRMATION_v1.0.0.yaml"
)
PENDING_REVIEW_INDEX = (
    REAL_APPRAISAL_DIR.parent
    / "FOUNDER_PENDING_CITATION_APPRAISAL_REVIEW_v1.0.0.md"
)


def _test_confirmation(
    *,
    batch_number: int,
    packet_path: Path,
    proposal_paths: list[Path],
) -> FullTextAppraisalBatchConfirmation:
    proposals = [
        FullTextAppraisalProposal.model_validate(yaml.safe_load(path.read_text()))
        for path in proposal_paths
    ]
    return FullTextAppraisalBatchConfirmation(
        confirmation_version="1.0.0",
        study_id="NAS-BRCA-002",
        batch_number=batch_number,
        packet_filename=packet_path.name,
        packet_sha256=hashlib.sha256(packet_path.read_bytes()).hexdigest(),
        proposal_count=len(proposal_paths),
        proposals=[
            {
                "filename": path.name,
                "screening_id": proposal.screening_id,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path, proposal in zip(proposal_paths, proposals, strict=True)
        ],
        confirmation_statement=appraisal_batch_confirmation_statement(batch_number),
        founder_id="dalron-j-robertson",
        founder_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        confirmed_at=datetime(2026, 7, 26, tzinfo=UTC),
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
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


def test_locked_appraisal_writer_is_exclusive(tmp_path: Path) -> None:
    appraisal = FullTextAppraisal.model_validate(_payload())
    path = tmp_path / "PMC123-v1.0.0.yaml"

    write_full_text_appraisal(path, appraisal)

    reloaded = FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))
    assert reloaded == appraisal
    with pytest.raises(FileExistsError):
        write_full_text_appraisal(path, appraisal)


def test_appraisal_proposal_is_explicitly_non_authoritative() -> None:
    payload = _payload(role="supporting", validation="some_concerns")
    payload["proposal_version"] = payload.pop("appraisal_version")
    payload["proposed_evidence_role"] = payload.pop("evidence_role")
    payload["assistant_id"] = "openai-codex"
    payload["assistant_disclosure"] = "AI-assisted draft for founder review."
    payload["proposed_at"] = payload.pop("assessed_at")
    payload["founder_decision_recorded"] = False
    payload.pop("reviewer_id")
    payload.pop("reviewer_name")
    payload.pop("review_method")
    payload.pop("founder_authorized")

    proposal = FullTextAppraisalProposal.model_validate(payload)

    assert proposal.proposed_evidence_role == "supporting"
    assert proposal.founder_decision_recorded is False
    assert proposal.scientific_conclusions_drawn is False


def test_appraisal_proposal_cannot_record_founder_decision() -> None:
    payload = _payload(role="supporting", validation="some_concerns")
    payload["proposal_version"] = payload.pop("appraisal_version")
    payload["proposed_evidence_role"] = payload.pop("evidence_role")
    payload["assistant_id"] = "openai-codex"
    payload["assistant_disclosure"] = "AI-assisted draft for founder review."
    payload["proposed_at"] = payload.pop("assessed_at")
    payload["founder_decision_recorded"] = True
    payload.pop("reviewer_id")
    payload.pop("reviewer_name")
    payload.pop("review_method")
    payload.pop("founder_authorized")

    with pytest.raises(ValidationError, match="cannot record a founder decision"):
        FullTextAppraisalProposal.model_validate(payload)


def test_first_citation_appraisal_batch_is_non_authoritative() -> None:
    paths = sorted(PROPOSAL_DIR.glob("*.yaml"))

    proposals = [
        FullTextAppraisalProposal.model_validate(yaml.safe_load(path.read_text()))
        for path in paths
    ]

    assert [path.stem for path in paths] == [
        "PMC11217366-v1.0.0",
        "PMC3487945-v1.0.0",
        "PMC6547580-v1.0.0",
    ]
    assert all(item.proposed_evidence_role == "context_only" for item in proposals)
    assert all(item.founder_decision_recorded is False for item in proposals)
    assert all(item.scientific_conclusions_drawn is False for item in proposals)


def test_second_citation_appraisal_batch_is_non_authoritative() -> None:
    paths = sorted((PROPOSAL_ROOT / "batch-0002").glob("*.yaml"))

    proposals = [
        FullTextAppraisalProposal.model_validate(yaml.safe_load(path.read_text()))
        for path in paths
    ]

    assert [path.stem for path in paths] == [
        "PMC10848444-v1.0.0",
        "PMC6219008-v1.0.0",
        "PMC8479681-v1.0.0",
        "PMC8796360-v1.0.0",
    ]
    assert sum(item.proposed_evidence_role == "supporting" for item in proposals) == 2
    assert sum(item.proposed_evidence_role == "context_only" for item in proposals) == 2
    assert all(item.founder_decision_recorded is False for item in proposals)
    assert all(item.scientific_conclusions_drawn is False for item in proposals)


def test_third_citation_appraisal_batch_is_non_authoritative() -> None:
    paths = sorted((PROPOSAL_ROOT / "batch-0003").glob("*.yaml"))

    proposals = [
        FullTextAppraisalProposal.model_validate(yaml.safe_load(path.read_text()))
        for path in paths
    ]

    assert [path.stem for path in paths] == [
        "PMC10771357-v1.0.0",
        "PMC1557722-v1.0.0",
        "PMC4546262-v1.0.0",
        "PMC4818440-v1.0.0",
        "PMC7470374-v1.0.0",
        "PMC8657125-v1.0.0",
    ]
    assert sum(item.proposed_evidence_role == "supporting" for item in proposals) == 4
    assert sum(item.proposed_evidence_role == "context_only" for item in proposals) == 2
    assert all(item.founder_decision_recorded is False for item in proposals)
    assert all(item.scientific_conclusions_drawn is False for item in proposals)


@pytest.mark.parametrize(
    ("batch_number", "expected_stem", "expected_role"),
    [
        (4, "PPR1259744-v1.0.0", "supporting"),
        (5, "PMID23907291-v1.0.0", "context_only"),
    ],
)
def test_non_pmc_citation_appraisal_batch_is_non_authoritative(
    batch_number: int,
    expected_stem: str,
    expected_role: str,
) -> None:
    paths = sorted(
        (PROPOSAL_ROOT / f"batch-{batch_number:04d}").glob("*.yaml")
    )
    proposals = [
        FullTextAppraisalProposal.model_validate(yaml.safe_load(path.read_text()))
        for path in paths
    ]

    assert [path.stem for path in paths] == [expected_stem]
    assert [item.proposed_evidence_role for item in proposals] == [expected_role]
    assert all(item.founder_decision_recorded is False for item in proposals)
    assert all(item.scientific_conclusions_drawn is False for item in proposals)


def test_appraisal_batch_confirmation_requires_exact_statement() -> None:
    payload = {
        "confirmation_version": "1.0.0",
        "study_id": "NAS-BRCA-002",
        "batch_number": 1,
        "packet_filename": "FOUNDER_CITATION_APPRAISAL_BATCH_0001_v1.0.0.md",
        "packet_sha256": "a" * 64,
        "proposal_count": 1,
        "proposals": [
            {
                "filename": "PMC11217366-v1.0.0.yaml",
                "screening_id": "b" * 64,
                "sha256": "c" * 64,
            }
        ],
        "confirmation_statement": "Looks good.",
        "founder_id": "dalron-j-robertson",
        "founder_name": "Dalron J. Robertson",
        "reviewer_role": "founder_internal_reviewer",
        "confirmed_at": datetime(2026, 7, 26, tzinfo=UTC),
        "founder_authorized": True,
        "founder_role_conflict_disclosed": True,
    }

    with pytest.raises(ValidationError, match="statement is not exact"):
        FullTextAppraisalBatchConfirmation.model_validate(payload)


def test_appraisal_batch_confirmation_statement_is_batch_specific() -> None:
    payload = {
        "confirmation_version": "1.0.0",
        "study_id": "NAS-BRCA-002",
        "batch_number": 2,
        "packet_filename": "FOUNDER_CITATION_APPRAISAL_BATCH_0002_v1.0.0.md",
        "packet_sha256": "a" * 64,
        "proposal_count": 1,
        "proposals": [
            {
                "filename": "PMC6219008-v1.0.0.yaml",
                "screening_id": "b" * 64,
                "sha256": "c" * 64,
            }
        ],
        "confirmation_statement": APPRAISAL_BATCH_CONFIRMATION_STATEMENT,
        "founder_id": "dalron-j-robertson",
        "founder_name": "Dalron J. Robertson",
        "reviewer_role": "founder_internal_reviewer",
        "confirmed_at": datetime(2026, 7, 26, tzinfo=UTC),
        "founder_authorized": True,
        "founder_role_conflict_disclosed": True,
    }

    with pytest.raises(ValidationError, match="statement is not exact"):
        FullTextAppraisalBatchConfirmation.model_validate(payload)


@pytest.mark.parametrize(
    "filename",
    [
        "PMC123-v1.0.0.yaml",
        "PMID23907291-v1.0.0.yaml",
        "PPR1259744-v1.0.0.yaml",
    ],
)
def test_appraisal_confirmation_accepts_supported_record_filename(
    filename: str,
) -> None:
    confirmation = FullTextAppraisalBatchConfirmation(
        confirmation_version="1.0.0",
        study_id="NAS-BRCA-002",
        batch_number=5,
        packet_filename="FOUNDER_CITATION_APPRAISAL_BATCH_0005_v1.0.0.md",
        packet_sha256="a" * 64,
        proposal_count=1,
        proposals=[
            {
                "filename": filename,
                "screening_id": "b" * 64,
                "sha256": "c" * 64,
            }
        ],
        confirmation_statement=appraisal_batch_confirmation_statement(5),
        founder_id="dalron-j-robertson",
        founder_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        confirmed_at=datetime(2026, 7, 26, tzinfo=UTC),
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )

    assert confirmation.proposals[0].filename == filename


def test_appraisal_batch_confirmation_rejects_cross_batch_packet() -> None:
    payload = {
        "confirmation_version": "1.0.0",
        "study_id": "NAS-BRCA-002",
        "batch_number": 2,
        "packet_filename": "FOUNDER_CITATION_APPRAISAL_BATCH_0003_v1.0.0.md",
        "packet_sha256": "a" * 64,
        "proposal_count": 1,
        "proposals": [
            {
                "filename": "PMC6219008-v1.0.0.yaml",
                "screening_id": "b" * 64,
                "sha256": "c" * 64,
            }
        ],
        "confirmation_statement": appraisal_batch_confirmation_statement(2),
        "founder_id": "dalron-j-robertson",
        "founder_name": "Dalron J. Robertson",
        "reviewer_role": "founder_internal_reviewer",
        "confirmed_at": datetime(2026, 7, 26, tzinfo=UTC),
        "founder_authorized": True,
        "founder_role_conflict_disclosed": True,
    }

    with pytest.raises(ValidationError, match="filename does not match"):
        FullTextAppraisalBatchConfirmation.model_validate(payload)


def test_appraisal_confirmation_service_rejects_packet_checksum(
    tmp_path: Path,
) -> None:
    packet = tmp_path / "FOUNDER_CITATION_APPRAISAL_BATCH_0001_v1.0.0.md"
    packet.write_text("changed", encoding="utf-8")
    confirmation = FullTextAppraisalBatchConfirmation(
        confirmation_version="1.0.0",
        study_id="NAS-BRCA-002",
        batch_number=1,
        packet_filename=packet.name,
        packet_sha256="a" * 64,
        proposal_count=1,
        proposals=[
            {
                "filename": "PMC11217366-v1.0.0.yaml",
                "screening_id": "b" * 64,
                "sha256": "c" * 64,
            }
        ],
        confirmation_statement=APPRAISAL_BATCH_CONFIRMATION_STATEMENT,
        founder_id="dalron-j-robertson",
        founder_name="Dalron J. Robertson",
        reviewer_role="founder_internal_reviewer",
        confirmed_at=datetime(2026, 7, 26, tzinfo=UTC),
        founder_authorized=True,
        founder_role_conflict_disclosed=True,
    )

    with pytest.raises(AppraisalConfirmationError, match="checksum failed"):
        AppraisalConfirmationService().authorize(
            confirmation=confirmation,
            packet_path=packet,
            proposal_paths=[],
        )


def test_real_appraisal_confirmation_authorizes_exact_proposal_set() -> None:
    confirmation = load_full_text_appraisal_batch_confirmation(APPRAISAL_CONFIRMATION)

    appraisals = AppraisalConfirmationService().authorize(
        confirmation=confirmation,
        packet_path=APPRAISAL_PACKET,
        proposal_paths=sorted(PROPOSAL_DIR.glob("*.yaml")),
    )

    assert len(appraisals) == 3
    assert all(item.founder_authorized for item in appraisals)
    assert all(item.evidence_role == "context_only" for item in appraisals)
    assert all(
        item.review_method == "founder_with_ai_assistance" for item in appraisals
    )


@pytest.mark.parametrize(
    ("batch_number", "expected_supporting", "expected_context"),
    [
        (2, 2, 2),
        (3, 4, 2),
        (4, 1, 0),
        (5, 0, 1),
        (6, 0, 2),
        (7, 0, 3),
    ],
)
def test_pending_real_batches_are_authorization_ready(
    batch_number: int,
    expected_supporting: int,
    expected_context: int,
) -> None:
    packet = (
        REAL_APPRAISAL_DIR.parent
        / f"FOUNDER_CITATION_APPRAISAL_BATCH_{batch_number:04d}_v1.0.0.md"
    )
    proposal_paths = sorted(
        (PROPOSAL_ROOT / f"batch-{batch_number:04d}").glob("*.yaml")
    )
    confirmation = _test_confirmation(
        batch_number=batch_number,
        packet_path=packet,
        proposal_paths=proposal_paths,
    )

    appraisals = AppraisalConfirmationService().authorize(
        confirmation=confirmation,
        packet_path=packet,
        proposal_paths=proposal_paths,
    )

    assert sum(item.evidence_role == "supporting" for item in appraisals) == (
        expected_supporting
    )
    assert sum(item.evidence_role == "context_only" for item in appraisals) == (
        expected_context
    )
    assert all(item.founder_authorized for item in appraisals)


def test_pending_review_index_binds_real_packet_hashes_and_counts() -> None:
    review_index = PENDING_REVIEW_INDEX.read_text(encoding="utf-8")

    for batch_number in range(2, 8):
        packet = (
            REAL_APPRAISAL_DIR.parent
            / f"FOUNDER_CITATION_APPRAISAL_BATCH_{batch_number:04d}_v1.0.0.md"
        )
        proposal_count = len(
            list(
                (
                    PROPOSAL_ROOT / f"batch-{batch_number:04d}"
                ).glob("*.yaml")
            )
        )
        packet_sha256 = hashlib.sha256(packet.read_bytes()).hexdigest()

        assert (
            f"| `{batch_number:04d}` | `{packet_sha256}` | {proposal_count} |"
            in review_index
        )
        assert (
            appraisal_batch_confirmation_statement(batch_number)
            in review_index
        )


def test_appraisal_confirmation_rejects_cross_study_proposal(tmp_path: Path) -> None:
    packet = tmp_path / "FOUNDER_CITATION_APPRAISAL_BATCH_0002_v1.0.0.md"
    packet.write_text("test packet", encoding="utf-8")
    source = PROPOSAL_ROOT / "batch-0002" / "PMC6219008-v1.0.0.yaml"
    payload = yaml.safe_load(source.read_text())
    payload["study_id"] = "NAS-OTHER-001"
    proposal = tmp_path / source.name
    proposal.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    confirmation = _test_confirmation(
        batch_number=2,
        packet_path=packet,
        proposal_paths=[proposal],
    )

    with pytest.raises(AppraisalConfirmationError, match="study identity changed"):
        AppraisalConfirmationService().authorize(
            confirmation=confirmation,
            packet_path=packet,
            proposal_paths=[proposal],
        )


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


def test_cross_condition_appraisal_records_high_transport_risk() -> None:
    path = REAL_APPRAISAL_DIR / "PMC5001207-v1.0.0.yaml"
    appraisal = FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))
    judgments = {item.domain: item.judgment for item in appraisal.domains}

    assert appraisal.pmid == "27556419"
    assert appraisal.doi == "10.1186/s12864-016-2903-z"
    assert appraisal.evidence_role == "context_only"
    assert judgments[AppraisalDomainName.CLASSIFIER_IMPLEMENTATION] == "high"
    assert judgments[AppraisalDomainName.VALIDATION_AND_TRANSPORTABILITY] == "high"
    assert appraisal.scientific_conclusions_drawn is False


def test_ki67_measurement_appraisal_is_context_only() -> None:
    path = REAL_APPRAISAL_DIR / "PMC7376512-v1.0.0.yaml"
    appraisal = FullTextAppraisal.model_validate(yaml.safe_load(path.read_text()))
    judgments = {item.domain: item.judgment for item in appraisal.domains}

    assert appraisal.pmid == "32572716"
    assert appraisal.doi == "10.1007/s10549-020-05752-w"
    assert appraisal.evidence_role == "context_only"
    assert judgments[AppraisalDomainName.ANALYSIS_AND_STATISTICS] == "high"
    assert judgments[AppraisalDomainName.VALIDATION_AND_TRANSPORTABILITY] == "high"
    assert appraisal.scientific_conclusions_drawn is False
