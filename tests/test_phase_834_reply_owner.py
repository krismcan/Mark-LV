"""Fake-only Increment A adversaries. No Tk/credentials/provider or UI claim."""

import copy
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import textwrap
import threading
import unittest
from unittest.mock import patch

from nayeon.desktop_alpha import reply_worker
from nayeon.desktop_alpha.reply_contracts import (
    DEADLINE_MS, MAX_CLOCK_MS, SIMULATED_TEXT, RefusalCode, ReplyContext,
    ReplyKind, ReplyRefused, ReplyRequest, ReplyResult, ReplyState, ReplyTicket,
)
from nayeon.desktop_alpha.reply_owner import ReplyOwner


class ReplyOwnerTests(unittest.TestCase):
    def setUp(self):
        self.root = object()
        self.context = ReplyContext(self.root, object(), 1, object(), 0)
        self.owner = ReplyOwner(self.root)
        self.assertTrue(self.owner.bind_context(self.context))
        self.held_lock = None

    def tearDown(self):
        self.release()
        self.owner.request_close()
        thread = self.owner._thread
        if thread is not None and thread.ident is not None:
            thread.join(2)
            self.assertFalse(thread.is_alive(), "test-owned finite worker did not exit")
        self.owner.retire(now_ms=self.owner._clock)
        self.assertFalse(self.owner.has_worker)
        self.assertTrue(self.owner.destroy())

    def start(self, *, now=0, prompt="hello"):
        return self.owner.start(prompt, context=self.context, now_ms=now, human_requested=True)

    def hold(self, *, now=0):
        """External test-owned lock holds the EXACT production target.

        No alternate responder/worker/callback is passed to production. The
        mailbox lock is acquired before native start and released by the test.
        """
        original = threading.Thread.start

        def start(thread):
            self.assertIs(thread._target, reply_worker.run_fake_reply)
            self.assertIsNone(thread._target.__closure__)
            self.assertFalse(thread.daemon)
            request, event, mailbox = thread._args
            self.assertIs(type(request), ReplyRequest)
            self.assertIs(type(event), threading.Event)
            self.assertIs(type(mailbox), reply_worker.ReplyMailbox)
            mailbox._lock.acquire()
            self.held_lock = mailbox._lock
            original(thread)

        with patch.object(threading.Thread, "start", new=start):
            return self.start(now=now)

    def release(self):
        if self.held_lock is not None:
            self.held_lock.release()
            self.held_lock = None

    def exited(self):
        self.owner._thread.join(2)
        self.assertFalse(self.owner._thread.is_alive())

    def poll(self, ticket, *, now=0, context=None):
        return self.owner.poll(ticket, context=self.context if context is None else context,
                               now_ms=now)

    def test_initial_bind_requires_plain_tokens_and_exact_root(self):
        other = ReplyOwner(object())
        self.assertFalse(other.bind_context(self.context))
        for bad in (object(), replace(self.context, root_identity=[]),
                    replace(self.context, generation=True), replace(self.context, epoch=-1)):
            self.assertFalse(self.owner.bind_context(bad))
        with self.assertRaises(ReplyRefused):
            ReplyOwner([])

    def test_one_reply_consumed_before_return_and_no_replay(self):
        ticket = self.start(prompt="Do not echo this unique input")
        self.exited()
        thread = self.owner._thread
        with patch.object(thread, "join", wraps=thread.join) as joined:
            result = self.poll(ticket)
        joined.assert_called_once_with(0)
        self.assertEqual(result.text, SIMULATED_TEXT)
        self.assertNotIn("unique input", result.text)
        self.assertIs(result.kind, ReplyKind.SIMULATED)
        self.assertIs(self.owner.state, ReplyState.RETIRED)
        self.assertIsNone(self.owner._active)
        self.assertFalse(self.owner.has_worker)
        self.assertIsNone(self.poll(ticket))

    def test_copied_forged_foreign_tickets_have_no_effect(self):
        ticket = self.hold()
        for forged in (ReplyTicket(), copy.copy(ticket), copy.deepcopy(ticket), object(), None):
            self.assertIsNot(forged, ticket)
            self.assertFalse(self.owner.cancel(forged))
            self.assertIsNone(self.poll(forged, now=MAX_CLOCK_MS))
            self.assertIs(self.owner._active, ticket)
            self.assertEqual(self.owner._clock, 0)
            self.assertFalse(self.owner._event.is_set())
        self.release()
        self.exited()
        self.assertIsNotNone(self.poll(ticket))

    def test_stale_a_cannot_cancel_expire_or_retire_b(self):
        a = self.start()
        self.exited()
        self.assertIsNotNone(self.poll(a))
        self.context = replace(self.context, view_identity=object(), generation=2, epoch=1)
        self.assertTrue(self.owner.bind_context(self.context))
        b = self.hold(now=1)
        thread = self.owner._thread
        self.assertFalse(self.owner.cancel(a))
        self.assertIsNone(self.poll(a, now=MAX_CLOCK_MS))
        self.assertIs(self.owner._thread, thread)
        self.assertIs(self.owner._active, b)
        self.assertEqual(self.owner._clock, 1)
        self.release()
        self.exited()
        self.assertIsNotNone(self.poll(b, now=1))

    def test_replacement_waits_for_physical_exit_join_and_drain(self):
        ticket = self.hold()
        thread = self.owner._thread
        self.owner.cancel(ticket)
        self.assertIs(self.owner.state, ReplyState.DRAINING)
        with patch.object(thread, "join", side_effect=AssertionError("live join")) as join:
            self.assertIsNone(self.poll(ticket))
            self.assertFalse(self.owner.retire(now_ms=0))
            join.assert_not_called()
        with self.assertRaises(ReplyRefused) as error:
            self.start()
        self.assertIs(error.exception.code, RefusalCode.BUSY)
        self.release()
        self.exited()
        with patch.object(thread, "join", wraps=thread.join) as join:
            self.assertIsNone(self.poll(ticket))
        join.assert_called_once_with(0)
        b = self.start(now=1)
        self.exited()
        self.assertIsNotNone(self.poll(b, now=1))

    def test_exited_but_unconsumed_worker_still_blocks_admission(self):
        ticket = self.start()
        self.exited()
        with self.assertRaises(ReplyRefused) as error:
            self.start()
        self.assertIs(error.exception.code, RefusalCode.BUSY)
        self.assertTrue(self.owner.has_worker)
        self.assertIs(self.owner.state, ReplyState.RUNNING)
        self.assertIsNotNone(self.poll(ticket))

    def test_cancel_revokes_before_event_and_empty_mailbox_retires(self):
        ticket = self.hold()
        event = self.owner._event
        original = event.set

        def signal():
            self.assertIsNone(self.owner._active)
            self.assertIs(self.owner.state, ReplyState.DRAINING)
            original()

        with patch.object(event, "set", new=signal):
            self.assertTrue(self.owner.cancel(ticket))
        self.release()
        self.exited()
        self.assertTrue(self.owner._mailbox._queue.empty())
        self.assertIsNone(self.poll(ticket))
        self.assertFalse(self.owner.has_worker)
        self.assertFalse(self.owner.poisoned)

    def test_navigation_defers_and_copied_context_cannot_deliver(self):
        ticket = self.hold()
        new = replace(self.context, generation=2)
        self.assertFalse(self.owner.bind_context(new))
        self.assertIs(self.owner._context, self.context)
        self.assertIs(self.owner.state, ReplyState.DRAINING)
        self.release()
        self.exited()
        self.assertIsNone(self.poll(ticket))
        self.assertTrue(self.owner.bind_context(new))
        self.context = new
        b = self.start(now=1)
        self.exited()
        self.assertIsNone(self.poll(b, now=1, context=copy.copy(new)))

    def test_admission_requires_exact_context_human_and_valid_prompt(self):
        with patch.object(threading.Thread, "start") as start:
            for context, human in ((copy.copy(self.context), True), (self.context, False),
                                   (self.context, 1)):
                with self.assertRaises(ReplyRefused):
                    self.owner.start("hello", context=context, now_ms=0, human_requested=human)
            for prompt in ("", " ", "x" * 513, "a\n", "\x00", "\u200b", "\ud800",
                           "e\u0301", "\u2028", object()):
                with self.assertRaises(ReplyRefused) as error:
                    self.start(prompt=prompt)
                self.assertIs(error.exception.code, RefusalCode.INPUT)
            start.assert_not_called()
        ticket = self.start(prompt="\U0001f600" * 512)
        self.exited()
        self.assertIsNotNone(self.poll(ticket))

    def test_deadline_revokes_but_does_not_retire_live_worker(self):
        ticket = self.hold(now=7)
        self.assertIsNone(self.poll(ticket, now=7 + DEADLINE_MS - 1))
        self.assertIs(self.owner._active, ticket)
        self.assertIsNone(self.poll(ticket, now=7 + DEADLINE_MS))
        self.assertIsNone(self.owner._active)
        self.assertTrue(self.owner._event.is_set())
        self.assertTrue(self.owner.has_worker)
        self.assertIs(self.owner.state, ReplyState.DRAINING)
        self.release()
        self.exited()
        self.assertIsNone(self.poll(ticket, now=7 + DEADLINE_MS))

    def test_already_completed_result_at_deadline_is_discarded(self):
        ticket = self.start()
        self.exited()
        self.assertIsNone(self.poll(ticket, now=DEADLINE_MS))
        self.assertFalse(self.owner.has_worker)

    def test_invalid_or_backwards_clock_poison_and_discard(self):
        ticket = self.start(now=10)
        self.exited()
        self.assertIsNone(self.poll(ticket, now=9))
        self.assertTrue(self.owner.poisoned)
        for now in (True, -1, MAX_CLOCK_MS + 1, 0.0):
            other = ReplyOwner(self.root)
            other.bind_context(self.context)
            with self.assertRaises(ReplyRefused) as error:
                other.start("hello", context=self.context, now_ms=now, human_requested=True)
            self.assertIs(error.exception.code, RefusalCode.CLOCK)
            self.assertFalse(other.has_worker)

    def test_malformed_foreign_and_duplicate_mailbox_outputs_poison(self):
        factories = (
            lambda r: None,
            lambda r: object(),
            lambda r: ReplyResult(copy.copy(r), ReplyKind.SIMULATED, SIMULATED_TEXT),
            lambda r: ReplyResult(r, "simulated", SIMULATED_TEXT),
            lambda r: ReplyResult(r, ReplyKind.SIMULATED, "user-controlled"),
            lambda r: ReplyResult(r, ReplyKind.SIMULATED, "x" * 2049),
        )
        for factory in factories:
            with self.subTest(factory=factory):
                owner = ReplyOwner(self.root)
                owner.bind_context(self.context)
                ticket = owner.start("hello", context=self.context, now_ms=0, human_requested=True)
                owner._thread.join(2)
                self.assertFalse(owner._thread.is_alive())
                mailbox = owner._mailbox
                mailbox._queue.get_nowait()
                mailbox._queue.put_nowait(factory(owner._request))
                self.assertIsNone(owner.poll(ticket, context=self.context, now_ms=0))
                self.assertTrue(owner.poisoned)
                self.assertFalse(owner.has_worker)
        ticket = self.start()
        self.exited()
        mailbox = self.owner._mailbox
        with mailbox._queue.mutex:
            mailbox._queue.queue.append(ReplyResult(self.owner._request,
                                                    ReplyKind.SIMULATED, SIMULATED_TEXT))
        self.assertIsNone(self.poll(ticket))
        self.assertTrue(self.owner.poisoned)

    def test_close_and_poison_keep_live_slot_until_explicit_retirement(self):
        self.hold()
        thread = self.owner._thread
        self.owner.poison()
        self.assertTrue(self.owner.poisoned)
        self.assertIs(self.owner.state, ReplyState.DRAINING)
        self.owner.request_close()
        self.assertIs(self.owner.state, ReplyState.CLOSING)
        self.assertFalse(self.owner.destroy())
        self.assertFalse(self.owner.retire(now_ms=0))
        self.assertIs(self.owner._thread, thread)
        self.release()
        self.exited()
        self.assertTrue(self.owner.retire(now_ms=0))
        self.assertTrue(self.owner.destroy())
        self.assertIs(self.owner.state, ReplyState.DESTROYED)
        with self.assertRaises(ReplyRefused):
            self.start()

    def test_dynamic_worker_responder_and_injection_keywords_refused_before_thread(self):
        for name in ("run_fake_reply", "simulated_reply", "ReplyMailbox"):
            owner = ReplyOwner(self.root)
            owner.bind_context(self.context)
            with patch.object(reply_worker, name, new=lambda *args: None):
                with patch.object(threading.Thread, "start") as start:
                    with self.assertRaises(ReplyRefused):
                        owner.start("hello", context=self.context, now_ms=0, human_requested=True)
                    start.assert_not_called()
            self.assertTrue(owner.poisoned)
            self.assertFalse(owner.has_worker)
        for keyword in ("worker", "responder", "thread_factory"):
            with patch.object(threading.Thread, "start") as start:
                with self.assertRaises(TypeError):
                    self.owner.start("hello", context=self.context, now_ms=0,
                                     human_requested=True, **{keyword: lambda: None})
                start.assert_not_called()

    def test_start_raise_after_effect_retains_slot_and_never_admits_replacement(self):
        original = threading.Thread.start

        def fail(thread):
            thread._args[2]._lock.acquire()
            self.held_lock = thread._args[2]._lock
            original(thread)
            raise RuntimeError("private exception must not escape")

        with patch.object(threading.Thread, "start", new=fail):
            with self.assertRaises(ReplyRefused) as error:
                self.start()
        self.assertEqual(str(error.exception), "REPLY_UNAVAILABLE")
        self.assertTrue(self.owner.poisoned)
        self.assertTrue(self.owner.has_worker)
        thread = self.owner._thread
        self.assertFalse(self.owner.retire(now_ms=0))
        self.assertIs(self.owner._thread, thread)
        with self.assertRaises(ReplyRefused) as error:
            self.start()
        self.assertIs(error.exception.code, RefusalCode.POISONED)
        self.release()
        self.exited()
        self.assertTrue(self.owner.retire(now_ms=0))
        with self.assertRaises(ReplyRefused):
            self.start()

    def test_public_worker_replaced_before_owner_import_refused_without_thread(self):
        # A fresh interpreter prevents an already-imported owner's anchors from
        # hiding the import-order defect. Only the public worker is replaced.
        code = textwrap.dedent("""
            import importlib
            import threading
            import unittest
            from unittest.mock import Mock, patch
            from nayeon.desktop_alpha import reply_worker
            from nayeon.desktop_alpha.reply_contracts import (
                RefusalCode, ReplyContext, ReplyRefused,
            )

            check = unittest.TestCase()
            substitute = Mock(side_effect=AssertionError("untrusted worker"))
            with patch.object(reply_worker, "run_fake_reply", new=substitute):
                module = importlib.import_module("nayeon.desktop_alpha.reply_owner")
                check.assertIs(module._WORKER, reply_worker._REVIEWED_WORKER)
                root = object()
                context = ReplyContext(root, object(), 1, object(), 0)
                owner = module.ReplyOwner(root)
                check.assertTrue(owner.bind_context(context))
                with patch.object(threading, "Thread") as constructor:
                    with check.assertRaises(ReplyRefused) as error:
                        owner.start("hello", context=context, now_ms=0,
                                    human_requested=True)
                    check.assertIs(error.exception.code, RefusalCode.UNAVAILABLE)
                    constructor.assert_not_called()
                    constructor.return_value.start.assert_not_called()
                substitute.assert_not_called()
                check.assertTrue(owner.poisoned)
                check.assertFalse(owner.has_worker)
                owner.request_close()
                check.assertTrue(owner.destroy())
        """)
        result = subprocess.run([sys.executable, "-B", "-c", code],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_start_raise_before_effect_allows_close_but_never_readmission(self):
        with patch.object(threading.Thread, "start",
                          side_effect=RuntimeError("private before-start failure")):
            with self.assertRaises(ReplyRefused) as error:
                self.start()
        self.assertIs(error.exception.code, RefusalCode.UNAVAILABLE)
        self.assertTrue(self.owner.poisoned)
        self.assertTrue(self.owner.has_worker)
        self.assertIsNone(self.owner._active)
        thread = self.owner._thread
        self.assertIsNone(thread.ident)
        self.assertFalse(thread._started.is_set())
        with self.assertRaises(ReplyRefused) as error:
            self.start()
        self.assertIs(error.exception.code, RefusalCode.POISONED)
        self.owner.request_close()
        self.assertFalse(self.owner.destroy())
        with patch.object(thread._started, "is_set",
                          side_effect=RuntimeError("private launch evidence failure")):
            self.assertFalse(self.owner.retire(now_ms=0))
            self.assertIs(self.owner._thread, thread)
            self.assertFalse(self.owner.destroy())
        with patch.object(thread, "join", side_effect=AssertionError("unstarted join")) as join:
            self.assertTrue(self.owner.retire(now_ms=0))
            join.assert_not_called()
        self.assertFalse(self.owner.has_worker)
        self.assertTrue(self.owner.poisoned)
        with self.assertRaises(ReplyRefused) as error:
            self.start()
        self.assertIs(error.exception.code, RefusalCode.CLOSED)
        self.assertTrue(self.owner.destroy())

    def test_failed_start_pending_native_launch_retains_slot_until_exit_and_join(self):
        original = threading.Thread.start
        launches = []

        def pending(thread):
            # Reproduce native-start's pre-bootstrap interval: no ident yet,
            # but a registered launch that must not be treated as unstarted.
            with threading._active_limbo_lock:
                threading._limbo[thread] = thread
            launches.append(thread)
            raise RuntimeError("private pending-start failure")

        try:
            with patch.object(threading.Thread, "start", new=pending):
                with self.assertRaises(ReplyRefused):
                    self.start()
            thread = self.owner._thread
            self.assertIsNone(thread.ident)
            self.assertFalse(thread.is_alive())
            self.assertTrue(self.owner.poisoned)
            self.owner.request_close()
            self.assertFalse(self.owner.retire(now_ms=0))
            self.assertIs(self.owner._thread, thread)
            self.assertFalse(self.owner.destroy())
        finally:
            # Complete the test-owned pending launch, even if an assertion
            # failed, so teardown can observe real physical exit and join.
            thread = launches[0] if launches else None
            if thread is not None:
                with threading._active_limbo_lock:
                    threading._limbo.pop(thread, None)
                original(thread)
        self.exited()
        with patch.object(thread, "join", wraps=thread.join) as joined:
            self.assertTrue(self.owner.retire(now_ms=0))
            joined.assert_called_once_with(0)
        self.assertTrue(self.owner.destroy())

    def test_constructor_failure_poison_has_no_physical_worker(self):
        with patch("nayeon.desktop_alpha.reply_owner.threading.Thread",
                   side_effect=RuntimeError("private constructor failure")):
            with self.assertRaises(ReplyRefused) as error:
                self.start()
        self.assertEqual(str(error.exception), "REPLY_UNAVAILABLE")
        self.assertTrue(self.owner.poisoned)
        self.assertFalse(self.owner.has_worker)
        self.assertIsNone(self.owner._active)
        self.assertIs(self.owner.state, ReplyState.RETIRED)

    def test_deadline_signal_reentrancy_cannot_retire_a_and_admit_b(self):
        ticket = self.start()
        self.exited()
        thread = self.owner._thread
        original = self.owner._event.set
        observations = []

        def signal():
            observations.append(self.poll(ticket, now=DEADLINE_MS))
            with self.assertRaises(ReplyRefused) as error:
                self.start(now=DEADLINE_MS)
            self.assertIs(error.exception.code, RefusalCode.BUSY)
            self.assertIs(self.owner._thread, thread)
            original()

        with patch.object(self.owner._event, "set", new=signal):
            self.assertIsNone(self.poll(ticket, now=DEADLINE_MS))
        self.assertEqual(observations, [None])
        self.assertFalse(self.owner.has_worker)
        self.assertFalse(self.owner.poisoned)

    def test_cancel_signal_reentrancy_cannot_admit_b_or_recurse(self):
        ticket = self.start()
        self.exited()
        original = self.owner._event.set
        signals = []

        def signal():
            signals.append(True)
            self.assertTrue(self.owner.cancel(ticket))
            self.assertIsNone(self.poll(ticket))
            with self.assertRaises(ReplyRefused) as error:
                self.start()
            self.assertIs(error.exception.code, RefusalCode.BUSY)
            original()

        with patch.object(self.owner._event, "set", new=signal):
            self.assertTrue(self.owner.cancel(ticket))
        self.assertEqual(signals, [True])
        self.assertIsNone(self.poll(ticket))
        self.assertFalse(self.owner.poisoned)

    def test_late_a_result_cannot_be_delivered_as_b(self):
        a = self.start()
        self.exited()
        result_a = self.poll(a)
        b = self.start(now=1)
        self.exited()
        self.owner._mailbox._queue.get_nowait()
        self.owner._mailbox._queue.put_nowait(result_a)
        self.assertIsNone(self.poll(b, now=1))
        self.assertTrue(self.owner.poisoned)

    def test_observation_join_and_drain_exceptions_retain_slot_and_revoke(self):
        ticket = self.start()
        self.exited()
        thread = self.owner._thread
        for name in ("is_alive", "join"):
            with patch.object(thread, name, side_effect=RuntimeError("private")):
                self.assertIsNone(self.poll(ticket))
            self.assertIs(self.owner._thread, thread)
            self.assertIsNone(self.owner._active)
            self.assertTrue(self.owner.poisoned)
        mailbox = self.owner._mailbox
        original = reply_worker.ReplyMailbox._drain

        def fail_after_drain(box):
            original(box)
            raise RuntimeError("private")

        with patch.object(reply_worker.ReplyMailbox, "_drain", new=fail_after_drain):
            self.assertIsNone(self.poll(ticket))
        self.assertIs(self.owner._thread, thread)
        self.assertTrue(self.owner.retire(now_ms=0))

    def test_signal_failure_poison_does_not_restore_authority(self):
        ticket = self.hold()
        with patch.object(self.owner._event, "set", side_effect=RuntimeError("private")):
            self.assertTrue(self.owner.cancel(ticket))
        self.assertIsNone(self.owner._active)
        self.assertTrue(self.owner.poisoned)
        self.release()
        self.exited()
        self.assertIsNone(self.poll(ticket))

    def test_reentrant_start_cannot_create_second_worker(self):
        original = threading.Thread.start
        starts = []

        def start(thread):
            starts.append(thread)
            with self.assertRaises(ReplyRefused) as error:
                self.start()
            self.assertIs(error.exception.code, RefusalCode.BUSY)
            original(thread)

        with patch.object(threading.Thread, "start", new=start):
            ticket = self.start()
        self.assertEqual(len(starts), 1)
        self.exited()
        self.assertIsNotNone(self.poll(ticket))

    def test_wrong_thread_is_first_gate_before_validation_state_and_effects(self):
        ticket = self.hold()
        before = dict(self.owner.__dict__)
        calls = (
            lambda: self.owner.state, lambda: self.owner.poisoned, lambda: self.owner.has_worker,
            lambda: self.owner.bind_context(object()),
            lambda: self.owner.start(object(), context=object(), now_ms=object(), human_requested=True),
            lambda: self.owner.cancel(ticket), lambda: self.owner.poison(),
            lambda: self.owner.request_close(), lambda: self.owner.destroy(),
            lambda: self.owner.retire(now_ms=object()),
            lambda: self.owner.poll(ticket, context=object(), now_ms=object()),
        )
        errors = []

        def wrong_thread():
            for call in calls:
                try:
                    call()
                except RuntimeError as error:
                    errors.append(str(error))

        thread = threading.Thread(target=wrong_thread)
        thread.start()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ["WRONG_THREAD"] * len(calls))
        self.assertEqual(self.owner.__dict__, before)
        self.assertFalse(self.owner._event.is_set())


if __name__ == "__main__":
    unittest.main()
