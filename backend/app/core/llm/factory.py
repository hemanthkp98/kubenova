"""
LLM provider factory.

`get_llm_provider()` is the single entry point for obtaining an LLMProvider
instance. It reads from LLMConfig (or the global Settings) and returns the
appropriate concrete implementation.

To add a new provider:
1. Implement the LLMProvider protocol in a new module under core/llm/
2. Add a case to the _PROVIDERS dict below.
"""

from __future__ import annotations

from loguru import logger

from app.config import get_settings
from app.core.llm.base import LLMConfig, LLMProvider

_provider_cache: dict[str, LLMProvider] = {}


def _build_config_from_settings() -> LLMConfig:
    """Create an LLMConfig from the global application settings."""
    settings = get_settings()
    return LLMConfig(
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )


def get_llm_provider(config: LLMConfig | None = None) -> LLMProvider:
    """
    Return the LLMProvider for the given configuration.

    Results are cached by (provider, model) so the same instance is
    reused across requests. Pass a fresh LLMConfig to override caching
    (e.g. when the user supplies a per-session API key from the frontend).

    Args:
        config: Optional LLMConfig. If None, reads from global Settings.

    Returns:
        An LLMProvider instance ready to call get_chat_model() on.

    Raises:
        ValueError: If the provider name is not recognised.
    """
    if config is None:
        config = _build_config_from_settings()

    cache_key = f"{config.provider}:{config.model}"
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]

    provider = _create_provider(config)
    _provider_cache[cache_key] = provider
    logger.info("Created LLM provider '{}' for model '{}'.", config.provider, config.model)
    return provider


def _create_provider(config: LLMConfig) -> LLMProvider:
    """Instantiate the concrete LLMProvider for the given config."""
    name = config.provider.lower()
    if name == "anthropic":
        from app.core.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(config)
    if name == "openai":
        from app.core.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(config)
    if name == "ollama":
        from app.core.llm.ollama_provider import OllamaProvider
        return OllamaProvider(config)
    raise ValueError(
        f"Unknown LLM provider: '{config.provider}'. "
        "Supported values: anthropic, openai, ollama."
    )


def clear_provider_cache() -> None:
    """Invalidate all cached provider instances — useful in tests."""
    _provider_cache.clear()
