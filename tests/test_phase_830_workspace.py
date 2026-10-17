"""Phase 8.30 native Tk acceptance against disposable synthetic storage ONLY."""
from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
import unittest
import weakref
from unittest import mock

from tests import test_phase_830_application as storage_fixture
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.controller import ChatOutcome


_retired_tk_roots = []  # weak refs only; no change to historical product


@unittest.skipUnless(os.name == "nt", "Native Windows Tk proof required")
class Phase830WorkspaceTests(unittest.TestCase):
    def setUp(self):
        # Never resolve or open the actual product-known-folder location.
        storage_fixture.Phase830ProductionAdmissionTests.setUp(self)
        self.root = tk.Tk()
        _retired_tk_roots.append(weakref.ref(self.root))
        self.addCleanup(self._cleanup_root)
        self.root.withdraw()
        self.app = OfflineWorkspaceApplication(self.root)
        self.assertEqual(str(self.app._active_view.winfo_name()), "conversation_view")

    def _cleanup_root(self):
        if hasattr(self, "app"):
            self.app.close()
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def test_conversation_and_connection_navigation_do_not_touch_storage(self):
        from nayeon.desktop_alpha import presentation_profile_owner as storage
        with mock.patch.object(storage, "_resolve_local_app_data",
                               side_effect=AssertionError("NO_STORAGE_READ")) as forbidden:
            view = self.app._active_view
            view.entry.insert(0, "open notepad")
            view.send_button.invoke()
            self.assertEqual(self.app.controller.send("open calculator").outcome,
                             ChatOutcome.PREVIEW)
            self.app.workspace.navigation_buttons[2].invoke()
            self.assertEqual(self.app._active_view.winfo_name(), "connection_view")
            self.assertIn("Not observed", str(
                self.app._active_view.winfo_children()[1].cget("text")
            ))
            self.app._active_view.back_button.invoke()
            self.assertEqual(self.app._active_view.winfo_name(), "conversation_view")
            forbidden.assert_not_called()
        self.assertFalse(self.app_dir.exists())

    def test_human_review_then_save_and_reopen_verified_profile(self):
        self.app.workspace.navigation_buttons[1].invoke()
        view = self.app._active_view
        self.assertEqual(view.winfo_name(), "presentation_view")
        self.assertFalse(self.app_dir.exists())
        self.assertIsNone(self.app._pending)
        view.assistant_name.set("Synthetic Nayeon")
        view.wake_name.set("Hey Synthetic")
        self.assertFalse(self.app_dir.exists())
        self.assertEqual(str(view.save_button.cget("state")), "disabled")
        view.review_button.invoke()
        self.assertIsNotNone(self.app._pending)
        self.assertFalse(self.app_dir.exists())
        self.assertEqual(str(view.save_button.cget("state")), "normal")
        view.save_button.invoke()
        self.assertIsNone(self.app._pending)
        self.assertTrue(self.profile_leaf.exists())
        self.assertEqual(self.app._published_document.assistant.display_name,
                         "Synthetic Nayeon")
        self.assertEqual(self.app.workspace.name_label.cget("text"),
                         "Synthetic Nayeon")
        self.app.show_conversation()
        self.app.show_settings()
        again = self.app._active_view
        self.assertEqual(again.assistant_name.get(), "Synthetic Nayeon")
        self.assertEqual(again.wake_name.get(), "Hey Synthetic")

    def test_changed_draft_invalidates_review_and_cancel_never_creates_storage(self):
        self.app.show_settings()
        view = self.app._active_view
        view.assistant_name.set("Synthetic First")
        view.review_button.invoke()
        self.assertIsNotNone(self.app._pending)
        view.assistant_name.set("Synthetic Changed")
        self.assertIsNone(self.app._pending)
        self.assertEqual(str(view.save_button.cget("state")), "disabled")
        self.app.show_conversation()
        self.assertFalse(self.app_dir.exists())

    def test_second_launch_reads_verified_saved_presentation_without_write(self):
        from nayeon.config.persistence import PresentationConfigurationFileStore
        self.app.close()
        native_fixture = storage_fixture.Phase830ProductionAdmissionTests
        native_fixture._private_directory(self, self.app_dir)
        native_fixture._private_directory(self, self.profile_dir)
        wanted = storage_fixture.Phase830ProductionAdmissionTests.document("Restarted Synthetic")
        PresentationConfigurationFileStore(self.profile_leaf).save(wanted)
        before = self.profile_leaf.read_bytes()
        self.root = tk.Tk()
        _retired_tk_roots.append(weakref.ref(self.root))
        self.root.withdraw()
        self.app = OfflineWorkspaceApplication(self.root)
        self.assertEqual(self.app.workspace.name_label.cget("text"), "Restarted Synthetic")
        self.assertEqual(self.app._published_document, wanted)
        self.assertFalse(self.sidecar.exists())
        self.assertEqual(self.profile_leaf.read_bytes(), before)

    def test_invalid_existing_profile_is_not_silently_treated_as_default(self):
        self.app.close()
        native_fixture = storage_fixture.Phase830ProductionAdmissionTests
        native_fixture._private_directory(self, self.app_dir)
        native_fixture._private_directory(self, self.profile_dir)
        self.profile_leaf.write_bytes(b'{"invalid":true}')
        self.root = tk.Tk()
        _retired_tk_roots.append(weakref.ref(self.root))
        self.root.withdraw()
        self.app = OfflineWorkspaceApplication(self.root)
        self.assertIn("unavailable", self.app.workspace.profile_status.cget("text").lower())
        self.assertEqual(self.app.workspace.name_label.cget("text"), "Nayeon")
        self.assertFalse(self.sidecar.exists())

    def test_mapped_return_event_review_and_save(self):
        # Genuine Tk event dispatch, but destination remains the private fixture.
        self.root.deiconify()
        self.root.update()
        try:
            settings = self.app.workspace.navigation_buttons[1]
            settings.focus_force()
            settings.event_generate("<Return>")
            self.root.update()
            view = self.app._active_view
            self.assertEqual(view.winfo_name(), "presentation_view")
            view.assistant_name.set("Keyboard Synthetic")
            view.review_button.focus_force()
            view.review_button.event_generate("<Return>")
            self.root.update()
            self.assertIsNotNone(self.app._pending)
            self.assertFalse(self.app_dir.exists())
            view.save_button.focus_force()
            view.save_button.event_generate("<Return>")
            self.root.update()
            self.assertTrue(self.profile_leaf.exists())
            self.assertEqual(self.app._published_document.assistant.display_name,
                             "Keyboard Synthetic")
        finally:
            if self.root.winfo_exists():
                self.root.withdraw()

    def test_stale_settings_callback_after_navigation_cannot_save(self):
        self.app.show_settings()
        old = self.app._active_view
        token, generation = self.app._active_token, self.app._generation
        old.review_button.invoke()
        self.assertIsNotNone(self.app._pending)
        self.app.show_connection()
        self.app._save(old, token, generation)
        self.assertFalse(self.app_dir.exists())
        self.assertEqual(self.app._active_view.winfo_name(), "connection_view")

    def test_root_close_revokes_review_before_write(self):
        self.app.show_settings()
        old = self.app._active_view
        token, generation = self.app._active_token, self.app._generation
        old.review_button.invoke()
        self.assertIsNotNone(self.app._pending)
        self.app.close()
        self.app._save(old, token, generation)
        self.assertFalse(self.app_dir.exists())


def tearDownModule():
    """Collect retired 8.30 Tk interpreters on their creating UI thread."""
    import gc
    import threading
    if threading.current_thread() is not threading.main_thread():
        raise AssertionError("Phase 8.30 Tk cleanup must run on its UI thread")
    gc.collect()
    survivors = sum(ref() is not None for ref in _retired_tk_roots)
    if survivors:
        raise AssertionError(f"{survivors} retired 8.30 Tk roots still live")
    _retired_tk_roots.clear()


if __name__ == "__main__":
    unittest.main()
