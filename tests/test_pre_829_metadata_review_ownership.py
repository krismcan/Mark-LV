"""Pre-8.29 adversarial Windows/Tk shared-host approval tests; fake-only."""
import sys
import tkinter as tk
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from nayeon.brain.connection_document import ProviderConnectionDocumentV1, parse_provider_connection_document
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.onboarding_metadata_commit import (
    TrustedMetadataCommitHost, MetadataOperation, MetadataCommitOutcome,
)
from nayeon.desktop_alpha.first_run_metadata_management_window import FirstRunMetadataManagementWindow
from tests.test_onboarding_coordination import FakeMutex


def canonical(model):
    return parse_provider_connection_document({
        "schema_version": 1,
        "connection": {"provider": "openai", "model": model,
                       "credential": "openai.api_key"},
    })


@unittest.skipUnless(sys.platform == "win32", "Windows Tk only")
class SharedMetadataReviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "settings.json"
        self.store = ProviderConnectionFileStore(self.path)
        self.store.save(canonical("gpt-5.6"))
        self.host = TrustedMetadataCommitHost(metadata_path=self.path, mutex=FakeMutex())
        self.controller = self.host.recovery_controller
        review = self.controller.request_reconciliation()
        self.assertTrue(self.controller.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.clean)
        self.a_root = tk.Toplevel(self.root)
        self.b_root = tk.Toplevel(self.root)
        self.a = FirstRunMetadataManagementWindow(self.a_root, host=self.host)
        self.b = FirstRunMetadataManagementWindow(self.b_root, host=self.host)
        self.a._model.insert(0, "gpt-6")

    def clean(self):
        if self.controller._ctx is not None:
            try:
                self.controller.close()
            except Exception:
                pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_second_window_cannot_reject_replace_or_approve_first_review(self):
        self.a.review_save_from_button()
        self.assertIs(self.a._operation, MetadataOperation.SAVE)
        self.assertTrue(self.host.has_pending)
        self.b.reject_from_button()  # Callback attack, even while disabled.
        self.b.review_clear_from_button()
        self.assertIsNone(self.b._operation)
        self.assertTrue(self.host.has_pending)
        self.a.approve_from_button()
        self.assertEqual(self.store.load(), canonical("gpt-6"))
        self.assertTrue(self.controller.ready)
        self.assertFalse(self.host.has_pending)

    def test_nonowner_close_cannot_cancel_review_or_revoke_mutex(self):
        self.a.review_save_from_button()
        self.b.close_from_window()
        self.assertTrue(self.controller.ready)
        self.assertTrue(self.host.has_pending)
        self.a.approve_from_button()
        self.assertEqual(self.store.load(), canonical("gpt-6"))
        self.assertTrue(self.controller.ready)

    def test_stale_ticket_replay_and_wrong_operation_refused(self):
        self.a.review_save_from_button()
        ticket = self.a._ticket
        owner = self.a._owner_token
        self.assertIsInstance(ticket, str)
        self.assertIs(self.host.pending_ui_operation(ticket=ticket, owner=owner),
                      MetadataOperation.SAVE)
        wrong = self.host.approve_ui(ticket=ticket, owner=owner,
                                      operation=MetadataOperation.CLEAR,
                                      human_approved=True, clear_acknowledged=True)
        self.assertIs(wrong.outcome, MetadataCommitOutcome.REFUSED)
        direct = self.host.approve(human_approved=True)
        self.assertIs(direct.outcome, MetadataCommitOutcome.REFUSED)
        self.assertTrue(self.host.has_pending)
        self.a.approve_from_button()
        self.assertEqual(self.store.load(), canonical("gpt-6"))
        replay = self.host.approve_ui(ticket=ticket, owner=owner,
                                      operation=MetadataOperation.SAVE, human_approved=True)
        self.assertIs(replay.outcome, MetadataCommitOutcome.REFUSED)
        self.assertEqual(self.store.load(), canonical("gpt-6"))

    def test_clear_requires_exact_owner_and_explicit_acknowledgement(self):
        self.a.review_clear_from_button()
        ticket = self.a._ticket
        owner = self.a._owner_token
        self.assertIs(self.host.approve_ui(ticket=ticket, owner=owner,
                                            operation=MetadataOperation.CLEAR,
                                            human_approved=True).outcome,
                      MetadataCommitOutcome.REFUSED)
        self.assertEqual(self.store.load(), canonical("gpt-5.6"))
        self.a.approve_from_button()  # No checkbox => still blocked.
        self.assertEqual(self.store.load(), canonical("gpt-5.6"))
        self.a._clear_acknowledged.set(True)
        self.a.approve_from_button()
        self.assertEqual(self.store.load(), ProviderConnectionDocumentV1(connection=None))

    def test_old_owner_cannot_cancel_new_window_review(self):
        old_owner = self.a._owner_token
        self.a.close_from_window()
        self.assertFalse(self.controller.ready)
        review = self.controller.request_reconciliation()
        self.assertTrue(self.controller.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))
        self.b.review_clear_from_button()
        self.assertIs(self.b._operation, MetadataOperation.CLEAR)
        result = self.host.reject_ui(ticket="a" * 32, owner=old_owner)
        self.assertIs(result.outcome, MetadataCommitOutcome.REFUSED)
        self.assertTrue(self.host.has_pending)
        self.b._clear_acknowledged.set(True)
        self.b.approve_from_button()
        self.assertEqual(self.store.load(), ProviderConnectionDocumentV1(connection=None))

    def test_second_host_close_cannot_release_first_host_recovery(self):
        second = TrustedMetadataCommitHost(metadata_path=self.path, mutex=self.host._mutex)
        second_window = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=second)
        self.a.review_save_from_button()
        self.assertTrue(self.host.has_pending)
        second_window.close_from_window()
        self.assertTrue(self.controller.ready)
        self.assertTrue(self.host.has_pending)
        self.a.approve_from_button()
        self.assertEqual(self.store.load(), canonical("gpt-6"))

    def test_closed_panel_callback_does_not_reclaim_host_or_widget(self):
        old_window = self.a
        old_window.close_from_window()
        self.assertTrue(old_window._closed)
        # A retained reference must not regain ownership or touch destroyed Tk widgets.
        old_window.review_save_from_button()
        old_window.approve_from_button()
        old_window.reject_from_button()
        old_window.open_reconciliation_from_button()
        self.assertFalse(self.host.has_pending)
        self.assertFalse(self.controller.ready)
        review = self.controller.request_reconciliation()
        self.assertTrue(self.controller.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))
        self.b.review_clear_from_button()
        self.assertIs(self.b._operation, MetadataOperation.CLEAR)
        self.b._clear_acknowledged.set(True)
        self.b.approve_from_button()
        self.assertEqual(self.store.load(), ProviderConnectionDocumentV1(connection=None))

    def test_exact_ticket_but_wrong_window_owner_refused_without_consuming(self):
        self.a.review_save_from_button()
        ticket = self.a._ticket
        self.assertIsNone(self.b._owner_token)
        result = self.host.approve_ui(ticket=ticket, owner=self.b._owner_token,
                                      operation=MetadataOperation.SAVE, human_approved=True)
        self.assertIs(result.outcome, MetadataCommitOutcome.REFUSED)
        self.assertTrue(self.host.has_pending)
        self.assertEqual(self.store.load(), canonical("gpt-5.6"))

    def test_widget_construction_failure_does_not_acquire_owner(self):
        from unittest.mock import patch
        root = tk.Toplevel(self.root)
        with patch("nayeon.desktop_alpha.first_run_metadata_management_window.tk.Label",
                   side_effect=RuntimeError("synthetic UI constructor failure")):
            with self.assertRaises(RuntimeError):
                FirstRunMetadataManagementWindow(root, host=self.host)
        # The original window retains its ownership; no secondary claim.
        self.assertTrue(self.host.has_ui_owner(owner=self.a._owner_token))
        self.a.review_save_from_button()
        self.a.approve_from_button()
        self.assertEqual(self.store.load(), canonical("gpt-6"))

    def test_two_host_instances_cannot_swap_effect_after_verified_first(self):
        other = TrustedMetadataCommitHost(metadata_path=self.path, mutex=self.host._mutex)
        other_a = FirstRunMetadataManagementWindow(tk.Toplevel(self.root), host=other)
        other_a.review_clear_from_button()
        self.a.review_save_from_button()
        self.a.approve_from_button()
        self.assertEqual(self.store.load(), canonical("gpt-6"))
        other_a._clear_acknowledged.set(True)
        other_a.approve_from_button()
        self.assertEqual(self.store.load(), canonical("gpt-6"))
