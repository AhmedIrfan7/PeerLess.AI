"""Environment-driven settings. All secrets must come from env vars — never hardcoded."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    secret_key: str = Field(default="dev-secret-change-in-production-min32!", description="Random secret, min 32 chars")
    version: str = "0.1.0"

    # ── Gemini ────────────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model_fast: str = "gemini-2.5-flash"
    gemini_model_smart: str = "gemini-2.5-pro"

    # ── Database ──────────────────────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "peerless"
    postgres_user: str = "peerless"
    postgres_password: str = "changeme_strong_password"

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_password: str = ""

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # ── Storage ───────────────────────────────────────────────────────────────
    storage_path: str = "./storage"
    max_upload_bytes: int = 25 * 1024 * 1024  # 25 MB

    # ── External APIs ─────────────────────────────────────────────────────────
    crossref_mailto: str = "researcher@example.com"
    pubmed_api_key: str = ""
    openalex_mailto: str = ""

    # ── n8n ───────────────────────────────────────────────────────────────────
    n8n_webhook_base: str = ""
    n8n_webhook_secret: str = ""

    # ── Cost controls ─────────────────────────────────────────────────────────
    max_daily_llm_cost_usd: float = 10.0
    llm_pricing_fast_per_1k_tokens: float = 0.000075  # gemini-2.5-flash estimate
    llm_pricing_smart_per_1k_tokens: float = 0.00125  # gemini-2.5-pro estimate

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_cors_origins: list[str] = ["http://localhost:3000"]

    # ── Admin ─────────────────────────────────────────────────────────────────
    admin_shared_password: str = ""

    # ── Feature flags ─────────────────────────────────────────────────────────
    feature_coi_agent: bool = False
    feature_reviewer_matcher: bool = False

    # ── SMTP (optional, Phase 3) ──────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""

    # ── Slack (optional, Phase 3) ─────────────────────────────────────────────
    slack_webhook_url: str = ""

    # ── Computed properties ───────────────────────────────────────────────────
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def llm_available(self) -> bool:
        return bool(
            self.gemini_api_key
            and self.gemini_api_key not in ("your_gemini_api_key_here", "")
        )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        v = v.upper()
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in valid:
            raise ValueError(f"log_level must be one of {valid}, got {v!r}")
        return v

    @field_validator("allowed_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [o.strip().rstrip("/") for o in v.split(",") if o.strip()]
        return list(v)  # type: ignore[arg-type]


@lru_cache
def get_settings() -> Settings:
    return Settings()
