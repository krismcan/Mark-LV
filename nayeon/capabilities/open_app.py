"""Open-application capability for Nayeon."""

from __future__ import annotations

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