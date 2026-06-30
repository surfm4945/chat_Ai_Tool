"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _secret_value(key: str, default: Any) -> Any:
    """Read a value from Streamlit secrets when available.

    Streamlit Community Cloud stores app values in `secrets.toml`, while local
    development usually relies on `.env`. This helper supports both.
    """

    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


class Settings(BaseSettings):
    """Load configuration from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(
        default_factory=lambda: str(_secret_value("APP_NAME", "chat_Ai_Tool")),
        validation_alias="APP_NAME",
    )
    app_debug: bool = Field(
        default_factory=lambda: bool(_secret_value("APP_DEBUG", False)),
        validation_alias="APP_DEBUG",
    )
    secret_key: str = Field(
        default_factory=lambda: str(_secret_value("SECRET_KEY", "change-me")),
        validation_alias="SECRET_KEY",
    )
    database_path: Path = Field(
        default_factory=lambda: Path(str(_secret_value("DATABASE_PATH", "data/app.db"))),
        validation_alias="DATABASE_PATH",
    )
    session_ttl_minutes: int = Field(
        default_factory=lambda: int(_secret_value("SESSION_TTL_MINUTES", 120)),
        validation_alias="SESSION_TTL_MINUTES",
    )
    gemini_api_key: str = Field(
        default_factory=lambda: str(_secret_value("GEMINI_API_KEY", "")),
        validation_alias="GEMINI_API_KEY",
    )
    gemini_model: str = Field(
        default_factory=lambda: str(_secret_value("GEMINI_MODEL", "gemini-1.5-flash")),
        validation_alias="GEMINI_MODEL",
    )
    gemini_timeout_seconds: float = Field(
        default_factory=lambda: float(_secret_value("GEMINI_TIMEOUT_SECONDS", 30.0)),
        validation_alias="GEMINI_TIMEOUT_SECONDS",
    )
    ai_system_prompt: str = Field(
        default_factory=lambda: str(
            _secret_value("AI_SYSTEM_PROMPT", "You are a helpful private chat assistant.")
        ),
        validation_alias="AI_SYSTEM_PROMPT",
    )

    @property
    def database_url(self) -> str:
        """Return a display-friendly SQLite URL."""

        return f"sqlite:///{self.database_path.as_posix()}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""

    return Settings()
