"""Phase10 integrity parser adversaries and SEPARATE native admission proof.

The in-memory topology fixtures are deliberately fictional, use real Git raw
object encoding, and exercise _prove_topology, NOT public source admission.
They do not replace, compute, patch or finalize candidate approval pins.
NativeAdmissionTests must pass independently on the host after all 32
approved paths are complete and statically pinned. Never count synthetic
parser tests alone as live source admission.
"""
from contextlib import contextmanager
import hashlib
from pathlib import Path
import stat
import unittest
from unittest import mock

from tests import phase10_perception_scope_migration as gate
from tests import phase8_byok_b_scope_migration as b_gate

STATES = ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD")


def object_oid(kind, raw):
    # Independent raw-object encoding; never expected source approval.
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode()
                        + b"\0" + raw).hexdigest()


def inventory(entries):
    return b"".join(f"{mode} {oid} 0\t{p}".encode() + b"\0"
                    for p, (mode, oid) in sorted(entries.items()))


def delta(before, after, paths, *, work=False):
    rows = []
    for p in sorted(paths):
        om, oi = before.get(p, ("000000", "0" * 40))
        nm, ni = ((om, "0" * 40) if work else
                  after.get(p, ("000000", "0" * 40)))
        status = ("D" if p not in after else
                  "M" if p in before else "A")
        rows.append(f":{om} {nm} {oi} {ni} {status}".encode()
                    + b"\0" + p.encode() + b"\0")
    return b"".join(rows)


@contextmanager
def topology(state, *, parents=None, transform=None, mutate_index=None,
             mutate_committed=None, others=None):
    """Fictional source inventory: proves topology parsing only, never source GO."""
    baseline = {p: ("100644", object_oid("blob", ("old " + p).encode()))
                for p in gate.MODIFIED | {"frozen.py"}}
    expected = dict(baseline)
    expected.update({p: ("100644", object_oid("blob", ("new " + p).encode()))
                     for p in gate.ENVELOPE})
    index = dict(baseline if state == "COMPLETE_UNSTAGED" else expected)
    committed = dict(expected if state == "EXACT_CHILD" else baseline)
    # The tree header here represents the actual Git tree for this toy fixture.
    child_raw = ("tree " + gate._tree_oid(expected) + "\n"
                 + "".join("parent " + p + "\n" for p in (
                     [gate.PARENT] if parents is None else parents))
                 + "author Fixture <fixture@example.invalid> 0 +0000\n"
                 + "committer Fixture <fixture@example.invalid> 0 +0000\n\nfixture\n").encode()
    child = object_oid("commit", child_raw)
    head = child if state == "EXACT_CHILD" else gate.PARENT
    if mutate_index:
        mutate_index(index, baseline, expected)
    if mutate_committed:
        mutate_committed(committed, baseline, expected)
    untracked = (gate.ADDED - set(index)) if others is None else others
    work_paths = {p for p in gate.MODIFIED if index.get(p) != expected[p]}
    disk_raw = delta(index, expected, work_paths, work=True)
    before = committed
    cached_paths = {p for p in set(index) | set(before) if index.get(p) != before.get(p)}
    calls = []

    def git(*args):
        calls.append(args)
        if args == gate.RAW + ("--cached",):
            raw = delta(before, index, cached_paths)
        elif args == gate.RAW + (gate.PARENT, child):
            raw = delta(baseline, committed, gate.ENVELOPE)
        elif args == ("cat-file", "-t", child):
            raw = b"commit\n"
        elif args == ("cat-file", "commit", child):
            raw = child_raw
        elif args == ("rev-list", "--parents", "-n", "1", child):
            raw = (child + " " + " ".join([gate.PARENT] if parents is None else parents)
                   + "\n").encode()
        else:
            raise AssertionError("Unexpected fixture Git read: " + repr(args))
        return transform(args, raw) if transform else raw

    with mock.patch.object(gate, "_git", side_effect=git):
        yield (head, baseline, expected, committed, index, untracked, disk_raw), calls


