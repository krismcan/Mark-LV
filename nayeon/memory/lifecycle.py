"""Pure projections over synthetic memory snapshots.

Owner, time, and revision values are caller-supplied data. Frozen Python
objects and these consistency checks confer no authentication or consent.
"""
from __future__ import annotations

from dataclasses import replace

from .contracts import (
    MAX_REVISION,
    DurableMemoryRecordV1,
    MemoryContractError,
    _identifier,
    _time,
)
from .storage_snapshot import MemoryStorageSnapshotV1, _validate_record


def _validated_snapshot(
    snapshot: MemoryStorageSnapshotV1, owner_namespace: str
) -> MemoryStorageSnapshotV1:
    _identifier(owner_namespace)
    if type(snapshot) is not MemoryStorageSnapshotV1:
        raise MemoryContractError("Invalid memory lifecycle snapshot") from None

    records = getattr(snapshot, "records", None)
    validated = MemoryStorageSnapshotV1(getattr(snapshot, "owner_namespace", None), records)
    if validated.owner_namespace != owner_namespace or validated.records != records:
        raise MemoryContractError("Invalid memory lifecycle snapshot") from None
    return validated


def _expected_record(
    snapshot: MemoryStorageSnapshotV1, record_id: str, expected_revision: int
) -> DurableMemoryRecordV1:
    if type(expected_revision) is not int or not 1 <= expected_revision <= MAX_REVISION:
        raise MemoryContractError("Invalid expected memory revision") from None
    record = snapshot.get_record(record_id)
    if record is None or record.revision != expected_revision:
        raise MemoryContractError("Memory record expectation did not match") from None
    return record


def add_memory_record_v1(
    snapshot: MemoryStorageSnapshotV1,
    record: DurableMemoryRecordV1,
    *,
    owner_namespace: str,
) -> MemoryStorageSnapshotV1:
    """Project an initial record with valid timestamps and an unused ID."""
    validated = _validated_snapshot(snapshot, owner_namespace)
    _validate_record(record)
    if record.revision != 1:
        raise MemoryContractError("Invalid initial memory revision") from None
    return MemoryStorageSnapshotV1(owner_namespace, validated.records + (record,))


def correct_memory_record_v1(
    snapshot: MemoryStorageSnapshotV1,
    record_id: str,
    *,
    owner_namespace: str,
    expected_revision: int,
    text: str,
    corrected_at_utc: int,
) -> MemoryStorageSnapshotV1:
    """Project a text correction within the current revision's active window.

    The window starts at confirmation or the most recent correction, inclusive,
    and ends at expiry, exclusive. Revisions order corrections in the same second.
    """
    validated = _validated_snapshot(snapshot, owner_namespace)
    record = _expected_record(validated, record_id, expected_revision)
    _time(corrected_at_utc)
    effective_at = record.corrected_at_utc
    if effective_at is None:
        effective_at = record.confirmed_at_utc
    if not effective_at <= corrected_at_utc < record.expires_at_utc:
        raise MemoryContractError("Invalid memory correction time") from None
    if record.revision == MAX_REVISION:
        raise MemoryContractError("Memory revision limit reached") from None

    corrected = replace(record, text=text, corrected_at_utc=corrected_at_utc,
                        revision=record.revision + 1)
    records = tuple(corrected if item is record else item for item in validated.records)
    return MemoryStorageSnapshotV1(owner_namespace, records)


def remove_memory_record_v1(
    snapshot: MemoryStorageSnapshotV1,
    record_id: str,
    *,
    owner_namespace: str,
    expected_revision: int,
) -> MemoryStorageSnapshotV1:
    """Project removal of a matching revision, including an expired record."""
    validated = _validated_snapshot(snapshot, owner_namespace)
    record = _expected_record(validated, record_id, expected_revision)
    return MemoryStorageSnapshotV1(
        owner_namespace, tuple(item for item in validated.records if item is not record)
    )


def filter_expired_memory_records_v1(
    snapshot: MemoryStorageSnapshotV1,
    *,
    owner_namespace: str,
    as_of_utc: int,
) -> MemoryStorageSnapshotV1:
    """Project removal at or after expiry, retaining future-effective records."""
    validated = _validated_snapshot(snapshot, owner_namespace)
    _time(as_of_utc)
    records = tuple(record for record in validated.records if as_of_utc < record.expires_at_utc)
    return MemoryStorageSnapshotV1(owner_namespace, records)
