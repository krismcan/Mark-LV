"""Deterministic dispatch-to-executor bridge for the first structured capability."""

from __future__ import annotations

from nayeon.agent.dispatch import DispatchKind, DispatchPlan
from nayeon.agent.executor import ActionExecutor, ExecutionResult, ExecutionStatus
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.capabilities.structured import StructuredCapability, StructuredCapabilityRequest
from nayeon.registry import CapabilityRegistry


class StructuredOrchestrationBridge:
    """Prepare open_app actions; all validation and execution remain with the executor.

    Plans must come from the intent/dispatch authority path. This bridge does not
    resolve language, call models, approve actions, or execute system controls.
    """

    def __init__(self, *, registry: CapabilityRegistry, executor: ActionExecutor) -> None:
        self._registry = registry
        self._executor = executor

    def execute(self, plan: DispatchPlan, *, original_request: str) -> ExecutionResult:
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
        return self._executor.execute_structured(capability, request)

    @staticmethod
    def _reject(plan: DispatchPlan, message: str) -> ExecutionResult:
        return ExecutionResult(
            status=ExecutionStatus.DENIED,
            capability=plan.intent or "",
            message=message,
        )
