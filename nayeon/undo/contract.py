"""Undo contract for reversible Nayeon capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol, runtime_checkable


UndoCallback = Callable[[], Any]


@dataclass(frozen=True)
class UndoRegistration:
    """Describes how a successfully executed action can be reversed."""

    description: str
    callback: UndoCallback

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Undo description is required.")

        if not callable(self.callback):
            raise TypeError("Undo callback must be callable.")


@runtime_checkable
class UndoProvider(Protocol):
    """Implemented by capabilities that can provide a real undo operation."""

    def build_undo(
        self,
        request: str,
        output: Any,
    ) -> UndoRegistration:
        ...