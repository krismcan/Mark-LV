"""P310 synthetic no-key transport fault injection and disposable Windows pipes.

The OS tests run in bounded children against random test-only endpoints, under
this test user's token. No installed service, key, credential API, or elevation.
"""

import ast
import hashlib
import inspect
import struct
from pathlib import Path
import runpy
import subprocess
import sys
import threading
import textwrap
import time
import unittest
import uuid
from unittest.mock import patch

from nayeon.desktop_alpha import byok_native_synthetic_request as requester
from nayeon.desktop_alpha import local_byok_window as window
from nayeon.brain import local_byok_user_scope as scope
from nayeon.secrets import windows_credential as storage


EXPECTED = b"C1|DENIED|HOLD|NO_CREDENTIALS"
ENDPOINT = r"\\.\pipe\NayeonV1ByokCustody.SyntheticDenied.v1"


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


class Overlapped:
    def __init__(self, api, kind):
        self.api = api
        self.kind = kind
        self.event = kind + "-event"
        self.cancelled = False

    def cancel(self):
        self.api.stage(self.kind + "-cancel")
        self.cancelled = True

    def GetOverlappedResult(self, wait):
        self.api.stage(self.kind + ("-drain" if wait else "-result"))
        if self.cancelled:
            return 0, 995  # ERROR_OPERATION_ABORTED
        if self.api.fail == "completion-error":
            return 0, 996  # ERROR_IO_INCOMPLETE
        if self.kind == "write":
            return (0 if self.api.fail == "short-write" else 13), 0
        return len(self.api.reply), (234 if self.api.fail == "more-data-result" else 0)

    def getbuffer(self):
        self.api.stage("getbuffer")
        return self.api.reply


class PipeAPI:
    FILE_FLAG_OVERLAPPED = 0x40000000
    PIPE_READMODE_MESSAGE = 2
    ERROR_IO_PENDING = 997
    ERROR_MORE_DATA = 234
    WAIT_TIMEOUT = 258

    def __init__(self, clock):
        self.clock = clock
        self.reply = EXPECTED
        self.calls = []
        self.fail = None
        self.advance = lambda stage: None
        self.pending = True
        self.peeks = 0

    def stage(self, name):
        self.calls.append(name)
        self.advance(name)
        if self.fail == name:
            raise OSError("private synthetic failure details")

    def CreateFile(self, path, access, share, security, disposition, flags, template):
        self.stage("CreateFile")
        assert (path, access, share, security, disposition, flags, template) == (
            ENDPOINT, 0xC0000000, 0, 0, 3, 0x40100000, 0)
        return 310

    def SetNamedPipeHandleState(self, handle, mode, maximum, timeout):
        self.stage("mode")
        assert (handle, mode, maximum, timeout) == (310, 2, None, None)

    def PeekNamedPipe(self, handle, size):
        assert (handle, size) == (310, 0)
        self.peeks += 1
        stage = "pre-peek" if self.peeks % 2 else "post-peek"
        self.stage(stage)
        return (4, 4) if self.fail == stage + "-data" else (0, 0)

    def WriteFile(self, handle, data, *, overlapped):
        self.stage("WriteFile")
        assert handle == 310 and data == struct.pack("<4sQB", b"C1T1", 0x0807060504030201, 1) and overlapped is True
        return Overlapped(self, "write"), (997 if self.pending else 0)

    def ReadFile(self, handle, capacity, *, overlapped):
        self.stage("ReadFile")
        assert handle == 310 and capacity == len(EXPECTED) + 1 and overlapped is True
        return Overlapped(self, "read"), (234 if self.fail == "more-data" else 997 if self.pending else 0)

    def WaitForSingleObject(self, event, milliseconds):
        self.stage(event)
        assert 0 <= milliseconds <= 750
        if self.fail == event + "-timeout":
            self.clock.now += milliseconds / 1000 + 0.001
            return 258
        if self.fail == "wait-error":
            return 0xFFFFFFFF
        self.clock.now += 0.001
        return 0

    def CloseHandle(self, handle):
        self.stage("CloseHandle")
        assert handle == 310


class TransportFixture:
    def setUp(self):
        self.clock = Clock()
        self.dll = PipeAPI(self.clock)
        self.enterContext(patch.object(requester.sys, "platform", "win32"))
        self.enterContext(patch.dict(sys.modules, {"_winapi": self.dll}))
        self.enterContext(patch.object(requester, "time", self.clock))
        self.random = self.enterContext(patch.object(
            requester.os, "urandom", return_value=bytes(range(1, 9))))

    def request(self):
        return requester.NativeSyntheticRequester().request()


