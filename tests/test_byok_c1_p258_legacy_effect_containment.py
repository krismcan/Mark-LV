"""P258 actual default composition negatives, using fake native adapters only.

No real WinCred, mutex, child process, provider, credential or service access.
Original P132/P133 and backend tests remain independent and unchanged.
"""
from __future__ import annotations

import runpy
import sys
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from nayeon.brain import local_byok_user_scope as scope
from nayeon.desktop_alpha import local_byok_launch_bridge as bridge
from nayeon.desktop_alpha import local_byok_window as window
from nayeon.secrets import windows_credential as storage
from nayeon.secrets.contracts import SecretIdentifier, SecretStorageError, SecretValue
from tests.test_local_user_scope_byok import FakeMutex, FakeNative
from tests.test_windows_credential_backend import FakeDLL


TARGET = "nayeon-v1/secret/openai.api_key"
IDENTIFIER = SecretIdentifier("openai.api_key")
FIXTURE = "p258-synthetic-not-a-key"


class DefaultCompositionTests(unittest.TestCase):
    def setUp(self):
        self.dll = FakeDLL()
        self.mutex = FakeMutex()
        self.loader = self.enterContext(patch.object(
            storage, "_load_advapi32", return_value=self.dll,
        ))
        self.enterContext(patch.object(scope, "WindowsOnboardingMutex", return_value=self.mutex))
        self.enterContext(patch.object(storage.ctypes, "get_last_error", return_value=1168, create=True))
        self.controller = scope.compose_user_scope_local_byok()

    def assert_no_access(self):
        self.loader.assert_not_called()
        self.assertEqual(self.dll.events, [])
        self.assertEqual(self.mutex.enters, 0)

    def test_actual_factory_exact_type_and_zero_native_construction(self):
        self.assertIs(type(self.controller), scope.LocalByokController)
        self.assertFalse(self.controller.mutation_available)
        self.assert_no_access()

    def test_default_begin_denies_all_operations_before_presence_or_mutex(self):
        for operation in (*scope.LocalByokOperation, "save", None, object()):
            with self.subTest(operation=operation):
                self.assertIsNone(self.controller.begin(operation))
                self.assertIsNone(self.controller._pending)
        self.assert_no_access()

    def test_default_approve_denies_exact_forged_pending_review_for_every_operation(self):
        for operation in scope.LocalByokOperation:
            with self.subTest(operation=operation):
                self.dll.read_result = int(operation is not scope.LocalByokOperation.SAVE)
                review = scope.LocalByokReview(operation, bool(self.dll.read_result), "forged")
                self.controller._pending = review
                outcome = self.controller.approve(
                    review, confirmed=True,
                    candidate=None if operation is scope.LocalByokOperation.REMOVE else SecretValue(FIXTURE),
                    deletion_acknowledged=operation is scope.LocalByokOperation.REMOVE,
                )
                self.assertIs(outcome, scope.LocalByokOutcome.REFUSED)
                self.assertIsNone(self.controller._pending)
        self.assert_no_access()

    def test_default_approve_denies_malformed_state_without_secret_reveal(self):
        for review in (None, object(), {"operation": "save"}):
            self.controller._pending = review
            with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")):
                self.assertIs(self.controller.approve(
                    review, confirmed=True, candidate=SecretValue(FIXTURE),
                    deletion_acknowledged=True,
                ), scope.LocalByokOutcome.REFUSED)
        self.assert_no_access()

    def test_explicit_refresh_uses_metadata_and_free_only_never_copies_blob(self):
        with patch.object(storage.ctypes, "string_at", side_effect=AssertionError("no plaintext")):
            self.assertIs(self.controller.inspect_presence(), scope.LocalByokPresence.PRESENT_UNVALIDATED)
        self.assertEqual([event[0] for event in self.dll.events], ["read", "free"])
        self.assertEqual(self.dll.events[0], ("read", TARGET, 1, 0))
        self.assertEqual(self.mutex.enters, 0)
        self.assertFalse(self.controller.mutation_available)

    def test_refresh_does_not_enable_begin_or_forged_approval(self):
        self.controller.inspect_presence()
        before = list(self.dll.events)
        for operation in scope.LocalByokOperation:
            self.assertIsNone(self.controller.begin(operation))
            review = scope.LocalByokReview(operation, True, "forged-after-refresh")
            self.controller._pending = review
            self.assertIs(self.controller.approve(
                review, confirmed=True,
                candidate=None if operation is scope.LocalByokOperation.REMOVE else SecretValue(FIXTURE),
                deletion_acknowledged=operation is scope.LocalByokOperation.REMOVE,
            ), scope.LocalByokOutcome.REFUSED)
        self.assertEqual(self.dll.events, before)
        self.assertEqual(self.mutex.enters, 0)

    def test_refresh_absent_and_unavailable_are_fixed_presence_outcomes(self):
        self.dll.read_result = 0
        self.assertIs(self.controller.inspect_presence(), scope.LocalByokPresence.NOT_STORED)
        with patch.object(self.dll, "CredReadW", side_effect=OSError("synthetic private failure")):
            self.assertIs(self.controller.inspect_presence(), scope.LocalByokPresence.UNAVAILABLE)
        self.assertFalse(self.controller.mutation_available)

    def test_no_default_writable_argument_or_presentation_setter(self):
        with self.assertRaises(TypeError):
            scope.compose_user_scope_local_byok(writable=True)
        with self.assertRaises(AttributeError):
            self.controller.mutation_available = True
        self.assert_no_access()

    def test_forging_observation_backend_does_not_supply_default_effect_binding(self):
        native = FakeNative()
        self.controller._backend = storage.WindowsCredentialBackend(_native=native)
        review = scope.LocalByokReview(scope.LocalByokOperation.SAVE, False, "forged-backend")
        self.controller._pending = review
        self.assertIsNone(self.controller.begin(scope.LocalByokOperation.SAVE))
        self.assertIs(self.controller.approve(
            review, confirmed=True, candidate=SecretValue(FIXTURE),
        ), scope.LocalByokOutcome.REFUSED)
        self.assertFalse(self.controller.mutation_available)
        self.assertEqual(native.calls, [])
        self.assert_no_access()

    def test_restart_constructs_another_presence_only_controller(self):
        self.controller._pending = scope.LocalByokReview(scope.LocalByokOperation.SAVE, False, "old")
        restarted = scope.compose_user_scope_local_byok()
        self.assertIsNot(restarted, self.controller)
        self.assertFalse(restarted.mutation_available)
        self.assertIsNone(restarted.begin(scope.LocalByokOperation.SAVE))
        self.assert_no_access()

    def test_explicit_fake_injected_original_workflow_is_preserved(self):
        native = FakeNative()
        controller = scope.LocalByokController(storage.WindowsCredentialBackend(_native=native), _mutex=self.mutex)
        self.assertTrue(controller.mutation_available)
        review = controller.begin(scope.LocalByokOperation.SAVE)
        self.assertIs(controller.approve(review, confirmed=True, candidate=SecretValue(FIXTURE)),
                      scope.LocalByokOutcome.SUBMITTED_UNVALIDATED)
        self.assertEqual(native.blobs[TARGET], FIXTURE.encode())
        self.loader.assert_not_called()
        self.assertEqual(self.dll.events, [])


