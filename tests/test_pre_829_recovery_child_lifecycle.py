"""Pre-8.29 adversarial stale-child recovery handoff regression (fake-only)."""
import sys
import tkinter as tk
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from nayeon.brain.onboarding_metadata_commit import TrustedMetadataCommitHost
from nayeon.brain.onboarding_recovery import RecoveryAdmissionError
from nayeon.brain.onboarding_recovery_document import RecoveryState
from nayeon.desktop_alpha.first_run_metadata_management_window import FirstRunMetadataManagementWindow
from nayeon.desktop_alpha.first_run_onboarding_recovery_window import FirstRunOnboardingRecoveryWindow
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

    def test_external_child_destroy_cancels_only_its_review_parent_keeps_tenure(self):
        """Red against 8.28.1: a child-only Destroy strands controller._review."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            self.assertIsNotNone(child)
            child._review_button.invoke()
            old_review = self.ctrl._review
            self.assertIsNotNone(old_review)
            owner = panel._owner_token
            self.assertTrue(self.first.has_ui_owner(owner=owner))
            self.assertIsNotNone(self.ctrl._ctx)
            self.assertFalse(self.ctrl.ready)

            # Deliberately bypass WM_DELETE; only this subordinate Tk root dies.
            child._root.destroy()
            self.assertIsNone(
                self.ctrl._review,
                "Destroy of a child-only root must cancel its exact pending review")
            self.assertIsNone(child._review)
            self.assertTrue(self.first.has_ui_owner(owner=owner))
            self.assertIsNotNone(self.ctrl._ctx, "Child must never close parent tenure")
            child.reject_from_button()
            child.approve_from_button()
            child.review_from_button()
            self.assertIsNone(self.ctrl._review)

            panel._recovery_button.invoke()
            replacement = panel._recovery_dialog
            self.assertIsNot(replacement, child)
            replacement._review_button.invoke()
            fresh = self.ctrl._review
            self.assertIsNotNone(fresh)
            self.assertIsNot(fresh, old_review)
            # Evidence fingerprints can repeat within the same unchanged tenure;
            # the retired child must be inert even when the digest repeats.
            child.close_from_window()
            child.reject_from_button()
            child.approve_from_button()
            self.assertIs(self.ctrl._review, fresh)
            replacement._reject.invoke()
            self.assertIsNone(self.ctrl._review)
            self.assertFalse(self.ctrl.ready)
            self.assertTrue(self.first.has_ui_owner(owner=owner))
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_child_destroy_during_reconciliation_request_cannot_strand_review(self):
        """Reentrant Tk Destroy after controller creates a review remains fail-closed."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            original = type(self.ctrl).request_reconciliation

            def destroy_after_request(controller, *, timeout_seconds=120.0):
                created = original(controller, timeout_seconds=timeout_seconds)
                child._root.destroy()
                return created

            with patch.object(type(self.ctrl), "request_reconciliation",
                              autospec=True, side_effect=destroy_after_request):
                child._review_button.invoke()
            self.assertFalse(child._root.winfo_exists())
            self.assertIsNone(child._review)
            self.assertIsNone(self.ctrl._review)
            self.assertFalse(self.ctrl.ready)
            self.assertIsNotNone(self.ctrl._ctx)
            self.assertTrue(self.first.has_ui_owner(owner=panel._owner_token))
            panel._recovery_button.invoke()
            fresh_child = panel._recovery_dialog
            fresh_child._review_button.invoke()
            self.assertIsNotNone(self.ctrl._review)
            fresh_child._reject.invoke()
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_reentrant_child_destroy_old_callback_must_not_cancel_same_fingerprint_successor(self):
        """Adversarial review-instance ABA: old request callback resumes after B exists."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        successor = []
        obsolete = []
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            self.assertIsNotNone(child)
            owner = panel._owner_token
            original = type(self.ctrl).request_reconciliation

            def reenter_with_successor(controller, *, timeout_seconds=120.0):
                # A is created, but the child has not yet assigned self._review.
                review_a = original(controller, timeout_seconds=timeout_seconds)
                obsolete.append(review_a)
                child._root.destroy()
                self.assertFalse(child._root.winfo_exists())
                self.assertTrue(self.first.has_ui_owner(owner=owner))
                self.assertIsNone(child._review)
                self.assertIs(self.ctrl._review, review_a)

                # A trusted reentrant cancellation supersedes A with B in the
                # *same* tenure, with identical evidence and fingerprint.
                self.assertFalse(controller.approve_reconciliation(
                    human_approved=False, fingerprint=review_a.fingerprint))
                review_b = original(controller, timeout_seconds=timeout_seconds)
                successor.append(review_b)
                self.assertIsNot(review_a, review_b)
                self.assertEqual(review_a.fingerprint, review_b.fingerprint)
                self.assertIs(self.ctrl._review, review_b)
                return review_a  # Retired A resumes after live B was opened.

            with patch.object(type(self.ctrl), "request_reconciliation",
                              autospec=True, side_effect=reenter_with_successor):
                child._review_button.invoke()

            self.assertEqual(len(obsolete), 1)
            self.assertEqual(len(successor), 1)
            self.assertIs(
                self.ctrl._review, successor[0],
                "An old destroyed child's callback must not consume same-fingerprint B")
            self.assertFalse(self.ctrl.ready)
            self.assertIsNotNone(self.ctrl._ctx)
            self.assertTrue(self.first.has_ui_owner(owner=owner))
            child.reject_from_button()
            self.assertIs(self.ctrl._review, successor[0])
        finally:
            # The parent retains ownership; clean only temporary fake state.
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_controller_exact_instance_blocks_same_fingerprint_stale_approval_and_cancel(self):
        """A trusted stale caller cannot approve or reject a successor review."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            old_child = panel._recovery_dialog
            old_child._review_button.invoke()
            review_a = old_child._review
            self.assertIsNotNone(review_a)
            self.assertFalse(self.ctrl.approve_reconciliation(
                human_approved=False, fingerprint=review_a.fingerprint,
                expected_review=review_a))
            new_child = FirstRunOnboardingRecoveryWindow(
                tk.Toplevel(panel._root), controller=self.ctrl)
            new_child._review_button.invoke()
            review_b = new_child._review
            self.assertIsNotNone(review_b)
            self.assertIsNot(review_a, review_b)
            self.assertEqual(review_a.fingerprint, review_b.fingerprint)
            self.assertFalse(self.ctrl.approve_reconciliation(
                human_approved=False, fingerprint=review_a.fingerprint,
                expected_review=review_a))
            self.assertIs(self.ctrl._review, review_b)
            self.assertFalse(self.ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review_a.fingerprint,
                expected_review=review_a))
            self.assertIs(self.ctrl._review, review_b)
            self.assertFalse(self.ctrl.ready)
            new_child._ack.set(True)
            new_child._approve.invoke()
            self.assertTrue(self.ctrl.ready)
            self.assertIsNone(self.ctrl._review)
            self.assertTrue(self.first.has_ui_owner(owner=panel._owner_token))
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_stale_live_child_cannot_approve_successor_with_same_fingerprint(self):
        """Old actual Tk approval button must not act on newly pending B."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            old_child = panel._recovery_dialog
            old_child._review_button.invoke()
            review_a = old_child._review
            self.assertIsNotNone(review_a)
            self.assertFalse(self.ctrl.approve_reconciliation(
                human_approved=False, fingerprint=review_a.fingerprint))
            new_child = FirstRunOnboardingRecoveryWindow(
                tk.Toplevel(panel._root), controller=self.ctrl)
            new_child._review_button.invoke()
            review_b = self.ctrl._review
            self.assertIsNotNone(review_b)
            self.assertIsNot(review_a, review_b)
            self.assertEqual(review_a.fingerprint, review_b.fingerprint)
            old_child._ack.set(True)
            old_child._approve.invoke()
            self.assertIs(self.ctrl._review, review_b)
            self.assertFalse(self.ctrl.ready)
            self.assertTrue(self.first.has_ui_owner(owner=panel._owner_token))
            new_child._reject.invoke()
            self.assertIsNone(self.ctrl._review)
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_stale_live_child_cannot_reject_successor_with_same_fingerprint(self):
        """Old actual Tk rejection button must not consume newly pending B."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            old_child = panel._recovery_dialog
            old_child._review_button.invoke()
            review_a = old_child._review
            self.assertIsNotNone(review_a)
            self.assertFalse(self.ctrl.approve_reconciliation(
                human_approved=False, fingerprint=review_a.fingerprint))
            new_child = FirstRunOnboardingRecoveryWindow(
                tk.Toplevel(panel._root), controller=self.ctrl)
            new_child._review_button.invoke()
            review_b = self.ctrl._review
            self.assertIsNotNone(review_b)
            self.assertEqual(review_a.fingerprint, review_b.fingerprint)
            old_child._reject.invoke()
            self.assertIs(self.ctrl._review, review_b)
            self.assertFalse(self.ctrl.ready)
            new_child._reject.invoke()
            self.assertIsNone(self.ctrl._review)
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_child_destroy_during_approval_cannot_grant_admission(self):
        """Human-button callback must not approve after its root is destroyed."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            child._review_button.invoke()
            self.assertIsNotNone(self.ctrl._review)
            child._ack.set(True)
            original = type(self.ctrl).approve_reconciliation

            def destroy_before_approval(controller, *, human_approved, fingerprint,
                                        archive_acknowledged=False, expected_review=None):
                child._root.destroy()
                return original(controller, human_approved=human_approved,
                                fingerprint=fingerprint,
                                archive_acknowledged=archive_acknowledged,
                                expected_review=expected_review)

            with patch.object(type(self.ctrl), "approve_reconciliation",
                              autospec=True, side_effect=destroy_before_approval):
                child._approve.invoke()
            self.assertIsNone(self.ctrl._review)
            self.assertFalse(self.ctrl.ready)
            self.assertIsNotNone(self.ctrl._ctx)
            self.assertTrue(self.first.has_ui_owner(owner=panel._owner_token))
            child.approve_from_button()
            child.reject_from_button()
            self.assertFalse(self.ctrl.ready)
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_descendant_widget_destroy_never_cancels_parent_recovery_review(self):
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            child._review_button.invoke()
            pending = self.ctrl._review
            self.assertIsNotNone(pending)
            child._evidence.destroy()  # A descendant event must be inert.
            self.assertIs(self.ctrl._review, pending)
            self.assertIs(child._review, pending)
            self.assertFalse(child._closed)
            child._reject.invoke()
            self.assertIsNone(self.ctrl._review)
            self.assertTrue(self.first.has_ui_owner(owner=panel._owner_token))
        finally:
            panel.close_from_window()

    def test_external_child_destroy_after_approval_keeps_parent_admission(self):
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            child._review_button.invoke()
            child._ack.set(True)
            child._approve.invoke()
            self.assertTrue(self.ctrl.ready)
            child._root.destroy()
            self.assertTrue(self.ctrl.ready)
            self.assertIsNone(self.ctrl._review)
            self.assertTrue(self.first.has_ui_owner(owner=panel._owner_token))
            child.reject_from_button()
            self.assertTrue(self.ctrl.ready)
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_external_destroy_cancellation_exception_preserves_blocked_parent_tenure(self):
        """Failed exact-review rejection is not permission to release parent or admit."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            child._review_button.invoke()
            pending = self.ctrl._review
            self.assertIsNotNone(pending)
            self.assertIs(child._review, pending)
            owner = panel._owner_token
            original = type(self.ctrl).approve_reconciliation
            calls = []

            def fail_exact_cancel(controller, *, human_approved, fingerprint,
                                  archive_acknowledged=False, expected_review=None):
                if human_approved is False and expected_review is pending:
                    calls.append((fingerprint, expected_review))
                    raise RuntimeError("synthetic cancellation failure")
                return original(controller, human_approved=human_approved,
                                fingerprint=fingerprint,
                                archive_acknowledged=archive_acknowledged,
                                expected_review=expected_review)

            with patch.object(type(self.ctrl), "approve_reconciliation",
                              autospec=True, side_effect=fail_exact_cancel):
                child._root.destroy()
            self.assertEqual(calls, [(pending.fingerprint, pending)])
            self.assertTrue(child._closed)
            self.assertIsNone(child._review)
            self.assertIs(self.ctrl._review, pending,
                          "A rejected cancellation cannot be claimed successful")
            self.assertFalse(self.ctrl.ready)
            self.assertIsNone(self.ctrl._store.read())
            self.assertIsNotNone(self.ctrl._ctx)
            self.assertTrue(self.first.has_ui_owner(owner=owner))
            child.close_from_window()
            child.approve_from_button()
            self.assertIs(self.ctrl._review, pending)
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)
        self.assertIsNone(self.ctrl._review)

    def test_destroy_after_approval_consumed_can_finish_only_prior_human_approval(self):
        """Destroy after consuming an approved review cannot invent or revoke consent."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            child._review_button.invoke()
            review = self.ctrl._review
            self.assertIsNotNone(review)
            child._ack.set(True)
            owner = panel._owner_token
            original = type(self.ctrl)._observe
            destroyed_at = []

            def destroy_on_first_approved_observation(controller):
                if not destroyed_at:
                    destroyed_at.append(controller._review)
                    child._root.destroy()
                return original(controller)

            with patch.object(type(self.ctrl), "_observe", autospec=True,
                              side_effect=destroy_on_first_approved_observation):
                child._approve.invoke()
            self.assertEqual(destroyed_at, [None],
                             "Destroy must occur after exact review consumption")
            self.assertTrue(child._closed)
            self.assertIsNone(child._review)
            self.assertIsNone(self.ctrl._review)
            self.assertTrue(self.ctrl.ready,
                            "Previously approved reconciliation may complete despite child close")
            chain = self.ctrl._store.read()
            self.assertIsNotNone(chain)
            self.assertEqual([record.state.value for record in chain],
                             ["reconciling", "ready"])
            self.assertIsNotNone(self.ctrl._ctx)
            self.assertTrue(self.first.has_ui_owner(owner=owner))
            child.reject_from_button()
            child.approve_from_button()
            self.assertTrue(self.ctrl.ready)
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_destroy_after_approval_consumed_observation_failure_stays_blocked(self):
        """No journal READY, retry or parent-owner release after a fake post-consent fault."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            child._review_button.invoke()
            self.assertIsNotNone(self.ctrl._review)
            child._ack.set(True)
            owner = panel._owner_token
            destroyed_at = []

            def destroy_then_raise(controller):
                destroyed_at.append(controller._review)
                child._root.destroy()
                raise RuntimeError("synthetic observation unavailable")

            with patch.object(type(self.ctrl), "_observe", autospec=True,
                              side_effect=destroy_then_raise):
                child._approve.invoke()
            self.assertEqual(destroyed_at, [None])
            self.assertTrue(child._closed)
            self.assertIsNone(child._review)
            self.assertIsNone(self.ctrl._review)
            self.assertFalse(self.ctrl.ready)
            self.assertTrue(self.ctrl._faulted)
            self.assertIsNone(self.ctrl._store.read())
            self.assertIsNotNone(self.ctrl._ctx)
            self.assertTrue(self.first.has_ui_owner(owner=owner))
            with self.assertRaises(RecoveryAdmissionError):
                self.ctrl.request_reconciliation()
            child.approve_from_button()
            self.assertFalse(self.ctrl.ready)
        finally:
            panel.close_from_window()
        self.assertIsNone(self.ctrl._ctx)

    def test_destroy_after_reconciling_checkpoint_failure_preserves_uncertain_journal(self):
        """Real fake-only journal must not promote a failed second checkpoint to READY."""
        panel = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=self.first)
        try:
            panel._recovery_button.invoke()
            child = panel._recovery_dialog
            child._review_button.invoke()
            self.assertIsNotNone(self.ctrl._review)
            child._ack.set(True)
            owner = panel._owner_token
            original = type(self.ctrl)._persist
            states = []

            def fault_on_ready(controller, state, *, kind=None,
                               operation_id=None, evidence_hash=None):
                states.append(state)
                if state is RecoveryState.READY:
                    raise RuntimeError("synthetic READY checkpoint failure")
                result = original(controller, state, kind=kind,
                                  operation_id=operation_id,
                                  evidence_hash=evidence_hash)
                if state is RecoveryState.RECONCILING:
                    self.assertIsNone(controller._review)
                    child._root.destroy()
                return result

            with patch.object(type(self.ctrl), "_persist", autospec=True,
                              side_effect=fault_on_ready):
                child._approve.invoke()
            self.assertEqual(states, [RecoveryState.RECONCILING, RecoveryState.READY])
            self.assertTrue(child._closed)
            self.assertIsNone(child._review)
            self.assertIsNone(self.ctrl._review)
            self.assertFalse(self.ctrl.ready)
            self.assertTrue(self.ctrl._faulted)
            chain = self.ctrl._store.read()
            self.assertEqual([record.state for record in chain],
                             [RecoveryState.RECONCILING])
            self.assertIsNotNone(self.ctrl._ctx)
            self.assertTrue(self.first.has_ui_owner(owner=owner))
            with self.assertRaises(RecoveryAdmissionError):
                self.ctrl.request_reconciliation()
            child.approve_from_button()
            self.assertFalse(self.ctrl.ready)
        finally:
            panel.close_from_window()
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
