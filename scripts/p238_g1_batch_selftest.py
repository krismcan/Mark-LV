"""P238 synthetic adversaries only. No original test import, discovery or Git."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "candidate", Path(__file__).with_name("p238_g1_immutable_batch_candidate.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class FakeProcess:
    def __init__(self, raw=b"", code=None):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(raw)
        self.returncode = code
        self.killed = False

    def poll(self):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = 125

    def wait(self, timeout):
        self.returncode = self.returncode or 0
        return self.returncode


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.path = "tests/synthetic.py"
        self.raw = b"synthetic bytes\r\n"
        self.oid = p.blob(self.raw)
        self.pin = p.sha(self.raw)
        self.header = f"{self.oid} blob {len(self.raw)}\n".encode()
        self.originals = {self.path: self.raw}
        patch = mock.patch.object(p, "MANIFEST", {self.path: (self.oid, self.pin)})
        patch.start()
        self.addCleanup(patch.stop)
        self.args = (["git", "show", p.B + ":" + self.path],)
        self.kwargs = dict(cwd=self.root, stderr=subprocess.DEVNULL, timeout=20)

    @staticmethod
    def digest(path, raw):
        return p.sha(raw)

    def verify(self, header=None, raw=None, delimiter=b"\n", **kwargs):
        return p.verify_frame(kwargs.get("path", self.path), self.header if header is None else header,
                              self.raw if raw is None else raw, delimiter,
                              kwargs.get("originals", self.originals), kwargs.get("digest", self.digest))

    def test_exact_intercept(self):
        self.assertEqual(p.intercept_path(self.args, self.kwargs, self.root), self.path)

    def test_mutable_and_unlisted_operations_delegate(self):
        commands = (["git", "show", "HEAD:" + self.path],
                    ["git", "show", p.B + ":unknown.py"],
                    ["git", "show", p.B.upper() + ":" + self.path],
                    ["git", "show", p.B + ":tests/../tests/synthetic.py"],
                    ["git", "show", p.B + ":" + self.path.upper()],
                    ["git", "show", p.B + ":" + self.path, "--"],
                    ["git", "status"], ["git", "branch", "--show-current"],
                    ["git", "cat-file", "-t", p.B],
                    ["git", "ls-files", "--stage", "-z"],
                    ["git", "show-ref", "--verify", "refs/tags/seal"],
                    ["git", "rev-parse", "HEAD"], ["git", "diff", "--cached"],
                    ["git", "cat-file", "--batch"], ["git.exe", "show", p.B + ":" + self.path])
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(p.intercept_path((command,), self.kwargs, self.root))

    def test_nonliteral_signature_delegates(self):
        changes = ({"cwd": self.root / "other"}, {"cwd": str(self.root)},
                   {"stderr": subprocess.PIPE}, {"timeout": 19}, {"timeout": 20.0},
                   {"env": {}}, {"shell": True}, {"text": True}, {"encoding": "utf8"})
        for change in changes:
            self.assertIsNone(p.intercept_path(self.args, dict(self.kwargs, **change), self.root))
        self.assertIsNone(p.intercept_path((tuple(self.args[0]),), self.kwargs, self.root))
        self.assertIsNone(p.intercept_path((), dict(self.kwargs, args=self.args[0]), self.root))
        self.assertIsNone(p.intercept_path(self.args, {"cwd": self.root}, self.root))

    def test_delegation_preserves_exact_args_bytes_and_nonzero(self):
        native = mock.Mock(return_value=b"native-negative-bytes")
        batch = mock.Mock()
        counts = dict(fresh_validated_reads=0, delegated_calls=0)
        limited = p.transport(self.root, batch, native, counts)
        args = (["git", "rev-parse", "HEAD"],)
        self.assertEqual(limited(*args, **self.kwargs), b"native-negative-bytes")
        native.assert_called_once_with(*args, **self.kwargs)
        error = subprocess.CalledProcessError(128, "SYNTHETIC", output=b"negative")
        native.side_effect = error
        with self.assertRaises(subprocess.CalledProcessError) as received:
            limited(*args, **self.kwargs)
        self.assertIs(received.exception, error)
        self.assertEqual(received.exception.returncode, 128)
        batch.get.assert_not_called()

    def test_byte_identity_positive(self):
        self.assertEqual(self.verify(), self.raw)

    def test_header_identity_type_size_and_delimiter_rejections(self):
        headers = (b"", b"not git\n", self.header.replace(self.oid.encode(), b"0" * 40),
                   self.header.replace(b" blob ", b" tree "),
                   f"{self.oid} blob 9999999\n".encode(),
                   f"{self.oid} blob 01\n".encode(), self.header[:-1], self.header + b"x")
        for header in headers:
            with self.subTest(header=header), self.assertRaises(RuntimeError):
                self.verify(header=header)
        for delimiter in (b"", b"x", b"\n\n"):
            with self.assertRaises(RuntimeError):
                self.verify(delimiter=delimiter)

    def test_wrong_bytes_and_truncation_rejected(self):
        for raw in (self.raw[:-1], self.raw + b"x", b"X" + self.raw[1:]):
            with self.assertRaises(RuntimeError):
                self.verify(raw=raw)

    def test_original_pin_independently_required(self):
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_NORMALIZED_PIN"):
            self.verify(digest=lambda path, raw: "0" * 64)

    def test_exact_original_show_bytes_independently_required(self):
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_SHOW_BYTES"):
            self.verify(originals={self.path: self.raw + b"x"})

    def test_path_and_fixed_oid_required(self):
        with self.assertRaisesRegex(RuntimeError, "PATH"):
            self.verify(path="outside")
        with mock.patch.dict(p.MANIFEST, {self.path: ("0" * 40, self.pin)}):
            with self.assertRaisesRegex(RuntimeError, "HEADER_IDENTITY"):
                self.verify()

    def test_short_pipe_chunks_accumulate_exactly(self):
        class Chunked(io.BytesIO):
            def read(self, size=-1):
                return super().read(min(size, 2))
        self.assertEqual(p.frame(Chunked(self.header + self.raw + b"\n")),
                         (self.header, self.raw, b"\n"))

    def test_partial_frame_and_cap_rejected(self):
        for raw in (self.header + self.raw[:-1], b"x" * 129,
                    f"{self.oid} blob {p.MAX_BLOB + 1}\n".encode()):
            with self.assertRaises(RuntimeError):
                p.frame(io.BytesIO(raw))

    def test_stale_ticket_and_failed_exchange_rejected(self):
        for received in ((1, ()), (3, ()), (2, None)):
            with self.assertRaisesRegex(RuntimeError, "STALE_OR_FAILED_EXCHANGE"):
                p.accept_reply(2, received)

    def test_repeated_identity_requires_fresh_pipe_read_each_time(self):
        fake = FakeProcess((self.header + self.raw + b"\n") * 2)
        with mock.patch.object(p.subprocess, "Popen", return_value=fake):
            batch = p.Batch(self.root, self.originals, self.digest)
        self.assertEqual(batch.get(self.path), self.raw)
        self.assertEqual(batch.get(self.path), self.raw)
        self.assertEqual(fake.stdin.getvalue(), ((self.oid + "\n") * 2).encode())
        self.assertEqual(batch.sequence, 2)
        batch.close()

    def test_positive_then_tamper_never_reuses_success(self):
        fake = FakeProcess(self.header + self.raw + b"\n" + self.header + b"X" + self.raw[1:] + b"\n")
        with mock.patch.object(p.subprocess, "Popen", return_value=fake):
            batch = p.Batch(self.root, self.originals, self.digest)
        batch.get(self.path)
        with self.assertRaisesRegex(RuntimeError, "BLOB_IDENTITY"):
            batch.get(self.path)
        with self.assertRaisesRegex(RuntimeError, "BATCH_STATE"):
            batch.get(self.path)
        with self.assertRaisesRegex(RuntimeError, "BATCH_CLEAN_EXIT"):
            batch.close()
        self.assertTrue(fake.killed)

    def test_replayed_other_object_rejected(self):
        other = b"other valid immutable blob"
        raw = f"{p.blob(other)} blob {len(other)}\n".encode() + other + b"\n"
        fake = FakeProcess(raw)
        with mock.patch.object(p.subprocess, "Popen", return_value=fake):
            batch = p.Batch(self.root, self.originals, self.digest)
        with self.assertRaisesRegex(RuntimeError, "HEADER_IDENTITY"):
            batch.get(self.path)
        with self.assertRaises(RuntimeError):
            batch.close()

    def test_read_timeout_poisoned_and_bounded(self):
        fake = FakeProcess(self.header + self.raw + b"\n")
        with mock.patch.object(p.subprocess, "Popen", return_value=fake):
            batch = p.Batch(self.root, self.originals, self.digest)
        with mock.patch.object(p.queue.Queue, "get", side_effect=queue.Empty) as get:
            with self.assertRaises(queue.Empty):
                batch.get(self.path)
            get.assert_called_once_with(timeout=20)
        with self.assertRaisesRegex(RuntimeError, "BATCH_STATE"):
            batch.get(self.path)
        with self.assertRaises(RuntimeError):
            batch.close()

    def test_nonzero_batch_exit_is_not_success(self):
        fake = FakeProcess(code=128)
        with mock.patch.object(p.subprocess, "Popen", return_value=fake):
            batch = p.Batch(self.root, self.originals, self.digest)
        with self.assertRaises(RuntimeError):
            batch.get(self.path)
        with self.assertRaises(RuntimeError):
            batch.close()

    def test_transport_counts_only_verified_return(self):
        batch = mock.Mock()
        counts = dict(fresh_validated_reads=0, delegated_calls=0)
        limited = p.transport(self.root, batch, mock.Mock(), counts)
        batch.get.return_value = self.raw
        self.assertEqual(limited(*self.args, **self.kwargs), self.raw)
        batch.get.side_effect = RuntimeError("tamper")
        with self.assertRaises(RuntimeError):
            limited(*self.args, **self.kwargs)
        self.assertEqual(counts["fresh_validated_reads"], 1)
        self.assertEqual(batch.get.call_count, 2)

    def test_read_count_cap(self):
        fake = FakeProcess()
        with mock.patch.object(p.subprocess, "Popen", return_value=fake):
            batch = p.Batch(self.root, self.originals, self.digest)
        batch.sequence = p.MAX_READS
        with self.assertRaisesRegex(RuntimeError, "BATCH_STATE"):
            batch.get(self.path)
        batch.close()

    def test_original_p234_classification_remains_held(self):
        original = p.load_original()  # stdlib controller only, never an original test
        process = dict(timed_out=False, tree_cleanup="JOB_EMPTY_CONFIRMED", aborted=False,
                       actual_process_exit=0)
        result = dict(assigned=[p.TEST], tests_run=1, original_unittest_exit=0,
                      failures=[], errors=[], skips=[], expected_failures=[], unexpected_successes=[])
        events = [dict(event=x, id=p.TEST) for x in ("start", "stop")]
        self.assertEqual(p.classify(process, result, events, original)[1], 3)
        result["failures"] = [p.TEST]
        result["original_unittest_exit"] = process["actual_process_exit"] = 1
        self.assertEqual(p.classify(process, result, events, original)[1], 1)
        process["timed_out"] = True
        self.assertEqual(p.classify(process, None, events[:1], original)[1], 124)
        process["tree_cleanup"] = "UNCERTAIN"
        summary, code = p.classify(process, None, events[:1], original)
        self.assertEqual((summary["status"], code), ("TIMEOUT", 125))

    def test_missing_result_and_skip_never_pass(self):
        original = p.load_original()
        process = dict(timed_out=False, tree_cleanup="JOB_EMPTY_CONFIRMED", aborted=False,
                       actual_process_exit=0)
        self.assertEqual(p.classify(process, None, [], original)[1], 125)
        result = dict(assigned=[p.TEST], tests_run=1, original_unittest_exit=0,
                      failures=[], errors=[], skips=[p.TEST], expected_failures=[], unexpected_successes=[])
        events = [dict(event=x, id=p.TEST) for x in ("start", "stop")]
        self.assertEqual(p.classify(process, result, events, original)[1], 125)

    def test_expected_failure_and_false_native_success_never_pass(self):
        original = p.load_original()
        process = dict(timed_out=False, tree_cleanup="JOB_EMPTY_CONFIRMED", aborted=False,
                       actual_process_exit=0)
        result = dict(assigned=[p.TEST], tests_run=1, original_unittest_exit=0,
                      failures=[], errors=[], skips=[], expected_failures=[p.TEST], unexpected_successes=[])
        events = [dict(event=x, id=p.TEST) for x in ("start", "stop")]
        self.assertEqual(p.classify(process, result, events, original)[1], 125)
        result["expected_failures"] = []
        result["failures"] = [p.TEST]
        result["original_unittest_exit"] = 1
        with self.assertRaises(RuntimeError):
            p.classify(process, result, events, original)

    def test_exact_parent_and_add_only_guard(self):
        rows = ["A\t" + x for x in p.ADDITIONS]
        p.check_delta([p.PARENT], rows)
        for parents, changed in (([], rows), ([p.PARENT, "0" * 40], rows),
                                 (["0" * 40], rows), ([p.PARENT], rows[:-1]),
                                 ([p.PARENT], rows + ["A\textra"]),
                                 ([p.PARENT], ["M\t" + p.ADDITIONS[0]] + rows[1:])):
            with self.assertRaises(RuntimeError):
                p.check_delta(parents, changed)

    def test_environment_scrubs_secrets_and_overrides(self):
        hostile = {"GIT_DIR": "private", "GIT_TRACE2_EVENT": "private", "CUSTOM_API_KEY": "secret",
                   "GH_TOKEN": "secret", "PYTHONPATH": "private", "P134_AUTH": "authority"}
        with mock.patch.dict(p.os.environ, hostile):
            env = p.environment()
            self.assertTrue(all(k not in env for k in hostile))
            self.assertEqual(p.os.environ["GH_TOKEN"], "secret")
            self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"], "1")

    def test_whole_child_deadline_and_cleanup_with_fake_job(self):
        with tempfile.TemporaryDirectory(prefix="p238-synthetic-") as folder:
            fake = FakeProcess()
            job = mock.Mock()
            job.active.side_effect = [1, 1, 0, 0]
            with mock.patch.object(p.subprocess, "Popen", return_value=fake), mock.patch.object(
                    p.time, "monotonic", side_effect=[0, 180, 181, 181, 182]):
                record = p.contained(self.root, Path(folder), job_factory=lambda: job)
            self.assertTrue(record["timed_out"])
            self.assertEqual(record["configured_whole_child_seconds"], 180)
            self.assertEqual(record["tree_cleanup"], "JOB_EMPTY_CONFIRMED")
            job.terminate.assert_called_once()
            job.assign.assert_called_once_with(fake)

    def test_assignment_failure_never_sends_handshake(self):
        with tempfile.TemporaryDirectory(prefix="p238-synthetic-") as folder:
            fake = FakeProcess()
            job = mock.Mock()
            job.assign.side_effect = RuntimeError("assignment")
            job.active.return_value = 0
            with mock.patch.object(p.subprocess, "Popen", return_value=fake):
                record = p.contained(self.root, Path(folder), job_factory=lambda: job)
            self.assertEqual(fake.stdin.getvalue(), b"")
            self.assertTrue(fake.killed)
            self.assertTrue(record["aborted"])

    def test_cleanup_query_failure_is_uncertain(self):
        with tempfile.TemporaryDirectory(prefix="p238-synthetic-") as folder:
            fake = FakeProcess()
            job = mock.Mock()
            job.active.side_effect = RuntimeError("query")
            with mock.patch.object(p.subprocess, "Popen", return_value=fake):
                record = p.contained(self.root, Path(folder), job_factory=lambda: job)
            self.assertEqual(record["tree_cleanup"], "UNCERTAIN")
            self.assertTrue(fake.killed)

    def test_job_termination_failure_and_close_failure_stay_uncertain(self):
        for failure in ("terminate", "close"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory(prefix="p238-synthetic-") as folder:
                fake = FakeProcess(code=0)
                job = mock.Mock()
                job.active.side_effect = [1, 1, 0, 0]
                getattr(job, failure).side_effect = RuntimeError("synthetic")
                with mock.patch.object(p.subprocess, "Popen", return_value=fake):
                    record = p.contained(self.root, Path(folder), job_factory=lambda: job)
                self.assertEqual(record["tree_cleanup"], "UNCERTAIN")

    def test_output_cap_abort_is_not_timeout_or_pass(self):
        with tempfile.TemporaryDirectory(prefix="p238-synthetic-") as folder:
            fake = FakeProcess()
            job = mock.Mock()
            job.active.side_effect = [1, 1, 0, 0]
            with mock.patch.object(p.subprocess, "Popen", return_value=fake), mock.patch.object(p, "MAX_LOG", -1):
                record = p.contained(self.root, Path(folder), job_factory=lambda: job)
            self.assertTrue(record["aborted"])
            self.assertFalse(record["timed_out"])
            summary, code = p.classify(record, None, [], p.load_original())
            self.assertEqual((summary["status"], code), ("INSTRUMENTATION_ERROR", 125))

    def test_budget_change_refused(self):
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_BUDGET"):
            p.contained(self.root, self.root, seconds=181)

    def test_clean_root_exit_with_residual_child_refuses_candidate_pass(self):
        with tempfile.TemporaryDirectory(prefix="p238-synthetic-") as folder:
            fake = FakeProcess(code=0)
            job = mock.Mock()
            job.active.side_effect = [1, 1, 0, 0]
            with mock.patch.object(p.subprocess, "Popen", return_value=fake):
                record = p.contained(self.root, Path(folder), job_factory=lambda: job)
            self.assertFalse(record["timed_out"])
            self.assertEqual(record["tree_cleanup"], "JOB_EMPTY_CONFIRMED")
            self.assertTrue(record["residual_descendants_after_root_exit"])
            result = dict(assigned=[p.TEST], tests_run=1, original_unittest_exit=0,
                          failures=[], errors=[], skips=[], expected_failures=[], unexpected_successes=[])
            events = [dict(event=x, id=p.TEST) for x in ("start", "stop")]
            summary, code = p.classify(record, result, events, p.load_original())
            self.assertEqual((summary["status"], code), ("INSTRUMENTATION_ERROR", 125))
            job.terminate.assert_called_once()

    def test_windows_job_contains_descendant_after_parent_exit(self):
        if sys.platform != "win32":
            with self.assertRaisesRegex(RuntimeError, "WINDOWS_JOB_REQUIRED"):
                p.Job()
            return
        # Tiny synthetic child only. Parent waits for assignment before spawning
        # one stdlib sleeper; no historical Git, admission or expensive G1.
        code = ("import sys,subprocess;sys.stdin.buffer.read(1);"
                "subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(30)'],"
                "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)")
        job = p.Job()
        proc = subprocess.Popen([sys.executable, "-B", "-c", code], stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=p.environment())
        try:
            job.assign(proc)
            self.assertEqual(job.active(), 1)
            proc.stdin.write(b"!")
            proc.stdin.close()
            proc.wait(timeout=5)
            self.assertEqual(job.active(), 1)
            job.terminate()
            deadline = time.monotonic() + 5
            while job.active() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(job.active(), 0)
        finally:
            job.close()
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CandidateTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    good = result.wasSuccessful() and not result.skipped
    if args.report:
        p.write(args.report, {"scope": "SYNTHETIC ONLY", "run": result.testsRun,
                            "failures": len(result.failures), "errors": len(result.errors),
                            "skips": len(result.skipped), "pass": good, "release": "HOLD"})
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
