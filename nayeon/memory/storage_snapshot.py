"""Read-only, in-memory snapshots of caller-supplied memory record data."""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import DurableMemoryRecordV1, MemoryContractError, _identifier


MAX_SNAPSHOT_RECORDS = 256
MAX_SNAPSHOT_TEXT_BYTES = 256 * 1024


def _validate_record(record: DurableMemoryRecordV1) -> None:
    if type(record) is DurableMemoryRecordV1:
        try:
            DurableMemoryRecordV1.__post_init__(record)
            return
        except AttributeError:
            # An exact instance can still have unset slots.
            pass
    raise MemoryContractError("Invalid memory storage record") from None


@dataclass(frozen=True, slots=True, repr=False)
class MemoryStorageSnapshotV1:
    """List records by ascending ID through the immutable ``records`` tuple.

    The owner namespace groups records as data. Caller authentication, consent,
    durable custody, erasure, and trusted time are outside this contract.
    """

    owner_namespace: str
    records: tuple[DurableMemoryRecordV1, ...] = ()

    def __post_init__(self) -> None:
        _identifier(self.owner_namespace)
        if type(self.records) is not tuple or len(self.records) > MAX_SNAPSHOT_RECORDS:
            raise MemoryContractError("Invalid memory storage snapshot") from None

        by_id: dict[str, DurableMemoryRecordV1] = {}
        total_bytes = 0
        for record in self.records:
            _validate_record(record)
            if record.owner_namespace != self.owner_namespace or record.record_id in by_id:
                raise MemoryContractError("Invalid memory storage snapshot") from None
            total_bytes += len(record.text.encode("utf-8"))
            if total_bytes > MAX_SNAPSHOT_TEXT_BYTES:
                raise MemoryContractError("Invalid memory storage snapshot") from None
            by_id[record.record_id] = record

        object.__setattr__(self, "records", tuple(by_id[key] for key in sorted(by_id)))

    def get_record(self, record_id: str) -> DurableMemoryRecordV1 | None:
        """Return the original record or None for a well-formed missing ID."""
        _identifier(record_id)
        for record in self.records:
            if record.record_id == record_id:
                return record
        return None
