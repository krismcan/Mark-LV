"""UNTESTED source: fictional parsers are separate from native live admission.

The historical fixture authenticates sealed bytes before installing any read
seam. It never changes pins or acts as a fallback in a source gate.
"""
from contextlib import ExitStack, contextmanager
import ast
import hashlib
from pathlib import Path
import re
import stat
import unittest
from unittest import mock

from tests import phase10_3_scope_migration as gate

STATES = ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD")


def _object(kind, body):
    return hashlib.sha1(kind.encode() + b" " + str(len(body)).encode()
                        + b"\0" + body).hexdigest()


def _raw(before, after, paths, *, work=False):
    rows = []
    for path in sorted(paths):
        old_mode, old_oid = before.get(path, ("000000", "0" * 40))
        new_mode, new_oid = (old_mode, "0" * 40) if work else after[path]
        status = "M" if path in before else "A"
        rows.append(f":{old_mode} {new_mode} {old_oid} {new_oid} {status}".encode()
                    + b"\0" + path.encode() + b"\0")
    return b"".join(rows)


def _index(entries):
    return b"".join(f"{mode} {oid} 0\t{p}".encode() + b"\0"
                    for p, (mode, oid) in sorted(entries.items()))


def _paths(paths):
    return b"".join(p.encode() + b"\0" for p in sorted(paths))


@contextmanager
def sealed_phase10_2(state="COMPLETE_UNSTAGED"):
    """Immutable 10.2 source under its original three-source delta topology.

    Native caller must prove live admission separately, outside this context.
    Reads of every fixture byte are bound to the authenticated 456-file tree.
    Only the explicit test context selects the saved private historical body.
    """
    from tests import phase_8_30_scope_migration as projection
    old = gate.historical
    if state not in STATES:
        raise AssertionError("Unknown historical fixture state")
    sealed = gate._baseline()
    before = old._baseline()
    real = projection._git
    content = {}
    for path, (_, oid) in sealed.items():
        body = real("show", gate.PARENT + ":" + path)
        if _object("blob", body) != oid:
            raise AssertionError("Unauthenticated historical fixture bytes")
        content[path] = body
    # Recheck the sealed 14-path manifest before substituting read seams.
    for path, pin in old.CANDIDATE_SHA256.items():
        if old._digest(path, content[path]) != pin:
            raise AssertionError("Historical fixture pin drift")
    index = before if state == "COMPLETE_UNSTAGED" else sealed
    head = gate.PARENT if state == "EXACT_CHILD" else old.PARENT
    untracked = old.ADDED if state == "COMPLETE_UNSTAGED" else set()
    baseline_views = {}
    for baseline in projection._PHASE10_2_DELTA_BASELINES:
        base = gate._tree(baseline)
        baseline_views[baseline] = {
            p for p in set(base) | set(index)
            if p.startswith("nayeon/") and base.get(p) != index.get(p)}

    def git(*args):
        if args == ("branch", "--show-current"):
            return (old.BRANCH + "\n").encode()
        if args == ("rev-parse", "HEAD"):
            return (head + "\n").encode()
        if args == ("ls-files", "--stage", "-z"):
            return _index(index)
        if args == ("ls-files", "-v", "--sparse", "-z"):
            return b"".join(b"H " + p.encode() + b"\0" for p in sorted(index))
        if args == ("ls-files", "--others", "--exclude-standard", "-z"):
            return _paths(untracked)
        if args == ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
            return b""
        if args == old.RAW:
            return _raw(index, sealed, old.MODIFIED if state == "COMPLETE_UNSTAGED" else set(), work=True)
        if args == old.RAW + ("--cached",):
            return _raw(before, sealed, old.ENVELOPE) if state == "EXACT_STAGED" else b""
        if args == old.RAW + (old.PARENT, gate.PARENT):
            return _raw(before, sealed, old.ENVELOPE)
        if args == ("ls-files", "--stage", "-z", "--", *sorted(projection._PHASE10_2_TRIO)):
            return _index({p: index[p] for p in projection._PHASE10_2_TRIO if p in index})
        if args == ("ls-files", "--others", "--exclude-standard", "-z", "--", "nayeon"):
            return _paths({p for p in untracked if p.startswith("nayeon/")})
        for baseline, paths in baseline_views.items():
            if args == ("diff", "--no-renames", "--name-only", "-z", baseline, "--", "nayeon"):
                return _paths(paths)
        # Only immutable object/ref reads may reach real Git in this fixture.
        if args[0] in {"show", "ls-tree", "cat-file", "show-ref", "rev-list"}:
            return real(*args)
        if args[0] == "rev-parse" and args != ("rev-parse", "HEAD"):
            return real(*args)
        raise AssertionError("Unmapped historical Git query")

    def disk(path):
        if path not in content:
            raise AssertionError("Unknown historical fixture path")
        return content[path]

    with ExitStack() as stack:
        stack.enter_context(mock.patch.object(projection, "_git", side_effect=git))
        stack.enter_context(mock.patch.object(old, "_disk", side_effect=disk))
        stack.enter_context(mock.patch.object(old, "assert_phase10_2_privacy_integrity",
                                              old._phase10_2_historical_assert))
        yield


