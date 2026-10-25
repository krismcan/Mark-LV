"""Exact 8.37 admission adversaries; read-only Git, synthetic current snapshots.

Immutable historical bytes/seals remain real. Fixtures never stage, commit,
write files, waive pins, or turn a failed admission into a successful result.
"""
from contextlib import contextmanager, ExitStack
import hashlib
from pathlib import Path
import re
import stat
import unittest
from unittest import mock

from tests import phase_8_37_scope_migration as scope
from tests.test_phase_836_scope_integrity import sealed_836_bytes

ADDED = frozenset({
    "nayeon/desktop_alpha/offline_request_draft.py",
    "nayeon/desktop_alpha/offline_draft_consent.py",
    "tests/test_phase_837_offline_request_draft.py",
    "tests/test_phase_837_draft_consent.py",
    "tests/test_phase_837_draft_tk.py",
    "tests/test_phase_837_draft_application.py",
    "tests/phase_8_37_scope_migration.py",
    "tests/test_phase_837_scope_integrity.py",
    "docs/phase_8_37_provider_request_draft_rfc.md",
})
MODIFIED = frozenset({
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "tests/phase_8_36_scope_migration.py",
    "tests/test_phase_836_scope_integrity.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/test_phase_830_scope_integrity.py",
    "tests/test_phase_831_scope_integrity.py",
    "tests/test_pre_829_a02_fake_isolation.py",
    "tests/test_phase_834_scope_integrity.py",
    "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_833_scope_integrity.py",
})
STATES = ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD")
RAW = ("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
CHILD = "e" * 40


def tree_bytes(entries, *, index=False):
    return b"".join((f"{mode} {oid} 0\t{p}" if index else
                     f"{mode} blob {oid}\t{p}").encode() + b"\0"
                    for p, (mode, oid) in sorted(entries.items()))


def raw_delta(before, after, paths):
    rows = []
    for p in sorted(paths):
        old = before.get(p, ("000000", "0" * 40))
        new = after.get(p, ("000000", "0" * 40))
        status = "A" if p not in before else "D" if p not in after else "M"
        rows.append(f":{old[0]} {new[0]} {old[1]} {new[1]} {status}".encode()
                    + b"\0" + p.encode() + b"\0")
    return b"".join(rows)


@contextmanager
def candidate(state="COMPLETE_UNSTAGED", *, transform=None, stage_paths=None,
              index_mutation=None, committed_mutation=None, parent=None,
              merge=False, disk_mutation=None):
    """Real frozen history, independent synthetic current bytes and Git reads.

    Transform runs after each query, including each repeated read. Synthetic
    pins apply only to current bytes; all 19 frozen 8.36 pins stay untouched.
    """
    actual = scope._git
    baseline = scope._tree(scope.PROTECTED)
    data = {p: ("# synthetic 837 " + p + "\n").encode() for p in ADDED | MODIFIED}
    data[scope.SELF] = b'{"tests/phase_8_37_scope_migration.py": "' + b"0" * 64 + b'",}\n'
    pins = {p: scope._digest(p, b) for p, b in data.items()}
    accepted = {**baseline, **{p: ("100644", scope._blob(b)) for p, b in data.items()}}
    head = CHILD if state == "EXACT_CHILD" else scope.PROTECTED
    committed = dict(accepted if state == "EXACT_CHILD" else baseline)
    index = dict(accepted if state != "COMPLETE_UNSTAGED" else baseline)
    if stage_paths is not None:
        index = {**baseline, **{p: accepted[p] for p in stage_paths}}
    if index_mutation:
        index_mutation(index)
    if committed_mutation:
        committed_mutation(committed)
    untracked = ADDED - set(index)
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
        elif args == ("rev-list", "--parents", "-n", "1", CHILD):
            value = (CHILD + " " + (parent or scope.PROTECTED)
                     + (" " + "d" * 40 if merge else "") + "\n").encode()
        elif args == ("ls-tree", "-r", "-z", "--full-tree", CHILD):
            value = tree_bytes(committed)
        elif args == ("ls-files", "--stage", "-z"):
            value = tree_bytes(index, index=True)
        elif args == ("ls-files", "-v", "--sparse", "-z"):
            value = b"".join(b"H " + p.encode() + b"\0" for p in sorted(index))
        elif args == ("ls-files", "--others", "--exclude-standard", "-z"):
            value = b"".join(p.encode() + b"\0" for p in sorted(untracked))
        elif args == ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
            value = b""
        elif args == RAW:
            disk = {**index, **{p: ("100644", "0" * 40) for p in working}}
            value = raw_delta(index, disk, working)
        elif args == RAW + ("--cached",):
            changed = {p for p in set(index) | set(committed) if index.get(p) != committed.get(p)}
            value = raw_delta(committed, index, changed)
        elif args == RAW + (scope.PROTECTED, CHILD):
            value = raw_delta(baseline, committed, ADDED | MODIFIED)
        else:
            value = actual(*args)
        return transform(args, value, calls) if transform else value

    def disk(path):
        reads.append(path)
        value = data[path]
        return disk_mutation(path, value) if disk_mutation else value

    with ExitStack() as stack:
        stack.enter_context(mock.patch.object(scope, "_git", side_effect=git))
        stack.enter_context(mock.patch.object(scope, "_disk", side_effect=disk))
        stack.enter_context(mock.patch.object(scope, "_frozen", side_effect=sealed_836_bytes))
        stack.enter_context(mock.patch.object(scope, "CANDIDATE_SHA256", pins))
        # This exact synthetic 8.37 fixture proves the original historical
        # body, not the live current BYOK descendant. No production fallback.
        stack.enter_context(mock.patch.object(
            scope, "assert_837_integrity", scope._assert_837_historical))
        yield calls, reads


class Phase837IntegrityTests(unittest.TestCase):
    def test_exact_manifest_and_live_topology(self):
        self.assertEqual(scope.ADDED, ADDED)
        self.assertEqual(scope.MODIFIED, MODIFIED)
        self.assertEqual(scope.ENVELOPE, ADDED | MODIFIED)
        self.assertEqual(len(scope.ENVELOPE), 20)
        self.assertTrue(ADDED.isdisjoint(MODIFIED))
        self.assertEqual(set(scope.CANDIDATE_SHA256), ADDED | MODIFIED)
        self.assertEqual(scope.PROTECTED, "a12565b9be070684e1d7d801ded4833d13121f94")
        self.assertEqual(scope.PROTECTED_TREE, "f2d35fef90add1bb3b14ab9a1b26b0235334bfbb")
        self.assertEqual(scope.PROTECTED_TAG, "nayeon-v1-phase-8-36-offline-request-review-01")
        self.assertEqual(scope.PROTECTED_TAG_OBJECT, "aca0de5a873cf41454fe1fa144d12f34d44418a4")
        for pin in scope.CANDIDATE_SHA256.values():
            self.assertRegex(pin, r"^[0-9a-f]{64}$")
            self.assertNotEqual(pin, "0" * 64)
        # The live current acceptance is the NEW exact BYOK successor;
        # all historical synthetic negative fixtures use the frozen body.
        from tests.phase8_byok_scope_migration import assert_byok_integrity, PARENT
        current = assert_byok_integrity()
        self.assertIn(current, STATES)
        head = scope._git("rev-parse", "HEAD").decode().strip()
        self.assertEqual(head, PARENT if current != "EXACT_CHILD" else head)

    def test_a02_isolated_child_uses_minus_b_and_leaves_no_ignored_cache(self):
        # Exercise the original A-02 test's REAL subprocess and bind its flags.
        # A bare -I ignores PYTHONDONTWRITEBYTECODE and PYCACHEPREFIX env vars.
        import subprocess
        from tests.test_pre_829_a02_fake_isolation import FakeOnlyCompositionTests
        case = FakeOnlyCompositionTests(
            "test_guarded_fresh_subprocess_import_and_factory_no_external_io")
        with mock.patch.object(subprocess, "run", wraps=subprocess.run) as child:
            result = unittest.TestResult()
            case.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)
        self.assertEqual(child.call_count, 1)
        self.assertEqual(child.call_args.args[0][1:4], ["-I", "-B", "-c"])
        self.assertEqual(
            scope._git("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
            b"", "Isolated A-02 child generated ignored executable bytecode")

    def test_all_three_topologies_prove_full_admission(self):
        for state in STATES:
            with self.subTest(state=state), candidate(state) as (calls, reads):
                self.assertEqual(scope.assert_837_integrity(), state)
                self.assertEqual(set(reads), ADDED | MODIFIED)
                if state == "EXACT_STAGED":
                    self.assertIn(RAW + ("--cached",), calls)
                elif state == "EXACT_CHILD":
                    self.assertIn(RAW + (scope.PROTECTED, CHILD), calls)

    def test_original_836_body_is_byte_identical_and_routes_unconditionally(self):
        original = sealed_836_bytes("tests/phase_8_36_scope_migration.py")
        current = (scope.ROOT / "tests/phase_8_36_scope_migration.py").read_bytes()
        self.assertEqual(current[:len(original)], original)
        self.assertIsNot(scope.prior.assert_836_integrity, scope.prior._assert_836_historical)
        with mock.patch.object(scope, "assert_837_integrity",
                               side_effect=AssertionError("successor refused")) as reached:
            with self.assertRaisesRegex(AssertionError, "^successor refused$"):
                scope.prior.assert_836_integrity()
            reached.assert_called_once_with()
        for state in STATES:
            with self.subTest(state=state), candidate(state):
                self.assertEqual(scope.prior.assert_836_integrity(), state)
                self.assertEqual(scope.canonical.assert_834_integrity(), state)

    def test_wrong_branch_format_and_head_refuse_before_seal(self):
        for query, value, message in (
            (("branch", "--show-current"), b"other\n", "Wrong 8.37 product branch"),
            (("branch", "--show-current"), b"\n", "Wrong 8.37 product branch"),
            (("rev-parse", "--show-object-format"), b"sha256\n", "Unsupported 8.37 Git object format"),
            (("rev-parse", "HEAD"), b"short\n", "Invalid 8.37 HEAD"),
        ):
            def inject(args, data, calls):
                return value if args == query else data
            with self.subTest(query=query, value=value), candidate(transform=inject), mock.patch.object(
                    scope, "_seal", side_effect=AssertionError("seal must not run")) as seal:
                with self.assertRaisesRegex(AssertionError, "^" + message + "$"):
                    scope.assert_837_integrity()
                seal.assert_not_called()

    def test_frozen_836_tree_parent_tag_type_and_peel(self):
        for query, value, message in (
            (("rev-parse", scope.PROTECTED + "^{tree}"), b"1" * 40 + b"\n", "8.36 protected tree mismatch"),
            (("rev-list", "--parents", "-n", "1", scope.PROTECTED),
             (scope.PROTECTED + " " + "1" * 40 + "\n").encode(), "8.36 protected parent mismatch"),
            (("show-ref", "--verify", "--hash", "--", "refs/tags/" + scope.PROTECTED_TAG),
             b"1" * 40 + b"\n", "8.36 annotated seal mismatch"),
            (("cat-file", "-t", scope.PROTECTED_TAG_OBJECT), b"commit\n", "8.36 annotated seal mismatch"),
            (("cat-file", "-t", scope.PROTECTED), b"tag\n", "8.36 annotated seal mismatch"),
            (("rev-parse", "--verify", "--end-of-options", scope.PROTECTED_TAG_OBJECT + "^{}"),
             b"1" * 40 + b"\n", "8.36 annotated seal mismatch"),
            (("rev-parse", scope.PROTECTED + "^{tree}"), b"not-an-oid\n", "Malformed 8.37 seal OID"),
        ):
            hit = []
            def inject(args, data, calls):
                if args == query:
                    hit.append(args)
                    return value
                return data
            with self.subTest(query=query), candidate(transform=inject):
                with self.assertRaisesRegex(AssertionError, "^" + re.escape(message) + "$"):
                    scope.assert_837_integrity()
            self.assertEqual(hit, [query])

    def test_every_original_836_pin_is_rechecked_including_normalized_self(self):
        self.assertEqual(len(scope.prior.CANDIDATE_SHA256), 19)
        for path in sorted(scope.prior.CANDIDATE_SHA256):
            query = ("show", scope.PROTECTED + ":" + path)
            hit = []
            def inject(args, data, calls):
                if args == query:
                    hit.append(args)
                    return data + b"tamper"
                return data
            with self.subTest(path=path), candidate(transform=inject):
                with self.assertRaisesRegex(AssertionError, "^Unapproved sealed 8.36 bytes: " + re.escape(path) + "$"):
                    scope.assert_837_integrity()
            self.assertEqual(hit, [query])

    def test_unpinned_current_bytes_and_zero_or_missing_pin_refuse(self):
        target = "nayeon/desktop_alpha/offline_request_draft.py"
        for state in STATES:
            with self.subTest(state=state), candidate(state, disk_mutation=lambda p, b:
                    b + b"tamper" if p == target else b):
                with self.assertRaisesRegex(AssertionError, "Unapproved 8.37 candidate bytes"):
                    scope.assert_837_integrity()
        with candidate(), mock.patch.dict(scope.CANDIDATE_SHA256, {target: "0" * 64}):
            with self.assertRaisesRegex(AssertionError, "Unfinalized 8.37 source pins"):
                scope.assert_837_integrity()
        with candidate():
            del scope.CANDIDATE_SHA256[target]
            with self.assertRaisesRegex(AssertionError, "Unapproved 8.37 file allowlist"):
                scope.assert_837_integrity()

    def test_extra_untracked_and_ignored_loaders_refused_in_every_state(self):
        for state in STATES:
            for ignored in (False, True):
                for path in ("extra.py", "tests/__pycache__/payload.cpython-312.pyc",
                             "sitecustomize.pyd", "sitecustomize.so", "bin/loader.dll"):
                    query = (("ls-files", "--others", "--ignored", "--exclude-standard", "-z")
                             if ignored else ("ls-files", "--others", "--exclude-standard", "-z"))
                    def inject(args, data, calls):
                        return data + path.encode() + b"\0" if args == query else data
                    with self.subTest(state=state, ignored=ignored, path=path), candidate(state, transform=inject):
                        with self.assertRaisesRegex(AssertionError, "Ignored 8.37|Missing or extra untracked|Partial 8.37|Unapproved 8.37 committed/index"):
                            scope.assert_837_integrity()

    def test_partial_stage_wrong_child_parent_merge_and_extra_generation_refuse(self):
        for paths in ({next(iter(ADDED))}, set(MODIFIED), (ADDED | MODIFIED) - {scope.SELF}):
            with self.subTest(paths=paths), candidate(stage_paths=paths):
                with self.assertRaisesRegex(AssertionError, "Partial 8.37 stage refused"):
                    scope.assert_837_integrity()
        for parent, merge in (("d" * 40, False), (scope.PROTECTED, True)):
            with self.subTest(parent=parent, merge=merge), candidate("EXACT_CHILD", parent=parent, merge=merge):
                with self.assertRaisesRegex(AssertionError, "8.37 unexpected product parent"):
                    scope.assert_837_integrity()

    def test_frozen_disk_and_frozen_index_or_commit_are_bound(self):
        target = "nayeon/desktop_alpha/reply_owner.py"
        for state in STATES:
            with self.subTest(state=state), candidate(state), mock.patch.object(scope, "_frozen", side_effect=lambda p:
                    sealed_836_bytes(p) + (b"tamper" if p == target else b"")):
                with self.assertRaisesRegex(AssertionError, "Frozen historical worktree bytes modified"):
                    scope.assert_837_integrity()
        for seam in ("index_mutation", "committed_mutation"):
            def tamper(entries):
                entries[target] = ("100644", "a" * 40)
            with self.subTest(seam=seam), candidate("EXACT_CHILD", **{seam: tamper}):
                with self.assertRaisesRegex(AssertionError, "Frozen 8.37 historical file modified"):
                    scope.assert_837_integrity()

    def test_full_raw_staged_and_committed_delta_status_mode_blob_path_and_count(self):
        for state in ("EXACT_STAGED", "EXACT_CHILD"):
            query = RAW + (("--cached",) if state == "EXACT_STAGED" else (scope.PROTECTED, CHILD))
            for mutation in (
                lambda b: b.replace(b" M\0", b" D\0", 1),
                lambda b: b.replace(b":100644 100644", b":100755 100644", 1),
                lambda b: b.replace(b" 100644 ", b" 100755 ", 1),
                lambda b: b.replace(b" 0000000000000000000000000000000000000000 ", b" " + b"1" * 40 + b" ", 1),
                lambda b: b.replace(b.split(b"\0")[0].split(b" ")[3], b"f" * 40, 1),
                lambda b: b.replace(b"nayeon/desktop_alpha/application.py", b"NAYEON/desktop_alpha/application.py", 1),
                lambda b: b + b.split(b"\0")[0] + b"\0extra.py\0",
                lambda b: b[:-1],
                lambda b: b"",
            ):
                hit = []
                def inject(args, data, calls):
                    if args == query:
                        altered = mutation(data)
                        self.assertNotEqual(altered, data)
                        hit.append(args)
                        return altered
                    return data
                with self.subTest(state=state, mutation=mutation), candidate(state, transform=inject):
                    with self.assertRaises(AssertionError):
                        scope.assert_837_integrity()
                self.assertEqual(hit, [query])

    def test_worktree_raw_delta_and_index_flags_cannot_hide_bytes(self):
        for mutation in (lambda b: b"", lambda b: b.replace(b" M\0", b" D\0", 1),
                         lambda b: b.replace(b" 100644 ", b" 120000 ", 1)):
            def inject(args, data, calls):
                return mutation(data) if args == RAW else data
            with candidate(transform=inject):
                with self.assertRaisesRegex(AssertionError, "8.37 disk delta"):
                    scope.assert_837_integrity()
        query = ("ls-files", "-v", "--sparse", "-z")
        for flag in (b"h ", b"S ", b"s "):
            def inject(args, data, calls):
                return flag + data[2:] if args == query else data
            with self.subTest(flag=flag), candidate(transform=inject):
                with self.assertRaisesRegex(AssertionError, "Unsupported 8.37 index flags"):
                    scope.assert_837_integrity()

    def test_complete_inventory_rejects_alias_symlink_extra_and_unmerged_stage(self):
        for query, suffix, message in (
            (("ls-tree", "-r", "-z", "--full-tree", scope.PROTECTED),
             b"100644 blob " + b"a" * 40 + b"\textra.py\0", "8.36 full inventory mismatch"),
            (("ls-files", "--stage", "-z"),
             b"100644 " + b"a" * 40 + b" 0\tTests/extra.py\0", "Aliased"),
            (("ls-files", "--stage", "-z"),
             b"120000 " + b"a" * 40 + b" 0\tlink\0", "Linked or nonregular"),
            (("ls-files", "--stage", "-z"),
             b"100644 " + b"a" * 40 + b" 2\textra.py\0", "Malformed"),
        ):
            def inject(args, data, calls):
                return data + suffix if args == query else data
            with self.subTest(query=query, suffix=suffix), candidate(transform=inject):
                with self.assertRaisesRegex(AssertionError, message):
                    scope.assert_837_integrity()
        for paths in (("other/A/x", "other/a/y"), ("docs/con.txt",), ("docs/a./x",),
                      ("docs/../x",), ("docs\\x",), ("docs/e\u0301.txt",)):
            with self.subTest(paths=paths), self.assertRaises(AssertionError):
                scope._canonical_paths(paths)

    def test_stale_callback_cannot_reuse_a_previous_successful_admission(self):
        # A callback holding the same checker must obtain fresh evidence each
        # time; an earlier GO cannot authorize later poisoned index/disk data.
        poisoned = [False]
        target = "nayeon/desktop_alpha/offline_request_draft.py"
        with candidate(disk_mutation=lambda p, b:
                b + b"tamper" if poisoned[0] and p == target else b):
            callback = scope.prior.assert_836_integrity
            self.assertEqual(callback(), "COMPLETE_UNSTAGED")
            poisoned[0] = True
            with self.assertRaisesRegex(AssertionError, "Unapproved 8.37 candidate bytes"):
                callback()

    def test_candidate_and_frozen_disk_refuse_links_reparse_and_hardlinks(self):
        path = "tests/test_phase_837_scope_integrity.py"
        target = scope.ROOT / path
        actual = Path.lstat
        for mode, links, attributes in (
                (stat.S_IFLNK, 1, 0), (stat.S_IFDIR, 1, 0),
                (stat.S_IFREG, 2, 0), (stat.S_IFREG, 1, 0x400)):
            info = mock.Mock(st_mode=mode, st_nlink=links, st_file_attributes=attributes)
            def lstat(p):
                return info if p == target else actual(p)
            for reader in (scope._disk, scope._frozen):
                with self.subTest(mode=mode, links=links, attributes=attributes,
                                  reader=reader), mock.patch.object(Path, "lstat", lstat):
                    with self.assertRaisesRegex(AssertionError, "Linked or nonregular"):
                        reader(path)

    def test_self_hash_normalizes_only_own_pin_and_requires_exactly_one(self):
        own = b'"tests/phase_8_37_scope_migration.py": "' + b"1" * 64 + b'",'
        old = b'"tests/phase_8_36_scope_migration.py": "' + b"2" * 64 + b'",'
        data = own + b"\r\n" + old + b"\x00raw\r\n"
        expected = own.replace(b"1" * 64, b"0" * 64) + b"\r\n" + old + b"\x00raw\r\n"
        self.assertEqual(scope._digest(scope.SELF, data), hashlib.sha256(expected).hexdigest())
        for altered in (data + b"x", data.replace(b"2" * 64, b"3" * 64), data.replace(b"\r\n", b"\n")):
            self.assertNotEqual(scope._digest(scope.SELF, data), scope._digest(scope.SELF, altered))
        for malformed in (old, own + own):
            with self.assertRaisesRegex(AssertionError, "Malformed 8.37 self pin"):
                scope._digest(scope.SELF, malformed)
        # Historical raw self-pin is bound to the immutable 8.37 commit,
        # not to the separate appended BYOK public successor adapter.
        live = scope._git("show",
            "87208af710bac90c440f2e0851854318b22e9b88:" + scope.SELF)
        self.assertEqual(scope._digest(scope.SELF, live), scope.CANDIDATE_SHA256[scope.SELF])
        self.assertTrue((scope.ROOT / scope.SELF).read_bytes().startswith(live))


class Phase837LegacyProjectionTests(unittest.TestCase):
    DRAFT_PATHS = {
        "nayeon/desktop_alpha/offline_request_draft.py",
        "nayeon/desktop_alpha/offline_draft_consent.py",
    }

    def projectors(self):
        from tests import phase_8_30_scope_migration as legacy
        return legacy.approved_830_scope, legacy.approved_830_files

    def test_only_exact_draft_paths_project_after_fresh_full_gate(self):
        extras = {p + ".bak" for p in self.DRAFT_PATHS} | {
            "NAYEON/desktop_alpha/offline_request_draft.py",
            "nayeon/desktop_alpha/unreviewed_draft.py",
        }
        # Caller inventories never authorize disk/index additions. Unrelated
        # names and aliases remain visible to each older scope comparison.
        for state in STATES:
            for project in self.projectors():
                with self.subTest(state=state, project=project), candidate(state) as (_, reads):
                    with mock.patch.object(scope, "assert_837_integrity",
                                           wraps=scope.assert_837_integrity) as gate:
                        self.assertEqual(project(self.DRAFT_PATHS | extras), extras)
                    self.assertEqual(gate.call_args_list, [mock.call(), mock.call()])
                    for path in scope.ENVELOPE:
                        self.assertEqual(reads.count(path), 2)

    def test_projection_refuses_unproven_gate_result(self):
        for project in self.projectors():
            for result in (None, True, "COMPLETE_UNSTAGED\n", "UNREVIEWED"):
                with self.subTest(project=project, result=result), mock.patch.object(
                        scope, "assert_837_integrity", return_value=result) as gate:
                    with self.assertRaisesRegex(AssertionError, "^Unadmitted 8.37 production projection$"):
                        project(set(self.DRAFT_PATHS))
                    self.assertEqual(gate.call_args_list, [mock.call(), mock.call()])

    def test_actual_extra_path_and_alias_refuse_before_projection(self):
        query = ("ls-files", "--others", "--exclude-standard", "-z")
        for path, message in (
            ("nayeon/desktop_alpha/offline_request_draft.py.bak",
             "Missing or extra untracked 8.37 paths"),
            ("nayeon/desktop_alpha/unreviewed_draft.py",
             "Missing or extra untracked 8.37 paths"),
            ("NAYEON/desktop_alpha/offline_draft_consent.py", "Aliased production root"),
        ):
            hit = []
            def inject(args, data, calls):
                if args == query:
                    hit.append(args)
                    return data + path.encode() + b"\0"
                return data
            with self.subTest(path=path), candidate(transform=inject):
                with self.assertRaisesRegex(AssertionError, "^" + message + "$"):
                    self.projectors()[0](set(self.DRAFT_PATHS))
            self.assertEqual(hit, [query])

    def test_changed_draft_and_modified_entrypoint_bytes_refuse_projection(self):
        for target in sorted(self.DRAFT_PATHS | {
                "nayeon/desktop_alpha/application.py",
                "nayeon/desktop_alpha/workspace_window.py"}):
            hit = []
            def tamper(path, data):
                if path == target:
                    hit.append(path)
                    return data + b"tamper"
                return data
            with self.subTest(target=target), candidate(disk_mutation=tamper):
                with self.assertRaisesRegex(AssertionError,
                        "^Unapproved 8.37 candidate bytes: " + re.escape(target) + "$"):
                    self.projectors()[1](set(self.DRAFT_PATHS))
            self.assertEqual(hit, [target])

    def test_wrong_branch_refuses_projection_at_live_successor(self):
        query = ("branch", "--show-current")
        hit = []
        def inject(args, data, calls):
            if args == query:
                hit.append(args)
                return b"wrong-branch\n"
            return data
        with candidate(transform=inject):
            with self.assertRaisesRegex(AssertionError, "^Wrong 8.37 product branch$"):
                self.projectors()[0](set(self.DRAFT_PATHS))
        self.assertEqual(hit, [query])

    def test_forged_staged_entrypoint_blob_refuses_projection(self):
        query = ("ls-files", "--stage", "-z")
        target = "nayeon/desktop_alpha/application.py"
        hit = []
        for state in STATES:
            def inject(args, data, calls):
                if args == query:
                    entries = scope._inventory(data, index=True)
                    self.assertNotEqual(entries[target][1], "1" * 40)
                    entries[target] = ("100644", "1" * 40)
                    hit.append(args)
                    return tree_bytes(entries, index=True)
                return data
            expected = ("Unapproved 8.37 committed/index snapshot" if state == "EXACT_CHILD"
                        else "Partial 8.37 stage refused")
            with self.subTest(state=state), candidate(state, transform=inject):
                with self.assertRaisesRegex(AssertionError, "^" + expected + "$"):
                    self.projectors()[1](set(self.DRAFT_PATHS))
        self.assertEqual(hit, [query] * len(STATES))


if __name__ == "__main__":
    unittest.main()
