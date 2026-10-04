"""Phase 6.15 deterministic fake-only coordinate-contract tests."""
from copy import copy, deepcopy
import ctypes
from ctypes import wintypes as W
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import pickle
import unittest
from unittest.mock import Mock, call, patch

from nayeon.services import pointer_coordinate_contract as m
from nayeon.services.pointer_hit_validation import _ProposedPoint as Point
from nayeon.verification.contract import VerificationStatus as V


class Int(int):
    pass


class Tests(unittest.TestCase):
    def certify(self, values=(2, 2), point=(17, -23), platform="win32"):
        native = Mock(spec=["awareness"])
        native.awareness.side_effect = values
        result = m._PhysicalCoordinateContractService(
            native=native, platform=platform).certify(Point(*point))
        return result, native

    def test_verified_exact_identity_and_read_order(self):
        result, native = self.certify()
        self.assertIs(result.status, V.VERIFIED)
        self.assertIs(result.evidence.point.__class__, Point)
        self.assertEqual((result.evidence.point.x, result.evidence.point.y), (17, -23))
        self.assertEqual(result.evidence.awareness, 2)
        self.assertEqual(native.mock_calls, [call.awareness(), call.awareness()])

    def test_non_per_monitor_never_certifies(self):
        for values in ((0, 0), (1, 1), (2, 1), (1, 2), (0, 2), (2, 0)):
            with self.subTest(values=values):
                result, native = self.certify(values)
                self.assertIs(result.status, V.INDETERMINATE)
                self.assertIsNone(result.evidence)
                self.assertEqual(native.awareness.call_count, 2)

    def test_never_not_verified(self):
        for values in ((2, 2), (0, 0), (1, 1), (2, 1)):
            self.assertIsNot(self.certify(values)[0].status, V.NOT_VERIFIED)

    def test_malformed_awareness_fails_closed(self):
        for bad in (None, True, False, 2.0, "2", Int(2), -1, 3, [], {}):
            for values in ((bad, 2), (2, bad)):
                with self.subTest(bad=bad, values=values):
                    result, native = self.certify(values)
                    self.assertIs(result.status, V.INDETERMINATE)
                    self.assertIsNone(result.evidence)
                    self.assertGreaterEqual(native.awareness.call_count, 1)
                    self.assertLessEqual(native.awareness.call_count, 2)

    def test_read_failure_no_retry(self):
        for index in (0, 1):
            native = Mock(spec=["awareness"])
            sequence = [2, 2]
            sequence[index] = OSError("secret native detail")
            native.awareness.side_effect = sequence
            result = m._PhysicalCoordinateContractService(
                native=native, platform="win32").certify(Point(0, 0))
            self.assertIs(result.status, V.INDETERMINATE)
            self.assertIsNone(result.evidence)
            self.assertEqual(native.awareness.call_count, index + 1)
            self.assertNotIn("secret", repr(result))

    def test_wrong_point_before_native_reads(self):
        class Sub(Point):
            pass
        native = Mock(spec=["awareness"])
        service = m._PhysicalCoordinateContractService(native=native, platform="win32")
        for point in (None, (0, 0), [0, 0], {}, True, Mock(), Sub(0, 0)):
            self.assertIs(service.certify(point).status, V.INDETERMINATE)
        native.awareness.assert_not_called()

    def test_tampered_point_before_native_reads(self):
        for field in ("x", "y"):
            for bad in (True, Int(0), 1.0, None, 2**31, -(2**31)-1):
                point = Point(0, 0)
                object.__setattr__(point, field, bad)
                native = Mock(spec=["awareness"])
                result = m._PhysicalCoordinateContractService(
                    native=native, platform="win32").certify(point)
                self.assertIs(result.status, V.INDETERMINATE)
                native.awareness.assert_not_called()

    def test_point_tamper_after_reads_fails_closed(self):
        point = Point(7, 8)
        native = Mock(spec=["awareness"])
        def awareness():
            if native.awareness.call_count == 2:
                object.__setattr__(point, "x", 9)
            return 2
        native.awareness.side_effect = awareness
        result = m._PhysicalCoordinateContractService(
            native=native, platform="win32").certify(point)
        self.assertIs(result.status, V.INDETERMINATE)
        self.assertIsNone(result.evidence)

    def test_platform_fail_closed_no_native(self):
        for platform in ("linux", "darwin", "", True, None):
            native = Mock(spec=["awareness"])
            result = m._PhysicalCoordinateContractService(
                native=native, platform=platform).certify(Point(0, 0))
            self.assertIs(result.status, V.INDETERMINATE)
            native.awareness.assert_not_called()

    def test_default_platform_factory(self):
        native = Mock(spec=["awareness"])
        native.awareness.side_effect = [2, 2]
        with patch.object(m.sys, "platform", "win32"), patch.object(
                m, "_DpiCoordinateNative", return_value=native) as factory:
            result = m._PhysicalCoordinateContractService().certify(Point(0, 0))
        self.assertIs(result.status, V.VERIFIED)
        factory.assert_called_once_with()

    def test_native_signatures_and_values(self):
        dll = Mock(spec=["GetThreadDpiAwarenessContext",
                         "GetAwarenessFromDpiAwarenessContext"])
        dll.GetThreadDpiAwarenessContext.return_value = 123
        dll.GetAwarenessFromDpiAwarenessContext.return_value = 2
        with patch.object(m.sys, "platform", "win32"), patch.object(
                ctypes, "WinDLL", return_value=dll, create=True) as loader:
            native = m._DpiCoordinateNative()
            self.assertEqual(native.awareness(), 2)
        loader.assert_called_once_with("user32")
        self.assertEqual(dll.GetThreadDpiAwarenessContext.argtypes, [])
        self.assertIs(dll.GetThreadDpiAwarenessContext.restype, W.HANDLE)
        self.assertEqual(dll.GetAwarenessFromDpiAwarenessContext.argtypes, [W.HANDLE])
        self.assertIs(dll.GetAwarenessFromDpiAwarenessContext.restype, ctypes.c_int)
        dll.GetThreadDpiAwarenessContext.assert_called_once_with()
        dll.GetAwarenessFromDpiAwarenessContext.assert_called_once_with(123)

    def test_native_invalid_context_or_awareness(self):
        dll = Mock(spec=["GetThreadDpiAwarenessContext",
                         "GetAwarenessFromDpiAwarenessContext"])
        with patch.object(m.sys, "platform", "win32"), patch.object(
                ctypes, "WinDLL", return_value=dll, create=True):
            native = m._DpiCoordinateNative()
        for context, awareness in ((0, 2), (None, 2), (123, -1), (123, 3)):
            dll.reset_mock()
            dll.GetThreadDpiAwarenessContext.return_value = context
            dll.GetAwarenessFromDpiAwarenessContext.return_value = awareness
            with self.assertRaises((OSError, ValueError)):
                native.awareness()

    def test_native_platform_guard(self):
        with patch.object(m.sys, "platform", "linux"), patch.object(
                ctypes, "WinDLL", create=True) as loader:
            with self.assertRaises(OSError):
                m._DpiCoordinateNative()
            loader.assert_not_called()

    def test_invariants_and_subclasses(self):
        evidence = m._PhysicalCoordinateEvidence(Point(0, 0), 2)
        for args in (("verified", evidence), (V.VERIFIED, None),
                     (V.NOT_VERIFIED, None), (V.INDETERMINATE, evidence)):
            with self.assertRaises((TypeError, ValueError)):
                m._PhysicalCoordinateResult(*args)
        for bad in (0, 1, True, Int(2), 2.0, None):
            with self.assertRaises((TypeError, ValueError)):
                replace(evidence, awareness=bad)
        class E(m._PhysicalCoordinateEvidence):
            pass
        class R(m._PhysicalCoordinateResult):
            pass
        with self.assertRaises(TypeError):
            E(Point(0, 0), 2)
        with self.assertRaises(TypeError):
            R()

    def test_privacy_frozen_slotted(self):
        result = self.certify()[0]
        native = object.__new__(m._DpiCoordinateNative)
        for value in (result, result.evidence, result.evidence.point, native,
                      m._PhysicalCoordinateContractService(),
                      m._PhysicalCoordinateResult()):
            self.assertFalse(hasattr(value, "__dict__"))
            self.assertEqual(repr(value), type(value).__name__ + "(<private>)")
            self.assertEqual(str(value), repr(value))
            for operation in (copy, deepcopy, pickle.dumps, json.dumps):
                with self.assertRaises(TypeError):
                    operation(value)
        with self.assertRaises(FrozenInstanceError):
            result.evidence.awareness = 1

    def test_source_guards(self):
        source = Path(m.__file__).read_text()
        self.assertEqual(m.__all__, ())
        for forbidden in ("SendInput", "SetCursorPos", "mouse_event", "keybd_event",
                          "pyautogui", "GetCursorPos", "SetForegroundWindow",
                          "SetProcessDpiAwareness", "SetThreadDpiAwarenessContext",
                          "UIAutomation", "ElementFromPoint", "screenshot", "OCR",
                          "AuditService", "UndoService", "StructuredCapability",
                          "IntentDispatcher"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(
            {name for name in vars(m._PhysicalCoordinateContractService)
             if not name.startswith("_")}, {"certify"})
        self.assertEqual(
            {name for name in vars(m._DpiCoordinateNative)
             if not name.startswith("_")}, {"awareness"})


if __name__ == "__main__":
    unittest.main()
