"""Native fake-only one-shot Tk inventory and interpreter lifetime evidence.

The isolated child is a test harness, never a production worker. It deliberately
collects on a worker while the creator retains the live Tcl graph, then proves
main-thread retirement before further worker collection.
"""
from contextlib import ExitStack
import gc
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import tkinter as tk
from types import SimpleNamespace
import unittest
import weakref
from unittest import mock

from nayeon.desktop_alpha import application
from nayeon.desktop_alpha.conversation_session import ResetOperation
from nayeon.desktop_alpha.offline_completion_admission import (
    CANCELLED, COMPLETE, UNAVAILABLE, WAITING, CompletionState,
)
from tests.phase_831_fake_session_support import ProhibitedEffects

_retired_tk_roots = []


@unittest.skipUnless(os.name == "nt", "Authoritative Windows Tk completion")
class Phase833TkCompletionTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        _retired_tk_roots.append(weakref.ref(self.root))
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args[0].__name__)
        self.effects = ProhibitedEffects()
        self.guards = ExitStack()
        self.addCleanup(self.effects.assert_clean)
        self.addCleanup(self.guards.close)
        for patcher in (*self.effects.patchers(), *self.effects.native_patchers()):
            self.guards.enter_context(patcher)
        # No known-folder/profile resolution or user data is needed here.
        self.guards.enter_context(mock.patch.object(application.OfflineWorkspaceApplication,
                                                   "_bootstrap_readonly_presentation", return_value=None))
        self.app = application.OfflineWorkspaceApplication(self.root)
        self.addCleanup(self._close)

    def _close(self):
        if self.app is not None:
            retired = weakref.ref(self.root)
            self.app.close()
            self.app = self.root = None
            _assert_graph_retired(self, (retired,))
        self.assertEqual(self.errors, [])

    def timers(self):
        return set(self.root.tk.call("after", "info"))

    def send(self, text="synthetic offline"):
        view = self.app._active_view
        view.entry.delete(0, "end")
        view.entry.insert(0, text)
        view._send()
        return self.app._conversation.snapshot

    def wait_completion(self):
        deadline = time.monotonic() + 2
        while self.app._completion.state is CompletionState.PENDING and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.005)
        self.assertEqual(self.app._completion.state, CompletionState.IDLE)

    def test_real_150ms_timer_status_only_and_readonly_immutable_transcript(self):
        foreign = self.root.after(60000, lambda: None)
        base = self.timers()
        before = self.send("open notepad")
        view = self.app._active_view
        transcript = view.transcript.get("1.0", "end")
        self.assertEqual(view.status.cget("text"), WAITING)
        self.assertEqual(self.timers(), base | {self.app._completion._handle})
        self.root.update_idletasks()
        self.assertEqual(view.status.cget("text"), WAITING)
        self.wait_completion()
        self.assertEqual(view.status.cget("text"), COMPLETE)
        self.assertIs(self.app._conversation.snapshot, before)
        self.assertEqual(view.transcript.get("1.0", "end"), transcript)
        self.assertEqual(str(view.transcript.cget("state")), "disabled")
        self.assertEqual(self.timers(), base)
        self.root.after_cancel(foreign)

    def test_a_b_stale_callback_exact_handle_cancel_and_explicit_cancel(self):
        foreign = self.root.after(60000, lambda: None)
        self.send("A")
        helper = self.app._completion
        a = helper._pending
        a_handle = helper._handle
        before = self.send("B")
        b_handle = helper._handle
        helper._deliver(a)
        self.assertEqual(helper._handle, b_handle)
        self.assertNotIn(a_handle, self.timers())
        self.assertEqual(self.timers(), {foreign, b_handle})
        self.app._active_view.cancel_simulation_button.invoke()
        self.assertEqual(self.app._active_view.status.cget("text"), CANCELLED)
        self.assertIs(self.app._conversation.snapshot, before)
        self.assertEqual(self.timers(), {foreign})
        self.root.after_cancel(foreign)

    def test_rejected_send_and_dismiss_expired_confirm_preserve_pending_a(self):
        self.send("A")
        helper = self.app._completion
        a = helper._handle
        view = self.app._active_view
        self.send("")
        self.assertEqual(helper._handle, a)
        with mock.patch.object(self.app, "_conversation_now", return_value=1000):
            view.clear_button.invoke()
        view.dismiss_button.invoke()
        self.assertEqual(helper._handle, a)
        with mock.patch.object(self.app, "_conversation_now", return_value=1000):
            view.clear_button.invoke()
        with mock.patch.object(self.app, "_conversation_now", return_value=31000):
            view.confirm_button.invoke()
        self.assertEqual(helper._handle, a)
        self.assertEqual(len(self.app._conversation.snapshot.entries), 2)

    def test_confirmed_resets_and_navigation_retire_only_owned_timer(self):
        foreign = self.root.after(60000, lambda: None)
        for operation in (ResetOperation.CLEAR, ResetOperation.NEW_SESSION):
            self.send()
            view = self.app._active_view
            with mock.patch.object(self.app, "_conversation_now", return_value=1000):
                self.app._conversation_review(view, self.app._active_token,
                                             self.app._generation, operation)
                view.confirm_button.invoke()
            self.assertEqual(self.timers(), {foreign})
            self.assertEqual(self.app._conversation.snapshot.entries, ())
        self.send()
        self.app.show_connection()
        self.assertEqual(self.timers(), {foreign})
        self.app.show_conversation()
        self.send()
        self.assertEqual(len(self.timers()), 2)
        self.root.after_cancel(foreign)

    def test_external_child_destroy_python_only_and_no_root_closed_claim(self):
        self.send()
        before = self.app._conversation.snapshot
        helper = self.app._completion
        a, handle = helper._pending, helper._handle
        view = self.app._active_view
        with (mock.patch.object(self.root, "after_cancel", side_effect=AssertionError("Destroy Tcl")),
              mock.patch.object(self.root, "winfo_exists", side_effect=AssertionError("Destroy query"))):
            view._destroyed(SimpleNamespace(widget=view))
        self.assertEqual(helper.state, CompletionState.POISONED)
        self.assertFalse(self.app._closed)
        self.assertIn(handle, self.timers())
        helper._deliver(a)
        self.assertIs(self.app._conversation.snapshot, before)
        # Synthetic event revokes Python lifetime; explicitly retire native pane
        # with the base implementation before rebuilding the same widget name.
        tk.BaseWidget.destroy(view)
        self.app.show_conversation()
        self.send("B")
        self.assertEqual(self.app._active_view.status.cget("text"), UNAVAILABLE)
        self.assertEqual(self.timers(), {handle})
        # The synthetic Destroy deliberately prevented production cancellation.
        # Retire this exact test-owned registration before native root teardown.
        self.root.after_cancel(handle)

    def test_root_destroy_handler_is_python_only(self):
        self.send()
        a = self.app._completion._pending
        handle = self.app._completion._handle
        with (mock.patch.object(self.root, "after_cancel", side_effect=AssertionError("Destroy Tcl")),
              mock.patch.object(self.root, "winfo_exists", side_effect=AssertionError("Destroy query"))):
            self.app._root_destroyed(SimpleNamespace(widget=self.root))
        self.assertEqual(self.app._completion.state, CompletionState.CLOSED)
        self.app._completion._deliver(a)
        self.assertTrue(self.app._conversation.snapshot.closed)
        self.root.after_cancel(handle)  # synthetic Destroy left this test timer
        self.root.destroy()  # actual native retirement remains test-owned

    def test_native_registration_and_cancel_faults_before_after_effect(self):
        self._close()
        for seam in ("after", "after_cancel"):
            for effective in (False, True):
                with self.subTest(seam=seam, effective=effective):
                    refs, publications, errors = _native_retirement_case(self, seam, effective)
                    _assert_graph_retired(self, refs)
                    self.assertNotIn(COMPLETE, publications)
                    self.assertEqual(errors, [])

    def test_delivery_reentered_during_admission_cannot_restore_waiting(self):
        helper = self.app._completion
        original = helper.start
        def deliver_before_return(*args, **kwargs):
            result = original(*args, **kwargs)
            # Retire the actual script before explicitly invoking its callback.
            self.root.after_cancel(helper._handle)
            helper._deliver(helper._pending)
            return result
        with mock.patch.object(helper, "start", side_effect=deliver_before_return):
            self.send()
        self.assertEqual(self.app._active_view.status.cget("text"), COMPLETE)
        self.assertEqual(self.timers(), set())

    def test_wrong_thread_handlers_refuse_before_native_or_owner_access(self):
        self.send()
        helper = self.app._completion
        ticket = helper._pending
        snapshot = self.app._conversation.snapshot
        view, token, generation = self.app._active_view, self.app._active_token, self.app._generation
        errors = []
        def worker():
            for handler in (helper.cancel, helper.destroyed, helper.pane_destroyed,
                            helper.publication_failed, lambda: helper.is_pending_for(snapshot),
                            lambda: helper._deliver(ticket),
                            lambda: self.app._conversation_cancel_simulation(view, token, generation)):
                try:
                    handler()
                except RuntimeError as error:
                    errors.append(str(error))
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ["WRONG_THREAD"] * 7)
        self.assertIs(helper._pending, ticket)

    def test_status_current_seam_cannot_overwrite_cancel_or_b_with_a(self):
        for action in ("cancel", "B"):
            self.send("A")
            helper = self.app._completion
            ticket = helper._pending
            self.root.after_cancel(helper._handle)  # test-owned explicit dispatch
            view = self.app._active_view
            original = view._is_current
            reached = []
            def reenter():
                if not reached:
                    reached.append(action)
                    if action == "cancel":
                        view.cancel_simulation_button.invoke()
                    else:
                        self.send("B")
                return original()
            with mock.patch.object(view, "_is_current", side_effect=reenter):
                helper._deliver(ticket)
            self.assertEqual(reached, [action])
            self.assertEqual(view.status.cget("text"), CANCELLED if action == "cancel" else WAITING)

    def test_cancel_a_view_current_seam_preserves_successor_b(self):
        before = self.send("A")
        helper = self.app._completion
        a, a_handle = helper._pending, helper._handle
        view = self.app._active_view
        original = view._is_current
        successor = []
        def send_b():
            if not successor:
                successor.append(None)  # guard B's own nested view-current calls
                self.assertNotIn(a_handle, self.timers())
                snapshot = self.send("B")
                successor[0] = (snapshot, helper._pending, helper._handle)
            return original()
        # Direct handler entry places the injection exactly inside cancellation's
        # status publication, after A's timer has already been retired.
        with mock.patch.object(view, "_is_current", side_effect=send_b):
            self.app._conversation_cancel_simulation(
                view, self.app._active_token, self.app._generation)
        self.assertEqual(len(successor), 1)
        snapshot, b, b_handle = successor[0]
        self.assertIsNot(snapshot, before)
        self.assertIs(self.app._conversation.snapshot, snapshot)
        self.assertIs(helper._pending, b)
        self.assertIs(b.snapshot, snapshot)
        self.assertNotEqual(a_handle, b_handle)
        self.assertEqual(self.timers(), {b_handle})
        self.assertEqual(view.status.cget("text"), WAITING)
        transcript = view.transcript.get("1.0", "end")
        helper._deliver(a)  # stale A cannot replay cancellation or completion
        self.assertIs(helper._pending, b)
        self.assertEqual(self.timers(), {b_handle})
        self.assertEqual(view.status.cget("text"), WAITING)
        self.wait_completion()
        self.assertEqual(view.status.cget("text"), COMPLETE)
        self.assertIs(self.app._conversation.snapshot, snapshot)
        self.assertEqual(view.transcript.get("1.0", "end"), transcript)
        self.assertEqual(self.timers(), set())

    def _check_cancel_publication_error(self, error_type):
        foreign = self.root.after(60000, lambda: None)
        original = self.send("A")
        view = self.app._active_view
        before = view.transcript.get("1.0", "end")
        with mock.patch.object(view, "show_simulation_status",
                               side_effect=error_type("private status failure")):
            with self.assertRaisesRegex(RuntimeError, "^CANCEL_STATUS_PUBLICATION_FAILED$"):
                self.app._conversation_cancel_simulation(
                    view, self.app._active_token, self.app._generation)
        self.assertIs(self.app._conversation.snapshot, original)
        self.assertEqual(view.transcript.get("1.0", "end"), before)
        self.assertEqual(self.app._completion.state, CompletionState.POISONED)
        self.assertEqual(self.timers(), {foreign})
        self.send("B")
        self.assertEqual(self.app._completion.state, CompletionState.POISONED)
        self.assertEqual(self.timers(), {foreign})
        self.assertEqual(view.status.cget("text"), UNAVAILABLE)
        self.root.after_cancel(foreign)

    def test_cancel_tcl_error_is_observable_and_fails_closed(self):
        self._check_cancel_publication_error(tk.TclError)

    def test_cancel_runtime_error_is_observable_and_fails_closed(self):
        self._check_cancel_publication_error(RuntimeError)

    def test_cancel_publication_failure_preserves_reentrant_successor_b(self):
        self.send("A")
        view = self.app._active_view
        original = view.show_simulation_status
        observed = []
        helper = self.app._completion
        def fail_after_successor(text, eligible):
            if text == CANCELLED:
                snapshot = self.send("B")
                # Pin B's exact owner ticket and physical handle INSIDE the
                # fault seam; replacement with a different successful B-like
                # request would otherwise pass a snapshot-only assertion.
                observed.append((snapshot, helper._pending, helper._handle))
                raise tk.TclError("private status failure")
            return original(text, eligible)
        with mock.patch.object(view, "show_simulation_status",
                               side_effect=fail_after_successor):
            with self.assertRaisesRegex(RuntimeError, "^CANCEL_STATUS_PUBLICATION_FAILED$"):
                self.app._conversation_cancel_simulation(
                    view, self.app._active_token, self.app._generation)
        self.assertEqual(len(observed), 1)
        snapshot, ticket, handle = observed[0]
        self.assertIsNotNone(ticket)
        self.assertIsNotNone(handle)
        self.assertIs(self.app._conversation.snapshot, snapshot)
        self.assertIs(ticket.snapshot, snapshot)
        self.assertIs(helper._pending, ticket)
        self.assertEqual(helper._handle, handle)
        self.assertEqual(self.timers(), {handle})
        self.assertEqual(helper.state, CompletionState.PENDING)
        self.assertEqual(view.status.cget("text"), WAITING)
        self.wait_completion()
        self.assertEqual(view.status.cget("text"), COMPLETE)
        self.assertIs(self.app._conversation.snapshot, snapshot)

    def test_cancel_failure_after_root_destroy_preserves_closed_state(self):
        self.send("A")
        view = self.app._active_view
        def retire_then_fail(text, eligible):
            self.root.destroy()
            raise RuntimeError("private status failure")
        with mock.patch.object(view, "show_simulation_status",
                               side_effect=retire_then_fail):
            with self.assertRaisesRegex(RuntimeError, "^CANCEL_STATUS_PUBLICATION_FAILED$"):
                self.app._conversation_cancel_simulation(
                    view, self.app._active_token, self.app._generation)
        self.assertEqual(self.app._completion.state, CompletionState.CLOSED)
        self.assertTrue(self.app._conversation.snapshot.closed)
        self.assertEqual(self.errors, [])

    def test_direct_pane_destroy_retires_exact_833_timer_before_tcl(self):
        self.send("A")
        view = self.app._active_view
        owned = self.app._completion._handle
        self.assertIn(owned, self.timers())
        view.destroy()
        self.assertNotIn(owned, self.timers())
        self.assertIsNone(self.app._conversation_view)
        self.app.show_conversation()
        self.send("B")
        self.wait_completion()
        self.assertEqual(self.app._active_view.status.cget("text"), COMPLETE)

    def test_before_destroy_nested_after_cancel_cannot_schedule_successor(self):
        self.send("A")
        view = self.app._active_view
        original_cancel = self.root.after_cancel
        owned = self.app._completion._handle
        committed = []
        reached = []
        def nested(handle):
            reached.append(handle)
            if len(reached) == 1:
                committed.append(self.send("B"))
            return original_cancel(handle)
        with mock.patch.object(self.root, "after_cancel", side_effect=nested):
            view.destroy()
        self.assertEqual(reached, [owned])
        self.assertEqual(len(committed), 1)
        self.assertIs(self.app._conversation.snapshot, committed[0])
        self.assertEqual(len(committed[0].entries), 4)
        self.assertIsNone(self.app._conversation_view)
        self.assertEqual(self.timers(), set())
        self.app.show_conversation()
        self.send("C")
        self.wait_completion()
        self.assertEqual(self.app._active_view.status.cget("text"), COMPLETE)

    def test_stale_direct_destroy_hook_cannot_cancel_successor_timer(self):
        self.send("A")
        old = self.app._active_view
        stale = old._on_before_destroy
        self.app.show_connection()
        self.app.show_conversation()
        snapshot = self.send("B")
        helper = self.app._completion
        handle, ticket = helper._handle, helper._pending
        stale()
        self.assertIs(self.app._conversation.snapshot, snapshot)
        self.assertIs(helper._pending, ticket)
        self.assertEqual(helper._handle, handle)
        self.assertEqual(self.timers(), {handle})
        self.wait_completion()
        self.assertEqual(self.app._active_view.status.cget("text"), COMPLETE)

    def test_cancel_runtime_publication_failure_preserves_successor_b(self):
        self.send("A")
        view = self.app._active_view
        original = view.show_simulation_status
        observed = []
        helper = self.app._completion
        def fault(text, eligible):
            if text == CANCELLED:
                snapshot = self.send("B")
                # B must retain the exact *original* ticket and timer; an
                # apparent B completion after replacement is not sufficient.
                observed.append((snapshot, helper._pending, helper._handle))
                raise RuntimeError("private status failure")
            return original(text, eligible)
        with mock.patch.object(view, "show_simulation_status", side_effect=fault):
            with self.assertRaisesRegex(RuntimeError, "^CANCEL_STATUS_PUBLICATION_FAILED$"):
                self.app._conversation_cancel_simulation(
                    view, self.app._active_token, self.app._generation)
        self.assertEqual(len(observed), 1)
        snapshot, ticket, handle = observed[0]
        self.assertIsNotNone(ticket)
        self.assertIsNotNone(handle)
        self.assertIs(self.app._conversation.snapshot, snapshot)
        self.assertIs(ticket.snapshot, snapshot)
        self.assertIs(helper._pending, ticket)
        self.assertEqual(helper._handle, handle)
        self.assertEqual(self.timers(), {handle})
        self.assertEqual(helper.state, CompletionState.PENDING)
        self.assertEqual(view.status.cget("text"), WAITING)
        self.wait_completion()
        self.assertEqual(view.status.cget("text"), COMPLETE)
        self.assertIs(self.app._conversation.snapshot, snapshot)

    def test_cancel_tcl_failure_after_root_destroy_preserves_closed_state(self):
        self.send("A")
        view = self.app._active_view
        def retire_then_fail(text, eligible):
            self.root.destroy()
            raise tk.TclError("private status failure")
        with mock.patch.object(view, "show_simulation_status",
                               side_effect=retire_then_fail):
            with self.assertRaisesRegex(RuntimeError, "^CANCEL_STATUS_PUBLICATION_FAILED$"):
                self.app._conversation_cancel_simulation(
                    view, self.app._active_token, self.app._generation)
        self.assertEqual(self.app._completion.state, CompletionState.CLOSED)
        self.assertTrue(self.app._conversation.snapshot.closed)
        self.assertEqual(self.errors, [])

    def test_waiting_publication_rechecks_pending_after_view_callback(self):
        helper = self.app._completion
        view = self.app._active_view
        original = view._is_current
        reached = []
        def deliver():
            if helper.state is CompletionState.PENDING and not reached:
                reached.append(True)
                self.root.after_cancel(helper._handle)
                helper._deliver(helper._pending)
            return original()
        with mock.patch.object(view, "_is_current", side_effect=deliver):
            self.send()
        self.assertEqual(reached, [True])
        self.assertEqual(view.status.cget("text"), COMPLETE)

    def test_publication_exception_retires_timer_and_poisons_future_registration(self):
        view = self.app._active_view
        with mock.patch.object(view, "show_simulation_status", side_effect=RuntimeError("private")):
            self.send()
        self.assertEqual(self.app._completion.state, CompletionState.POISONED)
        self.assertEqual(self.timers(), set())
        self.send("B")
        self.assertEqual(view.status.cget("text"), UNAVAILABLE)
        self.assertEqual(len(self.app._conversation.snapshot.entries), 4)


