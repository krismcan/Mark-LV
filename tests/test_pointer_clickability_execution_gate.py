"""Phase 6.22 fresh execution veto; deterministic seams, no live effects."""
import ast
from copy import copy, deepcopy
from dataclasses import fields
from pathlib import Path
import pickle
import subprocess
import sys
import unittest
from unittest.mock import patch

from nayeon.agent import pointer_binding as b
from nayeon.services import scoped_ui_element_observation as u
from nayeon.services.pointer_coordinates import _PointerCoordinateService
from nayeon.services.pointer_effect import _PointerEffectService, _EffectStatus as E
from tests import test_pointer_uia_gate as gate

ROOT = Path(__file__).resolve().parents[1]
HEAD = '0a7f8890f73399ef07c3048c8f19b49b8b1643dc'
OLD = ('                # Enabled is only a safety prerequisite, never clickability or\n'
       '                # semantic authorization. Do not retain this descriptive sample.\n')
NEW = ('                # Fresh actionability veto only, never semantic authorization.\n'
       '                if evidence.clickable is not True:\n'
       '                    return unknown\n'
       '                # Do not retain this descriptive sample.\n')


class ClickabilityExecutionTests(unittest.TestCase):
    setUp = gate.GateTests.setUp
    invocation = gate.GateTests.invocation
    prepare = gate.GateTests.prepare
    effect_once = gate.GateTests.effect_once
    valid = gate.GateTests.valid
    blocked = gate.GateTests.blocked

    def test_preconfirmation_false_and_true_have_same_runtime_binding(self):
        snapshots = []
        for clickable in (False, True):
            self.setUp()
            self.harness.clickable = clickable
            with self.invocation() as invocation:
                operation, request = self.prepare(invocation)
                self.assertIs(self.confirmation._bindings[request.token], operation)
                self.assertIn(request.token, self.confirmation._pending)
                self.assertEqual([f.name for f in fields(operation)],
                                 ['target', 'action', 'point', 'runtime_id'])
                self.assertIs(operation.runtime_id, self.harness.runtime)
                self.assertIs(operation.point, self.point)
                self.assertFalse(hasattr(operation, 'clickable'))
                self.assertEqual(len(invocation._snapshot), 9)
                snapshots.append(invocation._snapshot)
                for text in (repr(operation), repr(request), repr(self.audit.all())):
                    self.assertNotIn('clickable', text)
                self.metrics.metric.assert_not_called()
                self.effect_native._send_input.assert_not_called()
        self.assertEqual(snapshots[0], snapshots[1])

    def test_false_preparation_true_execution_uses_only_approved_point_once(self):
        self.harness.clickable = False
        with self.invocation() as invocation:
            operation, request = self.prepare(invocation)
            sample = self.valid(operation.point, clickable=True,
                                runtime_id=tuple(list(operation.runtime_id)))
            self.assertIsNot(sample.evidence.runtime_id, operation.runtime_id)
            normalize = _PointerCoordinateService.normalize
            insert = _PointerEffectService._insert
            with patch.object(u._ScopedUIElementObservationService, 'observe', return_value=sample) as observe, \
                    patch.object(_PointerCoordinateService, 'normalize', autospec=True, side_effect=normalize) as mapped, \
                    patch.object(_PointerEffectService, '_insert', autospec=True, side_effect=insert) as inserted, \
                    patch.object(self.confirmation, 'approve', wraps=self.confirmation.approve) as approve:
                self.assertIs(self.effect_once(invocation, operation).status, E.INSERTED)
                self.assertIs(self.effect_once(invocation, operation).status, E.NOT_ATTEMPTED)
                observe.assert_called_once_with(operation.point)
                mapped.assert_called_once_with(self.coordinates, operation.point)
                self.assertIs(inserted.call_args.args[1].point, operation.point)
                self.assertIs(approve.call_args.kwargs['binding'], operation)
                approve.assert_called_once()
            self.effect_native._send_input.assert_called_once()
            self.assertEqual(self.confirmation._bindings, {})
            self.assertEqual(self.confirmation._pending, {})
            self.assertEqual(invocation._verification.evidence, {})
            for text in (repr(operation), repr(self.audit.all()), repr(invocation._verification),
                         repr(invocation._post_observation)):
                self.assertNotIn('clickable', text)
            for slot in invocation.__slots__:
                self.assertIsNot(getattr(invocation, slot), sample)
                self.assertIsNot(getattr(invocation, slot), sample.evidence)
            for serializer in (copy, deepcopy, pickle.dumps):
                with self.assertRaises(TypeError):
                    serializer(operation)

    def test_fresh_false_disabled_runtime_mismatch_and_unavailable_veto(self):
        for options in ({'clickable': False}, {'enabled': False}, {'runtime_id': (17,)}, None):
            with self.subTest(options=options):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    sample = u._ScopedUIElementResult() if options is None else self.valid(operation.point, **options)
                    with patch.object(u._ScopedUIElementObservationService, 'observe', return_value=sample), \
                            patch.object(_PointerCoordinateService, 'normalize') as normalize, \
                            patch.object(_PointerEffectService, '_insert') as insert:
                        self.blocked(invocation, operation)
                        normalize.assert_not_called()
                        insert.assert_not_called()
                    self.assertEqual(self.confirmation._bindings, {})
                    self.assertEqual(self.confirmation._pending, {})
                    self.assertIs(self.effect_once(invocation, operation).status, E.NOT_ATTEMPTED)
                    self.assertNotIn('clickable', repr(self.audit.all()))

    def test_malformed_and_missing_clickability_fail_existing_contract(self):
        for value in (0, 1, None, 1.0, 'true', object(), 'missing'):
            with self.subTest(kind=type(value), missing=value == 'missing'):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    sample = self.valid(operation.point)
                    if value == 'missing':
                        object.__delattr__(sample.evidence, 'clickable')
                    else:
                        object.__setattr__(sample.evidence, 'clickable', value)
                    with self.assertRaises((TypeError, AttributeError)):
                        u._ScopedUIElementResult.__post_init__(sample)
                    with patch.object(u._ScopedUIElementObservationService, 'observe', return_value=sample), \
                            patch.object(_PointerCoordinateService, 'normalize') as normalize:
                        self.blocked(invocation, operation)
                        normalize.assert_not_called()

    def test_exact_execution_order_including_local_gate_lines(self):
        calls = []
        source = Path(b.__file__).read_text()
        runtime_line = next(i for i, line in enumerate(source.splitlines(), 1)
                            if 'if evidence.runtime_id != operation.runtime_id:' in line)
        clickable_line = next(i for i, line in enumerate(source.splitlines(), 1)
                              if 'if evidence.clickable is not True:' in line)
        def trace(frame, event, arg):
            if frame.f_code is b._PointerInvocation._consume.__code__ and event == 'line':
                if frame.f_lineno == runtime_line:
                    calls.append('runtime equality')
                elif frame.f_lineno == clickable_line:
                    calls.append('clickable gate')
            return trace
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            target = self.service.acquire_target
            hit = gate._PointerHitValidationService.validate_hit
            observe = u._ScopedUIElementObservationService.observe
            normalize = _PointerCoordinateService.normalize
            insert = _PointerEffectService._insert
            def call(name, function, *args):
                calls.append(name)
                return function(*args)
            self.metrics.metric.side_effect = lambda index: call(
                'metric', {76: 30000, 77: 26000, 78: 2000, 79: 2000}.__getitem__, index)
            self.effect_native._send_input.side_effect = lambda *args: call('SendInput', lambda: 3)
            with patch.object(self.service, 'acquire_target', side_effect=lambda: call('target', target)), \
                    patch.object(gate._PointerHitValidationService, 'validate_hit', autospec=True,
                                 side_effect=lambda *args: call('hit', hit, *args)), \
                    patch.object(u._ScopedUIElementObservationService, 'observe', autospec=True,
                                 side_effect=lambda *args: call('UIA', observe, *args)), \
                    patch.object(_PointerCoordinateService, 'normalize', autospec=True,
                                 side_effect=lambda *args: call('normalize', normalize, *args)), \
                    patch.object(_PointerEffectService, '_insert', autospec=True,
                                 side_effect=lambda *args: call('insert', insert, *args)):
                previous_trace = sys.gettrace()
                try:
                    sys.settrace(trace)
                    result = self.effect_once(invocation, operation)
                finally:
                    sys.settrace(previous_trace)
            self.assertIs(result.status, E.INSERTED)
        self.assertEqual(calls, ['target', 'hit', 'UIA', 'runtime equality', 'clickable gate',
                                 'normalize', 'metric', 'metric', 'metric', 'metric', 'insert', 'SendInput'])


