"""Five additive P248 properties. Original four FAIL outcomes stay unwaived."""
import hashlib
import os
import re
import unittest
from unittest import mock

from scripts import p248_p76_properties as candidate
from scripts import p245_p76_current_source as source
from tests import phase8_byok_b_scope_migration as byok_b
from tests import phase8_byok_scope_migration as byok_a
from tests import phase8_byok_c1_p76_scope as p76
from tests import phase_8_31_scope_migration as predecessor
from tests import phase_8_34_scope_migration as phase834
from tests import phase_8_36_scope_migration as phase836
from tests import test_phase_834_scope_integrity as original834


class P248CurrentPropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = candidate.source_snapshot()
        # unittest runs class cleanups even if a later setup operation fails.
        cls.addClassCleanup(cls.verify_final_source)

    @classmethod
    def verify_final_source(cls):
        if candidate.source_snapshot() != cls.before:
            raise AssertionError("P248 before/after source observation differs")

    def test_c01_literal_byok_b_parent_and_exact23_witness(self):
        self.assertEqual(byok_b.PARENT, "4110fa69849f8127a325f9a9001284cd1bd3a59c")
        self.assertEqual(byok_b.PARENT_TREE, "747f172144794d687251545ca923d5ebb5b1551b")
        self.assertEqual(byok_b.PARENT_TAG_OBJECT, "7496961c83de9607402dcdabff25917674d6688a")
        self.assertEqual(byok_b.PARENT_PARENT, byok_a.PARENT)
        self.assertEqual(len(byok_b.MODIFIED), 16)
        self.assertEqual(len(byok_b.ADDED), 7)
        self.assertEqual(len(byok_b.ENVELOPE), 23)
        self.assertTrue(byok_b.MODIFIED.isdisjoint(byok_b.ADDED))
        self.assertEqual(set(byok_b.CANDIDATE_SHA256), byok_b.ENVELOPE)
        # Check the actual immutable objects alongside the original literals.
        self.assertEqual(source.git("rev-parse", byok_b.PARENT + "^{tree}").strip().decode(),
                         byok_b.PARENT_TREE)
        self.assertEqual(source.git("show-ref", "--verify", "--hash", "--",
                                    "refs/tags/" + byok_b.PARENT_TAG).strip().decode(),
                         byok_b.PARENT_TAG_OBJECT)
        self.assertEqual(source.git("cat-file", "-t", byok_b.PARENT_TAG_OBJECT), b"tag\n")
        self.assertEqual(source.git("rev-parse", byok_b.PARENT_TAG_OBJECT + "^{}").strip().decode(),
                         byok_b.PARENT)

    def test_c02_sealed_834_twenty_source_pins_and_corruption(self):
        sealed = "b0490cd9e72104a74a32dc5315cbc55bc4034676"
        self.assertEqual(phase836.PROTECTED, sealed)
        paths = original834.ADDED | original834.MODIFIED
        self.assertEqual(len(paths), 20)
        self.assertEqual(set(phase834.CANDIDATE_SHA256), paths)
        for rel in sorted(paths):
            with self.subTest(path=rel):
                raw = source.git("show", sealed + ":" + rel)
                if rel == phase834.SELF:
                    raw, count = original834.SELF_PATTERN.subn(
                        lambda match: match[1] + b"0" * 64 + match[2], raw)
                    self.assertEqual(count, 1)
                expected = phase834.CANDIDATE_SHA256[rel]
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
                self.assertNotEqual(hashlib.sha256(raw + b"untrusted").hexdigest(), expected)

    def test_c03_current_brain_reader_corruption_and_restoration(self):
        baseline = candidate.current_read_pair()
        actual = source.raw_source
        for target in ("nayeon/brain/onboarding_coordination.py",
                       "nayeon/brain/onboarding_recovery.py"):
            reached = []

            def corrupt(rel):
                raw, identity = actual(rel)
                if rel == target:
                    reached.append(rel)
                    return raw + b"untrusted", identity
                return raw, identity

            with self.subTest(target=target):
                with mock.patch.object(source, "raw_source", side_effect=corrupt):
                    with self.assertRaisesRegex(source.CurrentSourceRefused,
                            "^P245 current-source diagnostic refused: tracked raw Git-byte mismatch: "
                            + re.escape(target) + "$"):
                        candidate.current_read_pair()
                self.assertEqual(reached, [target])
                self.assertEqual(candidate.current_read_pair(), baseline)

    def test_c04_current_predecessor_second_read_corruption_and_restoration(self):
        target = "nayeon/desktop_alpha/conversation_session.py"
        actual = source.raw_source
        reads = []

        def observe(rel):
            result = actual(rel)
            if rel == target:
                reads.append(rel)
            return result

        with mock.patch.object(source, "raw_source", side_effect=observe):
            baseline = candidate.current_read_pair()
        self.assertEqual(reads, [target, target])
        second_reads = []

        def corrupt_second(rel):
            raw, identity = actual(rel)
            if rel == target:
                second_reads.append(rel)
                if len(second_reads) == 2:
                    return raw + b"untrusted", identity
            return raw, identity

        with mock.patch.object(source, "raw_source", side_effect=corrupt_second):
            with self.assertRaisesRegex(source.CurrentSourceRefused,
                    "^P245 current-source diagnostic refused: tracked raw Git-byte mismatch: "
                    + re.escape(target) + "$"):
                candidate.current_read_pair()
        self.assertEqual(second_reads, [target, target])
        self.assertEqual(candidate.current_read_pair(), baseline)

    def test_c05_legacy_public_routes_reach_exact_p76_refusal(self):
        routes = (byok_b.assert_byok_b_integrity, byok_a.assert_byok_integrity,
                  phase834.assert_834_integrity, phase836.assert_836_integrity,
                  predecessor.assert_831_integrity)
        for route in routes:
            with self.subTest(route=route.__module__):
                with mock.patch.object(p76, "assert_p76_offline_integrity",
                                       wraps=p76.assert_p76_offline_integrity) as reached:
                    with self.assertRaisesRegex(p76.P76ScopeRefused,
                            r"\AP76 offline source refused: wrong exact P76 prototype branch\Z"):
                        route()
                reached.assert_called_once_with()


