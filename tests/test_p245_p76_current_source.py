"""P245 source-era split: pure negative tests and genuine hosted Windows candidate."""
from __future__ import annotations

import ast
import os
import unittest
from unittest import mock

from scripts import p245_p76_current_source as candidate
from tests import phase8_byok_c1_p76_scope as frozen


class P245PureNegativeTests(unittest.TestCase):
    def test_frozen_branch_literal_unchanged(self):
        raw = candidate.source_file("tests/phase8_byok_c1_p76_scope.py").read_bytes()
        self.assertEqual(candidate.historical_branch_literal(raw), candidate.HISTORICAL_P76_BRANCH)

    def test_real_historical_p76_gate_still_denies_descendant(self):
        with self.assertRaisesRegex(frozen.P76ScopeRefused, "wrong exact P76"):
            frozen.assert_p76_offline_integrity()

    def test_all_four_original_failed_methods_remain_unwaived(self):
        self.assertEqual(len(candidate.ORIGINAL_FAILURE_IDS), 4)
        self.assertEqual(len(set(candidate.ORIGINAL_FAILURE_IDS)), 4)
        self.assertTrue(all(t.startswith("tests.test_") for t in candidate.ORIGINAL_FAILURE_IDS))

    def test_no_paths_outside_exact_source_manifest(self):
        for path in ("../tests/phase8_byok_c1_p76_scope.py",
                     "/Windows/System32/config/SAM",
                     r"C:\Windows\System32\config",
                     "tests/../tests/phase8_byok_c1_p76_scope.py",
                     "nayeon/brain/user_secrets.py", "",
                     "tests//phase8_byok_c1_p76_scope.py"):
            with self.subTest(path=path):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.source_file(path)

    def test_historical_tag_pin_is_not_overrideable(self):
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "tag authority"):
            candidate.validate_historical_tag("f" * 40)

    def test_missing_or_nonliteral_historical_branch_denied(self):
        for raw in (b"BRANCH = compute_from_environment()\n", b"OTHER='a'\n",
                    b"BRANCH='a'\nBRANCH='b'\n"):
            with self.subTest(source=raw):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.historical_branch_literal(raw)

    def test_untrusted_host_environment_refused(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "hosted Windows"):
                candidate.validate_event(branch=candidate.BRANCH, head="a" * 40)

    def test_git_process_environment_drops_injected_authority(self):
        with mock.patch.dict(os.environ, {
            "GIT_INDEX_FILE": "C:/forged-index", "GIT_CONFIG_COUNT": "1",
            "P134_TEST_GRANT": "false", "GIT_WORK_TREE": "C:/wrong",
        }):
            env = candidate.environment()
        for key in ("GIT_INDEX_FILE", "GIT_CONFIG_COUNT", "P134_TEST_GRANT",
                    "GIT_WORK_TREE"):
            self.assertNotIn(key, env)
        self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")

    def test_read_only_script_imports_no_wincred_provider_or_effect_modules(self):
        source = candidate.source_file("scripts/p245_p76_current_source.py").read_bytes()
        tree = ast.parse(source)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                roots.add((node.module or "").split(".")[0])
        self.assertTrue(roots.isdisjoint({"ctypes", "winreg", "socket", "requests", "nayeon"}))
        self.assertNotIn(b"CredWriteW", source)
        self.assertNotIn(b"CredDeleteW", source)

    def test_candidate_never_classifies_legacy_failures_as_green(self):
        self.assertTrue(candidate.ORIGINAL_FAILURE_IDS[0].endswith("test_live_brain_reader_tamper_remains_rejected_after_historical_replay"))
        self.assertEqual(candidate.BASE, "da9c436a177b3ec68db0eff2b610180b745bfb2b")


class P245GenuineHostedWindowsCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # These methods are run only on genuine branch-bound GitHub Windows-2025.
        cls.sha = os.environ.get("GITHUB_SHA", "")
        cls.proof = candidate.verify_current(branch=candidate.BRANCH, head=cls.sha)

    def test_positive_read_only_current_source_and_all_six_frozen_witnesses(self):
        self.assertTrue(self.proof["candidate_source_pass"])
        self.assertEqual(self.proof["head"], self.sha)
        self.assertEqual(self.proof["parent"], candidate.BASE)
        self.assertEqual(self.proof["frozen_sha256"], candidate.FROZEN)
        self.assertEqual(self.proof["real_key_admission"], "NO-GO")
        self.assertEqual(self.proof["production_release"], "HOLD")

    def test_original_four_p234_failures_never_marked_pass(self):
        self.assertEqual(self.proof["four_original_P234_failures_unwaived"],
                         list(candidate.ORIGINAL_FAILURE_IDS))
        self.assertTrue(self.proof["historical_P76_wrong_branch_refusal_preserved"])

    def test_negative_historical_branch_is_not_new_authority(self):
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "signed event"):
            candidate.verify_current(branch=candidate.HISTORICAL_P76_BRANCH, head=self.sha)

    def test_negative_untrusted_new_head_cannot_pass(self):
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "signed event"):
            candidate.verify_current(branch=candidate.BRANCH, head="f" * 40)

    def test_negative_wrong_source_parent_not_admitted(self):
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "signed event"):
            candidate.verify_current(branch=candidate.BRANCH, head=self.sha,
                                     ancestor="f" * 40)

    def test_negative_substituted_frozen_p76_sha_denied(self):
        path = "tests/phase8_byok_c1_p76_scope.py"
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "witness mismatch"):
            candidate.verify_current(branch=candidate.BRANCH, head=self.sha,
                                     digest_override={path: "0" * 64})

    def test_original_historical_refusal_in_actual_current_branch(self):
        with self.assertRaisesRegex(frozen.P76ScopeRefused, "wrong exact P76"):
            frozen.assert_p76_offline_integrity()


if __name__ == "__main__":
    unittest.main()
