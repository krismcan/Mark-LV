"""P84 production-importable READ-ONLY pending custody presentation boundary.

This projects exact nonsecret, potentially stale advice beside the legacy
onboarding status. It does NOT observe a real credential or connect to the
legacy credential mutation host, Tk UI, provider, Windows service or WinCred.

Never treat an assessment or a displayed "unverified" hint as an execution,
consent, storage, recovery, connectivity or durability attestation.
"""
from dataclasses import dataclass
from enum import Enum

from nayeon.brain.onboarding_status_view import (
    OnboardingStatusView, OnboardingDisplayState,
)
from nayeon.brain.pending_credential_policy import (
    PendingCredentialAssessment, PendingCredentialState,
    PendingCredentialAction, PendingCredentialDecision,
    assess_pending_credential_action,
)


class PendingCustodyDisplay(Enum):
    NO_PENDING_EVIDENCE_ASSERTED = "no_pending_evidence_asserted"
    UNVERIFIED_PENDING_CLAIM = "unverified_pending_claim"
    RECOVERY_HOLD = "recovery_hold"


@dataclass(frozen=True, slots=True, repr=False)
class PendingCustodyStatusView:
    """Non-authoritative, nonsecret UI projection. Never a live observation."""

    legacy_status: OnboardingDisplayState
    pending_display: PendingCustodyDisplay
    proposed_action: PendingCredentialAction
    advisory_decision: PendingCredentialDecision
    must_reobserve: bool = True
    authorizes_effect: bool = False
    confirms_persistence: bool = False
    confirms_validation: bool = False
    confirms_provider_connection: bool = False
    clears_recovery: bool = False

    def __post_init__(self) -> None:
        if type(self.legacy_status) is not OnboardingDisplayState:
            raise TypeError("Exact legacy display status required")
        if type(self.pending_display) is not PendingCustodyDisplay:
            raise TypeError("Exact pending custody display required")
        if type(self.proposed_action) is not PendingCredentialAction:
            raise TypeError("Exact proposed pending action required")
        if type(self.advisory_decision) is not PendingCredentialDecision:
            raise TypeError("Exact non-authoritative advisory decision required")
        if (self.must_reobserve is not True or
                self.authorizes_effect is not False or
                self.confirms_persistence is not False or
                self.confirms_validation is not False or
                self.confirms_provider_connection is not False or
                self.clears_recovery is not False):
            raise ValueError("Pending custody presentation cannot grant authority")
        expected = assess_pending_credential_action(
            _STATE_FROM_DISPLAY[self.pending_display], self.proposed_action)
        if self.advisory_decision is not expected.decision:
            raise ValueError("Pending custody display contradicts canonical policy")

    def __repr__(self) -> str:
        return "PendingCustodyStatusView(<nonsecret, stale, no authority>)"


_PRESENT = {
    PendingCredentialState.ABSENT: PendingCustodyDisplay.NO_PENDING_EVIDENCE_ASSERTED,
    PendingCredentialState.STORED_UNVERIFIED: PendingCustodyDisplay.UNVERIFIED_PENDING_CLAIM,
    PendingCredentialState.RECOVERY_REQUIRED: PendingCustodyDisplay.RECOVERY_HOLD,
}
_STATE_FROM_DISPLAY = {display: state for state, display in _PRESENT.items()}


def present_pending_custody_advice(
    legacy: OnboardingStatusView,
    assessment: PendingCredentialAssessment,
) -> PendingCustodyStatusView:
    """Combine two separate nonsecret views without merging their authority.

    A legacy "stored credential" hint is NOT pending-key evidence. This
    function deliberately never maps legacy connection readiness to a pending
    credential state or vice versa. Calling it never performs native I/O.
    """
    if type(legacy) is not OnboardingStatusView:
        raise TypeError("Exact legacy status view required")
    if type(assessment) is not PendingCredentialAssessment:
        raise TypeError("Exact pending advisory assessment required")
    expected = assess_pending_credential_action(assessment.state, assessment.action)
    if assessment.decision is not expected.decision:
        raise ValueError("Pending policy decision does not match canonical matrix")
    return PendingCustodyStatusView(
        legacy_status=legacy.state,
        pending_display=_PRESENT[assessment.state],
        proposed_action=assessment.action,
        advisory_decision=assessment.decision,
    )
