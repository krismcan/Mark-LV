"""Pre-8.29 final lifecycle fault injection: fake kernel and actual Tk callbacks.

No native mutex, credential store, real provider, network, or production data.
Window destruction happens synchronously INSIDE the approval callback rather
than by manually adjusting a busy flag outside the approval lifecycle.
"""
import sys
import threading
import tkinter as tk
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from nayeon.brain import windows_onboarding_mutex as mutex_module
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.onboarding_coordination import (
    CooperativeOnboardingCoordinator, CoordinationReceipt, CoordinatedOutcome,
)
from nayeon.brain.onboarding_metadata_commit import (
    MetadataCommitOutcome, MetadataCommitReceipt, TrustedMetadataCommitHost,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation
from nayeon.desktop_alpha.first_run_credential_management_window import (
    FirstRunCredentialManagementWindow,
)
from nayeon.desktop_alpha.first_run_metadata_management_window import (
    FirstRunMetadataManagementWindow,
)
from tests.test_first_run_credential_management_window import Harness
from tests.test_onboarding_coordination import FakeMutex
from tests.test_pre_829_independent_lifecycle_findings import FakeKernel
from tests.test_pre_829_metadata_review_ownership import canonical


class RaisingNativeCall:
    """ctypes-call-shaped API stub, not an actual Win32 invocation."""

    def __init__(self, label):
        self.calls = 0
        self.label = label

    def __call__(self, *args):
        self.calls += 1
        raise OSError("synthetic " + self.label + " failure")


class NativeExceptionBoundaryTests(unittest.TestCase):
    def _assert_release_failure_remains_latched(self, failing_function):
        gate = threading.Lock()
        kernel = FakeKernel()
        setattr(kernel, failing_function, RaisingNativeCall(failing_function))
        try:
            with patch.object(mutex_module, "_PROCESS_LOCK", gate), \
                 patch.object(mutex_module.sys, "platform", "win32"), \
                 patch.object(mutex_module.ctypes, "WinDLL",
                              return_value=kernel, create=True):
                with self.assertRaisesRegex(
                        RuntimeError, "native release unverified"):
                    with mutex_module.WindowsOnboardingMutex().hold() as admitted:
                        self.assertIs(admitted, mutex_module.MutexAdmission.HELD)
                self.assertTrue(gate.locked(), "uncertain cleanup cannot reopen gate")
                with mutex_module.WindowsOnboardingMutex().hold() as new_admission:
                    self.assertIs(new_admission, mutex_module.MutexAdmission.BUSY)
                self.assertEqual(kernel.ReleaseMutex.calls, 1)
                self.assertEqual(kernel.CloseHandle.calls, 1)
        finally:
            # Never touch the real process lock: only the patched disposable gate.
            if gate.locked():
                gate.release()

    def test_release_mutex_native_exception_keeps_process_gate_closed(self):
        self._assert_release_failure_remains_latched("ReleaseMutex")

    def test_close_handle_native_exception_keeps_process_gate_closed(self):
        self._assert_release_failure_remains_latched("CloseHandle")

    def test_both_native_cleanup_exceptions_keep_process_gate_closed(self):
        gate = threading.Lock()
        kernel = FakeKernel()
        kernel.ReleaseMutex = RaisingNativeCall("ReleaseMutex")
        kernel.CloseHandle = RaisingNativeCall("CloseHandle")
        try:
            with patch.object(mutex_module, "_PROCESS_LOCK", gate), \
                 patch.object(mutex_module.sys, "platform", "win32"), \
                 patch.object(mutex_module.ctypes, "WinDLL",
                              return_value=kernel, create=True):
                with self.assertRaisesRegex(RuntimeError, "native release unverified"):
                    with mutex_module.WindowsOnboardingMutex().hold() as admitted:
                        self.assertIs(admitted, mutex_module.MutexAdmission.HELD)
                self.assertTrue(gate.locked())
                self.assertEqual(kernel.ReleaseMutex.calls, 1)
                self.assertEqual(kernel.CloseHandle.calls, 1)
        finally:
            if gate.locked():
                gate.release()


@unittest.skipUnless(sys.platform == "win32", "Real Windows Tk only")
class ApprovalCallbackRootDestructionTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self._safe_destroy)

    def _safe_destroy(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_metadata_destroy_inside_approve_callback_reject_receipt(self):
        self._metadata_during_approval(False)

    def test_metadata_destroy_inside_approve_callback_raises(self):
        self._metadata_during_approval(True)

    def _metadata_during_approval(self, raise_in_callback):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "provider.json"
            store = ProviderConnectionFileStore(path)
            initial = canonical("gpt-5.6")
            store.save(initial)
            host = TrustedMetadataCommitHost(metadata_path=path, mutex=FakeMutex())
            ctrl = host.recovery_controller
            review = ctrl.request_reconciliation()
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            window = FirstRunMetadataManagementWindow(
                tk.Toplevel(self.root), host=host)
            window._model.insert(0, "gpt-6")
            window.review_save_from_button()
            self.assertTrue(host.has_pending)
            owner = window._owner_token
            calls = []

            def destroy_during_real_approval(actual_host, **kwargs):
                self.assertIs(actual_host, host)
                self.assertTrue(window._busy)
                self.assertTrue(host.has_ui_owner(owner=owner))
                self.assertTrue(ctrl.ready)
                self.assertTrue(host.has_pending)
                window._root.destroy()  # Fires the exact-root Tk <Destroy> event.
                self.assertFalse(window._root.winfo_exists())
                self.assertTrue(window._closed)
                self.assertTrue(window._close_deferred)
                # Mutex and pending review are still retained DURING the operation.
                self.assertTrue(ctrl.ready)
                self.assertTrue(host.has_pending)
                calls.append(1)
                if raise_in_callback:
                    raise RuntimeError("synthetic in-flight metadata approval failure")
                return MetadataCommitReceipt(MetadataCommitOutcome.REFUSED)

            with patch.object(TrustedMetadataCommitHost, "approve_ui",
                              autospec=True, side_effect=destroy_during_real_approval):
                window.approve_from_button()

            self.assertEqual(calls, [1])
            self.assertFalse(window._close_deferred)
            self.assertFalse(ctrl.ready)
            self.assertIsNone(ctrl._ctx)
            self.assertIsNone(ctrl._ui_window_owner)
            self.assertFalse(host.has_pending)
            self.assertEqual(store.load(), initial)
            # A retained callback cannot approve the defunct review.
            window.approve_from_button()
            self.assertEqual(store.load(), initial)
            next_review = ctrl.request_reconciliation()
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=next_review.fingerprint))
            replacement = FirstRunMetadataManagementWindow(
                tk.Toplevel(self.root), host=host)
            self.assertTrue(host.has_ui_owner(owner=replacement._owner_token))
            replacement.close_from_window()

    def test_credential_destroy_inside_approve_callback_reject_receipt(self):
        self._credential_during_approval(False)

    def test_credential_destroy_inside_approve_callback_raises(self):
        self._credential_during_approval(True)

    def _credential_during_approval(self, raise_in_callback):
        harness = Harness()  # Fake backend, validator, mutex and temp metadata.
        self.addCleanup(harness.close)
        window = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=harness.coordinator)
        window.request_from_button(OnboardingOperation.CONNECT)
        self.assertTrue(harness.coordinator.has_pending)
        window._entry.insert(0, "synthetic-fixture-not-a-credential")
        owner = window._owner_token
        calls = []

        def destroy_during_real_approval(coordinator, *, ticket, owner_token,
                                        root, operation, candidate=None,
                                        acknowledged=False):
            self.assertIs(coordinator, harness.coordinator)
            self.assertIs(ticket, window._ticket)
            self.assertEqual(owner_token, owner)
            self.assertIs(root, window._root)
            self.assertIs(operation, OnboardingOperation.CONNECT)
            self.assertIs(acknowledged, False)
            self.assertTrue(window._busy)
            self.assertTrue(harness.controller.ready)
            self.assertTrue(harness.coordinator.has_pending)
            self.assertTrue(harness.controller.is_ui_window_owner(owner))
            self.assertIsNotNone(candidate)
            window._root.destroy()
            self.assertFalse(window._root.winfo_exists())
            self.assertTrue(window._closed)
            self.assertTrue(window._close_deferred)
            self.assertTrue(harness.controller.ready)
            calls.append(1)
            if raise_in_callback:
                raise RuntimeError("synthetic in-flight credential approval failure")
            return CoordinationReceipt(CoordinatedOutcome.REFUSED)

        with patch.object(CooperativeOnboardingCoordinator, "approve_ui",
                          autospec=True, side_effect=destroy_during_real_approval):
            window.approve_from_button()

        self.assertEqual(calls, [1])
        self.assertFalse(window._close_deferred)
        self.assertFalse(harness.controller.ready)
        self.assertIsNone(harness.controller._ctx)
        self.assertIsNone(harness.controller._ui_window_owner)
        self.assertFalse(harness.coordinator.has_pending)
        self.assertEqual((harness.backend.puts, harness.backend.deletes,
                          harness.validator.calls), (0, 0, 0))
        window.approve_from_button()  # Destroyed callback reference is inert.
        harness.reconcile()
        replacement = FirstRunCredentialManagementWindow(
            tk.Toplevel(self.root), coordinator=harness.coordinator)
        self.assertTrue(replacement._has_owner())
        replacement.close_from_window()


if __name__ == "__main__":
    unittest.main()
