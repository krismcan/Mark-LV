"""Core intent-understanding models for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentSource(str, Enum):
    """How Nayeon arrived at an intent interpretation."""

    LOCAL = "local"
    SEMANTIC = "semantic"
    NONE = "none"


@dataclass(frozen=True)
class IntentContext:
    """
    Runtime context that may help interpret natural language.

    This deliberately starts small. More context can be added later without
    changing the meaning of an intent itself.
    """

    pending_confirmation: bool = False
    undo_available: bool = False
    active_application: str | None = None
    recent_intent: str | None = None


@dataclass(frozen=True)
class IntentResolution:
    """
    Structured meaning extracted from a natural-language request.

    `intent` describes what the user is trying to achieve.

    `arguments` contains structured details needed to perform that intent,
    such as a file, application, destination, person, date, or query.
    """

    intent: str | None
    source: IntentSource
    confidence: float
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Intent confidence must be between 0.0 and 1.0.")

        if self.intent is not None and not self.intent.strip():
            raise ValueError("Intent name cannot be empty.")

        object.__setattr__(
            self,
            "arguments",
            dict(self.arguments),
        )

    @property
    def understood(self) -> bool:
        return self.intent is not None

    @property
    def needs_semantic_fallback(self) -> bool:
        return (
            self.intent is None
            and self.source is IntentSource.NONE
        )