"""C-M1..M4 exercise the real P273 callable; H fixtures remain immutable.

Physical mutation is guarded to disposable hosted Windows before any write.
No fake Git reply, branch override, original-test patch, skip or xfail.
"""
import hashlib
import copy
import json
import os
import re
import subprocess
import unittest
from unittest import mock

from scripts import p273_p76_current_admission as candidate
from scripts import p245_p76_current_source as source


class P273CurrentAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidate.require_domain(source.ROOT, hosted=True)
        cls.before = candidate.prove_authenticated_current_source(source.ROOT)
        cls.addClassCleanup(cls.final_proof)

    @classmethod
    def final_proof(cls):
        if candidate.prove_authenticated_current_source(source.ROOT) != cls.before:
            raise AssertionError("P273 complete before/after proof differs")

    def proof(self):
        proof = candidate.prove_authenticated_current_source(source.ROOT)
        self.assertEqual(proof["result"], "AUTHENTICATED_CURRENT_SOURCE_EVIDENCE")
        self.assertEqual(proof["provenance"], "C")
        self.assertEqual(proof, self.before)
        return proof

    def mutation(self, target, *, second=False):
        """Real readback, physical injected bytes, precise reach and restoration."""
        self.proof()
        actual = source.raw_source
        original, identity = actual(target)
        parent_blob = self.before["topology"]["parent_tree"][target][1]
        git_raw = source.git("cat-file", "blob", parent_blob)
        self.assertEqual(git_raw, original)
        self.assertEqual(source.blob_oid(original), parent_blob)
        reached = []
        writes = []

        def corrupt(rel):
            if rel == target:
                reached.append(rel)
                if len(reached) == (2 if second else 1):
                    # Status has already been observed clean. Corruption must
                    # be caught by actual disk/blob verification, not status.
                    candidate.require_domain(source.ROOT, hosted=True)
                    writes.append(rel)
                    (source.ROOT / rel).write_bytes(git_raw + b"\nP273 UNTRUSTED\n")
            return actual(rel)

        try:
            with mock.patch.object(source, "raw_source", side_effect=corrupt):
                with self.assertRaisesRegex(source.CurrentSourceRefused,
                        r"\AP245 current-source diagnostic refused: tracked raw Git-byte mismatch: "
                        + re.escape(target) + r"\Z"):
                    candidate.prove_authenticated_current_source(source.ROOT)
            self.assertEqual(writes, [target])
            self.assertEqual(reached, [target] * (2 if second else 1))
            self.assertEqual((source.ROOT / target).read_bytes(), git_raw + b"\nP273 UNTRUSTED\n")
            self.assertEqual(source.git("show", "HEAD:" + target), original)
        finally:
            if writes:
                # Restore only this owned mutation, in place; keep file identity.
                self.assertEqual(actual(target)[1], identity)
                (source.ROOT / target).write_bytes(original)
                self.assertEqual(actual(target), (original, identity))
        self.proof()

    def test_c_m1_live_reader_corruption_and_restoration(self):
        self.proof()
        actual = source.raw_source
        for target in ("nayeon/brain/onboarding_coordination.py",
                       "nayeon/brain/onboarding_recovery.py"):
            reached = []

            def corrupt(rel):
                raw, identity = actual(rel)
                if rel == target:
                    reached.append(rel)
                    self.assertEqual(raw, source.git("show", "HEAD:" + rel))
                    return raw + b"untrusted", identity
                return raw, identity

            with self.subTest(target=target):
                with mock.patch.object(source, "raw_source", side_effect=corrupt):
                    with self.assertRaisesRegex(source.CurrentSourceRefused,
                            r"\AP245 current-source diagnostic refused: tracked raw Git-byte mismatch: "
                            + re.escape(target) + r"\Z"):
                        candidate.prove_authenticated_current_source(source.ROOT)
                self.assertEqual(reached, [target])
                self.proof()

    def test_c_m2_current_parent_projection_physical_corruption_and_restoration(self):
        # Current C parent projection is real Git bytes, not the H factories'
        # nine synthetic states. No historical replay coverage is claimed.
        for target in ("nayeon/brain/onboarding_coordination.py",
                       "nayeon/brain/onboarding_recovery.py"):
            with self.subTest(target=target):
                self.mutation(target)

    def test_c_m3_literal_manifest_and_real_index_negative(self):
        from tests import phase8_byok_b_scope_migration as byok_b
        from tests import phase8_byok_scope_migration as byok_a
        self.assertEqual(byok_b.PARENT, "4110fa69849f8127a325f9a9001284cd1bd3a59c")
        self.assertEqual(byok_b.PARENT_TREE, "747f172144794d687251545ca923d5ebb5b1551b")
        self.assertEqual(byok_b.PARENT_TAG_OBJECT, "7496961c83de9607402dcdabff25917674d6688a")
        self.assertEqual(byok_b.PARENT_PARENT, byok_a.PARENT)
        self.assertEqual((len(byok_b.MODIFIED), len(byok_b.ADDED), len(byok_b.ENVELOPE)), (16, 7, 23))
        self.assertTrue(byok_b.MODIFIED.isdisjoint(byok_b.ADDED))
        self.assertEqual(set(byok_b.CANDIDATE_SHA256), byok_b.ENVELOPE)
        self.assertEqual(source.git("rev-parse", byok_b.PARENT + "^{tree}").strip().decode(), byok_b.PARENT_TREE)
        self.assertEqual(source.git("show-ref", "--verify", "--hash", "--",
                                    "refs/tags/" + byok_b.PARENT_TAG).strip().decode(), byok_b.PARENT_TAG_OBJECT)
        tag_raw = source.git("cat-file", "tag", byok_b.PARENT_TAG_OBJECT)
        self.assertEqual(candidate.object_oid("tag", tag_raw), byok_b.PARENT_TAG_OBJECT)
        self.assertEqual(source.git("rev-parse", byok_b.PARENT_TAG_OBJECT + "^{}").strip().decode(), byok_b.PARENT)
        proof = self.proof()
        self.assertEqual(len(proof["complete_source"]["tree"]), 1104)
        # Feed actual current Git commit/delta/tree into the same parser;
        # negative corruption of these observed bytes must causally refuse.
        head = proof["topology"]["identity"]["head"]
        raw = source.git("cat-file", "commit", head)
        delta = source.git("diff-tree", "--no-commit-id", "--raw", "--no-abbrev",
                           "--no-renames", "-r", "-z", candidate.PARENT, head, "--")
        tree = proof["complete_source"]["tree"]
        parent = proof["topology"]["parent_tree"]
        candidate.validate_child(head, raw, delta, tree, parent)
        for wrong_delta in (delta[:-1], delta + delta, delta.replace(b" A\0", b" M\0", 1)):
            with self.assertRaisesRegex(candidate.CurrentAdmissionRefused, "exact raw add-only child delta differs"):
                candidate.validate_child(head, raw, wrong_delta, tree, parent)
        with self.assertRaisesRegex(candidate.CurrentAdmissionRefused, "raw commit hash/tree/exact parents differ"):
            candidate.validate_child(head, raw + b"untrusted", delta, tree, parent)
        target = "nayeon/brain/onboarding_coordination.py"

        def flag(option):
            candidate.require_domain(source.ROOT, hosted=True)
            child = subprocess.run(["git", "-C", str(source.ROOT), "update-index", option, "--", target],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, timeout=35, env=source.environment(), check=False)
            self.assertEqual(child.returncode, 0, child.stderr)

        try:
            flag("--assume-unchanged")
            self.assertTrue(source.git("ls-files", "-v", "--", target).startswith(b"h "))
            with self.assertRaisesRegex(source.CurrentSourceRefused, "unsupported index flags, stage or entry"):
                candidate.prove_authenticated_current_source(source.ROOT)
        finally:
            flag("--no-assume-unchanged")
        self.assertEqual(source.index_entries(), proof["complete_source"]["index"])
        self.proof()

    def test_c_m4_sealed_pins_and_physical_second_read_negative(self):
        from tests import phase_8_34_scope_migration as phase834
        from tests import phase_8_36_scope_migration as phase836
        sealed = "b0490cd9e72104a74a32dc5315cbc55bc4034676"
        self.assertEqual(phase836.PROTECTED, sealed)
        self.assertEqual(set(phase834.CANDIDATE_SHA256), phase834.ENVELOPE)
        self.assertEqual(len(phase834.ENVELOPE), 20)
        for rel in sorted(phase834.ENVELOPE):
            raw = source.git("show", sealed + ":" + rel)
            if rel == phase834.SELF:
                raw, count = phase834.SELF_PIN.subn(lambda m: m[1] + b"0" * 64 + m[2], raw)
                self.assertEqual(count, 1)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), phase834.CANDIDATE_SHA256[rel])
            self.assertNotEqual(hashlib.sha256(raw + b"untrusted").hexdigest(), phase834.CANDIDATE_SHA256[rel])
        target = "nayeon/desktop_alpha/conversation_session.py"
        actual = source.raw_source
        reads = []

        def observe(rel):
            value = actual(rel)
            if rel == target:
                reads.append(rel)
            return value

        with mock.patch.object(source, "raw_source", side_effect=observe):
            self.proof()
        self.assertEqual(reads, [target, target])
        self.mutation(target, second=True)

    def test_original_public_routes_remain_archival_refusals(self):
        from tests import phase8_byok_c1_p76_scope as p76
        from tests import phase8_byok_b_scope_migration as byok_b
        from tests import phase8_byok_scope_migration as byok_a
        from tests import phase_8_31_scope_migration as old
        from tests import phase_8_34_scope_migration as phase834
        for route in (byok_b.assert_byok_b_integrity, byok_a.assert_byok_integrity,
                      phase834.assert_834_integrity, old.assert_831_integrity):
            with self.subTest(route=route.__module__):
                # Observe the real public call; do not substitute its result.
                with mock.patch.object(p76, "assert_p76_offline_integrity",
                                       wraps=p76.assert_p76_offline_integrity) as reached:
                    with self.assertRaisesRegex(p76.P76ScopeRefused,
                            r"\AP76 offline source refused: wrong exact P76 prototype branch\Z"):
                        route()
                reached.assert_called_once_with()
        self.proof()

    def test_all_five_candidate_files_physically_tampered_are_rejected(self):
        for target in sorted(candidate.ADDED):
            with self.subTest(target=target):
                self.proof()
                raw, identity = source.raw_source(target)
                try:
                    candidate.require_domain(source.ROOT, hosted=True)
                    (source.ROOT / target).write_bytes(raw + b"untrusted")
                    self.assertNotEqual(source.blob_oid((source.ROOT / target).read_bytes()),
                                        self.before["complete_source"]["tree"][target][1])
                    with self.assertRaisesRegex(candidate.CurrentAdmissionRefused,
                                               "dirty, untracked or ignored checkout"):
                        candidate.prove_authenticated_current_source(source.ROOT)
                finally:
                    self.assertEqual(source.raw_source(target)[1], identity)
                    (source.ROOT / target).write_bytes(raw)
                self.proof()

    def test_bracket_receipt_rejects_false_green_against_actual_source(self):
        from scripts import p273_p76_hosted_suite as runner
        proof = self.proof()
        good = {"native_exit": 0, "timeout": False, "process_reaped": True,
                "unittest_complete": True, "expected_tests": runner.TEST_COUNT,
                "before_attempted": True, "after_attempted": True}
        self.assertTrue(runner.qualifies(good, proof, proof))
        for key, value in (("native_exit", 1), ("native_exit", None), ("timeout", True),
                           ("process_reaped", False), ("unittest_complete", False),
                           ("expected_tests", 1), ("after_attempted", False),
                           ("error_type", "Interrupted"), ("after_error_type", "Refused")):
            with self.subTest(field=key, value=value):
                self.assertFalse(runner.qualifies(dict(good, **{key: value}), proof, proof))
        self.assertFalse(runner.qualifies(good, None, proof))
        self.assertFalse(runner.qualifies(good, proof, None))
        drift = copy.deepcopy(proof)
        target = "nayeon/brain/onboarding_recovery.py"
        drift["complete_source"]["disk"][target]["sha256"] = "0" * 64
        self.assertFalse(runner.qualifies(good, proof, drift))
        incomplete = copy.deepcopy(proof)
        incomplete["complete_source"]["disk"].pop(target)
        self.assertFalse(runner.qualifies(good, incomplete, incomplete))
        self.assertFalse(source.suite_log_complete(b"\nRan 11 tests in 1.0s\n\nOK (skipped=1)\n", 11))


