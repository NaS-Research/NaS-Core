"""Validate structured appraisal proposals against ephemeral full text."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from nas_core.domain.appraisal import (
    FullTextAppraisalProposal,
    FullTextInventoryRecord,
    FullTextReadOnlyReviewReceipt,
)
from nas_core.ingestion.gdc import sha256
from nas_core.retrieval.full_text_retrieval import normalize_article_title
from nas_core.retrieval.licensed_pdf import LicensedPdfImportService
from nas_core.retrieval.read_only_review import (
    APPROVED_PUBLISHER_PDF_URLS,
    INSTITUTIONAL_PDF_URLS,
    ReadOnlyReviewTransport,
    UrllibApprovedPublisherPdfReadOnlyReviewTransport,
    UrllibInstitutionalPdfReadOnlyReviewTransport,
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
