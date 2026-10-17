"""Phase 8.31 increment A: pure, synchronous, ephemeral offline state owner.

STATIC / UNTESTED pending authoritative host execution. No UI or effect wiring.
The trusted application supplies fresh opaque root/pane objects and monotonic
integer milliseconds for human reset reviews. Text can never select authority.
Review issuance must follow a genuine human Review gesture in the future UI;
an in-memory token cannot establish that a human actually clicked a button.

Only records and snapshots are immutable; the owner replaces its private state.
Terminal tickets are not retained in a growing replay ledger. Exact active-slot
identity rejects copies and replays. This is a single-thread owner, not a sandbox
against hostile arbitrary Python code or a cross-thread synchronisation service.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata


MAX_INPUT_CODE_POINTS = 512
MAX_INPUT_UTF8_BYTES = 2048
MAX_ENTRIES = 64
MAX_TRANSCRIPT_UTF8_BYTES = 65536
MAX_STATUS_CHARACTERS = 160
RESET_REVIEW_TTL_MS = 30000
MAX_CLOCK_MS = (1 << 63) - 1
OFFLINE_STATUS = "UNSENT / OFFLINE: Saved in this session only. No AI request or action was performed."


class EntrySource(Enum):
    USER = "USER"
    LOCAL_STATUS = "LOCAL_STATUS"


class EntryState(Enum):
    UNSENT_OFFLINE = "UNSENT_OFFLINE"
    BLOCKED = "BLOCKED"


class SubmissionState(Enum):
    ISSUED = "ISSUED"
    CLAIMED = "CLAIMED"
    COMMITTED = "COMMITTED"
    REVOKED = "REVOKED"


class ResetOperation(Enum):
    CLEAR = "CLEAR"
    NEW_SESSION = "NEW_SESSION"


class RefusalCode(Enum):
    AUTHORITY = "This conversation callback is no longer current."
    BUSY = "An offline submission is already active."
    INPUT = "Use 1-512 NFC Unicode characters, at most 2048 UTF-8 bytes, without controls or line breaks."
    FULL = "Session full. Review Clear or New session before submitting more text."
    REVIEW = "This reset review is no longer current. Review the command again."
    CLOCK = "Reset review time is invalid. Review the command again."
    CLOSED = "This offline conversation is closed."


class SessionRefused(RuntimeError):
    """Fixed bounded public status; never interpolate an input or exception."""

    def __init__(self, code: RefusalCode) -> None:
        self.code = code
        super().__init__(code.value)


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ConversationView:
    identity: object
    generation: int


@dataclass(frozen=True, slots=True, repr=False)
class ConversationEntry:
    sequence: int
    source: EntrySource
    state: EntryState
    payload: str
    byte_count: int


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class SessionSnapshot:
    session_identity: object
    epoch: int
    revision: int
    entries: tuple[ConversationEntry, ...]
    byte_count: int
    closed: bool


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class OfflineSubmission:
    pane: ConversationView
    session_identity: object
    epoch: int
    revision: int
    nonce: object
    payload: str
    byte_count: int


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ResetReview:
    pane: ConversationView
    operation: ResetOperation
    session_identity: object
    epoch: int
    revision: int
    nonce: object
    expires_at_ms: int


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class OfflineCommit:
    submission: OfflineSubmission
    state: SubmissionState
    snapshot: SessionSnapshot


@dataclass(frozen=True, slots=True, repr=False)
class _ActiveSubmission:
    ticket: OfflineSubmission
    state: SubmissionState


def validate_offline_text(candidate: str) -> int:
    """Validate the entire literal without normalising/trimming or retaining it.

    Returns its strict UTF-8 payload cost. Exact str prevents hostile subclass
    conversion/equality/encoding callbacks. Supplementary characters count once.
    This can also be used by future proposed-value widget validation.
    """
    if type(candidate) is not str or not 1 <= len(candidate) <= MAX_INPUT_CODE_POINTS:
        raise SessionRefused(RefusalCode.INPUT)
    for character in candidate:
        if (unicodedata.category(character) in {"Cc", "Cf", "Cs"}
                or character in {"\u2028", "\u2029"}):
            raise SessionRefused(RefusalCode.INPUT)
    if not candidate.strip() or unicodedata.normalize("NFC", candidate) != candidate:
        raise SessionRefused(RefusalCode.INPUT)
    try:
        byte_count = len(candidate.encode("utf-8", errors="strict"))
    except UnicodeError:
        raise SessionRefused(RefusalCode.INPUT) from None
    if byte_count > MAX_INPUT_UTF8_BYTES:
        raise SessionRefused(RefusalCode.INPUT)
    return byte_count


class OfflineConversationSession:
    """One trusted root, one live pane, one request and one human reset review.

    The root is held only privately, never in display snapshots or issued tokens.
    Exact active-slot ownership binds tokens transitively to that root. A copied
    token with identical fields is data, not authority. Revocation/close may run
    during validation; normal reentrant admission is refused. No callbacks,
    clocks, providers, storage, logging or background work are injected here.
    """

    def __init__(self, root_identity: object) -> None:
        if type(root_identity) is not object:
            raise SessionRefused(RefusalCode.AUTHORITY)
        self._root_identity = root_identity
        self._snapshot = SessionSnapshot(object(), 1, 0, (), 0, False)
        self._view: ConversationView | None = None
        self._view_generation = 0
        self._active: _ActiveSubmission | None = None
        self._review: ResetReview | None = None
        self._busy: object | None = None
        self._sequence = 0
        self._clock_ms = 0

    @property
    def snapshot(self) -> SessionSnapshot:
        """The single cached immutable display snapshot; no authority to mutate."""
        return self._snapshot

    @property
    def active_submission_state(self) -> SubmissionState | None:
        return None if self._active is None else self._active.state

    def _root_current(self, root: object) -> bool:
        return root is self._root_identity and not self._snapshot.closed

    def _current(self, root: object, pane: ConversationView) -> bool:
        return (self._root_current(root) and type(pane) is ConversationView
                and pane is self._view)

    def _require_current(self, root: object, pane: ConversationView) -> None:
        if not self._current(root, pane):
            raise SessionRefused(RefusalCode.AUTHORITY)

    def _same_transcript(self, identity: object, epoch: int, revision: int) -> bool:
        snapshot = self._snapshot
        return (snapshot.session_identity is identity and snapshot.epoch == epoch
                and snapshot.revision == revision and not snapshot.closed)

    def _revoke_work(self) -> None:
        self._active = None
        self._review = None
        self._busy = None

    def activate_view(self, root: object, identity: object) -> ConversationView:
        """Trusted navigation: revoke the previous pane, preserving history."""
        if not self._root_current(root):
            raise SessionRefused(RefusalCode.AUTHORITY)
        if type(identity) is not object or identity is self._root_identity:
            raise SessionRefused(RefusalCode.AUTHORITY)
        self._revoke_work()
        self._view_generation += 1
        pane = ConversationView(identity, self._view_generation)
        self._view = pane
        return pane

    def revoke_view(self, root: object, pane: ConversationView) -> bool:
        """Child Destroy/navigation does not close the application session."""
        if not self._current(root, pane):
            return False
        self._revoke_work()
        self._view = None
        return True

    def issue_submission(self, root: object, pane: ConversationView,
                         candidate: str) -> OfflineSubmission:
        self._require_current(root, pane)
        if self._active is not None or self._busy is not None:
            raise SessionRefused(RefusalCode.BUSY)
        before, operation = self._snapshot, object()
        self._busy = operation
        try:
            byte_count = validate_offline_text(candidate)
            # Validation is pure in production; retain this boundary for
            # adversarial reentrancy/future callers. Never clear a successor.
            self._require_current(root, pane)
            if (self._busy is not operation or self._active is not None
                    or not self._same_transcript(before.session_identity,
                                                 before.epoch, before.revision)):
                raise SessionRefused(RefusalCode.AUTHORITY)
            ticket = OfflineSubmission(pane, before.session_identity, before.epoch,
                                       before.revision, object(), candidate, byte_count)
            self._active = _ActiveSubmission(ticket, SubmissionState.ISSUED)
            return ticket
        finally:
            if self._busy is operation:
                self._busy = None

    def _request_current(self, root: object, pane: ConversationView,
                         ticket: OfflineSubmission, state: SubmissionState) -> bool:
        return (self._current(root, pane) and type(ticket) is OfflineSubmission
                and self._active is not None and self._active.ticket is ticket
                and self._active.state is state and ticket.pane is pane
                and self._same_transcript(ticket.session_identity,
                                          ticket.epoch, ticket.revision))

    def claim_submission(self, root: object, pane: ConversationView,
                         ticket: OfflineSubmission) -> None:
        if not self._request_current(root, pane, ticket, SubmissionState.ISSUED):
            raise SessionRefused(RefusalCode.AUTHORITY)
        if self._busy is not None:
            raise SessionRefused(RefusalCode.BUSY)
        self._active = _ActiveSubmission(ticket, SubmissionState.CLAIMED)

    def revoke_submission(self, root: object, ticket: OfflineSubmission) -> bool:
        """A's cleanup can revoke only A, regardless of pane/session changes."""
        if (not self._root_current(root) or type(ticket) is not OfflineSubmission
                or self._active is None or self._active.ticket is not ticket):
            return False
        self._active = None  # ISSUED/CLAIMED -> REVOKED; no terminal ledger.
        if self._busy is ticket:
            self._busy = None
        return True

    def commit_submission(self, root: object, pane: ConversationView,
                          ticket: OfflineSubmission) -> OfflineCommit:
        if not self._request_current(root, pane, ticket, SubmissionState.CLAIMED):
            raise SessionRefused(RefusalCode.AUTHORITY)
        if self._busy is not None:
            raise SessionRefused(RefusalCode.BUSY)
        self._busy = ticket
        try:
            byte_count = validate_offline_text(ticket.payload)
            if (self._busy is not ticket or not self._request_current(
                    root, pane, ticket, SubmissionState.CLAIMED)):
                raise SessionRefused(RefusalCode.AUTHORITY)
            if byte_count != ticket.byte_count:
                raise SessionRefused(RefusalCode.INPUT)
            before = self._snapshot
            status_bytes = len(OFFLINE_STATUS.encode("utf-8", errors="strict"))
            pair_bytes = byte_count + status_bytes
            if (len(before.entries) + 2 > MAX_ENTRIES
                    or before.byte_count + pair_bytes > MAX_TRANSCRIPT_UTF8_BYTES):
                raise SessionRefused(RefusalCode.FULL)
            pair = (
                ConversationEntry(self._sequence + 1, EntrySource.USER,
                                  EntryState.UNSENT_OFFLINE, ticket.payload, byte_count),
                ConversationEntry(self._sequence + 2, EntrySource.LOCAL_STATUS,
                                  EntryState.UNSENT_OFFLINE, OFFLINE_STATUS, status_bytes),
            )
            after = SessionSnapshot(before.session_identity, before.epoch,
                                    before.revision + 1, before.entries + pair,
                                    before.byte_count + pair_bytes, False)
            result = OfflineCommit(ticket, SubmissionState.COMMITTED, after)
            # Everything, including the return record, is built before the one
            # transcript publication. No externally supplied code follows it.
            self._review = None
            self._sequence += 2
            self._active = None
            self._snapshot = after
            return result
        except BaseException:
            self.revoke_submission(root, ticket)
            raise
        finally:
            if self._busy is ticket:
                self._busy = None

    def submit(self, root: object, pane: ConversationView, candidate: str) -> OfflineCommit:
        """Synchronous convenience path through the exact same ticket lifecycle."""
        ticket = self.issue_submission(root, pane, candidate)
        try:
            self.claim_submission(root, pane, ticket)
            return self.commit_submission(root, pane, ticket)
        except BaseException:
            self.revoke_submission(root, ticket)
            raise

    def _observe_clock(self, now_ms: int) -> None:
        if (type(now_ms) is not int or not self._clock_ms <= now_ms <= MAX_CLOCK_MS):
            raise SessionRefused(RefusalCode.CLOCK)
        self._clock_ms = now_ms

    def begin_reset_review(self, root: object, pane: ConversationView,
                           operation: ResetOperation, *, now_ms: int) -> ResetReview:
        """Trusted explicit human Review; supersedes any prior review instance."""
        self._require_current(root, pane)
        if type(operation) is not ResetOperation:
            raise SessionRefused(RefusalCode.REVIEW)
        if self._busy is not None:
            raise SessionRefused(RefusalCode.BUSY)
        self._observe_clock(now_ms)
        if now_ms > MAX_CLOCK_MS - RESET_REVIEW_TTL_MS:
            raise SessionRefused(RefusalCode.CLOCK)
        snapshot = self._snapshot
        review = ResetReview(pane, operation, snapshot.session_identity, snapshot.epoch,
                             snapshot.revision, object(), now_ms + RESET_REVIEW_TTL_MS)
        self._review = review
        return review

    def _review_current(self, root: object, pane: ConversationView,
                        review: ResetReview) -> bool:
        return (self._current(root, pane) and type(review) is ResetReview
                and self._review is review and review.pane is pane
                and self._same_transcript(review.session_identity,
                                          review.epoch, review.revision))

    def dismiss_reset_review(self, root: object, review: ResetReview) -> bool:
        """Exact cleanup only; never let stale callback A dismiss replacement B."""
        if (not self._root_current(root) or type(review) is not ResetReview
                or self._review is not review):
            return False
        self._review = None
        return True

    def expire_reset_review(self, root: object, pane: ConversationView,
                            review: ResetReview, *, now_ms: int) -> bool:
        if not self._review_current(root, pane, review):
            return False
        self._observe_clock(now_ms)
        if now_ms < review.expires_at_ms:
            return False
        self._review = None
        return True

    def confirm_reset(self, root: object, pane: ConversationView, review: ResetReview,
                      operation: ResetOperation, *, now_ms: int) -> SessionSnapshot:
        if (not self._review_current(root, pane, review)
                or type(operation) is not ResetOperation or operation is not review.operation):
            raise SessionRefused(RefusalCode.REVIEW)
        if self._busy is not None:
            raise SessionRefused(RefusalCode.BUSY)
        self._observe_clock(now_ms)
        if now_ms >= review.expires_at_ms:
            self._review = None
            raise SessionRefused(RefusalCode.REVIEW)
        # Consume the identical review BEFORE reset. No callbacks/I/O occur.
        self._review = None
        self._active = None
        before = self._snapshot
        new_session = operation is ResetOperation.NEW_SESSION
        self._snapshot = SessionSnapshot(
            object() if new_session else before.session_identity,
            before.epoch + int(new_session), before.revision + 1, (), 0, False)
        return self._snapshot

    def close(self, root: object) -> bool:
        """Terminal application-only revocation; call before root destruction.

        Discards owner-retained text. Previously handed-out immutable snapshots
        cannot be erased from callers; this is not secure memory zeroisation.
        """
        if root is not self._root_identity:
            raise SessionRefused(RefusalCode.AUTHORITY)
        if self._snapshot.closed:
            return False
        self._revoke_work()
        self._view = None
        before = self._snapshot
        self._snapshot = SessionSnapshot(before.session_identity, before.epoch,
                                         before.revision + 1, (), 0, True)
        return True
