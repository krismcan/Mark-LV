"""P132 synthetic acceptance of offline current-Windows-user BYOK.

No test uses a real API key, provider network or native Credential Manager
mutation. Windows native UI and mutex tests use an injected fake adapter.
"""
from __future__ import annotations

from contextlib import contextmanager
import ast
import inspect
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

from nayeon.brain.local_byok_user_scope import (
    LocalByokController, LocalByokOperation as Op, LocalByokOutcome as Outcome,
    LocalByokPresence as Presence, compose_user_scope_local_byok,
)
from nayeon.brain.windows_onboarding_mutex import MutexAdmission, WindowsOnboardingMutex
from nayeon.secrets.contracts import SecretValue
from nayeon.secrets.windows_credential import WindowsCredentialBackend


_TARGET = "nayeon-v1/secret/openai.api_key"
_FIXTURE = "fixture-local-test-value-not-an-api-key"
_ROOT = Path(__file__).resolve().parents[1]


class FakeNative:
    def __init__(self):
        self.blobs = {}
        self.calls = []
        self.raise_when = set()
        self.after_write_failure = False
        self.on_contains = None

    def contains(self, target):
        self.calls.append(("contains", target))
        if "contains" in self.raise_when:
            raise OSError("sensitive backend failure " + _FIXTURE)
        if self.on_contains is not None:
            self.on_contains()
        return target in self.blobs

    def read(self, target):
        self.calls.append(("read", target))
        raise AssertionError("No local BYOK controller/UI may read a stored key")

    def write(self, target, blob, credential_type, persist, username):
        self.calls.append(("write", target))
        if "write" in self.raise_when:
            raise OSError("sensitive WinCred failure " + _FIXTURE)
        if target != _TARGET or credential_type != 1 or persist != 2:
            raise AssertionError("Wrong fixed current-user generic key target")
        if type(blob) is not bytes:
            raise AssertionError("Expected UTF8 encoded secret from backend")
        self.blobs[target] = bytes(blob)
        if self.after_write_failure:
            raise OSError("after effect, uncertain " + _FIXTURE)

    def delete(self, target):
        self.calls.append(("delete", target))
        if "delete" in self.raise_when:
            raise OSError("secret error " + _FIXTURE)
        return self.blobs.pop(target, None) is not None


class FakeMutex:
    def __init__(self, state=MutexAdmission.HELD):
        self.state = state
        self.enters = 0
        self.exits = 0

    @contextmanager
    def hold(self):
        self.enters += 1
        try:
            yield self.state
        finally:
            self.exits += 1