class RequesterTests(TransportFixture, unittest.TestCase):
    def test_exact_response_overlapped_message_mode_and_anonymous_sqos(self):
        self.assertIs(self.request(), requester.SyntheticRequestStatus.UNTRUSTED_HOLD)
        self.assertEqual(self.dll.calls, ["CreateFile", "mode", "pre-peek", "WriteFile",
                         "write-event", "write-result", "ReadFile", "read-event",
                         "read-result", "getbuffer", "post-peek", "CloseHandle"])
        self.assertEqual(set(requester.SyntheticRequestStatus), {
            requester.SyntheticRequestStatus.UNAVAILABLE, requester.SyntheticRequestStatus.UNTRUSTED_HOLD})

    def test_immediate_overlapped_completion_needs_no_event_wait(self):
        self.dll.pending = False
        self.assertIs(self.request(), requester.SyntheticRequestStatus.UNTRUSTED_HOLD)
        self.assertNotIn("write-event", self.dll.calls)
        self.assertNotIn("read-event", self.dll.calls)
        self.assertIn("write-result", self.dll.calls)
        self.assertIn("read-result", self.dll.calls)

    def test_malformed_partial_empty_and_oversized_are_unavailable(self):
        for reply in (b"", EXPECTED[:-1], EXPECTED + b"x", EXPECTED + b"xx",
                      EXPECTED.lower(), b"READY", b"\xff" * len(EXPECTED)):
            with self.subTest(reply=reply):
                self.dll.reply = reply
                self.dll.calls.clear()
                self.dll.peeks = 0
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
                self.assertEqual(self.dll.calls.count("ReadFile"), 1)
                self.assertEqual(self.dll.calls.count("CloseHandle"), 1)

    def test_timeout_cancels_drains_before_close_for_read_and_write(self):
        for kind in ("read", "write"):
            with self.subTest(kind=kind):
                self.clock.now = 0
                self.dll.calls.clear()
                self.dll.peeks = 0
                self.dll.fail = kind + "-event-timeout"
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
                self.assertLessEqual(self.clock.now, 0.751)
                self.assertEqual(self.dll.calls[-3:], [kind + "-cancel", kind + "-drain", "CloseHandle"])
                self.assertEqual(self.dll.calls.count("CreateFile"), 1)
                if kind == "write":
                    self.assertNotIn("ReadFile", self.dll.calls)

    def test_more_data_in_start_or_completion_is_not_a_valid_reply(self):
        for failure in ("more-data", "more-data-result"):
            with self.subTest(failure=failure):
                self.dll.fail = failure
                self.dll.peeks = 0
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)

    def test_short_write_incomplete_completion_and_failed_wait_refuse(self):
        for failure in ("short-write", "completion-error", "wait-error"):
            with self.subTest(failure=failure):
                self.dll.fail = failure
                self.dll.peeks = 0
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)

    def test_unsolicited_and_extra_queued_frames_refuse(self):
        for stage in ("pre-peek", "post-peek"):
            with self.subTest(stage=stage):
                self.dll.fail = stage + "-data"
                self.dll.peeks = 0
                self.dll.calls.clear()
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
                if stage == "pre-peek":
                    self.assertNotIn("WriteFile", self.dll.calls)

    def test_exceptions_at_every_stage_refuse_and_close_only_acquired_handle(self):
        for failure in ("CreateFile", "mode", "pre-peek", "WriteFile", "write-event",
                        "write-result", "ReadFile", "read-event", "read-result",
                        "getbuffer", "post-peek", "CloseHandle"):
            with self.subTest(failure=failure):
                self.dll.fail = failure
                self.dll.calls.clear()
                self.dll.peeks = 0
                result = self.request()
                self.assertIs(result, requester.SyntheticRequestStatus.UNAVAILABLE)
                self.assertNotIn("private", repr(result))
                self.assertEqual(self.dll.calls.count("CloseHandle"), int(failure != "CreateFile"))

    def test_cancel_or_drain_errors_still_attempt_drain_and_close(self):
        for failure in ("read-cancel", "read-drain"):
            with self.subTest(failure=failure):
                self.dll.fail = failure
                self.dll.peeks = 0
                self.dll.calls.clear()
                self.dll.advance = lambda name: setattr(self.clock, "now", self.clock.now + 1) if name == "read-event" else None
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
                self.assertEqual(self.dll.calls[-3:], ["read-cancel", "read-drain", "CloseHandle"])

    def test_shared_deadline_rejects_late_results_at_each_boundary(self):
        for stage in ("CreateFile", "mode", "pre-peek", "WriteFile", "write-event",
                      "write-result", "ReadFile", "read-event", "read-result",
                      "getbuffer", "post-peek", "CloseHandle"):
            with self.subTest(stage=stage):
                self.clock.now = 0
                self.dll.calls.clear()
                self.dll.peeks = 0
                self.dll.advance = lambda name: setattr(self.clock, "now", 0.75) if name == stage else None
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
                self.assertEqual(self.dll.calls.count("CloseHandle"), 1)

    def test_completion_racing_cancellation_never_promotes_timeout(self):
        self.dll.fail = "read-event-timeout"
        with patch.object(Overlapped, "cancel", lambda operation: None):
            self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
        self.assertIn("read-drain", self.dll.calls)
        self.assertEqual(self.dll.calls[-1], "CloseHandle")

    def test_missing_standard_library_transport_fails_closed(self):
        with patch.dict(sys.modules, {"_winapi": None}):
            self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
        self.assertEqual(self.dll.calls, [])

    def test_import_and_construction_do_not_import_transport_or_probe(self):
        with patch.dict(sys.modules, {"_winapi": None}):
            runpy.run_path(requester.__file__, run_name="p310_import_only")
            requester.NativeSyntheticRequester()
        self.assertEqual(self.dll.calls, [])

    def test_non_windows_is_unavailable_without_transport(self):
        with patch.object(requester.sys, "platform", "linux"), patch.dict(sys.modules, {"_winapi": None}):
            self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
        self.assertEqual(self.dll.calls, [])

    def test_public_probe_has_no_endpoint_or_payload_arguments(self):
        self.assertEqual(list(inspect.signature(requester.NativeSyntheticRequester).parameters), [])
        self.assertEqual(list(inspect.signature(requester.NativeSyntheticRequester.request).parameters), ["self"])
        with self.assertRaises(TypeError):
            requester.NativeSyntheticRequester().request("other-pipe")

    def test_public_class_exposes_only_request(self):
        self.assertEqual([name for name in vars(requester.NativeSyntheticRequester)
                          if not name.startswith("_")], ["request"])
        for kwargs in ({"endpoint": ENDPOINT}, {"operation": 2}, {"payload": b""}):
            with self.assertRaises(TypeError):
                requester.NativeSyntheticRequester().request(**kwargs)

    def test_random_failure_zero_or_short_draw_has_no_transport_effect(self):
        for draw in (b"\0" * 8, b"", b"x" * 7, b"x" * 9):
            with self.subTest(draw=draw):
                self.random.return_value = draw
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
                self.assertEqual(self.dll.calls, [])
        self.random.side_effect = OSError("private random failure")
        self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
        self.assertEqual(self.dll.calls, [])

    def test_each_request_draws_fresh_random_id_and_always_add(self):
        frames = []
        def write(handle, data, *, overlapped):
            self.assertEqual((handle, overlapped), (310, True))
            frames.append(data)
            return Overlapped(self.dll, "write"), 0
        self.random.side_effect = [b"\x01" + b"\0" * 7, b"\xff" * 8]
        with patch.object(self.dll, "WriteFile", side_effect=write):
            for _ in range(2):
                self.assertIs(self.request(), requester.SyntheticRequestStatus.UNTRUSTED_HOLD)
        self.assertEqual(self.random.call_args_list, [unittest.mock.call(8)] * 2)
        self.assertEqual(frames, [struct.pack("<4sQB", b"C1T1", 1, 1),
                                  struct.pack("<4sQB", b"C1T1", 2**64 - 1, 1)])
        self.assertTrue(all(len(frame) == 13 for frame in frames))

    def test_random_or_clock_consuming_budget_prevents_open(self):
        def draw(_size):
            self.clock.now = 0.75
            return b"\x01" * 8
        self.random.side_effect = draw
        self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
        self.assertEqual(self.dll.calls, [])
        with patch.object(self.clock, "monotonic", side_effect=OSError):
            self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)

    def test_write_start_error_and_transferred_read_count_mismatch_refuse(self):
        with patch.object(self.dll, "WriteFile", return_value=(Overlapped(self.dll, "write"), 5)):
            self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)
            self.assertEqual(self.dll.calls[-3:], ["write-cancel", "write-drain", "CloseHandle"])
        original = Overlapped.GetOverlappedResult
        def wrong_count(operation, wait):
            if operation.kind == "read" and not wait:
                return len(EXPECTED) - 1, 0
            return original(operation, wait)
        self.dll.peeks = 0
        with patch.object(Overlapped, "GetOverlappedResult", wrong_count):
            self.assertIs(self.request(), requester.SyntheticRequestStatus.UNAVAILABLE)