def _fiction(state, *, parent=None):
    before = {p: ("100644", _object("blob", ("before " + p).encode()))
              for p in gate.MODIFIED | {"sealed.py"}}
    after = dict(before)
    after.update({p: ("100644", _object("blob", ("after " + p).encode())) for p in gate.ENVELOPE})
    parent = gate.PARENT if parent is None else parent
    body = ("tree " + gate.prior._tree_oid(after) + "\nparent " + parent + "\n"
            "author Test <test@example.invalid> 0 +0000\n"
            "committer Test <test@example.invalid> 0 +0000\n\nfixture\n").encode()
    child = _object("commit", body)
    head = child if state == "EXACT_CHILD" else gate.PARENT
    committed = after if state == "EXACT_CHILD" else before
    index = before if state == "COMPLETE_UNSTAGED" else after
    untracked = set(gate.ADDED) if state == "COMPLETE_UNSTAGED" else set()
    work = _raw(index, after, gate.MODIFIED if state == "COMPLETE_UNSTAGED" else set(), work=True)

    def git(*args):
        if args == gate.RAW + ("--cached",):
            return _raw(before, after, gate.ENVELOPE) if state == "EXACT_STAGED" else b""
        if args == ("cat-file", "-t", child):
            return b"commit\n"
        if args == ("cat-file", "commit", child):
            return body
        if args == ("rev-list", "--parents", "-n", "1", child):
            return (child + " " + parent + "\n").encode()
        if args == gate.RAW + (gate.PARENT, child):
            return _raw(before, after, gate.ENVELOPE)
        raise AssertionError("Unexpected fictional query")
    return [head, before, after, committed, index, untracked, work], git


