"""Founder-authorized reference-input decisions for NAS-BRCA-002."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReferenceInputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReferenceInputFounderDecision(ReferenceInputModel):
    schema_version: str = "1.0.0"
    decision_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    decision_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_audit_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    metadata_acquisition_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation_statement: str = Field(min_length=1)
    founder_id: str = Field(pattern=r"^[a-z0-9-]+$")
    founder_name: str = Field(min_length=1)
    reviewer_role: str = Field(pattern=r"^founder_internal_reviewer$")
    confirmed_at: datetime
    stored_input_representation: str = Field(pattern=r"^log2\(FPKM \+ 0\.1\)$")
    additional_transformation: str = Field(pattern=r"^none$")
    er_negative_consensus_code: int = Field(ge=0, le=3)
    er_positive_consensus_code: int = Field(ge=0, le=3)
    excluded_er_consensus_codes: list[int] = Field(min_length=2, max_length=2)
    limitations_preserved: bool
    protocol_amendment_authorized: bool
    metadata_parser_authorized: bool
    external_manifest_authorized: bool
    outcome_blind_reference_construction_authorized: bool
    outcome_access_authorized: bool
    validation_data_access_authorized: bool
    classifier_execution_authorized: bool
    scientific_conclusion_authorized: bool
    clinical_use_authorized: bool
    publication_authorized: bool
    submission_authorized: bool
    final_human_review_preserved: bool

    @model_validator(mode="after")
    def enforce_bounded_decision(self) -> ReferenceInputFounderDecision:
        if self.er_negative_consensus_code != 0:
            raise ValueError("the approved ER-negative consensus code is 0")
        if self.er_positive_consensus_code != 3:
            raise ValueError("the approved ER-positive consensus code is 3")
        if self.excluded_er_consensus_codes != [1, 2]:
            raise ValueError("the approved excluded ER codes are 1 and 2")
        if not all(
            (
                self.limitations_preserved,
                self.protocol_amendment_authorized,
                self.metadata_parser_authorized,
                self.external_manifest_authorized,
                self.outcome_blind_reference_construction_authorized,
                self.final_human_review_preserved,
            )
        ):
            raise ValueError("approved internal reference-input actions must be preserved")
        if any(
            (
                self.outcome_access_authorized,
                self.validation_data_access_authorized,
                self.classifier_execution_authorized,
                self.scientific_conclusion_authorized,
                self.clinical_use_authorized,
                self.publication_authorized,
                self.submission_authorized,
            )
        ):
            raise ValueError("reference-input decision cannot authorize later study stages")
        return self


def load_reference_input_founder_decision(
    path: Path,
) -> ReferenceInputFounderDecision:
    return ReferenceInputFounderDecision.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_reference_input_decision_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            ReferenceInputFounderDecision.model_json_schema(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
