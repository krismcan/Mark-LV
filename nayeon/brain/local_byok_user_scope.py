"""P132: explicit offline, user-account Windows Credential Manager BYOK slice.

A deliberately *narrower* product model than privileged BYOK C1: no service,
privileged journal, antirollback claims, native consent broker, provider API,
network call, startup storage access, or credential export/read-back.

Actual Windows CredWrite/CredDelete are reachable only when the separately
launched, local human UI calls approve() on its exact one-use review. This is
NOT a cryptographic proof of human presence inside a compromised process.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import secrets
import threading

from nayeon.brain.windows_onboarding_mutex import (
    MutexAdmission, WindowsOnboardingMutex,
)
from nayeon.secrets.contracts import SecretIdentifier, SecretValue
from nayeon.secrets.windows_credential import WindowsCredentialBackend


_FIXED_IDENTIFIER = SecretIdentifier("openai.api_key")


class LocalByokOperation(str, Enum):
    SAVE = "save"
    REPLACE = "replace"
    REMOVE = "remove"


class LocalByokPresence(str, Enum):
    NOT_STORED = "not_stored"
    PRESENT_UNVALIDATED = "present_unvalidated"
    UNAVAILABLE = "unavailable"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class LocalByokOutcome(str, Enum):
    SUBMITTED_UNVALIDATED = "submitted_unvalidated"
    SUBMITTED_REMOVAL = "submitted_removal"
    REFUSED = "refused"
    CONFLICT = "conflict"
    BUSY = "busy"
    RECONCILIATION_REQUIRED = "reconciliation_required"


@dataclass(frozen=True, eq=False, slots=True, repr=False)
class LocalByokReview:
    operation: LocalByokOperation
    original_present: bool
    ticket: str

    def __repr__(self) -> str:
        return "LocalByokReview(<redacted>)"


class LocalByokController:
    """One user's optional offline credential workflow, not an agent tool.

    Exact WindowsCredentialBackend, one fixed target and cooperative
    session-wide WindowsOnboardingMutex. The private mutex test seam never
    changes the production factory. In-process review and uncertainty state
    vanish on restart: this is a known user-scope tradeoff, NOT G3 recovery.

    A credential slot's presence is not provider validity, ciphertext
    readback or durable verification. External/same-user writers that replace
    an existing value without changing presence cannot be detected here.
    """

    __slots__ = ("_backend", "_mutex", "_gate", "_pending", "_busy", "_uncertain")

    def __init__(self, backend: WindowsCredentialBackend, *, _mutex=None) -> None:
        if type(backend) is not WindowsCredentialBackend:
            raise TypeError("Exact user-account Windows credential backend required")
        self._backend = backend
        self._mutex = WindowsOnboardingMutex() if _mutex is None else _mutex
        self._gate = threading.RLock()
        self._pending: LocalByokReview | None = None
        self._busy = False
        self._uncertain = False

    def inspect_presence(self) -> LocalByokPresence:
        """Explicit refresh only: call CredRead metadata presence, never get()."""
        with self._gate:
            if self._uncertain:
                return LocalByokPresence.RECONCILIATION_REQUIRED
            if self._busy:
                return LocalByokPresence.UNAVAILABLE
            try:
                present = self._backend.is_available(_FIXED_IDENTIFIER)
                if type(present) is not bool:
                    raise TypeError("Invalid storage presence")
            except Exception:
                return LocalByokPresence.UNAVAILABLE
            return (LocalByokPresence.PRESENT_UNVALIDATED if present
                    else LocalByokPresence.NOT_STORED)

    def begin(self, operation: LocalByokOperation) -> LocalByokReview | None:
        """A separate manual review step; no write, validation or key retained."""
        with self._gate:
            if (type(operation) is not LocalByokOperation or self._pending is not None
                    or self._busy or self._uncertain):
                return None
            try:
                present = self._backend.is_available(_FIXED_IDENTIFIER)
                if type(present) is not bool:
                    return None
            except Exception:
                return None
            if (operation is LocalByokOperation.SAVE and present) or (
                operation in (LocalByokOperation.REPLACE, LocalByokOperation.REMOVE)
                and not present
            ):
                return None
            review = LocalByokReview(operation, present, secrets.token_hex(16))
            self._pending = review
            return review

    def reject(self, review: LocalByokReview | None) -> bool:
        with self._gate:
            if self._pending is not review or review is None or self._busy:
                return False
            self._pending = None
            return True

    def approve(
        self, review: LocalByokReview | None, *,
        confirmed: bool = False,
        candidate: SecretValue | None = None,
        deletion_acknowledged: bool = False,
    ) -> LocalByokOutcome:
        """Consumes the exact local review ONCE, then attempts bounded effect.

        All errors become fixed, non-secret outcomes. The mutex is held
        through presence re-observation and CredWrite/CredDelete submission.
        No automatic retry, network, provider validation or secret read.
        """
        with self._gate:
            if (self._pending is not review or review is None
                    or type(review) is not LocalByokReview or self._busy):
                return LocalByokOutcome.REFUSED
            self._pending = None  # consumption BEFORE any delegated/native call
            if confirmed is not True or self._uncertain:
                return LocalByokOutcome.REFUSED

            if review.operation in (LocalByokOperation.SAVE, LocalByokOperation.REPLACE):
                if type(candidate) is not SecretValue or deletion_acknowledged is not False:
                    return LocalByokOutcome.REFUSED
            elif review.operation is LocalByokOperation.REMOVE:
                if candidate is not None or deletion_acknowledged is not True:
                    return LocalByokOutcome.REFUSED
            else:
                return LocalByokOutcome.REFUSED

            self._busy = True
            try:
                with self._mutex.hold() as admission:
                    if admission is MutexAdmission.BUSY:
                        return LocalByokOutcome.BUSY
                    if admission is not MutexAdmission.HELD:
                        self._uncertain = True
                        return LocalByokOutcome.RECONCILIATION_REQUIRED

                    present = self._backend.is_available(_FIXED_IDENTIFIER)
                    if type(present) is not bool or present != review.original_present:
                        # A change of presence is visible; same-presence ABA
                        # and external writers remain outside this model.
                        return LocalByokOutcome.CONFLICT

                    if review.operation is LocalByokOperation.REMOVE:
                        removed = self._backend.delete(_FIXED_IDENTIFIER)
                        if type(removed) is not bool or not removed:
                            self._uncertain = True
                            return LocalByokOutcome.RECONCILIATION_REQUIRED
                        expected = False
                    else:
                        self._backend.put(_FIXED_IDENTIFIER, candidate)
                        expected = True

                    now_present = self._backend.is_available(_FIXED_IDENTIFIER)
                    if type(now_present) is not bool or now_present != expected:
                        self._uncertain = True
                        return LocalByokOutcome.RECONCILIATION_REQUIRED
                    return (LocalByokOutcome.SUBMITTED_REMOVAL
                            if review.operation is LocalByokOperation.REMOVE
                            else LocalByokOutcome.SUBMITTED_UNVALIDATED)
            except Exception:
                # CredWrite may have happened before its exception. Never
                # claim no change or retry automatically.
                self._uncertain = True
                return LocalByokOutcome.RECONCILIATION_REQUIRED
            finally:
                self._busy = False

    def __repr__(self) -> str:
        return "LocalByokController(<redacted>)"

    __str__ = __repr__


def compose_user_scope_local_byok() -> LocalByokController:
    """Explicit interactive entry only; construction never touches WinCred."""
    return LocalByokController(WindowsCredentialBackend())
