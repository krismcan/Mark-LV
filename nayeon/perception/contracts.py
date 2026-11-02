"""Phase 10.1 perception evidence schema and PURE assessment.

This module never captures, reads, transmits, persists or displays screen/camera
content. Claims by the observation producer (including a digest and redaction
state) are NOT trusted capture attestations, user consent or task verification.
A trusted future service must separately enforce Permission -> Policy ->
Confirmation -> Execution -> Verification before invoking real capture.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z", re.ASCII)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
MAX_FRAME_DIMENSION = 16384
MAX_FRAME_PIXELS = 7680 * 4320
MAX_EVIDENCE_AGE_MS = 30_000
MAX_CLOCK_MS = 2**53 - 1


class ObservationSource(str, Enum):
    SCREEN = "screen"
    CAMERA = "camera"
    UI_METADATA = "ui_metadata"


class ObservationPurpose(str, Enum):
    DESCRIBE_CONTEXT = "describe_context"
    VERIFY_RESULT = "verify_result"


class RedactionClaim(str, Enum):
    """A producer-declared property; NOT independent proof of redaction."""
    UNKNOWN = "unknown"
    REDACTED = "redacted"
    UNREDACTED = "unredacted"


class AssessmentCode(str, Enum):
    """CANDIDATE never means authorized, authenticated or verified."""
    CANDIDATE = "candidate"
    BINDING_MISMATCH = "binding_mismatch"
    UNREDACTED = "unredacted_or_unproven"
    FUTURE_TIMESTAMP = "future_timestamp"
    STALE = "stale"


def _identifier(value: object, field: str) -> str:
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise ValueError("Invalid " + field)
    return value


def _clock_ms(value: object, field: str) -> int:
    if type(value) is not int or not 0 <= value <= MAX_CLOCK_MS:
        raise ValueError("Invalid " + field)
    return value


@dataclass(frozen=True, slots=True)
class ObservationRequest:
    """Untrusted intent metadata, not a permit to observe anything."""
    request_id: str
    session_id: str
    source: ObservationSource
    purpose: ObservationPurpose

    def __post_init__(self) -> None:
        _identifier(self.request_id, "request ID")
        _identifier(self.session_id, "session ID")
        if type(self.source) is not ObservationSource:
            raise TypeError("ObservationSource required")
        if type(self.purpose) is not ObservationPurpose:
            raise TypeError("ObservationPurpose required")


@dataclass(frozen=True, slots=True)
class ObservationCandidate:
    """Content-free producer claim; never carry pixels, audio or OCR text."""
    observation_id: str
    request_id: str
    session_id: str
    source: ObservationSource
    purpose: ObservationPurpose
    observed_at_ms: int
    content_sha256: str
    redaction: RedactionClaim
    width: int = 0
    height: int = 0

    def __post_init__(self) -> None:
        _identifier(self.observation_id, "observation ID")
        _identifier(self.request_id, "request ID")
        _identifier(self.session_id, "session ID")
        if type(self.source) is not ObservationSource:
            raise TypeError("ObservationSource required")
        if type(self.purpose) is not ObservationPurpose:
            raise TypeError("ObservationPurpose required")
        if type(self.redaction) is not RedactionClaim:
            raise TypeError("RedactionClaim required")
        _clock_ms(self.observed_at_ms, "observation time")
        if type(self.content_sha256) is not str or _DIGEST.fullmatch(self.content_sha256) is None:
            raise ValueError("Invalid content digest")
        if type(self.width) is not int or type(self.height) is not int:
            raise ValueError("Invalid frame dimensions")
        if self.source is ObservationSource.UI_METADATA:
            if self.width != 0 or self.height != 0:
                raise ValueError("UI metadata must not claim image dimensions")
        elif not (1 <= self.width <= MAX_FRAME_DIMENSION
                  and 1 <= self.height <= MAX_FRAME_DIMENSION
                  and self.width * self.height <= MAX_FRAME_PIXELS):
            raise ValueError("Invalid frame dimensions")


@dataclass(frozen=True, slots=True)
class ObservationAssessment:
    """Only structural/freshness eligibility for separate trusted review."""
    code: AssessmentCode
    observation_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.code) is not AssessmentCode:
            raise TypeError("AssessmentCode required")
        if self.observation_id is not None:
            _identifier(self.observation_id, "observation ID")

    @property
    def candidate_only(self) -> bool:
        """Not authorization, authenticated provenance or task outcome proof."""
        return self.code is AssessmentCode.CANDIDATE


def assess_observation(
    request: ObservationRequest,
    candidate: ObservationCandidate,
    *,
    now_ms: int,
    max_age_ms: int = MAX_EVIDENCE_AGE_MS,
) -> ObservationAssessment:
    """Pure, deterministic, fail-closed metadata screening.

    The caller must supply a trusted clock, and separately authenticate the
    origin, redaction, consent and permission state. This cannot confer
    authority even when returning CANDIDATE.
    """
    if type(request) is not ObservationRequest:
        raise TypeError("ObservationRequest required")
    if type(candidate) is not ObservationCandidate:
        raise TypeError("ObservationCandidate required")
    _clock_ms(now_ms, "current time")
    if type(max_age_ms) is not int or not 1 <= max_age_ms <= MAX_EVIDENCE_AGE_MS:
        raise ValueError("Invalid maximum age")
    if (request.request_id != candidate.request_id
            or request.session_id != candidate.session_id
            or request.source is not candidate.source
            or request.purpose is not candidate.purpose):
        return ObservationAssessment(AssessmentCode.BINDING_MISMATCH)
    if candidate.redaction is not RedactionClaim.REDACTED:
        return ObservationAssessment(AssessmentCode.UNREDACTED)
    if candidate.observed_at_ms > now_ms:
        return ObservationAssessment(AssessmentCode.FUTURE_TIMESTAMP)
    if now_ms - candidate.observed_at_ms > max_age_ms:
        return ObservationAssessment(AssessmentCode.STALE)
    return ObservationAssessment(AssessmentCode.CANDIDATE, candidate.observation_id)
