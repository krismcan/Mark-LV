"""Read-only 16-path admission, history and causal projection adversaries.

Synthetic candidate bytes/pins are confined to explicit fixtures. All immutable
predecessor history/pins and the real admission/checker bodies remain active.
No Git mutation, routing switches or cached approval are used.
"""
from contextlib import contextmanager, ExitStack
import hashlib
from pathlib import Path
import re
import sys
import unittest
from unittest import mock

from tests import phase_8_30_scope_migration as prior
from tests import phase_8_31_scope_migration as old
from tests import phase_8_32_scope_migration as legacy
from tests import phase_8_33_scope_migration as scope
from tests.test_phase_832_scope_integrity import tree_bytes, index_bytes, raw_delta, raw_blob_oid

P = "nayeon/desktop_alpha/offline_completion_admission.py"
ADDED = frozenset({
    "docs/phase_8_33_offline_delayed_completion_rfc.md",
    "docs/phase_8_33_offline_delayed_completion_review.md",
    "nayeon/desktop_alpha/offline_completion_admission.py",
    "tests/test_phase_833_offline_completion.py",
    "tests/test_phase_833_tk_completion.py",
    "tests/phase_8_33_scope_migration.py",
    "tests/test_phase_833_scope_integrity.py",
})
MODIFIED = frozenset({
    "nayeon/desktop_alpha/application.py", "nayeon/desktop_alpha/workspace_window.py",
    "tests/phase_8_32_scope_migration.py", "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_830_scope_integrity.py", "tests/test_phase_831_scope_integrity.py",
    "tests/phase_8_30_scope_migration.py", ".codex/CURRENT_STATE.md",
    "docs/pre_829_shutdown_ownership_failure_ledger.md",
})
STATES = ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD")
SELF_PATTERN = re.compile(rb'("tests/phase_8_33_scope_migration.py": ")[0-9a-f]{64}(",)')


