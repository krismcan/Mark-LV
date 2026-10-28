"""B exact23 adversaries. Read-only Git/disk seams; no stage/commit/writes.

Synthetic current Git records use the reviewed real source bytes and STATIC B
pins. No fixture recomputes/patches source digests or the approved envelope.
The public live test must fail until all twenty-three approved paths are complete.
"""
from contextlib import contextmanager, ExitStack
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import stat
import unittest
from unittest import mock

from tests import phase8_byok_b_scope_migration as gate
from tests import phase8_byok_scope_migration as historical

STATES = ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD")
RAW = ("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
CHILD = "e" * 40


@lru_cache(maxsize=None)
def sealed_bytes(path):
    # Cache only immutable fixture blobs, never a successful admission.
    return gate._git("show", gate.PARENT + ":" + path)


def inventory(entries, *, index=False):
    return b"".join((f"{mode} {oid} 0\t{p}" if index else
                    f"{mode} blob {oid}\t{p}").encode() + b"\0"
                    for p, (mode, oid) in sorted(entries.items()))


def delta(before, after, paths):
    rows = []
    for p in sorted(paths):
        om, oi = before.get(p, ("000000", "0" * 40))
        nm, ni = after[p]
        status = "A" if p not in before else "M"
        rows.append(f":{om} {nm} {oi} {ni} {status}".encode()
                    + b"\0" + p.encode() + b"\0")
    return b"".join(rows)


@contextmanager
def candidate(state="COMPLETE_UNSTAGED", *, transform=None, stage_paths=None,
              index_mutation=None, committed_mutation=None,
              parent=None, merge=False, disk_mutation=None):
    """Exercise real parsers, static source pins and seals with fake current Git."""
    actual = gate.prior._git
    baseline = gate.prior._tree(gate.PARENT)
    data = {p: gate._disk(p) for p in gate.ENVELOPE}
    # The host-protected CURRENT_STATE is the only intentionally unfinished
    # candidate file. Synthesize ONLY its already SHA-pinned intended bytes,
    # from the independently reviewed static design checkpoint, in memory.
    # The live real-Git admission below never receives this substitution.
    state_path = ".codex/CURRENT_STATE.md"
    design = data["docs/phase8_first_run_connection_ui_design.md"]
    fenced = re.search(rb"(?s)\x60\x60\x60text\r?\n(.*?)\r?\n\x60\x60\x60", design)
    if fenced is None:
        raise AssertionError("Missing reviewed checkpoint prefix")
    prefix = fenced.group(1).replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    raw_state = data[state_path]
    current_hash = hashlib.sha256(raw_state).hexdigest()
    # Before the separately approved host write, synthesize the single
    # pinned final image from the exact sealed original preimage. Afterwards,
    # use the actual final bytes unchanged. All other states fail closed.
    original_preimage_pin = "9a81ed97ce49c524acd48bc5f3d3ad3fdf73e3b9493d227be61d26690817b8fa"
    if current_hash == original_preimage_pin:
        planned_state = prefix + b"\r\n\r\n" + raw_state
    elif current_hash == gate.CANDIDATE_SHA256[state_path]:
        planned_state = raw_state
    else:
        raise AssertionError("Unapproved CURRENT_STATE preimage in synthetic fixture")
    if hashlib.sha256(planned_state).hexdigest() != gate.CANDIDATE_SHA256[state_path]:
        raise AssertionError("Planned checkpoint not equal to literal B pin")
    data[state_path] = planned_state
    expected = dict(baseline)
    expected.update({p: ("100644", gate.prior._blob(b)) for p, b in data.items()})
    head = CHILD if state == "EXACT_CHILD" else gate.PARENT
    committed = dict(expected if state == "EXACT_CHILD" else baseline)
    selected = (set() if state == "COMPLETE_UNSTAGED" else set(gate.ENVELOPE))
    if stage_paths is not None:
        selected = set(stage_paths)
    index = dict(baseline)
    index.update({p: expected[p] for p in selected})
    if index_mutation:
        index_mutation(index)
    if committed_mutation:
        committed_mutation(committed)
    untracked = gate.ADDED - set(index)
    working = {p for p in gate.MODIFIED if index.get(p) != expected[p]}
    calls = []

    def git(*args):
        calls.append(args)
        if args == ("rev-parse", "--show-object-format"):
            value = b"sha1\n"
        elif args == ("rev-parse", "HEAD"):
            value = (head + "\n").encode()
        elif args == ("branch", "--show-current"):
            value = b"nayeon-v1\n"
        elif args[:2] == ("merge-base", "--is-ancestor"):
            # Authentic old-chain ancestry/seal bytes remain checked below.
            if args[2] not in {gate.prior.PROTECTED, gate.PARENT}:
                raise AssertionError("Unexpected synthetic ancestry query")
            value = b""
        elif args == ("ls-tree", "-r", "-z", "--full-tree", head):
            value = inventory(committed)
        elif args == ("ls-files", "--stage", "-z"):
            value = inventory(index, index=True)
        elif args == ("ls-files", "-v", "--sparse", "-z"):
            value = b"".join(b"H " + p.encode() + b"\0" for p in sorted(index))
        elif args == ("ls-files", "--others", "--exclude-standard", "-z"):
            value = b"".join(p.encode() + b"\0" for p in sorted(untracked))
        elif args == ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
            value = b""
        elif args == RAW:
            disk = {**index, **{p: ("100644", "0" * 40) for p in working}}
            value = delta(index, disk, working)
        elif args == RAW + ("--cached",):
            value = delta(baseline, index, selected)
        elif args == RAW + (gate.PARENT, CHILD):
            value = delta(baseline, committed, gate.ENVELOPE)
        elif args == ("rev-list", "--parents", "-n", "1", CHILD):
            value = (CHILD + " " + (parent or gate.PARENT)
                     + (" " + "d" * 40 if merge else "") + "\n").encode()
        else:
            value = actual(*args)
        return transform(args, value) if transform else value

    def disk(path):
        raw = data[path]
        return disk_mutation(path, raw) if disk_mutation else raw

    with ExitStack() as stack:
        stack.enter_context(mock.patch.object(gate.prior, "_git", side_effect=git))
        stack.enter_context(mock.patch.object(gate, "_disk", side_effect=disk))
        stack.enter_context(mock.patch.object(gate.prior, "_frozen",
                                             side_effect=sealed_bytes))
        yield calls


class ExactBYOKBTests(unittest.TestCase):
    def test_literal_exact23_parent_manifest_and_live_admission(self):
        self.assertEqual(gate.PARENT, "4110fa69849f8127a325f9a9001284cd1bd3a59c")
        self.assertEqual(gate.PARENT_TREE, "747f172144794d687251545ca923d5ebb5b1551b")
        self.assertEqual(gate.PARENT_TAG_OBJECT, "7496961c83de9607402dcdabff25917674d6688a")
        self.assertEqual(gate.PARENT_PARENT, historical.PARENT)
        self.assertEqual(len(gate.MODIFIED), 16)
        self.assertEqual(len(gate.ADDED), 7)
        self.assertEqual(len(gate.ENVELOPE), 23)
        self.assertTrue(gate.MODIFIED.isdisjoint(gate.ADDED))
        self.assertEqual(set(gate.CANDIDATE_SHA256), gate.ENVELOPE)
        self.assertIn(gate.assert_byok_b_integrity(), STATES)
        self.assertEqual(historical.assert_byok_integrity(), gate.assert_byok_b_integrity())

    def test_static_pins_and_all_three_synthetic_topologies(self):
        for pin in gate.CANDIDATE_SHA256.values():
            self.assertRegex(pin, r"^[0-9a-f]{64}$")
            self.assertNotEqual(pin, "0" * 64)
        for state in STATES:
            with self.subTest(state=state), candidate(state) as calls:
                self.assertEqual(gate.assert_byok_b_integrity(), state)
                self.assertIn(("ls-files", "--stage", "-z"), calls)
                if state == "EXACT_STAGED":
                    self.assertIn(RAW + ("--cached",), calls)
                if state == "EXACT_CHILD":
                    self.assertIn(RAW + (gate.PARENT, CHILD), calls)

    def test_a_original_source_pins_and_private_body_are_immutable(self):
        sealed = sealed_bytes(historical.SELF)
        live = (gate.ROOT / historical.SELF).read_bytes()
        self.assertTrue(live.startswith(sealed))
        self.assertEqual(historical._digest(historical.SELF, sealed),
                         historical.CANDIDATE_SHA256[historical.SELF])
        self.assertIsNot(historical.assert_byok_integrity,
                         historical._assert_byok_historical)
        self.assertEqual(len(historical.CANDIDATE_SHA256), 11)
        for path, pin in historical.CANDIDATE_SHA256.items():
            self.assertEqual(historical._digest(path, sealed_bytes(path)), pin)
        self.assertEqual(gate._parent_tree(), gate.prior._tree(gate.PARENT))

    def test_every_candidate_source_byte_is_bound(self):
        for target in sorted(gate.ENVELOPE):
            hits = []
            def tamper(path, raw, expected_target=target):
                if path == expected_target:
                    hits.append(path)
                    return raw + b"tamper"
                return raw
            with self.subTest(target=target), candidate(disk_mutation=tamper):
                with self.assertRaisesRegex(AssertionError, "BYOK B candidate byte mismatch"):
                    gate.assert_byok_b_integrity()
            # A mismatch in the *other* pending checkpoint cannot count
            # as a successful tamper canary for this exact target.
            self.assertEqual(hits, [target])

    def test_each_historical_a_pin_remains_an_active_witness(self):
        for target in sorted(historical.ENVELOPE):
            query = ("show", gate.PARENT + ":" + target)
            def inject(args, raw):
                return raw + b"tamper" if args == query else raw
            with self.subTest(target=target), candidate(transform=inject):
                with self.assertRaisesRegex(AssertionError, "BYOK B changed sealed A bytes"):
                    gate.assert_byok_b_integrity()

    def test_parent_tree_ancestry_tag_object_type_and_peel_refused(self):
        cases = (
            (("rev-parse", gate.PARENT + "^{tree}"), b"1" * 40 + b"\n"),
            (("rev-list", "--parents", "-n", "1", gate.PARENT),
             (gate.PARENT + " " + "1" * 40 + "\n").encode()),
            (("show-ref", "--verify", "--hash", "--", "refs/tags/" + gate.PARENT_TAG),
             b"1" * 40 + b"\n"),
            (("cat-file", "-t", gate.PARENT_TAG_OBJECT), b"commit\n"),
            (("cat-file", "-t", gate.PARENT), b"tag\n"),
            (("rev-parse", "--verify", "--end-of-options", gate.PARENT_TAG_OBJECT + "^{}"),
             b"1" * 40 + b"\n"),
            (("branch", "--show-current"), b"another-branch\n"),
            (("rev-parse", "HEAD"), b"short\n"),
            (("rev-parse", "--show-object-format"), b"sha256\n"),
        )
        for query, payload in cases:
            hit = []
            def inject(args, raw):
                if args == query:
                    hit.append(args)
                    return payload
                return raw
            with self.subTest(query=query), candidate(transform=inject):
                with self.assertRaises(AssertionError):
                    gate.assert_byok_b_integrity()
            self.assertTrue(hit)

    def test_partial_stage_extra_stage_merge_and_cherry_pick_parent_refused(self):
        for paths in ({gate.SELF}, set(gate.MODIFIED), gate.ENVELOPE - {gate.SELF}):
            with self.subTest(paths=paths), candidate("EXACT_STAGED", stage_paths=paths):
                with self.assertRaisesRegex(AssertionError, "BYOK B partial stage"):
                    gate.assert_byok_b_integrity()
        for parent, merge in (("d" * 40, False), (gate.PARENT, True)):
            with self.subTest(parent=parent, merge=merge), candidate(
                    "EXACT_CHILD", parent=parent, merge=merge):
                with self.assertRaisesRegex(AssertionError, "BYOK B unexpected commit parent"):
                    gate.assert_byok_b_integrity()
        with candidate("EXACT_STAGED", index_mutation=lambda entries:
                       entries.update({"extra.py": ("100644", "a" * 40)})):
            with self.assertRaises(AssertionError):
                gate.assert_byok_b_integrity()

    def test_unknown_ignored_alias_and_index_flags_refused_in_every_state(self):
        for state in STATES:
            for query, suffix in (
                (("ls-files", "--others", "--exclude-standard", "-z"), b"extra.py\0"),
                (("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
                 b"tests/__pycache__/loader.pyc\0"),
                (("ls-files", "--stage", "-z"),
                 b"100644 " + b"a" * 40 + b" 0\tTests/alias.py\0"),
                (("ls-files", "--stage", "-z"),
                 b"120000 " + b"a" * 40 + b" 0\tlink\0"),
                (("ls-files", "--stage", "-z"),
                 b"100644 " + b"a" * 40 + b" 2\textra.py\0"),
            ):
                with self.subTest(state=state, suffix=suffix), candidate(
                        state, transform=lambda a, b: b + suffix if a == query else b):
                    with self.assertRaises(AssertionError):
                        gate.assert_byok_b_integrity()
            for flag in (b"h ", b"S ", b"s "):
                query = ("ls-files", "-v", "--sparse", "-z")
                with self.subTest(state=state, flag=flag), candidate(
                        state, transform=lambda a, b: flag + b[2:] if a == query else b):
                    with self.assertRaisesRegex(AssertionError, "index flags"):
                        gate.assert_byok_b_integrity()

    def test_raw_git_rename_status_blob_modes_counts_and_worktree_refused(self):
        for state in STATES:
            query = RAW if state == "COMPLETE_UNSTAGED" else (
                RAW + ("--cached",) if state == "EXACT_STAGED"
                else RAW + (gate.PARENT, CHILD))
            for mutate in (
                lambda b: b"",
                lambda b: b[:-1],
                lambda b: b.replace(b" M\0", b" R100\0", 1),
                lambda b: b.replace(b" M\0", b" D\0", 1),
                lambda b: b.replace(b" 100644 ", b" 120000 ", 1),
                lambda b: b.replace(b.split(b"\0")[0].split(b" ")[2], b"f" * 40, 1),
                lambda b: b.replace(b".codex/CURRENT_STATE.md", b".codex/../CURRENT_STATE.md", 1),
                lambda b: b + b.split(b"\0")[0] + b"\0extra.py\0",
            ):
                def inject(args, raw):
                    if args != query:
                        return raw
                    altered = mutate(raw)
                    self.assertNotEqual(altered, raw)
                    return altered
                with self.subTest(state=state, mutate=mutate), candidate(state, transform=inject):
                    with self.assertRaises(AssertionError):
                        gate.assert_byok_b_integrity()

    def test_frozen_commit_index_and_disk_stay_bound(self):
        target = "tests/test_first_run_connection_owner.py"
        for seam in ("index_mutation", "committed_mutation"):
            with self.subTest(seam=seam), candidate("EXACT_CHILD", **{
                    seam: lambda entries: entries.update({target: ("100644", "f" * 40)})}):
                with self.assertRaises(AssertionError):
                    gate.assert_byok_b_integrity()
        with candidate(), mock.patch.object(gate.prior, "_frozen",
                side_effect=lambda p: sealed_bytes(p) + (b"x" if p == target else b"")):
            with self.assertRaisesRegex(AssertionError, "BYOK B frozen disk bytes modified"):
                gate.assert_byok_b_integrity()

    def test_exact_new_window_projection_never_hides_unknowns_or_forged_admission(self):
        from tests import phase_8_30_scope_migration as legacy
        window = "nayeon/desktop_alpha/first_run_connection_window.py"
        unknown = "nayeon/desktop_alpha/unreviewed_window.py"
        for state in STATES:
            with candidate(state):
                self.assertEqual(legacy._project_837_draft_sources({window, unknown}), {unknown})
        for result in (None, True, "UNVERIFIED", "EXACT_CHILD "):
            with mock.patch.object(gate, "assert_byok_b_integrity", return_value=result):
                with self.assertRaisesRegex(AssertionError, "Unadmitted BYOK B window"):
                    legacy._project_837_draft_sources({window, unknown})
        with mock.patch.object(gate, "assert_byok_b_integrity",
                               side_effect=AssertionError("POISONED")):
            with self.assertRaisesRegex(AssertionError, "POISONED"):
                legacy._project_837_draft_sources({window})
            self.assertEqual(legacy._project_837_draft_sources({unknown}), {unknown})

    def test_self_canonicalization_only_zeros_own_single_literal(self):
        own = b'"tests/phase8_byok_b_scope_migration.py": "' + b"1" * 64 + b'",'
        other = b'"tests/phase8_byok_scope_migration.py": "' + b"2" * 64 + b'",'
        raw = own + b"\r\n" + other
        normalized = own.replace(b"1" * 64, b"0" * 64) + b"\r\n" + other
        self.assertEqual(gate._digest(gate.SELF, raw), hashlib.sha256(normalized).hexdigest())
        for malformed in (other, own + own):
            with self.assertRaises(AssertionError):
                gate._digest(gate.SELF, malformed)
        self.assertNotEqual(gate._digest(gate.SELF, raw),
                            gate._digest(gate.SELF, raw.replace(b"\r\n", b"\n")))
        self.assertNotEqual(gate._digest(gate.SELF, raw),
                            gate._digest(gate.SELF, raw + b"x"))
        # Every non-self file, including A's current source, hashes raw bytes.
        self.assertEqual(gate._digest(historical.SELF, raw), hashlib.sha256(raw).hexdigest())

    def test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused(self):
        with candidate(), mock.patch.dict(gate.CANDIDATE_SHA256, {gate.SELF: "0" * 64}):
            with self.assertRaisesRegex(AssertionError, "BYOK B unfinalized source pin"):
                gate.assert_byok_b_integrity()
        pins = dict(gate.CANDIDATE_SHA256)
        del pins[gate.SELF]
        with candidate(), mock.patch.object(gate, "CANDIDATE_SHA256", pins):
            with self.assertRaisesRegex(AssertionError, "BYOK B unapproved manifest"):
                gate.assert_byok_b_integrity()
        with candidate(disk_mutation=lambda p, b:
                b + b"tamper" if p == historical.SELF else b):
            with self.assertRaisesRegex(AssertionError, "BYOK B changed live A adapter bytes"):
                historical.assert_byok_integrity()

    def test_noncanonical_paths_and_extra_parent_inventory_refused(self):
        for paths in ({"other/A/x", "other/a/y"}, {"docs/con.txt"},
                      {"docs/a./x"}, {"docs/../x"}, {"docs\\x"},
                      {"docs/e\u0301.txt"}, {"NAYEON/desktop_alpha/evil.py"}):
            with self.subTest(paths=paths), self.assertRaises(AssertionError):
                gate.prior._canonical_paths(paths)
        query = ("ls-tree", "-r", "-z", "--full-tree", gate.PARENT)
        suffix = b"100644 blob " + b"a" * 40 + b"\textra.py\0"
        with candidate(transform=lambda a, b: b + suffix if a == query else b):
            with self.assertRaisesRegex(AssertionError, "BYOK B changed frozen inventory"):
                gate.assert_byok_b_integrity()

    def test_no_cached_live_success_after_disk_poisoning(self):
        poisoned = [False]
        with candidate(disk_mutation=lambda p, b:
                b + b"x" if poisoned[0] and p == gate.SELF else b):
            self.assertEqual(gate.assert_byok_b_integrity(), "COMPLETE_UNSTAGED")
            poisoned[0] = True
            with self.assertRaisesRegex(AssertionError, "BYOK B candidate byte mismatch"):
                gate.assert_byok_b_integrity()

    def test_disk_readers_refuse_links_reparse_and_hardlinks(self):
        target = gate.ROOT / gate.SELF
        actual = Path.lstat
        for mode, links, attrs in (
                (stat.S_IFLNK, 1, 0), (stat.S_IFDIR, 1, 0),
                (stat.S_IFREG, 2, 0), (stat.S_IFREG, 1, 0x400)):
            info = mock.Mock(st_mode=mode, st_nlink=links, st_file_attributes=attrs)
            def lstat(path):
                return info if path == target else actual(path)
            for reader in (gate._disk, gate.prior._frozen):
                with self.subTest(mode=mode, reader=reader), mock.patch.object(Path, "lstat", lstat):
                    with self.assertRaises(AssertionError):
                        reader(gate.SELF)


# Explicit historical test contexts never grant current B source admission.
def _historical_byok_b_fixtures():
    from tests import test_phase_832_scope_integrity as f832
    from tests import test_phase_833_scope_integrity as f833
    from tests import test_phase_834_scope_integrity as f834
    return (
        (f832, f832.snapshot, f832.scope._assert_832_historical,
         "03f247d8627bf1c51105f73b9de5c6bbdf389cf9"),
        (f833, f833.candidate, f833.scope._assert_833_historical, f833.scope.PROTECTED),
        (f834, f834.candidate, f834.scope._assert_834_historical, f834.scope.PROTECTED),
    )


class BYOKBHistoricalFixtureProjectionTests(unittest.TestCase):
    TARGETS = (
        "nayeon/brain/onboarding_coordination.py",
        "nayeon/brain/onboarding_recovery.py",
    )

    def test_projected_historical_brain_corruption_is_causally_rejected(self):
        self.assertIn(gate.assert_byok_b_integrity(), STATES)
        for fixture, factory, guard, _ in _historical_byok_b_fixtures():
            for state in STATES:
                with self.subTest(fixture=fixture.__name__, state=state), factory(state):
                    self.assertEqual(guard(), state)
                    for target in self.TARGETS:
                        original = fixture.scope._raw_frozen_disk
                        reached = []
                        def corrupt(path):
                            value = original(path)
                            if path == target:
                                reached.append(path)
                                return value + b"untrusted"
                            return value
                        with mock.patch.object(fixture.scope, "_raw_frozen_disk",
                                               side_effect=corrupt):
                            with self.assertRaises(AssertionError):
                                guard()
                        self.assertEqual(reached, [target])
                    self.assertEqual(guard(), state)
        self.assertIn(gate.assert_byok_b_integrity(), STATES)

    def test_forged_historical_brain_preimage_is_rejected_before_replay(self):
        for fixture, factory, guard, sealed in _historical_byok_b_fixtures():
            with factory():
                self.assertEqual(guard(), "COMPLETE_UNSTAGED")
            actual = fixture.prior._git
            for target in self.TARGETS:
                wanted = ("show", sealed + ":" + target)
                reached = []
                def corrupt(*args):
                    value = actual(*args)
                    if args == wanted:
                        reached.append(args)
                        return value + b"untrusted"
                    return value
                with self.subTest(fixture=fixture.__name__, target=target):
                    with mock.patch.object(fixture.prior, "_git", side_effect=corrupt):
                        with self.assertRaisesRegex(AssertionError,
                                "^Immutable BYOK B historical preimage changed$"):
                            with factory():
                                self.fail("Forged historical bytes reached replay")
                    self.assertEqual(reached, [wanted])

    def test_live_brain_reader_tamper_remains_rejected_after_historical_replay(self):
        self.assertIn(gate.assert_byok_b_integrity(), STATES)
        original = gate._disk
        for target in self.TARGETS:
            reached = []
            def corrupt(path):
                value = original(path)
                if path == target:
                    reached.append(path)
                    return value + b"untrusted"
                return value
            with self.subTest(target=target), mock.patch.object(
                    gate, "_disk", side_effect=corrupt):
                with self.assertRaisesRegex(AssertionError,
                        "^BYOK B candidate byte mismatch: " + re.escape(target) + "$"):
                    gate.assert_byok_b_integrity()
            self.assertEqual(reached, [target])
        self.assertIn(gate.assert_byok_b_integrity(), STATES)


if __name__ == "__main__":
    unittest.main()
