"""Phase 6.13 fake-only tests; NO LIVE NATIVE SMOKE AUTHORIZED."""
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path
import json
import pickle
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.pointer_binding import (
    _PointerInvocation, _PointerPostObservationResult, _PointerVerificationProvider, _REQUEST,
)
from nayeon.agent.executor import ExecutionResult, ExecutionStatus
from nayeon.audit.service import AuditEventType as A
from nayeon.services.pointer_effect import _EffectStatus as E, _PointerEffectReceipt, _PointerEffectService
from nayeon.verification.contract import VerificationProvider, VerificationResult, VerificationStatus as V
from nayeon.verification.service import VerificationService
from tests import test_pointer_binding as b
from tests import test_pointer_post_observation as p

CLAIM = (
    "The complete approved three-record input batch was inserted, and the bounded "
    "post-effect sample matched original-target identity/context and foreground "
    "within the original-binding age window; UI/task result unverified."
)


class ProviderTests(unittest.TestCase):
    def provider(self):
        return _PointerVerificationProvider(
            _PointerEffectReceipt(E.INSERTED, True, 3), _PointerPostObservationResult(V.VERIFIED))

    def verify(self, provider):
        return VerificationService().verify(provider, request=_REQUEST, output=None)

    def test_exact_complete_matrix_and_one_use(self):
        for effect, attempted, count, expected in (
                (E.INSERTED, True, 3, (V.VERIFIED, V.NOT_VERIFIED, V.INDETERMINATE)),
                (E.PARTIAL, True, 1, (V.NOT_VERIFIED,) * 3),
                (E.PARTIAL, True, 2, (V.NOT_VERIFIED,) * 3),
                (E.INDETERMINATE, True, 0, (V.INDETERMINATE,) * 3),
                (E.INDETERMINATE, True, None, (V.INDETERMINATE,) * 3),
                (E.NOT_ATTEMPTED, False, None, (V.INDETERMINATE,) * 3)):
            for observed, status in zip((V.VERIFIED, V.NOT_VERIFIED, V.INDETERMINATE), expected):
                with self.subTest(effect=effect, count=count, observation=observed):
                    provider = _PointerVerificationProvider(
                        _PointerEffectReceipt(effect, attempted, count), _PointerPostObservationResult(observed))
                    self.assertIsInstance(provider, VerificationProvider)
                    result = self.verify(provider)
                    self.assertIs(type(result), VerificationResult)
                    self.assertIs(result.status, status)
                    self.assertEqual(result.evidence, {})
                    wrapped = ExecutionResult(ExecutionStatus.EXECUTED, 'fake', 'returned', verification=result)
                    self.assertIs(wrapped.verification, result)
                    self.assertEqual(deepcopy(result), result)
                    self.assertIn('UI/task result unverified.', result.reason)
                    if status is V.VERIFIED:
                        self.assertEqual(result.reason, CLAIM)
                    self.assertIs(self.verify(provider).status, V.INDETERMINATE)

    def test_missing_malformed_subclass_and_uninitialized(self):
        class Receipt(_PointerEffectReceipt):
            pass
        class Observation(_PointerPostObservationResult):
            pass
        for attr, values in (
                ('_receipt', (None, {}, Mock(status=E.INSERTED), object.__new__(Receipt),
                              object.__new__(_PointerEffectReceipt))),
                ('_observation', (None, {}, Mock(status=V.VERIFIED), object.__new__(Observation),
                                  object.__new__(_PointerPostObservationResult)))):
            for bad in values:
                provider = self.provider()
                object.__setattr__(provider, attr, bad)
                self.assertIs(self.verify(provider).status, V.INDETERMINATE)
                with self.assertRaises((TypeError, AttributeError)):
                    _PointerVerificationProvider(provider._receipt, provider._observation)

    def test_tamper_including_valid_status_and_same_value_replacement(self):
        for attr, field, value in (('_receipt', 'status', 'inserted'), ('_receipt', 'inserted', True),
                ('_receipt', 'inserted', 2), ('_receipt', 'attempted', 1),
                ('_observation', 'status', 'verified'), ('_observation', 'status', V.NOT_VERIFIED)):
            provider = self.provider()
            object.__setattr__(getattr(provider, attr), field, value)
            self.assertIs(self.verify(provider).status, V.INDETERMINATE)
        for attr in ('_receipt', '_observation'):
            provider = self.provider()
            object.__setattr__(provider, attr, getattr(self.provider(), attr))
            self.assertIs(self.verify(provider).status, V.INDETERMINATE)

    def test_request_output_exception_and_local_only(self):
        for request, output in (('different', None), (_REQUEST, {}), (None, None)):
            self.assertIs(VerificationService().verify(self.provider(), request=request, output=output).status,
                          V.INDETERMINATE)
        provider = self.provider()
        with patch.object(_PointerVerificationProvider, '_evidence_snapshot',
                          side_effect=RuntimeError('PRIVATE_EVIDENCE_SECRET')):
            result = self.verify(provider)
        self.assertIs(result.status, V.INDETERMINATE)
        self.assertNotIn('PRIVATE', repr(result))
        self.assertEqual(repr(provider), '_PointerVerificationProvider(<private>)')
        self.assertFalse(hasattr(provider, '__dict__'))
        for export in (copy, deepcopy, pickle.dumps, json.dumps):
            with self.assertRaises(TypeError):
                export(provider)
        with self.assertRaises(FrozenInstanceError):
            provider._receipt = None
        class Provider(_PointerVerificationProvider):
            pass
        with self.assertRaises(TypeError):
            Provider(provider._receipt, provider._observation)


