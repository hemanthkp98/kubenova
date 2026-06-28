"""
Abstract LLM provider protocol and shared configuration dataclass.

Every concrete provider must implement the LLMProvider protocol so the
LangGraph agent can be written against a single interface regardless of
which backend is configured.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from langchain_core.language_models import BaseChatModel


@dataclass
class LLMConfig:
    """Configuration for a specific LLM provider instance."""

    provider: str  # "anthropic" | "openai" | "ollama"
    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    extra: dict[str, object] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol that all LLM provider implementations must satisfy."""

    @property
    def config(self) -> LLMConfig:
        """Return the configuration used to create this provider."""
        ...

    def get_chat_model(self) -> BaseChatModel:
        """
        Return a LangChain-compatible chat model instance.

        The returned model is used directly by LangGraph nodes. Implementations
        must bind any tool lists separately via model.bind_tools() at the call site.
        """
        ...

    def is_available(self) -> bool:
        """
        Check whether the provider can be reached.

        Returns True if the provider endpoint is reachable and credentials
        are present; False otherwise. Should not raise.
        """
        ...
