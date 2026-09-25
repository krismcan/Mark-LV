"""One explicit, bounded directory listing through structured execution only."""

from collections.abc import Mapping
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.filesystem import (
    DirectoryListError, DirectoryListFailure, FilesystemService, normalize_directory_path,
)


class ListDirectoryCapability(CapabilityModule):
    def __init__(self, *, service: FilesystemService | None = None) -> None:
        self._service = service if service is not None else FilesystemService()

    @property
    def capability(self) -> Capability:
        return Capability(
            name="list_directory", description="List one explicit directory (maximum 256 children).",
            execution_mode=ExecutionMode.LOCAL, service="filesystem",
            intent_patterns=("list directory ",), requires_llm=False,
            reversible=False, requires_confirmation=True,
        )

    def map_intent_arguments(
        self, arguments: Mapping[str, Any], *, original_request: str,
    ) -> dict[str, Any]:
        if "path" in arguments:
            return {"path": arguments["path"]}
        if arguments.get("request") == original_request:
            request = original_request.strip()
            prefix = "list directory "
            if request.lower().startswith(prefix):
                return {"path": request[len(prefix):]}
        raise ValueError("No deterministic directory mapping is available.")

    def validate_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, Mapping):
            raise TypeError("Directory arguments must be a mapping.")
        if set(arguments) != {"path"}:
            raise ValueError("Exactly the path argument is required.")
        return {"path": normalize_directory_path(arguments["path"])}

    def execute_structured(self, arguments: Mapping[str, Any]) -> object:
        return self._service.list_directory(self.validate_arguments(arguments)["path"])

    def execute(self, request: str) -> object:
        raise DirectoryListError(DirectoryListFailure.STRUCTURED_REQUIRED)