# Reuse inert fake Tk widgets only; no P308 tests or native observer are invoked.
from tests.test_byok_c1_p308_native_status_observer import Widget, Root, InlineThread


class SyntheticUITests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.enterContext(patch.object(window, "time", self.clock))
        for name in ("Label", "Button", "Entry", "Checkbutton", "BooleanVar"):
            self.enterContext(patch.object(window.tk, name, Widget))
        self.enterContext(patch.object(window.threading, "Thread", InlineThread))
        # Every native transport entry is blocked here. Clicks use a fake requester.
        self.enterContext(patch.dict(sys.modules, {"_winapi": None}))
        self.request = self.enterContext(patch.object(
            window.NativeSyntheticRequester, "request",
            return_value=requester.SyntheticRequestStatus.UNTRUSTED_HOLD))
        self.observe = self.enterContext(patch.object(
            window.NativeServiceObserver, "observe", return_value=window.NativeStatus.UNAVAILABLE))
        self.credentials = self.enterContext(patch.object(
            storage, "_load_advapi32", side_effect=AssertionError("no credential access")))
        self.controller = scope.compose_user_scope_local_byok()
        self.root = Root()
        self.ui = window.LocalByokWindow(self.root, controller=self.controller)

    def assert_no_grant(self):
        self.assertFalse(self.controller.mutation_available)
        for widget in (*self.ui._choices, self.ui._entry, self.ui._confirm,
                       self.ui._delete_ack, self.ui._approve, self.ui._reject):
            self.assertEqual(widget.cget("state"), "disabled")
        self.credentials.assert_not_called()

    def test_import_construction_main_and_close_do_not_request(self):
        runpy.run_path(window.__file__, run_name="p310_ui_import_only")
        with patch.object(window.tk, "Tk", return_value=self.root), \
                patch.object(self.root, "mainloop", create=True):
            window.main()
        self.assertEqual(self.ui._synthetic.cget("text"), "Test synthetic service denial (no key)")
        self.assertEqual(self.ui._synthetic_status.cget("text"), "not requested; release HOLD")
        self.ui.close_from_window()
        self.request.assert_not_called()
        self.observe.assert_not_called()
        self.assert_no_grant()

    def test_click_only_request_never_reads_controller_key_review_or_confirmation(self):
        with patch.object(scope.LocalByokController, "inspect_presence", side_effect=AssertionError), \
                patch.object(scope.LocalByokController, "begin", side_effect=AssertionError), \
                patch.object(scope.LocalByokController, "approve", side_effect=AssertionError), \
                patch.object(scope.LocalByokController, "reject", side_effect=AssertionError), \
                patch.object(Widget, "get", side_effect=AssertionError), \
                patch.object(Widget, "set", side_effect=AssertionError), \
                patch.object(Widget, "delete", side_effect=AssertionError):
            self.ui._synthetic.invoke()
            self.root.tick()
        self.request.assert_called_once_with()
        self.observe.assert_not_called()
        self.assertIn("UNTRUSTED_HOLD", self.ui._synthetic_status.cget("text"))
        self.assertIn("peer is not attested", self.ui._synthetic_status.cget("text"))
        self.assertEqual(self.ui._synthetic.cget("state"), "disabled")
        self.assert_no_grant()

    def test_every_outcome_permanently_disables_and_sync_cannot_reenable(self):
        for result in (*requester.SyntheticRequestStatus, "READY", None):
            with self.subTest(result=result):
                ui = window.LocalByokWindow(self.root, controller=self.controller)
                self.request.return_value = result
                self.request.reset_mock()
                ui._synthetic.invoke()
                self.root.tick()
                ui._sync()
                ui.synthetic_request_from_button()
                ui._synthetic.invoke()
                self.request.assert_called_once_with()
                self.assertEqual(ui._synthetic.cget("state"), "disabled")
                self.assertIn("Release HOLD", ui._synthetic_status.cget("text"))
                self.assertIn("no keys or approval", ui._synthetic_status.cget("text"))
                if result is not requester.SyntheticRequestStatus.UNTRUSTED_HOLD:
                    self.assertIn("UNAVAILABLE", ui._synthetic_status.cget("text"))
        self.assert_no_grant()

    def test_observe_refresh_and_mutation_routes_do_not_request(self):
        with patch.object(scope.LocalByokController, "inspect_presence",
                          return_value=scope.LocalByokPresence.NOT_STORED) as presence:
            self.ui._refresh.invoke()
            presence.assert_called_once_with()
        self.ui._observe.invoke()
        self.root.tick()
        self.observe.assert_called_once_with()
        for operation in scope.LocalByokOperation:
            self.ui.review_from_button(operation)
        self.ui.approve_from_button()
        self.ui.reject_from_button()
        self.request.assert_not_called()
        self.assertEqual(self.ui._synthetic_status.cget("text"), "not requested; release HOLD")
        self.assertEqual(self.ui._synthetic.cget("state"), "normal")
        self.assert_no_grant()

    def test_synthetic_does_not_modify_observation_or_existing_review_state(self):
        before = (self.ui._native_status.cget("text"), self.ui._observing,
                  self.ui._observer_disabled, self.ui._review, self.ui._busy)
        self.ui._synthetic.invoke()
        self.root.tick()
        self.assertEqual(before, (self.ui._native_status.cget("text"), self.ui._observing,
                                 self.ui._observer_disabled, self.ui._review, self.ui._busy))
        self.assert_no_grant()

    def test_start_or_request_exception_fails_closed_without_retry(self):
        for stage in ("start", "request"):
            with self.subTest(stage=stage):
                ui = window.LocalByokWindow(self.root, controller=self.controller)
                target, attribute = ((InlineThread, "start") if stage == "start" else
                                     (window.NativeSyntheticRequester, "request"))
                with patch.object(target, attribute, side_effect=RuntimeError("private")):
                    ui._synthetic.invoke()
                self.root.tick()
                self.assertIn("UNAVAILABLE", ui._synthetic_status.cget("text"))
                self.assertNotIn("private", ui._synthetic_status.cget("text"))
                self.assertEqual(ui._synthetic.cget("state"), "disabled")
        self.assert_no_grant()

    def stalled(self):
        workers = []
        class StalledThread(InlineThread):
            def start(self):
                self.alive = True
                workers.append(self)
        with patch.object(window.threading, "Thread", StalledThread):
            self.ui._synthetic.invoke()
        return workers

    def test_empty_queue_ui_budget_latches_late_worker_and_never_retries(self):
        workers = self.stalled()
        old_queue = self.ui._synthetic_results
        for _ in range(10):
            self.ui.synthetic_request_from_button()
        self.assertEqual(len(workers), 1)
        self.clock.now = 1.499
        self.root.tick()
        self.assertEqual(len(self.root.pending), 1)
        self.clock.now = 1.5
        self.root.tick()
        self.assertFalse(self.root.pending)
        self.assertFalse(self.ui._synthetic_pending)
        self.assertIsNone(self.ui._synthetic_results)
        text = self.ui._synthetic_status.cget("text")
        self.assertIn("UNAVAILABLE", text)
        workers[0].target()
        workers[0].alive = False
        self.assertFalse(old_queue.empty())
        self.ui._poll_synthetic_request()
        self.ui.synthetic_request_from_button()
        self.ui._synthetic.invoke()
        self.assertEqual(self.ui._synthetic_status.cget("text"), text)
        self.assertEqual(self.ui._synthetic.cget("state"), "disabled")
        self.assertFalse(self.root.pending)
        self.request.assert_called_once_with()
        self.assert_no_grant()

    def test_close_cancels_both_polls_and_worker_touches_no_tk_after_close(self):
        workers = self.stalled()
        self.ui._observe.invoke()
        self.assertEqual(len(self.root.pending), 2)
        self.ui.close_from_window()
        self.assertFalse(self.root.pending)
        text = self.ui._synthetic_status.cget("text")
        with patch.object(Widget, "configure", side_effect=AssertionError("Tk after close")):
            workers[0].target()
            self.ui._poll_synthetic_request()
            self.ui.synthetic_request_from_button()
        self.assertEqual(self.ui._synthetic_status.cget("text"), text)
        self.assertIsNone(self.ui._synthetic_results)
        self.assertFalse(self.root.live)
        self.assert_no_grant()

    def test_posted_result_at_deadline_or_missing_result_remains_disabled(self):
        self.ui._synthetic.invoke()
        self.clock.now = 1.5
        self.root.tick()
        self.assertIn("UNAVAILABLE", self.ui._synthetic_status.cget("text"))
        ui = window.LocalByokWindow(self.root, controller=self.controller)
        with patch.object(InlineThread, "start", return_value=None):
            ui._synthetic.invoke()
        self.clock.now = 3.0
        self.root.tick()
        self.assertFalse(self.root.pending)
        self.assertIn("UNAVAILABLE", ui._synthetic_status.cget("text"))
        self.assertEqual(ui._synthetic.cget("state"), "disabled")

    def test_worker_posted_but_alive_is_always_single_attempt(self):
        class PostingThread(InlineThread):
            def start(self):
                self.alive = True
                self.target()
        with patch.object(window.threading, "Thread", PostingThread):
            self.ui._synthetic.invoke()
        self.root.tick()
        self.ui.synthetic_request_from_button()
        self.request.assert_called_once_with()
        self.assertTrue(self.ui._synthetic_worker.is_alive())
        self.assertFalse(self.root.pending)
        self.assertEqual(self.ui._synthetic.cget("state"), "disabled")




