"""P239 instrumented, bounded progress witness. Every product gate stays HOLD.

No original test is imported by guard, parser or synthetic-only tests. Raw
evidence is private runner-temp data; public output contains fixed metrics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import types
import unittest
import uuid
from unittest import mock

PARENT = "6093f499f7824188603488c11e350c69140efab4"
SOURCE = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
BRANCH = "byok-c1-p239-g1-bounded-progress-20261115"
HELPER = "scripts/p238_g1_immutable_batch_candidate.py"
HELPER_SHA256 = "9f481c75764415fb4f829b3229d4989daf574b01ea7aa82241747a7cf4ff0eb7"
ADDITIONS = (
    ".github/workflows/p239-g1-bounded-progress.yml",
    "docs/byok-c1-p239-g1-progress.md",
    "scripts/p239_g1_progress_observer.py",
    "scripts/p239_g1_progress_selftest.py",
)
SECONDS = 180
SAMPLE = 32
MAX_EVENTS = 4096
MAX_PROGRESS = 2 * 1024 * 1024
MAX_LINE = 2048
MAX_COUNTER = 1_000_000
STAGES = ("child_started", "source_verified", "baseline_verified",
          "preflight_complete", "test_begun", "running", "test_finished",
          "postflight_complete")
COUNTERS = ("validated_reads", "delegated_started", "delegated_completed",
            "delegated_show_completed", "delegated_cat_file_completed",
            "delegated_ls_tree_completed", "delegated_other_completed",
            "subtests_completed", "subtests_failed")
KEYS = {"schema", "binding", "seq", "stage", "seconds", *COUNTERS}


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def authenticate_helper(raw):
    require(sha(raw) == HELPER_SHA256, "P238_RAW_SOURCE_PIN")
    return raw


def load_helpers():
    # Execute the very bytes checked, with no text normalization or guard patch.
    path = Path(__file__).resolve().parents[1] / HELPER
    raw = authenticate_helper(path.read_bytes())
    module = types.ModuleType("p239_pinned_p238")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    require(module.SOURCE == SOURCE and module.SECONDS == SECONDS
            and module.READ_SECONDS == 20 and len(module.MANIFEST) == 23,
            "P238_CONSTANTS")
    return module


def binding(run_id):
    require(type(run_id) is str and re.fullmatch(r"[0-9a-f]{32}", run_id), "RUN_ID")
    return sha((run_id + SOURCE + PARENT + HELPER_SHA256).encode("ascii"))


def zeros():
    return dict.fromkeys(COUNTERS, 0)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, "DUPLICATE_KEY")
        obj[key] = value
    return obj


def validate_event(event, previous, expected_binding):
    require(type(event) is dict and set(event) == KEYS, "EVENT_SCHEMA")
    require(type(event["schema"]) is int and event["schema"] == 239
            and event["binding"] == expected_binding, "FOREIGN_EVENT")
    require(type(event["seq"]) is int and event["seq"] == (
        previous["seq"] + 1 if previous else 1), "EVENT_SEQUENCE")
    seconds = event["seconds"]
    require(type(seconds) in (int, float) and 0 <= seconds <= SECONDS
            and math.isfinite(seconds), "EVENT_CLOCK")
    stage = event["stage"]
    require(type(stage) is str and stage in STAGES, "EVENT_STAGE")
    for key in COUNTERS:
        value = event[key]
        require(type(value) is int and 0 <= value <= MAX_COUNTER, "COUNTER_CAP")
        require(previous is None or value >= previous[key], "COUNTER_REGRESSION")
    require(event["validated_reads"] <= 4096
            and event["subtests_failed"] <= event["subtests_completed"] <= 23
            and event["delegated_completed"] <= event["delegated_started"]
            and sum(event[k] for k in COUNTERS[3:7]) == event["delegated_completed"],
            "COUNTER_RELATION")
    if previous is None:
        require(stage == STAGES[0] and all(event[k] == 0 for k in COUNTERS), "MISSING_START")
    else:
        old = previous["stage"]
        transitions = {
            "child_started": {"source_verified"},
            "source_verified": {"baseline_verified"},
            "baseline_verified": {"preflight_complete"},
            "preflight_complete": {"test_begun"},
            "test_begun": {"running", "test_finished"},
            "running": {"running", "test_finished"},
            "test_finished": {"postflight_complete"},
            "postflight_complete": set(),
        }
        require(stage in transitions[old], "STAGE_ORDER")
        require(seconds >= previous["seconds"], "CLOCK_REGRESSION")
        require(stage != "running" or any(event[k] != previous[k] for k in COUNTERS),
                "DUPLICATE_SAMPLE")
        require(event["subtests_completed"] - previous["subtests_completed"] in (0, 1)
                and 0 <= event["subtests_failed"] - previous["subtests_failed"]
                <= event["subtests_completed"] - previous["subtests_completed"],
                "SUBTEST_SEQUENCE")
        require(stage == "running" or event["subtests_completed"] == previous["subtests_completed"],
                "SUBTEST_STAGE")
        require(old != "test_finished" or all(event[k] == previous[k] for k in COUNTERS),
                "POSTFLIGHT_COUNTS")
    require(STAGES.index(stage) >= STAGES.index("test_begun")
            or event["subtests_completed"] == event["validated_reads"] == 0,
            "PREMATURE_COUNTS")
    require(stage not in STAGES[:3] or all(event[k] == 0 for k in COUNTERS), "PREFLIGHT_COUNTS")


def parse_progress(raw, run_id):
    """Read-only prefix parser. Last timestamp is a sample, NEVER a duration.

    Torn/invalid/foreign evidence cannot be complete. Safe prefix counters are
    lower bounds only; they never establish test success or source authority.
    """
    report = {"raw_sha256": sha(raw), "raw_bytes": len(raw), "accepted_events": 0,
              "records_valid": False, "observation_complete": False,
              "reason": "MISSING", "latest_stage": None,
              "latest_sample_seconds": None, "safe_counts": zeros(),
              "stage_first_seconds": dict.fromkeys(STAGES, None)}
    if not raw:
        return report
    if len(raw) > MAX_PROGRESS:
        report["reason"] = "BYTE_CAP"
        return report
    previous = None
    expected = binding(run_id)
    lines = raw.split(b"\n")
    try:
        for line in lines[:-1]:
            require(report["accepted_events"] < MAX_EVENTS, "EVENT_CAP")
            require(0 < len(line) <= MAX_LINE, "LINE_CAP")
            event = json.loads(line, object_pairs_hook=unique_object)
            validate_event(event, previous, expected)
            previous = event
            report.update(accepted_events=event["seq"], latest_stage=event["stage"],
                          latest_sample_seconds=event["seconds"],
                          safe_counts={k: event[k] for k in COUNTERS})
            if report["stage_first_seconds"][event["stage"]] is None:
                report["stage_first_seconds"][event["stage"]] = event["seconds"]
        require(not lines[-1], "TORN_TRAILING_LINE")
        require(previous is not None, "MISSING")
        report.update(records_valid=True, reason="VALID_PREFIX",
                      observation_complete=previous["stage"] == "postflight_complete")
    except (RuntimeError, ValueError, UnicodeError, RecursionError) as error:
        # JSON parser messages can contain raw data: export fixed codes only.
        report["reason"] = (str(error) if type(error) is RuntimeError else "INVALID_JSON")
    return report


class Progress:
    """One exclusive append-only file; <=4096 lines, <=2 MiB, flush each line."""
    def __init__(self, path, run_id, origin):
        self.stream = path.open("xb", buffering=0)
        self.binding, self.origin = binding(run_id), origin
        self.counts, self.previous, self.size = zeros(), None, 0
        self.reads_by_path = {}
        self.active = False

    def emit(self, stage):
        event = dict(self.counts, schema=239, binding=self.binding,
                     seq=self.previous["seq"] + 1 if self.previous else 1,
                     stage=stage, seconds=round(time.monotonic() - self.origin, 6))
        validate_event(event, self.previous, self.binding)
        raw = json.dumps(event, sort_keys=True, allow_nan=False).encode("ascii") + b"\n"
        require(event["seq"] <= MAX_EVENTS and len(raw) - 1 <= MAX_LINE
                and self.size + len(raw) <= MAX_PROGRESS, "PROGRESS_CAP")
        require(self.stream.write(raw) == len(raw), "PROGRESS_SHORT_WRITE")
        self.stream.flush()
        self.previous, self.size = event, self.size + len(raw)

    def sample(self, counter):
        if self.active and self.counts[counter] % SAMPLE == 0:
            self.emit("running")

    def subtest(self, err):
        require(self.active, "SUBTEST_OUTSIDE_TEST")
        self.counts["subtests_completed"] += 1
        self.counts["subtests_failed"] += int(err is not None)
        self.emit("running")

    def close(self):
        self.stream.close()


class JournalMirror:
    """Observe original start/stop only AFTER its private journal is flushed."""
    def __init__(self, stream, progress, test_id):
        self.stream, self.progress, self.test_id = stream, progress, test_id
        self.pending = None

    def write(self, raw):
        require(self.pending is None, "JOURNAL_PENDING")
        event = json.loads(raw)
        require(set(event) == {"event", "id"} and event["id"] == self.test_id
                and event["event"] in {"start", "stop"}, "JOURNAL_EVENT")
        result = self.stream.write(raw)
        self.pending = event["event"]
        return result

    def flush(self):
        self.stream.flush()
        if self.pending is not None:
            stage = "test_begun" if self.pending == "start" else "test_finished"
            self.progress.emit(stage)
            self.progress.active = self.pending == "start"
            self.pending = None


def result_class(original, progress):
    class InstrumentedJournalResult(original.JournalResult):
        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            progress.subtest(err)  # Completion observation only, no outcome change.
    return InstrumentedJournalResult


def delegated_kind(args):
    # Inspect only for aggregate fixed counters. Never serialize argv or paths.
    if (args and type(args[0]) is list and len(args[0]) >= 2
            and type(args[0][0]) is str and args[0][0] == "git"
            and type(args[0][1]) is str):
        return {"show": "show", "cat-file": "cat_file", "ls-tree": "ls_tree"}.get(
            args[0][1], "other")
    return "other"  # includes any unmatched check_output call; no inferred Git identity


def transport(helper, root, batch, native, progress):
    def limited(*args, **kwargs):
        path = helper.intercept_path(args, kwargs, root)
        if path is not None:
            raw = batch.get(path)  # unchanged P238 per-read frame/identity verification
            progress.counts["validated_reads"] += 1
            progress.reads_by_path[path] = progress.reads_by_path.get(path, 0) + 1
            progress.sample("validated_reads")
            return raw
        progress.counts["delegated_started"] += 1
        kind = delegated_kind(args)
        try:
            return native(*args, **kwargs)
        finally:
            progress.counts["delegated_completed"] += 1
            progress.counts["delegated_" + kind + "_completed"] += 1
            progress.sample("delegated_completed")
    return limited


def check_delta(parents, rows):
    require(parents == [PARENT], "EXACT_PARENT")
    require(sorted(rows) == sorted("A\t" + p for p in ADDITIONS), "EXACT_ADDITIONS")


def provenance(root, helper):
    # P239's own guard. P238.provenance is deliberately NEVER patched or called.
    require(sys.platform == "win32" and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_OS") == "Windows"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.getenv("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.getenv("GITHUB_EVENT_NAME") == "push"
            and os.getenv("GITHUB_REF_NAME") == BRANCH, "HOST_IDENTITY")
    git = lambda *args: helper.git(root, *args)
    head = git("rev-parse", "HEAD").decode().strip()
    require(head == os.getenv("GITHUB_SHA"), "HEAD")
    require(git("rev-parse", "--is-shallow-repository") == b"false\n", "SHALLOW")
    require(git("rev-parse", "--show-object-format") == b"sha1\n", "OBJECT_FORMAT")
    require(git("config", "--get", "core.autocrlf").strip() == b"false", "RAW_CHECKOUT")
    require(not git("status", "--porcelain=v1", "-uall", "--ignored=matching"), "DIRTY")
    require(not git("for-each-ref", "refs/replace"), "REPLACE")
    objdir = Path(git("rev-parse", "--absolute-git-dir").decode().strip())
    require(not (objdir / "info/grafts").exists(), "GRAFT")
    check_delta(git("rev-list", "--parents", "-n", "1", head).decode().split()[1:],
                git("diff-tree", "--no-commit-id", "--name-status", "-r", "--no-renames",
                    PARENT, head).decode().splitlines())
    hashes = []
    for path in ADDITIONS:
        require(git("ls-tree", head, "--", path).startswith(b"100644 blob "), "ADD_MODE")
        raw = helper.read(root / path)
        require(raw == git("show", head + ":" + path), "CONTROLLER_BYTES")
        hashes.append(sha(raw))  # fixed ADDITIONS order; no arbitrary public paths
    raw = authenticate_helper(helper.read(root / HELPER))
    require(raw == git("show", head + ":" + HELPER), "P238_DISK")
    p234 = "scripts/p234_windows_finegrain_diagnostic.py"
    require(git("rev-parse", head + ":" + p234).strip()
            == b"0c5781a28187bd5eddb5f7a3ff0d85c1a5430d6c", "P234_BLOB")
    require(helper.read(root / p234) == git("show", head + ":" + p234), "P234_DISK")
    return {"head": head, "parent": PARENT, "additions_sha256_in_fixed_order": hashes,
            "p238_helper_raw_sha256": sha(raw)}


def contained(source, private, run_id, helper, seconds=SECONDS, job_factory=None):
    """P238 supervisor semantics, separate P239 child; no budget extension."""
    require(type(seconds) is int and seconds == SECONDS, "ORIGINAL_BUDGET")
    binding(run_id)
    record = {"timed_out": False, "tree_cleanup": "UNCERTAIN", "aborted": False,
              "residual_descendants_after_root_exit": False,
              "configured_whole_child_seconds": SECONDS, "actual_process_exit": None}
    proc = None
    job = (job_factory or helper.Job)()
    began = time.monotonic()
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "_child",
               "--source", str(source), "--output", str(private), "--run-id", run_id,
               "--origin", repr(began)]
    try:
        with (private / "candidate.log").open("wb") as sink:
            proc = subprocess.Popen(command, cwd=source, env=helper.environment(),
                                    stdin=subprocess.PIPE, stdout=sink, stderr=subprocess.STDOUT)
            job.assign(proc)
            require(job.active() == 1, "JOB_HANDSHAKE")
            proc.stdin.write(b"!")
            proc.stdin.close()
            while proc.poll() is None:
                if time.monotonic() - began >= seconds:
                    record["timed_out"] = True
                    break
                require((private / "candidate.log").stat().st_size <= helper.MAX_LOG, "LOG_CAP")
                time.sleep(0.1)
    except Exception:
        record["aborted"] = True
    finally:
        try:
            active = job.active()
            if active and proc is not None and proc.poll() is not None and not record["timed_out"]:
                record["residual_descendants_after_root_exit"] = True
            if active:
                job.terminate()
            end = time.monotonic() + 5
            while job.active() and time.monotonic() < end:
                time.sleep(0.05)
            if job.active() == 0:
                record["tree_cleanup"] = "JOB_EMPTY_CONFIRMED"
            if proc is not None:
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=5)
                record["actual_process_exit"] = proc.returncode
        except Exception:
            record["tree_cleanup"] = "UNCERTAIN"
        finally:
            try:
                job.close()
            except Exception:
                record["tree_cleanup"] = "UNCERTAIN"
            if proc is not None and record["actual_process_exit"] is None:
                try:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(timeout=5)
                    record["actual_process_exit"] = proc.returncode
                except Exception:
                    record["tree_cleanup"] = "UNCERTAIN"
        record["elapsed_seconds_including_cleanup"] = round(time.monotonic() - began, 3)
    return record


def child(source, private, run_id, origin, helper):
    require(sys.stdin.buffer.read(1) == b"!", "SUPERVISOR_HANDSHAKE")
    runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    controller = Path(__file__).resolve().parents[1]
    require(sys.platform == "win32" and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"
            and private.is_relative_to(runner_temp) and private != runner_temp
            and not private.is_relative_to(source) and not private.is_relative_to(controller),
            "PRIVATE_HOSTED_CHILD")
    progress = Progress(private / "progress.jsonl", run_id, origin)
    try:
        progress.emit("child_started")
        original = helper.load_original()
        before = original.verify_source(source)  # unmodified full P233 verifier
        helper.write(private / "source-before.json", before)
        progress.emit("source_verified")
        sys.path.insert(0, str(source))
        originals, digest = helper.bootstrap(source)  # original B trees + 23 raw shows
        progress.emit("baseline_verified")
        batch = helper.Batch(source, originals, digest)
        result = None
        try:
            with mock.patch.object(subprocess, "check_output", transport(
                    helper, source, batch, subprocess.check_output, progress)):
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromName(helper.TEST)
                require(not loader.errors and suite.countTestCases() == 1, "ONE_G1_ONLY")
                progress.emit("preflight_complete")
                with (private / "events.jsonl").open("x", encoding="utf8") as stream:
                    cls = result_class(original, progress)
                    cls.journal = JournalMirror(stream, progress, helper.TEST)
                    result = unittest.TextTestRunner(verbosity=2, resultclass=cls).run(suite)
        finally:
            if result is not None:
                code = 0 if result.wasSuccessful() else 1
                helper.write(private / "result.json", {
                    "assigned": [helper.TEST], "tests_run": result.testsRun,
                    "original_unittest_exit": code,
                    "failures": [t.id() for t, _ in result.failures],
                    "errors": [t.id() for t, _ in result.errors],
                    "skips": [t.id() for t, _ in result.skipped],
                    "expected_failures": [t.id() for t in result.expectedFailures],
                    "unexpected_successes": [t.id() for t in result.unexpectedSuccesses]})
            try:
                batch.close()
            finally:
                helper.write(private / "metrics.json", {
                    "counts": progress.counts, "reads_by_path": progress.reads_by_path})
        require(progress.counts["validated_reads"] > 0, "NO_INTERCEPTION")
        require(original.verify_source(source) == before, "SOURCE_CHANGED")
        helper.write(private / "verified.json", {"before_after_equal": True})
        progress.emit("postflight_complete")
        return code
    finally:
        progress.close()


def evidence_exit(code, witness, source_equal):
    # Never convert the original classifier's failure into an evidence PASS.
    if code == 1:
        return 1
    if not witness["records_valid"] or source_equal is not True:
        return 125
    if code == 3 and (not witness["observation_complete"]
                      or witness["safe_counts"]["subtests_completed"] != 23
                      or witness["safe_counts"]["subtests_failed"] != 0
                      or witness["safe_counts"]["validated_reads"] == 0):
        return 125
    return code


def observe(source, output, helper):
    root = Path(__file__).resolve().parents[1]
    source, output = source.resolve(strict=True), output.resolve()
    runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    require(output.is_relative_to(runner_temp) and output != runner_temp
            and not output.is_relative_to(root) and not output.is_relative_to(source)
            and not root.is_relative_to(source) and not source.is_relative_to(root), "PATH_SEPARATION")
    output.mkdir(exist_ok=False)
    report = {"scope": "P239 INSTRUMENTED PROGRESS OBSERVATION", "release": "HOLD",
              "source": SOURCE, "full_unfiltered_regressions": "0/3",
              "independent_SEC03_SEC04": "MISSING", "exit": 125,
              "test_body_unchanged": True, "original_git_transport_instrumented": True}
    private = None
    try:
        controller = provenance(root, helper)
        report["controller"] = controller
        private = Path(tempfile.mkdtemp(prefix="p239-private-", dir=runner_temp)).resolve()
        require(not private.is_relative_to(root) and not private.is_relative_to(source)
                and not output.is_relative_to(private), "PRIVATE_SEPARATION")
        run_id = uuid.uuid4().hex
        report["progress_binding"] = binding(run_id)
        process = contained(source, private, run_id, helper)
        report["process"] = process
        report["candidate_status"] = "TIMEOUT" if process["timed_out"] else "INCOMPLETE"
        try:
            raw = helper.read(private / "progress.jsonl", MAX_PROGRESS) if (
                private / "progress.jsonl").exists() else b""
            witness = parse_progress(raw, run_id)
        except Exception:
            witness = parse_progress(b"", run_id)
            witness.update(raw_sha256=None, raw_bytes=None, reason="UNREADABLE_OR_OVERSIZED")
        report["progress"] = witness
        original = helper.load_original()
        result = json.loads(helper.read(private / "result.json")) if (
            private / "result.json").exists() else None
        if result is not None:
            report["recorded_candidate_unittest_exit"] = result["original_unittest_exit"]
        events = [json.loads(line) for line in helper.read(private / "events.jsonl").splitlines()] if (
            private / "events.jsonl").exists() else []
        summary, code = helper.classify(process, result, events, original)
        report["candidate_status"], report["classifier_exit"] = summary["status"], code
        # Only a confirmed empty job permits parent read-only source postflight.
        source_equal = None
        if process["tree_cleanup"] == "JOB_EMPTY_CONFIRMED":
            after = original.verify_source(source)
            helper.write(private / "source-after-parent.json", after)
            if (private / "source-before.json").exists():
                source_equal = after == json.loads(helper.read(private / "source-before.json"))
        report["source_before_after_equal"] = source_equal
        report["exit"] = evidence_exit(code, witness, source_equal)
        if code == 3:
            require(json.loads(helper.read(private / "verified.json"))
                    == {"before_after_equal": True}, "CHILD_POSTVERIFY")
            metrics = json.loads(helper.read(private / "metrics.json"))
            by_path = metrics["reads_by_path"]
            require(metrics["counts"] == witness["safe_counts"]
                    and set(by_path) == set(helper.MANIFEST)
                    and all(type(n) is int and n > 0 for n in by_path.values())
                    and sum(by_path.values()) == witness["safe_counts"]["validated_reads"],
                    "EXACT_PATH_COVERAGE")
            report["validated_manifest_paths"] = len(by_path)
        require(provenance(root, helper) == controller, "CONTROLLER_CHANGED")
    except Exception:
        report["error"] = "SOURCE_CONTAINMENT_INSTRUMENTATION_OR_RESULT_REFUSED"
        report["exit"] = 1 if report.get("classifier_exit") == 1 else 125
    finally:
        if private is not None:
            # Fixed filenames only. Raw journals/logs/witnesses are never public.
            receipts = {}
            for name in ("candidate.log", "progress.jsonl", "events.jsonl", "result.json",
                         "source-before.json", "verified.json", "source-after-parent.json", "metrics.json"):
                try:
                    if (private / name).exists():
                        receipts[name] = sha(helper.read(private / name))
                except Exception:
                    receipts[name] = "UNAVAILABLE_OR_OVERSIZED"
            report["raw_private_sha256"] = receipts
        helper.write(output / "candidate.json", report)
        print("P239_INSTRUMENTED_PROGRESS_EXIT=" + str(report["exit"]) + "|ALL_C1_GATES_HOLD")
    return report["exit"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("guard", "observe", "_child"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--origin", type=float)
    args = parser.parse_args()
    helper = load_helpers()
    if args.mode == "guard":
        helper.write(args.output / "controller-guard.json", provenance(
            Path(__file__).resolve().parents[1], helper))
        return 0
    if args.mode == "_child":
        require(args.origin is not None and math.isfinite(args.origin), "CLOCK_ORIGIN")
        return child(args.source.resolve(strict=True), args.output.resolve(strict=True),
                     args.run_id, args.origin, helper)
    return observe(args.source, args.output, helper)


if __name__ == "__main__":
    raise SystemExit(main())
