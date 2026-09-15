"""Central capability execution for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from nayeon.policy.confirmation import (
    ConfirmationRequest,
    ConfirmationService,
)
from nayeon.policy.service import PolicyAction, PolicyDecision, PolicyService
from nayeon.registry import Capability, CapabilityRegistry


class ExecutionStatus(str, Enum):
    EXECUTED = "executed"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    DENIED = "denied"
    FAILED = "failed"


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    capability: str
    message: str
    output: Any = None
    policy_decision: PolicyDecision | None = None
    confirmation_request: ConfirmationRequest | None = None

    @property
    def succeeded(self) -> bool:
        return self.status is ExecutionStatus.EXECUTED


class ActionExecutor:
    """Executes registered capabilities only after policy approval."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        policy: PolicyService,
        confirmation: ConfirmationService,
    ) -> None:
        self._registry = registry
        self._policy = policy
        self._confirmation = confirmation

    def execute(
        self,
        capability: Capability,
        request: str,
    ) -> ExecutionResult:
        policy_decision = self._policy.evaluate(capability)

        if policy_decision.action is PolicyAction.DENY:
            return ExecutionResult(
                status=ExecutionStatus.DENIED,
                capability=capability.name,
                message=policy_decision.reason,
                policy_decision=policy_decision,
            )

        if policy_decision.action is PolicyAction.CONFIRM:
            confirmation_request = self._confirmation.create(
                capability=capability.name,
                request=request,
            )

            return ExecutionResult(
                status=ExecutionStatus.REQUIRES_CONFIRMATION,
                capability=capability.name,
                message=policy_decision.reason,
                policy_decision=policy_decision,
                confirmation_request=confirmation_request,
            )

        return self._execute_capability(
            capability=capability,
            request=request,
            policy_decision=policy_decision,
        )

    def approve_and_execute(
        self,
        token: str,
        *,
        capability: Capability,
        request: str,
    ) -> ExecutionResult:
        confirmation_result = self._confirmation.approve(
            token,
            capability=capability.name,
            request=request,
        )

        if not confirmation_result.approved:
            return ExecutionResult(
                status=ExecutionStatus.DENIED,
                capability=capability.name,
                message=confirmation_result.reason,
            )

        policy_decision = self._policy.evaluate(capability)

        if policy_decision.action is PolicyAction.DENY:
            return ExecutionResult(
                status=ExecutionStatus.DENIED,
                capability=capability.name,
                message=policy_decision.reason,
                policy_decision=policy_decision,
            )

        return self._execute_capability(
            capability=capability,
            request=request,
            policy_decision=policy_decision,
        )

    def reject(
        self,
        token: str,
        *,
        capability: Capability,
    ) -> ExecutionResult:
        confirmation_result = self._confirmation.reject(token)

        return ExecutionResult(
            status=ExecutionStatus.DENIED,
            capability=capability.name,
            message=confirmation_result.reason,
        )

    def _execute_capability(
        self,
        *,
        capability: Capability,
        request: str,
        policy_decision: PolicyDecision,
    ) -> ExecutionResult:
        implementation = self._registry.get_implementation(capability.name)

        if implementation is None:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                capability=capability.name,
                message=f"No implementation registered for '{capability.name}'.",
                policy_decision=policy_decision,
            )

        try:
            output = implementation.execute(request)
        except Exception as exc:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                capability=capability.name,
                message=f"Capability '{capability.name}' failed: {exc}",
                policy_decision=policy_decision,
            )

        return ExecutionResult(
            status=ExecutionStatus.EXECUTED,
            capability=capability.name,
            message=f"Capability '{capability.name}' executed.",
            output=output,
            policy_decision=policy_decision,
        )