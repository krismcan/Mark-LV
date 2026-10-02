"""Phase 6.3 deterministic checks: all keyboard mutation is mocked."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
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
from nayeon.capabilities.structured import PreparedApprovalValidator, StructuredCapabilityRequest
from nayeon.capabilities.type_text import TypeTextCapability
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry, ExecutionMode
from nayeon.services.keyboard_text import (
    KeyboardTextResult, KeyboardTextService, TextInputState as S, _TextBinding, validate_text,
)
from nayeon.services.window_focus import _FocusBinding
from nayeon.services.windows_keyboard import (
    WindowsKeyboardAdapter, _KeyboardNative, _INPUT, _KEYBDINPUT, _MOUSEINPUT, _unicode_events,
)
from nayeon.undo.contract import UndoProvider
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationStatus as V
from tests import test_foreground_observation as fixtures

CONTEXT, IDENTITY = fixtures.CONTEXT, fixtures.IDENTITY
TEXT = "Private bounded text \U0001f642"


class KeyboardTests(unittest.TestCase):
    def setUp(self):
        self.native = fixtures.fake_native()
        self.native.inject.side_effect = lambda events: len(events)
        self.adapter = WindowsKeyboardAdapter(native=self.native, platform="win32")
        self.service = KeyboardTextService(adapter=self.adapter)
        self.impl = TypeTextCapability(service=self.service)
        self.cap = self.impl.capability
        self.registry = CapabilityRegistry()
        self.registry.register(self.cap, self.impl)
        self.permissions = PermissionService(default_allowed=False)
        self.confirmation = ConfirmationService()
        self.audit = AuditService()
        self.undo = UndoService()
        self.policy = PolicyService(self.permissions)
        self.executor = ActionExecutor(self.registry, self.policy, self.confirmation, self.audit, self.undo)
        self.request = StructuredCapabilityRequest("type text " + json.dumps(TEXT, ensure_ascii=False), {"text": TEXT})

    def pending(self):
        self.permissions.grant(self.cap.name)
        result = self.executor.execute_structured(self.cap, self.request)
        self.assertIs(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.native.inject.assert_not_called()
        return result.confirmation_request.token

    def approve(self, token, request=None):
        return self.executor.approve_and_execute_structured(
            token, capability=self.cap, request=request or self.request)

    def binding(self):
        return _TextBinding(_FocusBinding(IDENTITY, CONTEXT), TEXT)

    def session(self):
        return ConversationSession(
            resolver=IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry))),
            registry=self.registry, executor=self.executor)

    def test_metadata_discovery_construction_no_io(self):
        self.assertIs(self.cap.execution_mode, ExecutionMode.LOCAL)
        self.assertTrue(self.cap.requires_confirmation)
        self.assertFalse(self.cap.requires_llm)
        self.assertFalse(self.cap.reversible)
        self.assertNotIsInstance(self.impl, UndoProvider)
        self.assertIsInstance(self.impl, PreparedApprovalValidator)
        with patch("nayeon.services.windows_keyboard._KeyboardNative", side_effect=AssertionError()):
            registry = CapabilityRegistry()
            CapabilityLoader(registry).discover()
        self.assertIsInstance(registry.get_implementation("type_text"), TypeTextCapability)
        self.assertEqual(self.native.mock_calls, [])

    def test_default_deny_zero_injection(self):
        self.assertIs(self.executor.execute_structured(self.cap, self.request).status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()

    def test_permission_only_prepares_read_only(self):
        self.pending()
        self.assertEqual(self.native.foreground.call_count, 2)
        self.assertEqual(set(c[0] for c in self.native.mock_calls), {"context", "foreground", "identity", "state"})

    def test_approved_one_attempt_verified(self):
        result = self.approve(self.pending())
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.output.state, S.TYPED)
        self.assertIs(result.verification.status, V.VERIFIED)
        self.native.inject.assert_called_once()
        self.assertEqual(len(self.native.inject.call_args.args[0]), len(TEXT.encode("utf-16-le")))

    def test_rejected_consumed(self):
        token = self.pending()
        self.executor.reject(token, capability=self.cap)
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()

    def test_expired_consumed(self):
        token = self.pending()
        old = self.confirmation._pending[token]
        self.confirmation._pending[token] = replace(old, expires_at=old.created_at - timedelta(seconds=1))
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()

    def test_replay_no_second_attempt(self):
        token = self.pending()
        self.approve(token)
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.inject.assert_called_once()

    def test_text_or_original_mismatch_consumes_zero_injection(self):
        for request in (StructuredCapabilityRequest("different", {"text": TEXT}),
                        StructuredCapabilityRequest(self.request.original_request, {"text": TEXT + "x"}),
                        StructuredCapabilityRequest(self.request.original_request, {"text": TEXT, "hwnd": IDENTITY.hwnd})):
            with self.subTest(request=request):
                self.setUp()
                token = self.pending()
                self.assertIs(self.approve(token, request).status, ExecutionStatus.DENIED)
                self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
                self.native.inject.assert_not_called()

    def test_confirmation_action_binding_mismatch(self):
        token = self.pending()
        self.confirmation._bindings[token] = object()
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()

    def test_approval_no_recapture_saved_text_and_target(self):
        saved = self.impl.validate_arguments({"text": TEXT})
        self.native.reset_mock()
        self.assertEqual(self.impl.validate_approval_arguments({"text": TEXT}, prepared=saved), deepcopy(saved))
        self.assertEqual(self.native.mock_calls, [])
        self.assertEqual(set(saved), {"_binding"})
        with self.assertRaises(ValueError):
            self.impl.validate_arguments(saved)

    def test_approval_cannot_substitute_binding(self):
        for binding in (_TextBinding(_FocusBinding(replace(IDENTITY, tid=9), CONTEXT), TEXT),
                        _TextBinding(_FocusBinding(IDENTITY, CONTEXT), TEXT + "x")):
            with self.subTest(binding=binding):
                self.setUp()
                token = self.pending()
                with patch.object(self.impl, "validate_approval_arguments", return_value={"_binding": binding}):
                    self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
                self.native.inject.assert_not_called()

    def test_approval_exception_redacted_consumed(self):
        token = self.pending()
        with patch.object(self.impl, "validate_approval_arguments", side_effect=OSError(TEXT)):
            result = self.approve(token)
        self.assertIs(result.status, ExecutionStatus.DENIED)
        self.assertNotIn(TEXT, repr(result))
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()

    def test_permission_revoked(self):
        token = self.pending()
        self.permissions.revoke(self.cap.name)
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()

    def test_policy_block_after_preparation(self):
        token = self.pending()
        self.policy._blocked_capabilities.add(self.cap.name)
        self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()

    def test_registration_metadata_or_implementation_changed(self):
        for metadata in (False, True):
            with self.subTest(metadata=metadata):
                self.setUp()
                token = self.pending()
                self.registry.unregister(self.cap.name)
                self.registry.register(replace(self.cap, requires_confirmation=False) if metadata else self.cap,
                                       self.impl if metadata else TypeTextCapability(service=self.service))
                self.assertIs(self.approve(token).status, ExecutionStatus.DENIED)
                self.native.inject.assert_not_called()

    def test_registration_change_during_policy_recheck(self):
        token = self.pending()
        evaluate = self.policy.evaluate
        def changed(cap):
            decision = evaluate(cap)
            self.registry.unregister(cap.name)
            self.registry.register(cap, TypeTextCapability(service=self.service))
            return decision
        with patch.object(self.policy, "evaluate", side_effect=changed):
            self.assertIs(self.approve(token).status, ExecutionStatus.FAILED)
        self.native.inject.assert_not_called()

    def test_legacy_cannot_bypass_structure_or_approval(self):
        with self.assertRaises(ValueError):
            self.impl.execute('type text "fixture"')
        token = self.pending()
        result = self.executor.approve_and_execute(token, capability=self.cap, request=self.request.original_request)
        self.assertIs(result.status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()

    def test_foreground_drift_no_replacement_or_refocus(self):
        token = self.pending()
        self.native.reset_mock()
        self.native.foreground.return_value = IDENTITY.hwnd + 1
        result = self.approve(token)
        self.assertIs(result.output.state, S.TARGET_CHANGED)
        self.assertIs(result.verification.status, V.NOT_VERIFIED)
        self.native.inject.assert_not_called()
        self.native.focus.assert_not_called()
        self.native.state.assert_not_called()
        self.assertTrue(all(c.args == (IDENTITY.hwnd,) for c in self.native.identity.call_args_list))

    def test_all_identity_fields_drift_zero_injection(self):
        changes = ({"hwnd": IDENTITY.hwnd + 1, "root": IDENTITY.root + 1},
                   {"pid": 9}, {"tid": 9}, {"creation_time": 99}, {"executable": "replacement"},
                   {"window_class": "replacement"}, {"root": 9}, {"session": 9}, {"desktop": "Other"})
        for fields in changes:
            with self.subTest(fields=fields):
                self.setUp()
                token = self.pending()
                self.native.identity.return_value = replace(IDENTITY, **fields)
                self.assertIs(self.approve(token).output.state, S.TARGET_CHANGED)
                self.native.inject.assert_not_called()

    def test_all_context_fields_drift_zero_injection(self):
        for fields in ({"session": 9}, {"input_desktop": "Other"}, {"thread_desktop": "Other"},
                       {"station": "Other"}, {"active": False}):
            with self.subTest(fields=fields):
                self.setUp()
                token = self.pending()
                self.native.context.return_value = replace(CONTEXT, **fields)
                self.assertIs(self.approve(token).output.state, S.TARGET_CHANGED)
                self.native.inject.assert_not_called()

    def test_late_pre_context_and_identity_drift(self):
        for method, values in (("context", [CONTEXT] * 3 + [replace(CONTEXT, active=False)]),
                               ("identity", [IDENTITY, replace(IDENTITY, creation_time=99)])):
            with self.subTest(method=method):
                self.setUp()
                token = self.pending()
                getattr(self.native, method).side_effect = values
                self.assertIs(self.approve(token).output.state, S.TARGET_CHANGED)
                self.native.inject.assert_not_called()

    def test_pre_read_errors_and_malformed_values(self):
        for method, value in (("context", None), ("identity", {}), ("foreground", True),
                              ("foreground", -1), ("identity", OSError(TEXT))):
            with self.subTest(method=method, value=type(value)):
                self.setUp()
                token = self.pending()
                if isinstance(value, Exception):
                    getattr(self.native, method).side_effect = value
                else:
                    getattr(self.native, method).return_value = value
                result = self.approve(token)
                self.assertIs(result.output.state, S.INCONCLUSIVE)
                self.assertIs(result.verification.status, V.INDETERMINATE)
                self.assertNotIn(TEXT, repr(result))
                self.native.inject.assert_not_called()

    def test_zero_foreground_is_target_changed(self):
        token = self.pending()
        self.native.foreground.return_value = 0
        self.assertIs(self.approve(token).output.state, S.TARGET_CHANGED)
        self.native.inject.assert_not_called()

    def test_full_partial_zero_native_counts(self):
        count = len(TEXT.encode("utf-16-le"))
        for inserted, state, verified in ((count, S.TYPED, V.VERIFIED), (1, S.PARTIAL, V.NOT_VERIFIED),
                                          (count - 1, S.PARTIAL, V.NOT_VERIFIED), (0, S.NOT_TYPED, V.NOT_VERIFIED)):
            with self.subTest(inserted=inserted):
                self.setUp()
                self.native.inject.side_effect = None
                self.native.inject.return_value = inserted
                result = self.approve(self.pending())
                self.assertIs(result.output.state, state)
                self.assertIs(result.verification.status, verified)
                self.native.inject.assert_called_once()

    def test_invalid_native_counts_sanitized_inconclusive(self):
        for value in (True, False, -1, len(TEXT.encode("utf-16-le")) + 1, None, "private", 1.0, {}):
            with self.subTest(value=type(value)):
                self.setUp()
                self.native.inject.side_effect = None
                self.native.inject.return_value = value
                result = self.approve(self.pending())
                self.assertIs(result.output.state, S.INCONCLUSIVE)
                self.assertIs(result.verification.status, V.INDETERMINATE)
                self.assertNotIn("private", repr(result))
                self.native.inject.assert_called_once()

    def test_injection_exception_still_postchecks_no_retry(self):
        token = self.pending()
        self.native.reset_mock()
        self.native.inject.side_effect = OSError(TEXT)
        result = self.approve(token)
        self.assertIs(result.output.state, S.INCONCLUSIVE)
        self.assertIs(result.verification.status, V.INDETERMINATE)
        self.assertNotIn(TEXT, repr(result))
        self.native.inject.assert_called_once()
        self.assertEqual(self.native.foreground.call_count, 4)
        self.assertEqual(self.native.identity.call_count, 4)
        self.assertEqual(self.native.context.call_count, 8)

    def test_post_identity_context_foreground_drift(self):
        for method, value in (("identity", replace(IDENTITY, creation_time=99)),
                              ("context", replace(CONTEXT, active=False)), ("foreground", IDENTITY.hwnd + 1)):
            with self.subTest(method=method):
                self.setUp()
                token = self.pending()
                def inject(events):
                    getattr(self.native, method).return_value = value
                    return len(events)
                self.native.inject.side_effect = inject
                result = self.approve(token)
                self.assertIs(result.output.state, S.TARGET_CHANGED)
                self.assertIs(result.verification.status, V.NOT_VERIFIED)
                self.native.inject.assert_called_once()

    def test_partial_or_zero_plus_post_drift_never_typed(self):
        for count in (0, 1):
            with self.subTest(count=count):
                self.setUp()
                token = self.pending()
                def inject(events):
                    self.native.foreground.return_value = IDENTITY.hwnd + 1
                    return count
                self.native.inject.side_effect = inject
                self.assertIs(self.approve(token).output.state, S.TARGET_CHANGED)
                self.native.inject.assert_called_once()

    def test_post_read_failure_inconclusive(self):
        token = self.pending()
        def inject(events):
            self.native.identity.side_effect = OSError(TEXT)
            return len(events)
        self.native.inject.side_effect = inject
        result = self.approve(token)
        self.assertIs(result.output.state, S.INCONCLUSIVE)
        self.assertIs(result.verification.status, V.INDETERMINATE)
        self.native.inject.assert_called_once()

    def test_late_post_drift_caught(self):
        token = self.pending()
        self.native.identity.side_effect = [IDENTITY] * 3 + [replace(IDENTITY, tid=9)]
        self.assertIs(self.approve(token).output.state, S.TARGET_CHANGED)
        self.native.inject.assert_called_once()

    def test_verification_fresh_target_context_foreground(self):
        for method, values in (("foreground", [IDENTITY.hwnd] * 4 + [IDENTITY.hwnd + 1]),
                               ("identity", [IDENTITY] * 4 + [replace(IDENTITY, tid=9)] * 2),
                               ("context", [CONTEXT] * 8 + [replace(CONTEXT, active=False)] * 4)):
            with self.subTest(method=method):
                self.setUp()
                token = self.pending()
                getattr(self.native, method).side_effect = values
                result = self.approve(token)
                self.assertIs(result.output.state, S.TYPED)
                self.assertIs(result.verification.status, V.NOT_VERIFIED)
                self.native.inject.assert_called_once()

    def test_verification_read_error(self):
        token = self.pending()
        self.native.foreground.side_effect = [IDENTITY.hwnd] * 4 + [OSError(TEXT)]
        result = self.approve(token)
        self.assertIs(result.output.state, S.TYPED)
        self.assertIs(result.verification.status, V.INDETERMINATE)
        self.native.inject.assert_called_once()

    def test_negative_receipts_never_upgraded_or_mutated(self):
        request = StructuredCapabilityRequest("fixture", {"_binding": self.binding()})
        for state in (S.PARTIAL, S.NOT_TYPED, S.TARGET_CHANGED, S.INCONCLUSIVE):
            result = self.impl.verify_result(request=request, output=KeyboardTextResult(state, self.binding()))
            self.assertIs(result.status, V.INDETERMINATE if state is S.INCONCLUSIVE else V.NOT_VERIFIED)
        self.assertEqual(self.native.mock_calls, [])

    def test_verification_output_mismatch_and_untyped(self):
        request = StructuredCapabilityRequest("fixture", {"_binding": self.binding()})
        other = _TextBinding(_FocusBinding(IDENTITY, CONTEXT), TEXT + "x")
        for output in (KeyboardTextResult(S.TYPED, other), None, "typed", {}):
            self.assertIs(self.impl.verify_result(request=request, output=output).status, V.INDETERMINATE)
        self.assertEqual(self.native.mock_calls, [])

    def test_fixed_order_no_focus_content_or_geometry(self):
        self.adapter.type_text(self.binding())
        observation = ["context", "identity", "context", "foreground", "context", "identity", "context", "foreground"]
        self.assertEqual([c[0] for c in self.native.mock_calls], observation + ["inject"] + observation)
        self.native.focus.assert_not_called()
        self.native.state.assert_not_called()

    def test_preparation_inconsistent_unavailable(self):
        for method, values in (("foreground", [IDENTITY.hwnd, IDENTITY.hwnd + 1]),
                               ("identity", [IDENTITY, replace(IDENTITY, creation_time=99)]),
                               ("context", [CONTEXT, replace(CONTEXT, active=False)])):
            with self.subTest(method=method):
                self.setUp()
                getattr(self.native, method).side_effect = values
                self.assertIs(self.executor.execute_structured(self.cap, self.request).status, ExecutionStatus.FAILED)
                self.native.inject.assert_not_called()
        self.setUp()
        self.native.foreground.return_value = 0
        self.assertIs(self.executor.execute_structured(self.cap, self.request).status, ExecutionStatus.FAILED)
        self.native.inject.assert_not_called()

    def test_no_undo_audit_and_receipt_redaction(self):
        existing = self.undo.register(capability="fixture", description="fixture", callback=lambda: None)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            self.audit = AuditService(path)
            self.executor = ActionExecutor(self.registry, self.policy, self.confirmation, self.audit, self.undo)
            result = self.approve(self.pending())
            text = path.read_text(encoding="utf-8") + repr(result) + repr(result.output._binding)
            for secret in (TEXT, str(IDENTITY.hwnd), str(IDENTITY.pid), IDENTITY.executable, IDENTITY.window_class):
                self.assertNotIn(secret, text)
        self.assertEqual(self.undo.peek(), existing)
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, [e.event_type for e in self.audit.all()])

    def test_binding_deepcopy_immutable_redacted(self):
        binding = self.binding()
        self.assertEqual(binding, deepcopy(binding))
        self.assertIsNot(binding, deepcopy(binding))
        with self.assertRaises(AttributeError):
            binding.text = "replacement"
        for obj in (binding, binding.target, binding.target.identity, binding.target.context,
                    KeyboardTextResult(S.TYPED, binding)):
            for text in (str(obj), repr(obj)):
                for secret in (TEXT, str(IDENTITY.hwnd), IDENTITY.executable, "Default", "WinSta0"):
                    self.assertNotIn(secret, text)
        self.assertFalse(hasattr(binding, "__dict__"))

    def test_invalid_binding_and_platform_zero_calls(self):
        for binding in (None, {}, _TextBinding(None, TEXT), _TextBinding(_FocusBinding(IDENTITY, CONTEXT), "\n")):
            self.assertIs(self.adapter.type_text(binding), S.INCONCLUSIVE)
            self.assertIs(self.adapter.observe_target(binding), S.INCONCLUSIVE)
        self.adapter._platform = "linux"
        self.assertIs(self.adapter.type_text(self.binding()), S.INCONCLUSIVE)
        self.assertIs(self.adapter.observe_target(self.binding()), S.INCONCLUSIVE)
        self.assertEqual(self.native.mock_calls, [])

    def test_service_malformed_adapter_and_exceptions(self):
        adapter = Mock()
        service = KeyboardTextService(adapter=adapter)
        for value in (None, "typed", {}, True):
            adapter.type_text.return_value = adapter.observe_target.return_value = value
            self.assertIs(service.type_text(self.binding()).state, S.INCONCLUSIVE)
            self.assertIs(service.observe_target(self.binding()), S.INCONCLUSIVE)
        adapter.type_text.side_effect = adapter.observe_target.side_effect = OSError(TEXT)
        self.assertNotIn(TEXT, repr(service.type_text(self.binding())))
        self.assertIs(service.observe_target(self.binding()), S.INCONCLUSIVE)

    def test_session_local_cancel_saved_candidate(self):
        self.permissions.grant(self.cap.name)
        session = self.session()
        phrase = "type text " + json.dumps(TEXT)
        self.assertIs(session.request(phrase).status, ExecutionStatus.REQUIRES_CONFIRMATION)
        session.request("cancel")
        self.assertFalse(session.has_pending)
        self.native.inject.assert_not_called()
        self.assertIs(session.request(phrase).status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assertIs(session.approve_pending().verification.status, V.VERIFIED)
        self.native.inject.assert_called_once()

    def test_session_cannot_approve_via_prose_or_replace_pending(self):
        self.permissions.grant(self.cap.name)
        session = self.session()
        session.request("type text " + json.dumps(TEXT))
        self.assertIs(session.request("approve").status, ExecutionStatus.DENIED)
        self.assertIs(session.request('type text "replacement"').status, ExecutionStatus.DENIED)
        self.native.inject.assert_not_called()
        self.assertIs(session.approve_pending().verification.status, V.VERIFIED)
        units = [event.ki.wScan for event in self.native.inject.call_args.args[0][::2]]
        self.assertEqual(bytes(b for u in units for b in (u & 255, u >> 8)).decode("utf-16-le"), TEXT)


class AdditionalKeyboardTests(unittest.TestCase):
    def setUp(self):
        self.h = KeyboardTests()
        self.h.setUp()

    def test_final_pre_foreground_sample_zero_injection(self):
        token = self.h.pending()
        self.h.native.foreground.side_effect = [IDENTITY.hwnd, IDENTITY.hwnd + 1]
        result = self.h.approve(token)
        self.assertIs(result.output.state, S.TARGET_CHANGED)
        self.h.native.inject.assert_not_called()

    def test_final_post_foreground_sample_drift(self):
        token = self.h.pending()
        self.h.native.foreground.side_effect = [IDENTITY.hwnd] * 3 + [IDENTITY.hwnd + 1]
        result = self.h.approve(token)
        self.assertIs(result.output.state, S.TARGET_CHANGED)
        self.assertIs(result.verification.status, V.NOT_VERIFIED)
        self.h.native.inject.assert_called_once()

    def test_final_verification_foreground_sample_drift(self):
        token = self.h.pending()
        self.h.native.foreground.side_effect = [IDENTITY.hwnd] * 5 + [IDENTITY.hwnd + 1]
        result = self.h.approve(token)
        self.assertIs(result.output.state, S.TYPED)
        self.assertIs(result.verification.status, V.NOT_VERIFIED)
        self.h.native.inject.assert_called_once()

    def test_verification_has_fixed_read_cardinality_no_mutation(self):
        saved = self.h.impl.validate_arguments({"text": TEXT})
        output = self.h.service.type_text(saved["_binding"])
        self.h.native.reset_mock()
        result = self.h.impl.verify_result(
            request=StructuredCapabilityRequest("fixture", saved), output=output)
        self.assertIs(result.status, V.VERIFIED)
        self.assertEqual(self.h.native.context.call_count, 4)
        self.assertEqual(self.h.native.identity.call_count, 2)
        self.assertEqual(self.h.native.foreground.call_count, 2)
        self.h.native.inject.assert_not_called()
        self.h.native.state.assert_not_called()

    def test_session_cancel_consumes_executor_binding(self):
        self.h.permissions.grant(self.h.cap.name)
        session = self.h.session()
        pending = session.request("type text " + json.dumps(TEXT))
        session.request("cancel")
        self.assertEqual(self.h.executor._structured_pending, {})
        self.assertEqual(self.h.confirmation._bindings, {})
        self.assertIs(self.h.approve(pending.confirmation_request.token).status, ExecutionStatus.DENIED)
        self.h.native.inject.assert_not_called()

    def test_all_space_payload_preserved_to_events(self):
        self.h.request = StructuredCapabilityRequest('type text "   "', {"text": "   "})
        result = self.h.approve(self.h.pending())
        self.assertIs(result.verification.status, V.VERIFIED)
        self.assertEqual([e.ki.wScan for e in self.h.native.inject.call_args.args[0]], [32] * 6)

class TextValidationTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock()
        self.impl = TypeTextCapability(service=self.service)

    def test_exact_raw_shape_and_types(self):
        for arguments in (None, [], "text", {}, {"text": 9}, {"text": None}, {"text": ["a"]}):
            with self.subTest(arguments=arguments), self.assertRaises((TypeError, ValueError)):
                self.impl.validate_arguments(arguments)
        for key in ("hwnd", "identity", "context", "_binding", "_evidence", "title", "path",
                    "keys", "hotkey", "modifiers", "virtual_key", "request", "force"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.impl.validate_arguments({"text": "plain", key: "private"})
        self.service.prepare_text.assert_not_called()

    def test_empty_controls_surrogates_and_nonprintable_rejected(self):
        for text in ("", "\n", "a\tb", "\r", "\x1b", "\x00", "\x7f", "\x85", "\ud800", "\udfff",
                     "\ud83d\ude42", "\u200b", "\u2028", "\u202e", "\u00a0"):
            with self.subTest(text=ascii(text)), self.assertRaises(ValueError):
                validate_text(text)
        for code in range(32):
            with self.subTest(control=code), self.assertRaises(ValueError):
                validate_text("x" + chr(code))

    def test_spaces_unicode_scalar_bounds_no_normalization(self):
        for text in (" ", "  Case  ", "caf\u00e9", "e\u0301", "\U0001f642", "a" * 256, "\U0001f642" * 256):
            self.assertEqual(validate_text(text), text)
        for text in ("a" * 257, "\U0001f642" * 257):
            with self.assertRaises(ValueError):
                validate_text(text)

    def test_exact_conversational_json_mapping_preserves_text(self):
        for text in ("  Case  ", "\U0001f642", "e\u0301", "Ctrl+C {ENTER}"):
            request = " TYPE TEXT " + json.dumps(text) + " "
            self.assertEqual(self.impl.map_intent_arguments({"request": request}, original_request=request), {"text": text})
        self.assertEqual(self.impl.map_intent_arguments({"text": "  Case  "}, original_request="semantic"), {"text": "  Case  "})
        self.assertEqual(self.service.mock_calls, [])

    def test_mapping_rejects_implicit_commands_extra_args_and_json_nonstrings(self):
        for request in ('type text hello', 'type text ["a"]', 'type text {"keys": "ENTER"}',
                        'type text 9', 'type text null', 'type text "x" extra', 'type text "\\n"',
                        'type text "\\ud800"', 'type text ""', 'type keys "x"'):
            with self.subTest(request=request), self.assertRaises((ValueError, TypeError)):
                self.impl.map_intent_arguments({"request": request}, original_request=request)
        for arguments in ({"request": 'type text "x"', "hwnd": 7}, {"text": "x", "keys": []},
                          {"request": "different"}, {}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.impl.map_intent_arguments(arguments, original_request='type text "x"')
        self.assertEqual(self.service.mock_calls, [])

    def test_preparation_exception_and_wrong_saved_text_sanitized(self):
        self.service.prepare_text.side_effect = OSError(TEXT)
        with self.assertRaisesRegex(ValueError, "^Text target preparation could not be established\\.$"):
            self.impl.validate_arguments({"text": TEXT})
        self.service.prepare_text.side_effect = None
        self.service.prepare_text.return_value = _TextBinding(_FocusBinding(IDENTITY, CONTEXT), "replacement")
        with self.assertRaises(ValueError):
            self.impl.validate_arguments({"text": TEXT})


class KeyboardNativeTests(unittest.TestCase):
    def test_windows_abi_layout_and_signature_single_call(self):
        dlls = {name: Mock() for name in ("user32", "kernel32", "wtsapi32")}
        with patch("ctypes.WinDLL", side_effect=lambda name, **kw: dlls[name]):
            native = _KeyboardNative()
        pointer_size = ctypes.sizeof(ctypes.c_void_p)
        self.assertEqual(ctypes.sizeof(_INPUT), 40 if pointer_size == 8 else 28)
        self.assertEqual(_INPUT.data.offset, 8 if pointer_size == 8 else 4)
        self.assertEqual(ctypes.sizeof(_KEYBDINPUT), 24 if pointer_size == 8 else 16)
        self.assertEqual(ctypes.sizeof(_MOUSEINPUT), 32 if pointer_size == 8 else 24)
        self.assertEqual(native.u.SendInput.argtypes, [ctypes.wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int])
        self.assertIs(native.u.SendInput.restype, ctypes.wintypes.UINT)
        events = _unicode_events("A")
        native.u.SendInput.return_value = 2
        self.assertEqual(native.inject(events), 2)
        native.u.SendInput.assert_called_once_with(2, events, ctypes.sizeof(_INPUT))

    def test_unicode_utf16_units_down_up_only_no_virtual_keys(self):
        text = "A \u00e9\U0001f642e\u0301"
        encoded = text.encode("utf-16-le")
        units = [int.from_bytes(encoded[i:i + 2], "little") for i in range(0, len(encoded), 2)]
        events = _unicode_events(text)
        self.assertEqual(len(events), 2 * len(units))
        for i, unit in enumerate(units):
            down, up = events[2 * i], events[2 * i + 1]
            for event in (down, up):
                self.assertEqual(event.type, 1)
                self.assertEqual(event.ki.wVk, 0)
                self.assertEqual(event.ki.wScan, unit)
                self.assertEqual(event.ki.time, 0)
                self.assertEqual(event.ki.dwExtraInfo, 0)
            self.assertEqual(down.ki.dwFlags, 4)
            self.assertEqual(up.ki.dwFlags, 6)
        self.assertIn(0xD83D, units)
        self.assertIn(0xDE42, units)

    def test_max_event_cardinality_and_no_native_validation(self):
        self.assertEqual(len(_unicode_events("a" * 256)), 512)
        self.assertEqual(len(_unicode_events("\U0001f642" * 256)), 1024)
        for text in ("", "a" * 257, "\ud800", "\n"):
            with self.assertRaises(ValueError):
                _unicode_events(text)

    def test_resource_cleanup_success_pre_post_and_verification_errors(self):
        fixture = fixtures.NativeResourceTests()
        for stage in ("success", "pre", "post", "verification"):
            with self.subTest(stage=stage):
                fixture.setUp()
                fixture.configure_window()
                api = fixture.api
                api.foreground = Mock(return_value=IDENTITY.hwnd)
                api.inject = Mock(side_effect=lambda events: len(events))
                if stage == "pre":
                    api.k.GetProcessTimes.side_effect = OSError(TEXT)
                if stage == "post":
                    def inject(events):
                        api.k.GetProcessTimes.side_effect = OSError(TEXT)
                        return len(events)
                    api.inject.side_effect = inject
                adapter = WindowsKeyboardAdapter(native=api, platform="win32")
                binding = _TextBinding(_FocusBinding(IDENTITY, CONTEXT), TEXT)
                self.assertIs(adapter.type_text(binding), S.INCONCLUSIVE if stage in ("pre", "post") else S.TYPED)
                if stage == "pre":
                    api.inject.assert_not_called()
                else:
                    api.inject.assert_called_once()
                if stage == "verification":
                    api.u.GetUserObjectInformationW.side_effect = OSError(TEXT)
                    self.assertIs(adapter.observe_target(binding), S.INCONCLUSIVE)
                self.assertEqual(api.k.OpenProcess.call_count, api.k.CloseHandle.call_count)
                self.assertEqual(api.u.OpenInputDesktop.call_count, api.u.CloseDesktop.call_count)
                self.assertEqual(api.w.WTSQuerySessionInformationW.call_count, api.w.WTSFreeMemory.call_count)

    def test_cleanup_failure_zero_injection(self):
        fixture = fixtures.NativeResourceTests()
        for method in ("CloseHandle", "CloseDesktop", "WTSFreeMemory"):
            with self.subTest(method=method):
                fixture.setUp()
                fixture.configure_window()
                api = fixture.api
                api.foreground = Mock(return_value=IDENTITY.hwnd)
                api.inject = Mock()
                function = getattr(api.k if method == "CloseHandle" else api.w if method == "WTSFreeMemory" else api.u, method)
                if method == "WTSFreeMemory":
                    function.side_effect = OSError(TEXT)
                else:
                    function.return_value = False
                adapter = WindowsKeyboardAdapter(native=api, platform="win32")
                binding = _TextBinding(_FocusBinding(IDENTITY, CONTEXT), TEXT)
                self.assertIs(adapter.type_text(binding), S.INCONCLUSIVE)
                api.inject.assert_not_called()
                function.assert_called_once()

    def test_post_cleanup_failure_never_verified_or_retried(self):
        fixture = fixtures.NativeResourceTests()
        fixture.setUp()
        fixture.configure_window()
        api = fixture.api
        api.foreground = Mock(return_value=IDENTITY.hwnd)
        def inject(events):
            api.k.CloseHandle.return_value = False
            return len(events)
        api.inject = Mock(side_effect=inject)
        adapter = WindowsKeyboardAdapter(native=api, platform="win32")
        binding = _TextBinding(_FocusBinding(IDENTITY, CONTEXT), TEXT)
        self.assertIs(adapter.type_text(binding), S.INCONCLUSIVE)
        api.inject.assert_called_once()
        self.assertEqual(api.k.OpenProcess.call_count, api.k.CloseHandle.call_count)
        self.assertEqual(api.u.OpenInputDesktop.call_count, api.u.CloseDesktop.call_count)


if __name__ == "__main__":
    unittest.main()
