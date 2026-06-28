"""
OpenAI LLM provider implementation.

Uses langchain-openai's ChatOpenAI class. Supports custom base URLs for
Azure OpenAI or self-hosted OpenAI-compatible endpoints.
"""

from __future__ import annotations

from loguru import logger
from langchain_core.language_models import BaseChatModel

from app.core.llm.base import LLMConfig, LLMProvider


class OpenAIProvider:
    """LLM provider backed by OpenAI or OpenAI-compatible APIs."""

    def __init__(self, llm_config: LLMConfig) -> None:
        self._config = llm_config
        self._model: BaseChatModel | None = None

    @property
    def config(self) -> LLMConfig:
        """Return the LLMConfig for this provider."""
        return self._config

    def get_chat_model(self) -> BaseChatModel:
        """
        Return (or lazily create) a ChatOpenAI instance.

        If LLMConfig.base_url is set, it is forwarded to ChatOpenAI so that
        Azure or local OpenAI-compatible endpoints are supported.
        """
        if self._model is None:
            from langchain_openai import ChatOpenAI  # type: ignore[import]

            kwargs: dict[str, object] = {
                "model": self._config.model,
                "openai_api_key": self._config.api_key,
                "temperature": self._config.temperature,
                "max_tokens": self._config.max_tokens,
            }
            if self._config.base_url:
                kwargs["openai_api_base"] = self._config.base_url

            self._model = ChatOpenAI(**kwargs)  # type: ignore[arg-type]
            logger.info("Initialised OpenAI provider with model '{}'.", self._config.model)
        return self._model

    def is_available(self) -> bool:
        """Return True if an API key is configured."""
        available = bool(self._config.api_key)
        if not available:
            logger.warning("OpenAI provider: LLM_API_KEY is not set.")
        return available


assert isinstance(OpenAIProvider(LLMConfig(provider="openai", model="gpt-4o")), LLMProvider)
