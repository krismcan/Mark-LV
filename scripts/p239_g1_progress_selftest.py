"""Synthetic P239 adversaries; no original G1, source discovery or credentials.

Requires exact raw LF P238 helper bytes, even for synthetic execution. No source
guard override. The inherited 33 P238 synthetic tests run in this suite too.
"""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


p = load("p239_observer", "p239_g1_progress_observer.py")
h = p.load_helpers()  # exact raw pin, no normalization/fallback
old = load("p239_inherited_synthetic", "p238_g1_batch_selftest.py")
RUN = "1" * 32


def event(seq, stage, seconds=None, **counts):
    return dict(p.zeros(), schema=239, binding=p.binding(RUN), seq=seq,
                stage=stage, seconds=seq if seconds is None else seconds, **counts)


def encode(events, trailing=b""):
    return b"".join(json.dumps(e).encode("ascii") + b"\n" for e in events) + trailing


def preflight():
    return [event(i + 1, stage) for i, stage in enumerate(p.STAGES[:5])]


def completed():
    rows = preflight()
    for i in range(1, 24):
        rows.append(event(len(rows) + 1, "running", validated_reads=i * 32,
                          subtests_completed=i))
    for stage in ("test_finished", "postflight_complete"):
        rows.append(event(len(rows) + 1, stage, validated_reads=23 * 32,
                          subtests_completed=23))
    return rows


