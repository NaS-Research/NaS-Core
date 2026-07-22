from nas_core.config import Settings


def test_settings_use_nas_environment_prefix(monkeypatch) -> None:
    monkeypatch.setenv("NAS_ENVIRONMENT", "test")
    monkeypatch.setenv("NAS_API_PORT", "9000")

    settings = Settings(_env_file=None)

    assert settings.environment == "test"
    assert settings.api_port == 9000
    assert settings.object_store_backend == "filesystem"


def test_openai_key_uses_provider_standard_environment_name(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")

    settings = Settings(_env_file=None)

    assert settings.openai_api_key == "synthetic-test-key"
    assert "synthetic-test-key" not in repr(settings)
