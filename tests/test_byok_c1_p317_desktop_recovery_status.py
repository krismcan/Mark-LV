"""P317 deterministic fake UI cases, pending execution by later validation.

Only inert P308 widgets, clock and thread helpers are reused. Native observer
and requester methods are replaced; no service or credential operations belong
to these display-text cases. The P310 historical AST comparison is retained
on its immutable snapshot, with an exact P317 display-only successor check.
"""

import sys
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from nayeon.brain import local_byok_user_scope as scope
from nayeon.desktop_alpha import local_byok_window as window
from nayeon.secrets import windows_credential as storage
from tests.test_byok_c1_p308_native_status_observer import (
    Clock, InlineThread, Root, Widget,
)


# Entire display expressions, including their conditional and both outcomes.
# No generic removal/normalization of string constants is permitted.
DISPLAY_SUBSTITUTIONS = (
    (
        '            "UNTRUSTED_HOLD: fixed denial observed; peer is not attested. "\n'
        '            "Release HOLD; no keys or approval."\n'
        '            if result is NativeStatus.UNTRUSTED_HOLD else\n'
        '            "Native status unavailable (expected for desktop access under service-only ACL). "\n'
        '            "Release HOLD; no keys or approval."',
        '            "UNTRUSTED_HOLD: fixed denial observed; response is untrusted; peer is not attested. "\n'
        '            "No recovery state is verified. Release HOLD; no keys or approval. "\n'
        '            "Do not enter or retry credentials. Seek qualified service recovery review."\n'
        '            if result is NativeStatus.UNTRUSTED_HOLD else\n'
        '            "Native status unavailable; cause unknown. No recovery state is verified. "\n'
        '            "Release HOLD; no keys or approval. Do not enter or retry credentials. "\n'
        '            "Seek qualified service recovery review."',
    ),
    (
        '            "UNTRUSTED_HOLD: synthetic denial received; peer is not attested. "\n'
        '            "Release HOLD; no keys or approval."\n'
        '            if result is SyntheticRequestStatus.UNTRUSTED_HOLD else\n'
        '            "Synthetic request UNAVAILABLE (expected under service-only ACL). "\n'
        '            "Release HOLD; no keys or approval."',
        '            "UNTRUSTED_HOLD: synthetic denial received; response is untrusted; peer is not attested. "\n'
        '            "No recovery state is verified. Release HOLD; no keys or approval. "\n'
        '            "Do not enter or retry credentials. Seek qualified service recovery review."\n'
        '            if result is SyntheticRequestStatus.UNTRUSTED_HOLD else\n'
        '            "Synthetic request UNAVAILABLE; cause unknown. No recovery state is verified. "\n'
        '            "Release HOLD; no keys or approval. Do not enter or retry credentials. "\n'
        '            "Seek qualified service recovery review."',
    ),
)


def check_ui_successor(current, baseline):
    """Accept only the two literal, single-occurrence P316 substitutions."""
    expected = baseline
    for old, new in DISPLAY_SUBSTITUTIONS:
        if (baseline.count(old) != 1 or baseline.count(new) != 0
                or current.count(old) != 0 or current.count(new) != 1):
            raise AssertionError("P317 requires each exact display substitution once")
        expected = expected.replace(old, new, 1)
    if current != expected:
        raise AssertionError("P317 UI differs outside the two approved display expressions")


