"""P85 review-only exact-source proofs; does not activate credential custody."""
import ast
import hashlib
import inspect
import re
import unittest
from unittest import mock

from tests import phase8_byok_c1_p85_scope as gate


class P85SourceReviewTests(unittest.TestCase):
    def test_literal_parent_child_source_scope(self):
        self.assertEqual(gate.P80, "24da07345c67566d2e79f442aabfba36a1ebddb4")
        self.assertEqual(gate.P84, "c53b761ea4329ef395a0126097a5949d9a9947a5")
        self.assertEqual(gate.P84_TREE, "7a446c59ca077ecf177ad0906eedff6910ce5141")
        self.assertEqual(len(gate.P84_ADDITIONS), 2)
        self.assertEqual(gate.ADDED, {gate.SELF, gate.TEST})
        self.assertEqual(len(gate.P85_ADDITIONS), 2)
        self.assertTrue(set(gate.P85_ADDITIONS).isdisjoint(gate.P84_ADDITIONS))
        self.assertTrue(set(gate.P85_ADDITIONS).isdisjoint(gate.old.ENVELOPE))

    def test_exact_literal_source_and_normalized_self_sha256(self):
        for name, pin in gate.P85_ADDITIONS.items():
            content = gate._disk(name)
            self.assertRegex(pin, r"^[A-F0-9]{64}$")
            self.assertNotEqual(pin, "0" * 64)
            self.assertEqual(gate._digest(name, content), pin)
        source = gate._disk(gate.SELF)
        self.assertEqual(len(tuple(gate.SELF_PIN.finditer(source))), 1)

    def test_p84_new_sources_are_not_secret_or_effect_authority(self):
        for name, pin in gate.P84_ADDITIONS.items():
            content = gate._disk(name)
            self.assertEqual(hashlib.sha256(content).hexdigest().upper(), pin)
        modules = {n.module for n in ast.walk(ast.parse(inspect.getsource(gate)))
                   if isinstance(n, ast.ImportFrom)}
        self.assertEqual(modules, {
            "__future__", "tests",
        })
        forbidden = (
            "WindowsCredentialBackend", "WinCred", "LocalSystem",
            "credential_operation_host", "provider_validation", "tkinter",
            "subprocess", "requests", "socket", "ctypes",
        )
        source = inspect.getsource(gate)
        for item in forbidden:
            self.assertNotIn(item, source)

    def test_wrong_review_branch_fail_closed_at_entry(self):
        with mock.patch.object(gate, "_git", return_value=b"unapproved-branch\n") as fake:
            with self.assertRaisesRegex(gate.P85ScopeRefused, "wrong exact"):
                gate.assert_p85_offline_source_integrity()
        self.assertEqual(fake.call_count, 1)

    def test_p84_live_source_tamper_refused_from_frozen_manifest(self):
        p84 = gate._p84_baseline()
        path = "nayeon/brain/pending_custody_status_view.py"
        real = gate._disk
        with mock.patch.object(gate, "_disk",
                               side_effect=lambda p: real(p) + b"synthetic-p85"
                               if p == path else real(p)):
            with self.assertRaisesRegex(gate.P85ScopeRefused,
                                        "P84 frozen source changed"):
                gate._expected(p84)

    def test_exact_child_or_precommit_source_gate_succeeds(self):
        expected = gate.assert_p85_offline_source_integrity()
        self.assertIn(expected, {
            "COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD",
        })


if __name__ == "__main__":
    unittest.main()
