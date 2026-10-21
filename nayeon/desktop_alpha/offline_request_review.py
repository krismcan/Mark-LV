"""Phase 8.36 increment A: pure OFFLINE-only prompt review owner.

No Tk/widget, provider, file, secret, network, action, SDK, callbacks, clock
reads or arbitrary writable object graphs enter this owner. The trusted app
alone must verify displayed text and final widget state before calling arm().
This class makes no claim to prove a physical human click. Receipts never
confer transmission, action, persistence, or AI-response authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import threading

from nayeon.desktop_alpha.conversation_session import (
    SessionRefused, validate_offline_text,
)


MAX_CLOCK_MS = (1 << 63) - 1
REVIEW_TTL_MS = 30_000
DISCLOSURE = (
    "OFFLINE REVIEW ONLY - NO AI REQUEST, CREDENTIAL ACCESS, OR ACTION. "
    "MODEL NOT CONNECTED - OFFLINE PREVIEW ONLY."
)
RECEIPT_TEXT = "REVIEWED OFFLINE - NO AI REQUEST OR ACTION WAS SENT."


class ReviewState(Enum):
    IDLE = "IDLE"
    PREVIEW = "PREVIEW"
    ENABLING = "ENABLING"
    ARMED = "ARMED"
    POISONED = "POISONED"
    CLOSED = "CLOSED"


class ReviewRefused(RuntimeError):
    """Public refusal codes never include user input or exception internals."""


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ReviewContext:
    root: object
    pane: object
    session: object
    generation: int
    epoch: int
    revision: int


@dataclass(frozen=True, slots=True, repr=False)
class OfflineReviewPreview:
    prompt: str
    disclosure: str = DISCLOSURE


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ReviewTicket:
    pass


@dataclass(frozen=True, slots=True, repr=False)
class OfflineReviewReceipt:
    status: str = RECEIPT_TEXT
    permits_network: bool = False
    permits_action: bool = False
    permits_persistence: bool = False

    def __post_init__(self) -> None:
        if (self.status != RECEIPT_TEXT or self.permits_network is not False
                or self.permits_action is not False
                or self.permits_persistence is not False):
            raise ValueError("OFFLINE_RECEIPT_ONLY")


class OfflineRequestReviewOwner:
    """Exact single-creator-thread owner of one short-lived offline proposal.

    A pure owner intentionally cannot attest Tk's actual enabled state. The
    application MUST make the final Tcl observation its last Tcl seam, then
    perform pure checks and call arm_after_last_tk(). No boolean gesture proof.
    """

    __slots__ = (
        "_root", "_creator", "_state", "_context", "_prompt",
        "_ticket", "_deadline", "_last_ms",
    )

    def __init__(self, root: object) -> None:
        if type(root) is not object:
            raise ReviewRefused("ROOT_IDENTITY")
        self._root = root
        self._creator = threading.get_ident()
        self._state = ReviewState.IDLE
        self._context = None
        self._prompt = None
        self._ticket = None
        self._deadline = 0
        self._last_ms = 0

    def _thread(self) -> None:
        if threading.get_ident() != self._creator:
            raise ReviewRefused("WRONG_THREAD")

    @property
    def state(self) -> ReviewState:
        self._thread()
        return self._state

    def _clear(self) -> None:
        self._context = None
        self._prompt = None
        self._ticket = None
        self._deadline = 0

    def _poison(self) -> None:
        self._clear()
        if self._state is not ReviewState.CLOSED:
            self._state = ReviewState.POISONED

    def _clock(self, now_ms: int) -> None:
        if (type(now_ms) is not int or not self._last_ms <= now_ms <= MAX_CLOCK_MS):
            self._poison()
            raise ReviewRefused("CLOCK")
        self._last_ms = now_ms

    def _valid_context(self, ctx: ReviewContext) -> bool:
        return (
            type(ctx) is ReviewContext and ctx.root is self._root
            and type(ctx.pane) is object and type(ctx.session) is object
            and all(type(v) is int and 0 <= v <= MAX_CLOCK_MS for v in (
                ctx.generation, ctx.epoch, ctx.revision))
        )

    def _match(self, ctx: ReviewContext, prompt: str, now_ms: int) -> None:
        self._clock(now_ms)
        if (not self._valid_context(ctx) or ctx is not self._context
                or type(prompt) is not str or prompt != self._prompt
                or now_ms >= self._deadline):
            self._poison()
            raise ReviewRefused("STALE_REVIEW")

    def offer(self, ctx: ReviewContext, prompt: str,
              now_ms: int) -> OfflineReviewPreview:
        self._thread()
        if self._state is not ReviewState.IDLE:
            raise ReviewRefused("BUSY")
        if not self._valid_context(ctx):
            raise ReviewRefused("CONTEXT")
        try:
            validate_offline_text(prompt)
        except (SessionRefused, UnicodeError):
            raise ReviewRefused("PROMPT") from None
        self._clock(now_ms)
        if now_ms > MAX_CLOCK_MS - REVIEW_TTL_MS:
            raise ReviewRefused("CLOCK")
        self._context = ctx
        self._prompt = prompt
        self._deadline = now_ms + REVIEW_TTL_MS
        self._state = ReviewState.PREVIEW
        return OfflineReviewPreview(prompt)

    def begin_enable(self, ctx: ReviewContext, prompt: str,
                     now_ms: int) -> None:
        self._thread()
        if self._state is not ReviewState.PREVIEW:
            raise ReviewRefused("NOT_PREVIEW")
        self._match(ctx, prompt, now_ms)
        self._state = ReviewState.ENABLING

    def arm_after_last_tk(self, ctx: ReviewContext, prompt: str,
                          now_ms: int) -> ReviewTicket:
        """Only the trusted controller may call after final true Tk instate."""
        self._thread()
        if self._state is not ReviewState.ENABLING:
            raise ReviewRefused("NOT_ENABLING")
        self._match(ctx, prompt, now_ms)
        self._ticket = ReviewTicket()
        self._state = ReviewState.ARMED
        return self._ticket

    def confirm(self, ticket: ReviewTicket, ctx: ReviewContext,
                prompt: str, now_ms: int) -> OfflineReviewReceipt:
        self._thread()
        if self._state in (ReviewState.PREVIEW, ReviewState.ENABLING):
            self._poison()
            raise ReviewRefused("CONFIRM_BEFORE_ARM")
        if (self._state is not ReviewState.ARMED
                or type(ticket) is not ReviewTicket
                or ticket is not self._ticket):
            raise ReviewRefused("NO_TICKET")
        self._match(ctx, prompt, now_ms)
        self._clear()  # Consume BEFORE the caller performs any Tk effect.
        self._state = ReviewState.IDLE
        return OfflineReviewReceipt()

    def abort(self) -> None:
        self._thread()
        self._poison()

    def reset(self) -> None:
        self._thread()
        if self._state is ReviewState.CLOSED:
            raise ReviewRefused("CLOSED")
        self._clear()
        self._state = ReviewState.IDLE

    def close(self) -> None:
        self._thread()
        self._clear()
        self._state = ReviewState.CLOSED
