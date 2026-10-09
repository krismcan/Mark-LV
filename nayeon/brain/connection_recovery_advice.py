"""Pure, non-executable guidance from an explicitly requested observation.

No credentials, file access, retry loop, side effects or automatic recovery.
"""

from dataclasses import dataclass
from enum import Enum

from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)


class ConnectionRecoveryStep(str, Enum):
    CONFIGURE_PROVIDER = "configure_provider"
    REVIEW_SAVED_CREDENTIAL = "review_saved_credential"
    ADD_CREDENTIAL = "add_credential"
    REQUEST_EXPLICIT_VALIDATION = "request_explicit_validation"
    REVIEW_UNSUPPORTED_CONFIG = "review_unsupported_configuration"
    REOBSERVE = "reobserve"
    REVIEW_UNKNOWN_STATE = "review_unknown_state"


@dataclass(frozen=True, slots=True, repr=False)
class ConnectionRecoveryAdvice:
    """Proposed next human action only; no permission or execution authority."""

    step: ConnectionRecoveryStep

    def __post_init__(self) -> None:
        if type(self.step) is not ConnectionRecoveryStep:
            raise TypeError("Recovery advice must contain an exact step")


_STEPS = {
    ConnectionObservationStatus.SETUP_REQUIRED: ConnectionRecoveryStep.CONFIGURE_PROVIDER,
    ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT:
        ConnectionRecoveryStep.REVIEW_SAVED_CREDENTIAL,
    ConnectionObservationStatus.CREDENTIAL_REQUIRED: ConnectionRecoveryStep.ADD_CREDENTIAL,
    ConnectionObservationStatus.VALIDATION_REQUIRED:
        ConnectionRecoveryStep.REQUEST_EXPLICIT_VALIDATION,
    ConnectionObservationStatus.UNSUPPORTED_CONFIGURATION:
        ConnectionRecoveryStep.REVIEW_UNSUPPORTED_CONFIG,
    ConnectionObservationStatus.CHANGED_DURING_OBSERVATION: ConnectionRecoveryStep.REOBSERVE,
    ConnectionObservationStatus.UNKNOWN: ConnectionRecoveryStep.REVIEW_UNKNOWN_STATE,
}


def advise_connection_recovery(observation: ConnectionObservation) -> ConnectionRecoveryAdvice:
    """Map an exact non-secret observation to a fixed, non-executable suggestion."""
    if type(observation) is not ConnectionObservation:
        raise TypeError("Observation must be an exact ConnectionObservation")
    return ConnectionRecoveryAdvice(_STEPS[observation.status])
