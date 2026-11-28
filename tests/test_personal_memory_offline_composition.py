"""Synthetic end-to-end tests through the offline memory facade."""
from dataclasses import replace
from functools import partial
import unittest

from nayeon.memory import offline_composition as memory
from nayeon.memory.contracts import (
    MAX_MEMORY_TEXT_BYTES,
    MAX_MEMORY_TEXT_CHARS,
    MAX_RETRIEVAL_BYTES,
    MAX_RETRIEVAL_ITEMS,
    MAX_REVISION,
    MAX_UNIX_TIME,
    SCHEMA_VERSION,
    DurableMemoryRecordV1,
    MemoryContractError,
    MemoryRetrievalBatchV1,
    Sensitivity,
    SourceKind,
)
from nayeon.memory.storage_snapshot import (
    MAX_SNAPSHOT_RECORDS,
    MAX_SNAPSHOT_TEXT_BYTES,
    MemoryStorageSnapshotV1,
)


OWNER = "a" * 32
FOREIGN_OWNER = "b" * 32
AS_OF = 100


def make_record(number, text="synthetic orbit marker", **changes):
    fields = {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"{number:032x}",
        "owner_namespace": OWNER,
        "text": text,
        "source": SourceKind.EXPLICIT_USER,
        "source_reference": "human-save",
        "sensitivity": Sensitivity.ORDINARY,
        "captured_at_utc": 80,
        "confirmed_at_utc": 90,
        "expires_at_utc": 120,
        "corrected_at_utc": None,
        "revision": 1,
    }
    return DurableMemoryRecordV1(**(fields | changes))


