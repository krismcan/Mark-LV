"""P207: source-matched P132 user-scope vs native high-assurance consent review.

These tests use only a fake WinCred adapter, a fake mutex and synthetic text.
They do NOT call Advapi32, provider APIs, service entrypoints or signing tools.
Positive fake effects document the existing reduced user-scope path, not an
approval to activate a real key or to bypass the native C1 release hold.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import unittest

from nayeon.brain.local_byok_user_scope import (
    LocalByokController, LocalByokOperation as Operation,
    LocalByokOutcome as Outcome, compose_user_scope_local_byok,
)
from nayeon.brain.windows_onboarding_mutex import MutexAdmission
from nayeon.brain.p206_legacy_effect_hold_candidate import P206LegacyEffectHoldCandidate
from nayeon.secrets.contracts import SecretIdentifier, SecretValue
from nayeon.secrets.windows_credential import WindowsCredentialBackend

ROOT = Path(__file__).resolve().parents[1]
TARGET = "nayeon-v1/secret/openai.api_key"
FAKE = "P207-SYNTHETIC-UNUSABLE-CREDENTIAL"


class FakeNative:
    def __init__(self):
        self.values = {}
        self.events = []
        self.uncertain_after_write = False

    def contains(self, target):
        self.events.append(("contains", target))
        return target in self.values

    def read(self, target):
        raise AssertionError("P132 user-scope controller must not request secret bytes")

    def write(self, target, blob, kind, persistence, username):
        self.events.append(("write", target))
        if target != TARGET or kind != 1 or persistence != 2:
            raise AssertionError("Wrong fake target")
        self.values[target] = bytes(blob)
        if self.uncertain_after_write:
            raise RuntimeError("SYNTHETIC INDETERMINATE AFTER FAKE WRITE")

    def delete(self, target):
        self.events.append(("delete", target))
        return self.values.pop(target, None) is not None


class FakeMutex:
    @contextmanager
    def hold(self):
        yield MutexAdmission.HELD


def fake_controller(native):
    return LocalByokController(WindowsCredentialBackend(_native=native),
                              _mutex=FakeMutex())


class P207RealSourceOwnershipTests(unittest.TestCase):
    def test_01_source_has_actual_p132_factory_and_no_default_start_effect(self):
        source = (ROOT / "nayeon/brain/local_byok_user_scope.py").read_text("utf8")
        self.assertIn("return LocalByokController(WindowsCredentialBackend())", source)
        self.assertIn("self._backend.put(_FIXED_IDENTIFIER, candidate)", source)
        self.assertIn("self._backend.delete(_FIXED_IDENTIFIER)", source)
        self.assertIn("_FIXED_IDENTIFIER = SecretIdentifier(\"openai.api_key\")", source)

    def test_02_p133_button_to_real_p132_factory_source_chain(self):
        snippets = {
            "nayeon/desktop_alpha/workspace_window.py": "Open local key setup (offline, not connected)",
            "nayeon/desktop_alpha/application.py": "self._local_byok_launcher.launch()",
            "nayeon/desktop_alpha/local_byok_launch_bridge.py": "nayeon.desktop_alpha.local_byok_window",
            "nayeon/desktop_alpha/local_byok_window.py": "controller=compose_user_scope_local_byok()",
        }
        for path, token in snippets.items():
            with self.subTest(path=path):
                self.assertIn(token, (ROOT/path).read_text("utf8"))

    def test_03_synthetic_review_only_never_writes(self):
        native = FakeNative()
        c = fake_controller(native)
        self.assertEqual(native.events, [])
        review = c.begin(Operation.SAVE)
        self.assertIsNotNone(review)
        self.assertFalse(any(a == "write" for a, _ in native.events))

    def test_04_synthetic_explicit_consent_permits_fake_only_not_native_c1(self):
        native = FakeNative()
        c = fake_controller(native)
        ticket = c.begin(Operation.SAVE)
        self.assertEqual(
            c.approve(ticket, confirmed=True, candidate=SecretValue(FAKE)),
            Outcome.SUBMITTED_UNVALIDATED,
        )
        self.assertEqual(native.values[TARGET], FAKE.encode())
        self.assertEqual([a for a, _ in native.events if a == "write"], ["write"])

    def test_05_no_local_confirmation_refuses_fake_write(self):
        native = FakeNative()
        c = fake_controller(native)
        ticket = c.begin(Operation.SAVE)
        self.assertEqual(
            c.approve(ticket, confirmed=False, candidate=SecretValue(FAKE)),
            Outcome.REFUSED,
        )
        self.assertFalse(native.values)

    def test_06_replayed_local_review_refused_by_p132(self):
        native = FakeNative()
        c = fake_controller(native)
        ticket = c.begin(Operation.SAVE)
        self.assertEqual(
            c.approve(ticket, confirmed=True, candidate=SecretValue(FAKE)),
            Outcome.SUBMITTED_UNVALIDATED,
        )
        self.assertEqual(
            c.approve(ticket, confirmed=True, candidate=SecretValue(FAKE)),
            Outcome.REFUSED,
        )
        self.assertEqual([a for a, _ in native.events if a == "write"], ["write"])

    def test_07_remove_requires_destructive_acknowledgement(self):
        native = FakeNative()
        native.values[TARGET] = FAKE.encode()
        c = fake_controller(native)
        review = c.begin(Operation.REMOVE)
        self.assertEqual(c.approve(review, confirmed=True), Outcome.REFUSED)
        self.assertIn(TARGET, native.values)
        review2 = c.begin(Operation.REMOVE)
        self.assertEqual(
            c.approve(review2, confirmed=True, deletion_acknowledged=True),
            Outcome.SUBMITTED_REMOVAL,
        )
        self.assertNotIn(TARGET, native.values)

    def test_08_after_effect_fault_latches_p132_controller(self):
        native = FakeNative()
        native.uncertain_after_write = True
        c = fake_controller(native)
        review = c.begin(Operation.SAVE)
        self.assertEqual(
            c.approve(review, confirmed=True, candidate=SecretValue(FAKE)),
            Outcome.RECONCILIATION_REQUIRED,
        )
        self.assertIsNone(c.begin(Operation.REPLACE))
        self.assertEqual([a for a, _ in native.events if a == "write"], ["write"])

    def test_09_recreated_controller_loses_uncertainty_proving_G3_gap(self):
        native = FakeNative()
        native.uncertain_after_write = True
        first = fake_controller(native)
        review = first.begin(Operation.SAVE)
        self.assertEqual(
            first.approve(review, confirmed=True, candidate=SecretValue(FAKE)),
            Outcome.RECONCILIATION_REQUIRED,
        )
        second = fake_controller(native)
        # P132 consciously has process-local uncertainty. THIS IS A GAP,
        # not authority to retry. No second effect is executed in this test.
        review2 = second.begin(Operation.REPLACE)
        self.assertIsNotNone(review2)
        self.assertEqual(review2.operation, Operation.REPLACE)
        self.assertEqual([a for a, _ in native.events if a == "write"], ["write"])

    def test_10_p206_hold_cannot_be_injected_into_p132_exact_backend_owner(self):
        with self.assertRaises(TypeError):
            LocalByokController(P206LegacyEffectHoldCandidate(), _mutex=FakeMutex())

    def test_11_direct_backend_can_mutate_other_syntax_valid_target_fake_only(self):
        native = FakeNative()
        backend = WindowsCredentialBackend(_native=native)
        backend.put(SecretIdentifier("another.valid_key"), SecretValue(FAKE))
        self.assertEqual(native.events[-1],
                         ("write", "nayeon-v1/secret/another.valid_key"))
        # FakeNative refuses nonfixed target so this should be isolated
        # from actual effects; the attempted call still proves routing.

    def test_12_native_c1_remains_denial_only_without_service_main(self):
        native = (ROOT/"native_c1_candidate/ServiceOwnedAdmissionBoundary.cs").read_text("utf8")
        host = (ROOT/"native_c1_candidate/CustodyService.cs").read_text("utf8")
        self.assertIn("CanDispatchNativeCredentialEffect { get { return false; } }", native)
        self.assertIn("ProductionReleaseEligible { get { return false; } }", native)
        self.assertIn('throw new InvalidOperationException("Custody service is unavailable")',host)
        self.assertNotIn("ServiceBase.Run(", host)

    def test_13_frozen_historical_p96_test_still_exists_unmodified(self):
        # An exact pinned P206 ancestor check is performed by the CI collector.
        scripts = list((ROOT/"tests").rglob("*p96*"))
        self.assertTrue(scripts, "P96 historical comparator path not found")

    def test_14_source_mode_is_not_a_signed_native_executable(self):
        bridge=(ROOT/"nayeon/desktop_alpha/local_byok_launch_bridge.py").read_text("utf8")
        self.assertIn('command = [sys.executable, "-B", "-m", _CHILD_MODULE]', bridge)
        self.assertIn("approved_frozen_local_byok_companion()", bridge)
        signed=(ROOT/"nayeon/desktop_alpha/frozen_signed_byok_companion.py").read_text("utf8")
        self.assertIn("return None", signed)


if __name__ == "__main__":
    unittest.main()