@contextmanager
def candidate(state="COMPLETE_UNSTAGED", *, transform=None, stage_paths=None,
              disk_mutation=None, parent=None, merge=False, index_mutation=None):
    """Real immutable Git histories; synthetic current bytes, index and delta.

    Setup reads occur BEFORE injection/call counting. Historical second-tree
    attacks still hit exactly the second ls-tree in the actual admission body.
    """
    actual_git = prior._git
    baseline = scope._tree(scope.PROTECTED)
    data = {p: ("# 833 synthetic candidate " + p + "\n").encode() for p in ADDED | MODIFIED}
    data[scope.SELF] = b'{"tests/phase_8_33_scope_migration.py": "' + b"0" * 64 + b'",}\n'
    if state == "LEGACY":
        data.update({p: actual_git("show", scope.PROTECTED + ":" + p) for p in MODIFIED})
    pins = {p: scope._digest(p, b) for p, b in data.items()}
    accepted = {**baseline, **{p: ("100644", raw_blob_oid(b)) for p, b in data.items()}}
    child = "e" * 40
    head = child if state == "EXACT_CHILD" else scope.PROTECTED
    committed = dict(accepted if state == "EXACT_CHILD" else baseline)
    index = dict(accepted if state in {"EXACT_STAGED", "EXACT_CHILD"} else baseline)
    if stage_paths is not None:
        index = {**baseline, **{p: accepted[p] for p in stage_paths}}
    if index_mutation:
        index_mutation(index)
    untracked = set() if state == "LEGACY" else ADDED - set(index)
    working = MODIFIED if state == "COMPLETE_UNSTAGED" else set()
    calls, reads = [], []

    def git(*args):
        calls.append(args)
        if args == ("rev-parse", "HEAD"):
            value = (head + "\n").encode()
        elif args == ("branch", "--show-current"):
            value = b"nayeon-v1\n"
        elif args[:2] == ("merge-base", "--is-ancestor"):
            value = b""
        elif args == ("rev-list", "--parents", "-n", "1", child):
            value = (child + " " + (parent or scope.PROTECTED) +
                     (" " + "d" * 40 if merge else "") + "\n").encode()
        elif args == ("ls-tree", "-r", "-z", "--full-tree", child):
            value = tree_bytes(committed)
        elif args == ("ls-files", "--stage", "-z"):
            value = index_bytes(index)
        elif args == ("ls-files", "-v", "--sparse", "-z"):
            value = b"".join(b"H " + p.encode() + b"\0" for p in sorted(index))
        elif args == ("ls-files", "--others", "--exclude-standard", "-z"):
            value = b"".join(p.encode() + b"\0" for p in sorted(untracked))
        elif args == ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
            value = b"tests/__pycache__/synthetic.cpython-312.pyc\0"
        elif args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z"):
            disk = {**index, **{p: ("100644", "0" * 40) for p in working}}
            value = raw_delta(index, disk, working)
        elif args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z", "--cached"):
            changed = {p for p in set(index) | set(committed) if index.get(p) != committed.get(p)}
            value = raw_delta(committed, index, changed)
        elif args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z", scope.PROTECTED, child):
            value = raw_delta(baseline, committed, ADDED | MODIFIED)
        else:
            value = actual_git(*args)
        return transform(args, value, calls) if transform else value

    def disk(path):
        reads.append(path)
        value = data[path]
        return disk_mutation(path, value) if disk_mutation else value

    with ExitStack() as guards:
        # Explicit synthetic 8.33 topology: execute the original private guard,
        # including history, pins, raw inventories and causal failure seams.
        # Public production callers never select this test-owned route.
        guards.enter_context(mock.patch.object(scope, "assert_833_integrity",
                            side_effect=scope._assert_833_historical))
        guards.enter_context(mock.patch.object(prior, "_git", side_effect=git))
        guards.enter_context(mock.patch.object(scope, "_disk", side_effect=disk))
        guards.enter_context(mock.patch.object(scope, "CANDIDATE_SHA256", pins))
        if state == "LEGACY":
            exists = Path.exists
            guards.enter_context(mock.patch.object(Path, "exists", lambda path:
                False if path in {scope.ROOT / p for p in ADDED} else exists(path)))
        yield calls, reads


