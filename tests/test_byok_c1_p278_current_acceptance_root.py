"""Offline root custody and replacement acceptance proposal; no native effects.

Only stdlib, read-only Git, text copies and deterministic mocked metadata/Git.
No credential backend, package payload, service or reviewed AST is executed.
The original P216 suite is immutable and remains independently RED/unwaived.
"""
from contextlib import contextmanager
from dataclasses import replace
import hashlib
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from nayeon.brain import p211_high_assurance_package_quarantine as quarantine
from nayeon.brain import p216_service_store_decision as inventory


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_FIELDS = (
    "release_eligible", "real_key_admissible", "protected_service_store_installed",
    "legacy_route_isolated_by_OS", "trusted_user_presence_proven",
    "machine_code_integrity_approved", "user_scope_key_migration_authorized",
)


@contextmanager
def source_copy(*, nested=False):
    with TemporaryDirectory(prefix="p278-source-", dir=ROOT if nested else None) as directory:
        root = Path(directory).resolve(strict=True)
        for relative in quarantine._FIXED_LEGACY_FILES:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        yield root


def reply(stdout, stderr=b""):
    return subprocess.CompletedProcess(["git"], 0, stdout, stderr)


class CurrentAcceptanceRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = inventory._git_tracked_python(ROOT)
        cls.receipt = inventory.review_proposed_service_store(ROOT, cls.paths)

    def assert_hold(self, receipt, status):
        self.assertIs(receipt.status, status)
        for field in AUTHORITY_FIELDS:
            self.assertIs(getattr(receipt, field), False, field)
        self.assertEqual(receipt.outstanding_external_decisions, inventory.G0_R3_UNRESOLVED)
        if status is not inventory.P216ReviewStatus.SOURCE_RISK_REQUIRES_OWNER_DECISION:
            self.assertEqual(receipt.parsed_tracked_python, 0)
            self.assertEqual(receipt.findings, ())

    def test_01_actual_checkout_and_frozen_sources(self):
        self.assert_hold(self.receipt, inventory.P216ReviewStatus.SOURCE_RISK_REQUIRES_OWNER_DECISION)
        self.assertEqual(self.receipt.parsed_tracked_python, len(self.paths))
        for path, wanted in (
            (inventory.KNOWN_DIRECT_EFFECT, "9FFB136A73E4277B966FAE025A3962123433745B6BA8907AB3B8C4137F4A21B3"),
            ("tests/test_p216_service_store_decision_inventory.py", "FF077BB4959A0EB5D33D95397649C772F395FE89143C5A8643589E5CB9B4A1F5"),
        ):
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), wanted)

    def test_02_replacement_negative_properties_and_forged_claims(self):
        # Proposed current replacements for original test02/test06, NOT waivers.
        self.assertFalse(self.receipt.direct_effect_source_reachable)
        finding, = (f for f in self.receipt.findings if f.path == inventory.KNOWN_DIRECT_EFFECT)
        self.assertFalse(finding.wincred_native_adapter)
        self.assertTrue(finding.wincred_presence_only_adapter)
        self.assertTrue(finding.explicit_native_credential_call)
        self.assertFalse(finding.explicit_native_credential_mutation_call)
        self.assertTrue(self.receipt.source_mode_runtime_risk_reachable)
        claims = dict(G0="GO", R3="GO", signed_source=True, wdac=True,
                      owner_waiver=True, user_present=True, all_gates=True)
        self.assertFalse(inventory.proposed_service_store_admission(self.receipt, **claims))
        self.assertFalse(inventory.authorize_cross_principal_user_vault_migration(self.receipt, **claims))
        for field in AUTHORITY_FIELDS:
            with self.assertRaises(ValueError):
                replace(self.receipt, **{field: True})

    def test_03_real_nested_root_cannot_inherit_parent_inventory(self):
        with source_copy(nested=True) as root:
            with self.assertRaises(ValueError):
                inventory._git_tracked_python(root)
            self.assert_hold(inventory.review_proposed_service_store(root, self.paths),
                             inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)

    def test_04_foreign_git_root_and_nonrepository_temp_are_refused(self):
        with source_copy() as root:
            self.assert_hold(inventory.review_proposed_service_store(root, self.paths),
                             inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)
            with patch.object(inventory.subprocess, "run", return_value=reply(str(ROOT).encode() + b"\n")) as run:
                self.assert_hold(inventory.review_proposed_service_store(root, self.paths),
                                 inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)
                self.assertEqual(run.call_count, 1)  # No inventory after foreign top.

    def test_05_invalid_alias_symlink_and_reparse_roots_precede_git(self):
        with source_copy() as root:
            invalid = (Path("relative"), root / "absent", ROOT / "tests" / "..", ROOT / "AGENTS.md", None)
            with patch.object(inventory.subprocess, "run", side_effect=AssertionError("Git must not run")) as run:
                for candidate in invalid:
                    with self.subTest(root=candidate), self.assertRaises(ValueError):
                        inventory._git_tracked_python(candidate)
                with patch.object(Path, "is_symlink", return_value=True):
                    with self.assertRaises(ValueError):
                        inventory._git_tracked_python(root)
                original = Path.lstat
                for reparse in (root, root.parent):
                    def metadata(path, *, target=reparse):
                        meta = original(path)
                        if path == target:
                            return SimpleNamespace(st_mode=meta.st_mode, st_file_attributes=0x400)
                        return meta
                    with patch.object(Path, "lstat", metadata):
                        with self.assertRaises(ValueError):
                            inventory._git_tracked_python(root)
                        self.assert_hold(inventory.review_proposed_service_store(root, self.paths),
                                         inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)
                run.assert_not_called()

    def test_06_malformed_empty_or_aliased_git_top_is_refused(self):
        variants = (b"", b"\xff\n", b"relative\n", b"\n", b"x\x00\n",
                    str(ROOT).encode(), str(ROOT).encode() + b"\nextra\n",
                    str(ROOT / "tests" / "..").encode() + b"\n",
                    str(ROOT).encode() + b"/./\n", b"x" * 32769)
        for raw in variants:
            with self.subTest(raw=raw[:80]), patch.object(inventory.subprocess, "run", return_value=reply(raw)) as run:
                with self.assertRaises(ValueError):
                    inventory._git_tracked_python(ROOT)
                self.assert_hold(inventory.review_proposed_service_store(ROOT, self.paths),
                                 inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)
                self.assertEqual(run.call_count, 2)  # Both stopped at rev-parse.
        if ROOT.drive:  # Windows case/slash spelling is equivalent, not a waiver.
            raw_paths = ("\x00".join(self.paths) + "\x00").encode()
            with patch.object(inventory.subprocess, "run", side_effect=[
                reply(ROOT.as_posix().swapcase().encode() + b"\r\n"), reply(raw_paths),
            ]):
                self.assertEqual(inventory._git_tracked_python(ROOT), self.paths)

    def test_07_git_exit_timeout_stderr_and_bad_inventory_fail_closed(self):
        top = reply(str(ROOT).encode() + b"\n")
        errors = (subprocess.CalledProcessError(1, ["git"]),
                  subprocess.TimeoutExpired(["git"], 30), OSError("offline Git failure"))
        bad = (reply(str(ROOT).encode() + b"\n", b"warning"), reply(b""), reply(b"\xff\x00"),
               reply(b"nayeon/x.py"), reply(b"\x00"),
               reply(b"nayeon/x.py\x00nayeon/x.py\x00"),
               reply(b"x" * (inventory.MAX_TRACKED_PY_FILES * 201 + 1)))
        for stage in (0, 1):
            for failure in (*errors, *bad):
                responses = [failure] if stage == 0 else [top, failure]
                with self.subTest(stage=stage, failure=repr(failure)), patch.object(inventory.subprocess, "run", side_effect=responses):
                    with self.assertRaises(ValueError):
                        inventory._git_tracked_python(ROOT)
                with patch.object(inventory.subprocess, "run", side_effect=responses):
                    self.assert_hold(inventory.review_proposed_service_store(ROOT, self.paths),
                                     inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)

    def test_08_supplied_fake_tracking_is_not_authority(self):
        for paths in (self.paths + ("core/p278_untracked.py",), (), list(self.paths),
                      self.paths + (inventory.KNOWN_DIRECT_EFFECT,)):
            with self.subTest(paths=type(paths).__name__):
                self.assert_hold(inventory.review_proposed_service_store(ROOT, paths),
                                 inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)

    def test_09_malformed_tracked_python_is_not_executed(self):
        with source_copy() as root:
            path = "core/p278_synthetic.py"
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            paths = tuple(p for p in quarantine._FIXED_LEGACY_FILES if p.endswith(".py")) + (path,)
            for source in ("raise AssertionError('never execute')\ndef broken(:\n", "return\n", "\x00"):
                target.write_text(source, encoding="utf8")
                responses = [reply(str(root).encode() + b"\n"), reply(("\x00".join(paths) + "\x00").encode())]
                with patch.object(inventory.subprocess, "run", side_effect=responses):
                    self.assert_hold(inventory.review_proposed_service_store(root, paths),
                                     inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)

    def test_10_missing_unreadable_or_malformed_fixed_source_precedes_git(self):
        with patch.object(inventory.subprocess, "run", side_effect=AssertionError("Git must not run")) as run:
            for relative in quarantine._FIXED_LEGACY_FILES:
                with source_copy() as root:
                    (root / relative).unlink()
                    self.assert_hold(inventory.review_proposed_service_store(root, self.paths),
                                     inventory.P216ReviewStatus.SOURCE_UNPROVEN)
                with source_copy() as root:
                    original = quarantine._source
                    with patch.object(quarantine, "_source", side_effect=lambda r, p: None if p == relative else original(r, p)):
                        self.assert_hold(inventory.review_proposed_service_store(root, self.paths),
                                         inventory.P216ReviewStatus.SOURCE_UNPROVEN)
                if relative.endswith(".py"):
                    with source_copy() as root:
                        (root / relative).write_text("def broken(:\n", encoding="utf8")
                        self.assert_hold(inventory.review_proposed_service_store(root, self.paths),
                                         inventory.P216ReviewStatus.SOURCE_UNPROVEN)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
