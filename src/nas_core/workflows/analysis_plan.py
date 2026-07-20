"""Load and governance-check versioned analysis plans."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from nas_core.domain.research import AnalysisPlan
from nas_core.governance.policy import DataAction, GovernancePolicy
from nas_core.governance.registry import SourceRegistry

REQUIRED_RESEARCH_ACTIONS = (
    DataAction.INGEST,
    DataAction.STORE,
    DataAction.ANALYZE,
)


def load_analysis_plan(
    path: Path,
    *,
    registry: SourceRegistry | None = None,
    policy: GovernancePolicy | None = None,
) -> AnalysisPlan:
    """Parse a plan and authorize its source for the declared research purpose."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    plan = AnalysisPlan.model_validate(payload)

    if registry is not None:
        source = registry.get(plan.governance.source_id)
        if source.classification is not plan.governance.classification:
            raise ValueError(
                "analysis plan classification does not match the registered source classification"
            )
        active_policy = policy or GovernancePolicy()
        for action in REQUIRED_RESEARCH_ACTIONS:
            active_policy.authorize(
                source,
                action=action,
                purpose=plan.governance.purpose,
                actor_role=plan.governance.actor_role,
            )

    return plan


def write_analysis_plan_schema(path: Path) -> None:
    """Write the canonical JSON Schema produced by the runtime model."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(AnalysisPlan.model_json_schema(), indent=2, sort_keys=True)
    path.write_text(f"{payload}\n", encoding="utf-8")
