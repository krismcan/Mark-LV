"""P245 source-era split: pure negative tests and genuine hosted Windows candidate."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct
import tempfile
import unittest
from unittest import mock

from scripts import p245_p76_current_source as candidate
from tests import phase8_byok_c1_p76_scope as frozen


class P245PureNegativeTests(unittest.TestCase):
    def test_frozen_branch_literal_unchanged(self):
        raw = candidate.source_file("tests/phase8_byok_c1_p76_scope.py").read_bytes()
        self.assertEqual(candidate.historical_branch_literal(raw), candidate.HISTORICAL_P76_BRANCH)

    def test_real_historical_p76_gate_still_denies_descendant(self):
        with self.assertRaisesRegex(frozen.P76ScopeRefused, "wrong exact P76"):
            frozen.assert_p76_offline_integrity()

    def test_all_four_original_failed_methods_remain_unwaived(self):
        self.assertEqual(len(candidate.ORIGINAL_FAILURE_IDS), 4)
        self.assertEqual(len(set(candidate.ORIGINAL_FAILURE_IDS)), 4)
        self.assertTrue(all(t.startswith("tests.test_") for t in candidate.ORIGINAL_FAILURE_IDS))

    def test_no_paths_outside_exact_source_manifest(self):
        for path in ("../tests/phase8_byok_c1_p76_scope.py",
                     "/Windows/System32/config/SAM",
                     r"C:\Windows\System32\config",
                     "tests/../tests/phase8_byok_c1_p76_scope.py",
                     "nayeon/brain/user_secrets.py", "",
                     "tests//phase8_byok_c1_p76_scope.py"):
            with self.subTest(path=path):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.source_file(path)

    def test_historical_tag_pin_is_not_overrideable(self):
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "tag authority"):
            candidate.validate_historical_tag("f" * 40)

    def test_missing_or_nonliteral_historical_branch_denied(self):
        for raw in (b"BRANCH = compute_from_environment()\n", b"OTHER='a'\n",
                    b"BRANCH='a'\nBRANCH='b'\n"):
            with self.subTest(source=raw):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.historical_branch_literal(raw)

    def test_untrusted_host_environment_refused(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "hosted Windows"):
                candidate.validate_event(branch=candidate.BRANCH, head="a" * 40)

    def test_git_process_environment_drops_injected_authority(self):
        with mock.patch.dict(os.environ, {
            "GIT_INDEX_FILE": "C:/forged-index", "GIT_CONFIG_COUNT": "1",
            "P134_TEST_GRANT": "false", "GIT_WORK_TREE": "C:/wrong",
        }):
            env = candidate.environment()
        for key in ("GIT_INDEX_FILE", "GIT_CONFIG_COUNT", "P134_TEST_GRANT",
                    "GIT_WORK_TREE"):
            self.assertNotIn(key, env)
        self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")

    def test_read_only_script_imports_no_wincred_provider_or_effect_modules(self):
        source = candidate.source_file("scripts/p245_p76_current_source.py").read_bytes()
        tree = ast.parse(source)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                roots.add((node.module or "").split(".")[0])
        self.assertTrue(roots.isdisjoint({"ctypes", "winreg", "socket", "requests", "nayeon"}))
        self.assertNotIn(b"CredWriteW", source)
        self.assertNotIn(b"CredDeleteW", source)

    def test_candidate_never_classifies_legacy_failures_as_green(self):
        self.assertTrue(candidate.ORIGINAL_FAILURE_IDS[0].endswith("test_live_brain_reader_tamper_remains_rejected_after_historical_replay"))
        self.assertEqual(candidate.BASE, "da9c436a177b3ec68db0eff2b610180b745bfb2b")


class P245CompleteProofTests(unittest.TestCase):
    """All Git writes and hostile source changes stay in a disposable repository."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="p245-synthetic-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        self.env = candidate.environment()
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="P245 Synthetic", GIT_COMMITTER_NAME="P245 Synthetic",
                        GIT_AUTHOR_EMAIL="p245@example.invalid",
                        GIT_COMMITTER_EMAIL="p245@example.invalid")
        self.raw_git("init", "-q")
        (self.root / "ordinary.txt").write_bytes(b"original predecessor bytes\n")
        (self.root / "second.txt").write_bytes(b"second tracked source\n")
        self.raw_git("add", "--", "ordinary.txt", "second.txt")
        tree = self.raw_git("write-tree").strip().decode()
        commit = self.raw_git("commit-tree", tree, "-m", "Synthetic P245 fixture").strip().decode()
        self.raw_git("update-ref", "refs/heads/synthetic", commit)
        self.raw_git("symbolic-ref", "HEAD", "refs/heads/synthetic")
        patcher = mock.patch.object(candidate, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def raw_git(self, *args):
        child = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "-c", "core.fsmonitor=false",
             "-c", "commit.gpgsign=false", "-C", str(self.root), *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=True, timeout=15, env=self.env, shell=False)
        return child.stdout

    def test_complete_real_git_tree_index_and_raw_bytes(self):
        proof = candidate.complete_source()
        self.assertEqual(candidate.tree_oid(proof["tree"]), self.raw_git("rev-parse", "HEAD^{tree}").strip().decode())
        self.assertEqual(set(proof["tree"]), {"ordinary.txt", "second.txt"})
        self.assertEqual(set(proof["index"]), set(proof["disk"]))
        for rel, (mode, oid) in proof["tree"].items():
            self.assertEqual(proof["index"][rel], [mode, oid, "0"])
            self.assertEqual(proof["disk"][rel]["blob_oid"], oid)
            self.assertEqual(candidate.blob_oid((self.root / rel).read_bytes()), oid)

    def test_assume_unchanged_even_with_clean_porcelain_refused(self):
        self.raw_git("update-index", "--assume-unchanged", "--", "ordinary.txt")
        (self.root / "ordinary.txt").write_bytes(b"hidden predecessor tamper\n")
        self.assertEqual(self.raw_git("status", "--porcelain=v1"), b"")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index flags"):
            candidate.complete_source()

    def test_skip_worktree_even_with_clean_porcelain_refused(self):
        self.raw_git("update-index", "--skip-worktree", "--", "ordinary.txt")
        (self.root / "ordinary.txt").write_bytes(b"hidden predecessor tamper\n")
        self.assertEqual(self.raw_git("status", "--porcelain=v1"), b"")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index flags"):
            candidate.complete_source()

    def test_both_index_flags_refused_without_disk_edit(self):
        self.raw_git("update-index", "--skip-worktree", "--", "ordinary.txt")
        self.raw_git("update-index", "--assume-unchanged", "--", "ordinary.txt")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index flags"):
            candidate.complete_source()

    def test_intent_to_add_index_flag_refused(self):
        (self.root / "intent.txt").write_bytes(b"intent-to-add fixture\n")
        self.raw_git("add", "--intent-to-add", "--", "intent.txt")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index flags"):
            candidate.complete_source()

    def test_unknown_extended_index_flags_refused(self):
        raw = candidate.git("ls-files", "--stage", "--debug", "-v", "-z")
        for flag in (b"200000", b"20004000", b"1", b"8000", b"40004000"):
            with self.subTest(flag=flag), mock.patch.object(
                    candidate, "git", return_value=raw.replace(b"flags: 0\n", b"flags: " + flag + b"\n", 1)):
                with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index flags"):
                    candidate.index_entries()

    def test_raw_index_flags_cannot_hide_behind_synthetic_clean_git_debug(self):
        clean_debug = candidate.git("ls-files", "--stage", "--debug", "-v", "-z")
        real_git = candidate.git
        path = self.root / ".git" / "index"
        original = path.read_bytes()
        original_flags = struct.unpack_from(">H", original, 72)[0]

        def replies(*args):
            if args == ("ls-files", "--stage", "--debug", "-v", "-z"):
                return clean_debug
            return real_git(*args)

        for flag in (0x8000, 0x4000, 0x1000, 0x2000):
            hostile = bytearray(original[:-20])
            struct.pack_into(">H", hostile, 72, original_flags | flag)
            path.write_bytes(bytes(hostile) + hashlib.sha1(hostile).digest())
            with self.subTest(flag=flag), mock.patch.object(candidate, "git", side_effect=replies):
                with self.assertRaisesRegex(candidate.CurrentSourceRefused, "raw index flags"):
                    candidate.index_entries()
        path.write_bytes(original)

    def test_raw_index_oid_cannot_hide_behind_synthetic_git_inventory(self):
        clean_debug = candidate.git("ls-files", "--stage", "--debug", "-v", "-z")
        real_git = candidate.git
        path = self.root / ".git" / "index"
        raw = bytearray(path.read_bytes()[:-20])
        raw[52:72] = b"\x12" * 20
        path.write_bytes(bytes(raw) + hashlib.sha1(raw).digest())

        def replies(*args):
            if args == ("ls-files", "--stage", "--debug", "-v", "-z"):
                return clean_debug
            return real_git(*args)

        with mock.patch.object(candidate, "git", side_effect=replies):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "raw index and Git inventory"):
                candidate.index_entries()

    def test_raw_index_checksum_version_and_extensions_fail_closed(self):
        raw = (self.root / ".git" / "index").read_bytes()
        bad_version = bytearray(raw[:-20])
        struct.pack_into(">I", bad_version, 4, 4)
        invalid = [raw[:-1], b"bad header", bytes(bad_version) + hashlib.sha1(bad_version).digest()]
        for signature in (b"FSMN", b"link", b"sdir", b"ABCD"):
            extension = raw[:-20] + signature + struct.pack(">I", 0)
            invalid.append(extension + hashlib.sha1(extension).digest())
        for data in invalid:
            with self.subTest(data=data[:12]):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.parse_raw_index(data)

    def test_index_blob_divergence_from_head_refused(self):
        (self.root / "ordinary.txt").write_bytes(b"staged tamper\n")
        self.raw_git("add", "--", "ordinary.txt")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index differs"):
            candidate.complete_source()

    def test_index_mode_divergence_from_head_refused(self):
        self.raw_git("update-index", "--chmod=+x", "--", "ordinary.txt")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index differs"):
            candidate.complete_source()

    def test_extra_and_missing_index_entries_refused(self):
        (self.root / "extra.txt").write_bytes(b"unexpected index path\n")
        self.raw_git("add", "--", "extra.txt")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index differs"):
            candidate.complete_source()
        self.raw_git("update-index", "--force-remove", "--", "extra.txt", "second.txt")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index differs"):
            candidate.complete_source()

    def test_unmerged_index_stage_refused(self):
        raw = candidate.git("ls-files", "--stage", "--debug", "-v", "-z")
        with mock.patch.object(candidate, "git", return_value=raw.replace(b" 0\t", b" 2\t", 1)):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "index flags, stage"):
                candidate.index_entries()

    def test_malformed_duplicate_alias_and_nonblob_trees_refused(self):
        oid = b"a" * 40
        first = b"100644 blob " + oid + b"\tordinary.txt\0"
        for raw in (first[:-1], first + first,
                    b"120000 blob " + oid + b"\tlink\0",
                    b"160000 commit " + oid + b"\tmodule\0",
                    first + b"100644 blob " + oid + b"\tORDINARY.txt\0",
                    b"100644 blob " + oid + b"\tDir/a\0" +
                    b"100644 blob " + oid + b"\tdir/b\0"):
            with self.subTest(raw=raw), mock.patch.object(candidate, "git", return_value=raw):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.head_entries()

    def test_unexpected_tracked_path_tampering_refused(self):
        self.assertNotIn("ordinary.txt", candidate.FROZEN)
        self.assertNotIn("ordinary.txt", candidate.ADDED)
        (self.root / "ordinary.txt").write_bytes(b"ordinary tracked file corrupted\n")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "Git-byte mismatch: ordinary.txt"):
            candidate.complete_source()

    def test_live_verifier_cannot_accept_synthetic_clean_status_with_bad_bytes(self):
        (self.root / "ordinary.txt").write_bytes(b"synthetic false-green bytes\n")
        real_git = candidate.git

        def replies(*args):
            if args[0] == "status":
                return b""
            if args[0] == "merge-base":
                return candidate.BASE.encode() + b"\n"
            if args[0] == "diff":
                return ("\n".join(sorted(candidate.ADDED)) + "\n").encode()
            return real_git(*args)

        with mock.patch.object(candidate, "git", side_effect=replies), mock.patch.object(
                candidate, "validate_event"), mock.patch.object(candidate, "git_identity", return_value={}):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "Git-byte mismatch"):
                candidate.verify_current(branch=candidate.BRANCH, head="a" * 40)

    def test_crlf_raw_bytes_cannot_be_normalized_into_git_match(self):
        (self.root / "ordinary.txt").write_bytes(b"original predecessor bytes\r\n")
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "Git-byte mismatch"):
            candidate.complete_source()

    def test_hardlinked_source_refused(self):
        original = self.root / "ordinary.txt"
        alias = self.root / "alias.txt"
        os.link(original, alias)
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "hardlinked"):
            candidate.complete_source()

    def test_reparse_source_and_root_ancestor_refused(self):
        real_lstat = Path.lstat

        def reparse(path, *args, **kwargs):
            meta = real_lstat(path, *args, **kwargs)
            if path == target:
                return mock.Mock(st_mode=meta.st_mode, st_file_attributes=0x400)
            return meta

        for target in (self.root / "ordinary.txt", self.root, self.root.parent):
            with self.subTest(target=target), mock.patch.object(Path, "lstat", reparse):
                with self.assertRaisesRegex(candidate.CurrentSourceRefused, "reparse"):
                    candidate.raw_source("ordinary.txt")

    def test_symlink_metadata_refused(self):
        real_lstat = Path.lstat

        def symlink(path, *args, **kwargs):
            if path == self.root / "ordinary.txt":
                return mock.Mock(st_mode=0o120777, st_file_attributes=0)
            return real_lstat(path, *args, **kwargs)

        with mock.patch.object(Path, "lstat", symlink):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "linked"):
                candidate.raw_source("ordinary.txt")

    def test_windows_alias_and_traversal_paths_refused(self):
        for rel in ("../ordinary.txt", "dir//ordinary.txt", "dir/CON.txt", "ordinary.txt.",
                    "dir/NUL", "dir/COM1.txt", "ORDINA~1.TXT", "ordinary.txt:stream"):
            with self.subTest(rel=rel):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.raw_source(rel)

    def test_bounded_missing_and_oversized_sources_refused(self):
        (self.root / "ordinary.txt").unlink()
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "missing"):
            candidate.complete_source()
        (self.root / "ordinary.txt").write_bytes(b"x" * (candidate.MAX_FILE_BYTES + 1))
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "oversized"):
            candidate.complete_source()

    def test_source_identity_changes_during_read_refused(self):
        real_fstat = os.fstat

        def changed(fd):
            meta = real_fstat(fd)
            return mock.Mock(st_dev=meta.st_dev, st_ino=meta.st_ino + 1, st_size=meta.st_size,
                             st_mtime_ns=meta.st_mtime_ns, st_ctime_ns=meta.st_ctime_ns,
                             st_nlink=meta.st_nlink, st_mode=meta.st_mode)

        with mock.patch.object(candidate.os, "fstat", side_effect=changed):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "changed during"):
                candidate.raw_source("ordinary.txt")

    def bounded_read_metadata(self):
        meta = (self.root / "ordinary.txt").lstat()
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_nlink", "st_mode")
        snapshots = [mock.Mock(**{field: getattr(meta, field) for field in fields},
                               st_ctime_ns=ctime, st_file_attributes=0)
                     for ctime in (100, 200, 200, 100)]
        return snapshots

    def read_with_metadata(self, snapshots, limit=candidate.MAX_FILE_BYTES):
        before, opened, after, final = snapshots
        with mock.patch.object(candidate, "checked_node", side_effect=[before, final]), \
                mock.patch.object(candidate.os, "fstat", side_effect=[opened, after]):
            return candidate.bounded_file(self.root / "ordinary.txt", limit)

    def test_stable_cross_api_ctime_difference_accepts_exact_bytes(self):
        snapshots = self.bounded_read_metadata()
        raw, identity = self.read_with_metadata(snapshots)
        self.assertEqual(raw, b"original predecessor bytes\n")
        self.assertEqual(identity, [snapshots[0].st_dev, snapshots[0].st_ino])

    def test_ctime_changes_within_either_api_refused(self):
        for position in (2, 3):
            snapshots = self.bounded_read_metadata()
            snapshots[position].st_ctime_ns += 1
            with self.subTest(position=position):
                with self.assertRaisesRegex(candidate.CurrentSourceRefused, "changed during"):
                    self.read_with_metadata(snapshots)

    def test_cross_api_stable_metadata_changes_refused(self):
        for field in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_nlink", "st_mode"):
            for position in (1, 2, 3):
                snapshots = self.bounded_read_metadata()
                setattr(snapshots[position], field, getattr(snapshots[position], field) + 1)
                with self.subTest(field=field, position=position):
                    with self.assertRaisesRegex(candidate.CurrentSourceRefused, "changed during"):
                        self.read_with_metadata(snapshots)

    def test_reparse_metadata_at_any_read_observation_refused(self):
        for position in range(4):
            snapshots = self.bounded_read_metadata()
            snapshots[position].st_file_attributes = 0x400
            with self.subTest(position=position):
                with self.assertRaisesRegex(candidate.CurrentSourceRefused, "changed during"):
                    self.read_with_metadata(snapshots)

    def test_bounded_read_count_limits_and_read_errors_refused(self):
        snapshots = self.bounded_read_metadata()
        for meta in snapshots:
            meta.st_size -= 1
        for limit in (candidate.MAX_FILE_BYTES, snapshots[0].st_size):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(candidate.CurrentSourceRefused, "changed during"):
                    self.read_with_metadata(snapshots, limit=limit)
        snapshots = self.bounded_read_metadata()
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "oversized"):
            self.read_with_metadata(snapshots, limit=snapshots[0].st_size - 1)
        with mock.patch.object(Path, "open", side_effect=OSError("synthetic read refusal")):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "read unavailable"):
                candidate.raw_source("ordinary.txt")

    def test_index_changes_during_complete_proof_refused(self):
        first = candidate.index_entries()
        second = copy.deepcopy(first)
        second["ordinary.txt"][2] = "8000"
        with mock.patch.object(candidate, "index_entries", side_effect=[first, second]):
            with self.assertRaisesRegex(candidate.CurrentSourceRefused, "changed during"):
                candidate.complete_source()

    def test_object_format_replacement_and_both_graft_locations_refused(self):
        common = Path(self.temporary.name) / "common-git"
        worktree = Path(self.temporary.name) / "worktree-git"

        def replies(*args):
            table = {
                ("rev-parse", "HEAD"): ("a" * 40).encode() + b"\n",
                ("branch", "--show-current"): candidate.BRANCH.encode() + b"\n",
                ("rev-parse", "--is-shallow-repository"): b"false\n",
                ("rev-parse", "--show-object-format=storage"): b"sha1\n",
                ("rev-parse", "--show-object-format=input"): b"sha1\n",
                ("for-each-ref", "refs/replace"): b"",
                ("rev-parse", "--absolute-git-dir"): str(worktree).encode() + b"\n",
                ("rev-parse", "--path-format=absolute", "--git-common-dir"): str(common).encode() + b"\n",
            }
            if args == hostile:
                return bad
            return table[args]

        for hostile, bad in ((("rev-parse", "--show-object-format=storage"), b"sha256\n"),
                             (("rev-parse", "--show-object-format=input"), b"sha1 sha256\n"),
                             (("for-each-ref", "refs/replace"), b"replacement\n")):
            with self.subTest(hostile=hostile), mock.patch.object(candidate, "git", side_effect=replies):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.git_identity(branch=candidate.BRANCH, head="a" * 40)
        hostile, bad = (), b""
        for directory in (common, worktree):
            graft = directory / "info" / "grafts"
            graft.parent.mkdir(parents=True)
            graft.write_bytes(b"untrusted graft\n")
            with self.subTest(directory=directory), mock.patch.object(candidate, "git", side_effect=replies):
                with self.assertRaisesRegex(candidate.CurrentSourceRefused, "grafts"):
                    candidate.git_identity(branch=candidate.BRANCH, head="a" * 40)
            graft.unlink()


