"""Open-application capability for Nayeon."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.applications import ApplicationService, LaunchResult
from nayeon.services.application_observation import ApplicationDefinition, ApplicationObservation, ApplicationState
from nayeon.verification.contract import VerificationResult, VerificationStatus


class ApplicationLaunchError(RuntimeError):
    """The application service reported a failed launch attempt."""


class OpenAppCapability(CapabilityModule):
    """Launch local applications."""

    def __init__(self, *, service: ApplicationService | None = None) -> None:
        self._service = service if service is not None else ApplicationService()

    @property
    def capability(self) -> Capability:
        return Capability(
            name="open_app",
            description="Open a local application.",
            execution_mode=ExecutionMode.LOCAL,
            service="applications",
            intent_patterns=(
                "open ",
                "launch ",
                "start ",
            ),
            requires_llm=False,
            reversible=False,
            requires_confirmation=False,
        )

    def execute(self, request: str) -> object:
        """Execute an application launch request."""

        target = self._extract_target(request)

        return self._launch(target)

    def validate_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Validate an application target without performing any OS action."""
        if not isinstance(arguments, Mapping):
            raise TypeError("Application arguments must be a mapping.")
        if set(arguments) != {"application"}:
            raise ValueError("Exactly the application argument is required.")
        application = arguments["application"]
        if not isinstance(application, str):
            raise TypeError("Application must be a string.")
        if not application.strip():
            raise ValueError("Application must not be blank.")
        return {"application": application.strip()}

    def execute_structured(self, arguments: Mapping[str, Any]) -> object:
        """Revalidate before delegating to the existing application service."""
        validated = self.validate_arguments(arguments)
        return self._launch(validated["application"])

    def _launch(self, target: str) -> object:
        result = self._service.launch(target)
        if isinstance(result, LaunchResult) and result.success is False:
            # Do not echo platform errors, paths, or arbitrary service messages.
            raise ApplicationLaunchError("Application launch failed.")
        return result

    def verify_result(
        self, *, request: str | StructuredCapabilityRequest, output: Any,
    ) -> VerificationResult:
        unknown = VerificationResult(reason="Application state could not be observed reliably.")
        if not isinstance(output, LaunchResult) or output.success is not True:
            return unknown
        # Legacy verification uses the executed target in the launch receipt,
        # never another parse of user wording. Structured verification uses the
        # executor's normalized request and requires the receipt to match it.
        if isinstance(request, StructuredCapabilityRequest):
            target = self.validate_arguments(request.arguments)["application"]
            if target != output.target:
                return unknown
        else:
            target = output.target
        if not isinstance(target, str) or not target.strip():
            return unknown
        try:
            observation = self._service.observe(target)
            if (not isinstance(observation, ApplicationObservation)
                    or observation.target != target
                    or not isinstance(observation.state, ApplicationState)
                    or observation.state is ApplicationState.UNKNOWN):
                return unknown
            # Validate safe evidence and require explicit identity metadata even
            # for a typed provider result. Missing metadata is never negative.
            definition = ApplicationDefinition(observation.application_id, (target,),
                                               observation.expected_process_names)
            if not definition.expected_process_names:
                return unknown
            status = (VerificationStatus.VERIFIED
                      if observation.state is ApplicationState.OBSERVED_OPEN
                      else VerificationStatus.INDETERMINATE)
            return VerificationResult(
                status, "Configured application process observed." if status is VerificationStatus.VERIFIED
                # A single snapshot cannot distinguish delayed startup from failure.
                else "Process not yet observed; launch outcome remains indeterminate.",
                {"application_id": definition.application_id, "state": observation.state.value,
                 "expected_process_names": list(definition.expected_process_names)},
            )
        except Exception:
            return unknown

    @staticmethod
    def arguments_from_request(request: str) -> dict[str, Any]:
        """Map a local open/launch/start request without validation or OS effects."""
        target = OpenAppCapability._extract_target(request)
        if target == request.strip():
            raise ValueError("A local application-launch prefix is required.")
        return {"application": target}

    @staticmethod
    def _extract_target(request: str) -> str:
        """Extract the application name from a natural-language request."""

        normalized = request.strip()

        for prefix in (
            "open ",
            "launch ",
            "start ",
        ):
            if normalized.lower().startswith(prefix):
                return normalized[len(prefix):].strip()

        return normalized
