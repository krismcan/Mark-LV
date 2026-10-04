"""Phase 6.11 injected native tests; NO LIVE EFFECT SMOKE AUTHORIZED."""
from copy import copy, deepcopy
import ctypes
from dataclasses import FrozenInstanceError, replace
import json
import pickle
import unittest
from tests.test_scoped_ui_element_observation import Harness as _UIAHarness
from unittest.mock import Mock, patch
from nayeon.services import pointer_effect as m
from nayeon.services.pointer_coordinates import _CoordinateEvidence
from nayeon.services.pointer_hit_validation import _ProposedPoint


class NativeEffectTests(unittest.TestCase):
    def setUp(self):
        self.native = Mock(spec=['_send_input'])
        self.native._send_input.return_value = 3
        self.service = m._PointerEffectService(native=self.native, platform='win32')
        self.evidence = _CoordinateEvidence(_ProposedPoint(0, 0), -1, -1, 3, 3, 32767, 32767)
        guard = patch.object(m, '_PointerEffectNative', side_effect=AssertionError('LIVE FACADE FORBIDDEN'))
        self.factory = guard.start()
        self.addCleanup(guard.stop)

    def test_exact_batch_order_fields_and_size(self):
        receipt = self.service._insert(self.evidence)
        self.assertIs(receipt.status, m._EffectStatus.INSERTED)
        self.native._send_input.assert_called_once()
        count, batch, size = self.native._send_input.call_args.args
        self.assertEqual((count, len(batch), size), (3, 3, ctypes.sizeof(m._INPUT)))
        self.assertEqual(size, 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)
        self.assertEqual([r.type for r in batch], [0, 0, 0])
        self.assertEqual([r.data.mi.dwFlags for r in batch], [0xC001, 2, 4])
        self.assertEqual([(r.data.mi.dx, r.data.mi.dy) for r in batch], [(32767, 32767), (0, 0), (0, 0)])
        for r in batch:
            self.assertEqual((r.data.mi.mouseData, r.data.mi.time, r.data.mi.dwExtraInfo), (0, 0, 0))
        self.factory.assert_not_called()

    def test_abi_field_offsets(self):
        wide = ctypes.sizeof(ctypes.c_void_p) == 8
        self.assertEqual(m._MOUSEINPUT.dwExtraInfo.offset, 24 if wide else 20)
        self.assertEqual(ctypes.sizeof(m._MOUSEINPUT), 32 if wide else 24)
        self.assertEqual(m._INPUT.data.offset, 8 if wide else 4)

    def test_endpoints(self):
        for x, y in ((0, 0), (65535, 65535), (0, 65535), (65535, 0)):
            self.native.reset_mock()
            evidence = _CoordinateEvidence(_ProposedPoint(x, y), 0, 0, 65536, 65536, x, y)
            self.service._insert(evidence)
            batch = self.native._send_input.call_args.args[1]
            self.assertEqual((batch[0].data.mi.dx, batch[0].data.mi.dy), (x, y))

    def test_counts_no_retry(self):
        for count, status in ((3, m._EffectStatus.INSERTED), (2, m._EffectStatus.PARTIAL),
                              (1, m._EffectStatus.PARTIAL), (0, m._EffectStatus.INDETERMINATE)):
            self.native.reset_mock()
            self.native._send_input.return_value = count
            receipt = self.service._insert(self.evidence)
            self.assertEqual((receipt.status, receipt.attempted, receipt.inserted), (status, True, count))
            self.native._send_input.assert_called_once()

    def test_exception(self):
        self.native._send_input.side_effect = RuntimeError('PRIVATE_NATIVE_SECRET')
        receipt = self.service._insert(self.evidence)
        self.assertEqual((receipt.status, receipt.attempted, receipt.inserted), (m._EffectStatus.INDETERMINATE, True, None))
        self.native._send_input.assert_called_once()
        self.assertNotIn('SECRET', repr(receipt))

    def test_malformed_native_result(self):
        class Int(int):
            pass
        for count in (True, False, -1, 4, 3.0, '3', None, Int(3), Mock()):
            self.native.reset_mock()
            self.native._send_input.return_value = count
            receipt = self.service._insert(self.evidence)
            self.assertEqual((receipt.status, receipt.inserted), (m._EffectStatus.INDETERMINATE, None))
            self.assertTrue(receipt.attempted)
            self.native._send_input.assert_called_once()

    def test_invalid_and_tampered_evidence(self):
        for evidence in (None, {}, (0, 0), Mock(normalized_x=0)):
            self.assertFalse(self.service._insert(evidence).attempted)
        for field, value in (('normalized_x', True), ('normalized_y', 65536), ('normalized_x', 0),
                             ('width', 0), ('point', _ProposedPoint(5, 5))):
            evidence = replace(self.evidence)
            object.__setattr__(evidence, field, value)
            self.assertFalse(self.service._insert(evidence).attempted)
        self.native._send_input.assert_not_called()

    def test_platform_and_layout(self):
        for platform in ('linux', 'darwin', '', True, 1):
            self.assertFalse(m._PointerEffectService(native=self.native, platform=platform)._insert(self.evidence).attempted)
        with patch.object(m.ctypes, 'sizeof', return_value=16):
            self.assertFalse(self.service._insert(self.evidence).attempted)
        self.factory.assert_not_called()
        self.native._send_input.assert_not_called()

    def test_factory_failure(self):
        self.factory.side_effect = OSError('PRIVATE_FACTORY')
        receipt = m._PointerEffectService(platform='win32')._insert(self.evidence)
        self.assertFalse(receipt.attempted)
        self.factory.assert_called_once_with()

    def test_receipt_invariants_and_subclass(self):
        for args in (('inserted', True, 3), (m._EffectStatus.INSERTED, 1, 3),
                     (m._EffectStatus.INSERTED, True, True), (m._EffectStatus.INSERTED, True, 2),
                     (m._EffectStatus.PARTIAL, True, 0), (m._EffectStatus.NOT_ATTEMPTED, False, 0),
                     (m._EffectStatus.INDETERMINATE, False, None), (m._EffectStatus.INSERTED, True, 4)):
            with self.assertRaises((TypeError, ValueError)):
                m._PointerEffectReceipt(*args)
        class Receipt(m._PointerEffectReceipt):
            pass
        with self.assertRaises(TypeError):
            Receipt()

    def test_privacy_freezing_serialization(self):
        receipt = self.service._insert(self.evidence)
        for value in (receipt, self.service):
            self.assertFalse(hasattr(value, '__dict__'))
            self.assertEqual(repr(value), type(value).__name__ + '(<private>)')
            self.assertEqual(str(value), repr(value))
            for export in (copy, deepcopy, pickle.dumps, json.dumps):
                with self.assertRaises(TypeError):
                    export(value)
        with self.assertRaises(FrozenInstanceError):
            receipt.inserted = 1


