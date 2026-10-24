"""Pure composition of local draft data and a privately owned review lifetime.

No Tk, clock reads, effects or callbacks. A draft ticket is never a prompt-only
8.36 ticket, a human-gesture proof, or permission to perform any future action.
"""
from __future__ import annotations

from dataclasses import dataclass

from nayeon.desktop_alpha.offline_request_draft import (
    OfflineDraftReceipt, OfflineRequestDraft,
)
from nayeon.desktop_alpha.offline_request_review import (
    OfflineRequestReviewOwner, ReviewContext, ReviewRefused, ReviewState,
)


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class DraftTicket:
    pass


class OfflineDraftConsentOwner:
    """One exact draft, context and one-use ticket, on the creator thread."""

    __slots__ = ("_review", "_draft", "_ticket", "_review_ticket")

    def __init__(self, root: object) -> None:
        self._review = OfflineRequestReviewOwner(root)
        self._clear()

    def _thread(self) -> None:
        # Run before even reading or mutating this composition's state.
        self._review.state  # The independently owned review checks its thread.

    @property
    def state(self) -> ReviewState:
        self._thread()
        return self._review.state

    def _clear(self) -> None:
        self._draft = self._ticket = self._review_ticket = None

    def abort(self) -> None:
        self._thread()
        self._clear()
        self._review.abort()

    def reset(self) -> None:
        self._thread()
        self._clear()
        self._review.reset()

    def close(self) -> None:
        self._thread()
        self._clear()
        self._review.close()

    def offer(self, ctx: ReviewContext, provider: str, model: str, prompt: str,
              now_ms: int) -> OfflineRequestDraft:
        self._thread()
        try:
            draft = OfflineRequestDraft(provider, model, prompt)
            self._review.offer(ctx, prompt, now_ms)
            self._draft = draft
            return draft
        except (ValueError, RuntimeError):
            self.abort()
            raise ReviewRefused("DRAFT_REFUSED") from None

    def _match(self, draft: OfflineRequestDraft) -> None:
        if type(draft) is not OfflineRequestDraft or draft is not self._draft:
            raise ReviewRefused("STALE_DRAFT")

    def begin_enable(self, ctx: ReviewContext, draft: OfflineRequestDraft,
                     now_ms: int) -> None:
        self._thread()
        try:
            self._match(draft)
            self._review.begin_enable(ctx, draft.prompt, now_ms)
        except ReviewRefused:
            self.abort()
            raise

    def arm_after_last_tk(self, ctx: ReviewContext, draft: OfflineRequestDraft,
                          now_ms: int) -> DraftTicket:
        self._thread()
        try:
            self._match(draft)
            self._review_ticket = self._review.arm_after_last_tk(
                ctx, draft.prompt, now_ms)
            self._ticket = DraftTicket()
            return self._ticket
        except ReviewRefused:
            self.abort()
            raise

    def confirm(self, ticket: DraftTicket, ctx: ReviewContext, provider: str,
                model: str, prompt: str, now_ms: int) -> OfflineDraftReceipt:
        self._thread()
        try:
            draft = self._draft
            if (type(ticket) is not DraftTicket or ticket is not self._ticket
                    or draft is None
                    or type(provider) is not str or provider != draft.provider
                    or type(model) is not str or model != draft.model
                    or type(prompt) is not str or prompt != draft.prompt):
                raise ReviewRefused("STALE_DRAFT")
            self._review.confirm(self._review_ticket, ctx, prompt, now_ms)
            self._clear()  # Consume before returning data to a Tk publisher.
            return OfflineDraftReceipt(draft)
        except (ReviewRefused, ValueError):
            self.abort()
            raise ReviewRefused("DRAFT_REFUSED") from None
