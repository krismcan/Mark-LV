"""Deterministic desktop observation checks; no live desktop calls in discovery."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from tempfile import TemporaryDirectory
import ctypes
import json
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.dispatch import DispatchKind, DispatchPlan, IntentDispatcher
from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.orchestration import StructuredOrchestrationBridge
from nayeon.agent.router import TaskRouter
from nayeon.audit.service import AuditService, AuditEventType
from nayeon.capabilities.loader import CapabilityLoader
from nayeon.capabilities.observe_foreground_window import ObserveForegroundWindowCapability
from nayeon.capabilities.structured import StructuredCapability, IntentArgumentMapper, StructuredCapabilityRequest
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.model import IntentContext
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry, ExecutionMode
from nayeon.services.computer_control import (
    ComputerControlService, DesktopContext, ForegroundEvidence, ForegroundObservation,
    ForegroundState, ObservationReason, WindowIdentity, WindowState,
)
from nayeon.services.windows_desktop import WindowsDesktopAdapter, _WindowsNative
from nayeon.undo.contract import UndoProvider
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationProvider, VerificationStatus
from nayeon.verification.service import VerificationService


CONTEXT = DesktopContext(7, "Default", "Default", "WinSta0", True)
IDENTITY = WindowIdentity(987654, 456789, 345678, 123456789, r"C:\private\fixture.exe",
                          "PrivateFixtureClass", 987654, 7, "Default")
STATE = WindowState(True, False, False, (0, 0, 100, 100), (0, 0, 80, 80), (10, 10), 92, 96, 0, 0)


def observed():
    return ForegroundObservation(ForegroundState.OBSERVED, ObservationReason.CONSISTENT,
        ForegroundEvidence(IDENTITY, IDENTITY, CONTEXT, CONTEXT, STATE, 10, 20))


def fake_native():
    native = Mock()
    native.context.return_value = CONTEXT
    native.foreground.return_value = IDENTITY.hwnd
    native.identity.return_value = IDENTITY
    native.state.return_value = STATE
    return native


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.native = fake_native()
        self.adapter = WindowsDesktopAdapter(native=self.native, platform="win32", clock=Mock(side_effect=[10, 20]))

    def sample(self):
        return self.adapter.observe_foreground_window()

    def test_stable_snapshot(self):
        result = self.sample()
        self.assertEqual(result, observed())
        self.assertTrue(result._evidence.consistent())

    def test_fixed_acquisition_order_no_retry(self):
        self.sample()
        self.assertEqual([call[0] for call in self.native.mock_calls],
                         ["context", "foreground", "identity", "state", "context", "foreground", "identity"])

    def test_transition_is_partial_without_merged_evidence(self):
        self.native.foreground.side_effect = [IDENTITY.hwnd, IDENTITY.hwnd + 1]
        result = self.sample()
        self.assertIs(result.state, ForegroundState.PARTIAL)
        self.assertIs(result.reason, ObservationReason.CHANGED)
        self.assertIsNone(result._evidence)
        self.assertEqual(self.native.foreground.call_count, 2)
        self.assertEqual(self.native.identity.call_count, 1)

    def test_null_in_supported_context_has_no_identity(self):
        self.native.foreground.return_value = 0
        result = self.sample()
        self.assertIs(result.state, ForegroundState.NO_FOREGROUND)
        self.assertIsNone(result._evidence)
        self.native.identity.assert_not_called()
        self.native.state.assert_not_called()

    def test_unsupported_platform_zero_calls(self):
        result = WindowsDesktopAdapter(native=self.native, platform="linux").observe_foreground_window()
        self.assertIs(result.state, ForegroundState.UNAVAILABLE)
        self.assertEqual(self.native.mock_calls, [])

    def test_invalid_initial_context_never_samples_foreground(self):
        for context in (None, replace(CONTEXT, session=0), replace(CONTEXT, active=False),
                        replace(CONTEXT, input_desktop="Winlogon"),
                        replace(CONTEXT, thread_desktop="Alternate"), replace(CONTEXT, station="Other")):
            with self.subTest(context=context):
                native = fake_native()
                native.context.return_value = context
                result = WindowsDesktopAdapter(native=native, platform="win32").observe_foreground_window()
                self.assertIs(result.state, ForegroundState.UNAVAILABLE)
                native.foreground.assert_not_called()

    def test_initial_context_error_redacted(self):
        self.native.context.side_effect = OSError("private native failure")
        result = self.sample()
        self.assertIs(result.state, ForegroundState.UNAVAILABLE)
        self.assertNotIn("private native failure", repr(result))

    def test_process_access_error_is_partial(self):
        self.native.identity.side_effect = OSError("private process path")
        result = self.sample()
        self.assertIs(result.state, ForegroundState.PARTIAL)
        self.assertIsNone(result._evidence)

    def test_invalid_candidate_required_fields_partial(self):
        for changes in ({"hwnd": 0}, {"pid": 0}, {"tid": 0}, {"creation_time": 0},
                        {"executable": ""}, {"window_class": ""}, {"root": 8},
                        {"session": 99}, {"desktop": "Other"}):
            with self.subTest(changes=changes):
                self.setUp()
                self.native.identity.return_value = replace(IDENTITY, **changes)
                result = self.sample()
                self.assertIs(result.state, ForegroundState.PARTIAL)
                self.assertIsNone(result._evidence)

    def test_late_ownership_or_process_change_partial(self):
        for changes in ({"pid": IDENTITY.pid + 1}, {"tid": IDENTITY.tid + 1},
                        {"creation_time": IDENTITY.creation_time + 1},
                        {"executable": r"C:\private\replacement.exe"}, {"window_class": "Other"}):
            with self.subTest(changes=changes):
                self.setUp()
                self.native.identity.side_effect = [IDENTITY, replace(IDENTITY, **changes)]
                result = self.sample()
                self.assertIs(result.state, ForegroundState.PARTIAL)
                self.assertIsNone(result._evidence)

    def test_late_context_unavailable_is_candidate_partial(self):
        self.native.context.side_effect = [CONTEXT, OSError("private")]
        self.assertIs(self.sample().state, ForegroundState.PARTIAL)

    def test_late_context_mismatch_partial(self):
        self.native.context.side_effect = [CONTEXT, replace(CONTEXT, session=8)]
        self.assertIs(self.sample().state, ForegroundState.PARTIAL)

    def test_late_candidate_destroyed_partial(self):
        self.native.identity.side_effect = [IDENTITY, OSError("destroyed")]
        self.assertIs(self.sample().state, ForegroundState.PARTIAL)

    def test_same_process_windows_distinct(self):
        other = replace(IDENTITY, hwnd=IDENTITY.hwnd + 1, root=IDENTITY.root + 1)
        self.assertNotEqual(other, IDENTITY)
        self.assertEqual(other.pid, IDENTITY.pid)
        self.assertEqual(other.creation_time, IDENTITY.creation_time)

    def test_restart_same_executable_distinct(self):
        other = replace(IDENTITY, creation_time=IDENTITY.creation_time + 1)
        self.assertNotEqual(other, IDENTITY)
        self.assertEqual(other.executable, IDENTITY.executable)

    def test_visibility_iconic_independent(self):
        for visible, iconic in ((True, False), (True, True), (False, True), (False, False)):
            with self.subTest(visible=visible, iconic=iconic):
                native = fake_native()
                native.state.return_value = replace(STATE, visible=visible, iconic=iconic)
                result = WindowsDesktopAdapter(native=native, platform="win32").observe_foreground_window()
                self.assertIs(result.state, ForegroundState.OBSERVED)
                self.assertEqual(result._evidence.state.visible, visible)
                self.assertEqual(result._evidence.state.iconic, iconic)

    def test_geometry_dpi_optional_not_identity(self):
        self.native.state.return_value = WindowState()
        result = self.sample()
        self.assertIs(result.state, ForegroundState.OBSERVED)
        self.assertEqual(result._evidence.early, IDENTITY)
        self.assertIsNone(result._evidence.state.dpi)

    def test_evidence_deepcopy_and_frozen(self):
        value = observed()
        self.assertEqual(deepcopy(value), value)
        for obj, key, value in ((value, "state", None), (value._evidence, "early", None),
                                (IDENTITY, "pid", 0), (STATE, "visible", False), (CONTEXT, "session", 0)):
            self.assertFalse(hasattr(obj, "__dict__"))
            with self.subTest(obj=obj), self.assertRaises(FrozenInstanceError):
                setattr(obj, key, value)

    def test_all_representations_redacted(self):
        for obj in (observed(), observed()._evidence, IDENTITY, CONTEXT, STATE):
            for text in (repr(obj), str(obj)):
                for secret in (str(IDENTITY.hwnd), str(IDENTITY.pid), IDENTITY.executable,
                               IDENTITY.window_class, "WinSta0", "Default"):
                    self.assertNotIn(secret, text)

    def test_public_state_reason_are_typed(self):
        with self.assertRaises(TypeError):
            ForegroundObservation("observed", ObservationReason.CONSISTENT)
        with self.assertRaises(TypeError):
            ForegroundObservation(ForegroundState.OBSERVED, "raw detail")

    def test_service_exception_sanitized(self):
        adapter = Mock()
        adapter.observe_foreground_window.side_effect = OSError("private native error")
        result = ComputerControlService(adapter=adapter).observe_foreground_window()
        self.assertIs(result.state, ForegroundState.UNAVAILABLE)
        self.assertNotIn("private native error", repr(result))

    def test_service_invalid_result_conservative(self):
        adapter = Mock()
        adapter.observe_foreground_window.return_value = {"pid": 100}
        result = ComputerControlService(adapter=adapter).observe_foreground_window()
        self.assertIs(result.state, ForegroundState.UNAVAILABLE)

    def test_mutable_nested_evidence_rejected(self):
        for constructor in (lambda: WindowState(window_rect=[0, 0, 1, 1]),
                            lambda: replace(IDENTITY, executable=[]),
                            lambda: replace(CONTEXT, input_desktop=[]),
                            lambda: replace(observed()._evidence, state={})):
            with self.subTest(constructor=constructor), self.assertRaises(TypeError):
                constructor()

    def test_identity_must_bind_sampled_hwnd(self):
        self.native.identity.return_value = replace(IDENTITY, hwnd=8, root=8)
        self.assertIs(self.sample().state, ForegroundState.PARTIAL)

    def test_invalid_optional_state_cannot_escape(self):
        self.native.state.return_value = {"private": "detail"}
        result = self.sample()
        self.assertIs(result.state, ForegroundState.PARTIAL)
        self.assertIsNone(result._evidence)


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.native = fake_native()
        self.service = ComputerControlService(adapter=WindowsDesktopAdapter(native=self.native, platform="win32"))
        self.impl = ObserveForegroundWindowCapability(service=self.service)
        self.cap = self.impl.capability
        self.registry = CapabilityRegistry()
        self.registry.register(self.cap, self.impl)
        self.permissions = PermissionService(default_allowed=False)
        self.audit = AuditService()
        self.confirmation = ConfirmationService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions), self.confirmation,
                                       self.audit, self.undo)
        self.request = StructuredCapabilityRequest(self.impl.PHRASE, {})

    def run_action(self):
        return self.executor.execute_structured(self.cap, self.request)

    def test_metadata_and_protocols(self):
        self.assertEqual(self.cap.name, "observe_foreground_window")
        self.assertEqual(self.cap.service, "computer_control")
        self.assertIs(self.cap.execution_mode, ExecutionMode.LOCAL)
        self.assertFalse(self.cap.requires_llm)
        self.assertFalse(self.cap.requires_confirmation)
        self.assertFalse(self.cap.reversible)
        self.assertIsInstance(self.impl, StructuredCapability)
        self.assertIsInstance(self.impl, IntentArgumentMapper)
        self.assertIsInstance(self.impl, VerificationProvider)
        self.assertNotIsInstance(self.impl, UndoProvider)
        self.assertEqual(self.native.mock_calls, [])

    def test_discovery_without_native_reads(self):
        registry = CapabilityRegistry()
        with patch("nayeon.services.windows_desktop._WindowsNative", side_effect=AssertionError("native read")):
            CapabilityLoader(registry).discover()
        self.assertIsInstance(registry.get_implementation(self.cap.name), ObserveForegroundWindowCapability)

    def test_canonical_local_resolution_dispatch_bridge(self):
        self.permissions.grant(self.cap.name)
        resolution = LocalIntentInterpreter(router=TaskRouter(self.registry)).resolve(
            self.impl.PHRASE, context=IntentContext())
        self.assertEqual(resolution.intent, self.cap.name)
        plan = IntentDispatcher(registry=self.registry).plan(resolution)
        result = StructuredOrchestrationBridge(registry=self.registry, executor=self.executor).execute(
            plan, original_request=self.impl.PHRASE)
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.native.foreground.call_count, 2)

    def test_explicit_empty_args_authoritative(self):
        self.assertEqual(self.impl.map_intent_arguments({}, original_request="semantic wording"), {})

    def test_local_mapping_exact_binding_and_phrase(self):
        for original, args in (("inspect foreground window extra", {"request": "inspect foreground window extra"}),
                               (self.impl.PHRASE, {"request": "different"}),
                               ("observe foreground window", {"request": "observe foreground window"}),
                               (self.impl.PHRASE, {"request": self.impl.PHRASE, "pid": 1})):
            with self.subTest(original=original), self.assertRaises(ValueError):
                self.impl.map_intent_arguments(args, original_request=original)
        self.assertEqual(self.native.mock_calls, [])

    def test_private_extra_fields_rejected_without_reads(self):
        for key in ("hwnd", "pid", "tid", "title", "coordinates", "executable", "path", "_evidence", "extra"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.impl.validate_arguments({key: "private"})
            with self.assertRaises(ValueError):
                self.impl.map_intent_arguments({key: "private"}, original_request=self.impl.PHRASE)
        self.assertEqual(self.native.mock_calls, [])

    def test_invalid_mapping_type(self):
        for value in (None, [], "", 1):
            with self.subTest(value=value), self.assertRaises(TypeError):
                self.impl.validate_arguments(value)

    def test_legacy_execution_rejected_no_reads(self):
        with self.assertRaises(ValueError):
            self.impl.execute(self.impl.PHRASE)
        self.assertEqual(self.native.mock_calls, [])

    def test_default_denied_zero_native_reads(self):
        result = self.run_action()
        self.assertIs(result.status, ExecutionStatus.DENIED)
        self.assertEqual(self.native.mock_calls, [])

    def test_exact_permission_not_generic_group(self):
        self.permissions.grant("observe_desktop")
        self.assertIs(self.run_action().status, ExecutionStatus.DENIED)
        self.assertEqual(self.native.mock_calls, [])

    def test_explicit_permission_no_confirmation(self):
        self.permissions.grant(self.cap.name)
        result = self.run_action()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIsNone(result.confirmation_request)
        self.assertNotIn(AuditEventType.CONFIRMATION_CREATED, [event.event_type for event in self.audit.all()])

    def test_policy_blocked_zero_native_reads(self):
        self.permissions.grant(self.cap.name)
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions, {self.cap.name}),
                                       self.confirmation, self.audit, self.undo)
        self.assertIs(self.run_action().status, ExecutionStatus.DENIED)
        self.assertEqual(self.native.mock_calls, [])

    def test_invalid_structured_args_zero_native_reads(self):
        self.permissions.grant(self.cap.name)
        self.request = StructuredCapabilityRequest(self.impl.PHRASE, {"pid": 10})
        self.assertIs(self.run_action().status, ExecutionStatus.FAILED)
        self.assertEqual(self.native.mock_calls, [])

    def test_undo_history_unchanged(self):
        existing = self.undo.register(capability="fake", description="Fake", callback=lambda: None)
        self.permissions.grant(self.cap.name)
        self.run_action()
        self.assertEqual(self.undo.peek(), existing)
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, [event.event_type for event in self.audit.all()])

    def test_actual_audit_jsonl_redacted(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            self.audit = AuditService(path)
            self.executor = ActionExecutor(self.registry, PolicyService(self.permissions), self.confirmation,
                                           self.audit, self.undo)
            self.permissions.grant(self.cap.name)
            result = self.run_action()
            raw = path.read_text(encoding="utf-8")
            for secret in (str(IDENTITY.hwnd), str(IDENTITY.pid), str(IDENTITY.tid),
                           IDENTITY.executable, IDENTITY.window_class, "WinSta0", "Default"):
                self.assertNotIn(secret, raw)
                self.assertNotIn(secret, repr(result))
            events = [json.loads(line) for line in raw.splitlines()]
            self.assertIn("verification_outcome", [event["event_type"] for event in events])
            self.assertEqual(result.verification.evidence, {})

    def test_historical_verification_no_new_native_reads(self):
        output = self.service.observe_foreground_window()
        count = len(self.native.mock_calls)
        self.native.foreground.return_value = 999
        result = VerificationService().verify(self.impl, request=self.request, output=output)
        self.assertIs(result.status, VerificationStatus.VERIFIED)
        self.assertEqual(len(self.native.mock_calls), count)

    def test_incomplete_and_nonobserved_indeterminate(self):
        for output in (None, ForegroundObservation(ForegroundState.OBSERVED, ObservationReason.CONSISTENT),
                       ForegroundObservation(ForegroundState.PARTIAL, ObservationReason.INCOMPLETE),
                       ForegroundObservation(ForegroundState.NO_FOREGROUND, ObservationReason.NO_FOREGROUND),
                       ForegroundObservation(ForegroundState.UNAVAILABLE, ObservationReason.CONTEXT)):
            with self.subTest(output=output):
                self.assertIs(self.impl.verify_result(request=self.request, output=output).status,
                              VerificationStatus.INDETERMINATE)

    def test_trustworthy_contradiction_not_verified(self):
        evidence = replace(observed()._evidence, late=replace(IDENTITY, creation_time=IDENTITY.creation_time + 1))
        result = self.impl.verify_result(request=self.request, output=replace(observed(), _evidence=evidence))
        self.assertIs(result.status, VerificationStatus.NOT_VERIFIED)
        self.assertEqual(result.evidence, {})
        self.assertNotIn(str(IDENTITY.pid), result.reason)

    def test_invalid_evidence_indeterminate(self):
        evidence = replace(observed()._evidence, late=replace(IDENTITY, creation_time=0))
        result = self.impl.verify_result(request=self.request, output=replace(observed(), _evidence=evidence))
        self.assertIs(result.status, VerificationStatus.INDETERMINATE)


class NativeResourceTests(unittest.TestCase):
    """Mock ctypes entry points, including failure after owned allocation."""
    def setUp(self):
        self.api = _WindowsNative.__new__(_WindowsNative)
        self.api.u, self.api.k, self.api.w = Mock(), Mock(), Mock()
        self.api.k.OpenProcess.return_value = 101
        self.api.k.CloseHandle.return_value = True
        self.api.u.OpenInputDesktop.return_value = 202
        self.api.u.CloseDesktop.return_value = True
        self.api.k.GetCurrentProcessId.return_value = IDENTITY.pid
        self.api.k.GetCurrentThreadId.return_value = IDENTITY.tid
        self.api.u.GetThreadDesktop.return_value = 303
        self.api.u.GetProcessWindowStation.return_value = 404
        def session(pid, pointer):
            pointer._obj.value = 7
            return True
        self.api.k.ProcessIdToSessionId.side_effect = session
        def name(handle, index, buffer, size, needed):
            buffer.value = "WinSta0" if handle == 404 else "Default"
            needed._obj.value = (len(buffer.value) + 1) * ctypes.sizeof(ctypes.c_wchar)
            return True
        self.api.u.GetUserObjectInformationW.side_effect = name
        self.wts_value = ctypes.c_int(0)
        def wts(server, session, info, pointer, size):
            pointer._obj.value = ctypes.addressof(self.wts_value)
            size._obj.value = 4
            return True
        self.api.w.WTSQuerySessionInformationW.side_effect = wts
        def times(handle, creation, exit_time, kernel, user):
            creation._obj.dwLowDateTime = IDENTITY.creation_time
            return True
        self.api.k.GetProcessTimes.side_effect = times
        def image(handle, flags, buffer, size):
            buffer.value = IDENTITY.executable
            size._obj.value = len(buffer.value)
            return True
        self.api.k.QueryFullProcessImageNameW.side_effect = image
        def status(handle, pointer):
            pointer._obj.value = 259
            return True
        self.api.k.GetExitCodeProcess.side_effect = status

    def test_process_minimum_rights_exactly_once_close(self):
        self.assertEqual(self.api._process(IDENTITY.pid), (IDENTITY.creation_time, IDENTITY.executable))
        self.api.k.OpenProcess.assert_called_once_with(0x1000, False, IDENTITY.pid)
        self.api.k.CloseHandle.assert_called_once_with(101)

    def test_process_open_failure_never_closes_unowned(self):
        self.api.k.OpenProcess.return_value = 0
        with self.assertRaises(Exception):
            self.api._process(IDENTITY.pid)
        self.api.k.CloseHandle.assert_not_called()

    def test_all_process_read_exceptions_close_once(self):
        for name in ("GetProcessTimes", "QueryFullProcessImageNameW", "GetExitCodeProcess"):
            with self.subTest(name=name):
                self.setUp()
                getattr(self.api.k, name).side_effect = OSError("private")
                with self.assertRaises(Exception):
                    self.api._process(IDENTITY.pid)
                self.api.k.CloseHandle.assert_called_once_with(101)

    def test_malformed_process_fields_close_once(self):
        for name in ("GetProcessTimes", "QueryFullProcessImageNameW", "GetExitCodeProcess"):
            with self.subTest(name=name):
                self.setUp()
                getattr(self.api.k, name).side_effect = None
                getattr(self.api.k, name).return_value = False
                with self.assertRaises(Exception):
                    self.api._process(IDENTITY.pid)
                self.api.k.CloseHandle.assert_called_once_with(101)

    def test_context_owned_desktop_closed_borrowed_not_closed(self):
        self.assertEqual(self.api.context(), CONTEXT)
        self.api.u.CloseDesktop.assert_called_once_with(202)
        self.api.u.OpenInputDesktop.assert_called_once_with(0, False, 1)
        self.api.w.WTSFreeMemory.assert_called_once()
        self.api.k.CloseHandle.assert_not_called()

    def test_desktop_open_failure_no_close(self):
        self.api.u.OpenInputDesktop.return_value = 0
        with self.assertRaises(Exception):
            self.api.context()
        self.api.u.CloseDesktop.assert_not_called()

    def test_context_read_errors_close_once(self):
        for name in ("GetUserObjectInformationW", "GetThreadDesktop", "GetProcessWindowStation"):
            with self.subTest(name=name):
                self.setUp()
                getattr(self.api.u, name).side_effect = OSError("private")
                with self.assertRaises(Exception):
                    self.api.context()
                self.api.u.CloseDesktop.assert_called_once_with(202)

    def test_wts_allocated_then_failure_freed_once_and_desktop_closed(self):
        normal = self.api.w.WTSQuerySessionInformationW.side_effect
        def failure(*args):
            normal(*args)
            raise OSError("private")
        self.api.w.WTSQuerySessionInformationW.side_effect = failure
        with self.assertRaises(Exception):
            self.api.context()
        self.api.w.WTSFreeMemory.assert_called_once()
        self.api.u.CloseDesktop.assert_called_once_with(202)

    def test_wts_malformed_size_freed(self):
        normal = self.api.w.WTSQuerySessionInformationW.side_effect
        def malformed(*args):
            normal(*args)
            args[-1]._obj.value = 1
            return True
        self.api.w.WTSQuerySessionInformationW.side_effect = malformed
        with self.assertRaises(Exception):
            self.api.context()
        self.api.w.WTSFreeMemory.assert_called_once()
        self.api.u.CloseDesktop.assert_called_once_with(202)

    def test_wts_no_allocation_no_free(self):
        self.api.w.WTSQuerySessionInformationW.side_effect = None
        self.api.w.WTSQuerySessionInformationW.return_value = False
        with self.assertRaises(Exception):
            self.api.context()
        self.api.w.WTSFreeMemory.assert_not_called()
        self.api.u.CloseDesktop.assert_called_once_with(202)

    def test_close_failure_not_retried(self):
        self.api.k.CloseHandle.return_value = False
        with self.assertRaises(Exception):
            self.api._process(IDENTITY.pid)
        self.api.k.CloseHandle.assert_called_once_with(101)

    def test_optional_geometry_dpi_errors_not_fabricated(self):
        for name in ("GetWindowRect", "GetClientRect", "ClientToScreen", "MonitorFromWindow",
                     "GetDpiForWindow", "GetWindowDpiAwarenessContext", "GetThreadDpiAwarenessContext"):
            getattr(self.api.u, name).side_effect = OSError("private")
        result = self.api.state(IDENTITY.hwnd)
        for key in ("window_rect", "client_rect", "client_origin", "monitor", "dpi", "window_awareness", "observer_awareness"):
            self.assertIsNone(getattr(result, key))

    def test_no_title_or_mutation_entrypoints_in_source(self):
        source = Path("nayeon/services/windows_desktop.py").read_text(encoding="utf-8-sig")
        for name in ("GetWindowText", "GetWindowTextLength", "SetForegroundWindow", "AttachThreadInput",
                     "SendInput", "SetThreadDesktop", "SetProcessDpiAwareness", "sleep("):
            self.assertNotIn(name, source)

    def test_pointer_width_signatures_bound_without_native_calls(self):
        dlls = {name: Mock() for name in ("user32", "kernel32", "wtsapi32")}
        with patch("ctypes.WinDLL", side_effect=lambda name, **kw: dlls[name]):
            _WindowsNative()
        self.assertIs(dlls["user32"].GetForegroundWindow.restype, ctypes.wintypes.HWND)
        self.assertIs(dlls["kernel32"].OpenProcess.restype, ctypes.wintypes.HANDLE)
        self.assertIsNone(dlls["wtsapi32"].WTSFreeMemory.restype)
        for dll in dlls.values():
            self.assertEqual(dll.mock_calls, [])

    def configure_window(self):
        self.api.u.IsWindow.return_value = True
        def owner(hwnd, pid):
            pid._obj.value = IDENTITY.pid
            return IDENTITY.tid
        self.api.u.GetWindowThreadProcessId.side_effect = owner
        self.api.u.GetAncestor.return_value = IDENTITY.hwnd
        def window_class(hwnd, buffer, size):
            buffer.value = IDENTITY.window_class
            return len(buffer.value)
        self.api.u.GetClassNameW.side_effect = window_class

    def test_native_identity_no_owned_hwnd_or_desktop(self):
        self.configure_window()
        self.assertEqual(self.api.identity(IDENTITY.hwnd), IDENTITY)
        self.api.k.CloseHandle.assert_called_once_with(101)
        self.api.u.CloseDesktop.assert_not_called()

    def test_invalid_window_never_opens_process(self):
        self.configure_window()
        self.api.u.IsWindow.return_value = False
        with self.assertRaises(Exception):
            self.api.identity(IDENTITY.hwnd)
        self.api.k.OpenProcess.assert_not_called()
        self.api.k.CloseHandle.assert_not_called()

    def test_nonroot_candidate_rejected(self):
        self.configure_window()
        self.api.u.GetAncestor.return_value = 8
        with self.assertRaises(Exception):
            self.api.identity(IDENTITY.hwnd)
        self.api.k.OpenProcess.assert_not_called()

    def test_missing_class_after_process_read_closes_handle(self):
        self.configure_window()
        self.api.u.GetClassNameW.side_effect = None
        self.api.u.GetClassNameW.return_value = 0
        with self.assertRaises(Exception):
            self.api.identity(IDENTITY.hwnd)
        self.api.k.CloseHandle.assert_called_once_with(101)

    def test_process_restart_across_native_reads_partial_with_all_resources_closed(self):
        self.configure_window()
        self.api.u.GetForegroundWindow.return_value = IDENTITY.hwnd
        self.api.state = Mock(return_value=STATE)
        normal = self.api.k.GetProcessTimes.side_effect
        counter = 0
        def restart(*args):
            nonlocal counter
            normal(*args)
            args[1]._obj.dwLowDateTime += counter
            counter += 1
            return True
        self.api.k.GetProcessTimes.side_effect = restart
        result = WindowsDesktopAdapter(native=self.api, platform="win32").observe_foreground_window()
        self.assertIs(result.state, ForegroundState.PARTIAL)
        self.assertEqual(self.api.k.CloseHandle.call_count, 2)
        self.assertEqual(self.api.u.CloseDesktop.call_count, 2)
        self.assertEqual(self.api.w.WTSFreeMemory.call_count, 2)

    def test_native_stable_snapshot_no_live_handle_in_result(self):
        self.configure_window()
        self.api.u.GetForegroundWindow.return_value = IDENTITY.hwnd
        self.api.state = Mock(return_value=STATE)
        result = WindowsDesktopAdapter(native=self.api, platform="win32").observe_foreground_window()
        self.assertIs(result.state, ForegroundState.OBSERVED)
        self.assertEqual(self.api.k.CloseHandle.call_count, 2)
        self.assertEqual(self.api.u.CloseDesktop.call_count, 2)
        self.assertEqual(self.api.w.WTSFreeMemory.call_count, 2)
        self.assertNotIn("101", repr(result))
        self.assertEqual(result._evidence.early.hwnd, IDENTITY.hwnd)