def disposable_pipe_child(endpoint, scenario):
    """Real OS transport, isolated from the runner by a parent process deadline."""
    import _winapi

    prefix = r"\\.\pipe\P310.Disposable."
    assert endpoint.startswith(prefix) and endpoint != ENDPOINT
    identity = uuid.UUID(hex=endpoint[len(prefix):])
    assert identity.int != 0 and identity.hex == endpoint[len(prefix):]
    assert scenario in {"exact", "counterfeit", "delayed", "malformed", "partial", "oversize",
                        "extra", "absent", "stalled", "stop"}
    if scenario == "absent":
        with patch.object(requester, "_PIPE", endpoint):
            assert requester.NativeSyntheticRequester().request() is requester.SyntheticRequestStatus.UNAVAILABLE
        print("OS_PIPE=absent RESULT=UNAVAILABLE", flush=True)
        return

    ready = threading.Event()
    client_done = threading.Event()
    replies_ready = threading.Event()
    errors = []
    queries = []

    def server():
        handle = None
        active = None
        try:
            # Same test user's default security descriptor; one random, local,
            # first-instance-only message pipe. Never the product endpoint.
            handle = _winapi.CreateNamedPipe(
                endpoint, 3 | _winapi.FILE_FLAG_OVERLAPPED | 0x00080000,
                4 | _winapi.PIPE_READMODE_MESSAGE | 8, 1, 1024, 1024, 0, 0,
            )

            def finish(operation):
                assert _winapi.WaitForSingleObject(operation.event, 2000) == 0, "server I/O deadline"
                count, error = operation.GetOverlappedResult(False)
                assert error == 0, ("server I/O error", error)
                return count

            active = _winapi.ConnectNamedPipe(handle, overlapped=True)
            ready.set()
            finish(active)
            active = None
            active, error = _winapi.ReadFile(handle, 14, overlapped=True)
            assert error in (0, _winapi.ERROR_IO_PENDING)
            count = finish(active)
            query = active.getbuffer()
            active = None
            assert count == 13 and len(query) == 13, "exact thirteen-byte message required"
            magic, request_id, operation = struct.unpack("<4sQB", query)
            assert magic == b"C1T1" and request_id > 0 and operation == 1, "synthetic Add required"
            queries.append(query)
            if scenario == "stop":
                return  # Actual server handle closure before any reply.
            if scenario != "stalled":
                if scenario == "delayed":
                    assert not client_done.wait(0.15), "client must wait for delayed response"
                reply = {"exact": EXPECTED, "counterfeit": EXPECTED,
                         "delayed": EXPECTED, "extra": EXPECTED, "malformed": b"READY",
                         "partial": EXPECTED[:-1], "oversize": EXPECTED + b"x" * 200}[scenario]
                active, error = _winapi.WriteFile(handle, reply, overlapped=True)
                assert error in (0, _winapi.ERROR_IO_PENDING)
                assert finish(active) == len(reply)
                active = None
                if scenario == "extra":
                    active, error = _winapi.WriteFile(handle, b"extra", overlapped=True)
                    assert error in (0, _winapi.ERROR_IO_PENDING)
                    assert finish(active) == 5
                    active = None
                replies_ready.set()
            # Preserve buffered replies until the client consumes them. The
            # stalled case deliberately leaves the client's real read pending.
            assert client_done.wait(2), "client completion deadline"
        except BaseException as error:
            errors.append(error)
        finally:
            ready.set()
            try:
                if active is not None:
                    try:
                        active.cancel()
                    finally:
                        active.GetOverlappedResult(True)
            except BaseException as error:
                errors.append(error)
            finally:
                if handle is not None:
                    try:
                        _winapi.CloseHandle(handle)
                    except BaseException as error:
                        errors.append(error)

    thread = threading.Thread(target=server, daemon=True)
    thread.start()
    try:
        assert ready.wait(2), "server startup deadline"
        assert not errors, errors
        started = time.monotonic()
        read_file = _winapi.ReadFile
        def read_after_extra(handle, size, *, overlapped):
            # Test-only scheduling: both messages must really be queued before
            # the client reads. Server uses the original OS ReadFile directly.
            if threading.current_thread() is threading.main_thread():
                assert replies_ready.wait(2), "extra frame scheduling deadline"
            return read_file(handle, size, overlapped=overlapped)
        with patch.object(requester, "_PIPE", endpoint):
            if scenario == "extra":
                with patch.object(_winapi, "ReadFile", side_effect=read_after_extra):
                    result = requester.NativeSyntheticRequester().request()
            else:
                result = requester.NativeSyntheticRequester().request()
        elapsed = time.monotonic() - started
    finally:
        client_done.set()
        thread.join(3)
    assert not thread.is_alive(), "server cleanup deadline"
    assert not errors, errors
    assert len(queries) == 1 and len(queries[0]) == 13, queries
    expected = (requester.SyntheticRequestStatus.UNTRUSTED_HOLD
                if scenario in {"exact", "counterfeit", "delayed"}
                else requester.SyntheticRequestStatus.UNAVAILABLE)
    assert result is expected, (scenario, result)
    assert elapsed < 2, ("client deadline/cleanup", elapsed)
    if scenario == "stalled":
        assert elapsed >= 0.65, ("read was not actually stalled", elapsed)
    if scenario == "delayed":
        assert elapsed >= 0.14, ("response was not actually delayed", elapsed)
    print("OS_PIPE=" + scenario + " QUERY_BYTES=13 RESULT=" + result.value, flush=True)


