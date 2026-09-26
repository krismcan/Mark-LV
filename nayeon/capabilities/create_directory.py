"""Create one directory with an existing parent; irreversible and confirmed."""

from collections.abc import Mapping
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.filesystem import (
    DirectoryCreateError, DirectoryCreateFailure, DirectoryCreateObservation,
    DirectoryCreateResult, FilesystemService, normalize_file_path,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class CreateDirectoryCapability(CapabilityModule):
    def __init__(self, *, service: FilesystemService | None = None) -> None:
        self._service = service if service is not None else FilesystemService()

    @property
    def capability(self) -> Capability:
        return Capability(
            name="create_directory", description="Create one new directory. Irreversible; no undo.",
            execution_mode=ExecutionMode.LOCAL, service="filesystem",
            intent_patterns=("create directory ",), requires_llm=False,
            reversible=False, requires_confirmation=True,
        )

    def map_intent_arguments(self, arguments: Mapping[str, Any], *, original_request: str) -> dict[str, Any]:
        if "path" in arguments:
            return {"path": arguments["path"]}
        if arguments.get("request") == original_request:
            request = original_request.strip()
            prefix = "create directory "
            if request.lower().startswith(prefix):
                return {"path": request[len(prefix):]}
        raise ValueError("No deterministic directory-creation mapping is available.")

    def validate_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, Mapping):
            raise TypeError("Directory creation arguments must be a mapping.")
        if set(arguments) != {"path"}:
            raise ValueError("Exactly the path argument is required.")
        return {"path": normalize_file_path(arguments["path"])}

    def execute_structured(self, arguments: Mapping[str, Any]) -> object:
        return self._service.create_directory(self.validate_arguments(arguments)["path"])

    def execute(self, request: str) -> object:
        raise DirectoryCreateError(DirectoryCreateFailure.STRUCTURED_REQUIRED)

    def verify_result(self, *, request: str | StructuredCapabilityRequest, output: Any) -> VerificationResult:
        if (not isinstance(request, StructuredCapabilityRequest) or not isinstance(output, DirectoryCreateResult)
                or self.validate_arguments(request.arguments)["path"] != output.path):
            return VerificationResult(reason="Directory creation evidence is unavailable.")
        observation = self._service.observe_created_directory(output)
        if observation is DirectoryCreateObservation.CONTRADICTED:
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "Expected directory state is contradicted.")
        if observation is DirectoryCreateObservation.PRESENT:
            return VerificationResult(reason="A safe directory was observed; exact created-object continuity is unproven.")
        return VerificationResult(reason="Created directory state could not be established.")
