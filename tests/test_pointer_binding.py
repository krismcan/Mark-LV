"""Deterministic Phase 6.6 tests; no live desktop IO."""
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
import pickle
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor
from nayeon.agent.pointer_binding import _PointerAction, _PointerActionKind, _PointerInvocation, _PointerOperation
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode
from nayeon.services.target_validation import _TargetBinding, _TargetVerificationService
from nayeon.services.window_focus import _FocusBinding
from nayeon.services.keyboard_text import _TextBinding
from nayeon.undo.service import UndoService
from tests.test_foreground_observation import CONTEXT as C, IDENTITY as I


class PointerBindingTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()
        self.capability = Capability('test_pointer_binding', 'Test only', ExecutionMode.LOCAL,
                                     'fake', requires_confirmation=True)
        self.implementation = Mock(spec=['execute'])
        self.registry.register(self.capability, self.implementation)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant(self.capability.name)
        self.policy = PolicyService(self.permissions)
        self.confirmation, self.audit, self.undo = ConfirmationService(), AuditService(), UndoService()
        self.executor = ActionExecutor(self.registry, self.policy, self.confirmation, self.audit, self.undo)
        self.native = Mock(spec=['context', 'foreground', 'identity'])
        self.native.context.return_value = C
        self.native.foreground.return_value = I.hwnd
        self.native.identity.return_value = I
        self.service = _TargetVerificationService(native=self.native, platform='win32',
                                                  clock=Mock(side_effect=[10, 20]))
        self.action = _PointerAction()

    def invocation(self):
        return self.executor._pointer_invocation(self.capability, service=self.service)

    def assert_cleared(self, invocation):
        for name in ('_operation', '_target', '_action', '_snapshot', '_confirmation', '_service'):
            self.assertIsNone(getattr(invocation, name))
        self.assertTrue(invocation._closed)
        self.assertEqual(self.confirmation._pending, {})
        self.assertEqual(self.confirmation._bindings, {})
        self.implementation.execute.assert_not_called()
        self.assertEqual(self.undo.count(), 0)

    def test_exact_service_target_action_parameters_accepted_once(self):
        with self.invocation() as invocation, patch.object(self.service, 'verify_target') as verify:
            operation, confirmation = invocation.prepare(self.action)
            self.assertEqual(operation.target, _TargetBinding(I, C, 10, 20))
            self.assertIs(operation.action, self.action)
            self.assertEqual(operation.action.parameters, ())
            self.assertIs(self.confirmation._bindings[confirmation.token], operation)
            self.assertTrue(invocation.approve(operation, target=operation.target, action=self.action))
            self.assertFalse(invocation.approve(operation, target=operation.target, action=self.action))
            verify.assert_not_called()
        self.assertEqual(self.native.foreground.call_count, 2)
        self.assert_cleared(invocation)

    def test_reconstruction_or_substitution_rejected(self):
        for substitution in ('target_copy', 'target_changed', 'action_copy', 'operation_copy'):
            with self.subTest(substitution=substitution):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = invocation.prepare(self.action)
                    target, action, candidate = operation.target, self.action, operation
                    if substitution == 'target_copy':
                        target = replace(target)
                    elif substitution == 'target_changed':
                        target = replace(target, acquired_to_ns=21)
                    elif substitution == 'action_copy':
                        action = _PointerAction()
                    else:
                        candidate = _PointerOperation(target, action)
                    self.assertFalse(invocation.approve(candidate, target=target, action=action))
                    self.assert_cleared(invocation)

    def test_post_prepare_tampering_rejected(self):
        for tampering in ('parameters', 'kind', 'timestamp', 'bool_timestamp', 'identity', 'target', 'action'):
            with self.subTest(tampering=tampering):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = invocation.prepare(self.action)
                    if tampering == 'parameters':
                        object.__setattr__(self.action, 'parameters', (True,))
                    elif tampering == 'kind':
                        object.__setattr__(self.action, 'kind', 'single_left_click')
                    elif tampering in ('timestamp', 'bool_timestamp'):
                        object.__setattr__(operation.target, 'acquired_to_ns', True if tampering == 'bool_timestamp' else 21)
                    elif tampering == 'identity':
                        object.__setattr__(operation.target, 'identity', replace(I, executable='changed.exe'))
                    else:
                        object.__setattr__(operation, tampering,
                                           replace(operation.target) if tampering == 'target' else _PointerAction())
                    self.assertFalse(invocation.approve(operation, target=operation.target, action=operation.action))
                    self.assert_cleared(invocation)

    def test_action_exact_types_and_no_coordinate_parameters(self):
        for kind in (True, 1, 'single_left_click', None, Mock()):
            with self.assertRaises(TypeError):
                _PointerAction(kind)
        for parameters in (True, 1, [], {}, None, ''):
            with self.assertRaises(TypeError):
                _PointerAction(parameters=parameters)
        for parameters in ((True,), (1,), ((10, 20),), ('left',)):
            with self.assertRaises(ValueError):
                _PointerAction(parameters=parameters)
        self.assertEqual(list(_PointerActionKind), [_PointerActionKind.SINGLE_LEFT_CLICK])

    def test_legacy_or_malformed_target_cannot_construct_operation(self):
        for target in (None, {}, _FocusBinding(I, C), _TextBinding(_FocusBinding(I, C), 'test')):
            with self.assertRaises(TypeError):
                _PointerOperation(target, self.action)
        self.assertEqual(self.native.mock_calls, [])

    def test_frozen_slotted_redacted_no_copy_pickle_json_import(self):
        with self.invocation() as invocation:
            operation, _ = invocation.prepare(self.action)
            for value in (self.action, operation, invocation):
                self.assertFalse(hasattr(value, '__dict__'))
                self.assertEqual(repr(value), type(value).__name__ + '(<private>)')
                self.assertEqual(str(value), repr(value))
                for exporter in (copy, deepcopy, pickle.dumps, json.dumps):
                    with self.assertRaises(TypeError):
                        exporter(value)
            with self.assertRaises(FrozenInstanceError):
                self.action.parameters = (1,)
            with self.assertRaises(FrozenInstanceError):
                operation.target = None
            self.assertFalse(hasattr(operation, 'from_dict'))

    def test_construction_invalid_action_no_desktop_reads(self):
        with self.invocation() as invocation:
            self.assertEqual(self.native.mock_calls, [])
            self.service._clock.assert_not_called()
            with self.assertRaisesRegex(ValueError, '^Pointer binding preparation failed.$'):
                invocation.prepare({'kind': 'single_left_click'})
            self.assert_cleared(invocation)
        self.assertEqual(self.native.mock_calls, [])

    def test_permission_denial_policy_block_precede_acquisition(self):
        for denial in ('permission', 'policy'):
            with self.subTest(denial=denial):
                self.setUp()
                if denial == 'permission':
                    self.permissions.revoke(self.capability.name)
                else:
                    self.policy._blocked_capabilities.add(self.capability.name)
                with self.invocation() as invocation:
                    with self.assertRaises(ValueError):
                        invocation.prepare(self.action)
                    self.assert_cleared(invocation)
                self.assertEqual(self.native.mock_calls, [])
                self.assertEqual([e.event_type for e in self.audit.all()], [AuditEventType.POLICY_DECISION])

    def test_policy_acquisition_confirmation_recheck_order(self):
        calls = Mock()
        with patch.object(self.policy, 'evaluate', wraps=self.policy.evaluate) as policy, \
                patch.object(self.service, 'acquire_target', wraps=self.service.acquire_target) as acquire, \
                patch.object(self.confirmation, 'create', wraps=self.confirmation.create) as create, \
                patch.object(self.confirmation, 'approve', wraps=self.confirmation.approve) as approve:
            for name, mock in (('policy', policy), ('acquire', acquire), ('create', create), ('approve', approve)):
                calls.attach_mock(mock, name)
            with self.invocation() as invocation:
                operation, _ = invocation.prepare(self.action)
                self.assertTrue(invocation.approve(operation, target=operation.target, action=self.action))
        self.assertEqual([c[0] for c in calls.mock_calls], ['policy', 'acquire', 'create', 'approve', 'policy'])

    def test_permission_revocation_and_expiry_fail_closed(self):
        for denial in ('permission', 'expiry'):
            with self.subTest(denial=denial):
                self.setUp()
                with self.invocation() as invocation:
                    operation, confirmation = invocation.prepare(self.action)
                    if denial == 'permission':
                        self.permissions.revoke(self.capability.name)
                    else:
                        self.confirmation._pending[confirmation.token] = replace(
                            confirmation, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
                    self.assertFalse(invocation.approve(operation, target=operation.target, action=self.action))
                    self.assert_cleared(invocation)

    def test_legacy_confirmation_cannot_approve_private_operation(self):
        with self.invocation() as invocation:
            operation, confirmation = invocation.prepare(self.action)
            result = self.executor.approve_and_execute(confirmation.token, capability=self.capability,
                                                       request=confirmation.request)
            self.assertFalse(result.succeeded)
            self.assertFalse(invocation.approve(operation, target=operation.target, action=self.action))
            self.assert_cleared(invocation)

    def test_close_and_cross_invocation_reuse_rejected(self):
        with self.invocation() as invocation:
            operation, _ = invocation.prepare(self.action)
        self.assert_cleared(invocation)
        self.assertFalse(invocation.approve(operation, target=operation.target, action=self.action))
        self.setUp()
        with self.invocation() as next_invocation:
            next_invocation.prepare(self.action)
            self.assertFalse(next_invocation.approve(operation, target=operation.target, action=operation.action))
            self.assert_cleared(next_invocation)

    def test_second_prepare_fails_closed(self):
        with self.invocation() as invocation:
            invocation.prepare(self.action)
            with self.assertRaises(ValueError):
                invocation.prepare(self.action)
            self.assert_cleared(invocation)

    def test_acquisition_exception_sanitized_and_cleared(self):
        self.native.identity.side_effect = RuntimeError('PRIVATE_NATIVE_SECRET')
        with self.invocation() as invocation:
            with self.assertRaisesRegex(ValueError, '^Pointer binding preparation failed.$'):
                invocation.prepare(self.action)
            self.assert_cleared(invocation)
        self.assertNotIn('PRIVATE_NATIVE_SECRET', repr(self.audit.all()))

    def test_approval_exception_cleared(self):
        with self.invocation() as invocation:
            operation, _ = invocation.prepare(self.action)
            with patch.object(self.policy, 'evaluate', side_effect=RuntimeError('PRIVATE')):
                self.assertFalse(invocation.approve(operation, target=operation.target, action=self.action))
            self.assert_cleared(invocation)

    def test_lexical_exception_cleanup(self):
        with self.assertRaisesRegex(RuntimeError, 'caller'):
            with self.invocation() as invocation:
                invocation.prepare(self.action)
                raise RuntimeError('caller')
        self.assert_cleared(invocation)

    def test_registration_change_rejected(self):
        with self.invocation() as invocation:
            operation, _ = invocation.prepare(self.action)
            self.registry.unregister(self.capability.name)
            self.assertFalse(invocation.approve(operation, target=operation.target, action=self.action))
            self.assert_cleared(invocation)

    def test_reversible_or_unprotected_metadata_no_reads(self):
        for changes in ({'reversible': True}, {'requires_confirmation': False}):
            with self.subTest(changes=changes):
                self.setUp()
                self.capability = replace(self.capability, **changes)
                self.registry.unregister(self.capability.name)
                self.registry.register(self.capability, self.implementation)
                with self.invocation() as invocation:
                    with self.assertRaises(ValueError):
                        invocation.prepare(self.action)
                self.assertEqual(self.native.mock_calls, [])

    def test_public_evidence_no_private_fields_execution_or_undo(self):
        original_fields = set(vars(self.executor))
        with self.invocation() as invocation:
            operation, confirmation = invocation.prepare(self.action)
            self.assertTrue(invocation.approve(operation, target=operation.target, action=self.action))
        self.assertEqual(set(vars(self.executor)), original_fields)
        self.assertEqual(self.executor._structured_pending, {})
        for event in self.audit.all():
            self.assertEqual(event.details, {})
            self.assertNotIn(event.event_type, (AuditEventType.EXECUTION_STARTED,
                                               AuditEventType.EXECUTION_SUCCEEDED,
                                               AuditEventType.UNDO_REGISTERED))
        public = repr(self.audit.all()) + repr(confirmation)
        for private in (I.executable, I.window_class, 'acquired_from_ns', '_TargetBinding', 'coordinates'):
            self.assertNotIn(private, public)
        self.assert_cleared(invocation)

    def test_no_public_exports_or_native_mutation_methods(self):
        from nayeon.agent import pointer_binding
        self.assertEqual(pointer_binding.__all__, ())
        for cls in (_PointerAction, _PointerOperation, _PointerInvocation):
            for name in ('execute', 'click', 'move', 'focus', 'verify_target', 'to_dict', 'from_dict'):
                self.assertFalse(hasattr(cls, name))
        self.assertEqual([name for name in dir(ActionExecutor) if 'pointer' in name], ['_pointer_invocation'])
