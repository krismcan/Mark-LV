"""Strict non-secret journal evidence for trusted onboarding recovery.

Evidence is not authority. In particular, a persisted READY record never
authorizes a new Windows mutex tenure. Only a separate trusted controller may
admit operations after fresh human reconciliation.
"""
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

SCHEMA_VERSION = 1
MAX_RECORD_BYTES = 4096
MAX_RECORDS = 128
MAX_JOURNAL_BYTES = 131072
GENESIS_HASH = "0" * 64
_HEX32 = re.compile(r"[0-9a-f]{32}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_OPERATION_KINDS = frozenset({
    "save_metadata", "clear_metadata", "connect", "replace", "remove",
    "review", "test_candidate", "test_stored"
})
_FIELDS = frozenset({
    "schema_version", "sequence", "epoch", "generation", "state",
    "previous_hash", "operation_id", "operation_kind", "evidence_hash"
})


class RecoveryEvidenceError(ValueError):
    """Missing, malformed or unverifiable evidence must fail closed."""


class RecoveryState(str, Enum):
    UNINITIALIZED = "uninitialized"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    RECONCILING = "reconciling"
    READY = "ready"
    IN_FLIGHT = "in_flight"
    QUARANTINED = "quarantined"
    UNAVAILABLE = "unavailable"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True, repr=False)
class RecoveryRecord:
    schema_version: int
    sequence: int
    epoch: str
    generation: int
    state: RecoveryState
    previous_hash: str
    operation_id: str | None = None
    operation_kind: str | None = None
    evidence_hash: str | None = None

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != SCHEMA_VERSION:
            raise RecoveryEvidenceError("Unsupported evidence schema")
        if type(self.sequence) is not int or not 1 <= self.sequence <= MAX_RECORDS:
            raise RecoveryEvidenceError("Invalid sequence")
        if type(self.generation) is not int or not 0 <= self.generation <= 2**63 - 1:
            raise RecoveryEvidenceError("Invalid generation")
        if type(self.epoch) is not str or _HEX32.fullmatch(self.epoch) is None:
            raise RecoveryEvidenceError("Invalid tenure identifier")
        if type(self.state) is not RecoveryState:
            raise RecoveryEvidenceError("Invalid recovery state")
        if type(self.previous_hash) is not str or _HEX64.fullmatch(self.previous_hash) is None:
            raise RecoveryEvidenceError("Invalid predecessor checksum")
        if self.operation_id is not None and (
            type(self.operation_id) is not str or _HEX32.fullmatch(self.operation_id) is None
        ):
            raise RecoveryEvidenceError("Invalid operation identifier")
        if self.operation_kind is not None and (
            type(self.operation_kind) is not str or self.operation_kind not in _OPERATION_KINDS
        ):
            raise RecoveryEvidenceError("Invalid operation kind")
        if self.evidence_hash is not None and (
            type(self.evidence_hash) is not str or _HEX64.fullmatch(self.evidence_hash) is None
        ):
            raise RecoveryEvidenceError("Invalid evidence checksum")
        if self.state is RecoveryState.IN_FLIGHT:
            if self.operation_id is None or self.operation_kind is None or self.evidence_hash is None:
                raise RecoveryEvidenceError("Incomplete in-flight evidence")
        elif self.operation_id is not None or self.operation_kind is not None:
            raise RecoveryEvidenceError("Non-flight record has operation authority")
        if self.state is RecoveryState.READY and self.evidence_hash is None:
            raise RecoveryEvidenceError("Ready requires explicit evidence")

    def to_payload(self) -> dict:
        return {
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


def _canonical(record: RecoveryRecord) -> bytes:
    if type(record) is not RecoveryRecord:
        raise RecoveryEvidenceError("Exact recovery record required")
    data = json.dumps(record.to_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if len(data) > MAX_RECORD_BYTES:
        raise RecoveryEvidenceError("Oversized journal record")
    return data


def record_hash(record: RecoveryRecord) -> str:
    return hashlib.sha256(_canonical(record)).hexdigest()


def encode_frame(record: RecoveryRecord) -> bytes:
    body = _canonical(record)
    return b"NRJ1 " + f"{len(body):04x}".encode("ascii") + b" " + hashlib.sha256(body).hexdigest().encode("ascii") + b" " + body + b"\n"


def _unique_pairs(pairs: list[tuple]) -> dict:
    output = {}
    for key, value in pairs:
        if key in output:
            raise RecoveryEvidenceError("Duplicate evidence field")
        output[key] = value
    return output


def decode_frame(line: bytes) -> RecoveryRecord:
    if type(line) is not bytes or not line.endswith(b"\n") or len(line) > MAX_RECORD_BYTES + 80:
        raise RecoveryEvidenceError("Incomplete or oversized frame")
    parts = line[:-1].split(b" ", 3)
    if len(parts) != 4 or parts[0] != b"NRJ1":
        raise RecoveryEvidenceError("Invalid frame marker")
    size, digest, body = parts[1:]
    if len(size) != 4 or re.fullmatch(rb"[0-9a-f]{4}", size) is None:
        raise RecoveryEvidenceError("Invalid frame size")
    if len(body) != int(size, 16) or len(body) > MAX_RECORD_BYTES:
        raise RecoveryEvidenceError("Frame length mismatch")
    if re.fullmatch(rb"[0-9a-f]{64}", digest) is None or hashlib.sha256(body).hexdigest().encode("ascii") != digest:
        raise RecoveryEvidenceError("Frame digest mismatch")
    try:
        obj = json.loads(body.decode("ascii"), object_pairs_hook=_unique_pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(RecoveryEvidenceError("Invalid numeric value")))
        if type(obj) is not dict or set(obj) != _FIELDS:
            raise RecoveryEvidenceError("Unexpected journal fields")
        state = RecoveryState(obj["state"])
        record = RecoveryRecord(state=state, **{key: value for key, value in obj.items() if key != "state"})
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        raise RecoveryEvidenceError("Invalid journal payload") from exc
    if _canonical(record) != body:
        raise RecoveryEvidenceError("Noncanonical journal payload")
    return record


def decode_journal(data: bytes) -> tuple[RecoveryRecord, ...]:
    if type(data) is not bytes or not data or len(data) > MAX_JOURNAL_BYTES:
        raise RecoveryEvidenceError("Missing or oversized journal")
    lines = data.splitlines(keepends=True)
    if len(lines) > MAX_RECORDS:
        raise RecoveryEvidenceError("Too many journal records")
    result = []
    expected_hash = GENESIS_HASH
    for i, line in enumerate(lines, start=1):
        record = decode_frame(line)
        if record.sequence != i or record.previous_hash != expected_hash:
            raise RecoveryEvidenceError("Broken journal chain")
        if result and record.generation < result[-1].generation:
            raise RecoveryEvidenceError("Regressing generation")
        result.append(record)
        expected_hash = record_hash(record)
    return tuple(result)
