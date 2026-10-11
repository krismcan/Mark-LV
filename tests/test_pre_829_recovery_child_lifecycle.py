"""Pre-8.29 adversarial stale-child recovery handoff regression (fake-only)."""
import sys
import tkinter as tk
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nayeon.brain.onboarding_metadata_commit import TrustedMetadataCommitHost
from nayeon.desktop_alpha.first_run_metadata_management_window import FirstRunMetadataManagementWindow
from tests.test_onboarding_coordination import FakeMutex


@unittest.skipUnless(sys.platform == "win32", "Windows Tk acceptance")
class StaleRecoveryChildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.path = Path(self.tmp.name) / "provider.json"
        self.mutex = FakeMutex()
        self.first = TrustedMetadataCommitHost(metadata_path=self.path, mutex=self.mutex)
        self.ctrl = self.first.recovery_controller
        self.addCleanup(self.clean)

    def clean(self):
        if self.ctrl._ctx is not None:
            self.ctrl.close()

    def test_old_destroyed_child_cannot_cancel_new_window_reconciliation(self):
        a = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        a.open_reconciliation_from_button()
        prior = a._recovery_dialog
        self.assertIsNotNone(prior)
        prior.review_from_button()
        old = prior._review
        self.assertIsNotNone(old)
        a.close_from_window()
        self.assertIsNone(self.ctrl._ctx)
        # New window/host on SAME canonical path, SAME pooled recovery controller.
        second = TrustedMetadataCommitHost(metadata_path=self.path, mutex=self.mutex)
        b = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=second)
        b.open_reconciliation_from_button()
        current = b._recovery_dialog
        current.review_from_button()
        fresh = self.ctrl._review
        self.assertIsNotNone(fresh)
        self.assertNotEqual(old.fingerprint, fresh.fingerprint)
        # Host rejects invalid old identity before touching current review.
        self.assertFalse(self.ctrl.approve_reconciliation(
            human_approved=False, fingerprint=old.fingerprint))
        self.assertIs(self.ctrl._review, fresh)
        # Retained child callbacks after Tk destroyed must be terminal no-ops.
        prior.reject_from_button()
        prior.approve_from_button()
        prior.review_from_button()
        prior.close_from_window()
        self.assertIs(self.ctrl._review, fresh)
        current._ack.set(True)
        current.approve_from_button()
        self.assertTrue(self.ctrl.ready)
        b.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_correct_review_rejection_still_consumes_pending_review(self):
        a = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        a.open_reconciliation_from_button()
        dialog = a._recovery_dialog
        dialog.review_from_button()
        review = self.ctrl._review
        self.assertIsNotNone(review)
        dialog.reject_from_button()
        self.assertIsNone(self.ctrl._review)
        self.assertFalse(self.ctrl.ready)
        a.close_from_window()
