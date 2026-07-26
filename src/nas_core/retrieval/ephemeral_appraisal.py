"""Validate structured appraisal proposals against ephemeral full text."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from nas_core.domain.appraisal import (
    FullTextAppraisalProposal,
    FullTextContentRepresentation,
    FullTextInventoryRecord,
    FullTextReadOnlyReviewReceipt,
)
from nas_core.ingestion.gdc import sha256
from nas_core.retrieval.full_text_retrieval import normalize_article_title
from nas_core.retrieval.licensed_pdf import LicensedPdfImportService
from nas_core.retrieval.read_only_review import (
    APPROVED_PUBLISHER_HTML_URLS,
    APPROVED_PUBLISHER_PDF_URLS,
    INSTITUTIONAL_PDF_URLS,
    PMC_ARTICLE_URL,
    PMC_OAI_ARTICLE_URL,
    ApprovedPublisherHtmlReadOnlyReviewService,
    PmcOaiReadOnlyReviewService,
    PmcReadOnlyReviewService,
    ReadOnlyReviewTransport,
    UrllibApprovedPublisherHtmlReadOnlyReviewTransport,
    UrllibApprovedPublisherPdfReadOnlyReviewTransport,
    UrllibInstitutionalPdfReadOnlyReviewTransport,
    UrllibPmcOaiReadOnlyReviewTransport,
    UrllibReadOnlyReviewTransport,
    _CanonicalPublisherHtmlParser,
    canonicalize_pmc_oai_article,
)

MAX_TOTAL_NARRATIVE_WORDS = 2_000
MAX_RATIONALE_WORDS = 250
MAX_LIST_ITEM_WORDS = 80
MAX_EVIDENCE_LOCATION_WORDS = 20
MAX_CONFLICT_WORDS = 250
VERBATIM_SEQUENCE_WORDS = 12
WORD_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


class EphemeralAppraisalError(RuntimeError):
    """Raised when a proposal is not safely bound to ephemeral source content."""


class InstitutionalPdfAppraisalProposalService:
    """Verify and release a structured proposal while retaining no source bytes."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
        pdf_parser: Callable[[bytes], dict[str, str]] | None = None,
    ) -> None:
        self._transport = (
            transport or UrllibInstitutionalPdfReadOnlyReviewTransport()
        )
        self._pdf_parser = pdf_parser or LicensedPdfImportService._parse_pdf  # noqa: SLF001

    def validate(
        self,
        *,
        record: FullTextInventoryRecord,
        receipt: FullTextReadOnlyReviewReceipt,
        proposal: FullTextAppraisalProposal,
    ) -> FullTextAppraisalProposal:
        source_url = INSTITUTIONAL_PDF_URLS.get((record.doi or "").casefold())
        if source_url is None or receipt.source_url != source_url:
            raise EphemeralAppraisalError(
                "receipt is not bound to an approved institutional PDF"
            )
        response = self._transport.get(source_url)
        if response.status_code != 200:
            raise EphemeralAppraisalError("institutional PDF is unavailable")
        if (
            len(response.body) != receipt.content_size_bytes
            or sha256(response.body) != receipt.content_sha256
        ):
            raise EphemeralAppraisalError(
                "ephemeral PDF no longer matches the verified review receipt"
            )
        try:
            source_text = self._pdf_parser(response.body).get("text", "")
        except RuntimeError as error:
            raise EphemeralAppraisalError(
                "institutional PDF failed in-memory parsing"
            ) from error
        self._verify_record_and_receipt(record, receipt, source_text)
        self._verify_proposal_identity(proposal, receipt)
        self._verify_narrative_limits(proposal)
        self._reject_verbatim_passages(proposal, source_text)
        return proposal

    @staticmethod
    def _verify_record_and_receipt(
        record: FullTextInventoryRecord,
        receipt: FullTextReadOnlyReviewReceipt,
        source_text: str,
    ) -> None:
        normalized_source = re.sub(r"[^a-z0-9]+", "", source_text.casefold())
        normalized_record_title = re.sub(
            r"[^a-z0-9]+", "", record.title.casefold()
        )
        if (
            receipt.screening_id != record.screening_id
            or receipt.study_id == ""
            or receipt.pmid != record.pmid
            or (receipt.doi or "").casefold() != (record.doi or "").casefold()
            or normalize_article_title(receipt.title)
            != normalize_article_title(record.title)
            or normalized_record_title not in normalized_source
            or (record.doi or "").casefold() not in source_text.casefold()
        ):
            raise EphemeralAppraisalError(
                "inventory, receipt, and ephemeral PDF identity do not reconcile"
            )

    @staticmethod
    def _verify_proposal_identity(
        proposal: FullTextAppraisalProposal,
        receipt: FullTextReadOnlyReviewReceipt,
    ) -> None:
        if (
            proposal.study_id != receipt.study_id
            or proposal.screening_id != receipt.screening_id
            or proposal.pmid != receipt.pmid
            or (proposal.doi or "").casefold() != (receipt.doi or "").casefold()
            or normalize_article_title(proposal.title)
            != normalize_article_title(receipt.title)
            or proposal.full_text_source_url != receipt.source_url
            or proposal.full_text_sha256 != receipt.content_sha256
            or proposal.proposed_at < receipt.accessed_at
        ):
            raise EphemeralAppraisalError(
                "proposal identity or provenance does not match the review receipt"
            )
        normalized_basis = proposal.access_basis.casefold()
        if "ephemeral" not in normalized_basis or not any(
            phrase in normalized_basis
            for phrase in ("zero article bytes", "no article bytes", "not retained")
        ):
            raise EphemeralAppraisalError(
                "proposal access basis must disclose ephemeral zero-storage review"
            )

    @classmethod
    def _verify_narrative_limits(
        cls,
        proposal: FullTextAppraisalProposal,
    ) -> None:
        narratives: list[tuple[str, int]] = []
        for domain in proposal.domains:
            narratives.append((domain.rationale, MAX_RATIONALE_WORDS))
            narratives.extend(
                (location, MAX_EVIDENCE_LOCATION_WORDS)
                for location in domain.evidence_locations
            )
        narratives.extend(
            (item, MAX_LIST_ITEM_WORDS)
            for item in (*proposal.key_strengths, *proposal.key_limitations)
        )
        narratives.append((proposal.conflicts_and_funding, MAX_CONFLICT_WORDS))
        if proposal.full_text_exclusion_reason is not None:
            narratives.append(
                (proposal.full_text_exclusion_reason, MAX_RATIONALE_WORDS)
            )
        word_counts = [len(cls._words(text)) for text, _ in narratives]
        if any(
            count > limit
            for count, (_, limit) in zip(word_counts, narratives, strict=True)
        ):
            raise EphemeralAppraisalError(
                "proposal narrative exceeds bounded derivative-summary limits"
            )
        if sum(word_counts) > MAX_TOTAL_NARRATIVE_WORDS:
            raise EphemeralAppraisalError(
                "proposal exceeds the total derivative-summary word limit"
            )

    @classmethod
    def _reject_verbatim_passages(
        cls,
        proposal: FullTextAppraisalProposal,
        source_text: str,
    ) -> None:
        source_words = cls._words(source_text)
        source_sequences = cls._sequences(source_words, VERBATIM_SEQUENCE_WORDS)
        for text in cls._scientific_narratives(proposal):
            words = cls._words(text)
            if cls._sequences(words, VERBATIM_SEQUENCE_WORDS) & source_sequences:
                raise EphemeralAppraisalError(
                    "proposal contains an unapproved verbatim source passage"
                )

    @staticmethod
    def _scientific_narratives(
        proposal: FullTextAppraisalProposal,
    ) -> Sequence[str]:
        values = [domain.rationale for domain in proposal.domains]
        values.extend(proposal.key_strengths)
        values.extend(proposal.key_limitations)
        values.append(proposal.conflicts_and_funding)
        if proposal.full_text_exclusion_reason is not None:
            values.append(proposal.full_text_exclusion_reason)
        return values

    @staticmethod
    def _words(value: str) -> list[str]:
        return WORD_PATTERN.findall(value.casefold())

    @staticmethod
    def _sequences(words: list[str], size: int) -> set[tuple[str, ...]]:
        if len(words) < size:
            return set()
        return {
            tuple(words[index : index + size])
            for index in range(len(words) - size + 1)
        }


