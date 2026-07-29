from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.analysis.reference_development import (
    ReferenceDevelopmentProtocolError,
    ReferenceDevelopmentProtocolService,
)
from nas_core.domain.reference_development import (
    ReferenceDevelopmentProtocol,
    load_reference_development_protocol,
)
from nas_core.governance.registry import SourceRegistry

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
PROTOCOL = STUDY / "protocol/reference_development_protocol_v1.0.0.yaml"
AUTHORIZATION = STUDY / "reviews/FOUNDER_STANDING_AUTONOMY_AUTHORIZATION_v1.0.0.yaml"
PLATFORM = STUDY / "protocol/platform_compatibility_audit_receipt_v1.0.0.yaml"
CONFORMANCE = STUDY / "protocol/numerical_conformance_receipt_v1.0.0.yaml"
REGISTRY = ROOT / "data/source-registry.yaml"
SCHEMA = ROOT / "workflows/reference_development_protocol.schema.json"


def _validate(protocol: ReferenceDevelopmentProtocol) -> None:
    ReferenceDevelopmentProtocolService().validate(
        protocol,
        SourceRegistry.from_yaml(REGISTRY),
        registry_path=REGISTRY,
        standing_authorization_path=AUTHORIZATION,
        platform_audit_path=PLATFORM,
        numerical_conformance_path=CONFORMANCE,
    )


def test_reference_development_protocol_is_governed_and_nonexecuting() -> None:
    protocol = load_reference_development_protocol(PROTOCOL)
    _validate(protocol)

    assert protocol.intended_role.value == "reference_development_only"
    assert protocol.source_selection_status.value == "candidate"
    assert protocol.subset_rule.samples_per_stratum == 50
    assert protocol.subset_rule.outcome_fields_permitted is False
    assert protocol.preprocessing_bridge.unit_audit_required is True
    assert protocol.preprocessing_bridge.transformation_locked is False
    assert protocol.molecular_values_accessed is False
    assert protocol.reference_locked is False


def test_reference_development_rejects_premature_lock() -> None:
    protocol = load_reference_development_protocol(PROTOCOL)
    payload = protocol.model_dump(mode="json")
    payload["source_selection_status"] = "locked"

    with pytest.raises(ValidationError):
        ReferenceDevelopmentProtocol.model_validate(payload)


def test_reference_development_rejects_changed_provenance() -> None:
    protocol = load_reference_development_protocol(PROTOCOL)
    changed = protocol.model_copy(update={"source_registry_sha256": "0" * 64})

    with pytest.raises(
        ReferenceDevelopmentProtocolError,
        match="source registry",
    ):
        _validate(changed)


def test_reference_development_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        ReferenceDevelopmentProtocol.model_json_schema()
    )
