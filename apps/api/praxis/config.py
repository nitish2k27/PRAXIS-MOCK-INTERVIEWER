"""Typed application configuration. All model names, thresholds, weights live here."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "dev"

    # Database (async URL)
    database_url: str = "postgresql+asyncpg://praxis:praxis_dev@localhost:5432/praxis"

    # Redis (Phase 2+ live session state; declared now so config is stable)
    redis_url: str = "redis://localhost:6379/0"

    # Auth — JWT
    jwt_secret: str = "change-me-in-prod"
    jwt_alg: str = "HS256"
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 14

    # Auth — Google OIDC
    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_url: str = "http://localhost:8000/auth/google/callback"

    # Web app
    web_base_url: str = "http://localhost:5173"

    # Cookies
    cookie_secure: bool = False
    cookie_domain: str | None = None
    cookie_samesite: str = "lax"

    # Session middleware (Authlib OAuth state in a signed cookie)
    session_secret: str = "session-secret-change-me"

    # Storage (R2 / S3 in prod; local disk in dev/tests)
    storage_backend: str = "local"
    storage_local_dir: str = "./uploads"
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket: str = "praxis"
    s3_public_base_url: str | None = None

    # Chroma (Phase 1+)
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # Scoring (Phase 6)
    lora_scorer_url: str = "http://localhost:9000"

    # CORS
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])


settings = Settings()
