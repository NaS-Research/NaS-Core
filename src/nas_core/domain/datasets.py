from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, model_validator

from nas_core.governance.classifications import DataClassification


class SourceStatus(StrEnum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ApprovalDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class ApprovalRecord(BaseModel):
    approver: str = Field(min_length=1)
    role: str = Field(min_length=1)
    decision: ApprovalDecision
    decided_at: datetime
    rationale: str = Field(min_length=1)


class SourceRegistration(BaseModel):
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    authoritative_url: HttpUrl
    classification: DataClassification
    status: SourceStatus = SourceStatus.PROPOSED
    version: str = Field(min_length=1)
    access_method: str = Field(min_length=1)
    approved_purposes: set[str] = Field(min_length=1)
    intended_uses: list[str] = Field(min_length=1)
    prohibited_uses: list[str] = Field(min_length=1)
    license_or_terms: str = Field(min_length=1)
    terms_url: HttpUrl | None = None
    attribution: str = Field(min_length=1)
    authorized_roles: set[str] = Field(min_length=1)
    storage_restrictions: list[str] = Field(default_factory=list)
    geographic_restrictions: list[str] = Field(default_factory=list)
    retention_days: int | None = Field(default=None, gt=0)
    review_on: date | None = None
    ai_processing_allowed: bool = False
    embeddings_allowed: bool = False
    model_training_allowed: bool = False
    export_allowed: bool = False
    publication_allowed: bool = False
    approvals: list[ApprovalRecord] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_activation_and_licensing(self) -> "SourceRegistration":
        if self.status in {SourceStatus.APPROVED, SourceStatus.ACTIVE} and not any(
            approval.decision is ApprovalDecision.APPROVE for approval in self.approvals
        ):
            raise ValueError("Approved and active sources require an approval record")
        if self.classification is DataClassification.LICENSED and self.retention_days is None:
            raise ValueError("Licensed sources require a retention period")
        return self