class P273ParserTests(unittest.TestCase):
    """Parser-only adversaries carry no current-source acceptance credit."""
    def test_pull_request_event_parser_rejects_forged_metadata(self):
        # These invented bytes exercise only the pure parser. No environment
        # is patched, no live domain is admitted, and no source proof is earned.
        head = "1" * 40
        repo = {"full_name": candidate.REPOSITORY}
        event = {"action": "opened", "number": 73, "repository": dict(repo),
                 "pull_request": {"number": 73, "draft": True,
                    "head": {"sha": head, "ref": candidate.BRANCH, "repo": dict(repo)},
                    "base": {"sha": candidate.PARENT, "ref": candidate.BASE_BRANCH, "repo": dict(repo)}}}

        def parse(value, **changes):
            arguments = {"repository": candidate.REPOSITORY,
                         "ref": "refs/pull/73/merge", "head": head}
            arguments.update(changes)
            raw = value if type(value) is bytes else json.dumps(value).encode()
            return candidate.parse_pull_request_event(raw, **arguments)

        for action in ("opened", "synchronize", "reopened"):
            self.assertEqual(parse(dict(event, action=action))["head"], head)
        cases = [
            (("action",), value) for value in (None, True, 1, [], {}, "closed", "ready_for_review", "push")
        ]
        cases += [(("number",), value) for value in (None, True, False, 0, -1, 2147483648, 73.0, "73", [], {})]
        cases += [(("pull_request", "number"), value) for value in (True, 74, "73", 73.0)]
        cases += [(("pull_request", "draft"), value) for value in (False, None, 1, "true", {})]
        cases += [(("pull_request", side, "sha"), value)
                  for side in ("head", "base") for value in (None, True, "2" * 40, "A" * 40, "1" * 39, [])]
        cases += [(("pull_request", side, "ref"), value)
                  for side in ("head", "base") for value in (None, True, "main", candidate.BRANCH + "/extra")]
        cases += [(("pull_request", side, "repo", "full_name"), value)
                  for side in ("head", "base") for value in (None, True, "fork/Mark-LV", "krismcan/mark-lv")]
        cases += [(("repository", "full_name"), "fork/Mark-LV")]
        cases += [(path, None) for path in (("pull_request",), ("repository",),
                  ("pull_request", "head"), ("pull_request", "base"),
                  ("pull_request", "head", "repo"), ("pull_request", "base", "repo"))]
        for path, value in cases:
            changed = copy.deepcopy(event)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path, value=value):
                with self.assertRaises(candidate.CurrentAdmissionRefused):
                    parse(changed)
            missing = copy.deepcopy(event)
            target = missing
            for key in path[:-1]:
                target = target[key]
            del target[path[-1]]
            with self.assertRaises(candidate.CurrentAdmissionRefused):
                parse(missing)
        for arguments in ({"ref": "refs/heads/" + candidate.BRANCH},
                          {"ref": "refs/pull/74/merge"}, {"ref": "refs/pull/073/merge"},
                          {"ref": "refs/pull/73/head"}, {"repository": "fork/Mark-LV"},
                          {"head": "2" * 40}, {"head": True}):
            with self.subTest(arguments=arguments):
                with self.assertRaises(candidate.CurrentAdmissionRefused):
                    parse(event, **arguments)
        valid = json.dumps(event).encode()
        duplicate = valid.replace(b'"draft": true', b'"draft": false, "draft": true')
        nonfinite = valid.replace(b'"number": 73', b'"number": NaN', 1)
        overflow = valid.replace(b'"number": 73', b'"number": 1e999', 1)
        for raw in (b"", b"{", b"\xff", b"null", b"[]", b"true", duplicate, nonfinite,
                    overflow,
                    b"[" * 2000 + b"]" * 2000, valid + b" " * candidate.MAX_EVENT_BYTES):
            with self.assertRaises(candidate.CurrentAdmissionRefused):
                parse(raw)

    def test_exact_child_parser_rejects_wrong_parent_merge_modification_and_delta(self):
        parent = {"historic.py": ["100644", source.blob_oid(b"original")]}
        tree = dict(parent, **{rel: ["100644", source.blob_oid(rel.encode())] for rel in candidate.ADDED})

        def commit(parents, entries):
            raw = (b"tree " + source.tree_oid(entries).encode() + b"\n"
                   + b"".join(b"parent " + p.encode() + b"\n" for p in parents)
                   + b"author Parser <fake@example.invalid> 0 +0000\n"
                   + b"committer Parser <fake@example.invalid> 0 +0000\n\nparser only\n")
            return candidate.object_oid("commit", raw), raw

        delta = b"".join(b":000000 100644 " + b"0" * 40 + b" " + tree[rel][1].encode()
                          + b" A\0" + rel.encode() + b"\0" for rel in sorted(candidate.ADDED))
        head, raw = commit([candidate.PARENT], tree)
        candidate.validate_child(head, raw, delta, tree, parent)
        for parents in ([], ["1" * 40], [candidate.PARENT, "1" * 40]):
            head, raw = commit(parents, tree)
            with self.assertRaises(candidate.CurrentAdmissionRefused):
                candidate.validate_child(head, raw, delta, tree, parent)
        for changed in (dict(tree, **{"historic.py": ["100644", "1" * 40]}),
                        dict(tree, **{"extra.py": ["100644", "1" * 40]}),
                        {key: value for key, value in tree.items() if key != sorted(candidate.ADDED)[0]}):
            head, raw = commit([candidate.PARENT], changed)
            with self.assertRaises(candidate.CurrentAdmissionRefused):
                candidate.validate_child(head, raw, delta, changed, parent)
        head, raw = commit([candidate.PARENT], tree)
        for wrong in (b"", delta + delta, delta.replace(b" A\0", b" M\0", 1), delta[:-1]):
            with self.assertRaises(candidate.CurrentAdmissionRefused):
                candidate.validate_child(head, raw, wrong, tree, parent)
        with self.assertRaises(candidate.CurrentAdmissionRefused):
            candidate.validate_child(head, raw + b"forged", delta, tree, parent)

    def test_old_p248_root_refusal_is_preserved(self):
        from scripts import p248_p76_properties as old
        with self.assertRaisesRegex(source.CurrentSourceRefused, "P248 wrong assigned root"):
            old.source_snapshot()

    def test_unapproved_git_environment_refuses_without_git(self):
        with mock.patch.dict(os.environ, {"GIT_INDEX_FILE": "untrusted"}):
            with mock.patch.object(source, "git", wraps=source.git) as reached:
                with self.assertRaisesRegex(candidate.CurrentAdmissionRefused, "unsupported Git/P134 environment"):
                    candidate.require_domain(source.ROOT)
                reached.assert_not_called()


if __name__ == "__main__":
    unittest.main()
