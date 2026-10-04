"""Private location-bound approval, fresh eligibility, and bounded insertion."""
from copy import deepcopy
from dataclasses import dataclass, field, fields
from enum import Enum

from nayeon.audit.service import AuditEventType
from nayeon.policy.service import PolicyAction, PolicyDecision
from nayeon.policy.confirmation import ConfirmationResult
from nayeon.services.computer_control import _Redacted
from nayeon.services.pointer_hit_validation import (
    _PointerHitResult,
    _PointerHitValidationService,
    _ProposedPoint,
)
from nayeon.services.target_validation import (
    _TargetBinding,
    _TargetVerificationResult,
    _TargetVerificationService,
    _valid_target_binding,
)
from nayeon.verification.contract import VerificationResult, VerificationStatus
from nayeon.services.pointer_coordinates import _CoordinateResult, _PointerCoordinateService
from nayeon.services.pointer_effect import (
    _EffectStatus, _PointerEffectReceipt, _PointerEffectService,
)
from nayeon.services.scoped_ui_element_observation import (
    _ScopedUIElementObservationService, _ScopedUIElementResult,
    _ScopedUIElementEvidence, _runtime_id_valid,
)

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
    runtime_id: tuple[int, ...] | None = None

    def __post_init__(self):
        if (type(self.target) is not _TargetBinding
                or type(self.action) is not _PointerAction
                or type(self.point) is not _ProposedPoint):
            raise TypeError("Exact private target, action, and point required.")
        if not _valid_target_binding(self.target):
            raise ValueError("Valid private target required.")
        self.action.__post_init__()
        self.point.__post_init__()
        if self.runtime_id is not None:
            _runtime_id_valid(self.runtime_id)


@dataclass(frozen=True, slots=True, repr=False)
class _PointerEligibilityResult(_LocalOnly):
    """Post-confirmation read-only eligibility; never native effect authority."""
    status: VerificationStatus = VerificationStatus.INDETERMINATE

    def __post_init__(self):
        if type(self.status) is not VerificationStatus:
            raise TypeError("Exact private eligibility status required.")


@dataclass(frozen=True, slots=True, repr=False)
class _PointerPostObservationResult(_LocalOnly):
    """Original-target sampled equality only; no effect or semantic authority."""
    status: VerificationStatus = VerificationStatus.INDETERMINATE

    def __post_init__(self):
        if (type(self) is not _PointerPostObservationResult
                or type(self.status) is not VerificationStatus):
            raise TypeError("Exact private post-observation status required.")


@dataclass(frozen=True, slots=True, repr=False)
class _PointerVerificationProvider(_LocalOnly):
    """One-use trusted adapter of captured evidence; no observation or authority.

    Private receipts cannot cross VerificationService's deepcopy boundary.
    Keep them local to this ephemeral provider; pass only a fixed request and
    None output through the standard service. Never register this adapter.
    """
    _receipt: object
    _observation: object
    _sealed: tuple = field(default=(), init=False)
    _used: bool = field(default=False, init=False)

    def __post_init__(self):
        if type(self) is not _PointerVerificationProvider:
            raise TypeError("Exact private verification provider required.")
        object.__setattr__(self, "_sealed", self._evidence_snapshot())

    def _evidence_snapshot(self):
        if (type(self._receipt) is not _PointerEffectReceipt
                or type(self._observation) is not _PointerPostObservationResult):
            raise TypeError("Exact captured pointer evidence required.")
        self._receipt.__post_init__()
        self._observation.__post_init__()
        return (id(self._receipt), self._receipt.status, self._receipt.attempted,
                self._receipt.inserted, id(self._observation), self._observation.status)

    def verify_result(self, *, request, output):
        unknown = VerificationResult(reason="Bounded pointer evidence is inconclusive; UI/task result unverified.")
        try:
            if type(self) is not _PointerVerificationProvider or self._used:
                return unknown
            object.__setattr__(self, "_used", True)
            if (type(request) is not str or request != _REQUEST or output is not None
                    or self._evidence_snapshot() != self._sealed):
                return unknown
            _, effect, attempted, inserted, _, observed = self._sealed
            if not attempted or effect is _EffectStatus.INDETERMINATE:
                return unknown
            if effect is _EffectStatus.PARTIAL:
                return VerificationResult(VerificationStatus.NOT_VERIFIED,
                    "The complete approved input batch was not inserted; UI/task result unverified.")
            if effect is not _EffectStatus.INSERTED or inserted != 3:
                return unknown
            if observed is VerificationStatus.NOT_VERIFIED:
                return VerificationResult(VerificationStatus.NOT_VERIFIED,
                    "The bounded post-effect sample contradicted original-target identity/context and foreground equality; UI/task result unverified.")
            if observed is not VerificationStatus.VERIFIED:
                return unknown
            return VerificationResult(VerificationStatus.VERIFIED,
                "The complete approved three-record input batch was inserted, and the bounded post-effect sample matched original-target identity/context and foreground within the original-binding age window; UI/task result unverified.")
        except Exception:
            return unknown


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
        operation.runtime_id,
    )


