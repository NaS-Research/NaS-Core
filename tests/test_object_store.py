from pathlib import Path

import pytest

from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import FileSystemObjectStore, InMemoryObjectStore


def test_in_memory_object_store_round_trip() -> None:
    store = InMemoryObjectStore()

    assert not store.exists("studies/example/manifest.json")

    store.put_bytes(
        "studies/example/manifest.json",
        b'{"study":"example"}',
        content_type="application/json",
    )

    assert store.exists("studies/example/manifest.json")
    assert store.get_bytes("studies/example/manifest.json") == b'{"study":"example"}'


def test_filesystem_object_store_round_trip(tmp_path: Path) -> None:
    data_root = tmp_path / "NaS-Core-Data"
    DataLayout(data_root).initialize()
    store = FileSystemObjectStore(data_root)

    store.put_bytes("raw/study/page.json", b"{}", content_type="application/json")

    assert store.exists("raw/study/page.json")
    assert store.get_bytes("raw/study/page.json") == b"{}"
    assert (data_root / "object-store" / "raw" / "study" / "page.json").is_file()


@pytest.mark.parametrize("key", ["", "/absolute", "../escape", "raw/../../escape"])
def test_filesystem_object_store_rejects_unsafe_keys(tmp_path: Path, key: str) -> None:
    data_root = tmp_path / "NaS-Core-Data"
    DataLayout(data_root).initialize()
    store = FileSystemObjectStore(data_root)

    with pytest.raises(ValueError, match="safe relative|escapes"):
        store.exists(key)
