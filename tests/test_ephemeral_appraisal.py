from datetime import UTC, datetime

import pytest

from nas_core.domain.appraisal import (
    FullTextAppraisalProposal,
    FullTextInventoryRecord,
    FullTextReadOnlyReviewReceipt,
)
from nas_core.ingestion.gdc import HTTPResponse, sha256
from nas_core.retrieval.ephemeral_appraisal import (
    ApprovedPublisherHtmlAppraisalProposalService,
    ApprovedPublisherPdfAppraisalProposalService,
    EphemeralAppraisalError,
    InstitutionalPdfAppraisalProposalService,
    PmcHtmlAppraisalProposalService,
    PmcOaiAppraisalProposalService,
)
from nas_core.retrieval.read_only_review import (
    APPROVED_PUBLISHER_HTML_URLS,
    PMC_ARTICLE_URL,
    PMC_OAI_ARTICLE_URL,
    ApprovedPublisherHtmlReadOnlyReviewService,
    PmcOaiReadOnlyReviewService,
    PmcReadOnlyReviewService,
)

NOW = datetime(2026, 7, 26, tzinfo=UTC)
BODY = b"%PDF-1.7\n" + (b"synthetic " * 1200) + b"\n%%EOF"
TITLE = (
    "Assignment of tumor subtype by genomic testing and pathologic-based "
    "approximations: implications on patient's management and therapy selection."
)
DOI = "10.1007/s12094-013-1088-z"
SOURCE_URL = (
    "https://unclineberger.org/peroulab/wp-content/uploads/sites/1008/"
    "2013/10/July-16.pdf"
)
PUBLISHER_SOURCE_URL = (
    "https://www.e-crt.org/upload/pdf/crt-2018-342.pdf"
)


class FakeTransport:
    def __init__(self, body: bytes = BODY) -> None:
        self.body = body

    def get(self, url: str) -> HTTPResponse:
        assert url == SOURCE_URL
        return HTTPResponse(status_code=200, headers={}, body=self.body)


class StaticTransport:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def get(self, url: str) -> HTTPResponse:
        del url
        return HTTPResponse(status_code=200, headers={}, body=self.body)


def _record() -> FullTextInventoryRecord:
    return FullTextInventoryRecord(
        screening_id="a" * 64,
        record_key="MED:23907291",
        title=TITLE,
        pmid="23907291",
        doi=DOI,
        access_status="access_check_required",
    )


def _receipt() -> FullTextReadOnlyReviewReceipt:
    return FullTextReadOnlyReviewReceipt(
        receipt_version="1.0.0",
        review_id="b" * 64,
        study_id="NAS-BRCA-002",
        queue_id="c" * 64,
        progress_id="d" * 64,
        screening_id="a" * 64,
        pmid="23907291",
        doi=DOI,
        title=TITLE,
        source_url=SOURCE_URL,
        access_mode="read_only_ephemeral",
        access_basis="Public institutional author copy; ephemeral review only.",
        observed_rights="Publisher copyright; no reusable license verified.",
        rights_url="https://link.springer.com/article/10.1007/s12094-013-1088-z",
        content_sha256=sha256(BODY),
        content_size_bytes=len(BODY),
        accessed_at=NOW,
        verified_at=NOW,
        code_revision="abcdef1",
        checksum_verified=True,
        article_identity_verified=True,
        lawful_read_access_verified=True,
    )


