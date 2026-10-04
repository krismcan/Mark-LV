"""Phase 6.17 fake-only composition tests; no native calls."""
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, fields, replace
import hashlib
import json
from pathlib import Path
import pickle
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch

from nayeon.services import scoped_ui_element_observation as m
from nayeon.services import dpi_execution_context as d
from nayeon.services import pointer_coordinate_contract as c
from nayeon.services.pointer_hit_validation import _ProposedPoint as Point
from nayeon.verification.contract import VerificationStatus as V


class Int(int):
    pass


class Harness:
    def __init__(self):
        self.events = []
        self.hooks = {}
        self.current = 123
        self.ct = 50000
        self.enabled = True
        self.point = Point(-17, 23)
        self.coordinate_override = None

    def record(self, name, value=None, args=()):
        self.events.append((name, args, threading.current_thread()))
        hook = self.hooks.get(name)
        if isinstance(hook, BaseException):
            raise hook
        if hook is not None:
            return hook(value)
        return value

    def context(self):
        return self.record("context", self.current)

    def awareness(self, context):
        return self.record("awareness", 2 if context == d._PMV2 else 0, (context,))

    def valid(self, context):
        return self.record("valid", True, (context,))

    def equal(self, first, second):
        return self.record("equal", first == second, (first, second))

    def set_context(self, context):
        old = self.current
        self.current = context
        return self.record("enter" if context == d._PMV2 else "restore", old, (context,))

    def dpi_factory(self):
        return self.record("dpi_factory", self)

    def scope_factory(self):
        self.record("scope_factory")
        return d._ScopedDpiExecutionContext(native_factory=self.dpi_factory, platform="win32")

    def contract_factory(self):
        self.record("contract_factory")
        reader = Mock(spec=["awareness"])
        reader.awareness.side_effect = lambda: self.record(
            "coordinate_awareness", 2 if self.current == d._PMV2 else 0)
        real = c._PhysicalCoordinateContractService(native=reader, platform="win32")
        contract = Mock(spec=["certify"])
        def certify(point):
            self.record("certify", args=(point,))
            result = real.certify(point)
            self.record("certified")
            return self.coordinate_override(result) if self.coordinate_override else result
        contract.certify.side_effect = certify
        return contract

    def native_factory(self):
        return self.record("uia_factory", self)

    def initialize(self):
        self.record("initialize")

    def activate(self):
        self.record("activate")

    def element_from_point(self, x, y):
        self.record("element_from_point", args=(x, y))

    def control_type(self):
        return self.record("control_type", self.ct)

    def is_enabled(self):
        return self.record("is_enabled", self.enabled)

    def release_element(self):
        self.record("release_element")

    def release_automation(self):
        self.record("release_automation")

    def uninitialize(self):
        self.record("uninitialize")

    def service(self, **kwargs):
        options = dict(scope_factory=self.scope_factory, contract_factory=self.contract_factory,
                       native_factory=self.native_factory, platform="win32")
        options.update(kwargs)
        return m._ScopedUIElementObservationService(**options)

    def names(self):
        return [name for name, _, _ in self.events]


