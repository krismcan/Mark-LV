"""Open-application capability for Nayeon."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from nayeon.capabilities.base import CapabilityModule
from nayeon.registry import Capability, ExecutionMode
from nayeon.services.applications import ApplicationService


class OpenAppCapability(CapabilityModule):
    """Launch local applications."""

    def __init__(self) -> None:
        self._service = ApplicationService()

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

        return self._service.launch(target)

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
        return self._service.launch(validated["application"])

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
