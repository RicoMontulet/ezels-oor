from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPOSITORY_ROOT / ".env", extra="ignore")

    database_url: str = f"sqlite:///{REPOSITORY_ROOT / 'data' / 'ezelsoor.db'}"
    storage_path: Path = REPOSITORY_ROOT / "data" / "uploads"
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

    @model_validator(mode="after")
    def resolve_relative_paths(self) -> "Settings":
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.removeprefix("sqlite:///"))
            if not db_path.is_absolute():
                db_path = (REPOSITORY_ROOT / db_path).resolve()
                self.database_url = f"sqlite:///{db_path}"
        if not self.storage_path.is_absolute():
            self.storage_path = (REPOSITORY_ROOT / self.storage_path).resolve()
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
