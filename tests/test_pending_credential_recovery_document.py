"""C1 pending-custody EVIDENCE codec: no I/O, WinCred or authority."""
import ast
import inspect
import json
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from nayeon.brain import pending_credential_recovery_document as m


EPOCH_A = "a" * 32
EPOCH_B = "b" * 32
DIGEST = "c" * 64


def rec(seq=1, state=m.PendingRecordedState.UNINITIALIZED, *,
        previous=None, epoch=EPOCH_A, generation=0):
    options = dict(schema_version=1, sequence=seq, epoch=epoch,
                   generation=generation, state=state,
                   previous_hash=m._GENESIS if previous is None else previous)
    if state is m.PendingRecordedState.IN_FLIGHT:
        options.update(operation_id="d" * 32, operation_kind="pending_save",
                       evidence_hash=DIGEST)
    return m.PendingEvidenceRecord(**options)


class PendingRecoveryDocumentTests(unittest.TestCase):
    def assert_invalid(self, frame):
        with self.assertRaises(m.PendingEvidenceError):
            m.decode_frame(frame)

    def test_roundtrip_one_frame_and_two_linked_records(self):
        first = rec()
        second = rec(2, m.PendingRecordedState.IN_FLIGHT,
                     previous=m.record_hash(first))
        a, b = m.encode_frame(first), m.encode_frame(second)
        self.assertTrue(a.startswith(b"NPC1 "))
        self.assertTrue(a.endswith(b"\n"))
        self.assertEqual(m.decode_frame(a), first)
        self.assertEqual(m.decode_journal(a + b), (first, second))
        self.assertNotEqual(m.record_hash(first), m.record_hash(second))

    def test_output_is_immutable_untrusted_claims_without_ready_state(self):
        record = rec()
        self.assertFalse(hasattr(record, "__dict__"))
        self.assertNotIn("authorization", repr(record).lower())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            record.generation = 5
        self.assertFalse(any("READY" in name or "VALID" in name or
                             "APPROVED" in name
                             for name in m.PendingRecordedState.__members__))
        self.assertFalse(any(hasattr(m, name) for name in
                             ("grant", "approve", "authorize", "is_ready", "execute")))

    def test_bad_types_bounds_and_nullable_fields(self):
        for key, bad in (
            ("schema_version", True), ("schema_version", 2),
            ("sequence", 0), ("sequence", 129), ("sequence", False),
            ("epoch", "A" * 32), ("generation", -1),
            ("generation", 2**63), ("generation", True),
            ("previous_hash", "f" * 63), ("state", "in_flight"),
        ):
            args = dict(schema_version=1, sequence=1, epoch=EPOCH_A,
                        generation=0, state=m.PendingRecordedState.UNINITIALIZED,
                        previous_hash=m._GENESIS)
            args[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(m.PendingEvidenceError):
                m.PendingEvidenceRecord(**args)
        for params in (
            dict(operation_id="d" * 32),
            dict(operation_kind="pending_save"),
            dict(evidence_hash=DIGEST),
        ):
            with self.assertRaises(m.PendingEvidenceError):
                m.PendingEvidenceRecord(
                    1, 1, EPOCH_A, 0, m.PendingRecordedState.BLOCKED,
                    m._GENESIS, **params)
        for params in (
            dict(operation_id=None),
            dict(operation_kind="connect"),
            dict(evidence_hash="G" * 64),
        ):
            valid = dict(operation_id="d" * 32,
                         operation_kind="pending_save", evidence_hash=DIGEST)
            valid.update(params)
            with self.assertRaises(m.PendingEvidenceError):
                m.PendingEvidenceRecord(1, 1, EPOCH_A, 0,
                                        m.PendingRecordedState.IN_FLIGHT,
                                        m._GENESIS, **valid)

    def test_active_journal_and_cross_domain_rejected(self):
        self.assert_invalid(b"NRJ1 0001 " + b"0" * 64 + b" {}\n")
        original = m.encode_frame(rec())
        body = original.split(b" ", 3)[3][:-1]
        swapped = body.replace(b"nayeon-v1-pending-custody",
                               b"nayeon-v1-active-custody")
        self.assert_invalid(b"NPC1 " + f"{len(swapped):04x}".encode() +
                            b" " + b"0" * 64 + b" " + swapped + b"\n")

    def test_corrupt_framing_and_checksums_fail_closed(self):
        frame = m.encode_frame(rec())
        for bad in (
            frame[:-1], frame + b"junk", frame + b"\n",
            b"NPC0" + frame[4:], b"npc1" + frame[4:],
            frame[:5] + b"ffff" + frame[9:],
            frame[:10] + b"0" * 64 + frame[74:],
            frame.replace(b"NPC1 ", b"NRJ1 "),
            frame.replace(b"a" * 32, b"z" * 32),
        ):
            with self.subTest(candidate=bad[:25]):
                self.assert_invalid(bad)

    def test_canonical_json_encoding_only(self):
        frame = m.encode_frame(rec())
        body = frame.split(b" ", 3)[3][:-1]
        obj = json.loads(body)
        alternative = json.dumps(obj, sort_keys=False, separators=(", ", ": ")).encode()
        mutated = b"NPC1 " + f"{len(alternative):04x}".encode() + b" " + (
            m.hashlib.sha256(m._PREFIX + alternative).hexdigest().encode()
        ) + b" " + alternative + b"\n"
        self.assert_invalid(mutated)

    def test_nested_duplicate_keys_even_with_untrusted_extra_field(self):
        frame = m.encode_frame(rec())
        body = frame.split(b" ", 3)[3][:-1]
        modified = body[:-1] + b',"extra":{"x":1,"x":2}}'
        digest = m.hashlib.sha256(m._PREFIX + modified).hexdigest().encode()
        malformed = (b"NPC1 " + f"{len(modified):04x}".encode() +
                     b" " + digest + b" " + modified + b"\n")
        self.assert_invalid(malformed)

    def test_invalid_json_encoding_and_deep_nesting_fail_safely(self):
        frame = m.encode_frame(rec())
        for body in (b"\xff", b"NaN", b"[" * 900 + b"]" * 900):
            digest = m.hashlib.sha256(m._PREFIX + body).hexdigest().encode()
            candidate = (b"NPC1 " + f"{len(body):04x}".encode() +
                         b" " + digest + b" " + body + b"\n")
            self.assert_invalid(candidate)

    def test_journal_sequence_predecessor_and_epoch_rules(self):
        first = rec()
        valid = rec(2, m.PendingRecordedState.BLOCKED,
                    previous=m.record_hash(first), epoch=EPOCH_B, generation=1)
        self.assertEqual(len(m.decode_journal(m.encode_frame(first) +
                                              m.encode_frame(valid))), 2)
        bads = (
            rec(3, previous=m.record_hash(first)),
            rec(2, previous="f" * 64),
            rec(2, previous=m.record_hash(first), epoch=EPOCH_B, generation=0),
            rec(2, previous=m.record_hash(first), epoch=EPOCH_A, generation=1),
            rec(2, previous=m.record_hash(first), epoch=EPOCH_B, generation=2),
        )
        for bad in bads:
            with self.subTest(second=bad):
                with self.assertRaises(m.PendingEvidenceError):
                    m.decode_journal(m.encode_frame(first) + m.encode_frame(bad))

    def test_bounds_bad_type_and_truncated_journal(self):
        frame = m.encode_frame(rec())
        for data in (None, "", b"", bytearray(frame),
                     frame + b"x" * (m._MAX_JOURNAL_BYTES + 1)):
            with self.assertRaises(m.PendingEvidenceError):
                m.decode_journal(data)
        with self.assertRaises(m.PendingEvidenceError):
            m.decode_journal(frame * 129)
        with self.assertRaises(m.PendingEvidenceError):
            m.decode_journal(frame[:-1])

    def test_fully_recomputed_forgery_is_structurally_valid_not_authenticated(self):
        first = rec()
        forged = m.PendingEvidenceRecord(
            1, 1, "f" * 32, 0, m.PendingRecordedState.BLOCKED, m._GENESIS)
        self.assertEqual(m.decode_journal(m.encode_frame(forged)), (forged,))
        self.assertNotEqual(m.record_hash(first), m.record_hash(forged))
        # This is NOT security clearance: an attacker can replace complete history.

    def test_valid_prefix_truncation_is_accepted_as_untrusted_history(self):
        first = rec()
        second = rec(2, m.PendingRecordedState.IN_FLIGHT,
                     previous=m.record_hash(first))
        full = m.encode_frame(first) + m.encode_frame(second)
        prefix = m.encode_frame(first)
        self.assertEqual(m.decode_journal(full), (first, second))
        self.assertEqual(m.decode_journal(prefix), (first,))
        # Only a future separately reviewed controller may address rollback.

    def test_source_imports_and_no_effectful_api(self):
        source = Path(inspect.getfile(m)).read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertEqual({n.module for n in ast.walk(tree)
                          if isinstance(n, ast.ImportFrom)},
                         {"dataclasses", "enum"})
        self.assertEqual({alias.name for n in ast.walk(tree)
                          if isinstance(n, ast.Import)
                          for alias in n.names}, {"hashlib", "json", "re"})
        for symbol in ("OPENAI_API_KEY", "WindowsCredentialBackend", "SecretValue",
                       "SecretBackend", "openai.api_key", "WinDLL", "socket"):
            self.assertNotIn(symbol, source)


if __name__ == "__main__":
    unittest.main()
