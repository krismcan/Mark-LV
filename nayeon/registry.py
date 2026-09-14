"""Capability registry for Nayeon's tools and services."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionMode(str, Enum):
    """How a capability should normally execute."""

    LOCAL = "local"
    LLM_ASSISTED = "llm_assisted"
    AGENTIC = "agentic"


@dataclass(frozen=True)
class Capability:
    """Description of a capability Nayeon can execute."""

    name: str
    description: str
    execution_mode: ExecutionMode

    service: str

    intent_patterns: tuple[str, ...] = ()
    requires_llm: bool = False
    reversible: bool = False
    requires_confirmation: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)


class CapabilityRegistry:
    """Store and discover Nayeon's available capabilities."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        """Register a capability."""

        if capability.name in self._capabilities:
            raise ValueError(
                f"Capability already registered: {capability.name}"
            )

        self._capabilities[capability.name] = capability

    def unregister(self, name: str) -> None:
        """Remove a capability."""

        self._capabilities.pop(name, None)

    def get(self, name: str) -> Capability | None:
        """Return a capability by name."""

        return self._capabilities.get(name)

    def all(self) -> tuple[Capability, ...]:
        """Return all registered capabilities."""

        return tuple(self._capabilities.values())

    def find_by_service(self, service: str) -> tuple[Capability, ...]:
        """Return capabilities belonging to a service."""

        return tuple(
            capability
            for capability in self._capabilities.values()
            if capability.service == service
        )

    def find_by_mode(
        self,
        execution_mode: ExecutionMode,
    ) -> tuple[Capability, ...]:
        """Return capabilities matching an execution mode."""

        return tuple(
            capability
            for capability in self._capabilities.values()
            if capability.execution_mode == execution_mode
        )