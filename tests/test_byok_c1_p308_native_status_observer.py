"""P308 fake edge injection, UI lifecycle, and disposable real Windows pipes.

The OS tests run in bounded children against random test-only endpoints, under
this test user's token. No installed service, key, credential API, or elevation.
"""

import ast
import inspect
from pathlib import Path
import runpy
import subprocess
import sys
import threading
import time
import unittest
import uuid
from unittest.mock import patch

from nayeon.desktop_alpha import byok_native_service_observer as observer
from nayeon.desktop_alpha import local_byok_window as window
from nayeon.brain import local_byok_user_scope as scope
from nayeon.secrets import windows_credential as storage


EXPECTED = b"C1|NOT_AUTHORIZED|HOLD|NO_CREDENTIALS"
ENDPOINT = r"\\.\pipe\NayeonV1ByokCustody.Status.v1"


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
            return (0 if self.api.fail == "short-write" else 4), 0
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
        return 308

    def SetNamedPipeHandleState(self, handle, mode, maximum, timeout):
        self.stage("mode")
        assert (handle, mode, maximum, timeout) == (308, 2, None, None)

    def PeekNamedPipe(self, handle, size):
        assert (handle, size) == (308, 0)
        self.peeks += 1
        stage = "pre-peek" if self.peeks % 2 else "post-peek"
        self.stage(stage)
        return (4, 4) if self.fail == stage + "-data" else (0, 0)

    def WriteFile(self, handle, data, *, overlapped):
        self.stage("WriteFile")
        assert handle == 308 and data == b"C1S1" and overlapped is True
        return Overlapped(self, "write"), (997 if self.pending else 0)

    def ReadFile(self, handle, capacity, *, overlapped):
        self.stage("ReadFile")
        assert handle == 308 and capacity == len(EXPECTED) + 1 and overlapped is True
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
        assert handle == 308


class TransportFixture:
    def setUp(self):
        self.clock = Clock()
        self.dll = PipeAPI(self.clock)
        self.enterContext(patch.object(observer.sys, "platform", "win32"))
        self.enterContext(patch.dict(sys.modules, {"_winapi": self.dll}))
        self.enterContext(patch.object(observer, "time", self.clock))

    def observe(self):
        return observer.NativeServiceObserver().observe()


