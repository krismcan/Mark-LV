"""P90 real Git negative tests; mutations confined to disposable temp clones."""
from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest

from tests.p90_review_source_admission import (
    BRANCH, P88, ReviewHold, assert_review_source_snapshot, git, txt,
)

BASE = pathlib.Path(__file__).resolve().parents[1]


def run_git(root, *args):
    output = subprocess.run(["git", "-C", str(root), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=30, check=False)
    if output.returncode != 0:
        raise AssertionError("fixture Git setup failed: " + args[0])
    return output.stdout.decode("utf-8").strip()


class P90DisposableGitRefusalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if txt(BASE, "branch", "--show-current") != BRANCH:
            raise unittest.SkipTest("P90 exact branch not present")
        cls.external_pin = txt(BASE, "rev-parse", "HEAD")
        if txt(BASE, "rev-list", "--parents", "-n", "1", "HEAD") != (
                cls.external_pin + " " + P88):
            raise unittest.SkipTest("P90 exact committed child not yet ready")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nayeon-p90-git-negative-")
        self.addCleanup(self.temp.cleanup)
        self.copy = pathlib.Path(self.temp.name) / "isolated"
        cmd = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "clone", "--quiet",
             "--no-hardlinks", "--branch", BRANCH, str(BASE), str(self.copy)],
            capture_output=True, timeout=90, check=False)
        self.assertEqual(cmd.returncode, 0, cmd.stderr.decode(errors="replace"))
        run_git(self.copy, "config", "--local", "core.autocrlf", "false")
        self.assertEqual(txt(self.copy, "rev-parse", "HEAD"), self.external_pin)

    def prove(self):
        return assert_review_source_snapshot(self.copy, self.external_pin)

    def denied(self, *, pin=None, root=None):
        with self.assertRaises(ReviewHold):
            assert_review_source_snapshot(
                self.copy if root is None else root,
                self.external_pin if pin is None else pin,
            )

    def test_exact_clean_review_snapshot_still_release_hold(self):
        self.assertEqual(
            self.prove(), "EXACT_REVIEW_SNAPSHOT_ONLY__PRODUCTION_HOLD")

    def test_missing_external_sha_refused(self):
        self.denied(pin="")

    def test_invalid_external_sha_refused(self):
        self.denied(pin="not-a-reviewed-git-sha")

    def test_plausible_but_wrong_external_sha_refused(self):
        self.denied(pin="a" * 40)

    def test_stale_or_tampered_historical_source_refused(self):
        f = self.copy / "nayeon" / "brain" / "pending_custody_status_view.py"
        f.write_bytes(f.read_bytes() + b"\n# P90 DISPOSABLE TAMPER\n")
        self.denied()

    def test_modified_p90_guard_refused(self):
        f = self.copy / "tests" / "p90_review_source_admission.py"
        f.write_bytes(f.read_bytes() + b"\n# P90 DISPOSABLE TAMPER\n")
        self.denied()

    def test_modified_p90_workflow_refused(self):
        f = self.copy / ".github" / "workflows" / "p90-review-source-admission.yml"
        f.write_bytes(f.read_bytes() + b"\n# P90 DISPOSABLE TAMPER\n")
        self.denied()

    def test_missing_source_file_refused(self):
        (self.copy / "tests" / "test_p90_review_source_admission.py").unlink()
        self.denied()

    def test_untracked_source_refused(self):
        (self.copy / "tests" / "p90-unreviewed.py").write_text("x = 1\n")
        self.denied()

    def test_staged_source_edit_refused(self):
        f = self.copy / "tests" / "p90_review_source_admission.py"
        f.write_bytes(f.read_bytes() + b"\n# P90 STAGED TAMPER\n")
        run_git(self.copy, "add", "--", "tests/p90_review_source_admission.py")
        self.denied()

    def test_new_branch_identity_refused(self):
        run_git(self.copy, "branch", "-m", "byok-c1-not-reviewed")
        self.denied()

    def test_new_commit_even_without_source_change_refused(self):
        run_git(self.copy, "-c", "user.name=P90 Fixture",
                "-c", "user.email=p90-fixture@example.invalid",
                "commit", "--quiet", "--allow-empty", "-m", "disposable tamper")
        self.denied()

    def test_non_root_path_refused(self):
        self.denied(root=self.copy / "tests")

    def test_expected_p88_is_parent_but_old_gate_unchanged(self):
        self.assertEqual(txt(self.copy, "rev-parse", "HEAD^"), P88)
        self.assertEqual(
            txt(self.copy, "rev-parse",
                "HEAD:tests/phase8_byok_c1_p85_scope.py"),
            txt(self.copy, "rev-parse",
                "HEAD^:tests/phase8_byok_c1_p85_scope.py"))
        self.assertIn("HOLD", self.prove())

    def test_index_and_worktree_still_clean_on_success(self):
        self.prove()
        self.assertEqual(git(self.copy, "status", "--porcelain=v1",
                             "--untracked-files=all"), b"")


if __name__ == "__main__":
    unittest.main()
