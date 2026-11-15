"""P229 additive *current-source* GUI contract, NOT a replacement for P86/P87.

P133 intentionally added a third explicit offline setup button after P86/P87
historical two-button tests. No old assertion is edited or silently skipped.
Real Tk on Windows; only literal synthetic, non-secret values; no credential,
provider, subprocess, security ACL or production service effects.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import unittest
from unittest import mock

from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.workspace_window import ConnectionWindow


class CurrentConnectionViewRevision(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.close)
        with mock.patch.object(OfflineWorkspaceApplication,
                               "_bootstrap_readonly_presentation"):
            self.app=OfflineWorkspaceApplication(self.root)
        self.app.show_connection()
        self.view=self.app._active_view

    def close(self):
        app=getattr(self,"app",None)
        if app is not None:
            try: app.close()
            except tk.TclError: pass
        try:self.root.destroy()
        except tk.TclError:pass

    def buttons(self):
        return [x for x in self.view.winfo_children()
                if isinstance(x,ttk.Button)]

    def test_actual_current_three_explicit_buttons_and_status_unknown(self):
        self.assertIs(type(self.view),ConnectionWindow)
        self.assertEqual(len(self.buttons()),3)
        self.assertEqual(self.view.back_button.cget("text"),"Back to Conversation")
        self.assertEqual(self.view.manage_button.cget("text"),
                         "Manage provider (offline preview)")
        self.assertEqual(self.view.local_byok_button.cget("text"),
                         "Open local key setup (offline, not connected)")
        self.assertIn("NOT OBSERVED",self.view.pending_custody_label.cget("text"))
        self.assertIn("no trusted pending-key observation",
                      self.view.pending_custody_label.cget("text"))
        self.assertIsNone(self.app._connection)
        self.assertIsNone(self.app._connection_coordinator)
        self.assertIsNone(self.app._connection_test_harness)
        self.assertFalse(self.view.NativeEffectEnabled
                         if hasattr(self.view,"NativeEffectEnabled") else False)

    def test_default_navigation_has_no_local_launch_or_implicit_refresh(self):
        from nayeon.desktop_alpha.local_byok_launch_bridge import LocalByokLaunchBridge
        with mock.patch.object(LocalByokLaunchBridge,"launch",
                               side_effect=AssertionError("UNREQUESTED_LOCAL_PROCESS")) as launch:
            self.app.show_conversation()
            self.app.show_connection()
            self.assertEqual(len(self.buttons()),3)
            self.assertIsNone(self.app._connection)
            self.assertIn("NOT OBSERVED",
                          self.view.pending_custody_label.cget("text"))
            launch.assert_not_called()

    def test_exact_offline_setup_action_is_separate_and_explicit(self):
        with mock.patch.object(OfflineWorkspaceApplication,"_open_local_byok",
                               autospec=True) as action:
            self.app.show_conversation()
            self.app.show_connection()
            action.assert_not_called()
            self.view.local_byok_button.invoke()
            action.assert_called_once()
        self.assertIsNone(self.app._connection)
        self.assertIn("NOT OBSERVED",
                      self.view.pending_custody_label.cget("text"))

    def test_current_offline_ui_never_reports_validated_key(self):
        text=(self.view.pending_custody_label.cget("text")+" "+
              self.view.status_label.cget("text")).lower()
        for claim in ("validated successfully","connected successfully",
                      "credential stored successfully","provider enabled"):
            self.assertNotIn(claim,text)
        self.assertEqual(len(self.buttons()),3)
        self.assertIsNone(self.app._connection)


if __name__=="__main__":
    unittest.main()
