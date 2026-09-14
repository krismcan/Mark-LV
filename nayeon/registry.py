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


@dataclass(frozen=True)
class CapabilityEntry:
    """Registered capability metadata plus its executable implementation."""

    capability: Capability
    implementation: object | None = None


class CapabilityRegistry:
    """Store and discover Nayeon's available capabilities."""

    def __init__(self) -> None:
        self._entries: dict[str, CapabilityEntry] = {}

    def register(
        self,
        capability: Capability,
        implementation: object | None = None,
    ) -> None:
        """Register capability metadata and its implementation."""

        if capability.name in self._entries:
            raise ValueError(
                f"Capability already registered: {capability.name}"
            )

        self._entries[capability.name] = CapabilityEntry(
            capability=capability,
            implementation=implementation,
        )

    def unregister(self, name: str) -> None:
        """Remove a capability."""

        self._entries.pop(name, None)

    def get(self, name: str) -> Capability | None:
        """Return capability metadata by name."""

        entry = self._entries.get(name)
        return entry.capability if entry else None

    def get_implementation(self, name: str) -> object | None:
        """Return the executable implementation for a capability."""

        entry = self._entries.get(name)
        return entry.implementation if entry else None

    def all(self) -> tuple[Capability, ...]:
        """Return all registered capabilities."""

        return tuple(
            entry.capability
            for entry in self._entries.values()
        )

    def find_by_service(
        self,
        service: str,
    ) -> tuple[Capability, ...]:
        """Return capabilities belonging to a service."""

        return tuple(
            entry.capability
            for entry in self._entries.values()
            if entry.capability.service == service
        )

    def find_by_mode(
        self,
        execution_mode: ExecutionMode,
    ) -> tuple[Capability, ...]:
        """Return capabilities matching an execution mode."""

        return tuple(
            entry.capability
            for entry in self._entries.values()
            if entry.capability.execution_mode == execution_mode
        )