class TopologyParserTests(unittest.TestCase):
    def test_exact_three_topologies_with_real_raw_commit_encoding(self):
        for state in STATES:
            with self.subTest(state=state), topology(state) as (args, calls):
                self.assertEqual(gate._prove_topology(*args), state)
                self.assertIn(gate.RAW + ("--cached",), calls)
                if state == "EXACT_CHILD":
                    self.assertIn(("cat-file", "commit", args[0]), calls)
                    self.assertIn(gate.RAW + (gate.PARENT, args[0]), calls)

    def test_partial_stage_wrong_inventory_and_missing_or_extra_files(self):
        def partial(index, baseline, expected):
            p = next(iter(gate.MODIFIED))
            index[p] = baseline[p]
        def extra(index, baseline, expected):
            index["extra.py"] = ("100644", "a" * 40)
        def missing(index, baseline, expected):
            index.pop(next(iter(gate.ADDED)))
        for mutation in (partial, extra, missing):
            with self.subTest(mutation=mutation), topology(
                    "EXACT_STAGED", mutate_index=mutation) as (args, _):
                with self.assertRaises(AssertionError):
                    gate._prove_topology(*args)
        for others in (set(), set(gate.ADDED) | {"extra.py"}):
            with self.subTest(others=others), topology(
                    "COMPLETE_UNSTAGED", others=others) as (args, _):
                with self.assertRaises(AssertionError):
                    gate._prove_topology(*args)
        for mutation in (extra, missing):
            with topology("EXACT_CHILD", mutate_committed=mutation) as (args, _):
                with self.assertRaises(AssertionError):
                    gate._prove_topology(*args)

    def test_wrong_parent_merge_root_and_descendant_refused(self):
        for parents in (["a" * 40], [gate.PARENT, "a" * 40], []):
            with self.subTest(parents=parents), topology(
                    "EXACT_CHILD", parents=parents) as (args, calls):
                with self.assertRaisesRegex(AssertionError, "immediate single B child"):
                    gate._prove_topology(*args)
                self.assertIn(("cat-file", "commit", args[0]), calls)

    def test_committed_and_cached_delta_injections_are_reached(self):
        for state in ("EXACT_STAGED", "EXACT_CHILD"):
            for mutate in (
                    lambda raw: raw[:-1],
                    lambda raw: raw + raw.split(b"\0", 2)[0] + b"\0extra.py\0",
                    lambda raw: raw.replace(b" M\0", b" R100\0", 1),
                    lambda raw: raw.replace(b" M\0", b" D\0", 1),
                    lambda raw: raw.replace(b":100644", b":120000", 1),
                    lambda raw: raw.replace(b" 100644 ", b" 100755 ", 1),
                    lambda raw: raw.replace(b".codex/CURRENT_STATE.md", b".codex/../x", 1),
                    lambda raw: b"",
            ):
                reached = []
                def inject(query, raw):
                    wanted = (query == gate.RAW + ("--cached",) if state == "EXACT_STAGED"
                              else query[:len(gate.RAW) + 1] == gate.RAW + (gate.PARENT,))
                    if wanted:
                        reached.append(query)
                        changed = mutate(raw)
                        self.assertNotEqual(changed, raw)
                        return changed
                    return raw
                with self.subTest(state=state, mutate=mutate), topology(
                        state, transform=inject) as (args, _):
                    with self.assertRaises(AssertionError):
                        gate._prove_topology(*args)
                self.assertEqual(len(reached), 1)

    def test_worktree_delta_wrong_modes_oids_duplicate_and_aliased_paths(self):
        with topology("COMPLETE_UNSTAGED") as (args, _):
            raw = args[-1]
            meta, path, _ = raw.split(b"\0", 2)
            for altered in (b"", raw[:-1], raw + meta + b"\0" + path + b"\0",
                            raw.replace(b" M\0", b" R100\0", 1),
                            raw.replace(b" 100644 ", b" 120000 ", 1),
                            raw.replace(b".codex/CURRENT_STATE.md", b".CODEX/CURRENT_STATE.md", 1),
                            raw.replace(b"0" * 40 + b" M", b"f" * 40 + b" M", 1)):
                with self.subTest(altered=altered[:80]), self.assertRaises(AssertionError):
                    gate._prove_topology(*args[:-1], altered)

    def test_unexpected_staged_or_disk_changes_in_clean_states(self):
        for state in STATES:
            reached = []
            def inject(query, raw):
                if query == gate.RAW + ("--cached",) and state != "EXACT_STAGED":
                    reached.append(query)
                    return b"garbage\0"
                return raw
            with topology(state, transform=inject) as (args, _):
                if state == "EXACT_STAGED":
                    with self.assertRaises(AssertionError):
                        gate._prove_topology(*args[:-1], b"garbage\0")
                else:
                    with self.assertRaises(AssertionError):
                        gate._prove_topology(*args)
                    self.assertEqual(len(reached), 1)


