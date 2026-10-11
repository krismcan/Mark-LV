"""Pre-8.29 independently reported lifecycle findings: fake-only adversarial closure."""
import threading
import tkinter as tk
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from nayeon.brain import windows_onboarding_mutex as native
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.onboarding_metadata_commit import TrustedMetadataCommitHost
from nayeon.brain.onboarding_recovery import RecoveryAdmissionError
from nayeon.desktop_alpha.first_run_metadata_management_window import FirstRunMetadataManagementWindow
from nayeon.desktop_alpha.first_run_onboarding_recovery_window import FirstRunOnboardingRecoveryWindow
from nayeon.desktop_alpha.first_run_credential_management_window import FirstRunCredentialManagementWindow
from tests.test_onboarding_coordination import FakeMutex
from tests.test_pre_829_metadata_review_ownership import canonical
from tests.test_first_run_credential_management_window import Harness
from tests.test_pre_829_metadata_shutdown_boundaries import ExitFaultMutex


class NativeBool:
    """ctypes function-shaped deterministic Win32 fake, no native calls."""
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def __call__(self, *args):
        self.calls += 1
        return self.result


class FakeKernel:
    def __init__(self, release_result=1, close_result=1):
        self.CreateMutexW = NativeBool(31337)
        self.WaitForSingleObject = NativeBool(native._WAIT_OBJECT_0)
        self.ReleaseMutex = NativeBool(release_result)
        self.CloseHandle = NativeBool(close_result)


class MutexTeardownBoundaryTests(unittest.TestCase):
    def _failed_native_case(self, release, close):
        gate = threading.Lock()
        kernel = FakeKernel(release, close)
        with patch.object(native, "_PROCESS_LOCK", gate), \
             patch.object(native.sys, "platform", "win32"), \
             patch.object(native.ctypes, "WinDLL", return_value=kernel, create=True):
            with self.assertRaisesRegex(RuntimeError, "native release unverified"):
                with native.WindowsOnboardingMutex().hold() as status:
                    self.assertIs(status, native.MutexAdmission.HELD)
            self.assertTrue(gate.locked())
            with native.WindowsOnboardingMutex().hold() as status:
                self.assertIs(status, native.MutexAdmission.BUSY)
            self.assertEqual(kernel.ReleaseMutex.calls, 1)
            self.assertEqual(kernel.CloseHandle.calls, 1)
        # The patched disposable gate remains latched; real process gate untouched.
        gate.release()

    def test_release_mutex_zero_is_not_success(self):
        self._failed_native_case(0, 1)

    def test_close_handle_zero_is_not_success(self):
        self._failed_native_case(1, 0)

    def test_failed_generator_exit_cannot_be_retried_to_erase_owner(self):
        with TemporaryDirectory() as directory:
            fake = ExitFaultMutex()
            host = TrustedMetadataCommitHost(
                metadata_path=Path(directory) / "settings.json", mutex=fake)
            ctrl = host.recovery_controller
            owner = host.claim_ui_owner()
            review = ctrl.request_reconciliation()
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            with self.assertRaises(RuntimeError):
                host.close_ui_owner(owner=owner)
            with self.assertRaises(RecoveryAdmissionError):
                host.close_ui_owner(owner=owner)
            self.assertTrue(ctrl._release_uncertain)
            self.assertTrue(host.has_ui_owner(owner=owner))
            self.assertIsNone(ctrl.claim_ui_window_owner())
            self.assertIsNotNone(ctrl._ctx)
            self.assertTrue(fake.active)


class AlternateOwnerReleaseTests(unittest.TestCase):
    def test_legacy_owner_release_cannot_leave_mutex_tenure_admitted(self):
        with TemporaryDirectory() as directory:
            host = TrustedMetadataCommitHost(
                metadata_path=Path(directory) / "settings.json", mutex=FakeMutex())
            ctrl = host.recovery_controller
            owner = host.claim_ui_owner()
            review = ctrl.request_reconciliation()
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            # A legacy trusted release method must not grant another window
            # authority while the mutex is still owned and READY.
            self.assertFalse(host.release_ui_owner(owner=owner))
            self.assertTrue(host.has_ui_owner(owner=owner))
            self.assertTrue(ctrl.ready)
            self.assertIsNone(ctrl.claim_ui_window_owner())
            self.assertTrue(host.close_ui_owner(owner=owner))
            self.assertFalse(ctrl.ready)


