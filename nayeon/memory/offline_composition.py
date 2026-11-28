"""Offline composition over caller-supplied memory snapshots.

Lifecycle functions return prospective snapshots. Owner, revision, provenance
and time fields are data only. This facade confers no identity, consent,
persistent custody or erasure.
"""
from __future__ import annotations

from .contracts import DurableMemoryRecordV1, MemoryRetrievalBatchV1
from .lifecycle import (
    _validated_snapshot,
    add_memory_record_v1,
    correct_memory_record_v1,
    filter_expired_memory_records_v1,
    remove_memory_record_v1,
)
from .retrieval import retrieve_memory_v1 as _retrieve_memory_v1
from .storage_snapshot import MemoryStorageSnapshotV1


__all__ = [
    "add_memory_record_v1",
    "correct_memory_record_v1",
    "filter_expired_memory_records_v1",
    "get_memory_record_v1",
    "remove_memory_record_v1",
    "retrieve_memory_from_snapshot_v1",
]


def get_memory_record_v1(
    snapshot: MemoryStorageSnapshotV1,
    record_id: str,
    *,
    owner_namespace: str,
) -> DurableMemoryRecordV1 | None:
    """Look up stored data by ID, including expired or future-effective records."""
    return _validated_snapshot(snapshot, owner_namespace).get_record(record_id)


def retrieve_memory_from_snapshot_v1(
    snapshot: MemoryStorageSnapshotV1,
    query: str,
    *,
    owner_namespace: str,
    as_of_utc: int,
) -> MemoryRetrievalBatchV1:
    """Rank active records at the supplied time as bounded, untrusted data."""
    validated = _validated_snapshot(snapshot, owner_namespace)
    return _retrieve_memory_v1(
        query, validated.records, owner_namespace=owner_namespace, as_of_utc=as_of_utc,
    )
