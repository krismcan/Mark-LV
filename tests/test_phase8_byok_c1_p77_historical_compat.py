"""P77 historical source/negative-contract tests (offline, review-only).

The actual original Phase10.3 security test file remains byte-for-byte
unchanged. These NEW tests independently verify cause-specific refusals
in the P77 current route, without monkeypatching a success fallback.
"""
import hashlib
import unittest
from unittest import mock

from tests import phase8_byok_c1_p76_scope as new
from tests import phase10_3_scope_migration as old


class P77HistoricalContracts(unittest.TestCase):
    def test_original_phase10_3_negative_tests_byte_identical(self):
        rel = "tests/test_phase10_3_scope_integrity.py"
        original = new._git("show", new.PARENT + ":" + rel)
        current = new._disk(rel)
        self.assertEqual(hashlib.sha256(original).digest(),
                         hashlib.sha256(current).digest())
        self.assertEqual(original, current)

    def test_full_original_phase10_3_tree_rebuilt_from_sealed_ancestry(self):
        observed = new._baseline()
        self.assertEqual(len(observed), 462)
        self.assertEqual(old.prior._tree_oid(observed), new.PARENT_TREE)

    def test_frozen_state_tamper_retains_original_causal_refusal(self):
        target = ".codex/CURRENT_STATE.md"
        real = old._disk
        visited = []

        def tamper(path):
            raw = real(path)
            if path == target:
                visited.append(path)
                return raw + b"malicious test-only tail"
            return raw

        with mock.patch.object(old, "_disk", side_effect=tamper):
            with self.assertRaisesRegex(AssertionError,
                                        r"^Phase10\.2 frozen source modified: \.codex/CURRENT_STATE\.md$"):
                old.assert_phase10_3_integrity()
        self.assertEqual(visited, [target])

    def test_legacy_phase10_3_candidate_tamper_refusal(self):
        rel = "tests/test_phase_834_scope_integrity.py"
        self.assertIn(rel, old.ENVELOPE)
        real = old._disk
        reached = []

        def corrupt(path):
            raw = real(path)
            if path == rel:
                reached.append(path)
                return raw + b"unreviewed test-only edit"
            return raw

        with mock.patch.object(old, "_disk", side_effect=corrupt):
            with self.assertRaisesRegex(AssertionError,
                                        r"^Phase10\.2 candidate byte mismatch: " +
                                        rel.replace(".", r"\.") + r"$"):
                old.assert_phase10_3_integrity()
        self.assertEqual(reached, [rel])

    def test_legacy_self_literal_pin_tamper_refuses_exactly(self):
        source = old._disk(old.SELF)
        pins = tuple(old.SELF_PIN.finditer(source))
        self.assertEqual(len(pins), 1)
        pin = pins[0]
        changed = source[:pin.end(1)] + b"f" * 64 + source[pin.start(2):]
        if changed == source:
            changed = source[:pin.end(1)] + b"e" * 64 + source[pin.start(2):]
        real = old._disk
        reached = []

        def tamper(path):
            if path == old.SELF:
                reached.append(path)
                return changed
            return real(path)

        with mock.patch.object(old, "_disk", side_effect=tamper):
            with self.assertRaisesRegex(AssertionError,
                                        r"^Phase10\.3 self-pin literal mismatch$"):
                old.assert_phase10_3_integrity()
        self.assertEqual(reached, [old.SELF])

    def test_phase10_2_tag_ref_rechecked_after_live_source_window(self):
        query = ("show-ref", "--verify", "--hash", "--",
                 "refs/tags/" + old.PARENT_TAG)
        real = old._git
        seen = []

        def drift(*args):
            raw = real(*args)
            if args == query:
                seen.append(args)
                if len(seen) == 2:
                    return b"f" * 40 + b"\n"
            return raw

        with mock.patch.object(old, "_git", side_effect=drift):
            with self.assertRaises(AssertionError):
                old.assert_phase10_3_integrity()
        self.assertEqual(seen, [query, query])

    def test_no_fallback_if_current_verifier_denies(self):
        from tests import phase10_2_privacy_scope_migration as prev
        with mock.patch.object(new, "assert_p76_offline_integrity",
                               side_effect=AssertionError("P77 DENIAL")):
            with mock.patch.object(old,
                                   "_phase10_3_sealed_historical_assert",
                                   side_effect=AssertionError("BAD HISTORIC FALLBACK")) as fallback:
                with self.assertRaisesRegex(AssertionError, r"^P77 DENIAL$"):
                    prev.assert_phase10_2_privacy_integrity()
        fallback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
