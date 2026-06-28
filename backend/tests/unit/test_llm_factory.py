"""
Unit tests for app.core.llm.factory.

Verifies that get_llm_provider() returns the correct provider class
for each configured provider name, and that caching works correctly.
"""

from __future__ import annotations

import pytest

from app.core.llm.base import LLMConfig
from app.core.llm.factory import clear_provider_cache, get_llm_provider


class TestGetLlmProvider:
    """Tests for the LLM provider factory."""

    def setup_method(self) -> None:
        """Clear provider cache before each test."""
        clear_provider_cache()

    def test_returns_anthropic_provider(self) -> None:
        """Factory returns AnthropicProvider for provider='anthropic'."""
        from app.core.llm.anthropic_provider import AnthropicProvider
        config = LLMConfig(provider="anthropic", model="claude-sonnet-4-6", api_key="test")
        provider = get_llm_provider(config)
        assert isinstance(provider, AnthropicProvider)

    def test_returns_openai_provider(self) -> None:
        """Factory returns OpenAIProvider for provider='openai'."""
        from app.core.llm.openai_provider import OpenAIProvider
        config = LLMConfig(provider="openai", model="gpt-4o", api_key="test")
        provider = get_llm_provider(config)
        assert isinstance(provider, OpenAIProvider)

    def test_returns_ollama_provider(self) -> None:
        """Factory returns OllamaProvider for provider='ollama'."""
        from app.core.llm.ollama_provider import OllamaProvider
        config = LLMConfig(provider="ollama", model="llama3")
        provider = get_llm_provider(config)
        assert isinstance(provider, OllamaProvider)

    def test_unknown_provider_raises(self) -> None:
        """Unknown provider name raises ValueError."""
        config = LLMConfig(provider="unknown_provider", model="model")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider(config)

    def test_same_provider_cached(self) -> None:
        """Same provider+model returns the same instance."""
        config = LLMConfig(provider="anthropic", model="claude-sonnet-4-6", api_key="test")
        p1 = get_llm_provider(config)
        p2 = get_llm_provider(config)
        assert p1 is p2

    def test_different_models_not_cached(self) -> None:
        """Different model names result in different provider instances."""
        c1 = LLMConfig(provider="anthropic", model="claude-sonnet-4-6", api_key="test")
        c2 = LLMConfig(provider="anthropic", model="claude-opus-4-6", api_key="test")
        p1 = get_llm_provider(c1)
        p2 = get_llm_provider(c2)
        assert p1 is not p2

    def test_clear_cache_invalidates_singleton(self) -> None:
        """clear_provider_cache() causes a new instance to be returned."""
        config = LLMConfig(provider="anthropic", model="claude-sonnet-4-6", api_key="test")
        p1 = get_llm_provider(config)
        clear_provider_cache()
        p2 = get_llm_provider(config)
        assert p1 is not p2

    def test_anthropic_is_unavailable_without_key(self) -> None:
        """AnthropicProvider.is_available() returns False without an API key."""
        config = LLMConfig(provider="anthropic", model="claude-sonnet-4-6", api_key=None)
        provider = get_llm_provider(config)
        assert provider.is_available() is False
