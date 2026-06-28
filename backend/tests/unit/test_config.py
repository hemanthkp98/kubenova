"""
Unit tests for app.config.Settings.

Verifies that settings load from environment variables and that defaults
are correct without requiring a real .env file.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.config import Settings, get_settings


class TestSettingsDefaults:
    """Test that all default values are correct."""

    def test_default_env(self) -> None:
        """KUBENOVA_ENV defaults to 'development'."""
        s = Settings()
        assert s.KUBENOVA_ENV == "development"

    def test_default_llm_provider(self) -> None:
        """LLM_PROVIDER defaults to 'anthropic'."""
        s = Settings()
        assert s.LLM_PROVIDER == "anthropic"

    def test_default_llm_model(self) -> None:
        """LLM_MODEL defaults to claude-sonnet-4-6."""
        s = Settings()
        assert s.LLM_MODEL == "claude-sonnet-4-6"

    def test_default_audit_page_size(self) -> None:
        """AUDIT_PAGE_SIZE defaults to 50."""
        s = Settings()
        assert s.AUDIT_PAGE_SIZE == 50

    def test_default_max_log_lines(self) -> None:
        """MAX_LOG_LINES defaults to 500."""
        s = Settings()
        assert s.MAX_LOG_LINES == 500

    def test_default_database_url(self) -> None:
        """Default database URL is sqlite+aiosqlite."""
        s = Settings()
        assert "sqlite+aiosqlite" in s.KUBENOVA_DATABASE_URL

    def test_default_cors_origins(self) -> None:
        """Default CORS allows the Vite dev server."""
        s = Settings()
        assert "http://localhost:5173" in s.KUBENOVA_CORS_ORIGINS

    def test_default_api_key_none(self) -> None:
        """LLM_API_KEY is None by default."""
        s = Settings()
        assert s.LLM_API_KEY is None


class TestSettingsFromEnv:
    """Test environment variable override."""

    def test_env_override_provider(self) -> None:
        """LLM_PROVIDER can be overridden via environment."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}):
            s = Settings()
            assert s.LLM_PROVIDER == "openai"

    def test_env_override_api_key(self) -> None:
        """LLM_API_KEY is read from environment."""
        with patch.dict(os.environ, {"LLM_API_KEY": "sk-test-key"}):
            s = Settings()
            assert s.LLM_API_KEY == "sk-test-key"

    def test_env_override_log_level(self) -> None:
        """KUBENOVA_LOG_LEVEL can be changed."""
        with patch.dict(os.environ, {"KUBENOVA_LOG_LEVEL": "DEBUG"}):
            s = Settings()
            assert s.KUBENOVA_LOG_LEVEL == "DEBUG"

    def test_env_override_ollama_url(self) -> None:
        """LLM_BASE_URL is used for Ollama."""
        url = "http://ollama.local:11434"
        with patch.dict(os.environ, {"LLM_BASE_URL": url}):
            s = Settings()
            assert s.LLM_BASE_URL == url

    def test_production_env_valid(self) -> None:
        """KUBENOVA_ENV accepts 'production'."""
        with patch.dict(os.environ, {"KUBENOVA_ENV": "production"}):
            s = Settings()
            assert s.KUBENOVA_ENV == "production"


class TestGetSettings:
    """Test the singleton get_settings() helper."""

    def test_returns_same_instance(self) -> None:
        """get_settings() returns the same object on repeated calls."""
        # Reset singleton first.
        import app.config as cfg
        cfg._settings = None
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_is_settings_instance(self) -> None:
        """get_settings() returns a Settings instance."""
        import app.config as cfg
        cfg._settings = None
        assert isinstance(get_settings(), Settings)
