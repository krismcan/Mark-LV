"""P93 disposable subprocess crash fixture using the ACTUAL pending evidence codec.

TESTS-ONLY OS temporary directory. Nonsecret deterministic placeholders; no
WinCred, real service, credential material, protected directory, real journal
adapter, elevated rights, recovery approval, or production source integration.
The companion anchor is a structural TEST CLAIM, never OS authentication.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import os
from pathlib import Path
import sys
import tempfile

from nayeon.brain import pending_credential_recovery_document as codec

_EXIT_CUT = 73
_EPOCH = "a" * 32
_DIGEST = "c" * 64
_GENESIS = "0" * 64
CUTPOINTS = (
    "before_first_write",
    "after_initial_frame",
    "after_initial_anchor",
    "after_inflight_partial",
    "after_inflight_frame",
    "after_inflight_anchor",
    "after_blocked_frame",
    "after_blocked_anchor",
)
_MAX_BYTES = 131072


class FixtureReadKind(Enum):
    NO_TRUST_SOURCE = "no_trust_source"
    MISSING_PAIR = "missing_pair"
    INVALID_JOURNAL = "invalid_journal"
    INVALID_ANCHOR = "invalid_anchor"
    STRUCTURAL_INITIAL = "structural_initial"
    STRUCTURAL_IN_FLIGHT = "structural_in_flight"
    STRUCTURAL_BLOCKED = "structural_blocked"


@dataclass(frozen=True, slots=True)
class FixtureReadout:
    kind: FixtureReadKind
    # These are constant FALSE: structural validity never authenticates custody.
    retry_allowed: bool = False
    credential_authority: bool = False
    product_verified: bool = False

    def __repr__(self):
        return "<P93 fake-only, no authenticated recovery or retry>"


def _fixture_root(value: Path) -> Path:
    """Refuse unrecognised directories; no release-store or source-tree access."""
    path = Path(value).resolve(strict=True)
    parent = Path(tempfile.gettempdir()).resolve(strict=True)
    if (path.parent != parent or
            not path.name.startswith("nayeon-p93-test-") or
            not path.is_dir() or path.is_symlink()):
        raise ValueError("Not an isolated synthetic test directory")
    return path


def _paths(root: Path) -> tuple[Path, Path]:
    safe = _fixture_root(root)
    return safe / "fixture-journal.bytes", safe / "fixture-anchor.bytes"


def _initial() -> codec.PendingEvidenceRecord:
    return codec.PendingEvidenceRecord(
        1, 1, _EPOCH, 0, codec.PendingRecordedState.UNINITIALIZED, _GENESIS)


def _inflight(first: codec.PendingEvidenceRecord) -> codec.PendingEvidenceRecord:
    return codec.PendingEvidenceRecord(
        1, 2, _EPOCH, 0, codec.PendingRecordedState.IN_FLIGHT,
        codec.record_hash(first), "d" * 32, "pending_save", _DIGEST)


def _blocked(previous: codec.PendingEvidenceRecord) -> codec.PendingEvidenceRecord:
    return codec.PendingEvidenceRecord(
        1, 3, _EPOCH, 0, codec.PendingRecordedState.BLOCKED,
        codec.record_hash(previous))


def _persist_append(path: Path, blob: bytes, *, new: bool = False) -> None:
    if type(blob) is not bytes or not blob or len(blob) > 4096:
        raise ValueError("Invalid synthetic frame bytes")
    with path.open("xb" if new else "ab") as handle:
        handle.write(blob)
        handle.flush()
        os.fsync(handle.fileno())


def _claim(journal: bytes, count: int) -> bytes:
    return ("P93A|" + str(count) + "|" +
            hashlib.sha256(journal).hexdigest() + "\n").encode("ascii")


def _persist_claim(root: Path, journal: Path, anchor: Path, count: int) -> None:
    # A synthetic second-file write. This does not provide Windows ACL,
    # registry anchoring, atomicity of paired state, or crash-proof durability.
    data = journal.read_bytes()
    next_path = root / "fixture-anchor.next"
    with next_path.open("xb") as handle:
        handle.write(_claim(data, count))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(next_path, anchor)


def _cut(name: str, target: str) -> None:
    if name == target:
        os._exit(_EXIT_CUT)  # Deliberate disposable child process exit only.


def simulate_worker(root: Path, cutpoint: str) -> None:
    if type(cutpoint) is not str or cutpoint not in CUTPOINTS:
        raise ValueError("Unknown synthetic cutpoint")
    journal, anchor = _paths(root)
    if any(p.exists() for p in (journal, anchor)):
        raise ValueError("Fixture is not empty")
    _cut(cutpoint, "before_first_write")
    first = _initial()
    _persist_append(journal, codec.encode_frame(first), new=True)
    _cut(cutpoint, "after_initial_frame")
    _persist_claim(root, journal, anchor, 1)
    _cut(cutpoint, "after_initial_anchor")
    inflight = _inflight(first)
    frame = codec.encode_frame(inflight)
    if cutpoint == "after_inflight_partial":
        _persist_append(journal, frame[:19])
        _cut(cutpoint, "after_inflight_partial")
    _persist_append(journal, frame)
    _cut(cutpoint, "after_inflight_frame")
    _persist_claim(root, journal, anchor, 2)
    _cut(cutpoint, "after_inflight_anchor")
    blocked = _blocked(inflight)
    _persist_append(journal, codec.encode_frame(blocked))
    _cut(cutpoint, "after_blocked_frame")
    _persist_claim(root, journal, anchor, 3)
    _cut(cutpoint, "after_blocked_anchor")
    raise AssertionError("Synthetic cutpoint was not reached")


def observe_untrusted_fixture(root: Path) -> FixtureReadout:
    """Read-only structural view. Returns no trusted state or effect authority."""
    journal, anchor = _paths(root)
    if not journal.exists() and not anchor.exists():
        return FixtureReadout(FixtureReadKind.NO_TRUST_SOURCE)
    if not journal.is_file() or not anchor.is_file():
        return FixtureReadout(FixtureReadKind.MISSING_PAIR)
    try:
        if not (0 < journal.stat().st_size <= _MAX_BYTES and
                0 < anchor.stat().st_size <= 128):
            raise ValueError("Unbounded synthetic evidence")
        data = journal.read_bytes()
        records = codec.decode_journal(data)
        claim = anchor.read_bytes()
        if claim != _claim(data, len(records)):
            return FixtureReadout(FixtureReadKind.INVALID_ANCHOR)
    except (OSError, ValueError, TypeError, UnicodeError):
        return FixtureReadout(FixtureReadKind.INVALID_JOURNAL)
    state = records[-1].state
    if state is codec.PendingRecordedState.IN_FLIGHT:
        kind = FixtureReadKind.STRUCTURAL_IN_FLIGHT
    elif state is codec.PendingRecordedState.UNINITIALIZED:
        kind = FixtureReadKind.STRUCTURAL_INITIAL
    else:
        kind = FixtureReadKind.STRUCTURAL_BLOCKED
    return FixtureReadout(kind)


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "--worker":
        raise SystemExit(2)
    simulate_worker(Path(sys.argv[2]), sys.argv[3])
    raise SystemExit(3)