def synthetic_complete_witness():
    """Deterministic runner fixture, used only with a mocked live verifier."""
    tree, index, disk = {}, {}, {}
    for number, rel in enumerate(sorted(set(candidate.FROZEN) | candidate.ADDED | {"ordinary.txt"})):
        oid = candidate.blob_oid(rel.encode())
        tree[rel] = ["100644", oid]
        index[rel] = ["100644", oid, "0"]
        disk[rel] = {"blob_oid": oid, "sha256": candidate.FROZEN.get(rel, candidate.digest(rel.encode())),
                     "size": len(rel), "identity": [1, number + 1]}
    return {
        "schema": "P245-COMPLETE-SOURCE-V2", "candidate_source_pass": True,
        "head": "a" * 40, "branch": candidate.BRANCH, "parent": candidate.BASE,
        "original_immutable_source": candidate.HISTORICAL, "frozen_sha256": dict(candidate.FROZEN),
        "historical_P76_wrong_branch_refusal_preserved": True,
        "four_original_P234_failures_unwaived": list(candidate.ORIGINAL_FAILURE_IDS),
        "real_key_admission": "NO-GO", "production_release": "HOLD",
        "qualified_approvals": "0/7", "full_product_regressions": "0/3",
        "source_identity": {"root": "synthetic", "root_identity": [1, 2], "git_dir": "synthetic/git",
                            "common_dir": "synthetic/common", "head": "a" * 40, "branch": candidate.BRANCH,
                            "tree_oid": candidate.tree_oid(tree), "object_format": "sha1", "replacements": [], "grafts": [],
                            "tag": {"name": candidate.TAG, "oid": candidate.TAG_OID,
                                    "target": candidate.TAG_TARGET, "raw_sha256": "C" * 64}},
        "complete_source": {"tree": tree, "index": index, "disk": disk},
        "candidate_files": {rel: disk[rel] for rel in sorted(candidate.ADDED)},
    }


