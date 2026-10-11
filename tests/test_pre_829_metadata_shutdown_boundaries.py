"""Pre-8.29 adversarial fake-only shutdown boundary probes.

These probes intentionally exercise trusted callbacks directly, not model tools,
native secret storage, or provider calls. They must fail on a vulnerable tree.
"""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nayeon.brain.onboarding_metadata_commit import TrustedMetadataCommitHost
from nayeon.brain.windows_onboarding_mutex import MutexAdmission
from nayeon.desktop_alpha.first_run_credential_management_window import FirstRunCredentialManagementWindow


class ExitFaultMutex:
    def __init__(self):
        self.active = False

    @contextmanager
    def hold(self):
        if self.active:
            yield MutexAdmission.BUSY
            return
        self.active = True
        try:
            yield MutexAdmission.HELD
        finally:
            # Simulate a context exit failing without releasing its mutex.
            raise RuntimeError("synthetic mutex release failure")


class MetadataShutdownBoundaryTests(unittest.TestCase):
    def test_failed_mutex_exit_cannot_clear_live_ui_owner_and_regrant(self):
        with TemporaryDirectory() as directory:
            mutex = ExitFaultMutex()
            host = TrustedMetadataCommitHost(
                metadata_path=Path(directory) / "settings.json", mutex=mutex)
            controller = host.recovery_controller
            owner = host.claim_ui_owner()
            self.assertIsInstance(owner, str)
            review = controller.request_reconciliation()
            self.assertTrue(controller.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            with self.assertRaises(RuntimeError):
                host.close_ui_owner(owner=owner)
            self.assertFalse(controller.ready)
            # The failed mutex release must not permit a fresh window owner,
            # nor make the still-active native mutex tenure invisible.
            self.assertTrue(host.has_ui_owner(owner=owner))
            self.assertIsNone(controller.claim_ui_window_owner())
            self.assertIsNotNone(controller._ctx)
            self.assertTrue(mutex.active)

    def test_credential_window_close_cannot_revoke_foreign_metadata_owner(self):
        with TemporaryDirectory() as directory:
            from tests.test_onboarding_coordination import FakeMutex
            mutex = FakeMutex()
            host = TrustedMetadataCommitHost(
                metadata_path=Path(directory) / "settings.json", mutex=mutex)
            controller = host.recovery_controller
            owner = host.claim_ui_owner()
            review = controller.request_reconciliation()
            self.assertTrue(controller.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            # Same credential-window close method, with a fake-only
            # injected coordination handle; no actual Tk or credential key.
            panel = object.__new__(FirstRunCredentialManagementWindow)
            panel._busy = False
            panel._closed = False
            panel._owner_token = None
            panel._coordinator = type(
                "FakeCoordinator", (), {"recovery_controller": controller})()
            panel.reject_from_button = lambda: None
            panel._root = type("FakeRoot", (), {"destroy": lambda self: None})()
            try:
                panel.close_from_window()
                self.assertTrue(host.has_ui_owner(owner=owner))
                self.assertTrue(controller.ready)
                self.assertEqual(mutex.exited, 0)
            finally:
                if controller._ctx is not None:
                    controller.close()


@unittest.skipUnless(__import__("sys").platform == "win32", "Windows Tk only")
class RealTkCrossWindowShutdownTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from tests.test_first_run_credential_management_window import Harness
        self.h = Harness()  # Only fake secret backend/validator and fake mutex.
        self.addCleanup(self.h.close)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)

    def test_credential_window_cannot_close_metadata_owner_or_its_pending_save(self):
        import tkinter as tk
        from nayeon.desktop_alpha.first_run_metadata_management_window import (
            FirstRunMetadataManagementWindow,
        )
        from nayeon.brain.onboarding_metadata_commit import MetadataCommitOutcome
        from nayeon.brain.connection_persistence import ProviderConnectionFileStore
        metadata_host = TrustedMetadataCommitHost(
            metadata_path=self.h.path, mutex=self.h.mutex)
        a = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=metadata_host)
        b = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=self.h.coordinator)
        self.assertIsNone(b._owner_token)
        a._model.insert(0, "gpt-6")
        a.review_save_from_button()
        self.assertTrue(metadata_host.has_pending)
        b.close_from_window()
        self.assertTrue(metadata_host.has_ui_owner(owner=a._owner_token))
        self.assertTrue(self.h.controller.ready)
        self.assertTrue(metadata_host.has_pending)
        a.approve_from_button()
        self.assertEqual(
            ProviderConnectionFileStore(self.h.path).load().connection.model,
            "gpt-6")
        self.assertTrue(self.h.controller.ready)
        a.close_from_window()

    def test_second_credential_panel_cannot_cancel_then_closed_callback_cannot_reclaim(self):
        import tkinter as tk
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        a = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=self.h.coordinator)
        b = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=self.h.coordinator)
        self.assertTrue(a._has_owner())
        self.assertFalse(b._has_owner())
        a.request_from_button(OnboardingOperation.CONNECT)
        self.assertTrue(self.h.coordinator.has_pending)
        b.reject_from_button()
        b.request_from_button(OnboardingOperation.REMOVE)
        b.close_from_window()
        self.assertTrue(self.h.coordinator.has_pending)
        self.assertTrue(self.h.controller.ready)
        a.reject_from_button()
        self.assertFalse(self.h.coordinator.has_pending)
        a.close_from_window()
        self.h.reconcile()
        a.request_from_button(OnboardingOperation.CONNECT)
        a.open_reconciliation_from_button()
        a.close_from_window()
        self.assertTrue(self.h.controller.ready)
        self.assertEqual((self.h.backend.puts, self.h.backend.deletes), (0, 0))


    def test_destroyed_credential_root_callbacks_are_inert(self):
        import tkinter as tk
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        a = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=self.h.coordinator)
        a.request_from_button(OnboardingOperation.CONNECT)
        self.assertTrue(self.h.coordinator.has_pending)
        a._root.destroy()  # External Tk parent destruction, not WM_DELETE.
        # Retained Python callbacks may still be called programmatically.
        a.request_from_button(OnboardingOperation.REMOVE)
        a.approve_from_button()
        a.reject_from_button()
        a.open_reconciliation_from_button()
        # New exact-root destruction repair cancels the dead owner's pending
        # review; callback references remain inert and cannot reintroduce it.
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertEqual((self.h.backend.puts, self.h.backend.deletes), (0, 0))