class ObserverTests(TransportFixture, unittest.TestCase):
    def test_exact_response_overlapped_message_mode_and_anonymous_sqos(self):
        self.assertIs(self.observe(), observer.NativeStatus.UNTRUSTED_HOLD)
        self.assertEqual(self.dll.calls, ["CreateFile", "mode", "pre-peek", "WriteFile",
                         "write-event", "write-result", "ReadFile", "read-event",
                         "read-result", "getbuffer", "post-peek", "CloseHandle"])
        self.assertEqual(set(observer.NativeStatus), {
            observer.NativeStatus.UNAVAILABLE, observer.NativeStatus.UNTRUSTED_HOLD})

    def test_immediate_overlapped_completion_needs_no_event_wait(self):
        self.dll.pending = False
        self.assertIs(self.observe(), observer.NativeStatus.UNTRUSTED_HOLD)
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
                self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)
                self.assertEqual(self.dll.calls.count("ReadFile"), 1)
                self.assertEqual(self.dll.calls.count("CloseHandle"), 1)

    def test_timeout_cancels_drains_before_close_for_read_and_write(self):
        for kind in ("read", "write"):
            with self.subTest(kind=kind):
                self.clock.now = 0
                self.dll.calls.clear()
                self.dll.peeks = 0
                self.dll.fail = kind + "-event-timeout"
                self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)
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
                self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)

    def test_short_write_incomplete_completion_and_failed_wait_refuse(self):
        for failure in ("short-write", "completion-error", "wait-error"):
            with self.subTest(failure=failure):
                self.dll.fail = failure
                self.dll.peeks = 0
                self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)

    def test_unsolicited_and_extra_queued_frames_refuse(self):
        for stage in ("pre-peek", "post-peek"):
            with self.subTest(stage=stage):
                self.dll.fail = stage + "-data"
                self.dll.peeks = 0
                self.dll.calls.clear()
                self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)
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
                result = self.observe()
                self.assertIs(result, observer.NativeStatus.UNAVAILABLE)
                self.assertNotIn("private", repr(result))
                self.assertEqual(self.dll.calls.count("CloseHandle"), int(failure != "CreateFile"))

    def test_cancel_or_drain_errors_still_attempt_drain_and_close(self):
        for failure in ("read-cancel", "read-drain"):
            with self.subTest(failure=failure):
                self.dll.fail = failure
                self.dll.peeks = 0
                self.dll.calls.clear()
                self.dll.advance = lambda name: setattr(self.clock, "now", self.clock.now + 1) if name == "read-event" else None
                self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)
                self.assertEqual(self.dll.calls[-3:], ["read-cancel", "read-drain", "CloseHandle"])

    def test_shared_deadline_rejects_late_results_at_each_boundary(self):
        for stage in ("CreateFile", "mode", "pre-peek", "WriteFile", "write-event",
                      "write-result", "ReadFile", "read-event", "read-result",
                      "getbuffer", "post-peek"):
            with self.subTest(stage=stage):
                self.clock.now = 0
                self.dll.calls.clear()
                self.dll.peeks = 0
                self.dll.advance = lambda name: setattr(self.clock, "now", 0.75) if name == stage else None
                self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)
                self.assertEqual(self.dll.calls.count("CloseHandle"), 1)

    def test_completion_racing_cancellation_never_promotes_timeout(self):
        self.dll.fail = "read-event-timeout"
        with patch.object(Overlapped, "cancel", lambda operation: None):
            self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)
        self.assertIn("read-drain", self.dll.calls)
        self.assertEqual(self.dll.calls[-1], "CloseHandle")

    def test_missing_standard_library_transport_fails_closed(self):
        with patch.dict(sys.modules, {"_winapi": None}):
            self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)
        self.assertEqual(self.dll.calls, [])

    def test_import_and_construction_do_not_import_transport_or_probe(self):
        with patch.dict(sys.modules, {"_winapi": None}):
            runpy.run_path(observer.__file__, run_name="p308_import_only")
            observer.NativeServiceObserver()
        self.assertEqual(self.dll.calls, [])

    def test_non_windows_is_unavailable_without_transport(self):
        with patch.object(observer.sys, "platform", "linux"), patch.dict(sys.modules, {"_winapi": None}):
            self.assertIs(self.observe(), observer.NativeStatus.UNAVAILABLE)
        self.assertEqual(self.dll.calls, [])

    def test_public_probe_has_no_endpoint_or_payload_arguments(self):
        self.assertEqual(list(inspect.signature(observer.NativeServiceObserver).parameters), [])
        self.assertEqual(list(inspect.signature(observer.NativeServiceObserver.observe).parameters), ["self"])
        with self.assertRaises(TypeError):
            observer.NativeServiceObserver().observe("other-pipe")


class Widget:
    def __init__(self, *args, **kwargs):
        self.options = dict(kwargs)
        self.value = kwargs.get("value", False)

    def pack(self, **kwargs):
        pass

    def bind(self, *args):
        pass

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def cget(self, name):
        return self.options.get(name, "normal" if name == "state" else "")

    def invoke(self):
        if self.cget("state") != "disabled":
            return self.options["command"]()

    def delete(self, *args):
        pass

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class Root(Widget):
    def __init__(self):
        super().__init__()
        self.pending = {}
        self.live = True
        self.counter = 0

    def title(self, value):
        pass

    geometry = title

    def minsize(self, *args):
        pass

    def protocol(self, *args):
        pass

    def winfo_exists(self):
        return self.live

    def after(self, delay, callback):
        assert delay == 25
        self.counter += 1
        self.pending[self.counter] = callback
        return self.counter

    def after_cancel(self, identifier):
        del self.pending[identifier]

    def tick(self):
        callbacks, self.pending = self.pending, {}
        for callback in callbacks.values():
            callback()

    def destroy(self):
        self.live = False


class InlineThread:
    def __init__(self, *, target, daemon):
        assert daemon is True
        self.target = target
        self.alive = False

    def start(self):
        self.alive = True
        try:
            self.target()
        finally:
            self.alive = False

    def is_alive(self):
        return self.alive


