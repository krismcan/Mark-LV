"""Native Tk adversarial offline preview tests; no interactive acceptance."""
import gc
import subprocess
import sys
import threading
import tkinter as tk
import unittest
import weakref
from unittest import mock
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication

_roots = []


def tearDownModule():
    gc.collect()
    assert not any(ref() is not None for ref in _roots)


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        _roots.append(weakref.ref(self.root))
        self.root.withdraw()
        self.addCleanup(self.cleanup)
        with mock.patch.object(OfflineWorkspaceApplication, "_bootstrap_readonly_presentation"):
            self.app = OfflineWorkspaceApplication(self.root)
        self.app.show_connection()
        self.pane = self.app._active_view

    def cleanup(self):
        self.app.close()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def open(self):
        self.pane.manage_button.invoke()
        return self.app._connection

    def test_default_one_root_one_child_inert_and_legacy_label(self):
        self.assertIn("Not observed", self.pane.winfo_children()[1].cget("text"))
        self.assertIsNone(self.app._connection_coordinator)
        with mock.patch.object(tk, "Tk", side_effect=AssertionError("SECOND_ROOT")):
            host = self.open()
            self.assertIs(host.child.master, self.root)
            self.assertIsNone(host.owner)
            for button in (host.candidate_button, host.stored_button,
                           host.confirm_button, host.cancel_button):
                self.assertEqual(str(button.cget("state")), "disabled")
                button.invoke()
            host.request("TEST_CANDIDATE")
            host.confirm()
            self.assertIsNone(host.owner)
            self.assertIn("unavailable", host.status.cget("text"))
            self.assertIs(self.open(), host)
            self.assertEqual(sum(isinstance(c, tk.Toplevel) for c in self.root.winfo_children()), 1)

    def test_fresh_default_import_start_navigation_open_no_credentials(self):
        code = '''
import builtins, tkinter as tk
from unittest.mock import patch
original = builtins.__import__
def guarded(name, *args, **kwargs):
    forbidden = ("nayeon.secrets", "nayeon.brain.onboarding", "nayeon.brain.credential",
                 "nayeon.desktop_alpha.first_run_connection_owner", "openai", "httpx", "requests")
    if any(name.startswith(p) for p in forbidden):
        raise AssertionError("CREDENTIAL_DEPENDENCY: " + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
root = tk.Tk()
root.withdraw()
with patch.object(OfflineWorkspaceApplication, "_bootstrap_readonly_presentation"):
    app = OfflineWorkspaceApplication(root)
app.show_connection()
app._active_view.manage_button.invoke()
assert app._connection is not None and app._connection.owner is None
app.show_conversation()
app.close()
import gc
del app, root
gc.collect()
'''
        result = subprocess.run([sys.executable, "-B", "-c", code],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_nested_constructor_cannot_open_second_child(self):
        original = tk.Toplevel.__init__
        count = []
        def nested(child, *args, **kwargs):
            count.append(1)
            self.pane.manage_button.invoke()
            original(child, *args, **kwargs)
        with mock.patch.object(tk.Toplevel, "__init__", new=nested):
            host = self.open()
        self.assertEqual(len(count), 1)
        self.assertTrue(host.is_current())

    def test_navigation_before_native_child_construction_cleans_orphan(self):
        # This is the order missed by the original constructor tests:
        # the retired uninitialised child can be created *after* close.
        original = tk.Toplevel.__init__
        fired = []
        def navigate_before_native(child, *args, **kwargs):
            if not fired:
                fired.append(True)
                self.app.show_conversation()
            original(child, *args, **kwargs)
        with mock.patch.object(tk.Toplevel, "__init__", new=navigate_before_native):
            self.open()
        self.assertEqual(fired, [True])
        self.assertTrue(self.app._connection_blocked)
        self.assertEqual(sum(isinstance(c, tk.Toplevel)
                             for c in self.root.winfo_children()), 0)
        self.assertEqual(self.app._active_view.winfo_name(), "conversation_view")

    def test_failed_creation_before_native_widget_quarantines(self):
        with mock.patch.object(tk.Toplevel, "__init__", side_effect=RuntimeError("fixture")):
            self.open()
        self.assertFalse(self.app._connection_opening)
        self.assertTrue(self.app._connection_blocked)
        old = self.app._connection
        self.assertIs(self.open(), old)

    def test_failed_creation_after_native_widget_cleans_exact_child(self):
        original = tk.Toplevel.__init__
        def fail(child, *args, **kwargs):
            original(child, *args, **kwargs)
            raise RuntimeError("fixture")
        with mock.patch.object(tk.Toplevel, "__init__", new=fail):
            self.open()
        self.assertIsNone(self.app._connection)
        self.assertFalse(self.app._connection_opening)
        self.assertEqual(sum(isinstance(c, tk.Toplevel) for c in self.root.winfo_children()), 0)

    def test_route_away_and_stale_a_cannot_close_b(self):
        first = self.open()
        self.app.show_conversation()
        self.assertFalse(first.is_current())
        self.app.show_connection()
        self.pane = self.app._active_view
        second = self.open()
        first.retire()
        first.confirm()
        first.cancel()
        self.assertIs(self.app._connection, second)
        self.assertTrue(second.is_current())

    def test_pane_destroy_revokes_child(self):
        host = self.open()
        self.pane.destroy()
        self.assertFalse(host.is_current())
        self.assertFalse(host.child.winfo_exists())

    def test_exact_child_destroy_and_root_destroy(self):
        host = self.open()
        host._destroyed(type("Event", (), {"widget": host.status})())
        self.assertTrue(host.is_current())
        host.child.destroy()
        self.assertFalse(host.is_current())
        host = self.open()
        self.root.destroy()
        self.assertFalse(host.is_current())
        with mock.patch.object(self.root, "winfo_exists", side_effect=AssertionError("DEAD_TK")):
            host.confirm()
            host.cancel()
            host.request("TEST_CANDIDATE")

    def test_foreign_thread_refused_before_tk(self):
        host = self.open()
        errors = []
        def foreign():
            for call in (self.app.close, self.app.show_connection,
                         lambda: self.app._open_connection(self.pane, self.app._active_token,
                                                          self.app._generation),
                         host.is_current, host.open, host.retire, host.confirm, host.cancel,
                         lambda: host.request("TEST_STORED")):
                try:
                    call()
                except RuntimeError as ex:
                    errors.append(str(ex))
        worker = threading.Thread(target=foreign)
        worker.start()
        worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, ["WRONG_THREAD"] * 9)


if __name__ == "__main__":
    unittest.main()
