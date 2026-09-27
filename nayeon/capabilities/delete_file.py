"""Permanent single-file deletion with private pre-confirmation object binding."""

from collections.abc import Mapping
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.filesystem import (
    DeleteClose, DeleteDisposition, DeleteObservation, FileDeleteError, FileDeleteResult,
    FilesystemService, _valid_deletion_binding, normalize_file_path,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class DeleteFileCapability(CapabilityModule):
    def __init__(self, *, service: FilesystemService | None = None) -> None:
        self._service = service if service is not None else FilesystemService()

    @property
    def capability(self) -> Capability:
        return Capability(
            name="delete_file", description="Permanently delete one file. Irreversible; no undo.",
            execution_mode=ExecutionMode.LOCAL, service="filesystem",
            intent_patterns=("delete file ",), requires_llm=False,
            reversible=False, requires_confirmation=True,
        )

    def map_intent_arguments(self, arguments: Mapping[str, Any], *, original_request: str) -> dict[str, Any]:
        if "_binding" in arguments:
            raise ValueError("Private deletion evidence is not caller input.")
        if "path" in arguments:
            return {"path": arguments["path"]}
        if arguments.get("request") == original_request:
            request = original_request.strip()
            prefix = "delete file "
            if request.lower().startswith(prefix):
                return {"path": request[len(prefix):].strip()}
        raise ValueError("No deterministic deletion mapping is available.")

    def validate_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        # Raw input only. Never accept a binding from a caller, including a
        # previously returned binding. The executor stores this enriched result.
        if not isinstance(arguments, Mapping):
            raise TypeError("Deletion arguments must be a mapping.")
        if set(arguments) != {"path"}:
            raise ValueError("Exactly path is required.")
        path = normalize_file_path(arguments["path"])
        try:
            binding = self._service.prepare_deletion(path)
            if not _valid_deletion_binding(binding) or binding.path != path:
                raise ValueError()
        except Exception:
            raise ValueError("Deletion preparation could not be established.") from None
        return {"path": path, "_binding": binding}

    @staticmethod
    def _validated_binding(arguments):
        if (not isinstance(arguments, Mapping) or set(arguments) != {"path", "_binding"}
                or not _valid_deletion_binding(arguments["_binding"])
                or arguments["path"] != arguments["_binding"].path):
            raise FileDeleteError()
        return arguments["_binding"]

    def execute_structured(self, arguments: Mapping[str, Any]) -> object:
        # Consume the executor's SAVED binding. Re-preparing here would authorize
        # substitution. The service compares it against the retained target.
        return self._service.delete_file(self._validated_binding(arguments))

    def execute(self, request: str) -> object:
        raise FileDeleteError()

    def verify_result(self, *, request: str | StructuredCapabilityRequest, output: Any) -> VerificationResult:
        unknown = VerificationResult(reason="Deletion outcome could not be established.")
        if not isinstance(request, StructuredCapabilityRequest) or type(output) is not FileDeleteResult:
            return unknown
        binding = self._validated_binding(request.arguments)
        if (binding != output._binding or not isinstance(output.disposition, DeleteDisposition)
                or not isinstance(output.source_close, DeleteClose)
                or not isinstance(output.observation, DeleteObservation)):
            return unknown
        if output.disposition is DeleteDisposition.NOT_ACKNOWLEDGED:
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "Deletion was not acknowledged.")
        if (output.disposition is not DeleteDisposition.ACKNOWLEDGED
                or output.source_close is not DeleteClose.COMPLETE or output._cleanup_complete is not True):
            return unknown
        if output.observation is DeleteObservation.PRESENT_SAME_IDENTITY:
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "The original file remained after the attempt.")
        if output.observation is not DeleteObservation.CONFIRMED_ABSENT:
            return unknown
        observation = self._service.observe_deleted_file(output)
        if observation is DeleteObservation.CONFIRMED_ABSENT:
            return VerificationResult(VerificationStatus.VERIFIED, "Bound deletion and target absence are confirmed.")
        if observation is DeleteObservation.PRESENT_SAME_IDENTITY:
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "The original file remains at the approved target.")
        return unknown
