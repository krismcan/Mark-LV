"""Display-free application admission and native reset-fault assurance."""
import os
import threading
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
import unittest
from unittest import mock

from nayeon.desktop_alpha import application
from nayeon.desktop_alpha.conversation_session import SessionSnapshot
from tests.test_phase_837_draft_tk import DraftWindowHarness


class DraftApplicationTests(unittest.TestCase):
    def setUp(self):
        self.h = DraftWindowHarness(self)
        self.view = self.h.view
        self.app = object.__new__(application.OfflineWorkspaceApplication)
        app = self.app
        app._creator_thread = threading.get_ident()
        app._closed = app._busy = app._reply_busy = app._reply_closing = False
        app._root_alive = True
        app.root = object()
        app._active_view = self.view
        app._active_token = object()
        app._generation = 7
        app._conversation_view = object()
        app._conversation_root = object()
        app._conversation = SimpleNamespace(snapshot=self.h.snapshot)
        app._reply_ticket = app._reply_navigation = None
        app._reply_owner = SimpleNamespace(has_worker=False, poisoned=False)
        app._current = mock.Mock(return_value=True)

    def snapshot(self):
        return self.app._request_review_snapshot(
            self.view, self.app._active_token, 7)

    def test_existing_snapshot_callback_is_truthful_without_effects(self):
        self.assertIs(self.snapshot(), self.h.snapshot)
        self.view._request_snapshot = self.snapshot
        self.assertTrue(self.view._begin_draft())
        self.assertTrue(self.view._confirm_draft())
        self.assertEqual(self.app._conversation.snapshot.entries, ())
        self.assertFalse(self.app._reply_owner.has_worker)

    def test_worker_busy_ticket_and_lifetime_refusals_before_tcl(self):
        for attribute, value in (("_busy", True), ("_reply_busy", True),
                                 ("_reply_closing", True), ("_closed", True),
                                 ("_root_alive", False),
                                 ("_reply_ticket", object()),
                                 ("_conversation_view", None)):
            with self.subTest(attribute=attribute):
                previous = getattr(self.app, attribute)
                setattr(self.app, attribute, value)
                self.app._current.reset_mock()
                self.assertIsNone(self.snapshot())
                self.app._current.assert_not_called()
                setattr(self.app, attribute, previous)
        self.app._reply_owner.has_worker = True
        self.assertIsNone(self.snapshot())

    def test_reentrant_current_rechecks_worker_snapshot_and_identity(self):
        app = self.app
        mutations = (
            lambda: setattr(app._reply_owner, "has_worker", True),
            lambda: setattr(app, "_reply_busy", True),
            lambda: setattr(app, "_busy", True),
            lambda: setattr(app, "_closed", True),
            lambda: setattr(app, "_root_alive", False),
            lambda: setattr(app, "_active_view", object()),
            lambda: setattr(app, "_active_token", object()),
            lambda: setattr(app, "_generation", 8),
            lambda: setattr(app, "_conversation_view", None),
            lambda: setattr(app, "_conversation_view", object()),
            lambda: setattr(app, "_conversation_root", object()),
            lambda: setattr(app, "root", object()),
            lambda: setattr(app, "_conversation", SimpleNamespace(snapshot=self.h.snapshot)),
            lambda: setattr(app._conversation, "snapshot",
                            SessionSnapshot(object(), 2, 1, (), 0, False)),
        )
        for mutation in mutations:
            before = dict(app.__dict__)
            original_snapshot = app._conversation.snapshot
            original_worker = app._reply_owner.has_worker
            def reenter(*args):
                mutation()
                return True
            app._current = mock.Mock(side_effect=reenter)
            token = app._active_token
            with self.subTest(mutation=mutations.index(mutation)):
                self.assertIsNone(app._request_review_snapshot(self.view, token, 7))
            app.__dict__.update(before)
            app._conversation.snapshot = original_snapshot
            app._reply_owner.has_worker = original_worker

    def test_closed_snapshot_is_never_offered(self):
        self.app._conversation.snapshot = SessionSnapshot(object(), 1, 0, (), 0, True)
        self.assertIsNone(self.snapshot())

    def test_actual_reply_ingress_revokes_before_test_owned_worker_start(self):
        app = self.app
        app._reply_serial = 0
        app.root = object()
        app._conversation_now = lambda: 100
        app._reply_eligible = mock.Mock(return_value=True)
        app._reply_release_anchor = mock.Mock()
        app._reply_flush_invalidation = mock.Mock()
        app._reply_finish_deferred = mock.Mock()
        app._reply_schedule_fault = mock.Mock()
        app.workspace = SimpleNamespace(start_reply_poll=mock.Mock(return_value=True))
        app._reply_poll = app._reply_schedule_fault
        started = []
        def start(candidate, **kwargs):
            # No real Thread is constructed. This fake checks the exact point
            # where the sealed application would admit its simulation worker.
            self.assertIsNone(self.view._draft_ticket)
            self.assertIsNone(self.view._draft_receipt)
            started.append(candidate)
            app._reply_owner.has_worker = True
            return object()
        app._reply_owner.bind_context = mock.Mock(return_value=True)
        app._reply_owner.start = start
        self.assertTrue(self.view._begin_draft())
        with mock.patch.object(application, "_REPLY_LIFETIMES", {}), \
             mock.patch.object(threading.Thread, "start",
                               side_effect=AssertionError("real worker prohibited")):
            app._conversation_reply(self.view, app._active_token, 7)
        self.assertEqual(started, ["literal live prompt"])
        self.assertTrue(app._reply_owner.has_worker)
        app._reply_schedule_fault.assert_not_called()
        self.assertIsNone(self.view._draft_ticket)
        self.assertFalse(self.view._confirm_draft())

    def test_cross_thread_snapshot_refuses_before_current_or_state_access(self):
        errors = []
        def foreign():
            try:
                self.snapshot()
            except RuntimeError as error:
                errors.append(str(error))
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ["WRONG_THREAD"])
        self.app._current.assert_not_called()