def _proposal() -> FullTextAppraisalProposal:
    domains = [
        {
            "domain": domain,
            "judgment": "some_concerns",
            "rationale": (
                "The synthetic design provides relevant methodological context "
                "but does not independently validate transport."
            ),
            "evidence_locations": ["Methods — synthetic section"],
        }
        for domain in (
            "population_selection",
            "specimen_and_measurement",
            "classifier_implementation",
            "reference_comparator",
            "analysis_and_statistics",
            "validation_and_transportability",
            "reporting_and_reproducibility",
        )
    ]
    return FullTextAppraisalProposal(
        proposal_version="1.0.0",
        study_id="NAS-BRCA-002",
        screening_id="a" * 64,
        title=TITLE,
        pmid="23907291",
        doi=DOI,
        full_text_source_url=SOURCE_URL,
        full_text_sha256=sha256(BODY),
        access_basis=(
            "Ephemeral institutional review; zero article bytes retained."
        ),
        study_design="observational_concordance",
        eligibility="eligible",
        domains=domains,
        proposed_evidence_role="context_only",
        key_strengths=["Uses paired measurements in one defined cohort."],
        key_limitations=["Does not include independent external validation."],
        conflicts_and_funding="Synthetic fixture declares no competing interest.",
        assistant_id="openai-codex",
        assistant_disclosure="AI-assisted structured draft for founder review.",
        proposed_at=NOW,
    )


def _source_text() -> str:
    extracted_title = TITLE.replace("patient's", "patient’s").replace(
        "pathologic-based", "pathologic-\nbased"
    )
    return f"{extracted_title}\nDOI {DOI}\n" + (
        "The source describes a small paired cohort and several analytical methods. "
        * 100
    )


def _synthetic_pdf() -> bytes:
    return b"%PDF-1.7\n" + (b"stable source bytes " * 1200) + b"\n%%EOF"


def test_ephemeral_proposal_reconciles_without_retaining_source() -> None:
    proposal = InstitutionalPdfAppraisalProposalService(
        transport=FakeTransport(),
        pdf_parser=lambda value: {"text": _source_text()},
    ).validate(record=_record(), receipt=_receipt(), proposal=_proposal())

    assert proposal.full_text_sha256 == sha256(BODY)
    assert proposal.founder_decision_recorded is False
    assert proposal.scientific_conclusions_drawn is False


def test_ephemeral_proposal_rejects_changed_source_bytes() -> None:
    with pytest.raises(EphemeralAppraisalError, match="no longer matches"):
        InstitutionalPdfAppraisalProposalService(
            transport=FakeTransport(BODY + b"changed"),
            pdf_parser=lambda value: {"text": _source_text()},
        ).validate(record=_record(), receipt=_receipt(), proposal=_proposal())


def test_ephemeral_proposal_rejects_verbatim_source_passage() -> None:
    proposal = _proposal()
    proposal.domains[0].rationale = (
        "The source describes a small paired cohort and several analytical methods "
        "the source describes a small paired cohort."
    )

    with pytest.raises(EphemeralAppraisalError, match="verbatim"):
        InstitutionalPdfAppraisalProposalService(
            transport=FakeTransport(),
            pdf_parser=lambda value: {"text": _source_text()},
        ).validate(record=_record(), receipt=_receipt(), proposal=proposal)


def test_ephemeral_proposal_rejects_identity_mismatch() -> None:
    proposal = _proposal().model_copy(update={"full_text_sha256": "f" * 64})

    with pytest.raises(EphemeralAppraisalError, match="identity or provenance"):
        InstitutionalPdfAppraisalProposalService(
            transport=FakeTransport(),
            pdf_parser=lambda value: {"text": _source_text()},
        ).validate(record=_record(), receipt=_receipt(), proposal=proposal)


