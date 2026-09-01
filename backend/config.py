"""Minimal configuration for stateless Sentinel backend."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
