"""Creator-thread admission for a bounded fake offline status completion.

This helper owns the sole one-shot simulation registration for an application
root. It grants no model, provider, action or transcript-writing authority.
Scheduler uncertainty is terminal until the actual root is destroyed.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
import threading

from nayeon.desktop_alpha.conversation_session import (
    ConversationEntry, EntrySource, EntryState, OfflineCommit, OfflineSubmission,
    SessionSnapshot, SubmissionState,
)

WAITING = "Waiting for local offline simulation. No AI request or action was performed."
COMPLETE = "Local offline simulation complete; no AI request or action occurred."
UNAVAILABLE = "Local simulation unavailable. Saved offline only; no AI request or action occurred."
CANCELLED = "Local simulation cancelled. Saved offline only; no AI request or action occurred."
MAX_REQUEST_INDEX = 65535


class CompletionState(Enum):
    IDLE = "idle"
    REGISTERING = "registering"
    PENDING = "pending"
    CANCELLING = "cancelling"
    POISONED = "poisoned"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class _CompletionTicket:
    owner: object
    pane: object
    generation: int
    index: int
    operation: object
    snapshot: SessionSnapshot
    final_sequence: tuple[int, int]


class DelayedOfflineCompletion:
    """One root, one potential physical timer, no workers and no polling.

    Trusted composition supplies pure snapshot/current readers and bounded UI
    rendering. The opaque active slot, not the request integer, admits delivery.
    Failed scheduler calls conservatively retain one possible orphan until root
    destruction. No cancellation guess, retry, or replacement follows a failure.
    """

    def __init__(self, root):
        self._creator_thread = threading.get_ident()
        self._root = root
        self._owner = object()
        self._state = CompletionState.IDLE
        self._transaction = False
        self._pending = None
        self._handle = None
        self._index = 0
        self._delivery_authority = object()
        self._read_snapshot = self._current = self._render = None

    def _require_creator_thread(self):
        if threading.get_ident() != self._creator_thread:
            raise RuntimeError("WRONG_THREAD")

    @property
    def state(self):
        self._require_creator_thread()
        return self._state

    def _revoke(self):
        self._delivery_authority = object()
        self._pending = None
        self._read_snapshot = self._current = self._render = None

    def is_pending_for(self, snapshot):
        self._require_creator_thread()
        return (self._state is CompletionState.PENDING and self._pending is not None
                and self._pending.snapshot is snapshot)

    def _poison(self):
        self._revoke()
        self._handle = None
        if self._state is not CompletionState.CLOSED:
            self._state = CompletionState.POISONED

    def destroyed(self):
        """Actual root retirement; pure Python even during external Destroy."""
        self._require_creator_thread()
        self._revoke()
        self._handle = None
        self._state = CompletionState.CLOSED

    def pane_destroyed(self):
        """External child Destroy cannot cancel Tcl or declare the root closed.

        An unretired registration is conservatively counted until root destroy.
        A pane destroyed after ordinary navigation cancellation leaves IDLE.
        """
        self._require_creator_thread()
        self._revoke()
        if self._state not in {CompletionState.IDLE, CompletionState.CLOSED}:
            self._poison()

    def publication_failed(self):
        self._require_creator_thread()
        self.cancel()
        self._poison()

    def cancel(self):
        """Revoke first; retire only the exact returned owned registration."""
        self._require_creator_thread()
        self._revoke()
        if self._transaction:
            # The outer transaction alone owns publication/cancellation.
            return False
        if self._state is CompletionState.IDLE:
            return True
        if self._state is not CompletionState.PENDING:
            return False
        handle, self._handle = self._handle, None
        return self._cancel_handle(handle)

    def _cancel_handle(self, handle):
        self._require_creator_thread()
        if self._state in {CompletionState.CLOSED, CompletionState.POISONED}:
            return False
        self._state = CompletionState.CANCELLING
        self._transaction = True
        try:
            self._root.after_cancel(handle)
        except Exception:
            self._poison()
            return False
        finally:
            self._transaction = False
        if self._state is CompletionState.CANCELLING:
            self._state = CompletionState.IDLE
            return True
        return False

    def start(self, commit, *, pane, generation, read_snapshot, current, render):
        """Admit only an exact successful POSTCOMMIT snapshot; never submit text.

        A valid successor commit retires A before B admission. Rejected Sends
        never call this method. An in-flight transaction refuses B simulation
        without undoing B's already accurate immutable offline transcript.
        """
        self._require_creator_thread()
        if (type(commit) is not OfflineCommit or commit.state is not SubmissionState.COMMITTED
                or type(commit.snapshot) is not SessionSnapshot
                or type(commit.submission) is not OfflineSubmission
                or type(generation) is not int or generation < 0 or pane is None):
            return False
        snapshot = commit.snapshot
        if snapshot.closed or len(snapshot.entries) < 2:
            return False
        user, status = snapshot.entries[-2:]
        if (type(user) is not ConversationEntry or type(status) is not ConversationEntry
                or user.source is not EntrySource.USER or status.source is not EntrySource.LOCAL_STATUS
                or user.state is not EntryState.UNSENT_OFFLINE
                or status.state is not EntryState.UNSENT_OFFLINE
                or status.sequence != user.sequence + 1
                or commit.submission.session_identity is not snapshot.session_identity
                or commit.submission.epoch != snapshot.epoch
                or commit.submission.revision + 1 != snapshot.revision):
            return False
        if self._transaction:
            self._revoke()
            return False
        if self._state is CompletionState.PENDING and not self.cancel():
            return False
        if self._state is not CompletionState.IDLE or self._index >= MAX_REQUEST_INDEX:
            return False
        self._index += 1
        ticket = _CompletionTicket(self._owner, pane, generation, self._index,
                                   object(), snapshot, (user.sequence, status.sequence))
        self._pending = ticket
        self._read_snapshot, self._current, self._render = read_snapshot, current, render
        self._state = CompletionState.REGISTERING
        self._transaction = True
        try:
            # Serialize ALL callback seams, including pre-registration checks.
            # A nested Send can commit, but cannot publish a second timer.
            valid = current()
            if (not valid or self._pending is not ticket
                    or self._state is not CompletionState.REGISTERING):
                if self._state is CompletionState.REGISTERING:
                    self._revoke()
                    self._state = CompletionState.IDLE
                return False
            observed = read_snapshot()
            if (observed is not snapshot or self._pending is not ticket
                    or self._state is not CompletionState.REGISTERING):
                if self._state is CompletionState.REGISTERING:
                    self._revoke()
                    self._state = CompletionState.IDLE
                return False
            handle = self._root.after(150, lambda: self._deliver(ticket))
            if type(handle) is not str or not handle:
                raise RuntimeError("INVALID_TIMER_HANDLE")
        except Exception:
            self._poison()
            return False
        finally:
            self._transaction = False
        if self._state in {CompletionState.CLOSED, CompletionState.POISONED}:
            return False
        if self._pending is not ticket:
            return self._cancel_handle(handle) and False
        self._handle = handle
        self._state = CompletionState.PENDING
        return True

    def _deliver(self, ticket):
        self._require_creator_thread()
        if self._pending is not ticket or ticket.owner is not self._owner:
            return
        if self._state is CompletionState.REGISTERING:
            # A scheduler that dispatches synchronously cannot publish success.
            # Its returned handle still must be retired by the outer start.
            self._revoke()
            return
        if self._state is not CompletionState.PENDING or self._transaction:
            return
        current, read_snapshot, render = self._current, self._read_snapshot, self._render
        # Consume BEFORE any external seam or best-effort UI operation.
        self._revoke()
        self._handle = None
        self._state = CompletionState.IDLE
        delivery_authority = self._delivery_authority
        try:
            if (not current() or self._delivery_authority is not delivery_authority
                    or self._index != ticket.index or self._state is not CompletionState.IDLE):
                return
            snapshot = read_snapshot()
            if (snapshot is not ticket.snapshot or snapshot.closed
                    or snapshot.session_identity is not ticket.snapshot.session_identity
                    or snapshot.epoch != ticket.snapshot.epoch
                    or snapshot.revision != ticket.snapshot.revision
                    or tuple(e.sequence for e in snapshot.entries[-2:]) != ticket.final_sequence
                    or self._delivery_authority is not delivery_authority
                    or self._index != ticket.index or self._state is not CompletionState.IDLE):
                return
            def eligible():
                self._require_creator_thread()
                return (self._delivery_authority is delivery_authority
                        and self._index == ticket.index
                        and self._state is CompletionState.IDLE)
            # The UI rechecks this pure probe after its own current-view seam.
            # Cancellation or a nested B must not be overwritten by A's status.
            render(COMPLETE, eligible)
        except Exception:
            # An uncertain dependency or display never replays and never permits
            # further registration on this root. Exception text stays private.
            self._poison()
