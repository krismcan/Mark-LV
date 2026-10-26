"""Adversarial offline OM v2.1 canary evidence; does not test a live provider."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "om_v21_state_canary.py"
spec = importlib.util.spec_from_file_location("om21_canary", SCRIPT)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


def git(repo: Path, *args):
    p = subprocess.run(["git", "-C", str(repo), *args],
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=15, check=True)
    return p.stdout.strip()


class StateCanaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="om21_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "candidate"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "candidate")
        git(self.repo, "config", "user.name", "OM Test Only")
        git(self.repo, "config", "user.email", "om-test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        (self.repo/"tests").mkdir()
        (self.repo/"tests"/"__init__.py").write_text("", encoding="utf8")
        (self.repo/"tests"/"test_dummy.py").write_text(
            "import unittest\nclass X(unittest.TestCase):\n"
            " def test_dummy(self): self.assertTrue(True)\n", encoding="utf8")
        (self.repo/".gitignore").write_text("private_cache/\n", encoding="utf8")
        (self.repo/"text.txt").write_text("before\n", encoding="utf8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "baseline")
        self.parent = git(self.repo, "rev-parse", "HEAD")
        self.tag = "nayeon-v1-test-synthetic-baseline"
        git(self.repo, "tag", "-a", self.tag, "-m", "Synthetic baseline")
        (self.repo/"text.txt").write_text("after\n", encoding="utf8")

    def matrix(self):
        return dict(schema=1, baseline_commit=self.parent, baseline_tag=self.tag,
                    baseline_tag_object=git(self.repo, "rev-parse", "refs/tags/"+self.tag),
                    paths_sha256={"text.txt": hashlib.sha256((self.repo/"text.txt").read_bytes()).hexdigest()},
                    modules=["tests.test_dummy"])

    def test_actual_unstaged_then_exact_staged_then_exact_child(self):
        matrix = self.matrix()
        for state in ("complete_unstaged", "exact_staged", "exact_child"):
            paths, mods = gate.verify(self.repo, matrix, state)
            self.assertEqual(paths, ["text.txt"])
            self.assertEqual(mods, ["tests.test_dummy"])
            if state == "complete_unstaged":
                git(self.repo, "add", "text.txt")
            if state == "exact_staged":
                git(self.repo, "commit", "-m", "descendant")
        gate.execute(self.repo, ["tests.test_dummy"], Path(__import__("sys").executable), self.root)

    def test_wrong_topology_fails_closed(self):
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo, self.matrix(), "exact_staged")
        git(self.repo, "add", "text.txt")
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo, self.matrix(), "complete_unstaged")

    def test_unknown_untracked_fails_closed(self):
        (self.repo/"unknown.py").write_text("pass\n", encoding="utf8")
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo, self.matrix(), "complete_unstaged")

    def test_ignored_source_fails_closed(self):
        (self.repo/"private_cache").mkdir()
        (self.repo/"private_cache"/"hidden.py").write_text("pass\n",encoding="utf8")
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo, self.matrix(), "complete_unstaged")

    def test_changed_bytes_fails_closed(self):
        m = self.matrix()
        (self.repo/"text.txt").write_text("tampered\n", encoding="utf8")
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo, m, "complete_unstaged")

    def test_missing_historical_tag_or_parent_fails_closed(self):
        m=self.matrix()
        m["baseline_commit"]="0"*40
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo,m,"complete_unstaged")

    def test_unknown_test_module_or_invalid_census_fails_closed(self):
        m=self.matrix()
        m["modules"]=["os.system"]
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo,m,"complete_unstaged")
        m=self.matrix();m["paths_sha256"]={}
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo,m,"complete_unstaged")

    def test_missing_path_and_path_escape_fail_closed(self):
        m=self.matrix();m["paths_sha256"]={"../outside.py":"a"*64}
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo,m,"complete_unstaged")

    def test_quoted_ignored_source_fails_closed(self):
        (self.repo/"private_cache").mkdir()
        (self.repo/"private_cache"/"hidden source.py").write_text("pass\n", encoding="utf8")
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo, self.matrix(), "complete_unstaged")

    def test_staged_index_content_must_match_disk_pin(self):
        git(self.repo, "add", "text.txt")
        git(self.repo, "update-index", "--assume-unchanged", "text.txt")
        (self.repo/"text.txt").write_text("tampered\n", encoding="utf8")
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo, self.matrix(), "exact_staged")

    def test_committed_blob_content_must_match_disk_pin(self):
        git(self.repo, "add", "text.txt")
        git(self.repo, "commit", "-m", "child")
        git(self.repo, "update-index", "--assume-unchanged", "text.txt")
        (self.repo/"text.txt").write_text("tampered\n", encoding="utf8")
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo, self.matrix(), "exact_child")

    def test_zero_tests_cannot_claim_native_pass(self):
        import sys
        (self.repo/"tests"/"test_empty.py").write_text("# no tests\n",encoding="utf8")
        with self.assertRaises(gate.PreflightHold):
            gate.execute(self.repo, ["tests.test_empty"], Path(sys.executable), self.root)

    def test_non_annotated_tag_rejected(self):
        git(self.repo,"tag","nayeon-v1-lightweight")
        m=self.matrix();m["baseline_tag"]="nayeon-v1-lightweight"
        with self.assertRaises(gate.PreflightHold):
            gate.verify(self.repo,m,"complete_unstaged")


if __name__ == "__main__":
    unittest.main()
