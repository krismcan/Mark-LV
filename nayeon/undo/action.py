"""Executable undo action for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass

from nayeon.undo.service import UndoResult, UndoService


@dataclass(frozen=True)
class UndoActionResult:
    success: bool
    message: str
    undo_result: UndoResult


class UndoAction:
    """Executes the most recent registered undo operation."""

    def __init__(self, undo: UndoService) -> None:
        self._undo = undo

    def execute(self) -> UndoActionResult:
        result = self._undo.undo_last()

        return UndoActionResult(
            success=result.success,
            message=result.message,
            undo_result=result,
        )