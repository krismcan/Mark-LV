"""Phase 8.17: one bounded host-owned credential-onboarding review.

This is not a permission check or security principal. The trusted host must
connect finish() only to actual human UI controls; model text cannot do so.
No secrets, backend, IO, provider SDK or credentials are retained here.
"""
from dataclasses import dataclass
from enum import Enum
import math
import time
from collections.abc import Callable

from nayeon.brain.onboarding_operation_advice import (
    OnboardingOperation, OnboardingOperationAdvice, OperationEligibility,
)
from nayeon.brain.connection_reconciliation import ConnectionObservationStatus


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True, repr=False)
class CompletedOnboardingReview:
    operation: OnboardingOperation
    observed: ConnectionObservationStatus
    decision: ReviewDecision
    requires_reobservation: bool = True
    grants_execution_authority: bool = False

    def __post_init__(self) -> None:
        if type(self.operation) is not OnboardingOperation or self.operation is OnboardingOperation.REVIEW:
            raise ValueError("Exact non-readonly operation required")
        if type(self.observed) is not ConnectionObservationStatus:
            raise TypeError("Exact observed state required")
        if type(self.decision) is not ReviewDecision:
            raise TypeError("Exact decision required")
        if self.requires_reobservation is not True or self.grants_execution_authority is not False:
            raise ValueError("A review does not grant operation authority")


class OnboardingReviewSession:
    """A single pending human review; process-local, no secret payload."""

    __slots__ = ("_clock", "_timeout", "_pending", "_deadline")

    def __init__(self, *, clock: Callable[[], float] = time.monotonic,
                 timeout_seconds: float = 120.0) -> None:
        if not callable(clock):
            raise TypeError("Trusted monotonic clock required")
        if type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds):
            raise TypeError("Finite timeout required")
        if not 0 < timeout_seconds <= 300:
            raise ValueError("Review timeout must be bounded")
        self._clock = clock
        self._timeout = float(timeout_seconds)
        self._pending = None
        self._deadline = None

    @property
    def has_pending(self) -> bool:
        return self._pending is not None

    @property
    def pending_advice(self) -> OnboardingOperationAdvice | None:
        return self._pending

    def _now(self) -> float:
        try:
            value = self._clock()
        except Exception:
            raise RuntimeError("Review clock unavailable") from None
        if type(value) not in (int, float) or not math.isfinite(value):
            raise RuntimeError("Review clock unavailable")
        return float(value)

    def begin(self, advice: OnboardingOperationAdvice) -> None:
        if self.has_pending:
            raise RuntimeError("Resolve the pending onboarding review first")
        if type(advice) is not OnboardingOperationAdvice:
            raise TypeError("Exact operation advice required")
        if (advice.operation is OnboardingOperation.REVIEW or
                advice.eligibility is not OperationEligibility.SUGGESTED):
            raise ValueError("Operation may not be proposed for confirmation")
        deadline = self._now() + self._timeout
        if not math.isfinite(deadline):
            raise RuntimeError("Review deadline unavailable")
        self._pending = advice
        self._deadline = deadline

    def finish(self, *, human_approved: bool) -> CompletedOnboardingReview:
        """Trusted UI callback ONLY; model text never drives this operation."""
        if type(human_approved) is not bool:
            raise TypeError("Exact human button decision required")
        advice = self._pending
        if advice is None:
            raise RuntimeError("No pending onboarding review")
        # Fail closed even if clock becomes unavailable; clear pending once.
        try:
            valid = self._now() <= self._deadline
        except RuntimeError:
            valid = False
        self._pending = None
        self._deadline = None
        decision = (ReviewDecision.EXPIRED if not valid else
                    ReviewDecision.APPROVED if human_approved else ReviewDecision.REJECTED)
        return CompletedOnboardingReview(advice.operation, advice.observed, decision)

    def cancel(self) -> CompletedOnboardingReview:
        return self.finish(human_approved=False)
