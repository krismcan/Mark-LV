"""8.32 direct native application tests; no retired adapter or fake scheduler.

Workers call Python handlers only. Arbitrary worker Tk API calls are outside
this contract and are intentionally never attempted. Root weakrefs retire on UI
thread before later suites may trigger worker GC.
"""
from __future__ import annotations

import ast
from contextlib import ExitStack
import gc
import inspect
import os
from pathlib import Path
import threading
from types import SimpleNamespace
import tkinter as tk
import unittest
import weakref
from unittest import mock

from nayeon.desktop_alpha import application, presentation_window, workspace_window
from nayeon.desktop_alpha.conversation_session import (
    OfflineConversationSession, RefusalCode, ResetOperation, SessionRefused,
)
from tests import test_phase_830_application as profile_fixture
from tests.phase_831_fake_session_support import ProhibitedEffects

_retired_tk_roots = []


class Phase832StaticContractTests(unittest.TestCase):
    def test_every_direct_owned_method_has_first_pure_thread_gate(self):
        for cls in (application.OfflineWorkspaceApplication,
                    workspace_window.WorkspaceWindow, workspace_window.WorkspacePane,
                    workspace_window.ConversationWindow, workspace_window.ConnectionWindow,
                    presentation_window.PresentationWindow):
            tree = ast.parse(inspect.getsource(cls))
            for method in tree.body[0].body:
                if not isinstance(method, ast.FunctionDef) or method.name == "__init__":
                    continue
                if method.name == "_require_creator_thread":
                    calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)]
                    self.assertEqual(len(calls), 2)  # get_ident and fixed RuntimeError
                    continue
                with self.subTest(cls=cls.__name__, method=method.name):
                    first = method.body[0]
                    self.assertIsInstance(first, ast.Expr)
                    self.assertEqual(ast.unparse(first), "self._require_creator_thread()")

    def test_reset_timer_surface_removed_but_sealed_owner_deadline_retained(self):
        source = inspect.getsource(application)
        for name in ("_conversation_timer", "_conversation_expire", "_cancel_conversation_timer"):
            self.assertNotIn(name, source)
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                             and n.func.attr in {"after", "after_idle", "after_cancel"}
                             for n in ast.walk(tree)))
        self.assertIn("now_ms >= review.expires_at_ms", inspect.getsource(OfflineConversationSession.confirm_reset))