class DefaultBackendDenialTests(unittest.TestCase):
    def setUp(self):
        self.dll = FakeDLL()
        self.loader = self.enterContext(patch.object(storage, "_load_advapi32", return_value=self.dll))
        self.backend = storage.WindowsCredentialBackend()

    def test_direct_default_get_denies_before_adapter_access_or_setup(self):
        with patch.object(self.backend, "_adapter", side_effect=AssertionError("no adapter access")) as adapter:
            with self.assertRaisesRegex(SecretStorageError, "^Secret storage operation failed$"):
                self.backend.get(IDENTIFIER)
        adapter.assert_not_called()
        self.loader.assert_not_called()
        self.assertEqual(self.dll.events, [])

    def test_direct_default_get_stays_denied_after_presence_loads_adapter(self):
        with patch.object(storage.ctypes, "string_at", side_effect=AssertionError("no plaintext")) as copy:
            self.assertTrue(self.backend.is_available(IDENTIFIER))
        copy.assert_not_called()
        self.loader.assert_called_once_with()
        self.assertEqual([event[0] for event in self.dll.events], ["read", "free"])
        before = list(self.dll.events)
        with patch.object(self.backend, "_adapter", side_effect=AssertionError("no adapter access")) as adapter, \
                patch.object(storage._Advapi32Adapter, "read", side_effect=AssertionError("no plaintext read")) as read:
            with self.assertRaisesRegex(SecretStorageError, "^Secret storage operation failed$"):
                self.backend.get(IDENTIFIER)
        adapter.assert_not_called()
        read.assert_not_called()
        self.loader.assert_called_once_with()
        self.assertEqual(self.dll.events, before)

    def test_direct_default_put_delete_deny_before_setup_or_secret_reveal(self):
        with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
            with self.assertRaises(SecretStorageError):
                self.backend.put(IDENTIFIER, SecretValue(FIXTURE))
            with self.assertRaises(SecretStorageError):
                self.backend.delete(IDENTIFIER)
        reveal.assert_not_called()
        self.loader.assert_not_called()
        self.assertEqual(self.dll.events, [])

    def test_direct_default_put_delete_stay_denied_after_presence_loads_adapter(self):
        self.assertTrue(self.backend.is_available(IDENTIFIER))
        before = list(self.dll.events)
        with self.assertRaises(SecretStorageError):
            self.backend.put(IDENTIFIER, SecretValue(FIXTURE))
        with self.assertRaises(SecretStorageError):
            self.backend.delete(IDENTIFIER)
        self.assertEqual(self.dll.events, before)
        controller = scope.LocalByokController(self.backend, _mutex=FakeMutex())
        self.assertFalse(controller.mutation_available)
        self.assertIsNone(controller.begin(scope.LocalByokOperation.REPLACE))
        self.assertEqual(self.dll.events, before)

    def test_explicit_native_adapter_is_not_accepted_as_fake_mutation_binding(self):
        adapter = storage._Advapi32Adapter()  # Loader supplies ONLY FakeDLL.
        backend = storage.WindowsCredentialBackend(_native=adapter)
        controller = scope.LocalByokController(backend, _mutex=FakeMutex())
        self.assertFalse(controller.mutation_available)
        with self.assertRaises(SecretStorageError):
            backend.put(IDENTIFIER, SecretValue(FIXTURE))
        with self.assertRaises(SecretStorageError):
            backend.delete(IDENTIFIER)
        self.assertEqual(self.dll.events, [])


