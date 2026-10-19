"""Read-only 8.30 historical production-scope security negatives.

All synthetic Git records are injected in memory; Windows junction evidence uses
only a newly owned disposable TemporaryDirectory, never the repository.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from tests import phase_8_30_scope_migration as scope

# Current-reader migration lives only in this approved consumer test module.
# The historical helper and every immutable 8.30 SHA remain untouched.
_historical_approved_source = scope._approved_source


def _current_approved_source(relative):
    if (scope.ROOT / "tests/phase_8_32_scope_migration.py").is_file():
        from tests.phase_8_34_scope_migration import current_source_oid
        return current_source_oid(relative)
    return _historical_approved_source(relative)


scope._approved_source = _current_approved_source

OID = b"1" * 40


def tree_record(path: str) -> bytes:
    return b"100644 blob " + OID + b"\t" + path.encode("utf-8") + b"\0"


def index_record(path: str) -> bytes:
    return b"100644 " + OID + b" 0\t" + path.encode("utf-8") + b"\0"


def replace_or_add_record(raw: bytes, path: str, replacement: bytes) -> bytes:
    """One tampered Git pathname in either an unstaged or committed inventory."""
    encoded = path.encode("utf-8")
    rows = [item for item in raw.split(b"\0") if item]
    matches = [index for index, item in enumerate(rows)
               if item.split(b"\t", 1)[-1] == encoded]
    if len(matches) > 1:
        raise AssertionError("Git test fixture contains duplicate pathnames")
    if matches:
        rows[matches[0]] = replacement.rstrip(b"\0")
    else:
        rows.append(replacement.rstrip(b"\0"))
    return b"\0".join(rows) + b"\0"


def _staged_application_error_pattern(historical_pattern):
    """Validate the original snapshot before accepting an injection error."""
    if (scope.ROOT / "tests/phase_8_32_scope_migration.py").is_file():
        from tests.phase_8_32_scope_migration import _assert_832_historical
        state = _assert_832_historical()
        patterns = {
            "COMPLETE_UNSTAGED": "^Partial 8.32 staged snapshot refused$",
            "EXACT_STAGED": "^8.32 index/disk disagreement$",
            "EXACT_CHILD": "^Partial 8.32 staged snapshot refused$",
        }
        if state not in patterns:
            raise AssertionError("Expected complete 8.32 candidate baseline")
        return patterns[state]
    return "^(?:" + historical_pattern + ")$"


def _assert_staged_application_topologies(case, guard, canary):
    """Reuse the read-only raw snapshot fixture; never alter candidate pins.

    Import lazily: that fixture imports this module for its current reader.
    Real disk bytes and literal pins remain authoritative, including stale pins.
    """
    from tests import phase_8_32_scope_migration as successor
    from tests.test_phase_832_scope_integrity import snapshot
    target = "nayeon/desktop_alpha/application.py"
    case.assertEqual(len(successor.ENVELOPE), 14)
    for state in ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD"):
        with case.subTest(state=state), snapshot(state):
            case.assertEqual(successor._assert_832_historical(), state)
            successor._assert_832_historical()
            if state == "EXACT_STAGED":
                base = successor._tree(successor.PROTECTED)
                index = successor._index()
                delta = {p for p in set(base) | set(index)
                         if base.get(p) != index.get(p)}
                case.assertEqual(delta, successor.ENVELOPE)
            # Run the original malicious injection and its reached assertion.
            canary(_historical=True)
            successor._assert_832_historical()

    # A rejection already present in the original snapshot must propagate
    # before the canary's expected-error context can mistake it for its attack.
    controls = (
        ("EXACT_STAGED", {"corrupt_source": target},
         "^8.32 index/disk disagreement$"),
        ("EXACT_STAGED", {"stage_paths": {target}},
         "^Partial 8.32 staged snapshot refused$"),
        ("EXACT_STAGED", {"stage_paths": successor.ENVELOPE - {target}},
         "^Partial 8.32 staged snapshot refused$"),
        ("EXACT_CHILD", {"corrupt_source": target},
         "^Partial 8.32 staged snapshot refused$"),
        ("EXACT_CHILD", {"missing": target},
         "^Partial 8.32 staged snapshot refused$"),
        ("EXACT_CHILD", {"parent": "a" * 40},
         "^8.32 wrong immediate product parent$"),
    )
    for state, kwargs, expected in controls:
        with case.subTest(state=state, changes=kwargs), snapshot(state, **kwargs):
            if state == "EXACT_STAGED" and "corrupt_source" in kwargs:
                base = successor._tree(successor.PROTECTED)
                index = successor._index()
                wanted = dict(base)
                for path in successor.ENVELOPE:
                    wanted[path] = ("100644", scope._oid(successor._disk(path)))
                wanted[target] = ("100644", "1" * 40)
                case.assertEqual(index, wanted)
                case.assertEqual({p for p in set(base) | set(index)
                                  if base.get(p) != index.get(p)}, successor.ENVELOPE)
            with case.assertRaisesRegex(AssertionError, expected):
                successor._assert_832_historical()
            with case.assertRaisesRegex(AssertionError, expected):
                canary(_historical=True)


class Phase830ScopeIntegrityTests(unittest.TestCase):
    def test_current_protected_source_invariant(self):
        scope.assert_830_integrity()
        scope.assert_exact_owner_imports()

    def test_git_reads_complete_path_inventories(self):
        calls = []
        original = scope._git
        def observed(*args):
            calls.append(args)
            return original(*args)
        with mock.patch.object(scope, "_git", side_effect=observed):
            scope.assert_830_integrity()
        self.assertIn(("ls-files", "--stage", "-z"), calls)
        self.assertIn(("ls-files", "--others", "--exclude-standard", "-z"), calls)
        self.assertTrue(all(len(args) == 5 for args in calls if args[0] == "ls-tree"))

    def test_head_alias_after_clean_baseline(self):
        original = scope._git
        count = []
        def supplied(*args):
            response = original(*args)
            if args[0] == "ls-tree":
                count.append(args)
                if len(count) == 2:
                    return response + tree_record("nayeon./config/foreign.py")
            return response
        with mock.patch.object(scope, "_git", side_effect=supplied):
            with self.assertRaisesRegex(AssertionError, "Aliased production root"):
                scope.assert_830_integrity()
        self.assertEqual(len(count), 2)

    def test_all_approved_ui_configuration_imports_are_exact(self):
        scope.assert_exact_830_source_imports()
        for relative in scope.CONFIG_IMPORT_ALLOW:
            self.assertEqual(len(scope._approved_source(relative)), 40)

    def test_pinned_new_ui_hash_mismatch_refused(self):
        for relative in (
            "nayeon/desktop_alpha/application.py",
            "nayeon/desktop_alpha/workspace_window.py",
            "nayeon/desktop_alpha/presentation_window.py",
            "nayeon/desktop_alpha/window.py",
        ):
            with self.subTest(relative=relative):
                bad = dict(scope.APPROVED_SOURCE_SHA256)
                bad[relative] = "0" * 64
                with mock.patch.object(scope, "APPROVED_SOURCE_SHA256", bad):
                    with self.assertRaisesRegex(AssertionError, "Unapproved 8.30 source bytes"):
                        scope.assert_830_integrity()

    def test_staged_modified_entrypoint_bad_blob_refused(self):
        actual = scope._git
        file_name = b"nayeon/desktop_alpha/window.py"
        def supplied(*args):
            result = actual(*args)
            if args[:3] == ("ls-files", "--stage", "-z"):
                entries = result.split(b"\0")
                for i, item in enumerate(entries):
                    if item.endswith(b"\t" + file_name):
                        entries[i] = b"100644 " + OID + b" 0\t" + file_name
                        return b"\0".join(entries)
                raise AssertionError("Original entrypoint missing")
            return result
        expected = ("Unapproved entrypoint source change"
                    if actual("rev-parse", "HEAD").decode().strip() == scope.PROTECTED
                    else "Postcommit entrypoint rollback refused")
        with mock.patch.object(scope, "_git", side_effect=supplied):
            with self.assertRaisesRegex(AssertionError, expected):
                scope.assert_830_integrity()

    def test_staged_unapproved_new_ui_blob_refused(self, _historical=False):
        from tests.test_phase_832_scope_integrity import snapshot
        from tests.phase_8_32_scope_migration import _assert_832_historical
        if not _historical:
            with snapshot():
                return self.test_staged_unapproved_new_ui_blob_refused(_historical=True)
        actual = scope._git
        relative = "nayeon/desktop_alpha/application.py"
        reached = []
        def supplied(*args):
            result = actual(*args)
            if args[:3] == ("ls-files", "--stage", "-z"):
                reached.append(relative)
                return replace_or_add_record(result, relative, index_record(relative))
            return result
        from tests.phase_8_31_scope_migration import PARENT_831
        historical = ("Partial 8.31 staged production snapshot refused|Missing or unapproved staged 8.30 source|Unapproved staged 8.30 source|Unapproved staged 8.31 source"
                      if actual("rev-parse", "HEAD").decode().strip() == PARENT_831
                      else "8.31 staged/committed rollback refused")
        expected = _staged_application_error_pattern(historical)
        with mock.patch.object(scope, "_git", side_effect=supplied):
            with self.assertRaisesRegex(AssertionError, expected):
                _assert_832_historical()
        self.assertEqual(reached, [relative], "Forged application index blob was not reached")

    def test_staged_application_canary_across_exact_832_topologies(self):
        _assert_staged_application_topologies(
            self, scope.assert_830_integrity,
            self.test_staged_unapproved_new_ui_blob_refused)

    def test_committed_unapproved_new_ui_blob_refused(self):
        actual = scope._git
        seen = []
        relative = "nayeon/desktop_alpha/application.py"
        def supplied(*args):
            result = actual(*args)
            if args and args[0] == "ls-tree":
                seen.append(True)
                if len(seen) == 2:
                    return replace_or_add_record(result, relative, tree_record(relative))
            return result
        # The exact malicious ls-tree injection remains required to fail.
        # Once the separately sealed 8.31 docs child exists, its stronger
        # ancestor-consistency guard can reject it before the old 8.30 guard.
        expected = ("^Unexpected precommit 8.30 product source$"
                    if actual("rev-parse", "HEAD").decode().strip() == scope.PROTECTED
                    else "^(?:Missing or unapproved committed 8.30 source|Documentation descendant modified production|Maintenance descendant modified production)$")
        with mock.patch.object(scope, "_git", side_effect=supplied):
            with self.assertRaisesRegex(AssertionError, expected):
                scope.assert_830_integrity()
        self.assertGreaterEqual(len(seen), 2, "Malicious second ls-tree was not exercised")

    def test_approved_diff_scope_does_not_swallow_unrelated_changes(self):
        allow = set(scope.APPROVED_SOURCE_SHA256)
        extra = "nayeon/config/document.py"
        self.assertEqual(scope.approved_830_scope(allow | {extra}),
                         {extra, "nayeon/desktop_alpha/window.py"})
        self.assertEqual(scope.approved_830_files(set(scope.APPROVED_NEW_SHA256) | {extra}),
                         {extra})

    def test_staged_root_case_alias_refused(self):
        actual = scope._git
        def supplied(*args):
            result = actual(*args)
            if args[:3] == ("ls-files", "--stage", "-z"):
                return result + index_record("Nayeon/config/document.py")
            return result
        with mock.patch.object(scope, "_git", side_effect=supplied):
            with self.assertRaisesRegex(AssertionError, "Aliased production root"):
                scope.assert_830_integrity()

    def test_committed_root_case_alias_refused(self):
        actual = scope._git
        def supplied(*args):
            result = actual(*args)
            if args[:4] == ("ls-tree", "-r", "-z", "--full-tree"):
                return result + tree_record("NAYEON/config/document.py")
            return result
        with mock.patch.object(scope, "_git", side_effect=supplied):
            with self.assertRaisesRegex(AssertionError, "Aliased production root"):
                scope.assert_830_integrity()

    def test_untracked_root_alias_refused(self):
        actual = scope._git
        def supplied(*args):
            result = actual(*args)
            if args[:4] == ("ls-files", "--others", "--exclude-standard", "-z"):
                return result + b"Nayeon/foreign.py\0"
            return result
        with mock.patch.object(scope, "_git", side_effect=supplied):
            with self.assertRaisesRegex(AssertionError, "Aliased production root"):
                scope.assert_830_integrity()

    def test_trailing_dot_space_staged_aliases_refused(self):
        actual = scope._git
        for alias in ("nayeon./config/foreign.py", "nayeon /config/foreign.py",
                      "NAYEON. /config/foreign.py"):
            with self.subTest(alias=alias):
                def supplied(*args):
                    result = actual(*args)
                    if args[:3] == ("ls-files", "--stage", "-z"):
                        return result + index_record(alias)
                    return result
                with mock.patch.object(scope, "_git", side_effect=supplied):
                    with self.assertRaisesRegex(AssertionError, "Aliased production root"):
                        scope.assert_830_integrity()

    def test_trailing_dot_space_committed_aliases_refused(self):
        actual = scope._git
        for alias in ("nayeon./config/foreign.py", "nayeon /config/foreign.py"):
            with self.subTest(alias=alias):
                def supplied(*args):
                    result = actual(*args)
                    if args[:4] == ("ls-tree", "-r", "-z", "--full-tree"):
                        return result + tree_record(alias)
                    return result
                with mock.patch.object(scope, "_git", side_effect=supplied):
                    with self.assertRaisesRegex(AssertionError, "Aliased production root"):
                        scope.assert_830_integrity()

    def test_trailing_dot_space_untracked_aliases_refused(self):
        actual = scope._git
        for alias in ("nayeon./config/foreign.py", "nayeon /config/foreign.py"):
            with self.subTest(alias=alias):
                def supplied(*args):
                    result = actual(*args)
                    if args[:4] == ("ls-files", "--others", "--exclude-standard", "-z"):
                        return result + alias.encode("utf-8") + b"\0"
                    return result
                with mock.patch.object(scope, "_git", side_effect=supplied):
                    with self.assertRaisesRegex(AssertionError, "Aliased production root"):
                        scope.assert_830_integrity()

    def test_backslash_root_alias_refused(self):
        with self.assertRaisesRegex(AssertionError, "Aliased production root"):
            scope._production_git_path("NAYEON\\config\\document.py")

    def test_noncanonical_production_path_refused(self):
        for path in ("nayeon/config../document.py", "nayeon/../config/file.py",
                     "nayeon/config/file.py:", "nayeon//file.py"):
            with self.subTest(path=path):
                with self.assertRaises(AssertionError):
                    scope._production_git_path(path)

    @unittest.skipUnless(os.name == "nt", "Native Windows junction test")
    def test_junction_parent_refused(self):
        with tempfile.TemporaryDirectory(prefix="nayeon_830_scope_junction_") as temp:
            root = Path(temp)
            target = root / "ordinary_target"
            target.mkdir()
            junction = root / "nayeon"
            made = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(made.returncode, 0, made.stderr)
            try:
                with mock.patch.object(scope, "ROOT", root):
                    with self.assertRaisesRegex(AssertionError, "Linked or reparse"):
                        scope._reject_linked_parents(junction / "config" / "file.py")
            finally:
                os.rmdir(junction)

    def test_frozen_production_rejected_on_wrong_branch(self):
        actual = scope._git
        def supplied(*args):
            if args[:2] == ("branch", "--show-current"):
                return b"wrong-branch\n"
            return actual(*args)
        with mock.patch.object(scope, "_git", side_effect=supplied):
            with self.assertRaisesRegex(AssertionError, "Wrong production branch"):
                scope.assert_830_integrity()


if __name__ == "__main__":
    unittest.main()
