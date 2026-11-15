"""P237 OBSERVATION ONLY. Never returns release success; stdlib, one original G1.

Hosted entry: observe --source AUTHENTIC --output NEW_PUBLIC_DIRECTORY
Internal workers are separate processes; no test/import/mock/assertion changes.
Raw evidence stays in a disposable runner-temp directory, never uploaded.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time

PARENT = "97dcc779ccceef9e5957fe81eec4823e89546c43"
SOURCE = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
BRANCH = "byok-c1-p237-g1-original-trace-20261115"
TEST = "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_every_candidate_source_byte_is_bound"
CONTROLLER = "scripts/p234_windows_finegrain_diagnostic.py"
CONTROLLER_BLOB = "0c5781a28187bd5eddb5f7a3ff0d85c1a5430d6c"
ADDITIONS = (
    ".github/workflows/p237-g1-original-git-timing.yml",
    "docs/byok-c1-p237-g1-observation.md",
    "scripts/p237_g1_git_timing_observer.py",
    "scripts/p237_g1_observer_selftest.py",
)
SECONDS = 180  # original whole-child budget, including its own verification
HOLD = 3
MAX_FILES = 20000
MAX_BYTES = 128 * 1024 * 1024
MAX_FILE = 16 * 1024 * 1024
MAX_LINE = 256 * 1024
MAX_EVENTS = 500000
SAFE_OPS = frozenset({"version", "rev-parse", "status", "config", "for-each-ref",
                      "ls-tree", "show", "show-ref", "cat-file", "merge-base",
                      "rev-list", "diff", "diff-files", "diff-index", "ls-files",
                      "hash-object", "symbolic-ref", "update-index"})


def require(ok, code):
    if not ok:
        raise RuntimeError(code)  # fixed codes only; no raw exception/path disclosure


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def write(path, obj):
    path.write_bytes(canonical(obj))


def regular(path):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
            and not getattr(info, "st_file_attributes", 0) & 0x400, "NONREGULAR_FILE")
    return info


def read(path, limit=MAX_FILE):
    require(regular(path).st_size <= limit, "FILE_LIMIT")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "FILE_LIMIT")
    return raw


def clean_env(trace=None):
    # Do not modify the parent environment or any Git command/configuration.
    env = os.environ.copy()
    for key in list(env):
        upper = key.upper()
        if (upper.startswith(("GIT_", "P134_", "ACTIONS_", "INPUT_"))
                or any(word in upper for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))
                or upper in {"PYTHONPATH", "PYTHONHOME", "SSH_AUTH_SOCK", "SSH_AGENT_PID"}):
            del env[key]
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0",
               GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    if trace is not None:
        require(trace.is_absolute() and trace.is_dir() and not trace.is_symlink(), "TRACE_TARGET")
        env["GIT_TRACE2_EVENT"] = trace.as_posix()
    return env


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], env=clean_env(),
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=45, check=True).stdout


def check_delta(parents, rows):
    require(parents == [PARENT], "CONTROLLER_PARENT")
    expected = sorted("A\t" + path for path in ADDITIONS)
    require(sorted(rows) == expected, "CONTROLLER_EXACT_FOUR_ADDITIONS")


def controller_provenance(root):
    require(sys.platform == "win32" and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_OS") == "Windows"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.getenv("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.getenv("GITHUB_REF_NAME") == BRANCH, "HOST_IDENTITY")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    require(head == os.getenv("GITHUB_SHA"), "CONTROLLER_HEAD")
    require(git(root, "rev-parse", "--is-shallow-repository") == b"false\n", "CONTROLLER_SHALLOW")
    require(not git(root, "status", "--porcelain=v1", "-uall", "--ignored=matching").strip(),
            "CONTROLLER_DIRTY")
    require(not git(root, "for-each-ref", "refs/replace").strip(), "CONTROLLER_REPLACE")
    objdir = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
    require(not (objdir / "info/grafts").exists(), "CONTROLLER_GRAFT")
    parents = git(root, "rev-list", "--parents", "-n", "1", head).decode().split()[1:]
    rows = git(root, "diff-tree", "--no-commit-id", "--name-status", "-r", "--no-renames",
               PARENT, head).decode().splitlines()
    check_delta(parents, rows)
    raw = git(root, "show", PARENT + ":" + CONTROLLER)
    require(git(root, "rev-parse", PARENT + ":" + CONTROLLER).decode().strip()
            == CONTROLLER_BLOB, "HISTORICAL_CONTROLLER_BLOB")
    require(read(root / CONTROLLER) == raw, "HISTORICAL_CONTROLLER_BYTES")
    manifest = {}
    for path in ADDITIONS:
        disk = read(root / path)
        require(disk == git(root, "show", head + ":" + path), "CONTROLLER_RAW_BYTES")
        manifest[path] = sha(disk)
    return {"head": head, "parent": PARENT, "additions_raw_sha256": manifest,
            "p234_raw_sha256": sha(raw), "p234_blob": CONTROLLER_BLOB}


def load_p234():
    path = Path(__file__).with_name("p234_windows_finegrain_diagnostic.py")
    spec = importlib.util.spec_from_file_location("p237_original_p234", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.SECONDS == SECONDS and module.SOURCE == SOURCE, "P234_CONSTANTS")
    return module


def inventory(folder):
    """Flat private directories only. Rechecked during production, not just after."""
    files = []
    total = 0
    with os.scandir(folder) as entries:
        for entry in entries:
            require(len(files) < MAX_FILES, "FILE_COUNT_LIMIT")
            path = Path(entry.path)
            size = regular(path).st_size
            require(size <= MAX_FILE, "FILE_LIMIT")
            total += size
            require(total <= MAX_BYTES, "BYTE_LIMIT")
            files.append(path)
    return sorted(files)


def number(value):
    require(type(value) in (float, int) and math.isfinite(value) and 0 <= value <= 3600,
            "TRACE_DURATION")
    return float(value)


def trace_summary(folder, allow_incomplete=False):
    """Never export SID, PID, timestamps, argv, repository paths or arbitrary text."""
    files = inventory(folder)
    require(files, "MISSING_TRACE")
    totals = {}
    receipts = []
    sessions = set()
    events = 0
    incomplete = 0
    for path in files:
        require(path.name != "git-trace2-discard", "TRACE_DISCARDED")
        raw = read(path)
        receipts.append(sha(raw))
        require(raw.endswith(b"\n"), "TRACE_TRUNCATED")
        sid = None
        name = None
        start = False
        exit_event = None
        atexit = None
        version = False
        for line in raw.splitlines():
            events += 1
            require(events <= MAX_EVENTS and len(line) <= MAX_LINE, "EVENT_LIMIT")
            e = json.loads(line)
            require(isinstance(e, dict) and isinstance(e.get("sid"), str)
                    and 0 < len(e["sid"]) <= 1024, "TRACE_IDENTITY")
            sid = sid or e["sid"]
            require(e["sid"] == sid, "MIXED_TRACE_SESSION")
            kind = e.get("event")
            require(isinstance(kind, str), "TRACE_EVENT")
            require(atexit is None and (version or kind == "version"), "TRACE_ORDER")
            if kind == "version":
                require(not version and events >= 1, "DUPLICATE_VERSION")
                version = True
            elif kind == "start":
                require(version and not start, "DUPLICATE_START")
                start = True
            elif kind == "cmd_name":
                require(start and name is None and isinstance(e.get("name"), str), "TRACE_COMMAND")
                name = e["name"] if e["name"] in SAFE_OPS else "OTHER"
            elif kind in {"exit", "atexit"}:
                require(start and (kind == "exit" or exit_event is not None), "TRACE_ORDER")
                value = (number(e.get("t_abs")), e.get("code"))
                require(type(value[1]) is int, "TRACE_EXIT_CODE")
                if kind == "exit":
                    require(exit_event is None, "DUPLICATE_EXIT")
                    exit_event = value
                else:
                    require(atexit is None, "DUPLICATE_ATEXIT")
                    atexit = value
            elif kind == "too_many_files":
                raise RuntimeError("TRACE_DISCARDED")
        require(version and start and sid not in sessions, "TRACE_LIFECYCLE")
        sessions.add(sid)
        op = name or "UNKNOWN"
        row = totals.setdefault(op, {"started": 0, "completed": 0, "nonzero": 0,
                                     "incomplete": 0, "git_seconds_sum": 0.0,
                                     "git_seconds_max": 0.0})
        row["started"] += 1
        if exit_event is None or atexit is None or name is None:
            require(allow_incomplete, "TRACE_INCOMPLETE")
            incomplete += 1
            row["incomplete"] += 1
        else:
            require(atexit[0] >= exit_event[0] and atexit[1] == exit_event[1], "TRACE_EXIT_MISMATCH")
            row["completed"] += 1
            row["nonzero"] += int(exit_event[1] != 0)
            row["git_seconds_sum"] += exit_event[0]
            row["git_seconds_max"] = max(row["git_seconds_max"], exit_event[0])
    return {"process_files": len(files), "events": events, "incomplete": incomplete,
            "operations": totals, "raw_trace_sha256_multiset": sorted(receipts),
            "timing_basis": "Git exit t_abs; overlapping processes may double count"}


def cleanup(proc, sink):
    """Only a still-live Popen root; failure remains UNCERTAIN, no next single."""
    state = "UNCERTAIN"
    if proc.poll() is None:
        try:
            if sys.platform == "win32":
                killed = subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                                        stdout=sink, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL, timeout=30, check=False)
                if killed.returncode == 0:
                    state = "TREE_TERMINATED"
        except (OSError, subprocess.TimeoutExpired):
            state = "UNCERTAIN"
        finally:
            try:
                if proc.poll() is None:
                    proc.kill()  # retained Popen handle, root only
                proc.wait(timeout=30)
            except (OSError, subprocess.TimeoutExpired):
                state = "UNCERTAIN"
    return state


def original_process(command, cwd, folder):
    """External whole-child monotonic timing. Original P234 child and 180s wait."""
    process = {"timed_out": False, "tree_cleanup": "NOT_NEEDED"}
    with (folder / "single-0.log").open("wb") as sink:
        began = time.monotonic()
        proc = subprocess.Popen(command, cwd=cwd, env=os.environ.copy(),
                                stdin=subprocess.DEVNULL, stdout=sink, stderr=subprocess.STDOUT)
        spawned = time.monotonic()
        try:
            proc.wait(timeout=SECONDS)
        except subprocess.TimeoutExpired:
            process["timed_out"] = True
            process["deadline_observed_seconds"] = time.monotonic() - began
            process["wait_observed_seconds"] = time.monotonic() - began
            process["tree_cleanup"] = cleanup(proc, sink)
        else:
            process["wait_observed_seconds"] = time.monotonic() - began
        ended = time.monotonic()
    try:
        log_sha = sha(read(folder / "single-0.log"))
    except (OSError, RuntimeError):
        log_sha = None
    process.update(actual_process_exit=proc.returncode,
                   diagnostic_exit=124 if process["timed_out"] else proc.returncode,
                   spawn_seconds=spawned - began, whole_child_seconds=ended - began,
                   cleanup_seconds=ended - began - process["wait_observed_seconds"],
                   configured_wait_seconds=SECONDS, raw_log="single-0.log",
                   raw_log_sha256=log_sha, log_receipt_error=log_sha is None,
                   log_streams="original stdout and stderr combined, including cleanup")
    return process


def worker(args):
    # Not a public arbitrary-command surface. Supervisor fixes phase, source, output.
    p234 = load_p234()
    folder = args.output
    if args.phase == "verify":
        began = time.monotonic()
        source = p234.verify_source(args.source)
        write(folder / "source-witness.json", source)
        write(folder / "worker.json", {"verification_seconds": time.monotonic() - began,
                                      "source_witness_raw_sha256": sha(canonical(source))})
        return 0
    if args.phase == "probe":
        result = subprocess.run(["git", "version"], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        write(folder / "worker.json", {"native_exit": result.returncode,
                                      "stdout_sha256": sha(result.stdout),
                                      "stderr_sha256": sha(result.stderr)})
        return result.returncode
    command = [sys.executable, "-B", str(Path(p234.__file__).resolve()), "single",
               "--source", str(args.source), "--output", str(folder / "single-0.json"),
               "--test-id", TEST]
    process = original_process(command, args.source, folder)
    write(folder / "worker.json", process)
    return 0  # transport receipt only; supervisor classifies original, always HOLD


def supervised(phase, source, folder, trace, budget):
    """Bound an independent runner; no source/test imports in supervisor."""
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "_worker",
               "--phase", phase, "--source", str(source), "--output", str(folder)]
    aborted = None
    state = "NOT_NEEDED"
    with (folder / "runner.stdout").open("wb") as out, (folder / "runner.stderr").open("wb") as err:
        began = time.monotonic()
        proc = subprocess.Popen(command, cwd=source, env=clean_env(trace),
                                stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        try:
            while proc.poll() is None:
                inventory(folder)
                if trace is not None:
                    inventory(trace)
                require(time.monotonic() - began <= budget, "RUNNER_BUDGET")
                time.sleep(0.5)
        except Exception:
            aborted = "RUNNER_ABORTED_RESOURCE_OR_OBSERVER_ERROR"
            state = cleanup(proc, err)
        elapsed = time.monotonic() - began
    try:
        stdout_sha = sha(read(folder / "runner.stdout"))
        stderr_sha = sha(read(folder / "runner.stderr"))
    except (OSError, RuntimeError):
        stdout_sha = stderr_sha = None
        aborted = "RUNNER_LOG_RECEIPT_REFUSED"
    report = {"runner_native_exit": proc.returncode, "runner_elapsed_seconds": elapsed,
              "runner_cleanup": state, "aborted": aborted,
              "runner_stdout_sha256": stdout_sha,
              "runner_stderr_sha256": stderr_sha}
    return report


def finish_code(status, diagnostic=0):
    if diagnostic:
        return diagnostic
    return HOLD if status == "PASS" else 125


def observe(args):
    root = Path(__file__).resolve().parents[1]
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    require(not output.is_relative_to(root) and not output.is_relative_to(source)
            and not source.is_relative_to(root) and not root.is_relative_to(source), "PATH_SEPARATION")
    output.mkdir(parents=False, exist_ok=False)  # no reuse, including previous failure
    report = {"schema": "P237-v1", "release": "HOLD", "scope": "OBSERVATION ONLY",
              "run_id": os.getenv("GITHUB_RUN_ID"), "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
              "test_id": TEST, "source_head": SOURCE, "observer_exit": 125,
              "child_source_preflight_seconds": None,
              "child_source_preflight_note": "UNKNOWN: unchanged child has no timing boundary",
              "independent_review": "PENDING", "full_unfiltered_regressions": "0/3"}
    try:
        report["stage"] = "CONTROLLER_PROVENANCE"
        report["controller"] = controller_provenance(root)
        require(Path(os.environ["RUNNER_TEMP"]).resolve().is_dir(), "RUNNER_TEMP")
        # Private raw data is never globbed into upload-artifact. No recursive deletion.
        private = Path(tempfile.mkdtemp(prefix="p237-private-", dir=os.environ["RUNNER_TEMP"])).resolve()
        require(not private.is_relative_to(root) and not private.is_relative_to(source)
                and not output.is_relative_to(private), "PRIVATE_SEPARATION")
        folders = {}
        for phase in ("verify", "probe", "single"):
            report["stage"] = phase.upper()
            folder = private / phase
            folder.mkdir()
            trace = None
            if phase in {"probe", "single"}:
                trace = private / (phase + "-trace")
                trace.mkdir()  # Git requires an already-existing absolute directory
            folders[phase] = folder
            transport = supervised(phase, source, folder, trace, 270 if phase == "single" else 150)
            report[phase + "_runner"] = transport
            require(not transport["aborted"] and transport["runner_native_exit"] == 0, "RUNNER_FAILED")
            received = json.loads(read(folder / "worker.json"))
            report[phase] = received
            if phase == "verify":
                witness_raw = read(folder / "source-witness.json")
                witness = json.loads(witness_raw)
                require(witness["head"] == SOURCE and sha(witness_raw)
                        == received["source_witness_raw_sha256"], "WITNESS_MISMATCH")
                # Original verifier output: only public repo-relative source paths/tag pins.
                (output / "source-witness.json").write_bytes(witness_raw)
            elif phase == "probe":
                report["trace_probe"] = trace_summary(trace)
                require(received["native_exit"] == 0
                        and report["trace_probe"]["process_files"] == 1
                        and set(report["trace_probe"]["operations"]) == {"version"}, "TRACE_PROBE_FAILED")
            else:
                p234 = load_p234()  # unchanged classification only, no test source imports
                require(not received.get("log_receipt_error", False), "ORIGINAL_LOG_RECEIPT_REFUSED")
                result_file = folder / "single-0.json"
                result = json.loads(read(result_file)) if result_file.exists() else None
                event_file = folder / "single-0.events.jsonl"
                events = [json.loads(row) for row in read(event_file).splitlines()] if event_file.exists() else []
                report["journal_raw_sha256"] = sha(read(event_file)) if event_file.exists() else None
                report["result_raw_sha256"] = sha(read(result_file)) if result_file.exists() else None
                summary, code = p234.classify(received, result, events, TEST)
                report["original"] = summary
                report["original_diagnostic_exit"] = code
                report["git"] = trace_summary(trace, allow_incomplete=received["timed_out"])
                require(report["git"]["process_files"] > 1, "INSUFFICIENT_CHILD_TRACE")
                report["observer_exit"] = finish_code(summary["status"], code)
        # Authenticate unchanged source again in another bounded process, no trace pollution.
        report["stage"] = "POSTVERIFY"
        post = private / "postverify"
        post.mkdir()
        report["postverify_runner"] = supervised("verify", source, post, None, 150)
        require(report["postverify_runner"]["runner_native_exit"] == 0
                and not report["postverify_runner"]["aborted"], "POSTVERIFY_FAILED")
        require(read(post / "source-witness.json") == read(folders["verify"] / "source-witness.json"),
                "SOURCE_CHANGED")
        require(controller_provenance(root) == report["controller"], "CONTROLLER_CHANGED")
        report["stage"] = "COMPLETE_OBSERVATION_RELEASE_STILL_HELD"
    except Exception:
        # Never publish raw traceback/exception text (may include argv, paths or credentials).
        report.update(observer_exit=125, observation_error="PROVENANCE_INSTRUMENTATION_OR_RESULT_REFUSED")
    finally:
        write(output / "observation.json", report)
        write(output / "receipts.json", {p.name: sha(read(p)) for p in sorted(output.iterdir())
                                         if p.name != "receipts.json"})
        print(json.dumps({"scope": "OBSERVATION ONLY", "release": "HOLD",
                          "observer_exit": report["observer_exit"]}))
    return report["observer_exit"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("observe", "_worker"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--phase", choices=("verify", "probe", "single"))
    args = parser.parse_args()
    if args.mode == "_worker":
        require(args.phase is not None, "WORKER_PHASE")
        return worker(args)
    return observe(args)


if __name__ == "__main__":
    raise SystemExit(main())
