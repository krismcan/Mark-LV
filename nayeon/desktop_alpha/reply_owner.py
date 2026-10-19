"""Creator-thread fake reply owner, Phase 8.34 Increment A ONLY.

No Tk graph, scheduler, renderer or application wiring lives here. The later
bridge MUST anchor the entire interpreter graph until physical retirement and
check UI eligibility again at rendering seams. This module proves no Tk safety.
Trusted composition alone may bind context/admit an explicit human request;
an in-memory ticket cannot prove that a human actually pressed a button.
"""

import threading

from nayeon.desktop_alpha import reply_worker
from nayeon.desktop_alpha.reply_contracts import (
    DEADLINE_MS, MAX_CLOCK_MS, MAX_REQUEST_NUMBER, RefusalCode, ReplyRefused,
    ReplyContext, ReplyRequest, ReplyResult, ReplyState, ReplyTicket,
    valid_context, valid_prompt, valid_result,
)


# Capture defining-module anchors, never possibly replaced public aliases.
_WORKER = reply_worker._REVIEWED_WORKER
_RESPONDER = reply_worker._REVIEWED_RESPONDER
_EVENT = threading.Event
_MAILBOX = reply_worker.ReplyMailbox


class ReplyOwner:
    """One slot until exit + join(0), or positively proven never started.

    Both paths require bounded mailbox retirement before releasing the slot.
    Poison is an orthogonal, permanent admission block; it never implies that
    a live worker has retired. No destructor, daemon detachment or force-stop.
    Public methods/properties gate the creator thread before all other work.
    Clock values are trusted monotonic integer milliseconds, with no callback.
    """

    def __init__(self, root_identity: object):
        self._creator_thread = threading.get_ident()
        if type(root_identity) is not object:
            raise ReplyRefused(RefusalCode.AUTHORITY)
        self._root_identity = root_identity
        self._context = None
        self._state = ReplyState.IDLE
        self._poisoned = self._closing = self._transaction = False
        self._signalling = False
        self._thread = self._event = self._mailbox = None
        self._start_failed = False
        self._ticket = self._active = self._request = self._request_context = None
        self._deadline = self._clock = self._number = 0

    def _require_creator_thread(self):
        if threading.get_ident() != self._creator_thread:
            raise RuntimeError("WRONG_THREAD")

    @property
    def state(self) -> ReplyState:
        self._require_creator_thread()
        return self._state

    @property
    def poisoned(self) -> bool:
        self._require_creator_thread()
        return self._poisoned

    @property
    def has_worker(self) -> bool:
        self._require_creator_thread()
        return self._thread is not None

    def _revoke(self):
        self._require_creator_thread()
        self._active = None

    def _signal(self):
        self._require_creator_thread()
        # Callers ALWAYS revoke before this potentially uncertain operation.
        if self._event is None or self._signalling:
            return
        previous = self._transaction
        self._transaction = self._signalling = True
        try:
            self._event.set()
        except Exception:
            self._poisoned = True
        finally:
            self._signalling = False
            self._transaction = previous

    def _fault(self):
        self._require_creator_thread()
        self._revoke()
        self._poisoned = True
        if self._thread is not None:
            self._state = ReplyState.CLOSING if self._closing else ReplyState.DRAINING
        elif self._state is not ReplyState.DESTROYED:
            self._state = ReplyState.RETIRED
        self._signal()

    def _time(self, now_ms):
        self._require_creator_thread()
        if (type(now_ms) is not int or not self._clock <= now_ms <= MAX_CLOCK_MS):
            return False
        self._clock = now_ms
        return True

    def bind_context(self, context: ReplyContext) -> bool:
        """Navigation cannot replace a context until the worker is joined."""
        self._require_creator_thread()
        if (not valid_context(context) or context.root_identity is not self._root_identity
                or self._closing or self._poisoned or self._transaction):
            return False
        if self._thread is not None:
            if context is self._context:
                return True
            self.cancel(self._ticket)
            return False
        self._context = context
        return True

    def start(self, prompt: str, *, context: ReplyContext, now_ms: int,
              human_requested: bool) -> ReplyTicket:
        self._require_creator_thread()
        if self._closing or self._state is ReplyState.DESTROYED:
            raise ReplyRefused(RefusalCode.CLOSED)
        if self._poisoned:
            raise ReplyRefused(RefusalCode.POISONED)
        if self._transaction or self._thread is not None:
            raise ReplyRefused(RefusalCode.BUSY)
        if (human_requested is not True or context is not self._context
                or not valid_context(context)):
            raise ReplyRefused(RefusalCode.AUTHORITY)
        if not valid_prompt(prompt):
            raise ReplyRefused(RefusalCode.INPUT)
        if not self._time(now_ms) or now_ms > MAX_CLOCK_MS - DEADLINE_MS:
            raise ReplyRefused(RefusalCode.CLOCK)
        # Mutable module names must still denote the exact reviewed functions.
        if (reply_worker.run_fake_reply is not _WORKER
                or reply_worker._REVIEWED_WORKER is not _WORKER
                or reply_worker.simulated_reply is not _RESPONDER
                or reply_worker._REVIEWED_RESPONDER is not _RESPONDER
                or reply_worker.ReplyMailbox is not _MAILBOX
                or threading.Event is not _EVENT
                or self._number >= MAX_REQUEST_NUMBER):
            self._fault()
            raise ReplyRefused(RefusalCode.UNAVAILABLE)
        self._transaction = True
        self._start_failed = False
        try:
            self._number += 1
            self._request = ReplyRequest(self._number, prompt)
            self._request_context = context
            self._ticket = self._active = ReplyTicket()
            ticket = self._ticket
            self._deadline = now_ms + DEADLINE_MS
            self._state = ReplyState.RUNNING
            self._event = _EVENT()
            self._mailbox = _MAILBOX()
            self._thread = threading.Thread(
                target=_WORKER, args=(self._request, self._event, self._mailbox),
                daemon=False,
            )
            # Slot published before start: even a raise-after-start retains it.
            self._thread.start()
        except Exception:
            self._start_failed = self._thread is not None
            self._fault()
            raise ReplyRefused(RefusalCode.UNAVAILABLE) from None
        finally:
            self._transaction = False
        if self._active is not ticket:
            raise ReplyRefused(RefusalCode.UNAVAILABLE)
        return ticket

    def cancel(self, ticket: ReplyTicket) -> bool:
        self._require_creator_thread()
        if ticket is not self._ticket or ticket is None or self._thread is None:
            return False
        self._revoke()
        self._state = ReplyState.CLOSING if self._closing else ReplyState.DRAINING
        self._signal()
        return True

    def poison(self) -> None:
        """Future scheduler uncertainty: retain physical slot; no new poll."""
        self._require_creator_thread()
        self._fault()

    def request_close(self) -> None:
        self._require_creator_thread()
        if self._state is ReplyState.DESTROYED:
            return
        self._closing = True
        self._revoke()
        self._state = ReplyState.CLOSING if self._thread is not None else ReplyState.RETIRED
        self._signal()

    def poll(self, ticket: ReplyTicket, *, context: ReplyContext,
             now_ms: int) -> ReplyResult | None:
        """Return zero/one bounded result, consumed BEFORE returning to caller.

        Stale/copy callbacks have no effects, including no clock advancement.
        Cancelled tickets retain retirement access but never delivery authority.
        An empty mailbox after exit is terminal, not a request to wait/replay.
        """
        self._require_creator_thread()
        if (self._transaction or ticket is None or ticket is not self._ticket
                or self._thread is None):
            return None
        self._transaction = True
        try:
            # Serialize revocation/signalling too. A nested retirement at this
            # seam must not retire A, admit B, then let this stale A clear B.
            if not self._time(now_ms):
                self._fault()
            if self._clock >= self._deadline or context is not self._request_context:
                self.cancel(ticket)
            try:
                never_started = False
                if self._start_failed:
                    # CPython 3.12 registers a pending native launch in _limbo
                    # before spawning; bootstrap sets ident/_started BEFORE
                    # removing it under this lock. False is_alive() alone also
                    # describes a pending launch and cannot release its slot.
                    # Missing/uncertain evidence raises into retention below.
                    with threading._active_limbo_lock:
                        never_started = (self._thread.ident is None
                                         and not self._thread._started.is_set()
                                         and self._thread not in threading._limbo)
                if not never_started:
                    if self._thread.is_alive():
                        return None
                    self._thread.join(0)
                    if self._thread.is_alive():
                        self._fault()
                        return None
                invalid, result = self._mailbox._drain()
            except Exception:
                # Uncertain launch evidence/join/drain never releases the slot
                # or retries delivery. Explicit later retirement may discard.
                self._fault()
                return None
            if invalid or (result is not None and not valid_result(result, self._request)):
                self._fault()
            eligible = (self._active is ticket and context is self._context
                        and context is self._request_context and not self._poisoned
                        and not self._closing and self._clock < self._deadline)
            self._revoke()
            self._thread = self._event = self._mailbox = None
            self._ticket = self._request = self._request_context = None
            self._state = ReplyState.RETIRED
            return result if eligible else None
        except Exception:
            self._fault()
            return None
        finally:
            self._transaction = False

    def destroy(self) -> bool:
        """Logical retirement only; never destroys any widget or native root."""
        self._require_creator_thread()
        if self._thread is not None or self._transaction or not self._closing:
            return False
        self._revoke()
        self._context = None
        self._ticket = self._request = self._request_context = None
        self._event = self._mailbox = None
        self._state = ReplyState.DESTROYED
        return True

    def retire(self, *, now_ms: int) -> bool:
        """Explicit creator ingress for close/fault, including failed starts.

        This ingress always revokes delivery and never returns reply text. It
        does not create a timer or block on a worker that is still alive.
        """
        self._require_creator_thread()
        if self._transaction:
            return False
        if self._thread is None:
            return True
        ticket, context = self._ticket, self._request_context
        self.cancel(ticket)
        self.poll(ticket, context=context, now_ms=now_ms)
        return self._thread is None
