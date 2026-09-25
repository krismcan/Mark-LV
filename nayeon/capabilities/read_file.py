"""Explicit file reads through the existing structured execution boundary only."""

from collections.abc import Mapping
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.filesystem import (
    FileReadError, FileReadFailure, FilesystemService, normalize_file_path,
)


class ReadFileCapability(CapabilityModule):
    def __init__(self, *, service: FilesystemService | None = None) -> None:
        self._service = service if service is not None else FilesystemService()

    @property
    def capability(self) -> Capability:
        return Capability(
            name="read_file", description="Read one explicit UTF-8 file (maximum 64 KiB).",
            execution_mode=ExecutionMode.LOCAL, service="filesystem",
            requires_llm=False, reversible=False, requires_confirmation=True,
        )

    def validate_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, Mapping):
            raise TypeError("File arguments must be a mapping.")
        if set(arguments) != {"path"}:
            raise ValueError("Exactly the path argument is required.")
        return {"path": normalize_file_path(arguments["path"])}

    def execute_structured(self, arguments: Mapping[str, Any]) -> object:
        return self._service.read_file(self.validate_arguments(arguments)["path"])

    def execute(self, request: str) -> object:
        raise FileReadError(FileReadFailure.STRUCTURED_REQUIRED)
