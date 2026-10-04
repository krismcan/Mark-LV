"""Phase 6.16 deterministic fake-only scoped DPI execution-context tests."""
from copy import copy, deepcopy
import ctypes
from ctypes import wintypes as W
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import pickle
import threading
import unittest
from unittest.mock import Mock, patch

from nayeon.services import dpi_execution_context as m
from nayeon.services import pointer_coordinate_contract as c
from nayeon.services.pointer_hit_validation import _ProposedPoint as Point
from nayeon.verification.contract import VerificationStatus as V


class Int(int):
    pass


class Fake:
    def __init__(self, awareness=0, overrides=None):
        self.prior = 123
        self.current = self.prior
        self.prior_awareness = awareness
        self.overrides = overrides or {}
        self.events = []
        self.counts = {}

    def record(self, name, args=(), default=None):
        self.events.append((name, args, threading.current_thread()))
        self.counts[name] = self.counts.get(name, 0) + 1
        value = self.overrides.get((name, self.counts[name]), default)
        if isinstance(value, BaseException):
            raise value
        return value() if callable(value) else value

    def factory(self):
        self.record("factory")
        return self

    def context(self):
        return self.record("context", default=self.current)

    def awareness(self, context):
        return self.record("awareness", (context,),
                           2 if context == m._PMV2 else self.prior_awareness)

    def valid(self, context):
        return self.record("valid", (context,), True)

    def equal(self, first, second):
        return self.record("equal", (first, second), first == second)

    def set_context(self, context):
        old = self.current
        self.current = context
        return self.record("set", (context,), old)

    def callback(self):
        return self.record("callback", default="private callback value")


