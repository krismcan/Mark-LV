"""Owned fake Tcl seams exercise the real ConversationWindow without a display.

Fakes enforce creator-thread access and inject callbacks before/after effects;
they do not replace the production draft controller or consent owner.
"""
from contextlib import ExitStack
from dataclasses import replace
import builtins
import io
import threading
from types import SimpleNamespace
import tkinter as tk
import unittest
from unittest import mock

from nayeon.desktop_alpha import workspace_window as ui
from nayeon.desktop_alpha.conversation_session import SessionSnapshot
from nayeon.desktop_alpha.offline_request_draft import DISCLOSURE, RECEIPT_TEXT
from nayeon.desktop_alpha.offline_request_review import ReviewState
from tests.phase_831_fake_session_support import ProhibitedEffects


class OwnedWidget:
    """Small synchronous fake; every widget call is an observable Tcl seam."""

    def __init__(self, parent=None, **options):
        self.creator = threading.get_ident()
        self.options = dict(options)
        self.value = ""
        self.alive = self.visible = True
        self.before = self.after = None
        self.bindings = {}
        self.calls = []

    def call(self, operation, effect, **details):
        if threading.get_ident() != self.creator:
            raise AssertionError("foreign-thread widget access")
        self.calls.append((operation, details))
        if not self.alive:
            raise tk.TclError("retired fake widget")
        if self.before:
            self.before(operation, details)
        result = effect()
        if self.after:
            self.after(operation, details)
        return result

    def configure(self, **options):
        return self.call("configure", lambda: self.options.update(options), **options)

    def cget(self, key):
        return self.call("cget", lambda: self.options.get(key, ""), key=key)

    def instate(self, statespec):
        return self.call("instate", lambda: (
            self.options.get("state", "normal") != "disabled"
            if "!disabled" in statespec
            else self.options.get("state", "normal") == "disabled"))

    def winfo_exists(self):
        return self.call("winfo_exists", lambda: self.alive)

    def pack(self, **options):
        return self.call("pack", lambda: setattr(self, "visible", True))

    def pack_forget(self):
        return self.call("pack_forget", lambda: setattr(self, "visible", False))

    def bind(self, event, callback, add=None):
        return self.call("bind", lambda: self.bindings.setdefault(event, []).append(callback))

    def get(self, *args):
        return self.call("get", lambda: self.value)

    def edit(self, value):
        def apply():
            validation = self.options.get("validatecommand")
            if not validation or validation[0](value):
                self.value = value
        return self.call("edit", apply)

    def insert(self, position, text, *tags):
        self.edit(self.value + text)

    def delete(self, *args):
        self.edit("")

    def invoke(self):
        return self.call("invoke", lambda: (
            self.options["command"]()
            if self.options.get("state", "normal") != "disabled" else None))

    def destroy(self):
        def retire():
            self.alive = self.visible = False
            for callback in self.bindings.get("<Destroy>", ()):
                callback(SimpleNamespace(widget=self))
        return self.call("destroy", retire)

    def yview(self, *args):
        return self.call("yview", lambda: None)

    def set(self, *args):
        return self.call("set", lambda: None)

    def tag_configure(self, *args, **kwargs):
        return self.call("tag_configure", lambda: None)