class LocalOfflineControllerTests(unittest.TestCase):
    def setUp(self):
        self.native = FakeNative()
        self.backend = WindowsCredentialBackend(_native=self.native)
        self.mutex = FakeMutex()
        self.controller = LocalByokController(self.backend, _mutex=self.mutex)

    def connected(self):
        self.native.blobs[_TARGET] = b"previous-synthetic-only"

    def approve(self, op, *, value=_FIXTURE, confirmed=True, delete_ack=False):
        review = self.controller.begin(op)
        self.assertIsNotNone(review)
        return self.controller.approve(
            review, confirmed=confirmed,
            candidate=(None if op is Op.REMOVE else SecretValue(value)),
            deletion_acknowledged=delete_ack,
        )

    def test_constructor_and_factory_do_not_touch_native_credential_manager(self):
        self.assertEqual(self.native.calls, [])
        with patch(
            "nayeon.secrets.windows_credential._load_advapi32",
            side_effect=AssertionError("no native activation on construct"),
        ):
            factory = compose_user_scope_local_byok()
        self.assertIs(type(factory), LocalByokController)
        self.assertEqual(self.native.calls, [])

    def test_type_restrictions_do_not_allow_an_arbitrary_secret_backend(self):
        with self.assertRaises(TypeError):
            LocalByokController(self.native, _mutex=self.mutex)

    def test_initial_presence_is_explicit_and_only_uses_contains(self):
        self.assertEqual(self.native.calls, [])
        self.assertIs(self.controller.inspect_presence(), Presence.NOT_STORED)
        self.assertEqual(self.native.calls, [("contains", _TARGET)])
        self.assertNotIn(("read", _TARGET), self.native.calls)

    def test_existing_presence_never_claims_valid_connection(self):
        self.connected()
        self.assertIs(self.controller.inspect_presence(), Presence.PRESENT_UNVALIDATED)
        self.assertEqual(self.native.calls, [("contains", _TARGET)])

    def test_begin_save_never_mutates_or_validates(self):
        review = self.controller.begin(Op.SAVE)
        self.assertIs(review.operation, Op.SAVE)
        self.assertFalse(review.original_present)
        self.assertEqual(self.native.calls, [("contains", _TARGET)])
        self.assertEqual(self.mutex.enters, 0)
        self.assertNotIn(_FIXTURE, repr(review))

    def test_begin_prevents_save_over_existing_slot(self):
        self.connected()
        self.assertIsNone(self.controller.begin(Op.SAVE))
        self.assertEqual(self.native.blobs[_TARGET], b"previous-synthetic-only")

    def test_replace_requires_existing_key_and_does_not_auto_create(self):
        self.assertIsNone(self.controller.begin(Op.REPLACE))
        self.assertFalse(self.native.blobs)

    def test_remove_requires_existing_key(self):
        self.assertIsNone(self.controller.begin(Op.REMOVE))

    def test_invalid_operation_cannot_create_review(self):
        for op in ("save", 1, None, object()):
            self.assertIsNone(self.controller.begin(op))
        self.assertFalse(self.native.calls)

    def test_duplicate_pending_review_and_cancel_are_one_use(self):
        review = self.controller.begin(Op.SAVE)
        self.assertIsNone(self.controller.begin(Op.SAVE))
        self.assertTrue(self.controller.reject(review))
        self.assertFalse(self.controller.reject(review))
        self.assertIs(
            self.controller.approve(review, confirmed=True, candidate=SecretValue(_FIXTURE)),
            Outcome.REFUSED,
        )
        self.assertFalse(self.native.blobs)

    def test_explicit_confirmation_required_before_write(self):
        review = self.controller.begin(Op.SAVE)
        result = self.controller.approve(
            review, confirmed=False, candidate=SecretValue(_FIXTURE),
        )
        self.assertIs(result, Outcome.REFUSED)
        self.assertFalse(self.native.blobs)
        self.assertEqual(self.mutex.enters, 0)

    def test_raw_string_cannot_replace_opaque_secret_value(self):
        review = self.controller.begin(Op.SAVE)
        self.assertIs(
            self.controller.approve(review, confirmed=True, candidate=_FIXTURE),
            Outcome.REFUSED,
        )
        self.assertFalse(self.native.blobs)

    def test_save_with_deliberate_review_and_confirm_is_offline_only(self):
        result = self.approve(Op.SAVE)
        self.assertIs(result, Outcome.SUBMITTED_UNVALIDATED)
        self.assertEqual(self.native.blobs[_TARGET], _FIXTURE.encode("utf-8"))
        self.assertEqual(self.mutex.enters, 1)
        self.assertEqual(self.mutex.exits, 1)
        self.assertTrue(all(action[0] not in ("read", "network")
                            for action in self.native.calls))

    def test_explicit_replace_updates_only_fixed_slot(self):
        self.connected()
        self.assertIs(self.approve(Op.REPLACE), Outcome.SUBMITTED_UNVALIDATED)
        self.assertEqual(self.native.blobs[_TARGET], _FIXTURE.encode("utf-8"))
        self.assertEqual(set(self.native.blobs), {_TARGET})

    def test_replacement_storage_failure_preserves_old_fake_value(self):
        self.connected()
        self.native.raise_when.add("write")
        result = self.approve(Op.REPLACE)
        self.assertIs(result, Outcome.RECONCILIATION_REQUIRED)
        self.assertEqual(self.native.blobs[_TARGET], b"previous-synthetic-only")
        self.assertIs(self.controller.inspect_presence(), Presence.RECONCILIATION_REQUIRED)
        self.assertIsNone(self.controller.begin(Op.REPLACE))

    def test_write_then_exception_is_unknown_and_never_auto_retried(self):
        self.native.after_write_failure = True
        result = self.approve(Op.SAVE)
        self.assertIs(result, Outcome.RECONCILIATION_REQUIRED)
        self.assertEqual(self.native.blobs[_TARGET], _FIXTURE.encode("utf-8"))
        writes = len([x for x in self.native.calls if x[0] == "write"])
        self.assertIsNone(self.controller.begin(Op.REPLACE))
        self.assertEqual(
            len([x for x in self.native.calls if x[0] == "write"]), writes,
        )

    def test_explicit_delete_needs_destructive_acknowledgment(self):
        self.connected()
        review = self.controller.begin(Op.REMOVE)
        self.assertIs(
            self.controller.approve(
                review, confirmed=True, deletion_acknowledged=False,
            ), Outcome.REFUSED,
        )
        self.assertEqual(self.native.blobs[_TARGET], b"previous-synthetic-only")
        self.assertEqual(self.mutex.enters, 0)

    def test_delete_requires_both_confirmations_and_never_reads_key(self):
        self.connected()
        result = self.approve(Op.REMOVE, delete_ack=True)
        self.assertIs(result, Outcome.SUBMITTED_REMOVAL)
        self.assertNotIn(_TARGET, self.native.blobs)
        self.assertFalse(any(x[0] == "read" for x in self.native.calls))

    def test_stale_review_ticket_cannot_approve_successor(self):
        old = self.controller.begin(Op.SAVE)
        self.controller.reject(old)
        new = self.controller.begin(Op.SAVE)
        self.assertIsNot(old, new)
        self.assertIs(
            self.controller.approve(
                old, confirmed=True, candidate=SecretValue(_FIXTURE)
            ), Outcome.REFUSED,
        )
        self.assertIs(
            self.controller.approve(
                new, confirmed=True, candidate=SecretValue(_FIXTURE)
            ), Outcome.SUBMITTED_UNVALIDATED,
        )
        self.assertEqual(len([x for x in self.native.calls if x[0] == "write"]), 1)

    def test_slot_presence_change_before_effect_is_denied(self):
        review = self.controller.begin(Op.SAVE)
        self.native.blobs[_TARGET] = b"external-before-effect"
        result = self.controller.approve(
            review, confirmed=True, candidate=SecretValue(_FIXTURE),
        )
        self.assertIs(result, Outcome.CONFLICT)
        self.assertEqual(self.native.blobs[_TARGET], b"external-before-effect")

    def test_busy_other_cooperating_process_does_not_mutate(self):
        self.mutex.state = MutexAdmission.BUSY
        self.assertIs(self.approve(Op.SAVE), Outcome.BUSY)
        self.assertFalse(self.native.blobs)

    def test_abandoned_real_mutex_state_requires_reconciliation(self):
        self.mutex.state = MutexAdmission.ABANDONED
        self.assertIs(self.approve(Op.SAVE), Outcome.RECONCILIATION_REQUIRED)
        self.assertFalse(self.native.blobs)
        self.assertIsNone(self.controller.begin(Op.SAVE))

    def test_unavailable_mutex_state_requires_reconciliation(self):
        self.mutex.state = MutexAdmission.UNAVAILABLE
        self.assertIs(self.approve(Op.SAVE), Outcome.RECONCILIATION_REQUIRED)
        self.assertFalse(self.native.blobs)

    def test_backend_presence_error_is_non_secret_and_fail_closed(self):
        self.native.raise_when.add("contains")
        self.assertIs(self.controller.inspect_presence(), Presence.UNAVAILABLE)
        self.assertIsNone(self.controller.begin(Op.SAVE))
        self.assertNotIn(_FIXTURE, repr(self.controller))

    def test_delete_exception_never_claims_absence(self):
        self.connected()
        self.native.raise_when.add("delete")
        self.assertIs(
            self.approve(Op.REMOVE, delete_ack=True),
            Outcome.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(self.native.blobs[_TARGET], b"previous-synthetic-only")

    def test_racing_twelve_approvals_one_submission(self):
        review = self.controller.begin(Op.SAVE)
        gate = threading.Barrier(12)
        outcomes = []
        lock = threading.Lock()
        def worker():
            gate.wait()
            result = self.controller.approve(
                review, confirmed=True, candidate=SecretValue(_FIXTURE),
            )
            with lock:
                outcomes.append(result)
        threads = [threading.Thread(target=worker) for _ in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=3)
            self.assertFalse(t.is_alive())
        self.assertEqual(outcomes.count(Outcome.SUBMITTED_UNVALIDATED), 1)
        self.assertEqual(outcomes.count(Outcome.REFUSED), 11)
        self.assertEqual(len([x for x in self.native.calls if x[0] == "write"]), 1)

    def test_source_has_no_provider_network_or_automatic_key_read(self):
        import nayeon.brain.local_byok_user_scope as m
        text = inspect.getsource(m)
        self.assertNotIn("backend.get(", text)
        self.assertNotIn("requests.", text)
        self.assertNotIn("OpenAICredentialValidator", text)
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, {
                    "nayeon.brain.providers.openai_validation",
                    "nayeon.secrets.resolver",
                })
        self.assertNotIn(_FIXTURE, repr(self.controller))

    def test_normal_offline_app_entrypoint_unchanged_and_no_new_import(self):
        text = (_ROOT / "nayeon/desktop_alpha/__main__.py").read_text()
        self.assertNotIn("local_byok_window", text)
        self.assertIn("--notepad", text)


