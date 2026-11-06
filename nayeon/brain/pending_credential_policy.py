"""Phase 8 C1: pure policy for an unverified *pending* credential.

This module has no credential data, storage, validator, provider, UI, or effects.
An advisory decision is NEVER a consent ticket, execution permit, or readiness
signal. It cannot clear recovery or promote a key to an active provider.
"""
from dataclasses import dataclass
from enum import Enum


class PendingCredentialState(Enum):
    ABSENT = "absent"
    STORED_UNVERIFIED = "stored_unverified"
    RECOVERY_REQUIRED = "recovery_required"


class PendingCredentialAction(Enum):
    SAVE_PENDING = "save_pending"
    REPLACE_PENDING = "replace_pending"
    DELETE_PENDING = "delete_pending"


class PendingCredentialDecision(Enum):
    DENY = "deny"
    NEEDS_REVIEW = "needs_review"
    NEEDS_DESTRUCTIVE_ACK = "needs_destructive_ack"
    RECOVERY_BLOCKED = "recovery_blocked"


# Explicit exhaustive matrix. All entries are advisory and non-authoritative.
_RULES = {
    (PendingCredentialState.ABSENT, PendingCredentialAction.SAVE_PENDING):
        PendingCredentialDecision.NEEDS_REVIEW,
    (PendingCredentialState.ABSENT, PendingCredentialAction.REPLACE_PENDING):
        PendingCredentialDecision.DENY,
    (PendingCredentialState.ABSENT, PendingCredentialAction.DELETE_PENDING):
        PendingCredentialDecision.DENY,
    (PendingCredentialState.STORED_UNVERIFIED, PendingCredentialAction.SAVE_PENDING):
        PendingCredentialDecision.DENY,
    (PendingCredentialState.STORED_UNVERIFIED, PendingCredentialAction.REPLACE_PENDING):
        PendingCredentialDecision.NEEDS_REVIEW,
    (PendingCredentialState.STORED_UNVERIFIED, PendingCredentialAction.DELETE_PENDING):
        PendingCredentialDecision.NEEDS_DESTRUCTIVE_ACK,
    (PendingCredentialState.RECOVERY_REQUIRED, PendingCredentialAction.SAVE_PENDING):
        PendingCredentialDecision.RECOVERY_BLOCKED,
    (PendingCredentialState.RECOVERY_REQUIRED, PendingCredentialAction.REPLACE_PENDING):
        PendingCredentialDecision.RECOVERY_BLOCKED,
    (PendingCredentialState.RECOVERY_REQUIRED, PendingCredentialAction.DELETE_PENDING):
        PendingCredentialDecision.RECOVERY_BLOCKED,
}


@dataclass(frozen=True, slots=True, repr=False)
class PendingCredentialAssessment:
    """Non-secret metadata; not a consent or mutation capability."""

    state: PendingCredentialState
    action: PendingCredentialAction
    decision: PendingCredentialDecision

    def __post_init__(self) -> None:
        if type(self.state) is not PendingCredentialState:
            raise TypeError("Exact pending credential state required")
        if type(self.action) is not PendingCredentialAction:
            raise TypeError("Exact pending credential action required")
        if type(self.decision) is not PendingCredentialDecision:
            raise TypeError("Exact pending credential decision required")

    def __repr__(self) -> str:
        return "PendingCredentialAssessment(<nonsecret, nonauthoritative>)"


def assess_pending_credential_action(
    state: PendingCredentialState,
    action: PendingCredentialAction,
) -> PendingCredentialAssessment:
    """Return a fixed advisory decision; never authorise or perform an effect."""
    if type(state) is not PendingCredentialState:
        raise TypeError("Exact pending credential state required")
    if type(action) is not PendingCredentialAction:
        raise TypeError("Exact pending credential action required")
    return PendingCredentialAssessment(state, action, _RULES[(state, action)])
