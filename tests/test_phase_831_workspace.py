"""Phase 8.31 native Tk offline-session integration; synthetic storage only."""
from __future__ import annotations

import os
import tkinter as tk
import unittest
import weakref
from unittest import mock

from tests import test_phase_830_application as storage_fixture
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.conversation_session import ResetOperation, EntrySource


_retired_tk_roots = []  # weak observations only; never keeps a Tcl interpreter alive


@unittest.skipUnless(os.name == "nt", "Windows mapped Tk acceptance")
class Phase831WorkspaceTests(unittest.TestCase):
    def setUp(self):
        # Borrow the sealed Phase 8.30 private Windows-directory fixture.
        # It patches known-folder discovery BEFORE app construction.
        storage_fixture.Phase830ProductionAdmissionTests.setUp(self)
        self.root = tk.Tk()
        _retired_tk_roots.append(weakref.ref(self.root))
        self.addCleanup(self._close)
        self.root.withdraw()
        self.app = OfflineWorkspaceApplication(self.root)

    def _close(self):
        if hasattr(self, "app"):
            self.app.close()
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def _send(self, text):
        view = self.app._active_view
        self.assertEqual(view.winfo_name(), "conversation_view")
        view.entry.insert(0, text)
        view.send_button.invoke()
        return self.app._conversation.snapshot

    def test_literal_request_is_unsent_and_no_disk_created(self):
        snapshot = self._send("open notepad")
        self.assertEqual(len(snapshot.entries), 2)
        self.assertEqual(snapshot.entries[0].source, EntrySource.USER)
        self.assertEqual(snapshot.entries[0].payload, "open notepad")
        self.assertIn("No AI request or action", snapshot.entries[1].payload)
        self.assertIn("UNSENT_OFFLINE", self.app._active_view.transcript.get("1.0", "end"))
        self.assertFalse(self.app_dir.exists())

    def test_navigation_preserves_exact_session(self):
        old = self._send("one")
        self.app.show_connection()
        self.app.show_settings()
        self.app.show_conversation()
        self.assertIs(old.session_identity, self.app._conversation.snapshot.session_identity)
        self.assertEqual(self.app._conversation.snapshot.entries, old.entries)
        self._send("two")
        self.assertEqual(len(self.app._conversation.snapshot.entries), 4)
        self.assertFalse(self.app_dir.exists())

    def test_explicit_clear_review_and_one_use_confirm(self):
        self._send("one")
        old = self.app._conversation.snapshot
        view = self.app._active_view
        view.clear_button.invoke()
        review = view._reset_review
        self.assertIsNotNone(review)
        self.assertEqual(review.operation, ResetOperation.CLEAR)
        self.assertEqual(len(self.app._conversation.snapshot.entries), 2)
        view.confirm_button.invoke()
        new = self.app._conversation.snapshot
        self.assertIs(new.session_identity, old.session_identity)
        self.assertEqual(new.entries, ())
        self.assertGreater(new.revision, old.revision)
        self.app._conversation_reset(view, self.app._active_token,
                                     self.app._generation,
                                     self.app._conversation_view, review, True)
        self.assertEqual(self.app._conversation.snapshot, new)

    def test_new_session_changes_epoch_and_dismiss_never_resets(self):
        self._send("first")
        old = self.app._conversation.snapshot
        view = self.app._active_view
        view.new_session_button.invoke()
        view.dismiss_button.invoke()
        self.assertIs(self.app._conversation.snapshot, old)
        view.new_session_button.invoke()
        view.confirm_button.invoke()
        fresh = self.app._conversation.snapshot
        self.assertEqual(fresh.epoch, old.epoch + 1)
        self.assertIsNot(fresh.session_identity, old.session_identity)
        self.assertEqual(fresh.entries, ())

    def test_stale_review_a_cannot_consume_successor_review_b(self):
        self._send("first")
        view = self.app._active_view
        view.clear_button.invoke()
        a = view._reset_review
        view.new_session_button.invoke()
        b = view._reset_review
        self.assertIsNot(a, b)
        self.app._conversation_reset(view, self.app._active_token,
                                     self.app._generation,
                                     self.app._conversation_view, a, True)
        self.assertEqual(len(self.app._conversation.snapshot.entries), 2)
        self.assertIs(view._reset_review, b)
        view.confirm_button.invoke()
        self.assertEqual(self.app._conversation.snapshot.entries, ())

    def test_message_commit_invalidates_reset_review(self):
        view = self.app._active_view
        view.clear_button.invoke()
        old = view._reset_review
        self._send("fresh")
        self.assertIsNone(view._reset_review)
        self.app._conversation_reset(view, self.app._active_token,
                                     self.app._generation,
                                     self.app._conversation_view, old, True)
        self.assertEqual(len(self.app._conversation.snapshot.entries), 2)

    def test_reject_newline_bidi_and_paste_overflow_before_submit(self):
        view = self.app._active_view
        for candidate in ("line\nbreak", "\u202e", "x" * 513):
            view.entry.delete(0, "end")
            view.entry.insert(0, candidate)
            self.assertNotEqual(view.entry.get(), candidate)
        self.assertEqual(self.app._conversation.snapshot.entries, ())
        self.assertFalse(self.app_dir.exists())

    def test_32_pairs_capacity_refuses_extra_without_trim(self):
        for i in range(32):
            self._send(str(i))
        snapshot = self.app._conversation.snapshot
        self.assertEqual(len(snapshot.entries), 64)
        self._send("extra")
        self.assertIs(self.app._conversation.snapshot, snapshot)
        self.assertEqual(len(self.app._conversation.snapshot.entries), 64)

    def test_navigation_stale_view_cannot_add_messages(self):
        old_view = self.app._active_view
        old_token, old_gen = self.app._active_token, self.app._generation
        self.app.show_connection()
        self.app._conversation_send(old_view, old_token, old_gen)
        self.assertEqual(self.app._conversation.snapshot.entries, ())
        self.assertEqual(self.app._active_view.winfo_name(), "connection_view")

    def test_child_destroy_revokes_without_erasing_owned_history(self):
        self._send("first")
        view = self.app._active_view
        view.destroy()
        self.assertIsNone(self.app._conversation_view)
        self.assertEqual(len(self.app._conversation.snapshot.entries), 2)
        self.app.show_conversation()
        self.assertEqual(len(self.app._conversation.snapshot.entries), 2)

    def test_close_revokes_all_and_disposes_history(self):
        self._send("first")
        old_view = self.app._active_view
        old_token, old_gen = self.app._active_token, self.app._generation
        self.app.close()
        self.app._conversation_send(old_view, old_token, old_gen)
        self.assertTrue(self.app._conversation.snapshot.closed)
        self.assertEqual(self.app._conversation.snapshot.entries, ())

    def test_mapped_keyboard_return_saves_only_offline(self):
        self.root.deiconify()
        self.root.update()
        try:
            view = self.app._active_view
            view.entry.focus_force()
            view.entry.insert(0, "mapped event")
            view.entry.event_generate("<Return>")
            self.root.update()
            self.assertEqual(len(self.app._conversation.snapshot.entries), 2)
            self.assertEqual(self.app._conversation.snapshot.entries[0].payload,
                             "mapped event")
            self.assertFalse(self.app_dir.exists())
        finally:
            if self.root.winfo_exists():
                self.root.withdraw()


    def test_exactly_one_reset_timer_then_dismiss_confirm_and_navigation(self):
        def scheduled():
            info = self.root.tk.call("after", "info")
            return set(info if isinstance(info, tuple) else self.root.tk.splitlist(info))
        view = self.app._active_view
        baseline = scheduled()
        for i in range(12):
            button = view.clear_button if i % 2 == 0 else view.new_session_button
            button.invoke()
            active = self.app._conversation_timer
            self.assertIsNotNone(active)
            self.assertIn(active[1], scheduled())
            self.assertLessEqual(len(scheduled() - baseline), 1)
        last = self.app._conversation_timer
        view.dismiss_button.invoke()
        self.assertIsNone(self.app._conversation_timer)
        self.assertNotIn(last[1], scheduled())
        view.clear_button.invoke()
        self.assertIsNotNone(self.app._conversation_timer)
        view.confirm_button.invoke()
        self.assertIsNone(self.app._conversation_timer)
        view.new_session_button.invoke()
        self.assertIsNotNone(self.app._conversation_timer)
        self.app.show_connection()
        self.assertIsNone(self.app._conversation_timer)
        self.assertEqual(scheduled(), baseline)

    def test_external_destroy_cancels_pending_expiry(self):
        view = self.app._active_view
        view.clear_button.invoke()
        self.assertIsNotNone(self.app._conversation_timer)
        view.destroy()
        self.assertIsNone(self.app._conversation_timer)
        self.assertIsNone(self.app._conversation_view)
        self.assertEqual(self.app._conversation.snapshot.entries, ())

    def test_expired_review_does_not_reset_or_leave_timer(self):
        self._send("first")
        view = self.app._active_view
        view.clear_button.invoke()
        review, _after = self.app._conversation_timer
        self.assertIs(view._reset_review, review)
        with mock.patch.object(self.app, "_conversation_now",
                               return_value=review.expires_at_ms):
            self.app._conversation_expire(
                view, self.app._active_token, self.app._generation,
                self.app._conversation_view, review)
        self.assertIsNone(self.app._conversation_timer)
        self.assertIsNone(view._reset_review)
        self.assertEqual(len(self.app._conversation.snapshot.entries), 2)

    def test_render_failure_preserves_authoritative_accepted_pair(self):
        view = self.app._active_view
        with mock.patch.object(view, "render", side_effect=RuntimeError("render failure")):
            view.entry.insert(0, "accepted first")
            view.send_button.invoke()
        self.assertEqual(len(self.app._conversation.snapshot.entries), 2)
        self.assertIn("Display unavailable", str(view.status.cget("text")))
        self.app.show_connection()
        self.app.show_conversation()
        self.assertIn("accepted first", self.app._active_view.transcript.get("1.0", "end"))

    def test_reentrant_navigation_during_view_reset_cleanup_never_forges_reply(self):
        view = self.app._active_view
        view.entry.insert(0, "approved offline")
        original = view.clear_reset
        def navigate(*args, **kwargs):
            self.app.show_connection()
            return original(*args, **kwargs)
        with mock.patch.object(view, "clear_reset", side_effect=navigate):
            view.send_button.invoke()
        # Navigation during a busy operation revokes its old authority; any
        # in-memory result remains UNSENT_OFFLINE, never model VERIFIED.
        entries = self.app._conversation.snapshot.entries
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].payload, "approved offline")
        self.assertEqual(entries[1].state.value, "UNSENT_OFFLINE")
        self.assertFalse(any(e.state.value == "VERIFIED" for e in entries))
        self.app.show_conversation()
        self.assertTrue(self.app._active_view.exists())
        self.assertFalse(self.app_dir.exists())

    def test_transcript_is_not_user_editable_and_has_distinct_tags(self):
        view = self.app._active_view
        self._send("hello")
        before = view.transcript.get("1.0", "end")
        view.transcript.insert("end", "forged verified outcome")
        self.assertEqual(view.transcript.get("1.0", "end"), before)
        self.assertIn("USER", view.transcript.tag_names())
        self.assertIn("LOCAL_STATUS", view.transcript.tag_names())
        self.assertEqual(str(view.transcript.cget("state")), "disabled")

    def test_mapped_mouse_click_and_unicode_supplementary(self):
        self.root.deiconify()
        self.root.update()
        try:
            view = self.app._active_view
            view.entry.insert(0, "\U0001f642" * 512)
            self.root.update()
            button = view.send_button
            button.event_generate("<ButtonPress-1>", x=5, y=5)
            button.event_generate("<ButtonRelease-1>", x=5, y=5)
            self.root.update()
            self.assertEqual(len(self.app._conversation.snapshot.entries), 2)
            self.assertEqual(self.app._conversation.snapshot.entries[0].byte_count, 2048)
        finally:
            if self.root.winfo_exists():
                self.root.withdraw()

    def test_external_root_destroy_revokes_session_and_timers(self):
        self._send("first")
        self.app._active_view.clear_button.invoke()
        self.assertIsNotNone(self.app._conversation_timer)
        self.root.destroy()
        self.assertTrue(self.app._conversation.snapshot.closed)
        self.assertIsNone(self.app._conversation_timer)
        self.assertEqual(self.app._conversation.snapshot.entries, ())


    def test_timer_registration_destroy_between_schedule_and_publication(self):
        view = self.app._active_view
        baseline = set(self.root.tk.call("after", "info"))
        original = self.root.after
        invoked = []
        def injected(ms, callback):
            timer = original(ms, callback)
            invoked.append(timer)
            view.destroy()  # After registered but before owner publishes ID.
            return timer
        with mock.patch.object(self.root, "after", side_effect=injected):
            view.clear_button.invoke()
        self.assertEqual(len(invoked), 1)
        self.assertIsNone(self.app._conversation_timer)
        self.assertIsNone(self.app._conversation_view)
        self.assertNotIn(invoked[0], set(self.root.tk.call("after", "info")))
        self.assertEqual(set(self.root.tk.call("after", "info")), baseline)

    def test_nested_update_and_child_destroy_during_render_preserve_exact_commit(self):
        view = self.app._active_view
        original = view.render
        def nested(snapshot):
            view.destroy()
            self.root.update()
            return original(snapshot)
        with mock.patch.object(view, "render", side_effect=nested):
            view.entry.insert(0, "exact A")
            view.send_button.invoke()
        entries = self.app._conversation.snapshot.entries
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].payload, "exact A")
        self.assertEqual(entries[1].state.value, "UNSENT_OFFLINE")
        self.app.show_conversation()
        self.assertIn("exact A", self.app._active_view.transcript.get("1.0", "end"))

    def test_status_display_exception_cannot_create_false_verified_result(self):
        view = self.app._active_view
        original = view.show_status
        n = []
        def once(text):
            n.append(text)
            if len(n) == 1:
                raise RuntimeError("Synthetic status rendering failure")
            return original(text)
        with mock.patch.object(view, "show_status", side_effect=once):
            view.entry.insert(0, "exact B")
            view.send_button.invoke()
        entries = self.app._conversation.snapshot.entries
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].payload, "exact B")
        self.assertEqual(entries[1].state.value, "UNSENT_OFFLINE")
        self.assertTrue(all(e.state.value != "VERIFIED" for e in entries))

    def test_nested_text_events_during_writable_render_do_not_edit_payload(self):
        self.root.deiconify()
        self.root.update()
        try:
            view = self.app._active_view
            insert = view.transcript.insert
            evidence = []
            base_tags = view.transcript.bindtags()
            canary = "Nayeon831PasteCanary"
            observed = []
            # Insert a deterministic downstream probe. It never accesses the
            # system clipboard, and it consumes the virtual paste in control.
            view.transcript.bind_class(
                canary, "<<Paste>>", lambda e: (observed.append("delivered"), "break")[1])
            view.transcript.bindtags((base_tags[0], canary, *base_tags[1:]))
            def nested(*args, **kwargs):
                result = insert(*args, **kwargs)
                # Inject only AFTER both tagged entries were inserted,
                # BEFORE the owner restores the disabled Text state.
                if len(args) > 1 and str(args[1]).startswith("LOCAL_STATUS /") and not evidence:
                    self.assertEqual(str(view.transcript.cget("state")), "normal")
                    before = view.transcript.get("1.0", "end")
                    view.transcript.focus_force()
                    view.transcript.event_generate("<KeyPress>", keysym="x")
                    view.transcript.event_generate("<<Paste>>")
                    self.root.update()
                    self.assertEqual(observed, [], "Paste escaped widget break")
                    # Negative control: remove the no-edit widget bindtag.
                    # The same event MUST then reach canary and stop there,
                    # without invoking Tk class paste or touching clipboard.
                    view.transcript.bindtags((canary, *base_tags[1:]))
                    view.transcript.event_generate("<<Paste>>")
                    self.root.update()
                    self.assertEqual(observed, ["delivered"])
                    view.transcript.bindtags((base_tags[0], canary, *base_tags[1:]))
                    after = view.transcript.get("1.0", "end")
                    evidence.append((before, after))
                    self.assertEqual(after, before, "Nested Tk event edited trusted transcript")
                return result
            with mock.patch.object(view.transcript, "insert", side_effect=nested):
                view.entry.insert(0, "immutable payload")
                view.send_button.invoke()
            self.assertEqual(len(evidence), 1)
            shown = view.transcript.get("1.0", "end")
            expected_user = "USER\nimmutable payload\n\n"
            expected_status = ("LOCAL_STATUS / UNSENT_OFFLINE\n"
                               + self.app._conversation.snapshot.entries[1].payload + "\n\n")
            self.assertEqual(shown, expected_user + expected_status + "\n")
            self.assertEqual(str(view.transcript.cget("state")), "disabled")
            for tag, expected in (("USER", expected_user), ("LOCAL_STATUS", expected_status)):
                ranges = view.transcript.tag_ranges(tag)
                self.assertEqual(len(ranges), 2)
                self.assertEqual(view.transcript.get(*ranges), expected)
            self.assertTrue(view.transcript.bind("<<Paste>>"))
        finally:
            if "view" in locals() and "base_tags" in locals():
                view.transcript.bindtags(base_tags)
                view.transcript.unbind_class(canary, "<<Paste>>")
            if self.root.winfo_exists():
                self.root.withdraw()

    def test_nfc_control_surrogate_repetition_widget_contract(self):
        view = self.app._active_view
        for candidate in ("e\u0301", "\u202e", "\u2066", "\ud800"):
            self.assertFalse(view._proposed(candidate))
        for _ in range(25):
            view.entry.insert(0, "x" * 513)
            self.assertEqual(view.entry.get(), "")
        self.assertEqual(self.app._conversation.snapshot.entries, ())
        self.assertLessEqual(len(str(view.status.cget("text"))), 160)

    def test_a_exception_cleanup_preserves_successor_b_ticket_review_and_timer(self):
        # Synthetically switch the owner during a trusted callback, just as a
        # nested event could retire A. Never disable the production busy gate.
        from nayeon.desktop_alpha.conversation_session import SubmissionState
        view = self.app._active_view
        owner = self.app._conversation
        root = self.app._conversation_root
        original_commit = owner.commit_submission
        state = {}
        def inject(root_identity, old_auth, old_ticket):
            owner.revoke_view(root, old_auth)
            next_auth = owner.activate_view(root, object())
            self.app._conversation_view = next_auth
            b = owner.issue_submission(root, next_auth, "successor B")
            now = self.app._conversation_now()
            review_b = owner.begin_reset_review(root, next_auth,
                                                  ResetOperation.CLEAR, now_ms=now)
            timer_b = self.root.after(30000, lambda: None)
            self.app._conversation_timer = (review_b, timer_b)
            state.update(view=next_auth, ticket=b, review=review_b, timer=timer_b)
            raise RuntimeError("A injected exception")
        with mock.patch.object(owner, "commit_submission", side_effect=inject):
            view.entry.insert(0, "request A")
            view.send_button.invoke()
        self.assertEqual(owner.snapshot.entries, ())
        self.assertIs(owner.active_submission_state, SubmissionState.ISSUED)
        self.assertIs(self.app._conversation_timer[0], state["review"])
        self.assertIn(state["timer"], self.root.tk.call("after", "info"))
        self.assertIs(owner._review, state["review"])
        # A's exception cleanup has completed; finish B with the real method.
        owner.claim_submission(root, state["view"], state["ticket"])
        result = original_commit(root, state["view"], state["ticket"])
        self.assertEqual(result.snapshot.entries[0].payload, "successor B")
        self.assertEqual(result.snapshot.entries[1].state.value, "UNSENT_OFFLINE")
        self.assertTrue(self.app._cancel_conversation_timer(state["review"]))
        self.assertIsNone(self.app._conversation_timer)


def tearDownModule():
    """Finalize retired mapped Tk objects on their owning test thread.

    Earlier Phase 8.29/8.30 and this phase create real Tcl interpreters.
    Tk must not be finalised later by unrelated worker-thread GC in the
    pointer-observation suite. This test-only teardown never affects product.
    """
    import gc
    import threading
    if threading.current_thread() is not threading.main_thread():
        raise AssertionError("Native Tk module cleanup requires the UI owner thread")
    gc.collect()
    survivors = sum(root() is not None for root in _retired_tk_roots)
    if survivors:
        raise AssertionError(f"{survivors} retired Tk roots survived main-thread collection")
    _retired_tk_roots.clear()


if __name__ == "__main__":
    unittest.main()
