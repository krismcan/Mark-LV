"""Synthetic P237 adversaries only; never imports or executes an original test."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "observer", Path(__file__).with_name("p237_g1_git_timing_observer.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def trace(op="show", sid="synthetic-session", code=0):
    return [dict(event=event, sid=sid, **fields) for event, fields in (
        ("version", {}), ("start", {"argv": ["git", "PRIVATE-ARGUMENT"]}),
        ("cmd_name", {"name": op}), ("exit", {"t_abs": .25, "code": code}),
        ("atexit", {"t_abs": .26, "code": code}))]


class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="p237-selftest-",
                                               dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def save_trace(self, rows=None, name="synthetic"):
        path = self.root / name
        path.write_text("".join(json.dumps(e) + "\n" for e in (trace() if rows is None else rows)),
                        encoding="utf8")
        return path

    def test_valid_aggregate_does_not_export_arguments_paths_sid(self):
        self.save_trace()
        result = p.trace_summary(self.root)
        self.assertEqual(result["operations"]["show"]["git_seconds_sum"], .25)
        self.assertEqual(result["operations"]["show"]["completed"], 1)
        self.assertEqual(len(result["raw_trace_sha256_multiset"]), 1)
        for forbidden in ("PRIVATE-ARGUMENT", "synthetic-session", str(self.root), "argv"):
            self.assertNotIn(forbidden, json.dumps(result))

    def test_nonzero_git_exit_is_observed_not_rewritten(self):
        self.save_trace(trace(code=128))
        self.assertEqual(p.trace_summary(self.root)["operations"]["show"]["nonzero"], 1)

    def test_untrusted_operation_cannot_escape_aggregate(self):
        self.save_trace(trace(op="SECRET/PATH"))
        result = p.trace_summary(self.root)
        self.assertEqual(set(result["operations"]), {"OTHER"})
        self.assertNotIn("SECRET", json.dumps(result))

    def test_missing_trace_is_not_pass(self):
        with self.assertRaisesRegex(RuntimeError, "MISSING_TRACE"):
            p.trace_summary(self.root)

    def test_discard_sentinel_is_not_partial_success(self):
        self.save_trace(name="git-trace2-discard")
        with self.assertRaisesRegex(RuntimeError, "TRACE_DISCARDED"):
            p.trace_summary(self.root, allow_incomplete=True)

    def test_malformed_truncated_and_empty_trace_refused(self):
        for raw in (b"", b"{}", b"not json\n", b"{}\n"):
            with self.subTest(raw=raw):
                (self.root / "synthetic").write_bytes(raw)
                with self.assertRaises((RuntimeError, ValueError)):
                    p.trace_summary(self.root, allow_incomplete=True)

    def test_mixed_or_repeated_session_refused(self):
        rows = trace()
        rows[-1]["sid"] = "foreign"
        self.save_trace(rows)
        with self.assertRaisesRegex(RuntimeError, "MIXED_TRACE_SESSION"):
            p.trace_summary(self.root)
        self.save_trace()
        self.save_trace(name="second")
        with self.assertRaisesRegex(RuntimeError, "TRACE_LIFECYCLE"):
            p.trace_summary(self.root)

    def test_duplicate_lifecycle_refused(self):
        for index in (0, 1, 2, 3, 4):
            rows = trace()
            rows.insert(index, rows[index])
            self.save_trace(rows)
            with self.subTest(index=index), self.assertRaises(RuntimeError):
                p.trace_summary(self.root)

    def test_missing_start_or_version_refused_even_at_timeout(self):
        for index in (0, 1):
            rows = trace()
            del rows[index]
            self.save_trace(rows)
            with self.subTest(index=index), self.assertRaises(RuntimeError):
                p.trace_summary(self.root, allow_incomplete=True)

    def test_incomplete_only_allowed_for_original_timeout(self):
        self.save_trace(trace()[:-2])
        with self.assertRaisesRegex(RuntimeError, "TRACE_INCOMPLETE"):
            p.trace_summary(self.root)
        result = p.trace_summary(self.root, allow_incomplete=True)
        self.assertEqual(result["incomplete"], 1)
        self.assertEqual(result["operations"]["show"]["completed"], 0)

    def test_invalid_duration_types_ranges_and_nan_refused(self):
        for value in (True, -1, float("nan"), float("inf"), "0.2", 3601):
            rows = trace()
            rows[-2]["t_abs"] = value
            self.save_trace(rows)
            with self.subTest(value=value), self.assertRaisesRegex(RuntimeError, "TRACE_DURATION"):
                p.trace_summary(self.root)

    def test_exit_mismatch_and_reverse_time_refused(self):
        for field, value in (("code", 1), ("t_abs", .1)):
            rows = trace()
            rows[-1][field] = value
            self.save_trace(rows)
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, "TRACE_EXIT_MISMATCH"):
                p.trace_summary(self.root)

    def test_reordered_lifecycle_refused(self):
        for order in ((1, 0, 2, 3, 4), (0, 3, 1, 2, 4), (0, 1, 2, 4, 3)):
            rows = trace()
            self.save_trace([rows[index] for index in order])
            with self.subTest(order=order), self.assertRaises(RuntimeError):
                p.trace_summary(self.root)

    def test_file_byte_line_event_caps_refuse(self):
        self.save_trace()
        for key, value in (("MAX_FILES", 0), ("MAX_BYTES", 1), ("MAX_FILE", 1),
                           ("MAX_LINE", 1), ("MAX_EVENTS", 1)):
            with self.subTest(key=key), mock.patch.object(p, key, value), self.assertRaises(RuntimeError):
                p.trace_summary(self.root)

    def test_nested_directory_refused(self):
        (self.root / "nested").mkdir()
        with self.assertRaisesRegex(RuntimeError, "NONREGULAR_FILE"):
            p.inventory(self.root)

    def test_symlink_or_reparse_refused_without_following(self):
        info = argparse.Namespace(st_mode=0o100644, st_size=1, st_file_attributes=0x400)
        path = mock.Mock()
        path.lstat.return_value = info
        path.is_symlink.return_value = False
        with self.assertRaisesRegex(RuntimeError, "NONREGULAR_FILE"):
            p.regular(path)

    def test_exact_delta_and_parent(self):
        rows = ["A\t" + path for path in p.ADDITIONS]
        p.check_delta([p.PARENT], rows)
        cases = [([], rows), ([p.PARENT, p.PARENT], rows), (["forged"], rows),
                 ([p.PARENT], rows[:-1]), ([p.PARENT], rows + ["A\textra"]),
                 ([p.PARENT], ["M" + rows[0][1:]] + rows[1:]),
                 ([p.PARENT], rows[:-1] + rows[:1])]
        for parents, changed in cases:
            with self.subTest(parents=parents, changed=changed), self.assertRaises(RuntimeError):
                p.check_delta(parents, changed)

    def test_environment_is_disposable_and_drops_injection_and_secrets(self):
        original = {"GIT_TRACE2_EVENT": "elsewhere", "GIT_CONFIG_COUNT": "1", "P134_FAKE": "x",
                    "GITHUB_TOKEN": "secret", "OPENAI_API_KEY": "secret", "PYTHONPATH": "bad",
                    "ACTIONS_RUNTIME_TOKEN": "secret", "GITHUB_ACTIONS": "true", "PATH": "safe"}
        with mock.patch.dict(os.environ, original, clear=True):
            env = p.clean_env(self.root)
            self.assertEqual(dict(os.environ), original)
        for key in ("GIT_CONFIG_COUNT", "P134_FAKE", "GITHUB_TOKEN", "OPENAI_API_KEY", "PYTHONPATH",
                    "ACTIONS_RUNTIME_TOKEN"):
            self.assertNotIn(key, env)
        self.assertEqual(env["GIT_TRACE2_EVENT"], self.root.as_posix())
        self.assertEqual(env["GITHUB_ACTIONS"], "true")

    def test_trace_destination_must_exist_and_be_absolute(self):
        for path in (Path("relative"), self.root / "missing"):
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, "TRACE_TARGET"):
                p.clean_env(path)

    def test_held_release_never_returns_zero(self):
        for status in ("PASS", "FAIL_OR_ERROR", "TIMEOUT", "INCOMPLETE", "SKIP", "EXPECTED_FAILURE"):
            self.assertNotEqual(p.finish_code(status), 0)
        self.assertEqual(p.finish_code("PASS"), 3)
        for code in (1, 124, 125):
            self.assertEqual(p.finish_code("TIMEOUT", code), code)

    def test_real_tiny_synthetic_child_native_exit_and_stderr_hash(self):
        command = [sys.executable, "-B", "-c",
                   "import sys; print('synthetic stdout'); print('synthetic stderr',file=sys.stderr); sys.exit(1)"]
        result = p.original_process(command, self.root, self.root)
        self.assertEqual(result["actual_process_exit"], 1)
        self.assertEqual(result["diagnostic_exit"], 1)
        self.assertFalse(result["timed_out"])
        self.assertEqual(result["configured_wait_seconds"], 180)
        self.assertEqual(result["raw_log_sha256"], p.sha((self.root / "single-0.log").read_bytes()))
        self.assertIn(b"synthetic stderr", (self.root / "single-0.log").read_bytes())
        self.assertGreaterEqual(result["whole_child_seconds"], result["spawn_seconds"])

    def test_timeout_uses_exact_180_and_preserves_uncertain(self):
        proc = mock.Mock(returncode=1)
        proc.wait.side_effect = subprocess.TimeoutExpired("synthetic", 180)
        with mock.patch.object(p.subprocess, "Popen", return_value=proc), \
                mock.patch.object(p, "cleanup", return_value="UNCERTAIN"):
            result = p.original_process(["synthetic"], self.root, self.root)
        proc.wait.assert_called_once_with(timeout=180)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["tree_cleanup"], "UNCERTAIN")
        self.assertEqual(result["diagnostic_exit"], 124)

    def test_taskkill_failure_exception_or_exited_root_never_success(self):
        for reply in (argparse.Namespace(returncode=1), OSError("synthetic"),
                      subprocess.TimeoutExpired("synthetic", 30)):
            proc = mock.Mock(pid=1234)
            proc.poll.side_effect = [None, 1]
            kwargs = {"side_effect": reply} if isinstance(reply, Exception) else {"return_value": reply}
            with mock.patch.object(p.sys, "platform", "win32"), \
                    mock.patch.object(p.subprocess, "run", **kwargs) as run:
                state = p.cleanup(proc, mock.Mock())
            self.assertEqual(state, "UNCERTAIN")
            self.assertEqual(run.call_args.args[0], ["taskkill", "/PID", "1234", "/T", "/F"])
        proc = mock.Mock()
        proc.poll.return_value = 0
        with mock.patch.object(p.subprocess, "run") as run:
            self.assertEqual(p.cleanup(proc, mock.Mock()), "UNCERTAIN")
        run.assert_not_called()

    def test_supervisor_resource_failure_stops_only_its_root(self):
        proc = mock.Mock(returncode=1)
        proc.poll.return_value = None
        trace_dir = self.root / "trace"
        trace_dir.mkdir()
        folder = self.root / "runner"
        folder.mkdir()
        with mock.patch.object(p.subprocess, "Popen", return_value=proc), \
                mock.patch.object(p, "inventory", side_effect=RuntimeError("BYTE_LIMIT")), \
                mock.patch.object(p, "cleanup", return_value="UNCERTAIN") as cleanup:
            result = p.supervised("single", self.root, folder, trace_dir, 270)
        self.assertEqual(result["runner_cleanup"], "UNCERTAIN")
        self.assertIsNotNone(result["aborted"])
        self.assertIs(cleanup.call_args.args[0], proc)

    def test_final_root_cleanup_failure_preserves_uncertain_even_after_taskkill_zero(self):
        for failing in ("kill", "wait"):
            proc = mock.Mock(pid=1234)
            proc.poll.return_value = None
            getattr(proc, failing).side_effect = OSError("synthetic final cleanup failure")
            with mock.patch.object(p.sys, "platform", "win32"), \
                    mock.patch.object(p.subprocess, "run", return_value=argparse.Namespace(returncode=0)):
                self.assertEqual(p.cleanup(proc, mock.Mock()), "UNCERTAIN")

    def test_log_cap_preserves_native_exit_and_marks_missing_hash(self):
        proc = mock.Mock(returncode=1)
        with mock.patch.object(p.subprocess, "Popen", return_value=proc), \
                mock.patch.object(p, "read", side_effect=RuntimeError("FILE_LIMIT")):
            result = p.original_process(["synthetic"], self.root, self.root)
        self.assertEqual(result["actual_process_exit"], 1)
        self.assertTrue(result["log_receipt_error"])
        self.assertIsNone(result["raw_log_sha256"])

    def test_original_classifier_keeps_fail_timeout_missing_and_foreign_events(self):
        original = p.load_p234()
        result = {"assigned": [p.TEST], "tests_run": 1, "original_unittest_exit": 1,
                  "failures": [p.TEST], "errors": [], "skips": [],
                  "expected_failures": [], "unexpected_successes": []}
        events = [{"event": e, "id": p.TEST} for e in ("start", "stop")]
        process = {"timed_out": False, "actual_process_exit": 1, "tree_cleanup": "NOT_NEEDED"}
        summary, code = original.classify(process, result, events, p.TEST)
        self.assertEqual((summary["status"], code), ("FAIL_OR_ERROR", 1))
        process.update(timed_out=True, tree_cleanup="UNCERTAIN")
        self.assertEqual(original.classify(process, None, events[:1], p.TEST)[1], 125)
        process["tree_cleanup"] = "TREE_TERMINATED"
        self.assertEqual(original.classify(process, None, events[:1], p.TEST)[1], 124)
        process["timed_out"] = False
        self.assertEqual(original.classify(process, None, [], p.TEST)[1], 125)
        with self.assertRaises(RuntimeError):
            original.classify(process, result, [{"event": "start", "id": "foreign"}], p.TEST)

    def observation(self, status="PASS", break_at=None):
        source = self.root / "source"
        source.mkdir()
        output = self.root / "public"
        witness = {"head": p.SOURCE, "raw_tracked_sha256": {"public.py": "A" * 64}}
        launched = []

        def synthetic(phase, src, folder, trace_dir, budget):
            launched.append(phase)
            if phase == break_at:
                return {"runner_native_exit": 125, "aborted": None}
            if phase == "verify":
                p.write(folder / "source-witness.json", witness)
                p.write(folder / "worker.json", {"source_witness_raw_sha256": p.sha(p.canonical(witness)),
                                                "verification_seconds": .1})
            elif phase == "probe":
                p.write(folder / "worker.json", {"native_exit": 0})
                (trace_dir / "probe").write_text("".join(json.dumps(e) + "\n" for e in trace("version")))
            else:
                timed_out = status == "TIMEOUT"
                original_exit = 1 if status == "FAIL" else 0
                p.write(folder / "worker.json", {"timed_out": timed_out,
                        "actual_process_exit": original_exit,
                        "tree_cleanup": "UNCERTAIN" if timed_out else "NOT_NEEDED"})
                tid = p.TEST
                events = [{"event": e, "id": tid} for e in (("start",) if timed_out else ("start", "stop"))]
                (folder / "single-0.events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
                if not timed_out:
                    p.write(folder / "single-0.json", {"assigned": [tid], "tests_run": 1,
                            "original_unittest_exit": original_exit,
                            "failures": [tid] if original_exit else [], "errors": [], "skips": [],
                            "expected_failures": [], "unexpected_successes": []})
                for index in range(2):
                    rows = trace(sid="synthetic-" + str(index))
                    (trace_dir / str(index)).write_text("".join(json.dumps(e) + "\n" for e in rows))
            return {"runner_native_exit": 0, "aborted": None}

        original_controller = p.load_p234()
        with mock.patch.object(p, "__file__", str(self.root / "controller/scripts/observer.py")), \
                mock.patch.object(p, "load_p234", return_value=original_controller), \
                mock.patch.object(p, "controller_provenance", return_value={"parent": p.PARENT}), \
                mock.patch.object(p, "supervised", side_effect=synthetic), \
                mock.patch.dict(os.environ, {"RUNNER_TEMP": str(self.root)}):
            code = p.observe(argparse.Namespace(source=source, output=output))
        return code, json.loads((output / "observation.json").read_bytes()), launched, output

    def test_synthetic_end_to_end_pass_stays_held_with_receipts(self):
        code, report, launched, output = self.observation()
        self.assertEqual(code, 3)
        self.assertEqual(report["original"]["status"], "PASS")
        self.assertEqual(report["release"], "HOLD")
        self.assertEqual(launched, ["verify", "probe", "single", "verify"])
        receipts = json.loads((output / "receipts.json").read_bytes())
        self.assertEqual(receipts["observation.json"], p.sha((output / "observation.json").read_bytes()))
        self.assertEqual(set(path.name for path in output.iterdir()),
                         {"observation.json", "receipts.json", "source-witness.json"})

    def test_synthetic_end_to_end_original_fail_is_not_zero(self):
        code, report, _, _ = self.observation(status="FAIL")
        self.assertEqual(code, 1)
        self.assertEqual(report["original"]["status"], "FAIL_OR_ERROR")

    def test_synthetic_end_to_end_uncertain_timeout_retained(self):
        code, report, launched, _ = self.observation(status="TIMEOUT")
        self.assertEqual(code, 125)
        self.assertEqual(report["single"]["tree_cleanup"], "UNCERTAIN")
        self.assertEqual(report["original"]["status"], "TIMEOUT")
        self.assertEqual(launched.count("single"), 1)

    def test_synthetic_preflight_failure_prevents_probe_and_original(self):
        code, report, launched, _ = self.observation(break_at="verify")
        self.assertEqual(code, 125)
        self.assertEqual(launched, ["verify"])
        self.assertEqual(report["stage"], "VERIFY")

    def test_synthetic_probe_failure_prevents_original(self):
        code, _, launched, _ = self.observation(break_at="probe")
        self.assertEqual(code, 125)
        self.assertEqual(launched, ["verify", "probe"])

    def test_unhosted_controller_is_refused_before_git(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}), \
                mock.patch.object(p, "git") as git:
            with self.assertRaisesRegex(RuntimeError, "HOST_IDENTITY"):
                p.controller_provenance(self.root)
        git.assert_not_called()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ObserverTests))
    successful = (result.wasSuccessful() and result.testsRun == 33
                  and not result.skipped and not result.expectedFailures)
    if args.report:
        p.write(args.report, {"scope": "SYNTHETIC ONLY", "tests_run": result.testsRun,
                             "failed_ids": [t.id() for t, _ in result.failures],
                             "error_ids": [t.id() for t, _ in result.errors],
                             "skipped_ids": [t.id() for t, _ in result.skipped],
                             "native_exit": 0 if successful else 1})
    raise SystemExit(0 if successful else 1)