class ManifestTests(unittest.TestCase):
    def test_exact_six_added_eight_modified_fourteen_path_manifest(self):
        added = frozenset({
            "tests/phase10_3_synthetic_provenance_fixture.py",
            "tests/phase10_3_independent_redaction_oracle.py",
            "tests/test_phase10_3_synthetic_provenance_redaction.py",
            "tests/phase10_3_scope_migration.py",
            "tests/test_phase10_3_scope_integrity.py",
            "docs/phase10_3_synthetic_provenance_redaction_rfc.md",
        })
        modified = frozenset({
            "tests/phase10_2_privacy_scope_migration.py",
            "tests/test_phase10_2_privacy_scope_integrity.py",
            "tests/test_phase10_perception_scope_integrity.py",
            "tests/test_phase_836_scope_integrity.py",
            "tests/test_phase_837_scope_integrity.py",
            "tests/test_phase_832_scope_integrity.py",
            "tests/test_phase_833_scope_integrity.py",
            "tests/test_phase_834_scope_integrity.py",
        })
        self.assertEqual(gate.ADDED, added)
        self.assertEqual(gate.MODIFIED, modified)
        self.assertFalse(added & modified)
        self.assertEqual(gate.ENVELOPE, added | modified)
        self.assertEqual((len(gate.ADDED), len(gate.MODIFIED), len(gate.ENVELOPE)), (6, 8, 14))
        baseline = {p: ("100644", "1" * 40) for p in modified}
        gate._manifest(baseline)
        for changed in (dict(gate.CANDIDATE_SHA256, **{"unexpected.py": "1" * 64}),
                        {p: pin for p, pin in gate.CANDIDATE_SHA256.items() if p != gate.SELF}):
            with self.subTest(keys=sorted(changed)), mock.patch.object(gate, "CANDIDATE_SHA256", changed):
                with self.assertRaisesRegex(AssertionError, r"^Phase10\.3 wrong exact manifest$"):
                    gate._manifest(baseline)

    def test_literal_pins_keys_exact_envelope(self):
        source = ast.parse(gate._disk(gate.SELF).decode("utf-8"))
        manifests = [node.value for node in source.body if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == "CANDIDATE_SHA256"
                             for target in node.targets)]
        self.assertEqual(len(manifests), 1)
        manifest = manifests[0]
        self.assertIsInstance(manifest, ast.Dict)
        self.assertEqual(len(manifest.keys), 14)
        for key, value in zip(manifest.keys, manifest.values):
            self.assertIsInstance(key, ast.Constant)
            self.assertIs(type(key.value), str)
            self.assertIsInstance(value, ast.Constant)
            self.assertIs(type(value.value), str)
            self.assertIsNotNone(re.fullmatch(r"[0-9a-f]{64}", value.value))
            self.assertNotEqual(value.value, "0" * 64)
        keys = [key.value for key in manifest.keys]
        self.assertEqual(len(set(keys)), 14)
        self.assertEqual(set(keys), gate.ENVELOPE)
        self.assertEqual(ast.literal_eval(manifest), gate.CANDIDATE_SHA256)


class TopologyTests(unittest.TestCase):
    def test_all_three_exact_parser_states(self):
        for state in STATES:
            args, git = _fiction(state)
            with self.subTest(state=state), mock.patch.object(gate, "_git", side_effect=git):
                self.assertEqual(gate._prove_topology(*args), state)

    def test_partial_stage_extra_untracked_forged_blob_and_wrong_parent(self):
        for state in STATES:
            for fault in ("extra", "blob"):
                args, git = _fiction(state)
                args[4] = dict(args[4])
                args[5] = set(args[5])
                if fault == "extra":
                    args[5].add("unexpected.py")
                else:
                    args[4]["sealed.py"] = ("100644", "f" * 40)
                with self.subTest(state=state, fault=fault), mock.patch.object(gate, "_git", side_effect=git):
                    with self.assertRaises(AssertionError):
                        gate._prove_topology(*args)
        args, git = _fiction("EXACT_STAGED")
        args[4] = dict(args[4])
        key = sorted(gate.MODIFIED)[0]
        args[4][key] = args[1][key]
        with mock.patch.object(gate, "_git", side_effect=git):
            with self.assertRaisesRegex(AssertionError, "^Phase10.2 partial stage$"):
                gate._prove_topology(*args)
        for parent in ("f" * 40, gate.PARENT + "\nparent " + "f" * 40):
            args, git = _fiction("EXACT_CHILD", parent=parent)
            with mock.patch.object(gate, "_git", side_effect=git):
                with self.assertRaisesRegex(AssertionError, "immediate sealed child"):
                    gate._prove_topology(*args)

    def test_self_normalization_exactly_once(self):
        raw = b'"tests/phase10_3_scope_migration.py": "' + b"1" * 64 + b'",'
        self.assertEqual(gate._digest(gate.SELF, raw), hashlib.sha256(raw.replace(b"1" * 64, b"0" * 64)).hexdigest())
        self.assertEqual(gate._digest("other.py", raw), hashlib.sha256(raw).hexdigest())
        for invalid in (b"missing", raw + raw):
            with self.assertRaises(AssertionError):
                gate._digest(gate.SELF, invalid)

    def test_links_reparse_and_hardlink_metadata_refused(self):
        target = gate.ROOT / gate.SELF
        real = Path.lstat
        for mode, attrs, links in ((stat.S_IFLNK | 0o644, 0, 1),
                                   (stat.S_IFREG | 0o644, 0x400, 1),
                                   (stat.S_IFREG | 0o644, 0, 2)):
            info = mock.Mock(st_mode=mode, st_file_attributes=attrs, st_nlink=links)
            reached = []
            def lstat(path):
                if path == target:
                    reached.append(path)
                    return info
                return real(path)
            with self.subTest(mode=mode, attrs=attrs, links=links), mock.patch.object(Path, "lstat", lstat):
                with self.assertRaises(AssertionError):
                    gate._disk(gate.SELF)
            self.assertEqual(reached, [target])


