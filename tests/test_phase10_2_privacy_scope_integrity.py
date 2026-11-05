"""Phase 10.2 successor source admission — real and fictional adversaries.

Historical source seals are immutable. Fictional topology parsers are not
evidence that current Git/index/disk admission passed. Native real admission
runs separately and must fail until all literal SHA256 pins are finalized.
"""
import hashlib
import unittest
from unittest import mock

from tests import phase10_2_privacy_scope_migration as gate

STATES = ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD")


def git_object(kind, body):
    return hashlib.sha1(kind.encode() + b" " + str(len(body)).encode()
                        + b"\0" + body).hexdigest()


def raw_diff(before, after, paths, *, work=False):
    rows = []
    for path in sorted(paths):
        old_mode, old_oid = before.get(path, ("000000", "0" * 40))
        new_mode, new_oid = ((old_mode, "0" * 40) if work
                             else after[path])
        status = "M" if path in before else "A"
        meta = f":{old_mode} {new_mode} {old_oid} {new_oid} {status}"
        rows.append(meta.encode() + b"\0" + path.encode() + b"\0")
    return b"".join(rows)


def fictional_state(state, *, parent=None, extra_untracked=None):
    before = {p: ("100644", git_object("blob", ("before/" + p).encode()))
              for p in gate.MODIFIED | {"sealed.py"}}
    after = dict(before)
    for p in gate.ENVELOPE:
        after[p] = ("100644", git_object("blob", ("after/" + p).encode()))
    committed = after if state == "EXACT_CHILD" else before
    index = before if state == "COMPLETE_UNSTAGED" else after
    untracked = (set(gate.ADDED) if state == "COMPLETE_UNSTAGED" else set())
    if extra_untracked:
        untracked |= set(extra_untracked)
    changed = gate.MODIFIED if state == "COMPLETE_UNSTAGED" else set()
    raw_work = raw_diff(index, after, changed, work=True)
    child_commit = (
        "tree " + gate.prior._tree_oid(after) + "\n"
        "parent " + (gate.PARENT if parent is None else parent) + "\n"
        "author Synthetic <synthetic@example.invalid> 0 +0000\n"
        "committer Synthetic <synthetic@example.invalid> 0 +0000\n\n"
        "fixture\n").encode()
    child_id = git_object("commit", child_commit)
    head = child_id if state == "EXACT_CHILD" else gate.PARENT
    cached = raw_diff(committed, index, (
        gate.ENVELOPE if state == "EXACT_STAGED" else set()))
    delta = raw_diff(before, after, gate.ENVELOPE)

    def fake_git(*args):
        if args == gate.RAW + ("--cached",):
            return cached
        if args == ("cat-file", "-t", child_id):
            return b"commit\n"
        if args == ("cat-file", "commit", child_id):
            return child_commit
        if args == ("rev-list", "--parents", "-n", "1", child_id):
            return (child_id + " " +
                    (gate.PARENT if parent is None else parent) + "\n").encode()
        if args == gate.RAW + (gate.PARENT, child_id):
            return delta
        raise AssertionError("Unexpected fictional Git query")

    return (head, before, after, committed, index, untracked, raw_work,
            fake_git)


class SyntheticTopologyParserTests(unittest.TestCase):
    def test_three_fictional_exact_topologies(self):
        for state in STATES:
            args = fictional_state(state)
            with self.subTest(state=state), mock.patch.object(
                    gate, "_git", side_effect=args[-1]):
                self.assertEqual(gate._prove_topology(*args[:-1]), state)

    def test_untracked_missing_or_extra_rejected(self):
        for added in ({"unexpected.py"}, set()):
            args = fictional_state("COMPLETE_UNSTAGED")
            modified_args = list(args)
            modified_args[5] = added
            with self.subTest(added=added), mock.patch.object(
                    gate, "_git", side_effect=args[-1]):
                with self.assertRaises(AssertionError):
                    gate._prove_topology(*modified_args[:-1])

    def test_partial_staging_does_not_count_as_exact(self):
        args = list(fictional_state("EXACT_STAGED"))
        staged = dict(args[4])
        key = next(iter(gate.MODIFIED))
        staged[key] = args[1][key]
        args[4] = staged
        with mock.patch.object(gate, "_git", side_effect=args[-1]):
            with self.assertRaisesRegex(AssertionError, "partial stage"):
                gate._prove_topology(*args[:-1])

    def test_wrong_parent_or_merge_refused(self):
        args = fictional_state("EXACT_CHILD", parent="f" * 40)
        with mock.patch.object(gate, "_git", side_effect=args[-1]):
            with self.assertRaisesRegex(AssertionError, "immediate sealed child"):
                gate._prove_topology(*args[:-1])

    def test_raw_index_changes_and_malformed_deltas_refused(self):
        for state in STATES:
            args = fictional_state(state)
            if state == "COMPLETE_UNSTAGED":
                args = list(args)
                args[6] = b"garbage\0"
            else:
                calls = args[-1]
                def altered(*params):
                    raw = calls(*params)
                    if params == gate.RAW + ("--cached",):
                        return b"garbage\0"
                    return raw
                args = tuple(args[:-1]) + (altered,)
            with self.subTest(state=state), mock.patch.object(
                    gate, "_git", side_effect=args[-1]):
                with self.assertRaises(AssertionError):
                    gate._prove_topology(*args[:-1])

    def test_self_pin_normalized_once_and_only_for_self(self):
        own = b'"tests/phase10_2_privacy_scope_migration.py": "' + b"1"*64 + b'",'
        self.assertEqual(
            gate._digest(gate.SELF, own),
            hashlib.sha256(own.replace(b"1"*64, b"0"*64)).hexdigest())
        self.assertEqual(gate._digest("another.py", own),
                         hashlib.sha256(own).hexdigest())
        for malformed in (b"missing", own + own):
            with self.assertRaises(AssertionError):
                gate._digest(gate.SELF, malformed)

    def test_complete_parent_only_and_fixed_manifest(self):
        self.assertEqual(gate.PARENT,
                         "be6c126dc5f3a6814925bb95009ef2b2e6be80b7")
        self.assertEqual(len(gate.ADDED), 5)
        self.assertEqual(gate.ADDED & gate.MODIFIED, frozenset())
        self.assertEqual(set(gate.CANDIDATE_SHA256), gate.ENVELOPE)

    def test_wrong_branch_rejects_before_any_current_source(self):
        real = gate._git
        reached = []
        def bad(*args):
            if args == ("branch", "--show-current"):
                reached.append(args)
                return b"wrong-branch\n"
            return real(*args)
        with mock.patch.object(gate, "_git", side_effect=bad):
            with self.assertRaisesRegex(AssertionError, "^Phase10 wrong exact branch$"):
                gate.assert_phase10_2_privacy_integrity()
        self.assertEqual(len(reached), 1)