from tests.phase_831_fake_session_support import ProhibitedEffects
from nayeon.desktop_alpha.offline_request_draft import RECEIPT_TEXT


@unittest.skipUnless(os.name == "nt", "Native Windows Tk required")
class NativeDraftResetAssuranceTests(unittest.TestCase):
    """The real application must revoke draft before fallible reset cleanup."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.effects = ProhibitedEffects()
        self.guards = []
        for patcher in (*self.effects.patchers(), *self.effects.native_patchers(),
                        mock.patch.object(application.OfflineWorkspaceApplication,
                                          "_bootstrap_readonly_presentation",
                                          return_value=None)):
            patcher.__enter__()
            self.guards.append(patcher)
        self.addCleanup(self._cleanup)
        self.app = application.OfflineWorkspaceApplication(self.root)
        self.view = self.app._active_view
        self.view.entry.insert(0, "literal offline prompt")
        self.view.clear_button.invoke()
        self.assertIsNotNone(self.view._reset_review)
        self.view.draft_provider.insert(0, "openai")
        self.view.draft_model.insert(0, "example-model")
        self.assertTrue(self.view._begin_draft())
        self.assertTrue(self.view._confirm_draft())
        self.assertIsNotNone(self.view._draft_receipt)
        self.assertEqual(self.view.draft_status.cget("text"), RECEIPT_TEXT)

    def _cleanup(self):
        if hasattr(self, "app"):
            self.app.close()
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass
        for patcher in reversed(self.guards):
            patcher.__exit__(None, None, None)
        self.effects.assert_clean()
        self.assertEqual(self.errors, [])

    def test_committed_reset_cleanup_fault_cannot_retain_draft_receipt(self):
        before = self.app._conversation.snapshot
        original = ttk.Button.configure
        def reset_cleanup_fault(button, cnf=None, **options):
            if button is self.view.confirm_button and options.get("state") == "disabled":
                raise tk.TclError("reset cleanup refused")
            return original(button, cnf, **options)
        with mock.patch.object(ttk.Button, "configure", new=reset_cleanup_fault):
            self.view.confirm_button.invoke()
        self.assertIsNot(self.app._conversation.snapshot, before)
        self.assertIsNone(self.view._draft_ticket)
        self.assertIsNone(self.view._draft_data)
        self.assertIsNone(self.view._draft_snapshot)
        self.assertIsNone(self.view._draft_receipt)
        self.assertNotEqual(self.view.draft_status.cget("text"), RECEIPT_TEXT)

    def test_draft_cleanup_fault_refuses_reset_before_commit(self):
        before = self.app._conversation.snapshot
        original = ttk.Label.configure
        def draft_clear_fault(label, cnf=None, **options):
            result = original(label, cnf, **options)
            if label is self.view.draft_status and options.get("text") == "":
                raise tk.TclError("draft clear after-effect fault")
            return result
        with mock.patch.object(ttk.Label, "configure", new=draft_clear_fault):
            self.view.confirm_button.invoke()
        self.assertIs(self.app._conversation.snapshot, before)
        self.assertIsNone(self.view._draft_receipt)
        self.assertIsNone(self.view._draft_ticket)
        self.assertTrue(self.view._draft_faulted)
        self.assertNotEqual(self.view.draft_status.cget("text"), RECEIPT_TEXT)


if __name__ == "__main__":
    unittest.main()