class ApprovedPublisherPdfAppraisalProposalService:
    """Verify a bounded proposal against an approved publisher PDF."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
        pdf_parser: Callable[[bytes], dict[str, str]] | None = None,
    ) -> None:
        self._transport = (
            transport or UrllibApprovedPublisherPdfReadOnlyReviewTransport()
        )
        self._pdf_parser = pdf_parser or LicensedPdfImportService._parse_pdf  # noqa: SLF001

    def validate(
        self,
        *,
        record: FullTextInventoryRecord,
        receipt: FullTextReadOnlyReviewReceipt,
        proposal: FullTextAppraisalProposal,
    ) -> FullTextAppraisalProposal:
        source_url = APPROVED_PUBLISHER_PDF_URLS.get(
            (record.doi or "").casefold()
        )
        if source_url is None or receipt.source_url != source_url:
            raise EphemeralAppraisalError(
                "receipt is not bound to an approved publisher PDF"
            )
        response = self._transport.get(source_url)
        if response.status_code != 200:
            raise EphemeralAppraisalError("publisher PDF is unavailable")
        if (
            len(response.body) != receipt.content_size_bytes
            or sha256(response.body) != receipt.content_sha256
        ):
            raise EphemeralAppraisalError(
                "ephemeral publisher PDF no longer matches the review receipt"
            )
        try:
            source_text = self._pdf_parser(response.body).get("text", "")
        except RuntimeError as error:
            raise EphemeralAppraisalError(
                "publisher PDF failed in-memory parsing"
            ) from error
        InstitutionalPdfAppraisalProposalService._verify_record_and_receipt(  # noqa: SLF001
            record, receipt, source_text
        )
        InstitutionalPdfAppraisalProposalService._verify_proposal_identity(  # noqa: SLF001
            proposal, receipt
        )
        InstitutionalPdfAppraisalProposalService._verify_narrative_limits(  # noqa: SLF001
            proposal
        )
        InstitutionalPdfAppraisalProposalService._reject_verbatim_passages(  # noqa: SLF001
            proposal, source_text
        )
        return proposal


class PmcOaiAppraisalProposalService:
    """Verify a bounded proposal against stable canonical PMC article XML."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
    ) -> None:
        self._transport = transport or UrllibPmcOaiReadOnlyReviewTransport()

    def validate(
        self,
        *,
        record: FullTextInventoryRecord,
        receipt: FullTextReadOnlyReviewReceipt,
        proposal: FullTextAppraisalProposal,
    ) -> FullTextAppraisalProposal:
        if record.pmcid is None:
            raise EphemeralAppraisalError("PMC OAI proposal requires a PMCID")
        source_url = PMC_OAI_ARTICLE_URL.format(
            pmc_numeric_id=record.pmcid.removeprefix("PMC")
        )
        if receipt.source_url != source_url:
            raise EphemeralAppraisalError(
                "receipt is not bound to the exact PMC OAI record"
            )
        if (
            receipt.content_representation
            is not FullTextContentRepresentation.CANONICAL_PMC_OAI_ARTICLE_XML_V1
        ):
            raise EphemeralAppraisalError(
                "receipt does not declare canonical PMC OAI article XML"
            )
        response = self._transport.get(source_url)
        if (
            response.status_code != 200
            or not 10_000 <= len(response.body) <= 20_000_000
        ):
            raise EphemeralAppraisalError("PMC OAI article is unavailable")
        try:
            canonical_bytes, source_text, identity = canonicalize_pmc_oai_article(
                response.body
            )
        except RuntimeError as error:
            raise EphemeralAppraisalError(
                "PMC OAI article failed canonicalization"
            ) from error
        if (
            len(canonical_bytes) != receipt.content_size_bytes
            or sha256(canonical_bytes) != receipt.content_sha256
        ):
            raise EphemeralAppraisalError(
                "canonical PMC OAI article no longer matches the review receipt"
            )
        try:
            PmcOaiReadOnlyReviewService._verify_identity(  # noqa: SLF001
                record, identity
            )
        except RuntimeError as error:
            raise EphemeralAppraisalError(
                "inventory and canonical PMC OAI article identity do not reconcile"
            ) from error
        if receipt.pmcid != record.pmcid:
            raise EphemeralAppraisalError(
                "receipt PMCID does not match the inventory record"
            )
        InstitutionalPdfAppraisalProposalService._verify_proposal_identity(  # noqa: SLF001
            proposal, receipt
        )
        InstitutionalPdfAppraisalProposalService._verify_narrative_limits(  # noqa: SLF001
            proposal
        )
        InstitutionalPdfAppraisalProposalService._reject_verbatim_passages(  # noqa: SLF001
            proposal, source_text
        )
        return proposal


