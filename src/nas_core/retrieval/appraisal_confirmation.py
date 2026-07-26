"""Checksum-bound founder authorization for full-text appraisal proposals."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from nas_core.domain.appraisal import (
    AppraisalReviewMethod,
    FullTextAppraisal,
    FullTextAppraisalBatchConfirmation,
    PublicationVersionLinkDecision,
    load_full_text_appraisal_proposal,
    load_publication_version_link_proposal,
)


class AppraisalConfirmationError(RuntimeError):
    """Raised when appraisal authorization provenance does not verify."""


@dataclass(frozen=True)
class AppraisalAuthorizationBundle:
    appraisals: list[FullTextAppraisal]
    version_links: list[PublicationVersionLinkDecision]


class AppraisalConfirmationService:
    def authorize(
        self,
        *,
        confirmation: FullTextAppraisalBatchConfirmation,
        packet_path: Path,
        proposal_paths: list[Path],
        version_link_proposal_paths: list[Path] | None = None,
    ) -> list[FullTextAppraisal]:
        return self.authorize_bundle(
            confirmation=confirmation,
            packet_path=packet_path,
            proposal_paths=proposal_paths,
            version_link_proposal_paths=version_link_proposal_paths or [],
        ).appraisals

    def authorize_bundle(
        self,
        *,
        confirmation: FullTextAppraisalBatchConfirmation,
        packet_path: Path,
        proposal_paths: list[Path],
        version_link_proposal_paths: list[Path],
    ) -> AppraisalAuthorizationBundle:
        self._verify_file(
            packet_path,
            expected_filename=confirmation.packet_filename,
            expected_sha256=confirmation.packet_sha256,
        )
        references = {item.filename: item for item in confirmation.proposals}
        supplied = {path.name: path for path in proposal_paths}
        if set(supplied) != set(references):
            raise AppraisalConfirmationError(
                "supplied appraisal proposals do not match the confirmed set"
            )

        appraisals: list[FullTextAppraisal] = []
        for filename in sorted(references):
            reference = references[filename]
            path = supplied[filename]
            self._verify_file(
                path,
                expected_filename=filename,
                expected_sha256=reference.sha256,
            )
            proposal = load_full_text_appraisal_proposal(path)
            if proposal.study_id != confirmation.study_id:
                raise AppraisalConfirmationError(
                    f"study identity changed for {filename}"
                )
            if proposal.screening_id != reference.screening_id:
                raise AppraisalConfirmationError(
                    f"screening identity changed for {filename}"
                )
            payload = proposal.model_dump(mode="json")
            payload["appraisal_version"] = payload.pop("proposal_version")
            payload["evidence_role"] = payload.pop("proposed_evidence_role")
            payload["reviewer_id"] = confirmation.founder_id
            payload["reviewer_name"] = confirmation.founder_name
            payload["review_method"] = AppraisalReviewMethod.FOUNDER_WITH_AI_ASSISTANCE
            payload["founder_authorized"] = True
            payload["assessed_at"] = confirmation.confirmed_at
            for key in (
                "assistant_id",
                "proposed_at",
                "founder_decision_recorded",
            ):
                payload.pop(key)
            appraisals.append(FullTextAppraisal.model_validate(payload))

        version_references = {
            item.filename: item for item in confirmation.version_links
        }
        supplied_version_links = {
            path.name: path for path in version_link_proposal_paths
        }
        if set(supplied_version_links) != set(version_references):
            raise AppraisalConfirmationError(
                "supplied publication version links do not match the confirmed set"
            )

        appraisal_screening_ids = {item.screening_id for item in appraisals}
        version_links: list[PublicationVersionLinkDecision] = []
        for filename in sorted(version_references):
            version_reference = version_references[filename]
            path = supplied_version_links[filename]
            self._verify_file(
                path,
                expected_filename=filename,
                expected_sha256=version_reference.sha256,
            )
            version_proposal = load_publication_version_link_proposal(path)
            if version_proposal.study_id != confirmation.study_id:
                raise AppraisalConfirmationError(
                    f"version-link study identity changed for {filename}"
                )
            if (
                version_proposal.earlier.screening_id
                != version_reference.earlier_screening_id
                or version_proposal.canonical.screening_id
                != version_reference.canonical_screening_id
            ):
                raise AppraisalConfirmationError(
                    f"version-link record identity changed for {filename}"
                )
            if (
                version_proposal.canonical.screening_id
                not in appraisal_screening_ids
            ):
                raise AppraisalConfirmationError(
                    "canonical publication must be appraised in the confirmed batch"
                )
            payload = version_proposal.model_dump(mode="json")
            payload["decision_version"] = payload.pop("proposal_version")
            payload["reviewer_id"] = confirmation.founder_id
            payload["reviewer_name"] = confirmation.founder_name
            payload["review_method"] = AppraisalReviewMethod.FOUNDER_WITH_AI_ASSISTANCE
            payload["founder_authorized"] = True
            payload["decided_at"] = confirmation.confirmed_at
            for key in (
                "assistant_id",
                "proposed_at",
                "founder_decision_recorded",
            ):
                payload.pop(key)
            version_links.append(
                PublicationVersionLinkDecision.model_validate(payload)
            )
        return AppraisalAuthorizationBundle(
            appraisals=appraisals,
            version_links=version_links,
        )

    @staticmethod
    def _verify_file(
        path: Path,
        *,
        expected_filename: str,
        expected_sha256: str,
    ) -> None:
        if path.name != expected_filename:
            raise AppraisalConfirmationError(
                f"expected {expected_filename}, received {path.name}"
            )
        if not path.is_file():
            raise AppraisalConfirmationError(f"authorization source is missing: {path}")
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != expected_sha256:
            raise AppraisalConfirmationError(
                f"authorization checksum failed for {expected_filename}"
            )
