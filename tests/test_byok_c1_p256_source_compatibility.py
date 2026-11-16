"""Additive P256 synthetic admission tests and an isolated real-checkout CLI.

No product imports, credential calls, Git mutations, or original test edits.
Synthetic Git replies exercise admission logic without asserting Git authenticity.
"""

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import byok_c1_p255_effect_boundary as historical
from tools import byok_c1_p256_source_compatibility as probe


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class SyntheticAdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=probe.ROOT)
        self.addCleanup(temporary.cleanup)
        container = Path(temporary.name)
        self.root = container / "repo"
        self.common = container / "admin"
        self.admin = self.common / "worktrees/p256"
        self.root.mkdir()
        self.admin.mkdir(parents=True)
        (self.root / ".git").write_bytes(("gitdir: " + str(self.admin) + "\n").encode("utf-8"))
        (self.admin / "gitdir").write_bytes((str(self.root / ".git") + "\n").encode("utf-8"))
        (self.admin / "commondir").write_bytes(b"../..\n")
        (self.admin / "HEAD").write_bytes(("ref: " + probe.BRANCH + "\n").encode("ascii"))
        self.paths = sorted(set(historical.p251.SOURCE_HASHES) | set(probe.HELPER_PINS))
        for relative in self.paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((probe.ROOT / relative).read_bytes())
        for relative in probe.ADDITIONS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"# synthetic draft addition\n")
        for name, value in (("INTENDED_ROOT", self.root), ("COMMON_DIR", self.common), ("GIT_DIR", self.admin)):
            self.enterContext(patch.object(probe, name, value))
        self.enterContext(patch.object(probe, "_runtime_issues", side_effect=lambda: []))
        self.git = self.enterContext(patch.object(probe, "_git", side_effect=self.reply))
        self.replies = {
            ("symbolic-ref", "-q", "HEAD"): probe.BRANCH.encode() + b"\n",
            ("show-ref", "--verify", "--hash", probe.BRANCH): probe.BASE.encode() + b"\n",
            ("rev-parse", "--verify", "HEAD^{commit}"): probe.BASE.encode() + b"\n",
            ("rev-parse", "--verify", "HEAD^{tree}"): probe.TREE.encode() + b"\n",
            ("rev-list", "--parents", "-n", "1", "HEAD"):
                (probe.BASE + " " + probe.PARENT + "\n").encode(),
            ("rev-parse", "--is-shallow-repository"): b"false\n",
            ("rev-parse", "--show-object-format"): b"sha1\n",
            ("rev-parse", "--show-toplevel"): str(self.root).encode() + b"\n",
            ("rev-parse", "--absolute-git-dir"): str(self.admin).encode() + b"\n",
            ("rev-parse", "--path-format=absolute", "--git-common-dir"): str(self.common).encode() + b"\n",
            ("for-each-ref", "--format=%(refname)", "refs/replace/"): b"",
            ("merge-base", "--is-ancestor", probe.P251_COMMIT, probe.BASE): b"",
            ("worktree", "list", "--porcelain", "-z"):
                b"worktree " + str(self.root).replace("\\", "/").encode()
                + b"\0HEAD " + probe.BASE.encode() + b"\0branch " + probe.BRANCH.encode() + b"\0\0",
            ("ls-files", "--others", "-z"):
                b"".join(name.encode() + b"\0" for name in probe.ADDITIONS),
        }
        self.refresh_inventory()

    def reply(self, root, *args):
        self.assertEqual(root, self.root)
        return self.replies[args]

    def refresh_inventory(self):
        entries = [(name, blob((self.root / name).read_bytes())) for name in self.paths]
        self.replies["ls-tree", "-r", "-z", probe.BASE] = b"".join(
            ("100644 blob " + oid + "\t" + name).encode() + b"\0" for name, oid in entries
        )
        self.replies["ls-files", "--stage", "-z"] = b"".join(
            ("100644 " + oid + " 0\t" + name).encode() + b"\0" for name, oid in entries
        )

    def check_report(self, expected="UNKNOWN", reason=None):
        report = probe.assess(self.root)
        self.assertEqual(report["assessment"], expected, report["issues"])
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["source_context_admitted"], expected == "OPEN")
        self.assertEqual(report["effect_owner_exclusivity"], "NOT_ESTABLISHED")
        for field in ("release_admitted", "real_key_admitted", "independently_approved"):
            self.assertIs(report[field], False)
        if reason:
            self.assertIn(reason, {item["reason"] for item in report["issues"]})
        return report

    def test_exact_p256_context_reuses_all_p251_pins_and_p255_routes(self):
        report = self.check_report("OPEN")
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["source_context"]["head"], probe.BASE)
        self.assertEqual(report["source_context"]["parent"], probe.PARENT)
        self.assertEqual(report["source_context"]["p251_ancestor"], probe.P251_COMMIT)
        self.assertEqual({item["path"]: item["sha256"] for item in report["sources"]},
                         historical.p251.SOURCE_HASHES)
        self.assertEqual({route["route"] for route in report["routes"]}, set(historical.ROUTE_SITES))
        self.assertTrue(all(route["status"] == "OPEN" for route in report["routes"]))
        self.assertEqual(len(report["evidence"]), len(historical.p251.CALL_SITES) + len(historical.p251.TEXT_SITES))

    def test_changed_source_defeats_fake_clean_index_and_status_claims(self):
        path = self.root / historical.p251.BACKEND
        path.write_bytes(path.read_bytes() + b"\n# drift hidden by assume-unchanged\n")
        with patch.object(probe, "_source_report") as observed:
            self.check_report(reason="tracked_disk_blob_mismatch")
            observed.assert_not_called()
        self.assertFalse(any(call.args[1] == "status" for call in self.git.call_args_list))

    def test_changed_native_alias_is_unknown_even_with_matching_synthetic_git_inventory(self):
        path = self.root / historical.p251.BACKEND
        original = path.read_bytes()
        changed = original.replace(
            b"self._dll.CredWriteW(ctypes.byref(credential), 0)",
            b"getattr(self._dll, 'CredWriteW')(ctypes.byref(credential), 0)",
        )
        self.assertNotEqual(changed, original)
        path.write_bytes(changed)
        # The fixture deliberately claims the changed blob belongs to BASE.
        # Independent inherited raw pins and AST obligations must still refuse.
        self.refresh_inventory()
        report = self.check_report(reason="unresolved_p251_p255_source_evidence")
        reasons = {item["reason"] for item in report["issues"]}
        self.assertIn("source_hash_drift_including_possible_sink_or_import_change", reasons)
        self.assertIn({"reason": "unresolved_route_site", "site": "native_credential_write"}, report["issues"])

    def test_changed_source_pin_and_changed_helper_cannot_be_admitted_by_git_claims(self):
        for relative in probe.HELPER_PINS:
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_bytes()
                if relative.endswith("byok_c1_effect_exposure_gate.py"):
                    changed = original.replace(
                        historical.p251.SOURCE_HASHES[historical.p251.LAUNCH].encode(), b"0" * 64,
                    )
                else:
                    changed = original.replace(b"direct_python_native_write", b"removed_native_write_route")
                self.assertNotEqual(changed, original)
                path.write_bytes(changed + b"\nraise RuntimeError('must never execute')\n")
                self.refresh_inventory()
                with patch.object(probe, "_source_report") as observed:
                    self.check_report(reason="diagnostic_helper_pin_drift")
                    observed.assert_not_called()
                path.write_bytes(original)
                self.refresh_inventory()

    def test_preloaded_module_pin_or_assess_tampering_does_not_replace_verified_bytes(self):
        with patch.object(historical.p251, "SOURCE_HASHES", {}), patch.object(
            historical, "assess", side_effect=AssertionError("untrusted preloaded module used")
        ):
            report = self.check_report("OPEN")
        self.assertEqual(len(report["sources"]), 6)

    def test_source_loader_refuses_unverified_bytes_even_when_called_directly(self):
        helpers = {name: (self.root / name).read_bytes() for name in probe.HELPER_PINS}
        changed = dict(helpers)
        changed[next(iter(helpers))] = b"raise AssertionError('executed')\n"
        for bad in ({}, changed):
            with self.subTest(keys=list(bad)), self.assertRaisesRegex(probe.Refusal, "invalid_verified_helper_snapshot"):
                probe._source_report(self.root, bad)

    def test_missing_source(self):
        (self.root / historical.p251.BACKEND).unlink()
        self.check_report(reason="FileNotFoundError")

    def test_wrong_root_is_refused_before_git_or_source_read(self):
        with patch.object(probe, "INTENDED_ROOT", self.root / "other"), patch.object(probe, "_read") as read:
            self.check_report(reason="unintended_repository_root")
        self.git.assert_not_called()
        read.assert_not_called()

    def test_git_source_root_admin_and_common_mismatches(self):
        for command in (("rev-parse", "--show-toplevel"), ("rev-parse", "--absolute-git-dir"),
                        ("rev-parse", "--path-format=absolute", "--git-common-dir")):
            with self.subTest(command=command), patch.dict(self.replies, {command: b"D:/spoof\n"}):
                self.check_report(reason="git_source_root_mismatch")

    def test_wrong_branch_stale_head_parent_tree_and_ambiguous_ref(self):
        changes = (
            (("symbolic-ref", "-q", "HEAD"), b"refs/heads/wrong\n"),
            (("show-ref", "--verify", "--hash", probe.BRANCH), b"0" * 40 + b"\n"),
            (("rev-parse", "--verify", "HEAD^{commit}"), probe.PARENT.encode() + b"\n"),
            (("rev-parse", "--verify", "HEAD^{tree}"), b"0" * 40 + b"\n"),
            (("rev-list", "--parents", "-n", "1", "HEAD"), (probe.BASE + " " + probe.P251_COMMIT + "\n").encode()),
            (("show-ref", "--verify", "--hash", probe.BRANCH), (probe.BASE + "\n" + probe.BASE + "\n").encode()),
            (("rev-parse", "--is-shallow-repository"), b"true\n"),
        )
        for command, reply in changes:
            with self.subTest(command=command, reply=reply), patch.dict(self.replies, {command: reply}):
                self.check_report()

    def test_failed_ancestor_query_is_unknown(self):
        original = self.reply

        def reply(root, *args):
            if args[0] == "merge-base":
                raise probe.Refusal("git_command_failed")
            return original(root, *args)

        self.git.side_effect = reply
        self.check_report(reason="git_command_failed")

    def test_timeout_and_read_denial_are_unknown_without_private_error_details(self):
        with patch.object(probe, "_git", side_effect=subprocess.TimeoutExpired("private command", 30)):
            report = self.check_report(reason="TimeoutExpired")
        self.assertNotIn("private command", json.dumps(report))
        with patch.object(probe, "_read", side_effect=PermissionError("private detail")):
            report = self.check_report(reason="PermissionError")
        self.assertNotIn("private detail", json.dumps(report))

    def test_worktree_pointer_backpointer_common_and_head_spoofs(self):
        for path, raw in (
            (self.root / ".git", b"gitdir: D:/spoof\n"),
            (self.admin / "gitdir", b"D:/spoof/.git\n"),
            (self.admin / "commondir", b"../../spoof\n"),
            (self.admin / "HEAD", probe.BASE.encode() + b"\n"),
        ):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(raw)
                self.check_report()
                path.write_bytes(original)

    def test_missing_duplicated_and_stale_worktree_registration(self):
        command = ("worktree", "list", "--porcelain", "-z")
        good = self.replies[command]
        for raw in (b"", good + good, good.replace(probe.BASE.encode(), probe.PARENT.encode())):
            with self.subTest(raw=raw), patch.dict(self.replies, {command: raw}):
                self.check_report(reason="worktree_registration_mismatch")

    def test_index_drift_and_nonzero_stage(self):
        command = ("ls-files", "--stage", "-z")
        good = self.replies[command]
        for raw in (good.replace(b" 0\t", b" 1\t", 1), good.replace(b"100644 ", b"100755 ", 1), good.split(b"\0", 1)[1]):
            with self.subTest(raw=raw), patch.dict(self.replies, {command: raw}):
                self.check_report()

    def test_inventory_alias_duplicate_traversal_and_malformed_paths(self):
        good = b"100644 blob " + b"a" * 40 + b"\ttools/one.py\0"
        for raw in (good + good, good + good.replace(b"one.py", b"ONE.py"),
                    good.replace(b"tools/one.py", b"../one.py"),
                    good.replace(b"tools/one.py", b"tools/one.py:stream"),
                    good.replace(b"tools/one.py", b"tools\\one.py"), good[:-1], b"broken\0"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                probe._inventory(raw, index=False)

    def test_unexpected_untracked_and_ignored_files_are_blockers(self):
        command = ("ls-files", "--others", "-z")
        good = self.replies[command]
        for raw in (good + b"tools/__init__.py\0", good + b"__pycache__/ignored.pyc\0", good + good,
                    good.split(b"\0", 1)[1], b""):
            with self.subTest(raw=raw), patch.dict(self.replies, {command: raw}):
                self.check_report(reason="unexpected_untracked_files")

    def test_replace_refs_and_grafts_remain_blockers(self):
        command = ("for-each-ref", "--format=%(refname)", "refs/replace/")
        with patch.dict(self.replies, {command: b"refs/replace/fake\n"}):
            self.check_report(reason="replacement_refs_present")
        (self.common / "info").mkdir()
        (self.common / "info/grafts").write_bytes(b"synthetic\n")
        self.check_report(reason="grafts_present")

    def test_mocked_reparse_refused_before_open(self):
        real_lstat = Path.lstat

        class Reparse:
            st_mode = 0
            st_file_attributes = 0x400

        def lstat(path):
            return Reparse() if path == self.root else real_lstat(path)

        with patch.object(Path, "lstat", lstat), patch.object(Path, "open") as opened:
            self.check_report(reason="symlink_or_reparse_path")
            opened.assert_not_called()

    def test_hardlink_source_is_refused_without_creating_a_link(self):
        info = (self.root / historical.p251.BACKEND).lstat()

        class Hardlinked:
            st_mode = info.st_mode
            st_nlink = 2
            st_size = info.st_size

        with patch.object(probe, "_plain_path"), patch.object(Path, "lstat", return_value=Hardlinked()):
            with self.assertRaisesRegex(probe.Refusal, "nonregular_or_hardlinked_file"):
                probe._read(self.root / historical.p251.BACKEND)

    def test_second_sample_detects_changes_and_fresh_restoration(self):
        first = self.check_report("OPEN")
        source_report = probe._source_report

        def mutate(root, helpers):
            result = source_report(root, helpers)
            path = root / probe.ADDITIONS[0]
            path.write_bytes(path.read_bytes() + b"# changed during sampling\n")
            return result

        addition = self.root / probe.ADDITIONS[0]
        original = addition.read_bytes()
        with patch.object(probe, "_source_report", side_effect=mutate):
            self.check_report(reason="source_context_changed_during_assessment")
        addition.write_bytes(original)
        self.assertEqual(probe.assess(self.root), first)

    def test_no_product_imports_or_process_calls_during_source_assessment(self):
        before = set(sys.modules)
        with patch.object(subprocess, "run", side_effect=AssertionError("unexpected process")):
            self.check_report("OPEN")
        self.assertFalse(any(name == "nayeon" or name.startswith("nayeon.") for name in set(sys.modules) - before))

    def test_original_p251_report_still_has_separate_unmatched_root_contract(self):
        self.assertNotEqual(historical.p251.INTENDED_ROOT, probe.INTENDED_ROOT)
        with patch.object(historical.p251, "REPO_ROOT", self.root), patch.object(
            historical.p251, "_assess"
        ) as old_assess, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(historical.p251.main(["--report"]), 0)
        old_assess.assert_not_called()
        report = json.loads(output.getvalue())
        self.assertEqual(report["assessment"], "UNKNOWN")
        self.assertNotEqual(report["assessment"], "KNOWN_EFFECT_EXPOSURE")
        self.assertEqual(report["issues"], [{"reason": "unintended_repository_root"}])
        self.check_report("OPEN")

    def test_cli_has_mandatory_blocker_exit_for_open_and_unknown(self):
        with patch.object(probe, "ROOT", self.root):
            for expected in ("OPEN", "UNKNOWN"):
                if expected == "UNKNOWN":
                    (self.root / historical.p251.BACKEND).unlink()
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(probe.main([]), 3)
                self.assertEqual(json.loads(output.getvalue())["assessment"], expected)


class RuntimeAndInvocationTests(unittest.TestCase):
    def test_environment_overrides_block_before_any_source_or_git(self):
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS",
                     "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "PYTHONPATH", "PYTHONHOME"):
            with self.subTest(name=name), patch.dict(os.environ, {name: "synthetic"}), patch.object(
                probe, "_snapshot"
            ) as snapshot:
                report = probe.assess(probe.ROOT)
                self.assertEqual(report["assessment"], "UNKNOWN")
                self.assertIn({"reason": "unsafe_environment_override"}, report["issues"])
                snapshot.assert_not_called()

    def test_unisolated_invocation_is_unknown_and_exit_three(self):
        with patch.object(sys, "dont_write_bytecode", False), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(probe.main([]), 3)
        self.assertEqual(json.loads(output.getvalue())["assessment"], "UNKNOWN")

    def test_no_root_manifest_or_approval_override(self):
        for args in (["--root", "D:/spoof"], ["--manifest", "fake.json"], ["--grant-go"], ["--release-admission"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                probe.main(args)
            self.assertEqual(result.exception.code, 2)

    def test_git_wrapper_uses_fixed_offline_read_execution_and_fails_closed(self):
        child = subprocess.CompletedProcess([], 0, stdout=b"reply\n", stderr=b"")
        with patch.object(subprocess, "run", return_value=child) as run:
            self.assertEqual(probe._git(probe.ROOT, "rev-parse", "HEAD"), b"reply\n")
        args, kwargs = run.call_args
        self.assertEqual(args[0][0], str(probe.GIT))
        self.assertNotIn("shell", kwargs)
        for key in ("GIT_NO_REPLACE_OBJECTS", "GIT_NO_LAZY_FETCH", "GIT_CONFIG_NOSYSTEM"):
            self.assertEqual(kwargs["env"][key], "1")
        self.assertEqual(kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
        self.assertEqual(kwargs["timeout"], 30)
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"", b"private detail")):
            with self.assertRaisesRegex(probe.Refusal, "git_command_failed"):
                probe._git(probe.ROOT, "rev-parse", "HEAD")


class CheckoutTests(unittest.TestCase):
    def test_isolated_native_cli_exact_authorized_draft_checkout(self):
        # This is real read-only Git/source validation when run by the host.
        # Keep evidence logs outside this root. Unexpected files fail admission.
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(probe.ROOT / probe.ADDITIONS[0])],
            cwd=probe.ROOT, capture_output=True, text=True, timeout=120, check=False,
        )
        self.assertEqual(result.returncode, 3, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["assessment"], "OPEN", report["issues"])
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(report["source_context_admitted"])
        self.assertFalse(report["release_admitted"])
        self.assertEqual(report["source_context"]["head"], probe.BASE)


if __name__ == "__main__":
    unittest.main()
