from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from nas_core.domain.datasets import (
    ApprovalDecision,
    ApprovalRecord,
    SourceRegistration,
    SourceStatus,
)
from nas_core.governance.approvals import transition_source
from nas_core.governance.classifications import DataClassification, most_restrictive
from nas_core.governance.exceptions import (
    InvalidLifecycleTransitionError,
    PolicyDeniedError,
    SourceNotFoundError,
)
from nas_core.governance.policy import DataAction, GovernancePolicy
from nas_core.governance.registry import SourceRegistry

REGISTRY_PATH = Path(__file__).parents[1] / "data" / "source-registry.yaml"


def approval() -> ApprovalRecord:
    return ApprovalRecord(
        approver="Test Steward",
        role="data_steward",
        decision=ApprovalDecision.APPROVE,
        decided_at=datetime(2026, 7, 20, tzinfo=UTC),
        rationale="Synthetic test approval",
    )


def source(
    *,
    classification: DataClassification = DataClassification.PUBLIC_OPEN,
    status: SourceStatus = SourceStatus.ACTIVE,
    ai_processing_allowed: bool = True,
    embeddings_allowed: bool = True,
    model_training_allowed: bool = False,
    export_allowed: bool = True,
    publication_allowed: bool = True,
    retention_days: int | None = None,
) -> SourceRegistration:
    return SourceRegistration(
        source_id="synthetic-source",
        name="Synthetic source",
        owner="NaS tests",
        authoritative_url="https://example.test/data",
        classification=classification,
        status=status,
        version="1",
        access_method="Synthetic fixture",
        approved_purposes={"governance-test"},
        intended_uses=["Governance tests"],
        prohibited_uses=["Real research"],
        license_or_terms="Synthetic only",
        attribution="Synthetic source",
        authorized_roles={"researcher", "data_steward"},
        retention_days=retention_days,
        ai_processing_allowed=ai_processing_allowed,
        embeddings_allowed=embeddings_allowed,
        model_training_allowed=model_training_allowed,
        export_allowed=export_allowed,
        publication_allowed=publication_allowed,
        approvals=[approval()],
    )


def test_most_restrictive_classification_wins() -> None:
    result = most_restrictive([DataClassification.PUBLIC_OPEN, DataClassification.CONTROLLED])
    assert result is DataClassification.CONTROLLED


def test_empty_classification_list_is_invalid() -> None:
    with pytest.raises(ValueError, match="At least one"):
        most_restrictive([])


def test_registry_loads_approved_gdc_open_source() -> None:
    registry = SourceRegistry.from_yaml(REGISTRY_PATH)
    registered = registry.get("gdc-tcga-open")

    assert registered.classification is DataClassification.PUBLIC_OPEN
    assert registered.status is SourceStatus.ACTIVE
    assert not registered.model_training_allowed


def test_registry_loads_processed_scan_b_validation_source() -> None:
    registry = SourceRegistry.from_yaml(REGISTRY_PATH)
    registered = registry.get("ncbi-geo-gse96058")

    assert registered.classification is DataClassification.PUBLIC_OPEN
    assert registered.status is SourceStatus.ACTIVE
    assert registered.publication_allowed
    assert not registered.model_training_allowed


def test_registry_rejects_unknown_source() -> None:
    registry = SourceRegistry.from_yaml(REGISTRY_PATH)
    with pytest.raises(SourceNotFoundError):
        registry.get("not-registered")


def test_valid_lifecycle_transition() -> None:
    assert (
        transition_source(SourceStatus.PROPOSED, SourceStatus.UNDER_REVIEW)
        is SourceStatus.UNDER_REVIEW
    )


def test_invalid_lifecycle_transition() -> None:
    with pytest.raises(InvalidLifecycleTransitionError):
        transition_source(SourceStatus.PROPOSED, SourceStatus.ACTIVE)


@pytest.mark.parametrize("action", [DataAction.INGEST, DataAction.STORE, DataAction.ANALYZE])
def test_active_public_source_allows_core_research_actions(action: DataAction) -> None:
    decision = GovernancePolicy().evaluate(
        source(),
        action,
        actor_role="researcher",
        purpose="governance-test",
    )
    assert decision.allowed


@pytest.mark.parametrize(
    "classification",
    [DataClassification.CONTROLLED, DataClassification.PHI],
)
def test_v0_blocks_sensitive_classifications(classification: DataClassification) -> None:
    registration = source(
        classification=classification,
        retention_days=365 if classification is DataClassification.LICENSED else None,
    )
    with pytest.raises(PolicyDeniedError, match="prohibited in Cortex v0"):
        GovernancePolicy().authorize(
            registration,
            DataAction.ANALYZE,
            actor_role="researcher",
            purpose="governance-test",
        )


def test_non_active_source_is_denied() -> None:
    registration = source(status=SourceStatus.SUSPENDED)
    decision = GovernancePolicy().evaluate(
        registration,
        DataAction.INGEST,
        actor_role="researcher",
        purpose="governance-test",
    )
    assert not decision.allowed
    assert "not active" in decision.reason


def test_unauthorized_role_is_denied() -> None:
    decision = GovernancePolicy().evaluate(
        source(),
        DataAction.ANALYZE,
        actor_role="visitor",
        purpose="governance-test",
    )
    assert not decision.allowed
    assert "not authorized" in decision.reason


@pytest.mark.parametrize(
    ("action", "expected_reason"),
    [
        (DataAction.TRAIN_MODEL, "model training"),
        (DataAction.EMBED, "embeddings"),
        (DataAction.AI_PROCESS, "AI processing"),
        (DataAction.EXPORT, "export"),
        (DataAction.PUBLISH, "publication"),
    ],
)
def test_source_specific_permission_flags_are_enforced(
    action: DataAction,
    expected_reason: str,
) -> None:
    registration = source(
        ai_processing_allowed=False,
        embeddings_allowed=False,
        model_training_allowed=False,
        export_allowed=False,
        publication_allowed=False,
    )
    decision = GovernancePolicy().evaluate(
        registration,
        action,
        actor_role="researcher",
        purpose="governance-test",
    )
    assert not decision.allowed
    assert expected_reason in decision.reason


def test_licensed_source_requires_retention_period() -> None:
    with pytest.raises(ValueError, match="retention period"):
        source(classification=DataClassification.LICENSED)


def test_active_source_requires_approval_record() -> None:
    with pytest.raises(ValueError, match="approval record"):
        SourceRegistration(
            source_id="unapproved-source",
            name="Unapproved",
            owner="NaS tests",
            authoritative_url="https://example.test/unapproved",
            classification=DataClassification.PUBLIC_OPEN,
            status=SourceStatus.ACTIVE,
            version="1",
            access_method="Synthetic",
            approved_purposes={"governance-test"},
            intended_uses=["Test"],
            prohibited_uses=["Research"],
            license_or_terms="Synthetic",
            attribution="Synthetic",
            authorized_roles={"researcher"},
        )


def test_unapproved_research_purpose_is_denied() -> None:
    decision = GovernancePolicy().evaluate(
        source(),
        DataAction.ANALYZE,
        actor_role="researcher",
        purpose="different-study",
    )
    assert not decision.allowed
    assert "purpose is not approved" in decision.reason


def test_overdue_source_review_is_denied() -> None:
    registration = source().model_copy(update={"review_on": date(2026, 1, 1)})
    decision = GovernancePolicy().evaluate(
        registration,
        DataAction.ANALYZE,
        actor_role="researcher",
        purpose="governance-test",
        as_of=date(2026, 7, 20),
    )
    assert not decision.allowed
    assert "review was due" in decision.reason
