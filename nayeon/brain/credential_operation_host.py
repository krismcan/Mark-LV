"""Phase 8.18: explicit trusted-host credential-operation testbed.

Not a model tool, an automated setup service, a cross-store transaction or a
proof of human provenance. Trusted composition must own this service and route
requests/approval ONLY from a real human-controlled first-run interface.
Never retains a candidate SecretValue or exposes backend error details.
"""
from dataclasses import dataclass
from enum import Enum
from collections.abc import Callable
import secrets

from nayeon.brain.connection_reconciliation import ConnectionObservation
from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.onboarding_operation_advice import (
    OnboardingOperation, OperationEligibility, advise_onboarding_operation,
)
from nayeon.brain.onboarding_review_session import (
    OnboardingReviewSession, ReviewDecision,
)
from nayeon.secrets.contracts import SecretValue
from nayeon.secrets.lifecycle import CredentialValidationStatus


class CredentialHostOutcome(str, Enum):
    SUBMITTED = "submitted"
    INVALID = "invalid"
    INDETERMINATE = "indeterminate"
    NOT_APPLIED = "not_applied"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True, repr=False)
class CredentialHostResult:
    operation: OnboardingOperation
    outcome: CredentialHostOutcome
    requires_reobservation: bool = True
    confirms_durable_storage: bool = False

    def __post_init__(self) -> None:
        if type(self.operation) is not OnboardingOperation or self.operation is OnboardingOperation.REVIEW:
            raise TypeError("Exact actionable onboarding operation required")
        if type(self.outcome) is not CredentialHostOutcome:
            raise TypeError("Exact safe host result required")
        if self.requires_reobservation is not True or self.confirms_durable_storage is not False:
            raise ValueError("An operation result is never proof of durable storage")


_CANDIDATE_OPERATIONS = frozenset({
    OnboardingOperation.TEST_CANDIDATE, OnboardingOperation.CONNECT,
    OnboardingOperation.REPLACE,
})