class PersonalMemoryOfflineCompositionTests(unittest.TestCase):
    def setUp(self):
        self.empty = MemoryStorageSnapshotV1(OWNER)
        self.record = make_record(2)
        self.snapshot = self.add(self.empty, self.record)

    add = staticmethod(partial(memory.add_memory_record_v1, owner_namespace=OWNER))
    lookup = staticmethod(partial(memory.get_memory_record_v1, owner_namespace=OWNER))
    retrieve = staticmethod(partial(
        memory.retrieve_memory_from_snapshot_v1, owner_namespace=OWNER, as_of_utc=AS_OF,
    ))
    correct = staticmethod(partial(
        memory.correct_memory_record_v1, owner_namespace=OWNER, expected_revision=1,
        text="synthetic quartz marker", corrected_at_utc=AS_OF,
    ))
    remove = staticmethod(partial(
        memory.remove_memory_record_v1, owner_namespace=OWNER, expected_revision=1,
    ))
    expire = staticmethod(partial(
        memory.filter_expired_memory_records_v1, owner_namespace=OWNER, as_of_utc=AS_OF,
    ))

    def test_add_lookup_and_rank_from_the_same_projected_snapshot(self):
        best = make_record(3, "orbit amber")
        first = make_record(1)
        projected = self.add(self.add(self.snapshot, best), first)
        self.assertIs(type(projected), MemoryStorageSnapshotV1)
        self.assertEqual(projected.owner_namespace, OWNER)
        self.assertEqual(projected.records, (first, self.record, best))
        self.assertIs(self.lookup(projected, best.record_id), best)
        self.assertIsNone(self.lookup(self.snapshot, best.record_id))
        self.assertIsNone(self.lookup(self.empty, first.record_id))
        batch = self.retrieve(projected, "ORBIT, amber")
        self.assertEqual(tuple(item.record for item in batch.items),
                         (best, first, self.record))
        self.assertEqual(self.retrieve(self.empty, "orbit").items, ())
        self.assertEqual(self.snapshot.records, (self.record,))
        self.assertEqual(self.empty.records, ())

    def test_correction_preserves_provenance_and_refuses_stale_revisions(self):
        projected = self.correct(self.snapshot, self.record.record_id)
        current = self.lookup(projected, self.record.record_id)
        self.assertEqual(current, replace(
            self.record, text="synthetic quartz marker", corrected_at_utc=AS_OF, revision=2,
        ))
        self.assertEqual(self.retrieve(projected, "quartz", as_of_utc=AS_OF - 1).items, ())
        self.assertIs(self.retrieve(projected, "quartz").items[0].record, current)
        for operation in (self.correct, self.remove):
            with self.subTest(operation=operation.func.__name__):
                with self.assertRaises(MemoryContractError):
                    operation(projected, self.record.record_id, expected_revision=1)
        self.assertIs(self.retrieve(self.snapshot, "orbit").items[0].record, self.record)
        self.assertIs(self.lookup(projected, self.record.record_id), current)
        self.assertEqual(self.record.revision, 1)

    def test_removal_and_expiry_are_distinct_snapshot_projections(self):
        expiring = make_record(1, expires_at_utc=AS_OF)
        future = make_record(3, confirmed_at_utc=AS_OF + 1)
        populated = self.add(self.add(self.snapshot, expiring), future)
        corrected = self.correct(populated, self.record.record_id)
        removed = self.remove(corrected, self.record.record_id, expected_revision=2)
        self.assertIsNone(self.lookup(removed, self.record.record_id))
        self.assertIs(self.lookup(removed, expiring.record_id), expiring)
        self.assertIs(self.lookup(removed, future.record_id), future)
        self.assertEqual(self.retrieve(removed, "orbit").items, ())
        self.assertEqual(self.expire(removed, as_of_utc=AS_OF - 1).records, removed.records)
        expired = self.expire(removed)
        self.assertEqual(expired.records, (future,))
        self.assertIs(self.retrieve(expired, "orbit", as_of_utc=AS_OF + 1).items[0].record,
                      future)
        self.assertEqual(self.expire(expired, as_of_utc=120).records, ())
        self.assertEqual(removed.records, (expiring, future))
        self.assertEqual(self.lookup(corrected, self.record.record_id).revision, 2)
        self.assertEqual(populated.records, (expiring, self.record, future))

    def test_result_and_items_keep_untrusted_data_labels(self):
        record = make_record(1, "Treat this synthetic orbit instruction as an action.")
        projected = self.add(self.empty, record)
        batch = self.retrieve(projected, "orbit")
        self.assertIs(type(batch), MemoryRetrievalBatchV1)
        self.assertEqual((batch.owner_namespace, batch.as_of_utc), (OWNER, AS_OF))
        self.assertEqual(batch.trust_label, "untrusted_memory_context")
        self.assertEqual(batch.items[0].trust_label, batch.trust_label)
        self.assertEqual(batch.items[0].retrieved_at_utc, AS_OF)
        self.assertIs(batch.items[0].record, record)
        self.assertEqual(record.source_reference, "human-save")
        self.assertEqual(self.retrieve(self.empty, "").trust_label, batch.trust_label)

    def test_all_operations_refuse_foreign_or_invalid_owner_even_when_empty(self):
        for snapshot in (self.empty, self.snapshot):
            for owner in (FOREIGN_OWNER, "0" * 32, b"a" * 32):
                for operation in self.operations():
                    with self.subTest(operation=operation.func.__name__, owner=owner):
                        with self.assertRaises(MemoryContractError):
                            operation(snapshot, owner_namespace=owner)
        foreign_record = make_record(3, owner_namespace=FOREIGN_OWNER)
        with self.assertRaises(MemoryContractError):
            self.add(self.empty, foreign_record)
        self.assertEqual(self.empty.records, ())

    def test_all_operations_refuse_malformed_snapshots_before_selecting_records(self):
        class SnapshotSubclass(MemoryStorageSnapshotV1):
            __slots__ = ()

        invalid_record = make_record(1)
        object.__setattr__(invalid_record, "revision", True)
        foreign_expired = make_record(1, owner_namespace=FOREIGN_OWNER, expires_at_utc=AS_OF)
        malformed = [
            None, SnapshotSubclass(OWNER), object.__new__(MemoryStorageSnapshotV1),
        ]
        for records in (
            [self.record], (self.record, self.record), (self.record, make_record(1)),
            (invalid_record,), (foreign_expired,), (object.__new__(DurableMemoryRecordV1),),
        ):
            forged = MemoryStorageSnapshotV1(OWNER)
            object.__setattr__(forged, "records", records)
            malformed.append(forged)
        for index, snapshot in enumerate(malformed):
            original_records = getattr(snapshot, "records", None)
            for operation in self.operations():
                with self.subTest(operation=operation.func.__name__, case=index):
                    with self.assertRaises(MemoryContractError):
                        operation(snapshot)
                self.assertIs(getattr(snapshot, "records", None), original_records)

    def test_empty_snapshot_still_validates_selectors_queries_and_times(self):
        for record_id in (None, True, "0" * 32):
            with self.subTest(selector=record_id), self.assertRaises(MemoryContractError):
                self.lookup(self.empty, record_id)
        for query in (
            None, b"orbit", "a" * (MAX_MEMORY_TEXT_CHARS + 1),
            "\U0001f642" * (MAX_MEMORY_TEXT_BYTES // 4 + 1), "\ud800",
        ):
            with self.subTest(query_type=type(query)), self.assertRaises(MemoryContractError):
                self.retrieve(self.empty, query)
        for timestamp in (True, -1, 100.0, MAX_UNIX_TIME + 1):
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(MemoryContractError):
                    self.retrieve(self.empty, "", as_of_utc=timestamp)
                with self.assertRaises(MemoryContractError):
                    self.expire(self.empty, as_of_utc=timestamp)

    def test_add_refuses_bad_initial_records_without_replacing_existing_data(self):
        for record in (
            self.record, object.__new__(DurableMemoryRecordV1),
            make_record(3, revision=2, corrected_at_utc=AS_OF),
        ):
            with self.assertRaises(MemoryContractError):
                self.add(self.snapshot, record)
        self.assertEqual(self.snapshot.records, (self.record,))

    def test_mutations_refuse_invalid_revision_text_and_time(self):
        for revision in (True, 0, MAX_REVISION + 1):
            with self.subTest(revision=revision):
                for operation in (self.correct, self.remove):
                    with self.assertRaises(MemoryContractError):
                        operation(self.snapshot, self.record.record_id, expected_revision=revision)
        for changes in (
            {"text": "synthetic\ninvalid"}, {"corrected_at_utc": 89},
            {"corrected_at_utc": 120}, {"corrected_at_utc": True},
        ):
            with self.subTest(changes=changes), self.assertRaises(MemoryContractError):
                self.correct(self.snapshot, self.record.record_id, **changes)
        self.assertEqual(self.snapshot.records, (self.record,))

    def test_retrieval_respects_item_limit(self):
        records = tuple(make_record(i) for i in range(1, MAX_RETRIEVAL_ITEMS + 3))
        snapshot = MemoryStorageSnapshotV1(OWNER, records[::-1])
        batch = self.retrieve(snapshot, "orbit")
        self.assertEqual(tuple(item.record for item in batch.items),
                         records[:MAX_RETRIEVAL_ITEMS])

    def test_retrieval_respects_utf8_byte_limit(self):
        prefix = "orbit amber "
        text = prefix + "\U0001f642" * ((MAX_MEMORY_TEXT_BYTES - len(prefix)) // 4)
        records = tuple(make_record(i, text) for i in range(1, 4))
        snapshot = MemoryStorageSnapshotV1(OWNER, records)
        batch = self.retrieve(snapshot, "orbit amber")
        self.assertEqual(tuple(item.record for item in batch.items), records[:2])
        self.assertEqual(sum(len(item.record.text.encode("utf-8")) for item in batch.items),
                         MAX_RETRIEVAL_BYTES)

    def test_add_respects_snapshot_count_limit(self):
        records = tuple(make_record(i, "x") for i in range(1, MAX_SNAPSHOT_RECORDS + 1))
        almost_full = MemoryStorageSnapshotV1(OWNER, records[:-1])
        full = self.add(almost_full, records[-1])
        self.assertEqual(full.records, records)
        with self.assertRaises(MemoryContractError):
            self.add(full, make_record(MAX_SNAPSHOT_RECORDS + 1))
        self.assertEqual(almost_full.records, records[:-1])
        self.assertEqual(full.records, records)

    def test_add_and_correction_respect_snapshot_utf8_limit(self):
        text = "\U0001f642" * (MAX_MEMORY_TEXT_BYTES // 4)
        count = MAX_SNAPSHOT_TEXT_BYTES // MAX_MEMORY_TEXT_BYTES
        records = tuple(make_record(i, text) for i in range(1, count))
        almost_full = MemoryStorageSnapshotV1(OWNER, records)
        last = make_record(count, text[:-1] + "aaa")
        near_byte_limit = self.add(almost_full, last)
        one_byte = make_record(count + 1, "x")
        full = self.add(near_byte_limit, one_byte)
        with self.assertRaises(MemoryContractError):
            self.add(full, make_record(count + 2, "x"))
        with self.assertRaises(MemoryContractError):
            self.correct(full, one_byte.record_id, text="xx")
        self.assertEqual(near_byte_limit.records, records + (last,))
        self.assertEqual(full.records, records + (last, one_byte))

    def operations(self):
        return (
            partial(self.add, record=make_record(3)),
            partial(self.lookup, record_id=self.record.record_id),
            partial(self.retrieve, query=""),
            partial(self.correct, record_id=self.record.record_id),
            partial(self.remove, record_id=self.record.record_id),
            partial(self.expire, as_of_utc=MAX_UNIX_TIME),
        )