class NativeFacadeTests(unittest.TestCase):
    def test_signature_and_platform_guard_source_only_never_construct_facade(self):
        source = (Path(__file__).parents[1] / 'nayeon/services/pointer_effect.py').read_text()
        self.assertEqual(source.count('.SendInput'), 1)
        self.assertIn('self._send.argtypes = [ctypes.c_uint32, ctypes.POINTER(_INPUT), ctypes.c_int]', source)
        self.assertIn('self._send.restype = ctypes.c_uint32', source)
        self.assertIn('if sys.platform != "win32":', source)
        self.assertIn('native._send_input(3, records, ctypes.sizeof(_INPUT))', source)
        self.assertTrue(m._PointerEffectNative.__dataclass_params__.frozen)
        self.assertEqual(m._PointerEffectNative.__slots__, ('_send',))


from datetime import datetime, timedelta, timezone
from pathlib import Path
from nayeon.agent.pointer_binding import _PointerAction, _PointerOperation, _PointerEligibilityResult, _PointerInvocation
from nayeon.audit.service import AuditEventType
from nayeon.services.pointer_coordinates import _CoordinateResult, _PointerCoordinateService
from nayeon.services.pointer_hit_validation import _PointerHitValidationService
from nayeon.services.target_validation import MAX_AGE_NS
from nayeon.verification.contract import VerificationStatus as V
from tests import test_pointer_binding as b
_NORMALIZE = _PointerCoordinateService.normalize
_HIT = _PointerHitValidationService.validate_hit


