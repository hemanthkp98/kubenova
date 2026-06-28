"""
KubeNova application configuration.

Reads all settings from environment variables using pydantic-settings.
See .env.example for a full list of supported variables.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    KUBENOVA_ENV: Literal["development", "production"] = Field(
        default="development",
        description="Runtime environment. Controls logging verbosity and CORS strictness.",
    )
    KUBENOVA_LOG_LEVEL: str = Field(
        default="INFO",
        description="Loguru log level: DEBUG, INFO, WARNING, ERROR, CRITICAL.",
    )
    KUBENOVA_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:5173"],
        description="List of allowed CORS origins for the frontend.",
    )
    KUBENOVA_DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./kubenova.db",
        description="Async SQLAlchemy database URL. SQLite for MVP; swap for postgresql+asyncpg:// in production.",
    )

    # LLM Provider
    LLM_PROVIDER: Literal["anthropic", "openai", "ollama"] = Field(
        default="ollama",
        description="Which LLM backend to use: anthropic | openai | ollama.",
    )
    LLM_MODEL: str = Field(
        default="llama3.2",
        description="Model identifier. Examples: llama3.2, claude-sonnet-4-6, gpt-4o.",
    )
    LLM_API_KEY: str | None = Field(
        default=None,
        description="API key for Anthropic or OpenAI. Never logged or stored in the DB.",
    )
    LLM_BASE_URL: str | None = Field(
        default="http://ollama:11434",
        description="Base URL for Ollama or custom OpenAI-compatible endpoint.",
    )

    # Kubernetes
    KUBECONFIG_PATH: str | None = Field(
        default=None,
        description="Path to kubeconfig file. Defaults to ~/.kube/config if not set.",
    )
    DEFAULT_CLUSTER_CONTEXT: str | None = Field(
        default=None,
        description="Default kubeconfig context name to activate on startup.",
    )
    MAX_LOG_LINES: int = Field(
        default=500,
        description="Maximum number of log lines to tail from a pod container.",
    )
    AUDIT_PAGE_SIZE: int = Field(
        default=50,
        description="Default page size for paginated audit log queries.",
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance, creating it on first call."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
