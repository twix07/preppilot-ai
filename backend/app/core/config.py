"""Application settings loaded from environment (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    environment: str = "development"
    app_name: str = "PrepPilot AI"

    # Database
    database_url: str = "sqlite+aiosqlite:///./preppilot.db"

    @property
    def async_database_url(self) -> str:
        """Normalise Render's postgres:// or postgresql:// to asyncpg driver."""
        url = self.database_url
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Auth
    jwt_secret: str = "change-me-in-production-please"
    jwt_expire_minutes: int = 1440
    jwt_algorithm: str = "HS256"
    google_client_id: str = ""
    allow_dev_login: bool = True

    # Encryption
    encryption_key: str = ""

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5"
    llm_temperature: float = 0.2

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "preppilot"
    langchain_tracing_v2: bool = False

    # Cost & abuse
    daily_interview_cap: int = 10
    daily_llm_call_cap: int = 120
    answer_char_cap: int = 1800

    # Readiness
    readiness_alpha: float = 0.6
    readiness_min_sessions: int = 5

    # Privacy
    resume_retention_days: int = 90

    # CORS — single origin or comma-separated list, e.g.:
    # "https://preppilot.vercel.app,http://localhost:3000"
    frontend_origin: str = "http://localhost:3000"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origin.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def llm_mock_mode(self) -> bool:
        """No API key => deterministic mock so the app is demoable for free."""
        return not self.anthropic_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
