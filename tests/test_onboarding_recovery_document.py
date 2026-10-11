"""Fake-only tests for non-authoritative onboarding recovery evidence."""
import hashlib
import json
import unittest

from nayeon.brain.onboarding_recovery_document import (
    GENESIS_HASH, RecoveryEvidenceError, RecoveryRecord, RecoveryState,
    decode_frame, decode_journal, encode_frame, record_hash,
)


def record(*, seq=1, previous=GENESIS_HASH, state=RecoveryState.RECONCILIATION_REQUIRED,
           generation=0, epoch="a" * 32, **overrides):
    return RecoveryRecord(
        schema_version=1, sequence=seq, epoch=epoch, generation=generation,
        state=state, previous_hash=previous, **overrides
    )


class RecoveryJournalDocumentTests(unittest.TestCase):
    def test_round_trip_and_hash_chain(self):
        first = record()
        second = record(seq=2, previous=record_hash(first), state=RecoveryState.READY,
                        generation=1, evidence_hash="b" * 64)
        data = encode_frame(first) + encode_frame(second)
        self.assertEqual(decode_journal(data), (first, second))
        self.assertEqual(decode_frame(encode_frame(second)), second)

    def test_in_flight_needs_exact_bounded_ids(self):
        with self.assertRaises(RecoveryEvidenceError):
            record(state=RecoveryState.IN_FLIGHT)
        flight = record(state=RecoveryState.IN_FLIGHT, operation_id="c" * 32,
                        operation_kind="save_metadata", evidence_hash="d" * 64)
        self.assertEqual(decode_frame(encode_frame(flight)), flight)
        with self.assertRaises(RecoveryEvidenceError):
            record(state=RecoveryState.IN_FLIGHT, operation_id="sk-secret",
                   operation_kind="connect", evidence_hash="d" * 64)

    def test_ready_without_evidence_or_with_operation_is_refused(self):
        with self.assertRaises(RecoveryEvidenceError):
            record(state=RecoveryState.READY)
        with self.assertRaises(RecoveryEvidenceError):
            record(operation_kind="connect")

    def test_rejects_truncated_corrupt_and_extra_record_bytes(self):
        raw = encode_frame(record())
        for invalid in (raw[:-1], raw.replace(b"NRJ1", b"NRJ0"),
                        raw.replace(b"reconciliation_required", b"reconciliation_requireD"),
                        raw + b"junk", raw + raw):
            with self.subTest(invalid=invalid[:24]):
                with self.assertRaises(RecoveryEvidenceError):
                    decode_journal(invalid)

    def test_rejects_sequence_or_predecessor_replay(self):
        first = record()
        repeated = record(seq=2, previous=GENESIS_HASH)
        with self.assertRaises(RecoveryEvidenceError):
            decode_journal(encode_frame(first) + encode_frame(repeated))
        with self.assertRaises(RecoveryEvidenceError):
            decode_journal(encode_frame(record(seq=2)))

    def test_noncanonical_payload_and_unknown_fields_are_refused(self):
        raw = encode_frame(record())
        _, _, _, payload_with_lf = raw.split(b" ", 3)
        payload = json.loads(payload_with_lf[:-1])
        payload["model"] = "sk-test-not-a-model"
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        frame = b"NRJ1 " + f"{len(body):04x}".encode() + b" " + hashlib.sha256(body).hexdigest().encode() + b" " + body + b"\n"
        with self.assertRaises(RecoveryEvidenceError):
            decode_frame(frame)
        payload.pop("model")
        body = json.dumps(payload, sort_keys=False).encode()
        frame = b"NRJ1 " + f"{len(body):04x}".encode() + b" " + hashlib.sha256(body).hexdigest().encode() + b" " + body + b"\n"
        with self.assertRaises(RecoveryEvidenceError):
            decode_frame(frame)

    def test_type_confusion_and_unknown_state(self):
        with self.assertRaises(RecoveryEvidenceError):
            RecoveryRecord(schema_version=True, sequence=1, epoch="a" * 32,
                           generation=0, state=RecoveryState.CLOSED,
                           previous_hash=GENESIS_HASH)
        with self.assertRaises(RecoveryEvidenceError):
            RecoveryRecord(schema_version=1, sequence=1, epoch="a" * 32,
                           generation=0, state="ready",
                           previous_hash=GENESIS_HASH)


if __name__ == "__main__":
    unittest.main()


class RecoveryAdversarialJsonTests(unittest.TestCase):
    def test_deep_valid_checksum_frame_returns_typed_error(self):
        body = (b"[" * 1500) + b"0" + (b"]" * 1500)
        frame = (b"NRJ1 " + format(len(body), "04x").encode("ascii") + b" " +
                 hashlib.sha256(body).hexdigest().encode("ascii") + b" " + body + b"\n")
        with self.assertRaises(RecoveryEvidenceError):
            decode_frame(frame)

    def test_duplicate_json_key_is_rejected(self):
        first = record()
        canonical = json.dumps(first.to_payload(), sort_keys=True, separators=(",", ":"))
        body = (canonical[:-1] + ',"epoch":"b' + 'b'*31 + '"}').encode("ascii")
        frame = (b"NRJ1 " + format(len(body), "04x").encode("ascii") + b" " +
                 hashlib.sha256(body).hexdigest().encode("ascii") + b" " + body + b"\n")
        with self.assertRaises(RecoveryEvidenceError):
            decode_frame(frame)