class P248TopologyNegativeTests(unittest.TestCase):
    """Synthetic topology parser negatives; no historical-equivalence credit."""

    @classmethod
    def setUpClass(cls):
        cls.before = candidate.source_snapshot()
        cls.addClassCleanup(cls.verify_final_source)

    @classmethod
    def verify_final_source(cls):
        if candidate.source_snapshot() != cls.before:
            raise AssertionError("P248 topology test source observation differs")

    def test_child_raw_commit_and_delta_negatives(self):
        tree = {rel: ["100644", source.blob_oid(rel.encode())]
                for rel in candidate.ADDED}
        delta = b"".join(b":000000 100644 " + b"0" * 40 + b" "
                         + tree[rel][1].encode() + b" A\0" + rel.encode() + b"\0"
                         for rel in sorted(tree))

        def commit(parents):
            raw = (b"tree " + source.tree_oid(tree).encode() + b"\n"
                   + b"".join(b"parent " + parent.encode() + b"\n" for parent in parents)
                   + b"author Synthetic <fake@example.invalid> 0 +0000\n"
                   + b"committer Synthetic <fake@example.invalid> 0 +0000\n\nparser only\n")
            oid = hashlib.sha1(b"commit " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            return oid, raw

        head, raw = commit([candidate.HEAD])
        candidate._validate_child(head, raw, delta, tree)
        for parents in ([], ["1" * 40], [candidate.HEAD, "1" * 40]):
            with self.subTest(parents=parents):
                wrong_head, wrong_raw = commit(parents)
                with self.assertRaises(source.CurrentSourceRefused):
                    candidate._validate_child(wrong_head, wrong_raw, delta, tree)
        for wrong_delta in (b"", delta + delta, delta.replace(b" A\0", b" M\0", 1),
                            delta.replace(b"100644", b"100755", 1),
                            delta.replace(b"100644", b"120000", 1),
                            delta.replace(b"docs/", b"DOCS/", 1)):
            with self.subTest(delta=wrong_delta):
                with self.assertRaises(source.CurrentSourceRefused):
                    candidate._validate_child(head, raw, wrong_delta, tree)
        with self.assertRaises(source.CurrentSourceRefused):
            candidate._validate_child(head, raw + b"tamper", delta, tree)

    def test_status_rejects_staged_dirty_ignored_and_extra_paths(self):
        draft = b"".join(b"?? " + rel.encode() + b"\n" for rel in sorted(candidate.ADDED))
        for head in (candidate.HEAD, "1" * 40):
            for status in (draft.replace(b"?? ", b"A  ", 1),
                           draft + b"?? extra.py\n", b"!! ignored.py\n",
                           b" M scripts/p245_p76_current_source.py\n",
                           b"M  scripts/p245_p76_current_source.py\n"):
                def git(*args):
                    if args == ("rev-parse", "HEAD"):
                        return head.encode() + b"\n"
                    if args == ("status", "--porcelain=v1", "-uall", "--ignored=matching"):
                        return status
                    raise AssertionError("unexpected synthetic Git request")

                with self.subTest(head=head, status=status):
                    with mock.patch.dict(os.environ, {}, clear=True), \
                            mock.patch.object(source, "git", side_effect=git), \
                            mock.patch.object(source, "git_identity", return_value={}) as identity:
                        with self.assertRaises(source.CurrentSourceRefused):
                            candidate._topology()
                        identity.assert_called_once_with(branch=candidate.BRANCH, head=head)

    def test_environment_override_refuses_before_git(self):
        with mock.patch.dict(os.environ, {"GIT_INDEX_FILE": "untrusted"}), \
                mock.patch.object(source, "git") as git:
            with self.assertRaises(source.CurrentSourceRefused):
                candidate._topology()
            git.assert_not_called()

    def test_draft_addition_alias_refuses(self):
        if self.before["topology"] != "EXACT_UNSTAGED_DRAFT":
            # This specific draft path is exercised synthetically on a child;
            # every complete committed scan already rejects all disk aliases.
            topology = ("EXACT_UNSTAGED_DRAFT", candidate.HEAD, {}, b"synthetic")
        else:
            topology = (self.before["topology"], self.before["head"],
                        self.before["identity"], b"synthetic")
        actual = source.raw_source
        alias_identity = actual("scripts/p245_p76_current_source.py")[1]

        def alias(rel):
            raw, identity = actual(rel)
            return raw, alias_identity if rel in candidate.ADDED else identity

        # Exclude additions from a real child inventory only for this draft
        # alias seam. This is not a fabricated positive complete-source proof.
        complete = {key: {rel: value for rel, value in values.items()
                          if rel not in candidate.ADDED}
                    for key, values in self.before["complete_source"].items()}
        with mock.patch.object(candidate, "_topology", return_value=topology), \
                mock.patch.object(source, "complete_source", return_value=complete), \
                mock.patch.object(source, "raw_source", side_effect=alias):
            with self.assertRaisesRegex(source.CurrentSourceRefused,
                    r"\AP245 current-source diagnostic refused: P248 aliased draft source\Z"):
                candidate.source_snapshot()


if __name__ == "__main__":
    unittest.main()