class PmcHtmlAppraisalProposalService:
    """Verify a bounded proposal against an exact ephemeral PMC HTML page."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
    ) -> None:
        self._transport = transport or UrllibReadOnlyReviewTransport()

    def validate(
        self,
        *,
        record: FullTextInventoryRecord,
        receipt: FullTextReadOnlyReviewReceipt,
        proposal: FullTextAppraisalProposal,
    ) -> FullTextAppraisalProposal:
        if record.pmcid is None:
            raise EphemeralAppraisalError("PMC HTML proposal requires a PMCID")
        source_url = PMC_ARTICLE_URL.format(pmcid=record.pmcid)
        if receipt.source_url != source_url:
            raise EphemeralAppraisalError(
                "receipt is not bound to the exact PMC HTML article"
            )
        if (
            receipt.content_representation
            is not FullTextContentRepresentation.RAW_SOURCE_BYTES
        ):
            raise EphemeralAppraisalError(
                "receipt does not declare raw PMC HTML source bytes"
            )
        response = self._transport.get(source_url)
        if (
            response.status_code != 200
            or not 10_000 <= len(response.body) <= 20_000_000
        ):
            raise EphemeralAppraisalError("PMC HTML article is unavailable")
        if (
            len(response.body) != receipt.content_size_bytes
            or sha256(response.body) != receipt.content_sha256
        ):
            raise EphemeralAppraisalError(
                "PMC HTML article no longer matches the review receipt"
            )
        parser = _CanonicalPublisherHtmlParser()
        try:
            parser.feed(response.body.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise EphemeralAppraisalError(
                "PMC HTML article failed in-memory parsing"
            ) from error
        _, source_text = parser.canonical_representation()
        try:
            PmcReadOnlyReviewService._verify_identity(  # noqa: SLF001
                record, parser.metadata, source_url
            )
        except RuntimeError as error:
            raise EphemeralAppraisalError(
                "inventory and PMC HTML article identity do not reconcile"
            ) from error
        if receipt.pmcid != record.pmcid:
            raise EphemeralAppraisalError(
                "receipt PMCID does not match the inventory record"
            )
        InstitutionalPdfAppraisalProposalService._verify_proposal_identity(  # noqa: SLF001
            proposal, receipt
        )
        InstitutionalPdfAppraisalProposalService._verify_narrative_limits(  # noqa: SLF001
            proposal
        )
        InstitutionalPdfAppraisalProposalService._reject_verbatim_passages(  # noqa: SLF001
            proposal, source_text
        )
        return proposal


class ApprovedPublisherHtmlAppraisalProposalService:
    """Verify a bounded proposal against canonical allowlisted publisher HTML."""

    def __init__(
        self,
        *,
        transport: ReadOnlyReviewTransport | None = None,
    ) -> None:
        self._transport = (
            transport or UrllibApprovedPublisherHtmlReadOnlyReviewTransport()
        )

    def validate(
        self,
        *,
        record: FullTextInventoryRecord,
        receipt: FullTextReadOnlyReviewReceipt,
        proposal: FullTextAppraisalProposal,
    ) -> FullTextAppraisalProposal:
        source_url = APPROVED_PUBLISHER_HTML_URLS.get(
            (record.doi or "").casefold()
        )
        if source_url is None or receipt.source_url != source_url:
            raise EphemeralAppraisalError(
                "receipt is not bound to an approved publisher HTML page"
            )
        if (
            receipt.content_representation
            is not FullTextContentRepresentation.CANONICAL_PUBLISHER_HTML_V1
        ):
            raise EphemeralAppraisalError(
                "receipt does not declare canonical publisher HTML"
            )
        response = self._transport.get(source_url)
        if (
            response.status_code != 200
            or not 10_000 <= len(response.body) <= 20_000_000
        ):
            raise EphemeralAppraisalError("publisher HTML is unavailable")
        parser = _CanonicalPublisherHtmlParser()
        try:
            parser.feed(response.body.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise EphemeralAppraisalError(
                "publisher HTML failed in-memory parsing"
            ) from error
        canonical_bytes, source_text = parser.canonical_representation()
        if (
            len(canonical_bytes) != receipt.content_size_bytes
            or sha256(canonical_bytes) != receipt.content_sha256
        ):
            raise EphemeralAppraisalError(
                "canonical publisher HTML no longer matches the review receipt"
            )
        try:
            ApprovedPublisherHtmlReadOnlyReviewService._verify_identity(  # noqa: SLF001
                record, parser.metadata, source_text
            )
        except RuntimeError as error:
            raise EphemeralAppraisalError(
                "inventory and publisher HTML identity do not reconcile"
            ) from error
        InstitutionalPdfAppraisalProposalService._verify_proposal_identity(  # noqa: SLF001
            proposal, receipt
        )
        InstitutionalPdfAppraisalProposalService._verify_narrative_limits(  # noqa: SLF001
            proposal
        )
        InstitutionalPdfAppraisalProposalService._reject_verbatim_passages(  # noqa: SLF001
            proposal, source_text
        )
        return proposal