class UIRoutingTests(TransportFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.enterContext(patch.object(window, "time", self.clock))
        for name in ("Label", "Button", "Entry", "Checkbutton", "BooleanVar"):
            self.enterContext(patch.object(window.tk, name, Widget))
        self.enterContext(patch.object(window.threading, "Thread", InlineThread))
        self.credentials = self.enterContext(patch.object(
            storage, "_load_advapi32", side_effect=AssertionError("no credential access")))
        self.controller = scope.compose_user_scope_local_byok()
        self.root = Root()
        self.ui = window.LocalByokWindow(self.root, controller=self.controller)

    def assert_disabled(self):
        self.assertFalse(self.controller.mutation_available)
        for widget in (*self.ui._choices, self.ui._entry, self.ui._confirm,
                       self.ui._delete_ack, self.ui._approve, self.ui._reject):
            self.assertEqual(widget.cget("state"), "disabled")
        self.credentials.assert_not_called()

    def test_initial_creation_and_close_never_probe(self):
        runpy.run_path(window.__file__, run_name="p308_ui_import_only")
        self.assertEqual(self.ui._native_status.cget("text"), "not observed; release HOLD")
        self.assert_disabled()
        self.ui.close_from_window()
        self.assertEqual(self.dll.calls, [])

    def test_actual_main_never_probes_or_reads_credentials(self):
        with patch.object(window.tk, "Tk", return_value=self.root), \
                patch.object(self.root, "mainloop", create=True):
            window.main()
        self.assertEqual(self.dll.calls, [])
        self.credentials.assert_not_called()

    def test_clicked_exact_and_malformed_route_cannot_enable_mutation(self):
        for reply, text in ((EXPECTED, "UNTRUSTED_HOLD"), (b"bad", "unavailable")):
            with self.subTest(reply=reply):
                self.dll.reply = reply
                self.ui._observe.invoke()
                self.assertEqual(self.ui._observe.cget("state"), "disabled")
                count = len(self.dll.calls)
                self.ui.observe_native_from_button()
                self.assertEqual(len(self.dll.calls), count)
                self.root.tick()
                self.assertIn(text, self.ui._native_status.cget("text"))
                self.assertIn("no keys or approval", self.ui._native_status.cget("text"))
                self.assertEqual(self.ui._observe.cget("state"), "normal")
                self.assert_disabled()
                for operation in scope.LocalByokOperation:
                    self.ui.review_from_button(operation)
                self.ui.approve_from_button()
                self.assertIsNone(self.ui._review)
                self.assert_disabled()

    def test_refresh_and_observation_are_separate_routes(self):
        with patch.object(scope.LocalByokController, "inspect_presence",
                          return_value=scope.LocalByokPresence.NOT_STORED) as presence:
            self.ui._refresh.invoke()
            presence.assert_called_once_with()
            self.assertEqual(self.dll.calls, [])
            self.assertEqual(self.ui._native_status.cget("text"), "not observed; release HOLD")
            presence.reset_mock()
            self.ui._observe.invoke()
            self.root.tick()
            presence.assert_not_called()
        self.assert_disabled()

    def test_close_during_worker_cancels_tk_poll_and_late_result_has_no_tk_route(self):
        workers = []
        class DeferredThread(InlineThread):
            def start(self):
                self.alive = True
                def finish():
                    try:
                        self.target()
                    finally:
                        self.alive = False
                workers.append(finish)
        with patch.object(window.threading, "Thread", DeferredThread):
            self.ui._observe.invoke()
        self.root.tick()  # Empty queue reschedules without a busy wait
        self.assertEqual(len(self.root.pending), 1)
        self.ui.close_from_window()
        self.assertFalse(self.root.pending)
        workers[0]()  # Native work completes after Tk was destroyed
        self.ui._poll_native_observation()
        self.ui.observe_native_from_button()
        self.assertEqual(self.dll.calls.count("CreateFile"), 1)
        self.assertFalse(self.root.live)
        self.assert_disabled()

    def test_thread_start_failure_reports_unavailable_without_probe(self):
        with patch.object(InlineThread, "start", side_effect=RuntimeError("private")):
            self.ui._observe.invoke()
        self.root.tick()
        self.assertIn("unavailable", self.ui._native_status.cget("text"))
        self.assertEqual(self.dll.calls, [])
        self.assert_disabled()

    def test_ui_deadline_stops_polling_latches_worker_and_ignores_late_result(self):
        workers = []
        class StalledThread(InlineThread):
            def start(self):
                self.alive = True
                workers.append(self)
        with patch.object(window.threading, "Thread", StalledThread):
            self.ui._observe.invoke()
            for _ in range(10):
                self.ui.observe_native_from_button()
            self.assertEqual(len(workers), 1)
            self.clock.now = 1.499
            self.root.tick()
            self.assertEqual(len(self.root.pending), 1)
            self.clock.now = 1.5
            self.root.tick()
            self.assertFalse(self.root.pending)
            self.assertFalse(self.ui._observing)
            self.assertTrue(self.ui._observer_disabled)
            self.assertIn("unavailable", self.ui._native_status.cget("text"))
            text = self.ui._native_status.cget("text")
            workers[0].target()  # Exact HOLD arrives after the UI deadline.
            workers[0].alive = False
            self.ui._poll_native_observation()
            self.ui.observe_native_from_button()
            self.ui._observe.invoke()
            self.assertEqual(len(workers), 1)
            self.assertEqual(self.ui._native_status.cget("text"), text)
            self.assertEqual(self.ui._observe.cget("state"), "disabled")
            self.assertFalse(self.root.pending)
        self.assert_disabled()

    def test_posted_result_at_ui_deadline_is_stale_even_if_worker_finished(self):
        self.ui._observe.invoke()
        self.clock.now = 1.5
        self.root.tick()
        self.assertIn("unavailable", self.ui._native_status.cget("text"))
        self.assertEqual(self.ui._observe.cget("state"), "normal")
        self.assertFalse(self.root.pending)
        self.assert_disabled()

    def test_finished_worker_missing_result_times_out_then_fresh_queue_is_used(self):
        with patch.object(InlineThread, "start", return_value=None):
            self.ui._observe.invoke()
        old_results = self.ui._observation_results
        self.clock.now = 1.5
        self.root.tick()
        self.assertFalse(self.root.pending)
        self.assertFalse(self.ui._observer_disabled)
        self.assertIn("unavailable", self.ui._native_status.cget("text"))
        self.dll.reply = b"bad"
        self.ui._observe.invoke()
        old_results.put_nowait(observer.NativeStatus.UNTRUSTED_HOLD)
        self.root.tick()
        self.assertIsNot(self.ui._observation_results, old_results)
        self.assertIn("unavailable", self.ui._native_status.cget("text"))
        self.assert_disabled()

    def test_posted_result_with_worker_still_alive_latches_no_duplicate(self):
        class PostingThread(InlineThread):
            def start(self):
                self.alive = True
                self.target()
        with patch.object(window.threading, "Thread", PostingThread):
            self.ui._observe.invoke()
            self.root.tick()
            self.ui.observe_native_from_button()
        self.assertTrue(self.ui._observer_disabled)
        self.assertEqual(self.dll.calls.count("CreateFile"), 1)
        self.assertFalse(self.root.pending)
        self.assert_disabled()


def disposable_pipe_child(endpoint, scenario):
    """Real OS transport, isolated from the runner by a parent process deadline."""
    import _winapi

    prefix = r"\\.\pipe\P308.Disposable."
    assert endpoint.startswith(prefix) and endpoint != ENDPOINT
    assert uuid.UUID(hex=endpoint[len(prefix):]).hex == endpoint[len(prefix):]
    assert scenario in {"exact", "malformed", "partial", "oversize", "absent", "stalled", "stop"}
    if scenario == "absent":
        with patch.object(observer, "_PIPE", endpoint):
            assert observer.NativeServiceObserver().observe() is observer.NativeStatus.UNAVAILABLE
        print("OS_PIPE=absent RESULT=UNAVAILABLE", flush=True)
        return

    ready = threading.Event()
    client_done = threading.Event()
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
            active, error = _winapi.ReadFile(handle, 5, overlapped=True)
            assert error in (0, _winapi.ERROR_IO_PENDING)
            count = finish(active)
            query = active.getbuffer()
            active = None
            assert count == 4 and query == b"C1S1", "client must really write exactly four bytes"
            queries.append(query)
            if scenario == "stop":
                return  # Actual server handle closure before any reply.
            if scenario != "stalled":
                reply = {"exact": EXPECTED, "malformed": b"READY",
                         "partial": EXPECTED[:-1], "oversize": EXPECTED + b"x" * 200}[scenario]
                active, error = _winapi.WriteFile(handle, reply, overlapped=True)
                assert error in (0, _winapi.ERROR_IO_PENDING)
                assert finish(active) == len(reply)
                active = None
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
        with patch.object(observer, "_PIPE", endpoint):
            result = observer.NativeServiceObserver().observe()
        elapsed = time.monotonic() - started
    finally:
        client_done.set()
        thread.join(3)
    assert not thread.is_alive(), "server cleanup deadline"
    assert not errors, errors
    assert queries == [b"C1S1"], queries
    expected = observer.NativeStatus.UNTRUSTED_HOLD if scenario == "exact" else observer.NativeStatus.UNAVAILABLE
    assert result is expected, (scenario, result)
    assert elapsed < 2, ("client deadline/cleanup", elapsed)
    if scenario == "stalled":
        assert elapsed >= 0.65, ("read was not actually stalled", elapsed)
    print("OS_PIPE=" + scenario + " QUERY_BYTES=4 RESULT=" + result.value, flush=True)


@unittest.skipUnless(sys.platform == "win32", "real disposable named pipes require Windows")
class DisposableWindowsPipeTests(unittest.TestCase):
    def run_pipe(self, scenario):
        endpoint = r"\\.\pipe\P308.Disposable." + uuid.uuid4().hex
        # A blocked kernel drain or server cannot hang the suite. subprocess.run
        # kills and waits for this disposable child on its ten-second deadline.
        child = subprocess.run(
            [sys.executable, "-B", "-m", "tests.test_byok_c1_p308_native_status_observer",
             "--pipe-child", endpoint, scenario],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            timeout=10, check=False, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
        print(child.stdout, end="")
        self.assertIn("OS_PIPE=" + scenario, child.stdout)
        self.assertIn("RESULT=" + ("UNTRUSTED_HOLD" if scenario == "exact" else "UNAVAILABLE"), child.stdout)
        if scenario != "absent":
            self.assertIn("QUERY_BYTES=4", child.stdout)

    def test_os_exact_four_byte_query_and_fixed_reply(self):
        self.run_pipe("exact")

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


def check_observer_source(source):
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module)
    assert imports == {"__future__", "_winapi", "enum", "sys", "time"}
    native_import = next(node for node in ast.walk(tree) if isinstance(node, ast.Import)
                         and any(alias.name == "_winapi" for alias in node.names))
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                  and node.name == "observe")
    assert native_import in set(ast.walk(method))
    assert all(not isinstance(node, ast.Import) or
               all(alias.name != "_winapi" for alias in node.names) for node in tree.body)
    native_calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "_winapi"}
    assert native_calls == {"CreateFile", "SetNamedPipeHandleState", "WriteFile", "ReadFile",
                            "WaitForSingleObject", "PeekNamedPipe", "CloseHandle"}
    for forbidden in ("CredRead", "CredWrite", "CredDelete", "advapi", "provider", "subprocess",
                      "socket", "requests", "OpenSCManager", "StartService", "ShellExecute",
                      "FlushFileBuffers", "WaitNamedPipe", "PIPE_NOWAIT", "ctypes",
                      "eval(", "exec(", "__import__("):
        assert forbidden not in source