class Tests(unittest.TestCase):
    def unknown(self, result):
        self.assertIs(type(result), m._ScopedUIElementResult)
        self.assertIs(result.status, V.INDETERMINATE)
        self.assertIsNone(result.evidence)
        self.assertIsNot(result.status, V.NOT_VERIFIED)
        self.assertNotIn("secret", repr(result))

    def test_clean_exact_order_cardinality_and_same_worker(self):
        h = Harness()
        real_thread = threading.Thread
        with patch.object(d.threading, "Thread", wraps=real_thread) as constructor:
            result = h.service().observe(h.point)
        constructor.assert_called_once()
        self.assertIs(constructor.call_args.kwargs["daemon"], False)
        self.assertIs(result.status, V.VERIFIED)
        self.assertIs(result.evidence.point, h.point)
        self.assertEqual((result.evidence.awareness, result.evidence.control_type,
                          result.evidence.enabled), (2, 50000, True))
        self.assertEqual(h.names(), [
            "scope_factory", "dpi_factory", "context", "awareness", "valid", "enter",
            "equal", "context", "equal", "awareness", "contract_factory", "certify",
            "coordinate_awareness", "coordinate_awareness", "certified", "uia_factory",
            "initialize", "activate", "element_from_point", "control_type", "is_enabled",
            "release_element", "release_automation", "uninitialize", "restore", "equal",
            "context", "equal", "awareness"])
        worker = h.events[1][2]
        self.assertIsNot(worker, threading.current_thread())
        self.assertTrue(all(thread is worker for _, _, thread in h.events[1:]))
        self.assertFalse(worker.is_alive())
        self.assertFalse(worker.daemon)
        self.assertEqual(h.current, 123)
        self.assertEqual(next(args for name, args, _ in h.events
                              if name == "element_from_point"), (-17, 23))

    def test_fresh_scope_and_worker_per_observation(self):
        h = Harness()
        service = h.service()
        self.assertIs(service.observe(h.point).status, V.VERIFIED)
        first = h.events[1][2]
        h.events.clear()
        self.assertIs(service.observe(h.point).status, V.VERIFIED)
        self.assertIsNot(first, h.events[1][2])
        self.assertEqual(h.names().count("scope_factory"), 1)

    def test_defaults_construct_primitives_on_scoped_worker(self):
        h = Harness()
        with patch.object(m, "_ScopedDpiExecutionContext", side_effect=h.scope_factory), \
                patch.object(m, "_PhysicalCoordinateContractService", side_effect=h.contract_factory), \
                patch.object(m, "_UIANative", side_effect=h.native_factory):
            result = m._ScopedUIElementObservationService(platform="win32").observe(h.point)
        self.assertIs(result.status, V.VERIFIED)
        worker = h.events[1][2]
        for name in ("contract_factory", "uia_factory", "initialize", "uninitialize"):
            self.assertIs(next(t for n, _, t in h.events if n == name), worker)

    def test_every_uia_failure_cleanup_exactly_once(self):
        stages = ("uia_factory", "initialize", "activate", "element_from_point",
                  "control_type", "is_enabled", "release_element", "release_automation",
                  "uninitialize")
        for error in (OSError("secret HRESULT"), KeyboardInterrupt("secret")):
            for stage in stages:
                with self.subTest(stage=stage, error=type(error)):
                    h = Harness()
                    h.hooks[stage] = error
                    self.unknown(h.service().observe(h.point))
                    self.assertEqual(h.names().count(stage), 1)
                    for cleanup in ("release_element", "release_automation", "uninitialize"):
                        self.assertEqual(h.names().count(cleanup), 0 if stage == "uia_factory" else 1)
                    self.assertEqual(h.names().count("restore"), 1)
                    self.assertEqual(h.current, 123)

    def test_contract_failures_prevent_uia(self):
        for stage in ("contract_factory", "certify", "coordinate_awareness", "certified"):
            h = Harness()
            h.hooks[stage] = OSError("secret")
            self.unknown(h.service().observe(h.point))
            self.assertNotIn("uia_factory", h.names())
            self.assertEqual(h.names().count("restore"), 1)

    def test_coordinate_result_wrong_type_status_evidence_identity(self):
        class SubResult(c._PhysicalCoordinateResult):
            pass
        class SubEvidence(c._PhysicalCoordinateEvidence):
            pass
        for mode in ("none", "dict", "duck", "subresult", "subevidence", "unknown",
                     "status", "status_string", "evidence", "awareness", "other_point"):
            with self.subTest(mode=mode):
                h = Harness()
                def override(result):
                    if mode == "none": return None
                    if mode == "dict": return {}
                    if mode == "duck": return Mock(status=V.VERIFIED, evidence=result.evidence)
                    if mode == "unknown": return c._PhysicalCoordinateResult()
                    if mode == "subresult": return object.__new__(SubResult)
                    if mode == "subevidence":
                        object.__setattr__(result, "evidence", object.__new__(SubEvidence))
                    if mode == "status": object.__setattr__(result, "status", V.NOT_VERIFIED)
                    if mode == "status_string": object.__setattr__(result, "status", "verified")
                    if mode == "evidence": object.__setattr__(result, "evidence", None)
                    if mode == "awareness": object.__setattr__(result.evidence, "awareness", True)
                    if mode == "other_point":
                        object.__setattr__(result.evidence, "point", Point(-17, 23))
                    return result
                h.coordinate_override = override
                self.unknown(h.service().observe(h.point))
                self.assertNotIn("uia_factory", h.names())

    def test_coordinate_awareness_rejected(self):
        for bad in (0, 1, True, Int(2), 2.0, None, 3):
            h = Harness()
            h.hooks["coordinate_awareness"] = lambda value: bad
            self.unknown(h.service().observe(h.point))
            self.assertNotIn("uia_factory", h.names())

    def test_point_mutation_at_every_lifecycle_stage(self):
        stages = ("scope_factory", "enter", "contract_factory", "certify", "certified",
                  "uia_factory", "initialize", "activate", "element_from_point", "control_type",
                  "is_enabled", "release_element", "release_automation", "uninitialize", "restore")
        for field in ("x", "y"):
            for stage in stages:
                with self.subTest(field=field, stage=stage):
                    h = Harness()
                    def mutate(value):
                        object.__setattr__(h.point, field, 9)
                        return value
                    h.hooks[stage] = mutate
                    self.unknown(h.service().observe(h.point))
                    if "uia_factory" in h.names():
                        for cleanup in ("release_element", "release_automation", "uninitialize"):
                            self.assertEqual(h.names().count(cleanup), 1)
                    if stage in ("scope_factory", "enter", "contract_factory"):
                        self.assertNotIn("certify", h.names())
                    if stage in ("uia_factory", "initialize", "activate"):
                        self.assertNotIn("element_from_point", h.names())

    def test_invalid_points_before_scope_construction(self):
        class SubPoint(Point):
            pass
        points = [None, True, (0, 0), {}, SubPoint(0, 0)]
        for field in ("x", "y"):
            for bad in (True, Int(0), 0.0, None, 2**31, -(2**31)-1):
                point = Point(0, 0)
                object.__setattr__(point, field, bad)
                points.append(point)
        for point in points:
            h = Harness()
            self.unknown(h.service().observe(point))
            self.assertEqual(h.events, [])

    def test_platform_before_all_construction(self):
        for platform in ("linux", "darwin", "", None, True):
            h = Harness()
            self.unknown(h.service(platform=platform).observe(h.point))
            self.assertEqual(h.events, [])

    def test_control_type_and_exact_bool(self):
        for ct in range(50000, 50041):
            for enabled in (False, True):
                h = Harness()
                h.ct, h.enabled = ct, enabled
                self.assertIs(h.service().observe(h.point).status, V.VERIFIED)
        for ct in (49999, 50041, True, Int(50000), 50000.0, None):
            h = Harness()
            h.ct = ct
            self.unknown(h.service().observe(h.point))
        for enabled in (0, 1, Int(1), 1.0, None, "true"):
            h = Harness()
            h.enabled = enabled
            self.unknown(h.service().observe(h.point))

    def test_real_scope_restoration_discards_successful_sample(self):
        for bad in (None, 0, True, 456):
            h = Harness()
            h.hooks["restore"] = lambda value: bad
            self.unknown(h.service().observe(h.point))
            self.assertEqual(h.names().count("element_from_point"), 1)
            self.assertEqual(h.names().count("uninitialize"), 1)
            self.assertEqual(h.names().count("restore"), 1)
        h = Harness()
        h.hooks["restore"] = OSError("secret")
        self.unknown(h.service().observe(h.point))

    def test_scope_incomplete_wrong_type_tampered_and_subclass(self):
        class Sub(d._ScopedDpiResult):
            pass
        tampered = d._ScopedDpiResult()
        object.__setattr__(tampered, "completed", 1)
        invalid = d._ScopedDpiResult()
        object.__setattr__(invalid, "value", "secret")
        for value in (None, {}, Mock(completed=True), object.__new__(Sub),
                      d._ScopedDpiResult(), tampered, invalid,
                      d._ScopedDpiResult(True, None)):
            h = Harness()
            scope = Mock(spec=["run"])
            scope.run.return_value = value
            self.unknown(h.service(scope_factory=lambda: scope).observe(h.point))
            scope.run.assert_called_once()

    def test_scope_and_joined_publication_failures(self):
        for mode in ("factory", "run", "discard", "mutate", "wrong_value", "tamper_value"):
            h = Harness()
            def run(task):
                value = h.scope_factory().run(task)
                if mode == "run": raise RuntimeError("secret")
                if mode == "discard": return d._ScopedDpiResult()
                if mode == "mutate": object.__setattr__(h.point, "x", 9)
                if mode == "wrong_value": return d._ScopedDpiResult(True, {})
                if mode == "tamper_value": object.__setattr__(value.value.evidence, "enabled", 1)
                return value
            scope = Mock(spec=["run"])
            scope.run.side_effect = run
            factory = Mock(return_value=scope)
            if mode == "factory": factory.side_effect = OSError("secret")
            self.unknown(h.service(scope_factory=factory).observe(h.point))

    def test_evidence_and_result_invariants(self):
        evidence = m._ScopedUIElementEvidence(Point(0, 0), 2, 50000, True)
        for args in (("verified", evidence), (V.VERIFIED, None),
                     (V.NOT_VERIFIED, None), (V.INDETERMINATE, evidence)):
            with self.assertRaises((TypeError, ValueError)):
                m._ScopedUIElementResult(*args)
        for key, value in (("awareness", 1), ("awareness", True), ("awareness", Int(2)),
                           ("control_type", 50041), ("enabled", 1), ("point", (0, 0))):
            with self.assertRaises((TypeError, ValueError)):
                replace(evidence, **{key: value})
        class E(m._ScopedUIElementEvidence): pass
        class R(m._ScopedUIElementResult): pass
        with self.assertRaises(TypeError): E(Point(0, 0), 2, 50000, True)
        with self.assertRaises(TypeError): R()

    def test_private_frozen_slotted_redacted_nonserializable(self):
        h = Harness()
        result = h.service().observe(h.point)
        self.assertEqual([f.name for f in fields(result.evidence)],
                         ["point", "awareness", "control_type", "enabled"])
        for value in (result, result.evidence, h.point, h.service(), m._ScopedUIElementResult()):
            self.assertFalse(hasattr(value, "__dict__"))
            self.assertEqual(repr(value), type(value).__name__ + "(<private>)")
            self.assertEqual(str(value), repr(value))
            for operation in (copy, deepcopy, pickle.dumps, json.dumps):
                with self.assertRaises(TypeError): operation(value)
        with self.assertRaises(FrozenInstanceError): result.evidence.enabled = False
        with self.assertRaises(FrozenInstanceError): result.status = V.INDETERMINATE

    def test_static_no_routes_mutation_nested_workers_or_native_rebinding(self):
        source = Path(m.__file__).read_text()
        self.assertEqual(m.__all__, ())
        for forbidden in ("SendInput", "SetCursorPos", "GetCursorPos", "mouse_event", "keybd_event",
                          "SetForegroundWindow", "SetFocus", "pyautogui", "keyboard", "screenshot",
                          "OCR", "InvokePattern", "ValuePattern", "SetValue", "TreeWalker", "FindFirst",
                          "FindAll", "pointer_binding", "pointer_effect", "nayeon.capabilities",
                          "nayeon.intent", "nayeon.agent", "nayeon.brain", "nayeon.audit", "nayeon.undo",
                          "nayeon.policy", "confirmation", "_UIElementObservationService",
                          "_ScopedPhysicalCoordinateService", "_MTAWorker", "threading", "ctypes",
                          "WinDLL", "SetProcessDpi", "SetThreadDpi", "LogicalToPhysical",
                          "PhysicalToLogical", "MulDiv", "round(", "min(", "max(", "sleep(",
                          "while ", "ThreadPool", "NOT_VERIFIED"):
            self.assertNotIn(forbidden, source)
        for call in (".certify(point)", ".element_from_point(*coordinates)", ".initialize()",
                     ".activate()", ".control_type()", ".is_enabled()", ".run(task)"):
            self.assertEqual(source.count(call), 1)
        self.assertEqual({name for name in vars(m._ScopedUIElementObservationService)
                          if not name.startswith("_")}, {"observe"})

    def test_sealed_production_files_equal_protected_checkpoint(self):
        root = Path(__file__).resolve().parents[1]
        # Phase 6.18 explicitly integrates the private pointer binding. Its
        # new gate/final-gap guards live in test_pointer_uia_gate; services stay sealed.
        for path in ("nayeon/services/ui_element_observation.py",
                     "nayeon/services/pointer_coordinate_contract.py",
                     "nayeon/services/dpi_execution_context.py",
                     "nayeon/services/pointer_effect.py"):
            baseline = subprocess.check_output(
                ["git", "show", f"ab646bc51f34d9fd4a7ee747671465c92c0aada5:{path}"], cwd=root)
            current = (root / path).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(current).digest(), hashlib.sha256(baseline).digest())


if __name__ == "__main__":
    unittest.main()
