"""Private location-bound pointer approval and execution-eligibility proof.

No executable pointer authority or native mutation route.
"""
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
from nayeon.services.target_validation import (
    _TargetBinding,
    _TargetVerificationService,
    _valid_target_binding,
)
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


@dataclass(frozen=True, slots=True, repr=False)
class _PointerEligibilityResult(_LocalOnly):
    """Post-confirmation read-only eligibility; never native effect authority."""
    status: VerificationStatus = VerificationStatus.INDETERMINATE

    def __post_init__(self):
        if type(self.status) is not VerificationStatus:
            raise TypeError("Exact private eligibility status required.")


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
    """Own one exact target + action + location approval and eligibility check.

    Preparation performs the Phase 6.7 read-only hit check before confirmation.
    After one-time approval and policy recheck, execution eligibility is assessed
    using a brand-new foreground target baseline and a brand-new hit validation
    of the original approved point. Fresh evidence may confirm or reject the
    approval; it never replaces or refreshes what the human approved.

    Even VERIFIED eligibility is observational only. No native effect exists.
    """

    __slots__ = (
        "_executor", "_capability", "_service", "_hit_service",
        "_operation", "_target", "_action", "_point", "_snapshot",
        "_confirmation", "_closed", "_started",
    )

    def __init__(self, executor, capability, service, hit_service):
        if type(service) is not _TargetVerificationService:
            raise TypeError("Trusted target service required.")
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

    def _eligible_now(self, operation):
        """Gather new evidence; never mutate or replace the approved operation."""
        unknown = _PointerEligibilityResult()
        try:
            # Revalidate exact approved object/snapshot before any fresh reads.
            if (operation is not self._operation
                    or operation.target is not self._target
                    or operation.action is not self._action
                    or operation.point is not self._point
                    or _snapshot(operation) != self._snapshot):
                return unknown

            # A new baseline gets new timestamps. Only identity/context may match
            # the approval; the approved target object itself is never refreshed.
            fresh = self._service.acquire_target()
            if type(fresh) is not _TargetBinding:
                return unknown
            if (fresh.identity != operation.target.identity
                    or fresh.context != operation.target.context):
                return _PointerEligibilityResult(VerificationStatus.NOT_VERIFIED)

            # Phase 6.7 now gets the new baseline and the original approved point.
            hit = self._hit_service.validate_hit(operation.point, fresh)
            if type(hit) is not _PointerHitResult:
                return unknown
            return _PointerEligibilityResult(hit.status)
        except Exception:
            return unknown

    def approve(self, operation, *, target, action, point):
        """Consume approval, recheck policy, then assess fresh eligibility.

        The returned private status combines confirmation success with a fresh
        read-only eligibility assessment. VERIFIED still grants no native effect.
        """
        unknown = _PointerEligibilityResult()
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
                return unknown

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
            if not result.approved:
                return unknown
            if self._policy().action is not PolicyAction.CONFIRM:
                return unknown

            eligibility = self._eligible_now(operation)
            self._record(
                AuditEventType.VERIFICATION_OUTCOME,
                eligibility.status.value,
                "Post-confirmation pointer execution eligibility assessed.",
            )
            return eligibility
        except Exception:
            return unknown
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
