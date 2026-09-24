"""Deterministic dispatch-to-executor bridge for the first structured capability."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime

from nayeon.agent.dispatch import DispatchKind, DispatchPlan
from nayeon.agent.executor import ActionExecutor, ExecutionResult, ExecutionStatus
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.capabilities.structured import StructuredCapability, StructuredCapabilityRequest
from nayeon.registry import Capability, CapabilityRegistry


@dataclass(frozen=True, repr=False)
class PendingStructuredAction:
    """Isolated approval candidate; the executor still owns the bound authority."""

    token: str
    capability: Capability
    request: StructuredCapabilityRequest
    expires_at: datetime


@dataclass(frozen=True)
class OrchestrationResult:
    result: ExecutionResult
    pending: PendingStructuredAction | None = None


class StructuredOrchestrationBridge:
    """Prepare open_app actions; all validation and execution remain with the executor.

    Plans must come from the intent/dispatch authority path. This bridge does not
    resolve language, call models, approve actions, or execute system controls.
    """

    def __init__(self, *, registry: CapabilityRegistry, executor: ActionExecutor) -> None:
        self._registry = registry
        self._executor = executor

    def execute(self, plan: DispatchPlan, *, original_request: str) -> ExecutionResult:
        """Retain the original result-only API for existing callers."""
        return self.execute_with_pending(plan, original_request=original_request).result

    def execute_with_pending(
        self, plan: DispatchPlan, *, original_request: str,
    ) -> OrchestrationResult:
        """Return an isolated candidate only when execution awaits confirmation.

        Approval must submit this candidate to the same ActionExecutor. It is
        not authorization, and must never be reconstructed by interpreting text.
        """
        if plan.kind is DispatchKind.SYSTEM_CONTROL:
            return self._reject(plan, "System controls are not supported by this bridge.")
        if plan.kind is not DispatchKind.CAPABILITY:
            return self._reject(plan, "A resolved capability plan is required.")
        if plan.intent != "open_app":
            return self._reject(plan, "Only open_app is supported by this bridge.")

        capability = self._registry.get(plan.intent)
        if capability is None or plan.capability != capability:
            return self._reject(plan, "The capability plan is stale or unregistered.")
        implementation = self._registry.get_implementation(capability.name)
        if not isinstance(implementation, StructuredCapability):
            return self._reject(plan, "A structured capability implementation is required.")
        if not isinstance(original_request, str) or not original_request.strip():
            return self._reject(plan, "The original user request is required.")

        if "application" in plan.arguments:
            # Even an invalid candidate goes to capability validation, never to
            # a legacy fallback. All other model-produced fields are discarded.
            arguments = {"application": plan.arguments["application"]}
        elif plan.arguments.get("request") == original_request:
            # DispatchPlan has no source field. Bind the legacy request to the
            # caller's original text and accept only the deterministic prefixes.
            try:
                arguments = OpenAppCapability.arguments_from_request(original_request)
            except ValueError:
                return self._reject(plan, "No deterministic application target is available.")
        else:
            return self._reject(plan, "No application argument or matching local request is available.")

        request = StructuredCapabilityRequest(original_request, arguments)
        # Capture exactly what is submitted, before execution or caller mutation.
        # Validation/normalization and the authoritative snapshot stay in executor.
        try:
            saved_capability, saved_request = deepcopy(capability), deepcopy(request)
        except Exception:
            return self._reject(plan, "A stable structured request snapshot is required.")
        result = self._executor.execute_structured(capability, request)
        pending = None
        if (result.status is ExecutionStatus.REQUIRES_CONFIRMATION
                and result.confirmation_request is not None):
            confirmation = result.confirmation_request
            pending = PendingStructuredAction(
                confirmation.token, saved_capability, saved_request, confirmation.expires_at,
            )
        return OrchestrationResult(result, pending)

    @staticmethod
    def _reject(plan: DispatchPlan, message: str) -> OrchestrationResult:
        return OrchestrationResult(ExecutionResult(
            status=ExecutionStatus.DENIED,
            capability=plan.intent or "",
            message=message,
        ))