def _assert_graph_retired(check, refs):
    if threading.current_thread() is not threading.main_thread():
        raise AssertionError("Tk graph retirement requires creator thread")
    gc.collect()  # test-owned cycles, after all bound methods/closures left scope
    check.assertTrue(all(ref() is None for ref in refs),
                     "Predecessor Tk graph survived creator-thread retirement")


def _native_retirement_case(check, seam, effective=False):
    """Return only weakrefs/data; no bound method or Tk closure may escape."""
    root = tk.Tk()
    root.withdraw()
    errors, publications, owned, reached, cancel_args = [], [], [], [], []
    root.report_callback_exception = lambda *args: errors.append(args[0].__name__)
    refs = [weakref.ref(root)]
    _retired_tk_roots.append(refs[0])
    effects = ProhibitedEffects()
    with ExitStack() as guards:
        for patcher in (*effects.patchers(), *effects.native_patchers()):
            guards.enter_context(patcher)
        guards.enter_context(mock.patch.object(application.OfflineWorkspaceApplication,
                                               "_bootstrap_readonly_presentation", return_value=None))
        app = application.OfflineWorkspaceApplication(root)
        view, helper = app._active_view, app._completion
        refs.extend(weakref.ref(item) for item in (app, view, helper))
        foreign = root.after(60000, lambda: None)
        original_after, original_cancel = root.after, root.after_cancel
        original_status = view.show_simulation_status
        def publish(text, eligible):
            publications.append(text)
            original_status(text, eligible)
        def register(*args):
            if seam == "after":
                reached.append(True)
                if not effective:
                    raise RuntimeError("private fault before registration")
            handle = original_after(*args)
            owned.append(handle)  # exact result hidden from production on fault
            if seam == "after":
                raise RuntimeError("private fault after registration")
            return handle
        def cancel(handle):
            reached.append(True)
            cancel_args.append(handle)
            if effective:
                original_cancel(handle)
            raise RuntimeError("private cancellation fault")
        def send(text):
            current = app._active_view
            current.entry.insert(0, text)
            current._send()
        try:
            with (mock.patch.object(root, "after", side_effect=register),
                  mock.patch.object(view, "show_simulation_status", side_effect=publish)):
                if seam == "after_cancel":
                    send("A")
                    with mock.patch.object(root, "after_cancel", side_effect=cancel):
                        send("B")
                elif seam == "external":
                    send("A")
                    snapshot = app._conversation.snapshot
                    with (mock.patch.object(root, "after_cancel", side_effect=AssertionError("Destroy Tcl")),
                          mock.patch.object(root, "winfo_exists", side_effect=AssertionError("Destroy query"))):
                        view._destroyed(SimpleNamespace(widget=view))
                    check.assertFalse(app._closed)
                    check.assertIs(app._conversation.snapshot, snapshot)
                    tk.BaseWidget.destroy(view)  # synthetic event did not do this
                    app.show_conversation()
                else:
                    send("B")
                check.assertEqual(reached, [] if seam == "external" else [True])
                check.assertEqual(cancel_args, owned if seam == "after_cancel" else [])
                check.assertEqual(helper.state, CompletionState.POISONED)
                inventory = set(root.tk.call("after", "info"))
                retired_by_fault = seam == "after_cancel" and effective
                pending = set() if retired_by_fault else set(owned)
                check.assertEqual(inventory, {foreign} | pending)
                send("C")
                check.assertEqual(set(root.tk.call("after", "info")), inventory)
                check.assertEqual(app._active_view.status.cget("text"), UNAVAILABLE)
                check.assertNotIn(COMPLETE, publications)
        finally:
            # Only injection-observed/test-owned handles, never production guesses
            # or a blanket sweep. A before-cancel fault leaves A native and live.
            for handle in owned:
                if handle in root.tk.call("after", "info"):
                    original_cancel(handle)
            check.assertEqual(set(root.tk.call("after", "info")), {foreign})
            original_cancel(foreign)
            root.update_idletasks()  # finish native widget idles before destruction
            app.close()
        effects.assert_clean()
    check.assertEqual(errors, [])
    return tuple(refs), publications, errors


