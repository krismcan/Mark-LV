"""P211 security negatives for fail-closed high-assurance bundle intake.

Tests do not load WinCred, execute any installer, sign binaries or create
executable bundles. Original P132 user-scope code remains unchanged.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from nayeon.brain.p211_high_assurance_package_quarantine import (
    P211PackageRefusalReceipt,P211Refusal,inspect_current_source_tree,
    review_high_assurance_package_plan,
)

ROOT=Path(__file__).resolve().parents[1]
BENIGN="P211_QUARANTINE_README.txt"
BACKEND="nayeon/secrets/windows_credential.py"
USER_SCOPE="nayeon/brain/local_byok_user_scope.py"
LAUNCH="nayeon/desktop_alpha/local_byok_launch_bridge.py"
COMPANION="nayeon/desktop_alpha/frozen_signed_byok_companion.py"


def decision(names,root=ROOT,**kwargs):
    return review_high_assurance_package_plan(root,names,**kwargs)


class P211PackageIsolationTests(unittest.TestCase):
    def test_01_original_source_readable_not_signed(self):
        found=inspect_current_source_tree(ROOT)
        self.assertTrue(found.exact_legacy_source_readable)
        self.assertTrue(found.frozen_companion_pins_absent)
        self.assertTrue(found.native_c1_service_denial_only)

    def test_02_actual_python_wincred_effect_proven_source_reachable(self):
        found=inspect_current_source_tree(ROOT)
        self.assertTrue(found.python_direct_native_credential_effect)
        self.assertTrue(found.p132_product_constructor_and_effect)
        self.assertTrue(found.p133_source_mode_launcher)
        self.assertTrue(found.high_assurance_legacy_risk_present)

    def test_03_real_repository_code_plan_refused(self):
        receipt=decision([BACKEND,USER_SCOPE,LAUNCH])
        self.assertEqual(receipt.reason,P211Refusal.LEGACY_EFFECT_PATH)
        self.assertFalse(receipt.release_eligible)

    def test_04_python_module_in_untrusted_bundle_refused(self):
        receipt=decision(["nayeon/brain/supposed_safe.py"])
        self.assertEqual(receipt.reason,P211Refusal.LEGACY_EFFECT_PATH)

    def test_05_source_mode_byok_child_module_refused(self):
        self.assertEqual(decision(["nayeon/desktop_alpha/local_byok_window.py"]).reason,
                         P211Refusal.LEGACY_EFFECT_PATH)

    def test_06_unsigned_frozen_helper_payload_refused(self):
        self.assertEqual(decision(["NayeonLocalByokOffline.exe"]).reason,
                         P211Refusal.LEGACY_EFFECT_PATH)

    def test_07_hidden_compiled_extension_refused(self):
        for ext in (".pyc",".pyd",".dll",".msi",".msix",".whl",".zip",".ps1"):
            with self.subTest(ext=ext):
                self.assertEqual(decision(["unexpected"+ext]).reason,
                                 P211Refusal.LEGACY_EFFECT_PATH)

    def test_08_unapproved_readme_does_not_become_runtime_payload(self):
        self.assertEqual(decision(["README.md"]).reason,
                         P211Refusal.UNRECOGNISED_PAYLOAD)

    def test_09_only_safe_quarantine_metadata_still_NO_GO(self):
        receipt=decision([BENIGN])
        self.assertEqual(receipt.reason,P211Refusal.ABSENT_RELEASE_AUTHORITY)
        self.assertFalse(receipt.release_eligible)
        self.assertFalse(receipt.credential_mutation_authorised)
        self.assertFalse(receipt.signed_installer_authorised)
        self.assertFalse(receipt.trusted_runtime_isolation_proven)
        self.assertFalse(receipt.real_key_pilot_authorised)

    def test_10_forged_publisher_and_policy_approval_cannot_grant(self):
        receipt=decision([BENIGN],
                         claimed_signer="reviewer-approved-certificate",
                         claimed_policy_approval={"WDAC":True,"release":"GO"})
        self.assertEqual(receipt.reason,P211Refusal.ABSENT_RELEASE_AUTHORITY)
        self.assertFalse(receipt.release_eligible)

    def test_11_casefold_alias_collision_refused(self):
        self.assertEqual(decision([BENIGN,BENIGN.lower()]).reason,
                         P211Refusal.UNTRUSTED_PATH)

    def test_12_dotdot_traversal_and_dotted_component_refused(self):
        for value in ("../P211_QUARANTINE_README.txt",
                      "safe/../P211_QUARANTINE_README.txt",
                      "./P211_QUARANTINE_README.txt","a./x"):
            with self.subTest(path=value):
                self.assertEqual(decision([value]).reason,P211Refusal.UNTRUSTED_PATH)

    def test_13_windows_ADS_and_drive_relative_paths_refused(self):
        for value in ("C:payload","C:/NayeonDesktop.exe","file.txt:hidden",
                      "nayeon/secret.py:evil"):
            with self.subTest(path=value):
                self.assertEqual(decision([value]).reason,P211Refusal.UNTRUSTED_PATH)

    def test_14_backslash_unc_root_and_duplicate_separator_refused(self):
        for value in ("nayeon\\secrets\\windows_credential.py",
                      "\\\\server\\share\\file.py","/absolute/file",
                      "safe//nested"):
            with self.subTest(path=value):
                self.assertEqual(decision([value]).reason,P211Refusal.UNTRUSTED_PATH)

    def test_15_trailing_space_dot_and_control_character_refused(self):
        for value in ("name ","name."," leading","safe/\x00hack","a/\x7f"):
            with self.subTest():
                self.assertEqual(decision([value]).reason,P211Refusal.UNTRUSTED_PATH)

    def test_16_oversized_malformed_or_iterable_plan_refused(self):
        self.assertEqual(decision([]).reason,P211Refusal.INVALID_PLAN)
        self.assertEqual(decision([BENIGN]*129).reason,P211Refusal.INVALID_PLAN)
        self.assertEqual(decision((i for i in [BENIGN])).reason,
                         P211Refusal.INVALID_PLAN)
        self.assertEqual(decision([None]).reason,P211Refusal.UNTRUSTED_PATH)

    def test_17_missing_source_is_UNPROVEN_never_exclusion_pass(self):
        with TemporaryDirectory(prefix="p211-absent-") as t:
            r=decision([BENIGN],root=Path(t))
            self.assertEqual(r.reason,P211Refusal.SOURCE_UNPROVEN)
            self.assertFalse(r.release_eligible)

    def test_18_even_tampered_sanitized_P132_tree_cannot_mint_GO(self):
        # Synthetic isolated file copies; DO NOT edit the original product.
        with TemporaryDirectory(prefix="p211-sterile-") as t:
            dest=Path(t)
            files=(BACKEND,USER_SCOPE,LAUNCH,COMPANION,
                   "nayeon/desktop_alpha/local_byok_window.py",
                   "nayeon/desktop_alpha/application.py",
                   "nayeon/desktop_alpha/workspace_window.py",
                   "native_c1_candidate/CustodyService.cs")
            for p in files:
                target=dest/p
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/p,target)
            user=dest/USER_SCOPE
            original=user.read_text(encoding="utf8")
            self.assertIn("WindowsCredentialBackend()",original)
            user.write_text(original.replace(
                "WindowsCredentialBackend()","None",1),encoding="utf8")
            witness=inspect_current_source_tree(dest)
            self.assertTrue(witness.exact_legacy_source_readable)
            self.assertFalse(witness.p132_product_constructor_and_effect)
            # The policy does not equate missing one known route with verified
            # closure of all alternate code/WinCred paths.
            receipt=decision(["nayeon/brain/new_safe.py"],root=dest)
            self.assertEqual(receipt.reason,P211Refusal.UNRECOGNISED_PAYLOAD)
            self.assertFalse(receipt.release_eligible)

    def test_19_review_receipt_is_frozen_and_cannot_be_upgraded(self):
        receipt=decision([BENIGN])
        with self.assertRaises(FrozenInstanceError):
            receipt.release_eligible=True

    def test_20_constructor_rejects_fake_positive_authority(self):
        with self.assertRaises(ValueError):
            P211PackageRefusalReceipt(
                reason=P211Refusal.ABSENT_RELEASE_AUTHORITY,
                manifest_entries=1,source_witness=None,
                release_eligible=True)

    def test_21_mixed_good_and_bad_payload_is_not_whitelisted(self):
        receipt=decision([BENIGN,"any.dll"])
        self.assertEqual(receipt.reason,P211Refusal.LEGACY_EFFECT_PATH)
        self.assertEqual(receipt.manifest_entries,2)

    def test_22_actor_cannot_become_native_security_control_by_import(self):
        # Inspect executable AST, not quoted detection strings used by
        # the source scanner (which intentionally mentions ServiceBase.Run).
        import ast
        source=(ROOT/"nayeon/brain/p211_high_assurance_package_quarantine.py").read_text("utf8")
        tree=ast.parse(source)
        imported={a.name.split(".")[0] for n in ast.walk(tree)
                  if isinstance(n,ast.Import) for a in n.names}
        imported.update(n.module.split(".")[0] for n in ast.walk(tree)
                        if isinstance(n,ast.ImportFrom) and n.module)
        self.assertFalse(imported.intersection({"ctypes","subprocess",
                                                 "winreg","win32cred"}))
        call_names={n.func.attr for n in ast.walk(tree)
                    if isinstance(n,ast.Call)
                    and isinstance(n.func,ast.Attribute)}
        self.assertFalse(call_names.intersection(
            {"WinDLL","CredWriteW","CredDeleteW","Run","Popen"}))


if __name__=="__main__":
    unittest.main()
