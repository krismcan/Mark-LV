"""Routed undo capability for Nayeon."""

from __future__ import annotations

from nayeon.capabilities.base import CapabilityModule
from nayeon.registry import Capability, ExecutionMode
from nayeon.undo.action import UndoAction, UndoActionResult


class UndoCapability(CapabilityModule):
    """Exposes the shared undo action as a routable capability."""

    def __init__(self, action: UndoAction) -> None:
        self._action = action

    @property
    def capability(self) -> Capability:
        return Capability(
            name="undo_last",
            description="Undo the most recent reversible action.",
            execution_mode=ExecutionMode.LOCAL,
            service="undo",
            intent_patterns=(
                "undo",
                "undo that",
                "undo it",
                "revert that",
                "revert it",
                "put it back",
                "change it back",
                "reverse that",
            ),
            requires_llm=False,
            reversible=False,
            requires_confirmation=False,
        )

    def execute(self, request: str) -> UndoActionResult:
        return self._action.execute()