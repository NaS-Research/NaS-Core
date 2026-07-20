from nas_core.storage.object_store import InMemoryObjectStore


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
