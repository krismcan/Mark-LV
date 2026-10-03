"""Phase 6.7 deterministic tests; no live native reads or input."""
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, fields, replace
import ctypes
import json
import pickle
import unittest
from unittest.mock import Mock, call, patch

from nayeon.services.pointer_hit_validation import (
    _PointerHitResult, _PointerHitValidationService, _ProposedPoint,
)
from nayeon.services.target_validation import MAX_AGE_NS, _TargetBinding
from nayeon.services.window_focus import _FocusBinding
from nayeon.services.keyboard_text import _TextBinding
from nayeon.verification.contract import VerificationStatus as V
from tests.test_foreground_observation import CONTEXT as C, IDENTITY as I


class PointerHitValidationTests(unittest.TestCase):
    def setUp(self):
        self.point = _ProposedPoint(31415, -27182)
        self.target = _TargetBinding(I, C, 10, 20)
        self.native = Mock(spec=['context', 'window_at', 'root', 'identity'])
        self.native.context.return_value = C
        self.native.window_at.return_value = I.hwnd
        self.native.root.return_value = I.hwnd
        self.native.identity.return_value = I
        self.clock = Mock(side_effect=[30, 40])
        self.calls = Mock()
        self.calls.attach_mock(self.clock, 'clock')
        for name in ('context', 'window_at', 'root', 'identity'):
            self.calls.attach_mock(getattr(self.native, name), name)
        self.service = _PointerHitValidationService(
            native=self.native, platform='win32', clock=self.clock)

    def status(self):
        return self.service.validate_hit(self.point, self.target).status

    def test_stable_root_exact_read_order_and_unchanged_target(self):
        self.assertIs(self.status(), V.VERIFIED)
        self.assertEqual([c[0] for c in self.calls.mock_calls],
                         ['clock', 'context', 'window_at', 'root', 'identity',
                          'window_at', 'root', 'identity', 'context', 'clock'])
        self.assertEqual(self.native.window_at.call_args_list,
                         [call((self.point.x, self.point.y))] * 2)
        self.assertEqual(self.native.identity.call_args_list, [call(I.hwnd)] * 2)
        self.assertEqual(self.target, _TargetBinding(I, C, 10, 20))

    def test_changing_children_under_approved_root(self):
        self.native.window_at.side_effect = [I.hwnd + 1, I.hwnd + 2]
        self.assertIs(self.status(), V.VERIFIED)
        self.assertEqual(self.native.root.call_args_list,
                         [call(I.hwnd + 1), call(I.hwnd + 2)])

    def test_stable_different_root(self):
        other = replace(I, hwnd=I.hwnd + 1, root=I.hwnd + 1)
        self.native.root.return_value = other.hwnd
        self.native.identity.return_value = other
        self.assertIs(self.status(), V.NOT_VERIFIED)

    def test_valid_stable_identity_mismatches(self):
        for field, value in (('pid', I.pid + 1), ('tid', I.tid + 1),
                             ('creation_time', I.creation_time + 1),
                             ('executable', 'replacement.exe'), ('window_class', 'Other')):
            with self.subTest(field=field):
                self.setUp()
                self.native.identity.return_value = replace(I, **{field: value})
                self.assertIs(self.status(), V.NOT_VERIFIED)

    def test_root_or_identity_drift_is_inconclusive(self):
        other = replace(I, hwnd=I.hwnd + 1, root=I.hwnd + 1)
        self.native.root.side_effect = [I.hwnd, other.hwnd]
        self.native.identity.side_effect = [I, other]
        self.assertIs(self.status(), V.INDETERMINATE)
        self.setUp()
        self.native.identity.side_effect = [I, replace(I, creation_time=I.creation_time + 1)]
        self.assertIs(self.status(), V.INDETERMINATE)

    def test_changed_unsupported_or_different_supported_context(self):
        other = replace(C, session=C.session + 1)
        for contexts in ([C, other], [other, other], [C, replace(C, active=False)],
                         [None, C], [C, {}]):
            with self.subTest(contexts=contexts):
                self.setUp()
                self.native.context.side_effect = contexts
                self.assertIs(self.status(), V.INDETERMINATE)

    def test_unsupported_platform_initializes_nothing(self):
        self.service._platform = 'linux'
        self.service._native = None
        with patch('nayeon.services.windows_pointer._HitTestNative') as factory:
            self.assertIs(self.status(), V.INDETERMINATE)
            factory.assert_not_called()
        self.assertEqual(self.calls.mock_calls, [])

    def test_clock_brackets_fresh_native_setup(self):
        self.service._native = None
        with patch('nayeon.services.windows_pointer._HitTestNative', return_value=self.native) as factory:
            self.calls.attach_mock(factory, 'factory')
            self.assertIs(self.status(), V.VERIFIED)
        self.assertEqual([c[0] for c in self.calls.mock_calls][:3],
                         ['clock', 'factory', 'context'])

    def test_zero_or_malformed_handles_at_either_sample(self):
        huge = 2 ** (ctypes.sizeof(ctypes.c_void_p) * 8)
        for name in ('window_at', 'root'):
            for value in (0, None, True, False, -1, huge, '1', 1.0):
                for index in (0, 1):
                    with self.subTest(name=name, value=value, index=index):
                        self.setUp()
                        samples = [I.hwnd] * 2
                        samples[index] = value
                        getattr(self.native, name).side_effect = samples
                        self.assertIs(self.status(), V.INDETERMINATE)

    def test_invalid_inconsistent_identity_at_either_sample(self):
        bad = [None, {}, replace(I, pid=0), replace(I, tid=0),
               replace(I, creation_time=0), replace(I, executable=' '),
               replace(I, window_class=''), replace(I, session=0),
               replace(I, desktop='Other'), replace(I, root=I.root + 1),
               replace(I, hwnd=I.hwnd + 1, root=I.hwnd + 1)]
        for value in bad:
            for index in (0, 1):
                with self.subTest(value=value, index=index):
                    self.setUp()
                    samples = [I] * 2
                    samples[index] = value
                    self.native.identity.side_effect = samples
                    self.assertIs(self.status(), V.INDETERMINATE)

    def test_native_cleanup_errors_are_sanitized_no_retry(self):
        for name in ('context', 'window_at', 'root', 'identity'):
            for index in (0, 1):
                with self.subTest(name=name, index=index):
                    self.setUp()
                    good = C if name == 'context' else I if name == 'identity' else I.hwnd
                    getattr(self.native, name).side_effect = ([good] * index
                                                            + [OSError('private native error')])
                    result = self.service.validate_hit(self.point, self.target)
                    self.assertIs(result.status, V.INDETERMINATE)
                    self.assertNotIn('error', repr(result))
                    self.assertEqual(getattr(self.native, name).call_count, index + 1)

    def test_point_types_range_and_arity(self):
        class Int(int):
            pass
        for value in (True, False, 1.0, '1', None, Int(1)):
            for args in ((value, 1), (1, value)):
                with self.assertRaises(TypeError):
                    _ProposedPoint(*args)
        for value in (-(2 ** 31) - 1, 2 ** 31):
            for args in ((value, 0), (0, value)):
                with self.assertRaises(ValueError):
                    _ProposedPoint(*args)
        for args in ((), (1,), (1, 2, 3)):
            with self.assertRaises(TypeError):
                _ProposedPoint(*args)
        for point in (None, (), (1,), (1, 2), (1, 2, 3), [1, 2], {}, True):
            self.assertIs(self.service.validate_hit(point, self.target).status, V.INDETERMINATE)
        self.assertEqual(self.calls.mock_calls, [])

    def test_long_boundaries_passed_unchanged(self):
        self.point = _ProposedPoint(-(2 ** 31), 2 ** 31 - 1)
        self.assertIs(self.status(), V.VERIFIED)
        self.native.window_at.assert_called_with((-(2 ** 31), 2 ** 31 - 1))

    def test_wrong_legacy_reconstructed_types_and_tampering_no_reads(self):
        class Target(_TargetBinding):
            pass
        class Point(_ProposedPoint):
            pass
        with self.assertRaises(ValueError):
            Target(I, C, 10, 20)
        for target in (None, {}, Mock(), _FocusBinding(I, C),
                       _TextBinding(_FocusBinding(I, C), 'test')):
            self.assertIs(self.service.validate_hit(self.point, target).status, V.INDETERMINATE)
        self.assertIs(self.service.validate_hit(Point(1, 2), self.target).status, V.INDETERMINATE)
        for field, value in (('identity', None), ('context', None),
                             ('acquired_to_ns', True), ('acquired_from_ns', 21)):
            target = _TargetBinding(I, C, 10, 20)
            object.__setattr__(target, field, value)
            self.assertIs(self.service.validate_hit(self.point, target).status, V.INDETERMINATE)
        object.__setattr__(self.point, 'x', True)
        self.assertIs(self.status(), V.INDETERMINATE)
        self.assertEqual(self.calls.mock_calls, [])

    def test_stale_invalid_start_no_reads_or_reacquisition(self):
        for start in (20 + MAX_AGE_NS + 1, 19, -1, True, None, 30.0):
            self.setUp()
            self.clock.side_effect = [start]
            self.assertIs(self.status(), V.INDETERMINATE)
            self.assertEqual(self.native.mock_calls, [])
            self.assertEqual(self.clock.call_count, 1)

    def test_end_time_inclusive_freshness_limit(self):
        for times, expected in (((20, 20), V.VERIFIED),
                                ((20, 20 + MAX_AGE_NS), V.VERIFIED),
                                ((20 + MAX_AGE_NS, 20 + MAX_AGE_NS), V.VERIFIED),
                                ((30, 20 + MAX_AGE_NS + 1), V.INDETERMINATE),
                                ((30, 29), V.INDETERMINATE), ((30, True), V.INDETERMINATE),
                                ((30, None), V.INDETERMINATE)):
            self.setUp()
            self.clock.side_effect = times
            self.assertIs(self.status(), expected)

    def test_slotted_redacted_local_only_models_and_service(self):
        result = self.service.validate_hit(self.point, self.target)
        for value in (self.point, result, self.service):
            self.assertFalse(hasattr(value, '__dict__'))
            self.assertEqual(repr(value), type(value).__name__ + '(<private>)')
            self.assertEqual(str(value), repr(value))
            for serialize in (copy, deepcopy, pickle.dumps, json.dumps):
                with self.assertRaises(TypeError):
                    serialize(value)
        self.assertEqual([f.name for f in fields(result)], ['status'])
        with self.assertRaises(FrozenInstanceError):
            self.point.x = 0
        with self.assertRaises(FrozenInstanceError):
            result.status = V.VERIFIED
        with self.assertRaises(TypeError):
            _PointerHitResult('verified')
        self.assertEqual(self.service.__slots__, ('_native', '_platform', '_clock'))

    def test_invalid_initial_context_stops_before_hit_reads(self):
        self.native.context.return_value = replace(C, active=False)
        self.assertIs(self.status(), V.INDETERMINATE)
        self.native.window_at.assert_not_called()
        self.native.root.assert_not_called()
        self.native.identity.assert_not_called()

    def test_private_service_has_no_mutation_or_public_route(self):
        from pathlib import Path
        root = Path(__file__).parents[1]
        source = (root / 'nayeon/services/pointer_hit_validation.py').read_text()
        for forbidden in ('GetCursorPos', 'SetCursorPos', 'SendInput', 'mouse_event',
                          'keybd_event', 'pyautogui', 'SetForegroundWindow',
                          'AttachThreadInput', 'screenshot', 'OCR', 'UIAutomation',
                          'playwright', 'selenium', 'AuditService', 'UndoService'):
            self.assertNotIn(forbidden, source)
        for path in ('nayeon/services/__init__.py', 'nayeon/agent/router.py'):
            self.assertNotIn('pointer_hit_validation', (root / path).read_text())
        # Phase 6.8 permits exactly one private approval-binding integration.
        binding_source = (root / 'nayeon/agent/pointer_binding.py').read_text()
        self.assertIn('pointer_hit_validation', binding_source)
        self.assertIn('_PointerHitValidationService', binding_source)
        for capability_file in (root / 'nayeon/capabilities').glob('*.py'):
            self.assertNotIn(
                'pointer_hit_validation',
                capability_file.read_text(),
                capability_file.name,
            )


if __name__ == '__main__':
    unittest.main()
