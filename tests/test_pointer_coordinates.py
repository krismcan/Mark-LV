"""Phase 6.10 deterministic fake-only tests."""
from copy import copy, deepcopy
import ctypes
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import pickle
import unittest
from unittest.mock import Mock, call, patch
from nayeon.services import pointer_coordinates as m
from nayeon.services.pointer_hit_validation import _ProposedPoint as Point
from nayeon.verification.contract import VerificationStatus as V

class Int(int):
    pass

class CoordinateTests(unittest.TestCase):
    def sample(self, point=(0, 0), geometry=(0, 0, 1920, 1080)):
        native = Mock(spec=['metric'])
        native.metric.side_effect = geometry
        result = m._PointerCoordinateService(native=native, platform='win32').normalize(Point(*point))
        return result, native

    def test_read_order(self):
        result, native = self.sample()
        self.assertIs(result.status, V.VERIFIED)
        self.assertEqual(native.mock_calls, [call.metric(i) for i in (76, 77, 78, 79)])

    def test_multimonitor_negative_origin_corners(self):
        for point, expected in (((-1920, -1080), (0, 0)), ((3839, -1080), (65535, 0)),
                                ((-1920, 2159), (0, 65535)), ((3839, 2159), (65535, 65535))):
            result, _ = self.sample(point, (-1920, -1080, 5760, 3240))
            self.assertIs(result.status, V.VERIFIED)
            self.assertEqual((result.evidence.normalized_x, result.evidence.normalized_y), expected)

    def test_positive_origin_endpoint(self):
        e = self.sample((109, 219), (100, 200, 10, 20))[0].evidence
        self.assertEqual((e.normalized_x, e.normalized_y), (65535, 65535))

    def test_floor_and_negative_interior(self):
        for point, geometry, expected in (((1, 2), (0, 0, 3, 4), (32767, 43690)),
                                          ((0, 0), (-100, -200, 201, 401), (32767, 32767))):
            e = self.sample(point, geometry)[0].evidence
            self.assertEqual((e.normalized_x, e.normalized_y), expected)

    def test_one_coordinate_axes(self):
        for geometry, point, expected in (((-7, 9, 1, 1), (-7, 9), (0, 0)),
                                          ((-7, 9, 1, 2), (-7, 10), (0, 65535)),
                                          ((-7, 9, 2, 1), (-6, 9), (65535, 0))):
            e = self.sample(point, geometry)[0].evidence
            self.assertEqual((e.normalized_x, e.normalized_y), expected)

    def test_outside_no_clamp(self):
        for geometry, points in (((-10, 20, 10, 20), ((-11, 20), (0, 20), (-10, 19), (-10, 40))),
                                  ((0, 0, 1, 1), ((0, 1), (1, 0), (-1, 0), (0, -1)))):
            for point in points:
                result, native = self.sample(point, geometry)
                self.assertIs(result.status, V.INDETERMINATE)
                self.assertIsNone(result.evidence)
                self.assertEqual(native.metric.call_count, 4)

    def test_malformed_metrics_every_position(self):
        for index in range(4):
            for bad in (None, True, False, 0.0, '0', Int(1), ctypes.c_int(1), [], {}, -(2**31)-1, 2**31):
                with self.subTest(index=index, bad=bad):
                    geometry = [0, 0, 10, 10]
                    geometry[index] = bad
                    result, native = self.sample(geometry=geometry)
                    self.assertIs(result.status, V.INDETERMINATE)
                    self.assertIsNone(result.evidence)
                    self.assertEqual(native.metric.call_count, 4)

    def test_nonpositive_extents(self):
        for index in (2, 3):
            for bad in (0, -1, -(2**31)):
                geometry = [0, 0, 10, 10]
                geometry[index] = bad
                self.assertIs(self.sample(geometry=geometry)[0].status, V.INDETERMINATE)

    def test_last_coordinate_long_boundary(self):
        for g in ((2**31-1, 0, 1, 1), (0, 2**31-1, 1, 1),
                  (2**31-2, 0, 2, 1), (0, 2**31-2, 1, 2)):
            self.assertIs(self.sample((g[0], g[1]), g)[0].status, V.VERIFIED)
        for g in ((2**31-1, 0, 2, 1), (0, 2**31-1, 1, 2)):
            self.assertIs(self.sample((g[0], g[1]), g)[0].status, V.INDETERMINATE)

    def test_last_long_coordinate_maps_to_endpoint(self):
        for geometry, point, expected in (
            ((2**31-2, 0, 2, 1), (2**31-1, 0), (65535, 0)),
            ((0, 2**31-2, 1, 2), (0, 2**31-1), (0, 65535)),
        ):
            with self.subTest(geometry=geometry):
                result, _ = self.sample(point, geometry)
                self.assertIs(result.status, V.VERIFIED)
                self.assertEqual((result.evidence.normalized_x,
                                  result.evidence.normalized_y), expected)
                result.evidence.__post_init__()

    def test_safe_long_edges_and_product(self):
        for g in ((-(2**31), -(2**31), 2**31-1, 2**31-1),
                  (0, 0, 2**31-1, 2**31-1), (2**31-2, 2**31-2, 1, 1)):
            result, _ = self.sample((g[0]+g[2]-1, g[1]+g[3]-1), g)
            self.assertIs(result.status, V.VERIFIED)
            self.assertEqual(result.evidence.normalized_x, 0 if g[2] == 1 else 65535)

    def test_long_min_max_one_cell_combinations(self):
        for x in (m._LONG_MIN, m._LONG_MAX):
            for y in (m._LONG_MIN, m._LONG_MAX):
                result, _ = self.sample((x, y), (x, y, 1, 1))
                self.assertIs(result.status, V.VERIFIED)
                self.assertEqual((result.evidence.normalized_x,
                                  result.evidence.normalized_y), (0, 0))
    def test_monotone_bounded(self):
        values = [self.sample((x, 0), (-100, 0, 301, 1))[0].evidence.normalized_x for x in range(-100, 201)]
        self.assertEqual(values, sorted(values))
        self.assertEqual((values[0], values[-1]), (0, 65535))

    def test_wrong_point_types_no_reads(self):
        class Subpoint(Point):
            pass
        native = Mock(spec=['metric'])
        service = m._PointerCoordinateService(native=native, platform='win32')
        for point in (None, (0, 0), [0, 0], {}, True, Mock(), Subpoint(0, 0)):
            self.assertIs(service.normalize(point).status, V.INDETERMINATE)
        native.metric.assert_not_called()

    def test_tampered_point_no_reads(self):
        for field in ('x', 'y'):
            for bad in (True, Int(0), 1.0, None, 2**31, -(2**31)-1):
                point = Point(0, 0)
                object.__setattr__(point, field, bad)
                native = Mock(spec=['metric'])
                self.assertIs(m._PointerCoordinateService(native=native, platform='win32').normalize(point).status, V.INDETERMINATE)
                native.metric.assert_not_called()

    def test_unsupported_platform_no_factory(self):
        for platform in ('linux', 'darwin', '', True, None):
            with patch.object(m.sys, 'platform', 'linux'), patch.object(m, '_CoordinateNative') as factory:
                self.assertIs(m._PointerCoordinateService(platform=platform).normalize(Point(0, 0)).status, V.INDETERMINATE)
                factory.assert_not_called()

    def test_each_read_failure_no_retry_or_rescue(self):
        for index in range(4):
            native = Mock(spec=['metric'])
            native.metric.side_effect = [0, 0, 10, 10][:index] + [OSError('secret native detail')]
            with patch.object(m, '_CoordinateNative') as factory:
                result = m._PointerCoordinateService(native=native, platform='win32').normalize(Point(0, 0))
                factory.assert_not_called()
            self.assertIs(result.status, V.INDETERMINATE)
            self.assertEqual(native.metric.call_count, index+1)
            self.assertNotIn('secret', repr(result))

    def test_factory_failure(self):
        with patch.object(m, '_CoordinateNative', side_effect=OSError('private')) as factory:
            self.assertIs(m._PointerCoordinateService(platform='win32').normalize(Point(0, 0)).status, V.INDETERMINATE)
        factory.assert_called_once_with()

    def test_default_platform_factory(self):
        native = Mock(spec=['metric'])
        native.metric.side_effect = [0, 0, 1, 1]
        with patch.object(m.sys, 'platform', 'win32'), patch.object(m, '_CoordinateNative', return_value=native) as factory:
            self.assertIs(m._PointerCoordinateService().normalize(Point(0, 0)).status, V.VERIFIED)
        factory.assert_called_once_with()

    def test_native_signature(self):
        dll = Mock(spec=['GetSystemMetrics'])
        dll.GetSystemMetrics.return_value = -1920
        with patch.object(m.sys, 'platform', 'win32'), patch.object(ctypes, 'WinDLL', return_value=dll, create=True) as loader:
            native = m._CoordinateNative()
            self.assertEqual(native.metric(76), -1920)
        loader.assert_called_once_with('user32')
        self.assertEqual(dll.GetSystemMetrics.argtypes, [ctypes.c_int])
        self.assertIs(dll.GetSystemMetrics.restype, ctypes.c_int)
        dll.GetSystemMetrics.assert_called_once_with(76)

    def test_native_platform_guard(self):
        with patch.object(m.sys, 'platform', 'linux'), patch.object(ctypes, 'WinDLL', create=True) as loader:
            with self.assertRaises(OSError):
                m._CoordinateNative()
            loader.assert_not_called()

    def test_privacy_frozen_slotted_serialization(self):
        result = self.sample((31415, -27182), (30000, -30000, 2000, 4000))[0]
        native = object.__new__(m._CoordinateNative)  # No native initialization.
        for value in (result, result.evidence, result.evidence.point, native,
                      m._PointerCoordinateService(), m._CoordinateResult()):
            self.assertFalse(hasattr(value, '__dict__'))
            self.assertEqual(repr(value), type(value).__name__+'(<private>)')
            self.assertEqual(str(value), repr(value))
            for operation in (copy, deepcopy, pickle.dumps, json.dumps):
                with self.assertRaises(TypeError):
                    operation(value)
            with self.assertRaises(TypeError):
                value.__reduce_ex__(5)
        for value, field, replacement in ((result, 'status', V.INDETERMINATE), (result.evidence, 'left', 0)):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, field, replacement)

    def test_evidence_validation(self):
        evidence = self.sample()[0].evidence
        for field, bad in (('point', (0, 0)), ('left', True), ('top', Int(0)), ('width', 0),
                           ('height', -1), ('left', 2**31-1), ('point', Point(-1, 0)),
                           ('normalized_x', True), ('normalized_y', Int(0)),
                           ('normalized_x', -1), ('normalized_y', 65536), ('normalized_x', 1)):
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                replace(evidence, **{field: bad})

    def test_result_invariants_revalidation(self):
        evidence = self.sample()[0].evidence
        for args in (('verified', evidence), (V.VERIFIED, None), (V.VERIFIED, {}),
                     (V.NOT_VERIFIED, None), (V.INDETERMINATE, evidence)):
            with self.assertRaises((TypeError, ValueError)):
                m._CoordinateResult(*args)
        object.__setattr__(evidence, 'normalized_x', 1)
        with self.assertRaises(ValueError):
            m._CoordinateResult(V.VERIFIED, evidence)

    def test_evidence_result_subclasses(self):
        class Evidence(m._CoordinateEvidence):
            pass
        class Result(m._CoordinateResult):
            pass
        with self.assertRaises(TypeError):
            Evidence(Point(0, 0), 0, 0, 1, 1, 0, 0)
        with self.assertRaises(TypeError):
            Result()

    def test_private_no_mutation_routes(self):
        root = Path(__file__).parents[1]
        source = (root/'nayeon/services/pointer_coordinates.py').read_text()
        self.assertEqual(m.__all__, ())
        for forbidden in ('SendInput', 'SetCursorPos', 'mouse_event', 'keybd_event', 'pyautogui',
                          'GetCursorPos', 'SetForegroundWindow', 'AttachThreadInput', 'screenshot',
                          'OCR', 'UIAutomation', 'playwright', 'selenium', 'AuditService', 'UndoService'):
            self.assertNotIn(forbidden, source)
        for cls, expected in ((m._PointerCoordinateService, {'normalize'}),
                              (m._CoordinateNative, {'metric'})):
            self.assertEqual({name for name in vars(cls) if not name.startswith('_')}, expected)

if __name__ == '__main__':
    unittest.main()
