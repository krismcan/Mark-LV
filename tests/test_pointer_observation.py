"""Deterministic Phase 6.4 bounded pointer observation tests; no live pointer mutation."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from tempfile import TemporaryDirectory
import ctypes
import json
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities.loader import CapabilityLoader
from nayeon.capabilities.observe_pointer import ObservePointerCapability
from nayeon.capabilities.structured import IntentArgumentMapper, StructuredCapability, StructuredCapabilityRequest
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry, ExecutionMode
from nayeon.services.pointer_observation import (
    PointerObservation, PointerObservationService, PointerReason, PointerState,
    _PointerEvidence, _PointerSample, _point_valid,
)
from nayeon.services.windows_pointer import WindowsPointerAdapter, _PointerNative, _handle
from nayeon.undo.contract import UndoProvider
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationProvider, VerificationStatus
from nayeon.verification.service import VerificationService
from tests import test_foreground_observation as fixtures

CONTEXT = fixtures.CONTEXT
IDENTITY = fixtures.IDENTITY
POINT = (31415, 27182)
CHILD = IDENTITY.hwnd + 111


def pointer_sample(*, point=POINT, window=CHILD, root=IDENTITY.hwnd,
                   foreground_root=IDENTITY.hwnd, identity=IDENTITY,
                   foreground_identity=IDENTITY):
    return _PointerSample(point, window, root, foreground_root, identity, foreground_identity)


def observed():
    sample = pointer_sample()
    return PointerObservation(
        PointerState.OBSERVED, PointerReason.CONSISTENT,
        _PointerEvidence(sample, sample, CONTEXT, CONTEXT, 10, 20),
    )


def fake_native():
    native = Mock()
    native.context.return_value = CONTEXT
    native.cursor.return_value = POINT
    native.window_at.return_value = CHILD
    native.root.return_value = IDENTITY.hwnd
    native.foreground.return_value = IDENTITY.hwnd
    native.identity.return_value = IDENTITY
    return native


class PointerSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.native = fake_native()
        self.adapter = WindowsPointerAdapter(
            native=self.native, platform="win32", clock=Mock(side_effect=[10, 20])
        )

    def sample(self):
        return self.adapter.observe_pointer()

    def test_stable_snapshot(self):
        result = self.sample()
        self.assertEqual(result, observed())
        self.assertTrue(result._evidence.consistent())

    def test_fixed_read_only_acquisition_order(self):
        self.sample()
        self.assertEqual(
            [call[0] for call in self.native.mock_calls],
            ["context",
             "cursor", "window_at", "root", "foreground", "root", "identity", "identity",
             "window_at", "root", "foreground", "root", "identity", "identity", "cursor",
             "context"],
        )

    def test_no_target_is_bounded_without_identity(self):
        self.native.window_at.return_value = 0
        result = self.sample()
        self.assertIs(result.state, PointerState.NO_TARGET)
        self.assertIs(result.reason, PointerReason.NO_TARGET)
        self.assertIsNone(result._evidence)
        self.assertEqual(self.native.identity.call_count, 2)  # Foreground root only.
        self.assertIs(result._evidence, None)

    def test_no_foreground_does_not_invalidate_pointer_target(self):
        self.native.foreground.return_value = 0
        result = self.sample()
        self.assertIs(result.state, PointerState.OBSERVED)
        self.assertEqual(result._evidence.early.foreground_root, 0)
        self.assertIsNone(result._evidence.early.foreground_identity)

    def test_cursor_transition_fails_closed(self):
        self.native.cursor.side_effect = [POINT, (POINT[0] + 1, POINT[1])]
        result = self.sample()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertIs(result.reason, PointerReason.CHANGED)
        self.assertIsNone(result._evidence)

    def test_window_transition_fails_closed(self):
        self.native.window_at.side_effect = [CHILD, CHILD + 1]
        result = self.sample()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertIs(result.reason, PointerReason.CHANGED)

    def test_root_transition_fails_closed(self):
        other = replace(IDENTITY, hwnd=IDENTITY.hwnd + 1, root=IDENTITY.root + 1)
        self.native.root.side_effect = [
            IDENTITY.hwnd, IDENTITY.hwnd,
            other.hwnd, IDENTITY.hwnd,
        ]
        self.native.identity.side_effect = [IDENTITY, IDENTITY, other, IDENTITY]
        result = self.sample()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertIs(result.reason, PointerReason.CHANGED)

    def test_recycled_window_identity_fails_closed(self):
        restarted = replace(IDENTITY, creation_time=IDENTITY.creation_time + 1)
        self.native.identity.side_effect = [IDENTITY, IDENTITY, restarted, restarted]
        result = self.sample()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertIs(result.reason, PointerReason.CHANGED)

    def test_foreground_identity_drift_fails_closed(self):
        foreground = replace(IDENTITY, hwnd=IDENTITY.hwnd + 9, root=IDENTITY.root + 9)
        for field, value in (("pid", foreground.pid + 1), ("tid", foreground.tid + 1),
                             ("creation_time", foreground.creation_time + 1),
                             ("executable", "private-replacement"), ("window_class", "Other")):
            with self.subTest(field=field):
                self.setUp()
                self.native.root.side_effect = [IDENTITY.hwnd, foreground.hwnd] * 2
                self.native.identity.side_effect = [IDENTITY, foreground, IDENTITY,
                                                    replace(foreground, **{field: value})]
                result = self.sample()
                self.assertIs(result.state, PointerState.PARTIAL)
                self.assertIs(result.reason, PointerReason.CHANGED)
                self.assertIsNone(result._evidence)

    def test_same_root_conflicting_identities_are_incomplete(self):
        other = replace(IDENTITY, creation_time=IDENTITY.creation_time + 1)
        self.native.identity.side_effect = [IDENTITY, other, IDENTITY, other]
        result = self.sample()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertIs(result.reason, PointerReason.INCOMPLETE)

    def test_invalid_identity_fields_fail_closed_for_both_roots(self):
        changes = ({"hwnd": IDENTITY.hwnd + 1}, {"root": IDENTITY.root + 1},
                   {"pid": 0}, {"tid": 0}, {"creation_time": 0}, {"executable": ""},
                   {"window_class": ""}, {"session": 0}, {"desktop": "Other"})
        for fields in changes:
            for index in (0, 1, 2, 3):
                with self.subTest(fields=fields, index=index):
                    self.setUp()
                    identities = [IDENTITY] * 4
                    identities[index] = replace(IDENTITY, **fields)
                    self.native.identity.side_effect = identities
                    result = self.sample()
                    self.assertIs(result.state, PointerState.PARTIAL)
                    self.assertIsNone(result._evidence)

    def test_no_target_drift_cannot_become_no_target(self):
        for method, values in (("cursor", [POINT, (0, 0)]),
                               ("window_at", [0, CHILD]),
                               ("foreground", [IDENTITY.hwnd, 0]),
                               ("context", [CONTEXT, replace(CONTEXT, active=False)])):
            with self.subTest(method=method):
                self.setUp()
                self.native.window_at.return_value = 0
                getattr(self.native, method).side_effect = values
                result = self.sample()
                self.assertIs(result.state, PointerState.PARTIAL)
                self.assertIsNone(result._evidence)

    def test_null_target_and_foreground_needs_no_identity(self):
        self.native.window_at.return_value = 0
        self.native.foreground.return_value = 0
        self.assertIs(self.sample().state, PointerState.NO_TARGET)
        self.native.identity.assert_not_called()

    def test_malformed_clock_evidence_fails_closed(self):
        for values in ((20, 10), (-1, 20), (True, 20), (10, "private")):
            with self.subTest(values=values):
                self.setUp()
                self.adapter._clock = Mock(side_effect=values)
                self.assertIs(self.sample().state, PointerState.PARTIAL)

    def test_identity_field_drift_fails_closed(self):
        changes = (
            {"pid": IDENTITY.pid + 1},
            {"tid": IDENTITY.tid + 1},
            {"creation_time": IDENTITY.creation_time + 1},
            {"executable": r"C:\private\replacement.exe"},
            {"window_class": "ReplacementClass"},
        )
        for fields in changes:
            with self.subTest(fields=fields):
                self.setUp()
                changed = replace(IDENTITY, **fields)
                self.native.identity.side_effect = [IDENTITY, IDENTITY, changed, changed]
                result = self.sample()
                self.assertIs(result.state, PointerState.PARTIAL)
                self.assertIs(result.reason, PointerReason.CHANGED)

    def test_context_field_drift_fails_closed(self):
        changes = (
            {"session": CONTEXT.session + 1},
            {"input_desktop": "Other"},
            {"thread_desktop": "Other"},
            {"station": "Other"},
            {"active": False},
        )
        for fields in changes:
            with self.subTest(fields=fields):
                self.setUp()
                late_context = replace(CONTEXT, **fields)
                self.native.context.side_effect = [CONTEXT, late_context]
                result = self.sample()
                self.assertIs(result.state, PointerState.PARTIAL)
                self.assertIsNone(result._evidence)

    def test_foreground_relationship_transition_fails_closed(self):
        self.native.root.side_effect = [
            IDENTITY.hwnd, IDENTITY.hwnd,
            IDENTITY.hwnd, IDENTITY.hwnd + 1,
        ]
        self.native.identity.side_effect = [IDENTITY, IDENTITY, IDENTITY,
            replace(IDENTITY, hwnd=IDENTITY.hwnd + 1, root=IDENTITY.root + 1)]
        result = self.sample()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertIs(result.reason, PointerReason.CHANGED)

    def test_context_transition_fails_closed(self):
        late_context = replace(CONTEXT, session=8)
        late_identity = replace(IDENTITY, session=8)
        self.native.context.side_effect = [CONTEXT, late_context]
        self.native.identity.side_effect = [IDENTITY, IDENTITY, late_identity, late_identity]
        result = self.sample()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertIs(result.reason, PointerReason.CHANGED)

    def test_invalid_initial_context_zero_pointer_reads(self):
        for context in (None, replace(CONTEXT, session=0), replace(CONTEXT, active=False),
                        replace(CONTEXT, input_desktop="Winlogon"),
                        replace(CONTEXT, thread_desktop="Other"), replace(CONTEXT, station="Other")):
            with self.subTest(context=context):
                native = fake_native()
                native.context.return_value = context
                result = WindowsPointerAdapter(native=native, platform="win32").observe_pointer()
                self.assertIs(result.state, PointerState.UNAVAILABLE)
                native.cursor.assert_not_called()

    def test_late_context_error_is_partial(self):
        self.native.context.side_effect = [CONTEXT, OSError("private native error")]
        result = self.sample()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertNotIn("private native error", repr(result))

    def test_malformed_native_values_fail_closed(self):
        cases = (
            ("cursor", None), ("cursor", (True, 2)), ("cursor", (2 ** 31, 0)),
            ("window_at", True), ("window_at", -1), ("root", 0), ("identity", {}),
            ("foreground", True), ("foreground", -1), ("foreground", None),
            ("foreground", 2 ** (ctypes.sizeof(ctypes.c_void_p) * 8)),
        )
        for method, value in cases:
            with self.subTest(method=method, value=value):
                self.setUp()
                getattr(self.native, method).return_value = value
                result = self.sample()
                self.assertIs(result.state, PointerState.PARTIAL)
                self.assertIsNone(result._evidence)

    def test_native_exceptions_are_sanitized(self):
        for method in ("cursor", "window_at", "root", "foreground", "identity"):
            with self.subTest(method=method):
                self.setUp()
                getattr(self.native, method).side_effect = OSError("secret native text")
                result = self.sample()
                self.assertIs(result.state, PointerState.PARTIAL)
                self.assertNotIn("secret native text", repr(result))

    def test_unsupported_platform_zero_calls(self):
        result = WindowsPointerAdapter(native=self.native, platform="linux").observe_pointer()
        self.assertIs(result.state, PointerState.UNAVAILABLE)
        self.assertEqual(self.native.mock_calls, [])

    def test_private_evidence_is_frozen_and_redacted(self):
        value = observed()
        self.assertEqual(deepcopy(value), value)
        for obj, key in ((value._evidence, "early"), (value._evidence.early, "point")):
            self.assertFalse(hasattr(obj, "__dict__"))
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, key, None)
        for obj in (value, value._evidence, value._evidence.early,
                    value._evidence.early.identity, value._evidence.context):
            text = repr(obj) + str(obj)
            for secret in (str(POINT[0]), str(POINT[1]), str(IDENTITY.hwnd),
                           str(IDENTITY.pid), IDENTITY.executable, IDENTITY.window_class,
                           "WinSta0", "Default"):
                self.assertNotIn(secret, text)

    def test_typed_public_contract(self):
        with self.assertRaises(TypeError):
            PointerObservation("observed", PointerReason.CONSISTENT)
        with self.assertRaises(TypeError):
            PointerObservation(PointerState.OBSERVED, "raw")
        with self.assertRaises(TypeError):
            _PointerSample([1, 2], 1, 1, 1, IDENTITY, IDENTITY)

    def test_point_and_handle_bounds(self):
        self.assertTrue(_point_valid((-(2 ** 31), 2 ** 31 - 1)))
        for value in (None, [1, 2], (True, 1), (2 ** 31, 0), (0, -(2 ** 31) - 1)):
            self.assertFalse(_point_valid(value))
        for value in (True, -1, 1.0, None, 2 ** (ctypes.sizeof(ctypes.c_void_p) * 8)):
            with self.assertRaises(ValueError):
                _handle(value)

    def test_service_exception_and_invalid_result_sanitized(self):
        adapter = Mock()
        adapter.observe_pointer.side_effect = OSError("private")
        result = PointerObservationService(adapter=adapter).observe_pointer()
        self.assertIs(result.state, PointerState.UNAVAILABLE)
        self.assertNotIn("private", repr(result))
        adapter.observe_pointer.side_effect = None
        adapter.observe_pointer.return_value = {"coordinates": POINT}
        self.assertIs(PointerObservationService(adapter=adapter).observe_pointer().state,
                      PointerState.UNAVAILABLE)


class PointerCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.native = fake_native()
        self.service = PointerObservationService(
            adapter=WindowsPointerAdapter(native=self.native, platform="win32",
                                          clock=Mock(side_effect=[10, 20]))
        )
        self.impl = ObservePointerCapability(service=self.service)
        self.cap = self.impl.capability
        self.registry = CapabilityRegistry()
        self.registry.register(self.cap, self.impl)
        self.permissions = PermissionService(default_allowed=False)
        self.audit = AuditService()
        self.confirmation = ConfirmationService()
        self.undo = UndoService()
        self.executor = ActionExecutor(
            self.registry, PolicyService(self.permissions), self.confirmation, self.audit, self.undo
        )
        self.request = StructuredCapabilityRequest(self.impl.PHRASE, {})

    def run_action(self):
        return self.executor.execute_structured(self.cap, self.request)

    def session(self):
        return ConversationSession(
            resolver=IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry))),
            registry=self.registry, executor=self.executor,
        )

    def test_metadata_and_protocols(self):
        self.assertEqual(self.cap.name, "observe_pointer")
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

    def test_discovery_and_validation_do_no_native_io(self):
        registry = CapabilityRegistry()
        with patch("nayeon.services.windows_pointer._PointerNative",
                   side_effect=AssertionError("native read")):
            CapabilityLoader(registry).discover()
        self.assertIsInstance(registry.get_implementation(self.cap.name), ObservePointerCapability)
        self.assertEqual(self.impl.validate_arguments({}), {})
        self.assertEqual(self.native.mock_calls, [])

    def test_exact_phrase_and_empty_arguments_only(self):
        self.assertEqual(self.impl.map_intent_arguments({}, original_request="semantic wording"), {})
        self.assertEqual(
            self.impl.map_intent_arguments({"request": self.impl.PHRASE},
                                           original_request=self.impl.PHRASE), {}
        )
        invalid = (
            ("inspect current pointer extra", {"request": "inspect current pointer extra"}),
            ("inspect pointer", {"request": "inspect pointer"}),
            (self.impl.PHRASE, {"request": "different"}),
            (self.impl.PHRASE, {"request": self.impl.PHRASE, "x": 1}),
        )
        for original, args in invalid:
            with self.subTest(original=original), self.assertRaises(ValueError):
                self.impl.map_intent_arguments(args, original_request=original)
        self.assertEqual(self.native.mock_calls, [])

    def test_private_and_native_arguments_rejected_without_reads(self):
        for key in ("x", "y", "coordinates", "hwnd", "pid", "tid", "identity", "context",
                    "_evidence", "title", "path", "window_class", "foreground",
                    "_binding", "private_bindings", "target", "request"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.impl.validate_arguments({key: "private"})
        for value in (None, [], "", 1):
            with self.subTest(value=value), self.assertRaises(TypeError):
                self.impl.validate_arguments(value)
        self.assertEqual(self.native.mock_calls, [])

    def test_legacy_execution_rejected_without_reads(self):
        with self.assertRaises(ValueError):
            self.impl.execute(self.impl.PHRASE)
        self.assertEqual(self.native.mock_calls, [])

    def test_default_denied_zero_reads(self):
        self.assertIs(self.run_action().status, ExecutionStatus.DENIED)
        self.assertEqual(self.native.mock_calls, [])

    def test_exact_permission_required(self):
        self.permissions.grant("computer_control")
        self.assertIs(self.run_action().status, ExecutionStatus.DENIED)
        self.assertEqual(self.native.mock_calls, [])
        self.permissions.grant(self.cap.name)
        result = self.run_action()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIsNone(result.confirmation_request)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)

    def test_policy_blocked_zero_reads(self):
        self.permissions.grant(self.cap.name)
        self.executor = ActionExecutor(
            self.registry, PolicyService(self.permissions, {self.cap.name}),
            self.confirmation, self.audit, self.undo,
        )
        self.assertIs(self.run_action().status, ExecutionStatus.DENIED)
        self.assertEqual(self.native.mock_calls, [])

    def test_invalid_structured_args_zero_reads(self):
        self.permissions.grant(self.cap.name)
        self.request = StructuredCapabilityRequest(self.impl.PHRASE, {"x": POINT[0]})
        self.assertIs(self.run_action().status, ExecutionStatus.FAILED)
        self.assertEqual(self.native.mock_calls, [])

    def test_conversation_session_real_stack(self):
        self.permissions.grant(self.cap.name)
        result = self.session().request(self.impl.PHRASE)
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.native.cursor.call_count, 2)
        self.assertEqual(self.native.window_at.call_count, 2)

    def test_undo_history_unchanged(self):
        existing = self.undo.register(capability="fixture", description="fixture", callback=lambda: None)
        self.permissions.grant(self.cap.name)
        self.run_action()
        self.assertEqual(self.undo.peek(), existing)
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, [e.event_type for e in self.audit.all()])

    def test_audit_and_public_result_do_not_disclose_private_evidence(self):
        foreground = replace(IDENTITY, hwnd=7654321, root=7654321, pid=7654322,
                             tid=7654323, executable="private-foreground.exe",
                             window_class="PrivateForegroundClass")
        self.native.root.side_effect = [IDENTITY.hwnd, foreground.hwnd] * 2
        self.native.identity.side_effect = [IDENTITY, foreground] * 2
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            self.audit = AuditService(path)
            self.executor = ActionExecutor(
                self.registry, PolicyService(self.permissions), self.confirmation, self.audit, self.undo
            )
            self.permissions.grant(self.cap.name)
            result = self.run_action()
            raw = path.read_text(encoding="utf-8")
            public = raw + repr(result)
            for secret in (str(POINT[0]), str(POINT[1]), str(IDENTITY.hwnd), str(IDENTITY.pid),
                           IDENTITY.executable, IDENTITY.window_class, "WinSta0", "Default",
                           str(foreground.hwnd), str(foreground.pid), str(foreground.tid),
                           foreground.executable, foreground.window_class):
                self.assertNotIn(secret, public)
            events = [json.loads(line) for line in raw.splitlines()]
            self.assertIn("verification_outcome", [e["event_type"] for e in events])
            self.assertEqual(result.verification.evidence, {})

    def test_historical_verification_does_not_resample(self):
        output = self.service.observe_pointer()
        count = len(self.native.mock_calls)
        self.native.cursor.return_value = (0, 0)
        result = VerificationService().verify(self.impl, request=self.request, output=output)
        self.assertIs(result.status, VerificationStatus.VERIFIED)
        self.assertEqual(len(self.native.mock_calls), count)

    def test_nonobserved_results_are_indeterminate(self):
        for output in (
            None,
            PointerObservation(PointerState.OBSERVED, PointerReason.CONSISTENT),
            PointerObservation(PointerState.NO_TARGET, PointerReason.NO_TARGET),
            PointerObservation(PointerState.PARTIAL, PointerReason.INCOMPLETE),
            PointerObservation(PointerState.UNAVAILABLE, PointerReason.CONTEXT),
        ):
            with self.subTest(output=output):
                result = self.impl.verify_result(request=self.request, output=output)
                self.assertIs(result.status, VerificationStatus.INDETERMINATE)

    def test_trustworthy_contradiction_is_not_verified(self):
        evidence = observed()._evidence
        changed = replace(evidence, late=replace(evidence.late, point=(POINT[0] + 1, POINT[1])))
        result = self.impl.verify_result(
            request=self.request, output=replace(observed(), _evidence=changed)
        )
        self.assertIs(result.status, VerificationStatus.NOT_VERIFIED)
        self.assertEqual(result.evidence, {})

    def test_invalid_evidence_is_indeterminate(self):
        evidence = observed()._evidence
        invalid_identity = replace(IDENTITY, creation_time=0)
        invalid = replace(evidence, late=replace(evidence.late, identity=invalid_identity))
        result = self.impl.verify_result(
            request=self.request, output=replace(observed(), _evidence=invalid)
        )
        self.assertIs(result.status, VerificationStatus.INDETERMINATE)

    def test_negative_receipts_with_positive_evidence_never_upgrade(self):
        evidence = observed()._evidence
        count = len(self.native.mock_calls)
        for state in (PointerState.NO_TARGET, PointerState.PARTIAL, PointerState.UNAVAILABLE):
            with self.subTest(state=state):
                output = PointerObservation(state, PointerReason.CONSISTENT, evidence)
                result = self.impl.verify_result(request=self.request, output=output)
                self.assertIs(result.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(len(self.native.mock_calls), count)

    def test_negative_reason_cannot_verify_observed_claim(self):
        output = replace(observed(), reason=PointerReason.INCOMPLETE)
        result = self.impl.verify_result(request=self.request, output=output)
        self.assertIs(result.status, VerificationStatus.INDETERMINATE)

    def test_invalid_verification_request_does_no_io(self):
        for request in (None, self.impl.PHRASE,
                        StructuredCapabilityRequest(self.impl.PHRASE, {"_evidence": observed()._evidence})):
            with self.subTest(request=request):
                self.assertIs(self.impl.verify_result(request=request, output=observed()).status,
                              VerificationStatus.INDETERMINATE)
        self.assertEqual(self.native.mock_calls, [])


class PointerNativeTests(unittest.TestCase):
    def test_win32_signatures_bound_without_calls(self):
        dlls = {name: Mock() for name in ("user32", "kernel32", "wtsapi32")}
        with patch("ctypes.WinDLL", side_effect=lambda name, **kw: dlls[name]):
            _PointerNative()
        self.assertEqual(dlls["user32"].GetCursorPos.argtypes,
                         [ctypes.POINTER(ctypes.wintypes.POINT)])
        self.assertIs(dlls["user32"].GetCursorPos.restype, ctypes.wintypes.BOOL)
        self.assertEqual(dlls["user32"].WindowFromPoint.argtypes, [ctypes.wintypes.POINT])
        self.assertIs(dlls["user32"].WindowFromPoint.restype, ctypes.wintypes.HWND)
        for dll in dlls.values():
            self.assertEqual(dll.mock_calls, [])

    def test_native_pointer_helpers_are_query_only(self):
        api = _PointerNative.__new__(_PointerNative)
        api.u = Mock()
        def cursor(pointer):
            pointer._obj.x, pointer._obj.y = POINT
            return True
        api.u.GetCursorPos.side_effect = cursor
        api.u.WindowFromPoint.return_value = CHILD
        api.u.GetAncestor.return_value = IDENTITY.hwnd
        self.assertEqual(api.cursor(), POINT)
        self.assertEqual(api.window_at(POINT), CHILD)
        self.assertEqual(api.root(CHILD), IDENTITY.hwnd)

    def test_exact_native_positive_cardinality(self):
        fixture = fixtures.NativeResourceTests()
        fixture.setUp()
        fixture.configure_window()
        api = _PointerNative.__new__(_PointerNative)
        api.u, api.k, api.w = fixture.api.u, fixture.api.k, fixture.api.w
        def cursor(pointer):
            pointer._obj.x, pointer._obj.y = POINT
            return True
        api.u.GetCursorPos.side_effect = cursor
        api.u.WindowFromPoint.return_value = CHILD
        api.u.GetForegroundWindow.return_value = IDENTITY.hwnd
        result = WindowsPointerAdapter(native=api, platform="win32",
                                       clock=Mock(side_effect=[10, 20])).observe_pointer()
        self.assertIs(result.state, PointerState.OBSERVED)
        for name, count in (("GetCursorPos", 2), ("WindowFromPoint", 2),
                            ("GetForegroundWindow", 2), ("GetAncestor", 8),
                            ("IsWindow", 4), ("GetWindowThreadProcessId", 4),
                            ("GetClassNameW", 4), ("OpenInputDesktop", 2),
                            ("CloseDesktop", 2)):
            with self.subTest(name=name):
                self.assertEqual(getattr(api.u, name).call_count, count)
        self.assertEqual(api.k.OpenProcess.call_count, 4)
        self.assertEqual(api.k.CloseHandle.call_count, 4)
        self.assertEqual(api.k.ProcessIdToSessionId.call_count, 6)
        for call in api.u.WindowFromPoint.call_args_list:
            self.assertEqual((call.args[0].x, call.args[0].y), POINT)
        for call in api.u.GetAncestor.call_args_list:
            self.assertEqual(call.args[1], 2)
        api.u.GetWindowRect.assert_not_called()
        api.u.GetClientRect.assert_not_called()
        api.u.ClientToScreen.assert_not_called()

    def test_native_pointer_failures_do_not_retry(self):
        api = _PointerNative.__new__(_PointerNative)
        api.u = Mock()
        api.u.GetCursorPos.return_value = False
        with self.assertRaises(Exception):
            api.cursor()
        api.u.GetCursorPos.assert_called_once()
        api.u.GetAncestor.return_value = 0
        with self.assertRaises(Exception):
            api.root(CHILD)
        api.u.GetAncestor.assert_called_once_with(CHILD, 2)

    def _resource_adapter(self):
        fixture = fixtures.NativeResourceTests()
        fixture.setUp()
        fixture.configure_window()
        api = fixture.api
        api.cursor = Mock(return_value=POINT)
        api.window_at = Mock(return_value=CHILD)
        api.root = Mock(return_value=IDENTITY.hwnd)
        api.foreground = Mock(return_value=IDENTITY.hwnd)
        adapter = WindowsPointerAdapter(
            native=api, platform="win32", clock=Mock(side_effect=[10, 20])
        )
        return fixture, api, adapter

    def test_owned_resources_balance_and_hwnds_remain_borrowed(self):
        fixture, api, adapter = self._resource_adapter()
        result = adapter.observe_pointer()
        self.assertIs(result.state, PointerState.OBSERVED)
        self.assertEqual(api.k.OpenProcess.call_count, 4)
        self.assertEqual(api.k.CloseHandle.call_count, 4)
        self.assertEqual(api.u.OpenInputDesktop.call_count, 2)
        self.assertEqual(api.u.CloseDesktop.call_count, 2)
        self.assertEqual(api.w.WTSQuerySessionInformationW.call_count, 2)
        self.assertEqual(api.w.WTSFreeMemory.call_count, 2)
        for call in api.k.CloseHandle.call_args_list:
            self.assertEqual(call.args, (101,))
        for call in api.u.CloseDesktop.call_args_list:
            self.assertEqual(call.args, (202,))

    def test_process_cleanup_failure_prevents_observed(self):
        fixture, api, adapter = self._resource_adapter()
        api.k.CloseHandle.return_value = False
        result = adapter.observe_pointer()
        self.assertIs(result.state, PointerState.PARTIAL)
        self.assertEqual(api.k.CloseHandle.call_count, 1)

    def test_late_process_cleanup_failure_prevents_observed(self):
        fixture, api, adapter = self._resource_adapter()
        api.k.CloseHandle.side_effect = [True, True, True, False]
        self.assertIs(adapter.observe_pointer().state, PointerState.PARTIAL)
        self.assertEqual(api.k.CloseHandle.call_count, 4)

    def test_late_desktop_cleanup_failure_prevents_observed(self):
        fixture, api, adapter = self._resource_adapter()
        api.u.CloseDesktop.side_effect = [True, False]
        self.assertIs(adapter.observe_pointer().state, PointerState.PARTIAL)
        self.assertEqual(api.u.CloseDesktop.call_count, 2)

    def test_desktop_cleanup_failure_prevents_sampling(self):
        fixture, api, adapter = self._resource_adapter()
        api.u.CloseDesktop.return_value = False
        result = adapter.observe_pointer()
        self.assertIs(result.state, PointerState.UNAVAILABLE)
        api.cursor.assert_not_called()

    def test_wts_cleanup_failure_prevents_sampling(self):
        fixture, api, adapter = self._resource_adapter()
        api.w.WTSFreeMemory.side_effect = OSError("private")
        result = adapter.observe_pointer()
        self.assertIs(result.state, PointerState.UNAVAILABLE)
        api.cursor.assert_not_called()
        self.assertEqual(api.u.CloseDesktop.call_count, 1)

    def test_source_contains_no_pointer_mutation_or_content_reads(self):
        source = (
            Path("nayeon/services/windows_pointer.py").read_text(encoding="utf-8-sig")
            + Path("nayeon/services/pointer_observation.py").read_text(encoding="utf-8-sig")
            + Path("nayeon/capabilities/observe_pointer.py").read_text(encoding="utf-8-sig")
            + Path("nayeon/services/windows_desktop.py").read_text(encoding="utf-8-sig")
        )
        for forbidden in (
            "SetCursorPos", "SendInput", "mouse_event", "SetForegroundWindow",
            "AttachThreadInput", "GetWindowText", "GetWindowTextLength",
            "pyautogui", "UIAutomation", "screenshot", "OCR",
            "OpenClipboard", "SetClipboardData", "GetClipboardData", "playwright",
            "selenium", "SetThreadDesktop", "SetProcessWindowStation",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
