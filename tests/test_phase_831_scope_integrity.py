"""Phase 8.31 adversarial exact-scope proof. No real Git/index mutations."""
from __future__ import annotations

from pathlib import Path
from functools import wraps
import unittest
from unittest import mock

from tests import phase_8_30_scope_migration as previous
from tests import phase_8_31_scope_migration as scope
from tests.test_phase_830_scope_integrity import tree_record, index_record
from tests.test_phase_830_scope_integrity import (
    _staged_application_error_pattern, _assert_staged_application_topologies,
)


def _frozen_831_fixture(method):
    """Private, enumerated synthetic tests only; disk is immutable product831.

    Neither actual current-source admission nor public assert_831 selects this
    route. A fixture cannot approve current bytes by changing historical pins.
    """
    @wraps(method)
    def run(self, *args, **kwargs):
        saved_git = previous._git
        saved_rglob = Path.rglob
        frozen_tree = previous._tree(scope.PRODUCT_COMMIT_831)
        frozen_python = tuple(previous.ROOT / p for p in sorted(frozen_tree) if p.endswith(".py"))
        def git(*command):
            if command[:2] == ("branch", "--show-current"):
                return b"nayeon-v1\n"
            if command == ("ls-files", "--others", "--exclude-standard", "-z"):
                # This is a committed historical fixture, not a projection of
                # today's candidate. Current admission is tested separately.
                return b""
            return saved_git(*command)
        def rglob(path, pattern):
            if path == previous.ROOT / "nayeon" and pattern == "*.py":
                return iter(frozen_python)
            return saved_rglob(path, pattern)
        def frozen_disk(path):
            return previous._normal(saved_git("show", scope.PRODUCT_COMMIT_831 + ":" + path))
        with (mock.patch.object(previous, "_git", side_effect=git),
              mock.patch.object(scope, "_disk", side_effect=frozen_disk),
              mock.patch.object(Path, "rglob", rglob)):
            return method(self, *args, **kwargs)
    return run

