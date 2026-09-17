"""Semantic intent interpretation for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from nayeon.intent.model import (
    IntentContext,
    IntentResolution,
    IntentSource,
)
from nayeon.registry import CapabilityRegistry


@dataclass(frozen=True)
class SemanticModelResult:
    """
    Raw structured interpretation returned by a semantic model.

    This is NOT trusted yet. SemanticIntentInterpreter validates it before
    converting it into an IntentResolution.
    """

    intent: str | None
    confidence: float
    arguments: dict[str, Any]
    reason: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Semantic model confidence must be between 0.0 and 1.0."
            )

        if self.intent is not None and not self.intent.strip():
            raise ValueError("Semantic model intent cannot be empty.")

        object.__setattr__(
            self,
            "arguments",
            dict(self.arguments),
        )


class SemanticModel(Protocol):
    """Contract for the AI component that interprets natural language."""

    def interpret(
        self,
        request: str,
        *,
        context: IntentContext,
        allowed_intents: tuple[str, ...],
    ) -> SemanticModelResult:
        ...


class SemanticIntentInterpreter:
    """
    Converts AI semantic interpretation into a validated IntentResolution.

    The model may only select intents that are explicitly allowed by the
    current capability registry, plus approved system-level control intents.
    """

    _SYSTEM_INTENTS = {
        "cancel_pending",
        "undo_last",
    }

    def __init__(
        self,
        *,
        model: SemanticModel,
        registry: CapabilityRegistry,
    ) -> None:
        self._model = model
        self._registry = registry

    def resolve(
        self,
        request: str,
        *,
        context: IntentContext,
    ) -> IntentResolution:
        allowed_intents = self._allowed_intents()

        result = self._model.interpret(
            request,
            context=context,
            allowed_intents=allowed_intents,
        )

        if result.intent is None:
            return IntentResolution(
                intent=None,
                source=IntentSource.NONE,
                confidence=0.0,
                reason=result.reason or (
                    "Semantic interpretation could not determine "
                    "a supported intent."
                ),
            )

        normalized_intent = result.intent.strip()

        if normalized_intent not in allowed_intents:
            return IntentResolution(
                intent=None,
                source=IntentSource.NONE,
                confidence=0.0,
                reason=(
                    "Semantic interpretation produced an intent that "
                    "is not currently supported."
                ),
            )

        return IntentResolution(
            intent=normalized_intent,
            source=IntentSource.SEMANTIC,
            confidence=result.confidence,
            arguments=result.arguments,
            reason=result.reason,
        )

    def _allowed_intents(self) -> tuple[str, ...]:
        registered = {
            capability.name
            for capability in self._registry.all()
        }

        return tuple(
            sorted(
                registered | self._SYSTEM_INTENTS
            )
        )