class Tests(unittest.TestCase):
    def scope(self, fake):
        return m._ScopedDpiExecutionContext(native_factory=fake.factory, platform="win32")

    def closed(self, result):
        self.assertIs(type(result), m._ScopedDpiResult)
        self.assertFalse(result.completed)
        self.assertIsNone(result.value)
        self.assertNotIn("secret", repr(result))

    def unknown(self, result):
        self.assertIs(type(result), c._PhysicalCoordinateResult)
        self.assertIs(result.status, V.INDETERMINATE)
        self.assertIsNone(result.evidence)
        self.assertIsNot(result.status, V.NOT_VERIFIED)

    def test_clean_order_cardinality_worker_and_exact_restore(self):
        caller = threading.current_thread()
        for awareness in (0, 1, 2):
            with self.subTest(awareness=awareness):
                fake = Fake(awareness)
                real_thread = threading.Thread
                with patch.object(m.threading, "Thread", wraps=real_thread) as constructor:
                    result = self.scope(fake).run(fake.callback)
                self.assertTrue(result.completed)
                self.assertEqual(result.value, "private callback value")
                self.assertEqual(fake.current, fake.prior)
                constructor.assert_called_once()
                self.assertIs(constructor.call_args.kwargs["daemon"], False)
                expected = [
                    ("factory", ()), ("context", ()), ("awareness", (123,)),
                    ("valid", (m._PMV2,)), ("set", (m._PMV2,)),
                    ("equal", (123, 123)), ("context", ()),
                    ("equal", (m._PMV2, m._PMV2)), ("awareness", (m._PMV2,)),
                    ("callback", ()), ("set", (123,)),
                    ("equal", (m._PMV2, m._PMV2)), ("context", ()),
                    ("equal", (123, 123)), ("awareness", (123,)),
                ]
                self.assertEqual([(name, args) for name, args, _ in fake.events], expected)
                worker = fake.events[0][2]
                self.assertIsNot(worker, caller)
                self.assertFalse(worker.daemon)
                self.assertFalse(worker.is_alive())
                self.assertTrue(all(thread is worker for _, _, thread in fake.events))

    def test_new_owned_thread_each_run(self):
        fake = Fake()
        scope = self.scope(fake)
        self.assertTrue(scope.run(fake.callback).completed)
        first = fake.events[0][2]
        fake.events.clear()
        result = scope.run(lambda: None)
        self.assertTrue(result.completed)
        self.assertIsNone(result.value)
        self.assertIsNot(first, fake.events[0][2])

    def test_invalid_prior_context_no_set_or_callback(self):
        for bad in (None, 0, True, False, "123", 123.0, Int(123), [], {},
                    2 ** m._POINTER_BITS, -(2 ** (m._POINTER_BITS - 1)) - 1):
            with self.subTest(bad=bad):
                fake = Fake(overrides={("context", 1): bad})
                self.closed(self.scope(fake).run(fake.callback))
                self.assertEqual(fake.counts, {"factory": 1, "context": 1})

    def test_invalid_prior_awareness_and_invalid_target(self):
        for bad in (None, True, False, 0.0, "0", Int(0), -1, 3, [], {}):
            fake = Fake(overrides={("awareness", 1): bad})
            self.closed(self.scope(fake).run(fake.callback))
            self.assertNotIn("set", fake.counts)
            self.assertNotIn("callback", fake.counts)
        for bad in (False, None, 1, "true"):
            fake = Fake(overrides={("valid", 1): bad})
            self.closed(self.scope(fake).run(fake.callback))
            self.assertNotIn("set", fake.counts)
            self.assertNotIn("callback", fake.counts)

    def test_setup_mismatches_restore_once_without_callback(self):
        cases = [("set", 1, None), ("set", 1, 0), ("set", 1, True),
                 ("set", 1, 456), ("equal", 1, False),
                 ("context", 2, None), ("context", 2, 0),
                 ("context", 2, 456), ("equal", 2, False)]
        cases += [("awareness", 2, bad) for bad in
                  (0, 1, -1, 3, None, True, Int(2), 2.0)]
        for name, index, bad in cases:
            with self.subTest(name=name, index=index, bad=bad):
                fake = Fake(overrides={(name, index): bad})
                self.closed(self.scope(fake).run(fake.callback))
                self.assertEqual(fake.counts["set"], 2)
                self.assertNotIn("callback", fake.counts)
                self.assertEqual(fake.current, fake.prior)

    def test_callback_exception_restores_once_redacted(self):
        for error in (RuntimeError("secret callback"), KeyboardInterrupt("secret callback")):
            fake = Fake(overrides={("callback", 1): error})
            self.closed(self.scope(fake).run(fake.callback))
            self.assertEqual(fake.counts["callback"], 1)
            self.assertEqual(fake.counts["set"], 2)
            self.assertEqual(fake.current, fake.prior)

    def test_restoration_mismatches_discard_callback_value(self):
        cases = [("set", 2, None), ("set", 2, 0), ("set", 2, True),
                 ("set", 2, 456), ("equal", 3, False),
                 ("context", 3, None), ("context", 3, 456), ("equal", 4, False)]
        cases += [("awareness", 3, bad) for bad in
                  (1, 2, -1, 3, None, True, Int(0), 0.0)]
        for name, index, bad in cases:
            with self.subTest(name=name, index=index, bad=bad):
                fake = Fake(overrides={(name, index): bad})
                self.closed(self.scope(fake).run(fake.callback))
                self.assertEqual(fake.counts["callback"], 1)
                self.assertEqual(fake.counts["set"], 2)

    def test_every_native_and_comparison_exception_no_retry(self):
        for name, total in (("factory", 1), ("context", 3), ("awareness", 3),
                            ("valid", 1), ("set", 2), ("equal", 4)):
            for index in range(1, total + 1):
                with self.subTest(name=name, index=index):
                    fake = Fake(overrides={(name, index): OSError("secret native detail")})
                    self.closed(self.scope(fake).run(fake.callback))
                    self.assertLessEqual(fake.counts.get("set", 0), 2)
                    self.assertLessEqual(fake.counts.get("callback", 0), 1)
                    self.assertLessEqual(fake.counts.get("context", 0), 3)
                    self.assertLessEqual(fake.counts.get("awareness", 0), 3)
                    self.assertEqual(fake.counts["factory"], 1)
                    if name == "set" and index == 1:
                        self.assertEqual(fake.counts["set"], 2)
                        self.assertNotIn("callback", fake.counts)

    def test_unsupported_platform_zero_worker_native_callback(self):
        for platform in ("linux", "darwin", "", None, True):
            fake = Fake()
            with patch.object(m.threading, "Thread") as thread:
                self.closed(m._ScopedDpiExecutionContext(
                    native_factory=fake.factory, platform=platform).run(fake.callback))
                thread.assert_not_called()
            self.assertEqual(fake.events, [])
        fake = Fake()
        self.closed(self.scope(fake).run(123))
        self.assertEqual(fake.events, [])

    def coordinate_service(self, fake, factory=None):
        if factory is None:
            def factory():
                fake.record("contract_factory")
                reader = Mock(spec=["awareness"])
                reader.awareness.side_effect = lambda: fake.record(
                    "contract_awareness", default=2 if fake.current == m._PMV2 else 0)
                return c._PhysicalCoordinateContractService(native=reader, platform="win32")
        return m._ScopedPhysicalCoordinateService(scope=self.scope(fake), contract_factory=factory)

    def test_wrapper_existing_contract_same_point_worker_clean_restore(self):
        fake = Fake()
        point = Point(-17, 23)
        result = self.coordinate_service(fake).certify(point)
        self.assertIs(type(result), c._PhysicalCoordinateResult)
        self.assertIs(result.status, V.VERIFIED)
        self.assertIs(result.evidence.point, point)
        self.assertEqual(fake.current, fake.prior)
        names = [name for name, _, _ in fake.events]
        self.assertEqual(names.count("contract_factory"), 1)
        self.assertEqual(names.count("contract_awareness"), 2)
        self.assertLess(names.index("contract_awareness"), len(names) - 5)
        worker = fake.events[0][2]
        self.assertIsNot(worker, threading.current_thread())
        self.assertTrue(all(thread is worker for _, _, thread in fake.events))

    def test_wrapper_publishes_exact_existing_result_only_after_restore(self):
        point = Point(1, 2)
        verified = c._PhysicalCoordinateResult(V.VERIFIED, c._PhysicalCoordinateEvidence(point, 2))
        for failure in (False, True):
            fake = Fake(overrides={("set", 2): 0} if failure else None)
            reader = Mock(spec=["certify"])
            reader.certify.return_value = verified
            result = self.coordinate_service(fake, lambda: reader).certify(point)
            reader.certify.assert_called_once_with(point)
            if failure:
                self.unknown(result)
            else:
                self.assertIs(result, verified)

    def test_wrapper_wrong_bool_subclass_and_tampered_point_zero_native(self):
        class Sub(Point):
            pass
        points = [None, True, (0, 0), [0, 0], {}, Sub(0, 0)]
        for field in ("x", "y"):
            for bad in (True, Int(0), 0.0, None, 2**31, -(2**31)-1):
                point = Point(0, 0)
                object.__setattr__(point, field, bad)
                points.append(point)
        for point in points:
            fake = Fake()
            self.unknown(self.coordinate_service(fake).certify(point))
            self.assertEqual(fake.events, [])

    def test_wrapper_tamper_before_callback_during_contract_and_restore(self):
        for stage in ("set", "contract", "restore"):
            point = Point(1, 2)
            verified = c._PhysicalCoordinateResult(V.VERIFIED, c._PhysicalCoordinateEvidence(point, 2))
            fake = Fake()
            def tamper():
                object.__setattr__(point, "x", 9)
                return fake.prior if stage == "set" else m._PMV2
            if stage in ("set", "restore"):
                fake.overrides[("set", 1 if stage == "set" else 2)] = tamper
            def certify(value):
                if stage == "contract":
                    tamper()
                return verified
            reader = Mock(spec=["certify"])
            reader.certify.side_effect = certify
            self.unknown(self.coordinate_service(fake, lambda: reader).certify(point))
            self.assertEqual(fake.counts["set"], 2)
            self.assertEqual(reader.certify.call_count, 0 if stage == "set" else 1)

    def test_wrapper_rejects_malformed_results_other_point_and_not_verified(self):
        point = Point(1, 2)
        other = c._PhysicalCoordinateResult(V.VERIFIED, c._PhysicalCoordinateEvidence(Point(1, 2), 2))
        bad_status = c._PhysicalCoordinateResult()
        object.__setattr__(bad_status, "status", V.NOT_VERIFIED)
        bad_evidence = c._PhysicalCoordinateResult(V.VERIFIED, c._PhysicalCoordinateEvidence(point, 2))
        object.__setattr__(bad_evidence.evidence, "awareness", True)
        for value in (None, True, {}, other, bad_status, bad_evidence, c._PhysicalCoordinateResult()):
            reader = Mock(spec=["certify"])
            reader.certify.return_value = value
            self.unknown(self.coordinate_service(Fake(), lambda: reader).certify(point))

    def test_wrapper_platform_and_contract_factory_failure(self):
        fake = Fake()
        factory = Mock(side_effect=RuntimeError("secret contract detail"))
        self.unknown(self.coordinate_service(fake, factory).certify(Point(0, 0)))
        self.assertEqual(fake.counts["set"], 2)
        scope = m._ScopedDpiExecutionContext(native_factory=fake.factory, platform="linux")
        before = list(fake.events)
        self.unknown(m._ScopedPhysicalCoordinateService(
            scope=scope, contract_factory=factory).certify(Point(0, 0)))
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(fake.events, before)

    def test_native_five_signatures_and_target(self):
        names = ("GetThreadDpiAwarenessContext", "GetAwarenessFromDpiAwarenessContext",
                 "IsValidDpiAwarenessContext", "AreDpiAwarenessContextsEqual",
                 "SetThreadDpiAwarenessContext")
        dll = Mock(spec=names)
        dll.GetThreadDpiAwarenessContext.return_value = 123
        dll.GetAwarenessFromDpiAwarenessContext.return_value = 2
        dll.IsValidDpiAwarenessContext.return_value = 1
        dll.AreDpiAwarenessContextsEqual.return_value = 1
        dll.SetThreadDpiAwarenessContext.return_value = 123
        with patch.object(m.sys, "platform", "win32"), patch.object(
                ctypes, "WinDLL", return_value=dll, create=True) as loader:
            native = m._DpiExecutionNative()
            self.assertEqual(native.context(), 123)
            self.assertEqual(native.awareness(m._PMV2), 2)
            self.assertIs(native.valid(m._PMV2), True)
            self.assertIs(native.equal(123, 123), True)
            self.assertEqual(native.set_context(m._PMV2), 123)
        loader.assert_called_once_with("user32")
        self.assertEqual(m._PMV2, W.HANDLE(-4).value)
        for name, args, restype in zip(names,
                ([], [W.HANDLE], [W.HANDLE], [W.HANDLE, W.HANDLE], [W.HANDLE]),
                (W.HANDLE, ctypes.c_int, W.BOOL, W.BOOL, W.HANDLE)):
            self.assertEqual(getattr(dll, name).argtypes, args)
            self.assertIs(getattr(dll, name).restype, restype)
        dll.SetThreadDpiAwarenessContext.assert_called_once_with(m._PMV2)
        with patch.object(m.sys, "platform", "linux"), patch.object(
                ctypes, "WinDLL", create=True) as loader:
            with self.assertRaises(OSError):
                m._DpiExecutionNative()
            loader.assert_not_called()

    def test_default_native_facade_constructed_and_called_on_worker(self):
        events = []
        caller = threading.current_thread()
        names = ("GetThreadDpiAwarenessContext", "GetAwarenessFromDpiAwarenessContext",
                 "IsValidDpiAwarenessContext", "AreDpiAwarenessContextsEqual",
                 "SetThreadDpiAwarenessContext")
        dll = Mock(spec=names)
        def record(name, value):
            def invoke(*args):
                events.append((name, threading.current_thread()))
                return next(value) if hasattr(value, "__next__") else value
            return invoke
        dll.GetThreadDpiAwarenessContext.side_effect = record("get", iter((123, m._PMV2, 123)))
        dll.GetAwarenessFromDpiAwarenessContext.side_effect = record("awareness", iter((0, 2, 0)))
        dll.IsValidDpiAwarenessContext.side_effect = record("valid", 1)
        dll.AreDpiAwarenessContextsEqual.side_effect = record("equal", 1)
        dll.SetThreadDpiAwarenessContext.side_effect = record("set", iter((123, m._PMV2)))
        def load(name):
            self.assertEqual(name, "user32")
            events.append(("construct", threading.current_thread()))
            return dll
        with patch.object(m.sys, "platform", "win32"), patch.object(
                ctypes, "WinDLL", side_effect=load, create=True):
            result = m._ScopedDpiExecutionContext().run(record("callback", "value"))
        self.assertTrue(result.completed)
        self.assertEqual(result.value, "value")
        self.assertEqual(events[0][0], "construct")
        worker = events[0][1]
        self.assertIsNot(worker, caller)
        self.assertTrue(all(thread is worker for _, thread in events))
        self.assertEqual(sum(name == "callback" for name, _ in events), 1)

    def test_private_redacted_noncopyable_nonserializable_frozen(self):
        result = self.scope(Fake()).run(lambda: None)
        coordinate = c._PhysicalCoordinateResult()
        for value in (result, m._ScopedDpiResult(), object.__new__(m._DpiExecutionNative),
                      m._ScopedDpiExecutionContext(), m._ScopedPhysicalCoordinateService(), coordinate):
            self.assertFalse(hasattr(value, "__dict__"))
            self.assertEqual(repr(value), type(value).__name__ + "(<private>)")
            self.assertEqual(str(value), repr(value))
            for operation in (copy, deepcopy, pickle.dumps, json.dumps):
                with self.assertRaises(TypeError):
                    operation(value)
        with self.assertRaises(FrozenInstanceError):
            result.completed = False
        for args in ((1, None), (False, "value")):
            with self.assertRaises((TypeError, ValueError)):
                m._ScopedDpiResult(*args)
        class Sub(m._ScopedDpiResult):
            pass
        with self.assertRaises(TypeError):
            Sub()

    def test_static_source_guards(self):
        source = Path(m.__file__).read_text()
        self.assertEqual(m.__all__, ())
        for forbidden in (
            "SetProcessDpiAwarenessContext", "SetProcessDPIAware", "SetProcessDpiAwareness",
            "LogicalToPhysicalPoint", "PhysicalToLogicalPoint", "MulDiv",
            "UIAutomation", "ElementFromPoint", "CoInitialize", "comtypes",
            "SendInput", "SetCursorPos", "GetCursorPos", "SetForegroundWindow",
            "keyboard", "pyautogui", "pointer_binding", "pointer_effect",
            "ui_element_observation", "nayeon.capabilities", "nayeon.intent",
            "nayeon.agent", "nayeon.brain", "nayeon.audit", "nayeon.undo",
            "nayeon.policy", "confirmation", "sleep(", "ThreadPool", "while ",
            "round(", "min(", "max(", "manifest", "cache", "retry(",
        ):
            self.assertNotIn(forbidden, source)
        self.assertEqual(source.count("threading.Thread("), 1)
        self.assertEqual(source.count("thread.start()"), 1)
        self.assertEqual(source.count("thread.join()"), 1)
        self.assertNotIn("NOT_VERIFIED", source)
        self.assertEqual({name for name in vars(m._ScopedDpiExecutionContext)
                          if not name.startswith("_")}, {"run"})
        self.assertEqual({name for name in vars(m._ScopedPhysicalCoordinateService)
                          if not name.startswith("_")}, {"certify"})


if __name__ == "__main__":
    unittest.main()
