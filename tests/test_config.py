from nas_core.config import Settings


def test_settings_use_nas_environment_prefix(monkeypatch) -> None:
    monkeypatch.setenv("NAS_ENVIRONMENT", "test")
    monkeypatch.setenv("NAS_API_PORT", "9000")

    settings = Settings(_env_file=None)

    assert settings.environment == "test"
    assert settings.api_port == 9000
