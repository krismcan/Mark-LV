"""Exact empty arguments and historical pointer-snapshot verification."""
from collections.abc import Mapping

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.pointer_observation import (
    PointerObservationService, PointerObservation, PointerState, PointerReason,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class ObservePointerCapability(CapabilityModule):
    PHRASE = "inspect current pointer"

    def __init__(self, *, service=None):
        self._service = service if service is not None else PointerObservationService()

    @property
    def capability(self):
        return Capability(
            name="observe_pointer", description="Observe one bounded pointer snapshot.",
            execution_mode=ExecutionMode.LOCAL, service="computer_control",
            intent_patterns=(self.PHRASE,), requires_llm=False,
            reversible=False, requires_confirmation=False,
        )

    def map_intent_arguments(self, arguments, *, original_request):
        if not isinstance(arguments, Mapping):
            raise TypeError("Observation arguments must be a mapping.")
        if not arguments:
            return {}
        if (set(arguments) == {"request"} and arguments["request"] == original_request
                and isinstance(original_request, str)
                and original_request.strip().lower() == self.PHRASE):
            return {}
        raise ValueError("No exact pointer observation mapping is available.")

    def validate_arguments(self, arguments):
        if not isinstance(arguments, Mapping):
            raise TypeError("Observation arguments must be a mapping.")
        if arguments:
            raise ValueError("Pointer observation requires exactly empty arguments.")
        return {}

    def execute_structured(self, arguments):
        self.validate_arguments(arguments)
        return self._service.observe_pointer()

    def execute(self, request):
        raise ValueError("Pointer observation requires structured execution.")

    def verify_result(self, *, request, output):
        unknown = VerificationResult(reason="Bounded pointer evidence is inconclusive.")
        if not isinstance(request, StructuredCapabilityRequest) or request.arguments:
            return unknown
        if (type(output) is not PointerObservation or output.state is not PointerState.OBSERVED
                or output.reason is not PointerReason.CONSISTENT):
            return unknown
        evidence = output._evidence
        if evidence is None or not evidence.complete() or not evidence.early.root or not evidence.late.root:
            return unknown
        if not evidence.consistent():
            return VerificationResult(VerificationStatus.NOT_VERIFIED,
                                      "Bounded pointer evidence contradicts the observation claim.")
        return VerificationResult(VerificationStatus.VERIFIED,
                                  "Bounded pointer snapshot is internally consistent.")
