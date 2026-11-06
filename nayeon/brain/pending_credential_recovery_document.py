"""Phase 8 C1: UNTRUSTED pending-custody evidence codec. No I/O or authority.

A valid hash chain checks internal structure only. It is not authenticated:
an attacker can forge, truncate, replay, replace or roll back entire histories.
No decoded record can prove readiness, consent, durability, or retry safety.
"""
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

_DOMAIN = "nayeon-v1-pending-custody"
_VERSION = 1
_PREFIX = b"NPC1\x00nayeon-v1-pending-custody\x00v1\x00"
_MAX_FRAME_BYTES = 4096
_MAX_JOURNAL_BYTES = 131072
_MAX_RECORDS = 128
_GENESIS = "0" * 64
_HEX32 = re.compile(r"[0-9a-f]{32}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_HEX4_BYTES = re.compile(rb"[0-9a-f]{4}\Z")
_KINDS = frozenset(("pending_save", "pending_replace", "pending_delete"))
_FIELDS = frozenset((
    "domain", "schema_version", "sequence", "epoch", "generation",
    "state", "previous_hash", "operation_id", "operation_kind", "evidence_hash",
))


class PendingEvidenceError(ValueError):
    """Fixed safe error for untrustworthy pending journal input."""


class PendingRecordedState(Enum):
    UNINITIALIZED = "uninitialized"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    IN_FLIGHT = "in_flight"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True, repr=False)
class PendingEvidenceRecord:
    """Claimed historical data, never an executable authorization or readiness."""

    schema_version: int
    sequence: int
    epoch: str
    generation: int
    state: PendingRecordedState
    previous_hash: str
    operation_id: str | None = None
    operation_kind: str | None = None
    evidence_hash: str | None = None

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != _VERSION:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        if type(self.sequence) is not int or not 1 <= self.sequence <= _MAX_RECORDS:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        if type(self.generation) is not int or not 0 <= self.generation <= 2**63 - 1:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        if type(self.epoch) is not str or _HEX32.fullmatch(self.epoch) is None:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        if type(self.previous_hash) is not str or _HEX64.fullmatch(self.previous_hash) is None:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        if type(self.state) is not PendingRecordedState:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        if self.state is PendingRecordedState.IN_FLIGHT:
            if (type(self.operation_id) is not str or
                    _HEX32.fullmatch(self.operation_id) is None or
                    type(self.operation_kind) is not str or
                    self.operation_kind not in _KINDS or
                    type(self.evidence_hash) is not str or
                    _HEX64.fullmatch(self.evidence_hash) is None):
                raise PendingEvidenceError("Invalid pending recovery evidence")
        elif (self.operation_id is not None or self.operation_kind is not None
              or self.evidence_hash is not None):
            raise PendingEvidenceError("Invalid pending recovery evidence")

    def to_payload(self) -> dict:
        return {
            "domain": _DOMAIN,
            "schema_version": self.schema_version,
            "sequence": self.sequence,
            "epoch": self.epoch,
            "generation": self.generation,
            "state": self.state.value,
            "previous_hash": self.previous_hash,
            "operation_id": self.operation_id,
            "operation_kind": self.operation_kind,
            "evidence_hash": self.evidence_hash,
        }

    def __repr__(self) -> str:
        return "PendingEvidenceRecord(<untrusted, nonsecret, no authority>)"


def _canonical(record: PendingEvidenceRecord) -> bytes:
    if type(record) is not PendingEvidenceRecord:
        raise PendingEvidenceError("Invalid pending recovery evidence")
    return json.dumps(record.to_payload(), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def record_hash(record: PendingEvidenceRecord) -> str:
    """Only an untrusted structural hash; NOT an authentication digest."""
    return hashlib.sha256(_PREFIX + _canonical(record)).hexdigest()


def encode_frame(record: PendingEvidenceRecord) -> bytes:
    body = _canonical(record)
    frame = (b"NPC1 " + f"{len(body):04x}".encode("ascii") +
             b" " + record_hash(record).encode("ascii") + b" " + body + b"\n")
    if len(frame) > _MAX_FRAME_BYTES:
        raise PendingEvidenceError("Invalid pending recovery evidence")
    return frame


def _unique_pairs(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        result[key] = value
    return result


def _bad_constant(_text: str):
    raise PendingEvidenceError("Invalid pending recovery evidence")


def decode_frame(frame: bytes) -> PendingEvidenceRecord:
    if (type(frame) is not bytes or not 1 <= len(frame) <= _MAX_FRAME_BYTES
            or not frame.endswith(b"\n")):
        raise PendingEvidenceError("Invalid pending recovery evidence")
    try:
        components = frame[:-1].split(b" ", 3)
        if len(components) != 4 or components[0] != b"NPC1":
            raise PendingEvidenceError("Invalid pending recovery evidence")
        size, expected, body = components[1:]
        if (_HEX4_BYTES.fullmatch(size) is None or len(body) != int(size, 16)
                or len(expected) != 64 or
                re.fullmatch(rb"[0-9a-f]{64}", expected) is None):
            raise PendingEvidenceError("Invalid pending recovery evidence")
        obj = json.loads(body.decode("ascii"), object_pairs_hook=_unique_pairs,
                         parse_constant=_bad_constant)
        if type(obj) is not dict or set(obj) != _FIELDS:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        if obj["domain"] != _DOMAIN or type(obj["domain"]) is not str:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        state_raw = obj["state"]
        if type(state_raw) is not str:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        state = PendingRecordedState(state_raw)
        record = PendingEvidenceRecord(
            state=state, **{key: val for key, val in obj.items()
                            if key not in ("state", "domain")})
        if _canonical(record) != body or record_hash(record).encode("ascii") != expected:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        return record
    except (ValueError, TypeError, KeyError, OverflowError, UnicodeError,
            RecursionError) as exc:
        raise PendingEvidenceError("Invalid pending recovery evidence") from None


def decode_journal(blob: bytes) -> tuple[PendingEvidenceRecord, ...]:
    """Decode STRUCTURE only; NEVER grant ownership or effect authority."""
    if type(blob) is not bytes or not 1 <= len(blob) <= _MAX_JOURNAL_BYTES:
        raise PendingEvidenceError("Invalid pending recovery evidence")
    lines = blob.splitlines(keepends=True)
    if not 1 <= len(lines) <= _MAX_RECORDS:
        raise PendingEvidenceError("Invalid pending recovery evidence")
    history = []
    predecessor = _GENESIS
    for seq, line in enumerate(lines, 1):
        if len(line) > _MAX_FRAME_BYTES:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        record = decode_frame(line)
        if record.sequence != seq or record.previous_hash != predecessor:
            raise PendingEvidenceError("Invalid pending recovery evidence")
        if history:
            prior = history[-1]
            if (record.generation == prior.generation and
                    record.epoch != prior.epoch):
                raise PendingEvidenceError("Invalid pending recovery evidence")
            if (record.generation != prior.generation + 1 and
                    record.generation != prior.generation):
                raise PendingEvidenceError("Invalid pending recovery evidence")
            if (record.generation == prior.generation + 1 and
                    record.epoch == prior.epoch):
                raise PendingEvidenceError("Invalid pending recovery evidence")
        history.append(record)
        predecessor = record_hash(record)
    return tuple(history)
