"""Fake-only trusted Tk reconciliation handoff (no native credential backend)."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

from nayeon.brain.onboarding_metadata_commit import TrustedMetadataCommitHost
from nayeon.brain.onboarding_recovery import TrustedOnboardingRecoveryController
from nayeon.brain.windows_onboarding_mutex import MutexAdmission
from nayeon.desktop_alpha.first_run_metadata_management_window import FirstRunMetadataManagementWindow


class _Mutex:
    @contextmanager
    def hold(self):
        yield MutexAdmission.HELD


class ExpiryTests(unittest.TestCase):
    def test_reconciliation_expiry_blocks_human_approval(self):
        with TemporaryDirectory() as root:
            now = [20.]
            ctrl = TrustedOnboardingRecoveryController(
                Path(root)/"provider.json", mutex=_Mutex(), clock=lambda: now[0])
            review = ctrl.request_reconciliation(timeout_seconds=1.)
            now[0]=22.
            self.assertFalse(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            self.assertFalse(ctrl.ready)
            self.assertIsNone(ctrl._store.read())
            ctrl.close()


@unittest.skipUnless(sys.platform=="win32", "Requires real Windows Tk UI")
class TkRecoveryHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.patch_mutex = patch("nayeon.brain.onboarding_recovery.WindowsOnboardingMutex",_Mutex)
        self.patch_mutex.start()
        self.addCleanup(self.patch_mutex.stop)
        self.host = TrustedMetadataCommitHost(
            metadata_path=Path(self.tmp.name)/"provider.json")
        self.ctrl = self.host.recovery_controller
        self.root=tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.cleanup_ui)
        self.window=FirstRunMetadataManagementWindow(self.root,host=self.host)

    def cleanup_ui(self):
        try:
            if self.ctrl._ctx is not None:
                self.ctrl.close()
        except Exception:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_explicit_review_approval_handoff_to_metadata_save(self):
        self.assertFalse(self.ctrl.ready)
        self.window._recovery_button.invoke()
        dialog=self.window._recovery_dialog
        self.assertIsNotNone(dialog)
        self.assertFalse(self.ctrl.ready)
        dialog._review_button.invoke()
        self.assertIsNotNone(dialog._review)
        self.assertFalse(self.ctrl.ready)
        dialog._approve.invoke()  # no acknowledgement, must be refused
        self.assertFalse(self.ctrl.ready)
        dialog._ack.set(True)
        dialog._approve.invoke()
        self.assertTrue(self.ctrl.ready)
        dialog.close_from_window()
        self.assertTrue(self.ctrl.ready, "Closing review UI must not revoke trusted owner tenure")
        self.window._model.insert(0,"gpt-6")
        self.window._save.invoke()
        self.assertTrue(self.host.has_pending)
        self.window._approve.invoke()
        self.assertTrue(self.ctrl.ready)
        self.window.close_from_window()
        self.assertFalse(self.ctrl.ready)

    def test_reject_leaves_protected_action_unavailable(self):
        self.window._recovery_button.invoke()
        d=self.window._recovery_dialog
        d._review_button.invoke()
        d._reject.invoke()
        d.close_from_window()
        self.assertFalse(self.ctrl.ready)
        self.window._model.insert(0,"gpt-6")
        self.window._save.invoke()
        self.assertFalse(self.host.has_pending)


if __name__=="__main__":
    unittest.main()
