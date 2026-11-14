"""P206 Windows-safe synthetic tests: original Python effect-entry vs dormant hold.

NO REAL KEY, WinDLL, WinCred, provider calls, or native service install.
All positive effect demonstrations use an in-memory fake adapter exclusively.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.credential_onboarding_composition import compose_openai_credential_onboarding
from nayeon.brain.p206_legacy_effect_hold_candidate import P206LegacyEffectHoldCandidate
from nayeon.secrets.contracts import SecretIdentifier, SecretStorageError, SecretValue
from nayeon.secrets.lifecycle import BoundCredentialLifecycle, CredentialValidationStatus
from nayeon.secrets.windows_credential import WindowsCredentialBackend


ID = SecretIdentifier("openai.api_key")
OTHER = SecretIdentifier("other.api_key")
SYNTHETIC = SecretValue("P206-SYNTHETIC-NOT-A-REAL-KEY")
ROOT = Path(__file__).resolve().parents[1]


class FakeNative:
    """No ctypes or Windows calls; counts exact legacy adapter invocations."""
    def __init__(self):
        self.records = []
        self.stored = False

    def write(self, target, blob, credential_type, persist, username):
        self.records.append(("write", target))
        self.stored = True

    def delete(self, target):
        self.records.append(("delete", target))
        old = self.stored
        self.stored = False
        return old

    def read(self, target):
        self.records.append(("read", target))
        return b"P206-SYNTHETIC-NOT-A-REAL-KEY" if self.stored else None

    def contains(self, target):
        self.records.append(("contains", target))
        return self.stored


class AlwaysValidFake:
    def validate(self, value):
        if type(value) is not SecretValue:
            raise AssertionError("Invalid fake candidate")
        return CredentialValidationStatus.VALID


class P206SyntheticEffectEntryTests(unittest.TestCase):
    def test_01_direct_legacy_backend_put_and_delete_reach_fake_native(self):
        native = FakeNative()
        backend = WindowsCredentialBackend(_native=native)
        backend.put(ID, SYNTHETIC)
        self.assertTrue(backend.delete(ID))
        self.assertEqual([name for name, _ in native.records], ["write", "delete"])
        self.assertEqual(native.records[0][1], "nayeon-v1/secret/openai.api_key")
        # Risk witness: backend itself has no independent native owner consent.

    def test_02_direct_legacy_backend_can_address_other_namespace_with_fake(self):
        native = FakeNative()
        backend = WindowsCredentialBackend(_native=native)
        backend.put(OTHER, SYNTHETIC)
        self.assertEqual(native.records[0][1], "nayeon-v1/secret/other.api_key")
        # Exact raw SecretIdentifier syntax is not the canonical provider allowlist.

    def test_03_lifecycle_without_ui_approval_reaches_fake_mutations(self):
        native = FakeNative()
        lifecycle = BoundCredentialLifecycle(
            WindowsCredentialBackend(_native=native), ID, AlwaysValidFake())
        onboarding = OpenAICredentialOnboarding(lifecycle)
        self.assertEqual(onboarding.connect(SYNTHETIC), CredentialValidationStatus.VALID)
        self.assertEqual(onboarding.replace(SYNTHETIC), CredentialValidationStatus.VALID)
        self.assertTrue(onboarding.remove())
        self.assertEqual(
            [name for name, _ in native.records if name in ("write", "delete")],
            ["write", "write", "delete"])
        # Actual observed legacy behaviour, not permission to use real WinCred.

    def test_04_dormant_hold_denies_exact_target_reads_and_mutations(self):
        backend = P206LegacyEffectHoldCandidate()
        for call in (
            lambda: backend.get(ID),
            lambda: backend.is_available(ID),
            lambda: backend.put(ID, SYNTHETIC),
            lambda: backend.delete(ID),
        ):
            with self.subTest(operation=call), self.assertRaises(SecretStorageError):
                call()

    def test_05_wrong_target_cannot_mint_hold_approval(self):
        backend = P206LegacyEffectHoldCandidate()
        for target in (OTHER, None, object(), ID, ID):
            with self.subTest(target_type=type(target).__name__):
                with self.assertRaises(SecretStorageError):
                    backend.put(target, SYNTHETIC)

    def test_06_forged_approval_and_replay_have_no_candidate_surface(self):
        backend = P206LegacyEffectHoldCandidate()
        for attr in ("authorise", "authorize", "approve", "dispatch", "reset",
                     "effect_actor", "native", "permit", "issue", "retry"):
            with self.subTest(attribute=attr):
                self.assertFalse(hasattr(backend, attr))
        for _ in range(3):
            with self.assertRaises(SecretStorageError):
                backend.delete(ID)
        with self.assertRaises(AttributeError):
            backend.enabled = True

    def test_07_fault_and_restart_remain_denied_with_fresh_instance(self):
        first = P206LegacyEffectHoldCandidate()
        with self.assertRaises(SecretStorageError):
            first.delete(ID)
        second = P206LegacyEffectHoldCandidate()
        with self.assertRaises(SecretStorageError):
            second.put(ID, SYNTHETIC)
        self.assertNotIn("backend", getattr(second, "__slots__", ()))

    def test_08_existing_lifecycle_and_onboarding_with_hold_fail_closed(self):
        backend = P206LegacyEffectHoldCandidate()
        lifecycle = BoundCredentialLifecycle(backend, ID, AlwaysValidFake())
        onboarding = OpenAICredentialOnboarding(lifecycle)
        for attempt in (
            lambda: onboarding.connect(SYNTHETIC),
            lambda: onboarding.replace(SYNTHETIC),
            lambda: onboarding.remove(),
            lambda: onboarding.test_stored(),
        ):
            with self.subTest(operation=attempt), self.assertRaises(SecretStorageError):
                attempt()

    def test_09_original_composition_with_hold_never_calls_provider(self):
        onboarding = compose_openai_credential_onboarding(
            P206LegacyEffectHoldCandidate())
        with self.assertRaises(SecretStorageError):
            onboarding.is_connected()
        # No credential validator request follows an availability denial.

    def test_10_no_trusted_runtime_backend_constructors_in_current_product(self):
        names = {"WindowsCredentialBackend",
                 "compose_openai_credential_onboarding",
                 "TrustedCredentialOperationHost",
                 "CooperativeOnboardingCoordinator",
                 "FirstRunCredentialManagementWindow"}
        hits = []
        for path in sorted((ROOT / "nayeon").rglob("*.py")):
            node = ast.parse(path.read_text(encoding="utf-8"))
            for obj in ast.walk(node):
                if isinstance(obj, ast.Call):
                    f = obj.func
                    name = (f.id if isinstance(f, ast.Name) else
                            f.attr if isinstance(f, ast.Attribute) else "")
                    if name in names:
                        hits.append((str(path.relative_to(ROOT)), obj.lineno, name))
        normalized = [(p.replace("\\\\", "/"), n, name) for p, n, name in hits]
        self.assertEqual(
            normalized,
            [("nayeon/brain/local_byok_user_scope.py", 207, "WindowsCredentialBackend")],
            "P132 actual local-user Windows backend factory inventory changed")
        # The P133 human-clicked route can reach P132 despite no default-start
        # WinCred access. This is user-scope, NOT privileged native C1.
        application = (ROOT / "nayeon/desktop_alpha/application.py").read_text("utf-8")
        bridge = (ROOT / "nayeon/desktop_alpha/local_byok_launch_bridge.py").read_text("utf-8")
        window = (ROOT / "nayeon/desktop_alpha/local_byok_window.py").read_text("utf-8")
        controller = (ROOT / "nayeon/brain/local_byok_user_scope.py").read_text("utf-8")
        self.assertIn("self._local_byok_launcher.launch()", application)
        self.assertIn("nayeon.desktop_alpha.local_byok_window", bridge)
        self.assertIn("controller=compose_user_scope_local_byok()", window)
        self.assertIn("return LocalByokController(WindowsCredentialBackend())", controller)
        self.assertIn("self._backend.put(_FIXED_IDENTIFIER, candidate)", controller)
        self.assertIn("self._backend.delete(_FIXED_IDENTIFIER)", controller)

    def test_11_original_native_and_Python_denial_scopes_are_disjoint(self):
        original = (ROOT / "nayeon/secrets/windows_credential.py").read_text("utf-8")
        native = (ROOT / "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs").read_text("utf-8")
        self.assertIn("self._dll.CredWriteW(", original)
        self.assertIn("self._dll.CredDeleteW(", original)
        self.assertNotIn("ServiceOwnedAdmissionBoundary", original)
        self.assertIn("CanDispatchNativeCredentialEffect { get { return false; } }", native)
        self.assertNotIn("CredWriteW", native)

    def test_12_no_backend_custody_or_secret_reveal_in_hold(self):
        code = (ROOT / "nayeon/brain/p206_legacy_effect_hold_candidate.py").read_text("utf-8")
        tree = ast.parse(code)
        self.assertNotIn("ctypes", code)
        self.assertNotIn("WinDLL(", code)
        self.assertFalse(any(isinstance(node, ast.Call) and
                             isinstance(node.func, ast.Attribute) and
                             node.func.attr == "reveal"
                             for node in ast.walk(tree)))
        self.assertNotIn("WindowsCredentialBackend", code.split('"""', 2)[-1])
        self.assertTrue(any(isinstance(x, ast.ClassDef) and
                            x.name == "P206LegacyEffectHoldCandidate" for x in tree))


if __name__ == "__main__":
    unittest.main()
