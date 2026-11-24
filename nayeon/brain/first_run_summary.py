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
from nayeon.brain.pending_custody_status_view import PendingCustodyStatusView


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


def summarize_pending_custody_first_run(
    observation: ConnectionObservation,
    pending_custody: PendingCustodyStatusView,
) -> FirstRunSummary:
    """Compose pending-custody advice into a conservative first-run summary.

    All pending views are unverified claims, including claimed absence. They
    cannot establish recovered state, suggest credential operations or justify
    retry/replay. Require an explicit matching view; never fall back to legacy
    operation suggestions when custody input is missing or inconsistent.
    This pure seam observes nothing and does not decode journal evidence.
    """
    if type(pending_custody) is not PendingCustodyStatusView:
        raise TypeError("Exact pending custody status view required")
    legacy = summarize_first_run(observation)
    if pending_custody.legacy_status is not legacy.state:
        raise ValueError("Pending custody view does not match first-run status")
    return FirstRunSummary(
        legacy.state, ConnectionRecoveryStep.REVIEW_UNKNOWN_STATE, (),
    )