class ClickabilitySourceGuards(unittest.TestCase):
    def test_only_exact_approved_local_edit_and_no_preconfirmation_change(self):
        source = Path(b.__file__).read_text()
        baseline = subprocess.check_output(['git', 'show', HEAD + ':nayeon/agent/pointer_binding.py'],
                                           cwd=ROOT).decode().replace('\r\n', '\n')
        self.assertEqual(baseline.count(OLD), 1)
        self.assertEqual(source, baseline.replace(OLD, NEW, 1))
        tree = ast.parse(source)
        reads = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Attribute) and node.attr == 'clickable']
        self.assertEqual(len(reads), 1)
        invocation = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                          and node.name == '_PointerInvocation')
        prepare = next(node for node in invocation.body if isinstance(node, ast.FunctionDef)
                       and node.name == 'prepare')
        self.assertNotIn('clickable', ast.unparse(prepare))
        for forbidden in ('GetClickablePoint', 'clickable_point_available', 'provider_point',
                          'clickable_x', 'clickable_y', 'click_point', 'WinDLL', 'SendInput',
                          'CompareRuntimeIds', 'InvokePattern', 'SetCursorPos'):
            self.assertNotIn(forbidden, source)

    def test_final_normalization_insertion_content_identical(self):
        source = Path(b.__file__).read_text()
        baseline = subprocess.check_output(['git', 'show', HEAD + ':nayeon/agent/pointer_binding.py'],
                                           cwd=ROOT).decode().replace('\r\n', '\n')
        start = '                mapped = self._coordinate_service.normalize(operation.point)'
        end = '            else:\n                completed = eligibility'
        self.assertEqual(source[source.index(start):source.index(end)],
                         baseline[baseline.index(start):baseline.index(end)])
        runtime = source.index('if evidence.runtime_id != operation.runtime_id:')
        clickable = source.index('if evidence.clickable is not True:')
        self.assertLess(runtime, clickable)
        gap = source[clickable:source.index(start)]
        self.assertIn('del observed, evidence', gap)
        self.assertNotIn('(', gap)  # No call between the local gate and normalization.

    def test_production_scope_and_all_protected_content(self):
        changed = subprocess.check_output([
            'git', 'diff', HEAD, '--name-only', '--', 'nayeon/agent', 'nayeon/services'
        ], cwd=ROOT).decode().splitlines()
        self.assertEqual(changed, ['nayeon/agent/pointer_binding.py'])
        self.assertEqual(subprocess.check_output([
            'git', 'ls-files', '--others', '--exclude-standard', '--',
            'nayeon/agent', 'nayeon/services', 'nayeon/capabilities', 'nayeon/policy'
        ], cwd=ROOT), b'')
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', HEAD, '--', 'nayeon'],
                                        cwd=ROOT).decode().splitlines()
        for path in paths:
            # Phase 8.2 intentionally migrates OpenAIProvider's secret dependency;
            # its new exact boundary is frozen by the Phase 8.2 security guards.
            if path in ('nayeon/agent/pointer_binding.py',
                        'nayeon/brain/providers/openai.py'):
                continue
            baseline = subprocess.check_output(['git', 'show', HEAD + ':' + path], cwd=ROOT)
            self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'),
                             baseline.replace(b'\r\n', b'\n'), path)


if __name__ == '__main__':
    unittest.main()
