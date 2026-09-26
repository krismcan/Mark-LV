"""Central undo service for reversible Nayeon actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
import uuid

from nayeon.undo.contract import CleanupCallback


UndoCallback = Callable[[], Any]


@dataclass(frozen=True)
class UndoOperation:
    operation_id: str
    capability: str
    description: str
    created_at: datetime
    callback: UndoCallback
    cleanup: CleanupCallback | None = field(default=None, repr=False, compare=False)


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
        self._closed = False
        self._cleanup_failures = 0

    @property
    def cleanup_failures(self) -> int:
        """Number of failed cleanup attempts; no exception/resource data retained."""
        with self._lock:
            return self._cleanup_failures

    def register(
        self,
        *,
        capability: str,
        description: str,
        callback: UndoCallback,
        cleanup: CleanupCallback | None = None,
    ) -> UndoOperation:
        """Transfer ownership at insertion; rejection leaves ownership with caller.

        Cleanup of an evicted entry cannot turn a committed registration into
        an exception. Providers must not register the same owned resource twice.
        """
        capability = capability.strip()
        description = description.strip()

        if not capability:
            raise ValueError("Capability name is required.")

        if not description:
            raise ValueError("Undo description is required.")

        if not callable(callback):
            raise TypeError("Undo callback must be callable.")

        if cleanup is not None and not callable(cleanup):
            raise TypeError("Undo cleanup must be callable or None.")

        operation = UndoOperation(
            operation_id=str(uuid.uuid4()),
            capability=capability,
            description=description,
            created_at=datetime.now(timezone.utc),
            callback=callback,
            cleanup=cleanup,
        )

        evicted = None
        with self._lock:
            if self._closed:
                raise RuntimeError("Undo service is closed.")
            # Commit point: only this service is now responsible for cleanup.
            self._stack.append(operation)

            if len(self._stack) > self._max_depth:
                evicted = self._stack.pop(0)

        if evicted is not None:
            self._cleanup(evicted)

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
        finally:
            # Popped entries are owned by this call, not clear()/close().
            self._cleanup(operation)

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
        """Discard queued entries without undoing; remain reusable until closed."""
        with self._lock:
            removed, self._stack = self._stack, []
        for operation in removed:
            self._cleanup(operation)

    def close(self) -> None:
        """Terminal, idempotent drain; does not wait for in-flight undo callbacks.

        Those calls keep their resources until their finally blocks run. Hosts
        needing complete shutdown must finish active calls as well as close().
        No callback or cleanup executes under the history lock.
        """
        with self._lock:
            self._closed = True
            removed, self._stack = self._stack, []
        for operation in removed:
            self._cleanup(operation)

    def _cleanup(self, operation: UndoOperation) -> None:
        if operation.cleanup is not None:
            try:
                operation.cleanup()
            except BaseException:
                # Even an interrupt from external cleanup cannot obscure a new
                # registration's committed ownership or skip unrelated cleanup.
                # This reports failure, not successful release; never retry an
                # arbitrary cleanup that may already have released its resource.
                with self._lock:
                    self._cleanup_failures += 1