class EntryAndBridgeTests(unittest.TestCase):
    def test_source_main_passes_actual_presence_only_factory_without_native_access(self):
        root = Mock()
        captured = []
        def capture(actual_root, *, controller):
            self.assertIs(actual_root, root)
            self.assertIs(type(controller), scope.LocalByokController)
            self.assertFalse(controller.mutation_available)
            self.assertIsNone(controller.begin(scope.LocalByokOperation.SAVE))
            captured.append(controller)
        with patch.object(window.sys, "platform", "win32"), \
                patch.object(window.tk, "Tk", return_value=root), \
                patch.object(window, "LocalByokWindow", side_effect=capture), \
                patch.object(storage, "_load_advapi32", side_effect=AssertionError("no native access")) as loader:
            window.main()
        self.assertEqual(len(captured), 1)
        root.mainloop.assert_called_once_with()
        loader.assert_not_called()

    def test_manual_module_guard_reaches_same_actual_default_factory(self):
        root = Mock()
        # Execute the exact source as __main__, with only the Tk surface faked.
        # The real LocalByokWindow and factory run; no real GUI/native access.
        with patch.object(sys, "platform", "win32"), \
                patch.object(tk, "Tk", return_value=root), \
                patch.object(tk, "Label"), patch.object(tk, "Button"), \
                patch.object(tk, "Entry"), patch.object(tk, "Checkbutton"), \
                patch.object(tk, "BooleanVar"), \
                patch.object(storage, "_load_advapi32", side_effect=AssertionError("no native access")) as loader:
            namespace = runpy.run_path(window.__file__, run_name="__main__")
        self.assertIs(namespace["compose_user_scope_local_byok"], scope.compose_user_scope_local_byok)
        root.mainloop.assert_called_once_with()
        self.assertIn("read-only status", root.title.call_args.args[0])
        loader.assert_not_called()

    def test_source_bridge_retains_fixed_module_and_zero_native_access(self):
        child = Mock(pid=258)
        child.poll.return_value = None
        with patch.object(bridge.sys, "platform", "win32"), \
                patch.object(bridge.sys, "frozen", False, create=True), \
                patch.object(bridge.sys, "executable", "C:/p258-fixture/python.exe"), \
                patch.object(bridge.subprocess, "Popen", return_value=child) as popen, \
                patch.object(storage, "_load_advapi32", side_effect=AssertionError("no native access")) as loader:
            owner = bridge.LocalByokLaunchBridge()
            self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.LAUNCHED_OFFLINE)
            self.assertIs(owner.launch(), bridge.LocalByokLaunchResult.ALREADY_RUNNING)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(popen.call_args.args[0], ["C:/p258-fixture/python.exe", "-B", "-m",
                                                 "nayeon.desktop_alpha.local_byok_window"])
        self.assertFalse(popen.call_args.kwargs["shell"])
        loader.assert_not_called()

    def test_frozen_bridge_still_refuses_without_writable_python_fallback(self):
        with patch.object(bridge.sys, "platform", "win32"), \
                patch.object(bridge.sys, "frozen", True, create=True), \
                patch.object(bridge.sys, "executable", "C:/p258-fixture/nayeon.exe"), \
                patch.object(bridge.subprocess, "Popen") as popen:
            self.assertIs(bridge.LocalByokLaunchBridge().launch(), bridge.LocalByokLaunchResult.UNAVAILABLE)
        popen.assert_not_called()


