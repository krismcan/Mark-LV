"""Disposable Windows integration, never production identity qualification."""
from __future__ import annotations

import os
from pathlib import Path
import queue
import re
import struct
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
import uuid

from nayeon.desktop_alpha import byok_native_synthetic_request as requester

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "P309.Disposable."
PIPE_PREFIX = "\\\\.\\pipe\\" + PREFIX
REPLY = b"C1|DENIED|HOLD|NO_CREDENTIALS"
SCENARIOS = {"add", "replace", "delete", "magic", "zero", "operation", "oversize", "idle"}


def endpoint(value):
    if (type(value) is not str or
            re.fullmatch(r"P309\.Disposable\.[0-9a-f]{32}", value) is None or
            uuid.UUID(hex=value[len(PREFIX):]).int == 0):
        raise ValueError("isolated endpoint required")
    return "\\\\.\\pipe\\" + value


def harness_path():
    raw = os.environ.get("P311_TEST_HARNESS", "")
    temp = os.environ.get("RUNNER_TEMP", "")
    path = Path(raw)
    base = Path(temp)
    if (not raw or not temp or not path.is_absolute() or not base.is_absolute() or
            str(path.resolve(strict=True)) != raw or base.resolve(strict=True) not in path.parents or
            path.name != "P309.ProductService.Tests.exe" or not path.is_file()):
        raise ValueError("canonical runner-temp harness required")
    return raw


class Captured:
    """Drain both streams with a 4 KiB cap each; never include bytes in errors."""
    def __init__(self, process):
        self.process = process
        self.data = [bytearray(), bytearray()]
        self.overflow = threading.Event()
        self.lines = queue.Queue(maxsize=128)
        self.threads = []
        for index, stream in enumerate((process.stdout, process.stderr)):
            thread = threading.Thread(target=self.drain, args=(index, stream), daemon=True)
            thread.start()
            self.threads.append(thread)

    def drain(self, index, stream):
        while True:
            byte = stream.read(1)
            if not byte:
                return
            if len(self.data[index]) >= 4096:
                self.overflow.set()
                continue
            self.data[index].extend(byte)
            if index == 0 and byte == b"\n":
                try:
                    self.lines.put_nowait(bytes(self.data[0]).splitlines()[-1])
                except queue.Full:
                    self.overflow.set()

    def finish(self, deadline):
        self.process.wait(timeout=max(0.001, deadline - time.monotonic()))
        for thread in self.threads:
            thread.join(timeout=max(0.001, deadline - time.monotonic()))
            if thread.is_alive():
                raise AssertionError("output drain deadline")
        if self.overflow.is_set() or self.data[1]:
            raise AssertionError("unexpected child output")
        if self.process.returncode != 0:
            raise AssertionError("child failed")
        return bytes(self.data[0]).splitlines()


def spawn(arguments):
    return subprocess.Popen(arguments, cwd=ROOT, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW)


def stop(process):
    if process.poll() is None:
        process.kill()
    process.wait(timeout=2)
    for stream in (process.stdin, process.stdout, process.stderr):
        stream.close()


