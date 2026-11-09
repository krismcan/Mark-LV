"""P133 Windows Connection-page/manual process-launch tests.

No test writes to real Windows Credential Manager or launches real BYOK
child. All subprocess.Popen calls are FAKE. Genuine Windows Tk callbacks
and historical preview navigation are exercised in-process.
"""
from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
import unittest
from unittest import mock

from nayeon.desktop_alpha import local_byok_launch_bridge as bridge
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.workspace_window import ConnectionWindow


class FakeChild:
    def __init__(self, pid=41813, alive=True):
        self.pid = pid
        self.alive = alive
        self.poll_calls = 0

    def poll(self):
        self.poll_calls += 1
        return None if self.alive else 0


class LaunchBridgeTests(unittest.TestCase):
    def test_construction_is_not_a_process_or_credential_operation(self):
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=AssertionError("AUTO_START")):
            child = bridge.LocalByokLaunchBridge()
            self.assertEqual(repr(child), "LocalByokLaunchBridge(<redacted>)")

    def test_manual_launch_uses_fixed_module_never_shell_or_key_argument(self):
        child = FakeChild()
        with mock.patch.dict(os.environ, {
            "OPENAI_API_KEY": "must-not-be-inherited",
            "NAYEON_INTERNAL_SECRET": "must-not-be-inherited",
            "PATH": os.environ.get("PATH", ""),
        }, clear=True), mock.patch.object(bridge.subprocess, "Popen", return_value=child) as call:
            result = bridge.LocalByokLaunchBridge().launch()
        self.assertIs(result, bridge.LocalByokLaunchResult.LAUNCHED_OFFLINE)
        args, kwargs = call.call_args
        self.assertEqual(args[0], [
            sys.executable, "-B", "-m",
            "nayeon.desktop_alpha.local_byok_window",
        ])
        self.assertEqual(kwargs["shell"], False)
        self.assertEqual(kwargs["close_fds"], True)
        self.assertEqual(kwargs["stdin"], bridge.subprocess.DEVNULL)
        self.assertEqual(kwargs["stdout"], bridge.subprocess.DEVNULL)
        self.assertEqual(kwargs["stderr"], bridge.subprocess.DEVNULL)
        self.assertTrue(kwargs["cwd"].endswith("Mark-LV") or
                        kwargs["cwd"].endswith("BYOK_C1_P133_GITHUB_SOURCE_READBACK_20261109") or
                        "reviewed" in kwargs["cwd"])
        self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
        self.assertNotIn("NAYEON_INTERNAL_SECRET", kwargs["env"])
        self.assertNotIn("must-not-be-inherited", repr(call.call_args))

    def test_repeated_manual_click_does_not_start_second_active_child(self):
        child = FakeChild()
        owner = bridge.LocalByokLaunchBridge()
        with mock.patch.object(bridge.subprocess, "Popen", return_value=child) as started:
            self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.LAUNCHED_OFFLINE)
            self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.ALREADY_RUNNING)
            self.assertEqual(started.call_count, 1)

    def test_finished_child_allows_explicit_new_request(self):
        a, b = FakeChild(), FakeChild(pid=41814)
        owner = bridge.LocalByokLaunchBridge()
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=[a, b]) as started:
            self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.LAUNCHED_OFFLINE)
            a.alive = False
            self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.LAUNCHED_OFFLINE)
            self.assertEqual(started.call_count, 2)

    def test_unknown_child_state_fails_closed_without_second_spawn(self):
        owner = bridge.LocalByokLaunchBridge()
        with mock.patch.object(bridge.subprocess, "Popen", return_value=FakeChild()) as started:
            self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.LAUNCHED_OFFLINE)
            with mock.patch.object(FakeChild, "poll", side_effect=OSError("private path or secret")):
                self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.UNAVAILABLE)
            self.assertEqual(started.call_count, 1)

    def test_spawn_error_uses_fixed_nonsecret_refusal(self):
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=OSError("secret")):
            self.assertIs(bridge.LocalByokLaunchBridge().launch(),
                          bridge.LocalByokLaunchResult.UNAVAILABLE)

    def test_suspicious_missing_process_identity_is_not_claimed(self):
        with mock.patch.object(bridge.subprocess, "Popen", return_value=FakeChild(pid=-1)):
            self.assertIs(bridge.LocalByokLaunchBridge().launch(),
                          bridge.LocalByokLaunchResult.UNAVAILABLE)

    def test_cross_platform_launch_is_not_attempted(self):
        with mock.patch.object(bridge.sys, "platform", "linux"), mock.patch.object(
            bridge.subprocess, "Popen", side_effect=AssertionError("NO_LAUNCH")
        ):
            self.assertIs(bridge.LocalByokLaunchBridge().launch(),
                          bridge.LocalByokLaunchResult.UNAVAILABLE)

    def test_frozen_binary_requires_separately_reviewed_launcher(self):
        with mock.patch.object(bridge.sys, "frozen", True, create=True), mock.patch.object(
            bridge.subprocess, "Popen", side_effect=AssertionError("NO_FROZEN_LAUNCH")
        ):
            self.assertIs(bridge.LocalByokLaunchBridge().launch(),
                          bridge.LocalByokLaunchResult.UNAVAILABLE)

    def test_missing_exact_child_module_refuses_launch(self):
        with mock.patch.object(bridge.Path, "is_file", return_value=False), mock.patch.object(
            bridge.subprocess, "Popen", side_effect=AssertionError("NO_MODULE_LAUNCH")
        ):
            self.assertIs(bridge.LocalByokLaunchBridge().launch(),
                          bridge.LocalByokLaunchResult.UNAVAILABLE)

    def test_reentrant_launch_callback_is_blocked_by_gate(self):
        owner = bridge.LocalByokLaunchBridge()
        nested = []
        def spawn(*_args, **_kwargs):
            nested.append(owner.launch())
            return FakeChild()
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=spawn) as call:
            self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.LAUNCHED_OFFLINE)
        self.assertEqual(nested, [bridge.LocalByokLaunchResult.BUSY])
        self.assertEqual(call.call_count, 1)

    def test_local_child_environment_whitelists_no_provider_secrets(self):
        with mock.patch.dict(os.environ, {
            "PATH": "safe-fixture-path",
            "TEMP": "safe-fixture-temp",
            "OPENAI_API_KEY": "never-inherited",
            "AZURE_OPENAI_API_KEY": "never-inherited",
            "ANTHROPIC_API_KEY": "never-inherited",
            "PYTHONPATH": "untrusted-injection",
            "NAYEON_CONFIG_KEY": "untrusted-config",
        }, clear=True):
            safe = bridge._child_windows_environment()
        self.assertEqual(safe, {"PATH": "safe-fixture-path",
                                "TEMP": "safe-fixture-temp"})

    def test_bridge_source_excludes_provider_and_native_key_access(self):
        import inspect
        source = inspect.getsource(bridge)
        self.assertNotIn("CredentialBackend", source)
        self.assertNotIn("CredWriteW(", source)
        self.assertNotIn("backend.get(", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("shell=True", source)


@unittest.skipUnless(sys.platform == "win32", "Actual Windows Tk only")
class ConnectionPageTkLaunchTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.cleanup)
        with mock.patch.object(
            OfflineWorkspaceApplication, "_bootstrap_readonly_presentation"
        ):
            self.app = OfflineWorkspaceApplication(self.root)
        self.app.show_connection()
        self.page = self.app._active_view
        self.token = self.app._active_token
        self.generation = self.app._generation

    def cleanup(self):
        try:
            self.app.close()
        except Exception:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_startup_and_connection_navigation_never_launch_setup(self):
        self.assertIsNone(self.app._local_byok_launcher)
        self.assertFalse(self.app._local_byok_opening)
        self.assertIsNone(self.app._connection)
        self.assertEqual(str(self.page.local_byok_button.cget("state")), "normal")
        self.assertIn("offline", self.page.local_byok_button.cget("text"))
        self.assertIn("Not observed", self.page.status_label.cget("text"))

    def test_human_button_click_is_only_spawn_trigger(self):
        child = FakeChild()
        with mock.patch.object(bridge.subprocess, "Popen", return_value=child) as started:
            self.assertIsNone(self.app._local_byok_launcher)
            self.page.local_byok_button.invoke()
            self.assertEqual(started.call_count, 1)
            self.assertIn("Not connected", self.page.status_label.cget("text"))

    def test_double_click_same_alive_child_cannot_duplicate_process(self):
        with mock.patch.object(bridge.subprocess, "Popen", return_value=FakeChild()) as started:
            self.page.local_byok_button.invoke()
            self.page.local_byok_button.invoke()
            self.assertEqual(started.call_count, 1)
            self.assertIn("already running", self.page.status_label.cget("text"))

    def test_old_preview_button_still_exists_independently(self):
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=AssertionError("NO_CHILD")):
            self.page.manage_button.invoke()
            self.assertIsNotNone(self.app._connection)
            self.assertIsNone(self.app._local_byok_launcher)
            self.assertIn("offline", self.app._connection.status.cget("text").lower())

    def test_local_launch_refused_while_old_preview_owned(self):
        self.page.manage_button.invoke()
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=AssertionError("NO_CHILD")):
            self.page.local_byok_button.invoke()
            self.assertIsNone(self.app._local_byok_launcher)

    def test_stale_pane_click_after_navigation_refused_without_spawn(self):
        old, token, generation = self.page, self.token, self.generation
        self.app.show_conversation()
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=AssertionError("NO_CHILD")):
            self.app._open_local_byok(old, token, generation)
            self.assertIsNone(self.app._local_byok_launcher)

    def test_launch_does_not_create_second_tk_root_or_toplevel(self):
        with mock.patch.object(bridge.subprocess, "Popen", return_value=FakeChild()), mock.patch.object(
            tk.Tk, "__init__", side_effect=AssertionError("NO_SECOND_ROOT")
        ):
            self.page.local_byok_button.invoke()
            self.assertEqual(len([
                widget for widget in self.root.winfo_children()
                if isinstance(widget, tk.Toplevel)
            ]), 0)

    def test_subprocess_error_publishes_fixed_nonsecret_status(self):
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=OSError("fake-secret")):
            self.page.local_byok_button.invoke()
        self.assertIn("could not be opened", self.page.status_label.cget("text"))
        self.assertNotIn("fake-secret", self.page.status_label.cget("text"))

    def test_navigation_during_spawn_never_updates_stale_connection_pane(self):
        def navigate(*_args, **_kwargs):
            self.app.show_conversation()
            return FakeChild()
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=navigate):
            self.page.local_byok_button.invoke()
        self.assertEqual(self.app._active_view.winfo_name(), "conversation_view")

    def test_nested_button_callback_cannot_issue_second_spawn(self):
        calls = []
        def nested(*_args, **_kwargs):
            calls.append(1)
            self.page.local_byok_button.invoke()
            return FakeChild()
        with mock.patch.object(bridge.subprocess, "Popen", side_effect=nested) as started:
            self.page.local_byok_button.invoke()
            self.assertEqual(started.call_count, 1)
        self.assertEqual(len(calls), 1)

    def test_new_navigation_preserves_separate_active_child_owner(self):
        with mock.patch.object(bridge.subprocess, "Popen", return_value=FakeChild()) as started:
            self.page.local_byok_button.invoke()
            launcher = self.app._local_byok_launcher
            self.app.show_settings()
            self.app.show_connection()
            self.assertIs(self.app._local_byok_launcher, launcher)
            self.app._active_view.local_byok_button.invoke()
            self.assertEqual(started.call_count, 1)
            self.assertIn("already running", self.app._active_view.status_label.cget("text"))

    def test_foreign_thread_refused_before_launch(self):
        error = []
        def other():
            try:
                self.app._open_local_byok(self.page, self.token, self.generation)
            except RuntimeError as exc:
                error.append(str(exc))
        t = threading.Thread(target=other)
        t.start()
        t.join(timeout=4)
        self.assertFalse(t.is_alive())
        self.assertEqual(error, ["WRONG_THREAD"])


if __name__ == "__main__":
    unittest.main()