@unittest.skipUnless(os.name == "nt", "Native Windows Tk lifecycle assurance")
class Phase832LifecycleTests(unittest.TestCase):
    def setUp(self):
        # The sealed fixture explicitly replaces known-folder resolution with a
        # disposable synthetic profile before construction; no user's data read.
        profile_fixture.Phase830ProductionAdmissionTests.setUp(self)
        self.root = tk.Tk()
        self.root.withdraw()
        _retired_tk_roots.append(weakref.ref(self.root))
        self.effects = ProhibitedEffects()
        self.guards = ExitStack()
        self.addCleanup(self.effects.assert_clean)
        self.addCleanup(self.guards.close)
        for patcher in (*self.effects.patchers(), *self.effects.native_patchers()):
            self.guards.enter_context(patcher)
        self.addCleanup(self._close)
        self.callback_errors = []
        self.root.report_callback_exception = lambda *args: self.callback_errors.append(args[0].__name__)
        self.app = application.OfflineWorkspaceApplication(self.root)
        self.owner, self.identity = self.app._conversation, self.app._conversation_root

    def _close(self):
        if hasattr(self, "app"):
            self.app.close()
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass
        self.assertEqual(self.callback_errors, [], "Tk swallowed a Python callback error")

    def _send(self, text="synthetic offline"):
        view = self.app._active_view
        view.entry.delete(0, "end")
        view.entry.insert(0, text)
        view._send()
        return self.owner.snapshot

    def _review(self, now=1000):
        view = self.app._active_view
        with mock.patch.object(self.app, "_conversation_now", return_value=now):
            self.app._conversation_review(view, self.app._active_token,
                                          self.app._generation, ResetOperation.CLEAR)
        self.assertIsNotNone(view._reset_review)
        return view._reset_review

    def test_real_visible_controls_strict_deadline_before_at_after(self):
        self.root.deiconify()
        self.root.update()
        for offset in (-1, 0, 1):
            with self.subTest(offset=offset):
                before = self._send("deadline " + str(offset))
                review = self._review(100000 * (offset + 2))
                view = self.app._active_view
                self.root.update_idletasks()
                self.assertIn("Valid for 30 seconds", view.reset_status.cget("text"))
                self.assertIn("Expired confirmation is refused", view.reset_status.cget("text"))
                with mock.patch.object(self.app, "_conversation_now",
                                       return_value=review.expires_at_ms + offset):
                    # Even past TTL there is no automatic hiding or clock read.
                    self.root.update_idletasks()
                    self.assertEqual(str(view.confirm_button.cget("state")), "normal")
                    self.assertIs(self.owner.snapshot, before)
                    view.confirm_button.invoke()
                if offset < 0:
                    self.assertEqual(self.owner.snapshot.entries, ())
                    self.assertIn("cleared locally", view.status.cget("text"))
                else:
                    self.assertIs(self.owner.snapshot, before)
                    self.assertIn("Select Review again", view.status.cget("text"))
                self.assertIsNone(view._reset_review)
                self.assertIsNone(view._reset_confirm)
                self.assertIsNone(self.owner._review)
                self.assertEqual(str(view.confirm_button.cget("state")), "disabled")
        self.assertFalse(self.app_dir.exists())

    def test_zero_reset_after_commands_and_foreign_timer_survives_all_interactions(self):
        fired = []
        foreign = self.root.after(60000, lambda: fired.append("F"))
        baseline = set(self.root.tk.call("after", "info"))
        commands = set(self.root.tk.call("info", "commands"))
        with (mock.patch.object(self.root, "after", side_effect=AssertionError("reset timer attempt")),
              mock.patch.object(self.root, "after_cancel", side_effect=AssertionError("foreign cancel attempt"))):
            for i in range(12):
                self._review(100000 * (i + 1))
                self.assertEqual(set(self.root.tk.call("after", "info")), baseline)
                self.app._active_view._dismiss_reset()
            self._review(2000000)
            self.app._active_view._confirm_reset()  # normal clock: expired -> deny
            self.app.show_settings()
            self.app.show_conversation()
            self.app.show_connection()
            self.assertIn(foreign, self.root.tk.call("after", "info"))
        # Widget commands legitimately exist; the review path adds no new ones.
        self.assertTrue(commands)
        self.assertEqual(fired, [])
        self.root.after_cancel(foreign)

    def test_partial_show_publication_at_each_configure_revokes_exact_review(self):
        for name in ("reset_status", "confirm_button", "dismiss_button"):
            with self.subTest(widget=name):
                view = self.app._active_view
                before = self._send("preserved")
                original = getattr(view, name).configure
                published = []
                def fail_published(*args, **kwargs):
                    if view._reset_review is not None:
                        published.append(view._reset_review)
                        raise RuntimeError("partial publication")
                    return original(*args, **kwargs)
                with mock.patch.object(getattr(view, name), "configure", side_effect=fail_published):
                    self.app._conversation_review(view, self.app._active_token,
                        self.app._generation, ResetOperation.CLEAR)
                self.assertEqual(len(published), 1)
                self.assertIsNone(self.owner._review)
                self.assertIsNone(view._reset_review)
                self.assertIsNone(view._reset_confirm)
                self.assertIs(self.owner.snapshot, before)
                self.assertFalse(self.app._busy)

    def test_partial_clear_and_status_failure_revoke_before_failed_visual_cleanup(self):
        before = self._send()
        view = self.app._active_view
        for i, target in enumerate((view.confirm_button, view.dismiss_button, view.reset_status)):
            review = self._review(1000 + i * 1000)
            with mock.patch.object(target, "configure", side_effect=RuntimeError("partial clear")):
                self.app._conversation_reset(view, self.app._active_token, self.app._generation,
                    self.app._conversation_view, review, False)
            self.assertIsNone(self.owner._review)
            self.assertIsNone(view._reset_confirm)
            self.assertIs(self.owner.snapshot, before)
        self._review(5000)
        with (mock.patch.object(view, "clear_reset", side_effect=RuntimeError("clear unavailable")),
              mock.patch.object(view, "show_status", side_effect=RuntimeError("status unavailable"))):
            view._dismiss_reset()
        self.assertIsNone(self.owner._review)
        # Even a synthetic pre-body failure cannot resurrect dismissed authority.
        with mock.patch.object(self.app, "_conversation_now", return_value=5001):
            view._confirm_reset()
        self.assertIs(self.owner.snapshot, before)
        self.assertIsNone(view._reset_confirm)
        self.assertFalse(self.app._busy)

    def test_clock_review_busy_refusals_cleanup_and_preserve_history(self):
        before = self._send()
        for i, code in enumerate((RefusalCode.CLOCK, RefusalCode.REVIEW, RefusalCode.BUSY)):
            with self.subTest(code=code):
                view = self.app._active_view
                self._review(10000 + i * 100000)
                with mock.patch.object(self.owner, "confirm_reset", side_effect=SessionRefused(code)):
                    view._confirm_reset()
                self.assertIsNone(self.owner._review)
                self.assertIsNone(view._reset_review)
                self.assertIs(self.owner.snapshot, before)
                self.assertIn("Select Review again", view.status.cget("text"))
                self.assertFalse(self.app._busy)
        self._review(2000000)
        with mock.patch.object(self.app, "_conversation_now", return_value=-1):
            self.app._conversation_review(view, self.app._active_token,
                self.app._generation, ResetOperation.CLEAR)
        self.assertIsNone(self.owner._review)
        self.assertIsNone(view._reset_review)
        self.assertIs(self.owner.snapshot, before)

    def test_denied_send_retains_review_accepted_send_clears_it_and_render_fault_keeps_pair(self):
        before = self._send()
        a = self._review()
        view = self.app._active_view
        view.entry.delete(0, "end")
        view._send()  # owner refuses empty input, no commit
        self.assertIs(self.owner.snapshot, before)
        self.assertIs(self.owner._review, a)
        self.assertIs(view._reset_review, a)
        with mock.patch.object(view, "render", side_effect=RuntimeError("render")):
            self._send("accepted B")
        self.assertEqual(len(self.owner.snapshot.entries), 4)
        self.assertIsNone(self.owner._review)
        self.assertIsNone(view._reset_review)
        self.assertIn("No AI request or action", view.status.cget("text"))
        self.assertIn("Display unavailable", view.status.cget("text"))

    def test_stale_a_confirm_during_b_publication_preserves_confirmable_successor(self):
        before = self._send("preserve until B confirmation")
        view = self.app._active_view
        a = self._review(1000)
        stale_confirm = view._reset_confirm
        self.assertTrue(callable(stale_confirm))
        token, generation = self.app._active_token, self.app._generation
        authority = self.app._conversation_view
        original = view.reset_status.configure
        reached = []

        def replay_a_during_b(*args, **kwargs):
            b = view._reset_review
            if b is not None and b is not a and not reached:
                # Capture evidence before A can revoke B. Assertions belong
                # outside this seam: review publication catches exceptions.
                reached.append((b, self.owner._review, self.app._active_view,
                    self.app._conversation_view, self.owner._view, self.app._busy,
                    self.app._conversation_current(view, token, generation, authority),
                    view._reset_confirm))
                stale_confirm()
            return original(*args, **kwargs)

        with (mock.patch.object(self.app, "_conversation_now", return_value=2000),
              mock.patch.object(self.app, "_interrupt_operation",
                                wraps=self.app._interrupt_operation) as interrupt,
              mock.patch.object(view.reset_status, "configure", side_effect=replay_a_during_b)):
            self.app._conversation_review(view, token, generation, ResetOperation.CLEAR)

        self.assertEqual(len(reached), 1, "A was not replayed during B publication")
        b, owner_review, active_view, app_authority, owner_view, busy, current, confirm = reached[0]
        self.assertIsNot(b, a)
        self.assertIs(owner_review, b)
        self.assertIs(active_view, view)
        self.assertIs(app_authority, authority)
        self.assertIs(owner_view, authority)
        self.assertIs(b.pane, authority)
        self.assertTrue(busy, "A must run while B publication owns the busy guard")
        self.assertTrue(current, "B must still be the current same-view operation")
        self.assertTrue(callable(confirm))
        self.assertIsNot(confirm, stale_confirm)
        self.assertEqual(interrupt.call_count, 0,
            "Stale reset A called _interrupt_operation and revoked B during B publication")
        self.assertIs(self.owner.snapshot, before)
        self.assertIs(self.owner._review, b)
        self.assertIs(view._reset_review, b)
        self.assertIs(view._reset_confirm, confirm)
        self.assertIs(self.app._conversation_view, authority)
        self.assertFalse(self.app._busy)
        self.assertEqual(str(view.confirm_button.cget("state")), "normal")
        self.assertEqual(b.expires_at_ms, 2000 + 30000)
        with mock.patch.object(self.app, "_conversation_now", return_value=b.expires_at_ms - 1):
            view.confirm_button.invoke()
        self.assertEqual(self.owner.snapshot.entries, ())
        self.assertEqual(self.owner.snapshot.revision, before.revision + 1)
        self.assertIsNone(self.owner._review)
        self.assertIsNone(view._reset_review)
        self.assertIn("cleared locally", view.status.cget("text"))

    def test_a_fault_preserves_same_view_successor_b_controls_ticket_and_foreign_f(self):
        view = self.app._active_view
        a = self._review()
        authority = self.app._conversation_view
        foreign = self.root.after(60000, lambda: None)
        saved = {}
        def replace_a(*args, **kwargs):
            b = self.owner.begin_reset_review(self.identity, authority,
                                              ResetOperation.NEW_SESSION, now_ms=2000)
            ticket = self.owner.issue_submission(self.identity, authority, "B")
            view.show_reset(b, lambda: None, lambda: None)
            saved.update(review=b, ticket=ticket, confirm=view._reset_confirm)
            raise RuntimeError("A failed after B publication")
        with mock.patch.object(self.owner, "confirm_reset", side_effect=replace_a):
            view._confirm_reset()
        self.assertIs(self.owner._review, saved["review"])
        self.assertIs(view._reset_review, saved["review"])
        self.assertIs(view._reset_confirm, saved["confirm"])
        self.assertEqual(str(view.confirm_button.cget("state")), "normal")
        self.assertIn(foreign, self.root.tk.call("after", "info"))
        self.assertFalse(self.owner.dismiss_reset_review(self.identity, a))
        self.owner.claim_submission(self.identity, authority, saved["ticket"])
        self.assertEqual(self.owner.commit_submission(self.identity, authority,
            saved["ticket"]).snapshot.entries[0].payload, "B")
        self.root.after_cancel(foreign)

    def test_nested_close_before_commit_and_during_review_publication_is_terminal(self):
        view = self.app._active_view
        original = self.owner.issue_submission
        def close_before_claim(*args):
            result = original(*args)
            self.app.close()
            self.app.close()
            return result
        with mock.patch.object(self.owner, "issue_submission", side_effect=close_before_claim):
            self._send()
        self.assertTrue(self.owner.snapshot.closed)
        self.assertEqual(self.owner.snapshot.entries, ())
        self.assertIsNone(self.owner._review)
        self.assertFalse(self.app._busy)

    def test_nested_close_between_begin_review_and_show_has_no_orphan(self):
        view = self.app._active_view
        original = self.owner.begin_reset_review
        def close_review(*args, **kwargs):
            review = original(*args, **kwargs)
            self.app.close()
            return review
        with mock.patch.object(self.owner, "begin_reset_review", side_effect=close_review):
            self.app._conversation_review(view, self.app._active_token,
                self.app._generation, ResetOperation.CLEAR)
        self.assertTrue(self.owner.snapshot.closed)
        self.assertIsNone(self.owner._review)
        self.assertIsNone(view._reset_confirm)
        self.assertFalse(self.app._busy)

    def _worker_refusals(self, cases):
        errors = []
        def work():
            for callback, args, kwargs in cases:
                try:
                    callback(*args, **kwargs)
                except RuntimeError as error:
                    errors.append(str(error))
                except BaseException as error:
                    errors.append(type(error).__name__)
                else:
                    errors.append("ADMITTED")
        thread = threading.Thread(target=work, name="832-python-callback-probe")
        thread.start()
        thread.join(10)
        self.assertFalse(thread.is_alive(), "Callback entered Tk instead of pure refusal")
        self.assertEqual(errors, ["WRONG_THREAD"] * len(cases))

    def test_current_identity_worker_app_callbacks_refuse_before_tcl_owner_clock_mutation(self):
        view = self.app._active_view
        review = self._review()
        token, generation, authority = self.app._active_token, self.app._generation, self.app._conversation_view
        event = SimpleNamespace(widget=self.root)
        cases = [(getattr(self.app, n), (), {}) for n in (
            "_root_exists", "_bootstrap_readonly_presentation", "show_conversation",
            "show_settings", "show_connection", "close", "_retire_view",
            "_revoke_conversation_view", "_interrupt_operation", "_invalidate_owner", "_conversation_now")]
        for name in ("_current", "_owner_current", "_cancel", "_changed", "_review",
                     "_save", "_load_settings", "_conversation_send", "_view_destroyed"):
            cases.append((getattr(self.app, name), (view, token, generation), {}))
        cases.extend([
            (self.app._show, (application._Page.SETTINGS,), {}),
            (self.app._root_destroyed, (event,), {}),
            (self.app._conversation_review, (view, token, generation, ResetOperation.CLEAR), {}),
            (self.app._conversation_reset, (view, token, generation, authority, review, True), {}),
            (self.app._conversation_current, (view, token, generation, authority), {}),
            (self.app._cleanup_reset, (view, token, generation, review), {}),
            (self.app._reset_status, (view, token, generation, "unavailable"), {}),
        ])
        attempts = []
        def trap(*args, **kwargs):
            attempts.append("prohibited before gate")
            raise AssertionError("Foreign handler crossed pure boundary")
        before = (self.app._busy, self.app._closed, self.app._generation, self.owner.snapshot, view._reset_review)
        with ExitStack() as stack:
            for target, name in ((self.root, "winfo_exists"), (view, "exists"),
                                 (application.time, "monotonic_ns")):
                stack.enter_context(mock.patch.object(target, name, side_effect=trap))
            for name in ("begin_reset_review", "confirm_reset", "dismiss_reset_review",
                         "revoke_view", "close", "issue_submission"):
                stack.enter_context(mock.patch.object(self.owner, name, side_effect=trap))
            self._worker_refusals(cases)
        self.assertEqual(attempts, [])
        self.assertEqual((self.app._busy, self.app._closed, self.app._generation,
                          self.owner.snapshot, view._reset_review), before)

    def test_worker_direct_view_handlers_refuse_before_first_owned_tcl_or_callback(self):
        view = self.app._active_view
        review = self._review()
        attempts = []
        def trap(*args, **kwargs):
            attempts.append("Tcl/owner/callback")
            raise AssertionError("first effect reached")
        callback = trap
        cases = [(getattr(view, n), (), {}) for n in ("exists", "destroy", "dispose", "focus_initial",
                  "_confirm_reset", "_dismiss_reset", "_send", "clear_reset", "_block_edit")]
        cases.extend([
            (view._destroyed, (SimpleNamespace(widget=view),), {}),
            (view._proposed, ("valid text",), {}),
            (view.show_status, ("bounded",), {}),
            (view.render, (self.owner.snapshot,), {}),
            (view.show_reset, (review, callback, callback), {}),
            (view._return, (view.confirm_button.invoke,), {}),
            (view._dispatch, (callback,), {}),
        ])
        with (mock.patch.object(view, "_is_current", side_effect=trap),
              mock.patch.object(view.entry, "focus_set", side_effect=trap),
              mock.patch.object(view.confirm_button, "invoke", side_effect=trap)):
            self._worker_refusals(cases)
        self.assertIs(view._reset_review, review)
        self.assertFalse(view._sending)
        workspace = self.app.workspace
        self._worker_refusals([
            (workspace.set_busy, (True,), {}), (workspace.publish_name, ("worker",), {}),
            (workspace.publish_profile_status, ("worker",), {}),
            (workspace._dispatch, (callback,), {}),
            (workspace._return, (workspace.navigation_buttons[0].invoke,), {}),
        ])
        self.app.show_settings()
        settings = self.app._active_view
        revision = settings.revision
        cases = [(getattr(settings, n), (), {}) for n in ("exists", "destroy", "dispose",
            "_changed", "build_draft", "clear_review", "focus_initial")]
        cases.extend([
            (settings._destroyed, (SimpleNamespace(widget=settings),), {}),
            (settings.load_document, (self.app._published_document,), {"present": False}),
            (settings.show_review, (self.app._published_document,), {}),
            (settings.set_controls, (), {"editable": True}),
            (settings.show_status, ("worker",), {}),
            (settings._dispatch, (callback,), {}), (settings._return, (callback,), {}),
        ])
        with (mock.patch.object(settings.assistant_name, "get", side_effect=trap),
              mock.patch.object(settings.assistant_name, "set", side_effect=trap),
              mock.patch.object(settings.summary_label, "configure", side_effect=trap)):
            self._worker_refusals(cases)
        self.assertEqual(settings.revision, revision)
        self.app.show_connection()
        connection = self.app._active_view
        self._worker_refusals([(connection.focus_initial, (), {}),
            (connection._dispatch, (callback,), {}), (connection._return, (callback,), {})])
        self.assertEqual(attempts, [])


def tearDownModule():
    if threading.current_thread() is not threading.main_thread():
        raise AssertionError("Native Tk cleanup requires creator thread")
    gc.collect()
    survivors = sum(root() is not None for root in _retired_tk_roots)
    if survivors:
        raise AssertionError(f"{survivors} retired 8.32 roots survived main-thread GC")
    _retired_tk_roots.clear()


if __name__ == "__main__":
    unittest.main()
