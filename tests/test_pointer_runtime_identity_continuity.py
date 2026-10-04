"""Phase 6.20 approval-bound continuity; deterministic fakes only."""
import ast
import hashlib
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

from tests import test_pointer_uia_gate as gate
from tests import test_pointer_binding as binding
from nayeon.agent import pointer_binding as b
from nayeon.services import scoped_ui_element_observation as u
from nayeon.services.pointer_hit_validation import _PointerHitValidationService, _ProposedPoint
from nayeon.services.pointer_coordinates import _PointerCoordinateService
from nayeon.services.pointer_effect import _EffectStatus as E
from nayeon.verification.contract import VerificationStatus as V

ROOT = Path(__file__).resolve().parents[1]
HEAD = '382d44c3a944a0868c6af3350d4128e8799f8016'


class ContinuityTests(unittest.TestCase):
    setUp = gate.GateTests.setUp
    invocation = gate.GateTests.invocation
    prepare = gate.GateTests.prepare
    effect_once = gate.GateTests.effect_once
    valid = gate.GateTests.valid
    blocked = gate.GateTests.blocked

    def test_prepare_order_once_original_point_and_exact_binding(self):
        calls = Mock()
        observe = u._ScopedUIElementObservationService.observe
        hit = _PointerHitValidationService.validate_hit
        with patch.object(self.service, 'acquire_target', wraps=self.service.acquire_target) as target, \
                patch.object(_PointerHitValidationService, 'validate_hit', autospec=True, side_effect=hit) as hit_mock, \
                patch.object(u._ScopedUIElementObservationService, 'observe', autospec=True, side_effect=observe) as ui, \
                patch.object(self.confirmation, 'create', wraps=self.confirmation.create) as confirmation:
            for name, mock in (('target', target), ('hit', hit_mock), ('uia', ui), ('confirmation', confirmation)):
                calls.attach_mock(mock, name)
            with self.invocation() as invocation:
                operation, request = self.prepare(invocation)
                self.assertEqual([c[0] for c in calls.mock_calls], ['target', 'hit', 'uia', 'confirmation'])
                ui.assert_called_once_with(self.ui_element_service, self.point)
                self.assertIs(self.confirmation._bindings[request.token], operation)
                self.assertIs(operation.runtime_id, self.harness.runtime)
                self.assertEqual(self.harness.names().count('element_from_point'), 1)
                self.assertEqual([f.name for f in fields(operation)], ['target', 'action', 'point', 'runtime_id'])
                for name in ('evidence', 'enabled', 'control_type', 'observation'):
                    self.assertFalse(hasattr(operation, name))

    def test_preapproval_invalid_results_never_create_confirmation(self):
        class Result(u._ScopedUIElementResult):
            pass
        class Evidence(u._ScopedUIElementEvidence):
            pass
        cases = [None, {}, Mock(), object.__new__(Result), object.__new__(u._ScopedUIElementResult),
                 u._ScopedUIElementResult(), RuntimeError('PRIVATE_SAMPLE'),
                 self.valid(self.point, enabled=False), self.valid(_ProposedPoint(self.point.x, self.point.y))]
        for where, name, value in (
                ('result', 'status', 'verified'), ('result', 'status', V.NOT_VERIFIED),
                ('result', 'evidence', None), ('result', 'evidence', object.__new__(Evidence)),
                ('evidence', 'runtime_id', None), ('evidence', 'runtime_id', (True,)),
                ('evidence', 'runtime_id', ()), ('evidence', 'awareness', 1),
                ('evidence', 'enabled', 1), ('evidence', 'control_type', 49999)):
            sample = self.valid(self.point)
            object.__setattr__(sample if where == 'result' else sample.evidence, name, value)
            cases.append(sample)
        for bad in cases:
            with self.subTest(kind=type(bad)):
                options = {'side_effect': bad} if isinstance(bad, Exception) else {'return_value': bad}
                with self.invocation() as invocation, \
                        patch.object(u._ScopedUIElementObservationService, 'observe', **options) as ui, \
                        patch.object(self.confirmation, 'create', wraps=self.confirmation.create) as create:
                    # Each case gets a fresh deterministic target/hit clock.
                    self.service._clock.side_effect = [10, 20]
                    self.hit_service._clock.side_effect = [30, 40]
                    with self.assertRaises(ValueError):
                        self.prepare(invocation)
                    ui.assert_called_once_with(self.point)
                    create.assert_not_called()
                    self.assertEqual(self.confirmation._bindings, {})
                    self.assertEqual(self.confirmation._pending, {})
                    self.assertIsNone(invocation._operation)
        self.assertNotIn('PRIVATE_SAMPLE', repr(self.audit.all()))

    def test_preapproval_service_or_registration_mutation_blocks_confirmation(self):
        for mutation in ('service', 'registration'):
            self.setUp()
            with self.invocation() as invocation:
                def observe(point):
                    if mutation == 'service':
                        invocation._hit_service = Mock()
                    else:
                        self.registry.unregister(self.capability.name)
                    return self.valid(point)
                with patch.object(u._ScopedUIElementObservationService, 'observe', side_effect=observe), \
                        patch.object(self.confirmation, 'create', wraps=self.confirmation.create) as create:
                    with self.assertRaises(ValueError):
                        self.prepare(invocation)
                    create.assert_not_called()
                    self.assertEqual(self.confirmation._bindings, {})

    def test_snapshot_and_frozen_bypass_blocks_before_approval(self):
        for runtime in (None, (), [], (True,), (2**31,), (17,)):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                self.assertEqual(b._snapshot(operation)[-1], operation.runtime_id)
                with self.assertRaises(FrozenInstanceError):
                    operation.runtime_id = (17,)
                object.__setattr__(operation, 'runtime_id', runtime)
                with patch.object(self.confirmation, 'approve', wraps=self.confirmation.approve) as approve, \
                        patch.object(u._ScopedUIElementObservationService, 'observe') as ui:
                    self.blocked(invocation, operation)
                    approve.assert_not_called()
                    ui.assert_not_called()

    def test_legacy_default_none_and_readonly_no_uia(self):
        with binding.PointerBindingTests.invocation(self) as invocation, \
                patch.object(u._ScopedUIElementObservationService, 'observe') as ui:
            operation, _ = self.prepare(invocation)
            legacy = b._PointerOperation(operation.target, operation.action, operation.point)
            self.assertIsNone(legacy.runtime_id)
            self.assertIsNone(operation.runtime_id)
            self.assertTrue(invocation._bound(operation))
            self.assertIs(invocation.approve(operation, target=operation.target,
                action=operation.action, point=operation.point).status, V.VERIFIED)
            ui.assert_not_called()

    def test_effect_mode_readonly_approval_has_no_second_observation(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(u._ScopedUIElementObservationService, 'observe') as ui:
                result = invocation.approve(operation, target=operation.target,
                    action=operation.action, point=operation.point)
                ui.assert_not_called()
            self.assertIs(result.status, V.VERIFIED)
            self.assertEqual(self.harness.names().count('element_from_point'), 1)
            self.metrics.metric.assert_not_called()
            self.effect_native._send_input.assert_not_called()

    def test_operation_runtime_validation_and_non_effect_binding_requires_none(self):
        class Tuple(tuple):
            pass
        class Int(int):
            pass
        with binding.PointerBindingTests.invocation(self) as invocation:
            operation, _ = self.prepare(invocation)
            for runtime in ((), [], Tuple((1,)), (True,), (Int(1),), (1.0,),
                            (2**31,), (-(2**31)-1,), (1,) * 65):
                with self.assertRaises((TypeError, ValueError)):
                    b._PointerOperation(operation.target, operation.action, operation.point, runtime)
            object.__setattr__(operation, 'runtime_id', (1,))
            invocation._snapshot = b._snapshot(operation)
            self.assertFalse(invocation._bound(operation))

    def test_fresh_execution_order(self):
        gate.GateTests.test_exact_order_once_original_point_final_native_sample(self)

    def test_equal_distinct_runtime_tuple_and_changed_control_type_permit_insertion(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            runtime = tuple(list(operation.runtime_id))
            self.assertIsNot(runtime, operation.runtime_id)
            result = self.valid(operation.point, runtime_id=runtime, control_type=50001)
            self.assertNotEqual(result.evidence.control_type, self.harness.ct)
            with patch.object(u._ScopedUIElementObservationService, 'observe', return_value=result) as ui:
                self.assertIs(self.effect_once(invocation, operation).status, E.INSERTED)
                ui.assert_called_once_with(operation.point)
            self.metrics.metric.assert_called()
            self.effect_native._send_input.assert_called_once()

    def test_mismatch_blocks_normalization_and_insertion(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(u._ScopedUIElementObservationService, 'observe',
                              return_value=self.valid(operation.point, runtime_id=(17,))), \
                    patch.object(_PointerCoordinateService, 'normalize') as normalize:
                self.blocked(invocation, operation)
                normalize.assert_not_called()

    def test_post_disabled_blocks_effect(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(u._ScopedUIElementObservationService, 'observe',
                              return_value=self.valid(operation.point, enabled=False)):
                self.blocked(invocation, operation)

    def test_runtime_is_not_retained_or_disclosed_after_close(self):
        self.harness.runtime = (192837465, -918273645)
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            self.assertIs(self.effect_once(invocation, operation).status, E.INSERTED)
            self.assertEqual(invocation._verification.evidence, {})
            self.assertEqual([f.name for f in fields(invocation._post_observation)], ['status'])
            for name in ('_operation', '_target', '_action', '_point', '_snapshot', '_confirmation',
                         '_service', '_hit_service', '_coordinate_service', '_effect_service',
                         '_ui_element_service', '_services', '_registered', '_implementation'):
                self.assertIsNone(getattr(invocation, name))
            for text in (repr(self.audit.all()), repr(invocation._verification),
                         repr(invocation._post_observation), repr(operation)):
                for secret in ('192837465', '918273645', 'runtime_id'):
                    self.assertNotIn(secret, text)
            self.assertEqual(self.confirmation._bindings, {})


class ContinuitySourceGuards(unittest.TestCase):
    def test_local_opaque_runtime_usage_only(self):
        source = Path(b.__file__).read_text()
        for forbidden in ('CompareElements', 'CompareRuntimeIds', 'SafeArray', 'SAFEARRAY',
                          'ctypes', 'WinDLL', 'CoInitialize', 'comtypes', 'control_type', 'hash(', 'hashlib',
                          'json', 'pickle', 'runtime_id[', 'str(runtime_id', 'repr(runtime_id',
                          'nayeon.memory', 'open('):
            self.assertNotIn(forbidden, source)
        tree = ast.parse(source)
        # Every runtime-bearing statement has a reviewed local role; no parser,
        # persistence, native call, audit argument, or semantic lookup is allowed.
        uses = [ast.unparse(node.func) for node in ast.walk(tree)
                if isinstance(node, ast.Call) and 'runtime_id' in ast.unparse(node)]
        self.assertCountEqual(uses, ['_runtime_id_valid', '_PointerOperation'])
        self.assertEqual(source.count('if evidence.runtime_id != operation.runtime_id:'), 1)
        self.assertEqual(source.count('self._ui_element_service.observe('), 2)

    def test_order_and_final_gap_identical_to_protected_head(self):
        source = Path(b.__file__).read_text()
        baseline = subprocess.check_output(['git', 'show', HEAD + ':nayeon/agent/pointer_binding.py'], cwd=ROOT).decode().replace('\r\n', '\n')
        observe = source.index('observed = self._ui_element_service.observe(operation.point)')
        equal = source.index('if evidence.runtime_id != operation.runtime_id:')
        start = '                mapped = self._coordinate_service.normalize(operation.point)'
        end = '            else:\n                completed = eligibility'
        self.assertLess(observe, equal)
        self.assertLess(equal, source.index(start))
        self.assertLess(source.index(start), source.index('receipt = self._effect_service._insert(mapped.evidence)'))
        self.assertEqual(source[source.index(start):source.index(end)],
                         baseline[baseline.index(start):baseline.index(end)])

    def test_protected_files_and_only_one_production_change(self):
        paths = ('nayeon/agent/executor.py', 'nayeon/policy/confirmation.py',
                 'nayeon/services/scoped_ui_element_observation.py',
                 'nayeon/services/ui_element_observation.py', 'nayeon/services/pointer_effect.py',
                 'nayeon/services/pointer_coordinates.py')
        raw_seals = (
            '4458d285a2d08c68542b3a504e14a31bcaaeeaf44e39f44e68bea2204c38deb2',
            '88d88c9283ca2441c5d436c1cff7e983b57bdd3af9b179fdfbc4b44b6cdb84c7',
            '4dad12c4e042b9003867b04430d63a2993e47bae9b0479f10349963ce29f5e68',
            '0b3b9fd646d3f15a4764e645d1634a346b34611f71c3526be7519768603fe257',
            '4fb68cc2a18afce58cedbaa0bf9dd780b9ff2b92be1cf4e5a89c19da6c535e1c',
            '7a286a561c7c3711f110b773fd666a3ab919bc11d4e0355a9b242e830c3f8e1c')
        for path, seal in zip(paths, raw_seals):
            baseline = subprocess.check_output(['git', 'show', HEAD + ':' + path], cwd=ROOT)
            current = (ROOT / path).read_bytes()
            # The protected checkout contains mixed line endings. Compare Git
            # content independently and seal every raw checkout byte as well.
            normalized = baseline.replace(b'\r\n', b'\n')
            self.assertEqual(current.replace(b'\r\n', b'\n'), normalized, path)
            self.assertEqual(hashlib.sha256(current).hexdigest(), seal, path)
            self.assertEqual(subprocess.check_output(['git', 'diff', HEAD, '--', path], cwd=ROOT), b'')
        changed = subprocess.check_output(['git', 'diff', HEAD, '--name-only', '--', 'nayeon'], cwd=ROOT).decode().splitlines()
        self.assertEqual(changed, ['nayeon/agent/pointer_binding.py'])
        self.assertEqual(subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', 'nayeon'], cwd=ROOT), b'')
        self.assertEqual(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(), HEAD)
        self.assertEqual(subprocess.check_output(['git', 'rev-parse', 'nayeon-v1-bounded-uia-runtime-identity-01^{commit}'], cwd=ROOT).decode().strip(), HEAD)


if __name__ == '__main__':
    unittest.main()