class P245SuiteReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="p245-receipt-synthetic-")
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name) / "evidence"
        self.proof = synthetic_complete_witness()

    def run_synthetic(self, proofs=None, *, native_exit=0, log=b"Ran 1 test in 0.001s\n\nOK\n"):
        def child(*args, **kwargs):
            kwargs["stdout"].write(log)
            return subprocess.CompletedProcess(args[0], native_exit)

        if proofs is None:
            proofs = [copy.deepcopy(self.proof), copy.deepcopy(self.proof)]
        with mock.patch.object(candidate, "verify_current", side_effect=proofs) as verifier, mock.patch.object(
                candidate, "expected_tests", return_value=1), mock.patch.object(
                candidate.subprocess, "run", side_effect=child), mock.patch.dict(
                os.environ, {"GITHUB_SHA": "a" * 40}):
            result = candidate.run_hosted_suite(self.output)
        receipt = json.loads((self.output / "suite-receipt.json").read_text(encoding="utf-8"))
        return result, receipt, verifier.call_count

    def test_matching_complete_proofs_and_native_receipts(self):
        result, receipt, calls = self.run_synthetic()
        self.assertEqual((result, calls), (0, 2))
        self.assertTrue(receipt["candidate_suite_pass"])
        self.assertEqual(receipt["before"]["witness_sha256"], receipt["after"]["witness_sha256"])
        for label in candidate.SUITES:
            self.assertEqual(receipt["suites"][label]["native_exit"], 0)
            self.assertEqual(receipt["suites"][label]["log_sha256"],
                             candidate.digest((self.output / (label + ".log")).read_bytes()))
        self.assertNotIn("workflow_exit", receipt["suites"]["live-candidate"])

    def test_before_after_candidate_bytes_mismatch_refused(self):
        after = copy.deepcopy(self.proof)
        path = "scripts/p245_p76_current_source.py"
        after["complete_source"]["disk"][path]["sha256"] = "D" * 64
        result, receipt, calls = self.run_synthetic([self.proof, after])
        self.assertEqual((result, calls), (1, 2))
        self.assertFalse(receipt["candidate_suite_pass"])
        self.assertEqual(receipt["suites"]["live-candidate"]["native_exit"], 0)

    def test_before_after_other_tracked_bytes_mismatch_refused(self):
        after = copy.deepcopy(self.proof)
        after["complete_source"]["disk"]["ordinary.txt"]["sha256"] = "F" * 64
        result, receipt, calls = self.run_synthetic([self.proof, after])
        self.assertEqual((result, calls), (1, 2))
        self.assertFalse(receipt["candidate_suite_pass"])

    def test_before_after_identity_tree_tag_and_index_mismatch_refused(self):
        for field in ("root", "root_identity", "tree_oid", "tag", "index"):
            after = copy.deepcopy(self.proof)
            if field == "index":
                after["complete_source"]["index"][next(iter(candidate.FROZEN))][2] = "8000"
            elif field == "tag":
                after["source_identity"]["tag"]["raw_sha256"] = "E" * 64
            else:
                after["source_identity"][field] = {"root": "different", "root_identity": [9, 9],
                                                  "tree_oid": "c" * 40}[field]
            with self.subTest(field=field):
                with self.assertRaises(candidate.CurrentSourceRefused):
                    candidate.compare_witnesses(self.proof, after)

    def test_missing_incomplete_and_pass_only_witnesses_refused(self):
        for proof in (None, {}, {"candidate_source_pass": True},
                      {"schema": "P245-COMPLETE-SOURCE-V2", "candidate_source_pass": True}):
            with self.subTest(proof=proof):
                result, receipt, calls = self.run_synthetic([proof, proof])
                self.assertEqual((result, calls), (1, 2))
                self.assertFalse(receipt["candidate_suite_pass"])
                self.assertFalse(receipt["before"]["complete"])
                self.assertTrue(receipt["after"]["attempted"])

    def test_dropped_other_tracked_path_cannot_be_a_complete_witness(self):
        incomplete = copy.deepcopy(self.proof)
        for inventory in ("tree", "index", "disk"):
            del incomplete["complete_source"][inventory]["ordinary.txt"]
        result, receipt, calls = self.run_synthetic([incomplete, incomplete])
        self.assertEqual((result, calls), (1, 2))
        self.assertFalse(receipt["candidate_suite_pass"])

    def test_final_proof_failure_overrides_green_native_exits(self):
        result, receipt, calls = self.run_synthetic(
            [self.proof, candidate.CurrentSourceRefused("post-suite tamper")])
        self.assertEqual((result, calls), (1, 2))
        self.assertFalse(receipt["after"]["complete"])
        self.assertEqual(receipt["suites"]["live-candidate"]["native_exit"], 0)

    def test_before_proof_failure_still_records_final_attempt(self):
        result, receipt, calls = self.run_synthetic(
            [candidate.CurrentSourceRefused("initial source tamper"), self.proof])
        self.assertEqual((result, calls), (1, 2))
        self.assertEqual(receipt["suites"], {})
        self.assertTrue(receipt["after"]["complete"])

    def test_nonzero_native_exit_stays_distinct_from_workflow_hold_exit(self):
        result, receipt, calls = self.run_synthetic(native_exit=7)
        self.assertEqual((result, calls), (1, 2))
        self.assertEqual(receipt["suites"]["live-candidate"]["native_exit"], 7)
        self.assertFalse(receipt["candidate_suite_pass"])

    def test_synthetic_false_green_zero_or_missing_test_summary_refused(self):
        for log in (b"", b"OK\n", b"Ran 0 tests in 0.001s\n\nOK\n",
                    b"Ran 1 test in 0.001s\n\nOK (skipped=1)\n"):
            with self.subTest(log=log):
                result, receipt, calls = self.run_synthetic(log=log)
                self.assertEqual((result, calls), (1, 2))
                self.assertEqual(receipt["suites"]["live-candidate"]["native_exit"], 0)
                self.assertFalse(receipt["candidate_suite_pass"])

    def test_native_timeout_or_missing_attempt_refused(self):
        with mock.patch.object(candidate, "verify_current", side_effect=[self.proof, self.proof]), mock.patch.object(
                candidate, "expected_tests", return_value=1), mock.patch.object(
                candidate.subprocess, "run", side_effect=subprocess.TimeoutExpired("synthetic", 240)), mock.patch.dict(
                os.environ, {"GITHUB_SHA": "a" * 40}):
            self.assertEqual(candidate.run_hosted_suite(self.output), 1)
        receipt = json.loads((self.output / "suite-receipt.json").read_text(encoding="utf-8"))
        self.assertFalse(receipt["candidate_suite_pass"])
        self.assertIsNone(receipt["suites"]["live-candidate"]["native_exit"])

    def test_missing_second_suite_attempt_refused(self):
        def child(*args, **kwargs):
            kwargs["stdout"].write(b"Ran 1 test in 0.001s\n\nOK\n")
            return subprocess.CompletedProcess(args[0], 0)

        with mock.patch.object(candidate, "verify_current", side_effect=[self.proof, self.proof]), mock.patch.object(
                candidate, "expected_tests", side_effect=[1, candidate.CurrentSourceRefused("missing inventory")]), mock.patch.object(
                candidate.subprocess, "run", side_effect=child), mock.patch.dict(
                os.environ, {"GITHUB_SHA": "a" * 40}):
            self.assertEqual(candidate.run_hosted_suite(self.output), 1)
        receipt = json.loads((self.output / "suite-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(set(receipt["suites"]), {"pure-negative"})
        self.assertTrue(receipt["after"]["complete"])


class P245GenuineHostedWindowsCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # These methods are run only on genuine branch-bound GitHub Windows-2025.
        cls.sha = os.environ.get("GITHUB_SHA", "")
        cls.proof = candidate.verify_current(branch=candidate.BRANCH, head=cls.sha)

    def test_positive_read_only_current_source_and_all_six_frozen_witnesses(self):
        self.assertTrue(self.proof["candidate_source_pass"])
        self.assertEqual(self.proof["head"], self.sha)
        self.assertEqual(self.proof["parent"], candidate.BASE)
        self.assertEqual(self.proof["frozen_sha256"], candidate.FROZEN)
        self.assertEqual(self.proof["real_key_admission"], "NO-GO")
        self.assertEqual(self.proof["production_release"], "HOLD")

    def test_original_four_p234_failures_never_marked_pass(self):
        self.assertEqual(self.proof["four_original_P234_failures_unwaived"],
                         list(candidate.ORIGINAL_FAILURE_IDS))
        self.assertTrue(self.proof["historical_P76_wrong_branch_refusal_preserved"])

    def test_negative_historical_branch_is_not_new_authority(self):
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "signed event"):
            candidate.verify_current(branch=candidate.HISTORICAL_P76_BRANCH, head=self.sha)

    def test_negative_untrusted_new_head_cannot_pass(self):
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "signed event"):
            candidate.verify_current(branch=candidate.BRANCH, head="f" * 40)

    def test_negative_wrong_source_parent_not_admitted(self):
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "signed event"):
            candidate.verify_current(branch=candidate.BRANCH, head=self.sha,
                                     ancestor="f" * 40)

    def test_negative_substituted_frozen_p76_sha_denied(self):
        path = "tests/phase8_byok_c1_p76_scope.py"
        with self.assertRaisesRegex(candidate.CurrentSourceRefused, "witness mismatch"):
            candidate.verify_current(branch=candidate.BRANCH, head=self.sha,
                                     digest_override={path: "0" * 64})

    def test_original_historical_refusal_in_actual_current_branch(self):
        with self.assertRaisesRegex(frozen.P76ScopeRefused, "wrong exact P76"):
            frozen.assert_p76_offline_integrity()


if __name__ == "__main__":
    unittest.main()
