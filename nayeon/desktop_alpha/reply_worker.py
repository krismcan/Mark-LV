"""Exact module entrypoints for finite, constant, explicitly simulated work.

Only request/Event/mailbox are captured by the thread. No UI, callback,
provider, clock, SDK, persistence or action capability is accepted. This is a
direct-capture contract, not a claim about arbitrary process-wide reachability.
"""

from queue import Empty, Full, Queue
from threading import Event, Lock

from nayeon.desktop_alpha.reply_contracts import (
    ERROR_TEXT, SIMULATED_TEXT, ReplyKind, ReplyRequest, ReplyResult,
    valid_request, valid_result,
)


class ReplyMailbox:
    """Capacity one plus one activation/publication attempt for its lifetime.

    The owner drains only AFTER physical exit/join. Cancellation may race a
    raw put, but revoked owner authority can never trust that late data.
    Duplicate activation/publication taints the whole result, even after drain.
    """

    __slots__ = ("_lock", "_queue", "_activated", "_attempted", "_invalid", "_drained")

    def __init__(self):
        self._lock = Lock()
        self._queue = Queue(maxsize=1)
        self._activated = self._attempted = self._invalid = self._drained = False

    def _begin(self):
        with self._lock:
            if self._activated or self._drained:
                self._invalid = True
                return False
            self._activated = True
            return True

    def _invalidate(self):
        with self._lock:
            self._invalid = True

    def _publish(self, result, cancellation):
        with self._lock:
            if not self._activated or self._attempted or self._drained:
                self._invalid = True
                return
            self._attempted = True
            if cancellation.is_set():
                return
            if type(result) is not ReplyResult or not valid_result(result, result.request):
                self._invalid = True
                return
            try:
                self._queue.put_nowait(result)
            except Full:
                self._invalid = True

    def _drain(self):
        """Bounded read; caller must have observed physical exit and joined."""
        with self._lock:
            if self._drained:
                self._invalid = True
            self._drained = True
            try:
                result = self._queue.get_nowait()
            except Empty:
                result = None
            else:
                # A published None is malformed, not an empty mailbox.
                if type(result) is not ReplyResult:
                    self._invalid = True
            # Defensive duplicate detection; never loop on untrusted output.
            try:
                self._queue.get_nowait()
            except Empty:
                pass
            else:
                self._invalid = True
            return self._invalid, result


def simulated_reply(request: ReplyRequest) -> ReplyResult:
    """No echo, transformation, model inference, delay or external effect."""
    if not valid_request(request):
        raise ValueError("REPLY_INPUT")
    return ReplyResult(request, ReplyKind.SIMULATED, SIMULATED_TEXT)


def run_fake_reply(request: ReplyRequest, cancellation: Event, mailbox: ReplyMailbox):
    """Zero/one publication, no retry after an uncertain publication attempt."""
    if type(mailbox) is not ReplyMailbox:
        return
    try:
        if not mailbox._begin():
            return
        if (type(cancellation) is not Event or not valid_request(request)
                or run_fake_reply is not _REVIEWED_WORKER
                or simulated_reply is not _REVIEWED_RESPONDER):
            mailbox._invalidate()
            return
        if cancellation.is_set():
            return
        try:
            result = _REVIEWED_RESPONDER(request)
        except Exception:
            result = ReplyResult(request, ReplyKind.ERROR, ERROR_TEXT)
        if cancellation.is_set():
            return
        # Deliberately one call, including when a put raised after its effect.
        mailbox._publish(result, cancellation)
    except Exception:
        # Never expose exception text or attempt a replacement publication.
        mailbox._invalidate()


_REVIEWED_WORKER = run_fake_reply
_REVIEWED_RESPONDER = simulated_reply
