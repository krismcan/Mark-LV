"""P93 genuine Windows child-process stop points, no protected custody I/O."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nayeon.brain import pending_credential_recovery_document as codec
from tests.p93_disposable_crash_recovery import (
    CUTPOINTS, FixtureReadKind, observe_untrusted_fixture, _claim,
)

REPO = Path(__file__).resolve().parents[1]
EXIT_CUT = 73
EXPECTED = {
    "before_first_write": FixtureReadKind.NO_TRUST_SOURCE,
    "after_initial_frame": FixtureReadKind.MISSING_PAIR,
    "after_initial_anchor": FixtureReadKind.STRUCTURAL_INITIAL,
    "after_inflight_partial": FixtureReadKind.INVALID_JOURNAL,
    "after_inflight_frame": FixtureReadKind.INVALID_ANCHOR,
    "after_inflight_anchor": FixtureReadKind.STRUCTURAL_IN_FLIGHT,
    "after_blocked_frame": FixtureReadKind.INVALID_ANCHOR,
    "after_blocked_anchor": FixtureReadKind.STRUCTURAL_BLOCKED,
}


class DisposableCrashRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nayeon-p93-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.journal = self.root / "fixture-journal.bytes"
        self.anchor = self.root / "fixture-anchor.bytes"

    def stop_child(self, stage: str):
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, "-B", "-m",
             "tests.p93_disposable_crash_recovery",
             "--worker", str(self.root), stage],
            cwd=str(REPO), env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=20, check=False)
        self.assertEqual(result.returncode, EXIT_CUT,
                         result.stderr.decode("utf-8", "replace")[:350])
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")
        return observe_untrusted_fixture(self.root)

    def claim_no_authority(self, observation, expected):
        self.assertEqual(observation.kind, expected)
        self.assertFalse(observation.retry_allowed)
        self.assertFalse(observation.credential_authority)
        self.assertFalse(observation.product_verified)
        self.assertNotIn("fixture-journal", repr(observation))

    def test_before_first_write_crash_not_trusted(self):
        self.claim_no_authority(
            self.stop_child("before_first_write"), EXPECTED["before_first_write"])
        self.assertFalse(self.journal.exists())
        self.assertFalse(self.anchor.exists())

    def test_after_first_journal_frame_crash_refuses_unanchored_history(self):
        self.claim_no_authority(self.stop_child("after_initial_frame"),
                                EXPECTED["after_initial_frame"])
        self.assertEqual(len(codec.decode_journal(self.journal.read_bytes())), 1)

    def test_after_first_anchor_crash_still_no_trust(self):
        self.claim_no_authority(self.stop_child("after_initial_anchor"),
                                EXPECTED["after_initial_anchor"])
        self.assertEqual(len(codec.decode_journal(self.journal.read_bytes())), 1)

    def test_after_partial_inflight_frame_crash_refuses(self):
        self.claim_no_authority(self.stop_child("after_inflight_partial"),
                                EXPECTED["after_inflight_partial"])
        with self.assertRaises(codec.PendingEvidenceError):
            codec.decode_journal(self.journal.read_bytes())

    def test_after_inflight_journal_before_anchor_crash_refuses(self):
        self.claim_no_authority(self.stop_child("after_inflight_frame"),
                                EXPECTED["after_inflight_frame"])
        self.assertEqual(len(codec.decode_journal(self.journal.read_bytes())), 2)

    def test_after_inflight_anchor_crash_never_retries(self):
        self.claim_no_authority(self.stop_child("after_inflight_anchor"),
                                EXPECTED["after_inflight_anchor"])
        self.assertEqual(codec.decode_journal(self.journal.read_bytes())[-1].state,
                         codec.PendingRecordedState.IN_FLIGHT)

    def test_after_blocked_record_before_anchor_crash_refuses(self):
        self.claim_no_authority(self.stop_child("after_blocked_frame"),
                                EXPECTED["after_blocked_frame"])
        self.assertEqual(len(codec.decode_journal(self.journal.read_bytes())), 3)

    def test_after_blocked_anchor_crash_remains_recovery_only(self):
        self.claim_no_authority(self.stop_child("after_blocked_anchor"),
                                EXPECTED["after_blocked_anchor"])
        self.assertEqual(codec.decode_journal(self.journal.read_bytes())[-1].state,
                         codec.PendingRecordedState.BLOCKED)

    def test_every_disposable_cutpoint_refuses_restart_authority(self):
        # Multiple independent terminated child processes, each in fresh root.
        for stage in CUTPOINTS:
            with self.subTest(stage=stage):
                with tempfile.TemporaryDirectory(prefix="nayeon-p93-test-") as temp:
                    old_root = self.root
                    self.root = Path(temp)
                    try:
                        observation = self.stop_child(stage)
                        self.claim_no_authority(observation, EXPECTED[stage])
                    finally:
                        self.root = old_root

    def test_forged_valid_history_and_anchor_still_not_authoritative(self):
        self.stop_child("after_initial_anchor")
        raw = self.journal.read_bytes()
        original = codec.decode_journal(raw)[0]
        forged = codec.PendingEvidenceRecord(
            1, 1, "f" * 32, 0, codec.PendingRecordedState.BLOCKED,
            "0" * 64)
        self.assertNotEqual(forged.epoch, original.epoch)
        forged_bytes = codec.encode_frame(forged)
        self.journal.write_bytes(forged_bytes)
        self.anchor.write_bytes(_claim(forged_bytes, 1))
        self.claim_no_authority(observe_untrusted_fixture(self.root),
                                FixtureReadKind.STRUCTURAL_BLOCKED)

    def test_valid_prefix_truncation_and_recomputed_anchor_not_authority(self):
        self.stop_child("after_inflight_anchor")
        full = self.journal.read_bytes()
        first = codec.encode_frame(codec.decode_journal(full)[0])
        self.journal.write_bytes(first)
        self.anchor.write_bytes(_claim(first, 1))
        self.claim_no_authority(observe_untrusted_fixture(self.root),
                                FixtureReadKind.STRUCTURAL_INITIAL)

    def test_wrong_anchor_digest_refused(self):
        self.stop_child("after_inflight_anchor")
        self.anchor.write_bytes(b"P93A|2|" + b"0" * 64 + b"\n")
        self.claim_no_authority(observe_untrusted_fixture(self.root),
                                FixtureReadKind.INVALID_ANCHOR)

    def test_missing_anchor_after_full_commit_refused(self):
        self.stop_child("after_blocked_anchor")
        self.anchor.unlink()
        self.claim_no_authority(observe_untrusted_fixture(self.root),
                                FixtureReadKind.MISSING_PAIR)

    def test_external_non_fixture_root_is_refused(self):
        with self.assertRaises(ValueError):
            observe_untrusted_fixture(REPO)
        with tempfile.TemporaryDirectory(prefix="unrelated-") as wrong:
            with self.assertRaises(ValueError):
                observe_untrusted_fixture(Path(wrong))

    def test_second_writer_cannot_resume_an_existing_inflight_fixture(self):
        self.stop_child("after_inflight_anchor")
        old_journal = self.journal.read_bytes()
        old_anchor = self.anchor.read_bytes()
        child = subprocess.run(
            [sys.executable, "-B", "-m",
             "tests.p93_disposable_crash_recovery",
             "--worker", str(self.root), "after_blocked_anchor"],
            cwd=str(REPO), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=20, check=False)
        self.assertNotEqual(child.returncode, EXIT_CUT)
        self.assertEqual(self.journal.read_bytes(), old_journal)
        self.assertEqual(self.anchor.read_bytes(), old_anchor)
        self.claim_no_authority(observe_untrusted_fixture(self.root),
                                FixtureReadKind.STRUCTURAL_IN_FLIGHT)

    def test_alien_cutpoint_does_not_create_files(self):
        child = subprocess.run(
            [sys.executable, "-B", "-m",
             "tests.p93_disposable_crash_recovery",
             "--worker", str(self.root), "not_a_valid_cut"],
            cwd=str(REPO), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=20, check=False)
        self.assertNotEqual(child.returncode, EXIT_CUT)
        self.assertFalse(self.journal.exists())
        self.assertFalse(self.anchor.exists())

    def test_disposable_run_never_creates_real_key_artifacts(self):
        self.stop_child("after_blocked_anchor")
        self.assertEqual(
            {p.name for p in self.root.iterdir()},
            {"fixture-journal.bytes", "fixture-anchor.bytes"})
        self.assertFalse(any(p.suffix in (".cred", ".key", ".pfx", ".pem")
                             for p in self.root.iterdir()))

    def test_original_source_codec_is_the_tested_reader(self):
        self.stop_child("after_inflight_anchor")
        self.assertEqual(
            codec.decode_journal(self.journal.read_bytes())[-1].state,
            codec.PendingRecordedState.IN_FLIGHT)
        self.assertFalse(hasattr(codec, "authorize_replay"))
        self.assertFalse(hasattr(codec, "approve_credential"))


if __name__ == "__main__":
    unittest.main()
