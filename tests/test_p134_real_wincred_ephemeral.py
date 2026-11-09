"""P134: genuine Win32 CredWriteW/CredReadW/CredDeleteW with ONLY synthetic data.

IMPORTANT: This is an explicit ephemeral GitHub-hosted Windows runner proof.
It MUST NOT run on Kristian, a developer desktop, a real user's Credential
Manager, or a machine with persistent user state. The target is a fresh random
P134-specific namespace, never 'openai.api_key'. No real API key, secret,
provider connection, registry or privileged service is touched.

The Python process is signed/distributed by the hosted Windows runtime, NOT
a signed Nayeon production package. Test-mode gates are not production trust.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
import uuid
from unittest.mock import patch

from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretStorageError, SecretValue,
)
from nayeon.secrets.windows_credential import WindowsCredentialBackend


_EPHEMERAL_APPROVAL = "EPHEMERAL_GITHUB_WINDOWS_ONLY"
_PREFIX = "p134.synthetic."
_PRODUCTION_TARGET = "nayeon-v1/secret/openai.api_key"
_NAMESPACE = re.compile(r"\Ap134\.synthetic\.[a-f0-9]{32}\Z")
_CHILD_MARKER = "P134_CHILD_SYNTHETIC_PROBE_OK"


def _require_ephemeral_windows() -> None:
    if not (
        sys.platform == "win32"
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_OS") == "Windows"
        and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
        and os.environ.get("P134_NATIVE_WINCRED_EPHEMERAL_AUTH")
        == _EPHEMERAL_APPROVAL
        and os.environ.get("RUNNER_TEMP")
    ):
        raise RuntimeError("P134 genuine WinCred test requires disposable hosted Windows approval")


def _identifier(hex_part: str) -> SecretIdentifier:
    if type(hex_part) is not str or re.fullmatch(r"[a-f0-9]{32}", hex_part) is None:
        raise ValueError("P134 requires canonical synthetic-only identifier")
    result = SecretIdentifier(_PREFIX + hex_part)
    if _NAMESPACE.fullmatch(result.value) is None:
        raise ValueError("P134 namespace violation")
    if WindowsCredentialBackend._target(result) == _PRODUCTION_TARGET:
        raise RuntimeError("P134 production credential target forbidden")
    return result


def _synthetic_value(hex_part: str, version: str) -> SecretValue:
    if version not in ("v1", "v2", "unicode"):
        raise ValueError("Unsupported test fixture")
    if version == "unicode":
        return SecretValue("P134-SYNTHETIC-NONKEY-" + hex_part + "-한글-🌸-v3")
    return SecretValue("P134-SYNTHETIC-NONKEY-" + hex_part + "-" + version)


def _child_probe(argv: list[str]) -> int:
    # Child receives only the public synthetic fixture ID and action;
    # no credential bytes, API keys or values via argv/stdout/stderr.
    try:
        _require_ephemeral_windows()
        if len(argv) != 3 or argv[0] != "--probe":
            return 44
        hex_part, version = argv[1:]
        identifier = _identifier(hex_part)
        backend = WindowsCredentialBackend()
        if version == "absent":
            success = backend.is_available(identifier) is False
        else:
            expected = _synthetic_value(hex_part, version)
            present = backend.is_available(identifier)
            value = backend.get(identifier) if present else None
            success = (
                present is True
                and type(value) is SecretValue
                and value.reveal() == expected.reveal()
            )
        if success:
            print(_CHILD_MARKER)
            return 0
    except Exception:
        pass
    print("P134_CHILD_SYNTHETIC_PROBE_REFUSED")
    return 45


@unittest.skipUnless(sys.platform == "win32", "Windows host only")
class GenuineEphemeralWinCredTests(unittest.TestCase):
    def setUp(self):
        _require_ephemeral_windows()
        self.hex_part = uuid.uuid4().hex
        self.identifier = _identifier(self.hex_part)
        self.backend = WindowsCredentialBackend()
        self.assertNotEqual(
            WindowsCredentialBackend._target(self.identifier),
            _PRODUCTION_TARGET,
        )
        # A collision must fail BEFORE deletion or mutation. A fresh UUID
        # under a reserved test prefix should never be an existing credential.
        self.assertFalse(self.backend.is_available(self.identifier))
        self.addCleanup(self._delete_owned_fixture)

    def _delete_owned_fixture(self):
        # Cleanup runs even after a partial native failure; this fresh unique
        # test target was verified absent before any write by this test.
        self.backend.delete(self.identifier)
        self.assertFalse(self.backend.is_available(self.identifier))

    def _child(self, version: str) -> None:
        _require_ephemeral_windows()
        self.assertIn(version, ("v1", "v2", "unicode", "absent"))
        # No inherited provider API secrets or Nayeon runtime key variables.
        keep = ("SystemRoot", "WINDIR", "USERPROFILE", "APPDATA",
                "LOCALAPPDATA", "TEMP", "TMP", "PATH", "COMSPEC",
                "GITHUB_ACTIONS", "RUNNER_OS", "GITHUB_REPOSITORY",
                "RUNNER_TEMP", "P134_NATIVE_WINCRED_EPHEMERAL_AUTH")
        env = {k: os.environ[k] for k in keep if k in os.environ}
        self.assertNotIn("OPENAI_API_KEY", env)
        result = subprocess.run(
            [sys.executable, "-B", "-m", "tests.test_p134_real_wincred_ephemeral",
             "--probe", self.hex_part, version],
            cwd=os.getcwd(), env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0, "separate Windows process refused synthetic probe")
        self.assertEqual(result.stdout.strip(), _CHILD_MARKER)
        self.assertEqual(result.stderr, "")

    def test_real_windows_credential_target_initially_missing(self):
        self.assertFalse(self.backend.is_available(self.identifier))
        with self.assertRaises(SecretNotFoundError):
            self.backend.get(self.identifier)
        self.assertFalse(self.backend.delete(self.identifier))

    def test_real_windows_native_save_presence_and_synthetic_read(self):
        self.backend.put(
            self.identifier, _synthetic_value(self.hex_part, "v1"),
        )
        self.assertTrue(self.backend.is_available(self.identifier))
        actual = self.backend.get(self.identifier)
        self.assertEqual(
            actual.reveal(), _synthetic_value(self.hex_part, "v1").reveal(),
        )

    def test_real_windows_native_replacement_uses_exact_same_slot(self):
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v1"))
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v2"))
        self.assertEqual(
            self.backend.get(self.identifier).reveal(),
            _synthetic_value(self.hex_part, "v2").reveal(),
        )
        self.assertTrue(self.backend.is_available(self.identifier))

    def test_real_windows_native_delete_and_idempotent_absence(self):
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v1"))
        self.assertTrue(self.backend.delete(self.identifier))
        self.assertFalse(self.backend.is_available(self.identifier))
        self.assertFalse(self.backend.delete(self.identifier))

    def test_real_windows_native_utf8_roundtrip(self):
        self.backend.put(
            self.identifier, _synthetic_value(self.hex_part, "unicode"),
        )
        self.assertEqual(
            self.backend.get(self.identifier).reveal(),
            _synthetic_value(self.hex_part, "unicode").reveal(),
        )

    def test_real_windows_distinct_process_observes_synthetic_key(self):
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v1"))
        self._child("v1")

    def test_real_windows_distinct_process_observes_replacement(self):
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v1"))
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v2"))
        self._child("v2")

    def test_real_windows_distinct_process_observes_deletion(self):
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v1"))
        self.assertTrue(self.backend.delete(self.identifier))
        self._child("absent")

    def test_real_windows_utf8_visible_to_distinct_process(self):
        self.backend.put(
            self.identifier, _synthetic_value(self.hex_part, "unicode"),
        )
        self._child("unicode")

    def test_real_windows_max_blob_guard_before_native_effect(self):
        with self.assertRaises(SecretStorageError):
            self.backend.put(self.identifier, SecretValue("X" * 2561))
        self.assertFalse(self.backend.is_available(self.identifier))

    def test_real_windows_explicit_cleanup_after_replace(self):
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v1"))
        self.backend.put(self.identifier, _synthetic_value(self.hex_part, "v2"))
        self.assertTrue(self.backend.delete(self.identifier))
        self.assertFalse(self.backend.is_available(self.identifier))

    def test_real_windows_adapter_constructs_without_creating_any_slot(self):
        with patch(
            "nayeon.secrets.windows_credential._load_advapi32",
            side_effect=AssertionError("native access during construction"),
        ):
            backend = WindowsCredentialBackend()
        self.assertIs(type(backend), WindowsCredentialBackend)
        self.assertFalse(self.backend.is_available(self.identifier))


def _main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--probe":
        return _child_probe(sys.argv[1:])
    _require_ephemeral_windows()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        GenuineEphemeralWinCredTests,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful() and result.testsRun == 12:
        print("P134_ACTUAL_WINDOWS_CREDWRITE_CREDREAD_CREDDELETE_SYNTHETIC=12_PASS")
        print("P134_REAL_WIN32_CREDENTIAL_TARGET=EPHEMERAL_RANDOM_NAMESPACE_ONLY")
        print("P134_REAL_OPENAI_API_KEY_TARGET=NEVER_TOUCHED")
        print("P134_SEPARATE_WINDOWS_PROCESS_READ_REPLACE_DELETE=TESTED")
        print("P134_SYNTHETIC_TEST_CREDENTIAL_CLEANUP=REQUIRED")
        print("P134_KRISTIAN_NATIVE_WINCRED=NOT_TOUCHED")
        print("P134_REAL_API_KEY_OR_PROVIDER_NETWORK=NONE")
        print("P134_SIGNED_PRODUCTION_PACKAGE=ABSENT")
        print("P134_USER_SCOPE_FIRST_RELEASE=HOLD")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