class NativeExactSourceAdmissionTests(unittest.TestCase):
    """Real host Git, static pins, actual disk: mandatory release entrypoint."""

    def test_authenticated_sealed_phase10_1_parent_tree_and_tag(self):
        baseline = gate._baseline()
        self.assertEqual(gate.prior._tree_oid(baseline), gate.PARENT_TREE)
        self.assertEqual(gate._oid("rev-parse", gate.PARENT + "^{tree}"),
                         gate.PARENT_TREE)

    def test_real_complete_source_live_admission(self):
        self.assertIn(gate.assert_phase10_2_privacy_integrity(), STATES)

    def test_real_source_tamper_causes_exact_refusal(self):
        self.assertIn(gate.assert_phase10_2_privacy_integrity(), STATES)
        path = "nayeon/perception/contracts.py"
        self.assertNotIn(path, gate.MODIFIED)
        true_reader = gate._disk
        observed = []
        def tamper(actual):
            raw = true_reader(actual)
            if actual == path:
                observed.append(actual)
                return raw + b"HOSTILE"
            return raw
        with mock.patch.object(gate, "_disk", side_effect=tamper):
            with self.assertRaisesRegex(
                    AssertionError, "Phase10.2 frozen source modified"):
                gate.assert_phase10_2_privacy_integrity()
        self.assertEqual(observed, [path])

    def test_sealed_tag_tamper_reached_and_denied(self):
        self.assertIn(gate.assert_phase10_2_privacy_integrity(), STATES)
        real = gate._git
        key = ("show-ref", "--verify", "--hash",
               "--", "refs/tags/" + gate.PARENT_TAG)
        reached = []
        def swapped(*args):
            if args == key:
                reached.append(args)
                return b"a"*40 + b"\n"
            return real(*args)
        with mock.patch.object(gate, "_git", side_effect=swapped):
            with self.assertRaisesRegex(AssertionError,
                                        "Phase10.2 sealed parent tag mismatch"):
                gate.assert_phase10_2_privacy_integrity()
        self.assertEqual(reached, [key])

    def test_late_parent_tag_ref_drift_is_causally_refused(self):
        self.assertIn(gate.assert_phase10_2_privacy_integrity(), STATES)
        key = ("show-ref", "--verify", "--hash",
               "--", "refs/tags/" + gate.PARENT_TAG)
        real = gate._git
        reached = []
        def swap_after_first(*args):
            if args == key:
                reached.append(args)
                if len(reached) == 2:
                    return b"f" * 40 + b"\n"
            return real(*args)
        with mock.patch.object(gate, "_git", side_effect=swap_after_first):
            with self.assertRaisesRegex(
                    AssertionError,
                    r"^Phase10\.2 sealed parent tag changed during admission$"):
                gate.assert_phase10_2_privacy_integrity()
        self.assertEqual(reached, [key, key])

    def test_three_perception_source_projection_never_accepts_partial(self):
        from tests import phase_8_30_scope_migration as projection
        self.assertIn(gate.assert_phase10_2_privacy_integrity(), STATES)
        paths = sorted({
            "nayeon/perception/__init__.py",
            "nayeon/perception/contracts.py",
            "nayeon/perception/permissions.py",
        })
        other = "unrelated-valid.py"
        for mask in range(1, 7):
            partial = {p for i, p in enumerate(paths) if mask & (1 << i)}
            with self.subTest(partial=sorted(partial)):
                with self.assertRaisesRegex(
                        AssertionError,
                        r"^Partial Phase10\.2 perception source inventory$"):
                    projection._project_837_draft_sources(partial | {other})
        self.assertEqual(projection._project_837_draft_sources({other}), {other})
        self.assertEqual(projection._project_837_draft_sources(set(paths) | {other}),
                         {other})

    def test_legacy_presentation_git_delta_view_exact_not_subset(self):
        # Prove current admission independently, then replay ONLY sealed 10.2
        # bytes under its original tracked/untracked production topology.
        live_state = gate.assert_phase10_2_privacy_integrity()
        self.assertIn(live_state, STATES)
        from tests.test_phase10_3_scope_integrity import sealed_phase10_2
        try:
            with sealed_phase10_2(live_state):
                from tests import phase_8_30_scope_migration as projection
                state = gate.assert_phase10_2_privacy_integrity()
                self.assertIn(state, STATES)
                trio = projection._PHASE10_2_TRIO
                pair = projection._PHASE10_PERCEPTION_SOURCES
                if state != "COMPLETE_UNSTAGED":
                    other = "unrelated-valid.py"
                    self.assertEqual(projection._project_837_draft_sources(
                        set(trio) | {other}), {other})
                    self.assertEqual(projection.approved_830_scope(set(trio) | {other}),
                                     {other})
                    self.assertEqual(projection.approved_830_scope(set()), set())
                    for partial in (set(pair), {"nayeon/perception/permissions.py"}):
                        with self.subTest(state=state, partial=sorted(partial)):
                            with self.assertRaisesRegex(
                                    AssertionError,
                                    "delta exception requires unstaged source"):
                                projection.approved_830_scope(partial)
                    for baseline in sorted(projection._PHASE10_2_DELTA_BASELINES):
                        view = projection._phase10_2_nul_git_paths(
                            "diff", "--no-renames", "--name-only", "-z",
                            baseline, "--", "nayeon")
                        self.assertEqual(view & trio, trio)
                    self.assertEqual(projection._phase10_2_nul_git_paths(
                        "ls-files", "--others", "--exclude-standard",
                        "-z", "--", "nayeon"), frozenset())
                    return
                for baseline in sorted(projection._PHASE10_2_DELTA_BASELINES):
                    raw = projection._phase10_2_nul_git_paths(
                        "diff", "--no-renames", "--name-only", "-z",
                        baseline, "--", "nayeon")
                    self.assertEqual(raw & trio, pair)
                    self.assertGreater(len(raw), len(pair))
                    supplied = set(raw)
                    result = projection.approved_830_scope(supplied)
                    self.assertIs(type(result), set)
                    self.assertFalse(result & trio)
                    self.assertEqual(supplied, raw)
                    for bad in (set(pair), set(raw) - {next(
                            p for p in sorted(raw) if p not in trio)},
                            set(raw) | {"nayeon/unapproved-unknown.py"}):
                        with self.subTest(baseline=baseline, partial=len(bad)):
                            with self.assertRaisesRegex(
                                    AssertionError,
                                    "^Phase10\\.2 partial delta not exact current Git view$"):
                                projection.approved_830_scope(bad)
                untracked = projection._phase10_2_nul_git_paths(
                    "ls-files", "--others", "--exclude-standard",
                    "-z", "--", "nayeon")
                self.assertEqual(untracked, {_p for _p in trio if _p not in pair})
                supplied = set(untracked)
                self.assertEqual(projection.approved_830_scope(supplied), set())
                self.assertEqual(supplied, untracked)
                with self.assertRaisesRegex(
                        AssertionError, "partial delta not exact current Git view"):
                    projection.approved_830_scope(
                        supplied | {"nayeon/unapproved-unknown.py"})
        finally:
            self.assertIn(gate.assert_phase10_2_privacy_integrity(), STATES)

    def test_legacy_delta_adapter_refuses_fake_staged_or_child(self):
        from tests import phase_8_30_scope_migration as projection
        untracked = {"nayeon/perception/permissions.py"}
        original = gate.assert_phase10_2_privacy_integrity
        self.assertIn(original(), STATES)
        for state in ("EXACT_STAGED", "EXACT_CHILD"):
            with self.subTest(state=state), mock.patch.object(
                    gate, "assert_phase10_2_privacy_integrity",
                    return_value=state):
                with self.assertRaisesRegex(
                        AssertionError,
                        "delta exception requires unstaged source"):
                    projection.approved_830_scope(untracked)

    def test_ignored_source_tamper_rejected(self):
        self.assertIn(gate.assert_phase10_2_privacy_integrity(), STATES)
        real = gate._git
        key = ("ls-files", "--others", "--ignored",
               "--exclude-standard", "-z")
        def swapped(*args):
            return b"hidden.py\0" if args == key else real(*args)
        with mock.patch.object(gate, "_git", side_effect=swapped):
            with self.assertRaisesRegex(AssertionError,
                                        "Phase10.2 ignored source present"):
                gate.assert_phase10_2_privacy_integrity()


if __name__ == "__main__":
    unittest.main()
