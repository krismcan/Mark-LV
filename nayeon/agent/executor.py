"""Central capability execution for Nayeon."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities.structured import StructuredCapability, StructuredCapabilityRequest
from nayeon.policy.confirmation import (
    ConfirmationRequest,
    ConfirmationService,
)
from nayeon.policy.service import PolicyAction, PolicyDecision, PolicyService
from nayeon.registry import Capability, CapabilityRegistry
from nayeon.undo.contract import UndoProvider
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationResult
from nayeon.verification.service import VerificationService


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
    verification: VerificationResult = field(default_factory=VerificationResult)

    @property
    def succeeded(self) -> bool:
        """Execution returned successfully; this does not assert a verified outcome."""
        return self.status is ExecutionStatus.EXECUTED


@dataclass(frozen=True, repr=False)
class _StructuredAction:
    capability: Capability
    implementation: StructuredCapability
    request: str
    arguments: dict[str, Any]
    binding: object = field(default_factory=object)


class ActionExecutor:
    """Executes registered capabilities only after policy approval."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        policy: PolicyService,
        confirmation: ConfirmationService,
        audit: AuditService,
        undo: UndoService,
    ) -> None:
        self._registry = registry
        self._policy = policy
        self._confirmation = confirmation
        self._audit = audit
        self._undo = undo
        self._verification = VerificationService()
        self._structured_pending: dict[str, tuple[ConfirmationRequest, _StructuredAction]] = {}

    def _prepare_structured(
        self, capability: Capability, request: StructuredCapabilityRequest,
    ) -> _StructuredAction:
        # Resolve authoritative metadata, not caller-supplied policy flags.
        registered = self._registry.get(capability.name)
        implementation = self._registry.get_implementation(capability.name)
        if registered is None or not isinstance(implementation, StructuredCapability):
            raise ValueError("Registered structured implementation required.")
        arguments = implementation.validate_arguments(deepcopy(request.arguments))
        if not isinstance(arguments, dict):
            raise TypeError("Validation must return a dictionary.")
        return _StructuredAction(
            deepcopy(registered), implementation, request.original_request,
            deepcopy(arguments),
        )

    def _structured_failure(self, capability: Capability) -> ExecutionResult:
        # Validator exceptions may contain arguments or credentials. Never echo them.
        message = "Structured capability validation failed."
        self._audit.record(
            AuditEventType.EXECUTION_FAILED, capability=capability.name,
            outcome="validation_failed", message=message,
        )
        return ExecutionResult(ExecutionStatus.FAILED, capability.name, message)

    def _prune_structured_pending(self) -> None:
        now = datetime.now(timezone.utc)
        for token, (confirmation, _) in tuple(self._structured_pending.items()):
            if now > confirmation.expires_at:
                self._structured_pending.pop(token)
                self._confirmation.reject(token)

    def execute_structured(
        self, capability: Capability, request: StructuredCapabilityRequest,
    ) -> ExecutionResult:
        """Validate untrusted arguments before entering the shared trust boundary."""
        self._prune_structured_pending()
        try:
            action = self._prepare_structured(capability, request)
        except Exception:
            return self._structured_failure(capability)
        return self._begin_execution(action.capability, action.request, action)

    def approve_and_execute_structured(
        self, token: str, *, capability: Capability,
        request: StructuredCapabilityRequest,
    ) -> ExecutionResult:
        """Approve only the same validated action; consume mismatches as rejections."""
        self._prune_structured_pending()
        pending = self._structured_pending.pop(token, None)
        if pending is None:
            return self.reject(token, capability=capability)
        _, action = pending
        try:
            candidate = self._prepare_structured(capability, request)
            matches = (
                candidate.capability == action.capability
                and candidate.implementation is action.implementation
                and candidate.request == action.request
                and candidate.arguments == action.arguments
            )
        except Exception:
            matches = False
        if not matches:
            return self.reject(token, capability=capability)
        return self._approve_execution(
            token, capability=action.capability, request=action.request,
            structured=action,
        )

    def execute(
        self,
        capability: Capability,
        request: str,
    ) -> ExecutionResult:
        return self._begin_execution(capability, request)

    def _begin_execution(
        self, capability: Capability, request: str,
        structured: _StructuredAction | None = None,
    ) -> ExecutionResult:
        policy_decision = self._policy.evaluate(capability)

        self._audit.record(
            AuditEventType.POLICY_DECISION,
            capability=capability.name,
            outcome=policy_decision.action.value,
            message=policy_decision.reason,
        )

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
                binding=structured.binding if structured else None,
            )

            if structured is not None:
                self._structured_pending[confirmation_request.token] = (
                    confirmation_request, structured,
                )

            self._audit.record(
                AuditEventType.CONFIRMATION_CREATED,
                capability=capability.name,
                outcome="pending",
                message="Confirmation required before execution.",
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
            structured=structured,
        )

    def approve_and_execute(
        self,
        token: str,
        *,
        capability: Capability,
        request: str,
    ) -> ExecutionResult:
        self._structured_pending.pop(token, None)
        return self._approve_execution(token, capability=capability, request=request)

    def _approve_execution(
        self, token: str, *, capability: Capability, request: str,
        structured: _StructuredAction | None = None,
    ) -> ExecutionResult:
        confirmation_result = self._confirmation.approve(
            token,
            capability=capability.name,
            request=request,
            binding=structured.binding if structured else None,
        )

        if not confirmation_result.approved:
            self._audit.record(
                AuditEventType.CONFIRMATION_REJECTED,
                capability=capability.name,
                outcome="denied",
                message=confirmation_result.reason,
            )

            return ExecutionResult(
                status=ExecutionStatus.DENIED,
                capability=capability.name,
                message=confirmation_result.reason,
            )

        self._audit.record(
            AuditEventType.CONFIRMATION_APPROVED,
            capability=capability.name,
            outcome="approved",
            message=confirmation_result.reason,
        )

        policy_decision = self._policy.evaluate(capability)

        self._audit.record(
            AuditEventType.POLICY_DECISION,
            capability=capability.name,
            outcome=policy_decision.action.value,
            message=policy_decision.reason,
        )

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
            structured=structured,
        )

    def reject(
        self,
        token: str,
        *,
        capability: Capability,
    ) -> ExecutionResult:
        self._structured_pending.pop(token, None)
        confirmation_result = self._confirmation.reject(token)

        self._audit.record(
            AuditEventType.CONFIRMATION_REJECTED,
            capability=capability.name,
            outcome="denied",
            message=confirmation_result.reason,
        )

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
        structured: _StructuredAction | None = None,
    ) -> ExecutionResult:
        implementation = self._registry.get_implementation(capability.name)

        if implementation is None:
            message = f"No implementation registered for '{capability.name}'."

            self._audit.record(
                AuditEventType.EXECUTION_FAILED,
                capability=capability.name,
                outcome="failed",
                message=message,
            )

            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                capability=capability.name,
                message=message,
                policy_decision=policy_decision,
            )

        # A capability must never claim to be reversible unless it can
        # actually provide a concrete undo operation.
        if capability.reversible and not isinstance(implementation, UndoProvider):
            message = (
                f"Capability '{capability.name}' is marked reversible "
                "but does not provide an undo operation."
            )

            self._audit.record(
                AuditEventType.EXECUTION_FAILED,
                capability=capability.name,
                outcome="configuration_error",
                message=message,
            )

            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                capability=capability.name,
                message=message,
                policy_decision=policy_decision,
            )

        self._audit.record(
            AuditEventType.EXECUTION_STARTED,
            capability=capability.name,
            outcome="started",
            message=f"Capability '{capability.name}' execution started.",
        )

        try:
            if structured is None:
                output = implementation.execute(request)
            else:
                if (implementation is not structured.implementation
                        or self._registry.get(capability.name) != structured.capability):
                    raise ValueError("Structured capability registration changed.")
                output = structured.implementation.execute_structured(
                    deepcopy(structured.arguments)
                )
        except Exception as exc:
            message = (
                f"Capability '{capability.name}' failed."
                if structured is not None
                else f"Capability '{capability.name}' failed: {exc}"
            )

            self._audit.record(
                AuditEventType.EXECUTION_FAILED,
                capability=capability.name,
                outcome="failed",
                message=message,
            )

            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                capability=capability.name,
                message=message,
                policy_decision=policy_decision,
            )

        self._audit.record(
            AuditEventType.EXECUTION_SUCCEEDED,
            capability=capability.name,
            outcome="success",
            message=f"Capability '{capability.name}' executed successfully.",
        )

        message = f"Capability '{capability.name}' executed."
        if capability.reversible:
            assert isinstance(implementation, UndoProvider)

            try:
                registration = implementation.build_undo(
                    request=request,
                    output=output,
                )

                undo_operation = self._undo.register(
                    capability=capability.name,
                    description=registration.description,
                    callback=registration.callback,
                )
            except Exception as exc:
                self._audit.record(
                    AuditEventType.UNDO_REGISTRATION_FAILED,
                    capability=capability.name,
                    outcome="failed",
                    message=(
                        f"Capability '{capability.name}' executed, "
                        "but undo could not be registered."
                    ),
                    details={
                        "error_type": type(exc).__name__,
                    },
                )

                message = (
                    f"Capability '{capability.name}' executed, "
                    "but undo could not be registered."
                )
            else:
                self._audit.record(
                    AuditEventType.UNDO_REGISTERED,
                    capability=capability.name,
                    outcome="registered",
                    message=f"Undo registered for '{capability.name}'.",
                    details={
                        "operation_id": undo_operation.operation_id,
                    },
                )
                message = f"Capability '{capability.name}' executed. Undo is available."

        # Use the implementation that executed, never a fresh registry lookup.
        # Structured arguments come from the bound normalized snapshot, not from
        # caller input, approval reinterpretation, or the capability's mutable copy.
        verification_request = (
            StructuredCapabilityRequest(structured.request, structured.arguments)
            if structured is not None else request
        )
        verification = self._verification.verify(
            implementation, request=verification_request, output=output,
        )
        self._audit.record(
            AuditEventType.VERIFICATION_OUTCOME,
            capability=capability.name,
            outcome=verification.status.value,
            message="Post-execution verification completed.",
        )
        return ExecutionResult(
            status=ExecutionStatus.EXECUTED,
            capability=capability.name,
            message=message,
            output=output,
            policy_decision=policy_decision,
            verification=verification,
        )
