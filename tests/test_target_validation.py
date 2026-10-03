"""Phase 6.5 deterministic read-only checks; all native entry points are mocked."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
import ctypes
import unittest
from unittest.mock import Mock, call, patch

from nayeon.services.target_validation import (
    MAX_AGE_NS, _TargetBinding, _TargetVerificationResult, _TargetVerificationService,
    _valid_target_binding,
)
from nayeon.services.window_focus import _FocusBinding, _valid_focus_binding
from nayeon.services.keyboard_text import _TextBinding, _valid_text_binding
from nayeon.verification.contract import VerificationStatus as V
from tests import test_foreground_observation as fixtures

C, I = fixtures.CONTEXT, fixtures.IDENTITY
ORDER = ["clock", "context", "foreground", "identity", "identity", "foreground", "context", "clock"]


class TargetValidationTests(unittest.TestCase):
    def setup_service(self, times=(10, 20, 30, 40), platform="win32"):
        self.native = Mock(spec=["context", "foreground", "identity"])
        self.native.context.return_value = C
        self.native.foreground.return_value = I.hwnd
        self.native.identity.return_value = I
        self.clock = Mock(side_effect=times)
        self.calls = Mock()
        self.calls.attach_mock(self.clock, "clock")
        for name in ("context", "foreground", "identity"):
            self.calls.attach_mock(getattr(self.native, name), name)
        self.service = _TargetVerificationService(native=self.native, platform=platform, clock=self.clock)

    def setUp(self):
        self.setup_service()

    def test_construction_has_no_io_or_retained_binding(self):
        self.assertEqual(self.calls.mock_calls, [])
        self.assertEqual(set(vars(self.service)), {"_native", "_platform", "_clock"})

    def test_baseline_and_validation_exact_order_cardinality_same_clock(self):
        binding = self.service.acquire_target()
        self.assertEqual(binding, _TargetBinding(I, C, 10, 20))
        self.assertEqual([c[0] for c in self.calls.mock_calls], ORDER)
        result = self.service.verify_target(binding)
        self.assertIs(result.status, V.VERIFIED)
        self.assertEqual([c[0] for c in self.calls.mock_calls], ORDER * 2)
        self.assertEqual(self.native.identity.call_args_list, [call(I.hwnd)] * 4)
        self.assertEqual(set(vars(self.service)), {"_native", "_platform", "_clock"})

    def test_clock_brackets_native_initialization_too(self):
        self.service._native = None
        with patch("nayeon.services.windows_desktop._WindowsNative", return_value=self.native) as factory:
            self.calls.attach_mock(factory, "factory")
            self.service.acquire_target()
        self.assertEqual([c[0] for c in self.calls.mock_calls], ["clock", "factory"] + ORDER[1:])

    def test_binding_types_bool_subclasses_and_invalid_intervals(self):
        class Int(int):
            pass
        for field in ("acquired_from_ns", "acquired_to_ns"):
            for value in (True, False, None, "10", 10.0, Int(10)):
                with self.subTest(field=field, value=value), self.assertRaises(TypeError):
                    replace(_TargetBinding(I, C, 10, 20), **{field: value})
        for start, end in ((-1, 20), (10, -1), (21, 20)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                _TargetBinding(I, C, start, end)
        self.assertTrue(_valid_target_binding(_TargetBinding(I, C, 0, 0)))
        for identity, context in ((None, C), (I, None), (Mock(), C)):
            with self.assertRaises(TypeError):
                _TargetBinding(identity, context, 10, 20)

    def test_binding_existing_identity_context_validity_and_native_width(self):
        bad = ((replace(I, root=I.root + 1), C), (replace(I, pid=0), C),
               (replace(I, tid=-1), C), (replace(I, creation_time=0), C),
               (replace(I, executable=" "), C), (replace(I, window_class=""), C),
               (replace(I, desktop="Other"), C), (replace(I, session=0), C),
               (I, replace(C, active=False)), (I, replace(C, station="Other")),
               (I, replace(C, input_desktop="Other")), (I, replace(C, thread_desktop="Other")),
               (I, replace(C, session=0)))
        for identity, context in bad:
            with self.subTest(identity=identity, context=context), self.assertRaises(ValueError):
                _TargetBinding(identity, context, 10, 20)
        huge = 2 ** (ctypes.sizeof(ctypes.c_void_p) * 8)
        with self.assertRaises(ValueError):
            _TargetBinding(replace(I, hwnd=huge, root=huge), C, 10, 20)

    def test_identity_and_context_reject_bool_integer_fields(self):
        for name in ("hwnd", "pid", "tid", "creation_time", "root", "session"):
            with self.subTest(name=name), self.assertRaises(TypeError):
                replace(I, **{name: True})
        with self.assertRaises(TypeError):
            replace(C, session=True)
        with self.assertRaises(TypeError):
            replace(C, active=1)

    def test_immutable_slotted_redacted_binding_and_result(self):
        binding = self.service.acquire_target()
        result = self.service.verify_target(binding)
        self.assertEqual([f.name for f in fields(binding)],
                         ["identity", "context", "acquired_from_ns", "acquired_to_ns"])
        for value in (binding, result):
            self.assertFalse(hasattr(value, "__dict__"))
            self.assertEqual(str(value), type(value).__name__ + "(<private>)")
            self.assertEqual(repr(value), str(value))
            self.assertEqual(deepcopy(value), value)
        with self.assertRaises(FrozenInstanceError):
            binding.acquired_to_ns = 40
        with self.assertRaises(FrozenInstanceError):
            result.status = V.VERIFIED
        with self.assertRaises(TypeError):
            _TargetVerificationResult("verified")

    def test_legacy_bindings_or_missing_baseline_cannot_gain_later_timestamp(self):
        for binding in (None, {}, _FocusBinding(I, C), _TextBinding(_FocusBinding(I, C), "test")):
            self.assertIs(self.service.verify_target(binding).status, V.INDETERMINATE)
        self.assertEqual(self.calls.mock_calls, [])

    def test_timestamped_binding_grants_no_legacy_focus_or_keyboard_authority(self):
        binding = self.service.acquire_target()
        self.assertFalse(_valid_focus_binding(binding))
        self.assertFalse(_valid_text_binding(_TextBinding(binding, "test")))

    def test_invalid_binding_rechecked_before_io(self):
        for field, value in (("acquired_from_ns", True), ("acquired_to_ns", -1),
                             ("acquired_from_ns", 21), ("identity", None), ("context", None)):
            binding = _TargetBinding(I, C, 10, 20)
            # Bypass frozen construction only to test defensive consumption.
            object.__setattr__(binding, field, value)
            self.assertIs(self.service.verify_target(binding).status, V.INDETERMINATE)
        self.assertEqual(self.calls.mock_calls, [])

    def test_every_identity_field_mismatch_never_verified(self):
        changes = {"hwnd": I.hwnd + 1, "pid": I.pid + 1, "tid": I.tid + 1,
                   "creation_time": I.creation_time + 1, "executable": "other",
                   "window_class": "Other", "root": I.root + 1,
                   "session": I.session + 1, "desktop": "Other"}
        for field, value in changes.items():
            for position in (0, 1):
                with self.subTest(field=field, position=position):
                    self.setup_service()
                    binding = self.service.acquire_target()
                    changed = replace(I, **{field: value})
                    if field == "hwnd":
                        changed = replace(changed, root=value)
                    samples = [I, I]
                    samples[position] = changed
                    self.native.identity.side_effect = samples
                    expected = V.INDETERMINATE if field in ("root", "session", "desktop") else V.NOT_VERIFIED
                    self.assertIs(self.service.verify_target(binding).status, expected)
                    self.assertEqual([c[0] for c in self.calls.mock_calls], ORDER * 2)

    def test_every_context_field_mismatch_and_supported_session_drift(self):
        changes = {"session": C.session + 1, "input_desktop": "Other", "thread_desktop": "Other",
                   "station": "Other", "active": False}
        for field, value in changes.items():
            for position in (0, 1):
                with self.subTest(field=field, position=position):
                    self.setup_service()
                    binding = self.service.acquire_target()
                    samples = [C, C]
                    samples[position] = replace(C, **{field: value})
                    self.native.context.side_effect = samples
                    identities = [I, I]
                    if field == "session":
                        identities[position] = replace(I, session=value)
                    self.native.identity.side_effect = identities
                    expected = V.NOT_VERIFIED if field == "session" else V.INDETERMINATE
                    self.assertIs(self.service.verify_target(binding).status, expected)

    def test_foreground_drift_both_samples_only_saved_hwnd_queried(self):
        for values in ((I.hwnd + 1, I.hwnd), (I.hwnd, I.hwnd + 1), (I.hwnd + 1,) * 2):
            self.setup_service()
            binding = self.service.acquire_target()
            self.native.foreground.side_effect = values
            self.assertIs(self.service.verify_target(binding).status, V.NOT_VERIFIED)
            self.assertEqual(self.native.identity.call_args_list, [call(I.hwnd)] * 4)

    def test_invalid_missing_evidence_takes_precedence_over_contradiction(self):
        for name, values in (("context", (None, {}, replace(C, active=False))),
                             ("identity", (None, {}, replace(I, pid=0), replace(I, root=I.root + 1))),
                             ("foreground", (None, True, False, 0, -1, 1.0, "1",
                                             2 ** (ctypes.sizeof(ctypes.c_void_p) * 8)))):
            for value in values:
                for position in (0, 1):
                    with self.subTest(name=name, value=value, position=position):
                        self.setup_service()
                        binding = self.service.acquire_target()
                        self.native.foreground.return_value = I.hwnd + 1
                        good = {"context": C, "identity": I, "foreground": I.hwnd + 1}[name]
                        samples = [good, good]
                        samples[position] = value
                        getattr(self.native, name).side_effect = samples
                        self.assertIs(self.service.verify_target(binding).status, V.INDETERMINATE)

    def test_exceptions_at_each_read_or_clock_no_retry_no_error_disclosure(self):
        for phase in ("baseline", "validation"):
            for name in ("context", "foreground", "identity", "clock"):
                for position in (0, 1):
                    with self.subTest(phase=phase, name=name, position=position):
                        self.setup_service()
                        binding = self.service.acquire_target() if phase == "validation" else None
                        self.calls.reset_mock()
                        method = self.clock if name == "clock" else getattr(self.native, name)
                        good = {"context": C, "foreground": I.hwnd, "identity": I, "clock": 30}[name]
                        samples = [good, good]
                        samples[position] = OSError("private native error")
                        method.side_effect = samples
                        if binding is None:
                            with self.assertRaisesRegex(ValueError, "^Target baseline acquisition could not be established.$"):
                                self.service.acquire_target()
                        else:
                            self.assertIs(self.service.verify_target(binding).status, V.INDETERMINATE)
                        self.assertEqual(method.call_count, position + 1)

    def test_baseline_rejects_contradictory_or_invalid_samples(self):
        for name, values in (("foreground", [I.hwnd, I.hwnd + 1]),
                             ("identity", [I, replace(I, creation_time=I.creation_time + 1)]),
                             ("context", [C, replace(C, active=False)]),
                             ("identity", [None, I])):
            self.setup_service()
            getattr(self.native, name).side_effect = values
            with self.assertRaises(ValueError):
                self.service.acquire_target()

    def test_baseline_missing_malformed_unsupported_evidence_never_retained(self):
        for name, values in (("context", (None, {}, replace(C, active=False))),
                             ("identity", (None, {}, replace(I, pid=0))),
                             ("foreground", (None, True, 0, -1, 1.0, "1"))):
            for value in values:
                for position in (0, 1):
                    with self.subTest(name=name, value=value, position=position):
                        self.setup_service()
                        good = {"context": C, "identity": I, "foreground": I.hwnd}[name]
                        samples = [good, good]
                        samples[position] = value
                        getattr(self.native, name).side_effect = samples
                        with self.assertRaises(ValueError):
                            self.service.acquire_target()
                        self.assertEqual(set(vars(self.service)), {"_native", "_platform", "_clock"})

    def test_freshness_exact_boundary_one_ns_stale_and_completion_cutoff(self):
        for start, end, expected in ((30, 20 + MAX_AGE_NS, V.VERIFIED),
                                     (30, 21 + MAX_AGE_NS, V.INDETERMINATE),
                                     (20 + MAX_AGE_NS, 20 + MAX_AGE_NS, V.VERIFIED),
                                     (21 + MAX_AGE_NS, 22 + MAX_AGE_NS, V.INDETERMINATE)):
            with self.subTest(start=start, end=end):
                self.setup_service((10, 20, start, end))
                self.assertIs(self.service.verify_target(self.service.acquire_target()).status, expected)

    def test_age_is_from_acquisition_end_not_start(self):
        self.setup_service((0, MAX_AGE_NS * 2, MAX_AGE_NS * 2, MAX_AGE_NS * 3))
        self.assertIs(self.service.verify_target(self.service.acquire_target()).status, V.VERIFIED)

    def test_clock_malformed_reversed_and_overlapping_intervals(self):
        for times in ((-1, 20), (True, 20), (10.0, 20), (None, 20), ("10", 20),
                      (21, 20), (10, False), (10, -1), (10, None), (10, "20")):
            self.setup_service(times)
            with self.assertRaises(ValueError):
                self.service.acquire_target()
        for t0, t1 in ((-1, 40), (True, 40), (30.0, 40), (None, 40), ("30", 40),
                       (40, 30), (19, 40), (30, False), (30, -1), (30, None), (30, "40")):
            self.setup_service((10, 20, t0, t1))
            self.assertIs(self.service.verify_target(self.service.acquire_target()).status, V.INDETERMINATE)
        self.setup_service((0, 0, 0, 0))
        self.assertIs(self.service.verify_target(self.service.acquire_target()).status, V.VERIFIED)

    def test_stale_contradiction_is_indeterminate(self):
        self.setup_service((10, 20, 30, MAX_AGE_NS + 21))
        binding = self.service.acquire_target()
        self.native.foreground.return_value = I.hwnd + 1
        self.assertIs(self.service.verify_target(binding).status, V.INDETERMINATE)

    def test_unsupported_platform_and_factory_failure_zero_native_reads(self):
        for platform in ("linux", "darwin", "unsupported"):
            self.setup_service(platform=platform)
            with patch("nayeon.services.windows_desktop._WindowsNative") as factory:
                with self.assertRaises(ValueError):
                    self.service.acquire_target()
                self.assertIs(self.service.verify_target(_TargetBinding(I, C, 0, 0)).status, V.INDETERMINATE)
                factory.assert_not_called()
            self.assertEqual(self.native.mock_calls, [])
        self.setup_service()
        self.service._native = None
        with patch("nayeon.services.windows_desktop._WindowsNative", side_effect=OSError("private")) as factory:
            self.assertIs(self.service.verify_target(_TargetBinding(I, C, 0, 0)).status, V.INDETERMINATE)
            factory.assert_called_once()

    def test_same_field_replacement_and_unsampled_change_away_back_indistinguishable(self):
        # This hidden fixture state never enters the sampled Win32 fields.
        hidden = {"generation": 1, "foreground": I.hwnd}
        binding = self.service.acquire_target()
        hidden["generation"] = 2  # Same-field HWND replacement.
        hidden["foreground"] = I.hwnd + 1
        hidden["foreground"] = I.hwnd  # Change away and back between samples.
        self.native.identity.return_value = replace(I)
        self.native.foreground.side_effect = lambda: hidden["foreground"]
        self.assertIs(self.service.verify_target(binding).status, V.VERIFIED)
        self.assertEqual([f.name for f in fields(_TargetVerificationResult)], ["status"])

    def test_no_mutation_routes_exports_or_audit_integration(self):
        source = (Path(__file__).parents[1] / "nayeon/services/target_validation.py").read_text()
        for forbidden in ("SetCursorPos", "SendInput", "mouse_event", "SetForegroundWindow",
                          "AttachThreadInput", "GetWindowText", "OpenClipboard", "pyautogui",
                          "UIAutomation", "screenshot", "OCR", "playwright", "selenium",
                          "AuditService", "CapabilityModule", "ConfirmationService", "json", "pickle"):
            self.assertNotIn(forbidden, source)
        for path in ("nayeon/services/__init__.py", "nayeon/agent/router.py", "nayeon/agent/executor.py",
                     "nayeon/capabilities/focus_window.py", "nayeon/capabilities/type_text.py"):
            self.assertNotIn("target_validation", (Path(__file__).parents[1] / path).read_text())
        self.assertEqual({name for name in dir(self.service) if not name.startswith("_")},
                         {"acquire_target", "verify_target"})


class TargetNativeCleanupTests(unittest.TestCase):
    def setUp(self):
        # Reuse only the mocked query fixture setup, not its TestCase methods.
        self.fixture = fixtures.NativeResourceTests()
        self.fixture.setUp()
        self.fixture.configure_window()
        self.api = self.fixture.api
        self.api.u.GetForegroundWindow.return_value = I.hwnd
        self.service = _TargetVerificationService(native=self.api, platform="win32",
                                                  clock=Mock(side_effect=[10, 20, 30, 40]))

    def test_success_scoped_ownership_all_queries_closed(self):
        binding = self.service.acquire_target()
        self.assertIs(self.service.verify_target(binding).status, V.VERIFIED)
        self.assertEqual(self.api.k.CloseHandle.call_args_list, [call(101)] * 4)
        self.assertEqual(self.api.u.CloseDesktop.call_args_list, [call(202)] * 4)
        self.assertEqual(self.api.w.WTSFreeMemory.call_count, 4)

    def test_cleanup_failure_at_each_sample_never_positive_or_retried(self):
        for phase in ("baseline", "validation"):
            for dll, name in (("k", "CloseHandle"), ("u", "CloseDesktop"), ("w", "WTSFreeMemory")):
                for position in (0, 1):
                    for failure in (False, OSError("private cleanup")):
                        if name == "WTSFreeMemory" and failure is False:
                            continue  # Native void return has no failure acknowledgement.
                        with self.subTest(phase=phase, name=name, position=position, failure=type(failure)):
                            self.setUp()
                            binding = self.service.acquire_target() if phase == "validation" else None
                            for library in (self.api.k, self.api.u, self.api.w):
                                library.reset_mock()
                            close = getattr(getattr(self.api, dll), name)
                            close.side_effect = [True] * position + [failure]
                            if binding is None:
                                with self.assertRaises(ValueError):
                                    self.service.acquire_target()
                            else:
                                self.assertIs(self.service.verify_target(binding).status, V.INDETERMINATE)
                            self.assertEqual(close.call_count, position + 1)


if __name__ == "__main__":
    unittest.main()
