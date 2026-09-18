"""Validated intent-to-capability dispatch planning for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from nayeon.intent.model import IntentResolution
from nayeon.registry import Capability, CapabilityRegistry


class DispatchKind(str, Enum):
    CAPABILITY = "capability"
    SYSTEM_CONTROL = "system_control"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class DispatchPlan:
    """Trusted plan produced from an already-resolved user intent."""

    kind: DispatchKind
    intent: str | None
    capability: Capability | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "arguments",
            dict(self.arguments),
        )

    @property
    def ready(self) -> bool:
        return self.kind is not DispatchKind.UNRESOLVED


class IntentDispatcher:
    """
    Converts validated IntentResolution objects into trusted dispatch plans.

    This layer does not execute anything.
    """

    _SYSTEM_CONTROLS = {
        "cancel_pending",
        "undo_last",
    }

    def __init__(
        self,
        *,
        registry: CapabilityRegistry,
    ) -> None:
        self._registry = registry

    def plan(
        self,
        resolution: IntentResolution,
    ) -> DispatchPlan:
        if not resolution.understood or resolution.intent is None:
            return DispatchPlan(
                kind=DispatchKind.UNRESOLVED,
                intent=None,
                reason=(
                    resolution.reason
                    or "No resolved intent is available for dispatch."
                ),
            )

        intent = resolution.intent.strip()

        if intent in self._SYSTEM_CONTROLS:
            return DispatchPlan(
                kind=DispatchKind.SYSTEM_CONTROL,
                intent=intent,
                arguments=resolution.arguments,
                reason="Resolved to an approved system control.",
            )

        capability = self._registry.get(intent)

        if capability is None:
            return DispatchPlan(
                kind=DispatchKind.UNRESOLVED,
                intent=intent,
                arguments=resolution.arguments,
                reason=(
                    f"Resolved intent '{intent}' does not map to a "
                    "registered capability."
                ),
            )

        return DispatchPlan(
            kind=DispatchKind.CAPABILITY,
            intent=intent,
            capability=capability,
            arguments=resolution.arguments,
            reason="Resolved intent mapped to a registered capability.",
        )