class DraftWindowHarness:
    def __init__(self, case):
        self.clock = 100
        self.current = True
        self.worker = False
        self.snapshot = SessionSnapshot(object(), 1, 0, (), 0, False)
        self.saved = []
        self.commands = set()
        self.effects = ProhibitedEffects()
        stack = ExitStack()
        case.addCleanup(stack.close)
        case.addCleanup(self.effects.assert_clean)
        for patcher in (*self.effects.patchers(), *self.effects.native_patchers()):
            stack.enter_context(patcher)
        def pane_init(view, parent, *, name, on_destroy):
            view._creator_thread = threading.get_ident()
            view._alive = True
            view._on_destroy = on_destroy
        stack.enter_context(mock.patch.object(ui.WorkspacePane, "__init__", pane_init))
        def register(view, callback):
            self.commands.add(callback)
            return callback
        stack.enter_context(mock.patch.object(ui.ConversationWindow, "register", register))
        stack.enter_context(mock.patch.object(ui.ConversationWindow, "deletecommand",
                                             lambda view, command: self.commands.remove(command)))
        for name in ("Frame", "Label", "Entry", "Button", "Scrollbar"):
            stack.enter_context(mock.patch.object(ui.ttk, name, OwnedWidget))
        stack.enter_context(mock.patch.object(ui.tk, "Text", OwnedWidget))
        self.view = ui.ConversationWindow(object(),
            on_send=lambda: self.saved.append(self.view.entry.get()),
            on_reset=lambda operation: None, is_current=lambda: self.current,
            on_destroy=lambda: None, assistant_name="Nayeon", user_name="You",
            on_request_snapshot=lambda: None if self.worker else self.snapshot)
        self.view._request_now = lambda: self.clock
        self.view.entry.edit("literal live prompt")
        self.view.draft_provider.edit("openai")
        self.view.draft_model.edit("example-model")

    def admit_fake_worker(self):
        # Exact production app ingress seam, before a worker can be started.
        self.view._cancel_request_review()
        self.worker = True


