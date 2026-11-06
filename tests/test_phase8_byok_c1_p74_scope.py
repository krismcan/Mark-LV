"""P74 independent-negative-style tests for a NON-AUTHORITATIVE offline gate.

These tests do not exercise native Windows credential operations, a service,
or consent. Successful source integrity is never approval to perform effects.
"""
import ast
from pathlib import Path
import unittest
from unittest import mock

from tests import phase8_byok_c1_p74_scope as gate


class P74OfflineScopeTests(unittest.TestCase):
    def test_parent_and_exact_additive_manifest_are_literal(self):
        self.assertEqual(
            gate.PARENT, "cacb5c320d26ffa28faf1f15a5e088029ee1453b")
        self.assertEqual(
            gate.PARENT_TREE, "0773c02397b96de1ad4080017e6c8f58ed192a91")
        self.assertEqual(
            gate.PARENT_TAG_OBJECT,
            "ed68953eaacee301592c6349a590a17be9638be5")
        self.assertEqual(gate.PARENT_COUNT, 462)
        self.assertEqual(len(gate.ENVELOPE), 8)
        self.assertEqual(set(gate.CANDIDATE_SHA256), gate.ENVELOPE)
        self.assertTrue(all(p.startswith(("tests/", "nayeon/brain/"))
                            for p in gate.ENVELOPE))
        self.assertFalse(any("src/" in p or "WinCred" in p
                             for p in gate.ENVELOPE))
        self.assertEqual(gate._digest(gate.SELF, (gate.ROOT / gate.SELF).read_bytes()),
                         gate.CANDIDATE_SHA256[gate.SELF])

    def test_declared_gate_source_does_not_import_privileged_code(self):
        path = gate.ROOT / gate.SELF
        source = path.read_bytes()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse(any(
                    n.name.startswith(("subprocess", "ctypes", "winreg",
                                       "requests", "socket"))
                    for n in node.names
                ))
            if isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith(
                    ("nayeon.", "winreg", "ctypes", "subprocess", "socket")
                ))
        self.assertNotIn(b"CredWriteW", source)
        self.assertNotIn(b"CredDeleteW", source)

    def test_exact_review_branch_is_required_even_if_old_seal_is_valid(self):
        with mock.patch.object(gate, "_git", return_value=b"wrong-branch\n"):
            with self.assertRaisesRegex(gate.OfflineC1AdmissionRefused,
                                        "wrong exact C1 offline branch"):
                gate.assert_p74_offline_integrity()

    def test_annotated_tag_must_have_exact_original_object(self):
        with mock.patch.object(gate, "_git", return_value=b"0" * 40 + b"\n"):
            with self.assertRaisesRegex(gate.OfflineC1AdmissionRefused,
                                        "tag reference changed"):
                gate._tag()

    def test_untracked_extras_fail_before_source_can_be_admitted(self):
        with mock.patch.object(gate, "_git", return_value=b""):
            with self.assertRaisesRegex(gate.OfflineC1AdmissionRefused,
                                        "missing or extra untracked source"):
                gate._proof(gate.PARENT, {}, {}, {}, {},
                            gate.ENVELOPE | {"nayeon/brain/extra.py"})

    def test_wrong_child_parent_is_rejected(self):
        with mock.patch.object(gate, "_git", return_value=b""):
            with mock.patch.object(gate.sealed, "_commit",
                                   return_value=(gate.PARENT_TREE, ["0" * 40])):
                with self.assertRaisesRegex(gate.OfflineC1AdmissionRefused,
                                            "requires immediate Phase10.3 child"):
                    gate._proof("1" * 40, {}, {}, {}, {}, frozenset())

    def test_modified_pure_file_is_rejected_against_unchanged_pin(self):
        baseline = gate.sealed._tree(gate.PARENT)
        original = gate._disk

        def disk(path):
            b = original(path)
            if path == "nayeon/brain/pending_credential_policy.py":
                return b + b"\n# unauthorised change\n"
            return b

        with mock.patch.object(gate, "_disk", side_effect=disk):
            with self.assertRaisesRegex(gate.OfflineC1AdmissionRefused,
                                        "candidate byte mismatch"):
                gate._expected(baseline)

    def test_native_exact_source_state_is_read_only_verified(self):
        self.assertIn(gate.assert_p74_offline_integrity(),
                      ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD"))


if __name__ == "__main__":
    unittest.main()
