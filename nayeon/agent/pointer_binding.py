"""Private Phase 6.6 binding proof. No executable pointer authority or route."""
from copy import deepcopy
from dataclasses import dataclass, fields
from enum import Enum

from nayeon.audit.service import AuditEventType
from nayeon.policy.service import PolicyAction
from nayeon.services.computer_control import _Redacted
from nayeon.services.target_validation import _TargetBinding, _valid_target_binding

__all__ = ()
_REQUEST = "Prepare future single left click intent (no executable location)."


class _LocalOnly(_Redacted):
    __slots__ = ()

    def __reduce_ex__(self, protocol):
        raise TypeError("Private invocation state cannot be serialized or copied.")

    def __copy__(self):
        raise TypeError("Private invocation state cannot be serialized or copied.")

    def __deepcopy__(self, memo):
        raise TypeError("Private invocation state cannot be serialized or copied.")


class _PointerActionKind(Enum):
    SINGLE_LEFT_CLICK = "single_left_click"


@dataclass(frozen=True, slots=True, repr=False)
class _PointerAction(_LocalOnly):
    kind: _PointerActionKind = _PointerActionKind.SINGLE_LEFT_CLICK
    parameters: tuple = ()

    def __post_init__(self):
        if type(self.kind) is not _PointerActionKind or type(self.parameters) is not tuple:
            raise TypeError("Exact private pointer action types required.")
        if self.kind is not _PointerActionKind.SINGLE_LEFT_CLICK or self.parameters != ():
            raise ValueError("Only a location-free single left click intent is supported.")


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class _PointerOperation(_LocalOnly):
    target: _TargetBinding
    action: _PointerAction

    def __post_init__(self):
        if type(self.target) is not _TargetBinding or type(self.action) is not _PointerAction:
            raise TypeError("Exact private target and action required.")
        if not _valid_target_binding(self.target):
            raise ValueError("Valid private target required.")
        self.action.__post_init__()


def _snapshot(operation):
    # Independent immutable scalar snapshot also detects accidental frozen bypass.
    operation.__post_init__()
    target = operation.target
    return (tuple(getattr(target.identity, f.name) for f in fields(target.identity)),
            tuple(getattr(target.context, f.name) for f in fields(target.context)),
            target.acquired_from_ns, target.acquired_to_ns,
            operation.action.kind, operation.action.parameters)


class _PointerInvocation(_LocalOnly):
    """Owned only by ActionExecutor's private lexical context, never a registry.

    Prepare acquires through the trusted service AFTER policy. Approval consumes
    exactly once and only reports binding equality, never execution eligibility.
    """
    __slots__ = ("_executor", "_capability", "_service", "_operation", "_target",
                 "_action", "_snapshot", "_confirmation", "_closed", "_started")

    def __init__(self, executor, capability, service):
        self._executor, self._capability, self._service = executor, deepcopy(capability), service
        self._operation = self._target = self._action = self._snapshot = None
        self._confirmation = None
        self._closed = self._started = False

    def _record(self, event, outcome, message):
        self._executor._audit.record(event, capability=self._capability.name,
                                     outcome=outcome, message=message)

    def _policy(self):
        decision = self._executor._policy.evaluate(self._capability)
        self._record(AuditEventType.POLICY_DECISION, decision.action.value, decision.reason)
        return decision

    def prepare(self, action):
        if self._closed or self._started:
            self.close()
            raise ValueError("Pointer binding invocation unavailable.")
        self._started = True
        try:
            if (self._executor._registry.get(self._capability.name) != self._capability
                    or self._capability.reversible or not self._capability.requires_confirmation):
                raise ValueError("Protected non-reversible metadata required.")
            if type(action) is not _PointerAction:
                raise TypeError("Exact private pointer action required.")
            action.__post_init__()
            if self._policy().action is not PolicyAction.CONFIRM:
                raise ValueError("Pointer binding preparation denied.")
            # Caller/model cannot supply a target, a timestamp, or a legacy binding.
            target = self._service.acquire_target()
            operation = _PointerOperation(target, action)
            self._snapshot = _snapshot(operation)
            self._operation, self._target, self._action = operation, target, action
            self._confirmation = self._executor._confirmation.create(
                self._capability.name, _REQUEST, binding=operation)
            self._record(AuditEventType.CONFIRMATION_CREATED, "pending",
                         "Private pointer intent binding confirmation required.")
            return operation, self._confirmation
        except Exception:
            self.close()
            raise ValueError("Pointer binding preparation failed.") from None

    def approve(self, operation, *, target, action):
        """Trusted human-confirmation seam; bool is NOT native authority.

        Fresh verify_target is deliberately absent: a future approved execution
        seam must verify the ORIGINAL target on the SAME service immediately
        before any future effect, without returning a reusable validation result.
        """
        try:
            if (self._closed or self._confirmation is None
                    or operation is not self._operation or target is not self._target
                    or action is not self._action or operation.target is not target
                    or operation.action is not action or _snapshot(operation) != self._snapshot
                    or self._executor._registry.get(self._capability.name) != self._capability):
                return False
            result = self._executor._confirmation.approve(
                self._confirmation.token, capability=self._capability.name,
                request=_REQUEST, binding=operation)
            self._record(AuditEventType.CONFIRMATION_APPROVED if result.approved
                         else AuditEventType.CONFIRMATION_REJECTED,
                         "approved" if result.approved else "denied", result.reason)
            return result.approved and self._policy().action is PolicyAction.CONFIRM
        except Exception:
            return False
        finally:
            self.close()

    def close(self):
        confirmation, self._confirmation = self._confirmation, None
        self._closed = True
        self._operation = self._target = self._action = self._snapshot = None
        try:
            if confirmation is not None:
                result = self._executor._confirmation.reject(confirmation.token)
                if result.reason == "Action rejected by user.":
                    self._record(AuditEventType.CONFIRMATION_REJECTED, "denied",
                                 "Private pointer intent binding discarded.")
        except Exception:
            raise ValueError("Pointer binding cleanup failed.") from None
        finally:
            self._service = None
