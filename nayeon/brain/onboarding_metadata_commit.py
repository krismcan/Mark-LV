"""Phase 8.28: explicit trusted metadata confirmation and cooperative commit.

This is NOT a model tool, key lifecycle, cross-store transaction or credential
authority. Only trusted human UI handlers may call request/approve. Exact
canonical OpenAI metadata, no credential backend, network or automatic recovery.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import math
import os
import time
from collections.abc import Callable

from nayeon.brain.connection_document import (
    ProviderConnectionDocumentV1, parse_provider_connection_document,
)
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.windows_onboarding_mutex import MutexAdmission, WindowsOnboardingMutex


class MetadataOperation(str, Enum):
    SAVE = "save"
    CLEAR = "clear"


class MetadataCommitOutcome(str, Enum):
    PENDING = "pending"
    REFUSED = "refused"
    EXPIRED = "expired"
    BUSY = "busy"
    CONFLICT = "conflict"
    RECOVERY_REQUIRED = "recovery_required"
    UNAVAILABLE = "unavailable"
    VERIFIED = "verified"


@dataclass(frozen=True, slots=True, repr=False)
class MetadataCommitReceipt:
    outcome: MetadataCommitOutcome
    requires_reobservation: bool = True
    grants_credential_authority: bool = False
    confirms_cross_store_transaction: bool = False

    def __post_init__(self) -> None:
        if type(self.outcome) is not MetadataCommitOutcome:
            raise TypeError("Exact metadata outcome required")
        if (self.requires_reobservation is not True or
                self.grants_credential_authority is not False or
                self.confirms_cross_store_transaction is not False):
            raise ValueError("Metadata receipts grant no credential authority or transaction")


@dataclass(frozen=True, slots=True, repr=False)
class _MetadataStamp:
    current: ProviderConnectionDocumentV1 | None
    identity: tuple | None


@dataclass(frozen=True, slots=True, repr=False)
class _Pending:
    operation: MetadataOperation
    before: _MetadataStamp
    target: ProviderConnectionDocumentV1
    deadline: float


def _canonical(record: ProviderConnectionDocumentV1 | None) -> bool:
    if record is None or record.connection is None:
        return True
    cfg = record.connection
    return cfg.provider == "openai" and cfg.credential.value == "openai.api_key"


def _target_from_model(model: str) -> ProviderConnectionDocumentV1:
    # Parsing reuses the existing exact typed metadata/identifier contracts.
    # Do not relax model/provenance validation or accept provider identifiers.
    if type(model) is not str:
        raise TypeError("Exact model name required")
    # A model field is not a secret entry: reject recognizable credential
    # shapes even though the older generic document codec accepts text.
    if model.lower().startswith(("sk-", "bearer ", "ghp_", "gho_",
                                  "github_pat_", "-----begin", "eyj")):
        raise ValueError("Credential-shaped text cannot be a model identifier")
    return parse_provider_connection_document({
        "schema_version": 1,
        "connection": {"provider": "openai", "model": model,
                       "credential": "openai.api_key"},
    })


class TrustedMetadataCommitHost:
    """Independent, expiring single-use metadata approval, no ambient authority.

    Trusted composition owns canonical path, same Windows-session mutex name
    and marker convention as Phase 8.26 credential coordinator. A review does
    not hold the mutex; approval acquires it nonblocking and rechecks before
    any write. External writers and equal-state ABA are outside guarantees.
    """

    __slots__ = ("_path", "_store", "_mutex", "_clock", "_timeout", "_pending")

    def __init__(self, *, metadata_path: Path, mutex: object | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 timeout_seconds: float = 120.0) -> None:
        if type(metadata_path) is not type(Path()):
            raise TypeError("Exact native metadata path required")
        if mutex is not None and not callable(getattr(mutex, "hold", None)):
            raise TypeError("Cooperative mutex must have hold")
        if not callable(clock):
            raise TypeError("Trusted monotonic clock required")
        if (type(timeout_seconds) not in (float, int) or
                not math.isfinite(timeout_seconds)):
            raise TypeError("Finite timeout required")
        if not 0 < timeout_seconds <= 300:
            raise ValueError("Review lifetime must be bounded")
        self._path = metadata_path
        self._store = ProviderConnectionFileStore(metadata_path)
        self._mutex = WindowsOnboardingMutex() if mutex is None else mutex
        self._clock = clock
        self._timeout = float(timeout_seconds)
        self._pending: _Pending | None = None

    @property
    def has_pending(self) -> bool:
        return self._pending is not None

    @property
    def recovery_marker_path(self) -> Path:
        return self._path.with_name(self._path.name + ".nayeon-onboarding-inflight")

    def _now(self) -> float:
        try:
            now = self._clock()
        except Exception:
            raise RuntimeError("Review clock unavailable") from None
        if type(now) not in (float, int) or not math.isfinite(now):
            raise RuntimeError("Review clock unavailable")
        return float(now)

    def _identity(self) -> tuple | None:
        try:
            info = self._path.stat()
        except FileNotFoundError:
            return None
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)

    def _fresh(self) -> _MetadataStamp | None:
        try:
            first_identity = self._identity()
            first_record = self._store.load()
            second_record = self._store.load()
            second_identity = self._identity()
            if (first_identity != second_identity or
                    first_record != second_record or not _canonical(first_record)):
                return None
            return _MetadataStamp(first_record, second_identity)
        except Exception:
            return None

    def _recovering(self) -> bool:
        try:
            return self.recovery_marker_path.exists()
        except Exception:
            return True

    def _mark_inflight(self) -> bool:
        # Exact marker path is shared with credential coordination. Exclusive
        # creation prevents overwriting a prior unresolved operation.
        try:
            with self.recovery_marker_path.open("xb") as output:
                output.write(b"Nayeon v1 onboarding metadata operation needs human reconciliation.\n")
                output.flush()
                os.fsync(output.fileno())
            return True
        except Exception:
            return False

    def _clear_marker(self) -> bool:
        try:
            self.recovery_marker_path.unlink()
            return True
        except Exception:
            return False

    def _request(self, operation: MetadataOperation,
                 target: ProviderConnectionDocumentV1 | None) -> MetadataCommitReceipt:
        if self.has_pending:
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
        if self._recovering():
            return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
        before = self._fresh()
        if before is None:
            return MetadataCommitReceipt(MetadataCommitOutcome.UNAVAILABLE)
        if operation is MetadataOperation.CLEAR:
            if before.current is None or before.current.connection is None:
                return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
            target = ProviderConnectionDocumentV1(connection=None)
        elif operation is MetadataOperation.SAVE:
            if (type(target) is not ProviderConnectionDocumentV1 or
                    not _canonical(target) or target.connection is None or
                    before.current == target):
                return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
        else:
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
        try:
            deadline = self._now() + self._timeout
            if not math.isfinite(deadline):
                raise RuntimeError("Nonfinite deadline")
        except Exception:
            return MetadataCommitReceipt(MetadataCommitOutcome.UNAVAILABLE)
        if self._fresh() != before:
            return MetadataCommitReceipt(MetadataCommitOutcome.CONFLICT)
        self._pending = _Pending(operation, before, target, deadline)
        return MetadataCommitReceipt(MetadataCommitOutcome.PENDING)

    def request_save(self, model: str) -> MetadataCommitReceipt:
        """Human-triggered non-secret preview; never persists on request."""
        try:
            target = _target_from_model(model)
        except (ValueError, TypeError):
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
        return self._request(MetadataOperation.SAVE, target)

    def request_clear(self) -> MetadataCommitReceipt:
        """Human-triggered metadata-only clear; never deletes stored key."""
        return self._request(MetadataOperation.CLEAR, None)

    def reject(self) -> MetadataCommitReceipt:
        self._pending = None
        return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)

    def approve(self, *, human_approved: bool) -> MetadataCommitReceipt:
        """Only trusted human UI event handler may call with True."""
        pending = self._pending
        # Consume the review before attempting any external operation.
        self._pending = None
        if pending is None or type(human_approved) is not bool or not human_approved:
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
        try:
            if self._now() > pending.deadline:
                return MetadataCommitReceipt(MetadataCommitOutcome.EXPIRED)
        except Exception:
            return MetadataCommitReceipt(MetadataCommitOutcome.UNAVAILABLE)
        try:
            with self._mutex.hold() as admission:
                if admission is not MutexAdmission.HELD:
                    if admission is MutexAdmission.ABANDONED:
                        self._mark_inflight()
                        return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
                    if admission is MutexAdmission.BUSY:
                        return MetadataCommitReceipt(MetadataCommitOutcome.BUSY)
                    return MetadataCommitReceipt(MetadataCommitOutcome.UNAVAILABLE)
                if self._recovering():
                    return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
                current = self._fresh()
                if current is None or current != pending.before:
                    return MetadataCommitReceipt(MetadataCommitOutcome.CONFLICT)
                if not self._mark_inflight():
                    return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
                # A subsequent exception might occur *after* os.replace. In
                # that case preserve marker rather than retry or rollback.
                try:
                    self._store.save(pending.target)
                except Exception:
                    return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
                after = self._fresh()
                if after is None or after.current != pending.target:
                    return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
                if not self._clear_marker():
                    return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
                return MetadataCommitReceipt(MetadataCommitOutcome.VERIFIED)
        except Exception:
            # Never report failure as "no write" after an uncertain effect.
            return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