@unittest.skipUnless(sys.platform == "win32", "Genuine Windows host only")
class WindowsUserScopeNativeMutexTests(unittest.TestCase):
    def test_real_windows_mutex_with_fake_credential_backend(self):
        backend = WindowsCredentialBackend(_native=FakeNative())
        ctrl = LocalByokController(backend, _mutex=WindowsOnboardingMutex())
        review = ctrl.begin(Op.SAVE)
        self.assertIsNotNone(review)
        self.assertIs(
            ctrl.approve(review, confirmed=True, candidate=SecretValue(_FIXTURE)),
            Outcome.SUBMITTED_UNVALIDATED,
        )
        self.assertIs(ctrl.inspect_presence(), Presence.PRESENT_UNVALIDATED)


@unittest.skipUnless(sys.platform == "win32", "Windows Tk only")
class WindowsLocalByokRealTkTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from nayeon.desktop_alpha.local_byok_window import LocalByokWindow
        self.tk = tk
        self.root = tk.Tk()
        self.root.withdraw()
        self.native = FakeNative()
        self.ctrl = LocalByokController(
            WindowsCredentialBackend(_native=self.native),
            _mutex=FakeMutex(),
        )
        self.window = LocalByokWindow(self.root, controller=self.ctrl)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        try:
            self.window.close_from_window()
        except Exception:
            pass
        try:
            self.root.destroy()
        except self.tk.TclError:
            pass

    def test_real_tk_initial_launch_no_credential_access(self):
        self.assertEqual(self.native.calls, [])
        self.assertEqual(self.window._entry.cget("show"), "*")
        self.assertEqual(self.window._entry.cget("state"), "disabled")

    def test_real_tk_save_needs_review_then_explicit_confirm(self):
        self.window._choices[0].invoke()
        self.window._entry.insert(0, _FIXTURE)
        self.window._approve.invoke()
        self.assertFalse(self.native.blobs)
        self.window._confirm.invoke()
        self.window._approve.invoke()
        self.assertEqual(self.native.blobs[_TARGET], _FIXTURE.encode("utf-8"))
        self.assertEqual(self.window._entry.get(), "")
        self.assertEqual(self.window._entry.cget("state"), "disabled")
        self.assertIn("NOT confirmed", self.window._status.cget("text"))

    def test_real_tk_delete_requires_two_acknowledgements(self):
        self.native.blobs[_TARGET] = b"old-synthetic"
        self.window._choices[2].invoke()
        self.window._confirm.invoke()
        self.window._approve.invoke()
        self.assertIn(_TARGET, self.native.blobs)
        self.window._delete_ack.invoke()
        self.window._approve.invoke()
        self.assertNotIn(_TARGET, self.native.blobs)

    def test_real_tk_reject_scrubs_candidate_without_write(self):
        self.window._choices[0].invoke()
        self.window._entry.insert(0, _FIXTURE)
        self.window._reject.invoke()
        self.assertEqual(self.window._entry.get(), "")
        self.assertFalse(self.native.blobs)

    def test_real_tk_close_rejects_pending_without_effect(self):
        self.window._choices[0].invoke()
        self.window._entry.insert(0, _FIXTURE)
        self.window.close_from_window()
        self.assertFalse(self.native.blobs)

    def test_real_tk_status_is_presence_only(self):
        self.native.blobs[_TARGET] = b"synthetic-old"
        self.window._refresh.invoke()
        self.assertIn("NOT been validated", self.window._status.cget("text"))
        self.assertEqual(self.native.calls, [("contains", _TARGET)])

    def test_real_tk_source_has_no_direct_credential_native_or_provider(self):
        from nayeon.desktop_alpha import local_byok_window as m
        text = inspect.getsource(m)
        for forbidden in (
            "WindowsCredentialBackend", "CredWriteW", "CredReadW",
            "OpenAICredentialValidator", "requests.", "backend.get(",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
