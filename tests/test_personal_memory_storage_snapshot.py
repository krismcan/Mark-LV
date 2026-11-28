"""Synthetic tests for the offline memory storage snapshot."""
from dataclasses import FrozenInstanceError, replace
import traceback
import unittest

from nayeon.memory.contracts import (
    SCHEMA_VERSION,
    DurableMemoryRecordV1,
    MemoryContractError,
    Sensitivity,
    SourceKind,
    memory_record_to_json_v1,
)
from nayeon.memory.retrieval import retrieve_memory_v1
from nayeon.memory.storage_snapshot import MemoryStorageSnapshotV1


OWNER = "a" * 32
FOREIGN_OWNER = "b" * 32
SYNTHETIC_TEXT = "synthetic orbit marker"


def make_record(number, *, record_type=DurableMemoryRecordV1, **changes):
    fields = {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"{number:032x}",
        "owner_namespace": OWNER,
        "text": SYNTHETIC_TEXT,
        "source": SourceKind.EXPLICIT_USER,
        "source_reference": "human-save",
        "sensitivity": Sensitivity.ORDINARY,
        "captured_at_utc": 80,
        "confirmed_at_utc": 90,
        "expires_at_utc": 120,
        "corrected_at_utc": None,
        "revision": 1,
    }
    return record_type(**(fields | changes))


