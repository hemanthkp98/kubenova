"""
Ollama local LLM provider implementation.

Uses langchain-community's ChatOllama class to talk to a locally running
Ollama server. The base URL defaults to http://localhost:11434.
No API key is required.
"""

from __future__ import annotations

from loguru import logger
from langchain_core.language_models import BaseChatModel

from app.core.llm.base import LLMConfig, LLMProvider

_DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaProvider:
    """LLM provider backed by a locally running Ollama instance."""

    def __init__(self, llm_config: LLMConfig) -> None:
        self._config = llm_config
        self._model: BaseChatModel | None = None

    @property
    def config(self) -> LLMConfig:
        """Return the LLMConfig for this provider."""
        return self._config

    def get_chat_model(self) -> BaseChatModel:
        """
        Return (or lazily create) a ChatOllama instance.

        The Ollama server URL is taken from LLMConfig.base_url, falling
        back to http://localhost:11434 if not set.
        """
        if self._model is None:
            from langchain_ollama import ChatOllama  # type: ignore[import]

            base_url = self._config.base_url or _DEFAULT_OLLAMA_URL
            self._model = ChatOllama(
                model=self._config.model,
                base_url=base_url,
                temperature=self._config.temperature,
            )
            logger.info(
                "Initialised Ollama provider: model='{}' url='{}'.",
                self._config.model,
                base_url,
            )
        return self._model

    def is_available(self) -> bool:
        """
        Return True if the Ollama server responds to a health check.

        A failed check is logged as a warning but never raises.
        """
        import urllib.request
        import urllib.error

        base_url = self._config.base_url or _DEFAULT_OLLAMA_URL
        try:
            with urllib.request.urlopen(f"{base_url}/api/tags", timeout=3):
                return True
        except (urllib.error.URLError, OSError) as exc:
            logger.warning("Ollama server at '{}' is unreachable: {}", base_url, exc)
            return False


assert isinstance(OllamaProvider(LLMConfig(provider="ollama", model="llama3")), LLMProvider)
