"""Deterministic one-shot admission adversaries; no Tcl, workers or effects."""
from dataclasses import replace
import ast
import inspect
import unittest
from unittest import mock

from nayeon.desktop_alpha import offline_completion_admission as completion
from nayeon.desktop_alpha.conversation_session import (
    OfflineConversationSession, SessionRefused, SubmissionState,
)


class Scheduler:
    def __init__(self):
        self.timers = {}
        self.calls = []
        self.serial = 0
        self.on_after = self.on_cancel = None

    def after(self, delay, callback):
        self.serial += 1
        handle = "owned-" + str(self.serial)
        self.calls.append(("after", delay, handle))
        self.timers[handle] = callback
        if self.on_after:
            self.on_after(handle, callback)
        return handle

    def after_cancel(self, handle):
        self.calls.append(("cancel", handle))
        if self.on_cancel:
            self.on_cancel(handle)
        self.timers.pop(handle, None)

    def fire(self, handle):
        self.timers.pop(handle)()


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.root = Scheduler()
        self.helper = completion.DelayedOfflineCompletion(self.root)
        self.identity = object()
        self.session = OfflineConversationSession(self.identity)
        self.pane = self.session.activate_view(self.identity, object())
        self.rendered = []
        self.live = True

    def commit(self, text="synthetic"):
        ticket = self.session.issue_submission(self.identity, self.pane, text)
        self.session.claim_submission(self.identity, self.pane, ticket)
        return self.session.commit_submission(self.identity, self.pane, ticket)

    def start(self, commit=None, **overrides):
        args = dict(pane=self.pane, generation=1,
                    read_snapshot=lambda: self.session.snapshot,
                    current=lambda: self.live,
                    render=lambda text, eligible: self.rendered.append(text) if eligible() else None)
        args.update(overrides)
        return self.helper.start(commit if commit is not None else self.commit(), **args)

    def test_postcommit_one_shot_consumed_before_render_and_never_changes_transcript(self):
        commit = self.commit("open notepad")
        self.assertTrue(self.start(commit))
        handle = self.helper._handle
        callback = self.root.timers[handle]
        self.assertEqual(self.root.calls, [("after", 150, handle)])
        self.root.fire(handle)
        callback()
        self.assertEqual(self.rendered, [completion.COMPLETE])
        self.assertIs(self.session.snapshot, commit.snapshot)
        self.assertIsNone(self.helper._pending)
        self.assertEqual(self.helper.state, completion.CompletionState.IDLE)
        self.assertEqual(self.root.timers, {})

    def test_exact_snapshot_commit_validation_and_request_exhaustion(self):
        commit = self.commit()
        for bad in (None, object(), replace(commit, state=SubmissionState.ISSUED),
                    replace(commit, snapshot=replace(commit.snapshot, closed=True)),
                    replace(commit, snapshot=replace(commit.snapshot, revision=77))):
            with self.subTest(bad=type(bad)):
                self.assertFalse(self.helper.start(bad, pane=self.pane, generation=1,
                    read_snapshot=lambda: self.session.snapshot,
                    current=lambda: True, render=self.rendered.append))
        self.assertFalse(self.start(commit, read_snapshot=lambda: replace(commit.snapshot)))
        self.helper._index = completion.MAX_REQUEST_INDEX
        self.assertFalse(self.start(commit))
        self.assertEqual(self.root.calls, [])

    def test_stale_a_after_b_and_foreign_timer_retained(self):
        self.root.timers["foreign"] = lambda: None
        self.assertTrue(self.start())
        a = self.helper._handle
        callback = self.root.timers[a]
        self.assertTrue(self.start(self.commit("B")))
        b = self.helper._handle
        callback()
        self.assertEqual(self.helper._handle, b)
        self.assertEqual(self.rendered, [])
        self.assertEqual(set(self.root.timers), {"foreign", b})
        self.root.fire(b)
        self.assertEqual(self.rendered, [completion.COMPLETE])
        self.assertIn("foreign", self.root.timers)

    def test_rejected_send_does_not_retire_a(self):
        self.assertTrue(self.start())
        a = self.helper._handle
        with self.assertRaises(SessionRefused):
            self.commit("\n")
        self.assertEqual(self.helper._handle, a)
        self.assertEqual(len(self.root.calls), 1)

    def test_unicode_input_bounds_preserve_a_and_exact_snapshot_identity(self):
        self.assertTrue(self.start(self.commit("\U0001f600" * 512)))
        a = self.helper._handle
        for text in ("x" * 513, "\U0001f600" * 513, "\u202e", "e\u0301", "\ud800"):
            with self.subTest(length=len(text)), self.assertRaises(SessionRefused):
                self.commit(text)
            self.assertEqual(self.helper._handle, a)
        self.session._snapshot = replace(self.session.snapshot)
        self.root.fire(a)
        self.assertEqual(self.rendered, [])

    def test_copied_foreign_ticket_and_request_integer_cannot_deliver(self):
        self.helper._index = completion.MAX_REQUEST_INDEX - 1
        self.assertTrue(self.start())
        ticket = self.helper._pending
        self.assertEqual(ticket.index, completion.MAX_REQUEST_INDEX)
        for forged in (replace(ticket), replace(ticket, owner=object()), ticket.index):
            self.helper._deliver(forged)
        self.assertEqual(self.rendered, [])
        self.root.fire(self.helper._handle)
        self.assertEqual(self.rendered, [completion.COMPLETE])
        self.assertFalse(self.start(self.commit("exhausted")))
        self.assertEqual(self.root.serial, 1)

    def test_registration_fault_before_and_after_effect_permanently_poison(self):
        for effective in (False, True):
            self.setUp()
            real = self.root.after
            def fail(delay, callback):
                if effective:
                    real(delay, callback)
                raise RuntimeError("private exception must not render")
            with self.subTest(effective=effective), mock.patch.object(self.root, "after", side_effect=fail):
                self.assertFalse(self.start())
            self.assertEqual(self.helper.state, completion.CompletionState.POISONED)
            self.assertFalse(self.start(self.commit("B")))
            self.assertLessEqual(len(self.root.timers), 1)
            for callback in list(self.root.timers.values()):
                callback()
            self.assertEqual(self.rendered, [])

    def test_cancel_fault_before_and_after_effect_never_registers_b(self):
        for effective in (False, True):
            self.setUp()
            self.assertTrue(self.start())
            a = self.helper._handle
            callback = self.root.timers[a]
            def fail(handle):
                self.assertEqual(handle, a)
                if effective:
                    self.root.timers.pop(handle, None)
                raise RuntimeError("cancel uncertainty")
            self.root.on_cancel = fail
            self.assertFalse(self.start(self.commit("B")))
            callback()
            self.assertEqual(self.helper.state, completion.CompletionState.POISONED)
            self.assertFalse(self.start(self.commit("C")))
            self.assertEqual(self.root.serial, 1)
            self.assertEqual(self.rendered, [])

    def test_nested_start_cancel_and_synchronous_delivery_retire_exact_a(self):
        for operation in ("start", "cancel", "deliver"):
            self.setUp()
            nested = []
            def reenter(handle, callback):
                if operation == "start":
                    nested.append(self.start(self.commit("B")))
                elif operation == "cancel":
                    nested.append(self.helper.cancel())
                else:
                    callback()
            self.root.on_after = reenter
            self.assertFalse(self.start())
            self.assertEqual(self.root.serial, 1)
            self.assertEqual(self.root.calls[-1], ("cancel", "owned-1"))
            self.assertEqual(self.root.timers, {})
            self.assertEqual(self.rendered, [])
            self.assertTrue(all(value is False for value in nested))

    def test_cancel_reentrancy_never_publishes_b(self):
        self.assertTrue(self.start())
        nested = []
        def reenter(handle):
            nested.append(self.start(self.commit("nested B")))
            nested.append(self.helper.cancel())
        self.root.on_cancel = reenter
        self.assertTrue(self.helper.cancel())
        self.assertEqual(nested, [False, False])
        self.assertEqual(self.root.serial, 1)
        self.assertEqual(self.root.timers, {})

    def test_child_destroy_python_only_poison_pending_but_not_root_closed(self):
        self.assertTrue(self.start())
        callback = self.root.timers[self.helper._handle]
        calls = list(self.root.calls)
        self.helper.pane_destroyed()
        self.assertEqual(self.root.calls, calls)
        self.assertEqual(self.helper.state, completion.CompletionState.POISONED)
        callback()
        self.assertFalse(self.start(self.commit("new pane")))
        self.helper.destroyed()
        self.assertEqual(self.helper.state, completion.CompletionState.CLOSED)
        self.assertEqual(self.rendered, [])

    def test_destroy_during_register_or_cancel_does_not_call_tcl_again(self):
        self.root.on_after = lambda *args: self.helper.destroyed()
        self.assertFalse(self.start())
        self.assertEqual(len(self.root.calls), 1)
        self.assertEqual(self.helper.state, completion.CompletionState.CLOSED)
        self.setUp()
        self.assertTrue(self.start())
        self.root.on_cancel = lambda *args: self.helper.destroyed()
        self.assertFalse(self.helper.cancel())
        self.assertEqual(len(self.root.calls), 2)
        self.assertEqual(self.helper.state, completion.CompletionState.CLOSED)

    def test_each_delivery_seam_reentrancy_revokes_a_before_render(self):
        for seam in ("current", "snapshot"):
            self.setUp()
            nested = [False]
            def invalidate():
                if nested[0]:
                    self.helper.cancel()
                return True
            args = {"current": invalidate} if seam == "current" else {
                "read_snapshot": lambda: (invalidate(), self.session.snapshot)[1]}
            self.assertTrue(self.start(**args))
            nested[0] = True
            self.root.fire(self.helper._handle)
            self.assertEqual(self.rendered, [])

    def test_seam_and_render_exceptions_poison_without_replay(self):
        for seam in ("current", "read_snapshot", "render"):
            self.setUp()
            def fail(*args):
                raise RuntimeError("private")
            if seam == "render":
                self.assertTrue(self.start(render=fail))
                self.root.fire(self.helper._handle)
            else:
                self.assertFalse(self.start(**{seam: fail}))
            self.assertEqual(self.helper.state, completion.CompletionState.POISONED)
            self.assertFalse(self.start(self.commit("B")))
            self.assertEqual(self.rendered, [])

    def test_wrong_thread_first_before_any_state_or_scheduler_effect(self):
        self.assertTrue(self.start())
        ticket = self.helper._pending
        commit = self.commit("prepared B")
        owner_before = self.session.snapshot
        before = dict(vars(self.helper))
        calls = list(self.root.calls)
        with mock.patch.object(completion.threading, "get_ident", return_value=-1):
            for invoke in (lambda: self.helper.state, self.helper.cancel,
                           self.helper.destroyed, self.helper.pane_destroyed,
                           self.helper.publication_failed,
                           lambda: self.helper.is_pending_for(owner_before),
                           lambda: self.helper._deliver(ticket), lambda: self.start(commit)):
                with self.assertRaisesRegex(RuntimeError, "^WRONG_THREAD$"):
                    invoke()
        self.assertEqual(vars(self.helper), before)
        self.assertEqual(self.root.calls, calls)
        self.assertIs(self.session.snapshot, owner_before)

    def test_static_only_one_fixed_timer_no_worker_queue_or_dynamic_tcl(self):
        tree = ast.parse(inspect.getsource(completion))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        timers = [node for node in calls if isinstance(node.func, ast.Attribute)
                  and node.func.attr in {"after", "after_idle"}]
        self.assertEqual(len(timers), 1)
        self.assertEqual(ast.literal_eval(timers[0].args[0]), 150)
        names = {ast.unparse(node.func) for node in calls}
        self.assertFalse(names & {"threading.Thread", "threading.Timer", "eval", "exec", "getattr"})
        source = inspect.getsource(completion)
        for forbidden in (".tk.call", ".eval(", "deletecommand", "import queue", "import socket", "subprocess"):
            self.assertNotIn(forbidden, source)
        for text in (completion.WAITING, completion.COMPLETE, completion.CANCELLED, completion.UNAVAILABLE):
            self.assertLessEqual(len(text), 160)
            self.assertIn("No AI".lower(), text.lower())
