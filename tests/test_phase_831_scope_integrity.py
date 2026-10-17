"""Phase 8.31 adversarial exact-scope proof. No real Git/index mutations."""
from __future__ import annotations

from pathlib import Path
import unittest
from unittest import mock

from tests import phase_8_30_scope_migration as previous
from tests import phase_8_31_scope_migration as scope
from tests.test_phase_830_scope_integrity import tree_record, index_record


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
        real = scope._disk
        def missing(path):
            if path in scope.NEW:
                raise AssertionError("Missing, linked or nonregular 8.31 source")
            return real(path)
        with mock.patch.object(scope, "_disk", side_effect=missing):
            with self.assertRaisesRegex(AssertionError, "Missing"):
                scope.assert_831_integrity()

    def test_index_tampered_working_tree_disagreement_refused(self):
        real = previous._git
        target = b"nayeon/desktop_alpha/application.py"
        fake = b"100644 " + b"1"*40 + b" 0\t" + target
        def injected(*args):
            response = real(*args)
            if args[:3] == ("ls-files", "--stage", "-z"):
                return b"\0".join(
                    fake if entry.endswith(b"\t"+target) else entry
                    for entry in response.split(b"\0"))
            return response
        with mock.patch.object(previous, "_git", side_effect=injected):
            expected = ("(?:Partial 8.31 staged production snapshot|Unapproved staged 8.30 source)" if
                        previous._git("rev-parse", "HEAD").decode().strip() == scope.PARENT_831
                        else "8.31 staged/committed rollback refused")
            with self.assertRaisesRegex(AssertionError, expected):
                scope.assert_831_integrity()

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
            scope.assert_831_integrity()

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
                        scope.assert_831_integrity()
            # The *same* partial index after a simulated valid product commit
            # must instead refuse the exact committed/index mismatch.
            with self.subTest(phase="postcommit", staged=subset):
                with self.assertRaisesRegex(AssertionError,
                                            "8.31 staged/committed rollback refused|8.31 new-source committed/index rollback refused"):
                    self._postcommit(index_staged_paths=subset)

    def test_complete_precommit_staging_accepted(self):
        complete = previous._tree(scope.PRODUCT_830)
        for path in scope.ALL_831:
            complete[path] = (scope.OWNER_MODE, previous._oid(scope._disk(path)))
        with mock.patch.object(previous, "_index", return_value=complete):
            scope.assert_831_integrity()

    def test_ancestor_but_wrong_immediate_parent_refused(self):
        with self.assertRaisesRegex(AssertionError, "wrong immediate product parent"):
            self._postcommit(immediate_parent="a"*40)

    def test_merge_commit_with_correct_parent_refused(self):
        with self.assertRaisesRegex(AssertionError, "wrong immediate product parent"):
            self._postcommit(merge_parent="b"*40)

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
            scope.assert_831_integrity()

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


if __name__ == "__main__":
    unittest.main()
