"""Read-only raw Git adversaries for the fourteen-file 8.32 transition.

Every positive/negative is synthetic or read-only. No staging/commits/refs are
created. Historical negatives prove injection reached the intended raw read.
"""
from __future__ import annotations

from contextlib import contextmanager, ExitStack
import hashlib
from pathlib import Path
import unittest
from unittest import mock

from tests import phase_8_30_scope_migration as prior
from tests import phase_8_31_scope_migration as old
from tests import phase_8_32_scope_migration as scope
from tests import test_phase_830_scope_integrity as current_reader


def tree_bytes(entries):
    return b"".join(f"{mode} blob {oid}\t{path}".encode() + b"\0"
                    for path, (mode, oid) in sorted(entries.items()))


def index_bytes(entries):
    return b"".join(f"{mode} {oid} 0\t{path}".encode() + b"\0"
                    for path, (mode, oid) in sorted(entries.items()))


def raw_blob_oid(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def raw_delta(before, after, paths):
    records = []
    for path in sorted(paths):
        previous = before.get(path, ("000000", "0" * 40))
        current = after.get(path, ("000000", "0" * 40))
        status = "A" if path not in before else ("D" if path not in after else "M")
        records.append(f":{previous[0]} {current[0]} {previous[1]} {current[1]} {status}".encode()
                       + b"\0" + path.encode() + b"\0")
    return b"".join(records)


# Independent test inventory: never derive the expected seals from scope.SEALS.
REPAIR_SEALS = {
    "nayeon-v1-phase-8-30-offline-workspace-product-01":
        ("3f9e236a2cecec90cb5302df2e4348e6f96611a2", old.PRODUCT_830),
    "nayeon-v1-phase-8-30-handover-documentation-01":
        ("4e2554d30bc49f4b788b8998dd8326ae2fd15c80", "8b2fecf00d48324a187d931156cfa463bbd0aa67"),
    "nayeon-v1-phase-8-30-offline-workspace-rfc-go-01":
        ("0c986ea1bf859c710a6d4cb7fe92f7e0f29658a2", "058c622a04a26a882c773533c568371c53b9b140"),
    "nayeon-v1-phase-8-31-offline-conversation-session-product-01":
        ("2db31d688c12f9a845d903a2d1db14a9d2aa7a5e", old.PRODUCT_COMMIT_831),
    "nayeon-v1-phase-8-31-offline-conversation-handover-01":
        ("2d74f06ceac02781edee5a0bd15c4361cc5ec03c", old.DOC_COMMIT_831),
    "nayeon-v1-phase-8-31-postdocs-guard-maintenance-01":
        ("48907e80d9c69916d521b18f2f4f8c1bfab76e00", scope.PROTECTED),
}
HISTORICAL_READS = (prior.PROTECTED, old.PRODUCT_830, old.PRODUCT_COMMIT_831,
                    scope.PROTECTED, old.DOC_COMMIT_831)


def synthetic_seal_git(args):
    """Exact refs and immutable-object queries, independent of scope.SEALS."""
    for tag, (obj, commit) in REPAIR_SEALS.items():
        if args == ("show-ref", "--verify", "--hash", "--", "refs/tags/" + tag):
            return (obj + "\n").encode()
        if args == ("rev-parse", "--verify", "--end-of-options", obj + "^{}"):
            return (commit + "\n").encode()
        if args == ("cat-file", "-t", obj):
            return b"tag\n"
        if args == ("cat-file", "-t", commit):
            return b"commit\n"
    return None


@contextmanager
def repair_fixture(*, transform=None, changed_disk=None, disk_mutation=None, state="COMPLETE_UNSTAGED"):
    """Pure fake Git/disk; real parsing, history, pins and admission code run.

    No host Git, filesystem, source pins or tag refs are changed. Synthetic
    byte pins apply only within this fixture, including the self-pin format.
    """
    calls, reads = [], []
    base_data = {p: ("# base " + p + "\n").encode() for p in scope.MODIFIED
                 if p not in prior.APPROVED_NEW_SHA256}
    base_data.update({p: ("# frozen " + p + "\n").encode() for p in (
        "nayeon/frozen.py", "tests/test_phase_831_session.py", "docs/frozen.md", "README.md")})
    base_data.update({"LICENSE": b"Frozen license\r\nSecond line\r\n",
                      "config/jarvis.ico": b"\x00\x00\x01\x00\xff\r\n\x00\x80\r\n\xfe"})
    for p in prior.APPROVED_MODIFIED_SHA256:
        base_data[p] = b"# before 830\n"
    bytes830 = {p: ("# 830 " + p + "\n").encode() for p in prior.APPROVED_SOURCE_SHA256}
    bytes831 = {p: ("# 831 " + p + "\n").encode() for p in old.ALL_831}
    product830 = {**base_data, **bytes830}
    product831 = {**product830, **bytes831}
    histories = {prior.PROTECTED: base_data, old.PRODUCT_830: product830,
                 old.PRODUCT_COMMIT_831: product831, scope.PROTECTED: product831,
                 old.DOC_COMMIT_831: product831}
    refs = lambda data: {p: ("100644", raw_blob_oid(b)) for p, b in data.items()}
    protected = refs(product831)
    disk_data = dict(product831)
    disk_data.update({p: ("# 832 " + p + "\n").encode() for p in scope.ENVELOPE})
    disk_data[scope.SELF] = b'{"tests/phase_8_32_scope_migration.py": "' + b"0" * 64 + b'",}\n'
    pins = {p: scope._digest(p, disk_data[p]) for p in scope.ENVELOPE}
    accepted = {**protected, **refs({p: disk_data[p] for p in scope.ENVELOPE})}
    index = accepted if state == "EXACT_STAGED" else protected
    parents = {scope.PROTECTED: old.DOC_COMMIT_831,
               old.DOC_COMMIT_831: old.PRODUCT_COMMIT_831,
               old.PRODUCT_COMMIT_831: old.PARENT_831}

    def git(*args):
        calls.append(args)
        seal_data = synthetic_seal_git(args)
        if seal_data is not None:
            data = seal_data
        elif args == ("rev-parse", "--show-object-format"):
            data = b"sha1\n"
        elif args == ("rev-parse", "HEAD"):
            data = (scope.PROTECTED + "\n").encode()
        elif args == ("branch", "--show-current"):
            data = b""
        elif args == ("merge-base", "--is-ancestor", scope.PROTECTED, scope.PROTECTED):
            data = b""
        elif args[:4] == ("ls-tree", "-r", "-z", "--full-tree") and len(args) == 5:
            data = tree_bytes(refs(histories[args[4]]))
        elif args[0] == "show" and len(args) == 2:
            commit, path = args[1].split(":", 1)
            data = histories[commit][path]
        elif args == ("rev-parse", scope.PROTECTED + ":nayeon"):
            data = (scope.PROTECTED_PRODUCT_TREE + "\n").encode()
        elif args[:4] == ("rev-list", "--parents", "-n", "1") and len(args) == 5:
            data = (args[4] + " " + parents[args[4]] + "\n").encode()
        elif args[0] == "rev-parse" and len(args) == 2:
            peeled = args[1].endswith("^{}")
            ref = args[1][:-3] if peeled else args[1]
            # Revision lookup permits nested fallback even for refs/tags/name.
            tag = (ref[len("refs/refs/tags/"):] if ref.startswith("refs/refs/tags/") else
                   ref[len("refs/tags/"):] if ref.startswith("refs/tags/") else
                   ref[len("refs/"):] if ref.startswith("refs/") else ref)
            data = (REPAIR_SEALS[tag][int(peeled)] + "\n").encode()
        elif args == ("ls-files", "--stage", "-z"):
            data = index_bytes(index)
        elif args == ("ls-files", "-v", "--sparse", "-z"):
            data = b"".join(b"H " + p.encode() + b"\0" for p in sorted(index))
        elif args == ("ls-files", "--others", "--exclude-standard", "-z"):
            data = b"" if state == "EXACT_STAGED" else b"".join(
                p.encode() + b"\0" for p in sorted(scope.ADDED))
        elif args == ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
            data = b"tests/__pycache__/synthetic.cpython-312.pyc\0"
        elif args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z"):
            working = dict(index)
            working.update({p: ("100644", "0" * 40) for p in scope.MODIFIED})
            data = b"" if state == "EXACT_STAGED" else raw_delta(index, working, scope.MODIFIED)
        elif args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z", "--cached"):
            data = raw_delta(protected, index, scope.ENVELOPE)
        else:
            raise AssertionError("Unexpected synthetic Git call: " + repr(args))
        return transform(args, data, calls) if transform else data

    def disk(path):
        reads.append(path)
        data = disk_data[path]
        if path == changed_disk:
            return disk_mutation(data) if disk_mutation else data + b"# hidden mutation\n"
        return data

    with ExitStack() as patches:
        patches.enter_context(mock.patch.object(prior, "_git", side_effect=git))
        patches.enter_context(mock.patch.object(scope, "_disk", side_effect=lambda p: prior._normal(disk(p))))
        patches.enter_context(mock.patch.object(scope, "_raw_frozen_disk", side_effect=disk))
        patches.enter_context(mock.patch.object(scope, "CANDIDATE_SHA256", pins))
        patches.enter_context(mock.patch.object(prior, "APPROVED_SOURCE_SHA256",
                                                {p: old._sha(b) for p, b in bytes830.items()}))
        patches.enter_context(mock.patch.object(old, "ALL_831",
                                                {p: old._sha(b) for p, b in bytes831.items()}))
        yield calls, reads


class Phase832RepairCanaryTests(unittest.TestCase):
    """Run this class on the host while final literal pins remain zero/HOLD."""

    def test_synthetic_clean_positive_reaches_frozen_disk_and_all_six_seals(self):
        with repair_fixture() as (calls, reads):
            self.assertEqual(scope.assert_832_integrity(), "COMPLETE_UNSTAGED")
        self.assertIn("tests/test_phase_831_session.py", reads)
        self.assertIn("docs/frozen.md", reads)
        self.assertIn("LICENSE", reads)
        self.assertIn("config/jarvis.ico", reads)
        self.assertNotIn("tests/__pycache__/synthetic.cpython-312.pyc", reads)
        self.assertEqual(scope.SEALS, REPAIR_SEALS)
        for tag, (obj, commit) in REPAIR_SEALS.items():
            self.assertIn(("show-ref", "--verify", "--hash", "--", "refs/tags/" + tag), calls)
            self.assertIn(("rev-parse", "--verify", "--end-of-options", obj + "^{}"), calls)
            self.assertIn(("cat-file", "-t", obj), calls)
            self.assertIn(("cat-file", "-t", commit), calls)
            self.assertNotIn(("rev-parse", "refs/tags/" + tag), calls)
            self.assertNotIn(("rev-parse", "refs/tags/" + tag + "^{}"), calls)

    def test_real_clean_crlf_license_and_binary_ico_match_raw_head_index(self):
        # Read-only real controls bypass candidate pins, not the raw reader.
        head = scope._tree("HEAD")
        protected = scope._tree(scope.PROTECTED)
        index = scope._index()
        scope._index_flags(index)
        for path in ("LICENSE", "config/jarvis.ico"):
            with self.subTest(path=path):
                data = scope._raw_frozen_disk(path)
                self.assertIn(b"\r\n", data)
                self.assertEqual(data, scope._git("show", "HEAD:" + path))
                self.assertEqual(head[path], ("100644", raw_blob_oid(data)))
                self.assertEqual(index[path], head[path])
                self.assertEqual(protected[path], head[path])
                self.assertNotEqual(raw_blob_oid(prior._normal(data)), head[path][1])

    def test_raw_reader_preserves_crlf_and_binary_and_candidate_normalization(self):
        for data in (b"first\r\nsecond\r\n", b"\x00\xff\r\n\x80\x00\r\n"):
            with self.subTest(data=data), mock.patch.object(Path, "read_bytes", return_value=data):
                self.assertEqual(scope._raw_frozen_disk("LICENSE"), data)
                self.assertEqual(scope._disk("LICENSE"), prior._normal(data))

    def test_raw_reader_rejects_linked_nonregular_files_and_unsafe_ancestors(self):
        from types import SimpleNamespace
        path = "config/jarvis.ico"
        candidate = scope.ROOT / path
        real_lstat = Path.lstat
        regular = real_lstat(candidate)
        directory = real_lstat(candidate.parent)
        file_cases = ((0o120777, 0, 1), (regular.st_mode, 0x400, 1),
                      (regular.st_mode, 0, 2), (0o040755, 0, 1))
        parent_cases = ((0o120777, 0, 1), (directory.st_mode, 0x400, 1),
                        (regular.st_mode, 0, 1))
        for target, cases, message in ((candidate, file_cases, "Linked or nonregular"),
                                       (candidate.parent, parent_cases, "Linked or reparse"),
                                       (scope.ROOT, parent_cases, "Linked or reparse")):
            for mode, attributes, links in cases:
                fake = SimpleNamespace(st_mode=mode, st_file_attributes=attributes, st_nlink=links)
                reached = []
                def lstat(name, *args, **kwargs):
                    if name == target:
                        reached.append(name)
                        return fake
                    return real_lstat(name, *args, **kwargs)
                with self.subTest(target=target, mode=mode, attributes=attributes, links=links), \
                        mock.patch.object(Path, "lstat", autospec=True, side_effect=lstat), \
                        mock.patch.object(Path, "read_bytes") as read:
                    with self.assertRaisesRegex(AssertionError, message):
                        scope._raw_frozen_disk(path)
                    self.assertEqual(reached, [target])
                    read.assert_not_called()

    def test_hidden_frozen_test_and_docs_bytes_rejected_without_diff_evidence(self):
        # Frozen HEAD/index stay identical and the entire worktree diff is
        # empty. The injected target disk read MUST be reached.
        for target in ("tests/test_phase_831_session.py", "docs/frozen.md", "LICENSE", "config/jarvis.ico"):
            with self.subTest(target=target), repair_fixture(
                    changed_disk=target, state="EXACT_STAGED") as (_, reads):
                self.assertEqual(scope._git("diff", "--no-renames", "--raw", "--no-abbrev", "-z"), b"")
                try:
                    with self.assertRaisesRegex(AssertionError, "Frozen .*worktree bytes modified"):
                        scope.assert_832_integrity()
                finally:
                    self.assertIn(target, reads, "Hidden frozen bytes were never read")

    def test_synthetic_staged_positive_with_empty_worktree_diff(self):
        with repair_fixture(state="EXACT_STAGED"):
            self.assertEqual(scope.assert_832_integrity(), "EXACT_STAGED")

    def test_normalization_equivalent_frozen_mutations_hidden_by_diff_rejected(self):
        for target in ("LICENSE", "config/jarvis.ico"):
            mutations = []
            def normalize(data):
                changed = prior._normal(data)
                self.assertNotEqual(changed, data)
                self.assertEqual(prior._normal(changed), prior._normal(data))
                mutations.append(True)
                return changed
            with self.subTest(target=target), repair_fixture(
                    changed_disk=target, disk_mutation=normalize, state="EXACT_STAGED") as (_, reads):
                self.assertEqual(scope._git("diff", "--no-renames", "--raw", "--no-abbrev", "-z"), b"")
                with self.assertRaisesRegex(AssertionError, "Frozen tracked worktree bytes modified"):
                    scope.assert_832_integrity()
                self.assertEqual(mutations, [True])
                self.assertIn(target, reads)

    def test_index_suppression_sparse_and_malformed_flags_rejected(self):
        target = b"tests/test_phase_831_session.py"
        for flag in (b"h", b"S", b"s", b"?", b"HH", b"", b"M"):
            reached = []
            def inject(args, data, calls):
                if args == ("ls-files", "-v", "--sparse", "-z"):
                    reached.append(True)
                    return data.replace(b"H " + target + b"\0", flag + b" " + target + b"\0")
                return data
            with self.subTest(flag=flag), repair_fixture(transform=inject):
                try:
                    with self.assertRaisesRegex(AssertionError, "8.32 index flags"):
                        scope.assert_832_integrity()
                finally:
                    self.assertEqual(reached, [True])

    def test_index_flag_inventory_requires_complete_unique_canonical_records(self):
        target = b"H tests/test_phase_831_session.py\0"
        mutations = (
            lambda data: data[:-1],
            lambda data: data.replace(target, b""),
            lambda data: data + target,
            lambda data: data + b"H Tests/test_phase_831_session.py\0",
            lambda data: data + b"S tests/sparse/\0",
            lambda data: data.replace(target, b"H\ttests/test_phase_831_session.py\0"),
        )
        for number, mutate in enumerate(mutations):
            reached = []
            def inject(args, data, calls):
                if args == ("ls-files", "-v", "--sparse", "-z"):
                    reached.append(True)
                    return mutate(data)
                return data
            with self.subTest(mutation=number), repair_fixture(transform=inject):
                try:
                    with self.assertRaises(AssertionError):
                        scope.assert_832_integrity()
                finally:
                    self.assertEqual(reached, [True])

    def test_each_seal_deletion_tag_object_and_peeled_retarget_rejected(self):
        for tag, (obj, _) in REPAIR_SEALS.items():
            for attack in ("deleted", "tag-object", "peeled"):
                reached = []
                wanted = (("rev-parse", "--verify", "--end-of-options", obj + "^{}")
                          if attack == "peeled" else
                          ("show-ref", "--verify", "--hash", "--", "refs/tags/" + tag))
                def inject(args, data, calls):
                    if args == wanted:
                        reached.append(True)
                        if attack == "deleted":
                            raise AssertionError("Unable to verify exact Git snapshot")
                        return b"f" * 40 + b"\n"
                    return data
                with self.subTest(tag=tag, attack=attack), repair_fixture(transform=inject):
                    try:
                        with self.assertRaisesRegex(AssertionError, "Frozen seal changed|Unable to verify exact Git snapshot"):
                            scope._history()
                    finally:
                        self.assertEqual(reached, [True], "Seal attack did not reach the Git seam")

    def test_each_seal_short_ref_shadow_cannot_hide_missing_or_retargeted_tag(self):
        for tag, pins in REPAIR_SEALS.items():
            for attack in ("missing", "tag-object", "peeled"):
                reached = []
                aliases = []
                ref = "refs/tags/" + tag
                wanted = (("rev-parse", "--verify", "--end-of-options", pins[0] + "^{}")
                          if attack == "peeled" else
                          ("show-ref", "--verify", "--hash", "--", ref))
                def inject(args, data, calls):
                    if args == wanted:
                        reached.append(args)
                        if attack == "missing":
                            raise AssertionError("Unable to verify exact Git snapshot")
                        return b"f" * 40 + b"\n"
                    if args[0] == "rev-parse" and len(args) == 2:
                        name = args[1]
                        peeled = name.endswith("^{}")
                        base = name[:-3] if peeled else name
                        if base in {tag, "refs/" + tag}:
                            aliases.append(name)
                            return (pins[int(peeled)] + "\n").encode()
                    return data
                with self.subTest(tag=tag, attack=attack), repair_fixture(transform=inject):
                    # refs/<name> still resolves to the original pinned object
                    # and peel, as does the shadowed short spelling. No ref writes.
                    for alias in (tag, "refs/" + tag):
                        for suffix, expected in (("", pins[0]), ("^{}", pins[1])):
                            self.assertEqual(scope._git("rev-parse", alias + suffix),
                                             (expected + "\n").encode())
                    self.assertEqual(len(aliases), 4)
                    with self.assertRaisesRegex(AssertionError, "Frozen seal changed|Unable to verify exact Git snapshot"):
                        scope._history()
                    self.assertEqual(reached, [wanted], "Shadow attack never checked the protected tag ref")
                    self.assertEqual(len(aliases), 4, "History used a shadowable short ref")

    def test_missing_exact_tag_with_good_nested_ref_fallback_rejected(self):
        for tag, pins in REPAIR_SEALS.items():
            reached, aliases = [], []
            ref = "refs/tags/" + tag
            exact = ("show-ref", "--verify", "--hash", "--", ref)
            def inject(args, data, calls):
                if args == exact:
                    reached.append(args)
                    raise AssertionError("Unable to verify exact Git snapshot")
                if args[0] == "rev-parse" and len(args) == 2:
                    name = args[1]
                    peeled = name.endswith("^{}")
                    base = name[:-3] if peeled else name
                    if base in {tag, "refs/" + tag, ref, "refs/" + ref}:
                        aliases.append(args)
                        return (pins[int(peeled)] + "\n").encode()
                return data
            with self.subTest(tag=tag), repair_fixture(transform=inject) as (calls, _):
                # The actual tag is absent; refs/refs/tags/name still points to
                # the correct annotated object. Every revision spelling works.
                for alias in (tag, "refs/" + tag, ref, "refs/" + ref):
                    for suffix, expected in (("", pins[0]), ("^{}", pins[1])):
                        self.assertEqual(scope._git("rev-parse", alias + suffix),
                                         (expected + "\n").encode())
                self.assertEqual(len(aliases), 8)
                calls.clear()
                with self.assertRaisesRegex(AssertionError, "Unable to verify exact Git snapshot"):
                    scope.assert_832_integrity()
                self.assertEqual(reached, [exact], "Missing exact tag check was never reached")
                self.assertEqual(len(aliases), 8, "Candidate used fallback revision resolution")
                self.assertNotIn(("rev-parse", "--verify", "--end-of-options", pins[0] + "^{}"), calls)

    def test_each_seal_malformed_oid_and_wrong_object_types_rejected(self):
        bad_oids = (b"", b"\n", b"not-an-oid\n", b"F" * 40 + b"\n",
                    b"1" * 39 + b"\n", b"1" * 41 + b"\n",
                    b"1" * 40 + b"\n" + b"2" * 40 + b"\n",
                    b" " + b"1" * 40 + b"\n", "1" * 40, None)
        for tag, (obj, commit) in REPAIR_SEALS.items():
            queries = (
                (("show-ref", "--verify", "--hash", "--", "refs/tags/" + tag), bad_oids),
                (("rev-parse", "--verify", "--end-of-options", obj + "^{}"), bad_oids),
                (("cat-file", "-t", obj), (b"commit\n", b"blob\n", b"tree\n", b"", b"tag\ncommit\n", "tag\n")),
                (("cat-file", "-t", commit), (b"tag\n", b"blob\n", b"tree\n", b"", b"commit\ntag\n", "commit\n")),
            )
            for wanted, values in queries:
                for value in values:
                    reached = []
                    def inject(args, data, calls):
                        if args == wanted:
                            reached.append(args)
                            return value
                        return data
                    with self.subTest(tag=tag, query=wanted, value=value), repair_fixture(transform=inject):
                        with self.assertRaisesRegex(AssertionError, "Frozen seal changed"):
                            scope.assert_832_integrity()
                        self.assertEqual(reached, [wanted], "Malformed seal evidence was never reached")

    def test_historical_nonproduction_metadata_and_duplicate_aliases_rejected(self):
        bad_records = (
            b"100644 blob NOT_AN_OID\tREADME.md\0",
            b"100644 tree " + b"1" * 40 + b"\tforeign.md\0",
            b"040000 tree " + b"1" * 40 + b"\tforeign.md\0",
            b"100644 blob " + b"1" * 40 + b"\tREADME.md\0",
            b"100644 blob " + b"1" * 40 + b"\treadme.md\0",
        )
        for position, commit in enumerate(HISTORICAL_READS, 1):
            for record in bad_records:
                reached = []
                def inject(args, data, calls):
                    if args[0] == "ls-tree" and sum(c[0] == "ls-tree" for c in calls) == position:
                        self.assertEqual(args[-1], commit)
                        reached.append(True)
                        return data + record
                    return data
                with self.subTest(position=position, record=record), repair_fixture(transform=inject) as (calls, _):
                    try:
                        with self.assertRaisesRegex(AssertionError, "Malformed 8.32 Git inventory|Repeated or aliased 8.32 Git path"):
                            scope._history()
                    finally:
                        self.assertEqual(reached, [True])
                        self.assertEqual(sum(c[0] == "ls-tree" for c in calls), position)

    def test_historical_second_tree_production_injection_preserves_old_rejection(self):
        with repair_fixture():
            scope._history()
        reached = []
        def inject(args, data, calls):
            if args[0] == "ls-tree" and sum(c[0] == "ls-tree" for c in calls) == 2:
                reached.append(args[-1])
                return data + b"100644 blob " + b"1" * 40 + b"\tnayeon/foreign.py\0"
            return data
        with repair_fixture(transform=inject) as (calls, _):
            with self.assertRaisesRegex(AssertionError, "^Missing or unapproved committed 8.30 source$"):
                old.assert_831_integrity()
        self.assertEqual(reached, [old.PRODUCT_830])
        self.assertEqual(sum(c[0] == "ls-tree" for c in calls), 2)


@contextmanager
def snapshot(state="COMPLETE_UNSTAGED", *, stage_paths=None, parent=None, merge=False,
             mode_path=None, corrupt_source=None, extra_index=None, missing=None):
    """All raw histories/index/deltas, including valid positive controls."""
    actual = prior._git
    base = scope._tree(scope.PROTECTED)
    accepted = dict(base)
    for path in scope.ENVELOPE:
        accepted[path] = ("100644", prior._oid(scope._disk(path)))
    child = "e" * 40
    head = child if state == "EXACT_CHILD" else scope.PROTECTED
    committed = dict(accepted if head == child else base)
    index = dict(accepted if state in {"EXACT_CHILD", "EXACT_STAGED"} else base)
    if stage_paths is not None:
        index = dict(base)
        for path in stage_paths:
            index[path] = accepted[path]
    if mode_path:
        index[mode_path] = ("120000", accepted[mode_path][1])
    if corrupt_source:
        index[corrupt_source] = ("100644", "1" * 40)
    if extra_index:
        index[extra_index] = ("100644", "1" * 40)
    if missing:
        committed.pop(missing, None)
    changed = {p for p in set(index) | set(committed) if index.get(p) != committed.get(p)}
    untracked = set(scope.ADDED) - set(index)
    if head == child:
        untracked = set()
    working = scope.MODIFIED if state == "COMPLETE_UNSTAGED" and stage_paths is None else set()
    def git(*args):
        if args == ("rev-parse", "HEAD"):
            return (head + "\n").encode()
        seal_data = synthetic_seal_git(args)
        if seal_data is not None:
            return seal_data
        if args[:2] == ("merge-base", "--is-ancestor"):
            return b""
        if args == ("rev-list", "--parents", "-n", "1", child):
            return (child + " " + (parent or scope.PROTECTED)
                    + (" " + "d" * 40 if merge else "") + "\n").encode()
        if args == ("ls-tree", "-r", "-z", "--full-tree", child):
            return tree_bytes(committed)
        if args == ("ls-files", "--stage", "-z"):
            return index_bytes(index)
        if args == ("ls-files", "-v", "--sparse", "-z"):
            return b"".join(b"H " + p.encode() + b"\0" for p in sorted(index))
        if args == ("ls-files", "--others", "--exclude-standard", "-z"):
            return b"".join(p.encode() + b"\0" for p in sorted(untracked))
        if args == ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
            return b""
        if args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z"):
            disk = dict(index)
            for path in working:
                disk[path] = ("100644", "0" * 40)
            return raw_delta(index, disk, working)
        if args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z", "--cached"):
            return raw_delta(committed, index, changed)
        if args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z", scope.PROTECTED, child):
            return raw_delta(base, committed, scope.ENVELOPE)
        return actual(*args)
    with mock.patch.object(prior, "_git", side_effect=git):
        yield


class Phase832ScopeIntegrityTests(unittest.TestCase):
    def test_real_candidate_is_exact_unstaged_and_public_831_delegates(self):
        head = prior._git("rev-parse", "HEAD").decode("ascii").strip()
        self.assertRegex(head, r"^[0-9a-f]{40}$")
        committed, index = scope._tree(head), scope._index()
        staged_delta = {p for p in set(committed) | set(index)
                        if committed.get(p) != index.get(p)}
        if head == scope.PROTECTED:
            if staged_delta:
                self.assertEqual(staged_delta, scope.ENVELOPE)
                expected = "EXACT_STAGED"
            else:
                expected = "COMPLETE_UNSTAGED"
        else:
            self.assertEqual(staged_delta, set())
            expected = "EXACT_CHILD"
        self.assertEqual(scope.assert_832_integrity(), expected)
        with mock.patch.object(scope, "assert_832_integrity", return_value=expected) as gate:
            old.assert_831_integrity()
        gate.assert_called_once_with()
        self.assertEqual(len(scope.ENVELOPE), 14)
        self.assertEqual(len(scope.ADDED), 5)
        self.assertEqual(len(scope.MODIFIED), 9)

    def test_complete_unstaged_staged_and_one_exact_child_positive_controls(self):
        for state in ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD"):
            with self.subTest(state=state), snapshot(state):
                self.assertEqual(scope.assert_832_integrity(), state)

    def test_partial_staging_of_each_path_and_nearly_complete_refused(self):
        for path in scope.ENVELOPE:
            with self.subTest(path=path), snapshot(stage_paths={path}):
                with self.assertRaisesRegex(AssertionError, "Partial 8.32 staged"):
                    scope.assert_832_integrity()
        with snapshot(stage_paths=scope.ENVELOPE - {scope.SELF}):
            with self.assertRaisesRegex(AssertionError, "Partial 8.32 staged"):
                scope.assert_832_integrity()

    def test_child_wrong_immediate_parent_and_merge_refused(self):
        for kwargs in ({"parent": "a" * 40}, {"merge": True}):
            with self.subTest(kwargs=kwargs), snapshot("EXACT_CHILD", **kwargs):
                with self.assertRaisesRegex(AssertionError, "wrong immediate product parent"):
                    scope.assert_832_integrity()

    def test_mode_missing_source_corrupt_index_and_extra_path_refused(self):
        path = "nayeon/desktop_alpha/application.py"
        for kwargs in ({"mode_path": path}, {"corrupt_source": path},
                       {"extra_index": "tests/foreign.py"}):
            with self.subTest(kwargs=kwargs), snapshot("EXACT_STAGED", **kwargs):
                with self.assertRaises(AssertionError):
                    scope.assert_832_integrity()
        with snapshot("EXACT_CHILD", missing=path):
            real_tree = scope._tree
            reached = []
            def missing_tree(revision):
                tree = real_tree(revision)
                if revision == "e" * 40:
                    self.assertNotIn(path, tree)
                    reached.append(revision)
                return tree
            with mock.patch.object(scope, "_tree", side_effect=missing_tree):
                # The injected child omits application.py while its index
                # retains it. That staged disagreement is refused first.
                with self.assertRaisesRegex(AssertionError, "^Partial 8.32 staged snapshot refused$"):
                    scope.assert_832_integrity()
            self.assertEqual(reached, ["e" * 40], "Missing child-source injection was not reached")

    def test_every_pin_rejects_modified_bytes(self):
        real = scope._disk
        for path in scope.ENVELOPE:
            def disk(name):
                return real(name) + b"\n# unreviewed\n" if name == path else real(name)
            with self.subTest(path=path), mock.patch.object(scope, "_disk", side_effect=disk):
                with self.assertRaisesRegex(AssertionError, "PARTIAL or unapproved"):
                    scope.assert_832_integrity()

    def test_absent_candidate_file_and_retired_adapter_fail_closed(self):
        real_disk = scope._disk
        path = "tests/test_phase_832_lifecycle_assurance.py"
        def missing(name):
            if name == path:
                raise AssertionError("Missing 8.32 candidate")
            return real_disk(name)
        with mock.patch.object(scope, "_disk", side_effect=missing):
            with self.assertRaisesRegex(AssertionError, "Missing"):
                scope.assert_832_integrity()
        actual = prior._git
        def adapter(*args):
            data = actual(*args)
            if args == ("ls-files", "--others", "--exclude-standard", "-z"):
                return data + b"tests/phase_832_cancel_adapter.py\0"
            return data
        with mock.patch.object(prior, "_git", side_effect=adapter):
            with self.assertRaisesRegex(AssertionError, "Unauthorized untracked"):
                scope.assert_832_integrity()

    def test_malformed_nonproduction_raw_records_are_not_filtered_away(self):
        for raw, indexed in ((b"garbage\tREADME.md\0", False),
                             (b"100644 blob bad\tREADME.md\0", False),
                             (b"100644 " + b"1" * 40 + b" 1\tREADME.md\0", True),
                             (b"100644 blob " + b"1" * 40 + b"\tREADME.md", False)):
            with self.subTest(raw=raw), self.assertRaisesRegex(AssertionError, "Malformed"):
                scope._inventory(raw, index=indexed)

    def test_aliases_in_head_index_untracked_and_ignored_are_refused_before_filtering(self):
        real = prior._git
        for alias in ("NAYEON/foreign.py", "nayeon./foreign.py", "nayeon /foreign.py",
                      "nayeon/../foreign.py", "nayeon/file.py:evil", "nayeon\\file.py",
                      "Tests/foreign.py", "tests/foreign.py.", "docs//foreign.md"):
            for surface in ("tree", "index", "untracked", "ignored"):
                reached = []
                def inject(*args):
                    data = real(*args)
                    if surface == "tree" and args[0] == "ls-tree":
                        reached.append(True)
                        return data + b"100644 blob " + b"1" * 40 + b"\t" + alias.encode() + b"\0"
                    if surface == "index" and args == ("ls-files", "--stage", "-z"):
                        reached.append(True)
                        return data + b"100644 " + b"1" * 40 + b" 0\t" + alias.encode() + b"\0"
                    if surface == "untracked" and args == ("ls-files", "--others", "--exclude-standard", "-z"):
                        reached.append(True)
                        return data + alias.encode() + b"\0"
                    if surface == "ignored" and args == ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
                        reached.append(True)
                        return data + alias.encode() + b"\0"
                    return data
                with self.subTest(alias=alias, surface=surface), mock.patch.object(prior, "_git", side_effect=inject):
                    with self.assertRaises(AssertionError):
                        scope.assert_832_integrity()
                self.assertTrue(reached, "Alias negative failed before malicious raw inventory")

    def test_ignored_production_source_and_unapproved_worktree_delta_refused(self):
        actual = prior._git
        for surface in ("ignored", "worktree"):
            reached = []
            def inject(*args):
                data = actual(*args)
                if surface == "ignored" and args == ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
                    reached.append(True)
                    return data + b"nayeon/ignored_authority.py\0"
                if surface == "worktree" and args == ("diff", "--no-renames", "--raw", "--no-abbrev", "-z"):
                    reached.append(True)
                    return data + b":100644 100644 " + b"1" * 40 + b" " + b"0" * 40 + b" M\0tests/foreign.py\0"
                return data
            with mock.patch.object(prior, "_git", side_effect=inject):
                with self.assertRaises(AssertionError):
                    scope.assert_832_integrity()
            self.assertTrue(reached)

    def test_historical_second_tree_injection_reached_with_clean_positive_control(self):
        scope.assert_832_integrity()
        actual = prior._git
        calls = []
        def inject(*args):
            data = actual(*args)
            if args[0] == "ls-tree":
                calls.append(args)
                if len(calls) == 2:
                    from tests.test_phase_830_scope_integrity import replace_or_add_record, tree_record
                    return replace_or_add_record(data, "nayeon/desktop_alpha/application.py",
                                                  tree_record("nayeon/desktop_alpha/application.py"))
            return data
        with mock.patch.object(prior, "_git", side_effect=inject):
            with self.assertRaisesRegex(AssertionError, "^Missing or unapproved committed 8.30 source$"):
                old.assert_831_integrity()
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][-1], old.PRODUCT_830)

    def test_current_reader_routes_to_successor_and_old_pins_still_fail(self):
        for path in ("nayeon/desktop_alpha/application.py", "nayeon/desktop_alpha/workspace_window.py",
                     "nayeon/desktop_alpha/presentation_window.py"):
            self.assertEqual(prior._approved_source(path), prior._oid(scope._disk(path)))
            with mock.patch.dict(prior.APPROVED_SOURCE_SHA256, {path: "0" * 64}):
                with self.assertRaisesRegex(AssertionError, "Unapproved 8.30 source bytes"):
                    prior._approved_source(path)

    def test_link_reparse_hardlink_and_nonregular_candidates_are_refused(self):
        path = "nayeon/desktop_alpha/application.py"
        real = (scope.ROOT / path).lstat()
        from types import SimpleNamespace
        for mode, attributes, links in ((0o120777, 0, 1), (real.st_mode, 0x400, 1),
                                       (real.st_mode, 0, 2), (0o040755, 0, 1)):
            fake = SimpleNamespace(st_mode=mode, st_file_attributes=attributes, st_nlink=links)
            with mock.patch.object(Path, "lstat", return_value=fake), mock.patch.object(prior, "_reject_linked_parents"):
                with self.assertRaisesRegex(AssertionError, "Linked or nonregular"):
                    scope._disk(path)

    def test_self_pin_checks_code_and_every_other_pin_not_only_product(self):
        data = scope._disk(scope.SELF)
        self.assertEqual(scope._digest(scope.SELF, data), scope.CANDIDATE_SHA256[scope.SELF])
        self.assertNotEqual(scope._digest(scope.SELF, data + b"\n# changed guard"),
                            scope.CANDIDATE_SHA256[scope.SELF])
        self.assertEqual(set(scope.CANDIDATE_SHA256), scope.ENVELOPE)
        self.assertFalse(any(value == "0" * 64 for value in scope.CANDIDATE_SHA256.values()))


if __name__ == "__main__":
    unittest.main()
