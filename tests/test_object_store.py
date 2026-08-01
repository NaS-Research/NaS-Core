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
    with store.open_binary("studies/example/manifest.json") as stream:
        assert stream.read() == b'{"study":"example"}'


def test_filesystem_object_store_round_trip(tmp_path: Path) -> None:
    data_root = tmp_path / "NaS-Core-Data"
    DataLayout(data_root).initialize()
    store = FileSystemObjectStore(data_root)

    store.put_bytes("raw/study/page.json", b"{}", content_type="application/json")

    assert store.exists("raw/study/page.json")
    assert store.get_bytes("raw/study/page.json") == b"{}"
    with store.open_binary("raw/study/page.json") as stream:
        assert stream.read() == b"{}"
    assert (data_root / "object-store" / "raw" / "study" / "page.json").is_file()


def test_filesystem_object_store_streams_file_without_overwrite(tmp_path: Path) -> None:
    data_root = tmp_path / "NaS-Core-Data"
    DataLayout(data_root).initialize()
    source = tmp_path / "source.bin"
    source.write_bytes(b"governed-source-bytes")
    store = FileSystemObjectStore(data_root)

    store.put_file("raw/study/source.bin", source, content_type="application/octet-stream")

    assert store.get_bytes("raw/study/source.bin") == b"governed-source-bytes"
    with pytest.raises(FileExistsError):
        store.put_file("raw/study/source.bin", source, content_type="application/octet-stream")


@pytest.mark.parametrize("key", ["", "/absolute", "../escape", "raw/../../escape"])
def test_filesystem_object_store_rejects_unsafe_keys(tmp_path: Path, key: str) -> None:
    data_root = tmp_path / "NaS-Core-Data"
    DataLayout(data_root).initialize()
    store = FileSystemObjectStore(data_root)

    with pytest.raises(ValueError, match="safe relative|escapes"):
        store.exists(key)
