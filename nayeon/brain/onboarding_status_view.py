"""Phase 8.10: bounded first-run status presentation contract.

This projection is intentionally not a GUI and cannot activate a provider,
validate credentials or authorize remediation. All data is non-secret.
"""
from dataclasses import dataclass
from enum import Enum

from nayeon.brain.connection_reconciliation import (
    ConnectionObservation,
    ConnectionObservationStatus,
)
from nayeon.brain.connection_recovery_advice import (
    ConnectionRecoveryAdvice,
    ConnectionRecoveryStep,
)


class OnboardingDisplayState(str, Enum):
    NEEDS_SETUP = "needs_setup"
    SAVED_KEY_NEEDS_REVIEW = "saved_key_needs_review"
    NEEDS_CREDENTIAL = "needs_credential"
    NEEDS_EXPLICIT_VALIDATION = "needs_explicit_validation"
    UNSUPPORTED = "unsupported"
    OBSERVATION_CHANGED = "observation_changed"
    STATE_UNKNOWN = "state_unknown"


@dataclass(frozen=True, slots=True, repr=False)
class OnboardingStatusView:
    """Non-secret display hint, never a live status or action permit."""

    state: OnboardingDisplayState
    step: ConnectionRecoveryStep
    must_reobserve: bool = True

    def __post_init__(self) -> None:
        if type(self.state) is not OnboardingDisplayState:
            raise TypeError("Invalid display state")
        if type(self.step) is not ConnectionRecoveryStep:
            raise TypeError("Invalid display step")
        if self.must_reobserve is not True:
            raise ValueError("An observation is never lasting authorization")


_MAPPING = {
    ConnectionObservationStatus.SETUP_REQUIRED:
        (OnboardingDisplayState.NEEDS_SETUP, ConnectionRecoveryStep.CONFIGURE_PROVIDER),
    ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT:
        (OnboardingDisplayState.SAVED_KEY_NEEDS_REVIEW,
         ConnectionRecoveryStep.REVIEW_SAVED_CREDENTIAL),
    ConnectionObservationStatus.CREDENTIAL_REQUIRED:
        (OnboardingDisplayState.NEEDS_CREDENTIAL, ConnectionRecoveryStep.ADD_CREDENTIAL),
    ConnectionObservationStatus.VALIDATION_REQUIRED:
        (OnboardingDisplayState.NEEDS_EXPLICIT_VALIDATION,
         ConnectionRecoveryStep.REQUEST_EXPLICIT_VALIDATION),
    ConnectionObservationStatus.UNSUPPORTED_CONFIGURATION:
        (OnboardingDisplayState.UNSUPPORTED, ConnectionRecoveryStep.REVIEW_UNSUPPORTED_CONFIG),
    ConnectionObservationStatus.CHANGED_DURING_OBSERVATION:
        (OnboardingDisplayState.OBSERVATION_CHANGED, ConnectionRecoveryStep.REOBSERVE),
    ConnectionObservationStatus.UNKNOWN:
        (OnboardingDisplayState.STATE_UNKNOWN, ConnectionRecoveryStep.REVIEW_UNKNOWN_STATE),
}


def present_onboarding_status(
    observation: ConnectionObservation,
    advice: ConnectionRecoveryAdvice,
) -> OnboardingStatusView:
    """Project only a matched trusted observation/advice pair to UI-safe hints."""
    if type(observation) is not ConnectionObservation:
        raise TypeError("Exact observation required")
    if type(advice) is not ConnectionRecoveryAdvice:
        raise TypeError("Exact recovery advice required")
    display, required_step = _MAPPING[observation.status]
    if advice.step is not required_step:
        raise ValueError("Recovery advice does not match observation")
    return OnboardingStatusView(display, required_step)
