"""Unintegrated Windows-only original BYOK-B NTFS source-admission candidate.

P201 review candidate, NOT the public current Phase10 product verifier.
Never overwrites or monkeypatches historical security assertions. No credential
authority, installer, service, signing root, or production activation.

The historical full B gate callback is supplied by an isolated trusted-test
harness; a hostile caller can fake it. Future production integration MUST
bind an actual independently authenticated gate in the trusted service.
"""
from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys
from typing import Callable

class PhysicalAdmissionDenied(RuntimeError):
    """Fail-closed candidate denial; no fallback to legacy admission."""

@dataclass(frozen=True)
class PhysicalBAdmission:
    historical_gate_state: str
    admitted_source_count: int
    original_b_pins: tuple[str, ...]
    integration_status: str = "ISOLATED_P201_CANDIDATE_NOT_PRODUCTION"

ALLOWED_STATES = frozenset(("COMPLETE_UNSTAGED","EXACT_STAGED","EXACT_CHILD"))

def assert_isolated_original_b_with_ntfs_physical_guard(
    root: Path, *, historical_gate: Callable[[], str] | None = None,
) -> PhysicalBAdmission:
    """Wrap original complete historical B gate with 23 exact HANDLE checks.

    Every allowed original-B path is opened on a genuine Windows HANDLE by
    the P190 proof-of-concept helper; it refuses all non-default NTFS streams,
    extra hardlinks, reparse components, bad source bytes and unreadable
    metadata. Original historical gate executes BEFORE and AFTER these 23
    inspections; no decision is cached or inherited across invocations.

    Limitations: the pre/post sequence is NOT atomic across the 23 source
    files, and the P190 parent identity snapshot can be ABA-raced. Caller-
    supplied historical_gate is a LAB injection point only. Raw validated
    bytes are NOT delivered to a trusted executing consumer by this API.
    """
    if sys.platform != "win32" or os.name != "nt":
        raise PhysicalAdmissionDenied("P201_ONLY_TRUE_NATIVE_WINDOWS")
    if historical_gate is None or not callable(historical_gate):
        raise PhysicalAdmissionDenied("P201_INDEPENDENT_FULL_B_GATE_MISSING")
    if not isinstance(root, Path) or not root.is_absolute():
        raise PhysicalAdmissionDenied("P201_ABSOLUTE_SOURCE_ROOT_REQUIRED")

    # Import source authority only at call time so importing this dormant
    # candidate never starts a service or touches credentials.
    try:
        from tests import phase8_byok_b_scope_migration as B
        from scripts.p190_windows_handle_bound_source_probe import (
            Win32HandleBoundSourceProbe, SourceDenied
        )
        if (len(B.CANDIDATE_SHA256) != 23 or len(B.ENVELOPE) != 23 or
            set(B.CANDIDATE_SHA256) != set(B.ENVELOPE) or
            B.SELF not in B.CANDIDATE_SHA256 or
            len(B.ADDED) != 7 or len(B.MODIFIED) != 16):
            raise PhysicalAdmissionDenied("P201_ORIGINAL_B_23_PIN_ENVELOPE_INVALID")
        if not all(type(p) is str and "/" in p and
                   ".." not in p.split("/") and ":" not in p and "\\" not in p and
                   isinstance(digest,str) and re.fullmatch(r"[0-9a-f]{64}",digest)
                   for p,digest in B.CANDIDATE_SHA256.items()):
            raise PhysicalAdmissionDenied("P201_INVALID_ORIGINAL_B_CANONICAL_PATH_OR_PIN")
        candidate = Win32HandleBoundSourceProbe(root)
        before = historical_gate()
        if type(before) is not str or before not in ALLOWED_STATES:
            raise PhysicalAdmissionDenied("P201_FULL_ORIGINAL_B_BEFORE_ADMISSION_DENIED")
        for path in sorted(B.ENVELOPE):
            try:
                raw = candidate.read(path)
            except SourceDenied as exc:
                raise PhysicalAdmissionDenied("P201_PHYSICAL_B_SOURCE_REFUSED:"+str(exc)) from exc
            # This is intentionally redundant with candidate.read's original
            # literal SHA verification, not a weakening or a new trust root.
            if B._digest(path,raw) != B.CANDIDATE_SHA256[path]:
                raise PhysicalAdmissionDenied("P201_ORIGINAL_B_SOURCE_DIGEST_MISMATCH")
        after = historical_gate()
        if type(after) is not str or after != before:
            raise PhysicalAdmissionDenied("P201_FULL_ORIGINAL_B_AFTER_ADMISSION_DRIFT")
        return PhysicalBAdmission(before,len(B.ENVELOPE),tuple(sorted(B.ENVELOPE)))
    except PhysicalAdmissionDenied:
        raise
    except BaseException as exc:
        # NEVER convert a failed Git integrity check, metadata exception or
        # legacy gate refusal into success. Preserve denial provenance.
        raise PhysicalAdmissionDenied("P201_B_CANDIDATE_FAIL_CLOSED:"+
                                      type(exc).__name__+":"+str(exc)[:240]) from exc
