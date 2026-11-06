"""P76 isolated nonprivileged public-route prototype tests.

These tests are NOT an independent review, release proof or service consent.
"""
import ast
from pathlib import Path
import unittest
from unittest import mock

from tests import phase8_byok_c1_p76_scope as gate
from tests import phase10_3_scope_migration as current

STATES = ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD")


class P76OfflineRoutingTests(unittest.TestCase):
    def test_exact_phase10_3_seal_and_manifest(self):
        self.assertEqual(gate.PARENT,
                         "cacb5c320d26ffa28faf1f15a5e088029ee1453b")
        self.assertEqual(gate.PARENT_TREE,
                         "0773c02397b96de1ad4080017e6c8f58ed192a91")
        self.assertEqual(gate.PARENT_TAG_OBJECT,
                         "ed68953eaacee301592c6349a590a17be9638be5")
        self.assertEqual(len(gate.ADDED), 7)
        self.assertEqual(len(gate.MODIFIED), 1)
        self.assertEqual(gate.MODIFIED, {gate.ROUTE})
        self.assertEqual(set(gate.CANDIDATE_SHA256), gate.ENVELOPE)
        self.assertEqual(gate._digest(gate.SELF, (gate.ROOT/gate.SELF).read_bytes()),
                         gate.CANDIDATE_SHA256[gate.SELF])

    def test_frozen_historical_bytes_are_preserved_as_prefix(self):
        original = gate._git("show", gate.PARENT + ":" + gate.ROUTE)
        proposed = gate._disk(gate.ROUTE)
        self.assertGreater(len(proposed), len(original))
        self.assertTrue(proposed.startswith(original))
        self.assertIsNot(current._phase10_3_sealed_historical_assert,
                         current.assert_phase10_3_integrity)

    def test_source_verifier_is_pure_and_has_no_credential_effects(self):
        source = (gate.ROOT/gate.SELF).read_bytes()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse(any(
                    alias.name.startswith(("socket", "ctypes", "winreg",
                                          "requests", "subprocess"))
                    for alias in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith((
                    "nayeon.", "ctypes", "winreg", "socket", "subprocess")))
        for item in (b"CredWriteW", b"CredDeleteW", b"LocalSystem",
                     b"OperationBoundConsent"):
            self.assertNotIn(item, source)

    def test_wrong_branch_refused_before_other_work(self):
        with mock.patch.object(gate, "_git", return_value=b"unauthorised\n"):
            with self.assertRaisesRegex(gate.P76ScopeRefused, "wrong exact"):
                gate.assert_p76_offline_integrity()

    def test_wrong_annotated_tag_ref_refused(self):
        with mock.patch.object(gate, "_git", return_value=b"0"*40+b"\n"):
            with self.assertRaisesRegex(gate.P76ScopeRefused,
                                        "tag reference changed"):
                gate._tag()

    def test_unknown_untracked_path_refused(self):
        with mock.patch.object(gate, "_git", return_value=b""):
            with self.assertRaisesRegex(gate.P76ScopeRefused,
                                        "missing/extra untracked"):
                gate._proof(gate.PARENT, {}, {}, {}, {},
                            gate.ADDED | {"nayeon/brain/unapproved.py"})

    def test_wrong_commit_parent_refused(self):
        with mock.patch.object(gate, "_git", return_value=b""):
            with mock.patch.object(gate.sealed, "_commit",
                                   return_value=(gate.PARENT_TREE, ["f"*40])):
                with self.assertRaisesRegex(gate.P76ScopeRefused,
                                            "one-commit Phase10.3 child"):
                    gate._proof("1"*40, {}, {}, {}, {}, set())

    def test_old_sealed_live_body_still_rejects_successor_branch(self):
        with self.assertRaisesRegex(AssertionError, "Phase10 wrong exact branch"):
            current._phase10_3_sealed_historical_assert()

    def test_new_public_and_private_gate_agree(self):
        direct = gate.assert_p76_offline_integrity()
        via_current = current.assert_phase10_3_integrity()
        self.assertIn(direct, STATES)
        self.assertEqual(via_current, direct)

    def test_five_public_routes_use_same_source_proof(self):
        from tests.phase8_byok_scope_migration import assert_byok_integrity
        from tests.phase8_byok_b_scope_migration import assert_byok_b_integrity
        from tests.phase10_perception_scope_migration import assert_phase10_integrity
        from tests.phase10_2_privacy_scope_migration import assert_phase10_2_privacy_integrity
        expected = gate.assert_p76_offline_integrity()
        self.assertIn(expected, STATES)
        for fn in (assert_byok_integrity, assert_byok_b_integrity,
                   assert_phase10_integrity, assert_phase10_2_privacy_integrity,
                   current.assert_phase10_3_integrity):
            with self.subTest(fn=fn.__name__):
                self.assertEqual(fn(), expected)


if __name__ == "__main__":
    unittest.main()