def _pump_successor(check):
    root = tk.Tk()
    root.withdraw()
    errors, done = [], []
    root.report_callback_exception = lambda *args: errors.append(args[0].__name__)
    ref = weakref.ref(root)
    handle = root.after(200, lambda: done.append(True))
    try:
        deadline = time.monotonic() + 3
        while not done and time.monotonic() < deadline:
            root.update()
            time.sleep(.005)
        check.assertEqual(done, [True], "Successor did not dispatch past 150 ms")
        check.assertEqual(errors, [])
    finally:
        if handle in root.tk.call("after", "info"):
            root.after_cancel(handle)
        root.destroy()
    return ref


def _native_retirement_child():
    check = unittest.TestCase()
    for seam, effective in (("after", False), ("after", True),
                            ("after_cancel", False), ("after_cancel", True),
                            ("external", False)):
        refs, publications, errors = _native_retirement_case(check, seam, effective)
        _assert_graph_retired(check, refs)
        before = tuple(publications)
        successor = _pump_successor(check)
        _assert_graph_retired(check, (*refs, successor))
        check.assertEqual(tuple(publications), before)
        check.assertNotIn(COMPLETE, publications)
        check.assertEqual(errors, [])
    print("833_TK_RETIREMENT_CHILD_OK", flush=True)