class IntegrationTests(unittest.TestCase):
    invocation = p.PostObservationTests.invocation
    prepare = p.PostObservationTests.prepare
    effect_once = p.PostObservationTests.effect_once
    assert_cleared = p.PostObservationTests.assert_cleared
    setUp = p.PostObservationTests.setUp

    def test_standard_service_exact_claim_no_extra_reads_or_effects_and_no_reuse(self):
        with self.invocation() as invocation:
            operation, confirmation = self.prepare(invocation)
            with patch.object(self.executor._verification, 'verify',
                              wraps=self.executor._verification.verify) as bridge:
                receipt = self.effect_once(invocation, operation)
                bridge.assert_called_once()
                provider = bridge.call_args.args[0]
                self.assertIs(type(provider), _PointerVerificationProvider)
                self.assertEqual(bridge.call_args.kwargs, {'request': _REQUEST, 'output': None})
                self.assertIs(provider._receipt, receipt)
                self.assertIs(provider._observation, invocation._post_observation)
                result = invocation._verification
                self.assertIs(type(result), VerificationResult)
                self.assertIs(result.status, V.VERIFIED)
                self.assertEqual(result.reason, CLAIM)
                self.assert_cleared(invocation)
                counts = (self.native.context.call_count, self.native.foreground.call_count,
                          self.native.identity.call_count, self.hit_native.window_at.call_count,
                          self.metrics.metric.call_count)
                self.assertEqual(counts, (6, 6, 6, 4, 4))
                self.assertFalse(self.effect_once(invocation, operation).attempted)
                self.assertIs(invocation._verification, result)
                bridge.assert_called_once()
                self.assertEqual(counts, (self.native.context.call_count, self.native.foreground.call_count,
                                         self.native.identity.call_count, self.hit_native.window_at.call_count,
                                         self.metrics.metric.call_count))
            self.effect_native._send_input.assert_called_once()
            self.target_factory.assert_not_called()
        public = repr(result) + repr(self.audit.all()) + json.dumps(result.evidence)
        for secret in (confirmation.token, b.I.executable, b.I.window_class,
                       str(b.POINT[0]), str(b.POINT[1]), 'PRIVATE_', 'clicked successfully'):
            self.assertNotIn(secret, public)
        outcomes = [event for event in self.audit.all() if event.message ==
                    'Captured bounded pointer evidence assessed; UI/task result unverified.']
        self.assertEqual([(event.event_type, event.outcome, event.details) for event in outcomes],
                         [(A.VERIFICATION_OUTCOME, 'verified', {})])
        self.assertFalse(any(event.event_type in (A.EXECUTION_SUCCEEDED, A.UNDO_REGISTERED)
                             for event in self.audit.all()))

    def test_observation_and_effect_status_matrix(self):
        for count, observed, expected in ((3, V.VERIFIED, V.VERIFIED),
                (3, V.NOT_VERIFIED, V.NOT_VERIFIED), (3, V.INDETERMINATE, V.INDETERMINATE),
                (1, V.VERIFIED, V.NOT_VERIFIED), (2, V.INDETERMINATE, V.NOT_VERIFIED),
                (0, V.VERIFIED, V.INDETERMINATE), (None, V.NOT_VERIFIED, V.INDETERMINATE)):
            self.setUp()
            self.effect_native._send_input.return_value = count
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(_PointerInvocation, '_observe_after_effect',
                                  return_value=_PointerPostObservationResult(observed)) as observe:
                    receipt = self.effect_once(invocation, operation)
                observe.assert_called_once_with(operation)
                self.assertIs(invocation._post_observation.status, observed)
                self.assertIs(invocation._verification.status, expected)
                self.assertTrue(receipt.attempted)
                self.assert_cleared(invocation)
            self.effect_native._send_input.assert_called_once()

    def test_no_attempt_and_readonly_have_no_verified_claim(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            self.permissions.revoke(self.capability.name)
            with patch.object(self.service, 'verify_target') as observe:
                receipt = self.effect_once(invocation, operation)
                observe.assert_not_called()
            self.assertFalse(receipt.attempted)
            self.assertIsNone(invocation._post_observation)
            self.assertIs(invocation._verification.status, V.INDETERMINATE)
        self.effect_native._send_input.assert_not_called()
        self.setUp()
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(self.executor._verification, 'verify') as bridge:
                invocation.approve(operation, target=operation.target, action=operation.action, point=operation.point)
                bridge.assert_not_called()
            self.assertIs(invocation._verification.status, V.INDETERMINATE)
            self.assertIsNone(invocation._post_observation)
        self.effect_native._send_input.assert_not_called()

    def test_bridge_exception_invalid_result_and_binding_or_evidence_tamper(self):
        for gate in ('exception', 'invalid', 'operation', 'registry', 'receipt', 'observation'):
            self.setUp()
            original = self.executor._verification.verify
            def verify(provider, **kwargs):
                if gate == 'exception':
                    raise RuntimeError('PRIVATE_BRIDGE_SECRET')
                if gate == 'invalid':
                    return Mock(status=V.VERIFIED)
                result = original(provider, **kwargs)
                if gate == 'operation':
                    object.__setattr__(operation.point, 'x', operation.point.x + 1)
                elif gate == 'registry':
                    self.registry.unregister(self.capability.name)
                elif gate == 'receipt':
                    object.__setattr__(provider, '_receipt', _PointerEffectReceipt(E.INSERTED, True, 3))
                else:
                    object.__setattr__(provider, '_observation', _PointerPostObservationResult(V.VERIFIED))
                return result
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(self.executor._verification, 'verify', side_effect=verify) as bridge:
                    receipt = self.effect_once(invocation, operation)
                    bridge.assert_called_once()
                self.assertEqual((receipt.status, receipt.inserted), (E.INSERTED, 3))
                self.assertIs(invocation._post_observation.status, V.VERIFIED)
                self.assertIs(invocation._verification.status, V.INDETERMINATE)
                self.assertNotIn('PRIVATE', repr(invocation._verification))
                self.assert_cleared(invocation)

    def test_tamper_between_capture_and_bridge_and_audit_failure(self):
        for gate in ('receipt', 'observation', 'replace', 'audit_error'):
            self.setUp()
            original = self.audit.record
            receipt = _PointerEffectReceipt(E.PARTIAL, True, 1)
            def audit(event, **kwargs):
                if event is A.POINTER_POST_OBSERVATION_OUTCOME:
                    if gate == 'receipt':
                        object.__setattr__(receipt, 'status', E.INSERTED)
                        object.__setattr__(receipt, 'inserted', 3)
                    elif gate == 'observation':
                        object.__setattr__(invocation._post_observation, 'status', V.NOT_VERIFIED)
                    elif gate == 'replace':
                        invocation._post_observation = _PointerPostObservationResult(V.VERIFIED)
                    else:
                        raise OSError('PRIVATE_AUDIT_SECRET')
                return original(event, **kwargs)
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(_PointerEffectService, '_insert', return_value=receipt), patch.object(
                        self.audit, 'record', side_effect=audit):
                    returned = self.effect_once(invocation, operation)
                self.assertIs(returned, receipt)
                self.assertIs(invocation._verification.status,
                              V.NOT_VERIFIED if gate == 'audit_error' else V.INDETERMINATE)
                self.assert_cleared(invocation)

    def test_malformed_post_evidence_and_effect_exception_never_verified(self):
        class Observation(_PointerPostObservationResult):
            pass
        malformed = _PointerPostObservationResult(V.VERIFIED)
        object.__setattr__(malformed, 'status', 'verified')
        for bad in (None, Mock(status=V.VERIFIED), object.__new__(Observation), malformed,
                    RuntimeError('PRIVATE_POST_SECRET')):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(_PointerInvocation, '_observe_after_effect',
                                  side_effect=bad if isinstance(bad, Exception) else None,
                                  return_value=bad):
                    receipt = self.effect_once(invocation, operation)
                self.assertEqual((receipt.status, receipt.inserted), (E.INSERTED, 3))
                self.assertIs(invocation._post_observation.status, V.INDETERMINATE)
                self.assertIs(invocation._verification.status, V.INDETERMINATE)
                self.assert_cleared(invocation)
        self.setUp()
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(_PointerEffectService, '_insert', side_effect=RuntimeError('PRIVATE_EFFECT')):
                receipt = self.effect_once(invocation, operation)
            self.assertEqual((receipt.status, receipt.attempted), (E.INDETERMINATE, True))
            self.assertIs(invocation._post_observation.status, V.VERIFIED)
            self.assertIs(invocation._verification.status, V.INDETERMINATE)
            self.assert_cleared(invocation)

    def test_verification_audit_and_cleanup_errors_do_not_erase_evidence(self):
        for gate in ('audit', 'cleanup'):
            self.setUp()
            original = self.audit.record
            def audit(event, **kwargs):
                if kwargs.get('message') == 'Captured bounded pointer evidence assessed; UI/task result unverified.':
                    raise OSError('PRIVATE_AUDIT')
                return original(event, **kwargs)
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(self.audit, 'record', side_effect=audit), patch.object(
                        self.confirmation, 'reject', side_effect=RuntimeError('PRIVATE_CLEANUP')
                        if gate == 'cleanup' else None, wraps=self.confirmation.reject):
                    receipt = self.effect_once(invocation, operation)
                self.assertEqual((receipt.status, receipt.inserted), (E.INSERTED, 3))
                self.assertIs(invocation._post_observation.status, V.VERIFIED)
                self.assertIs(invocation._verification.status, V.VERIFIED)
                self.assert_cleared(invocation)


class SourceBoundaryTests(unittest.TestCase):
    def test_no_new_native_read_mutation_public_route_or_semantic_claim(self):
        root = Path(__file__).parents[1] / 'nayeon'
        source = (root / 'agent/pointer_binding.py').read_text()
        provider = source.split('class _PointerVerificationProvider(', 1)[1].split('\ndef _snapshot(', 1)[0]
        bridge = source.split('    def _verify_captured_effect(', 1)[1].split('    def _consume(', 1)[0]
        for forbidden in ('verify_target(', 'acquire_target(', 'validate_hit(', 'normalize(', '_insert(',
                          'SendInput', 'WinDLL', 'SetCursorPos', 'SetForegroundWindow', 'sleep(',
                          'pyautogui', 'mouse_event', 'screenshot', 'ui_success', 'semantic_success'):
            self.assertNotIn(forbidden, provider + bridge)
        self.assertIn('self._executor._verification.verify(', bridge)
        self.assertIn('__all__ = ()', source)
        for directory in ('capabilities', 'intent', 'runtime'):
            for path in (root / directory).rglob('*.py'):
                self.assertNotIn('_PointerVerificationProvider', path.read_text())
                self.assertNotIn('_verify_captured_effect', path.read_text())
        for forbidden in ('control activated', 'button activated', 'task succeeded', 'click succeeded',
                          'clicked successfully', 'delivered successfully'):
            self.assertNotIn(forbidden, provider.lower())
