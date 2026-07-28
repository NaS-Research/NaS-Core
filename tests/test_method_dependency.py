import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from nas_core.analysis.method_dependency import (
    MethodDependencyAuditError,
    MethodDependencyAuditService,
)
from nas_core.cli import main
from nas_core.domain.evidence_synthesis import (
    load_authorized_saturated_evidence_synthesis,
)
from nas_core.domain.method_dependency import (
    MethodDependencyAuditProposal,
    load_method_dependency_audit,
)
from nas_core.domain.reliability import load_reliability_specification

ROOT = Path(__file__).parents[1]
STUDY = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
)
AUDIT = STUDY / "protocol" / "method_dependency_audit_proposal_v1.0.0.yaml"
SYNTHESIS = STUDY / "literature" / "saturated_evidence_synthesis_v1.0.0.yaml"
SPECIFICATION = STUDY / "protocol" / "reliability_specification.yaml"
SCHEMA = ROOT / "workflows" / "method_dependency_audit.schema.json"


def test_checked_in_method_audit_is_bound_and_nonexecuting() -> None:
    audit = MethodDependencyAuditService().validate(
        load_method_dependency_audit(AUDIT),
        load_authorized_saturated_evidence_synthesis(SYNTHESIS),
        load_reliability_specification(SPECIFICATION),
        synthesis_path=SYNTHESIS,
        specification_path=SPECIFICATION,
    )

    assert audit.recommended_route_id == "ROUTE-C"
    assert len(audit.dependencies) == 7
    assert audit.artifact_candidates[0].status == "verified_candidate"
    assert audit.founder_decision_required is True
    assert audit.method_execution_authorized is False
    assert audit.molecular_data_access_authorized is False
    assert audit.outcome_data_access_authorized is False


def test_method_audit_cli_validates_governed_bindings(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(
        [
            "reliability",
            "audit-validate",
            str(AUDIT),
            str(SYNTHESIS),
            str(SPECIFICATION),
        ]
    )

    assert result == 0
    assert "founder decision required" in capsys.readouterr().out


def test_checked_in_method_audit_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        MethodDependencyAuditProposal.model_json_schema()
    )


def test_method_audit_rejects_tampered_synthesis_binding() -> None:
    audit = load_method_dependency_audit(AUDIT).model_copy(
        update={"authorized_synthesis_sha256": "0" * 64}
    )

    with pytest.raises(MethodDependencyAuditError, match="different authorized"):
        MethodDependencyAuditService().validate(
            audit,
            load_authorized_saturated_evidence_synthesis(SYNTHESIS),
            load_reliability_specification(SPECIFICATION),
            synthesis_path=SYNTHESIS,
            specification_path=SPECIFICATION,
        )


def test_method_audit_cannot_authorize_data_or_execution() -> None:
    payload = deepcopy(yaml.safe_load(AUDIT.read_text(encoding="utf-8")))
    payload["molecular_data_access_authorized"] = True

    with pytest.raises(ValidationError, match="cannot access data"):
        MethodDependencyAuditProposal.model_validate(payload)


def test_method_audit_requires_exactly_one_matching_preferred_route() -> None:
    payload = deepcopy(yaml.safe_load(AUDIT.read_text(encoding="utf-8")))
    payload["routes"][0]["recommendation"] = "preferred"

    with pytest.raises(ValidationError, match="exactly one preferred"):
        MethodDependencyAuditProposal.model_validate(payload)