def _gc_child():
    """Invoked only by the bounded subprocess test below on the host."""
    errors = []
    roots = []
    for action in ("pending", "navigation", "close", "external"):
        root = tk.Tk()
        root.withdraw()
        roots.append(weakref.ref(root))
        root.report_callback_exception = lambda *args: errors.append(args[0].__name__)
        effects = ProhibitedEffects()
        with ExitStack() as guards:
            for patcher in (*effects.patchers(), *effects.native_patchers()):
                guards.enter_context(patcher)
            guards.enter_context(mock.patch.object(application.OfflineWorkspaceApplication,
                                                   "_bootstrap_readonly_presentation", return_value=None))
            app = application.OfflineWorkspaceApplication(root)
            view = app._active_view
            view.entry.insert(0, "synthetic")
            view._send()
            helper = app._completion
            handle = helper._handle
            wrong_thread = []
            def collect():
                try:
                    helper.cancel()
                except RuntimeError as error:
                    wrong_thread.append(str(error))
                gc.collect()
            worker = threading.Thread(target=collect)
            worker.start()
            if action == "navigation":
                app.show_connection()
            elif action == "close":
                app.close()
            elif action == "external":
                root.after_cancel(handle)  # exact test-owned external-root timer
                root.destroy()
            worker.join(3)
            assert not worker.is_alive() and wrong_thread == ["WRONG_THREAD"]
            app.close()
            effects.assert_clean()
        del view, helper, app, root, worker, collect, guards, effects, patcher
        gc.collect()  # creator thread owns retirement of every test Tk cycle
        assert all(ref() is None for ref in roots), "Tk root survived main-thread retirement"
        worker = threading.Thread(target=gc.collect)
        worker.start()
        worker.join(3)
        assert not worker.is_alive()
        del worker
    assert not errors
    print("833_TK_GC_CHILD_OK", flush=True)


@unittest.skipUnless(os.name == "nt", "Native Tcl finalization child")
class Phase833IsolatedGC(unittest.TestCase):
    def test_fault_and_external_child_retirement_before_successor_dispatch(self):
        result = subprocess.run([sys.executable, "-B", "-c",
            "from tests.test_phase_833_tk_completion import _native_retirement_child; _native_retirement_child()"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("833_TK_RETIREMENT_CHILD_OK", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_adversarial_worker_gc_during_owned_lifecycle_and_after_retirement(self):
        result = subprocess.run([sys.executable, "-B", "-c",
            "from tests.test_phase_833_tk_completion import _gc_child; _gc_child()"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("833_TK_GC_CHILD_OK", result.stdout)
        self.assertEqual(result.stderr, "")


def tearDownModule():
    if threading.current_thread() is not threading.main_thread():
        raise AssertionError("Phase 8.33 Tk cleanup requires creator thread")
    gc.collect()
    survivors = [ref for ref in _retired_tk_roots if ref() is not None]
    if survivors:
        raise AssertionError("Phase 8.33 test Tcl graph survived creator-thread cleanup")
    _retired_tk_roots.clear()
