"""Checksum-bound founder authorization for full-text appraisal proposals."""

from __future__ import annotations

import hashlib
from pathlib import Path

from nas_core.domain.appraisal import (
    AppraisalReviewMethod,
    FullTextAppraisal,
    FullTextAppraisalBatchConfirmation,
    load_full_text_appraisal_proposal,
)


class AppraisalConfirmationError(RuntimeError):
    """Raised when appraisal authorization provenance does not verify."""


class AppraisalConfirmationService:
    def authorize(
        self,
        *,
        confirmation: FullTextAppraisalBatchConfirmation,
        packet_path: Path,
        proposal_paths: list[Path],
    ) -> list[FullTextAppraisal]:
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
        return appraisals

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