class SourceBoundaryTests(unittest.TestCase):
    def test_observer_imports_and_native_call_surface_are_bounded(self):
        source = Path(observer.__file__).read_text(encoding="utf-8")
        check_observer_source(source)
        for addition in ("\nimport socket\n", "\nimport nayeon.secrets.windows_credential\n",
                         "\n_winapi.CredWriteW()\n", "\n_winapi.StartServiceW()\n",
                         "\nimport ctypes\n"):
            with self.subTest(addition=addition), self.assertRaises(AssertionError):
                check_observer_source(source + addition)

    def test_actual_ui_observation_methods_have_no_controller_or_submission_route(self):
        for method in (window.LocalByokWindow.observe_native_from_button,
                       window.LocalByokWindow._poll_native_observation):
            source = inspect.getsource(method)
            for forbidden in ("_controller", "SecretValue", "approve_from_button",
                              "review_from_button", "inspect_presence", "_sync(", "_entry"):
                self.assertNotIn(forbidden, source)
        self.assertNotIn("observe()", inspect.getsource(window.LocalByokWindow.__init__))
        self.assertNotIn("observe", inspect.getsource(window.LocalByokWindow.refresh_from_button))
        self.assertNotIn("observe", inspect.getsource(window.main))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--pipe-child":
        disposable_pipe_child(sys.argv[2], sys.argv[3])
    else:
        unittest.main()