class SourceAndObjectParserTests(unittest.TestCase):
    def test_normalization_occurs_only_once_only_for_self(self):
        own = b'"tests/phase10_perception_scope_migration.py": "' + b"1" * 64 + b'",'
        other = b'"other.py": "' + b"2" * 64 + b'",'
        data = own + b"\r\n" + other
        normalized = own.replace(b"1" * 64, b"0" * 64) + b"\r\n" + other
        self.assertEqual(gate._digest(gate.SELF, data), hashlib.sha256(normalized).hexdigest())
        self.assertEqual(gate._digest("other.py", data), hashlib.sha256(data).hexdigest())
        for bad in (other, own + own):
            with self.assertRaises(AssertionError):
                gate._digest(gate.SELF, bad)
        self.assertNotEqual(gate._digest(gate.SELF, data), gate._digest(gate.SELF, data + b"x"))

    def test_real_git_blob_and_tree_wire_format(self):
        # Known Git empty tree and hello-newline blob identities.
        self.assertEqual(gate._tree_oid({}), "4b825dc642cb6eb9a060e54bf8d69288fbee4904")
        hello = "ce013625030ba8dba906f756967f9e9ca394464a"
        self.assertEqual(gate._blob(b"hello\n"), hello)
        nested = object_oid("tree", b"100644 x\0" + bytes.fromhex(hello))
        # Git compares directory names as if suffixed by slash: a.c sorts first.
        expected = object_oid("tree", b"100644 a.c\0" + bytes.fromhex(hello)
                              + b"40000 a\0" + bytes.fromhex(nested))
        self.assertEqual(gate._tree_oid({"a/x": ("100644", hello),
                                        "a.c": ("100644", hello)}), expected)

    def test_aliased_noncanonical_linked_and_file_directory_tree_entries(self):
        oid = "a" * 40
        for entries in (
                {"A/x": ("100644", oid), "a/y": ("100644", oid)},
                {"x": ("100644", oid), "x/y": ("100644", oid)},
                {"x/y": ("100644", oid), "x": ("100644", oid)},
                {"x": ("120000", oid)}, {"x": ("160000", oid)},
                {"docs/con.txt": ("100644", oid)}, {"docs/a./x": ("100644", oid)},
                {"docs/../x": ("100644", oid)}, {"docs\\x": ("100644", oid)},
                {"docs/e\u0301.txt": ("100644", oid)}):
            with self.subTest(entries=entries), self.assertRaises(AssertionError):
                gate._tree_oid(entries)

    def test_branch_rejection_and_public_b_delegation_have_no_fallback(self):
        for raw in (b"nayeon-v1\n", b"another\n", b"", (gate.BRANCH + " \n").encode()):
            calls = []
            def git(*query):
                calls.append(query)
                return b"sha1\n" if query == ("rev-parse", "--show-object-format") else raw
            with mock.patch.object(gate, "_git", side_effect=git):
                with self.assertRaisesRegex(AssertionError, "wrong exact branch"):
                    gate.assert_phase10_integrity()
            self.assertEqual(calls[-1], ("branch", "--show-current"))
        with mock.patch.object(gate, "assert_phase10_integrity", side_effect=AssertionError("POISON")) as live:
            with mock.patch.object(b_gate, "_assert_byok_b_historical") as old:
                with self.assertRaisesRegex(AssertionError, "^POISON$"):
                    b_gate.assert_byok_b_integrity()
                self.assertEqual(live.call_count, 1)
                old.assert_not_called()

    def test_index_hidden_flags_modes_duplicate_and_ignored_inventory(self):
        entries = {"frozen.py": ("100644", "a" * 40)}
        queries = {
            ("ls-files", "--stage", "-z"): inventory(entries),
            ("ls-files", "-v", "--sparse", "-z"): b"H frozen.py\0",
            ("ls-files", "--others", "--exclude-standard", "-z"): b"",
            ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"): b"",
        }
        with mock.patch.object(gate, "_git", side_effect=lambda *q: queries[q]):
            self.assertEqual(gate._working_inventory(entries), (entries, set()))
        stage = ("ls-files", "--stage", "-z")
        flags = ("ls-files", "-v", "--sparse", "-z")
        cases = [(flags, p + b" frozen.py\0") for p in (b"h", b"S", b"s")]
        cases += [(flags, b"H frozen.py\0H frozen.py\0"), (flags, b""),
                  (stage, queries[stage] * 2),
                  (stage, queries[stage].replace(b"100644", b"120000")),
                  (stage, queries[stage].replace(b" 0\t", b" 2\t")),
                  (stage, queries[stage] + b"100644 " + b"a" * 40 + b" 0\tFROZEN.py\0"),
                  (stage, queries[stage][:-1]),
                  (("ls-files", "--others", "--exclude-standard", "-z"), b"a\0a\0"),
                  (("ls-files", "--others", "--ignored", "--exclude-standard", "-z"), b"extra.py\0")]
        for query, altered in cases:
            reached = []
            def git(*q):
                if q == query:
                    reached.append(q)
                    return altered
                return queries[q]
            with self.subTest(query=query, altered=altered), mock.patch.object(gate, "_git", side_effect=git):
                with self.assertRaises(AssertionError):
                    gate._working_inventory(entries)
            self.assertEqual(reached, [query])

    def test_real_disk_reader_refuses_link_reparse_hardlink_and_nonregular(self):
        actual = Path.lstat
        target = gate.ROOT / gate.SELF
        for mode, links, attrs in ((stat.S_IFLNK, 1, 0), (stat.S_IFDIR, 1, 0),
                                   (stat.S_IFREG, 2, 0), (stat.S_IFREG, 1, 0x400)):
            info = mock.Mock(st_mode=mode, st_nlink=links, st_file_attributes=attrs)
            reached = []
            def lstat(path):
                if path == target:
                    reached.append(path)
                    return info
                return actual(path)
            with mock.patch.object(Path, "lstat", lstat):
                with self.assertRaises(AssertionError):
                    gate._disk(gate.SELF)
            self.assertEqual(reached, [target])


