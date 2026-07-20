from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from nas_core.domain.datasets import SourceRegistration, SourceStatus
from nas_core.governance.classifications import DataClassification
from nas_core.governance.exceptions import PolicyDeniedError


class DataAction(StrEnum):
    INGEST = "ingest"
    STORE = "store"
    ANALYZE = "analyze"
    AI_PROCESS = "ai_process"
    EMBED = "embed"
    TRAIN_MODEL = "train_model"
    EXPORT = "export"
    PUBLISH = "publish"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


class GovernancePolicy:
    """Cortex v0 deny-by-default policy engine."""

    _V0_BLOCKED = {DataClassification.CONTROLLED, DataClassification.PHI}

    def evaluate(
        self,
        source: SourceRegistration,
        action: DataAction,
        *,
        actor_role: str,
        purpose: str,
        as_of: date | None = None,
    ) -> PolicyDecision:
        evaluation_date = as_of or date.today()

        if source.status is not SourceStatus.ACTIVE:
            return PolicyDecision(False, f"Source status is {source.status.value}, not active")

        if source.review_on is not None and source.review_on < evaluation_date:
            return PolicyDecision(False, f"Source review was due on {source.review_on.isoformat()}")

        if source.classification in self._V0_BLOCKED:
            return PolicyDecision(
                False,
                f"{source.classification.value} data is prohibited in Cortex v0",
            )

        if purpose not in source.approved_purposes:
            return PolicyDecision(False, f"Research purpose is not approved: {purpose}")

        if actor_role not in source.authorized_roles:
            return PolicyDecision(False, f"Role is not authorized: {actor_role}")

        if action is DataAction.AI_PROCESS and not source.ai_processing_allowed:
            return PolicyDecision(False, "Source does not permit AI processing")
        if action is DataAction.EMBED and not source.embeddings_allowed:
            return PolicyDecision(False, "Source does not permit embeddings")
        if action is DataAction.TRAIN_MODEL and not source.model_training_allowed:
            return PolicyDecision(False, "Source does not permit model training")
        if action is DataAction.EXPORT and not source.export_allowed:
            return PolicyDecision(False, "Source does not permit export")
        if action is DataAction.PUBLISH and not source.publication_allowed:
            return PolicyDecision(False, "Source does not permit publication")

        return PolicyDecision(True, "Action is permitted by the active source registration")

    def authorize(
        self,
        source: SourceRegistration,
        action: DataAction,
        *,
        actor_role: str,
        purpose: str,
        as_of: date | None = None,
    ) -> None:
        decision = self.evaluate(
            source,
            action,
            actor_role=actor_role,
            purpose=purpose,
            as_of=as_of,
        )
        if not decision.allowed:
            raise PolicyDeniedError(decision.reason)