class Phase831ScopeTests(unittest.TestCase):
    def test_current_831_preseal_exact_source_inventory(self):
        scope.assert_831_integrity()
        self.assertEqual(set(scope.NEW), {
            "nayeon/desktop_alpha/conversation_session.py"})
        self.assertEqual(set(scope.MODIFIED), {
            "nayeon/desktop_alpha/application.py",
            "nayeon/desktop_alpha/workspace_window.py"})

    def test_historical_830_pins_are_still_immutable(self):
        with mock.patch.dict(previous.APPROVED_SOURCE_SHA256,
                             {"nayeon/desktop_alpha/application.py": "0" * 64}):
            with self.assertRaisesRegex(AssertionError, "Unapproved 8.30 source bytes"):
                scope.assert_831_integrity()

    def test_changed_831_disk_hash_is_exact_not_wildcard(self):
        with mock.patch.dict(scope.ALL_831,
                             {"nayeon/desktop_alpha/application.py": "0" * 64}):
            with self.assertRaisesRegex(AssertionError, "Unapproved 8.31 source bytes"):
                scope.assert_831_integrity()

    def test_new_831_file_missing_fails_closed(self):
        from tests import phase_8_32_scope_migration as successor
        from tests.test_phase_832_scope_integrity import snapshot
        real = successor._raw_frozen_disk
        target = "nayeon/desktop_alpha/conversation_session.py"
        reached = []
        def missing(path):
            if path == target:
                reached.append(path)
                raise AssertionError("Missing, linked or nonregular 8.31 source")
            return real(path)
        with snapshot(), mock.patch.object(successor, "_raw_frozen_disk", side_effect=missing):
            with self.assertRaisesRegex(AssertionError, "^Missing, linked or nonregular 8.31 source$"):
                successor._assert_832_historical()
        self.assertEqual(reached, [target], "Frozen owner missing-read injection was not reached")

    def test_index_tampered_working_tree_disagreement_refused(self, _historical=False):
        from tests.test_phase_832_scope_integrity import snapshot
        from tests.phase_8_32_scope_migration import _assert_832_historical
        if not _historical:
            with snapshot():
                return self.test_index_tampered_working_tree_disagreement_refused(_historical=True)
        real = previous._git
        target = b"nayeon/desktop_alpha/application.py"
        fake = b"100644 " + b"1"*40 + b" 0\t" + target
        reached = []
        def injected(*args):
            response = real(*args)
            if args[:3] == ("ls-files", "--stage", "-z"):
                if any(entry.endswith(b"\t" + target) for entry in response.split(b"\0")):
                    reached.append(target)
                return b"\0".join(
                    fake if entry.endswith(b"\t"+target) else entry
                    for entry in response.split(b"\0"))
            return response
        historical = ("Partial 8.31 staged production snapshot refused|Unapproved staged 8.30 source" if
                      real("rev-parse", "HEAD").decode().strip() == scope.PARENT_831
                      else "8.31 staged/committed rollback refused")
        expected = _staged_application_error_pattern(historical)
        with mock.patch.object(previous, "_git", side_effect=injected):
            with self.assertRaisesRegex(AssertionError, expected):
                _assert_832_historical()
        self.assertEqual(reached, [target], "Forged application index blob was not reached")

    def test_staged_application_canary_across_exact_832_topologies(self):
        _assert_staged_application_topologies(
            self, scope.assert_831_integrity,
            self.test_index_tampered_working_tree_disagreement_refused)

    def test_unlisted_staged_and_untracked_paths_refused(self):
        real = previous._git
        for operation in ("index", "untracked"):
            with self.subTest(operation=operation):
                def injected(*args):
                    response = real(*args)
                    if operation == "index" and args[:3] == ("ls-files","--stage","-z"):
                        return response + index_record("nayeon/desktop_alpha/foreign.py")
                    if operation == "untracked" and args[:4] == (
                            "ls-files","--others","--exclude-standard","-z"):
                        return response + b"nayeon/desktop_alpha/foreign.py\0"
                    return response
                with mock.patch.object(previous, "_git", side_effect=injected):
                    with self.assertRaises(AssertionError):
                        scope.assert_831_integrity()

    def test_case_dot_space_and_ads_aliases_are_not_allowed(self):
        real = previous._git
        for alias in ("NAYEON/foreign.py", "nayeon./config/foreign.py",
                      "nayeon /config/foreign.py",
                      "nayeon/config/foreign.py:evil"):
            with self.subTest(alias=alias):
                def injected(*args):
                    response = real(*args)
                    if args[:3] == ("ls-files","--stage","-z"):
                        return response + index_record(alias)
                    return response
                with mock.patch.object(previous, "_git", side_effect=injected):
                    with self.assertRaises(AssertionError):
                        scope.assert_831_integrity()

    def test_commit_tree_alias_refused_before_path_filtering(self):
        real = previous._git
        def injected(*args):
            response = real(*args)
            if args[:4] == ("ls-tree","-r","-z","--full-tree"):
                return response + tree_record("NAYEON/malicious.py")
            return response
        with mock.patch.object(previous, "_git", side_effect=injected):
            with self.assertRaisesRegex(AssertionError, "Aliased production root"):
                scope.assert_831_integrity()

    def test_wrong_branch_and_wrong_parent_refused(self):
        real = previous._git
        def wrong_branch(*args):
            if args[:2] == ("branch", "--show-current"):
                return b"other-branch\n"
            return real(*args)
        with mock.patch.object(previous, "_git", side_effect=wrong_branch):
            with self.assertRaisesRegex(AssertionError, "Wrong production branch"):
                scope.assert_831_integrity()
        def wrong_parent(*args):
            if args[:2] == ("merge-base","--is-ancestor"):
                raise AssertionError("Wrong protected parent")
            return real(*args)
        with mock.patch.object(previous, "_git", side_effect=wrong_parent):
            with self.assertRaisesRegex(AssertionError, "Wrong protected parent"):
                scope.assert_831_integrity()

    def test_pure_owner_rejects_unsafe_import_or_tests_module(self):
        path = next(iter(scope.NEW))
        for source in (b"import subprocess\n", b"from tests.fake import x\n",
                       b"from nayeon.credential.backend import WinCred\n"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(AssertionError, "(Forbidden|Unknown)"):
                    scope._no_unsafe_imports(path, source)

    def test_full_git_inventory_reads_are_unfiltered(self):
        real = previous._git
        calls = []
        def traced(*args):
            calls.append(args)
            return real(*args)
        with mock.patch.object(previous, "_git", side_effect=traced):
            scope.assert_831_integrity()
        self.assertIn(("ls-files","--stage","-z"),calls)
        self.assertIn(("ls-files","--others","--exclude-standard","-z"),calls)
        self.assertTrue(all(len(a)==5 for a in calls if a[0]=="ls-tree"))

    @_frozen_831_fixture
    def _postcommit(self, *, stale_index_path=None, omit_head_new=False,
                    corrupt_head_path=None, immediate_parent=None,
                    merge_parent=None, index_staged_paths=None):
        """Synthetic Git snapshot: all 8.31 stage/commit transitions in memory."""
        fake = "f" * 40
        actual_git = previous._git
        actual_tree = previous._tree
        actual_index = previous._index
        product = actual_tree(scope.PRODUCT_830)
        complete = dict(product)
        for path in scope.ALL_831:
            complete[path] = (scope.OWNER_MODE, previous._oid(scope._disk(path)))
        head = dict(complete)
        if omit_head_new:
            head.pop(next(iter(scope.NEW)))
        if corrupt_head_path:
            head[corrupt_head_path] = (scope.OWNER_MODE, "1"*40)
        index = dict(complete)
        if index_staged_paths is not None:
            index = dict(product)
            for path in index_staged_paths:
                index[path] = complete[path]
        if stale_index_path:
            index[stale_index_path] = product[stale_index_path]
        def git(*args):
            if args[:2] == ("rev-parse","HEAD"):
                return (fake+"\n").encode()
            if args[:2] == ("merge-base","--is-ancestor"):
                return b""
            if args[:4] == ("rev-list","--parents","-n","1"):
                parent = immediate_parent or scope.PARENT_831
                suffix = " " + merge_parent if merge_parent else ""
                return (fake + " " + parent + suffix + "\n").encode()
            return actual_git(*args)
        def tree(revision):
            if revision == fake:
                return head
            return actual_tree(revision)
        with (mock.patch.object(previous, "_git", side_effect=git),
              mock.patch.object(previous, "_tree", side_effect=tree),
              mock.patch.object(previous, "_index", return_value=index)):
            scope._assert_831_historical_integrity()

    def test_synthetic_completed_commit_and_index_is_accepted(self):
        self._postcommit()

    def test_synthetic_postcommit_old_index_rollback_rejected(self):
        with self.assertRaisesRegex(AssertionError, "8.31 staged/committed rollback"):
            self._postcommit(stale_index_path="nayeon/desktop_alpha/application.py")

    def test_synthetic_postcommit_new_source_missing_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Unauthorized committed production inventory"):
            self._postcommit(omit_head_new=True)

    def test_synthetic_postcommit_wrong_source_blob_rejected(self):
        with self.assertRaisesRegex(AssertionError, "8.31 staged/committed rollback"):
            self._postcommit(corrupt_head_path="nayeon/desktop_alpha/workspace_window.py")


    @_frozen_831_fixture
    def test_partial_staging_of_each_phase_file_is_rejected(self):
        product = previous._tree(scope.PRODUCT_830)
        full = dict(product)
        for path in scope.ALL_831:
            full[path] = (scope.OWNER_MODE, previous._oid(scope._disk(path)))
        # A complete synthetic PRECOMMIT HEAD/index context is essential:
        # after a real 8.31 commit, this test must still prove the same
        # precommit negative, rather than relying on whichever HEAD is live.
        saved_git = previous._git
        saved_tree = previous._tree
        subsets = ({"nayeon/desktop_alpha/application.py"},
                   {"nayeon/desktop_alpha/workspace_window.py"},
                   {"nayeon/desktop_alpha/conversation_session.py"},
                   {"nayeon/desktop_alpha/application.py",
                    "nayeon/desktop_alpha/conversation_session.py"},
                   {"nayeon/desktop_alpha/workspace_window.py",
                    "nayeon/desktop_alpha/conversation_session.py"},
                   set(scope.MODIFIED))
        def precommit_git(*args):
            if args[:2] == ("rev-parse", "HEAD"):
                return (scope.PARENT_831 + "\n").encode("ascii")
            if args[:2] == ("merge-base", "--is-ancestor"):
                return b""
            return saved_git(*args)
        def precommit_tree(commit):
            return product if commit == scope.PARENT_831 else saved_tree(commit)
        for subset in subsets:
            with self.subTest(phase="precommit", staged=subset):
                fake = dict(product)
                for path in subset:
                    fake[path] = full[path]
                with (mock.patch.object(previous, "_git", side_effect=precommit_git),
                      mock.patch.object(previous, "_tree", side_effect=precommit_tree),
                      mock.patch.object(previous, "_index", return_value=fake)):
                    with self.assertRaisesRegex(AssertionError, "Partial 8.31 staged"):
                        scope._assert_831_historical_integrity()
            # The *same* partial index after a simulated valid product commit
            # must instead refuse the exact committed/index mismatch.
            with self.subTest(phase="postcommit", staged=subset):
                with self.assertRaisesRegex(AssertionError,
                                            "8.31 staged/committed rollback refused|8.31 new-source committed/index rollback refused"):
                    self._postcommit(index_staged_paths=subset)

    @_frozen_831_fixture
    def test_complete_precommit_staging_accepted(self):
        complete = previous._tree(scope.PRODUCT_830)
        for path in scope.ALL_831:
            complete[path] = (scope.OWNER_MODE, previous._oid(scope._disk(path)))
        saved_git, saved_tree = previous._git, previous._tree
        def git(*args):
            if args[:2] == ("rev-parse", "HEAD"):
                return (scope.PARENT_831 + "\n").encode()
            return saved_git(*args)
        def tree(commit):
            return saved_tree(scope.PRODUCT_830 if commit == scope.PARENT_831 else commit)
        with (mock.patch.object(previous, "_index", return_value=complete),
              mock.patch.object(previous, "_tree", side_effect=tree),
              mock.patch.object(previous, "_git", side_effect=git)):
            scope._assert_831_historical_integrity()

    def test_ancestor_but_wrong_immediate_parent_refused(self):
        with self.assertRaisesRegex(AssertionError, "wrong immediate product parent"):
            self._postcommit(immediate_parent="a"*40)

    def test_merge_commit_with_correct_parent_refused(self):
        with self.assertRaisesRegex(AssertionError, "wrong immediate product parent"):
            self._postcommit(merge_parent="b"*40)

    @_frozen_831_fixture
    def _docs_descendant(self, *, changed=None, source_tamper=False,
                         merge=False, wrong_product_parent=False, deleted=False):
        """Synthetic exact product+one documentation-only child Git history."""
        product_commit, docs_commit = "e" * 40, "d" * 40
        real_git, real_tree = previous._git, previous._tree
        production = dict(real_tree(scope.PRODUCT_830))
        for path in scope.ALL_831:
            production[path] = (scope.OWNER_MODE, previous._oid(scope._disk(path)))
        head = dict(production)
        if source_tamper:
            head["nayeon/desktop_alpha/application.py"] = (
                scope.OWNER_MODE, "1" * 40)
        index = dict(production)
        changes = ([".codex/CURRENT_STATE.md",
                    "docs/phase_8_31_offline_conversation_session_rfc.md"]
                   if changed is None else changed)
        def git(*args):
            if args[:2] == ("rev-parse", "HEAD"):
                return (docs_commit + "\n").encode()
            if args[:2] == ("merge-base", "--is-ancestor"):
                return b""
            if args[:4] == ("rev-list", "--parents", "-n", "1"):
                if args[4] == docs_commit:
                    return (docs_commit + " " + product_commit
                            + (" " + "a"*40 if merge else "") + "\n").encode()
                if args[4] == product_commit:
                    parent = "a"*40 if wrong_product_parent else scope.PARENT_831
                    return (product_commit + " " + parent + "\n").encode()
            if args[:4] == ("diff", "--no-renames", "--name-only", "-z"):
                return b"".join(x.encode("utf-8") + b"\0" for x in changes)
            if args[:2] == ("cat-file", "-e"):
                if deleted:
                    raise AssertionError("Missing committed documentation")
                return b""
            return real_git(*args)
        def tree(revision):
            if revision == product_commit:
                return production
            if revision == docs_commit:
                return head
            return real_tree(revision)
        with (mock.patch.object(previous, "_git", side_effect=git),
              mock.patch.object(previous, "_tree", side_effect=tree),
              mock.patch.object(previous, "_index", return_value=index)):
            scope._assert_831_historical_integrity()

    def test_single_docs_only_descendant_is_allowed(self):
        self._docs_descendant()

    def test_unlisted_docs_path_is_not_authorized(self):
        with self.assertRaisesRegex(AssertionError, "Unapproved 8.31 documentation-only"):
            self._docs_descendant(changed=["tests/phase_8_31_scope_migration.py"])

    def test_historical_test_renamed_into_allowlisted_docs_is_refused(self):
        # No-renames must expose BOTH the deleted test and added doc file.
        # With rename detection, Git may report only the doc destination.
        with self.assertRaisesRegex(AssertionError, "Unapproved 8.31 documentation-only descendant"):
            self._docs_descendant(changed=[
                "tests/test_phase_830_scope_integrity.py",
                "docs/phase_8_31_offline_conversation_session_review.md",
            ])

    def test_docs_only_descendant_cannot_modify_production(self):
        with self.assertRaisesRegex(AssertionError, "Documentation descendant modified"):
            self._docs_descendant(source_tamper=True)

    def test_docs_only_merge_and_bad_product_parent_refused(self):
        with self.assertRaisesRegex(AssertionError, "wrong immediate product parent"):
            self._docs_descendant(merge=True)
        with self.assertRaisesRegex(AssertionError, "wrong immediate product parent"):
            self._docs_descendant(wrong_product_parent=True)

    def test_empty_doc_commit_and_deletion_refused(self):
        with self.assertRaisesRegex(AssertionError, "Unapproved 8.31 documentation-only"):
            self._docs_descendant(changed=[])
        with self.assertRaisesRegex(AssertionError, "Missing committed documentation"):
            self._docs_descendant(deleted=True)


    @_frozen_831_fixture
    def _maintenance_descendant(self, *, paths=None, status="M",
                                old_mode="100644", new_mode="100644",
                                merge=False, wrong_docs_parent=False,
                                wrong_product_parent=False, changed_source=False,
                                missing_document=False, corrupt_index=False):
        """Synthetic child of the exact PRODUCT→DOCS history, fake-only Git."""
        maint = "f" * 40
        original_git, original_tree, original_index = (
            previous._git, previous._tree, previous._index
        )
        allowed = sorted(scope.MAINTENANCE_FILES)
        changed = allowed if paths is None else paths
        full = dict(original_tree(scope.DOC_COMMIT_831))
        if changed_source:
            full["nayeon/desktop_alpha/application.py"] = (
                scope.OWNER_MODE, "1"*40)
        index = dict(original_tree(scope.PRODUCT_COMMIT_831))
        if corrupt_index:
            index["nayeon/desktop_alpha/application.py"] = (
                scope.OWNER_MODE, "2"*40)
        def git(*args):
            if args[:2] == ("rev-parse", "HEAD"):
                return (maint + "\n").encode()
            if args[:2] == ("merge-base", "--is-ancestor"):
                return b""
            if args[:4] == ("rev-list", "--parents", "-n", "1"):
                if args[4] == maint:
                    return (maint + " " + scope.DOC_COMMIT_831 +
                            (" " + "a"*40 if merge else "") + "\n").encode()
                if args[4] == scope.DOC_COMMIT_831:
                    parent = "a"*40 if wrong_docs_parent else scope.PRODUCT_COMMIT_831
                    return (scope.DOC_COMMIT_831 + " " + parent + "\n").encode()
                if args[4] == scope.PRODUCT_COMMIT_831:
                    parent = "a"*40 if wrong_product_parent else scope.PARENT_831
                    return (scope.PRODUCT_COMMIT_831 + " " + parent + "\n").encode()
            if args[:4] == ("diff", "--no-renames", "--raw", "-z"):
                records = []
                for path in changed:
                    meta = (f":{old_mode} {new_mode} " + "a"*40 + " " +
                            "b"*40 + f" {status}").encode()
                    records.append(meta + b"\0" + path.encode() + b"\0")
                return b"".join(records)
            if args[:2] == ("cat-file", "-e"):
                if missing_document and args[2].startswith(maint + ":"):
                    raise AssertionError("Missing maintenance file")
                if args[2].startswith(maint + ":"):
                    return b""
            return original_git(*args)
        def tree(commit):
            if commit == maint:
                return full
            return original_tree(commit)
        with (mock.patch.object(previous, "_git", side_effect=git),
              mock.patch.object(previous, "_tree", side_effect=tree),
              mock.patch.object(previous, "_index", return_value=index)):
            scope._assert_831_historical_integrity()

    def test_exact_maintenance_child_five_modified_files_allowed(self):
        self._maintenance_descendant()

    def test_maintenance_missing_extra_duplicate_and_renamed_paths_refused(self):
        expected = set(scope.MAINTENANCE_FILES)
        for paths in (sorted(expected)[:-1],
                      sorted(expected) + ["tests/extra.py"],
                      sorted(expected) + [sorted(expected)[0]],
                      sorted(expected-{sorted(expected)[0]}) + ["tests/swap.py"]):
            with self.subTest(paths=paths):
                with self.assertRaisesRegex(AssertionError, "maintenance scope"):
                    self._maintenance_descendant(paths=paths)

    def test_maintenance_file_add_delete_modes_and_types_refused(self):
        for kwargs in ({"status": "A"}, {"status": "D"},
                       {"status": "R100"}, {"old_mode": "100755"},
                       {"new_mode": "120000"}, {"new_mode": "000000"}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(AssertionError, "maintenance scope"):
                    self._maintenance_descendant(**kwargs)

    def test_maintenance_merge_wrong_docs_and_product_parent_refused(self):
        for kwargs in ({"merge": True}, {"wrong_docs_parent": True},
                       {"wrong_product_parent": True}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(AssertionError,
                                            "wrong.*parent"):
                    self._maintenance_descendant(**kwargs)

    def test_maintenance_production_change_and_staged_rollback_refused(self):
        with self.assertRaisesRegex(AssertionError, "Maintenance descendant modified production"):
            self._maintenance_descendant(changed_source=True)
        with self.assertRaisesRegex(AssertionError, "8.31 staged/committed rollback refused"):
            self._maintenance_descendant(corrupt_index=True)

    def test_maintenance_deleted_or_unverifiable_file_refused(self):
        with self.assertRaisesRegex(AssertionError, "Missing maintenance file"):
            self._maintenance_descendant(missing_document=True)

    @_frozen_831_fixture
    def test_maintenance_second_descendant_is_not_admitted(self):
        oldgit = previous._git
        fakehead = "9"*40
        def git(*args):
            if args[:2] == ("rev-parse", "HEAD"):
                return (fakehead + "\n").encode()
            if args[:2] == ("merge-base", "--is-ancestor"):
                return b""
            if args[:4] == ("rev-list", "--parents", "-n", "1") and args[4] == fakehead:
                return (fakehead + " " + "f"*40 + "\n").encode()
            if args[:4] == ("rev-list", "--parents", "-n", "1") and args[4] == "f"*40:
                return ("f"*40 + " " + scope.DOC_COMMIT_831 + "\n").encode()
            return oldgit(*args)
        with mock.patch.object(previous, "_git", side_effect=git):
            with self.assertRaisesRegex(AssertionError, "wrong immediate product parent"):
                scope._assert_831_historical_integrity()


if __name__ == "__main__":
    unittest.main()
