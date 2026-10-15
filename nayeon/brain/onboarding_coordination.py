"""Phase 8.26: cooperative, fail-closed trusted onboarding operation coordination.

This is an injected trusted-host wrapper, NOT a model tool or new lifecycle.
It serializes *execution* for cooperative Windows-session Nayeon processes,
checks non-secret file identity and current availability, and leaves a recovery
marker on uncertain mutation or interruption. No cross-store CAS/transaction.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import math
import os
import secrets
import time
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_reconciliation import (
    ConnectionObservationStatus, observe_connection,
)
from nayeon.brain.credential_operation_host import (
    CredentialHostOutcome, CredentialHostResult, TrustedCredentialOperationHost,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation
from nayeon.brain.onboarding_recovery import TrustedOnboardingRecoveryController, RecoveryAdmissionError
from nayeon.brain.onboarding_recovery_evidence import canonical_evidence_digest
from nayeon.brain.windows_onboarding_mutex import (
    MutexAdmission, WindowsOnboardingMutex,
)


class CoordinatedOutcome(str, Enum):
    PENDING = "pending"
    REFUSED = "refused"
    BUSY = "busy"
    CONFLICT = "conflict"
    RECOVERY_REQUIRED = "recovery_required"
    UNAVAILABLE = "unavailable"
    COMPLETED = "completed"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True, repr=False)
class CoordinationReceipt:
    outcome: CoordinatedOutcome
    host_outcome: CredentialHostOutcome | None = None
    requires_reobservation: bool = True
    confirms_transaction: bool = False

    def __post_init__(self):
        if type(self.outcome) is not CoordinatedOutcome:
            raise TypeError("Exact coordination outcome required")
        if self.host_outcome is not None and type(self.host_outcome) is not CredentialHostOutcome:
            raise TypeError("Exact host outcome required")
        if self.requires_reobservation is not True or self.confirms_transaction is not False:
            raise ValueError("Onboarding coordination never proves a transaction")


@dataclass(frozen=True, slots=True, repr=False)
class _FreshStamp:
    """Internal only: non-secret typed document + file metadata + state."""
    connection_record: object
    file_identity: tuple | None
    status: ConnectionObservationStatus


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class _UiApprovalTicket:
    """One exact trusted UI review; not a provider secret or model action.

    Exact object identity, not equal evidence or equal operation, is the
    authorisation key. The coordinator alone controls its consumption.
    """
    owner_token: str
    root: object
    operation: OnboardingOperation
    pending: _FreshStamp
    epoch: str
    generation: int
    issued: float
    expires_at: float
    nonce: bytes


_UI_REVIEW_TTL_SECONDS = 300.0

_MUTATING = frozenset({
    OnboardingOperation.CONNECT, OnboardingOperation.REPLACE, OnboardingOperation.REMOVE,
})
_UNSAFE = frozenset({
    ConnectionObservationStatus.UNKNOWN,
    ConnectionObservationStatus.CHANGED_DURING_OBSERVATION,
})


class CooperativeOnboardingCoordinator:
    """Trusted composition supplies one host, canonical path and availability.

    The current process-local review is still single-use. A named mutex gates
    the side-effecting approval path only (not human review think-time).
    Another cooperating process can review simultaneously, but only one can
    execute; its losing stale review must be retried explicitly. No external
    writer prevention and no guarantee of detecting same-state key ABA.
    """

    __slots__ = ("_host", "_path", "_availability", "_mutex", "_pending", "_operation", "_recovery", "_pending_epoch", "_pending_generation", "_pending_host_review", "_ui_ticket")

    def __init__(self, *, host: TrustedCredentialOperationHost,
                 metadata_path: Path, availability: object,
                 mutex: object | None = None):
        if type(host) is not TrustedCredentialOperationHost:
            raise TypeError("Exact trusted host required")
        if type(metadata_path) is not type(Path()):
            raise TypeError("Exact native metadata path required")
        if not callable(getattr(availability, "is_available", None)):
            raise TypeError("Read-only availability required")
        if mutex is not None and not callable(getattr(mutex, "hold", None)):
            raise TypeError("Cooperative mutex hold required")
        self._host = host
        self._path = metadata_path
        self._availability = availability
        self._mutex = WindowsOnboardingMutex() if mutex is None else mutex
        self._recovery = TrustedOnboardingRecoveryController.for_path(metadata_path, availability=availability, mutex=mutex)
        self._pending_epoch = None
        self._pending_generation = None
        self._pending_host_review = None
        self._pending: _FreshStamp | None = None
        self._operation: OnboardingOperation | None = None
        self._ui_ticket: _UiApprovalTicket | None = None

    @property
    def recovery_controller(self):
        return self._recovery

    @property
    def has_pending(self) -> bool:
        return self._pending is not None and self._host.has_pending

    @property
    def recovery_marker_path(self) -> Path:
        """Trusted-host diagnostic only; never a model-selected filesystem path."""
        return self._path.with_name(self._path.name + ".nayeon-onboarding-inflight")

    def _file_identity(self) -> tuple | None:
        try:
            data = self._path.stat()
        except FileNotFoundError:
            return None
        return (data.st_dev, data.st_ino, data.st_size, data.st_mtime_ns, data.st_ctime_ns)

    def _fresh(self) -> _FreshStamp | None:
        try:
            before = self._file_identity()
            first = ProviderConnectionFileStore(self._path).load()
            observed = observe_connection(self._path, self._availability)
            second = ProviderConnectionFileStore(self._path).load()
            after = self._file_identity()
            if (before != after or first != second or
                    observed.status in _UNSAFE):
                return None
            return _FreshStamp(first, after, observed.status)
        except Exception:
            return None

    def _recovering(self) -> bool:
        try:
            return self.recovery_marker_path.exists()
        except Exception:
            return True

    def request(self, operation: OnboardingOperation) -> CoordinationReceipt:
        if self.has_pending or self._host.has_pending or type(operation) is not OnboardingOperation:
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        if self._recovery is not None and not self._recovery.ready:
            return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
        if self._recovering():
            return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
        before = self._fresh()
        if before is None:
            return CoordinationReceipt(CoordinatedOutcome.UNAVAILABLE)
        try:
            allowed = self._host.request(operation)
        except Exception:
            allowed = False
        # Bind this exact host review; a reentrant dependency may have
        # replaced an earlier review without changing operation or evidence.
        host_review = self._host.pending_review_identity if allowed is True else None
        if allowed is not True or host_review is None:
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        after = self._fresh()
        if (after is None or after != before or
                self._host.pending_review_identity is not host_review):
            self._host.reject_if_current(host_review)
            return CoordinationReceipt(CoordinatedOutcome.CONFLICT)
        self._pending = after
        self._operation = operation
        self._pending_host_review = host_review
        self._pending_epoch = None if self._recovery is None else self._recovery.epoch
        self._pending_generation = None if self._recovery is None else self._recovery.generation
        return CoordinationReceipt(CoordinatedOutcome.PENDING)

    def request_ui(self, operation: OnboardingOperation, *,
                   owner_token: str, root: object):
        """Issue an exact, one-use review for the owning trusted Tk window.

        Return (CoordinationReceipt, private_ticket_or_None). Existing
        request()/approve()/reject() remain trusted non-UI compatibility only.
        """
        if (type(owner_token) is not str or not owner_token or root is None or
                type(operation) is not OnboardingOperation or
                not self._recovery.is_ui_window_owner(owner_token)):
            return CoordinationReceipt(CoordinatedOutcome.REFUSED), None
        outcome = self.request(operation)
        if outcome.outcome is not CoordinatedOutcome.PENDING:
            return outcome, None
        # Retain the exact A review BEFORE any clock/randomness dependency
        # can reenter and replace it with a same-operation successor B.
        issued_pending = self._pending
        issued_epoch = self._pending_epoch
        issued_generation = self._pending_generation
        try:
            # A reentrant Tk Destroy may have released the owner mid-request.
            if not self._recovery.is_ui_window_owner(owner_token):
                raise ValueError("UI owner no longer active")
            issued = time.monotonic()
            nonce = secrets.token_bytes(16)
            epoch, generation = self._pending_epoch, self._pending_generation
            if (type(issued) is not float or not math.isfinite(issued) or
                    type(nonce) is not bytes or len(nonce) != 16 or
                    type(epoch) is not str or not epoch or
                    type(generation) is not int or issued_pending is None or
                    self._pending is not issued_pending or
                    self._operation is not operation or
                    self._pending_epoch != issued_epoch or
                    self._pending_generation != issued_generation or
                    self._ui_ticket is not None or
                    self._pending_host_review is None or
                    self._host.pending_review_identity is not self._pending_host_review or
                    not self._recovery.is_ui_window_owner(owner_token) or
                    not self._recovery.ready or
                    epoch != self._recovery.epoch or
                    generation != self._recovery.generation):
                raise ValueError("No trusted review-instance admission")
            ticket = _UiApprovalTicket(
                owner_token=owner_token, root=root, operation=operation,
                pending=self._pending, epoch=epoch, generation=generation,
                issued=issued, expires_at=issued + _UI_REVIEW_TTL_SECONDS,
                nonce=nonce)
            if not math.isfinite(ticket.expires_at):
                raise ValueError("Review deadline invalid")
            self._ui_ticket = ticket
            return outcome, ticket
        except Exception:
            # An issuance fault may have reentered and replaced A with B.
            # Reject only the exact originally requested A when it remains
            # unbound; never use raw reject() against B or B's UI ticket.
            if (self._pending is issued_pending and
                    self._operation is operation and
                    self._ui_ticket is None):
                self.reject()
            return CoordinationReceipt(CoordinatedOutcome.UNAVAILABLE), None

    def is_current_ui_ticket(self, *, ticket: object, owner_token: str,
                             root: object, operation: OnboardingOperation,
                             allow_expired: bool = False) -> bool:
        """Read-only exact identity check, including current owner tenure."""
        ctrl = self._recovery

        def exactly_current():
            # All of these checks refer to the same exact review instance,
            # not just its operation or an equal evidence fingerprint.
            return (type(ticket) is _UiApprovalTicket and
                    ticket is self._ui_ticket and
                    type(owner_token) is str and
                    owner_token == ticket.owner_token and
                    root is ticket.root and
                    type(operation) is OnboardingOperation and
                    operation is ticket.operation and
                    self._pending is ticket.pending and
                    self._operation is operation and
                    self._pending_host_review is not None and
                    self._host.pending_review_identity is self._pending_host_review and
                    ctrl.ready and
                    ctrl.is_ui_window_owner(owner_token) and
                    self._pending_epoch == ticket.epoch and
                    self._pending_generation == ticket.generation and
                    ctrl.epoch == ticket.epoch and
                    ctrl.generation == ticket.generation)

        try:
            if not exactly_current():
                return False
            if not allow_expired:
                # This dependency could reenter Tk/trusted callbacks and
                # replace A with B while returning a valid-looking timestamp.
                # Revalidate the WHOLE identity after it returns; otherwise
                # A's human approval could flow into B's pending operation.
                now = time.monotonic()
                if (type(now) is not float or not math.isfinite(now) or
                        not (ticket.issued <= now <= ticket.expires_at)):
                    return False
                return exactly_current()
            return True
        except Exception:
            return False

    def approve_ui(self, *, ticket: object, owner_token: str, root: object,
                   operation: OnboardingOperation, candidate: object = None,
                   acknowledged: bool = False) -> CoordinationReceipt:
        """Consume only this UI review before entering original host path."""
        if not self.is_current_ui_ticket(ticket=ticket, owner_token=owner_token,
                                         root=root, operation=operation):
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        if (type(acknowledged) is not bool or
                (operation is OnboardingOperation.REMOVE and not acknowledged)):
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        exact_pending = self._pending
        try:
            # Keep the UI ticket installed while processing, so reentrant
            # raw approve()/reject() cannot bypass consent binding.
            return self._approve_pending(candidate=candidate)
        finally:
            # A delegated approval may throw or return before consuming A.
            # Clear/reject only A; reentrant B may have identical evidence.
            if self._ui_ticket is ticket:
                self._ui_ticket = None
            if (self._pending is exact_pending and
                    self._operation is operation and
                    self._ui_ticket is None):
                self.reject()

    def reject_ui(self, *, ticket: object, owner_token: str, root: object,
                  operation: OnboardingOperation) -> CoordinationReceipt:
        """Exact-owner cleanup may reject expired A but never successor B."""
        if not self.is_current_ui_ticket(
                ticket=ticket, owner_token=owner_token, root=root,
                operation=operation, allow_expired=True):
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        self._ui_ticket = None
        return self.reject()

    def reject_ui_for_owner_shutdown(self, *, owner_token: str,
                                     root: object) -> CoordinationReceipt:
        """Trusted owner-root teardown of its CURRENT active review.

        This is deliberately distinct from A's stale callback reject_ui(A):
        an old callback cannot cancel B, but closing the actual owning root
        must revoke its own current B before owner tenure is released.
        A foreign window or released owner cannot invoke this route.
        """
        ticket = self._ui_ticket
        if (type(ticket) is not _UiApprovalTicket or
                type(owner_token) is not str or
                ticket.owner_token != owner_token or
                ticket.root is not root or
                not self._recovery.is_ui_window_owner(owner_token)):
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        return self.reject_ui(ticket=ticket, owner_token=owner_token,
                              root=root, operation=ticket.operation)

    def reject(self) -> CoordinationReceipt:
        # Trusted legacy calls cannot steal a pending UI-ticket-owned review.
        if self._ui_ticket is not None:
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        host_review = self._pending_host_review
        self._pending = None
        self._operation = None
        self._pending_epoch = None
        self._pending_generation = None
        self._pending_host_review = None
        try:
            if host_review is None:
                self._host.reject()  # Explicit trusted orphan cleanup only.
            else:
                self._host.reject_if_current(host_review)
        except Exception:
            return CoordinationReceipt(CoordinatedOutcome.UNAVAILABLE)
        return CoordinationReceipt(CoordinatedOutcome.REFUSED)

    def _mark_inflight(self) -> bool:
        """Fail closed if a prior operation may have died or been indeterminate."""
        path = self.recovery_marker_path
        try:
            with path.open("xb") as file:
                file.write(b"Nayeon v1 onboarding operation needs review if interrupted.\n")
                file.flush()
                os.fsync(file.fileno())
            return True
        except Exception:
            return False

    def _clear_marker(self) -> bool:
        try:
            self.recovery_marker_path.unlink()
            return True
        except Exception:
            return False

    def approve(self, *, candidate: object = None) -> CoordinationReceipt:
        # Never let raw trusted direct calls consume a UI-owned review.
        if self._ui_ticket is not None:
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        return self._approve_pending(candidate=candidate)

    def _approve_pending(self, *, candidate: object = None) -> CoordinationReceipt:
        """Shared consumption body; approval entrypoint enforces UI provenance."""
        pending = self._pending
        operation = self._operation
        host_review = self._pending_host_review
        if (pending is None or operation is None or host_review is None or
                self._host.pending_review_identity is not host_review):
            self._pending = None
            self._operation = None
            self._pending_host_review = None
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        epoch = self._pending_epoch
        generation = self._pending_generation
        self._pending = None
        self._operation = None
        self._pending_epoch = None
        self._pending_generation = None
        self._pending_host_review = None
        if self._recovery is None:
            self._host.reject_if_current(host_review)
            return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
        return self._approve_recovered(pending, operation, candidate, epoch, generation,
                                       host_review)

    def _approve_recovered(self, pending: _FreshStamp, operation: OnboardingOperation,
                           candidate: object, epoch: str | None,
                           generation: int | None,
                           host_review: object) -> CoordinationReceipt:
        """Trusted active-tenure path, bound to A's exact host review."""
        ctrl = self._recovery
        if (not ctrl.ready or epoch != ctrl.epoch or generation != ctrl.generation or
                self._recovering()):
            self._host.reject_if_current(host_review)
            return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
        current = self._fresh()
        if (current is None or current != pending or
                self._host.pending_review_identity is not host_review):
            self._host.reject_if_current(host_review)
            return CoordinationReceipt(CoordinatedOutcome.CONFLICT)
        try:
            fingerprint = canonical_evidence_digest(
                kind=operation.value, before=pending.connection_record,
                after=None, identity=pending.file_identity,
                observation=pending.status.value)
            # A successful reentrant callback may have replaced A with B.
            # Do not even start the IN_FLIGHT journal for B using A's consent.
            if self._host.pending_review_identity is not host_review:
                return CoordinationReceipt(CoordinatedOutcome.UNAVAILABLE)
            permit = ctrl.begin_operation(kind=operation.value, evidence_hash=fingerprint,
                                          epoch=epoch, generation=generation)
        except Exception as exc:
            # A's exceptional cleanup must not cancel a distinct successor B.
            # Admission could already have persisted IN_FLIGHT: never retry.
            try:
                self._host.reject_if_current(host_review)
            except Exception:
                pass
            return CoordinationReceipt(
                CoordinatedOutcome.RECOVERY_REQUIRED
                if isinstance(exc, RecoveryAdmissionError)
                else CoordinatedOutcome.UNAVAILABLE)
        try:
            host_result = self._host.approve_if_current(host_review, candidate=candidate)
        except Exception:
            # The permit may already have journaled IN_FLIGHT. A dependency
            # exception before host review consumption must not strand A,
            # but A must never reject a distinct host-only or coordinator B.
            try:
                self._host.reject_if_current(host_review)
            except Exception:
                pass
            host_result = None
        after = self._fresh()
        # CONNECT/REPLACE have no trusted exact-value readback. A mere
        # SUBMITTED result/presence cannot independently verify the key.
        verified = (
            type(host_result) is CredentialHostResult
            and host_result.outcome is not CredentialHostOutcome.INDETERMINATE
            and after is not None
            and after.connection_record == pending.connection_record
            and after.file_identity == pending.file_identity
            and (operation is OnboardingOperation.REMOVE and
                 host_result.outcome is CredentialHostOutcome.SUBMITTED and
                 ctrl.verify_credential_absent() or
                 operation not in (OnboardingOperation.CONNECT,
                                   OnboardingOperation.REPLACE, OnboardingOperation.REMOVE))
        )
        try:
            confirmed = ctrl.finish_operation(permit, verified=verified)
        except RecoveryAdmissionError:
            confirmed = False
        if not confirmed:
            return CoordinationReceipt(
                CoordinatedOutcome.RECOVERY_REQUIRED,
                host_result.outcome if type(host_result) is CredentialHostResult else None)
        return CoordinationReceipt(
            CoordinatedOutcome.COMPLETED,
            host_result.outcome if type(host_result) is CredentialHostResult else None)
