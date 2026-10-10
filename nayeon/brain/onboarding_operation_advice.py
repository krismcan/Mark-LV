"""Phase 8.16: pure human-facing credential operation eligibility advice.

An observed status is a point-in-time hint, never consent, authentication or
storage authority. This module must not invoke secrets, provider SDK or writes.
"""
from dataclasses import dataclass
from enum import Enum

from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)


class OnboardingOperation(str, Enum):
    REVIEW = "review"
    TEST_CANDIDATE = "test_candidate"
    TEST_STORED = "test_stored"
    CONNECT = "connect"
    REPLACE = "replace"
    REMOVE = "remove"


class OperationEligibility(str, Enum):
    SUGGESTED = "suggested"
    BLOCKED = "blocked"


_ALLOWED = {
    OnboardingOperation.REVIEW: frozenset(ConnectionObservationStatus),
    OnboardingOperation.TEST_CANDIDATE: frozenset({
        ConnectionObservationStatus.SETUP_REQUIRED,
        ConnectionObservationStatus.CREDENTIAL_REQUIRED,
        ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT,
        ConnectionObservationStatus.VALIDATION_REQUIRED,
    }),
    OnboardingOperation.TEST_STORED: frozenset({
        ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT,
        ConnectionObservationStatus.VALIDATION_REQUIRED,
    }),
    OnboardingOperation.CONNECT: frozenset({
        ConnectionObservationStatus.SETUP_REQUIRED,
        ConnectionObservationStatus.CREDENTIAL_REQUIRED,
    }),
    OnboardingOperation.REPLACE: frozenset({
        ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT,
        ConnectionObservationStatus.VALIDATION_REQUIRED,
    }),
    OnboardingOperation.REMOVE: frozenset({
        ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT,
        ConnectionObservationStatus.VALIDATION_REQUIRED,
    }),
}


@dataclass(frozen=True, slots=True, repr=False)
class OnboardingOperationAdvice:
    operation: OnboardingOperation
    observed: ConnectionObservationStatus
    eligibility: OperationEligibility
    requires_fresh_state: bool = True
    requires_real_human_intent: bool = True

    def __post_init__(self) -> None:
        if type(self.operation) is not OnboardingOperation:
            raise TypeError("Exact onboarding operation required")
        if type(self.observed) is not ConnectionObservationStatus:
            raise TypeError("Exact observed status required")
        if type(self.eligibility) is not OperationEligibility:
            raise TypeError("Exact eligibility required")
        correct = (OperationEligibility.SUGGESTED if self.observed in _ALLOWED[self.operation]
                   else OperationEligibility.BLOCKED)
        if self.eligibility is not correct:
            raise ValueError("Eligibility cannot contradict the conservative matrix")
        if self.requires_fresh_state is not True or self.requires_real_human_intent is not True:
            raise ValueError("Advice never creates action authority")


def advise_onboarding_operation(
    observation: ConnectionObservation, operation: OnboardingOperation,
) -> OnboardingOperationAdvice:
    """Offer non-secret operation advice; never run, validate or authorize."""
    if type(observation) is not ConnectionObservation:
        raise TypeError("Exact connection observation required")
    if type(operation) is not OnboardingOperation:
        raise TypeError("Exact onboarding operation required")
    eligibility = (OperationEligibility.SUGGESTED if observation.status in _ALLOWED[operation]
                   else OperationEligibility.BLOCKED)
    return OnboardingOperationAdvice(operation, observation.status, eligibility)
