"""P87 explicit synthetic-only read-only custody observation contract.

This is NOT an operating or trusted native custody observer.  A live source
cannot be inferred from a P84 policy assessment, a Connection page or silence.
No secrets, tickets, provider identifiers, arbitrary strings or effect flags.
A separately reviewed native observation adapter is required for real state.
"""
from dataclasses import dataclass
from enum import Enum


class CustodyObservationKind(Enum):
    NOT_OBSERVED = "not_observed"
    UNAVAILABLE = "unavailable"
    NO_PENDING_EVIDENCE_ASSERTED = "no_pending_evidence_asserted"
    UNVERIFIED_PENDING_CLAIM = "unverified_pending_claim"
    RECOVERY_HOLD = "recovery_hold"


class CustodyObservationOrigin(Enum):
    SYNTHETIC_TEST = "synthetic_test"


@dataclass(frozen=True, slots=True, repr=False)
class SyntheticCustodyObservation:
    kind: CustodyObservationKind
    origin: CustodyObservationOrigin = CustodyObservationOrigin.SYNTHETIC_TEST
    authorizes_effect: bool = False
    confirms_persistence: bool = False
    confirms_validation: bool = False
    confirms_connection: bool = False
    clears_recovery: bool = False

    def __post_init__(self):
        if type(self.kind) is not CustodyObservationKind:
            raise TypeError("Exact bounded custody state required")
        if type(self.origin) is not CustodyObservationOrigin or (
                self.origin is not CustodyObservationOrigin.SYNTHETIC_TEST):
            raise ValueError("Only explicit synthetic observations accepted")
        if (self.authorizes_effect is not False or
                self.confirms_persistence is not False or
                self.confirms_validation is not False or
                self.confirms_connection is not False or
                self.clears_recovery is not False):
            raise ValueError("Read-only observation cannot grant authority")

    def __repr__(self):
        return "SyntheticCustodyObservation(<nonsecret, test-only, no authority>)"


@dataclass(frozen=True, slots=True, repr=False)
class SyntheticObservationLease:
    """A per-view, per-generation *presentation* lease, never consent."""

    owner: object
    generation: int

    def __post_init__(self):
        if type(self.owner) is not object or type(self.generation) is not int:
            raise TypeError("Exact internal observation lease required")
        if self.generation < 1:
            raise ValueError("Invalid observation generation")

    def __repr__(self):
        return "SyntheticObservationLease(<presentation only>)"


_FIXED_MESSAGES = {
    CustodyObservationKind.NOT_OBSERVED:
        "BYOK C1 pending-key custody: NOT OBSERVED (SYNTHETIC TEST ONLY). "
        "No native service, key state or credential authority observed.",
    CustodyObservationKind.UNAVAILABLE:
        "BYOK C1 pending-key custody: STATUS UNAVAILABLE (SYNTHETIC TEST ONLY). "
        "No credential state, connection or operation verified.",
    CustodyObservationKind.NO_PENDING_EVIDENCE_ASSERTED:
        "BYOK C1 pending-key custody: NO PENDING EVIDENCE ASSERTED "
        "(SYNTHETIC TEST ONLY; NOT proof of absence). No custody state verified.",
    CustodyObservationKind.UNVERIFIED_PENDING_CLAIM:
        "BYOK C1 pending-key custody: UNVERIFIED PENDING CLAIM "
        "(SYNTHETIC TEST ONLY). Storage, key validity and provider connection "
        "are NOT confirmed.",
    CustodyObservationKind.RECOVERY_HOLD:
        "BYOK C1 pending-key custody: RECOVERY HOLD CLAIM "
        "(SYNTHETIC TEST ONLY). No automatic retry or recovery clearance.",
}


def synthetic_observation_message(observation: SyntheticCustodyObservation) -> str:
    """Pure, bounded presentation mapping with no I/O or arbitrary source text."""
    if type(observation) is not SyntheticCustodyObservation:
        raise TypeError("Exact synthetic observation required")
    # Explicit revalidation protects against forged instances/field mutation.
    observation.__post_init__()
    return _FIXED_MESSAGES[observation.kind]
