"""Fake-only storage-failure tests for the recovery evidence journal."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from nayeon.brain.onboarding_recovery_document import (
    GENESIS_HASH, RecoveryRecord, RecoveryState, encode_frame, record_hash,
)
from nayeon.brain.onboarding_recovery_store import (
    OnboardingRecoveryJournalStore, RecoveryStoreUnavailable,
)


def record(seq, prev, *, epoch="a" * 32, state=RecoveryState.RECONCILIATION_REQUIRED,
           generation=0, evidence_hash=None):
    return RecoveryRecord(
        schema_version=1, sequence=seq, previous_hash=prev, epoch=epoch,
        generation=generation, state=state, evidence_hash=evidence_hash
    )


class OnboardingRecoveryStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "recovery.journal"
        self.store = OnboardingRecoveryJournalStore(self.path)
        self.first = record(1, GENESIS_HASH)

    def test_missing_evidence_never_means_ready(self):
        self.assertIsNone(self.store.read())
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.append(self.first)

    def test_explicit_create_then_checked_append(self):
        self.assertEqual(self.store.append(self.first, create=True), (self.first,))
        second = record(2, record_hash(self.first), state=RecoveryState.READY,
                        generation=1, evidence_hash="f" * 64)
        self.assertEqual(self.store.append(second), (self.first, second))
        self.assertEqual(self.store.read(), (self.first, second))
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.append(self.first, create=True)

    def test_corrupt_or_partial_tail_never_falls_back_to_ready(self):
        self.store.append(self.first, create=True)
        second = record(2, record_hash(self.first), state=RecoveryState.READY,
                        evidence_hash="f" * 64)
        self.store.append(second)
        with self.path.open("ab") as f:
            f.write(b"NRJ1 partial")
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.read()
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.append(record(3, record_hash(second)))

    def test_parent_missing_or_symlink_unavailable(self):
        with self.assertRaises(RecoveryStoreUnavailable):
            OnboardingRecoveryJournalStore(self.path / "other").read()
        self.store.append(self.first, create=True)
        if hasattr(os, "symlink"):
            link = Path(self.tmp.name) / "linked.journal"
            try:
                link.symlink_to(self.path)
            except (OSError, NotImplementedError):
                return
            with self.assertRaises(RecoveryStoreUnavailable):
                OnboardingRecoveryJournalStore(link).read()

    def test_failed_fsync_is_not_reported_as_success(self):
        with patch("nayeon.brain.onboarding_recovery_store.os.fsync",
                   side_effect=OSError("synthetic fsync error")):
            with self.assertRaises(RecoveryStoreUnavailable):
                self.store.append(self.first, create=True)
        # A file may have been partially or fully written; it is not trusted as an
        # established admission record simply because it exists.
        self.assertTrue(self.path.exists())

    def test_failed_reopen_is_not_reported_as_success(self):
        original = OnboardingRecoveryJournalStore._read
        calls = 0
        def read_after_write(obj):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RecoveryStoreUnavailable("synthetic readback failure")
            return original(obj)
        with patch.object(OnboardingRecoveryJournalStore, "_read", read_after_write):
            with self.assertRaises(RecoveryStoreUnavailable):
                self.store.append(self.first, create=True)
        self.assertEqual(self.store.read(), (self.first,))

    def test_duplicate_sequence_and_chain_guard(self):
        self.store.append(self.first, create=True)
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.append(record(2, GENESIS_HASH))
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.append(self.first)

    def test_corrupt_or_invalid_initial_record_denies_append(self):
        self.path.write_bytes(b"NRJ1 malformed\n")
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.append(self.first)
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.append(self.first, create=True)


if __name__ == "__main__":
    unittest.main()


class RecoveryJournalRaceTests(OnboardingRecoveryStoreTests):
    def test_aliased_open_descriptor_denies_write_before_effect(self):
        """Deterministic Windows alias attack: opened fd differs from checked path.

        This tests descriptor binding without needing a privileged symlink or
        developer-mode filesystem setting; the unrelated file MUST stay intact.
        """
        self.store.append(self.first, create=True)
        victim = Path(self.tmp.name) / "unrelated.txt"
        victim.write_bytes(b"DO NOT TOUCH")
        original_open = os.open
        aliased = False

        def swapped_open(path, flags, *args, **kwargs):
            nonlocal aliased
            if not aliased and Path(path) == self.path and (flags & os.O_WRONLY):
                aliased = True
                return original_open(victim, flags, *args, **kwargs)
            return original_open(path, flags, *args, **kwargs)

        second = record(2, record_hash(self.first), state=RecoveryState.READY,
                        generation=1, evidence_hash="f" * 64)
        with patch("nayeon.brain.onboarding_recovery_store.os.open",
                   side_effect=swapped_open):
            with self.assertRaises(RecoveryStoreUnavailable):
                self.store.append(second)
        self.assertTrue(aliased)
        self.assertEqual(victim.read_bytes(), b"DO NOT TOUCH")
        self.assertEqual(self.store.read(), (self.first,))

    def test_nested_json_is_typed_unavailable_from_store(self):
        import hashlib
        body = b"[" * 1500 + b"0" + b"]" * 1500
        digest = hashlib.sha256(body).hexdigest().encode("ascii")
        frame = b"NRJ1 " + f"{len(body):04x}".encode() + b" " + digest + b" " + body + b"\n"
        self.path.write_bytes(frame)
        with self.assertRaises(RecoveryStoreUnavailable):
            self.store.read()


    def test_replacement_with_regular_file_before_open_fails_before_write(self):
        """No symlink privilege needed: replacement identity must be rejected."""
        first = self.first
        self.store.append(first, create=True)
        old = self.path.with_name("moved-original.journal")
        candidate = self.path.with_name("innocent-destination.txt")
        candidate.write_bytes(b"INNOCENT")
        actual_open = os.open
        swapped = False

        def inject(path, flags, *args, **kwargs):
            nonlocal swapped
            if not swapped and Path(path) == self.path and (flags & os.O_WRONLY):
                swapped = True
                os.replace(self.path, old)
                os.replace(candidate, self.path)
            return actual_open(path, flags, *args, **kwargs)

        next_rec = record(2, record_hash(first), state=RecoveryState.READY,
                          generation=1, evidence_hash="a" * 64)
        with patch("nayeon.brain.onboarding_recovery_store.os.open", side_effect=inject):
            with self.assertRaises(RecoveryStoreUnavailable):
                self.store.append(next_rec)
        self.assertTrue(swapped)
        self.assertEqual(self.path.read_bytes(), b"INNOCENT")
        self.assertTrue(old.exists())
