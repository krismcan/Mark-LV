"""Synthetic tests for the pure memory snapshot JSON codec."""
from dataclasses import replace
import traceback
import unittest
from unittest.mock import patch

from nayeon.memory import offline_composition, snapshot_codec
from nayeon.memory.contracts import (
    MAX_RECORD_JSON_BYTES,
    SCHEMA_VERSION,
    DurableMemoryRecordV1,
    MemoryContractError,
    Sensitivity,
    SourceKind,
    memory_record_to_json_v1,
)
from nayeon.memory.snapshot_codec import (
    MAX_SNAPSHOT_JSON_BYTES,
    memory_snapshot_to_json_v1,
    parse_memory_snapshot_json_v1,
)
from nayeon.memory.storage_snapshot import (
    MAX_SNAPSHOT_RECORDS,
    MAX_SNAPSHOT_TEXT_BYTES,
    MemoryStorageSnapshotV1,
)


OWNER = "a" * 32
FOREIGN_OWNER = "b" * 32
OWNER_BYTES = OWNER.encode("ascii")
TEXT = "synthetic orbit marker"


def make_record(number, text=TEXT, **changes):
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


def envelope(*record_json, owner=OWNER_BYTES):
    return (
        b'{"schema_version":1,"owner_namespace":"' + owner
        + b'","records":[' + b','.join(record_json) + b']}'
    )


