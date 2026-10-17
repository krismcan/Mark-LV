"""Phase 8.31 bounded fake-only effect and lifecycle acceptance."""
from __future__ import annotations

import ast
from contextlib import ExitStack
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
import unittest
import weakref
from unittest import mock

from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.conversation_session import (
    EntryState, OfflineConversationSession, ResetOperation, SubmissionState,
)
from tests import test_phase_830_application as profile_fixture
from tests.phase_831_fake_session_support import (
    FakeDeliveryState, FakeOfflineCompletionQueue, ProhibitedEffects,
)


_retired_tk_roots = []  # weak refs never retain a Tcl interpreter


@unittest.skipUnless(os.name == "nt", "Windows Tk fake-only acceptance")
class Phase831EffectIsolationTests(unittest.TestCase):
    def setUp(self):
        # Scoped native disposable source resolver is patched BEFORE app init.
        profile_fixture.Phase830ProductionAdmissionTests.setUp(self)
        self.existing_profile_bytes = None
        if self._testMethodName == "test_existing_synthetic_profile_remains_byte_identical":
            # A genuine synthetic, separately reviewed 8.30 Save occurs
            # BEFORE our forbidden-effect scope or app construction.
            edit = self.production.load_for_edit()
            review = self.production.review_save(
                edit, profile_fixture.Phase830ProductionAdmissionTests.document(
                    "Synthetic Existing Profile"))
            self.production.save(review)
            self.existing_profile_bytes = {
                str(path.relative_to(self.synthetic_local)): path.read_bytes()
                for path in self.synthetic_local.rglob("*") if path.is_file()
            }
        self.root = tk.Tk()
        _retired_tk_roots.append(weakref.ref(self.root))
        self.root.withdraw()
        self.effects = ProhibitedEffects()
        self._guards = ExitStack()
        # Cleanup is LIFO: close UI while tripwires are ACTIVE, then unpatch,
        # then assert zero forbidden attempts; native fixture cleanup is later.
        self.addCleanup(self.effects.assert_clean)
        self.addCleanup(self._guards.close)
        for patcher in self.effects.patchers():
            self._guards.enter_context(patcher)
        for patcher in self.effects.native_patchers():
            self._guards.enter_context(patcher)
        self.addCleanup(self._close)

    def _close(self):
        if hasattr(self, "fake") and self.fake._entry is not None:
            self.fake.cancel(self.fake._entry)
        if hasattr(self, "app"):
            self.app.close()
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass
        if hasattr(self, "fake"):
            self.assertEqual(self.fake.callback_errors, [],
                             "Fake Tk callback failed and Tk swallowed exception")

    def _setup(self):
        if self.existing_profile_bytes is None:
            self.assertFalse(self.app_dir.exists())
        else:
            self.assertTrue(self.profile_leaf.exists())
        self.app = OfflineWorkspaceApplication(self.root)
        self.fake = FakeOfflineCompletionQueue(
            self.root, self.app._conversation, self.app._conversation_root, self.effects)
        return self.app._conversation_view

    def test_production_startup_navigation_close_never_uses_effects(self):
        self._setup()
        self.app.show_settings()
        self.app.show_conversation()
        self.app.show_connection()
        self.app.show_conversation()
        self.app.close()
        self.effects.assert_clean()
        self.assertFalse(self.app_dir.exists())
        self.assertEqual(self.effects.fake_completions, 0)

    def test_fake_exact_delivery_once_and_offline_only(self):
        view = self._setup()
        ticket = self.fake.issue(view, "Fake request")
        self.assertIs(self.fake.state, FakeDeliveryState.QUEUED)
        self.assertEqual(self.app._conversation.snapshot.entries, ())
        self.root.update_idletasks()
        self.assertEqual(self.fake.deliveries, 1)
        self.assertEqual(self.effects.fake_completions, 1)
        self.assertIs(self.fake.state, FakeDeliveryState.DELIVERED)
        entries = self.app._conversation.snapshot.entries
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].payload, "Fake request")
        self.assertTrue(all(e.state is EntryState.UNSENT_OFFLINE for e in entries))
        self.assertFalse(self.fake.deliver(ticket))
        self.assertEqual(self.fake.deliveries, 1)
        self.effects.assert_clean()
        self.assertFalse(self.app_dir.exists())

    def test_fake_cancel_before_dispatch_is_exact_once(self):
        view = self._setup()
        ticket = self.fake.issue(view, "cancel")
        self.assertTrue(self.fake.cancel(ticket))
        self.assertFalse(self.fake.cancel(ticket))
        self.root.update_idletasks()
        self.assertEqual(self.fake.deliveries, 0)
        self.assertIsNone(self.app._conversation.active_submission_state)
        self.assertEqual(self.app._conversation.snapshot.entries, ())
        self.assertFalse(self.fake.deliver(ticket))

    def test_stale_a_navigation_must_leave_queue_reusable_for_b(self):
        view = self._setup()
        a = self.fake.issue(view, "old A")
        self.app.show_connection()
        self.app.show_conversation()
        self.root.update_idletasks()  # queued A delivered late, must retire.
        self.assertIs(self.fake.state, FakeDeliveryState.CANCELLED)
        self.assertFalse(self.fake.deliver(a))
        b = self.fake.issue(self.app._conversation_view, "new B")
        self.root.update_idletasks()
        self.assertIs(self.fake.state, FakeDeliveryState.DELIVERED)
        self.assertEqual(self.fake.deliveries, 1)
        self.assertEqual(self.effects.fake_completions, 1)
        self.assertFalse(self.fake.deliver(a))
        self.assertEqual(self.app._conversation.snapshot.entries[0].payload, "new B")

    def test_new_session_epoch_rejects_a_and_accepts_b(self):
        view = self._setup()
        a = self.fake.issue(view, "A")
        owner = self.app._conversation
        old = owner.snapshot
        review = owner.begin_reset_review(self.app._conversation_root, view,
                                          ResetOperation.NEW_SESSION, now_ms=100)
        owner.confirm_reset(self.app._conversation_root, view, review,
                            ResetOperation.NEW_SESSION, now_ms=101)
        self.assertEqual(owner.snapshot.epoch, old.epoch + 1)
        self.assertFalse(self.fake.deliver(a))
        b = self.fake.issue(view, "B")
        self.root.update_idletasks()
        self.assertIs(self.fake.state, FakeDeliveryState.DELIVERED)
        self.assertEqual(owner.snapshot.entries[0].payload, "B")
        self.assertFalse(self.fake.deliver(a))
        self.assertEqual(self.fake.deliveries, 1)

    def test_foreign_queue_receipt_cannot_complete_other_owner(self):
        self._setup()
        foreign_root = object()
        foreign = OfflineConversationSession(foreign_root)
        foreign_view = foreign.activate_view(foreign_root, object())
        other = FakeOfflineCompletionQueue(self.root, foreign, foreign_root)
        receipt = other.issue(foreign_view, "other owner")
        self.assertFalse(self.fake.deliver(receipt))
        self.assertTrue(other.deliver(receipt))
        self.assertEqual(len(self.app._conversation.snapshot.entries), 0)
        self.assertEqual(foreign.snapshot.entries[0].payload, "other owner")
        self.root.update_idletasks()
        self.assertEqual(other.callback_errors, [])

    def test_terminal_root_close_with_outstanding_owner_ticket(self):
        view = self._setup()
        ticket = self.fake.issue(view, "stale after close")
        self.assertIs(self.app._conversation.active_submission_state,
                      SubmissionState.ISSUED)
        # Only the synthetic Tcl command is detached; the owner ticket is
        # deliberately left live until terminal application.close revokes it.
        self.assertTrue(self.fake.detach_schedule_for_terminal_close(ticket))
        self.assertIs(self.app._conversation.active_submission_state,
                      SubmissionState.ISSUED)
        self.app.close()
        self.assertTrue(self.app._conversation.snapshot.closed)
        self.assertIsNone(self.app._conversation.active_submission_state)
        self.assertFalse(self.fake.deliver(ticket))
        self.assertIs(self.fake.state, FakeDeliveryState.CANCELLED)
        self.assertEqual(self.app._conversation.snapshot.entries, ())

    def test_normal_ui_send_remains_offline_not_fake_provider(self):
        self._setup()
        view = self.app._active_view
        view.entry.insert(0, "don't run programs")
        view.send_button.invoke()
        self.assertEqual(self.fake.deliveries, 0)
        entries = self.app._conversation.snapshot.entries
        self.assertEqual(len(entries), 2)
        self.assertIs(entries[1].state, EntryState.UNSENT_OFFLINE)
        self.assertFalse(self.app_dir.exists())

    def test_scheduler_failure_revokes_issued_ticket_and_reusable(self):
        view = self._setup()
        with mock.patch.object(self.root, "after_idle", side_effect=RuntimeError("fake scheduling")):
            with self.assertRaisesRegex(RuntimeError, "fake scheduling"):
                self.fake.issue(view, "A")
        self.assertIsNone(self.app._conversation.active_submission_state)
        self.assertIsNone(self.fake._entry)
        self.assertIs(self.fake.state, FakeDeliveryState.CANCELLED)
        self.fake.issue(view, "B")
        self.root.update_idletasks()
        self.assertEqual(self.app._conversation.snapshot.entries[0].payload, "B")

    def test_timer_cancellation_exception_still_revokes_ticket(self):
        view = self._setup()
        a = self.fake.issue(view, "A")
        with mock.patch.object(self.root, "after_cancel", side_effect=RuntimeError("cancel fault")):
            with self.assertRaisesRegex(RuntimeError, "cancel fault"):
                self.fake.cancel(a)
        self.assertIsNone(self.app._conversation.active_submission_state)
        self.assertIsNone(self.fake._entry)
        # Still-registered synthetic callback is now stale and harmless.
        self.root.update_idletasks()
        self.assertEqual(self.fake.callback_errors, [])
        b = self.fake.issue(view, "B")
        self.root.update_idletasks()
        self.assertEqual(self.app._conversation.snapshot.entries[0].payload, "B")

    def test_claim_exception_does_not_orphan_owner_or_b(self):
        view = self._setup()
        a = self.fake.issue(view, "A")
        with mock.patch.object(self.app._conversation, "claim_submission",
                               side_effect=RuntimeError("claim fault")):
            with self.assertRaisesRegex(RuntimeError, "claim fault"):
                self.fake.deliver(a)
        self.assertIsNone(self.fake._entry)
        self.assertIsNone(self.app._conversation.active_submission_state)
        self.assertIs(self.fake.state, FakeDeliveryState.CANCELLED)
        self.fake.issue(view, "B")
        self.root.update_idletasks()
        self.assertEqual(self.app._conversation.snapshot.entries[0].payload, "B")

    def test_commit_exception_does_not_orphan_owner_or_b(self):
        view = self._setup()
        a = self.fake.issue(view, "A")
        with mock.patch.object(self.app._conversation, "commit_submission",
                               side_effect=RuntimeError("commit fault")):
            with self.assertRaisesRegex(RuntimeError, "commit fault"):
                self.fake.deliver(a)
        self.assertIsNone(self.fake._entry)
        self.assertIsNone(self.app._conversation.active_submission_state)
        self.assertIs(self.fake.state, FakeDeliveryState.CANCELLED)
        self.fake.issue(view, "B")
        self.root.update_idletasks()
        self.assertEqual(self.app._conversation.snapshot.entries[0].payload, "B")

    def test_fake_callback_exceptions_are_recorded_as_failures(self):
        view = self._setup()
        a = self.fake.issue(view, "A")
        # Remove the queued Tcl command before directly invoking its Python
        # callback; otherwise later root destruction would leave an orphan.
        self.assertTrue(self.fake.detach_schedule_for_terminal_close(a))
        with mock.patch.object(self.app._conversation, "claim_submission",
                               side_effect=RuntimeError("callback fault")):
            with self.assertRaisesRegex(RuntimeError, "callback fault"):
                self.fake._deliver_idle(a)
        self.assertEqual(self.fake.callback_errors, ["RuntimeError"])
        self.fake.callback_errors.clear()
        self.assertIsNone(self.app._conversation.active_submission_state)

    def test_attempt_counter_detects_swallowed_exception_not_only_success(self):
        isolated = ProhibitedEffects()
        with ExitStack() as stack:
            for patcher in isolated.patchers():
                stack.enter_context(patcher)
            try:
                os.system("synthetic attempt; shell must never start")
            except AssertionError:
                pass
            try:
                __import__("openai")
            except AssertionError:
                pass
        self.assertEqual(isolated.counts, {"command": 1, "forbidden-import": 1})
        self.assertEqual(isolated.completed, {})
        self.assertEqual(isolated.fake_completions, 0)
        with self.assertRaisesRegex(AssertionError, "Forbidden effect"):
            isolated.assert_clean()

    def test_static_production_import_closure_forbids_test_and_effect_routes(self):
        root = Path(__file__).resolve().parents[1]
        for relative in ("nayeon/desktop_alpha/application.py",
                         "nayeon/desktop_alpha/workspace_window.py",
                         "nayeon/desktop_alpha/conversation_session.py"):
            with self.subTest(source=relative):
                tree = ast.parse((root / relative).read_text(encoding="utf-8"))
                imported = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported.extend(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported.append(node.module)
                forbidden = ("tests", "socket", "subprocess", "winreg",
                             "nayeon.brain", "nayeon.actions", "nayeon.credentials")
                self.assertFalse(any(
                    name == item or name.startswith(item + ".")
                    for name in imported for item in forbidden
                ), relative)


    def test_existing_synthetic_profile_remains_byte_identical(self):
        """Native profile read remains legal; any mutation is evidence failure."""
        self.assertIsNotNone(self.existing_profile_bytes)
        directories_before = sorted(
            str(p.relative_to(self.synthetic_local))
            for p in self.synthetic_local.rglob("*") if p.is_dir())
        self._setup()
        self.assertEqual(self.app._published_document.assistant.display_name,
                         "Synthetic Existing Profile")
        self.app.show_settings()
        self.app.show_connection()
        self.app.show_conversation()
        self.app._active_view.entry.insert(0, "do not save transcripts")
        self.app._active_view.send_button.invoke()
        self.app.close()
        after = {
            str(path.relative_to(self.synthetic_local)): path.read_bytes()
            for path in self.synthetic_local.rglob("*") if path.is_file()
        }
        directories_after = sorted(
            str(p.relative_to(self.synthetic_local))
            for p in self.synthetic_local.rglob("*") if p.is_dir())
        self.assertEqual(after, self.existing_profile_bytes)
        self.assertEqual(directories_after, directories_before)
        self.effects.assert_clean()

    def test_native_write_service_boundary_detects_caught_attempt(self):
        # Canary runs on separate isolated recorder so a deliberately denied
        # synthetic invocation doesn't pollute the real production smoke.
        from nayeon.desktop_alpha.presentation_profile_owner import (
            ProductionPresentationProfileOwner,
        )
        isolated = ProhibitedEffects()
        with ExitStack() as stack:
            for patcher in isolated.native_patchers():
                stack.enter_context(patcher)
            try:
                ProductionPresentationProfileOwner._admit_storage(
                    self.production, None, 0, create=True)
            except AssertionError:
                pass
        self.assertEqual(isolated.counts, {"native-profile-create": 1})
        self.assertEqual(isolated.completed, {})
        with self.assertRaisesRegex(AssertionError, "Forbidden effect"):
            isolated.assert_clean()

    def test_completed_vs_attempted_instrumentation_canary(self):
        isolated = ProhibitedEffects()
        value = isolated.observe("synthetic-only", lambda: "fake-done")()
        self.assertEqual(value, "fake-done")
        self.assertEqual(isolated.counts, {"synthetic-only": 1})
        self.assertEqual(isolated.completed, {"synthetic-only": 1})
        with self.assertRaisesRegex(AssertionError, "Forbidden effect"):
            isolated.assert_clean()


@unittest.skipUnless(os.name == "nt", "Fresh Windows process import test")
class Phase831FreshImportTripwireTests(unittest.TestCase):
    def test_fresh_offline_application_import_is_guarded_before_import(self):
        # A fresh interpreter is essential: current process imports are cached
        # by unittest discovery. Child does not construct a real service/root.
        script = """
from contextlib import ExitStack
from tests.phase_831_fake_session_support import ProhibitedEffects
effects = ProhibitedEffects()
with ExitStack() as stack:
    for patcher in effects.patchers():
        stack.enter_context(patcher)
    from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
    from nayeon.desktop_alpha.controller import PreviewOnlyController
    from nayeon.desktop_alpha.conversation_session import OfflineConversationSession
    assert OfflineWorkspaceApplication.__name__ == 'OfflineWorkspaceApplication'
    assert PreviewOnlyController.__name__ == 'PreviewOnlyController'
    assert OfflineConversationSession.__name__ == 'OfflineConversationSession'
    effects.assert_clean()
print('FRESH_GUARDED_IMPORT_OK')
"""
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, "-B", "-c", script], cwd=root,
            env=env, capture_output=True, text=True, timeout=35,
            check=False,
        )
        self.assertEqual(result.returncode, 0,
                         "Fresh guarded application import failed: " + result.stderr[-700:])
        self.assertEqual(result.stdout.strip(), "FRESH_GUARDED_IMPORT_OK")


def tearDownModule():
    """Finalise retired test Tk roots on their UI thread, not worker GC."""
    import gc
    import threading
    if threading.current_thread() is not threading.main_thread():
        raise AssertionError("Phase 8.31 fake Tk cleanup must run on UI thread")
    gc.collect()
    survivors = sum(ref() is not None for ref in _retired_tk_roots)
    if survivors:
        raise AssertionError(f"{survivors} retired fake Tk roots still live")
    _retired_tk_roots.clear()


if __name__ == "__main__":
    unittest.main()