@unittest.skipUnless(__import__("sys").platform == "win32", "Real Windows Tk only")
class RealTkLifecycleFindings(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)

    def test_destroyed_metadata_review_cannot_approve_and_new_owner_recovers(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = ProviderConnectionFileStore(path)
            store.save(canonical("gpt-5.6"))
            host = TrustedMetadataCommitHost(metadata_path=path, mutex=FakeMutex())
            ctrl = host.recovery_controller
            review = ctrl.request_reconciliation()
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            a = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=host)
            a._model.insert(0, "gpt-6")
            a.review_save_from_button()
            self.assertTrue(host.has_pending)
            a._root.destroy()  # Independent external Tk destruction.
            a.approve_from_button()  # Retained Python callback attack.
            self.assertEqual(store.load(), canonical("gpt-5.6"))
            self.assertFalse(host.has_pending)
            self.assertFalse(ctrl.ready)
            self.assertIsNone(ctrl._ctx)
            review2 = ctrl.request_reconciliation()
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review2.fingerprint))
            b = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=host)
            self.assertTrue(host.has_ui_owner(owner=b._owner_token))
            a.approve_from_button()
            b.close_from_window()

    def test_destroyed_credential_root_releases_tenure_and_allows_new_owner(self):
        h = Harness()
        self.addCleanup(h.close)
        a = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=h.coordinator)
        self.assertTrue(a._has_owner())
        a._root.destroy()
        self.assertFalse(h.controller.ready)
        self.assertIsNone(h.controller._ctx)
        self.assertIsNone(h.controller._ui_window_owner)
        a.approve_from_button()
        h.reconcile()
        b = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=h.coordinator)
        self.assertTrue(b._has_owner())
        self.assertEqual((h.backend.puts, h.backend.deletes), (0, 0))
        b.close_from_window()

    def test_live_stale_recovery_child_cannot_close_newer_reconciliation(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            host = TrustedMetadataCommitHost(metadata_path=path, mutex=FakeMutex())
            ctrl = host.recovery_controller
            a = FirstRunOnboardingRecoveryWindow(
                tk.Toplevel(self.root), controller=ctrl)
            a.review_from_button()
            self.assertIsNotNone(a._review)
            # A trusted owner restart occurred while this child stayed alive.
            ctrl.close()
            b = ctrl.request_reconciliation()
            a.close_from_window()  # Reject old fingerprint, never revoke B.
            self.assertIs(ctrl._review, b)
            self.assertIsNotNone(ctrl._ctx)
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=b.fingerprint))
            self.assertTrue(ctrl.ready)
            ctrl.close()

    def test_metadata_destroy_during_busy_defers_owner_release(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            host = TrustedMetadataCommitHost(metadata_path=path, mutex=FakeMutex())
            ctrl = host.recovery_controller
            review = ctrl.request_reconciliation()
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            a = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=host)
            child = tk.Label(a._root)
            child.destroy()  # Not the root: must not revoke tenure.
            self.assertTrue(ctrl.ready)
            a._busy = True  # Fake in-progress trusted callback.
            a._root.destroy()
            self.assertTrue(a._close_deferred)
            self.assertTrue(ctrl.ready)
            a._busy = False
            a._finish_deferred_close()
            self.assertFalse(ctrl.ready)
            self.assertIsNone(ctrl._ctx)
            self.assertIsNone(ctrl._ui_window_owner)

    def test_credential_destroy_during_busy_defers_owner_release(self):
        h = Harness()
        self.addCleanup(h.close)
        a = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=h.coordinator)
        child = tk.Label(a._root)
        child.destroy()
        self.assertTrue(h.controller.ready)
        a._busy = True
        a._root.destroy()
        self.assertTrue(a._close_deferred)
        self.assertTrue(h.controller.ready)
        a._busy = False
        a._finish_deferred_close()
        self.assertFalse(h.controller.ready)
        self.assertIsNone(h.controller._ctx)
        self.assertIsNone(h.controller._ui_window_owner)
