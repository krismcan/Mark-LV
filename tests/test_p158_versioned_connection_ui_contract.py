"""P158: versioned post-P133 Connection UI acceptance; NEVER changes P86/P87.

These are new positive current-branch tests, not replacement historical PASS claims.
Real Windows Tk, synthetic pending advice, fake process launch, NO live WinCred.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import ttk
import unittest
from unittest import mock

from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)
from nayeon.brain.connection_recovery_advice import advise_connection_recovery
from nayeon.brain.onboarding_status_view import present_onboarding_status
from nayeon.brain.pending_credential_policy import (
    PendingCredentialAction, PendingCredentialState, assess_pending_credential_action,
)
from nayeon.brain.pending_custody_observation_boundary import (
    CustodyObservationKind, SyntheticCustodyObservation,
)
from nayeon.desktop_alpha import local_byok_launch_bridge as bridge
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.workspace_window import ConnectionWindow
from tests.test_p133_connection_launch import FakeChild


EXPECTED_THREE = (
    "Back to Conversation",
    "Manage provider (offline preview)",
    "Open local key setup (offline, not connected)",
)


def _buttons(view):
    return tuple(w for w in view.winfo_children() if isinstance(w, ttk.Button))


def _synthetic_advice(state=PendingCredentialState.STORED_UNVERIFIED):
    obs = ConnectionObservation(ConnectionObservationStatus.UNKNOWN)
    return (present_onboarding_status(obs, advise_connection_recovery(obs)),
            assess_pending_credential_action(state, PendingCredentialAction.SAVE_PENDING))


@unittest.skipUnless(sys.platform == "win32", "Original post-P133 Windows Tk required")
class P158VersionedCurrentConnectionUI(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self._cleanup)
        with mock.patch.object(OfflineWorkspaceApplication, "_bootstrap_readonly_presentation"):
            self.app = OfflineWorkspaceApplication(self.root)
        self.app.show_connection()
        self.page = self.app._active_view
        self.token = self.app._active_token
        self.generation = self.app._generation

    def _cleanup(self):
        try:
            self.app.close()
        except Exception:
            pass
        try:
            self.root.destroy()
        except (tk.TclError, RuntimeError):
            pass

    def test_versioned_three_button_inventory_and_explicit_legacy_preservation(self):
        buttons = _buttons(self.page)
        self.assertEqual(len(buttons), 3)
        self.assertEqual(
            tuple(sorted(str(w.cget("text")) for w in buttons)),
            tuple(sorted(EXPECTED_THREE)),
        )
        self.assertIs(self.page.back_button, buttons[0])
        self.assertIs(self.page.manage_button, buttons[1])
        self.assertIs(self.page.local_byok_button, buttons[2])
        self.assertIn("NOT OBSERVED", self.page.pending_custody_label.cget("text"))
        self.assertIn("Not observed", self.page.status_label.cget("text"))
        self.assertIsNone(self.app._connection)
        self.assertIsNone(self.app._connection_coordinator)
        self.assertIsNone(self.app._connection_test_harness)
        self.assertIsNone(self.app._local_byok_launcher)

    def test_no_implicit_process_or_key_access_during_navigation_and_advice(self):
        legacy, assessment = _synthetic_advice()
        with mock.patch.object(bridge.subprocess, "Popen",
                               side_effect=AssertionError("IMPLICIT_PROCESS")) as spawned:
            self.assertTrue(self.page.show_pending_custody_advisory(legacy, assessment))
            self.assertIn("advisory only", self.page.pending_custody_label.cget("text"))
            self.app.show_settings()
            self.app.show_connection()
            self.assertIsNone(self.app._local_byok_launcher)
            self.assertIsNone(self.app._connection)
            spawned.assert_not_called()

    def test_explicit_human_click_runs_one_fake_child_with_no_secret_argument(self):
        child = FakeChild()
        self.assertEqual(str(self.page.local_byok_button.cget("state")), "normal")
        with mock.patch.object(bridge.subprocess, "Popen", return_value=child) as launched:
            self.page.local_byok_button.invoke()
            self.assertEqual(launched.call_count, 1)
            args, kwargs = launched.call_args
            self.assertEqual(args[0], [
                sys.executable, "-B", "-m", "nayeon.desktop_alpha.local_byok_window",
            ])
            self.assertFalse(kwargs["shell"])
            self.assertTrue(kwargs["close_fds"])
            self.assertEqual(kwargs["stdin"], bridge.subprocess.DEVNULL)
            self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
            self.assertNotIn("ANTHROPIC_API_KEY", kwargs["env"])
            self.assertNotIn("NAYEON_INTERNAL_SECRET", kwargs["env"])
            self.assertNotIn("openai.api_key", repr(launched.call_args))
            self.assertIn("Not connected", self.page.status_label.cget("text"))
            self.page.local_byok_button.invoke()
            self.assertEqual(launched.call_count, 1)
        self.assertEqual(len(_buttons(self.page)), 3)

    def test_legacy_offline_preview_blocks_separate_key_process(self):
        self.assertIsNone(self.app._connection)
        with mock.patch.object(bridge.subprocess, "Popen",
                               side_effect=AssertionError("ILLEGAL_CHILD")) as launched:
            self.page.manage_button.invoke()
            self.assertIsNotNone(self.app._connection)
            self.page.local_byok_button.invoke()
            self.assertIsNone(self.app._local_byok_launcher)
            launched.assert_not_called()

    def test_advisory_and_synthetic_lease_never_invoke_launch_button(self):
        with mock.patch.object(bridge.subprocess, "Popen",
                               side_effect=AssertionError("ILLEGAL_AUTO_LAUNCH")) as launched:
            lease = self.page.begin_synthetic_pending_observation()
            self.assertIsNotNone(lease)
            self.assertTrue(self.page.publish_synthetic_pending_observation(
                lease, SyntheticCustodyObservation(CustodyObservationKind.RECOVERY_HOLD)
            ))
            self.assertIn("SYNTHETIC TEST ONLY", self.page.pending_custody_label.cget("text"))
            legacy, assessment = _synthetic_advice(PendingCredentialState.RECOVERY_REQUIRED)
            self.assertTrue(self.page.show_pending_custody_advisory(legacy, assessment))
            self.assertIn("advisory only", self.page.pending_custody_label.cget("text"))
            self.assertIsNone(self.app._local_byok_launcher)
            launched.assert_not_called()
        self.assertEqual(len(_buttons(self.page)), 3)

    def test_stale_page_or_token_refused_without_child(self):
        page, token, generation = self.page, self.token, self.generation
        self.app.show_conversation()
        with mock.patch.object(bridge.subprocess, "Popen",
                               side_effect=AssertionError("STALE_LAUNCH")) as launched:
            self.app._open_local_byok(page, token, generation)
            self.assertIsNone(self.app._local_byok_launcher)
            launched.assert_not_called()

    def test_wrong_thread_refused_before_starting_child(self):
        observed = []
        with mock.patch.object(bridge.subprocess, "Popen",
                               side_effect=AssertionError("WRONG_THREAD_CHILD")) as launched:
            def worker():
                try:
                    self.app._open_local_byok(self.page, self.token, self.generation)
                except RuntimeError as e:
                    observed.append(str(e))
            other = threading.Thread(target=worker)
            other.start()
            other.join(timeout=4)
            self.assertFalse(other.is_alive())
            self.assertEqual(observed, ["WRONG_THREAD"])
            launched.assert_not_called()

    def test_direct_window_without_explicit_launcher_is_disabled(self):
        orphan = ConnectionWindow(
            self.root, on_destroy=lambda _event=None: None,
            on_conversation=lambda: None, on_manage=None, on_local_byok=None,
        )
        self.addCleanup(lambda: orphan.destroy() if orphan.winfo_exists() else None)
        self.assertEqual(len(_buttons(orphan)), 3)
        self.assertEqual(str(orphan.local_byok_button.cget("state")), "disabled")
        self.assertEqual(str(orphan.manage_button.cget("state")), "disabled")
        with mock.patch.object(bridge.subprocess, "Popen",
                               side_effect=AssertionError("DISABLED_CHILD")) as launched:
            orphan.local_byok_button.invoke()
            self.assertIsNone(self.app._local_byok_launcher)
            launched.assert_not_called()

    def test_hist_original_ui_contract_is_unmodified_and_explicitly_distinct(self):
        root = Path(__file__).resolve().parents[1]
        p86 = ast.parse((root/"tests/test_p86_live_pending_status_integration.py")
                        .read_text(encoding="utf8"))
        p87 = ast.parse((root/"tests/test_p87_readonly_custody_observation.py")
                        .read_text(encoding="utf8"))
        required = {
            "test_live_connection_page_default_is_explicitly_unobserved": 2,
            "test_no_credential_action_and_no_implicit_refresh": 2,
            "test_production_default_remains_not_observed_without_any_session": 2,
        }
        actual = {}
        for tree in (p86, p87):
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name in required:
                    expected_two = [
                        expr.value for expr in ast.walk(node)
                        if isinstance(expr, ast.Constant)
                        and type(expr.value) is int and expr.value == 2
                    ]
                    self.assertTrue(expected_two, node.name)
                    actual[node.name] = 2
        self.assertEqual(actual, required)
        self.assertEqual(len(_buttons(self.page)), 3)


if __name__ == "__main__":
    unittest.main()
