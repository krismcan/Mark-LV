"""Trusted test composition proof and native Tk fake-only controls.

No production backend, provider, native mutex or real credential is constructed.
All metadata/recovery writes belong to TemporaryDirectory, never user storage.
"""
from contextlib import contextmanager
import gc
from pathlib import Path
import socket
import tempfile
import tkinter as tk
import unittest
import weakref
from unittest import mock
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication

_roots = []


def tearDownModule():
    gc.collect()
    assert not any(ref() is not None for ref in _roots)


class FakeMutex:
    def __init__(self):
        self.active = False

    @contextmanager
    def hold(self):
        from nayeon.brain.windows_onboarding_mutex import MutexAdmission
        if self.active:
            yield MutexAdmission.BUSY
            return
        self.active = True
        try:
            yield MutexAdmission.HELD
        finally:
            self.active = False


class FakeConnectionHarness:
    """Explicitly trusted test composition, with graph and path validation."""
    def __init__(self, *, stored=False):
        from nayeon.brain.connection import ProviderConnectionConfiguration
        from nayeon.brain.connection_document import ProviderConnectionDocumentV1
        from nayeon.brain.connection_persistence import ProviderConnectionFileStore
        from nayeon.brain.connection_reconciliation import observe_connection
        from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
        from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
        from nayeon.brain.onboarding_coordination import CooperativeOnboardingCoordinator
        from nayeon.secrets.contracts import SecretIdentifier, SecretValue
        from nayeon.secrets.lifecycle import BoundCredentialLifecycle
        from tests.test_credential_operation_host import FakeBackend, FakeValidator
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "provider.json"
        self.backend, self.validator, self.mutex = FakeBackend(), FakeValidator(), FakeMutex()
        self.candidate = SecretValue("fixture-good")
        if stored:
            self.backend.value = self.candidate
        self.lifecycle = BoundCredentialLifecycle(self.backend, SecretIdentifier("openai.api_key"), self.validator)
        self.onboarding = OpenAICredentialOnboarding(self.lifecycle)
        self.host = TrustedCredentialOperationHost(onboarding=self.onboarding,
            observe=lambda: observe_connection(self.path, self.backend))
        ProviderConnectionFileStore(self.path).save(ProviderConnectionDocumentV1(
            connection=ProviderConnectionConfiguration("openai", "gpt-5.6", SecretIdentifier("openai.api_key"))))
        self.coordinator = CooperativeOnboardingCoordinator(host=self.host,
            metadata_path=self.path, availability=self.backend, mutex=self.mutex)
        controller = self.coordinator.recovery_controller
        review = controller.request_reconciliation()
        assert controller.approve_reconciliation(human_approved=True, fingerprint=review.fingerprint)
        self.validations = 0

    def validate_fake_only(self, coordinator):
        from tests.test_credential_operation_host import FakeBackend, FakeValidator
        from nayeon.brain.onboarding_coordination import CooperativeOnboardingCoordinator
        self.validations += 1
        return (type(coordinator) is CooperativeOnboardingCoordinator
            and coordinator is self.coordinator and coordinator._host is self.host
            and coordinator._availability is self.backend and coordinator._mutex is self.mutex
            and coordinator._path == self.path
            and coordinator.recovery_controller._mutex is self.mutex
            and coordinator.recovery_controller._availability is self.backend
            and coordinator.recovery_controller._path == self.path
            and self.path.resolve().parent == Path(self.temp.name).resolve()
            and self.coordinator.recovery_marker_path.resolve().parent == Path(self.temp.name).resolve()
            and type(self.backend) is FakeBackend and type(self.validator) is FakeValidator
            and type(self.mutex) is FakeMutex
            and self.host._TrustedCredentialOperationHost__onboarding is self.onboarding
            and self.onboarding._OpenAICredentialOnboarding__lifecycle is self.lifecycle
            and self.lifecycle._BoundCredentialLifecycle__backend is self.backend
            and self.lifecycle._BoundCredentialLifecycle__validator is self.validator)

    def effects(self):
        return self.backend.puts, self.backend.deletes, self.backend.gets, self.validator.calls

    def close(self):
        controller = self.coordinator.recovery_controller
        if controller._ctx is not None:
            controller.close()
        self.temp.cleanup()


