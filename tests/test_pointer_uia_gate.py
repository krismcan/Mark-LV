"""Phase 6.18 deterministic pre-effect gate tests; no live desktop effects."""
import ast
from dataclasses import fields, replace
import inspect
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

from nayeon.agent import pointer_binding as b
from nayeon.services import scoped_ui_element_observation as u
from nayeon.services.pointer_coordinates import _PointerCoordinateService
from nayeon.services.pointer_effect import _PointerEffectService, _EffectStatus as E
from nayeon.services.pointer_hit_validation import _PointerHitValidationService, _ProposedPoint
from nayeon.services.ui_element_observation import _CONTROL_TYPES
from nayeon.verification.contract import VerificationStatus as V
from tests import test_pointer_effect as e
from tests.test_pointer_verification import CLAIM
from tests.test_scoped_ui_element_observation import Harness

HEAD = '18e69f8eb2590a68aa0651f264aec123b9b316a1'
ROOT = Path(__file__).resolve().parents[1]


class GateTests(unittest.TestCase):
    invocation = e.EffectIntegrationTests.invocation
    prepare = e.EffectIntegrationTests.prepare
    effect_once = e.EffectIntegrationTests.effect_once

    def setUp(self):
        e.EffectIntegrationTests.setUp(self)
        self.harness = Harness()
        self.ui_element_service = self.harness.service()
        self.service._clock.side_effect = [10, 20, 50, 60, 90, 100]
        for module, factory in (
                ('ui_element_observation', '_UIANative'),
                ('dpi_execution_context', '_DpiExecutionNative'),
                ('pointer_coordinates', '_CoordinateNative'),
                ('windows_desktop', '_WindowsNative')):
            # Factory names are resolved explicitly; mocks must never fall back
            # to a real native facade, including during post-effect observation.
            guard = patch('nayeon.services.' + module + '.' + factory,
                          side_effect=AssertionError('LIVE NATIVE FORBIDDEN'))
            mock = guard.start()
            self.addCleanup(guard.stop)
            self.addCleanup(mock.assert_not_called)

    def valid(self, point, *, enabled=True, control_type=50000):
        return u._ScopedUIElementResult(V.VERIFIED,
            u._ScopedUIElementEvidence(point, 2, control_type, enabled))

    def blocked(self, invocation, operation):
        result = self.effect_once(invocation, operation)
        self.assertIs(result.status, E.NOT_ATTEMPTED)
        self.assertFalse(result.attempted)
        self.metrics.metric.assert_not_called()
        self.effect_native._send_input.assert_not_called()
        self.assertIsNone(invocation._post_observation)
        self.assertIsNone(invocation._ui_element_service)
        self.assertIsNone(invocation._services)
        self.assertEqual(invocation._verification.evidence, {})

    def test_exact_order_once_original_point_final_native_sample(self):
        calls = []
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            self.assertEqual(self.harness.events, [])
            original_observe = u._ScopedUIElementObservationService.observe
            original_normalize = _PointerCoordinateService.normalize
            original_insert = _PointerEffectService._insert
            def normalize(service, point):
                calls.append('normalize')
                self.assertIs(point, operation.point)
                return original_normalize(service, point)
            def insert(service, evidence):
                calls.append('insert')
                self.assertIs(evidence.point, operation.point)
                return original_insert(service, evidence)
            def sampled_observe(service, point):
                calls.append('uia')
                self.assertIs(service, self.ui_element_service)
                self.assertIs(point, operation.point)
                return original_observe(service, point)
            target = self.service.acquire_target
            hit = _PointerHitValidationService.validate_hit
            def fresh_target():
                calls.append('target')
                return target()
            def fresh_hit(service, point, target):
                calls.append('hit')
                return hit(service, point, target)
            self.metrics.metric.side_effect = lambda index: (
                calls.append('metric'), {76: 30000, 77: 26000, 78: 2000, 79: 2000}[index])[1]
            self.effect_native._send_input.side_effect = lambda *args: (calls.append('send'), 3)[1]
            audit = self.audit.record
            def record(*args, **kwargs):
                calls.append('audit')
                return audit(*args, **kwargs)
            with patch.object(self.service, 'acquire_target', side_effect=fresh_target), \
                    patch.object(_PointerHitValidationService, 'validate_hit', autospec=True, side_effect=fresh_hit), \
                    patch.object(u._ScopedUIElementObservationService, 'observe', autospec=True, side_effect=sampled_observe) as ui, \
                    patch.object(_PointerCoordinateService, 'normalize', autospec=True, side_effect=normalize), \
                    patch.object(_PointerEffectService, '_insert', autospec=True, side_effect=insert), \
                    patch.object(self.audit, 'record', side_effect=record):
                result = self.effect_once(invocation, operation)
                ui.assert_called_once_with(self.ui_element_service, operation.point)
            self.assertIs(result.status, E.INSERTED)
            start, end = calls.index('target'), calls.index('send')
            self.assertEqual(calls[start:end + 1],
                ['target', 'hit', 'uia', 'normalize', 'metric', 'metric', 'metric', 'metric', 'insert', 'send'])
            self.assertEqual(self.harness.names().count('element_from_point'), 1)
            self.assertEqual(invocation._verification.reason, CLAIM)

    def test_approve_read_only_even_in_effect_mode(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(u._ScopedUIElementObservationService, 'observe') as ui:
                result = invocation.approve(operation, target=operation.target,
                    action=operation.action, point=operation.point)
                ui.assert_not_called()
            self.assertIs(result.status, V.VERIFIED)
            self.metrics.metric.assert_not_called()
            self.effect_native._send_input.assert_not_called()

    def test_indeterminate_and_disabled_reject_before_mapping(self):
        for disabled in (False, True):
            with self.subTest(disabled=disabled):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    result = self.valid(operation.point, enabled=False) if disabled else u._ScopedUIElementResult()
                    with patch.object(u._ScopedUIElementObservationService, 'observe', return_value=result) as ui:
                        self.blocked(invocation, operation)
                        ui.assert_called_once_with(operation.point)

    def test_every_reviewed_control_type_equivalent_no_semantic_claim(self):
        for ct in sorted(_CONTROL_TYPES):
            with self.subTest(control_type=ct):
                self.setUp()
                self.harness.ct = ct
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    self.assertIs(self.effect_once(invocation, operation).status, E.INSERTED)
                    self.assertEqual(invocation._verification.reason, CLAIM)
                    self.assertEqual(invocation._verification.evidence, {})
                    self.assertEqual({f.name for f in fields(invocation._post_observation)}, {'status'})

    def test_wrong_subclass_uninitialized_and_exception_results(self):
        class Result(u._ScopedUIElementResult):
            pass
        for bad in (None, {}, Mock(), object.__new__(Result),
                    object.__new__(u._ScopedUIElementResult), RuntimeError('PRIVATE_UIA')):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                options = {'side_effect': bad} if isinstance(bad, Exception) else {'return_value': bad}
                with patch.object(u._ScopedUIElementObservationService, 'observe', **options):
                    self.blocked(invocation, operation)
            self.assertNotIn('PRIVATE_UIA', repr(self.audit.all()))

    def test_tampered_result_and_evidence_invariants(self):
        class Evidence(u._ScopedUIElementEvidence):
            pass
        cases = [('result', 'status', 'verified'), ('result', 'status', V.NOT_VERIFIED),
                 ('result', 'evidence', None), ('result', 'evidence', Mock()),
                 ('result', 'evidence', object.__new__(Evidence)),
                 ('result', 'evidence', object.__new__(u._ScopedUIElementEvidence)),
                 ('evidence', 'awareness', 1), ('evidence', 'awareness', True),
                 ('evidence', 'enabled', 1), ('evidence', 'enabled', False),
                 ('evidence', 'control_type', 49999), ('evidence', 'control_type', True),
                 ('evidence', 'point', _ProposedPoint(31415, 27182))]
        for where, name, value in cases:
            with self.subTest(where=where, name=name, value_type=type(value)):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    result = self.valid(operation.point)
                    object.__setattr__(result if where == 'result' else result.evidence, name, value)
                    with patch.object(u._ScopedUIElementObservationService, 'observe', return_value=result):
                        self.blocked(invocation, operation)

    def test_observation_mutations_invalidate_snapshot_before_mapping(self):
        for mutation in ('point', 'point_identity', 'target', 'action', 'operation',
                         'registry', 'implementation', 'target_service', 'hit_service',
                         'coordinate_service', 'effect_service', 'uia_service'):
            with self.subTest(mutation=mutation):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    def observe(point):
                        result = self.valid(point)
                        if mutation == 'point':
                            object.__setattr__(point, 'x', point.x + 1)
                        elif mutation == 'point_identity':
                            object.__setattr__(operation, 'point', _ProposedPoint(point.x, point.y))
                        elif mutation == 'target':
                            object.__setattr__(operation, 'target', replace(operation.target))
                        elif mutation == 'action':
                            object.__setattr__(operation, 'action', b._PointerAction())
                        elif mutation == 'operation':
                            invocation._operation = replace(operation)
                        elif mutation in ('registry', 'implementation'):
                            self.registry.unregister(self.capability.name)
                            self.registry.register(replace(self.capability) if mutation == 'registry' else self.capability,
                                Mock() if mutation == 'implementation' else self.implementation)
                        else:
                            attr = {'target_service': '_service', 'hit_service': '_hit_service',
                                    'uia_service': '_ui_element_service'}.get(mutation, '_' + mutation)
                            setattr(invocation, attr, Harness().service() if mutation == 'uia_service' else Mock())
                        return result
                    with patch.object(u._ScopedUIElementObservationService, 'observe', side_effect=observe):
                        self.blocked(invocation, operation)

    def test_replacement_before_uia_and_after_coordinate_fail_closed(self):
        for stage in ('before_uia', 'after_coordinate'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                if stage == 'before_uia':
                    invocation._ui_element_service = Harness().service()
                    with patch.object(u._ScopedUIElementObservationService, 'observe') as ui:
                        self.blocked(invocation, operation)
                        ui.assert_not_called()
                else:
                    normalize = _PointerCoordinateService.normalize
                    def changed(service, point):
                        result = normalize(service, point)
                        invocation._ui_element_service = Harness().service()
                        return result
                    with patch.object(_PointerCoordinateService, 'normalize', autospec=True, side_effect=changed):
                        self.assertIs(self.effect_once(invocation, operation).status, E.NOT_ATTEMPTED)
                    self.effect_native._send_input.assert_not_called()

    def test_mutation_during_local_result_validation_fails_closed(self):
        self.setUp()
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            result = self.valid(operation.point)
            validate = u._ScopedUIElementResult.__post_init__
            def changed(observed):
                validate(observed)
                invocation._ui_element_service = Harness().service()
            with patch.object(u._ScopedUIElementObservationService, 'observe', return_value=result), \
                    patch.object(u._ScopedUIElementResult, '__post_init__', changed):
                self.blocked(invocation, operation)

    def test_existing_policy_and_fresh_eligibility_failures_do_not_call_uia(self):
        for stage in ('permission', 'target', 'hit'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                if stage == 'permission':
                    self.permissions.revoke(self.capability.name)
                elif stage == 'target':
                    self.native.foreground.return_value += 1
                else:
                    self.hit_native.window_at.return_value = 0
                with patch.object(u._ScopedUIElementObservationService, 'observe') as ui:
                    self.blocked(invocation, operation)
                    ui.assert_not_called()

    def test_constructor_and_executor_exact_service_requirements(self):
        class Service(u._ScopedUIElementObservationService):
            pass
        for coordinate, effect, ui in (
                (self.coordinates, self.effect, None), (self.coordinates, self.effect, Mock()),
                (self.coordinates, self.effect, Service()), (None, self.effect, self.ui_element_service),
                (self.coordinates, None, None), (None, None, self.ui_element_service),
                (Mock(), self.effect, self.ui_element_service), (self.coordinates, Mock(), self.ui_element_service)):
            options = dict(coordinate_service=coordinate, effect_service=effect, ui_element_service=ui)
            with self.assertRaises(TypeError):
                b._PointerInvocation(self.executor, self.capability, self.service, self.hit_service, **options)
            with self.assertRaises(TypeError):
                with self.executor._pointer_invocation(self.capability, service=self.service,
                        hit_service=self.hit_service, **options):
                    self.fail('Invalid service accepted')
        self.assertEqual(self.harness.events, [])
        self.native.foreground.assert_not_called()

    def test_uia_evidence_never_retained_or_bridged(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            result = self.valid(operation.point)
            captured = []
            original = b._PointerVerificationProvider.__post_init__
            def provider_init(provider):
                original(provider)
                captured.append(provider)
            with patch.object(u._ScopedUIElementObservationService, 'observe', return_value=result), \
                    patch.object(b._PointerVerificationProvider, '__post_init__', provider_init):
                self.assertIs(self.effect_once(invocation, operation).status, E.INSERTED)
            self.assertEqual(len(captured), 1)
            self.assertEqual({f.name for f in fields(captured[0])}, {'_receipt', '_observation', '_sealed', '_used'})
            self.assertIs(captured[0]._observation, invocation._post_observation)
            self.assertEqual(invocation._verification.evidence, {})
            for slot in invocation.__slots__:
                self.assertIsNot(getattr(invocation, slot), result)
                self.assertIsNot(getattr(invocation, slot), result.evidence)
            for event in self.audit.all():
                self.assertNotIn('control_type', repr(event))
                self.assertNotIn('awareness', repr(event))
                self.assertNotIn('enabled', repr(event))
            self.assertEqual(invocation._verification.reason, CLAIM)


class SourceGuards(unittest.TestCase):
    def test_no_new_executor_route_or_changed_posteffect_verification(self):
        path = 'nayeon/agent/executor.py'
        source = (ROOT / path).read_text(encoding='utf-8-sig')
        baseline = subprocess.check_output(['git', 'show', HEAD + ':' + path], cwd=ROOT).decode('utf-8-sig')
        start, end = '    @contextmanager\n    def _pointer_invocation(', '    @property\n    def unregistered_cleanup_failures'
        self.assertEqual(source[:source.index(start)], baseline[:baseline.index(start)])
        self.assertEqual(source[source.index(end):], baseline[baseline.index(end):])
        path = 'nayeon/agent/pointer_binding.py'
        source = (ROOT / path).read_text(encoding='utf-8-sig')
        baseline = subprocess.check_output(['git', 'show', HEAD + ':' + path], cwd=ROOT).decode('utf-8-sig')
        current_ast, baseline_ast = ast.parse(source), ast.parse(baseline)
        for name in ('_PointerVerificationProvider', '_PointerPostObservationResult'):
            current = next(node for node in current_ast.body if isinstance(node, ast.ClassDef) and node.name == name)
            old = next(node for node in baseline_ast.body if isinstance(node, ast.ClassDef) and node.name == name)
            self.assertEqual(ast.dump(current), ast.dump(old))
        for tree in (current_ast, baseline_ast):
            invocation = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == '_PointerInvocation')
            method = next(node for node in invocation.body if isinstance(node, ast.FunctionDef) and node.name == '_observe_after_effect')
            if tree is current_ast:
                current = ast.dump(method)
            else:
                self.assertEqual(current, ast.dump(method))

    def test_final_gap_byte_unchanged_and_precoordinate_local_only(self):
        path = 'nayeon/agent/pointer_binding.py'
        source = (ROOT / path).read_text(encoding='utf-8-sig')
        baseline = subprocess.check_output(['git', 'show', HEAD + ':' + path], cwd=ROOT).decode('utf-8-sig')
        start = '                mapped = self._coordinate_service.normalize(operation.point)'
        end = '            else:\n                completed = eligibility'
        self.assertEqual(source[source.index(start):source.index(end)],
                         baseline[baseline.index(start):baseline.index(end)])
        begin = source.index('                observed = self._ui_element_service.observe(operation.point)')
        gap = source[begin:source.index(start)]
        tree = ast.parse(inspect.cleandoc(gap))
        calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertCountEqual(calls, ['self._ui_element_service.observe', 'type',
            '_ScopedUIElementResult.__post_init__', 'type', '_ScopedUIElementEvidence.__post_init__', 'self._bound'])
        self.assertEqual(source.count('self._ui_element_service.observe('), 1)
        self.assertNotIn('control_type', source)
        for forbidden in ('SendInput', 'SetCursorPos', 'WinDLL', 'InvokePattern', 'ValuePattern',
                          'SetValue', 'sleep(', 'ThreadPool', 'screenshot', 'AutomationId'):
            self.assertNotIn(forbidden, source)

    def test_sealed_services_byte_identical_to_protected_head(self):
        for name in ('scoped_ui_element_observation', 'dpi_execution_context',
                     'pointer_coordinate_contract', 'ui_element_observation',
                     'pointer_coordinates', 'pointer_effect', 'target_validation',
                     'pointer_hit_validation'):
            path = 'nayeon/services/' + name + '.py'
            baseline = subprocess.check_output(['git', 'show', HEAD + ':' + path], cwd=ROOT)
            current = (ROOT / path).read_bytes()
            self.assertIn(current, (baseline, baseline.replace(b'\n', b'\r\n')), path)
            self.assertEqual(subprocess.check_output(['git', 'diff', HEAD, '--', path], cwd=ROOT), b'')


if __name__ == '__main__':
    unittest.main()
