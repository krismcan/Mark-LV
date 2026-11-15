"""P243 focused synthetic proof. No product test import, discovery or G1 run."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import queue
import subprocess
import tempfile
import time
import types
import unittest
from unittest import mock

import p243_g1_older_seal_batch as p

ROOT = Path(__file__).resolve().parents[1]
MODULES = p.load_dependencies(ROOT)  # authenticate all inherited code FIRST
H = MODULES["p238_g1_immutable_batch_candidate"]
EQUALITY = MODULES["p240_g1_safe_transport"]
ORIGINAL = MODULES["p234_windows_finegrain_diagnostic"]
import p238_g1_batch_selftest as inherited_batch
import p239_g1_progress_selftest as inherited_progress
import p240_g1_safe_transport_selftest as inherited_equality

RUN = "1" * 32


def raw_sources():
    return {name: (ROOT / "tests" / (name + ".py")).read_bytes() for name in p.SOURCE_PINS}


class SourceProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raws = raw_sources()
        cls.manifest, cls.digests, cls.values = p.derive_sources(cls.raws)

    def test_131_literal_source_pins_and_exact_23_B_entries(self):
        self.assertEqual(len(self.manifest), 131)
        self.assertEqual([s[4] for s in p.SPECS], [5, 3, 14, 16, 20, 19, 20, 11, 23])
        b = p.SPECS[-1][0]
        self.assertEqual({q[len(b) + 1:]: v for q, v in self.manifest.items()
                          if q.startswith(b + ":")}, H.MANIFEST)
        self.assertTrue(all(q.split(":", 1)[0] in self.digests for q in self.manifest))
        with self.assertRaises(TypeError):
            self.manifest["synthetic"] = ("a" * 40, "b" * 64)

    def test_every_original_source_byte_is_authenticated(self):
        for name in self.raws:
            with self.subTest(source=name), self.assertRaisesRegex(RuntimeError, "ORIGINAL_SOURCE_PIN"):
                p.derive_sources(dict(self.raws, **{name: self.raws[name] + b"tamper"}))

    def test_missing_extra_and_foreign_sources_refused(self):
        missing = dict(self.raws)
        missing.pop(next(iter(missing)))
        for changed in (missing, dict(self.raws, synthetic=b"")):
            with self.assertRaisesRegex(RuntimeError, "SOURCE_SET"):
                p.derive_sources(changed)

    def test_forged_rows_cannot_teach_new_expected_pins(self):
        for index in range(len(p.ROWS)):
            query, oid, pin = p.ROWS[index]
            rows = list(p.ROWS)
            rows[index] = (query, oid, "0" * 64)
            with self.subTest(row=index), mock.patch.object(p, "ROWS", tuple(rows)):
                with self.assertRaisesRegex(RuntimeError, "LITERAL_MANIFEST_EQUALITY"):
                    p.derive_sources(self.raws)

    def test_added_missing_duplicate_and_mutable_queries_refused(self):
        for rows in (p.ROWS[:-1], p.ROWS + (p.ROWS[0],),
                     p.ROWS + (("HEAD:synthetic.py", "a" * 40, "b" * 64),)):
            with mock.patch.object(p, "ROWS", rows), self.assertRaises(RuntimeError):
                p.derive_sources(self.raws)

    def test_830_and_831_use_original_crlf_normalization(self):
        for spec in p.SPECS[:2]:
            digest = self.digests[spec[0]]
            self.assertEqual(digest("synthetic", b"a\r\nb\n"), p.sha(b"a\nb\n"))
            self.assertNotEqual(digest("synthetic", b"a\rb\n"), p.sha(b"a\nb\n"))

    def test_832_normalizes_then_zeros_exactly_one_self_pin(self):
        commit, name = p.SPECS[2][:2]
        path = "tests/" + name + ".py"
        text = ('"' + path + '": "' + "a" * 64 + '",\r\n').encode()
        expected = ('"' + path + '": "' + "0" * 64 + '",\n').encode()
        self.assertEqual(self.digests[commit](path, text), p.sha(expected))
        for raw in (b"absent", text + text):
            with self.assertRaises(AssertionError):
                self.digests[commit](path, raw)

    def test_later_rules_preserve_crlf_and_binary_for_nonself_paths(self):
        raw = b"\0\xff\r\n\r\x80"
        for spec in p.SPECS[3:]:
            self.assertEqual(self.digests[spec[0]]("synthetic.bin", raw), p.sha(raw))
            self.assertNotEqual(self.digests[spec[0]]("synthetic.bin", raw),
                                p.sha(raw.replace(b"\r\n", b"\n")))

    def test_all_self_rules_require_one_original_literal(self):
        for spec in p.SPECS[2:]:
            commit, name = spec[:2]
            path = "tests/" + name + ".py"
            raw = ('"' + path + '": "' + "c" * 64 + '",\n').encode()
            zeroed = raw.replace(b"c" * 64, b"0" * 64)
            self.assertEqual(self.digests[commit](path, raw), p.sha(zeroed))
            for changed in (b"", raw + raw, raw.replace(b"c" * 64, b"C" * 64)):
                with self.subTest(source=name), self.assertRaises(AssertionError):
                    self.digests[commit](path, changed)

    def test_literal_reader_refuses_executable_and_duplicate_values(self):
        for raw in (b'P = {"a": "x", "a": "y"}', b'P = dict(a="x")', b'P = unknown.value'):
            with self.assertRaises(RuntimeError):
                p.literal("P", p.assignments(raw))
        with self.assertRaisesRegex(RuntimeError, "DUPLICATE_SOURCE_ASSIGNMENT"):
            p.assignments(b'P = 1\nP = 2\n')

    def test_exact_parent_four_additions_only(self):
        rows = ["A\t" + path for path in p.ADDITIONS]
        p.check_delta([p.PARENT], rows)
        for parents, paths in (([], rows), ([p.PARENT, "a" * 40], rows),
                               ([p.PARENT], rows[:-1]), ([p.PARENT], rows + ["A\textra"])):
            with self.assertRaises(RuntimeError):
                p.check_delta(parents, paths)

    def test_every_dependency_is_authenticated_before_execution(self):
        raws = {name: (ROOT / "scripts" / (name + ".py")).read_bytes()
                for name in p.DEPENDENCIES}
        for target in raws:
            def changed(path, selected=target):
                raw = raws[path.stem]
                return raw + b"tamper" if path.stem == selected else raw
            with self.subTest(dependency=target), mock.patch.object(
                    Path, "read_bytes", autospec=True, side_effect=changed):
                with self.assertRaisesRegex(RuntimeError, "DEPENDENCY_PIN"):
                    p.load_dependencies(ROOT)

    def test_p243_host_guard_requires_the_strict_host_identity(self):
        with mock.patch.dict(p.os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "HOST_IDENTITY"):
                p.provenance(ROOT, H)


class TransportTests(unittest.TestCase):
    def setUp(self):
        # This stand-in tests the transport primitive. Production admission
        # exclusively constructs its immutable manifest through derive_sources.
        self.commit = "a" * 40
        self.query = self.commit + ":tests/synthetic.bin"
        self.raw = b"synthetic\r\n\0\xff"
        self.oid = H.blob(self.raw)
        self.manifest = {self.query: (self.oid, p.sha(self.raw))}
        self.witness = {self.query: self.raw}
        self.digests = {self.commit: lambda path, raw: p.sha(raw)}
        self.header = f"{self.oid} blob {len(self.raw)}\n".encode()
        self.frame = self.header + self.raw + b"\n"
        self.args = (["git", "show", self.query],)
        self.kwargs = dict(cwd=ROOT, stderr=subprocess.DEVNULL, timeout=20)
        self.progress = types.SimpleNamespace(counts=p.zeros(), reads_by_path={}, sample=mock.Mock())

    def verify(self, header=None, raw=None, delimiter=b"\n", witness=None, digests=None):
        return p.verify_frame(self.query, self.header if header is None else header,
                              self.raw if raw is None else raw, delimiter, self.manifest,
                              self.witness if witness is None else witness,
                              self.digests if digests is None else digests, H)

    def batch(self, raw):
        fake = inherited_batch.FakeProcess(raw)
        with mock.patch.object(p.subprocess, "Popen", return_value=fake):
            batch = p.Batch(ROOT, self.manifest, self.witness, self.digests, H)
        return batch, fake

    def test_exact_match_and_all_131_literal_queries(self):
        self.assertEqual(p.intercept_query(self.args, self.kwargs, ROOT, self.manifest), self.query)
        manifest = {q: (oid, pin) for q, oid, pin in p.ROWS}
        for query in manifest:
            self.assertEqual(p.intercept_query((["git", "show", query],),
                                               self.kwargs, ROOT, manifest), query)

    def test_mutable_identity_type_tree_and_unlisted_queries_delegate(self):
        commands = (["git", "show", "HEAD:tests/synthetic.bin"],
                    ["git", "show", self.commit + ":tests/unknown.bin"],
                    ["git", "show", self.query.upper()],
                    ["git", "show", self.query.replace("tests/", "tests/../tests/")],
                    ["git", "show", self.query, "--"], ["git.exe", "show", self.query],
                    ["git", "cat-file", "-t", self.commit], ["git", "cat-file", "--batch"],
                    ["git", "ls-tree", self.commit], ["git", "status"],
                    ["git", "branch", "--show-current"], ["git", "rev-parse", "HEAD"],
                    ["git", "merge-base", "--is-ancestor", self.commit, "HEAD"],
                    ["git", "show-ref", "--verify", "refs/tags/seal"],
                    ["git", "ls-files", "--stage", "-z"], ["git", "diff", "--cached"])
        native = mock.Mock(return_value=b"intentional-negative")
        batch = mock.Mock()
        limited = p.transport(ROOT, self.manifest, batch, native, self.progress)
        for command in commands:
            args = (command,)
            self.assertIsNone(p.intercept_query(args, self.kwargs, ROOT, self.manifest))
            self.assertEqual(limited(*args, **self.kwargs), b"intentional-negative")
            self.assertEqual(native.call_args, mock.call(*args, **self.kwargs))
        batch.get.assert_not_called()

    def test_near_signatures_and_path_aliases_delegate(self):
        changes = ({"cwd": str(ROOT)}, {"cwd": ROOT / "other"}, {"stderr": subprocess.PIPE},
                   {"timeout": 20.0}, {"timeout": True}, {"timeout": 19},
                   {"env": {}}, {"text": True}, {"shell": False}, {"encoding": "utf8"})
        for change in changes:
            self.assertIsNone(p.intercept_query(self.args, dict(self.kwargs, **change),
                                                ROOT, self.manifest))
        self.assertIsNone(p.intercept_query((tuple(self.args[0]),), self.kwargs, ROOT, self.manifest))
        self.assertIsNone(p.intercept_query((), dict(self.kwargs, args=self.args[0]), ROOT, self.manifest))
        self.assertIsNone(p.intercept_query(self.args, {"cwd": ROOT}, ROOT, self.manifest))

    def test_native_mock_keeps_call_record_side_effect_bytes_and_exception_identity(self):
        native = mock.Mock(return_value=b"injected fake negative")
        batch = mock.Mock()
        limited = p.transport(ROOT, self.manifest, batch, native, self.progress)
        self.assertEqual(limited(*self.args, **self.kwargs), b"injected fake negative")
        native.assert_called_once_with(*self.args, **self.kwargs)
        for error in (subprocess.CalledProcessError(128, "SYNTHETIC", output=b"negative"),
                      subprocess.TimeoutExpired("SYNTHETIC", 20), RuntimeError("synthetic")):
            native.side_effect = error
            with self.assertRaises(type(error)) as received:
                limited(*self.args, **self.kwargs)
            self.assertIs(received.exception, error)
        batch.get.assert_not_called()
        self.assertEqual(self.progress.counts["delegated_started"], 4)
        self.assertEqual(self.progress.counts["delegated_completed"], 4)

    def test_fixture_captured_git_and_transforming_mock_remain_causal(self):
        batch = mock.Mock()
        batch.get.return_value = self.raw
        limited = p.transport(ROOT, self.manifest, batch, p.NATIVE, self.progress)
        def actual(*args):
            return subprocess.check_output(["git", *args], **self.kwargs)
        hits = []
        def fake_git(*args):
            value = actual(*args)
            if args == ("show", self.query):
                hits.append(args)
                return value + b"intentional tamper"
            return value
        with mock.patch.object(subprocess, "check_output", limited):
            seam = mock.Mock(side_effect=fake_git)
            self.assertEqual(seam("show", self.query), self.raw + b"intentional tamper")
        self.assertEqual(hits, [("show", self.query)])
        self.assertEqual(self.progress.counts["validated_reads"], 1)
        batch.get.assert_called_once_with(self.query)

    def test_native_failure_identity_survives_a_progress_sampling_failure(self):
        error = subprocess.CalledProcessError(128, "SYNTHETIC", output=b"negative")
        native = mock.Mock(side_effect=error)
        self.progress.sample.side_effect = RuntimeError("synthetic progress refusal")
        limited = p.transport(ROOT, self.manifest, mock.Mock(), native, self.progress)
        with self.assertRaises(subprocess.CalledProcessError) as received:
            limited(*self.args, **self.kwargs)
        self.assertIs(received.exception, error)
        self.progress.sample.assert_not_called()

    def test_wrapper_above_transport_can_intentionally_return_fake_negative(self):
        batch = mock.Mock()
        batch.get.return_value = self.raw
        limited = p.transport(ROOT, self.manifest, batch, p.NATIVE, self.progress)
        wrapper = mock.Mock(side_effect=lambda *a, **kw: limited(*a, **kw) + b"tamper")
        self.assertEqual(wrapper(*self.args, **self.kwargs), self.raw + b"tamper")
        wrapper.assert_called_once_with(*self.args, **self.kwargs)

    def test_exact_fresh_frame_success(self):
        self.assertEqual(self.verify(), self.raw)

    def test_header_oid_type_size_cap_and_delimiter(self):
        for header in (b"", b"x" * 129, self.header.replace(self.oid.encode(), b"0" * 40),
                       self.header.replace(b" blob ", b" tree "), self.header[:-1],
                       f"{self.oid} blob 01\n".encode(),
                       f"{self.oid} blob {H.MAX_BLOB + 1}\n".encode()):
            with self.assertRaises(RuntimeError):
                self.verify(header=header)
        for delimiter in (b"", b"x", b"\n\n"):
            with self.assertRaises(RuntimeError):
                self.verify(delimiter=delimiter)

    def test_size_sha1_frozen_sha256_and_show_witness_are_independent(self):
        for raw in (self.raw[:-1], self.raw + b"x", b"X" + self.raw[1:]):
            with self.assertRaises(RuntimeError):
                self.verify(raw=raw)
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_NORMALIZED_PIN"):
            self.verify(digests={self.commit: lambda path, raw: "0" * 64})
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_SHOW_BYTES"):
            self.verify(witness={self.query: self.raw + b"tamper"})

    def test_repeated_calls_write_two_fresh_oid_requests(self):
        batch, fake = self.batch(self.frame * 2)
        self.assertEqual(batch.get(self.query), self.raw)
        self.assertEqual(batch.get(self.query), self.raw)
        self.assertEqual(fake.stdin.getvalue(), ((self.oid + "\n") * 2).encode())
        self.assertEqual(batch.sequence, 2)
        batch.close()

    def test_valid_then_tampered_read_poisoned_without_retry_or_fallback(self):
        batch, fake = self.batch(self.frame + self.header + b"X" + self.raw[1:] + b"\n")
        self.assertEqual(batch.get(self.query), self.raw)
        with self.assertRaisesRegex(RuntimeError, "BLOB_IDENTITY"):
            batch.get(self.query)
        with self.assertRaisesRegex(RuntimeError, "BATCH_STATE"):
            batch.get(self.query)
        self.assertEqual(batch.sequence, 2)
        with self.assertRaisesRegex(RuntimeError, "BATCH_CLEAN_EXIT"):
            batch.close()
        self.assertTrue(fake.killed)

    def test_missing_truncated_and_different_frames_refused(self):
        for raw in (b"", self.frame[:-2], b"0" * 40 + self.frame[40:]):
            batch, _ = self.batch(raw)
            with self.assertRaises(RuntimeError):
                batch.get(self.query)
            with self.assertRaises(RuntimeError):
                batch.close()

    def test_timeout_remains_20_seconds_and_poisoned(self):
        batch, _ = self.batch(self.frame)
        with mock.patch.object(p.queue.Queue, "get", side_effect=queue.Empty) as get:
            with self.assertRaises(queue.Empty):
                batch.get(self.query)
            get.assert_called_once_with(timeout=20)
        with self.assertRaises(RuntimeError):
            batch.get(self.query)
        with self.assertRaises(RuntimeError):
            batch.close()

    def test_read_limit_and_concurrent_exchange_fail_closed(self):
        batch, _ = self.batch(self.frame)
        batch.sequence = p.MAX_READS
        with self.assertRaisesRegex(RuntimeError, "BATCH_STATE"):
            batch.get(self.query)
        with self.assertRaises(RuntimeError):
            batch.close()
        batch, _ = self.batch(self.frame)
        batch.lock.acquire()
        try:
            with self.assertRaisesRegex(RuntimeError, "CONCURRENT_BATCH_CALL"):
                batch.get(self.query)
        finally:
            batch.lock.release()
        with self.assertRaises(RuntimeError):
            batch.close()

    def test_failed_verified_read_propagates_and_does_not_count(self):
        batch = mock.Mock()
        error = RuntimeError("synthetic refusal")
        batch.get.side_effect = error
        limited = p.transport(ROOT, self.manifest, batch, p.NATIVE, self.progress)
        with self.assertRaises(RuntimeError) as received:
            limited(*self.args, **self.kwargs)
        self.assertIs(received.exception, error)
        self.assertEqual(self.progress.counts["validated_reads"], 0)
        self.assertEqual(self.progress.counts["delegated_started"], 0)


class LifecycleTests(unittest.TestCase):
    def test_bounded_progress_accepts_older_reads_above_4096_and_rejects_cap(self):
        with tempfile.TemporaryDirectory(prefix="p243-synthetic-") as directory:
            path = Path(directory) / "progress.jsonl"
            progress = p.Progress(path, RUN, time.monotonic())
            for stage in p.STAGES[:5]:
                progress.emit(stage)
            progress.counts["validated_reads"] = 5000
            progress.emit("running")
            progress.close()
            witness = p.parse_progress(path.read_bytes(), RUN)
            self.assertTrue(witness["records_valid"])
            self.assertFalse(witness["observation_complete"])
            self.assertEqual(witness["safe_counts"]["validated_reads"], 5000)
            last = json.loads(path.read_bytes().splitlines()[-1])
            changed = dict(last, seq=last["seq"] + 1, validated_reads=p.MAX_READS + 1)
            with self.assertRaisesRegex(RuntimeError, "COUNTER_RELATION"):
                p.validate_event(changed, last, p.binding(RUN))

    def test_foreign_torn_and_counter_regression_cannot_prove_completion(self):
        events = inherited_progress.completed()
        for event in events:
            event.update(schema=243, binding=p.binding(RUN))
        raw = inherited_progress.encode(events)
        self.assertTrue(p.parse_progress(raw, RUN)["observation_complete"])
        for changed, run in ((raw, "2" * 32), (raw + b"torn", RUN),
                             (raw.replace(b'"schema": 243', b'"schema": 239'), RUN)):
            self.assertFalse(p.parse_progress(changed, run)["records_valid"])

    def test_exact_180_spawn_budget_and_confirmed_empty_job(self):
        with tempfile.TemporaryDirectory(prefix="p243-synthetic-") as folder:
            fake, job = inherited_batch.FakeProcess(), mock.Mock()
            job.active.side_effect = [1, 1, 0, 0]
            with mock.patch.object(p.subprocess, "Popen", return_value=fake) as spawn, mock.patch.object(
                    p.time, "monotonic", side_effect=[0, 180, 181, 181, 182]):
                record = p.contained(Path(folder), Path(folder), RUN, H, job_factory=lambda: job)
            self.assertTrue(record["timed_out"])
            self.assertEqual(record["tree_cleanup"], "JOB_EMPTY_CONFIRMED")
            self.assertEqual(record["configured_whole_child_seconds"], 180)
            self.assertEqual(Path(spawn.call_args.args[0][2]).name, "p243_g1_older_seal_batch.py")
            self.assertEqual(H.classify(record, None, [], ORIGINAL)[1], 124)
            job.terminate.assert_called_once()
        for seconds in (179, 181, 180.0, True):
            with self.assertRaisesRegex(RuntimeError, "ORIGINAL_BUDGET"):
                p.contained(Path(), Path(), RUN, H, seconds=seconds)

    def test_assignment_failure_blocks_child_handshake(self):
        with tempfile.TemporaryDirectory(prefix="p243-synthetic-") as folder:
            fake, job = inherited_batch.FakeProcess(), mock.Mock()
            job.assign.side_effect = RuntimeError("synthetic")
            job.active.return_value = 0
            with mock.patch.object(p.subprocess, "Popen", return_value=fake):
                record = p.contained(Path(folder), Path(folder), RUN, H, job_factory=lambda: job)
            self.assertEqual(fake.stdin.getvalue(), b"")
            self.assertTrue(record["aborted"])
            self.assertTrue(fake.killed)

    def test_cleanup_uncertain_and_residual_descendants_stay_hold(self):
        for failure in (None, "active", "terminate", "close"):
            with tempfile.TemporaryDirectory(prefix="p243-synthetic-") as folder:
                fake, job = inherited_batch.FakeProcess(code=0), mock.Mock()
                job.active.side_effect = [1, 1, 0, 0]
                if failure:
                    getattr(job, failure).side_effect = RuntimeError("synthetic")
                with mock.patch.object(p.subprocess, "Popen", return_value=fake):
                    record = p.contained(Path(folder), Path(folder), RUN, H, job_factory=lambda: job)
                self.assertEqual(H.classify(record, None, [], ORIGINAL)[1], 125)

    def test_p240_canonical_comparison_uses_complete_original_bytes(self):
        value = {"head": p.SOURCE, "raw_tracked_sha256": {"synthetic": "a" * 64},
                 "historical_tags": {"synthetic": ("b" * 40, "c" * 40)},
                 "hook_free_methods": {"synthetic": ["synthetic.method"]}}
        raw = ORIGINAL.canonical(value)
        self.assertNotEqual(value, json.loads(raw))
        self.assertTrue(EQUALITY.compare_witness(ORIGINAL, raw, p.sha(raw), value)["canonical_bytes_equal"])
        changed = copy.deepcopy(value)
        changed["raw_tracked_sha256"]["synthetic"] = "d" * 64
        with self.assertRaisesRegex(RuntimeError, "SOURCE_WITNESS_BYTES_CHANGED"):
            EQUALITY.compare_witness(ORIGINAL, raw, p.sha(raw), changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in (
        inherited_batch.CandidateTests, inherited_progress.ProgressTests,
        inherited_equality.WitnessTests, inherited_equality.GuardTests,
        SourceProofTests, TransportTests, LifecycleTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    good = result.wasSuccessful() and not result.skipped
    if args.report:
        H.write(args.report, {"schema": 243, "scope": "SYNTHETIC ONLY", "run": result.testsRun,
                             "failures": len(result.failures), "errors": len(result.errors),
                             "skips": len(result.skipped), "pass": good, "release": "HOLD",
                             "g1_executed": False})
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
