"""Field-isolated GSE81538 metadata selection and external manifest freezing."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from nas_core.domain.matrix_audit import (
    GSE81538MatrixAuditReceipt,
    MatrixAuditDecision,
)
from nas_core.domain.public_artifact import (
    PublicArtifactAcquisitionReceipt,
    PublicArtifactKind,
)
from nas_core.domain.reference_development import ReferenceDevelopmentProtocol
from nas_core.domain.reference_input import ReferenceInputFounderDecision
from nas_core.domain.reference_metadata import (
    GSE81538ReferenceMetadataPlan,
    GSE81538ReferenceMetadataReceipt,
    ReferenceMetadataDecision,
)
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore

TITLE_PATTERN = re.compile(r"^T[1-9][0-9]*$")
ACCESSION_PATTERN = re.compile(r"^GSM[1-9][0-9]*$")
ER_PATTERN = re.compile(
    r"^!Sample_characteristics_ch1 = er consensus: (?P<code>[0-3])$"
)


class ReferenceMetadataError(RuntimeError):
    """Raised when field isolation, provenance, or selection fails closed."""


@dataclass(frozen=True, slots=True)
class _SampleRecord:
    title: str
    accession: str
    er_consensus: int


class GSE81538ReferenceMetadataService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def select(
        self,
        plan: GSE81538ReferenceMetadataPlan,
        acquisition: PublicArtifactAcquisitionReceipt,
        matrix_audit: GSE81538MatrixAuditReceipt,
        founder_decision: ReferenceInputFounderDecision,
        protocol: ReferenceDevelopmentProtocol,
        *,
        plan_path: Path,
        acquisition_path: Path,
        matrix_audit_path: Path,
        founder_decision_path: Path,
        protocol_path: Path,
        code_revision: str,
        audited_at: datetime | None = None,
    ) -> GSE81538ReferenceMetadataReceipt:
        self._validate_provenance(
            plan,
            acquisition,
            matrix_audit,
            founder_decision,
            protocol,
            acquisition_path=acquisition_path,
            matrix_audit_path=matrix_audit_path,
            founder_decision_path=founder_decision_path,
            protocol_path=protocol_path,
        )
        observed_sha, observed_bytes = self._hash_object(plan.metadata_object_key)
        if (
            observed_sha != plan.expected_metadata_sha256
            or observed_sha != acquisition.sha256
            or observed_bytes != plan.expected_metadata_bytes
            or observed_bytes != acquisition.content_length_bytes
        ):
            raise ReferenceMetadataError("metadata object does not match acquisition")

        records = self._parse_records(plan.metadata_object_key)
        if len(records) != plan.expected_sample_count:
            raise ReferenceMetadataError("metadata sample count changed")
        accessions = [record.accession for record in records]
        titles = [record.title for record in records]
        if len(set(accessions)) != len(accessions):
            raise ReferenceMetadataError("metadata contains duplicate GEO accessions")
        if len(set(titles)) != len(titles):
            raise ReferenceMetadataError("metadata contains duplicate sample titles")
        expected_titles = [
            f"{plan.expected_title_prefix}{index}"
            for index in range(1, plan.expected_sample_count + 1)
        ]
        if titles != expected_titles:
            raise ReferenceMetadataError("metadata sample-title sequence changed")

        counts = Counter(record.er_consensus for record in records)
        if set(counts) - {0, 1, 2, 3}:
            raise ReferenceMetadataError("metadata contains an undeclared ER code")
        negative = sorted(
            (
                record
                for record in records
                if record.er_consensus == plan.er_negative_consensus_code
            ),
            key=lambda record: record.accession,
        )
        positive = sorted(
            (
                record
                for record in records
                if record.er_consensus == plan.er_positive_consensus_code
            ),
            key=lambda record: record.accession,
        )
        if min(len(negative), len(positive)) < plan.samples_per_stratum:
            raise ReferenceMetadataError("an approved ER stratum is too small")
        selected_negative = negative[: plan.samples_per_stratum]
        selected_positive = positive[: plan.samples_per_stratum]
        manifest_bytes = self._manifest_bytes(
            plan,
            selected_negative=selected_negative,
            selected_positive=selected_positive,
        )
        if self._store.exists(plan.manifest_object_key):
            raise ReferenceMetadataError("immutable selection manifest already exists")
        self._store.put_bytes(
            plan.manifest_object_key,
            manifest_bytes,
            content_type="application/json",
        )
        stored_manifest = self._store.get_bytes(plan.manifest_object_key)
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
        if stored_manifest != manifest_bytes:
            raise ReferenceMetadataError("stored selection manifest changed")

        ambiguous_count = sum(
            counts.get(code, 0) for code in plan.excluded_er_consensus_codes
        )
        return GSE81538ReferenceMetadataReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            source_id=plan.source_id,
            source_accession=plan.source_accession,
            code_revision=code_revision,
            audited_at=audited_at or datetime.now(UTC),
            plan_sha256=sha256(plan_path.read_bytes()),
            metadata_acquisition_receipt_sha256=sha256(acquisition_path.read_bytes()),
            matrix_audit_receipt_sha256=sha256(matrix_audit_path.read_bytes()),
            founder_decision_sha256=sha256(founder_decision_path.read_bytes()),
            reference_protocol_sha256=sha256(protocol_path.read_bytes()),
            metadata_object_sha256_verified=True,
            metadata_bytes=observed_bytes,
            parsed_sample_fields=plan.permitted_sample_fields,
            sample_record_count=len(records),
            unique_accession_count=len(set(accessions)),
            unique_title_count=len(set(titles)),
            exact_title_sequence_verified=True,
            matrix_title_linkage_verified=True,
            er_consensus_counts={code: counts.get(code, 0) for code in range(4)},
            er_negative_eligible_count=len(negative),
            er_positive_eligible_count=len(positive),
            ambiguous_excluded_count=ambiguous_count,
            selected_negative_count=len(selected_negative),
            selected_positive_count=len(selected_positive),
            manifest_object_key=plan.manifest_object_key,
            manifest_sha256=manifest_hash,
            manifest_bytes=len(manifest_bytes),
            manifest_record_count=len(selected_negative) + len(selected_positive),
            manifest_immutable_verified=True,
            relationship_to_validation=(
                "The primary publication describes GSE81538 as the 405-tumor "
                "training cohort and GSE96058 as an independent 3,273-tumor "
                "validation cohort; identifier-level non-overlap remains unverified."
            ),
            er_codebook_status="founder_approved_conservative_inference",
            decision=ReferenceMetadataDecision.PASS,
            limitations=[
                "The public metadata has no inline codebook for ER consensus 0–3.",
                "Extreme codes 0 and 3 are a founder-approved conservative inference.",
                "Publication-described independence is not an identifier-level audit.",
                "The deterministic subset may not represent all source variation.",
            ],
            participant_identifiers_stored_external=True,
            participant_identifiers_retained_in_git=False,
            outcome_values_accessed=False,
            expression_values_accessed=False,
            validation_data_accessed=False,
            classifier_executed=False,
            generative_ai_received_participant_data=False,
        )

    def _parse_records(self, key: str) -> list[_SampleRecord]:
        records: list[_SampleRecord] = []
        current: dict[str, str | int] | None = None
        with (
            self._store.open_binary(key) as raw,
            gzip.GzipFile(fileobj=raw, mode="rb") as compressed,
            io.TextIOWrapper(compressed, encoding="utf-8") as text,
        ):
            for raw_line in text:
                line = raw_line.rstrip("\r\n")
                if line.startswith("^SAMPLE = "):
                    self._finish_record(current, records)
                    current = {}
                    continue
                if current is None:
                    continue
                if line.startswith("!Sample_title = "):
                    self._set_once(current, "title", line.removeprefix("!Sample_title = "))
                elif line.startswith("!Sample_geo_accession = "):
                    self._set_once(
                        current,
                        "accession",
                        line.removeprefix("!Sample_geo_accession = "),
                    )
                else:
                    er_match = ER_PATTERN.fullmatch(line)
                    if er_match is not None:
                        self._set_once(current, "er_consensus", int(er_match.group("code")))
        self._finish_record(current, records)
        return records

    @staticmethod
    def _set_once(target: dict[str, str | int], field: str, value: str | int) -> None:
        if field in target:
            raise ReferenceMetadataError(f"duplicate permitted metadata field: {field}")
        target[field] = value

    @staticmethod
    def _finish_record(
        current: dict[str, str | int] | None,
        records: list[_SampleRecord],
    ) -> None:
        if current is None:
            return
        if set(current) != {"title", "accession", "er_consensus"}:
            raise ReferenceMetadataError("sample lacks one or more permitted fields")
        title = current["title"]
        accession = current["accession"]
        er_consensus = current["er_consensus"]
        if not isinstance(title, str) or TITLE_PATTERN.fullmatch(title) is None:
            raise ReferenceMetadataError("sample title has an invalid form")
        if not isinstance(accession, str) or ACCESSION_PATTERN.fullmatch(accession) is None:
            raise ReferenceMetadataError("GEO accession has an invalid form")
        if not isinstance(er_consensus, int):
            raise ReferenceMetadataError("ER consensus has an invalid form")
        records.append(
            _SampleRecord(
                title=title,
                accession=accession,
                er_consensus=er_consensus,
            )
        )

    @staticmethod
    def _manifest_bytes(
        plan: GSE81538ReferenceMetadataPlan,
        *,
        selected_negative: list[_SampleRecord],
        selected_positive: list[_SampleRecord],
    ) -> bytes:
        payload = {
            "schema_version": "1.0.0",
            "study_id": plan.study_id,
            "source_accession": plan.source_accession,
            "selection_algorithm": {
                "ordering": plan.deterministic_ordering,
                "er_negative_consensus_code": plan.er_negative_consensus_code,
                "er_positive_consensus_code": plan.er_positive_consensus_code,
                "excluded_er_consensus_codes": plan.excluded_er_consensus_codes,
                "samples_per_stratum": plan.samples_per_stratum,
            },
            "records": [
                *[
                    {
                        "geo_accession": record.accession,
                        "sample_title": record.title,
                        "er_stratum": "ER-negative",
                    }
                    for record in selected_negative
                ],
                *[
                    {
                        "geo_accession": record.accession,
                        "sample_title": record.title,
                        "er_stratum": "ER-positive",
                    }
                    for record in selected_positive
                ],
            ],
        }
        return (
            json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
            + "\n"
        ).encode("utf-8")

    def _hash_object(self, key: str) -> tuple[str, int]:
        digest = hashlib.sha256()
        size = 0
        with self._store.open_binary(key) as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
        return digest.hexdigest(), size

    @staticmethod
    def _validate_provenance(
        plan: GSE81538ReferenceMetadataPlan,
        acquisition: PublicArtifactAcquisitionReceipt,
        matrix_audit: GSE81538MatrixAuditReceipt,
        founder_decision: ReferenceInputFounderDecision,
        protocol: ReferenceDevelopmentProtocol,
        *,
        acquisition_path: Path,
        matrix_audit_path: Path,
        founder_decision_path: Path,
        protocol_path: Path,
    ) -> None:
        declared = {
            "metadata acquisition": (
                plan.metadata_acquisition_receipt_sha256,
                acquisition_path,
            ),
            "matrix audit": (plan.matrix_audit_receipt_sha256, matrix_audit_path),
            "founder decision": (plan.founder_decision_sha256, founder_decision_path),
            "reference protocol": (plan.reference_protocol_sha256, protocol_path),
        }
        changed = [
            label
            for label, (expected, path) in declared.items()
            if expected != sha256(path.read_bytes())
        ]
        if changed:
            raise ReferenceMetadataError(
                f"reference-metadata provenance changed: {', '.join(changed)}"
            )
        if (
            acquisition.artifact_kind is not PublicArtifactKind.SAMPLE_METADATA
            or acquisition.object_key != plan.metadata_object_key
        ):
            raise ReferenceMetadataError("acquisition receipt identifies another artifact")
        if (
            matrix_audit.decision is not MatrixAuditDecision.PASS
            or not matrix_audit.sample_header_sequence_verified
            or matrix_audit.sample_column_count != plan.expected_sample_count
        ):
            raise ReferenceMetadataError("matrix-title lineage is not verified")
        if (
            not founder_decision.metadata_parser_authorized
            or not founder_decision.external_manifest_authorized
            or founder_decision.er_negative_consensus_code
            != plan.er_negative_consensus_code
            or founder_decision.er_positive_consensus_code
            != plan.er_positive_consensus_code
            or founder_decision.excluded_er_consensus_codes
            != plan.excluded_er_consensus_codes
        ):
            raise ReferenceMetadataError("founder decision does not authorize this rule")
        if (
            protocol.protocol_version != "1.1.0"
            or protocol.preprocessing_bridge.unit_audit_required
            or not protocol.preprocessing_bridge.transformation_locked
            or protocol.subset_rule.samples_per_stratum != plan.samples_per_stratum
        ):
            raise ReferenceMetadataError("reference protocol does not match selection")
