"""Central undo service for reversible Nayeon actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
import uuid


UndoCallback = Callable[[], Any]


@dataclass(frozen=True)
class UndoOperation:
    operation_id: str
    capability: str
    description: str
    created_at: datetime
    callback: UndoCallback


@dataclass(frozen=True)
class UndoResult:
    success: bool
    operation_id: str | None
    capability: str | None
    message: str
    output: Any = None


class UndoService:
    """Stores and executes bounded undo operations."""

    def __init__(self, *, max_depth: int = 10) -> None:
        if max_depth <= 0:
            raise ValueError("max_depth must be greater than zero.")

        self._max_depth = max_depth
        self._stack: list[UndoOperation] = []
        self._lock = RLock()

    def register(
        self,
        *,
        capability: str,
        description: str,
        callback: UndoCallback,
    ) -> UndoOperation:
        capability = capability.strip()
        description = description.strip()

        if not capability:
            raise ValueError("Capability name is required.")

        if not description:
            raise ValueError("Undo description is required.")

        if not callable(callback):
            raise TypeError("Undo callback must be callable.")

        operation = UndoOperation(
            operation_id=str(uuid.uuid4()),
            capability=capability,
            description=description,
            created_at=datetime.now(timezone.utc),
            callback=callback,
        )

        with self._lock:
            self._stack.append(operation)

            if len(self._stack) > self._max_depth:
                self._stack.pop(0)

        return operation

    def undo_last(self) -> UndoResult:
        with self._lock:
            if not self._stack:
                return UndoResult(
                    success=False,
                    operation_id=None,
                    capability=None,
                    message="There is nothing to undo.",
                )

            operation = self._stack.pop()

        try:
            output = operation.callback()
        except Exception as exc:
            return UndoResult(
                success=False,
                operation_id=operation.operation_id,
                capability=operation.capability,
                message=f"Undo failed: {exc}",
            )

        return UndoResult(
            success=True,
            operation_id=operation.operation_id,
            capability=operation.capability,
            message=f"Undo completed for '{operation.capability}'.",
            output=output,
        )

    def peek(self) -> UndoOperation | None:
        with self._lock:
            if not self._stack:
                return None

            return self._stack[-1]

    def count(self) -> int:
        with self._lock:
            return len(self._stack)

    def clear(self) -> None:
        with self._lock:
            self._stack.clear()