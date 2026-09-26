"""One new empty file; explicitly irreversible, protected by confirmation."""

from collections.abc import Mapping
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.filesystem import (
    FileCreateError, FileCreateFailure, FileCreateObservation, FileCreateResult,
    FilesystemService, normalize_file_path,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class CreateFileCapability(CapabilityModule):
    def __init__(self, *, service: FilesystemService | None = None) -> None:
        self._service = service if service is not None else FilesystemService()

    @property
    def capability(self) -> Capability:
        return Capability(
            name="create_file", description="Create one new empty file. Irreversible; no undo.",
            execution_mode=ExecutionMode.LOCAL, service="filesystem",
            intent_patterns=("create empty file ",), requires_llm=False,
            reversible=False, requires_confirmation=True,
        )

    def map_intent_arguments(self, arguments: Mapping[str, Any], *, original_request: str) -> dict[str, Any]:
        if "path" in arguments:
            return {"path": arguments["path"]}
        if arguments.get("request") == original_request:
            request = original_request.strip()
            prefix = "create empty file "
            if request.lower().startswith(prefix):
                return {"path": request[len(prefix):]}
        raise ValueError("No deterministic empty-file mapping is available.")

    def validate_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, Mapping):
            raise TypeError("Creation arguments must be a mapping.")
        if set(arguments) != {"path"}:
            raise ValueError("Exactly the path argument is required.")
        return {"path": normalize_file_path(arguments["path"])}

    def execute_structured(self, arguments: Mapping[str, Any]) -> object:
        return self._service.create_empty_file(self.validate_arguments(arguments)["path"])

    def execute(self, request: str) -> object:
        raise FileCreateError(FileCreateFailure.STRUCTURED_REQUIRED)

    def verify_result(self, *, request: str | StructuredCapabilityRequest, output: Any) -> VerificationResult:
        if (not isinstance(request, StructuredCapabilityRequest) or not isinstance(output, FileCreateResult)
                or self.validate_arguments(request.arguments)["path"] != output.path):
            return VerificationResult(reason="Creation evidence is unavailable.")
        observation = self._service.observe_created_file(output)
        if observation is FileCreateObservation.MATCHED:
            return VerificationResult(VerificationStatus.VERIFIED, "Created empty-file identity and state match.")
        if observation is FileCreateObservation.CHANGED:
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "Created empty-file state no longer matches.")
        return VerificationResult(reason="Created empty-file state could not be established.")
