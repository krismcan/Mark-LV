"""Synthetic tests for prospective memory lifecycle projections."""
from dataclasses import FrozenInstanceError, replace
from functools import partial
import traceback
import unittest

from nayeon.memory.contracts import (
    MAX_REVISION,
    MAX_UNIX_TIME,
    SCHEMA_VERSION,
    DurableMemoryRecordV1,
    MemoryContractError,
    Sensitivity,
    SourceKind,
)
from nayeon.memory.lifecycle import (
    add_memory_record_v1,
    correct_memory_record_v1,
    filter_expired_memory_records_v1,
    remove_memory_record_v1,
)
from nayeon.memory.retrieval import retrieve_memory_v1
from nayeon.memory.storage_snapshot import (
    MAX_SNAPSHOT_RECORDS,
    MAX_SNAPSHOT_TEXT_BYTES,
    MemoryStorageSnapshotV1,
)


OWNER = "a" * 32
FOREIGN_OWNER = "b" * 32
ORIGINAL_TEXT = "synthetic orbit marker"
CORRECTED_TEXT = "synthetic quartz marker"


def make_record(number, **changes):
    return DurableMemoryRecordV1(**({
        "schema_version": SCHEMA_VERSION,
        "record_id": f"{number:032x}",
        "owner_namespace": OWNER,
        "text": ORIGINAL_TEXT,
        "source": SourceKind.EXPLICIT_USER,
        "source_reference": "human-save",
        "sensitivity": Sensitivity.ORDINARY,
        "captured_at_utc": 80,
        "confirmed_at_utc": 90,
        "expires_at_utc": 120,
        "corrected_at_utc": None,
        "revision": 1,
    } | changes))


class PersonalMemoryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.record = make_record(2)
        self.snapshot = MemoryStorageSnapshotV1(OWNER, (self.record,))
        self.add = partial(add_memory_record_v1, self.snapshot, owner_namespace=OWNER)
        self.correct = partial(
            correct_memory_record_v1, self.snapshot, self.record.record_id,
            owner_namespace=OWNER, expected_revision=1, text=CORRECTED_TEXT,
            corrected_at_utc=100,
        )
        self.remove = partial(
            remove_memory_record_v1, self.snapshot, self.record.record_id,
            owner_namespace=OWNER, expected_revision=1,
        )

    def test_add_projects_a_new_sorted_immutable_snapshot(self):
        new_record = make_record(1)
        result = self.add(new_record)
        self.assertIsNot(result, self.snapshot)
        self.assertEqual(result.records, (new_record, self.record))
        self.assertEqual(result.owner_namespace, OWNER)
        self.assertEqual(self.snapshot.records, (self.record,))
        with self.assertRaises(FrozenInstanceError):
            result.records = ()
        with self.assertRaises(FrozenInstanceError):
            result.records[0].text = CORRECTED_TEXT

    def test_correction_changes_only_text_revision_and_correction_time(self):
        neighbor = make_record(1)
        snapshot = self.add(neighbor)
        corrected = correct_memory_record_v1(
            snapshot, self.record.record_id, owner_namespace=OWNER,
            expected_revision=1, text=CORRECTED_TEXT, corrected_at_utc=90,
        )
        first = corrected.records[1]
        self.assertEqual(first, replace(self.record, text=CORRECTED_TEXT,
                                        revision=2, corrected_at_utc=90))
        self.assertIs(corrected.records[0], neighbor)
        second = correct_memory_record_v1(
            corrected, self.record.record_id, owner_namespace=OWNER,
            expected_revision=2, text="synthetic amber marker", corrected_at_utc=90,
        )
        self.assertEqual(second.records[1].revision, 3)
        self.assertEqual(first.revision, 2)
        self.assertEqual(snapshot.records, (neighbor, make_record(2)))
        with self.assertRaises(MemoryContractError):
            correct_memory_record_v1(
                corrected, self.record.record_id, owner_namespace=OWNER,
                expected_revision=1, text=ORIGINAL_TEXT, corrected_at_utc=101,
            )
        self.assertEqual(corrected.records, (neighbor, first))

    def test_remove_projects_the_exact_expected_revision(self):
        corrected = self.correct()
        expired = make_record(1, expires_at_utc=91)
        snapshot = add_memory_record_v1(corrected, expired, owner_namespace=OWNER)
        with self.assertRaises(MemoryContractError):
            remove_memory_record_v1(snapshot, self.record.record_id,
                                    owner_namespace=OWNER, expected_revision=1)
        remaining = remove_memory_record_v1(
            snapshot, expired.record_id, owner_namespace=OWNER, expected_revision=1,
        )
        self.assertEqual(remaining.records, corrected.records)
        empty = remove_memory_record_v1(
            remaining, self.record.record_id, owner_namespace=OWNER, expected_revision=2,
        )
        self.assertEqual(empty.records, ())
        self.assertEqual(empty.owner_namespace, OWNER)
        self.assertEqual(snapshot.records, (expired, corrected.records[0]))

    def test_expiry_is_inclusive_and_retains_future_effective_records(self):
        early = make_record(1, expires_at_utc=100)
        future = make_record(3, confirmed_at_utc=110, expires_at_utc=130)
        snapshot = MemoryStorageSnapshotV1(OWNER, (early, self.record, future))
        for as_of, expected in ((99, snapshot.records), (100, (self.record, future)),
                                (120, (future,)), (MAX_UNIX_TIME, ())):
            with self.subTest(as_of=as_of):
                filtered = filter_expired_memory_records_v1(
                    snapshot, owner_namespace=OWNER, as_of_utc=as_of,
                )
                self.assertIsNot(filtered, snapshot)
                self.assertEqual(filtered.records, expected)
        self.assertEqual(snapshot.records, (early, self.record, future))

    def test_projected_snapshots_work_with_retrieval(self):
        corrected = self.correct()
        before = retrieve_memory_v1("quartz", corrected.records,
                                    owner_namespace=OWNER, as_of_utc=99)
        self.assertEqual(before.items, ())
        filtered = filter_expired_memory_records_v1(corrected, owner_namespace=OWNER,
                                                   as_of_utc=100)
        after = retrieve_memory_v1("quartz", filtered.records,
                                   owner_namespace=OWNER, as_of_utc=100)
        self.assertEqual(after.trust_label, "untrusted_memory_context")
        self.assertIs(after.items[0].record, corrected.records[0])
        original = retrieve_memory_v1("orbit", self.snapshot.records,
                                      owner_namespace=OWNER, as_of_utc=100)
        self.assertIs(original.items[0].record, self.record)

    def test_add_refuses_duplicate_foreign_or_invalid_initial_records(self):
        class RecordSubclass(DurableMemoryRecordV1):
            __slots__ = ()

        malformed = make_record(1)
        object.__setattr__(malformed, "confirmed_at_utc", 79)
        for candidate in (
            replace(self.record, text=CORRECTED_TEXT),
            make_record(1, owner_namespace=FOREIGN_OWNER),
            make_record(1, revision=2, corrected_at_utc=100),
            malformed, object.__new__(DurableMemoryRecordV1), object.__new__(RecordSubclass),
        ):
            with self.assertRaises(MemoryContractError):
                self.add(candidate)
            self.assertEqual(self.snapshot.records, (make_record(2),))

    def test_refuses_missing_ids_stale_revisions_and_nonexact_selectors(self):
        class IntSubclass(int):
            pass

        class StrSubclass(str):
            pass

        for operation, extra in (
            (correct_memory_record_v1, {"text": CORRECTED_TEXT, "corrected_at_utc": 100}),
            (remove_memory_record_v1, {}),
        ):
            for record_id, revision in (
                (make_record(1).record_id, 1), (StrSubclass(self.record.record_id), 1),
                ("0" * 32, 1), (self.record.record_id, 2),
                (self.record.record_id, True), (self.record.record_id, IntSubclass(1)),
                (self.record.record_id, 0), (self.record.record_id, MAX_REVISION + 1),
            ):
                with self.assertRaises(MemoryContractError):
                    operation(self.snapshot, record_id, owner_namespace=OWNER,
                              expected_revision=revision, **extra)
                self.assertEqual(self.snapshot.records, (make_record(2),))

    def test_refuses_invalid_times_text_and_revision_overflow(self):
        for timestamp in (True, 100.0, -1, MAX_UNIX_TIME + 1):
            with self.assertRaises(MemoryContractError):
                self.correct(corrected_at_utc=timestamp)
            with self.assertRaises(MemoryContractError):
                filter_expired_memory_records_v1(self.snapshot, owner_namespace=OWNER,
                                                as_of_utc=timestamp)
        for timestamp in (89, 120, 121):
            with self.assertRaises(MemoryContractError):
                self.correct(corrected_at_utc=timestamp)
        for text in (b"synthetic bytes", "\n", "\ud800", "a" * 1025):
            with self.assertRaises(MemoryContractError):
                self.correct(text=text)
        self.assertEqual(self.snapshot.records, (make_record(2),))

        for revision, timestamp in ((2, 99), (MAX_REVISION, 100)):
            record = make_record(2, revision=revision, corrected_at_utc=100)
            snapshot = MemoryStorageSnapshotV1(OWNER, (record,))
            with self.assertRaises(MemoryContractError):
                correct_memory_record_v1(
                    snapshot, record.record_id, owner_namespace=OWNER,
                    expected_revision=revision, text=CORRECTED_TEXT, corrected_at_utc=timestamp,
                )
            self.assertEqual(snapshot.records,
                             (make_record(2, revision=revision, corrected_at_utc=100),))

    def test_refuses_count_and_utf8_budget_overflow_without_mutation(self):
        small = tuple(make_record(i, text="x") for i in range(1, MAX_SNAPSHOT_RECORDS + 1))
        full = MemoryStorageSnapshotV1(OWNER, small)
        with self.assertRaises(MemoryContractError):
            add_memory_record_v1(full, make_record(MAX_SNAPSHOT_RECORDS + 1), owner_namespace=OWNER)
        self.assertEqual(full.records, small)

        text = "\U0001f642" * 512
        large = tuple(make_record(i, text=text)
                      for i in range(1, MAX_SNAPSHOT_TEXT_BYTES // 2048))
        last = make_record(len(large) + 1, text=text[:-1] + "aaa")
        near_limit = MemoryStorageSnapshotV1(OWNER, large + (last,))
        new_record = make_record(len(large) + 2, text="x")
        at_limit = add_memory_record_v1(near_limit, new_record, owner_namespace=OWNER)
        with self.assertRaises(MemoryContractError):
            add_memory_record_v1(at_limit, make_record(len(large) + 3, text="x"),
                                 owner_namespace=OWNER)
        with self.assertRaises(MemoryContractError):
            correct_memory_record_v1(at_limit, new_record.record_id, owner_namespace=OWNER,
                                     expected_revision=1, text="xx", corrected_at_utc=100)
        self.assertEqual(near_limit.records, large + (last,))
        self.assertEqual(at_limit.records, large + (last, new_record))

    def test_all_operations_revalidate_snapshot_and_owner(self):
        class SnapshotSubclass(MemoryStorageSnapshotV1):
            __slots__ = ()

        class StrSubclass(str):
            pass

        def forged(records):
            snapshot = MemoryStorageSnapshotV1(OWNER)
            object.__setattr__(snapshot, "records", records)
            return snapshot

        malformed = make_record(1)
        object.__setattr__(malformed, "text", "\ud800")
        cases = (
            (self.snapshot, FOREIGN_OWNER), (self.snapshot, StrSubclass(OWNER)),
            (SnapshotSubclass(OWNER), OWNER), (object.__new__(MemoryStorageSnapshotV1), OWNER),
            (forged((self.record, self.record)), OWNER),
            (forged((self.record, make_record(1))), OWNER),
            (forged((make_record(1, owner_namespace=FOREIGN_OWNER),)), OWNER),
            (forged((malformed,)), OWNER), (forged([self.record]), OWNER),
        )
        operations = (
            partial(add_memory_record_v1, record=make_record(3)),
            partial(correct_memory_record_v1, record_id=self.record.record_id,
                    expected_revision=1, text=CORRECTED_TEXT, corrected_at_utc=100),
            partial(remove_memory_record_v1, record_id=self.record.record_id,
                    expected_revision=1),
            partial(filter_expired_memory_records_v1, as_of_utc=MAX_UNIX_TIME),
        )
        for snapshot, owner in cases:
            original_records = getattr(snapshot, "records", None)
            for operation in operations:
                with self.assertRaises(MemoryContractError):
                    operation(snapshot, owner_namespace=owner)
                self.assertIs(getattr(snapshot, "records", None), original_records)

    def test_failure_messages_omit_synthetic_content_and_ids(self):
        invalid_text = "synthetic-invalid-marker\ud800"
        for operation in (partial(self.correct, text=invalid_text),
                          partial(self.add, replace(self.record, text=CORRECTED_TEXT)),
                          partial(self.remove, expected_revision=2)):
            with self.assertRaises(MemoryContractError) as caught:
                operation()
            error = caught.exception
            self.assertIsNone(error.__context__)
            rendered = "".join(traceback.format_exception(error))
            for value in (ORIGINAL_TEXT, CORRECTED_TEXT, "synthetic-invalid-marker",
                          OWNER, self.record.record_id):
                self.assertNotIn(value, rendered)