class EffectIntegrationTests(unittest.TestCase):
    def setUp(self):
        b.PointerBindingTests.setUp(self)
        self.ui_element_service = _UIAHarness().service()
        self.metrics = Mock(spec=['metric'])
        self.metrics.metric.side_effect = [30000, 26000, 2000, 2000]
        self.coordinates = _PointerCoordinateService(native=self.metrics, platform='win32')
        self.effect_native = Mock(spec=['_send_input'])
        self.effect_native._send_input.return_value = 3
        self.effect = m._PointerEffectService(native=self.effect_native, platform='win32')
        guard = patch.object(m, '_PointerEffectNative', side_effect=AssertionError('LIVE FACADE FORBIDDEN'))
        self.factory = guard.start()
        self.addCleanup(guard.stop)

    def invocation(self):
        return self.executor._pointer_invocation(self.capability, service=self.service,
            hit_service=self.hit_service, coordinate_service=self.coordinates, effect_service=self.effect, ui_element_service=self.ui_element_service)

    def prepare(self, invocation):
        return invocation.prepare(self.action, self.point)

    def effect_once(self, invocation, operation):
        return invocation._execute_effect(operation, target=operation.target,
            action=operation.action, point=operation.point)

    def assert_cleared(self, invocation):
        b.PointerBindingTests.assert_cleared(self, invocation)
        self.assertIsNone(invocation._coordinate_service)
        self.assertIsNone(invocation._effect_service)
        self.factory.assert_not_called()

    def assert_no_effect(self):
        self.effect_native._send_input.assert_not_called()
        self.metrics.metric.assert_not_called()

    def test_order_original_point_once_and_fresh_mapping(self):
        calls = Mock()
        with patch.object(self.confirmation, 'approve', wraps=self.confirmation.approve) as approval, patch.object(self.policy, 'evaluate', wraps=self.policy.evaluate) as policy, patch.object(self.service, 'acquire_target', wraps=self.service.acquire_target) as target, patch.object(_PointerHitValidationService, 'validate_hit', autospec=True, side_effect=_HIT) as hit, patch.object(_PointerCoordinateService, 'normalize', autospec=True, side_effect=_NORMALIZE) as normalize:
            for name, mock in (('approval', approval), ('policy', policy), ('target', target), ('hit', hit), ('map', normalize), ('native', self.effect_native._send_input)):
                calls.attach_mock(mock, name)
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                self.assert_no_effect()
                receipt = self.effect_once(invocation, operation)
                self.assertIs(receipt.status, m._EffectStatus.INSERTED)
                self.assertFalse(self.effect_once(invocation, operation).attempted)
                normalize.assert_called_once_with(self.coordinates, self.point)
                self.assertIs(operation.point, self.point)
                self.assertEqual((operation.point.x, operation.point.y), b.POINT)
                self.assertEqual(operation.target.acquired_to_ns, 20)
                self.assert_cleared(invocation)
        self.assertEqual([c[0] for c in calls.mock_calls], ['policy', 'target', 'hit', 'approval', 'policy', 'target', 'hit', 'map', 'native'])
        self.assertEqual([c.args[0] for c in self.metrics.metric.call_args_list], [76, 77, 78, 79])
        batch = self.effect_native._send_input.call_args.args[1]
        self.assertEqual((batch[0].data.mi.dx, batch[0].data.mi.dy), (((b.POINT[0]-30000)*65535)//1999, ((b.POINT[1]-26000)*65535)//1999))

    def test_readonly_approval_cannot_be_reused_for_effect(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            result = invocation.approve(operation, target=operation.target, action=self.action, point=self.point)
            self.assertIs(result.status, V.VERIFIED)
            self.assertFalse(self.effect_once(invocation, operation).attempted)
        self.assert_no_effect()
        self.assert_cleared(invocation)

    def test_close_without_approval(self):
        with self.invocation() as invocation:
            self.prepare(invocation)
        self.assert_no_effect()
        self.assert_cleared(invocation)

    def test_counts_and_exception_no_retry(self):
        for count in (3, 2, 1, 0, RuntimeError('PRIVATE_EFFECT')):
            with self.subTest(count=repr(count)):
                self.setUp()
                if isinstance(count, Exception):
                    self.effect_native._send_input.side_effect = count
                else:
                    self.effect_native._send_input.return_value = count
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    receipt = self.effect_once(invocation, operation)
                    self.assertTrue(receipt.attempted)
                    self.assertEqual(receipt.inserted, None if isinstance(count, Exception) else count)
                    self.assertFalse(self.effect_once(invocation, operation).attempted)
                self.effect_native._send_input.assert_called_once()
                self.assert_cleared(invocation)
                self.assertNotIn('PRIVATE_EFFECT', repr(self.audit.all()))

    def test_policy_permission_registry_and_implementation_gates(self):
        for gate in ('permission', 'policy', 'registry', 'implementation'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                if gate == 'permission':
                    self.permissions.revoke(self.capability.name)
                elif gate == 'policy':
                    self.policy._blocked_capabilities.add(self.capability.name)
                else:
                    self.registry.unregister(self.capability.name)
                    if gate == 'implementation':
                        self.registry.register(self.capability, Mock(spec=['execute']))
                self.assertFalse(self.effect_once(invocation, operation).attempted)
            self.assert_no_effect()
            self.assert_cleared(invocation)

    def test_confirmation_expiry_rejection_consumption_and_binding(self):
        for gate in ('expired', 'rejected', 'consumed', 'binding'):
            self.setUp()
            with self.invocation() as invocation:
                operation, confirmation = self.prepare(invocation)
                if gate == 'expired':
                    self.confirmation._pending[confirmation.token] = replace(confirmation, expires_at=datetime.now(timezone.utc)-timedelta(seconds=1))
                elif gate == 'rejected':
                    self.confirmation.reject(confirmation.token)
                elif gate == 'consumed':
                    self.confirmation.approve(confirmation.token, capability=self.capability.name, request=confirmation.request, binding=operation)
                else:
                    self.confirmation._bindings[confirmation.token] = _PointerOperation(operation.target, self.action, self.point)
                self.assertFalse(self.effect_once(invocation, operation).attempted)
            self.assert_no_effect()
            self.assert_cleared(invocation)

    def test_substitution_and_snapshot_tamper(self):
        for gate in ('operation', 'target', 'action', 'point', 'x', 'parameters', 'timestamp'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                if gate == 'operation':
                    operation = _PointerOperation(operation.target, self.action, self.point)
                elif gate == 'target':
                    object.__setattr__(operation, 'target', replace(operation.target))
                elif gate == 'action':
                    object.__setattr__(operation, 'action', _PointerAction())
                elif gate == 'point':
                    object.__setattr__(operation, 'point', _ProposedPoint(*b.POINT))
                elif gate == 'x':
                    object.__setattr__(operation.point, 'x', operation.point.x+1)
                elif gate == 'parameters':
                    object.__setattr__(operation.action, 'parameters', (1,))
                else:
                    object.__setattr__(operation.target, 'acquired_to_ns', 21)
                self.assertFalse(self.effect_once(invocation, operation).attempted)
            self.assert_no_effect()
            self.assert_cleared(invocation)

    def test_eligibility_exact_verified_required(self):
        malformed = _PointerEligibilityResult()
        object.__setattr__(malformed, 'status', 'verified')
        for result in (_PointerEligibilityResult(V.NOT_VERIFIED), _PointerEligibilityResult(), Mock(status=V.VERIFIED), malformed):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(_PointerInvocation, '_eligible_now', return_value=result):
                    self.assertFalse(self.effect_once(invocation, operation).attempted)
            self.assert_no_effect()
            self.assert_cleared(invocation)

    def test_fresh_target_context_hit_stale_and_failure(self):
        for gate in ('target', 'context', 'hit', 'stale', 'error'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                if gate == 'target':
                    self.native.identity.return_value = replace(b.I, executable='changed.exe')
                elif gate == 'context':
                    self.native.context.return_value = replace(b.C, active=False)
                elif gate == 'hit':
                    self.hit_native.root.return_value = b.I.hwnd+1
                elif gate == 'stale':
                    self.hit_service._clock = Mock(return_value=60+MAX_AGE_NS+1)
                else:
                    self.native.foreground.side_effect = RuntimeError('PRIVATE_FRESH')
                self.assertFalse(self.effect_once(invocation, operation).attempted)
            self.assert_no_effect()
            self.assert_cleared(invocation)

    def test_mapping_unavailable_no_effect(self):
        for metrics in ((0, 0, 1, 1), (30000, 26000, 0, 2000), (True, 26000, 2000, 2000), (RuntimeError('PRIVATE_METRIC'),)):
            self.setUp()
            self.metrics.metric.side_effect = list(metrics)
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                self.assertFalse(self.effect_once(invocation, operation).attempted)
            self.effect_native._send_input.assert_not_called()
            self.assert_cleared(invocation)

    def test_mapping_result_and_evidence_tamper_or_substitution(self):
        for gate in ('fake', 'empty', 'point_copy', 'normalized', 'status', 'evidence'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                evidence = _CoordinateEvidence(self.point, 30000, 26000, 2000, 2000, ((b.POINT[0]-30000)*65535)//1999, ((b.POINT[1]-26000)*65535)//1999)
                mapped = _CoordinateResult(V.VERIFIED, evidence)
                if gate == 'fake':
                    mapped = Mock(status=V.VERIFIED)
                elif gate == 'empty':
                    mapped = _CoordinateResult()
                elif gate == 'point_copy':
                    object.__setattr__(evidence, 'point', _ProposedPoint(*b.POINT))
                elif gate == 'normalized':
                    object.__setattr__(evidence, 'normalized_x', True)
                elif gate == 'status':
                    object.__setattr__(mapped, 'status', 'verified')
                else:
                    object.__setattr__(mapped, 'evidence', {})
                with patch.object(_PointerCoordinateService, 'normalize', return_value=mapped):
                    self.assertFalse(self.effect_once(invocation, operation).attempted)
            self.effect_native._send_input.assert_not_called()
            self.assert_cleared(invocation)

    def test_tamper_during_mapping_rechecked(self):
        for gate in ('point', 'action', 'target', 'registry', 'service'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                def normalize(service, point):
                    mapped = _NORMALIZE(service, point)
                    if gate == 'point':
                        object.__setattr__(point, 'x', point.x+1)
                    elif gate == 'action':
                        object.__setattr__(operation, 'action', _PointerAction())
                    elif gate == 'target':
                        object.__setattr__(operation, 'target', replace(operation.target))
                    elif gate == 'service':
                        invocation._effect_service = Mock()
                    else:
                        self.registry.unregister(self.capability.name)
                    return mapped
                with patch.object(_PointerCoordinateService, 'normalize', autospec=True, side_effect=normalize):
                    self.assertFalse(self.effect_once(invocation, operation).attempted)
            self.effect_native._send_input.assert_not_called()
            self.assert_cleared(invocation)

    def test_malformed_effect_result_no_retry(self):
        malformed = m._PointerEffectReceipt(m._EffectStatus.INSERTED, True, 3)
        object.__setattr__(malformed, 'inserted', True)
        for result in (None, Mock(status=m._EffectStatus.INSERTED), malformed):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                with patch.object(m._PointerEffectService, '_insert', return_value=result) as insert:
                    receipt = self.effect_once(invocation, operation)
                self.assertEqual((receipt.status, receipt.attempted, receipt.inserted), (m._EffectStatus.INDETERMINATE, True, None))
                insert.assert_called_once()
            self.assert_cleared(invocation)

    def test_audit_sanitized_no_semantic_success_no_undo(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            self.effect_once(invocation, operation)
        effects = [e for e in self.audit.all() if e.event_type is AuditEventType.POINTER_EFFECT_OUTCOME]
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].outcome, 'inserted')
        for event in self.audit.all():
            self.assertEqual(event.details, {})
            self.assertNotIn(event.event_type, (AuditEventType.EXECUTION_SUCCEEDED, AuditEventType.UNDO_REGISTERED))
        for private in (b.I.executable, b.I.window_class, str(b.POINT[0]), str(b.POINT[1]), 'clicked successfully'):
            self.assertNotIn(private, repr(self.audit.all()))
        self.assert_cleared(invocation)

    def test_audit_failure_preserves_receipt(self):
        original = self.audit.record
        def record(event, **kwargs):
            if event is AuditEventType.POINTER_EFFECT_OUTCOME:
                raise OSError('PRIVATE_AUDIT')
            return original(event, **kwargs)
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(self.audit, 'record', side_effect=record):
                receipt = self.effect_once(invocation, operation)
            self.assertEqual((receipt.status, receipt.inserted), (m._EffectStatus.INSERTED, 3))
        self.effect_native._send_input.assert_called_once()
        self.assert_cleared(invocation)

    def test_untrusted_services_and_metadata(self):
        for coordinates, effect in ((Mock(), self.effect), (self.coordinates, Mock()), (self.coordinates, None)):
            with self.assertRaises(TypeError):
                with self.executor._pointer_invocation(self.capability, service=self.service, hit_service=self.hit_service, coordinate_service=coordinates, effect_service=effect, ui_element_service=self.ui_element_service):
                    pass
        for changes in ({'reversible': True}, {'requires_confirmation': False}):
            self.setUp()
            self.capability = replace(self.capability, **changes)
            self.registry.unregister(self.capability.name)
            self.registry.register(self.capability, self.implementation)
            with self.invocation() as invocation:
                with self.assertRaises(ValueError):
                    self.prepare(invocation)
            self.assert_no_effect()
            self.assert_cleared(invocation)

    def test_private_routes_and_no_alternate_mutation(self):
        self.assertEqual(m.__all__, ())
        self.assertEqual(
            {n for n in vars(m._PointerEffectService) if not n.startswith('_')}, set()
        )
        root = Path(__file__).parents[1]
        for path in (root/'nayeon/services/pointer_effect.py', root/'nayeon/agent/pointer_binding.py'):
            for forbidden in ('SetCursorPos', 'mouse_event', 'keybd_event', 'pyautogui', 'SetForegroundWindow', 'AttachThreadInput', 'GetCursorPos'):
                self.assertNotIn(forbidden, path.read_text())
        for directory in ('capabilities', 'intent', 'runtime'):
            for path in (root/'nayeon'/directory).rglob('*.py'):
                self.assertNotIn('pointer_effect', path.read_text())
        self.assertEqual([n for n in dir(type(self.executor)) if 'pointer' in n], ['_pointer_invocation'])



class EffectAdditionalContractTests(unittest.TestCase):
    setUp = NativeEffectTests.setUp

    def test_service_is_frozen_and_subclass_rejected(self):
        with self.assertRaises(FrozenInstanceError):
            self.service._native = Mock()
        with self.assertRaises(FrozenInstanceError):
            self.service._platform = 'linux'
        class Service(m._PointerEffectService):
            pass
        with self.assertRaises(TypeError):
            Service(native=self.native, platform='win32')
        self.native._send_input.assert_not_called()
        self.factory.assert_not_called()

    def test_batch_zero_padding_and_no_semantic_success_properties(self):
        receipt = self.service._insert(self.evidence)
        records = self.native._send_input.call_args.args[1]
        expected = (m._INPUT * 3)()
        expected[0].data.mi.dx = expected[0].data.mi.dy = 32767
        for record, flags in zip(expected, (0xC001, 2, 4)):
            record.data.mi.dwFlags = flags
        self.assertEqual(bytes(records), bytes(expected))
        for name in ('succeeded', 'verified', 'verification', 'ui_success', 'undo'):
            self.assertFalse(hasattr(receipt, name))
        self.native._send_input.assert_called_once()

    def test_evidence_subclasses_and_tampered_point_block(self):
        class Evidence(_CoordinateEvidence):
            pass
        self.assertFalse(self.service._insert(object.__new__(Evidence)).attempted)
        point = _ProposedPoint(0, 0)
        evidence = _CoordinateEvidence(point, -1, -1, 3, 3, 32767, 32767)
        object.__setattr__(point, 'x', True)
        self.assertFalse(self.service._insert(evidence).attempted)
        self.native._send_input.assert_not_called()

    def test_floor_normalization_and_one_cell_are_used_without_remapping(self):
        for point, geometry, normalized in (((1, 2), (0, 0, 3, 4), (32767, 43690)),
                                           ((-7, 9), (-7, 9, 1, 1), (0, 0))):
            self.native.reset_mock()
            evidence = _CoordinateEvidence(_ProposedPoint(*point), *geometry, *normalized)
            self.service._insert(evidence)
            records = self.native._send_input.call_args.args[1]
            self.assertEqual((records[0].data.mi.dx, records[0].data.mi.dy), normalized)
            self.native._send_input.assert_called_once()


if __name__ == '__main__':
    unittest.main()
