"""Optional capability-owned observation, separate from execution success."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Protocol, runtime_checkable

from nayeon.capabilities.structured import StructuredCapabilityRequest


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    NOT_VERIFIED = "not_verified"
    INDETERMINATE = "indeterminate"


def _copy_evidence(value: Any) -> Any:
    """Copy plain JSON data only; reject opaque objects and non-finite numbers."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is list:
        return [_copy_evidence(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: _copy_evidence(item) for key, item in value.items()}
    raise TypeError("Verification evidence must contain plain JSON data.")


@dataclass(frozen=True)
class VerificationResult:
    """A separate outcome claim, with provider-curated non-secret evidence.

    NOT_VERIFIED means a check found the requested outcome was not established.
    INDETERMINATE means no conclusive check is available. Neither is success.
    Providers must supply concise, safe reasons and exclude credentials and
    unnecessary personal data. JSON validation cannot establish confidentiality.
    """

    status: VerificationStatus = VerificationStatus.INDETERMINATE
    reason: str = "Outcome has not been verified."
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, VerificationStatus):
            raise TypeError("A VerificationStatus is required.")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("A verification reason is required.")
        if type(self.evidence) is not dict:
            raise TypeError("Verification evidence must be a dictionary.")
        object.__setattr__(self, "reason", self.reason.strip())
        object.__setattr__(self, "evidence", _copy_evidence(self.evidence))


@runtime_checkable
class VerificationProvider(Protocol):
    """Optional observational check owned by a trusted capability implementation.

    Called only after successful execution. Inspect evidence or delegate to a
    service-owned observation; never retry the action, execute another action,
    or use a model to assert success. Structured requests carry the exact
    normalized execution arguments; legacy requests remain strings.
    """

    def verify_result(
        self, *, request: str | StructuredCapabilityRequest, output: Any,
    ) -> VerificationResult:
        ...
