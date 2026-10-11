"""Phase 8.25 maintenance: actual Windows Tk widgets, fake credential services.

Invisible Tk root, no native secret backend, no network or provider SDK. These
callbacks validate UI wiring, not real-human provenance or release acceptance.
"""
import sys
import tkinter as tk
import unittest

from nayeon.desktop_alpha.first_run_credential_validation_window import (
    FirstRunCredentialValidationWindow,
)
from tests.test_credential_operation_host import factory


@unittest.skipUnless(sys.platform == "win32", "Windows Tk acceptance only")
class WindowsRealTkAcceptance(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.host, self.backend, self.validator, self.state = factory()
        self.panel = FirstRunCredentialValidationWindow(self.root, host=self.host)

    def test_review_approval_real_widget_invocation_never_persists(self):
        p = self.panel
        self.assertEqual(p._entry.cget("show"), "*")
        self.assertEqual(p._entry.cget("state"), "disabled")
        self.assertEqual(self.validator.calls, 0)
        p._request.invoke()
        self.assertTrue(self.host.has_pending)
        self.assertEqual(p._entry.cget("state"), "normal")
        self.assertEqual(self.validator.calls, 0)
        p._entry.insert(0, "fixture-good")
        p._approve.invoke()
        self.assertFalse(self.host.has_pending)
        self.assertEqual(self.validator.calls, 1)
        self.assertEqual((self.backend.puts, self.backend.gets,
                          self.backend.deletes), (0, 0, 0))
        self.assertEqual(p._entry.get(), "")
        self.assertEqual(p._entry.cget("state"), "disabled")
        self.assertIn("not saved", p._status.cget("text").lower())
        p._approve.invoke()
        self.assertEqual(self.validator.calls, 1)

    def test_rejection_clears_real_entry_without_validation(self):
        p = self.panel
        p._request.invoke()
        p._entry.insert(0, "fixture-good")
        p._reject.invoke()
        self.assertFalse(self.host.has_pending)
        self.assertEqual(p._entry.get(), "")
        self.assertEqual(self.validator.calls, 0)
        self.assertEqual((self.backend.puts, self.backend.gets,
                          self.backend.deletes), (0, 0, 0))

    def test_invalid_entry_does_not_retain_or_save(self):
        p = self.panel
        p._request.invoke()
        p._entry.insert(0, "fixture-invalid-marker")
        p._approve.invoke()
        self.assertEqual(self.validator.calls, 1)
        self.assertEqual(self.backend.puts, 0)
        self.assertEqual(p._entry.get(), "")
        self.assertNotIn("fixture-invalid-marker", p._status.cget("text"))
        self.assertIn("rejected", p._status.cget("text"))


if __name__ == "__main__":
    unittest.main()
