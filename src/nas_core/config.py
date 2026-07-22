from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NAS_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    data_root: Path = Path(".local/nas-core-data")

    database_url: str = "postgresql+psycopg://nas_core:nas_core@localhost:5432/nas_core"

    object_store_backend: Literal["filesystem", "s3"] = "filesystem"
    object_store_bucket: str = "nas-core-local"
    object_store_region: str = "us-east-1"
    object_store_endpoint_url: str | None = "http://localhost:9000"
    object_store_access_key: str | None = Field(default=None, repr=False)
    object_store_secret_key: str | None = Field(default=None, repr=False)
    object_store_secure: bool = False

    ai_provider: Literal["openai"] = "openai"
    ai_screening_model: str = "gpt-5.6-sol"
    ai_screening_reasoning_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    openai_api_key: str | None = Field(default=None, repr=False, validation_alias="OPENAI_API_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
