"""Typed contracts for the founder-authorized field-isolated metadata audit."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FieldIsolationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FieldIsolationDecision(StrEnum):
    PASS = "pass"
    CHANGES_REQUESTED = "changes_requested"
    HOLD = "hold"
    FAIL = "fail"


class FieldIsolationStatus(StrEnum):
    VERIFIED = "verified"
    UNRESOLVED = "unresolved"
    FAILED = "failed"


class FieldIsolatedMetadataAuthorization(FieldIsolationModel):
    schema_version: str = Field(pattern=r"^1\.0\.0$")
    study_id: str = Field(pattern=r"^NAS-BRCA-002$")
    question_id: str = Field(pattern=r"^NAS-RQ-BRCA002$")
    question_version: str = Field(pattern=r"^0\.3\.0$")
    audit_version: str = Field(pattern=r"^1\.0\.[01]$")
    packet_filename: str = Field(min_length=1)
    packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prior_receipt_filename: str | None = None
    prior_receipt_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    authorization_statement: str = Field(min_length=1)
    founder_id: str = Field(min_length=1)
    founder_name: str = Field(min_length=1)
    founder_role: str = Field(min_length=1)
    authorized_at: str = Field(min_length=1)
    founder_authorized: bool
    transient_field_isolated_access_authorized: bool
    patient_level_data_retention_authorized: bool
    molecular_value_analysis_authorized: bool
    outcome_data_access_authorized: bool
    cohort_construction_authorized: bool
    classifier_execution_authorized: bool
    scientific_conclusions_authorized: bool
    ai_assistance_disclosure: str = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_narrow_authorization(self) -> FieldIsolatedMetadataAuthorization:
        if not self.founder_authorized or not self.transient_field_isolated_access_authorized:
            raise ValueError("field-isolated transient access must be founder-authorized")
        prohibited = (
            self.patient_level_data_retention_authorized,
            self.molecular_value_analysis_authorized,
            self.outcome_data_access_authorized,
            self.cohort_construction_authorized,
            self.classifier_execution_authorized,
            self.scientific_conclusions_authorized,
        )
        if any(prohibited):
            raise ValueError("authorization exceeds the field-isolated Phase 0 boundary")
        expected = {
            "1.0.0": (
                "FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md",
                "I authorize field-isolated metadata audit 1.0.0 as written.",
            ),
            "1.0.1": (
                "FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_v1.0.1.md",
                "I authorize field-isolated metadata audit amendment 1.0.1 as written.",
            ),
        }
        expected_packet, expected_statement = expected[self.audit_version]
        if self.packet_filename != expected_packet:
            raise ValueError("authorization packet filename does not match audit version")
        if self.authorization_statement != expected_statement:
            raise ValueError("authorization statement does not match audit version")
        if self.audit_version == "1.0.1":
            if (
                self.prior_receipt_filename
                != "field_isolated_metadata_receipt_v1.0.0.yaml"
                or self.prior_receipt_sha256 is None
            ):
                raise ValueError("audit 1.0.1 must bind the immutable 1.0.0 receipt")
        elif self.prior_receipt_filename is not None or self.prior_receipt_sha256 is not None:
            raise ValueError("audit 1.0.0 cannot declare a prior receipt")
        return self


class SourceArtifactEvidence(FieldIsolationModel):
    source_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    url: str = Field(pattern=r"^https://")
    file_id: str | None = None
    filename: str = Field(min_length=1)
    declared_md5: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    representation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    representation_size_bytes: int = Field(ge=1)
    parser_name: str = Field(min_length=1)
    raw_artifact_stored: bool
    permitted_field_names: list[str]
    rejected_field_names: list[str]

    @model_validator(mode="after")
    def prohibit_raw_storage(self) -> SourceArtifactEvidence:
        if self.raw_artifact_stored:
            raise ValueError("field-isolated source artifacts cannot be stored")
        overlap = set(self.permitted_field_names) & set(self.rejected_field_names)
        if overlap:
            raise ValueError(f"fields cannot be both permitted and rejected: {sorted(overlap)}")
        return self


class GeneCoverageSummary(FieldIsolationModel):
    source_id: str = Field(min_length=1)
    required_gene_count: int = Field(ge=1)
    observed_identifier_count: int = Field(ge=0)
    unique_identifier_count: int = Field(ge=0)
    canonical_genes_present: list[str]
    alias_resolutions: dict[str, str]
    missing_canonical_genes: list[str]
    duplicate_canonical_mappings: list[str]
    unmapped_identifier_count: int = Field(ge=0)
    expression_values_parsed: bool

    @model_validator(mode="after")
    def enforce_gene_projection(self) -> GeneCoverageSummary:
        if self.expression_values_parsed:
            raise ValueError("the gene-coverage projection cannot parse expression values")
        if self.required_gene_count != (
            len(self.canonical_genes_present) + len(self.missing_canonical_genes)
        ):
            raise ValueError("canonical present and missing genes must partition the panel")
        if self.unique_identifier_count > self.observed_identifier_count:
            raise ValueError("unique identifier count cannot exceed observed count")
        return self


class ReceptorCompletenessSummary(FieldIsolationModel):
    source_id: str = Field(min_length=1)
    record_count: int = Field(ge=1)
    er_present_count: int = Field(ge=0)
    pr_present_count: int = Field(ge=0)
    her2_present_count: int = Field(ge=0)
    all_three_present_count: int = Field(ge=0)
    er_category_counts: dict[str, int]
    pr_category_counts: dict[str, int]
    her2_category_counts: dict[str, int]

    @model_validator(mode="after")
    def validate_completeness_counts(self) -> ReceptorCompletenessSummary:
        counts = (
            self.er_present_count,
            self.pr_present_count,
            self.her2_present_count,
            self.all_three_present_count,
        )
        if any(count > self.record_count for count in counts):
            raise ValueError("receptor completeness count exceeds record count")
        return self


class ReplicateSummary(FieldIsolationModel):
    source_id: str = Field(min_length=1)
    sample_record_count: int = Field(ge=1)
    primary_record_count: int = Field(ge=0)
    technical_replicate_count: int = Field(ge=0)
    linked_technical_replicate_count: int = Field(ge=0)
    unclassified_record_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_partition(self) -> ReplicateSummary:
        classified = (
            self.primary_record_count
            + self.technical_replicate_count
            + self.unclassified_record_count
        )
        if classified != self.sample_record_count:
            raise ValueError("replicate-state counts must partition sample records")
        if self.linked_technical_replicate_count > self.technical_replicate_count:
            raise ValueError("linked replicate count exceeds technical replicate count")
        return self


class FieldIsolationCheck(FieldIsolationModel):
    check_id: str = Field(min_length=1)
    status: FieldIsolationStatus
    finding: str = Field(min_length=1)
    evidence_source_ids: list[str] = Field(min_length=1)
    limitation: str | None = None

    @model_validator(mode="after")
    def require_limitation_for_nonverified(self) -> FieldIsolationCheck:
        if self.status is not FieldIsolationStatus.VERIFIED and not self.limitation:
            raise ValueError("nonverified checks require a limitation")
        return self


class FieldIsolatedMetadataReceipt(FieldIsolationModel):
    schema_version: str = Field(pattern=r"^1\.0\.0$")
    audit_version: str = Field(pattern=r"^1\.0\.[01]$")
    study_id: str = Field(pattern=r"^NAS-BRCA-002$")
    question_id: str = Field(pattern=r"^NAS-RQ-BRCA002$")
    question_version: str = Field(pattern=r"^0\.3\.0$")
    executed_at: str = Field(min_length=1)
    software_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    authorization_path: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    authorization_packet_path: str = Field(min_length=1)
    authorization_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prior_receipt_path: str | None = None
    prior_receipt_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    transient_field_isolated_access: bool
    prohibited_fields_transiently_transferred: bool
    patient_level_records_retained: bool
    molecular_values_parsed: bool
    outcome_values_parsed: bool
    raw_artifacts_stored: bool
    cohort_constructed: bool
    classifier_executed: bool
    artifacts: list[SourceArtifactEvidence] = Field(min_length=4)
    tcga_gene_coverage: GeneCoverageSummary
    gse96058_gene_coverage: GeneCoverageSummary
    tcga_receptor_completeness: ReceptorCompletenessSummary
    gse96058_receptor_completeness: ReceptorCompletenessSummary
    gse96058_replicates: ReplicateSummary
    checks: list[FieldIsolationCheck] = Field(min_length=5)
    decision: FieldIsolationDecision
    decision_rationale: str = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    next_authorization_required: list[str]

    @model_validator(mode="after")
    def enforce_projection_boundary(self) -> FieldIsolatedMetadataReceipt:
        if not self.transient_field_isolated_access:
            raise ValueError("receipt must disclose transient field-isolated access")
        prohibited = (
            self.patient_level_records_retained,
            self.molecular_values_parsed,
            self.outcome_values_parsed,
            self.raw_artifacts_stored,
            self.cohort_constructed,
            self.classifier_executed,
        )
        if any(prohibited):
            raise ValueError("receipt crosses the authorized field-isolated boundary")
        if self.decision is FieldIsolationDecision.PASS and any(
            check.status is not FieldIsolationStatus.VERIFIED for check in self.checks
        ):
            raise ValueError("a passing receipt cannot contain a nonverified check")
        if self.audit_version == "1.0.1":
            if self.prior_receipt_path is None or self.prior_receipt_sha256 is None:
                raise ValueError("audit 1.0.1 must bind its prior immutable receipt")
        elif self.prior_receipt_path is not None or self.prior_receipt_sha256 is not None:
            raise ValueError("audit 1.0.0 cannot bind a prior receipt")
        return self


def load_field_isolated_metadata_authorization(
    path: Path,
) -> FieldIsolatedMetadataAuthorization:
    return FieldIsolatedMetadataAuthorization.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def load_field_isolated_metadata_receipt(path: Path) -> FieldIsolatedMetadataReceipt:
    return FieldIsolatedMetadataReceipt.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_field_isolated_metadata_receipt(
    path: Path,
    receipt: FieldIsolatedMetadataReceipt,
) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite immutable receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        receipt.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        allow_unicode=True,
    )
    path.write_text(payload, encoding="utf-8")


def write_field_isolated_metadata_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        FieldIsolatedMetadataReceipt.model_json_schema(),
        indent=2,
        sort_keys=True,
    )
    path.write_text(f"{payload}\n", encoding="utf-8")
