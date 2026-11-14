"""P213 actual read-only Windows Authenticode / unsigned candidate tests.

The OS Microsoft-signed PowerShell file is only a calibration reference:
a valid Microsoft signature does not authorise Nayeon service/UI/installer.
The P210 C1 test executable is genuinely unsigned and not installed.
"""
from __future__ import annotations
from dataclasses import FrozenInstanceError
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from nayeon.brain import p213_readonly_windows_signer_observer as probe
from nayeon.brain.p211_high_assurance_package_quarantine import inspect_current_source_tree
from scripts.p212_high_assurance_build_gate import refuse_high_assurance_build

ROOT=Path(__file__).resolve().parents[1]


class P213GenuineWindowsSignerReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P213 must test real hosted Windows, not mocks")
        exe=os.environ.get("P210_NATIVE_EXE","")
        if not exe or not Path(exe).is_file() or Path(exe).suffix.lower()!=".exe":
            raise RuntimeError("P213 original native unsigned test executable absent")
        cls.unsigned=Path(exe)
        cls.microsoft=probe.system_powershell_reference()
        if cls.microsoft is None:
            raise RuntimeError("P213 Microsoft Windows signature reference absent")
        cls.unsigned_result=probe.observe_readonly_windows_signer(cls.unsigned)
        cls.microsoft_result=probe.observe_readonly_windows_signer(cls.microsoft)

    def test_01_all_nayeon_signer_release_and_code_policy_pins_absent(self):
        self.assertTrue(probe.source_pins_unissued())

    def test_02_actual_windows_os_reference_returns_definitive_native_policy(self):
        a=self.microsoft_result
        self.assertIn(a.status,(
            probe.P213SignatureStatus.OS_POLICY_ACCEPTED_UNPINNED,
            probe.P213SignatureStatus.OS_POLICY_REJECTED,
        ))  # cache-only revocation can reject a real Microsoft-signed file
        self.assertRegex(a.file_sha256,r"^[0-9a-f]{64}$")
        self.assertNotEqual(a.status,probe.P213SignatureStatus.UNKNOWN)
        self.assertIsNone(a.signer_cert_sha256) # P116 exposes policy status, no signer pin

    def test_03_actual_compiled_p210_native_executable_is_unsigned(self):
        a=self.unsigned_result
        self.assertEqual(a.status,probe.P213SignatureStatus.OS_POLICY_REJECTED)
        self.assertIsNone(a.signer_cert_sha256)

    def test_04_Microsoft_valid_signature_does_not_enroll_nayeon(self):
        self.assertFalse(probe.is_approved_nayeon_service(self.microsoft_result))
        self.assertFalse(self.microsoft_result.approved_publisher_proven)
        self.assertFalse(self.microsoft_result.release_eligible)

    def test_05_actual_unsigned_C1_candidate_cannot_approve(self):
        self.assertFalse(probe.is_approved_nayeon_service(self.unsigned_result))
        self.assertFalse(self.unsigned_result.real_key_admission)

    def test_06_OS_file_identity_and_hash_observation_is_only_readonly(self):
        a=self.microsoft_result
        self.assertTrue(a.stable_stat_and_bytes_observed)
        self.assertTrue(a.platform_windows)
        self.assertEqual(a.file_sha256,hashlib.sha256(
            self.microsoft.read_bytes()).hexdigest())

    def test_07_original_test_unsigned_file_SHA_and_metadata_stable(self):
        a=self.unsigned_result
        self.assertTrue(a.stable_stat_and_bytes_observed)
        self.assertEqual(a.file_sha256,hashlib.sha256(
            self.unsigned.read_bytes()).hexdigest())

    def test_08_observation_is_not_kernel_loaded_image_attestation(self):
        for a in (self.microsoft_result,self.unsigned_result):
            self.assertFalse(a.kernel_code_integrity_load_enforced)
            self.assertFalse(a.elevated_service_identity_proven)
            self.assertFalse(a.protected_installer_accepted)

    def test_09_nonexistent_path_is_unknown_without_signer_query(self):
        with tempfile.TemporaryDirectory(prefix="p213-missing-") as t:
            a=probe.observe_readonly_windows_signer(Path(t)/"notpresent.exe")
        self.assertEqual(a.status,probe.P213SignatureStatus.UNKNOWN)
        self.assertFalse(a.stable_stat_and_bytes_observed)

    def test_10_relative_path_refused(self):
        a=probe.observe_readonly_windows_signer(Path("powershell.exe"))
        self.assertEqual(a.status,probe.P213SignatureStatus.UNKNOWN)

    def test_11_directory_and_zero_length_file_refused(self):
        with tempfile.TemporaryDirectory(prefix="p213-bad-") as t:
            folder=Path(t)
            empty=folder/"empty.exe"
            empty.write_bytes(b"")
            self.assertEqual(probe.observe_readonly_windows_signer(
                folder).status,probe.P213SignatureStatus.UNKNOWN)
            self.assertEqual(probe.observe_readonly_windows_signer(
                empty).status,probe.P213SignatureStatus.UNKNOWN)

    def test_12_tampered_bytes_have_different_SHA_on_new_observation(self):
        # No real signed image or production source is edited, only tiny
        # unprivileged disposable test bytes.
        with tempfile.TemporaryDirectory(prefix="p213-tamper-") as t:
            path=Path(t)/"test.exe"
            path.write_bytes(b"MZ"+b"untrusted-nonPE" * 90)
            one=probe._file_evidence(path)
            self.assertIsNotNone(one)
            path.write_bytes(b"MZ"+b"changed-untrusted" * 90)
            two=probe._file_evidence(path)
            self.assertIsNotNone(two)
            self.assertNotEqual(one[-1],two[-1])

    def test_13_fake_signer_environment_cannot_upgrade_existing_pins(self):
        with mock.patch.dict(os.environ, {
            "NAYEON_SERVICE_SHA256": "a"*64,
            "NAYEON_P213_SIGNATURE_GO":"true",
            "NAYEON_WDAC_GO":"approved",
        }):
            self.assertTrue(probe.source_pins_unissued())
            self.assertFalse(probe.is_approved_nayeon_service(self.microsoft_result))

    def test_14_forged_positive_observation_cannot_be_constructed(self):
        with self.assertRaises(ValueError):
            probe.P213WindowsSignatureObservation(
                probe.P213SignatureStatus.VALID,
                "a"*64,"b"*64,True,True,release_eligible=True)

    def test_15_observation_receipt_cannot_be_modified_after_creation(self):
        with self.assertRaises(FrozenInstanceError):
            self.microsoft_result.release_eligible=True

    def test_16_actual_P132_legacy_effect_remains_source_reachable(self):
        risk=inspect_current_source_tree(ROOT)
        self.assertTrue(risk.high_assurance_legacy_risk_present)
        self.assertTrue(risk.frozen_companion_pins_absent)
        self.assertTrue(risk.native_c1_service_denial_only)

    def test_17_P212_production_builder_still_refuses_actual_source(self):
        receipt=refuse_high_assurance_build(
            ROOT,["nayeon/secrets/windows_credential.py"])
        self.assertFalse(receipt.release_eligible)
        self.assertFalse(receipt.product_bundle_written)

    def test_18_signature_inspection_source_contains_no_mutator(self):
        import ast
        source=(ROOT/"nayeon/brain/p213_readonly_windows_signer_observer.py").read_text("utf8")
        tree=ast.parse(source)
        names={n.func.attr for n in ast.walk(tree)
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(names.intersection({
            "CredWriteW","CredDeleteW","CreateService","StartService",
            "SetNamedSecurityInfo","SetACL","InstallService","put","delete"
        }))
        self.assertFalse(any(
            isinstance(n,ast.ImportFrom)
            and n.module=="nayeon.secrets.windows_credential"
            for n in ast.walk(tree)))

    def test_19_unsigned_C1_candidate_not_renamed_into_signed_release(self):
        self.assertIn("p210_synthetic_python_native.exe",
                      self.unsigned.name)
        self.assertFalse(self.unsigned_result.approved_publisher_proven)

    def test_20_no_r0_r4_or_prod_authority_from_any_observation(self):
        for a in (self.unsigned_result,self.microsoft_result):
            self.assertFalse(a.release_eligible)
            self.assertFalse(a.real_key_admission)
            self.assertFalse(a.kernel_code_integrity_load_enforced)
            self.assertFalse(a.approved_publisher_proven)


if __name__=="__main__":
    unittest.main()
