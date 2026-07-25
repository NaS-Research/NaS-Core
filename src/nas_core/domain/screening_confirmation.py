"""Founder authorization contract for an exact advisory screening packet."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

CONFIRMATION_STATEMENT = "I confirm the screening packet as written."


class ScreeningConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    confirmation_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_previous_progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reviewer_name: str = Field(min_length=1)
    confirmation_statement: str
    author_year_links_rejected: bool
    founder_authorized: bool
    confirmed_at: datetime
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_founder_authorization(self) -> ScreeningConfirmation:
        if self.confirmation_statement != CONFIRMATION_STATEMENT:
            raise ValueError("confirmation statement does not authorize the exact packet")
        if not self.author_year_links_rejected:
            raise ValueError("confirmation must resolve the five author-year links")
        if not self.founder_authorized:
            raise ValueError("screening confirmation requires founder authorization")
        if self.scientific_conclusions_drawn:
            raise ValueError("screening confirmation cannot draw scientific conclusions")
        return self


class ScreeningPacketPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    queue_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    based_on_progress_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pending_record_count: int = Field(ge=1)
    proposed_include_count: int = Field(ge=0)
    proposed_exclude_count: int = Field(ge=0)
    complete_coverage_verified: bool
    immutable_identity_verified: bool
    founder_authorized: bool = False
    scientific_conclusions_drawn: bool = False

    @model_validator(mode="after")
    def validate_preview(self) -> ScreeningPacketPreview:
        if (
            self.proposed_include_count + self.proposed_exclude_count
            != self.pending_record_count
        ):
            raise ValueError("preview decisions must cover every pending record")
        if not self.complete_coverage_verified or not self.immutable_identity_verified:
            raise ValueError("preview requires verified coverage and identity")
        if self.founder_authorized:
            raise ValueError("packet preview cannot claim founder authorization")
        if self.scientific_conclusions_drawn:
            raise ValueError("packet preview cannot draw scientific conclusions")
        return self


def load_screening_confirmation(path: Path) -> ScreeningConfirmation:
    return ScreeningConfirmation.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
