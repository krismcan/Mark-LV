"""P212 20 executable-build refusal and metadata-only evidence negatives.

No real keys, WinCred, signer, installer, native service, provider or unsafe
unattended executable. All file fixtures are harmless disposable text only.
"""
from __future__ import annotations
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError
from pathlib import Path
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from nayeon.brain.p211_high_assurance_package_quarantine import (
    P211Refusal, inspect_current_source_tree, review_high_assurance_package_plan,
)
from scripts.p212_high_assurance_build_gate import (
    P212BuildRefusal, refuse_high_assurance_build, emit_nonexecutable_review_only,
    main, _REVIEW_BODY, _REVIEW_NAME, _FIXED_UNSAFE_BUNDLE,
    _ci_review_dir,
)

ROOT=Path(__file__).resolve().parents[1]


class P212MandatoryBuildGateTests(unittest.TestCase):
    def test_01_original_python_backend_must_be_denied_before_build(self):
        r=refuse_high_assurance_build(ROOT,_FIXED_UNSAFE_BUNDLE)
        self.assertEqual(r.reason,P211Refusal.LEGACY_EFFECT_PATH)
        self.assertFalse(r.release_eligible)
        self.assertFalse(r.product_bundle_written)

    def test_02_empty_benign_plan_still_cannot_build_product(self):
        r=refuse_high_assurance_build(ROOT,["P211_QUARANTINE_README.txt"])
        self.assertEqual(r.reason,P211Refusal.ABSENT_RELEASE_AUTHORITY)
        self.assertFalse(r.release_eligible)

    def test_03_unknown_signed_executable_name_not_allowlisted(self):
        r=refuse_high_assurance_build(ROOT,["ApprovedNayeonDesktop.exe"])
        self.assertEqual(r.reason,P211Refusal.LEGACY_EFFECT_PATH)

    def test_04_alternate_executable_and_script_payloads_refused(self):
        for s in ["scripts/setup.py","nayeon/brain/injection.py",
                  "NativeWinCred.dll","ByokSetup.msix","content.whl"]:
            with self.subTest(s=s):
                self.assertNotEqual(
                    refuse_high_assurance_build(ROOT,[s]).reason,
                    P211Refusal.ABSENT_RELEASE_AUTHORITY)

    def test_05_aliases_and_windows_ads_fail_before_bundle(self):
        for s in ["C:relative.exe","readme.txt:evil",
                  "../NayeonDesktop.exe","nayeon\\credential.py"]:
            with self.subTest(s=s):
                self.assertEqual(refuse_high_assurance_build(ROOT,[s]).reason,
                                 P211Refusal.UNTRUSTED_PATH)

    def test_06_empty_or_generator_manifest_does_not_bypass(self):
        self.assertEqual(refuse_high_assurance_build(ROOT,[]).reason,
                         P211Refusal.INVALID_PLAN)
        self.assertEqual(refuse_high_assurance_build(
            ROOT,(x for x in _FIXED_UNSAFE_BUNDLE)).reason,
            P211Refusal.INVALID_PLAN)

    def test_07_source_missing_is_NOT_accepted_as_effect_closure(self):
        with tempfile.TemporaryDirectory(prefix="p212-missing-") as t:
            r=refuse_high_assurance_build(Path(t),["P211_QUARANTINE_README.txt"])
            self.assertEqual(r.reason,P211Refusal.SOURCE_UNPROVEN)
            self.assertFalse(r.release_eligible)

    def test_08_no_separate_signer_flag_can_issue_build_authority(self):
        r=review_high_assurance_package_plan(
            ROOT,["P211_QUARANTINE_README.txt"],
            claimed_signer="self-approved",
            claimed_policy_approval={"G0":True,"R0":True,"P0":True})
        self.assertEqual(r.reason,P211Refusal.ABSENT_RELEASE_AUTHORITY)
        self.assertFalse(r.release_eligible)

    def test_09_denial_receipt_cannot_be_mutated(self):
        r=refuse_high_assurance_build(ROOT,_FIXED_UNSAFE_BUNDLE)
        with self.assertRaises(FrozenInstanceError):
            r.release_eligible=True

    def test_10_no_forged_positive_build_receipt_constructor(self):
        with self.assertRaises(ValueError):
            P212BuildRefusal(P211Refusal.ABSENT_RELEASE_AUTHORITY,1,
                             product_bundle_written=True)

    def test_11_actual_CLI_high_assurance_attempt_returns_nonzero(self):
        p=subprocess.run([sys.executable,"-B","-m",
            "scripts.p212_high_assurance_build_gate",
            "--attempt-ha-release"],cwd=ROOT,stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=False)
        self.assertEqual(p.returncode,41)
        self.assertEqual(p.stderr,b"")
        s=p.stdout.decode("utf8")
        self.assertIn("P212_BUILD=DENIED_LEGACY_EFFECT_PATH",s)
        self.assertIn("P212_OUTPUT_PRODUCT_COUNT=0",s)
        self.assertIn("P212_REAL_KEY=NO_GO|PRODUCTION=HOLD",s)

    def test_12_unknown_CLI_command_returns_nonzero(self):
        with io.StringIO() as capture, redirect_stdout(capture):
            self.assertEqual(main(["--enable-prod"]),64)
            self.assertIn("DENIED_INVALID_COMMAND",capture.getvalue())

    def test_13_extra_approval_CLI_flags_cannot_pass(self):
        with io.StringIO() as capture, redirect_stdout(capture):
            self.assertEqual(main(["--attempt-ha-release","--approved"]),64)
            self.assertIn("DENIED",capture.getvalue())

    def test_14_invalid_CI_identity_refuses_review_receipt(self):
        with mock.patch.dict(os.environ,{"GITHUB_ACTIONS":"false"},clear=False):
            self.assertIsNone(_ci_review_dir())

    def test_15_review_note_contains_no_binary_and_explicit_NO_GO(self):
        with tempfile.TemporaryDirectory(prefix="p212-note-") as t:
            folder=Path(t)
            item=emit_nonexecutable_review_only(ROOT,folder)
            self.assertEqual(item,folder/_REVIEW_NAME)
            assert item is not None
            self.assertEqual(item.read_text(encoding="utf8"),_REVIEW_BODY)
            self.assertIn("HIGH_ASSURANCE_RELEASE=NO_GO",_REVIEW_BODY)
            self.assertIn("ARTIFACT_CLASS=NONEXECUTABLE_REVIEW_TEXT_ONLY",_REVIEW_BODY)
            self.assertEqual([p.name for p in folder.iterdir()],[_REVIEW_NAME])

    def test_16_second_review_emit_cannot_overwrite_prior_receipt(self):
        with tempfile.TemporaryDirectory(prefix="p212-duplicate-") as t:
            folder=Path(t)
            first=emit_nonexecutable_review_only(ROOT,folder)
            self.assertIsNotNone(first)
            sentinel=first.read_bytes()
            self.assertIsNone(emit_nonexecutable_review_only(ROOT,folder))
            self.assertEqual(first.read_bytes(),sentinel)

    def test_17_nonexistent_review_destination_is_never_created(self):
        with tempfile.TemporaryDirectory(prefix="p212-no-dir-") as t:
            folder=Path(t)/"missing"
            self.assertIsNone(emit_nonexecutable_review_only(ROOT,folder))
            self.assertFalse(folder.exists())

    def test_18_source_missing_never_emits_review_receipt(self):
        with tempfile.TemporaryDirectory(prefix="p212-missing-root-") as source:
            with tempfile.TemporaryDirectory(prefix="p212-output-") as target:
                self.assertIsNone(emit_nonexecutable_review_only(
                    Path(source),Path(target)))
                self.assertEqual(list(Path(target).iterdir()),[])

    def test_19_original_p132_direct_WinCred_remains_unmodified(self):
        s=inspect_current_source_tree(ROOT)
        self.assertTrue(s.high_assurance_legacy_risk_present)
        self.assertTrue(s.frozen_companion_pins_absent)
        self.assertTrue(s.native_c1_service_denial_only)

    def test_20_deny_only_gate_cannot_call_installer_or_WinCred(self):
        src=(ROOT/"scripts/p212_high_assurance_build_gate.py").read_text("utf8")
        import ast
        tree=ast.parse(src)
        mods={n.module.split(".")[0] for n in ast.walk(tree)
              if isinstance(n,ast.ImportFrom) and n.module}
        mods.update(a.name.split(".")[0] for n in ast.walk(tree)
                    if isinstance(n,ast.Import) for a in n.names)
        self.assertFalse(mods.intersection({
            "ctypes","subprocess","winreg","win32cred","PyInstaller",
            "nayeon.secrets.windows_credential"}))
        self.assertNotIn("CredWriteW(",src)
        self.assertNotIn("CredDeleteW(",src)
        self.assertNotIn("ServiceBase.Run(",src)


if __name__=="__main__":
    unittest.main()
