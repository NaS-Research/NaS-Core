"""Derive citation-pass closure from verified screening and appraisal receipts."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from nas_core.domain.appraisal import (
    AppraisalCompletionStatus,
    EvidenceRole,
    FullTextAppraisal,
    FullTextAppraisalProgress,
    FullTextAppraisalProgressRecord,
    FullTextInventory,
    FullTextInventoryRecord,
    load_full_text_appraisal,
    load_full_text_appraisal_progress,
    load_full_text_inventory,
)
from nas_core.domain.citation_chain import (
    CitationChainReceipt,
    CitationScreeningPreparationReceipt,
    load_citation_chain_receipt,
    load_citation_screening_preparation_receipt,
)
from nas_core.domain.citation_confirmation import (
    CitationDecisionLedgerReceipt,
    load_citation_decision_ledger_receipt,
)
from nas_core.domain.citation_reconciliation import (
    CitationInclusionDisposition,
    CitationInclusionReconciliationReceipt,
    CitationInclusionReconciliationRecord,
    load_citation_inclusion_reconciliation_receipt,
)
from nas_core.domain.citation_saturation import CitationPassClosureReceipt
from nas_core.domain.evidence_amendment import (
    CitationAppraisalQueueRecord,
    CitationPassAppraisalQueueReceipt,
    EvidenceCapAmendmentActivationReceipt,
    load_citation_access_queue_receipt,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

_RECONCILIATION = TypeAdapter(list[CitationInclusionReconciliationRecord])
_QUEUE = TypeAdapter(list[CitationAppraisalQueueRecord])


class CitationPassClosureError(RuntimeError):
    """Raised when a citation pass cannot prove complete saturation accounting."""


class CitationPassClosureService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def close(
        self,
        citation: CitationChainReceipt,
        preparation: CitationScreeningPreparationReceipt,
        decision: CitationDecisionLedgerReceipt,
        reconciliation: CitationInclusionReconciliationReceipt,
        queue_receipt: (
            EvidenceCapAmendmentActivationReceipt
            | CitationPassAppraisalQueueReceipt
        ),
        *,
        citation_receipt_path: Path,
        preparation_receipt_path: Path,
        decision_receipt_path: Path,
        reconciliation_receipt_path: Path,
        queue_receipt_path: Path,
        code_revision: str,
        access_inventory: FullTextInventory | None = None,
        access_inventory_path: Path | None = None,
        appraisal_progress: FullTextAppraisalProgress | None = None,
        appraisal_progress_path: Path | None = None,
        prior_appraisal_paths: list[Path] | None = None,
        closed_at: datetime | None = None,
    ) -> CitationPassClosureReceipt:
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CitationPassClosureError(
                "code revision must be a 7-to-40 character Git SHA"
            )
        self._verify_receipt_files(
            citation,
            preparation,
            decision,
            reconciliation,
            queue_receipt,
            citation_receipt_path=citation_receipt_path,
            preparation_receipt_path=preparation_receipt_path,
            decision_receipt_path=decision_receipt_path,
            reconciliation_receipt_path=reconciliation_receipt_path,
            queue_receipt_path=queue_receipt_path,
        )
        self._validate_identities(
            citation,
            preparation,
            decision,
            reconciliation,
            queue_receipt,
        )
        self._verify_object(citation.raw_responses_object)
        self._verify_object(citation.candidates_object)
        self._verify_object(preparation.inventory_object)
        self._verify_object(preparation.screening_candidates_object)
        self._verify_object(decision.ledger_object)
        reconciliation_rows = self._load_reconciliation(reconciliation)
        queue = self._load_queue(queue_receipt)
        if (
            len(reconciliation_rows) != decision.included_count
            or len(queue) != decision.included_count
            or reconciliation.active_inventory_match_count
        ):
            raise CitationPassClosureError(
                "citation-pass inclusion routing is incomplete or reuses active inventory"
            )
        queue_by_key = {record.record_key: record for record in queue}
        if len(queue_by_key) != len(queue) or set(queue_by_key) != {
            record.record_key for record in reconciliation_rows
        }:
            raise CitationPassClosureError(
                "citation-pass queue does not cover reconciled inclusions"
            )

        prior_paths = sorted(prior_appraisal_paths or [])
        prior_appraisals = [load_full_text_appraisal(path) for path in prior_paths]
        prior_by_id = self._unique_appraisals(prior_appraisals)
        prior_rows = [
            record
            for record in reconciliation_rows
            if record.disposition is CitationInclusionDisposition.PRIOR_APPRAISAL
        ]
        required_prior_ids = {
            record.matched_screening_id for record in prior_rows
        }
        if None in required_prior_ids or set(prior_by_id) != required_prior_ids:
            raise CitationPassClosureError(
                "citation-pass prior appraisals do not match reconciliation"
            )

        net_new_rows = [
            record
            for record in reconciliation_rows
            if record.disposition is CitationInclusionDisposition.NET_NEW
        ]
        progress_by_id: dict[str, FullTextAppraisalProgressRecord] = {}
        inventory_by_key: dict[str, FullTextInventoryRecord] = {}
        if net_new_rows:
            if (
                access_inventory is None
                or access_inventory_path is None
                or appraisal_progress is None
                or appraisal_progress_path is None
            ):
                raise CitationPassClosureError(
                    "net-new inclusions require access inventory and appraisal progress"
                )
            if load_full_text_inventory(access_inventory_path) != access_inventory:
                raise CitationPassClosureError(
                    "access inventory bytes do not match the loaded contract"
                )
            if (
                load_full_text_appraisal_progress(appraisal_progress_path)
                != appraisal_progress
            ):
                raise CitationPassClosureError(
                    "appraisal progress bytes do not match the loaded contract"
                )
            queue_id = self._queue_id(queue_receipt)
            if (
                access_inventory.study_id != citation.study_id
                or access_inventory.queue_id != queue_id
                or access_inventory.progress_id != reconciliation.reconciliation_id
                or appraisal_progress.study_id != citation.study_id
                or appraisal_progress.queue_id != access_inventory.queue_id
                or appraisal_progress.progress_id != access_inventory.progress_id
                or len(access_inventory.records) != len(net_new_rows)
                or len(appraisal_progress.records) != len(net_new_rows)
            ):
                raise CitationPassClosureError(
                    "citation-pass access and appraisal identities do not reconcile"
                )
            inventory_by_key = {
                record.record_key: record for record in access_inventory.records
            }
            progress_by_id = {
                record.screening_id: record for record in appraisal_progress.records
            }
            if (
                len(inventory_by_key) != len(net_new_rows)
                or set(inventory_by_key)
                != {record.record_key for record in net_new_rows}
                or set(progress_by_id)
                != {
                    record.screening_id for record in access_inventory.records
                }
            ):
                raise CitationPassClosureError(
                    "citation-pass net-new appraisal coverage is incomplete"
                )
            incomplete = [
                record
                for record in appraisal_progress.records
                if record.status
                not in {
                    AppraisalCompletionStatus.COMPLETED,
                    AppraisalCompletionStatus.ACCESS_RESTRICTED,
                    AppraisalCompletionStatus.DUPLICATE_RESOLVED,
                }
            ]
            if incomplete:
                raise CitationPassClosureError(
                    "citation-pass appraisal progress contains unresolved records"
                )
        elif any(
            value is not None
            for value in (
                access_inventory,
                access_inventory_path,
                appraisal_progress,
                appraisal_progress_path,
            )
        ):
            raise CitationPassClosureError(
                "zero-net-new citation pass cannot bind access artifacts"
            )

        eligible_ids = self._eligible_ids(
            prior_rows,
            prior_by_id,
            net_new_rows,
            inventory_by_key,
            progress_by_id,
        )
        timestamp = closed_at or datetime.now(UTC)
        receipt_hashes = {
            "citation_receipt_sha256": sha256(citation_receipt_path.read_bytes()),
            "screening_preparation_receipt_sha256": sha256(
                preparation_receipt_path.read_bytes()
            ),
            "decision_receipt_sha256": sha256(decision_receipt_path.read_bytes()),
            "reconciliation_receipt_sha256": sha256(
                reconciliation_receipt_path.read_bytes()
            ),
            "queue_receipt_sha256": sha256(queue_receipt_path.read_bytes()),
        }
        identity = {
            "closed_at": timestamp.isoformat(),
            "code_revision": code_revision,
            "pass_number": citation.pass_number,
            "study_id": citation.study_id,
            **receipt_hashes,
        }
        progress = appraisal_progress
        return CitationPassClosureReceipt(
            closure_id=sha256(canonical_json(identity)),
            study_id=citation.study_id,
            pass_number=citation.pass_number,
            code_revision=code_revision,
            closed_at=timestamp,
            citation_execution_id=citation.execution_id,
            screening_preparation_id=preparation.preparation_id,
            decision_id=decision.decision_id,
            reconciliation_id=reconciliation.reconciliation_id,
            queue_id=self._queue_id(queue_receipt),
            **receipt_hashes,
            access_inventory_sha256=(
                sha256(access_inventory_path.read_bytes())
                if access_inventory_path is not None
                else None
            ),
            appraisal_progress_sha256=(
                sha256(appraisal_progress_path.read_bytes())
                if appraisal_progress_path is not None
                else None
            ),
            prior_appraisal_sha256s=sorted(
                sha256(path.read_bytes()) for path in prior_paths
            ),
            seed_evidence_ids=citation.seed_evidence_ids,
            backward_candidate_count=citation.backward_candidate_count,
            forward_candidate_count=citation.forward_candidate_count,
            unique_candidate_count=citation.unique_candidate_count,
            already_screened_count=preparation.already_screened_count,
            duplicate_candidate_count=preparation.duplicate_candidate_count,
            founder_screened_candidate_count=preparation.requires_screening_count,
            included_count=decision.included_count,
            excluded_count=decision.excluded_count,
            prior_appraisal_reuse_count=len(prior_rows),
            prior_appraisal_excluded_count=sum(
                appraisal.evidence_role is EvidenceRole.EXCLUDED
                for appraisal in prior_by_id.values()
            ),
            net_new_count=len(net_new_rows),
            appraisals_completed_count=(
                progress.appraisals_completed if progress is not None else 0
            ),
            access_restricted_count=(
                progress.access_restricted_count if progress is not None else 0
            ),
            duplicate_resolved_count=(
                progress.duplicate_resolved_count if progress is not None else 0
            ),
            appraisal_excluded_count=(
                progress.excluded_count if progress is not None else 0
            ),
            new_eligible_evidence_ids=eligible_ids,
            input_receipt_checksums_verified=True,
            retrieval_complete=True,
            deduplication_complete=True,
            founder_screening_complete=True,
            appraisal_accounting_complete=True,
            founder_authorized=True,
            ai_decisions_recorded=0,
            molecular_data_access_authorized=False,
            outcome_data_access_authorized=False,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def _queue_id(
        receipt: (
            EvidenceCapAmendmentActivationReceipt
            | CitationPassAppraisalQueueReceipt
        ),
    ) -> str:
        return (
            receipt.activation_id
            if isinstance(receipt, EvidenceCapAmendmentActivationReceipt)
            else receipt.queue_id
        )

    def _load_reconciliation(
        self,
        receipt: CitationInclusionReconciliationReceipt,
    ) -> list[CitationInclusionReconciliationRecord]:
        body = self._verify_object(receipt.reconciliation_object)
        try:
            return _RECONCILIATION.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationPassClosureError(
                "citation-pass reconciliation object is invalid"
            ) from error

    def _load_queue(
        self,
        receipt: (
            EvidenceCapAmendmentActivationReceipt
            | CitationPassAppraisalQueueReceipt
        ),
    ) -> list[CitationAppraisalQueueRecord]:
        body = self._verify_object(receipt.queue_object)
        try:
            return _QUEUE.validate_python(json.loads(body))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise CitationPassClosureError(
                "citation-pass appraisal queue is invalid"
            ) from error

    def _verify_object(self, stored: StoredObject) -> bytes:
        body = self._store.get_bytes(stored.object_key)
        if len(body) != stored.size_bytes or sha256(body) != stored.sha256:
            raise CitationPassClosureError(
                "citation-pass stored object does not match its receipt"
            )
        return body

    @staticmethod
    def _unique_appraisals(
        appraisals: list[FullTextAppraisal],
    ) -> dict[str, FullTextAppraisal]:
        by_id = {appraisal.screening_id: appraisal for appraisal in appraisals}
        if len(by_id) != len(appraisals):
            raise CitationPassClosureError(
                "citation-pass prior appraisals contain duplicate screening IDs"
            )
        return by_id

    @classmethod
    def _eligible_ids(
        cls,
        prior_rows: list[CitationInclusionReconciliationRecord],
        prior_by_id: dict[str, FullTextAppraisal],
        net_new_rows: list[CitationInclusionReconciliationRecord],
        inventory_by_key: dict[str, FullTextInventoryRecord],
        progress_by_id: dict[str, FullTextAppraisalProgressRecord],
    ) -> list[str]:
        eligible: list[str] = []
        for row in prior_rows:
            screening_id = row.matched_screening_id
            assert screening_id is not None
            if prior_by_id[screening_id].evidence_role is not EvidenceRole.EXCLUDED:
                eligible.append(cls._evidence_id(row))
        for row in net_new_rows:
            inventory = inventory_by_key[row.record_key]
            screening_id = inventory.screening_id
            progress = progress_by_id[screening_id]
            status = progress.status
            role = progress.evidence_role
            if status is AppraisalCompletionStatus.ACCESS_RESTRICTED or (
                status is AppraisalCompletionStatus.COMPLETED
                and role is not EvidenceRole.EXCLUDED
            ):
                eligible.append(cls._evidence_id(row))
        return sorted(eligible)

    @staticmethod
    def _evidence_id(record: CitationInclusionReconciliationRecord) -> str:
        if record.pmid is not None:
            return f"PMID:{record.pmid}"
        if re.fullmatch(r"PPR:PPR[0-9]+", record.record_key):
            return record.record_key
        raise CitationPassClosureError(
            f"eligible citation lacks a supported seed identity: {record.record_key}"
        )

    @staticmethod
    def _validate_identities(
        citation: CitationChainReceipt,
        preparation: CitationScreeningPreparationReceipt,
        decision: CitationDecisionLedgerReceipt,
        reconciliation: CitationInclusionReconciliationReceipt,
        queue: (
            EvidenceCapAmendmentActivationReceipt
            | CitationPassAppraisalQueueReceipt
        ),
    ) -> None:
        identities = {
            (citation.study_id, citation.pass_number),
            (preparation.study_id, preparation.pass_number),
            (decision.study_id, decision.pass_number),
            (reconciliation.study_id, reconciliation.pass_number),
        }
        queue_pass = (
            1
            if isinstance(queue, EvidenceCapAmendmentActivationReceipt)
            else queue.pass_number
        )
        identities.add((queue.study_id, queue_pass))
        if len(identities) != 1:
            raise CitationPassClosureError(
                "citation-pass closure receipt identities differ"
            )
        if (
            preparation.citation_execution_id != citation.execution_id
            or preparation.input_candidate_count != citation.unique_candidate_count
            or decision.candidate_count != preparation.requires_screening_count
            or decision.included_count != reconciliation.confirmed_inclusion_count
            or decision.decision_id != reconciliation.decision_id
        ):
            raise CitationPassClosureError(
                "citation-pass closure count or receipt lineage differs"
            )
        if isinstance(queue, EvidenceCapAmendmentActivationReceipt):
            if queue.reconciliation_id != reconciliation.reconciliation_id:
                raise CitationPassClosureError(
                    "pass-1 queue does not match inclusion reconciliation"
                )
        elif (
            queue.decision_id != decision.decision_id
            or queue.reconciliation_id != reconciliation.reconciliation_id
        ):
            raise CitationPassClosureError(
                "later-pass queue does not match founder decisions"
            )
        if not (
            citation.manifest_checksum_verified
            and citation.object_checksums_verified
            and citation.endpoint_counts_verified
            and citation.candidate_count_verified
            and preparation.input_checksums_verified
            and preparation.prior_decision_checksums_verified
            and preparation.output_checksums_verified
            and preparation.count_invariants_verified
            and decision.packet_checksums_verified
            and decision.appendix_checksums_verified
            and decision.record_coverage_verified
            and decision.founder_authorized
            and not decision.ai_decisions_recorded
            and reconciliation.decision_ledger_checksum_verified
            and reconciliation.exact_identifier_matching_only
            and reconciliation.count_invariants_verified
        ):
            raise CitationPassClosureError(
                "citation-pass closure inputs are not fully verified"
            )

    @staticmethod
    def _verify_receipt_files(
        citation: CitationChainReceipt,
        preparation: CitationScreeningPreparationReceipt,
        decision: CitationDecisionLedgerReceipt,
        reconciliation: CitationInclusionReconciliationReceipt,
        queue: (
            EvidenceCapAmendmentActivationReceipt
            | CitationPassAppraisalQueueReceipt
        ),
        *,
        citation_receipt_path: Path,
        preparation_receipt_path: Path,
        decision_receipt_path: Path,
        reconciliation_receipt_path: Path,
        queue_receipt_path: Path,
    ) -> None:
        if (
            load_citation_chain_receipt(citation_receipt_path) != citation
            or load_citation_screening_preparation_receipt(
                preparation_receipt_path
            )
            != preparation
            or load_citation_decision_ledger_receipt(decision_receipt_path)
            != decision
            or load_citation_inclusion_reconciliation_receipt(
                reconciliation_receipt_path
            )
            != reconciliation
            or load_citation_access_queue_receipt(queue_receipt_path) != queue
        ):
            raise CitationPassClosureError(
                "citation-pass receipt bytes do not match loaded contracts"
            )
