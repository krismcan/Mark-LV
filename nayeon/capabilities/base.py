"""Base contract for self-describing Nayeon capabilities."""

from __future__ import annotations

from abc import ABC, abstractmethod

from nayeon.registry import Capability


class CapabilityModule(ABC):
    """Base class for a self-describing Nayeon capability."""

    @property
    @abstractmethod
    def capability(self) -> Capability:
        """Return this module's capability metadata."""
        ...

    @abstractmethod
    def execute(self, request: str) -> object:
        """Execute the capability request."""
        ...