@unittest.skipUnless(sys.platform == "win32", "real disposable named pipes require Windows")
class DisposableWindowsPipeTests(unittest.TestCase):
    def run_pipe(self, scenario):
        endpoint = r"\\.\pipe\P310.Disposable." + uuid.uuid4().hex
        # A blocked kernel drain or server cannot hang the suite. subprocess.run
        # kills and waits for this disposable child on its ten-second deadline.
        child = subprocess.run(
            [sys.executable, "-B", "-m", "tests.test_byok_c1_p310_native_synthetic_request",
             "--pipe-child", endpoint, scenario],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            timeout=10, check=False, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
        print(child.stdout, end="")
        self.assertIn("OS_PIPE=" + scenario, child.stdout)
        expected = "UNTRUSTED_HOLD" if scenario in {"exact", "counterfeit", "delayed"} else "UNAVAILABLE"
        self.assertIn("RESULT=" + expected, child.stdout)
        if scenario != "absent":
            self.assertIn("QUERY_BYTES=13", child.stdout)

    def test_os_exact_thirteen_byte_query_and_fixed_reply(self):
        self.run_pipe("exact")

    def test_os_untrusted_counterfeit_exact_denial_is_only_hold(self):
        self.run_pipe("counterfeit")

    def test_os_extra_complete_message_is_rejected(self):
        self.run_pipe("extra")

    def test_os_delayed_response_within_budget_is_still_only_untrusted_hold(self):
        self.run_pipe("delayed")

    def test_os_malformed_reply(self):
        self.run_pipe("malformed")

    def test_os_partial_reply(self):
        self.run_pipe("partial")

    def test_os_oversized_message(self):
        self.run_pipe("oversize")

    def test_os_absent_random_endpoint(self):
        self.run_pipe("absent")

    def test_os_stalled_read_cancels_and_cleans_up(self):
        self.run_pipe("stalled")

    def test_os_server_stop_closes_without_reply(self):
        self.run_pipe("stop")


def check_requester_source(source):
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.asname is None for alias in node.names)
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0 and all(alias.asname is None for alias in node.names)
            imports.add(node.module)
    assert imports == {"__future__", "enum", "os", "struct", "sys", "time", "_winapi"}
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
               and node.name == "NativeSyntheticRequester")
    methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)]
    assert len(methods) == 1 and methods[0].name == "request"
    method = methods[0]
    assert ast.dump(method.args) == ast.dump(ast.parse("def request(self): pass").body[0].args)
    assert ast.dump(method.body[0]) == ast.dump(ast.parse(
        'if sys.platform != "win32": return SyntheticRequestStatus.UNAVAILABLE').body[0])
    native_imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import)
                      and any(alias.name == "_winapi" for alias in node.names)]
    assert len(native_imports) == 1 and native_imports[0] in set(ast.walk(method))
    assert native_imports[0] in method.body[4].body  # Inside the explicit try only.
    assert not any(isinstance(node, (ast.For, ast.While, ast.AsyncFunctionDef)) for node in ast.walk(tree))
    constants = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                 if isinstance(node, ast.Assign)}
    assert constants == {"_PIPE": ENDPOINT, "_REPLY": EXPECTED, "_SECONDS": 0.75}
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    native = [node.func.attr for node in calls if isinstance(node.func, ast.Attribute)
              and isinstance(node.func.value, ast.Name) and node.func.value.id == "_winapi"]
    assert sorted(native) == sorted(["CreateFile", "SetNamedPipeHandleState", "WriteFile",
                                     "ReadFile", "WaitForSingleObject", "PeekNamedPipe",
                                     "PeekNamedPipe", "CloseHandle"])
    packs = [node for node in calls if ast.unparse(node.func) == "struct.pack"]
    assert len(packs) == 1 and ast.dump(packs[0]) == ast.dump(ast.parse(
        "struct.pack('<4sQB', b'C1T1', request_id, 1)", mode="eval").body)
    random = [node for node in calls if ast.unparse(node.func) == "os.urandom"]
    assert len(random) == 1 and ast.dump(random[0]) == ast.dump(ast.parse(
        "os.urandom(8)", mode="eval").body)
    for forbidden in ("CredRead", "CredWrite", "CredDelete", "advapi", "provider",
                      "subprocess", "socket", "requests", "OpenSCManager", "StartService",
                      "ShellExecute", "FlushFileBuffers", "WaitNamedPipe", "PIPE_NOWAIT",
                      "ctypes", "eval(", "exec(", "__import__(", "getattr(", "setattr("):
        assert forbidden not in source


