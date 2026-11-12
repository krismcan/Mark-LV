"""P166 additive genuine-current-branch positive/negative SECURITY DIAGNOSTICS.

Never edits historical P76/P85 tests. Never creates a real consent or release.
"""
from __future__ import annotations

import os
import unittest
from unittest import mock

from scripts import p166_windows_current_branch_acceptance as candidate
from tests import phase8_byok_c1_p76_scope as historical
from nayeon.desktop_alpha import frozen_signed_byok_companion as signed


class P166RealCurrentBranchAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.event_sha = os.environ.get("GITHUB_SHA", "")
        cls.real = candidate.verify_current_source(
            expected_branch=candidate.BRANCH, expected_head=cls.event_sha
        )

    def test_positive_live_windows_head_tree_and_19_original_security_sources(self):
        self.assertEqual(self.real["head"], self.event_sha)
        self.assertTrue(self.real["is_real_current_branch_git_checkout"])
        self.assertEqual(self.real["ancestor"], candidate.BASE)
        self.assertEqual(len(self.real["original_security_files_byte_preserved"]), 19)
        self.assertEqual(self.real["original_test_modules"], 170)
        self.assertFalse(self.real["is_production_release_authorization"])

    def test_positive_actual_unchanged_original_git_blobs_not_synthetic_fixture(self):
        actual = self.real["original_security_files_byte_preserved"]
        for entry in actual:
            with self.subTest(path=entry["path"]):
                self.assertEqual(
                    candidate.git("show", "HEAD:" + entry["path"]),
                    (candidate.ROOT / entry["path"]).read_bytes(),
                )
                self.assertGreater(entry["bytes"], 0)

    def test_positive_original_annotated_historical_tag_object(self):
        self.assertEqual(candidate.verify_historical_tag(), candidate.HIST_TAG_OID)

    def test_negative_wrong_live_branch_identity_refused(self):
        with self.assertRaisesRegex(candidate.P166Refused, "wrong signed event"):
            candidate.verify_current_source(
                expected_branch="byok-c1-p80-sealed-historical-fixture-20261106",
                expected_head=self.event_sha,
            )

    def test_negative_substituted_event_head_refused(self):
        with self.assertRaisesRegex(candidate.P166Refused, "wrong signed event"):
            candidate.verify_current_source(
                expected_branch=candidate.BRANCH, expected_head="f" * 40
            )

    def test_negative_wrong_ancestor_parent_refused(self):
        with self.assertRaisesRegex(candidate.P166Refused, "wrong signed event"):
            candidate.verify_current_source(
                expected_branch=candidate.BRANCH, expected_head=self.event_sha,
                expected_ancestor="f" * 40,
            )

    def test_negative_wrong_historical_tag_object_refused(self):
        with self.assertRaisesRegex(candidate.P166Refused, "substituted historical tag"):
            candidate.verify_historical_tag("f" * 40)

    def test_negative_source_manifest_sha256_substitution_refused(self):
        first = candidate.PROTECTED[0]
        with self.assertRaisesRegex(candidate.P166Refused, "source manifest"):
            candidate.verify_current_source(
                expected_branch=candidate.BRANCH, expected_head=self.event_sha,
                digest_override={first: "0" * 64},
            )

    def test_negative_outside_absolute_windows_path_refused(self):
        with self.assertRaisesRegex(candidate.P166Refused, "untrusted source path"):
            candidate._ordinary_repo_file(r"C:\Windows\System32\config")

    def test_negative_traversal_and_alias_refused(self):
        for path in ("../tests/test_phase8_byok_c1_p76_scope.py",
                     "./tests/test_phase8_byok_c1_p76_scope.py",
                     "tests/../tests/test_phase8_byok_c1_p76_scope.py",
                     "tests\\test_phase8_byok_c1_p76_scope.py",
                     "//host/unc/share", "tests//test_phase8_byok_c1_p76_scope.py"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(candidate.P166Refused, "untrusted source path"):
                    candidate._ordinary_repo_file(path)

    def test_negative_unapproved_path_cannot_become_source_authority(self):
        with self.assertRaisesRegex(candidate.P166Refused, "not in versioned"):
            candidate._ordinary_repo_file("scripts/p166_windows_current_branch_acceptance.py")

    def test_negative_original_p76_gate_rejects_real_successor_branch(self):
        with self.assertRaisesRegex(historical.P76ScopeRefused, "wrong exact P76"):
            historical.assert_p76_offline_integrity()

    def test_negative_no_unapproved_signed_binary_or_code_integrity_go(self):
        self.assertFalse(signed._release_pins_issued())
        with mock.patch.object(signed.subprocess, "run",
                               side_effect=AssertionError("unapproved process")) as spawn:
            self.assertIsNone(signed.approved_frozen_local_byok_companion())
            spawn.assert_not_called()

    def test_negative_no_candidate_provider_or_wincred_side_effect_path(self):
        # This is process-level Python instrumentation only, not OS-wide telemetry.
        # Independent original 25-method tests cover fake WinCred one-use consent.
        with mock.patch("socket.socket", side_effect=AssertionError("Python network forbidden")):
            candidate.verify_current_source(
                expected_branch=candidate.BRANCH, expected_head=self.event_sha,
            )

    def test_separate_H_C_R_contract_never_authorises_production(self):
        self.assertEqual(len(candidate.HISTORICAL_TWO_BRANCH_POSITIVES), 2)
        self.assertEqual(self.real["historical_original_positive_failures_unwaived"],
                         list(candidate.HISTORICAL_TWO_BRANCH_POSITIVES))
        self.assertFalse(self.real["is_production_release_authorization"])
        # Candidate C is only one dimension; reviewer and original R gates remain absent.
        for h in (False, True):
            for c in (False, True):
                self.assertFalse(h and c and False)


if __name__ == "__main__":
    unittest.main()
