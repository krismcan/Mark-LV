"""P140: signed companion policy / frozen launcher fail-closed tests.

No signing key, actual signed Nayeon executable, real API key, real WinCred
mutation or real subprocess launch is used in this module. Positive paths
use explicit mocks and MUST NEVER imply a real publisher/WDAC approval.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

from nayeon.desktop_alpha import frozen_signed_byok_companion as policy
from nayeon.desktop_alpha import local_byok_launch_bridge as bridge


class FakeChild:
    pid = 41382
    def poll(self):
        return None


class FrozenSignedCompanionGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="p140_nonsecret_")
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.main = self.folder / "NayeonDesktop.exe"
        self.helper = self.folder / "NayeonLocalByokOffline.exe"
        # Fixture is NOT real PE; only used for hash-path and mock-signature
        # source contract tests. Actual PE/signer acceptance requires a
        # separately authorised signed release, not fake data.
        self.main.write_bytes(b"MZ" + b"synthetic-main" * 110)
        self.helper.write_bytes(b"MZ" + b"synthetic-helper" * 110)
        self.publisher = "a" * 64
        self.main_digest = hashlib.sha256(self.main.read_bytes()).hexdigest()
        self.helper_digest = hashlib.sha256(self.helper.read_bytes()).hexdigest()

    def _fake_release(self, *, main=None, helper=None, publisher=None,
                      owner=True, frozen=True, executable=None):
        from contextlib import ExitStack
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(
            policy, "_APPROVED_MAIN_SHA256",
            self.main_digest if main is None else main))
        stack.enter_context(mock.patch.object(
            policy, "_APPROVED_COMPANION_SHA256",
            self.helper_digest if helper is None else helper))
        stack.enter_context(mock.patch.object(
            policy, "_APPROVED_SIGNER_CERT_SHA256",
            self.publisher if publisher is None else publisher))
        stack.enter_context(mock.patch.object(
            policy, "_APPROVED_CODE_INTEGRITY_RELEASE", owner))
        stack.enter_context(mock.patch.object(policy.sys, "platform", "win32"))
        stack.enter_context(mock.patch.object(
            policy.sys, "executable", str(executable or self.main)))
        stack.enter_context(mock.patch.object(
            policy.sys, "frozen", frozen, create=True))
        return stack

    def test_production_release_pins_are_deliberately_absent(self):
        self.assertEqual(policy._APPROVED_MAIN_SHA256, "")
        self.assertEqual(policy._APPROVED_COMPANION_SHA256, "")
        self.assertEqual(policy._APPROVED_SIGNER_CERT_SHA256, "")
        self.assertIs(policy._APPROVED_CODE_INTEGRITY_RELEASE, False)
        self.assertFalse(policy._release_pins_issued())

    def test_frozen_launch_default_never_spawns_unapproved_companion(self):
        with mock.patch.object(
            bridge.sys, "platform", "win32"
        ), mock.patch.object(
            bridge.sys, "frozen", True, create=True
        ), mock.patch.object(
            bridge.subprocess, "Popen",
            side_effect=AssertionError("no unapproved native process")
        ):
            self.assertIs(
                bridge.LocalByokLaunchBridge().launch(),
                bridge.LocalByokLaunchResult.UNAVAILABLE,
            )

    def test_pins_required_before_filesystem_or_signer_access(self):
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            side_effect=AssertionError("no signer query with no pins")
        ), mock.patch.object(
            policy, "_hex_sha256",
            side_effect=AssertionError("no file hash with no pins")
        ), mock.patch.object(
            policy.sys, "platform", "win32"
        ), mock.patch.object(
            policy.sys, "frozen", True, create=True
        ):
            self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_no_code_integrity_policy_owner_approval(self):
        self._fake_release(owner=False)
        self.assertFalse(policy._release_pins_issued())
        self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_empty_main_pin_refused(self):
        self._fake_release(main="")
        self.assertFalse(policy._release_pins_issued())
        self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_empty_companion_pin_refused(self):
        self._fake_release(helper="")
        self.assertFalse(policy._release_pins_issued())
        self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_malformed_signer_fingerprint_refused(self):
        self._fake_release(publisher="not-a-real-public-cert-fingerprint")
        self.assertFalse(policy._release_pins_issued())
        self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_uppercase_hash_without_canonical_release_pin_refused(self):
        self._fake_release(main=self.main_digest.upper())
        self.assertFalse(policy._release_pins_issued())
        self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_source_mode_never_admits_frozen_companion(self):
        self._fake_release(frozen=False)
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            side_effect=AssertionError("no frozen signer call in source mode")
        ):
            self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_non_windows_os_refused_even_with_fake_pins(self):
        self._fake_release()
        with mock.patch.object(policy.sys, "platform", "linux"):
            self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_cannot_launch_arbitrary_executable_name(self):
        self._fake_release(executable=self.folder / "TrojanDesktop.exe")
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            side_effect=AssertionError("must refuse unexpected executable name")
        ):
            self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_no_missing_companion_file(self):
        self._fake_release()
        self.helper.unlink()
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            side_effect=AssertionError("no signer for absent helper")
        ):
            self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_companion_content_changed_refuses_before_signature(self):
        self._fake_release()
        self.helper.write_bytes(b"MZ" + b"tampered-companion" * 110)
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            side_effect=AssertionError("no signer for hash mismatch")
        ):
            self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_parent_content_changed_refuses_before_signature(self):
        self._fake_release()
        self.main.write_bytes(b"MZ" + b"tampered-main" * 110)
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            side_effect=AssertionError("no signer for changed parent")
        ):
            self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_failed_main_authenticode_cannot_launch(self):
        self._fake_release()
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            return_value=None,
        ) as signed:
            self.assertIsNone(policy.approved_frozen_local_byok_companion())
            self.assertEqual(signed.call_count, 1)

    def test_failed_companion_authenticode_cannot_launch(self):
        self._fake_release()
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            side_effect=[self.publisher, None],
        ) as signed:
            self.assertIsNone(policy.approved_frozen_local_byok_companion())
            self.assertEqual(signed.call_count, 2)

    def test_wrong_cert_publisher_refused(self):
        self._fake_release()
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            return_value="b" * 64,
        ):
            self.assertIsNone(policy.approved_frozen_local_byok_companion())

    def test_regular_small_or_directory_executable_refused(self):
        short = self.folder / "short.exe"
        short.write_bytes(b"MZ")
        self.assertFalse(policy._ordinary_executable(short))
        self.assertFalse(policy._ordinary_executable(self.folder))

    def test_reparse_attribute_refuses_regardless_of_file_extension(self):
        attributes = mock.Mock(
            st_mode=stat.S_IFREG,
            st_file_attributes=0x400,
            st_size=2000,
        )
        with mock.patch.object(Path, "lstat", return_value=attributes):
            self.assertFalse(policy._ordinary_executable(self.main))

    def test_genuine_unsigned_local_fixture_is_not_signed(self):
        if sys.platform != "win32":
            self.skipTest("actual Authenticode status is Windows-only")
        # This only INSPECTS a synthetic ordinary non-PE test fixture.
        # No key, no code signing and no credential mutation.
        self.assertIsNone(policy._trusted_authenticode_signer(self.main))

    def test_mocked_positive_receipt_is_only_a_wiring_unit_test(self):
        self._fake_release()
        with mock.patch.object(
            policy, "_trusted_authenticode_signer",
            return_value=self.publisher,
        ):
            self.assertEqual(
                policy.approved_frozen_local_byok_companion(), self.helper
            )
        # Successful test mocking is NOT genuine signer/WDAC validation.

    def test_frozen_bridge_uses_exact_fake_approved_path_no_shell(self):
        self._fake_release()
        with mock.patch.object(
            policy, "approved_frozen_local_byok_companion",
            return_value=self.helper,
        ), mock.patch.object(
            bridge.subprocess, "Popen", return_value=FakeChild(),
        ) as started:
            result = bridge.LocalByokLaunchBridge().launch()
        self.assertIs(result, bridge.LocalByokLaunchResult.LAUNCHED_OFFLINE)
        argv, kwargs = started.call_args
        self.assertEqual(argv[0], [str(self.helper)])
        self.assertEqual(kwargs["cwd"], str(self.folder))
        self.assertIs(kwargs["shell"], False)
        self.assertIs(kwargs["close_fds"], True)
        self.assertIs(kwargs["stdin"], bridge.subprocess.DEVNULL)
        self.assertEqual(len(argv[0]), 1)

    def test_frozen_bridge_does_not_fallback_to_python_on_failed_policy(self):
        self._fake_release()
        with mock.patch.object(
            policy, "approved_frozen_local_byok_companion",
            return_value=None,
        ), mock.patch.object(
            bridge.subprocess, "Popen",
            side_effect=AssertionError("no unsigned fallback"),
        ):
            self.assertIs(
                bridge.LocalByokLaunchBridge().launch(),
                bridge.LocalByokLaunchResult.UNAVAILABLE,
            )

    def test_release_pin_source_not_set_by_environment(self):
        with mock.patch.dict(os.environ, {
            "NAYEON_P140_SIGNER": "a" * 64,
            "NAYEON_P140_MAIN_SHA": "b" * 64,
            "NAYEON_P140_COMPANION_SHA": "c" * 64,
            "P140_RELEASE_GO": "TRUE",
        }):
            self.assertFalse(policy._release_pins_issued())
        self.assertEqual(policy._APPROVED_SIGNER_CERT_SHA256, "")


if __name__ == "__main__":
    unittest.main()
