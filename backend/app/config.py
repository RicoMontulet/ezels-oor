from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPOSITORY_ROOT / ".env", extra="ignore")

    database_url: str = "sqlite:///./data/ezelsoor.db"
    storage_path: Path = Path("./data/uploads")
    upload_max_bytes: int = 100 * 1024 * 1024
    default_locale: str = "nl-NL"
    worker_lease_seconds: int = 15 * 60
    worker_poll_seconds: float = 2.0
    max_processing_attempts: int = 3
    retry_delay_seconds: int = 30

    speech_endpoint: str | None = None
    speech_api_key: str | None = None
    speech_api_version: str = "2025-10-15"
    language_endpoint: str | None = None
    language_api_key: str | None = None
    language_api_version: str = "2024-11-01"
    llm_endpoint: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_max_tokens: int = 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