class NativeAdmissionTests(unittest.TestCase):
    def test_protected_state_excluded_and_frozen_in_sealed_inventory(self):
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)
        path = ".codex/CURRENT_STATE.md"
        for candidate in (gate.ADDED, gate.MODIFIED, gate.ENVELOPE, gate.CANDIDATE_SHA256):
            self.assertNotIn(path, candidate)
        baseline = gate._baseline()
        self.assertEqual(len(baseline), 456)
        self.assertIn(path, baseline)
        self.assertIn(path, gate.historical.MODIFIED)
        self.assertIn(path, gate.historical.CANDIDATE_SHA256)
        sealed = gate._git("show", gate.PARENT + ":" + path)
        self.assertEqual(baseline[path], ("100644", gate.prior._blob(sealed)))
        self.assertEqual(hashlib.sha256(sealed).hexdigest(),
                         "5775c68f8d0428004de85c9a2695fd7d06ea8bb98d3e8dbbfdf2fe647e8373a1")
        self.assertEqual(gate._disk(path), sealed)
        real_disk = gate._disk
        reached = []
        def corrupt(p):
            raw = real_disk(p)
            if p == path:
                reached.append(p)
                return raw + b"tamper"
            return raw
        with mock.patch.object(gate, "_disk", side_effect=corrupt):
            with self.assertRaisesRegex(AssertionError,
                                        r"^Phase10\.2 frozen source modified: \.codex/CURRENT_STATE\.md$"):
                gate.assert_phase10_3_integrity()
        self.assertEqual(reached, [path])
        self.assertEqual(gate._disk(path), sealed)
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)

    def test_wrong_branch_extra_ignored_index_alias_and_forged_staged_blob(self):
        state = gate.assert_phase10_3_integrity()
        self.assertIn(state, STATES)
        real = gate._git
        key_index = ("ls-files", "--stage", "-z")
        cases = (
            (("branch", "--show-current"), lambda raw: b"wrong\n"),
            (("ls-files", "--others", "--exclude-standard", "-z"),
             lambda raw: raw + b"unexpected.py\0"),
            (("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
             lambda raw: b"hidden.py\0"),
            (key_index, lambda raw: raw + raw.split(b"\0", 1)[0] + b"\0"),
            (key_index, lambda raw: raw.replace(b"\ttests/", b"\tTests/", 1)),
        )
        for query, transform in cases:
            reached = []
            def corrupt(*args):
                raw = real(*args)
                if args == query:
                    reached.append(args)
                    return transform(raw)
                return raw
            with self.subTest(query=query), mock.patch.object(gate, "_git", side_effect=corrupt):
                with self.assertRaises(AssertionError):
                    gate.assert_phase10_3_integrity()
            self.assertEqual(reached, [query])
            self.assertIn(gate.assert_phase10_3_integrity(), STATES)
        target = b"nayeon/desktop_alpha/window.py"
        reached = []
        def forged(*args):
            raw = real(*args)
            if args == key_index:
                rows = raw.split(b"\0")
                for i, row in enumerate(rows):
                    if row.endswith(b"\t" + target):
                        reached.append(args)
                        rows[i] = b"100644 " + b"f" * 40 + b" 0\t" + target
                        return b"\0".join(rows)
                raise AssertionError("Frozen staged target absent")
            return raw
        with mock.patch.object(gate, "_git", side_effect=forged):
            expected = "unapproved child inventory" if state == "EXACT_CHILD" else "partial stage"
            with self.assertRaisesRegex(AssertionError, "^Phase10.2 " + expected + "$"):
                gate.assert_phase10_3_integrity()
        self.assertEqual(reached, [key_index])
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)

    def test_live_and_unconditional_predecessor_route(self):
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)
        with mock.patch.object(gate, "assert_phase10_3_integrity", wraps=gate.assert_phase10_3_integrity) as route:
            self.assertIn(gate.historical.assert_phase10_2_privacy_integrity(), STATES)
        route.assert_called_once_with()
        with mock.patch.object(gate, "assert_phase10_3_integrity", side_effect=AssertionError("fixed refusal")), mock.patch.object(
                gate.historical, "_phase10_2_historical_assert", side_effect=AssertionError("fallback reached")) as fallback:
            with self.assertRaisesRegex(AssertionError, "^fixed refusal$"):
                gate.historical.assert_phase10_2_privacy_integrity()
        fallback.assert_not_called()
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)

    def test_authenticated_historical_original_topologies_and_frozen_reader(self):
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)
        for state in STATES:
            with self.subTest(state=state), sealed_phase10_2(state):
                old = gate.historical
                self.assertEqual(old._phase10_2_historical_assert(), state)
                path = "nayeon/perception/contracts.py"
                actual = old._disk
                reached = []
                def corrupt(p):
                    value = actual(p)
                    if p == path:
                        reached.append(p)
                        return value + b"tamper"
                    return value
                with mock.patch.object(old, "_disk", side_effect=corrupt):
                    with self.assertRaisesRegex(AssertionError, "^Phase10.2 frozen source modified: "):
                        old._phase10_2_historical_assert()
                self.assertEqual(reached, [path])
                self.assertEqual(old._phase10_2_historical_assert(), state)
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)

    def test_post_import_self_pin_literal_tamper_refused(self):
        # Only the literal itself changes, retaining the normalized digest.
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)
        original = gate._disk
        # P80 review-only migration: the historical self-pin authenticates
        # the sealed Phase10.3 parent Git blob, not the appended C1 router.
        raw = gate._git("show", "cacb5c320d26ffa28faf1f15a5e088029ee1453b:" + gate.SELF)
        self.assertEqual(gate.prior._blob(raw),
                         gate._tree("cacb5c320d26ffa28faf1f15a5e088029ee1453b")[gate.SELF][1])
        self.assertTrue(original(gate.SELF).startswith(raw))
        matches = list(gate.SELF_PIN.finditer(raw))
        self.assertEqual(len(matches), 1)
        match = matches[0]
        prior_pin = raw[match.end(1):match.start(2)]
        self.assertEqual(prior_pin, gate.CANDIDATE_SHA256[gate.SELF].encode("ascii"))
        forged_pin = b"f" * 64 if prior_pin != b"f" * 64 else b"e" * 64
        forged = raw[:match.end(1)] + forged_pin + raw[match.start(2):]
        # Old normalization by itself is insufficient: both digests agree.
        self.assertEqual(gate._digest(gate.SELF, forged),
                         gate.CANDIDATE_SHA256[gate.SELF])
        reached = []
        def tampered_disk(path):
            if path == gate.SELF:
                reached.append(path)
                return forged
            return original(path)
        with mock.patch.object(gate, "_disk", side_effect=tampered_disk):
            with self.assertRaisesRegex(AssertionError,
                                        r"^Phase10\.3 self-pin literal mismatch$"):
                gate.assert_phase10_3_integrity()
        self.assertEqual(reached, [gate.SELF])
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)

    def test_three_amended_historical_sources_are_literally_pinned(self):
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)
        original_disk = gate._disk
        for target in (
                "tests/test_phase_832_scope_integrity.py",
                "tests/test_phase_833_scope_integrity.py",
                "tests/test_phase_834_scope_integrity.py"):
            reached = []
            def corrupt(path):
                raw = original_disk(path)
                if path == target:
                    reached.append(path)
                    return raw + b"tampered"
                return raw
            with self.subTest(target=target), mock.patch.object(
                    gate, "_disk", side_effect=corrupt):
                with self.assertRaisesRegex(
                        AssertionError,
                        r"^Phase10\.2 candidate byte mismatch: " + re.escape(target) + r"$"):
                    gate.assert_phase10_3_integrity()
            self.assertEqual(reached, [target])
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)

    def test_exact_parent_inventory_and_raw_object_tamper_reach(self):
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)
        baseline = gate._baseline()
        self.assertEqual(len(baseline), 456)
        self.assertEqual(gate.prior._tree_oid(baseline), gate.PARENT_TREE)
        real = gate._git
        queries = (
            (("cat-file", "tag", gate.PARENT_TAG_OBJECT), b"forged\n"),
            (("cat-file", "commit", gate.PARENT), b"forged\n"),
            (("ls-tree", "-r", "-z", "--full-tree", gate.PARENT), b""),
            (("show", gate.PARENT + ":" + gate.historical.SELF), b"forged\n"),
            (("show-ref", "--verify", "--hash", "--", "refs/tags/" + gate.PARENT_TAG), b"f" * 40 + b"\n"),
        )
        for query, payload in queries:
            reached = []
            def corrupt(*args):
                if args == query:
                    reached.append(args)
                    return payload
                return real(*args)
            with self.subTest(query=query), mock.patch.object(gate, "_git", side_effect=corrupt):
                with self.assertRaises(AssertionError):
                    gate.assert_phase10_3_integrity()
            self.assertEqual(reached, [query])
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)

    def test_ref_and_disk_read_drift_refused(self):
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)
        for query, bad in ((("rev-parse", "HEAD"), b"f" * 40 + b"\n"),
                           (("branch", "--show-current"), b"wrong\n"),
                           (("show-ref", "--verify", "--hash", "--", "refs/tags/" + gate.PARENT_TAG), b"f" * 40 + b"\n")):
            real = gate._git
            reached = []
            def drift(*args):
                if args == query:
                    reached.append(args)
                    if len(reached) == 2:
                        return bad
                return real(*args)
            with self.subTest(query=query), mock.patch.object(gate, "_git", side_effect=drift):
                with self.assertRaises(AssertionError):
                    gate.assert_phase10_3_integrity()
            self.assertEqual(reached, [query, query])
        real_disk = gate._disk
        reached = []
        def changed(path):
            raw = real_disk(path)
            if path == gate.SELF:
                reached.append(path)
                if len(reached) == 2:
                    return raw + b"changed"
            return raw
        with mock.patch.object(gate, "_disk", side_effect=changed):
            with self.assertRaisesRegex(AssertionError, "^Phase10.2 candidate byte mismatch: "):
                gate.assert_phase10_3_integrity()
        self.assertEqual(reached, [gate.SELF, gate.SELF])
        self.assertIn(gate.assert_phase10_3_integrity(), STATES)


if __name__ == "__main__":
    unittest.main()
