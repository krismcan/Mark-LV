"""P86: native Tk live Connection view, read-only pending C1 projection only.

Tests invoke no privileged/native credential service, WinCred, provider,
network or real key. UI receives explicitly constructed synthetic advice.
"""
import ast
import inspect
import threading
import tkinter as tk
import unittest
from unittest import mock

from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)
from nayeon.brain.connection_recovery_advice import advise_connection_recovery
from nayeon.brain.onboarding_status_view import present_onboarding_status
from nayeon.brain.pending_credential_policy import (
    PendingCredentialAssessment, PendingCredentialAction,
    PendingCredentialDecision, PendingCredentialState,
    assess_pending_credential_action,
)
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha import workspace_window as module


def trusted_synthetic_views(state, action=PendingCredentialAction.SAVE_PENDING):
    observation = ConnectionObservation(ConnectionObservationStatus.UNKNOWN)
    legacy = present_onboarding_status(
        observation, advise_connection_recovery(observation))
    advice = assess_pending_credential_action(state, action)
    return legacy, advice


class P86ActualConnectionViewTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.cleanup)
        with mock.patch.object(OfflineWorkspaceApplication,
                               "_bootstrap_readonly_presentation"):
            self.app = OfflineWorkspaceApplication(self.root)
        self.app.show_connection()
        self.view = self.app._active_view

    def cleanup(self):
        if getattr(self, "app", None) is not None:
            try:
                self.app.close()
            except tk.TclError:
                pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_live_connection_page_default_is_explicitly_unobserved(self):
        self.assertIs(type(self.view), module.ConnectionWindow)
        self.assertIn("NOT OBSERVED",
                      self.view.pending_custody_label.cget("text"))
        self.assertIn("no trusted pending-key observation",
                      self.view.pending_custody_label.cget("text"))
        self.assertIn("Not observed", self.view.status_label.cget("text"))
        self.assertIsNone(self.app._connection_coordinator)
        self.assertIsNone(self.app._connection_test_harness)
        self.assertEqual(len([w for w in self.view.winfo_children()
                              if isinstance(w, tk.Button)]), 0)
        self.assertEqual(len([w for w in self.view.winfo_children()
                              if isinstance(w, module.ttk.Button)]), 2)

    def test_three_pending_states_render_bounded_advisory_only(self):
        cases = (
            (PendingCredentialState.ABSENT,
             "NO PENDING EVIDENCE ASSERTED", "NOT proof of absence"),
            (PendingCredentialState.STORED_UNVERIFIED,
             "UNVERIFIED PENDING CLAIM", "NOT confirmed"),
            (PendingCredentialState.RECOVERY_REQUIRED,
             "RECOVERY HOLD CLAIM", "No automatic retry"),
        )
        for state, flag, qualifier in cases:
            with self.subTest(state=state):
                legacy, assessment = trusted_synthetic_views(state)
                self.assertTrue(self.view.show_pending_custody_advisory(
                    legacy, assessment))
                message = self.view.pending_custody_label.cget("text")
                self.assertIn(flag, message)
                self.assertIn(qualifier, message)
                self.assertIn("advisory only", message)
                for forbidden in ("fixture-secret", "connected successfully",
                                  "saved successfully", "validation passed"):
                    self.assertNotIn(forbidden, message.lower())

    def test_inconsistent_or_untrusted_advice_cannot_be_shown(self):
        legacy, _ = trusted_synthetic_views(
            PendingCredentialState.RECOVERY_REQUIRED)
        forged = PendingCredentialAssessment(
            PendingCredentialState.RECOVERY_REQUIRED,
            PendingCredentialAction.SAVE_PENDING,
            PendingCredentialDecision.NEEDS_REVIEW)
        self.assertFalse(self.view.show_pending_custody_advisory(
            legacy, forged))
        self.assertIn("STATUS UNAVAILABLE",
                      self.view.pending_custody_label.cget("text"))
        for bad in (None, "fixture-secret", object()):
            with self.subTest(type=type(bad)):
                self.assertFalse(self.view.show_pending_custody_advisory(
                    legacy, bad))
                self.assertNotIn("fixture-secret",
                                 self.view.pending_custody_label.cget("text"))

    def test_no_credential_action_and_no_implicit_refresh(self):
        old = self.view.manage_button
        self.assertEqual(old.cget("text"),
                         "Manage provider (offline preview)")
        legacy, assessment = trusted_synthetic_views(
            PendingCredentialState.STORED_UNVERIFIED)
        with mock.patch.object(self.app, "_open_connection",
                               side_effect=AssertionError("MUTATION_PATH")):
            self.assertTrue(self.view.show_pending_custody_advisory(
                legacy, assessment))
        self.assertIsNone(self.app._connection)
        self.assertEqual(len([w for w in self.view.winfo_children()
                              if isinstance(w, module.ttk.Button)]), 2)

    def test_navigation_revokes_stale_pending_status_updates(self):
        old = self.view
        legacy, assessment = trusted_synthetic_views(
            PendingCredentialState.ABSENT)
        self.app.show_conversation()
        self.assertFalse(old._alive)
        self.assertFalse(old.show_pending_custody_advisory(legacy, assessment))

    def test_wrong_thread_refuses_before_tk(self):
        legacy, assessment = trusted_synthetic_views(
            PendingCredentialState.ABSENT)
        failures = []
        def worker():
            try:
                self.view.show_pending_custody_advisory(legacy, assessment)
            except RuntimeError as exc:
                failures.append(str(exc))
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(failures, ["WRONG_THREAD"])

    def test_no_effectful_imports_or_callbacks_in_new_method(self):
        tree = ast.parse(inspect.getsource(module.ConnectionWindow))
        method = next(n for n in tree.body[0].body
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "show_pending_custody_advisory")
        imported = [n.module for n in ast.walk(method)
                    if isinstance(n, ast.ImportFrom)]
        self.assertEqual(imported,
                         ["nayeon.brain.pending_custody_status_view"])
        names = {n.func.id if isinstance(n.func, ast.Name) else n.func.attr
                 for n in ast.walk(method) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Name, ast.Attribute))}
        self.assertFalse(names & {
            "connect", "approve", "delete", "save", "validate", "reveal",
            "Popen", "WinDLL", "open", "exec", "eval", "get", "put",
            "startfile", "start", "after", "after_idle",
        })


if __name__ == "__main__":
    unittest.main()
