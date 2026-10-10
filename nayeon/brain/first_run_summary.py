"""Phase 8.20: an immutable, non-secret first-run decision summary.

This is human-facing information only: statuses and suggested operations are
never permission, consent, credential availability guarantees, or execution.
"""
from dataclasses import dataclass

from nayeon.brain.connection_reconciliation import ConnectionObservation
from nayeon.brain.connection_recovery_advice import (
    ConnectionRecoveryStep, advise_connection_recovery,
)
from nayeon.brain.onboarding_operation_advice import (
    OnboardingOperation, OperationEligibility, advise_onboarding_operation,
)
from nayeon.brain.onboarding_status_view import (
    OnboardingDisplayState, present_onboarding_status,
)


_ACTIONS = (
    OnboardingOperation.TEST_CANDIDATE,
    OnboardingOperation.TEST_STORED,
    OnboardingOperation.CONNECT,
    OnboardingOperation.REPLACE,
    OnboardingOperation.REMOVE,
)


@dataclass(frozen=True, slots=True, repr=False)
class FirstRunSummary:
    state: OnboardingDisplayState
    recovery_step: ConnectionRecoveryStep
    suggested_operations: tuple[OnboardingOperation, ...]
    requires_reobservation: bool = True
    grants_execution_authority: bool = False

    def __post_init__(self) -> None:
        if type(self.state) is not OnboardingDisplayState:
            raise TypeError("Exact display state required")
        if type(self.recovery_step) is not ConnectionRecoveryStep:
            raise TypeError("Exact recovery step required")
        if type(self.suggested_operations) is not tuple or any(
            type(op) is not OnboardingOperation or op not in _ACTIONS
            for op in self.suggested_operations
        ) or len(set(self.suggested_operations)) != len(self.suggested_operations):
            raise TypeError("Canonical suggested actions required")
        if self.requires_reobservation is not True or self.grants_execution_authority is not False:
            raise ValueError("A summary is never fresh authority")


def summarize_first_run(observation: ConnectionObservation) -> FirstRunSummary:
    """Pure projection of one point-in-time typed, non-secret observation."""
    if type(observation) is not ConnectionObservation:
        raise TypeError("Exact connection observation required")
    advice = advise_connection_recovery(observation)
    projection = present_onboarding_status(observation, advice)
    eligible = tuple(op for op in _ACTIONS
                     if advise_onboarding_operation(observation, op).eligibility
                     is OperationEligibility.SUGGESTED)
    return FirstRunSummary(projection.state, projection.step, eligible)