class PersonalMemorySnapshotCodecTests(unittest.TestCase):
    def encode(self, snapshot, owner=OWNER):
        return memory_snapshot_to_json_v1(snapshot, owner_namespace=owner)

    def decode(self, blob, owner=OWNER):
        return parse_memory_snapshot_json_v1(blob, owner_namespace=owner)

    def assert_rejected(self, cases):
        for name, blob in cases.items():
            with self.subTest(case=name), self.assertRaises(MemoryContractError):
                self.decode(blob)

    def test_empty_snapshot_has_explicit_owner_version_and_inventory(self):
        blob = self.encode(MemoryStorageSnapshotV1(OWNER))
        self.assertEqual(blob, envelope())
        snapshot = self.decode(blob)
        self.assertIs(type(snapshot), MemoryStorageSnapshotV1)
        self.assertEqual((snapshot.owner_namespace, snapshot.records), (OWNER, ()))

    def test_roundtrip_is_canonical_for_every_input_order(self):
        first = make_record(1, 'synthetic caf\u00e9 {[]}, "quote" \\ marker')
        second = make_record(2, expires_at_utc=99)
        canonical = envelope(memory_record_to_json_v1(first), memory_record_to_json_v1(second))
        for records in ((first, second), (second, first)):
            snapshot = MemoryStorageSnapshotV1(OWNER, records)
            blob = self.encode(snapshot)
            self.assertEqual(blob, canonical)
            self.assertIn(b"caf\xc3\xa9", blob)
            self.assertEqual(self.decode(blob).records, (first, second))
            self.assertEqual(self.encode(self.decode(blob)), blob)

    def test_requires_exact_blob_snapshot_and_owner_types(self):
        class BytesSubclass(bytes):
            pass

        class StringSubclass(str):
            pass

        class SnapshotSubclass(MemoryStorageSnapshotV1):
            __slots__ = ()

        blob = envelope()
        self.assert_rejected({
            "bytes subclass": BytesSubclass(blob),
            "bytearray": bytearray(blob),
            "memoryview": memoryview(blob),
            "text": blob.decode("ascii"),
            "none": None,
        })
        snapshot = MemoryStorageSnapshotV1(OWNER)
        for owner in (StringSubclass(OWNER), OWNER_BYTES, True, "0" * 32, "A" * 32):
            with self.assertRaises(MemoryContractError):
                self.decode(blob, owner)
            with self.assertRaises(MemoryContractError):
                self.encode(snapshot, owner)
        for candidate in (None, SnapshotSubclass(OWNER),
                          object.__new__(MemoryStorageSnapshotV1)):
            with self.assertRaises(MemoryContractError):
                self.encode(candidate)

    def test_encode_revalidates_forged_snapshot_instances(self):
        first, second = make_record(1), make_record(2)
        invalid = make_record(3)
        object.__setattr__(invalid, "revision", True)
        for records in ([first], (first, first), (second, first), (invalid,),
                        (object.__new__(DurableMemoryRecordV1),)):
            snapshot = MemoryStorageSnapshotV1(OWNER)
            object.__setattr__(snapshot, "records", records)
            with self.assertRaises(MemoryContractError):
                self.encode(snapshot)
            self.assertIs(snapshot.records, records)

    def test_owner_isolation_checks_envelope_and_every_record(self):
        local = make_record(1)
        foreign = make_record(2, owner_namespace=FOREIGN_OWNER, expires_at_utc=91)
        for records in ((), (local,)):
            snapshot = MemoryStorageSnapshotV1(OWNER, records)
            with self.assertRaises(MemoryContractError):
                self.encode(snapshot, FOREIGN_OWNER)
            with patch.object(snapshot_codec, "parse_memory_record_json_v1") as parser:
                with self.assertRaises(MemoryContractError):
                    self.decode(self.encode(snapshot), FOREIGN_OWNER)
                parser.assert_not_called()
        self.assert_rejected({
            "foreign header": envelope(owner=FOREIGN_OWNER.encode("ascii")),
            "foreign record": envelope(memory_record_to_json_v1(local),
                                       memory_record_to_json_v1(foreign)),
        })

    def test_rejects_invalid_envelope_fields_types_and_versions(self):
        blob = envelope()
        self.assert_rejected({
            "root list": b"[]",
            "unknown": blob.replace(b'"records":', b'"extra":0,"records":'),
            "duplicate version": blob.replace(b'"records":', b'"schema_version":1,"records":'),
            "duplicate owner": blob.replace(
                b'"records":', b'"owner_namespace":"' + OWNER_BYTES + b'","records":',
            ),
            "duplicate inventory": blob.replace(b'"records":', b'"records":[],"records":'),
            "missing inventory": blob.replace(b',"records":[]', b''),
            "missing version": blob.replace(b'"schema_version":1,', b''),
            "missing owner": blob.replace(b'"owner_namespace":"' + OWNER_BYTES + b'",', b''),
            "unsupported version": blob.replace(b':1,', b':2,'),
            "boolean version": blob.replace(b':1,', b':true,'),
            "float version": blob.replace(b':1,', b':1.0,'),
            "string version": blob.replace(b':1,', b':"1",'),
            "null owner": blob.replace(b'"' + OWNER_BYTES + b'"', b'null'),
            "object inventory": blob.replace(b'[]', b'{}'),
            "string record": envelope(b'"synthetic"'),
        })

    def test_rejects_malformed_noncanonical_and_trailing_data(self):
        record = memory_record_to_json_v1(make_record(1))
        self.assert_rejected({
            "empty": b"",
            "truncated": envelope(record)[:-1],
            "trailing object": envelope() + b"{}",
            "trailing whitespace": envelope() + b"\n",
            "leading whitespace": b" " + envelope(),
            "BOM": b"\xef\xbb\xbf" + envelope(),
            "trailing record comma": envelope(record, b""),
            "missing record comma": envelope(record + record),
            "invalid UTF-8": envelope(record.replace(TEXT.encode("ascii"), b"\xff")),
            "unpaired surrogate": envelope(record.replace(TEXT.encode("ascii"), b"\\ud800")),
            "unterminated string": envelope(b'{"text":"synthetic}'),
            "envelope whitespace": envelope().replace(b":1", b": 1"),
            "record whitespace": envelope(record.replace(b":1", b": 1")),
            "noncanonical Unicode escape": envelope(record.replace(b"orbit", b"\\u006frbit")),
        })

    def test_uses_strict_record_contract_for_fields_and_values(self):
        record = memory_record_to_json_v1(make_record(1))
        self.assert_rejected({
            "duplicate field": envelope(record[:-1] + b',"revision":1}'),
            "unknown field": envelope(record[:-1] + b',"extra":0}'),
            "missing field": envelope(record.replace(b',"revision":1', b'')),
            "bool revision": envelope(record.replace(b'"revision":1', b'"revision":true')),
            "NaN revision": envelope(record.replace(b'"revision":1', b'"revision":NaN')),
            "null source": envelope(record.replace(b'"explicit_user"', b'null')),
            "unsupported record version": envelope(record.replace(b'"schema_version":1',
                                                                   b'"schema_version":2')),
            "correction missing timestamp": envelope(record.replace(
                b'"revision":1', b'"revision":2',
            )),
        })

    def test_rejects_duplicate_ids_and_noncanonical_record_order(self):
        first = make_record(1)
        first_json = memory_record_to_json_v1(first)
        second_json = memory_record_to_json_v1(make_record(2))
        conflict_json = memory_record_to_json_v1(replace(first, text="synthetic amber"))
        self.assert_rejected({
            "repeated record": envelope(first_json, first_json),
            "conflicting ID": envelope(first_json, conflict_json),
            "out of order": envelope(second_json, first_json),
        })

    def test_preflight_rejects_payload_record_and_depth_limits_before_parsing(self):
        record = memory_record_to_json_v1(make_record(1))
        oversized_payload = envelope(record[:-1] + b" " * MAX_SNAPSHOT_JSON_BYTES + b"}")
        with patch.object(snapshot_codec, "_record_end") as scanner:
            with self.assertRaises(MemoryContractError):
                self.decode(oversized_payload)
            scanner.assert_not_called()

        padded = record[:-1] + b" " * (MAX_RECORD_JSON_BYTES - len(record))
        oversized_record = padded + b" }"
        nested_array = b'{"text":' + b"[" * 1000 + b"0" + b"]" * 1000 + b"}"
        with patch.object(snapshot_codec, "parse_memory_record_json_v1") as parser:
            self.assert_rejected({
                "oversized later record": envelope(record, oversized_record),
                "deep later record": envelope(record, nested_array),
                "nested object": envelope(record, b'{"text":{}}'),
            })
            parser.assert_not_called()

        # At the raw size boundary, the record parser accepts the padding as
        # JSON whitespace and the snapshot codec rejects the noncanonical bytes.
        parse_record = snapshot_codec.parse_memory_record_json_v1
        with patch.object(snapshot_codec, "parse_memory_record_json_v1",
                          wraps=parse_record) as parser:
            with self.assertRaises(MemoryContractError):
                self.decode(envelope(padded + b"}"))
            parser.assert_called_once_with(padded + b"}")

    def test_record_count_boundary_and_early_rejection(self):
        records = tuple(make_record(i, "x") for i in range(1, MAX_SNAPSHOT_RECORDS + 2))
        snapshot = MemoryStorageSnapshotV1(OWNER, records[:-1])
        self.assertEqual(self.decode(self.encode(snapshot)).records, records[:-1])
        oversized = envelope(*map(memory_record_to_json_v1, records))
        with patch.object(snapshot_codec, "parse_memory_record_json_v1") as parser:
            with self.assertRaises(MemoryContractError):
                self.decode(oversized)
            parser.assert_not_called()

    def test_aggregate_utf8_budget_accepts_boundary_and_rejects_one_extra_byte(self):
        text = "\U0001f642" * 256
        count = MAX_SNAPSHOT_TEXT_BYTES // len(text.encode("utf-8"))
        records = tuple(make_record(i, text) for i in range(1, count + 1))
        full = MemoryStorageSnapshotV1(OWNER, records)
        self.assertEqual(self.decode(self.encode(full)).records, records)
        over = records[:-1] + (replace(records[-1], text=text + "x"),)
        with self.assertRaises(MemoryContractError):
            self.decode(envelope(*map(memory_record_to_json_v1, over)))

    def test_rejected_values_are_absent_from_error_and_exception_chain(self):
        record = make_record(1)
        identifier = record.record_id.encode("ascii")
        encoded = memory_record_to_json_v1(record)
        for blob in (
            envelope(encoded, encoded),
            envelope(encoded.replace(b'"explicit_user"', b'"synthetic rejected source"')),
            envelope(encoded.replace(b'"revision":1', b'"revision":')),
            envelope(encoded.replace(TEXT.encode("ascii"), b"\xff")),
            envelope(encoded, owner=FOREIGN_OWNER.encode("ascii")),
        ):
            with self.assertRaises(MemoryContractError) as failure:
                self.decode(blob)
            error = failure.exception
            self.assertIsNone(error.__context__)
            self.assertIsNone(error.__cause__)
            self.assertTrue(error.__suppress_context__)
            for rendered in (str(error), repr(error), "".join(traceback.format_exception(error))):
                for value in (TEXT, OWNER, FOREIGN_OWNER, identifier.decode("ascii"),
                              "synthetic rejected source"):
                    self.assertNotIn(value, rendered)

    def test_corrected_snapshot_roundtrips_through_existing_composition(self):
        record = make_record(1)
        initial = offline_composition.add_memory_record_v1(
            MemoryStorageSnapshotV1(OWNER), record, owner_namespace=OWNER,
        )
        corrected = offline_composition.correct_memory_record_v1(
            initial, record.record_id, owner_namespace=OWNER, expected_revision=1,
            text="synthetic quartz marker", corrected_at_utc=100,
        )
        decoded = self.decode(self.encode(corrected))
        current = offline_composition.get_memory_record_v1(
            decoded, record.record_id, owner_namespace=OWNER,
        )
        self.assertEqual(current, replace(
            record, text="synthetic quartz marker", corrected_at_utc=100, revision=2,
        ))
        for as_of, expected in ((99, ()), (100, (current,)), (120, ())):
            batch = offline_composition.retrieve_memory_from_snapshot_v1(
                decoded, "quartz", owner_namespace=OWNER, as_of_utc=as_of,
            )
            self.assertEqual(tuple(item.record for item in batch.items), expected)
            self.assertEqual(batch.trust_label, "untrusted_memory_context")
        with self.assertRaises(MemoryContractError):
            offline_composition.remove_memory_record_v1(
                decoded, record.record_id, owner_namespace=OWNER, expected_revision=1,
            )
        removed = offline_composition.remove_memory_record_v1(
            decoded, record.record_id, owner_namespace=OWNER, expected_revision=2,
        )
        self.assertEqual(removed.records, ())
