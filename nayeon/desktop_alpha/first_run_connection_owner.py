"""Phase 8 BYOK: isolated, fake-first ownership bridge for existing onboarding.

Only an injected, already constructed trusted coordinator can perform operations.
This module imports no provider, WinCred, Tk, store, subprocess or SDK adapter.
The default desktop application does NOT import or instantiate this owner.
"""
from __future__ import annotations

from dataclasses import dataclass
import threading
from collections.abc import Callable

from nayeon.brain.onboarding_coordination import (
    CooperativeOnboardingCoordinator, CoordinationReceipt, CoordinatedOutcome,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation


class JourneyRefused(RuntimeError):
    """Fixed non-secret refusal; never contains candidate, path or dependency errors."""


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class JourneyContext:
    root: object
    application: object
    pane: object
    journey: object
    generation: int


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class JourneyReview:
    operation: OnboardingOperation
    _ticket: object
    _context: JourneyContext


def _refused() -> CoordinationReceipt:
    return CoordinationReceipt(CoordinatedOutcome.REFUSED)


class TrustedFirstRunConnectionOwner:
    """One creator thread, one exact injected coordinator and one UI tenure.

    Trusted callers own context truth and explicit physical human UI callbacks.
    This is NOT approval provenance or a real provider runtime factory.
    """

    __slots__ = (
        "_coordinator", "_ctx", "_live", "_creator", "_owner_token",
        "_active", "_closed", "_uncertain", "_pending", "_busy", "_deferred_close",
    )

    def __init__(self, *, coordinator: CooperativeOnboardingCoordinator,
                 context: JourneyContext, is_current: Callable[[], bool]) -> None:
        if type(coordinator) is not CooperativeOnboardingCoordinator:
            raise JourneyRefused("COORDINATOR")
        if not self._valid_context(context):
            raise JourneyRefused("CONTEXT")
        if not callable(is_current):
            raise JourneyRefused("LIVENESS")
        # Strictly no dependency calls before this point or in this constructor.
        self._creator = threading.get_ident()
        self._coordinator = coordinator
        self._ctx = context
        self._live = is_current
        self._owner_token = None
        self._active = False
        self._closed = False
        self._uncertain = False
        self._pending = None
        self._busy = False
        self._deferred_close = False

    @staticmethod
    def _valid_context(ctx: object) -> bool:
        return (
            type(ctx) is JourneyContext and ctx.root is not None
            and type(ctx.application) is object and type(ctx.pane) is object
            and type(ctx.journey) is object
            and type(ctx.generation) is int
            and 0 <= ctx.generation < (1 << 63)
        )

    def _thread(self) -> None:
        if threading.get_ident() != self._creator:
            raise JourneyRefused("WRONG_THREAD")

    def _pure_identity(self, ctx: object) -> bool:
        original = self._ctx
        return (
            not self._closed and not self._uncertain and ctx is original
            and self._valid_context(original) and self._valid_context(ctx)
            and ctx.root is original.root
            and ctx.application is original.application
            and ctx.pane is original.pane
            and ctx.journey is original.journey
            and ctx.generation == original.generation
        )

    def _fresh(self, ctx: object) -> bool:
        # Identity BEFORE calling potentially reentrant trusted UI liveness.
        if not self._pure_identity(ctx):
            return False
        try:
            observed = self._live()
        except Exception:
            return False
        # The callback can reenter close/reset or change exact context.
        return observed is True and self._pure_identity(ctx)

    def _still_owner(self, ctx: JourneyContext, token: str) -> bool:
        if not self._fresh(ctx) or not self._active or token is not self._owner_token:
            return False
        try:
            present = self._coordinator.recovery_controller.is_ui_window_owner(token)
        except Exception:
            return False
        return present is True and self._fresh(ctx) and token is self._owner_token

    @property
    def closed(self) -> bool:
        self._thread()
        return self._closed

    @property
    def uncertain(self) -> bool:
        self._thread()
        return self._uncertain

    def start(self, ctx: JourneyContext) -> bool:
        """Explicit trusted UI start. Never performs validation/storage/network."""
        self._thread()
        if self._busy or self._active or not self._fresh(ctx):
            return False
        self._busy = True
        token = None
        try:
            # Recovery/controller is invoked ONLY on deliberate start, not init.
            controller = self._coordinator.recovery_controller
            token = controller.claim_ui_window_owner()
            if type(token) is not str or not token:
                return False
            # Store owned identity BEFORE any later potentially reentrant
            # Tk/liveness probe. Cleanup must close this exact tenure, not
            # attempt release_ui_window_owner while a mutex is still held.
            self._owner_token = token
            if not self._fresh(ctx) or controller.is_ui_window_owner(token) is not True:
                self._closed = True
                self._deferred_close = True
                return False
            self._active = True
            return True
        except Exception:
            if type(token) is str and token:
                self._closed = True
                self._deferred_close = True
                self._uncertain = True
            return False
        finally:
            self._busy = False
            if self._deferred_close:
                self._finish_close()

    def request(self, ctx: JourneyContext, operation: OnboardingOperation
                ) -> tuple[CoordinationReceipt, JourneyReview | None]:
        """Request only. The coordinator's one-use UI ticket remains authoritative."""
        self._thread()
        if (self._busy or not self._active or not self._fresh(ctx)
                or type(operation) is not OnboardingOperation
                or operation is OnboardingOperation.REVIEW or self._pending is not None):
            return _refused(), None
        token = self._owner_token
        if type(token) is not str or not self._still_owner(ctx, token):
            return _refused(), None
        self._busy = True
        try:
            receipt, ticket = self._coordinator.request_ui(
                operation, owner_token=token, root=ctx.root)
            if (type(receipt) is not CoordinationReceipt or
                    receipt.outcome is not CoordinatedOutcome.PENDING or
                    ticket is None or not self._still_owner(ctx, token) or
                    not self._coordinator.is_current_ui_ticket(
                        ticket=ticket, owner_token=token, root=ctx.root,
                        operation=operation) or
                    # Last check MUST be pure: the validation clock itself
                    # can reenter a close after the coordinator's check.
                    not self._pure_identity(ctx) or not self._active or
                    token is not self._owner_token):
                if (type(receipt) is CoordinationReceipt and
                        receipt.outcome is CoordinatedOutcome.PENDING and ticket is None):
                    self._uncertain = True
                # Only the issuing owner's A may be rejected; never raw reject B.
                if ticket is not None:
                    try:
                        self._coordinator.reject_ui(
                            ticket=ticket, owner_token=token,
                            root=ctx.root, operation=operation)
                    except Exception:
                        self._uncertain = True
                # Never publish PENDING after revocation if no live review
                # can be handed to the original trusted UI.
                if (type(receipt) is CoordinationReceipt and
                        receipt.outcome is not CoordinatedOutcome.PENDING):
                    return receipt, None
                return _refused(), None
            review = JourneyReview(operation, ticket, ctx)
            self._pending = review
            return receipt, review
        except Exception:
            self._uncertain = True
            return CoordinationReceipt(CoordinatedOutcome.UNAVAILABLE), None
        finally:
            self._busy = False
            if self._deferred_close:
                self._finish_close()

    def confirm(self, ctx: JourneyContext, review: JourneyReview, *,
                candidate: object = None,
                explicitly_approved: bool = False,
                acknowledged_delete: bool = False) -> CoordinationReceipt:
        """Only a trusted human-operated UI may pass explicitly_approved=True.

        This stage has no registered UI caller, real validator or native backend.
        """
        self._thread()
        if (self._busy or not self._fresh(ctx) or
                type(review) is not JourneyReview or
                review is not self._pending or review._context is not ctx or
                type(explicitly_approved) is not bool or not explicitly_approved or
                type(acknowledged_delete) is not bool):
            return _refused()
        operation = review.operation
        if (type(operation) is not OnboardingOperation or
                (operation is OnboardingOperation.REMOVE and not acknowledged_delete) or
                (operation in (OnboardingOperation.CONNECT, OnboardingOperation.REPLACE)
                 and candidate is None) or
                (operation is OnboardingOperation.REMOVE and candidate is not None)):
            return _refused()
        token = self._owner_token
        if type(token) is not str or not self._still_owner(ctx, token):
            return _refused()
        # Consume local review BEFORE external callback/reentrant effect.
        self._pending = None
        self._busy = True
        try:
            result = self._coordinator.approve_ui(
                ticket=review._ticket, owner_token=token, root=ctx.root,
                operation=operation, candidate=candidate,
                acknowledged=acknowledged_delete)
            if type(result) is not CoordinationReceipt:
                self._uncertain = True
                return CoordinationReceipt(CoordinatedOutcome.INDETERMINATE)
            # Approval effects may already have happened: never claim NO_ACTION
            # if caller navigated/reentered during the operation.
            if not self._still_owner(ctx, token):
                self._uncertain = True
                return CoordinationReceipt(CoordinatedOutcome.INDETERMINATE)
            return result
        except Exception:
            self._uncertain = True
            return CoordinationReceipt(CoordinatedOutcome.INDETERMINATE)
        finally:
            self._busy = False
            if self._deferred_close:
                self._finish_close()

    def cancel(self, ctx: JourneyContext, review: JourneyReview) -> CoordinationReceipt:
        """Cancel only this exact pending A, never another window's successor."""
        self._thread()
        if (self._busy or not self._fresh(ctx) or
                type(review) is not JourneyReview or review is not self._pending
                or review._context is not ctx):
            return _refused()
        token = self._owner_token
        if type(token) is not str:
            return _refused()
        self._pending = None
        self._busy = True
        try:
            result = self._coordinator.reject_ui(
                ticket=review._ticket, owner_token=token, root=ctx.root,
                operation=review.operation)
            return result if type(result) is CoordinationReceipt else _refused()
        except Exception:
            self._uncertain = True
            return CoordinationReceipt(CoordinatedOutcome.INDETERMINATE)
        finally:
            self._busy = False
            if self._deferred_close:
                self._finish_close()

    def _finish_close(self) -> bool:
        """Single creator-thread cleanup after an in-flight callback completes."""
        self._deferred_close = False
        self._pending = None
        self._active = False
        token = self._owner_token
        if type(token) is not str:
            return not self._uncertain
        try:
            recovery = self._coordinator.recovery_controller
            if not recovery.is_ui_window_owner(token):
                self._uncertain = True
                return False
            # Reject only this exact UI tenure's current review, never a
            # different root or a successor owner on the pooled coordinator.
            self._coordinator.reject_ui_for_owner_shutdown(
                owner_token=token, root=self._ctx.root)
            if recovery.close_ui_window_owner(token) is not True:
                self._uncertain = True
                return False
            self._owner_token = None
            return not self._uncertain
        except Exception:
            # Preserve the token and recovery marker on uncertain release.
            self._uncertain = True
            return False

    def close(self, ctx: JourneyContext) -> bool:
        """Invalidate immediately, including during reentrant dependency calls."""
        self._thread()
        if self._closed or ctx is not self._ctx:
            return False
        self._closed = True  # Invalidate BEFORE any externally reentrant cleanup.
        self._pending = None
        if self._busy:
            self._deferred_close = True
            return False  # Deferred cleanup is not evidence of clean retirement.
        return self._finish_close()

    def reset(self, ctx: JourneyContext) -> bool:
        """Reset permanently retires; fresh journey requires new review/tenure."""
        self._thread()
        return self.close(ctx)
