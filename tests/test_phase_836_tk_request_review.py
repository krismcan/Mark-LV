"""Phase 8.36 native Windows Tk integration, no network or provider."""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
import unittest
from unittest import mock

from nayeon.desktop_alpha import application, workspace_window
from nayeon.desktop_alpha.offline_request_review import (
    DISCLOSURE, RECEIPT_TEXT, ReviewState,
)
from tests.phase_831_fake_session_support import ProhibitedEffects


@unittest.skipUnless(os.name == "nt", "Authoritative native Windows Tk required")
class Phase836NativeReviewTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self._close)
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.effects = ProhibitedEffects()
        self.addCleanup(self.effects.assert_clean)
        self.guards = []
        for ctx in (*self.effects.patchers(), *self.effects.native_patchers(),
                    mock.patch.object(application.OfflineWorkspaceApplication,
                                      "_bootstrap_readonly_presentation", return_value=None)):
            ctx.__enter__()
            self.guards.append(ctx)
        self.addCleanup(self._unpatch)
        self.app = application.OfflineWorkspaceApplication(self.root)
        self.view = self.app._active_view
        self.view.entry.insert(0, "Hello Nayeon")

    def _unpatch(self):
        for p in reversed(self.guards):
            p.__exit__(None, None, None)

    def _close(self):
        if hasattr(self, "app"):
            self.app.close()
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass
        self.assertEqual(self.errors, [])

    def arm(self):
        self.assertTrue(self.view._begin_request_review())
        self.assertIs(self.view._request_owner.state, ReviewState.ARMED)
        self.assertTrue(self.view.request_confirm_button.instate(("!disabled",)))

    def test_complete_offline_receipt_and_non_mutation(self):
        before = self.app._conversation.snapshot
        self.arm()
        self.assertIn("Hello Nayeon", self.view.request_disclosure.cget("text"))
        self.assertIn(DISCLOSURE, self.view.request_disclosure.cget("text"))
        self.assertTrue(self.view._confirm_request_review())
        self.assertEqual(self.view.request_status.cget("text"), RECEIPT_TEXT)
        self.assertEqual(self.app._conversation.snapshot, before)
        self.assertEqual(len(before.entries), 0)
        self.assertIsNone(self.view._request_ticket)
        self.assertFalse(self.view._confirm_request_review())

    def test_text_change_refuses_stale_prompt(self):
        self.arm()
        self.view.entry.insert("end", " changed")
        self.assertFalse(self.view._confirm_request_review())
        self.assertIsNone(self.view._request_ticket)

    def test_user_cancel_revokes_prompt(self):
        self.arm()
        self.assertTrue(self.view._cancel_request_review())
        self.assertFalse(self.view._confirm_request_review())
        self.assertTrue(self.view.request_confirm_button.instate(("disabled",)))

    def test_nested_confirm_during_button_enable_before_effect(self):
        original = ttk.Button.configure
        called = []
        def injected(widget,cnf=None,**kwargs):
            if widget is self.view.request_confirm_button and kwargs.get("state")=="normal":
                called.append(self.view._confirm_request_review())
            return original(widget,cnf,**kwargs)
        with mock.patch.object(ttk.Button,"configure",new=injected):
            self.assertFalse(self.view._begin_request_review())
        self.assertEqual(called,[False])
        self.assertIsNone(self.view._request_ticket)
        self.assertTrue(self.view.request_confirm_button.instate(("disabled",)))

    def test_nested_confirm_during_button_enable_after_effect(self):
        original = ttk.Button.configure
        called = []
        def injected(widget,cnf=None,**kwargs):
            result=original(widget,cnf,**kwargs)
            if widget is self.view.request_confirm_button and kwargs.get("state")=="normal":
                called.append(self.view._confirm_request_review())
            return result
        with mock.patch.object(ttk.Button,"configure",new=injected):
            self.assertFalse(self.view._begin_request_review())
        self.assertEqual(called,[False])
        self.assertIsNone(self.view._request_ticket)

    def test_enable_succeeds_but_control_remains_disabled(self):
        original=ttk.Button.configure
        def injected(widget,cnf=None,**kwargs):
            if widget is self.view.request_confirm_button and kwargs.get("state")=="normal":
                return original(widget,cnf,state="disabled")
            return original(widget,cnf,**kwargs)
        with mock.patch.object(ttk.Button,"configure",new=injected):
            self.assertFalse(self.view._begin_request_review())
        self.assertIsNone(self.view._request_ticket)
        self.assertTrue(self.view.request_confirm_button.instate(("disabled",)))

    def test_late_entry_query_disables_before_final_instate(self):
        original=ttk.Entry.get
        fired=[]
        def injected(widget):
            result=original(widget)
            if widget is self.view.entry and self.view._request_owner.state is ReviewState.ENABLING and not fired:
                fired.append(True)
                self.view.request_confirm_button.configure(state="disabled")
            return result
        with mock.patch.object(ttk.Entry,"get",new=injected):
            self.assertFalse(self.view._begin_request_review())
        self.assertEqual(fired,[True])
        self.assertIsNone(self.view._request_ticket)

    def test_reply_worker_admission_during_last_instate_revokes(self):
        original = ttk.Button.instate
        fired = []
        def injected(button, statespec, callback=None):
            if button is self.view.request_confirm_button and not fired:
                fired.append(True)
                self.view.reply_button.invoke()
            return original(button, statespec, callback)
        with mock.patch.object(ttk.Button, "instate", new=injected):
            self.assertFalse(self.view._begin_request_review())
        self.assertEqual(fired, [True])
        self.assertIsNone(self.view._request_ticket)
        worker = self.app._reply_owner._thread
        if worker is not None and worker.ident is not None:
            worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertTrue(self.app.retry_reply_retirement())

    def test_receipt_cleared_even_if_following_button_disable_fails(self):
        self.arm()
        original_label = ttk.Label.configure
        original_button = ttk.Button.configure
        injected_status = []
        disable_calls = []
        def status(widget, cnf=None, **kwargs):
            result = original_label(widget, cnf, **kwargs)
            if (widget is self.view.request_status
                    and kwargs.get("text") == RECEIPT_TEXT
                    and not injected_status):
                injected_status.append(True)
                self.view._cancel_request_review()
            return result
        def button(widget, cnf=None, **kwargs):
            value = original_button(widget, cnf, **kwargs)
            if (widget is self.view.request_confirm_button
                    and kwargs.get("state") == "disabled"):
                disable_calls.append(True)
                if len(disable_calls) == 2:
                    raise tk.TclError("after effect cleanup fault")
            return value
        with mock.patch.object(ttk.Label, "configure", new=status), \
             mock.patch.object(ttk.Button, "configure", new=button):
            self.assertFalse(self.view._confirm_request_review())
        self.assertEqual(injected_status, [True])
        self.assertGreaterEqual(len(disable_calls), 2)
        self.assertNotEqual(self.view.request_status.cget("text"), RECEIPT_TEXT)

    def test_nested_reset_during_status_publication_wins(self):
        self.arm()
        original=ttk.Label.configure
        fired=[]
        def injected(widget,cnf=None,**kwargs):
            result=original(widget,cnf,**kwargs)
            if widget is self.view.request_status and kwargs.get("text")==RECEIPT_TEXT and not fired:
                fired.append(True)
                self.view._cancel_request_review()
            return result
        with mock.patch.object(ttk.Label,"configure",new=injected):
            self.assertFalse(self.view._confirm_request_review())
        self.assertEqual(fired,[True])
        self.assertNotEqual(self.view.request_status.cget("text"),RECEIPT_TEXT)

    def test_save_offline_revokes_review(self):
        self.arm()
        self.view.send_button.invoke()
        self.assertIsNone(self.view._request_ticket)
        self.assertEqual(len(self.app._conversation.snapshot.entries),2)

    def test_reset_review_revokes_prompt(self):
        self.arm()
        self.view.clear_button.invoke()
        self.assertIsNone(self.view._request_ticket)
        self.assertFalse(self.view._confirm_request_review())

    def test_navigation_revokes_and_closes_old_review(self):
        self.arm()
        old=self.view
        self.app.show_connection()
        self.assertIs(old._request_owner.state,ReviewState.CLOSED)
        self.app.show_conversation()
        self.assertIsNot(old,self.app._active_view)

    def test_expired_ticket_refused(self):
        self.arm()
        deadline=self.view._request_owner._deadline
        with mock.patch.object(workspace_window.time,"monotonic_ns",return_value=deadline*1_000_000):
            self.assertFalse(self.view._confirm_request_review())
        self.assertIsNone(self.view._request_ticket)

if __name__=="__main__":
    unittest.main()
