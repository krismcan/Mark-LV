"""One irreversible new UTF-8 file; committed creation is not verified content."""

from collections.abc import Mapping
import json
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.filesystem import (
    FileCreateObservation, FilesystemService, TextFileCreateError,
    TextFileCreateFailure, TextFileCreateResult, encode_creation_text, normalize_file_path,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class CreateTextFileCapability(CapabilityModule):
    def __init__(self, *, service: FilesystemService | None = None) -> None:
        self._service = service if service is not None else FilesystemService()

    @property
    def capability(self) -> Capability:
        return Capability(
            name="create_text_file", description="Create one new UTF-8 text file. Irreversible; no undo.",
            execution_mode=ExecutionMode.LOCAL, service="filesystem",
            intent_patterns=("create text file ",), requires_llm=False,
            reversible=False, requires_confirmation=True,
        )

    def map_intent_arguments(self, arguments: Mapping[str, Any], *, original_request: str) -> dict[str, Any]:
        if "path" in arguments or "text" in arguments:
            # Missing/malformed explicit values are never repaired from prose.
            return {key: arguments[key] for key in ("path", "text") if key in arguments}
        if arguments.get("request") == original_request:
            request = original_request.strip()
            prefix = "create text file "
            if request.lower().startswith(prefix):
                path, separator, suffix = request[len(prefix):].partition(" :: ")
                if separator:
                    try:
                        text = json.loads(suffix)
                    except (ValueError, TypeError):
                        raise ValueError("A JSON text string is required.") from None
                    if isinstance(text, str):
                        return {"path": path, "text": text}
        raise ValueError("No deterministic text-file mapping is available.")

    def validate_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, Mapping):
            raise TypeError("Text creation arguments must be a mapping.")
        if set(arguments) != {"path", "text"}:
            raise ValueError("Exactly path and text are required.")
        path = normalize_file_path(arguments["path"])
        encode_creation_text(arguments["text"])
        return {"path": path, "text": arguments["text"]}

    def execute_structured(self, arguments: Mapping[str, Any]) -> object:
        validated = self.validate_arguments(arguments)
        return self._service.create_text_file(validated["path"], validated["text"])

    def execute(self, request: str) -> object:
        raise TextFileCreateError(TextFileCreateFailure.STRUCTURED_REQUIRED)

    def verify_result(self, *, request: str | StructuredCapabilityRequest, output: Any) -> VerificationResult:
        if not isinstance(request, StructuredCapabilityRequest) or not isinstance(output, TextFileCreateResult):
            return VerificationResult(reason="Text creation evidence is unavailable.")
        arguments = self.validate_arguments(request.arguments)
        if arguments["path"] != output.path:
            return VerificationResult(reason="Text creation evidence is unavailable.")
        observation = self._service.observe_created_text_file(output, arguments["text"])
        if observation is FileCreateObservation.MATCHED:
            return VerificationResult(VerificationStatus.VERIFIED, "Created file identity and exact text match.")
        if observation is FileCreateObservation.CHANGED:
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "Requested text-file state is contradicted.")
        return VerificationResult(reason="Requested text-file state could not be established.")
