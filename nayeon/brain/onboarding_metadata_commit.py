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
import secrets
import time
from collections.abc import Callable

from nayeon.brain.connection_document import (
    ProviderConnectionDocumentV1, parse_provider_connection_document,
)
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.windows_onboarding_mutex import MutexAdmission, WindowsOnboardingMutex
from nayeon.brain.onboarding_recovery import TrustedOnboardingRecoveryController, RecoveryAdmissionError
from nayeon.brain.onboarding_recovery_evidence import canonical_evidence_digest


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
    epoch: str | None = None
    generation: int | None = None


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

    __slots__ = ("_path", "_store", "_mutex", "_clock", "_timeout", "_pending", "_recovery", "_ui_ticket", "_ui_owner")

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
        # Only default trusted production composition uses the new recovery
        # authority. Historical explicitly injected fake mutexes remain solely
        # for compatibility with sealed fake-only regression fixtures.
        self._recovery = TrustedOnboardingRecoveryController.for_path(metadata_path, mutex=mutex)
        self._clock = clock
        self._timeout = float(timeout_seconds)
        self._pending: _Pending | None = None
        self._ui_ticket: str | None = None
        self._ui_owner: str | None = None

    @property
    def recovery_controller(self):
        return self._recovery

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
        if self._recovery is not None and not self._recovery.ready:
            return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
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
        self._pending = _Pending(operation, before, target, deadline,
                                 None if self._recovery is None else self._recovery.epoch,
                                 None if self._recovery is None else self._recovery.generation)
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

    def claim_ui_owner(self) -> str | None:
        """One UI owns this host's pending-review namespace at a time."""
        if self._ui_owner is not None:
            if self._recovery.is_ui_window_owner(self._ui_owner):
                return None
            # A trusted explicit reconciliation restart invalidated the old
            # token. A fresh claim must still compete with any other owner.
            self._ui_owner = None
        self._ui_owner = self._recovery.claim_ui_window_owner()
        return self._ui_owner

    def has_ui_owner(self, *, owner: str | None) -> bool:
        return (type(owner) is str and self._ui_owner is not None and
                secrets.compare_digest(owner, self._ui_owner) and
                self._recovery.is_ui_window_owner(owner))

    def release_ui_owner(self, *, owner: str | None) -> bool:
        if not self.has_ui_owner(owner=owner):
            return False
        if not self._recovery.release_ui_window_owner(owner):
            return False
        if self._ui_ticket is not None:
            self._ui_ticket = None
            self._pending = None
        self._ui_owner = None
        return True

    def request_ui_save(self, model: str, *, owner: str | None = None
                        ) -> tuple[MetadataCommitReceipt, str | None]:
        return self._request_ui(MetadataOperation.SAVE, model, owner=owner)

    def request_ui_clear(self, *, owner: str | None = None
                         ) -> tuple[MetadataCommitReceipt, str | None]:
        return self._request_ui(MetadataOperation.CLEAR, None, owner=owner)

    def _request_ui(self, operation: MetadataOperation, model: str | None, *, owner: str | None
                    ) -> tuple[MetadataCommitReceipt, str | None]:
        """Human UI gets one-use ticket for the exact review; foreign UI denied."""
        if not self.has_ui_owner(owner=owner):
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED), None
        if self._ui_ticket is not None or self.has_pending:
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED), None
        # Acquire all nonce material BEFORE opening the pending review:
        # RNG failure must never leave a raw approvable ticketless review.
        ticket = secrets.token_hex(16)
        result = self.request_save(model) if operation is MetadataOperation.SAVE else self.request_clear()
        if result.outcome is not MetadataCommitOutcome.PENDING:
            return result, None
        self._ui_ticket = ticket
        return result, ticket

    def pending_ui_operation(self, *, ticket: str, owner: str | None = None) -> MetadataOperation | None:
        if (not self.has_ui_owner(owner=owner) or
                type(ticket) is not str or self._ui_ticket is None or
                not secrets.compare_digest(ticket, self._ui_ticket) or self._pending is None):
            return None
        return self._pending.operation

    def reject_ui(self, *, ticket: str, owner: str | None = None) -> MetadataCommitReceipt:
        if self.pending_ui_operation(ticket=ticket, owner=owner) is None:
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
        self._ui_ticket = None
        self._pending = None
        return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)

    def approve_ui(self, *, ticket: str, operation: MetadataOperation,
                   human_approved: bool, clear_acknowledged: bool = False,
                   owner: str | None = None) -> MetadataCommitReceipt:
        """No foreign, stale, wrong-operation, or unacknowledged CLEAR can execute."""
        if (type(operation) is not MetadataOperation or
                type(human_approved) is not bool or
                type(clear_acknowledged) is not bool or
                not human_approved or
                self.pending_ui_operation(ticket=ticket, owner=owner) is not operation or
                (operation is MetadataOperation.CLEAR and not clear_acknowledged)):
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
        self._ui_ticket = None
        return self.approve(human_approved=True)

    def reject(self) -> MetadataCommitReceipt:
        if self._ui_ticket is not None:
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
        self._pending = None
        return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)

    def approve(self, *, human_approved: bool) -> MetadataCommitReceipt:
        """Trusted legacy direct review; UI-owned reviews require matching ticket."""
        if self._ui_ticket is not None:
            return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)
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
        if self._recovery is None:
            return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
        return self._approve_recovered(pending)

    def _approve_recovered(self, pending: _Pending) -> MetadataCommitReceipt:
        """Production-only tenure-bound, verified write-ahead metadata approval."""
        ctrl = self._recovery
        if (not ctrl.ready or pending.epoch != ctrl.epoch or
                pending.generation != ctrl.generation or self._recovering()):
            return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
        before = self._fresh()
        if before is None or before != pending.before:
            return MetadataCommitReceipt(MetadataCommitOutcome.CONFLICT)
        # Fingerprint is exclusively nonsecret canonical metadata and file state.
        fingerprint = canonical_evidence_digest(
            kind="save_metadata" if pending.operation is MetadataOperation.SAVE else "clear_metadata",
            before=pending.before.current, after=pending.target,
            identity=pending.before.identity)
        try:
            permit = ctrl.begin_operation(
                kind="save_metadata" if pending.operation is MetadataOperation.SAVE else "clear_metadata",
                evidence_hash=fingerprint, epoch=pending.epoch, generation=pending.generation)
        except RecoveryAdmissionError:
            return MetadataCommitReceipt(MetadataCommitOutcome.RECOVERY_REQUIRED)
        verified = False
        try:
            self._store.save(pending.target)
            after = self._fresh()
            verified = after is not None and after.current == pending.target
        except Exception:
            verified = False
        try:
            confirmed = ctrl.finish_operation(permit, verified=verified)
        except RecoveryAdmissionError:
            confirmed = False
        return MetadataCommitReceipt(
            MetadataCommitOutcome.VERIFIED if confirmed else MetadataCommitOutcome.RECOVERY_REQUIRED)
