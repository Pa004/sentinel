"""Minimal configuration for stateless Sentinel backend."""

from __future__ import annotations

import json

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_prefix": "", "env_file": ".env"}

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> object:
        # Accepts JSON list '["https://a","https://b"]' or comma-separated
        # 'https://a, https://b' (fly secrets friendly).
        if isinstance(v, str):
            text = v.strip()
            if not text:
                return []
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid CORS_ORIGINS JSON: {exc}") from exc
                if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
                    raise ValueError("CORS_ORIGINS JSON must be a list of strings")
                return [origin.strip().rstrip("/") for origin in parsed if origin.strip()]
            return [origin.strip().rstrip("/") for origin in text.split(",") if origin.strip()]
        return v


settings = Settings()