class Phase833CandidateTests(unittest.TestCase):
    def test_literal_inventory_parent_and_seal_are_independent(self):
        self.assertEqual(scope.ADDED, ADDED)
        self.assertEqual(scope.MODIFIED, MODIFIED)
        self.assertEqual(len(scope.ENVELOPE), 16)
        self.assertEqual(scope.PROTECTED, "03f247d8627bf1c51105f73b9de5c6bbdf389cf9")
        self.assertEqual(scope.PROTECTED_TREE, "4caa8a65b22041b6e1abc2fdf4d249d181082431")
        self.assertEqual(scope.PROTECTED_TAG, "nayeon-v1-phase-8-32-lifecycle-assurance-01")
        self.assertEqual(scope.PROTECTED_TAG_OBJECT, "9fb0f2da5d0e3666fad0c1534fe80fc3b6086c34")

    def test_real_candidate_exact_bytes_and_live_predecessor_route(self):
        from tests import phase_8_34_scope_migration as successor
        from tests import phase_8_36_scope_migration as latest
        state = latest.assert_836_integrity()
        self.assertIn(state, STATES)
        self.assertEqual(scope.assert_833_integrity(), state)
        self.assertEqual(set(scope.CANDIDATE_SHA256), ADDED | MODIFIED)
        # Historical 8.33 literal pins bind the immutable seal, never today's
        # intentionally modified 8.34 files. Raw full-tree/OID proof is retained.
        sealed = successor._tree(successor.PROTECTED)
        for path in sorted(ADDED | MODIFIED):
            data = prior._git("show", successor.PROTECTED + ":" + path)
            self.assertEqual(scope._digest(path, data), scope.CANDIDATE_SHA256[path], path)
            self.assertEqual(sealed[path], ("100644", raw_blob_oid(data)))
        reached = []
        actual = successor._raw_frozen_disk
        target = "nayeon/desktop_alpha/conversation_session.py"
        def read(path):
            reached.append(path)
            return actual(path)
        with mock.patch.object(successor, "_raw_frozen_disk", side_effect=read):
            old.assert_831_integrity()
        self.assertEqual(reached.count(target), 1)

    def test_all_three_complete_controls_reach_current_pin_reads(self):
        for state in STATES:
            with self.subTest(state=state), candidate(state) as (calls, reads):
                self.assertEqual(scope.assert_833_integrity(), state)
                self.assertEqual(set(reads), ADDED | MODIFIED)
                self.assertEqual(len(reads), 16)
                self.assertIn(("ls-files", "--stage", "-z"), calls)

    def test_successor_proof_never_enters_predecessor_admission_or_projection(self):
        with candidate("EXACT_CHILD"), ExitStack() as guards:
            for module, names in ((prior, ("assert_830_integrity", "approved_830_scope",
                    "approved_830_files", "migrated_scope", "_approved_source")),
                    (old, ("assert_831_integrity", "_assert_831_historical_integrity")),
                    (legacy, ("assert_832_integrity", "_assert_832_historical", "current_source_oid"))):
                for name in names:
                    guards.enter_context(mock.patch.object(module, name,
                        side_effect=AssertionError("Recursive predecessor admission")))
            self.assertEqual(scope.assert_833_integrity(), "EXACT_CHILD")

    def test_clean_legacy_h_preserves_guard_but_cannot_project_new_source(self):
        with candidate("LEGACY"):
            self.assertEqual(scope.assert_833_integrity(), "LEGACY")
            for adapter in (prior.approved_830_scope, prior.approved_830_files):
                with self.assertRaisesRegex(AssertionError, "^Unadmitted 8.33 production projection$"):
                    adapter({P})

    def test_every_partial_index_and_nearly_complete_index_refused(self):
        for path in ADDED | MODIFIED:
            for paths in ({path}, (ADDED | MODIFIED) - {path}):
                with self.subTest(path=path, count=len(paths)), candidate(stage_paths=paths):
                    with self.assertRaisesRegex(AssertionError, "^Partial 8.33 staged snapshot refused$"):
                        scope.assert_833_integrity()

    def test_stale_each_candidate_pin_and_disk_mutation_after_positive(self):
        with candidate():
            self.assertEqual(scope.assert_833_integrity(), "COMPLETE_UNSTAGED")
        for path in ADDED | MODIFIED:
            with self.subTest(path=path), candidate() as (_, reads):
                with mock.patch.dict(scope.CANDIDATE_SHA256, {path: "1" * 64}):
                    with self.assertRaisesRegex(AssertionError,
                            "^PARTIAL or unapproved 8.33 candidate bytes: " + re.escape(path) + "$"):
                        scope.assert_833_integrity()
                self.assertIn(path, reads)
            reached = []
            def mutate(p, data):
                if p == path:
                    reached.append(p)
                    return data + b"# tamper\n"
                return data
            with candidate(disk_mutation=mutate):
                with self.assertRaisesRegex(AssertionError, "^PARTIAL or unapproved 8.33 candidate bytes: " + re.escape(path) + "$"):
                    scope.assert_833_integrity()
            self.assertEqual(reached, [path])

    def test_zero_unknown_and_missing_pin_fail_closed(self):
        for value in ("0" * 64, "F" * 64, None, "short"):
            with self.subTest(value=value), candidate():
                with mock.patch.dict(scope.CANDIDATE_SHA256, {P: value}):
                    with self.assertRaisesRegex(AssertionError, "^Unfinalised 8.33 candidate pins$"):
                        scope.assert_833_integrity()
        with candidate():
            del scope.CANDIDATE_SHA256[P]
            with self.assertRaisesRegex(AssertionError, "^Incomplete 8.33 pin manifest$"):
                scope.assert_833_integrity()

    def test_missing_context_and_new_source_are_not_waived(self):
        for path in (".codex/CURRENT_STATE.md", P):
            reached = []
            def missing(p, data):
                if p == path:
                    reached.append(p)
                    raise AssertionError("Missing 8.33 candidate")
                return data
            with self.subTest(path=path), candidate(disk_mutation=missing):
                with self.assertRaisesRegex(AssertionError, "^Missing 8.33 candidate$"):
                    scope.assert_833_integrity()
            self.assertEqual(reached, [path])

    def test_missing_frozen_owner_uses_actual_live_reader(self):
        target = "nayeon/desktop_alpha/conversation_session.py"
        with candidate():
            self.assertEqual(scope.assert_833_integrity(), "COMPLETE_UNSTAGED")
        reached = []
        actual = scope._raw_frozen_disk
        def missing(path):
            if path == target:
                reached.append(path)
                raise AssertionError("Missing 8.33 frozen file")
            return actual(path)
        with candidate(), mock.patch.object(scope, "_raw_frozen_disk", side_effect=missing):
            with self.assertRaisesRegex(AssertionError, "^Missing 8.33 frozen file$"):
                prior.assert_830_integrity()
        self.assertEqual(reached, [target])

    def test_index_source_disagreement_causal_after_complete_positive(self):
        for state, error in (("EXACT_STAGED", "8.33 index/disk disagreement"),
                             ("EXACT_CHILD", "Partial 8.33 staged snapshot refused")):
            with candidate(state):
                self.assertEqual(scope.assert_833_integrity(), state)
            reached = []
            def mutate(index):
                reached.append(P)
                index[P] = ("100644", "1" * 40)
            with self.subTest(state=state), candidate(state, index_mutation=mutate):
                with self.assertRaisesRegex(AssertionError, "^" + error + "$"):
                    scope.assert_833_integrity()
            self.assertEqual(reached, [P])

    def test_wrong_parent_merge_and_descendant_refused(self):
        for kwargs in ({"parent": "a" * 40}, {"merge": True}):
            with candidate("EXACT_CHILD", **kwargs):
                with self.assertRaisesRegex(AssertionError, "^8.33 wrong immediate product parent$"):
                    scope.assert_833_integrity()

    def test_unapproved_committed_source_after_clean_child_is_reached_and_refused(self):
        with candidate("EXACT_CHILD"):
            self.assertEqual(scope.assert_833_integrity(), "EXACT_CHILD")
        wanted = ("ls-tree", "-r", "-z", "--full-tree", "e" * 40)
        reached = []
        def inject(args, data, calls):
            if args == wanted:
                reached.append(args)
                return data + b"100644 blob " + b"1" * 40 + b"\tnayeon/foreign.py\0"
            return data
        with candidate("EXACT_CHILD", transform=inject):
            with self.assertRaisesRegex(AssertionError, "^Unauthorized committed 8.33 scope$"):
                scope.assert_833_integrity()
        self.assertEqual(reached, [wanted])

    def test_historical_second_tree_attack_has_positive_and_exact_reach(self):
        with candidate():
            self.assertEqual(scope.assert_833_integrity(), "COMPLETE_UNSTAGED")
        reached = []
        def inject(args, data, calls):
            if args[0] == "ls-tree" and sum(c[0] == "ls-tree" for c in calls) == 2:
                reached.append(args[-1])
                return data + b"100644 blob " + b"1" * 40 + b"\tnayeon/foreign.py\0"
            return data
        with candidate(transform=inject) as (calls, _):
            with self.assertRaisesRegex(AssertionError, "^Missing or unapproved committed 8.30 source$"):
                prior.assert_830_integrity()
        self.assertEqual(reached, [old.PRODUCT_830])
        self.assertEqual(sum(c[0] == "ls-tree" for c in calls), 2)

    def test_history_pin_and_new_seal_corruption_reached_without_prior_failure(self):
        with candidate():
            self.assertEqual(scope.assert_833_integrity(), "COMPLETE_UNSTAGED")
        path = "nayeon/desktop_alpha/application.py"
        for module, name, message in ((prior, "APPROVED_SOURCE_SHA256", "Unapproved 8.30 source bytes"),
                                      (old, "ALL_831", "Unapproved 8.31 source bytes"),
                                      (legacy, "CANDIDATE_SHA256", "Unapproved sealed 8.32 bytes")):
            reached = []
            def observe(args, data, calls):
                if args[0] == "show" and args[1].endswith(":" + path):
                    reached.append(args[1])
                return data
            with candidate(transform=observe), mock.patch.dict(getattr(module, name), {path: "1" * 64}):
                with self.assertRaisesRegex(AssertionError, "^" + message + "$"):
                    scope.assert_833_integrity()
            self.assertTrue(reached)
        wanted = ("show-ref", "--verify", "--hash", "--", "refs/tags/" + scope.PROTECTED_TAG)
        reached = []
        def seal(args, data, calls):
            if args == wanted:
                reached.append(args)
                return b"1" * 40 + b"\n"
            return data
        with candidate(transform=seal):
            with self.assertRaisesRegex(AssertionError, "^Frozen seal changed$"):
                scope.assert_833_integrity()
        self.assertEqual(reached, [wanted])

    def test_unauthorized_source_inventory_and_index_flags_reached(self):
        cases = (
            (("ls-files", "--others", "--exclude-standard", "-z"),
             lambda b: b + b"nayeon/foreign.py\0", "Unauthorized untracked 8.33 path"),
            (("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
             lambda b: b + b"nayeon/hidden.py\0", "Ignored 8.33 source refused"),
            (("ls-files", "--stage", "-z"),
             lambda b: b + b"100644 " + b"1" * 40 + b" 0\tnayeon/foreign.py\0",
             "Incomplete 8.33 index flags"),
            (("ls-files", "-v", "--sparse", "-z"),
             lambda b: b.replace(b"H ", b"h ", 1), "Unsupported 8.33 index flags"),
        )
        for wanted, mutate, error in cases:
            with candidate():
                self.assertEqual(scope.assert_833_integrity(), "COMPLETE_UNSTAGED")
            reached = []
            def inject(args, data, calls):
                if args == wanted:
                    reached.append(args)
                    return mutate(data)
                return data
            with self.subTest(query=wanted), candidate(transform=inject):
                with self.assertRaisesRegex(AssertionError, "^" + error + "$"):
                    scope.assert_833_integrity()
            self.assertEqual(reached, [wanted])

    def test_raw_inventory_alias_mode_unmerged_and_duplicate_records(self):
        records = (
            b"100644 blob BAD\tREADME.md\0", b"040000 tree " + b"1" * 40 + b"\tforeign\0",
            b"100644 blob " + b"1" * 40 + b"\tTests/foreign.py\0",
            b"100644 blob " + b"1" * 40 + b"\tnayeon./foreign.py\0",
            b"100644 blob " + b"1" * 40 + b"\ttests/a/../b.py\0",
            b"100644 blob " + b"1" * 40 + b"\tdocs/x.\0",
        )
        for record in records:
            with self.subTest(record=record), self.assertRaises(AssertionError):
                scope._inventory(record)
        normal = b"100644 blob " + b"1" * 40 + b"\ttests/a.py\0"
        with self.assertRaisesRegex(AssertionError, "Repeated or aliased"):
            scope._inventory(normal + normal)
        with self.assertRaisesRegex(AssertionError, "Repeated or aliased"):
            scope._inventory(normal + normal.replace(b"a.py", b"A.py"))
        for record in (b"100644 " + b"1" * 40 + b" 1\ttests/a.py\0", normal[:-1]):
            with self.assertRaisesRegex(AssertionError, "Malformed 8.33 Git inventory"):
                scope._inventory(record, index=True)

    def test_aliases_rejected_at_each_live_raw_surface_with_reach(self):
        queries = (("ls-files", "--stage", "-z"),
                   ("ls-files", "--others", "--exclude-standard", "-z"),
                   ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
                   ("ls-tree", "-r", "-z", "--full-tree", scope.PROTECTED))
        for wanted in queries:
            for alias in ("NAYEON/foreign.py", "tests/x.py:ads", "Docs/x.md", "tests/x.py."):
                reached = []
                def inject(args, data, calls):
                    if args == wanted:
                        reached.append(args)
                        name = alias.encode() + b"\0"
                        if args[0] == "ls-tree":
                            name = b"100644 blob " + b"1" * 40 + b"\t" + name
                        elif "--stage" in args:
                            name = b"100644 " + b"1" * 40 + b" 0\t" + name
                        return data + name
                    return data
                with self.subTest(query=wanted, alias=alias), candidate(transform=inject):
                    with self.assertRaisesRegex(AssertionError, "Aliased|Noncanonical"):
                        scope.assert_833_integrity()
                self.assertEqual(reached, [wanted])

    def test_raw_delta_status_modes_blobs_and_unauthorized_worktree_are_reached(self):
        base_query = ("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
        attacks = (
            ("EXACT_STAGED", base_query + ("--cached",),
             lambda data: data.replace(b"100644", b"120000", 1), "Wrong 8.33 raw status/mode/blob"),
            ("EXACT_CHILD", base_query + (scope.PROTECTED, "e" * 40),
             lambda data: data.replace(b" A\0", b" R\0", 1), "Wrong 8.33 raw status/mode/blob"),
            ("COMPLETE_UNSTAGED", base_query,
             lambda data: data + b":100644 100644 " + b"1" * 40 + b" " + b"0" * 40 + b" M\0tests/foreign.py\0",
             "Unauthorized 8.33 worktree delta"),
            ("COMPLETE_UNSTAGED", base_query,
             lambda data: data.replace(b" M\0", b" D\0", 1), "Wrong 8.33 worktree status/mode/blob"),
        )
        for state, wanted, mutate, message in attacks:
            with candidate(state):
                self.assertEqual(scope.assert_833_integrity(), state)
            reached = []
            def inject(args, data, calls):
                if args == wanted:
                    reached.append(args)
                    return mutate(data)
                return data
            with self.subTest(state=state, query=wanted), candidate(state, transform=inject):
                with self.assertRaisesRegex(AssertionError, "^" + message + "$"):
                    scope.assert_833_integrity()
            self.assertEqual(reached, [wanted])

    def test_candidate_readers_reject_links_modes_and_missing_without_writing(self):
        real_lstat = Path.lstat
        path = P
        for reader in (scope._disk, scope._raw_frozen_disk):
            for change in ({"st_nlink": 2}, {"st_mode": 0o120777}, {"st_file_attributes": 0x400}):
                info = real_lstat(scope.ROOT / path)
                fake = mock.Mock(st_mode=info.st_mode, st_nlink=1, st_file_attributes=0)
                for key, value in change.items():
                    setattr(fake, key, value)
                with (mock.patch.object(prior, "_reject_linked_parents"),
                      mock.patch.object(Path, "lstat", return_value=fake) as reached):
                    with self.assertRaisesRegex(AssertionError, "^Linked or nonregular 8.33"):
                        reader(path)
                    reached.assert_called_once_with()
            with mock.patch.object(Path, "read_bytes", side_effect=FileNotFoundError):
                with self.assertRaisesRegex(AssertionError, "^Missing 8.33"):
                    reader(path)


class Phase833ProjectionTests(unittest.TestCase):
    def adapters(self):
        return (prior.approved_830_scope, prior.approved_830_files)

    def test_complete_topologies_remove_only_exact_new_path_and_leave_input(self):
        unrelated = {"nayeon/unrelated.py", P + ".bak", P.upper()}
        original = unrelated | {P, "nayeon/desktop_alpha/conversation_session.py"} | set(prior.APPROVED_NEW_SHA256)
        for state in STATES:
            for adapter in self.adapters():
                actual = set(original)
                with self.subTest(state=state, adapter=adapter.__name__), candidate(state):
                    self.assertEqual(adapter(actual), unrelated)
                self.assertEqual(actual, original)

    def test_actual_adapter_routes_bounded_double_successor_and_migrated_composition(self):
        for state in STATES:
            for adapter in self.adapters():
                with candidate(state), mock.patch.object(scope, "assert_833_integrity",
                        wraps=scope.assert_833_integrity) as guard:
                    self.assertEqual(adapter({P, "nayeon/unrelated.py"}), {"nayeon/unrelated.py"})
                    self.assertEqual(guard.call_count, 2)
            with candidate(state), mock.patch.object(prior, "_phase829_migrated_scope",
                    wraps=prior._phase829_migrated_scope) as older:
                actual = {P, "nayeon/unrelated.py"}
                prior.migrated_scope(actual, include_onboarding=True)
                older.assert_called_once_with({"nayeon/unrelated.py"}, include_onboarding=True)
                self.assertEqual(actual, {P, "nayeon/unrelated.py"})

    def test_invalid_inputs_rejected_before_either_admission(self):
        class SetSubclass(set):
            pass
        class StrSubclass(str):
            pass
        for adapter in self.adapters():
            for value in (None, [P], frozenset({P}), SetSubclass({P}), {1}, {StrSubclass(P)}):
                with mock.patch.object(prior, "assert_830_integrity") as old_guard, mock.patch.object(
                        scope, "assert_833_integrity") as new_guard:
                    with self.subTest(adapter=adapter.__name__, value=type(value)), self.assertRaises(AssertionError):
                        adapter(value)
                    old_guard.assert_not_called()
                    new_guard.assert_not_called()

    def test_legacy_unknown_exceptions_and_import_failure_never_authorize(self):
        for adapter in self.adapters():
            for value in ("LEGACY", "UNKNOWN", None, True, [], {"EXACT_CHILD"}):
                with mock.patch.object(prior, "assert_830_integrity") as previous, mock.patch.object(
                        scope, "assert_833_integrity", return_value=value) as successor:
                    with self.assertRaisesRegex(AssertionError, "^Unadmitted 8.33 production projection$"):
                        adapter({P})
                    previous.assert_called_once_with()
                    successor.assert_called_once_with()
            for error in (AssertionError("pin failure"), ImportError("missing successor"), RuntimeError("read failed")):
                with mock.patch.object(prior, "assert_830_integrity"), mock.patch.object(
                        scope, "assert_833_integrity", side_effect=error):
                    with self.assertRaises(type(error)) as caught:
                        adapter({P})
                    self.assertIs(caught.exception, error)
            with mock.patch.object(prior, "assert_830_integrity"), mock.patch.dict(
                    sys.modules, {"tests.phase_8_33_scope_migration": None}):
                with self.assertRaises(ImportError):
                    adapter({P})

    def test_absent_new_path_preserves_legacy_projection_without_successor_import(self):
        original = {"nayeon/frozen.py", P + ".bak", "nayeon/desktop_alpha/conversation_session.py"} | set(prior.APPROVED_NEW_SHA256)
        expected = {"nayeon/frozen.py", P + ".bak"}
        for adapter in self.adapters():
            with mock.patch.object(prior, "assert_830_integrity") as guard, mock.patch.dict(
                    sys.modules, {"tests.phase_8_33_scope_migration": None}):
                self.assertEqual(adapter(set(original)), expected)
                guard.assert_called_once_with()

    def test_predecessor_failure_propagates_before_new_projection(self):
        for adapter in self.adapters():
            with mock.patch.object(prior, "assert_830_integrity", side_effect=AssertionError("old refusal")), mock.patch.object(
                    scope, "assert_833_integrity") as successor:
                with self.assertRaisesRegex(AssertionError, "^old refusal$"):
                    adapter({P})
                successor.assert_not_called()