class TrustedCredentialOperationHost:
    """Explicit in-process UI host boundary; no ambient backend creation."""

    __slots__ = ("__onboarding", "__observe", "__review", "__validation_ticket")

    def __init__(self, *, onboarding: OpenAICredentialOnboarding,
                 observe: Callable[[], ConnectionObservation],
                 review: OnboardingReviewSession | None = None) -> None:
        if type(onboarding) is not OpenAICredentialOnboarding:
            raise TypeError("Exact bound onboarding lifecycle required")
        if not callable(observe):
            raise TypeError("Trusted observation callback required")
        if review is not None and type(review) is not OnboardingReviewSession:
            raise TypeError("Exact host review session required")
        self.__onboarding = onboarding
        self.__observe = observe
        self.__review = review if review is not None else OnboardingReviewSession()
        self.__validation_ticket = None

    @property
    def has_pending(self) -> bool:
        return self.__review.has_pending

    def _fresh(self) -> ConnectionObservation | None:
        try:
            observed = self.__observe()
        except Exception:
            return None
        return observed if type(observed) is ConnectionObservation else None

    def request(self, operation: OnboardingOperation) -> bool:
        """Trusted UI-triggered request only; never auto-validates or mutates."""
        if self.has_pending or type(operation) is not OnboardingOperation or operation is OnboardingOperation.REVIEW:
            return False
        observed = self._fresh()
        if observed is None:
            return False
        advice = advise_onboarding_operation(observed, operation)
        if advice.eligibility is not OperationEligibility.SUGGESTED:
            return False
        try:
            self.__review.begin(advice)
        except Exception:
            return False
        self.__validation_ticket = None
        return True

    def request_candidate_validation(self) -> str | None:
        """Start an exact test-only review and return its opaque one-use UI ticket.

        A different window's pending CONNECT/REPLACE/REMOVE is never adopted.
        This ticket is in-process UI identity, not a recovery/credential permit.
        """
        if self.has_pending or not self.request(OnboardingOperation.TEST_CANDIDATE):
            return None
        ticket = secrets.token_hex(16)
        self.__validation_ticket = ticket
        return ticket

    def approve_candidate_validation(
        self, *, ticket: str, candidate: SecretValue
    ) -> CredentialHostResult:
        """Atomically verify both operation and originating UI ticket BEFORE effect."""
        pending = self.__review.pending_advice
        if (type(ticket) is not str or self.__validation_ticket is None
                or not secrets.compare_digest(ticket, self.__validation_ticket)
                or pending is None
                or pending.operation is not OnboardingOperation.TEST_CANDIDATE):
            return CredentialHostResult(
                OnboardingOperation.TEST_CANDIDATE, CredentialHostOutcome.BLOCKED
            )
        self.__validation_ticket = None
        return self.approve(candidate=candidate)

    def reject_candidate_validation(self, *, ticket: str) -> CredentialHostResult | None:
        pending = self.__review.pending_advice
        if (type(ticket) is not str or self.__validation_ticket is None
                or not secrets.compare_digest(ticket, self.__validation_ticket)
                or pending is None
                or pending.operation is not OnboardingOperation.TEST_CANDIDATE):
            return None
        self.__validation_ticket = None
        return self.reject()

    def reject(self) -> CredentialHostResult | None:
        """Explicit UI rejection; no credential operation is invoked."""
        if not self.has_pending:
            self.__validation_ticket = None
            return None
        self.__validation_ticket = None
        try:
            decision=self.__review.cancel()
        except Exception:
            return None
        return CredentialHostResult(decision.operation, CredentialHostOutcome.BLOCKED)

    def approve(self, *, candidate: SecretValue | None = None) -> CredentialHostResult | None:
        """Trusted UI callback only. Candidate exists on the stack, not in pending state."""
        pending=self.__review.pending_advice
        if pending is None:
            return None
        operation=pending.operation
        self.__validation_ticket = None
        if ((operation in _CANDIDATE_OPERATIONS and type(candidate) is not SecretValue)
                or (operation not in _CANDIDATE_OPERATIONS and candidate is not None)):
            self.reject()
            return CredentialHostResult(operation, CredentialHostOutcome.BLOCKED)
        observed=self._fresh()
        if (observed is None or observed.status is not pending.observed or
                advise_onboarding_operation(observed,operation).eligibility
                is not OperationEligibility.SUGGESTED):
            self.reject()
            return CredentialHostResult(operation, CredentialHostOutcome.BLOCKED)
        try:
            approval=self.__review.finish(human_approved=True)
        except Exception:
            self.reject()
            return CredentialHostResult(operation, CredentialHostOutcome.BLOCKED)
        if approval.decision is not ReviewDecision.APPROVED:
            return CredentialHostResult(operation, CredentialHostOutcome.BLOCKED)
        try:
            if operation is OnboardingOperation.TEST_CANDIDATE:
                status=self.__onboarding.test_candidate(candidate)
            elif operation is OnboardingOperation.TEST_STORED:
                status=self.__onboarding.test_stored()
            elif operation is OnboardingOperation.CONNECT:
                status=self.__onboarding.connect(candidate)
            elif operation is OnboardingOperation.REPLACE:
                status=self.__onboarding.replace(candidate)
            elif operation is OnboardingOperation.REMOVE:
                deleted=self.__onboarding.remove()
                return CredentialHostResult(operation, (
                    CredentialHostOutcome.SUBMITTED if deleted is True
                    else CredentialHostOutcome.NOT_APPLIED if deleted is False
                    else CredentialHostOutcome.INDETERMINATE))
            else:
                return CredentialHostResult(operation, CredentialHostOutcome.BLOCKED)
        except Exception:
            return CredentialHostResult(operation, CredentialHostOutcome.INDETERMINATE)
        if type(status) is not CredentialValidationStatus:
            return CredentialHostResult(operation, CredentialHostOutcome.INDETERMINATE)
        outcome={CredentialValidationStatus.VALID: CredentialHostOutcome.SUBMITTED,
                 CredentialValidationStatus.INVALID: CredentialHostOutcome.INVALID,
                 CredentialValidationStatus.INDETERMINATE: CredentialHostOutcome.INDETERMINATE}[status]
        return CredentialHostResult(operation, outcome)
