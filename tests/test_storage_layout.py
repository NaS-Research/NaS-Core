import json
from pathlib import Path

import pytest

from nas_core.storage.layout import DataLayout, InvalidDataRootError


def test_initialize_creates_and_validates_layout(tmp_path: Path) -> None:
    root = tmp_path / "NaS-Core-Data"
    layout = DataLayout(root)

    layout.initialize()
    layout.validate()

    for directory in layout.REQUIRED_DIRECTORIES:
        assert (root / directory).is_dir()

    metadata = json.loads((root / layout.MARKER_FILE).read_text(encoding="utf-8"))
    assert metadata["kind"] == "nas-core-data-root"
    assert metadata["schema_version"] == 1
    assert "raw/" in metadata["object_store_prefixes"]


def test_validate_rejects_uninitialized_root(tmp_path: Path) -> None:
    root = tmp_path / "uninitialized"
    root.mkdir()

    with pytest.raises(InvalidDataRootError, match="marker is missing"):
        DataLayout(root).validate()


def test_validate_rejects_incomplete_layout(tmp_path: Path) -> None:
    root = tmp_path / "incomplete"
    layout = DataLayout(root)
    layout.initialize()
    (root / "quarantine").rmdir()

    with pytest.raises(InvalidDataRootError, match="quarantine"):
        layout.validate()


@pytest.mark.parametrize("unsafe_root", [Path("/"), Path.home(), Path("/Volumes")])
def test_rejects_unsafe_broad_roots(unsafe_root: Path) -> None:
    with pytest.raises(InvalidDataRootError, match="Unsafe"):
        DataLayout(unsafe_root).initialize()
