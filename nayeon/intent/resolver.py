"""System-wide intent resolution orchestration for Nayeon."""

from __future__ import annotations

from typing import Protocol

from nayeon.intent.model import (
    IntentContext,
    IntentResolution,
    IntentSource,
)


class IntentInterpreter(Protocol):
    """Contract for any component capable of interpreting user intent."""

    def resolve(
        self,
        request: str,
        *,
        context: IntentContext,
    ) -> IntentResolution:
        ...


class IntentResolver:
    """
    Coordinates local and semantic intent understanding.

    Local deterministic understanding is preferred when confidence is high.
    Semantic reasoning is used only when the local result is missing or
    insufficiently confident.

    Neither local nor semantic interpretations are allowed through unless
    they meet their configured confidence threshold.
    """

    def __init__(
        self,
        *,
        local: IntentInterpreter,
        semantic: IntentInterpreter | None = None,
        local_confidence_threshold: float = 0.90,
        semantic_confidence_threshold: float = 0.85,
    ) -> None:
        self._validate_threshold(
            local_confidence_threshold,
            name="Local",
        )

        self._validate_threshold(
            semantic_confidence_threshold,
            name="Semantic",
        )

        self._local = local
        self._semantic = semantic
        self._local_confidence_threshold = local_confidence_threshold
        self._semantic_confidence_threshold = semantic_confidence_threshold

    def resolve(
        self,
        request: str,
        *,
        context: IntentContext,
    ) -> IntentResolution:
        local_result = self._local.resolve(
            request,
            context=context,
        )

        if (
            local_result.understood
            and local_result.confidence >= self._local_confidence_threshold
        ):
            return local_result

        if self._semantic is not None:
            semantic_result = self._semantic.resolve(
                request,
                context=context,
            )

            if (
                semantic_result.understood
                and semantic_result.confidence
                >= self._semantic_confidence_threshold
            ):
                return semantic_result

            if semantic_result.understood:
                return IntentResolution(
                    intent=None,
                    source=IntentSource.NONE,
                    confidence=0.0,
                    reason=(
                        "Semantic interpretation was below the configured "
                        "confidence threshold and was not accepted."
                    ),
                )

            return IntentResolution(
                intent=None,
                source=IntentSource.NONE,
                confidence=0.0,
                reason=(
                    "Neither local nor semantic interpretation "
                    "resolved the request safely."
                ),
            )

        return IntentResolution(
            intent=None,
            source=IntentSource.NONE,
            confidence=0.0,
            reason=(
                "Local interpretation was not confident enough and "
                "no semantic interpreter is available."
            ),
        )

    @staticmethod
    def _validate_threshold(
        value: float,
        *,
        name: str,
    ) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{name} confidence threshold must be between 0.0 and 1.0."
            )