def test_publisher_pdf_proposal_reconciles_without_retaining_source() -> None:
    body = _synthetic_pdf()
    publisher_title = (
        "Discordance of the PAM50 Intrinsic Subtypes Compared with "
        "Immunohistochemistry-Based Surrogate in Breast Cancer Patients: "
        "Potential Implication of Genomic Alterations of Discordance."
    )
    record = _record().model_copy(
        update={
            "title": publisher_title,
            "pmid": "30189722",
            "pmcid": "PMC6473265",
            "doi": "10.4143/crt.2018.342",
        }
    )
    receipt = _receipt().model_copy(
        update={
            "title": publisher_title,
            "pmid": "30189722",
            "pmcid": "PMC6473265",
            "doi": "10.4143/crt.2018.342",
            "source_url": PUBLISHER_SOURCE_URL,
            "content_sha256": sha256(body),
            "content_size_bytes": len(body),
        }
    )
    proposal = _proposal().model_copy(
        update={
            "title": publisher_title,
            "pmid": "30189722",
            "doi": "10.4143/crt.2018.342",
            "full_text_source_url": PUBLISHER_SOURCE_URL,
            "full_text_sha256": sha256(body),
        }
    )
    source_text = (
        f"{publisher_title}\nDOI 10.4143/crt.2018.342\n"
        "A bounded synthetic source used for verification."
    )

    verified = ApprovedPublisherPdfAppraisalProposalService(
        transport=StaticTransport(body),
        pdf_parser=lambda value: {"text": source_text},
    ).validate(record=record, receipt=receipt, proposal=proposal)

    assert verified.full_text_sha256 == sha256(body)
    assert verified.founder_decision_recorded is False
    assert verified.scientific_conclusions_drawn is False


def _oai_body(
    *,
    response_date: str = "2026-07-26T03:00:00Z",
    source_phrase: str = "A bounded synthetic source used for verification.",
) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>{response_date}</responseDate>
  <GetRecord><record><metadata>
    <article><front><article-meta>
      <article-id pub-id-type="pmcid">PMC123</article-id>
      <article-id pub-id-type="pmid">23907291</article-id>
      <article-id pub-id-type="doi">{DOI}</article-id>
      <title-group><article-title>{TITLE}</article-title></title-group>
    </article-meta></front>
    <body><sec><title>Methods</title><p>{source_phrase * 800}</p></sec></body></article>
  </metadata></record></GetRecord>
</OAI-PMH>""".encode()


def _oai_record() -> FullTextInventoryRecord:
    return _record().model_copy(update={"pmcid": "PMC123"})


def _oai_receipt(body: bytes) -> FullTextReadOnlyReviewReceipt:
    return PmcOaiReadOnlyReviewService(
        transport=StaticTransport(body),
        clock=lambda: NOW,
    ).review(
        _oai_record(),
        study_id="NAS-BRCA-002",
        queue_id="c" * 64,
        progress_id="d" * 64,
        code_revision="abcdef1",
        access_basis=(
            "Official PMC OAI article XML reviewed ephemerally; canonical article "
            "representation hashed; zero article bytes retained."
        ),
        observed_rights="All rights reserved.",
        rights_url="https://pmc.ncbi.nlm.nih.gov/about/copyright/",
    )


def test_pmc_oai_proposal_ignores_changed_delivery_envelope() -> None:
    receipt = _oai_receipt(_oai_body())
    proposal = _proposal().model_copy(
        update={
            "full_text_source_url": PMC_OAI_ARTICLE_URL.format(
                pmc_numeric_id="123"
            ),
            "full_text_sha256": receipt.content_sha256,
        }
    )

    verified = PmcOaiAppraisalProposalService(
        transport=StaticTransport(
            _oai_body(response_date="2026-07-26T04:00:00Z")
        )
    ).validate(record=_oai_record(), receipt=receipt, proposal=proposal)

    assert verified.full_text_sha256 == receipt.content_sha256
    assert verified.founder_decision_recorded is False


def test_pmc_oai_proposal_rejects_changed_article_content() -> None:
    receipt = _oai_receipt(_oai_body())
    proposal = _proposal().model_copy(
        update={
            "full_text_source_url": receipt.source_url,
            "full_text_sha256": receipt.content_sha256,
        }
    )

    with pytest.raises(EphemeralAppraisalError, match="no longer matches"):
        PmcOaiAppraisalProposalService(
            transport=StaticTransport(
                _oai_body(source_phrase="Changed article content.")
            )
        ).validate(record=_oai_record(), receipt=receipt, proposal=proposal)


def test_pmc_html_proposal_reconciles_canonical_source_receipt() -> None:
    source_url = PMC_ARTICLE_URL.format(pmcid="PMC123")
    body = f"""<!doctype html><html><head>
