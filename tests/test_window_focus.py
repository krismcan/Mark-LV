"""Deterministic Phase 6.2 authority and native checks."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import ctypes
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.session import ConversationSession
from nayeon.agent.router import TaskRouter
from nayeon.audit.service import AuditService, AuditEventType
from nayeon.capabilities.focus_window import FocusWindowCapability
from nayeon.capabilities.loader import CapabilityLoader
from nayeon.capabilities.structured import StructuredCapabilityRequest, PreparedApprovalValidator
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry, ExecutionMode
from nayeon.services.window_focus import FocusState, WindowFocusService, _FocusBinding
from nayeon.services.windows_focus import WindowsFocusAdapter, _FocusNative
from nayeon.undo.service import UndoService
from nayeon.undo.contract import UndoProvider
from nayeon.verification.contract import VerificationStatus
from tests import test_foreground_observation as fixtures

CONTEXT, IDENTITY = fixtures.CONTEXT, fixtures.IDENTITY


class FocusTests(unittest.TestCase):
    def setUp(self):
        self.native = fixtures.fake_native()
        self.native.focus.return_value = True
        self.adapter = WindowsFocusAdapter(native=self.native, platform="win32")
        self.service = WindowFocusService(adapter=self.adapter)
        self.impl = FocusWindowCapability(service=self.service)
        self.cap = self.impl.capability
        self.registry = CapabilityRegistry()
        self.registry.register(self.cap, self.impl)
        self.permissions = PermissionService(default_allowed=False)
        self.confirmation = ConfirmationService()
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions),
                                      self.confirmation, self.audit, self.undo)
        self.request = StructuredCapabilityRequest(self.impl.PHRASE, {})

    def pending(self):
        self.permissions.grant(self.cap.name)
        result = self.executor.execute_structured(self.cap, self.request)
        self.assertIs(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.native.focus.assert_not_called()
        return result.confirmation_request.token

    def approve(self, token):
        return self.executor.approve_and_execute_structured(token, capability=self.cap, request=self.request)

    def test_metadata_discovery_no_native_calls(self):
        self.assertIs(self.cap.execution_mode, ExecutionMode.LOCAL)
        self.assertTrue(self.cap.requires_confirmation)
        self.assertFalse(self.cap.requires_llm)
        self.assertFalse(self.cap.reversible)
        self.assertNotIsInstance(self.impl, UndoProvider)
        self.assertIsInstance(self.impl, PreparedApprovalValidator)
        with patch("nayeon.services.windows_focus._FocusNative", side_effect=AssertionError()):
            registry = CapabilityRegistry()
            CapabilityLoader(registry).discover()
        self.assertIsInstance(registry.get_implementation(self.cap.name), FocusWindowCapability)
        self.assertEqual(self.native.mock_calls, [])

    def test_default_deny_zero_mutations(self):
        result = self.executor.execute_structured(self.cap, self.request)
        self.assertIs(result.status, ExecutionStatus.DENIED)
        self.native.focus.assert_not_called()

    def test_permission_alone_only_prepares(self):
        self.pending()
        self.assertEqual(self.native.foreground.call_count, 2)
        self.native.focus.assert_not_called()

    def test_approved_single_attempt_verified(self):
        result = self.approve(self.pending())
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.output.state, FocusState.FOCUSED)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)
        self.native.focus.assert_called_once_with(IDENTITY.hwnd)

    def test_foreground_changes_during_confirmation_saved_target_used(self):
        token = self.pending()
        self.native.foreground.return_value = IDENTITY.hwnd + 1
        def focus(hwnd):
            self.assertEqual(hwnd, IDENTITY.hwnd)
            self.native.foreground.return_value = hwnd
            return True
        self.native.focus.side_effect = focus
        self.assertIs(self.approve(token).verification.status, VerificationStatus.VERIFIED)
        self.native.focus.assert_called_once_with(IDENTITY.hwnd)
        self.assertEqual(self.native.foreground.call_count, 4)

    def test_rejection_replay_zero_attempts(self):
        token = self.pending()
        self.executor.reject(token, capability=self.cap)
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.focus.assert_not_called()

    def test_expired_zero_attempts(self):
        token = self.pending()
        value = self.confirmation._pending[token]
        self.confirmation._pending[token] = replace(value, expires_at=value.created_at - timedelta(seconds=1))
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.focus.assert_not_called()

    def test_mismatched_original_or_arguments_zero_attempts(self):
        for request in (StructuredCapabilityRequest("different", {}),
                        StructuredCapabilityRequest(self.impl.PHRASE, {"hwnd": IDENTITY.hwnd}),
                        StructuredCapabilityRequest(self.impl.PHRASE, {"_binding": _FocusBinding(IDENTITY, CONTEXT)})):
            with self.subTest(request=request):
                self.setUp()
                token = self.pending()
                result = self.executor.approve_and_execute_structured(token, capability=self.cap, request=request)
                self.assertIs(result.status, ExecutionStatus.DENIED)
                self.native.focus.assert_not_called()

    def test_confirmation_binding_mismatch_zero_attempts(self):
        token = self.pending()
        self.confirmation._bindings[token] = object()
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.focus.assert_not_called()

    def test_permission_revoked_after_preparation_zero_attempts(self):
        token = self.pending()
        self.permissions.revoke(self.cap.name)
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.focus.assert_not_called()

    def test_registration_replaced_zero_attempts(self):
        token = self.pending()
        self.registry.unregister(self.cap.name)
        self.registry.register(self.cap, FocusWindowCapability(service=self.service))
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.focus.assert_not_called()

    def test_pre_mutation_identity_drift_zero_attempts(self):
        changes = ({"hwnd": IDENTITY.hwnd + 1, "root": IDENTITY.root + 1},
                   {"pid": IDENTITY.pid + 1}, {"tid": IDENTITY.tid + 1},
                   {"creation_time": IDENTITY.creation_time + 1}, {"executable": "replacement"},
                   {"window_class": "replacement"}, {"root": 9}, {"session": 9}, {"desktop": "Other"})
        for fields in changes:
            with self.subTest(fields=fields):
                self.setUp()
                token = self.pending()
                self.native.identity.return_value = replace(IDENTITY, **fields)
                result = self.approve(token)
                self.assertIs(result.output.state, FocusState.TARGET_CHANGED)
                self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)
                self.native.focus.assert_not_called()

    def test_context_drift_during_pre_identity_zero_attempts(self):
        token = self.pending()
        self.native.context.side_effect = [CONTEXT, replace(CONTEXT, session=9)]
        self.assertIs(self.approve(token).output.state, FocusState.TARGET_CHANGED)
        self.native.focus.assert_not_called()

    def test_pre_native_error_zero_attempts_sanitized(self):
        token = self.pending()
        self.native.identity.side_effect = OSError("private native error")
        result = self.approve(token)
        self.assertIs(result.output.state, FocusState.INCONCLUSIVE)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn("private native error", repr(result))
        self.native.focus.assert_not_called()

    def test_os_denial_never_verified_even_already_foreground(self):
        token = self.pending()
        self.native.focus.return_value = False
        result = self.approve(token)
        self.assertIs(result.output.state, FocusState.NOT_FOCUSED)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.native.focus.assert_called_once()
        self.assertEqual(self.native.foreground.call_count, 4)

    def test_same_process_other_foreground_not_success(self):
        token = self.pending()
        self.native.foreground.return_value = IDENTITY.hwnd + 1
        result = self.approve(token)
        self.assertIs(result.output.state, FocusState.NOT_FOCUSED)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.native.focus.assert_called_once()

    def test_mutation_exception_still_samples_no_retry(self):
        token = self.pending()
        self.native.focus.side_effect = OSError("private")
        result = self.approve(token)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.native.focus.assert_called_once()
        self.assertEqual(self.native.foreground.call_count, 4)

    def test_identity_recycled_during_mutation_never_verified(self):
        token = self.pending()
        def focus(hwnd):
            self.native.identity.return_value = replace(IDENTITY, creation_time=IDENTITY.creation_time + 1)
            return True
        self.native.focus.side_effect = focus
        result = self.approve(token)
        self.assertIs(result.output.state, FocusState.TARGET_CHANGED)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.native.focus.assert_called_once()

    def test_late_post_identity_drift_never_verified(self):
        token = self.pending()
        self.native.identity.side_effect = [IDENTITY, IDENTITY, replace(IDENTITY, tid=9)]
        self.assertIs(self.approve(token).verification.status, VerificationStatus.NOT_VERIFIED)
        self.native.focus.assert_called_once()

    def test_verification_resamples_target_context_and_foreground(self):
        token = self.pending()
        self.native.foreground.side_effect = [IDENTITY.hwnd, IDENTITY.hwnd + 1]
        result = self.approve(token)
        self.assertIs(result.output.state, FocusState.FOCUSED)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.assertEqual(self.native.identity.call_count, 7)
        self.assertEqual(self.native.context.call_count, 12)
        self.native.focus.assert_called_once()

    def test_verification_identity_or_context_drift(self):
        for method, values in (("identity", [IDENTITY] * 3 + [replace(IDENTITY, tid=9)] * 2),
                               ("context", [CONTEXT] * 6 + [replace(CONTEXT, session=9)] * 4)):
            with self.subTest(method=method):
                self.setUp()
                token = self.pending()
                getattr(self.native, method).side_effect = values
                result = self.approve(token)
                self.assertIs(result.output.state, FocusState.FOCUSED)
                self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)

    def test_post_read_failure_inconclusive_no_retry(self):
        token = self.pending()
        self.native.identity.side_effect = [IDENTITY, OSError("private")]
        self.assertIs(self.approve(token).verification.status, VerificationStatus.INDETERMINATE)
        self.native.focus.assert_called_once()

    def test_approved_token_cannot_repeat_attempt(self):
        token = self.pending()
        self.approve(token)
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.focus.assert_called_once()

    def test_raw_private_inputs_and_legacy_rejected(self):
        for key in ("hwnd", "identity", "context", "_binding", "_evidence", "title", "path", "force"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.impl.validate_arguments({key: "private"})
        with self.assertRaises(ValueError):
            self.impl.execute(self.impl.PHRASE)
        self.assertEqual(self.native.mock_calls, [])

    def test_preparation_unavailable_fails_closed(self):
        self.native.foreground.return_value = 0
        result = self.executor.execute_structured(self.cap, self.request)
        self.assertIs(result.status, ExecutionStatus.FAILED)
        self.native.focus.assert_not_called()

    def test_mapping_exact_and_no_io(self):
        self.assertEqual(self.impl.map_intent_arguments({}, original_request="semantic"), {})
        self.assertEqual(self.impl.map_intent_arguments({"request": self.impl.PHRASE}, original_request=self.impl.PHRASE), {})
        for text in (self.impl.PHRASE + " extra", "focus window", "focus last window"):
            with self.assertRaises(ValueError):
                self.impl.map_intent_arguments({"request": text}, original_request=text)
        self.assertEqual(self.native.mock_calls, [])

    def test_binding_copy_and_approval_no_native_recapture(self):
        saved = self.impl.validate_arguments({})
        self.native.reset_mock()
        self.assertEqual(self.impl.validate_approval_arguments({}, prepared=saved), deepcopy(saved))
        self.assertEqual(self.native.mock_calls, [])
        with self.assertRaises(ValueError):
            self.impl.validate_arguments(saved)

    def test_no_undo_and_audit_privacy(self):
        existing = self.undo.register(capability="fixture", description="fixture", callback=lambda: None)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            self.audit = AuditService(path)
            self.executor = ActionExecutor(self.registry, PolicyService(self.permissions),
                                          self.confirmation, self.audit, self.undo)
            result = self.approve(self.pending())
            text = path.read_text(encoding="utf-8") + repr(result) + str(result.output._binding)
            for secret in (str(IDENTITY.hwnd), str(IDENTITY.pid), IDENTITY.executable, IDENTITY.window_class):
                self.assertNotIn(secret, text)
        self.assertEqual(self.undo.peek(), existing)
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, [x.event_type for x in self.audit.all()])

    def test_invalid_binding_zero_calls_and_output_binding_mismatch(self):
        self.assertIs(self.adapter.focus_window(None), FocusState.INCONCLUSIVE)
        self.assertEqual(self.native.mock_calls, [])
        saved = self.impl.validate_arguments({})
        output = self.service.focus_window(saved["_binding"])
        other = {"_binding": _FocusBinding(replace(IDENTITY, tid=9), CONTEXT)}
        result = self.impl.verify_result(request=StructuredCapabilityRequest(self.impl.PHRASE, other), output=output)
        self.assertIs(result.status, VerificationStatus.INDETERMINATE)

    def test_unsupported_platform_zero_calls(self):
        self.adapter._platform = "linux"
        self.assertIs(self.adapter.focus_window(_FocusBinding(IDENTITY, CONTEXT)), FocusState.INCONCLUSIVE)
        self.assertEqual(self.native.mock_calls, [])

    def test_native_fixed_order(self):
        self.adapter.focus_window(_FocusBinding(IDENTITY, CONTEXT))
        self.assertEqual([x[0] for x in self.native.mock_calls],
                         ["context", "identity", "context", "focus", "context", "identity", "context",
                          "foreground", "context", "identity", "context"])

    def test_session_cancel_and_approval_saved_candidate(self):
        self.permissions.grant(self.cap.name)
        session = ConversationSession(resolver=IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry))),
                                      registry=self.registry, executor=self.executor)
        self.assertIs(session.request(self.impl.PHRASE).status, ExecutionStatus.REQUIRES_CONFIRMATION)
        session.request("cancel")
        self.native.focus.assert_not_called()
        session.request(self.impl.PHRASE)
        self.assertIs(session.approve_pending().verification.status, VerificationStatus.VERIFIED)
        self.native.focus.assert_called_once()


class FocusNativeTests(unittest.TestCase):
    def test_pointer_width_signature_and_single_plain_call(self):
        dlls = {name: Mock() for name in ("user32", "kernel32", "wtsapi32")}
        with patch("ctypes.WinDLL", side_effect=lambda name, **kw: dlls[name]):
            native = _FocusNative()
        self.assertEqual(native.u.SetForegroundWindow.argtypes, [ctypes.wintypes.HWND])
        self.assertIs(native.u.SetForegroundWindow.restype, ctypes.wintypes.BOOL)
        native.u.SetForegroundWindow.return_value = False
        self.assertFalse(native.focus(IDENTITY.hwnd))
        native.u.SetForegroundWindow.assert_called_once_with(IDENTITY.hwnd)

    def test_no_forced_focus_or_content_apis(self):
        source = Path("nayeon/services/windows_focus.py").read_text(encoding="utf-8")
        for forbidden in ("SendInput", "AttachThreadInput", "AllowSetForegroundWindow", "GetWindowText",
                          "mouse_event", "keybd_event", "ShowWindow", "sleep("):
            self.assertNotIn(forbidden, source)

    def test_focus_resource_cleanup_success_and_post_failure(self):
        # Reuse query-resource setup without inheriting/rediscovering its tests.
        fixture = fixtures.NativeResourceTests()
        for fail in (False, True):
            with self.subTest(fail=fail):
                fixture.setUp()
                fixture.configure_window()
                api = fixture.api
                api.focus = Mock(return_value=True)
                api.foreground = Mock(return_value=IDENTITY.hwnd)
                if fail:
                    api.focus.side_effect = lambda hwnd: setattr(api.k.GetProcessTimes, "side_effect", OSError("private")) or True
                result = WindowsFocusAdapter(native=api, platform="win32").focus_window(_FocusBinding(IDENTITY, CONTEXT))
                self.assertIs(result, FocusState.INCONCLUSIVE if fail else FocusState.FOCUSED)
                api.focus.assert_called_once()
                self.assertEqual(api.k.OpenProcess.call_count, api.k.CloseHandle.call_count)
                self.assertEqual(api.u.OpenInputDesktop.call_count, api.u.CloseDesktop.call_count)
                self.assertEqual(api.w.WTSQuerySessionInformationW.call_count, api.w.WTSFreeMemory.call_count)


class AdditionalFocusTests(unittest.TestCase):
    def setUp(self):
        self.h = FocusTests()
        self.h.setUp()

    def test_approval_validator_cannot_substitute_saved_binding(self):
        token = self.h.pending()
        other = {"_binding": _FocusBinding(replace(IDENTITY, tid=9), CONTEXT)}
        with patch.object(self.h.impl, "validate_approval_arguments", return_value=other):
            self.assertIs(self.h.approve(token).status, ExecutionStatus.DENIED)
        self.h.native.focus.assert_not_called()

    def test_approval_validator_exception_redacted_and_consumed(self):
        token = self.h.pending()
        with patch.object(self.h.impl, "validate_approval_arguments", side_effect=ValueError("private")):
            result = self.h.approve(token)
        self.assertIs(result.status, ExecutionStatus.DENIED)
        self.assertNotIn("private", repr(result))
        self.assertIs(self.h.approve(token).status, ExecutionStatus.DENIED)
        self.h.native.focus.assert_not_called()

    def test_legacy_approval_cannot_use_structured_token(self):
        token = self.h.pending()
        result = self.h.executor.approve_and_execute(token, capability=self.h.cap, request=self.h.impl.PHRASE)
        self.assertIs(result.status, ExecutionStatus.DENIED)
        self.h.native.focus.assert_not_called()

    def test_policy_block_after_preparation_zero_mutation(self):
        token = self.h.pending()
        self.h.executor._policy._blocked_capabilities.add(self.h.cap.name)
        self.assertIs(self.h.approve(token).status, ExecutionStatus.DENIED)
        self.h.native.focus.assert_not_called()

    def test_binding_and_result_immutable_redacted(self):
        binding = self.h.impl.validate_arguments({})["_binding"]
        self.assertEqual(binding, deepcopy(binding))
        self.assertIsNot(binding, deepcopy(binding))
        with self.assertRaises(AttributeError):
            binding.identity = None
        result = self.h.service.focus_window(binding)
        for obj in (binding, result, binding.identity, binding.context):
            for text in (repr(obj), str(obj)):
                for secret in (str(IDENTITY.hwnd), str(IDENTITY.pid), IDENTITY.executable,
                               IDENTITY.window_class, "WinSta0", "Default"):
                    self.assertNotIn(secret, text)
        self.assertFalse(hasattr(binding, "__dict__"))

    def test_no_geometry_or_content_acquisition_during_focus(self):
        token = self.h.pending()
        self.h.native.reset_mock()
        self.h.approve(token)
        self.h.native.state.assert_not_called()
        self.assertEqual(set(x[0] for x in self.h.native.mock_calls),
                         {"context", "identity", "focus", "foreground"})

    def test_preparation_stability_required(self):
        for method, values in (("foreground", [IDENTITY.hwnd, IDENTITY.hwnd + 1]),
                               ("identity", [IDENTITY, replace(IDENTITY, creation_time=99)]),
                               ("context", [CONTEXT, replace(CONTEXT, session=9)])):
            with self.subTest(method=method):
                self.h.setUp()
                getattr(self.h.native, method).side_effect = values
                result = self.h.executor.execute_structured(self.h.cap, self.h.request)
                self.assertIs(result.status, ExecutionStatus.FAILED)
                self.h.native.focus.assert_not_called()

    def test_service_malformed_native_results_fail_closed(self):
        binding = _FocusBinding(IDENTITY, CONTEXT)
        adapter = Mock()
        service = WindowFocusService(adapter=adapter)
        for value in (None, "focused", {}, True):
            adapter.focus_window.return_value = value
            adapter.observe_focus.return_value = value
            self.assertIs(service.focus_window(binding).state, FocusState.INCONCLUSIVE)
            self.assertIs(service.observe_focus(binding), FocusState.INCONCLUSIVE)
        adapter.focus_window.side_effect = OSError("private")
        self.assertNotIn("private", repr(service.focus_window(binding)))

    def test_verification_native_error_cannot_upgrade_receipt(self):
        token = self.h.pending()
        self.h.native.foreground.side_effect = [IDENTITY.hwnd, OSError("private")]
        result = self.h.approve(token)
        self.assertIs(result.output.state, FocusState.FOCUSED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.h.native.focus.assert_called_once()

    def test_denied_receipt_cannot_upgrade_on_later_foreground_change(self):
        token = self.h.pending()
        self.h.native.focus.return_value = False
        self.h.native.foreground.side_effect = [IDENTITY.hwnd + 1, IDENTITY.hwnd]
        result = self.h.approve(token)
        self.assertIs(result.output.state, FocusState.NOT_FOCUSED)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.h.native.focus.assert_called_once()

    def test_native_pre_read_failure_cleans_owned_resources_zero_mutation(self):
        fixture = fixtures.NativeResourceTests()
        for fail in ("GetProcessTimes", "GetUserObjectInformationW"):
            with self.subTest(fail=fail):
                fixture.setUp()
                fixture.configure_window()
                api = fixture.api
                api.focus = Mock()
                function = getattr(api.k if fail == "GetProcessTimes" else api.u, fail)
                function.side_effect = OSError("private")
                adapter = WindowsFocusAdapter(native=api, platform="win32")
                self.assertIs(adapter.focus_window(_FocusBinding(IDENTITY, CONTEXT)), FocusState.INCONCLUSIVE)
                api.focus.assert_not_called()
                self.assertEqual(api.k.OpenProcess.call_count, api.k.CloseHandle.call_count)
                self.assertEqual(api.u.OpenInputDesktop.call_count, api.u.CloseDesktop.call_count)

    def test_cleanup_failure_never_verifies_or_retries(self):
        fixture = fixtures.NativeResourceTests()
        fixture.setUp()
        fixture.configure_window()
        api = fixture.api
        api.focus = Mock()
        api.k.CloseHandle.return_value = False
        adapter = WindowsFocusAdapter(native=api, platform="win32")
        self.assertIs(adapter.focus_window(_FocusBinding(IDENTITY, CONTEXT)), FocusState.INCONCLUSIVE)
        api.focus.assert_not_called()
        api.k.CloseHandle.assert_called_once()
