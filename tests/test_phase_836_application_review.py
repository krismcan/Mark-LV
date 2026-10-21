"""Phase 8.36 app composition: no provider capabilities or hidden worker admission."""
from __future__ import annotations
import os
import tkinter as tk
from tkinter import ttk
import unittest
from unittest import mock

from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.offline_request_review import ReviewState
from nayeon.desktop_alpha import workspace_window
from tests.phase_831_fake_session_support import ProhibitedEffects


@unittest.skipUnless(os.name=="nt","Native Windows required")
class Phase836ApplicationReviewTests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk()
        self.root.withdraw()
        self.errors=[]
        self.root.report_callback_exception=lambda *args:self.errors.append(args)
        self.effects=ProhibitedEffects()
        self.guards=[]
        for x in (*self.effects.patchers(),*self.effects.native_patchers(),
                  mock.patch.object(OfflineWorkspaceApplication,
                      "_bootstrap_readonly_presentation",return_value=None)):
            x.__enter__()
            self.guards.append(x)
        self.addCleanup(self._cleanup)
        self.app=OfflineWorkspaceApplication(self.root)
        self.view=self.app._active_view
        self.view.entry.insert(0,"safe offline text")

    def _cleanup(self):
        if hasattr(self,"app"):
            self.app.close()
        try:
            if self.root.winfo_exists():self.root.destroy()
        except tk.TclError:
            pass
        for x in reversed(self.guards):x.__exit__(None,None,None)
        self.effects.assert_clean()
        self.assertEqual(self.errors,[])

    def test_offline_button_is_real_and_not_connected(self):
        self.assertEqual(self.view.request_review_button.cget("text"),"Review offline prompt")
        self.assertEqual(str(self.view.request_review_button.cget("state")),"normal")
        before=self.app._conversation.snapshot
        self.view.request_review_button.invoke()
        self.assertIs(self.view._request_owner.state,ReviewState.ARMED)
        self.view.request_confirm_button.invoke()
        self.assertIs(self.app._conversation.snapshot,before)
        self.assertEqual(len(before.entries),0)

    def test_reply_busy_blocks_request_admission(self):
        self.app._reply_busy=True
        try:
            self.assertFalse(self.view._begin_request_review())
            self.assertIsNone(self.view._request_ticket)
        finally:
            self.app._reply_busy=False

    def test_nonretired_worker_blocks_admission(self):
        with mock.patch.object(type(self.app._reply_owner),"has_worker",
                               new_callable=mock.PropertyMock,return_value=True):
            self.assertFalse(self.view._begin_request_review())
        self.assertIsNone(self.view._request_ticket)

    def test_old_view_callback_cannot_issue_new_ticket(self):
        old=self.view
        self.app.show_connection()
        self.app.show_conversation()
        self.assertFalse(old._begin_request_review())
        self.assertIsNone(old._request_ticket)

    def test_direct_model_ready_claim_is_absent(self):
        for value in (self.app,self.view,self.view._request_owner):
            for key in ("_provider_connection","_provider_service","_connection_store",
                        "_openai_provider","_secret_resolver","_network_client"):
                self.assertFalse(hasattr(value,key))
        self.assertNotIn("API VERIFIED",self.view.request_disclosure.cget("text"))
        self.view.request_review_button.invoke()
        self.assertIn("MODEL NOT CONNECTED",
                      self.view.request_disclosure.cget("text"))

    def test_callback_during_last_widget_check_refuses_arm(self):
        original=ttk.Button.instate
        fired=[]
        def injected(button,statespec,callback=None):
            if button is self.view.request_confirm_button and not fired:
                fired.append(True)
                self.view._cancel_request_review()
            return original(button,statespec,callback)
        with mock.patch.object(ttk.Button,"instate",new=injected):
            self.assertFalse(self.view._begin_request_review())
        self.assertEqual(fired,[True])
        self.assertIsNone(self.view._request_ticket)

    def test_after_effect_enabled_throw_refuses_arm(self):
        original=ttk.Button.configure
        def injected(button,cnf=None,**kwargs):
            val=original(button,cnf,**kwargs)
            if button is self.view.request_confirm_button and kwargs.get("state")=="normal":
                raise tk.TclError("injected after effect")
            return val
        with mock.patch.object(ttk.Button,"configure",new=injected):
            self.assertFalse(self.view._begin_request_review())
        self.assertIsNone(self.view._request_ticket)

    def test_no_readable_secrets_or_ai_in_receipt(self):
        self.assertTrue(self.view._begin_request_review())
        self.assertTrue(self.view._confirm_request_review())
        self.assertEqual(self.view._request_owner.state,ReviewState.IDLE)
        self.assertEqual(len(self.app._conversation.snapshot.entries),0)

if __name__=="__main__":
    unittest.main()