@unittest.skipUnless(sys.platform == "win32", "Actual Windows Tk only")
class DefaultReadOnlyTkTests(unittest.TestCase):
    def setUp(self):
        self.dll = FakeDLL()
        self.loader = self.enterContext(patch.object(storage, "_load_advapi32", return_value=self.dll))
        self.enterContext(patch.object(scope, "WindowsOnboardingMutex", return_value=FakeMutex()))
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.controller = scope.compose_user_scope_local_byok()
        self.window = window.LocalByokWindow(self.root, controller=self.controller)

    def assert_mutation_disabled(self):
        for widget in (*self.window._choices, self.window._entry, self.window._confirm,
                       self.window._delete_ack, self.window._approve, self.window._reject):
            self.assertEqual(str(widget.cget("state")), "disabled")
        self.assertEqual(str(self.window._refresh.cget("state")), "normal")

    def test_default_window_explains_wait_and_disables_all_mutation_affordances(self):
        self.assert_mutation_disabled()
        notice = self.window._mode_notice.cget("text")
        self.assertIn("READ-ONLY", notice)
        self.assertIn("service-only", notice)
        self.assertIn("waiting", notice)
        self.loader.assert_not_called()
        self.assertEqual(self.dll.events, [])
        self.window._entry.insert(0, FIXTURE)
        self.assertEqual(self.window._entry.get(), "")

    def test_disabled_buttons_and_direct_callbacks_cannot_mutate_or_read_entry(self):
        for button in (*self.window._choices, self.window._confirm,
                       self.window._delete_ack, self.window._approve):
            button.invoke()
        for operation in scope.LocalByokOperation:
            self.window.review_from_button(operation)
            review = scope.LocalByokReview(operation, True, "forged-ui-review")
            self.window._review = self.controller._pending = review
            self.window._confirmed.set(True)
            self.window._delete_checked.set(True)
            self.window._sync()
            self.assert_mutation_disabled()
            with patch.object(self.window._entry, "get", side_effect=AssertionError("no candidate read")):
                self.window.approve_from_button()
        self.loader.assert_not_called()
        self.assertEqual(self.dll.events, [])

    def test_explicit_ui_refresh_remains_presence_only_and_never_enables_mutation(self):
        with patch.object(storage.ctypes, "string_at", side_effect=AssertionError("no plaintext")):
            self.window._refresh.invoke()
        self.assertEqual([event[0] for event in self.dll.events], ["read", "free"])
        self.assertIn("NOT been validated", self.window._status.cget("text"))
        self.assert_mutation_disabled()


if __name__ == "__main__":
    unittest.main()
