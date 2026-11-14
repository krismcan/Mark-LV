"""P220 no-secret actual ZIP inventory test: source/package exclusion != OS approval."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import hashlib
import tempfile
import unittest
import zipfile

from nayeon.brain.p220_artifact_effect_closure import (
    P220InventoryDisposition, inspect_bounded_zip,
    approve_high_assurance_release,
)

ROOT = Path(__file__).resolve().parents[1]


class P220ActualArchiveClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p220-no-secret-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "candidate.zip"

    def write(self, files):
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for name, content in files:
                bundle.writestr(name, content)
        return inspect_bounded_zip(self.path)

    def test_01_actual_original_P132_WinCred_source_is_rejected_as_a_shipped_member(self):
        source = (ROOT / "nayeon/secrets/windows_credential.py").read_bytes()
        self.assertIn(b"CredWriteW", source)
        result = self.write([("nayeon/secrets/windows_credential.py", source)])
        self.assertEqual(result.disposition, P220InventoryDisposition.LEGACY_EFFECT_PRESENT)
        self.assertEqual(result.legacy_members, ("nayeon/secrets/windows_credential.py",))
        self.assertEqual(result.member_count, 1)
        self.assertFalse(result.production_release_allowed)

    def test_02_real_original_P132_controller_cannot_be_hidden_by_app_prefix(self):
        source = (ROOT / "nayeon/brain/local_byok_user_scope.py").read_bytes()
        self.assertIn(b"self._backend.put", source)
        result = self.write([("_internal/nayeon/brain/local_byok_user_scope.py", source)])
        self.assertEqual(result.disposition, P220InventoryDisposition.LEGACY_EFFECT_PRESENT)

    def test_03_p133_launcher_python_bytecode_name_is_detected(self):
        result = self.write([("vendor/nayeon/desktop_alpha/local_byok_launch_bridge.cpython-312.pyc", b"fake no-op bytecode placeholder")])
        self.assertEqual(result.disposition, P220InventoryDisposition.LEGACY_EFFECT_PRESENT)

    def test_04_original_manual_UI_in_a_case_alias_is_detected(self):
        result = self.write([("NAYEON/DESKTOP_ALPHA/LOCAL_BYOK_WINDOW.PY", b"test only")])
        self.assertEqual(result.disposition, P220InventoryDisposition.LEGACY_EFFECT_PRESENT)

    def test_05_nested_binary_payload_is_UNPROVEN_not_clean(self):
        result = self.write([("bundle/companion.exe", b"MZ-test-not-an-executable")])
        self.assertEqual(result.disposition, P220InventoryDisposition.OPAQUE_CODE_UNPROVEN)
        self.assertFalse(result.native_effect_allowed)

    def test_06_nested_wheel_and_pyz_are_UNPROVEN(self):
        result = self.write([("payload/repackaged.whl", b"test only"), ("boot/entry.pyz", b"test only")])
        self.assertEqual(result.disposition, P220InventoryDisposition.OPAQUE_CODE_UNPROVEN)
        self.assertEqual(result.member_count, 2)

    def test_07_plain_source_only_zip_is_NOT_release_admission(self):
        result = self.write([("doc/readme.txt", b"test only"), ("nayeon/brain/harmless.py", b"x=1\n")])
        self.assertEqual(result.disposition, P220InventoryDisposition.SOURCE_ONLY_UNPROVEN)
        self.assertFalse(result.real_key_allowed)
        self.assertFalse(result.signed_installed_image_verified)
        self.assertFalse(result.os_code_integrity_admitted)
        self.assertFalse(result.service_store_isolated)

    def test_08_actual_ZIP_digest_matches_original_bytes(self):
        result = self.write([("docs/hello.txt", b"harmless test")])
        self.assertEqual(result.archive_sha256, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_09_traversal_ADS_backslash_and_absolute_member_all_refused(self):
        for bad in ("../outside.py", "C:/nayeon/secrets/windows_credential.py",
                    "nayeon\\secrets\\windows_credential.py", "/absolute.py",
                    "nayeon/x.py:evil", "nayeon/%2e%2e/x.py"):
            with self.subTest(path=bad):
                result = self.write([(bad, b"test")])
                self.assertEqual(result.disposition, P220InventoryDisposition.INVALID)
                self.assertFalse(result.production_release_allowed)

    def test_10_casefold_colliding_members_are_refused(self):
        result = self.write([("some/SOURCE.py", b"1"), ("some/source.PY", b"2")])
        self.assertEqual(result.disposition, P220InventoryDisposition.INVALID)

    def test_11_unicode_normalization_alias_is_refused(self):
        result = self.write([("sourc\u212a.py", b"test")])
        self.assertEqual(result.disposition, P220InventoryDisposition.INVALID)

    def test_12_symlink_entry_is_refused(self):
        with zipfile.ZipFile(self.path, "w") as z:
            info = zipfile.ZipInfo("link.py")
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            z.writestr(info, "target.py")
        result = inspect_bounded_zip(self.path)
        self.assertEqual(result.disposition, P220InventoryDisposition.INVALID)

    def test_13_corrupt_or_non_zip_never_produces_clean_state(self):
        self.path.write_bytes(b"not a zip")
        self.assertEqual(inspect_bounded_zip(self.path).disposition,
                         P220InventoryDisposition.INVALID)

    def test_14_untrusted_review_GO_and_signature_claim_do_not_mint_authority(self):
        result = self.write([("docs/harmless.txt", b"test")])
        self.assertFalse(approve_high_assurance_release(
            result, SEC03="GO", SEC04="GO", signed_binary=True,
            admin=True, wdac=True, human_consent=True, release=True))
        self.assertFalse(result.production_release_allowed)

    def test_15_review_receipt_is_immutable(self):
        result = self.write([("docs/harmless.txt", b"test")])
        with self.assertRaises(FrozenInstanceError):
            result.production_release_allowed = True


if __name__ == "__main__":
    unittest.main()
