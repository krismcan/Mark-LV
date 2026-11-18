"""P277 offline source inventory tests; never import a credential backend.

The actual checkout is read only. Synthetic trees contain text copies and
use an explicitly mocked Git inventory, never a staged synthetic repository.
AST payloads are parsed/compiled in memory, never imported or executed.
Source findings prove neither OS isolation nor absence of alternate callers.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from nayeon.brain import p211_high_assurance_package_quarantine as quarantine
from nayeon.brain import p216_service_store_decision as inventory


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC = "core/p277_synthetic_source.py"
AUTHORITY_FIELDS = (
    "release_eligible", "real_key_admissible",
    "protected_service_store_installed", "legacy_route_isolated_by_OS",
    "trusted_user_presence_proven", "machine_code_integrity_approved",
    "user_scope_key_migration_authorized",
)


def actual_tracked_python():
    result = subprocess.run(
        ["git", "ls-files", "--full-name", "-z", "--", "nayeon", "core"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=30, check=True,
    )
    if result.stderr:
        raise AssertionError("Actual Git source inventory must be proven")
    return tuple(path for path in result.stdout.decode("utf-8").split("\x00")
                 if path.endswith(".py"))


@contextmanager
def source_copy():
    with TemporaryDirectory(prefix="p277-source-only-") as directory:
        root = Path(directory)
        for relative in quarantine._FIXED_LEGACY_FILES:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        yield root


def synthetic_inventory(root, source):
    target = root / SYNTHETIC
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return tuple(path for path in quarantine._FIXED_LEGACY_FILES
                 if path.endswith(".py")) + (SYNTHETIC,)


class CurrentStoreSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = actual_tracked_python()
        cls.receipt = inventory.review_proposed_service_store(ROOT, cls.paths)

    def assert_denied(self, receipt):
        for field in AUTHORITY_FIELDS:
            self.assertIs(getattr(receipt, field), False, field)

    def test_01_actual_git_tracked_sources_are_completely_parsed(self):
        self.assertEqual(self.paths, inventory._git_tracked_python(ROOT))
        self.assertGreater(len(self.paths), 10)
        self.assertEqual(len(self.paths), len(set(self.paths)))
        self.assertTrue({inventory.KNOWN_DIRECT_EFFECT, inventory.KNOWN_CONSUMER,
                         inventory.KNOWN_LAUNCHER}.issubset(self.paths))
        self.assertIs(self.receipt.status,
                      inventory.P216ReviewStatus.SOURCE_RISK_REQUIRES_OWNER_DECISION)
        self.assertEqual(self.receipt.parsed_tracked_python, len(self.paths))
        self.assertTrue({finding.path for finding in self.receipt.findings}
                        .issubset(self.paths))
        consumers = [finding for finding in self.receipt.findings
                     if finding.path == inventory.KNOWN_CONSUMER]
        self.assertEqual(len(consumers), 1)
        self.assertTrue(consumers[0].wincred_backend_import)

    def test_02_current_adapter_is_presence_only_without_native_mutation(self):
        findings = [finding for finding in self.receipt.findings
                    if finding.path == inventory.KNOWN_DIRECT_EFFECT]
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertTrue(finding.wincred_presence_only_adapter)
        self.assertTrue(finding.explicit_native_credential_call)  # CredReadW
        self.assertFalse(finding.explicit_native_credential_mutation_call)
        self.assertFalse(finding.wincred_native_adapter)  # Retired write/delete
        with self.assertRaises(FrozenInstanceError):
            finding.explicit_native_credential_mutation_call = True

    def test_03_source_mode_risk_survives_native_effect_retirement(self):
        witness = quarantine.inspect_current_source_tree(ROOT)
        self.assertTrue(witness.exact_legacy_source_readable)
        self.assertFalse(witness.high_assurance_legacy_risk_present)
        self.assertFalse(self.receipt.direct_effect_source_reachable)
        self.assertTrue(self.receipt.local_user_controller_reachable)
        self.assertTrue(self.receipt.source_launcher_reachable)
        self.assertTrue(self.receipt.original_native_C1_host_denial_only)
        self.assertTrue(self.receipt.source_mode_runtime_risk_reachable)
        self.assertEqual(self.receipt.source_mode_runtime_risk_reachable,
                         witness.source_mode_runtime_risk_present)
        self.assert_denied(self.receipt)

    def test_04_immutable_receipt_cannot_construct_any_positive_authority(self):
        self.assert_denied(self.receipt)
        for field in AUTHORITY_FIELDS:
            with self.subTest(field=field):
                with self.assertRaises(FrozenInstanceError):
                    setattr(self.receipt, field, True)
                with self.assertRaises(ValueError):
                    replace(self.receipt, **{field: True})
        with self.assertRaises(FrozenInstanceError):
            self.receipt.outstanding_external_decisions = ()
        self.assertIsInstance(self.receipt.findings, tuple)
        self.assertIsInstance(self.receipt.outstanding_external_decisions, tuple)

    def test_05_external_approvals_remain_absent_and_claims_are_deny_only(self):
        self.assertEqual(self.receipt.outstanding_external_decisions,
                         inventory.G0_R3_UNRESOLVED)
        self.assertEqual(len(self.receipt.outstanding_external_decisions), 13)
        for missing in (
            "G0:independent_windows_native_security_review",
            "R3:service_owned_separate_target_and_secret_isolation",
            "P0:legacy_user_scope_P132_P133_effect_elimination_or_OS_isolation",
            "P2:three_unfiltered_native_Windows_product_regressions",
        ):
            self.assertIn(missing, self.receipt.outstanding_external_decisions)
        claims = dict(G0="GO", R3="GO", signed_installer=True, wdac=True,
                      user_confirmed=True, admin_approved=True, all_gates=True)
        self.assertIs(inventory.proposed_service_store_admission(
            self.receipt, **claims), False)
        self.assertIs(inventory.authorize_cross_principal_user_vault_migration(
            self.receipt, **claims), False)
        self.assertTrue(quarantine.inspect_current_source_tree(ROOT)
                        .frozen_companion_pins_absent)
        self.assert_denied(self.receipt)

    def test_06_malformed_tracked_python_is_rejected_without_partial_findings(self):
        for source in ("def broken(:\n", "\x00", "return\n"):
            with self.subTest(source=repr(source)), source_copy() as root:
                paths = synthetic_inventory(root, source)
                with patch.object(inventory, "_git_tracked_python",
                                  return_value=paths) as tracked:
                    receipt = inventory.review_proposed_service_store(root, paths)
                tracked.assert_called_once_with(root)
                self.assertIs(receipt.status,
                              inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)
                self.assertEqual(receipt.parsed_tracked_python, 0)
                self.assertEqual(receipt.findings, ())
                self.assert_denied(receipt)

    def test_07_untrusted_paths_are_refused_even_in_claimed_git_inventory(self):
        invalid = (
            "../outside.py", "nayeon/../outside.py", "/nayeon/source.py",
            "C:/nayeon/source.py", "nayeon/source.py:stream.py",
            "nayeon\\source.py", "nayeon//source.py", "nayeon/./source.py",
            "nayeon/bad./source.py", "nayeon/bad /source.py",
            "tests/source.py", "nayeon/" + "x" * 201 + ".py",
        )
        for path in invalid:
            with self.subTest(path=path):
                self.assertIsNone(inventory._safe_tracked_path(ROOT, path))
                # Matching a hostile Git reply cannot bypass path validation.
                paths = self.paths + (path,)
                with patch.object(inventory, "_git_tracked_python",
                                  return_value=paths):
                    receipt = inventory.review_proposed_service_store(ROOT, paths)
                self.assertIs(receipt.status,
                              inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)
                self.assertEqual(receipt.findings, ())
                self.assert_denied(receipt)

    def test_08_supplied_inventory_cannot_replace_actual_git_tracking(self):
        # No mocked Git here: a plausible extra path is still untracked.
        invalid = (
            (), list(self.paths),
            tuple(path for path in self.paths
                  if path != inventory.KNOWN_DIRECT_EFFECT),
            self.paths + (SYNTHETIC,),
            self.paths + (inventory.KNOWN_DIRECT_EFFECT,),
            self.paths + (inventory.KNOWN_DIRECT_EFFECT.upper(),),
        )
        for paths in invalid:
            with self.subTest(kind=type(paths).__name__, count=len(paths)):
                receipt = inventory.review_proposed_service_store(ROOT, paths)
                self.assertIs(receipt.status,
                              inventory.P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)
                self.assertEqual(receipt.parsed_tracked_python, 0)
                self.assertEqual(receipt.findings, ())
                self.assert_denied(receipt)

    def test_09_synthetic_ast_mutation_aliases_are_detected_without_execution(self):
        payloads = (
            "CredWriteW()\n",
            "native.CredDeleteW()\n",
            "from p277_nonexistent_native import CredWriteW as effect\neffect()\n",
            "effect = native.CredDeleteW\nsecond = effect\nsecond()\n",
            "effect: object = native.CredWriteW\neffect()\n",
            "second = first\nfirst = native.CredDeleteW\nsecond()\n",
        )
        for payload in payloads:
            with self.subTest(payload=payload), source_copy() as root:
                # Successful inspection proves this top-level tripwire and
                # the nonexistent import/native calls were never executed.
                source = "raise AssertionError('P277 source executed')\n" + payload
                paths = synthetic_inventory(root, source)
                with patch.object(inventory, "_git_tracked_python", return_value=paths):
                    receipt = inventory.review_proposed_service_store(root, paths)
                self.assertIs(receipt.status,
                              inventory.P216ReviewStatus.SOURCE_RISK_REQUIRES_OWNER_DECISION)
                self.assertEqual(receipt.parsed_tracked_python, len(paths))
                findings = [finding for finding in receipt.findings
                            if finding.path == SYNTHETIC]
                self.assertEqual(len(findings), 1)
                self.assertTrue(findings[0].explicit_native_credential_call)
                self.assertTrue(findings[0].explicit_native_credential_mutation_call)
                self.assertFalse(findings[0].wincred_presence_only_adapter)
                self.assert_denied(receipt)
        read = inventory._finding(SYNTHETIC, "read = native.CredReadW\nread()\n")
        self.assertTrue(read.explicit_native_credential_call)
        self.assertFalse(read.explicit_native_credential_mutation_call)
        text = inventory._finding(SYNTHETIC, '"CredWriteW()"\n# CredDeleteW()\n')
        self.assertFalse(text.explicit_native_credential_call)
        self.assertFalse(text.explicit_native_credential_mutation_call)

    def test_10_missing_fixed_source_precedes_any_tracked_inventory(self):
        for relative in quarantine._FIXED_LEGACY_FILES:
            with self.subTest(missing=relative), source_copy() as root:
                (root / relative).unlink()
                with patch.object(inventory, "_git_tracked_python",
                                  side_effect=AssertionError("Git must not run")) as tracked:
                    for paths in (self.paths, ()):
                        receipt = inventory.review_proposed_service_store(root, paths)
                        self.assertIs(receipt.status,
                                      inventory.P216ReviewStatus.SOURCE_UNPROVEN)
                        self.assertEqual(receipt.parsed_tracked_python, 0)
                        self.assertEqual(receipt.findings, ())
                        self.assertEqual(receipt.outstanding_external_decisions,
                                         inventory.G0_R3_UNRESOLVED)
                        self.assert_denied(receipt)
                tracked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