class DraftTkTests(unittest.TestCase):
    def setUp(self):
        self.h = DraftWindowHarness(self)
        self.view = self.h.view

    def arm(self):
        self.assertTrue(self.view._begin_draft())
        self.assertIs(self.view._draft_owner.state, ReviewState.ARMED)
        self.assertIsNotNone(self.view._draft_ticket)

    def assert_cancelled(self):
        self.assertIsNone(self.view._draft_ticket)
        self.assertIsNone(self.view._draft_receipt)
        self.assertFalse(self.view._confirm_draft())
        self.assertTrue(self.view.draft_status.options.get("text") != RECEIPT_TEXT
                        or not self.view.draft_status.visible)

    def test_real_controls_same_prompt_exact_json_and_immutable_receipt(self):
        before = self.h.snapshot
        self.view.draft_prepare_button.invoke()
        draft = self.view._draft_data
        self.assertEqual(self.view.draft_disclosure.cget("text"), DISCLOSURE)
        self.assertEqual(self.view.draft_json.get("1.0", "end-1c"), draft.to_json())
        self.assertEqual(draft.prompt, self.view.entry.get())
        self.assertEqual(draft.model, "example-model")
        self.assertTrue(self.view._confirm_draft())
        self.assertEqual(self.view.draft_status.cget("text"), RECEIPT_TEXT)
        self.assertIs(self.view._draft_receipt.draft, draft)
        self.assertIs(self.h.snapshot, before)
        self.assertEqual(self.h.saved, [])
        self.assertFalse(self.view._confirm_draft())

    def test_provider_is_explicit_and_invalid_offer_can_be_reprepared(self):
        self.view.draft_provider.edit("")
        self.assertFalse(self.view._begin_draft())
        self.assertIsNone(self.view._draft_ticket)
        self.view.draft_provider.edit("openai")
        self.arm()

    def test_cancel_drops_ticket_without_transcript_change(self):
        self.arm()
        self.assertTrue(self.view._cancel_draft())
        self.assert_cancelled()
        self.assertTrue(self.view.draft_confirm_button.instate(("disabled",)))
        self.assertEqual(self.h.snapshot.entries, ())

    def test_model_provider_and_prompt_edits_cancel_immediately(self):
        for field, value in (("draft_model", "changed"), ("draft_provider", "other"),
                             ("entry", "new prompt")):
            with self.subTest(field=field):
                self.arm()
                getattr(self.view, field).edit(value)
                self.assert_cancelled()
                self.view.draft_provider.edit("openai")

    def test_thirty_second_boundary_refuses_even_enabled_control(self):
        self.arm()
        self.h.clock = 30_100
        self.assertTrue(self.view.draft_confirm_button.instate(("!disabled",)))
        self.assertFalse(self.view._confirm_draft())
        self.assert_cancelled()

    def test_session_epoch_revision_and_closed_snapshot_changes_refuse(self):
        original = self.h.snapshot
        for change in (dict(session_identity=object()), dict(epoch=2),
                       dict(revision=1), dict(closed=True), {}):
            self.h.snapshot = original
            self.arm()
            self.h.snapshot = replace(original, **change)
            self.assertFalse(self.view._confirm_draft())
            self.assert_cancelled()

    def test_navigation_and_stale_callback_cannot_issue_a_success(self):
        self.arm()
        old_callback = self.view._confirm_draft
        self.h.current = False
        self.assertFalse(old_callback())
        self.assert_cancelled()
        self.assertFalse(self.view._begin_draft())

    def test_captured_old_confirm_callback_cancels_instead_of_confirming_successor(self):
        self.arm()
        old_callback = self.view.draft_confirm_button.options["command"]
        self.view._cancel_draft()
        self.arm()
        successor = self.view._draft_ticket
        self.assertFalse(old_callback())
        self.assertIsNotNone(successor)
        self.assert_cancelled()

    def test_confirm_callback_registration_is_bounded_across_cancel_and_reprepare(self):
        baseline = len(self.h.commands)
        for _ in range(8):
            self.arm()
            self.assertEqual(len(self.h.commands), baseline + 1)
            self.assertTrue(self.view._cancel_draft())
            self.assertEqual(len(self.h.commands), baseline)

    def test_render_and_reset_cancel_draft_without_new_authority(self):
        self.arm()
        self.view.render(self.h.snapshot)
        self.assert_cancelled()
        self.arm()
        self.view.show_reset(SimpleNamespace(operation=SimpleNamespace(value="CLEAR")),
                             lambda: None, lambda: None)
        self.assert_cancelled()

    def test_pane_destruction_revokes_and_closes_without_widget_access(self):
        self.arm()
        for widget in (self.view.draft_status, self.view.draft_confirm_button,
                       self.view.draft_disclosure):
            widget.before = lambda *args: self.fail("Tcl queried during destruction")
        self.view._destroyed(SimpleNamespace(widget=self.view))
        self.assertIs(self.view._draft_owner.state, ReviewState.CLOSED)
        self.assert_cancelled()

    def test_prompt_only_review_and_draft_have_independent_tickets(self):
        self.assertTrue(self.view._begin_request_review())
        prompt_ticket = self.view._request_ticket
        self.arm()
        self.assertIs(self.view._request_ticket, prompt_ticket)
        self.assertIsNot(self.view._draft_ticket, prompt_ticket)
        self.assertTrue(self.view._confirm_request_review())
        self.assertTrue(self.view._confirm_draft())
        self.assertIn("REVIEWED OFFLINE", self.view.request_status.cget("text"))
        self.assertEqual(self.view.draft_status.cget("text"), RECEIPT_TEXT)

    def test_draft_fault_does_not_poison_prompt_only_review(self):
        def inject(op, details):
            if op == "configure" and details.get("state") == "normal":
                raise tk.TclError("draft-only publication fault")
        self.view.draft_confirm_button.before = inject
        self.assertFalse(self.view._begin_draft())
        self.assertTrue(self.view._draft_faulted)
        self.assertTrue(self.view._begin_request_review())
        self.assertTrue(self.view._confirm_request_review())
        self.assertIn("REVIEWED OFFLINE", self.view.request_status.cget("text"))

    def test_maximum_escaped_json_is_exact_and_in_fixed_height_read_only_field(self):
        self.view.entry.edit("\U0001f600" * 512)
        self.arm()
        self.assertEqual(self.view.draft_json.options["height"], 3)
        self.assertEqual(self.view.draft_json.cget("state"), "disabled")
        self.assertEqual(self.view.draft_json.get("1.0", "end-1c"),
                         self.view._draft_data.to_json())

    def test_reentrant_cancel_confirm_prepare_at_final_tcl_seam(self):
        for operation in (self.view._cancel_draft, self.view._confirm_draft,
                          self.view._begin_draft):
            fired = []
            def inject(op, details):
                if op == "instate" and not fired:
                    fired.append(operation())
            self.view.draft_confirm_button.after = inject
            self.assertFalse(self.view._begin_draft())
            self.view.draft_confirm_button.after = None
            self.assertEqual(len(fired), 1)
            self.assert_cancelled()

    def test_model_edit_during_final_instate_revokes_after_effect(self):
        fired = []
        def inject(op, details):
            if op == "instate" and not fired:
                fired.append(True)
                self.view.draft_model.edit("successor")
        self.view.draft_confirm_button.after = inject
        self.assertFalse(self.view._begin_draft())
        self.assertEqual(fired, [True])
        self.assert_cancelled()

    def test_deadline_during_last_instate_and_success_publication_refuses(self):
        for stage in ("arm", "confirm", "receipt"):
            h = DraftWindowHarness(self)
            if stage != "arm":
                self.assertTrue(h.view._begin_draft())
            def inject(op, details):
                if ((stage != "receipt" and op == "instate")
                        or (stage == "receipt" and op == "configure"
                            and details.get("text") == RECEIPT_TEXT)):
                    h.clock = 30_100
            widget = h.view.draft_status if stage == "receipt" else h.view.draft_confirm_button
            widget.after = inject
            action = h.view._begin_draft if stage == "arm" else h.view._confirm_draft
            self.assertFalse(action())
            self.assertIsNone(h.view._draft_ticket)
            self.assertIsNone(h.view._draft_receipt)

    def test_fake_worker_admission_at_final_tcl_seam_revokes(self):
        fired = []
        def inject(op, details):
            if op == "instate" and not fired:
                fired.append(True)
                self.h.admit_fake_worker()
        self.view.draft_confirm_button.after = inject
        self.assertFalse(self.view._begin_draft())
        self.assertEqual(fired, [True])
        self.assertTrue(self.h.worker)
        self.assert_cancelled()

    def test_widget_teardown_at_final_seam_cancels_without_dead_widget_queries(self):
        def inject(op, details):
            if op == "instate":
                self.view.draft_model.destroy()
        self.view.draft_confirm_button.after = inject
        self.assertFalse(self.view._begin_draft())
        self.assert_cancelled()
        self.assertTrue(self.view._draft_faulted)

    def test_enable_before_and_after_effect_fault_permanently_refuses(self):
        for seam in ("before", "after"):
            h = DraftWindowHarness(self)
            def inject(op, details):
                if op == "configure" and details.get("state") == "normal":
                    raise tk.TclError("injected enable fault")
            setattr(h.view.draft_confirm_button, seam, inject)
            self.assertFalse(h.view._begin_draft())
            self.assertIsNone(h.view._draft_ticket)
            self.assertTrue(h.view._draft_faulted)

    def test_success_publication_cancel_then_cleanup_fault_cannot_leave_success(self):
        self.arm()
        fired = []
        def publish(op, details):
            if op == "configure" and details.get("text") == RECEIPT_TEXT and not fired:
                fired.append(True)
                self.view._cancel_draft()
        def cleanup(op, details):
            if fired and op == "configure" and details.get("text") == "":
                raise tk.TclError("status cleanup refused before effect")
        self.view.draft_status.after = publish
        self.view.draft_status.before = cleanup
        self.assertFalse(self.view._confirm_draft())
        self.assertEqual(fired, [True])
        self.assertFalse(self.view.draft_status.visible)
        self.assert_cancelled()
        self.assertTrue(self.view._draft_faulted)

    def test_cancel_during_success_before_or_after_effect_clears_late_write(self):
        for seam in ("before", "after"):
            self.arm()
            fired = []
            def inject(op, details):
                if op == "configure" and details.get("text") == RECEIPT_TEXT and not fired:
                    fired.append(True)
                    self.view._cancel_draft()
            setattr(self.view.draft_status, seam, inject)
            self.assertFalse(self.view._confirm_draft())
            setattr(self.view.draft_status, seam, None)
            self.assert_cancelled()

    def test_worker_after_receipt_publication_cancels_receipt(self):
        self.arm()
        fired = []
        def inject(op, details):
            if op == "configure" and details.get("text") == RECEIPT_TEXT and not fired:
                fired.append(True)
                self.h.admit_fake_worker()
        self.view.draft_status.after = inject
        self.assertFalse(self.view._confirm_draft())
        self.assert_cancelled()

    def test_cleanup_button_failure_clears_preexisting_success_first(self):
        self.arm()
        self.assertTrue(self.view._confirm_draft())
        def inject(op, details):
            if op == "configure":
                raise tk.TclError("button cleanup fault")
        self.view.draft_confirm_button.before = inject
        self.assertFalse(self.view._cancel_draft())
        self.assert_cancelled()
        self.assertEqual(self.view.draft_status.cget("text"), "")
        self.assertFalse(self.view._begin_draft())

    def test_callback_cleanup_fault_revokes_and_blocks_reprepare(self):
        self.arm()
        with mock.patch.object(self.view, "deletecommand",
                               side_effect=tk.TclError("callback cleanup fault")):
            self.assertFalse(self.view._cancel_draft())
        self.assert_cancelled()
        self.assertTrue(self.view._draft_faulted)
        self.assertFalse(self.view._begin_draft())

    def test_json_cleanup_fault_cannot_preserve_a_success_receipt(self):
        self.arm()
        self.assertTrue(self.view._confirm_draft())
        def inject(op, details):
            if op == "configure":
                raise tk.TclError("JSON cleanup fault")
        self.view.draft_json.before = inject
        self.assertFalse(self.view._cancel_draft())
        self.assert_cancelled()
        self.assertFalse(self.view.draft_json.visible)

    def test_no_worker_is_admitted_by_draft_lifecycle(self):
        with mock.patch.object(threading.Thread, "start",
                               side_effect=self.h.effects.deny("worker")), \
             mock.patch.object(builtins, "open", self.h.effects.deny("file-read")), \
             mock.patch.object(io, "open", self.h.effects.deny("file-read")):
            self.arm()
            self.assertTrue(self.view._confirm_draft())
            self.view._cancel_draft()

    def test_display_tamper_and_disabled_confirm_refuse(self):
        self.arm()
        self.view.draft_disclosure.options["text"] += "tampered"
        self.assertFalse(self.view._confirm_draft())
        self.assert_cancelled()
        # A tampered disclosure must not be silently accepted on re-offer.
        self.assertFalse(self.view._begin_draft())
        self.assert_cancelled()
        self.view.draft_disclosure.options["text"] = DISCLOSURE
        self.arm()
        self.view.draft_confirm_button.options["state"] = "disabled"
        self.assertFalse(self.view._confirm_draft())
        self.assert_cancelled()

    def test_foreign_thread_all_controller_surfaces_fail_before_widgets(self):
        self.arm()
        ticket = self.view._draft_ticket
        operations = (self.view._begin_draft, self.view._confirm_draft,
                      self.view._cancel_draft, self.view._drop_draft,
                      lambda: self.view._draft_model_proposed("new"),
                      lambda: self.view._draft_provider_proposed("openai"),
                      lambda: self.view._draft_widget_destroyed(None))
        failures = []
        def foreign():
            for operation in operations:
                try:
                    operation()
                except RuntimeError as error:
                    failures.append(str(error))
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(failures, ["WRONG_THREAD"] * len(operations))
        self.assertIs(self.view._draft_ticket, ticket)


if __name__ == "__main__":
    unittest.main()
