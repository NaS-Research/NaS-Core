from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nas_core.domain.storage_readiness import StorageReadinessReceipt
from nas_core.storage.layout import DataLayout
from nas_core.storage.readiness import StorageReadinessService

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "workflows/storage_readiness_receipt.schema.json"


def test_storage_readiness_is_non_mutating_and_reconciled(tmp_path: Path) -> None:
    data_root = tmp_path / "nas-data"
    DataLayout(data_root).initialize()

    receipt = StorageReadinessService().inspect(
        data_root,
        minimum_required_bytes=1,
        code_revision="1178bde",
        checked_at=datetime(2026, 7, 29, 22, 0, tzinfo=UTC),
    )

    assert receipt.decision.value == "ready"
    assert receipt.mount_read_only is False
    assert receipt.operating_system_write_access is True
    assert receipt.write_probe_performed is False
    assert receipt.source_bytes_written is False
    assert receipt.biomedical_data_accessed is False


def test_storage_readiness_rejects_inconsistent_decision(tmp_path: Path) -> None:
    data_root = tmp_path / "nas-data"
    DataLayout(data_root).initialize()
    receipt = StorageReadinessService().inspect(
        data_root,
        minimum_required_bytes=1,
        code_revision="1178bde",
        checked_at=datetime(2026, 7, 29, 22, 0, tzinfo=UTC),
    )
    payload = receipt.model_dump(mode="json")
    payload["mount_read_only"] = True

    with pytest.raises(ValidationError, match="does not reconcile"):
        StorageReadinessReceipt.model_validate(payload)


def test_storage_readiness_schema_matches_runtime_model() -> None:
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == (
        StorageReadinessReceipt.model_json_schema()
    )