def client(name, scenario):
    pipe = endpoint(name)  # Validate before importing native APIs or opening anything.
    if scenario not in SCENARIOS - {"idle"}:
        raise ValueError("synthetic scenario required")
    if scenario == "add":
        with patch.object(requester, "_PIPE", pipe):
            result = requester.NativeSyntheticRequester().request()
        if result is not requester.SyntheticRequestStatus.UNTRUSTED_HOLD or result.value == "READY":
            raise AssertionError("untrusted HOLD required")
        print("UNTRUSTED_HOLD", flush=True)
        return
    import _winapi
    deadline = time.monotonic() + 2
    handle = None
    active = None

    def complete(operation, error):
        remaining = int((deadline - time.monotonic()) * 1000)
        if remaining <= 0:
            raise TimeoutError
        if error == _winapi.ERROR_IO_PENDING:
            if _winapi.WaitForSingleObject(operation.event, remaining) != 0:
                raise TimeoutError
        elif error != 0:
            raise OSError(error, "synthetic I/O failed")
        count, error = operation.GetOverlappedResult(False)
        if error:
            raise OSError(error, "synthetic I/O failed")
        if time.monotonic() >= deadline:
            raise TimeoutError
        return count

    denied = scenario in {"replace", "delete"}
    frame = struct.pack("<4sQB", b"BAD!" if scenario == "magic" else b"C1T1",
                        0 if scenario == "zero" else 0x0102030405060708,
                        {"replace": 2, "delete": 3, "operation": 4}.get(scenario, 1))
    if scenario == "oversize":
        frame += b"X" * 243
    try:
        handle = _winapi.CreateFile(pipe, 0xC0000000, 0, 0, 3,
                                   _winapi.FILE_FLAG_OVERLAPPED | 0x00100000, 0)
        _winapi.SetNamedPipeHandleState(handle, _winapi.PIPE_READMODE_MESSAGE, None, None)
        try:
            active, error = _winapi.WriteFile(handle, frame, overlapped=True)
            if complete(active, error) != len(frame):
                raise AssertionError("short synthetic write")
            active = None
            active, error = _winapi.ReadFile(handle, len(REPLY) + 1, overlapped=True)
            count = complete(active, error)
            reply = active.getbuffer()
            active = None
            if denied:
                if count != len(REPLY) or reply != REPLY:
                    raise AssertionError("fixed denial required")
            elif count != 0:
                raise AssertionError("refusal must not reply")
        except OSError as error:
            # Only remote pipe closure is a valid malformed-frame refusal.
            if denied or (getattr(error, "winerror", None) or error.errno) not in (109, 232, 233):
                raise
    finally:
        if active is not None:
            active.cancel()
            # Kernel cancellation must drain before buffer release. Parent kills
            # this disposable Python process if the kernel cleanup ever hangs.
            try:
                active.GetOverlappedResult(True)
            except OSError as error:
                if (getattr(error, "winerror", None) or error.errno) not in (109, 232, 233, 995):
                    raise
        if handle is not None:
            _winapi.CloseHandle(handle)
    print("DENIED" if denied else "REFUSED", flush=True)


@unittest.skipUnless(sys.platform == "win32", "Windows integration required")
class CrossLanguageTests(unittest.TestCase):
    def run_case(self, scenario):
        name = PREFIX + uuid.uuid4().hex
        endpoint(name)
        expected = "Idle" if scenario == "idle" else "Denied" if scenario in {
            "add", "replace", "delete"} else "Refused"
        deadline = time.monotonic() + 10
        children = []
        try:
            server = spawn([harness_path(), name, expected])
            children.append(server)
            output = Captured(server)
            self.assertEqual(output.lines.get(timeout=3), b"READY")
            if scenario != "idle":
                peer = spawn([sys.executable, "-B", "-m", __name__, "--client", name, scenario])
                children.append(peer)
                result = Captured(peer).finish(deadline)
                self.assertEqual(result, [b"UNTRUSTED_HOLD" if scenario == "add" else expected.upper().encode()])
                server.stdin.write(b"DONE\n")
                server.stdin.flush()
            result = output.finish(deadline)
            self.assertEqual(result, [b"READY", b"IDLE_DISPOSED" if scenario == "idle" else expected.upper().encode()])
        finally:
            cleanup_failed = False
            for process in reversed(children):
                try:
                    stop(process)
                except (OSError, subprocess.TimeoutExpired):
                    cleanup_failed = True
            if cleanup_failed:
                raise AssertionError("child cleanup incomplete")

    def test_real_p310_add_untrusted_hold(self): self.run_case("add")
    def test_typed_replace_denied(self): self.run_case("replace")
    def test_typed_delete_denied(self): self.run_case("delete")
    def test_malformed_magic_refused(self): self.run_case("magic")
    def test_zero_request_id_refused(self): self.run_case("zero")
    def test_invalid_operation_refused(self): self.run_case("operation")
    def test_oversized_message_refused(self): self.run_case("oversize")
    def test_quiet_accept_then_dispose(self): self.run_case("idle")


class BoundaryTests(unittest.TestCase):
    def test_endpoint_guard_before_native_access(self):
        for value in ("other", PREFIX + "0" * 32, PREFIX + "A" * 32,
                      "\\\\remote\\pipe\\" + PREFIX + uuid.uuid4().hex,
                      PIPE_PREFIX + uuid.uuid4().hex):
            with self.subTest(value=value), patch.dict(sys.modules, {"_winapi": object()}):
                with self.assertRaises(ValueError):
                    client(value, "add")

    def test_source_never_names_product_endpoint(self):
        forbidden = "NayeonV1" + "ByokCustody"
        for path in (Path(__file__), ROOT / "tests/p311_crosslanguage/P311CrossLanguageHarness.cs"):
            self.assertNotIn(forbidden, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--client":
        try:
            client(sys.argv[2], sys.argv[3])
        except Exception:
            sys.exit(1)
    else:
        unittest.main()
