"""Capability-owned empty argument mapping and historical snapshot verification."""
from collections.abc import Mapping

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.computer_control import (
    ComputerControlService, ForegroundObservation, ForegroundState,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class ObserveForegroundWindowCapability(CapabilityModule):
    PHRASE = "inspect foreground window"

    def __init__(self, *, service=None):
        self._service = service if service is not None else ComputerControlService()

    @property
    def capability(self):
        return Capability(
            name="observe_foreground_window", description="Observe one bounded foreground snapshot.",
            execution_mode=ExecutionMode.LOCAL, service="computer_control",
            intent_patterns=(self.PHRASE,), requires_llm=False,
            reversible=False, requires_confirmation=False,
        )

    def map_intent_arguments(self, arguments, *, original_request):
        if not isinstance(arguments, Mapping):
            raise TypeError("Observation arguments must be a mapping.")
        if not arguments:  # Explicit structured empty arguments are authoritative.
            return {}
        if (set(arguments) == {"request"} and arguments["request"] == original_request
                and isinstance(original_request, str)
                and original_request.strip().lower() == self.PHRASE):
            return {}
        raise ValueError("No exact foreground observation mapping is available.")

    def validate_arguments(self, arguments):
        if not isinstance(arguments, Mapping):
            raise TypeError("Observation arguments must be a mapping.")
        if arguments:
            raise ValueError("Foreground observation requires exactly empty arguments.")
        return {}

    def execute_structured(self, arguments):
        self.validate_arguments(arguments)
        return self._service.observe_foreground_window()

    def execute(self, request):
        raise ValueError("Foreground observation requires structured execution.")

    def verify_result(self, *, request, output):
        unknown = VerificationResult(reason="Bounded foreground evidence is inconclusive.")
        if not isinstance(request, StructuredCapabilityRequest) or request.arguments:
            return unknown
        if type(output) is not ForegroundObservation or output.state is not ForegroundState.OBSERVED:
            return unknown
        evidence = output._evidence
        if evidence is None or not evidence.complete():
            return unknown
        if not evidence.consistent():
            return VerificationResult(VerificationStatus.NOT_VERIFIED,
                                      "Bounded foreground evidence contradicts the observation claim.")
        return VerificationResult(VerificationStatus.VERIFIED,
                                  "Bounded foreground snapshot is internally consistent.")