class SourceSuccessorTests(unittest.TestCase):
    def test_exact_successor_and_negative_source_fixtures(self):
        baseline = subprocess.run(
            ["git", "show", "ed769a2f472cbaecc2c2df3fff9deea606c36036:"
             "nayeon/desktop_alpha/local_byok_window.py"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            encoding="utf-8", errors="strict", timeout=5, check=True,
        ).stdout
        current = Path(window.__file__).read_text(encoding="utf-8")
        check_ui_successor(current, baseline)
        mutations = [
            baseline,  # Neither substitution applied.
            current + "\n# unrelated source change\n",
            current.replace("def main() -> None:", "def main(unapproved=None) -> None:", 1),
            current.replace("cause unknown", "expected ACL failure", 1),
            current.replace("response is untrusted", "response is trusted", 1),
            current.replace("1.5", "15.0", 1),
        ]
        for old, new in DISPLAY_SUBSTITUTIONS:
            mutations.extend((
                current.replace(new, old, 1),  # Missing one substitution.
                current + "\n" + new,  # Duplicate approved expression.
                current.replace(new, "", 1),
            ))
        for index, mutated in enumerate(mutations):
            self.assertNotEqual(mutated, current, "negative fixture must change source")
            with self.subTest(index=index), self.assertRaises(AssertionError):
                check_ui_successor(mutated, baseline)
        for old, new in DISPLAY_SUBSTITUTIONS:
            for invalid_baseline in (baseline.replace(old, "", 1),
                                     baseline + "\n" + old,
                                     baseline + "\n" + new):
                with self.subTest(baseline=old[:60]), self.assertRaises(AssertionError):
                    check_ui_successor(current, invalid_baseline)


class RecoveryStatusDisplayTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.enterContext(patch.object(window, "time", self.clock))
        for name in ("Label", "Button", "Entry", "Checkbutton", "BooleanVar"):
            self.enterContext(patch.object(window.tk, name, Widget))
        self.enterContext(patch.object(window.threading, "Thread", InlineThread))
        self.enterContext(patch.dict(sys.modules, {"_winapi": None}))
        self.credentials = self.enterContext(patch.object(
            storage, "_load_advapi32", side_effect=AssertionError("no credential access")))
        self.observe = self.enterContext(patch.object(
            window.NativeServiceObserver, "observe",
            return_value=window.NativeStatus.UNAVAILABLE))
        self.request = self.enterContext(patch.object(
            window.NativeSyntheticRequester, "request",
            return_value=window.SyntheticRequestStatus.UNAVAILABLE))
        self.controller = scope.compose_user_scope_local_byok()
        self.root = Root()
        self.ui = window.LocalByokWindow(self.root, controller=self.controller)
        self.addCleanup(self.ui.close_from_window)

    def routes(self):
        return (
            ("native", self.ui._observe, self.ui._native_status, self.observe),
            ("synthetic", self.ui._synthetic, self.ui._synthetic_status, self.request),
        )

    def assert_guidance(self, label):
        text = label.cget("text")
        for required in (
            "No recovery state is verified.", "Release HOLD; no keys or approval.",
            "Do not enter or retry credentials.", "Seek qualified service recovery review.",
        ):
            self.assertIn(required, text)
        self.assertNotIn("expected", text.lower())
        self.assertNotIn("acl", text.lower())
        self.assertFalse(self.controller.mutation_available)
        self.assertIsNone(self.ui._review)
        for widget in (*self.ui._choices, self.ui._entry, self.ui._confirm,
                       self.ui._delete_ack, self.ui._approve, self.ui._reject):
            self.assertEqual(widget.cget("state"), "disabled")
        self.credentials.assert_not_called()

    def test_unavailable_has_unknown_cause_and_unverified_recovery(self):
        for name, button, label, operation in self.routes():
            with self.subTest(route=name):
                button.invoke()
                self.root.tick()
                operation.assert_called_once_with()
                self.assertIn("cause unknown", label.cget("text"))
                self.assert_guidance(label)
        self.assertEqual(self.ui._observe.cget("state"), "normal")
        self.assertEqual(self.ui._synthetic.cget("state"), "disabled")

    def test_fixed_denials_are_untrusted_and_do_not_verify_recovery(self):
        self.observe.return_value = window.NativeStatus.UNTRUSTED_HOLD
        self.request.return_value = window.SyntheticRequestStatus.UNTRUSTED_HOLD
        for name, button, label, operation in self.routes():
            with self.subTest(route=name):
                button.invoke()
                self.root.tick()
                operation.assert_called_once_with()
                text = label.cget("text")
                self.assertIn("UNTRUSTED_HOLD", text)
                self.assertIn("response is untrusted", text)
                self.assertIn("peer is not attested", text)
                self.assert_guidance(label)
        self.assertIn("fixed denial observed", self.ui._native_status.cget("text"))
        self.assertIn("synthetic denial received", self.ui._synthetic_status.cget("text"))

    def test_worker_exceptions_use_unknown_cause_without_private_details(self):
        self.observe.side_effect = RuntimeError("private observer detail")
        self.request.side_effect = RuntimeError("private requester detail")
        for name, button, label, operation in self.routes():
            with self.subTest(route=name):
                button.invoke()
                self.root.tick()
                operation.assert_called_once_with()
                self.assertIn("cause unknown", label.cget("text"))
                self.assertNotIn("private", label.cget("text"))
                self.assert_guidance(label)

    def test_thread_start_failure_uses_same_conservative_guidance(self):
        with patch.object(InlineThread, "start", side_effect=RuntimeError("private start detail")):
            for name, button, label, operation in self.routes():
                with self.subTest(route=name):
                    button.invoke()
                    self.root.tick()
                    operation.assert_not_called()
                    self.assertIn("cause unknown", label.cget("text"))
                    self.assertNotIn("private", label.cget("text"))
                    self.assert_guidance(label)

    def test_timeout_ignores_late_fixed_denial_without_changing_guidance(self):
        workers = []

        class StalledThread(InlineThread):
            def start(self):
                self.alive = True
                workers.append(self)

        self.observe.return_value = window.NativeStatus.UNTRUSTED_HOLD
        self.request.return_value = window.SyntheticRequestStatus.UNTRUSTED_HOLD
        with patch.object(window.threading, "Thread", StalledThread):
            self.ui._observe.invoke()
            self.ui._synthetic.invoke()
        self.clock.now = 1.499
        self.root.tick()
        self.assertEqual(len(self.root.pending), 2)
        self.clock.now = 1.5
        self.root.tick()
        self.assertFalse(self.root.pending)
        texts = [label.cget("text") for _, _, label, _ in self.routes()]
        for _, button, label, operation in self.routes():
            self.assertIn("cause unknown", label.cget("text"))
            self.assert_guidance(label)
            self.assertEqual(button.cget("state"), "disabled")
            operation.assert_not_called()
        for worker in workers:
            worker.target()
            worker.alive = False
        self.ui._poll_native_observation()
        self.ui._poll_synthetic_request()
        self.ui._observe.invoke()
        self.ui._synthetic.invoke()
        self.assertEqual(len(workers), 2)
        self.assertEqual(texts, [label.cget("text") for _, _, label, _ in self.routes()])
        self.assertTrue(self.ui._observer_disabled)
        self.assertTrue(self.ui._synthetic_attempted)
        self.observe.assert_called_once_with()
        self.request.assert_called_once_with()
        self.credentials.assert_not_called()
