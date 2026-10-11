"""Trusted, tenure-bound onboarding admission. Not a model capability.

Cooperating Windows-session processes share a named mutex. One controller
owns it continuously across an explicit, expiring human reconciliation review
and subsequent single-use operation approvals. Historical disk READY is never
authority; every new mutex tenure begins unauthorised, including after an
abandoned acquisition with a failed quarantine write. No provider validation,
credential mutation or backend lifecycle is owned here.
"""
from dataclasses import dataclass
from pathlib import Path
from threading import RLock, get_ident
from weakref import WeakValueDictionary
from time import monotonic
import hashlib
import math
import secrets

from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.onboarding_recovery_document import (
    GENESIS_HASH, RecoveryRecord, RecoveryState, record_hash,
)
from nayeon.brain.onboarding_recovery_store import (
    OnboardingRecoveryJournalStore, RecoveryStoreUnavailable,
)
from nayeon.brain.windows_onboarding_mutex import MutexAdmission, WindowsOnboardingMutex
from nayeon.brain.connection_reconciliation import _IDENTIFIER as _TRUSTED_OPENAI_KEY_REFERENCE


class RecoveryAdmissionError(RuntimeError):
    """Admission/refusal is not evidence that no earlier side effect occurred."""


@dataclass(frozen=True, slots=True, repr=False)
class RecoveryReview:
    epoch: str
    expires_at: float
    journal_state: RecoveryState
    provider: str | None
    model: str | None
    credential_reference: str | None
    credential_presence: str
    legacy_marker_present: bool
    operation_uncertain: bool
    generation: int
    fingerprint: str
    archive_required: bool = False
    archive_present: bool = False


@dataclass(frozen=True, slots=True, repr=False)
class RecoveryPermit:
    epoch: str
    generation: int
    operation_id: str
    kind: str


_POOL_LOCK = RLock()
_POOL = WeakValueDictionary()


