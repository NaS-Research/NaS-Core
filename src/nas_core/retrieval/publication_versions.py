"""Reconcile publication versions so one study cannot be counted twice."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from nas_core.domain.appraisal import (
    EvidenceStudyFamily,
    EvidenceStudyFamilyMember,
    FullTextAppraisal,
    PublicationVersionIdentity,
    PublicationVersionLinkDecision,
    PublicationVersionReconciliationReceipt,
)
from nas_core.retrieval.full_text_retrieval import normalize_article_title


class PublicationVersionReconciliationError(RuntimeError):
    """Raised when appraisals and founder-authorized version links conflict."""


class PublicationVersionReconciliationService:
    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))

    def build(
        self,
        *,
        appraisals: Sequence[FullTextAppraisal],
        version_links: Sequence[PublicationVersionLinkDecision],
    ) -> PublicationVersionReconciliationReceipt:
        if not appraisals:
            raise PublicationVersionReconciliationError(
                "version reconciliation requires at least one appraisal"
            )
        by_id: dict[str, FullTextAppraisal] = {}
        for appraisal in appraisals:
            if appraisal.screening_id in by_id:
                raise PublicationVersionReconciliationError(
                    "version reconciliation contains duplicate appraisals"
                )
            by_id[appraisal.screening_id] = appraisal
        study_ids = {item.study_id for item in appraisals}
        if len(study_ids) != 1:
            raise PublicationVersionReconciliationError(
                "version reconciliation cannot combine study workspaces"
            )
        study_id = next(iter(study_ids))

        linked_ids: set[str] = set()
        linked_families: list[EvidenceStudyFamily] = []
        for link in version_links:
            if link.study_id != study_id:
                raise PublicationVersionReconciliationError(
                    "publication version link belongs to another study workspace"
                )
            earlier = by_id.get(link.earlier.screening_id)
            canonical = by_id.get(link.canonical.screening_id)
            if earlier is None or canonical is None:
                raise PublicationVersionReconciliationError(
                    "publication version link references an unappraised record"
                )
            if linked_ids & {earlier.screening_id, canonical.screening_id}:
                raise PublicationVersionReconciliationError(
                    "one appraisal cannot appear in multiple publication links"
                )
            self._verify_identity(earlier, link.earlier)
            self._verify_identity(canonical, link.canonical)
            linked_ids.update((earlier.screening_id, canonical.screening_id))
            linked_families.append(
                EvidenceStudyFamily(
                    canonical_screening_id=canonical.screening_id,
                    canonical_title=canonical.title,
                    members=[
                        EvidenceStudyFamilyMember(
                            screening_id=earlier.screening_id,
                            title=earlier.title,
                            publication_stage=link.earlier.publication_stage,
                            canonical=False,
                        ),
                        EvidenceStudyFamilyMember(
                            screening_id=canonical.screening_id,
                            title=canonical.title,
                            publication_stage=link.canonical.publication_stage,
                            canonical=True,
                        ),
                    ],
                )
            )

        singleton_families = [
            EvidenceStudyFamily(
                canonical_screening_id=appraisal.screening_id,
                canonical_title=appraisal.title,
                members=[
                    EvidenceStudyFamilyMember(
                        screening_id=appraisal.screening_id,
                        title=appraisal.title,
                        canonical=True,
                    )
                ],
            )
            for appraisal in appraisals
            if appraisal.screening_id not in linked_ids
        ]
        families = sorted(
            [*linked_families, *singleton_families],
            key=lambda item: item.canonical_screening_id,
        )
        return PublicationVersionReconciliationReceipt(
            receipt_version="1.0.0",
            study_id=study_id,
            generated_at=self._clock(),
            appraisal_count=len(appraisals),
            version_link_count=len(version_links),
            unique_study_count=len(families),
            families=families,
        )

    @staticmethod
    def _verify_identity(
        appraisal: FullTextAppraisal,
        identity: PublicationVersionIdentity,
    ) -> None:
        # Kept structural rather than fuzzy: a version decision must bind the exact
        # screening record and every bibliographic identifier present in appraisal.
        if normalize_article_title(appraisal.title) != normalize_article_title(
            identity.title
        ):
            raise PublicationVersionReconciliationError(
                "publication version title does not match appraisal"
            )
        if appraisal.pmid is not None and appraisal.pmid != identity.pmid:
            raise PublicationVersionReconciliationError(
                "publication version PMID does not match appraisal"
            )
        if appraisal.doi is not None and (appraisal.doi.casefold()) != (
            identity.doi or ""
        ).casefold():
            raise PublicationVersionReconciliationError(
                "publication version DOI does not match appraisal"
            )
