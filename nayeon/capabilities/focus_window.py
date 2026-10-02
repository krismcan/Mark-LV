"""Focus the foreground target captured during this action's preparation."""
from collections.abc import Mapping
from copy import deepcopy

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.window_focus import (
    FocusState, WindowFocusResult, WindowFocusService, _valid_focus_binding,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class FocusWindowCapability(CapabilityModule):
    PHRASE = "focus current window"

    def __init__(self, *, service=None):
        self._service = service if service is not None else WindowFocusService()

    @property
    def capability(self):
        return Capability(
            name="focus_window", description="Best-effort focus of the window captured before confirmation.",
            execution_mode=ExecutionMode.LOCAL, service="computer_control",
            intent_patterns=(self.PHRASE,), requires_llm=False,
            reversible=False, requires_confirmation=True,
        )

    @staticmethod
    def _raw(arguments):
        if not isinstance(arguments, Mapping):
            raise TypeError("Focus arguments must be a mapping.")
        if arguments:
            raise ValueError("Focus requires exactly empty arguments.")

    def map_intent_arguments(self, arguments, *, original_request):
        if not isinstance(arguments, Mapping):
            raise TypeError("Focus arguments must be a mapping.")
        if not arguments:
            return {}
        if (set(arguments) == {"request"} and arguments["request"] == original_request
                and isinstance(original_request, str)
                and original_request.strip().lower() == self.PHRASE):
            return {}
        raise ValueError("No exact focus mapping is available.")

    def validate_arguments(self, arguments):
        self._raw(arguments)
        try:
            binding = self._service.prepare_focus()
            if not _valid_focus_binding(binding):
                raise ValueError()
        except Exception:
            raise ValueError("Focus target preparation could not be established.") from None
        return {"_binding": binding}

    @staticmethod
    def _binding(arguments):
        if (not isinstance(arguments, Mapping) or set(arguments) != {"_binding"}
                or not _valid_focus_binding(arguments["_binding"])):
            raise ValueError("Invalid saved focus action.")
        return arguments["_binding"]

    def validate_approval_arguments(self, arguments, *, prepared):
        self._raw(arguments)
        self._binding(prepared)
        return deepcopy(dict(prepared))

    def execute_structured(self, arguments):
        return self._service.focus_window(self._binding(arguments))

    def execute(self, request):
        raise ValueError("Focus requires structured execution.")

    def verify_result(self, *, request, output):
        unknown = VerificationResult(reason="Bounded focus outcome is inconclusive.")
        if not isinstance(request, StructuredCapabilityRequest) or type(output) is not WindowFocusResult:
            return unknown
        binding = self._binding(request.arguments)
        if binding != output._binding:
            return unknown
        # Negative focus receipts are sampled again but can never be upgraded
        # by a later independent foreground change (or a denied API attempt).
        state = (self._service.observe_focus(binding)
                 if output.state in (FocusState.FOCUSED, FocusState.NOT_FOCUSED) else None)
        if output.state in (FocusState.NOT_FOCUSED, FocusState.TARGET_CHANGED):
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "The approved window focus was not established.")
        if output.state is not FocusState.FOCUSED:
            return unknown
        if state is FocusState.FOCUSED:
            return VerificationResult(VerificationStatus.VERIFIED, "The exact approved window is foreground in the bounded check.")
        if state in (FocusState.NOT_FOCUSED, FocusState.TARGET_CHANGED):
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "The approved window focus was not established.")
        return unknown
