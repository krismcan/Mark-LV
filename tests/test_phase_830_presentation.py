"""Adversarial native Tk review/save proof; fixture never opens a real profile."""
from __future__ import annotations

import os
import tkinter as tk
import unittest
from unittest import mock

from tests import test_phase_830_application as storage_fixture
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.presentation_profile_owner import ProfileUnverified


@unittest.skipUnless(os.name == "nt", "Windows native Tk required")
class Phase830PresentationTests(unittest.TestCase):
    def setUp(self):
        storage_fixture.Phase830ProductionAdmissionTests.setUp(self)
        self.root = tk.Tk()
        self.callback_exceptions = []
        self.root.report_callback_exception = (
            lambda *args: self.callback_exceptions.append(args[0].__name__))
        self.addCleanup(self._cleanup_root)
        self.root.withdraw()
        self.app = OfflineWorkspaceApplication(self.root)
        self.app.show_settings()
        self.view = self.app._active_view

    def _cleanup_root(self):
        if hasattr(self, "app"):
            self.app.close()
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def tearDown(self):
        self.assertEqual(self.callback_exceptions, [],
                         "Unexpected Tk callback exception escaped")

    def _review(self, name):
        self.view.assistant_name.set(name)
        self.view.review_button.invoke()
        self.assertIsNotNone(self.app._pending)

    def test_navigation_reentrant_during_save_revokes_consent(self):
        self._review("Synthetic Reentrant")
        owner = self.app._profile_owner
        original = owner.save
        def reentrant(receipt):
            self.app.show_connection()  # Busy navigation must revoke owner.
            return original(receipt)
        with mock.patch.object(owner, "save", side_effect=reentrant) as hook:
            self.view.save_button.invoke()
            hook.assert_called_once()
        self.assertFalse(self.profile_leaf.exists())
        self.assertEqual(self.app._published_document.assistant.display_name, "Nayeon")
        self.assertIsNone(self.app._pending)

    def test_unverified_postwrite_never_publishes_identity(self):
        self._review("Uncertain Synthetic")
        owner = self.app._profile_owner
        original = owner.save
        def uncertain(receipt):
            original(receipt)
            raise ProfileUnverified("Synthetic uncertainty")
        with mock.patch.object(owner, "save", side_effect=uncertain) as hook:
            self.view.save_button.invoke()
            hook.assert_called_once()
        self.assertTrue(self.profile_leaf.exists())
        self.assertEqual(self.app._published_document.assistant.display_name, "Nayeon")
        self.assertEqual(self.app.workspace.name_label.cget("text"), "Nayeon")
        self.assertIn("unverified", self.view.status_label.cget("text"))

    def test_native_unlock_release_failure_after_replace_never_publishes_ui(self):
        from nayeon.desktop_alpha.presentation_profile_owner import _Win32
        self._review("Native Release Synthetic")
        original_init = _Win32.__init__
        calls = []
        def init_failure(native):
            original_init(native)
            def refuse_unlock(*args):
                calls.append(args)
                return False
            native.unlock_file = refuse_unlock
        with mock.patch.object(_Win32, "__init__", init_failure):
            self.view.save_button.invoke()
        self.assertEqual(len(calls), 1)
        self.assertTrue(self.profile_leaf.exists())
        self.assertEqual(self.app._published_document.assistant.display_name, "Nayeon")
        self.assertEqual(self.app.workspace.name_label.cget("text"), "Nayeon")
        self.assertIn("unverified", self.view.status_label.cget("text").lower())
        self.assertIsNone(self.app._pending)
        self.assertEqual(str(self.view.save_button.cget("state")), "disabled")

    def test_destruction_during_save_cannot_publish_or_write(self):
        self._review("Destroyed Synthetic")
        owner = self.app._profile_owner
        original = owner.save
        def destroy_then_save(receipt):
            self.app.close()
            return original(receipt)
        with mock.patch.object(owner, "save", side_effect=destroy_then_save) as hook:
            self.view.save_button.invoke()
            hook.assert_called_once()
        self.assertFalse(self.profile_leaf.exists())
        self.assertEqual(self.app._published_document.assistant.display_name, "Nayeon")

    def test_invalid_draft_does_not_issue_storage_review(self):
        self.view.assistant_name.set("  invalid surrounding spaces  ")
        owner = self.app._profile_owner
        with mock.patch.object(owner, "review_save", wraps=owner.review_save) as review:
            self.view.review_button.invoke()
            review.assert_not_called()
        self.assertIsNone(self.app._pending)
        self.assertFalse(self.app_dir.exists())

    def test_review_only_and_cancel_have_zero_storage_effects(self):
        self._review("Review Only Synthetic")
        self.assertFalse(self.app_dir.exists())
        self.view.cancel_button.invoke()
        self.assertFalse(self.app_dir.exists())
        self.assertEqual(self.app._active_view.winfo_name(), "conversation_view")

    def test_old_settings_callbacks_cannot_steal_successor(self):
        self._review("Old Synthetic")
        old, token, generation = (
            self.view, self.app._active_token, self.app._generation)
        self.app.show_conversation()
        self.app.show_settings()
        successor = self.app._active_view
        self.app._save(old, token, generation)
        self.assertFalse(self.app_dir.exists())
        successor.assistant_name.set("Successor Synthetic")
        successor.review_button.invoke()
        successor.save_button.invoke()
        self.assertEqual(self.app._published_document.assistant.display_name,
                         "Successor Synthetic")
        self.app._save(old, token, generation)
        self.assertEqual(self.app.workspace.name_label.cget("text"),
                         "Successor Synthetic")

    def test_duplicate_save_uses_exactly_one_storage_receipt(self):
        self._review("Once Synthetic")
        owner = self.app._profile_owner
        view, token, generation = (
            self.view, self.app._active_token, self.app._generation)
        with mock.patch.object(owner, "save", wraps=owner.save) as hook:
            self.view.save_button.invoke()
            self.view.save_button.invoke()
            self.app._save(view, token, generation)
            hook.assert_called_once()
        self.assertEqual(self.app._published_document.assistant.display_name,
                         "Once Synthetic")

    def test_destroy_during_human_receipt_issuance_cannot_write(self):
        self._review("Receipt Synthetic")
        owner = self.app._profile_owner
        original = owner.review_save
        def destroy_then_issue(edit, document):
            self.app.close()
            return original(edit, document)
        with mock.patch.object(owner, "review_save", side_effect=destroy_then_issue) as hook:
            self.view.save_button.invoke()
            hook.assert_called_once()
        self.assertFalse(self.profile_leaf.exists())
        self.assertEqual(self.app._published_document.assistant.display_name, "Nayeon")

    def test_mapped_mouse_navigation_and_return(self):
        self.root.deiconify()
        self.root.update()
        try:
            button = self.app.workspace.navigation_buttons[2]
            button.event_generate("<ButtonPress-1>", x=8, y=8)
            button.event_generate("<ButtonRelease-1>", x=8, y=8)
            self.root.update()
            self.assertEqual(self.app._active_view.winfo_name(), "connection_view")
            back = self.app._active_view.back_button
            back.event_generate("<ButtonPress-1>", x=8, y=8)
            back.event_generate("<ButtonRelease-1>", x=8, y=8)
            self.root.update()
            self.assertEqual(self.app._active_view.winfo_name(), "conversation_view")
            self.assertFalse(self.app_dir.exists())
        finally:
            if self.root.winfo_exists():
                self.root.withdraw()


if __name__ == "__main__":
    unittest.main()
