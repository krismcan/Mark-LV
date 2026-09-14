"""Nayeon AI service abstraction.

The rest of Nayeon talks to this service instead of calling a model
provider directly.

Provider-specific implementations will be added later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class AIMessage:
    """A single message exchanged with an AI provider."""

    role: str
    content: str


@dataclass(frozen=True)
class AIResponse:
    """Normalized response returned by the AI service."""

    text: str
    provider: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)


class AIProvider(Protocol):
    """Interface that every Nayeon AI provider must implement."""

    @property
    def name(self) -> str:
        """Return the provider name."""
        ...

    @property
    def model(self) -> str:
        """Return the active model name."""
        ...

    def generate(
        self,
        messages: list[AIMessage],
        *,
        system_prompt: str | None = None,
    ) -> AIResponse:
        """Generate a response from the provider."""
        ...


class AIService:
    """Provider-independent entry point for Nayeon's AI capabilities."""

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        """Return the active provider name."""

        return self._provider.name

    @property
    def model_name(self) -> str:
        """Return the active model name."""

        return self._provider.model

    def generate(
        self,
        messages: list[AIMessage],
        *,
        system_prompt: str | None = None,
    ) -> AIResponse:
        """Generate a response through the configured provider."""

        if not messages:
            raise ValueError("At least one message is required.")

        return self._provider.generate(
            messages,
            system_prompt=system_prompt,
        )