<meta name="citation_title" content="{TITLE}">
<meta name="citation_doi" content="{DOI}">
<meta name="citation_pmid" content="23907291">
<meta name="citation_fulltext_html_url" content="{source_url}">
</head><body><article><h1>{TITLE}</h1>
<p>DOI {DOI}</p>
<p>{"Source-specific analytical observations. " * 800}</p>
</article></body></html>""".encode()
    record = _oai_record()
    receipt = PmcReadOnlyReviewService(
        transport=StaticTransport(body),
        clock=lambda: NOW,
    ).review(
        record,
        study_id="NAS-BRCA-002",
        queue_id="c" * 64,
        progress_id="d" * 64,
        code_revision="abcdef1",
        access_basis="Official PMC HTML reviewed ephemerally; zero article bytes retained.",
        observed_rights="PMC-hosted article; corpus reuse not assumed.",
        rights_url="https://pmc.ncbi.nlm.nih.gov/about/copyright/",
    )
    proposal = _proposal().model_copy(
        update={
            "full_text_source_url": receipt.source_url,
            "full_text_sha256": receipt.content_sha256,
        }
    )

    verified = PmcHtmlAppraisalProposalService(
        transport=StaticTransport(body)
    ).validate(record=record, receipt=receipt, proposal=proposal)

    assert verified.full_text_sha256 == receipt.content_sha256
    assert verified.founder_decision_recorded is False


def _publisher_html() -> bytes:
    title = (
        "A three-gene model to robustly identify breast cancer molecular subtypes."
    )
    return f"""<!doctype html><html><head>
<meta name="citation_title" content="{title}">
<meta name="citation_doi" content="10.1093/jnci/djr545">
<meta name="citation_pmid" content="22262870">
</head><body><article>
<h1>{title}</h1>
{"Methods and results. " * 1200}</article>
<script>dynamic = "ignored";</script></body></html>""".encode()


def test_publisher_html_proposal_reconciles_canonical_article() -> None:
    publisher_title = (
        "A three-gene model to robustly identify breast cancer molecular subtypes."
    )
    record = _record().model_copy(
        update={
            "title": publisher_title,
            "pmid": "22262870",
            "pmcid": "PMC3283537",
            "doi": "10.1093/jnci/djr545",
        }
    )
    receipt = ApprovedPublisherHtmlReadOnlyReviewService(
        transport=StaticTransport(_publisher_html()),
        clock=lambda: NOW,
    ).review(
        record,
        study_id="NAS-BRCA-002",
        queue_id="c" * 64,
        progress_id="d" * 64,
        code_revision="abcdef1",
        access_basis=(
            "Official publisher HTML reviewed ephemerally; canonical article "
            "representation hashed; zero article bytes retained."
        ),
        observed_rights="Publisher open-access article; corpus reuse not assumed.",
        rights_url="https://academic.oup.com/jnci/article/104/4/311/979947",
    )
    proposal = _proposal().model_copy(
        update={
            "title": publisher_title,
            "pmid": "22262870",
            "doi": "10.1093/jnci/djr545",
            "full_text_source_url": APPROVED_PUBLISHER_HTML_URLS[
                "10.1093/jnci/djr545"
            ],
            "full_text_sha256": receipt.content_sha256,
        }
    )

    verified = ApprovedPublisherHtmlAppraisalProposalService(
        transport=StaticTransport(_publisher_html())
    ).validate(record=record, receipt=receipt, proposal=proposal)

    assert verified.full_text_sha256 == receipt.content_sha256
    assert verified.founder_decision_recorded is False


def test_publisher_html_allowlist_binds_confirmed_oxford_article() -> None:
    assert APPROVED_PUBLISHER_HTML_URLS["10.1093/jnci/djw303"] == (
        "https://academic.oup.com/jnci/article/109/7/djw303/3064533"
    )
