"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Sentinel SaaS settings loaded from environment variables."""

    database_url: str = "sqlite+aiosqlite:///./sentinel.db"
    github_client_id: str = ""
    github_client_secret: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