class TrustedOnboardingRecoveryController:
    __slots__ = (
        "_path", "_store", "_marker", "_mutex", "_ctx", "_owner",
        "_epoch", "_ready", "_review", "_generation", "_last",
        "_active", "_availability", "_clock", "_faulted", "_abandoned",
        "_baseline", "_ui_window_owner", "__weakref__"
    )

    @classmethod
    def for_path(cls, path: Path, *, availability=None, mutex=None) -> "TrustedOnboardingRecoveryController":
        if type(path) is not type(Path()):
            raise TypeError("Canonical metadata path required")
        key = str(path.absolute()).casefold()
        with _POOL_LOCK:
            existing = _POOL.get(key)
            if existing is not None:
                if mutex is not None and existing._mutex is not mutex:
                    raise RecoveryAdmissionError("Conflicting recovery mutex for canonical path")
                if availability is not None and existing._availability is not availability:
                    if existing._availability is not None:
                        # An unowned controller has no admitted action to revoke.
                        # Reject a conflicting second observer without poisoning
                        # the existing owner's future human reconciliation path.
                        if existing._ctx is not None:
                            existing._ready = False
                            existing._review = None
                            existing._faulted = True
                        raise RecoveryAdmissionError("Conflicting credential observer; tenure invalid")
                    if existing._ctx is not None:
                        existing._ready = False
                        existing._review = None
                        existing._faulted = True
                        raise RecoveryAdmissionError(
                            "Observer cannot be added after tenure begins; restart reconciliation")
                    existing._availability = availability
                return existing
            instance = cls(path, availability=availability, mutex=mutex)
            _POOL[key] = instance
            return instance

    def __init__(self, path: Path, *, availability=None, mutex=None, clock=monotonic):
        if type(path) is not type(Path()):
            raise TypeError("Canonical metadata path required")
        if availability is not None and not callable(getattr(availability, "is_available", None)):
            raise TypeError("Read-only credential observer required")
        if mutex is not None and not callable(getattr(mutex, "hold", None)):
            raise TypeError("Trusted mutex required")
        self._path = path
        self._store = OnboardingRecoveryJournalStore(
            path.with_name(path.name + ".nayeon-recovery-journal"))
        self._marker = path.with_name(path.name + ".nayeon-onboarding-inflight")
        self._mutex = WindowsOnboardingMutex() if mutex is None else mutex
        self._ctx = None
        self._owner = None
        self._epoch = None
        self._ready = False
        self._review = None
        self._generation = 0
        self._last = None
        self._active = None
        self._availability = availability
        self._clock = clock
        self._faulted = False
        self._baseline = None
        self._ui_window_owner = None

    def claim_ui_window_owner(self) -> str | None:
        """One trusted management window across all hosts sharing this path."""
        if self._ui_window_owner is not None:
            return None
        value = secrets.token_hex(16)
        self._ui_window_owner = value
        return value

    def is_ui_window_owner(self, owner: str | None) -> bool:
        return (type(owner) is str and self._ui_window_owner is not None and
                secrets.compare_digest(owner, self._ui_window_owner))

    def release_ui_window_owner(self, owner: str | None) -> bool:
        if not self.is_ui_window_owner(owner):
            return False
        self._ui_window_owner = None
        return True

    @property
    def journal_path(self) -> Path:
        return self._store.path

    @property
    def ready(self) -> bool:
        return (self._ready and not self._faulted and self._ctx is not None
                and get_ident() == self._owner and self._active is None)

    @property
    def epoch(self) -> str | None:
        return self._epoch if self.ready else None

    @property
    def generation(self) -> int | None:
        return self._generation if self.ready else None

    def _time(self) -> float:
        value = self._clock()
        if type(value) not in (float, int) or not math.isfinite(value):
            raise RecoveryAdmissionError("Trusted review clock unavailable")
        return float(value)

    def _ownership(self):
        if self._ctx is None or self._owner != get_ident():
            raise RecoveryAdmissionError("No continuous same-thread mutex tenure")

    def _enter(self):
        if self._ctx is not None:
            self._ownership()
            return
        if self._faulted:
            raise RecoveryAdmissionError("Recovery is latched; close and re-reconcile")
        ctx = self._mutex.hold()
        outcome = ctx.__enter__()
        if outcome not in (MutexAdmission.HELD, MutexAdmission.ABANDONED):
            ctx.__exit__(None, None, None)
            raise RecoveryAdmissionError("Onboarding mutex unavailable/busy")
        self._ctx = ctx
        self._owner = get_ident()
        self._epoch = secrets.token_hex(16)
        self._ready = False
        self._review = None
        self._active = None
        self._last = None
        self._baseline = None
        # ABANDONED is diagnosed for humans, NEVER grants authority.
        self._abandoned = outcome is MutexAdmission.ABANDONED

    def _observe(self) -> tuple:
        """Strict twice-read nonsecret metadata + optional presence only."""
        store = ProviderConnectionFileStore(self._path)
        try:
            first_stat = self._path.stat() if self._path.exists() else None
            first = store.load()
            second = store.load()
            last_stat = self._path.stat() if self._path.exists() else None
            def ident(s):
                return None if s is None else (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            if first != second or ident(first_stat) != ident(last_stat):
                raise RecoveryAdmissionError("Metadata changed while observing")
            connection = None if first is None else first.connection
            details = (None, None, None) if connection is None else (
                connection.provider, connection.model, connection.credential.value)
            if details[0] not in (None, "openai") or details[2] not in (None, "openai.api_key"):
                raise RecoveryAdmissionError("Noncanonical metadata")
            presence = "unknown"
            if self._availability is not None:
                before = self._availability.is_available(_TRUSTED_OPENAI_KEY_REFERENCE)
                after = self._availability.is_available(_TRUSTED_OPENAI_KEY_REFERENCE)
                if type(before) is not bool or before != after:
                    raise RecoveryAdmissionError("Credential observation inconsistent")
                presence = "present" if before else "absent"
            return (*details, presence)
        except RecoveryAdmissionError:
            raise
        except Exception as exc:
            raise RecoveryAdmissionError("Trusted observation unavailable") from exc

    def _persist(self, state: RecoveryState, *, kind=None, operation_id=None, evidence_hash=None):
        self._ownership()
        old = self._last
        rec = RecoveryRecord(
            schema_version=1,
            sequence=1 if old is None else old.sequence + 1,
            epoch=self._epoch,
            generation=self._generation,
            state=state,
            previous_hash=GENESIS_HASH if old is None else record_hash(old),
            operation_id=operation_id, operation_kind=kind,
            evidence_hash=evidence_hash,
        )
        try:
            chain = self._store.append(rec, create=old is None)
            if chain[-1] != rec:
                raise RecoveryAdmissionError("Readback evidence mismatch")
            self._last = rec
            return rec
        except Exception as exc:
            self._ready = False
            self._faulted = True
            raise RecoveryAdmissionError("Journal persistence unavailable") from exc

    def request_reconciliation(self, *, timeout_seconds: float = 120.0) -> RecoveryReview:
        if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 300:
            raise RecoveryAdmissionError("Bounded review timeout required")
        self._enter()
        self._ownership()
        if self._ready or self._review is not None or self._faulted:
            raise RecoveryAdmissionError("Reconciliation unavailable")
        try:
            history = self._store.read()
            self._last = None if history is None else history[-1]
            self._generation = 0 if self._last is None else self._last.generation + 1
            state = RecoveryState.UNINITIALIZED if self._last is None else self._last.state
            legacy = self._marker.exists()
            archived = self._store.archive_present()
            needs_archive = self._store.archive_required(history)
            details = self._observe()
            prior = None if self._last is None else record_hash(self._last)
            fingerprint = hashlib.sha256(repr((details, state.value, legacy,
                                                archived, needs_archive, prior,
                                                self._generation, self._epoch)).encode()).hexdigest()
            review = RecoveryReview(
                epoch=self._epoch, expires_at=self._time() + timeout_seconds,
                journal_state=state, provider=details[0], model=details[1],
                credential_reference=details[2], credential_presence=details[3],
                legacy_marker_present=legacy,
                operation_uncertain=(self._abandoned or legacy or state in (
                    RecoveryState.IN_FLIGHT, RecoveryState.QUARANTINED,
                    RecoveryState.RECONCILING, RecoveryState.UNAVAILABLE)) or archived,
                generation=self._generation, fingerprint=fingerprint,
                archive_required=needs_archive, archive_present=archived,
            )
            self._review = review
            return review
        except Exception as exc:
            self._faulted = True
            raise RecoveryAdmissionError("Cannot begin reconciliation") from exc

    def approve_reconciliation(self, *, human_approved: bool, fingerprint: str,
                               archive_acknowledged: bool = False) -> bool:
        self._ownership()
        review = self._review
        self._review = None
        if (not human_approved or type(human_approved) is not bool or
                review is None or type(fingerprint) is not str or
                fingerprint != review.fingerprint or
                (review.archive_required and archive_acknowledged is not True)):
            return False
        try:
            if self._faulted or self._time() > review.expires_at:
                return False
            details = self._observe()
            legacy = self._marker.exists()
            if details != (review.provider, review.model, review.credential_reference,
                           review.credential_presence) or legacy != review.legacy_marker_present:
                raise RecoveryAdmissionError("Review evidence changed")
            # Archive only after a separate deliberate human acknowledgement.
            # The complete prior journal is preserved; failure latches this tenure.
            if review.archive_required:
                if self._last is None:
                    raise RecoveryAdmissionError("No archive baseline")
                self._store.archive_exact(self._last)
                self._last = None
            # Make a blocking checkpoint before legacy marker cleanup.
            self._persist(RecoveryState.RECONCILING, evidence_hash=review.fingerprint)
            if legacy:
                self._marker.unlink()  # Explicit approved reconciliation, never automatic.
                if self._marker.exists():
                    raise RecoveryAdmissionError("Legacy marker still present")
            if self._observe() != details:
                raise RecoveryAdmissionError("Reconciliation state changed")
            self._persist(RecoveryState.READY, evidence_hash=review.fingerprint)
            self._baseline = details
            self._ready = True
            self._abandoned = False
            return True
        except Exception:
            self._ready = False
            self._faulted = True
            return False

    def begin_operation(self, *, kind: str, evidence_hash: str,
                        epoch: str, generation: int) -> RecoveryPermit:
        self._ownership()
        if not self.ready or epoch != self._epoch or generation != self._generation:
            raise RecoveryAdmissionError("No fresh reconciled admission")
        if type(evidence_hash) is not str or len(evidence_hash) != 64:
            raise RecoveryAdmissionError("Bounded nonsecret evidence digest required")
        try:
            # An unexpected external/legacy marker is always blocking.
            if self._marker.exists():
                raise RecoveryAdmissionError("Recovery marker newly present")
            if self._baseline is None or self._observe() != self._baseline:
                raise RecoveryAdmissionError("Trusted reconciliation baseline changed")
            chain = self._store.read()
            if not chain or chain[-1] != self._last or self._last.state is not RecoveryState.READY:
                raise RecoveryAdmissionError("Journal continuity unavailable")
            op_id = secrets.token_hex(16)
            self._persist(RecoveryState.IN_FLIGHT, kind=kind,
                          operation_id=op_id, evidence_hash=evidence_hash)
            permit = RecoveryPermit(self._epoch, self._generation, op_id, kind)
            self._active = permit
            self._ready = False
            return permit
        except Exception as exc:
            self._ready = False
            self._faulted = True
            raise RecoveryAdmissionError("Operation admission refused") from exc

    def verify_credential_absent(self) -> bool:
        """Trusted read-only absence proof; never resolves/reads an actual secret."""
        self._ownership()
        if self._active is None or self._availability is None:
            return False
        try:
            # Reuse the established typed reference; never construct/resolve a key.
            reference = _TRUSTED_OPENAI_KEY_REFERENCE
            first = self._availability.is_available(reference)
            second = self._availability.is_available(reference)
            return type(first) is bool and first is False and second is False
        except Exception:
            return False

    def finish_operation(self, permit: RecoveryPermit, *, verified: bool) -> bool:
        self._ownership()
        if self._active is None or permit is not self._active:
            raise RecoveryAdmissionError("No matching in-flight operation")
        self._active = None
        if type(verified) is not bool or not verified:
            self._ready = False
            self._faulted = True
            return False
        try:
            new_baseline = self._observe()
            self._generation += 1
            self._persist(RecoveryState.READY, evidence_hash=self._last.evidence_hash)
            self._baseline = new_baseline
            self._ready = True
            return True
        except Exception:
            self._ready = False
            self._faulted = True
            return False

    def close(self) -> None:
        self._ownership()
        self._ready = False
        self._review = None
        self._active = None
        self._faulted = False
        ctx = self._ctx
        self._ctx = None
        self._owner = None
        self._epoch = None
        self._last = None
        self._baseline = None
        self._ui_window_owner = None
        ctx.__exit__(None, None, None)
