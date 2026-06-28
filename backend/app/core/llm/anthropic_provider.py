"""
Anthropic Claude LLM provider implementation.

Uses langchain-anthropic's ChatAnthropic class. The API key is read from
LLMConfig and never stored in the audit log or database.
"""

from __future__ import annotations

from loguru import logger
from langchain_core.language_models import BaseChatModel

from app.core.llm.base import LLMConfig, LLMProvider


class AnthropicProvider:
    """LLM provider backed by Anthropic's Claude models."""

    def __init__(self, llm_config: LLMConfig) -> None:
        self._config = llm_config
        self._model: BaseChatModel | None = None

    @property
    def config(self) -> LLMConfig:
        """Return the LLMConfig for this provider."""
        return self._config

    def get_chat_model(self) -> BaseChatModel:
        """
        Return (or lazily create) a ChatAnthropic instance.

        The model is cached after first creation so the same instance is
        reused within a process lifecycle.
        """
        if self._model is None:
            from langchain_anthropic import ChatAnthropic  # type: ignore[import]

            self._model = ChatAnthropic(  # type: ignore[call-arg]
                model=self._config.model,
                anthropic_api_key=self._config.api_key,  # type: ignore[arg-type]
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )
            logger.info("Initialised Anthropic provider with model '{}'.", self._config.model)
        return self._model

    def is_available(self) -> bool:
        """Return True if an API key is configured."""
        available = bool(self._config.api_key)
        if not available:
            logger.warning("Anthropic provider: LLM_API_KEY is not set.")
        return available


# Verify the class satisfies the protocol at import time.
assert isinstance(AnthropicProvider(LLMConfig(provider="anthropic", model="claude-sonnet-4-6")), LLMProvider)
