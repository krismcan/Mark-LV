"""Phase 6.12 fake-only tests; NO LIVE SMOKE AUTHORIZED."""
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
import json
import pickle
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.pointer_binding import _PointerInvocation, _PointerPostObservationResult
from nayeon.audit.service import AuditEventType as A
from nayeon.services.pointer_effect import _EffectStatus as E, _PointerEffectReceipt, _PointerEffectService
from nayeon.services.target_validation import MAX_AGE_NS, _TargetVerificationResult, _TargetVerificationService
from nayeon.verification.contract import VerificationStatus as V
from tests import test_pointer_binding as b
from tests import test_pointer_effect as e


class PostObservationTests(unittest.TestCase):
    invocation = e.EffectIntegrationTests.invocation
    prepare = e.EffectIntegrationTests.prepare
    effect_once = e.EffectIntegrationTests.effect_once
    assert_cleared = e.EffectIntegrationTests.assert_cleared

    def setUp(self):
        e.EffectIntegrationTests.setUp(self)
        self.service._clock = Mock(side_effect=[10, 20, 50, 60, 90, 100])
        guard = patch('nayeon.services.windows_desktop._WindowsNative',
                      side_effect=AssertionError('LIVE TARGET FACADE FORBIDDEN'))
        self.target_factory = guard.start()
        self.addCleanup(guard.stop)

    def test_inserted_verified_original_target_exact_read_order_no_retry(self):
        calls = Mock()
        for name in ('context', 'foreground', 'identity'):
            calls.attach_mock(getattr(self.native, name), name)
        calls.attach_mock(self.service._clock, 'clock')
        def send(*args):
            calls.reset_mock()
            return 3
        self.effect_native._send_input.side_effect = send
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(self.service, 'verify_target', wraps=self.service.verify_target) as verify:
                receipt = self.effect_once(invocation, operation)
                verify.assert_called_once_with(operation.target)
                observed = invocation._post_observation
                self.assertIs(observed.status, V.VERIFIED)
                self.assertEqual((receipt.status, receipt.attempted, receipt.inserted), (E.INSERTED, True, 3))
                self.assertFalse(self.effect_once(invocation, operation).attempted)
                self.assertIs(invocation._post_observation, observed)
                verify.assert_called_once()
            self.assert_cleared(invocation)
        self.assertEqual([c[0] for c in calls.mock_calls],
                         ['clock', 'context', 'foreground', 'identity', 'identity', 'foreground', 'context', 'clock'])
        self.assertEqual([c.args for c in self.native.identity.call_args_list], [(b.I.hwnd,)] * 2)
        self.effect_native._send_input.assert_called_once()
        self.target_factory.assert_not_called()
        self.assertEqual(self.hit_native.window_at.call_count, 4)
        self.assertEqual(self.metrics.metric.call_count, 4)

    def test_changed_unavailable_failed_and_expired_observation_preserves_inserted(self):
        for gate, expected in (('foreground', V.NOT_VERIFIED), ('identity', V.NOT_VERIFIED),
                               ('error', V.INDETERMINATE), ('invalid', V.INDETERMINATE),
                               ('age', V.INDETERMINATE)):
            self.setUp()
            def send(*args):
                if gate == 'foreground':
                    self.native.foreground.return_value = b.I.hwnd + 1
                elif gate == 'identity':
                    self.native.identity.return_value = replace(b.I, executable='changed.exe')
                elif gate == 'error':
                    self.native.identity.side_effect = RuntimeError('PRIVATE_READ_SECRET')
                elif gate == 'invalid':
                    self.native.identity.return_value = None
                else:
                    self.service._clock.side_effect = [MAX_AGE_NS + 21, MAX_AGE_NS + 22]
                return 3
            self.effect_native._send_input.side_effect = send
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                receipt = self.effect_once(invocation, operation)
                self.assertEqual((receipt.status, receipt.inserted), (E.INSERTED, 3))
                self.assertIs(invocation._post_observation.status, expected)
                self.assert_cleared(invocation)
            self.effect_native._send_input.assert_called_once()

    def test_partial_and_indeterminate_attempts_observed_once(self):
        for count, status in ((1, E.PARTIAL), (2, E.PARTIAL), (0, E.INDETERMINATE),
                              (RuntimeError('PRIVATE_EFFECT_SECRET'), E.INDETERMINATE)):
            self.setUp()
            if isinstance(count, Exception):
                self.effect_native._send_input.side_effect = count
            else:
                self.effect_native._send_input.return_value = count
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(self.service, 'verify_target', wraps=self.service.verify_target) as verify:
                    receipt = self.effect_once(invocation, operation)
                    verify.assert_called_once_with(operation.target)
                self.assertEqual((receipt.status, receipt.attempted), (status, True))
                self.assertIs(invocation._post_observation.status, V.VERIFIED)
            self.effect_native._send_input.assert_called_once()

    def test_not_attempted_no_post_observation(self):
        for gate in ('permission', 'mapping', 'effect_setup'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                if gate == 'permission':
                    self.permissions.revoke(self.capability.name)
                elif gate == 'mapping':
                    self.metrics.metric.side_effect = [0, 0, 0, 0]
                else:
                    object.__setattr__(self.effect, '_platform', 'unsupported')
                with patch.object(self.service, 'verify_target') as verify:
                    receipt = self.effect_once(invocation, operation)
                    verify.assert_not_called()
                self.assertIs(receipt.status, E.NOT_ATTEMPTED)
                self.assertIsNone(invocation._post_observation)
            self.effect_native._send_input.assert_not_called()
            self.assertFalse(any(event.event_type is A.POINTER_POST_OBSERVATION_OUTCOME for event in self.audit.all()))

    def test_exact_receipt_preserved_on_verification_exception(self):
        receipt = _PointerEffectReceipt(E.INSERTED, True, 3)
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(_PointerEffectService, '_insert', return_value=receipt), patch.object(
                    self.service, 'verify_target', side_effect=RuntimeError('PRIVATE_OBSERVATION_SECRET')) as verify:
                self.assertIs(self.effect_once(invocation, operation), receipt)
                verify.assert_called_once_with(operation.target)
            self.assertIs(invocation._post_observation.status, V.INDETERMINATE)

    def test_effect_seam_exception_still_observed(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(_PointerEffectService, '_insert', side_effect=RuntimeError('PRIVATE_SEAM')), patch.object(
                    self.service, 'verify_target', wraps=self.service.verify_target) as verify:
                receipt = self.effect_once(invocation, operation)
                verify.assert_called_once_with(operation.target)
            self.assertEqual((receipt.status, receipt.attempted, receipt.inserted), (E.INDETERMINATE, True, None))
            self.assertIs(invocation._post_observation.status, V.VERIFIED)

    def test_exact_target_result_validation(self):
        class Result(_TargetVerificationResult):
            pass
        malformed = _TargetVerificationResult(V.VERIFIED)
        object.__setattr__(malformed, 'status', 'verified')
        for result in (None, Mock(status=V.VERIFIED), Result(V.VERIFIED), malformed):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(self.service, 'verify_target', return_value=result) as verify:
                    receipt = self.effect_once(invocation, operation)
                    verify.assert_called_once()
                self.assertIs(receipt.status, E.INSERTED)
                self.assertIs(invocation._post_observation.status, V.INDETERMINATE)

    def test_post_effect_binding_service_and_registry_tamper(self):
        for gate in ('service', 'operation', 'point', 'registry'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                def send(*args):
                    if gate == 'service':
                        invocation._service = _TargetVerificationService(native=self.native, platform='win32')
                    elif gate == 'operation':
                        object.__setattr__(operation, 'target', replace(operation.target))
                    elif gate == 'point':
                        object.__setattr__(operation.point, 'x', operation.point.x + 1)
                    else:
                        self.registry.unregister(self.capability.name)
                    return 3
                self.effect_native._send_input.side_effect = send
                with patch.object(_TargetVerificationService, 'verify_target') as verify:
                    receipt = self.effect_once(invocation, operation)
                    verify.assert_not_called()
                self.assertIs(receipt.status, E.INSERTED)
                self.assertIs(invocation._post_observation.status, V.INDETERMINATE)

    def test_tamper_during_verification(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            def verify(target):
                object.__setattr__(operation.target, 'acquired_to_ns', 21)
                return _TargetVerificationResult(V.VERIFIED)
            with patch.object(self.service, 'verify_target', side_effect=verify) as check:
                receipt = self.effect_once(invocation, operation)
                check.assert_called_once()
            self.assertIs(receipt.status, E.INSERTED)
            self.assertIs(invocation._post_observation.status, V.INDETERMINATE)

    def test_audit_cleanup_failures_preserve_both_evidence_categories(self):
        for gate in ('post_audit', 'all_post_audit', 'cleanup'):
            self.setUp()
            original = self.audit.record
            def record(event, **kwargs):
                if (event is A.POINTER_POST_OBSERVATION_OUTCOME
                        or (gate == 'all_post_audit' and self.effect_native._send_input.called)):
                    raise OSError('PRIVATE_AUDIT_SECRET')
                return original(event, **kwargs)
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(self.audit, 'record', side_effect=record), patch.object(
                        self.confirmation, 'reject', side_effect=RuntimeError('PRIVATE_CLEANUP_SECRET')
                        if gate == 'cleanup' else None, wraps=self.confirmation.reject):
                    receipt = self.effect_once(invocation, operation)
                self.assertEqual((receipt.status, receipt.inserted), (E.INSERTED, 3))
                observed = invocation._post_observation
                self.assertIs(observed.status, V.VERIFIED)
                self.assert_cleared(invocation)
            self.assertIs(invocation._post_observation, observed)

    def test_separate_sanitized_audit_no_semantic_success(self):
        with self.invocation() as invocation:
            operation, confirmation = self.prepare(invocation)
            self.effect_once(invocation, operation)
        events = self.audit.all()
        post = [event for event in events if event.event_type is A.POINTER_POST_OBSERVATION_OUTCOME]
        effect = [event for event in events if event.event_type is A.POINTER_EFFECT_OUTCOME]
        self.assertEqual([(event.outcome, event.details) for event in post], [('verified', {})])
        self.assertEqual([(event.outcome, event.details) for event in effect], [('inserted', {})])
        self.assertEqual(post[0].message, 'Original target post-effect equality sampled; UI result unverified.')
        self.assertEqual(post[0].capability, self.capability.name)
        for private in (confirmation.token, b.I.executable, b.I.window_class,
                        str(b.POINT[0]), str(b.POINT[1]), 'PRIVATE_', 'clicked successfully'):
            self.assertNotIn(private, repr(events))
        self.assertFalse(any(event.event_type in (A.EXECUTION_SUCCEEDED, A.UNDO_REGISTERED) for event in events))

    def test_post_observation_boundary_failure_keeps_receipt(self):
        class Result(_PointerPostObservationResult):
            pass
        malformed = _PointerPostObservationResult(V.VERIFIED)
        object.__setattr__(malformed, 'status', 'verified')
        for result in (Mock(status=V.VERIFIED), object.__new__(Result), malformed,
                       RuntimeError('PRIVATE_POST_BOUNDARY')):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(_PointerInvocation, '_observe_after_effect',
                                  side_effect=result if isinstance(result, Exception) else None,
                                  return_value=result) as observe:
                    receipt = self.effect_once(invocation, operation)
                    observe.assert_called_once_with(operation)
                self.assertEqual((receipt.status, receipt.inserted), (E.INSERTED, 3))
                self.assertIs(invocation._post_observation.status, V.INDETERMINATE)
                self.assert_cleared(invocation)
            self.effect_native._send_input.assert_called_once()

    def test_approve_readonly_without_post_observation(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(self.service, 'verify_target') as verify:
                result = invocation.approve(operation, target=operation.target, action=self.action, point=self.point)
                verify.assert_not_called()
            self.assertIs(result.status, V.VERIFIED)
            self.assertIsNone(invocation._post_observation)
            self.assertFalse(self.effect_once(invocation, operation).attempted)
        self.effect_native._send_input.assert_not_called()
        self.metrics.metric.assert_not_called()


class PostObservationContractTests(unittest.TestCase):
    def test_immutable_redacted_local_only_exact_result(self):
        result = _PointerPostObservationResult(V.VERIFIED)
        self.assertEqual([field.name for field in fields(result)], ['status'])
        self.assertFalse(hasattr(result, '__dict__'))
        self.assertEqual(repr(result), '_PointerPostObservationResult(<private>)')
        self.assertEqual(str(result), repr(result))
        with self.assertRaises(FrozenInstanceError):
            result.status = V.NOT_VERIFIED
        for export in (copy, deepcopy, pickle.dumps, json.dumps):
            with self.assertRaises(TypeError):
                export(result)
        for value in (True, 'verified', Mock(), None):
            with self.assertRaises(TypeError):
                _PointerPostObservationResult(value)
        class Result(_PointerPostObservationResult):
            pass
        with self.assertRaises(TypeError):
            Result()
        for name in ('target', 'binding', 'receipt', 'succeeded', 'ui_success', 'undo'):
            self.assertFalse(hasattr(result, name))

    def test_source_guards_private_route_no_alternate_mutation(self):
        root = Path(__file__).parents[1] / 'nayeon'
        source = (root / 'agent/pointer_binding.py').read_text()
        post = source.split('    def _observe_after_effect(', 1)[1].split('    def _execute_effect(', 1)[0]
        self.assertEqual(post.count('.verify_target('), 1)
        self.assertNotIn('acquire_target', post)
        self.assertNotIn('_insert', post)
        self.assertIn('__all__ = ()', source)
        for path in (root / 'agent/pointer_binding.py', root / 'services/pointer_effect.py'):
            for forbidden in ('SetCursorPos', 'mouse_event', 'keybd_event', 'pyautogui',
                              'SetForegroundWindow', 'AttachThreadInput', 'sleep(', 'OCR', 'UIA',
                              'screenshot', 'double_click', 'right_click', 'scroll(', 'keyboard.'):
                self.assertNotIn(forbidden, path.read_text())
        self.assertEqual((root / 'services/pointer_effect.py').read_text().count('.SendInput'), 1)
        for directory in ('capabilities', 'intent', 'runtime'):
            for path in (root / directory).rglob('*.py'):
                self.assertNotIn('PostObservation', path.read_text())
                self.assertNotIn('_observe_after_effect', path.read_text())
        self.assertFalse(any('observe' in name and not name.startswith('_') for name in vars(_PointerInvocation)))