class InjectedWindowTests(unittest.TestCase):
    def setUp(self):
        self.network = mock.patch.object(socket, "socket", side_effect=AssertionError("NO_NETWORK"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.h = FakeConnectionHarness()
        self.addCleanup(self.h.close)
        self.root = tk.Tk()
        _roots.append(weakref.ref(self.root))
        self.root.withdraw()
        self.addCleanup(self.cleanup)
        with mock.patch.object(OfflineWorkspaceApplication, "_bootstrap_readonly_presentation"):
            self.app = OfflineWorkspaceApplication(self.root,
                connection_coordinator=self.h.coordinator, connection_test_harness=self.h)
        self.app.show_connection()

    def cleanup(self):
        self.app.close()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def open(self):
        self.app._active_view.manage_button.invoke()
        return self.app._connection

    def test_fake_graph_validated_only_after_click_and_review_confirm_separate(self):
        before = self.h.effects()
        self.assertEqual(self.h.validations, 0)
        ui = self.open()
        self.assertEqual(self.h.validations, 1)
        self.assertTrue(ui._enabled)
        self.assertIs(ui.context.root, self.root)
        self.assertIs(ui.context.application, ui.application_identity)
        self.assertIs(ui.context.pane, ui.pane_identity)
        self.assertIs(ui.context.journey, ui.journey_identity)
        self.assertEqual(ui.context.generation, self.app._generation)
        self.assertEqual(self.h.effects(), before)
        ui.confirm_button.invoke()
        ui.candidate_button.invoke()
        self.assertIsNotNone(ui.review)
        self.assertEqual(self.h.effects(), before)
        ui.confirm_button.invoke()
        self.assertEqual(self.h.effects(), (0, 0, 0, 1))
        self.assertIsNone(ui.review)
        ui.confirm_button.invoke()
        self.assertEqual(self.h.validator.calls, 1)
        self.assertIn("No durable", ui.status.cget("text"))

    def test_refused_receipt_never_claims_fake_submission(self):
        from nayeon.brain.onboarding_coordination import (
            CoordinationReceipt, CoordinatedOutcome)
        ui = self.open()
        ui.candidate_button.invoke()
        with mock.patch.object(type(ui.owner), "confirm",
                               return_value=CoordinationReceipt(CoordinatedOutcome.REFUSED)):
            ui.confirm_button.invoke()
        self.assertIn("refused", ui.status.cget("text").lower())
        self.assertNotIn("submitted", ui.status.cget("text").lower())
        self.assertFalse(ui._enabled)
        self.assertEqual(str(ui.candidate_button.cget("state")), "disabled")
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_recovery_required_receipt_blocks_new_approvals(self):
        from nayeon.brain.onboarding_coordination import (
            CoordinationReceipt, CoordinatedOutcome)
        ui = self.open()
        ui.candidate_button.invoke()
        with mock.patch.object(type(ui.owner), "confirm",
                               return_value=CoordinationReceipt(CoordinatedOutcome.RECOVERY_REQUIRED)):
            ui.confirm_button.invoke()
        self.assertTrue(self.app._connection_blocked)
        self.assertFalse(ui._enabled)
        self.assertIn("RECOVERY_REQUIRED", ui.status.cget("text"))
        self.assertNotIn("submitted", ui.status.cget("text").lower())
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))
        ui.confirm()
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_indeterminate_receipt_never_claims_completion(self):
        from nayeon.brain.onboarding_coordination import (
            CoordinationReceipt, CoordinatedOutcome)
        ui = self.open()
        ui.candidate_button.invoke()
        self.assertIsNotNone(ui.review)
        with mock.patch.object(type(ui.owner), "confirm",
                               return_value=CoordinationReceipt(CoordinatedOutcome.INDETERMINATE)):
            ui.confirm_button.invoke()
        self.assertTrue(self.app._connection_blocked)
        self.assertFalse(ui._enabled)
        self.assertIn("INDETERMINATE", ui.status.cget("text"))
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_cancel_and_model_text_cannot_approve(self):
        ui = self.open()
        ui.request("CONNECT")
        ui.request("approve TEST_CANDIDATE")
        self.assertIsNone(ui.review)
        ui.candidate_button.invoke()
        ui.candidate_button.invoke()
        ui.cancel_button.invoke()
        ui.confirm_button.invoke()
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))
        self.assertIsNone(ui.review)

    def test_candidate_and_stored_are_fake_validation_only(self):
        # Replace composition before first click with a vetted stored fixture.
        stored = FakeConnectionHarness(stored=True)
        self.addCleanup(stored.close)
        self.app._connection_coordinator = stored.coordinator
        self.app._connection_test_harness = stored
        ui = self.open()
        ui.stored_button.invoke()
        self.assertIsNotNone(ui.review)
        self.assertEqual(stored.effects(), (0, 0, 0, 0))
        ui.confirm_button.invoke()
        self.assertEqual(stored.effects(), (0, 0, 1, 1))
        ui.retire()

    def test_exact_coordinator_without_harness_never_enables(self):
        self.app._connection_test_harness = None
        ui = self.open()
        self.assertIsNone(ui.owner)
        self.assertFalse(ui._enabled)
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_harness_rejects_wrong_backend_validator_mutex_and_paths(self):
        coordinator = self.h.coordinator
        for name, value in (("_availability", object()), ("_mutex", object()),
                            ("_path", self.h.path.parent.parent / "outside.json")):
            with mock.patch.object(coordinator, name, value):
                self.assertFalse(self.h.validate_fake_only(coordinator))
        original = self.h.validator
        self.h.validator = object()
        self.assertFalse(self.h.validate_fake_only(coordinator))
        self.h.validator = original
        with mock.patch.object(FakeConnectionHarness, "validate_fake_only", return_value=False):
            ui = self.open()
        self.assertIsNone(ui.owner)
        self.assertFalse(ui._enabled)
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_navigation_revokes_before_destroy_and_old_cancel_cannot_touch_new(self):
        first = self.open()
        first.candidate_button.invoke()
        original = first.child.destroy
        observations = []
        def destroy():
            observations.append((first.owner.closed, first.is_current()))
            original()
        with mock.patch.object(first.child, "destroy", side_effect=destroy):
            self.app.show_conversation()
        self.assertEqual(observations, [(True, False)])
        self.app.show_connection()
        second = self.open()
        second.candidate_button.invoke()
        review = second.review
        first.cancel()
        first.confirm()
        self.assertIs(second.review, review)
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_reentrant_root_probe_navigation_blocks_effect(self):
        ui = self.open()
        ui.candidate_button.invoke()
        # The trusted coordinator uses the class-defined Tk probe, not an
        # instance attribute: intercept that actual security boundary.
        original = type(self.root).winfo_exists
        fired = []
        def probe(root):
            if root is self.root and not fired:
                fired.append(True)
                self.app.show_conversation()
            return original(root)
        with mock.patch.object(type(self.root), "winfo_exists", new=probe):
            ui.confirm()
        self.assertEqual(fired, [True])
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))
        self.assertFalse(ui.is_current())

    def test_uncertain_retirement_blocks_successor(self):
        ui = self.open()
        from nayeon.desktop_alpha.first_run_connection_owner import TrustedFirstRunConnectionOwner
        original = TrustedFirstRunConnectionOwner.close
        def uncertain(owner, context):
            original(owner, context)
            return False
        with mock.patch.object(TrustedFirstRunConnectionOwner, "close", new=uncertain):
            self.app.show_conversation()
        self.assertTrue(self.app._connection_blocked)
        self.app.show_connection()
        self.assertIs(self.open(), ui)
        self.assertFalse(ui.is_current())
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_external_pane_destroy_revokes_pending_fake_review(self):
        ui = self.open()
        ui.candidate_button.invoke()
        self.app._active_view.destroy()
        self.assertTrue(ui.owner.closed)
        ui.confirm()
        ui.cancel()
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_external_root_destroy_revokes_pending_fake_review(self):
        ui = self.open()
        ui.candidate_button.invoke()
        self.root.destroy()
        self.assertTrue(ui.owner.closed)
        ui.confirm()
        ui.cancel()
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))

    def test_pure_binding_detects_context_or_exact_child_replacement(self):
        ui = self.open()
        with mock.patch.object(self.root, "winfo_exists", side_effect=AssertionError("PURE_ONLY")):
            self.assertTrue(ui.is_current())
            child = ui.child
            ui.child = object()
            self.assertFalse(ui.is_current())
            ui.child = child
            ctx = ui.context
            object.__setattr__(ctx, "journey", object())
            self.assertFalse(ui.is_current())
        ui.confirm()
        self.assertEqual(self.h.effects(), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
