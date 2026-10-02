"""Explicit bounded plain text into the foreground window saved before approval."""
from collections.abc import Mapping
from copy import deepcopy
import json

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.keyboard_text import (
    KeyboardTextResult, KeyboardTextService, TextInputState, _valid_text_binding, validate_text,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus


class TypeTextCapability(CapabilityModule):
    PHRASE = "type text "

    def __init__(self, *, service=None):
        self._service = service if service is not None else KeyboardTextService()

    @property
    def capability(self):
        return Capability(
            name="type_text", description="Attempt bounded plain text into the exact approved foreground window.",
            execution_mode=ExecutionMode.LOCAL, service="computer_control",
            intent_patterns=(self.PHRASE,), requires_llm=False,
            reversible=False, requires_confirmation=True,
        )

    @staticmethod
    def _raw(arguments):
        if not isinstance(arguments, Mapping):
            raise TypeError("Text arguments must be a mapping.")
        if set(arguments) != {"text"}:
            raise ValueError("Exactly one text argument is required.")
        return validate_text(arguments["text"])

    def map_intent_arguments(self, arguments, *, original_request):
        if not isinstance(arguments, Mapping):
            raise TypeError("Text arguments must be a mapping.")
        if set(arguments) == {"text"}:
            return {"text": self._raw(arguments)}
        if (set(arguments) == {"request"} and arguments["request"] == original_request
                and isinstance(original_request, str)):
            request = original_request.strip()
            if request.lower().startswith(self.PHRASE):
                try:
                    text = json.loads(request[len(self.PHRASE):])
                except (TypeError, ValueError):
                    raise ValueError("An explicit JSON text string is required.") from None
                return {"text": validate_text(text)}
        raise ValueError("No exact text mapping is available.")

    def validate_arguments(self, arguments):
        text = self._raw(arguments)
        try:
            binding = self._service.prepare_text(text)
            if not _valid_text_binding(binding) or binding.text != text:
                raise ValueError()
        except Exception:
            raise ValueError("Text target preparation could not be established.") from None
        return {"_binding": binding}

    @staticmethod
    def _binding(arguments):
        if (not isinstance(arguments, Mapping) or set(arguments) != {"_binding"}
                or not _valid_text_binding(arguments["_binding"])):
            raise ValueError("Invalid saved text action.")
        return arguments["_binding"]

    def validate_approval_arguments(self, arguments, *, prepared):
        text = self._raw(arguments)
        binding = self._binding(prepared)
        if text != binding.text:
            raise ValueError("Text differs from the saved action.")
        return deepcopy(dict(prepared))

    def execute_structured(self, arguments):
        return self._service.type_text(self._binding(arguments))

    def execute(self, request):
        raise ValueError("Text input requires structured execution.")

    def verify_result(self, *, request, output):
        unknown = VerificationResult(reason="Bounded keyboard outcome is inconclusive.")
        if not isinstance(request, StructuredCapabilityRequest) or type(output) is not KeyboardTextResult:
            return unknown
        binding = self._binding(request.arguments)
        if binding != output._binding:
            return unknown
        if output.state in (TextInputState.PARTIAL, TextInputState.NOT_TYPED, TextInputState.TARGET_CHANGED):
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "Complete approved keyboard input was not established.")
        if output.state is not TextInputState.TYPED:
            return unknown
        state = self._service.observe_target(binding)
        if state is TextInputState.TYPED:
            return VerificationResult(VerificationStatus.VERIFIED,
                                      "The complete planned keyboard sequence was accepted and the exact target remained valid in the bounded check.")
        if state is TextInputState.TARGET_CHANGED:
            return VerificationResult(VerificationStatus.NOT_VERIFIED, "The approved foreground target changed.")
        return unknown