class NativeAdmissionTests(unittest.TestCase):
    """Real Git/disk/source evidence. No fake Git or expected-pin substitutions."""

    def test_authenticated_B_complete_source_and_append_only_historical_wrapper(self):
        baseline = gate._baseline()
        self.assertEqual(gate._tree_oid(baseline), gate.PARENT_TREE)
        sealed = gate._git("show", gate.PARENT + ":tests/phase8_byok_b_scope_migration.py")
        self.assertTrue(gate._disk("tests/phase8_byok_b_scope_migration.py").startswith(sealed))
        self.assertIsNot(b_gate._assert_byok_b_historical, b_gate.assert_byok_b_integrity)

    def test_real_native_full_admission_required_independently(self):
        self.assertIn(gate.assert_phase10_integrity(), STATES)
        self.assertIn(b_gate.assert_byok_b_integrity(), STATES)

    def test_actual_live_candidate_and_frozen_reader_tamper_has_exact_reach(self):
        # Native Phase 10.2 admission FIRST, then genuine disk tamper.
        # Old Phase 10.1 envelope/error expectations are historical fixtures,
        # not the current Phase 10.2 permission-source inventory.
        from tests import phase10_2_privacy_scope_migration as current
        self.assertIn(current.assert_phase10_2_privacy_integrity(), STATES)
        baseline = current._baseline()
        frozen = "nayeon/brain/onboarding_coordination.py"
        self.assertIn(frozen, baseline)
        self.assertNotIn(frozen, current.ENVELOPE)
        actual = current._disk
        for target in sorted(current.ENVELOPE | {frozen}):
            reached = []
            def corrupt(path):
                raw = actual(path)
                if path == target:
                    reached.append(path)
                    return raw + b"untrusted"
                return raw
            cause = ("frozen source modified" if target == frozen
                     else "candidate byte mismatch")
            with self.subTest(target=target), mock.patch.object(
                    current, "_disk", side_effect=corrupt):
                with self.assertRaisesRegex(
                        AssertionError, r"^Phase10\.2 " + cause + r": "):
                    current.assert_phase10_2_privacy_integrity()
            self.assertEqual(reached, [target])
        self.assertIn(current.assert_phase10_2_privacy_integrity(), STATES)

    def test_forged_B_tag_commit_tree_and_historical_blob_queries_are_reached(self):
        self.assertEqual(gate._tree_oid(gate._baseline()), gate.PARENT_TREE)
        actual = gate._git
        targets = (
            (("show-ref", "--verify", "--hash", "--", "refs/tags/" + gate.PARENT_TAG), b"a" * 40 + b"\n"),
            (("cat-file", "-t", gate.PARENT_TAG_OBJECT), b"commit\n"),
            (("cat-file", "tag", gate.PARENT_TAG_OBJECT), b"forged tag\n"),
            (("cat-file", "commit", gate.PARENT), b"forged commit\n"),
            (("rev-parse", gate.PARENT + "^{tree}"), b"a" * 40 + b"\n"),
            (("rev-parse", "--verify", "--end-of-options", gate.PARENT_TAG_OBJECT + "^{}"), b"a" * 40 + b"\n"),
            (("ls-tree", "-r", "-z", "--full-tree", gate.PARENT), b""),
            (("show", gate.PARENT + ":.codex/CURRENT_STATE.md"), b"forged context\n"),
        )
        for query, payload in targets:
            reached = []
            def corrupt(*q):
                if q == query:
                    reached.append(q)
                    return payload
                return actual(*q)
            with self.subTest(query=query), mock.patch.object(gate, "_git", side_effect=corrupt):
                with self.assertRaises(AssertionError):
                    gate._baseline()
            self.assertEqual(reached, [query])


if __name__ == "__main__":
    unittest.main()