class PersonalMemoryStorageSnapshotTests(unittest.TestCase):
    def test_empty_snapshot_and_missing_lookup(self):
        empty = MemoryStorageSnapshotV1(OWNER)
        self.assertEqual(empty.owner_namespace, OWNER)
        self.assertEqual(empty.records, ())
        self.assertIsNone(empty.get_record(f"{1:032x}"))

    def test_orders_by_id_and_preserves_canonical_records(self):
        expected = (make_record(2, revision=7, corrected_at_utc=105),
                    make_record(16), make_record(255, expires_at_utc=99))
        original_bytes = tuple(map(memory_record_to_json_v1, expected))
        for order in (expected, expected[::-1], expected[1:] + expected[:1]):
            snapshot = MemoryStorageSnapshotV1(OWNER, order)
            self.assertEqual(snapshot.records, expected)
            self.assertEqual(tuple(map(memory_record_to_json_v1, snapshot.records)),
                             original_bytes)
            for listed, original in zip(snapshot.records, expected):
                self.assertIs(listed, original)
                self.assertIs(snapshot.get_record(original.record_id), original)
            self.assertIsNone(snapshot.get_record(f"{3:032x}"))

    def test_input_and_snapshot_are_immutable(self):
        first, second = make_record(1), make_record(2)
        supplied = (second, first)
        snapshot = MemoryStorageSnapshotV1(OWNER, supplied)
        self.assertEqual(supplied, (second, first))
        self.assertIs(type(snapshot.records), tuple)
        with self.assertRaises(FrozenInstanceError):
            snapshot.owner_namespace = FOREIGN_OWNER
        with self.assertRaises(FrozenInstanceError):
            snapshot.records = ()
        with self.assertRaises(FrozenInstanceError):
            snapshot.records[0].text = "changed"

    def test_enforces_record_count_independently_of_text_bytes(self):
        records = tuple(make_record(i, text="x") for i in range(1, 258))
        self.assertEqual(len(MemoryStorageSnapshotV1(OWNER, records[:256]).records), 256)
        with self.assertRaises(MemoryContractError):
            MemoryStorageSnapshotV1(OWNER, records)

    def test_aggregate_utf8_limit_includes_exact_boundary(self):
        text = "\U0001f642" * 256  # 1,024 UTF-8 bytes per record.
        records = tuple(make_record(i, text=text) for i in range(1, 257))
        snapshot = MemoryStorageSnapshotV1(OWNER, records)
        self.assertEqual(sum(len(record.text.encode("utf-8")) for record in snapshot.records),
                         256 * 1024)
        one_byte_over = records[:-1] + (replace(records[-1], text=text + "x"),)
        with self.assertRaises(MemoryContractError):
            MemoryStorageSnapshotV1(OWNER, one_byte_over)

    def test_rejects_duplicate_records_and_conflicting_ids(self):
        original = make_record(1)
        for conflict in (original, replace(original), replace(original, text="amber"),
                         replace(original, revision=2, corrected_at_utc=100)):
            with self.assertRaises(MemoryContractError):
                MemoryStorageSnapshotV1(OWNER, (original, conflict))

    def test_rejects_foreign_owner_even_for_expired_record(self):
        local = make_record(1)
        foreign = make_record(2, owner_namespace=FOREIGN_OWNER, expires_at_utc=91)
        with self.assertRaises(MemoryContractError):
            MemoryStorageSnapshotV1(OWNER, (local, foreign))

    def test_requires_exact_input_types_and_valid_identifiers(self):
        class StringSubclass(str):
            pass

        class TupleSubclass(tuple):
            pass

        class RecordSubclass(DurableMemoryRecordV1):
            __slots__ = ()

        record = make_record(1)
        for records in ([record], iter((record,)), TupleSubclass((record,)), None,
                        (object(),), (make_record(2, record_type=RecordSubclass),)):
            with self.assertRaises(MemoryContractError):
                MemoryStorageSnapshotV1(OWNER, records)
        snapshot = MemoryStorageSnapshotV1(OWNER, (record,))
        for identifier in (StringSubclass(OWNER), "0" * 32, "A" * 32, "a" * 31, True):
            with self.assertRaises(MemoryContractError):
                MemoryStorageSnapshotV1(identifier)
            with self.assertRaises(MemoryContractError):
                snapshot.get_record(identifier)

    def test_revalidates_exact_record_instances_with_invalid_or_missing_slots(self):
        missing = object.__new__(DurableMemoryRecordV1)
        object.__setattr__(missing, "schema_version", SCHEMA_VERSION)
        for field, value in (("revision", True), ("expires_at_utc", 90),
                             ("text", SYNTHETIC_TEXT + "\ud800")):
            with self.subTest(field=field):
                invalid = make_record(1)
                object.__setattr__(invalid, field, value)
                with self.assertRaises(MemoryContractError):
                    MemoryStorageSnapshotV1(OWNER, (invalid,))
        with self.assertRaises(MemoryContractError) as failure:
            MemoryStorageSnapshotV1(OWNER, (missing,))
        self.assertIsNone(failure.exception.__context__)

    def test_representations_do_not_echo_record_content_or_identifiers(self):
        record = make_record(1)
        snapshot = MemoryStorageSnapshotV1(OWNER, (record,))
        with self.assertRaises(MemoryContractError) as failure:
            MemoryStorageSnapshotV1(OWNER, (record, replace(record, text="conflicting amber")))
        error = failure.exception
        self.assertIsNone(error.__context__)
        self.assertIsNone(error.__cause__)
        for representation in (repr(snapshot), str(error), repr(error),
                               "".join(traceback.format_exception(error))):
            for value in (SYNTHETIC_TEXT, "conflicting amber", OWNER, record.record_id):
                self.assertNotIn(value, representation)

    def test_listing_can_be_passed_to_existing_retrieval(self):
        corrected = make_record(2, corrected_at_utc=100, revision=2)
        expired = make_record(1, expires_at_utc=99)
        current = make_record(3)
        snapshot = MemoryStorageSnapshotV1(OWNER, (current, corrected, expired))
        before = retrieve_memory_v1("orbit", snapshot.records,
                                    owner_namespace=snapshot.owner_namespace, as_of_utc=99)
        after = retrieve_memory_v1("orbit", snapshot.records,
                                   owner_namespace=snapshot.owner_namespace, as_of_utc=100)
        self.assertEqual(tuple(item.record for item in before.items), (current,))
        self.assertEqual(tuple(item.record for item in after.items), (corrected, current))
        self.assertIs(after.items[0].record, corrected)
        self.assertEqual(after.trust_label, "untrusted_memory_context")
        self.assertIs(snapshot.get_record(expired.record_id), expired)
