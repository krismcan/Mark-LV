"""Pure, in-process snapshot JSON for explicitly supplied synthetic records.

Plaintext bytes have no custody or confidentiality and MUST NOT be persisted,
logged or sent to any provider. The owner namespace is a data selector.

V1 uses compact UTF-8 JSON with ordered schema_version, owner_namespace and
records fields. The array contains canonical record JSON objects in ascending
record ID order. The decoder accepts only that exact representation.
"""
from __future__ import annotations

from .contracts import (
    MAX_RECORD_JSON_BYTES,
    MemoryContractError,
    _identifier,
    memory_record_to_json_v1,
    parse_memory_record_json_v1,
)
from .lifecycle import _validated_snapshot
from .storage_snapshot import MAX_SNAPSHOT_RECORDS, MemoryStorageSnapshotV1


_PREFIX = b'{"schema_version":1,"owner_namespace":"'
_RECORDS = b'","records":['
_SUFFIX = b']}'
MAX_SNAPSHOT_JSON_BYTES = (
    len(_PREFIX) + 32 + len(_RECORDS) + len(_SUFFIX)
    + MAX_SNAPSHOT_RECORDS * (MAX_RECORD_JSON_BYTES + 1) - 1
)


def _deny() -> None:
    raise MemoryContractError("Invalid memory snapshot JSON") from None


def _header(owner_namespace: str) -> bytes:
    _identifier(owner_namespace)
    return _PREFIX + owner_namespace.encode("ascii") + _RECORDS


def _record_end(blob: bytes, start: int, stop: int) -> int:
    """Find the end of a bounded flat object before calling the record parser."""
    if blob[start:start + 1] != b'{':
        _deny()
    quoted = False
    escaped = False
    for index in range(start + 1, min(stop, start + MAX_RECORD_JSON_BYTES)):
        char = blob[index:index + 1]
        if quoted:
            if escaped:
                escaped = False
            elif char == b'\\':
                escaped = True
            elif char == b'"':
                quoted = False
        elif char == b'"':
            quoted = True
        elif char == b'}':
            return index + 1
        elif char in (b'{', b'[', b']'):
            _deny()
    _deny()


def memory_snapshot_to_json_v1(
    snapshot: MemoryStorageSnapshotV1, *, owner_namespace: str,
) -> bytes:
    """Encode an exact, validated snapshot for the supplied owner namespace."""
    snapshot = _validated_snapshot(snapshot, owner_namespace)
    records = b','.join(memory_record_to_json_v1(record) for record in snapshot.records)
    return _header(owner_namespace) + records + _SUFFIX


def parse_memory_snapshot_json_v1(
    blob: bytes, *, owner_namespace: str,
) -> MemoryStorageSnapshotV1:
    """Decode canonical V1 bytes and enforce the supplied owner and snapshot bounds."""
    if type(blob) is not bytes or not 1 <= len(blob) <= MAX_SNAPSHOT_JSON_BYTES:
        _deny()
    header = _header(owner_namespace)
    if not blob.startswith(header) or not blob.endswith(_SUFFIX):
        _deny()

    # Check every record's framing, size and depth before parsing any JSON.
    cursor = len(header)
    stop = len(blob) - len(_SUFFIX)
    spans: list[tuple[int, int]] = []
    while cursor < stop:
        if len(spans) == MAX_SNAPSHOT_RECORDS:
            _deny()
        end = _record_end(blob, cursor, stop)
        spans.append((cursor, end))
        cursor = end
        if cursor < stop:
            if blob[cursor:cursor + 1] != b',' or cursor + 1 == stop:
                _deny()
            cursor += 1

    records = []
    for start, end in spans:
        encoded = blob[start:end]
        record = parse_memory_record_json_v1(encoded)
        if memory_record_to_json_v1(record) != encoded:
            _deny()
        records.append(record)

    inventory = tuple(records)
    snapshot = MemoryStorageSnapshotV1(owner_namespace, inventory)
    if snapshot.records != inventory:
        _deny()
    return snapshot