class SourceBoundaryTests(unittest.TestCase):
    def test_requester_ast_effect_boundary_and_negative_tampering(self):
        source = Path(requester.__file__).read_text(encoding="utf-8")
        check_requester_source(source)
        mutations = [source + addition for addition in (
            "\nimport socket\n", "\nimport ctypes\n", "\n_winapi.CredWriteW()\n",
            "\nimport nayeon.secrets.windows_credential\n", "\n_winapi.StartServiceW()\n")]
        mutations += [source.replace("request_id, 1)", "request_id, 2)"),
                      source.replace("os.urandom(8)", "os.urandom(7)"),
                      source.replace("def request(self)", "def request(self, endpoint)"),
                      source.replace("0.75", "5.0")]
        for mutated in mutations:
            with self.subTest(mutation=mutated[-80:]), self.assertRaises(AssertionError):
                check_requester_source(mutated)

    def test_synthetic_ui_ast_has_no_key_controller_or_observation_route(self):
        for method in (window.LocalByokWindow.synthetic_request_from_button,
                       window.LocalByokWindow._poll_synthetic_request):
            source = inspect.getsource(method)
            for forbidden in ("_controller", "SecretValue", "approve_from_button",
                              "review_from_button", "inspect_presence", "_sync(", "_entry",
                              "_confirmed", "_delete_checked", "NativeServiceObserver", "_observe"):
                self.assertNotIn(forbidden, source)
        source = inspect.getsource(window.LocalByokWindow.synthetic_request_from_button)
        tree = ast.parse(textwrap.dedent(source))
        worker = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                      and node.name == "worker")
        self.assertNotIn("self", {node.id for node in ast.walk(worker) if isinstance(node, ast.Name)})
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and ast.unparse(node.func) == "threading.Thread"]
        self.assertEqual(len(calls), 1)
        self.assertIn("daemon=True", ast.unparse(calls[0]))

    def test_frozen_p275_p308_and_p309_sources_equal_parent(self):
        root = Path(__file__).resolve().parents[1]
        frozen = {
            "scripts/p275_product_effect_entrypoint_inventory.py":
                "48e7cc20c83b984b80c25a2fa4217baaf84a94f45618518c26eebd14e7125ee7",
            "tests/test_byok_c1_p275_native_effect_retirement.py":
                "78b53c5bd8ca7d7e8f0bb51aa52de081c46956930aa248c03e371499b5e97c26",
            "nayeon/desktop_alpha/byok_native_service_observer.py":
                "273c203ca5848d76845adeaa04158adf4954fea28cda4aadeb17e81e3785f0a4",
            "src/Nayeon.ByokC1.Service/SyntheticIngressServer.cs":
                "d75cd0206f2d4d86f993fb86c730be68e51dad283c6e0f67d5109e21b6ce3c9c",
        }
        for path, digest in frozen.items():
            with self.subTest(path=path):
                # Git checkout may convert line endings; frozen semantics bind LF bytes.
                self.assertEqual(hashlib.sha256((root / path).read_bytes().replace(
                    b"\r\n", b"\n")).hexdigest(), digest)

    def test_existing_ui_methods_frozen_ast_and_only_button_calls_new_handler(self):
        parent = subprocess.run(
            ["git", "show", "adff32e2978c7dd21fb3c10f9a8805e555d5c41f:"
             "nayeon/desktop_alpha/local_byok_window.py"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            encoding="utf-8", errors="strict", timeout=5, check=True,
        ).stdout
        current = Path(window.__file__).read_text(encoding="utf-8")
        before, after = ast.parse(parent), ast.parse(current)
        def functions(tree):
            nodes = list(tree.body)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    nodes.extend(node.body)
            return {node.name: node for node in nodes if isinstance(node, ast.FunctionDef)}
        old, new = functions(before), functions(after)
        for name, method in old.items():
            if name in {"__init__", "close_from_window"}:
                new[name].body = [node for node in new[name].body
                                  if "synthetic" not in ast.unparse(node)]
            self.assertEqual(ast.dump(method), ast.dump(new[name]), name)
        for node in ast.walk(after):
            if isinstance(node, ast.Call):
                self.assertNotEqual(ast.unparse(node.func), "self.synthetic_request_from_button")
        self.assertNotIn("request()", inspect.getsource(window.LocalByokWindow.__init__))
        self.assertNotIn("synthetic", inspect.getsource(window.main))

    def test_child_refuses_product_noncanonical_and_zero_uuid_before_any_open(self):
        for endpoint in (ENDPOINT, r"\\.\pipe\P310.Disposable." + "0" * 32,
                         r"\\.\pipe\P310.Disposable." + "A" * 32,
                         r"\\remote\pipe\P310.Disposable." + uuid.uuid4().hex):
            with self.subTest(endpoint=endpoint), patch.dict(sys.modules, {"_winapi": object()}):
                with self.assertRaises(AssertionError):
                    disposable_pipe_child(endpoint, "exact")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--pipe-child":
        disposable_pipe_child(sys.argv[2], sys.argv[3])
    else:
        unittest.main()
