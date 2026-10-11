"""Phase 8.26: cooperative, fail-closed trusted onboarding operation coordination.

This is an injected trusted-host wrapper, NOT a model tool or new lifecycle.
It serializes *execution* for cooperative Windows-session Nayeon processes,
checks non-secret file identity and current availability, and leaves a recovery
marker on uncertain mutation or interruption. No cross-store CAS/transaction.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import os
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_reconciliation import (
    ConnectionObservationStatus, observe_connection,
)
from nayeon.brain.credential_operation_host import (
    CredentialHostOutcome, CredentialHostResult, TrustedCredentialOperationHost,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation
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

    __slots__ = ("_host", "_path", "_availability", "_mutex", "_pending", "_operation")

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
        self._pending: _FreshStamp | None = None
        self._operation: OnboardingOperation | None = None

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
        if self._recovering():
            return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
        before = self._fresh()
        if before is None:
            return CoordinationReceipt(CoordinatedOutcome.UNAVAILABLE)
        try:
            allowed = self._host.request(operation)
        except Exception:
            allowed = False
        if allowed is not True or not self._host.has_pending:
            self._host.reject()
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        after = self._fresh()
        if after is None or after != before:
            self._host.reject()
            return CoordinationReceipt(CoordinatedOutcome.CONFLICT)
        self._pending = after
        self._operation = operation
        return CoordinationReceipt(CoordinatedOutcome.PENDING)

    def reject(self) -> CoordinationReceipt:
        self._pending = None
        self._operation = None
        try:
            self._host.reject()
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
        pending = self._pending
        operation = self._operation
        if pending is None or operation is None or not self._host.has_pending:
            self._pending = None
            self._operation = None
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)
        self._pending = None
        self._operation = None
        try:
            with self._mutex.hold() as admission:
                if admission is not MutexAdmission.HELD:
                    self._host.reject()
                    if admission is MutexAdmission.ABANDONED:
                        # Previously acquired mutex was abandoned: quarantine
                        # cooperating writers until a human-led recovery.
                        self._mark_inflight()
                        return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
                    if admission is MutexAdmission.BUSY:
                        return CoordinationReceipt(CoordinatedOutcome.BUSY)
                    return CoordinationReceipt(CoordinatedOutcome.UNAVAILABLE)
                if self._recovering():
                    self._host.reject()
                    return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
                current = self._fresh()
                if current is None or current != pending:
                    self._host.reject()
                    return CoordinationReceipt(CoordinatedOutcome.CONFLICT)
                if not self._mark_inflight():
                    self._host.reject()
                    return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
                # From here a crash or backend failure may have partially
                # mutated one store; preserve the marker in uncertain cases.
                try:
                    host_result = self._host.approve(candidate=candidate)
                except Exception:
                    host_result = None
                return self._finish(host_result, operation, pending)
        except Exception:
            self._host.reject()
            return CoordinationReceipt(CoordinatedOutcome.UNAVAILABLE)

    def _finish(self, result: object, operation: OnboardingOperation,
                before: _FreshStamp) -> CoordinationReceipt:
        if type(result) is not CredentialHostResult:
            if operation in _MUTATING:
                return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
            if not self._clear_marker():
                return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)
            return CoordinationReceipt(CoordinatedOutcome.INDETERMINATE)
        if operation in _MUTATING and result.outcome is CredentialHostOutcome.INDETERMINATE:
            return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED, result.outcome)
        # Re-observe metadata while still holding the mutex. Credential
        # availability may legitimately change after CONNECT/REMOVE; only
        # the metadata document and its file identity should remain stable.
        after = self._fresh()
        if (after is None or after.connection_record != before.connection_record
                or after.file_identity != before.file_identity):
            if operation in _MUTATING:
                return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED, result.outcome)
            if not self._clear_marker():
                return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED, result.outcome)
            return CoordinationReceipt(CoordinatedOutcome.CONFLICT, result.outcome)
        if not self._clear_marker():
            return CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED, result.outcome)
        return CoordinationReceipt(CoordinatedOutcome.COMPLETED, result.outcome)