class _PointerInvocation(_LocalOnly):
    """Own one exact target + action + location approval and eligibility check.

    Preparation performs the Phase 6.7 read-only hit check before confirmation.
    After one-time approval and policy recheck, execution eligibility is assessed
    using a brand-new foreground target baseline and a brand-new hit validation
    of the original approved point. Fresh evidence may confirm or reject the
    approval; it never replaces or refreshes what the human approved.

    VERIFIED eligibility is observational only. Optional effect mode consumes
    approval in this same invocation and maps fresh coordinates before insertion.
    """

    __slots__ = (
        "_executor", "_capability", "_service", "_hit_service",
        "_operation", "_target", "_action", "_point", "_snapshot",
        "_confirmation", "_closed", "_started",
        "_coordinate_service", "_effect_service", "_ui_element_service",
        "_services", "_registered", "_implementation",
        "_post_observation",
        "_verification",
    )

    def __init__(self, executor, capability, service, hit_service, *,
                 coordinate_service=None, effect_service=None, ui_element_service=None):
        if type(service) is not _TargetVerificationService:
            raise TypeError("Trusted target service required.")
        if type(hit_service) is not _PointerHitValidationService:
            raise TypeError("Trusted pointer hit validation service required.")
        if effect_service is not None:
            if (type(effect_service) is not _PointerEffectService
                    or type(coordinate_service) is not _PointerCoordinateService
                    or type(ui_element_service) is not _ScopedUIElementObservationService):
                raise TypeError("Trusted effect, coordinate, and scoped element services required.")
        elif coordinate_service is not None or ui_element_service is not None:
            raise TypeError("Coordinate mapping and scoped element gate require bounded effect mode.")
        self._executor = executor
        self._capability = deepcopy(capability)
        self._service = service
        self._hit_service = hit_service
        self._coordinate_service = coordinate_service
        self._effect_service = effect_service
        self._ui_element_service = ui_element_service
        self._services = (service, hit_service, coordinate_service, effect_service, ui_element_service)
        self._registered = executor._registry.get(capability.name)
        self._implementation = executor._registry.get_implementation(capability.name)
        self._operation = self._target = self._action = self._point = self._snapshot = None
        self._confirmation = None
        self._closed = self._started = False
        self._post_observation = None
        self._verification = VerificationResult()

    def _record(self, event, outcome, message):
        self._executor._audit.record(
            event,
            capability=self._capability.name,
            outcome=outcome,
            message=message,
        )

    def _policy(self):
        decision = self._executor._policy.evaluate(self._capability)
        if type(decision) is not PolicyDecision or type(decision.action) is not PolicyAction:
            raise TypeError("Exact policy decision required.")
        self._record(
            AuditEventType.POLICY_DECISION,
            decision.action.value,
            "Private pointer policy assessed.",
        )
        return decision

    def _services_valid(self):
        current = (self._service, self._hit_service,
                   self._coordinate_service, self._effect_service, self._ui_element_service)
        if self._services is None or any(a is not b for a, b in zip(current, self._services)):
            return False
        return (type(self._service) is _TargetVerificationService
                and type(self._hit_service) is _PointerHitValidationService
                and ((self._coordinate_service is None and self._effect_service is None
                      and self._ui_element_service is None)
                     or (type(self._coordinate_service) is _PointerCoordinateService
                         and type(self._effect_service) is _PointerEffectService
                         and type(self._ui_element_service) is _ScopedUIElementObservationService)))

    def _registration_valid(self):
        return (self._executor._registry.get(self._capability.name) is self._registered
                and self._registered == self._capability
                and self._executor._registry.get_implementation(self._capability.name)
                is self._implementation)

    def _bound(self, operation):
        return (type(operation) is _PointerOperation
                and operation is self._operation
                and operation.target is self._target
                and operation.action is self._action
                and operation.point is self._point
                and ((self._effect_service is None and operation.runtime_id is None)
                     or (self._effect_service is not None and operation.runtime_id is not None))
                and _snapshot(operation) == self._snapshot
                and self._services_valid() and self._registration_valid())

    def prepare(self, action, point):
        if self._closed or self._started:
            self.close()
            raise ValueError("Pointer binding invocation unavailable.")
        self._started = True
        try:
            if (not self._services_valid() or not self._registration_valid()
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
            hit.__post_init__()

            runtime_id = None
            if self._effect_service is not None:
                if not self._services_valid() or not self._registration_valid():
                    raise ValueError("Protected observation services required.")
                observed = self._ui_element_service.observe(point)
                if type(observed) is not _ScopedUIElementResult:
                    raise ValueError("Exact scoped observation required.")
                _ScopedUIElementResult.__post_init__(observed)
                if observed.status is not VerificationStatus.VERIFIED:
                    raise ValueError("Scoped observation unavailable.")
                evidence = observed.evidence
                if type(evidence) is not _ScopedUIElementEvidence:
                    raise ValueError("Exact scoped evidence required.")
                _ScopedUIElementEvidence.__post_init__(evidence)
                if (evidence.point is not point or evidence.enabled is not True
                        or not self._services_valid() or not self._registration_valid()):
                    raise ValueError("Approved point observation unavailable.")
                runtime_id = evidence.runtime_id
                # Retain only the bounded opaque tuple, never the observation sample.
                del observed, evidence

            operation = _PointerOperation(target, action, point, runtime_id)
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
            if not self._bound(operation):
                return unknown

            # A new baseline gets new timestamps. Only identity/context may match
            # the approval; the approved target object itself is never refreshed.
            fresh = self._service.acquire_target()
            if type(fresh) is not _TargetBinding or not _valid_target_binding(fresh):
                return unknown
            if (fresh.identity != operation.target.identity
                    or fresh.context != operation.target.context):
                return _PointerEligibilityResult(VerificationStatus.NOT_VERIFIED)

            # Phase 6.7 now gets the new baseline and the original approved point.
            hit = self._hit_service.validate_hit(operation.point, fresh)
            if type(hit) is not _PointerHitResult:
                return unknown
            hit.__post_init__()
            return _PointerEligibilityResult(hit.status)
        except Exception:
            return unknown

    def approve(self, operation, *, target, action, point):
        """Consume approval and assess fresh eligibility; always read-only."""
        return self._consume(operation, target=target, action=action, point=point, effect=False)

    def _observe_after_effect(self, operation):
        """One fresh verification of the original target, never a new baseline."""
        unknown = _PointerPostObservationResult()
        try:
            if not self._bound(operation):
                return unknown
            observed = self._service.verify_target(operation.target)
            if type(observed) is not _TargetVerificationResult:
                return unknown
            observed.__post_init__()
            if not self._bound(operation):
                return unknown
            return _PointerPostObservationResult(observed.status)
        except Exception:
            return unknown

    def _execute_effect(self, operation, *, target, action, point):
        """Consume exact approval for one effect; accept no VERIFIED authority."""
        return self._consume(operation, target=target, action=action, point=point, effect=True)

    def _verify_captured_effect(self, operation, receipt, receipt_seal, observation_seal):
        """Standard verification of local evidence only, before authority cleanup."""
        unknown = VerificationResult(reason="Bounded pointer evidence is inconclusive; UI/task result unverified.")
        try:
            if not self._bound(operation):
                return unknown
            provider = _PointerVerificationProvider(receipt, self._post_observation)
            if provider._sealed != (*receipt_seal, *observation_seal):
                return unknown
            result = self._executor._verification.verify(provider, request=_REQUEST, output=None)
            # No read or mutation: detect binding/evidence changes during the bridge.
            if (not self._bound(operation)
                    or provider._evidence_snapshot() != provider._sealed
                    or type(result) is not VerificationResult):
                return unknown
            return result
        except Exception:
            return unknown

    def _consume(self, operation, *, target, action, point, effect):
        unknown = (_PointerEffectReceipt() if effect
                   else _PointerEligibilityResult())
        completed = unknown
        receipt_seal = None
        observation_seal = None
        try:
            if (self._closed or self._confirmation is None
                    or (effect and self._effect_service is None)
                    or not self._bound(operation)
                    or target is not self._target
                    or action is not self._action
                    or point is not self._point
                    or operation.target is not target
                    or operation.action is not action
                    or operation.point is not point):
                return unknown

            result = self._executor._confirmation.approve(
                self._confirmation.token,
                capability=self._capability.name,
                request=_REQUEST,
                binding=operation,
            )
            if type(result) is not ConfirmationResult or type(result.approved) is not bool:
                return unknown
            self._record(
                AuditEventType.CONFIRMATION_APPROVED
                if result.approved else AuditEventType.CONFIRMATION_REJECTED,
                "approved" if result.approved else "denied",
                "Private pointer confirmation assessed.",
            )
            if not result.approved:
                return unknown
            if self._policy().action is not PolicyAction.CONFIRM:
                return unknown
            if not self._bound(operation):
                return unknown

            eligibility = self._eligible_now(operation)
            if type(eligibility) is not _PointerEligibilityResult:
                return unknown
            eligibility.__post_init__()
            if effect:
                if eligibility.status is not VerificationStatus.VERIFIED:
                    return unknown
                if not self._bound(operation):
                    return unknown
                observed = self._ui_element_service.observe(operation.point)
                if type(observed) is not _ScopedUIElementResult:
                    return unknown
                _ScopedUIElementResult.__post_init__(observed)
                if observed.status is not VerificationStatus.VERIFIED:
                    return unknown
                evidence = observed.evidence
                if type(evidence) is not _ScopedUIElementEvidence:
                    return unknown
                _ScopedUIElementEvidence.__post_init__(evidence)
                if (evidence.point is not operation.point or evidence.enabled is not True
                        or not self._bound(operation)):
                    return unknown
                # Exact local opaque tuple equality only; no native comparison.
                if evidence.runtime_id != operation.runtime_id:
                    return unknown
                # Enabled is only a safety prerequisite, never clickability or
                # semantic authorization. Do not retain this descriptive sample.
                del observed, evidence
                # Only local checks above: normalization remains the final
                # native desktop sample before the existing insertion path.
                mapped = self._coordinate_service.normalize(operation.point)
                if type(mapped) is not _CoordinateResult:
                    return unknown
                mapped.__post_init__()
                if mapped.status is not VerificationStatus.VERIFIED:
                    return unknown
                if (mapped.evidence.point is not self._point
                        or not self._bound(operation)):
                    return unknown
                # Only local validation/construction follows the last sample.
                # Assume an indeterminate attempt if the trusted seam violates
                # its result contract after being called. Never retry it.
                completed = _PointerEffectReceipt(_EffectStatus.INDETERMINATE, True)
                try:
                    receipt = self._effect_service._insert(mapped.evidence)
                    if type(receipt) is _PointerEffectReceipt:
                        receipt.__post_init__()
                        completed = receipt
                finally:
                    receipt_seal = (id(completed), completed.status, completed.attempted, completed.inserted)
                # Auditing follows the bounded effect: no file I/O between the
                # final evidence samples and native insertion. Preserve receipt
                # even if audit writing fails after an actual attempt.
            else:
                completed = eligibility
            self._record(
                AuditEventType.VERIFICATION_OUTCOME,
                eligibility.status.value,
                "Post-confirmation pointer execution eligibility assessed.",
            )
            return completed
        except Exception:
            return completed
        finally:
            # Only after the effect seam has returned/raised and a conservative
            # receipt exists. No post work enters the final pre-insertion gap.
            # Retain only a separate status, never raw target evidence/authority.
            if effect and completed.attempted:
                self._post_observation = _PointerPostObservationResult()
                try:
                    observed = self._observe_after_effect(operation)
                    if type(observed) is _PointerPostObservationResult:
                        observed.__post_init__()
                        self._post_observation = observed
                except Exception:
                    pass  # Observation failure cannot change the effect receipt.
                observation_seal = (id(self._post_observation), self._post_observation.status)
                try:
                    self._record(
                        AuditEventType.POINTER_POST_OBSERVATION_OUTCOME,
                        self._post_observation.status.value,
                        "Original target post-effect equality sampled; UI result unverified.",
                    )
                except Exception:
                    pass  # Preserve both evidence categories if auditing fails.
            # Preserve the original receipt/observation APIs. Only the first
            # effect consume gets a standard result; closed calls cannot reuse
            # evidence or overwrite the retained, authority-free conclusion.
            if effect and not self._closed:
                self._verification = self._verify_captured_effect(
                    operation, completed, receipt_seal, observation_seal)
                try:
                    self._record(
                        AuditEventType.VERIFICATION_OUTCOME,
                        self._verification.status.value,
                        "Captured bounded pointer evidence assessed; UI/task result unverified.",
                    )
                except Exception:
                    pass
            try:
                if effect:
                    self._record(
                        AuditEventType.POINTER_EFFECT_OUTCOME,
                        completed.status.value,
                        "Bounded native insertion assessed; UI result unverified.",
                    )
            except Exception:
                pass  # An audit failure cannot erase an insertion receipt.
            finally:
                try:
                    self.close()
                except Exception:
                    if not effect:
                        raise
                    # close() has cleared local state in its finally block.
                    # Do not hide a partial/indeterminate insertion outcome.
                    try:
                        self._record(
                            AuditEventType.CONFIRMATION_REJECTED,
                            "indeterminate",
                            "Private pointer binding cleanup failed.",
                        )
                    except Exception:
                        pass

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
            self._coordinate_service = None
            self._effect_service = None
            self._ui_element_service = None
            self._services = self._registered = self._implementation = None
