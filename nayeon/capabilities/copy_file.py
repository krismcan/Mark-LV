"""One bounded same-volume binary copy; no overwrite, rollback or undo."""

from collections.abc import Mapping
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.filesystem import (
    FileCopyError, FileCopyFailure, FileCopyResult, FileCreateObservation,
    FilesystemService, normalize_file_path,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class CopyFileCapability(CapabilityModule):
    def __init__(self, *, service: FilesystemService | None = None) -> None:
        self._service = service if service is not None else FilesystemService()

    @property
    def capability(self) -> Capability:
        return Capability(
            name="copy_file", description="Copy one bounded file to a new same-volume file. Irreversible; no undo.",
            execution_mode=ExecutionMode.LOCAL, service="filesystem",
            intent_patterns=("copy file ",), requires_llm=False,
            reversible=False, requires_confirmation=True,
        )

    def map_intent_arguments(self, arguments: Mapping[str, Any], *, original_request: str) -> dict[str, Any]:
        fields = ("source_path", "destination_path")
        if any(key in arguments for key in fields):
            return {key: arguments[key] for key in fields if key in arguments}
        if arguments.get("request") == original_request:
            request = original_request.strip()
            prefix = "copy file "
            if request.lower().startswith(prefix):
                source, separator, destination = request[len(prefix):].partition("::")
                if separator and "::" not in destination and source.strip() and destination.strip():
                    return {"source_path": source.strip(), "destination_path": destination.strip()}
        raise ValueError("No deterministic file-copy mapping is available.")

    def validate_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, Mapping):
            raise TypeError("Copy arguments must be a mapping.")
        if set(arguments) != {"source_path", "destination_path"}:
            raise ValueError("Exactly source_path and destination_path are required.")
        source = normalize_file_path(arguments["source_path"])
        destination = normalize_file_path(arguments["destination_path"])
        if source.casefold() == destination.casefold():
            raise ValueError("Self-copy is not supported.")
        return {"source_path": source, "destination_path": destination}

    def execute_structured(self, arguments: Mapping[str, Any]) -> object:
        validated = self.validate_arguments(arguments)
        return self._service.copy_file(validated["source_path"], validated["destination_path"])

    def execute(self, request: str) -> object:
        raise FileCopyError(FileCopyFailure.STRUCTURED_REQUIRED)

    def verify_result(self, *, request: str | StructuredCapabilityRequest, output: Any) -> VerificationResult:
        if not isinstance(request, StructuredCapabilityRequest) or not isinstance(output, FileCopyResult):
            return VerificationResult(reason="Copy evidence is unavailable.")
        arguments = self.validate_arguments(request.arguments)
        if (arguments["source_path"] != output.source_path
                or arguments["destination_path"] != output.destination_path):
            return VerificationResult(reason="Copy evidence is unavailable.")
        observation = self._service.observe_copied_file(output)
        if observation is FileCreateObservation.MATCHED:
            return VerificationResult(VerificationStatus.VERIFIED, "Destination matches the execution-time copy evidence.")
        if observation is FileCreateObservation.CHANGED:
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "Requested copy result is contradicted.")
        return VerificationResult(reason="Requested copy result could not be established.")
