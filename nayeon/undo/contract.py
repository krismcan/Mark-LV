"""Undo contract for reversible Nayeon capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable


UndoCallback = Callable[[], Any]
CleanupCallback = Callable[[], None]


@dataclass(frozen=True)
class UndoRegistration:
    """Describes how a successfully executed action can be reversed."""

    description: str
    callback: UndoCallback
    cleanup: CleanupCallback | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Undo description is required.")

        if not callable(self.callback):
            raise TypeError("Undo callback must be callable.")

        if self.cleanup is not None and not callable(self.cleanup):
            raise TypeError("Undo cleanup must be callable or None.")


@runtime_checkable
class UndoProvider(Protocol):
    """Implemented by capabilities that can provide a real undo operation."""

    def build_undo(
        self,
        request: str,
        output: Any,
    ) -> UndoRegistration:
        ...


@runtime_checkable
class UnregisteredResourceProvider(Protocol):
    """Optional cleanup for returned output not transferred into undo history.

    The provider owns failures before execution returns. After return, the
    executor invokes this hook once on exit unless undo registration committed.
    Implementations release resources only, never retry or undo the action.
    """

    def release_unregistered_resources(self, *, output: Any) -> None:
        ...
