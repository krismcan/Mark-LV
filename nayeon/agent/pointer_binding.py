"""Private location-bound pointer approval proof. No executable pointer authority or route."""
from copy import deepcopy
from dataclasses import dataclass, fields
from enum import Enum

from nayeon.audit.service import AuditEventType
from nayeon.policy.service import PolicyAction
from nayeon.services.computer_control import _Redacted
from nayeon.services.pointer_hit_validation import (
    _PointerHitResult,
    _PointerHitValidationService,
    _ProposedPoint,
)
from nayeon.services.target_validation import _TargetBinding, _valid_target_binding
from nayeon.verification.contract import VerificationStatus

__all__ = ()
_REQUEST = "Prepare future single left click at the approved native screen point."


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
            raise ValueError("Only a single left click intent is supported.")


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class _PointerOperation(_LocalOnly):
    target: _TargetBinding
    action: _PointerAction
    point: _ProposedPoint

    def __post_init__(self):
        if (type(self.target) is not _TargetBinding
                or type(self.action) is not _PointerAction
                or type(self.point) is not _ProposedPoint):
            raise TypeError("Exact private target, action, and point required.")
        if not _valid_target_binding(self.target):
            raise ValueError("Valid private target required.")
        self.action.__post_init__()
        self.point.__post_init__()


def _snapshot(operation):
    # Independent immutable scalar snapshot also detects accidental frozen bypass.
    operation.__post_init__()
    target = operation.target
    return (
        tuple(getattr(target.identity, f.name) for f in fields(target.identity)),
        tuple(getattr(target.context, f.name) for f in fields(target.context)),
        target.acquired_from_ns,
        target.acquired_to_ns,
        operation.action.kind,
        operation.action.parameters,
        operation.point.x,
        operation.point.y,
    )


class _PointerInvocation(_LocalOnly):
    """Own one exact target + action + location approval binding.

    Preparation performs the Phase 6.7 read-only hit check before confirmation.
    That check establishes only preparation-time eligibility. Human confirmation
    commonly outlives Phase 6.5 freshness, so neither approval nor the retained
    point is execution authority. A later executor-owned phase must gather fresh
    post-confirmation target/location evidence immediately before any effect.
    """

    __slots__ = (
        "_executor", "_capability", "_service", "_hit_service",
        "_operation", "_target", "_action", "_point", "_snapshot",
        "_confirmation", "_closed", "_started",
    )

    def __init__(self, executor, capability, service, hit_service):
        if type(hit_service) is not _PointerHitValidationService:
            raise TypeError("Trusted pointer hit validation service required.")
        self._executor = executor
        self._capability = deepcopy(capability)
        self._service = service
        self._hit_service = hit_service
        self._operation = self._target = self._action = self._point = self._snapshot = None
        self._confirmation = None
        self._closed = self._started = False

    def _record(self, event, outcome, message):
        self._executor._audit.record(
            event,
            capability=self._capability.name,
            outcome=outcome,
            message=message,
        )

    def _policy(self):
        decision = self._executor._policy.evaluate(self._capability)
        self._record(
            AuditEventType.POLICY_DECISION,
            decision.action.value,
            decision.reason,
        )
        return decision

    def prepare(self, action, point):
        if self._closed or self._started:
            self.close()
            raise ValueError("Pointer binding invocation unavailable.")
        self._started = True
        try:
            if (self._executor._registry.get(self._capability.name) != self._capability
                    or self._capability.reversible
                    or not self._capability.requires_confirmation):
                raise ValueError("Protected non-reversible metadata required.")
            if type(action) is not _PointerAction or type(point) is not _ProposedPoint:
                raise TypeError("Exact private pointer action and point required.")
            action.__post_init__()
            point.__post_init__()
            if self._policy().action is not PolicyAction.CONFIRM:
                raise ValueError("Pointer binding preparation denied.")

            # Caller/model cannot supply target evidence, timestamps, HWNDs, or
            # a validation result. The target is acquired by the trusted service.
            target = self._service.acquire_target()
            hit = self._hit_service.validate_hit(point, target)
            if (type(hit) is not _PointerHitResult
                    or hit.status is not VerificationStatus.VERIFIED):
                raise ValueError("Pointer location could not be verified.")

            operation = _PointerOperation(target, action, point)
            self._snapshot = _snapshot(operation)
            self._operation = operation
            self._target = target
            self._action = action
            self._point = point
            self._confirmation = self._executor._confirmation.create(
                self._capability.name,
                _REQUEST,
                binding=operation,
            )
            self._record(
                AuditEventType.CONFIRMATION_CREATED,
                "pending",
                "Private target, action, and location confirmation required.",
            )
            return operation, self._confirmation
        except Exception:
            self.close()
            raise ValueError("Pointer binding preparation failed.") from None

    def approve(self, operation, *, target, action, point):
        """Consume approval only for the exact preparation-time composite binding.

        Approval proves which target/action/point combination was authorized.
        It deliberately does not rerun Phase 6.5 or 6.7, because a human delay
        normally makes that preparation evidence stale. Approval therefore does
        not grant native execution authority.
        """
        try:
            if (self._closed or self._confirmation is None
                    or operation is not self._operation
                    or target is not self._target
                    or action is not self._action
                    or point is not self._point
                    or operation.target is not target
                    or operation.action is not action
                    or operation.point is not point
                    or _snapshot(operation) != self._snapshot
                    or self._executor._registry.get(self._capability.name) != self._capability):
                return False
            result = self._executor._confirmation.approve(
                self._confirmation.token,
                capability=self._capability.name,
                request=_REQUEST,
                binding=operation,
            )
            self._record(
                AuditEventType.CONFIRMATION_APPROVED
                if result.approved else AuditEventType.CONFIRMATION_REJECTED,
                "approved" if result.approved else "denied",
                result.reason,
            )
            return result.approved and self._policy().action is PolicyAction.CONFIRM
        except Exception:
            return False
        finally:
            self.close()

    def close(self):
        confirmation, self._confirmation = self._confirmation, None
        self._closed = True
        self._operation = self._target = self._action = self._point = self._snapshot = None
        try:
            if confirmation is not None:
                result = self._executor._confirmation.reject(confirmation.token)
                if result.reason == "Action rejected by user.":
                    self._record(
                        AuditEventType.CONFIRMATION_REJECTED,
                        "denied",
                        "Private pointer approval binding discarded.",
                    )
        except Exception:
            raise ValueError("Pointer binding cleanup failed.") from None
        finally:
            self._service = None
            self._hit_service = None