class ProgressTests(unittest.TestCase):
    def parse(self, rows, trailing=b""):
        return p.parse_progress(encode(rows, trailing), RUN)

    def rejected(self, rows, reason=None):
        report = self.parse(rows)
        self.assertFalse(report["records_valid"])
        self.assertFalse(report["observation_complete"])
        if reason:
            self.assertEqual(report["reason"], reason)
        return report

    def test_valid_prefix_is_observation_only(self):
        report = self.parse(preflight())
        self.assertTrue(report["records_valid"])
        self.assertFalse(report["observation_complete"])
        self.assertEqual(report["latest_stage"], "test_begun")
        self.assertEqual(report["stage_first_seconds"]["source_verified"], 2)
        self.assertEqual(report["stage_first_seconds"]["test_begun"], 5)
        self.assertIsNone(report["stage_first_seconds"]["test_finished"])
        self.assertNotIn("duration", report)
        self.assertNotIn("pass", report)
        self.assertNotIn("status", report)

    def test_complete_observation_not_test_success(self):
        report = self.parse(completed())
        self.assertTrue(report["observation_complete"])
        self.assertEqual(report["safe_counts"]["subtests_completed"], 23)
        self.assertNotIn("pass", report)
        self.assertEqual(p.evidence_exit(1, report, True), 1)
        self.assertEqual(p.evidence_exit(124, report, True), 124)

    def test_missing_empty_and_newline_only(self):
        self.assertEqual(p.parse_progress(b"", RUN)["reason"], "MISSING")
        report = p.parse_progress(b"\n", RUN)
        self.assertFalse(report["records_valid"])
        self.assertEqual(report["accepted_events"], 0)

    def test_torn_tail_preserves_only_safe_prefix_and_raw_hash(self):
        raw = encode(preflight(), b'{"seq":6')
        report = p.parse_progress(raw, RUN)
        self.assertEqual(report["reason"], "TORN_TRAILING_LINE")
        self.assertEqual(report["raw_sha256"], p.sha(raw))
        self.assertEqual(report["accepted_events"], 5)
        self.assertEqual(report["latest_sample_seconds"], 5)
        self.assertFalse(report["records_valid"])

    def test_even_valid_json_without_newline_is_torn(self):
        raw = encode(completed())[:-1]
        report = p.parse_progress(raw, RUN)
        self.assertFalse(report["observation_complete"])
        self.assertEqual(report["latest_stage"], "test_finished")
        self.assertEqual(report["reason"], "TORN_TRAILING_LINE")
        self.assertIsNone(report["stage_first_seconds"]["postflight_complete"])

    def test_torn_first_line_establishes_no_counts(self):
        report = p.parse_progress(b'{"schema":239', RUN)
        self.assertEqual(report["safe_counts"], p.zeros())
        self.assertIsNone(report["latest_stage"])

    def test_invalid_complete_line_stops_before_later_pass(self):
        raw = encode(preflight()) + b'broken\n' + encode(completed()[5:])
        report = p.parse_progress(raw, RUN)
        self.assertEqual(report["accepted_events"], 5)
        self.assertEqual(report["reason"], "INVALID_JSON")
        self.assertFalse(report["observation_complete"])

    def test_double_missing_or_reordered_events(self):
        rows = preflight()
        for changed in (rows + [rows[-1]], rows[1:], rows[:2] + rows[3:],
                        rows[:1] + [rows[2], rows[1]] + rows[3:]):
            with self.subTest(case=len(changed)):
                self.rejected(changed)

    def test_duplicate_keys_and_foreign_fields(self):
        line = json.dumps(event(1, "child_started"))[:-1] + ',"seq":1}\n'
        self.assertEqual(p.parse_progress(line.encode(), RUN)["reason"], "DUPLICATE_KEY")
        for key in ("path", "argv", "pid", "secret", "success"):
            row = event(1, "child_started")
            row[key] = "synthetic"
            self.rejected([row], "EVENT_SCHEMA")

    def test_foreign_run_schema_and_source_bound_receipt(self):
        rows = completed()
        report = p.parse_progress(encode(rows), "2" * 32)
        self.assertEqual(report["reason"], "FOREIGN_EVENT")
        for value in (238, True, "239"):
            row = event(1, "child_started")
            row["schema"] = value
            self.rejected([row], "FOREIGN_EVENT")
        with mock.patch.object(p, "SOURCE", "0" * 40):
            self.assertNotEqual(p.binding(RUN), rows[0]["binding"])

    def test_nonmonotonic_and_nonfinite_seconds(self):
        for seconds in (-1, 181, 10 ** 1000, float("nan"), float("inf"), True, "1", None):
            row = event(1, "child_started")
            row["seconds"] = seconds
            self.rejected([row], "EVENT_CLOCK")
        rows = preflight()
        rows[-1]["seconds"] = 1
        self.rejected(rows, "CLOCK_REGRESSION")

    def test_nonmonotonic_counts_and_bad_relations(self):
        rows = completed()
        for key, value in (("validated_reads", 0), ("subtests_completed", 0),
                           ("subtests_failed", 2), ("delegated_completed", 1),
                           ("subtests_completed", 24), ("validated_reads", 4097)):
            changed = [dict(r) for r in rows]
            changed[6][key] = value
            self.rejected(changed)
        for value in (-1, True, 1.5, p.MAX_COUNTER + 1):
            self.rejected(preflight() + [event(6, "running", validated_reads=value)])

    def test_started_completed_and_category_totals(self):
        row = event(6, "running", delegated_started=32, delegated_completed=32,
                    delegated_show_completed=16, delegated_other_completed=16)
        self.assertTrue(self.parse(preflight() + [row])["records_valid"])
        row["delegated_started"] = 31
        self.rejected(preflight() + [row], "COUNTER_RELATION")

    def test_no_stage_skipping_repetition_or_samples_after_finish(self):
        for rows in ([event(1, "test_begun")], preflight()[:2] + [event(3, "test_begun")],
                     preflight() + [event(6, "test_begun")],
                     completed() + [event(31, "running", subtests_completed=23)],
                     preflight() + [event(6, "running")]):
            self.rejected(rows)

    def test_no_fake_subtest_jump_or_premature_read_counts(self):
        self.rejected(preflight() + [event(6, "running", subtests_completed=2)], "SUBTEST_SEQUENCE")
        rows = completed()
        rows[7].update(subtests_completed=2, subtests_failed=1)
        self.rejected(rows, "SUBTEST_SEQUENCE")
        rows = preflight()
        rows[2]["validated_reads"] = 1
        self.rejected(rows, "PREMATURE_COUNTS")

    def test_byte_line_and_event_caps(self):
        report = p.parse_progress(b"x" * (p.MAX_PROGRESS + 1), RUN)
        self.assertEqual(report["reason"], "BYTE_CAP")
        report = p.parse_progress(b"x" * (p.MAX_LINE + 1) + b"\n", RUN)
        self.assertEqual(report["reason"], "LINE_CAP")
        with mock.patch.object(p, "MAX_EVENTS", 4):
            report = self.parse(preflight())
        self.assertEqual(report["reason"], "EVENT_CAP")
        self.assertEqual(report["accepted_events"], 4)

    def test_progress_append_only_flush_and_caps(self):
        with tempfile.TemporaryDirectory(prefix="p239-synthetic-") as folder:
            path = Path(folder) / "progress.jsonl"
            with mock.patch.object(p.time, "monotonic", return_value=1):
                witness = p.Progress(path, RUN, 0)
                witness.emit("child_started")
                first = path.read_bytes()  # externally visible while writer is open
                witness.emit("source_verified")
                self.assertTrue(path.read_bytes().startswith(first))
                self.assertEqual(len(path.read_bytes().splitlines()), 2)
                with mock.patch.object(p, "MAX_EVENTS", 2), self.assertRaises(RuntimeError):
                    witness.emit("baseline_verified")
                witness.close()
            with self.assertRaises(FileExistsError):
                p.Progress(path, RUN, 0)

    def test_validated_reads_only_and_no_log_per_git_call(self):
        observer = mock.Mock()
        observer.counts, observer.reads_by_path = p.zeros(), {}
        batch, native = mock.Mock(), mock.Mock(return_value=b"native")
        limited = p.transport(h, Path("synthetic"), batch, native, observer)
        path = next(iter(h.MANIFEST))
        args = (["git", "show", h.B + ":" + path],)
        kwargs = dict(cwd=Path("synthetic"), stderr=subprocess.DEVNULL, timeout=20)
        batch.get.return_value = b"validated synthetic seam"
        self.assertEqual(limited(*args, **kwargs), batch.get.return_value)
        self.assertEqual(observer.counts["validated_reads"], 1)
        batch.get.side_effect = RuntimeError("SYNTHETIC_CORRUPT_FRAME")
        with self.assertRaises(RuntimeError):
            limited(*args, **kwargs)
        self.assertEqual(observer.counts["validated_reads"], 1)
        native.assert_not_called()
        observer.sample.assert_called_once_with("validated_reads")

    def test_exact_native_errors_args_and_completed_attempt_counts(self):
        observer = mock.Mock()
        observer.counts = p.zeros()
        error = subprocess.CalledProcessError(128, "synthetic", output=b"negative")
        native = mock.Mock(side_effect=error)
        limited = p.transport(h, Path("synthetic"), mock.Mock(), native, observer)
        args, kwargs = (["git", "cat-file", "-t", "synthetic"],), {"timeout": 20}
        with self.assertRaises(subprocess.CalledProcessError) as got:
            limited(*args, **kwargs)
        self.assertIs(got.exception, error)
        native.assert_called_once_with(*args, **kwargs)
        self.assertEqual(observer.counts["delegated_started"], 1)
        self.assertEqual(observer.counts["delegated_completed"], 1)
        self.assertEqual(observer.counts["delegated_cat_file_completed"], 1)

    def test_sampling_only_every_32_completions(self):
        observer = object.__new__(p.Progress)
        observer.counts, observer.active = p.zeros(), True
        observer.emit = mock.Mock()
        for count in range(1, 65):
            observer.counts["validated_reads"] = count
            observer.sample("validated_reads")
        self.assertEqual(observer.emit.call_count, 2)
        self.assertEqual(p.SAMPLE, 32)

    def test_failed_subtests_count_after_super_and_skips_do_not_count(self):
        original = h.load_original()
        with tempfile.TemporaryDirectory(prefix="p239-synthetic-") as folder:
            observer = p.Progress(Path(folder) / "progress.jsonl", RUN, time.monotonic())
            for stage in p.STAGES[:4]:
                observer.emit(stage)
            cls = p.result_class(original, observer)
            cls.journal = p.JournalMirror(io.StringIO(), observer, "synthetic")
            class Synthetic(unittest.TestCase):
                def id(self):
                    return "synthetic"
                def runTest(self):
                    with self.subTest(i=0):
                        self.fail("synthetic failing subtest")
                    with self.subTest(i=1):
                        self.skipTest("synthetic skipped subtest")
                    with self.subTest(i=2):
                        pass
            result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=cls).run(Synthetic())
            observer.close()
            self.assertEqual(observer.counts["subtests_completed"], 2)
            self.assertEqual(observer.counts["subtests_failed"], 1)
            self.assertEqual(len(result.failures), 1)
            self.assertEqual(len(result.skipped), 1)

    def test_writer_byte_cap_refuses_extra_record(self):
        with tempfile.TemporaryDirectory(prefix="p239-synthetic-") as folder:
            path = Path(folder) / "progress.jsonl"
            observer = p.Progress(path, RUN, time.monotonic())
            observer.emit("child_started")
            before = path.read_bytes()
            try:
                with mock.patch.object(p, "MAX_PROGRESS", len(before)), self.assertRaisesRegex(
                        RuntimeError, "PROGRESS_CAP"):
                    observer.emit("source_verified")
                self.assertEqual(path.read_bytes(), before)
            finally:
                observer.close()

    def test_result_subclass_only_addsubtest_and_super_first(self):
        original = h.load_original()
        observer = mock.Mock()
        cls = p.result_class(original, observer)
        self.assertEqual({k for k in cls.__dict__ if not k.startswith("__")}, {"addSubTest"})
        result = cls(unittest.runner._WritelnDecorator(io.StringIO()), True, 0)
        test = unittest.FunctionTestCase(lambda: None)
        def verify_after_super(err):
            self.assertEqual(len(result.failures), 1)
            self.assertIsNotNone(err)
        observer.subtest.side_effect = verify_after_super
        err = (AssertionError, AssertionError("synthetic"), None)
        result.addSubTest(test, test, err)
        observer.subtest.assert_called_once_with(err)

    def test_counted_subtests_are_not_whole_method_success(self):
        original = h.load_original()
        with tempfile.TemporaryDirectory(prefix="p239-synthetic-") as folder:
            observer = p.Progress(Path(folder) / "progress.jsonl", RUN, time.monotonic())
            for stage in p.STAGES[:4]:
                observer.emit(stage)
            cls = p.result_class(original, observer)
            cls.journal = p.JournalMirror(io.StringIO(), observer, "synthetic")
            class Synthetic(unittest.TestCase):
                def id(self):
                    return "synthetic"
                def runTest(self):
                    with self.subTest(i=0):
                        pass
                    self.fail("assertion AFTER completed subtest")
            result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=cls).run(Synthetic())
            observer.close()
            self.assertEqual(observer.counts["subtests_completed"], 1)
            self.assertEqual(observer.counts["subtests_failed"], 0)
            self.assertFalse(result.wasSuccessful())
            self.assertEqual(len(result.failures), 1)

    def test_journal_start_observed_only_after_original_flush(self):
        stream, observer = mock.Mock(), mock.Mock()
        mirror = p.JournalMirror(stream, observer, "synthetic")
        mirror.write(json.dumps({"event": "start", "id": "synthetic"}) + "\n")
        observer.emit.assert_not_called()
        mirror.flush()
        stream.flush.assert_called_once()
        observer.emit.assert_called_once_with("test_begun")
        self.assertTrue(observer.active)

    def test_helper_raw_pin_and_delta_guard_fail_closed(self):
        raw = (Path(__file__).resolve().parents[1] / p.HELPER).read_bytes()
        self.assertEqual(p.authenticate_helper(raw), raw)
        for bad in (raw + b"\n", raw.replace(b"\n", b"\r\n"), raw[:-1]):
            with self.assertRaisesRegex(RuntimeError, "P238_RAW_SOURCE_PIN"):
                p.authenticate_helper(bad)
        rows = ["A\t" + x for x in p.ADDITIONS]
        p.check_delta([p.PARENT], rows)
        for parents, changed in (([], rows), ([h.PARENT], rows), ([p.PARENT] * 2, rows),
                                 ([p.PARENT], rows[:-1]), ([p.PARENT], rows + ["A\textra"]),
                                 ([p.PARENT], ["M\t" + p.ADDITIONS[0]] + rows[1:]),
                                 ([p.PARENT], rows + [rows[0]])):
            with self.assertRaises(RuntimeError):
                p.check_delta(parents, changed)

    def test_p239_never_changes_inherited_guard_identity(self):
        self.assertEqual(h.BRANCH, "byok-c1-p238-g1-immutable-batch-equivalence-20261115")
        self.assertEqual(h.PARENT, "f66358de30fcb451e660e500df6a7843c6bbf0a6")
        with self.assertRaises(RuntimeError):
            h.provenance(Path(__file__).resolve().parents[1])

    def test_new_source_guard_with_synthetic_git_refuses_disk_or_parent_tamper(self):
        # Fake topology only; never original/P238 provenance or source authority.
        helper_raw = (Path(__file__).resolve().parents[1] / p.HELPER).read_bytes()
        with tempfile.TemporaryDirectory(prefix="p239-synthetic-") as folder:
            root, head = Path(folder), "a" * 40
            raw = dict.fromkeys(p.ADDITIONS, b"synthetic addition\n")
            raw[p.HELPER] = helper_raw
            p234 = "scripts/p234_windows_finegrain_diagnostic.py"
            raw[p234] = b"synthetic P234 Git/disk seam\n"
            disk = dict(raw)
            parents = [p.PARENT]
            def git(unused_root, *args):
                table = {
                    ("rev-parse", "HEAD"): (head + "\n").encode(),
                    ("rev-parse", "--is-shallow-repository"): b"false\n",
                    ("rev-parse", "--show-object-format"): b"sha1\n",
                    ("config", "--get", "core.autocrlf"): b"false\n",
                    ("status", "--porcelain=v1", "-uall", "--ignored=matching"): b"",
                    ("for-each-ref", "refs/replace"): b"",
                    ("rev-parse", "--absolute-git-dir"): str(root / "fake-git").encode(),
                    ("rev-list", "--parents", "-n", "1", head):
                        (head + " " + " ".join(parents)).encode(),
                    ("diff-tree", "--no-commit-id", "--name-status", "-r", "--no-renames", p.PARENT, head):
                        "\n".join("A\t" + x for x in p.ADDITIONS).encode(),
                    ("rev-parse", head + ":" + p234): b"0c5781a28187bd5eddb5f7a3ff0d85c1a5430d6c\n",
                }
                if args[0] == "ls-tree":
                    return b"100644 blob synthetic\tfixture\n"
                if args[0] == "show":
                    return raw[args[1].split(":", 1)[1]]
                return table[args]
            fake = mock.Mock()
            fake.git.side_effect = git
            fake.read.side_effect = lambda path: disk[path.relative_to(root).as_posix()]
            env = dict(GITHUB_ACTIONS="true", RUNNER_OS="Windows", RUNNER_ENVIRONMENT="github-hosted",
                       GITHUB_REPOSITORY="krismcan/Mark-LV", GITHUB_EVENT_NAME="push",
                       GITHUB_REF_NAME=p.BRANCH, GITHUB_SHA=head)
            with mock.patch.dict(p.os.environ, env), mock.patch.object(p.sys, "platform", "win32"):
                self.assertEqual(p.provenance(root, fake)["head"], head)
                disk[p.ADDITIONS[0]] += b"tamper"
                with self.assertRaisesRegex(RuntimeError, "CONTROLLER_BYTES"):
                    p.provenance(root, fake)
                disk[p.ADDITIONS[0]] = raw[p.ADDITIONS[0]]
                parents.append("b" * 40)
                with self.assertRaisesRegex(RuntimeError, "EXACT_PARENT"):
                    p.provenance(root, fake)

    def test_no_stale_pass_and_outcome_preservation(self):
        witness = self.parse(completed())
        self.assertEqual(p.evidence_exit(3, witness, True), 3)
        for code in (1, 124, 125):
            self.assertEqual(p.evidence_exit(code, witness, True), code)
        for bad in (self.parse(preflight()), self.parse(completed(), b"torn"),
                    p.parse_progress(encode(completed()), "2" * 32),
                    p.parse_progress(b"", RUN)):
            self.assertEqual(p.evidence_exit(3, bad, True), 125)
            self.assertEqual(p.evidence_exit(1, bad, False), 1)
        self.assertEqual(p.evidence_exit(3, witness, False), 125)

    def test_exact_180_spawn_budget_and_zero_progress_timeout(self):
        with tempfile.TemporaryDirectory(prefix="p239-synthetic-") as folder:
            fake, job = old.FakeProcess(), mock.Mock()
            job.active.side_effect = [1, 1, 0, 0]
            with mock.patch.object(p.subprocess, "Popen", return_value=fake) as spawn, mock.patch.object(
                    p.time, "monotonic", side_effect=[0, 180, 181, 181, 182]):
                record = p.contained(Path(folder), Path(folder), RUN, h, job_factory=lambda: job)
            self.assertTrue(record["timed_out"])
            self.assertEqual(record["configured_whole_child_seconds"], 180)
            self.assertEqual(record["tree_cleanup"], "JOB_EMPTY_CONFIRMED")
            command = spawn.call_args.args[0]
            self.assertIn("p239_g1_progress_observer.py", command[2])
            self.assertEqual(command[-2:], ["--origin", "0"])
            self.assertEqual(h.classify(record, None, [], h.load_original())[1], 124)
            self.assertEqual(p.evidence_exit(124, p.parse_progress(b"", RUN), None), 125)
            job.terminate.assert_called_once()
        for seconds in (179, 181, 180.0, True):
            with self.assertRaisesRegex(RuntimeError, "ORIGINAL_BUDGET"):
                p.contained(Path(), Path(), RUN, h, seconds=seconds)

    def test_assignment_failure_blocks_child_handshake(self):
        with tempfile.TemporaryDirectory(prefix="p239-synthetic-") as folder:
            fake, job = old.FakeProcess(), mock.Mock()
            job.assign.side_effect = RuntimeError("synthetic")
            job.active.return_value = 0
            with mock.patch.object(p.subprocess, "Popen", return_value=fake):
                record = p.contained(Path(folder), Path(folder), RUN, h, job_factory=lambda: job)
            self.assertEqual(fake.stdin.getvalue(), b"")
            self.assertTrue(record["aborted"])
            self.assertTrue(fake.killed)

    def test_residual_descendant_and_cleanup_errors_cannot_pass(self):
        for failure in (None, "active", "terminate", "close"):
            with tempfile.TemporaryDirectory(prefix="p239-synthetic-") as folder:
                fake, job = old.FakeProcess(code=0), mock.Mock()
                job.active.side_effect = [1, 1, 0, 0]
                if failure:
                    getattr(job, failure).side_effect = RuntimeError("synthetic")
                with mock.patch.object(p.subprocess, "Popen", return_value=fake):
                    record = p.contained(Path(folder), Path(folder), RUN, h, job_factory=lambda: job)
                self.assertEqual(h.classify(record, None, [], h.load_original())[1], 125)
                if failure:
                    self.assertEqual(record["tree_cleanup"], "UNCERTAIN")
                else:
                    self.assertTrue(record["residual_descendants_after_root_exit"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(old.CandidateTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(ProgressTests),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    good = result.wasSuccessful() and not result.skipped
    if args.report:
        h.write(args.report, {"scope": "SYNTHETIC ONLY; P238 + P239", "run": result.testsRun,
                             "failures": len(result.failures), "errors": len(result.errors),
                             "skips": len(result.skipped), "pass": good, "release": "HOLD"})
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
