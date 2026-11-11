"""P161 diagnostic only: measure genuine original Phase8.37 Git subprocess calls.

Only the external diagnostic process wraps subprocess.check_output to record
timing; original tests, security readers, Git bytes and exceptions are unchanged.
A green collector is never an original test, regression or production GO.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import time
import uuid

from scripts.p139_native_fs_verified_local_temp_root import _guard_runner, _verify_original_handle_policy

ROOT = Path(__file__).resolve().parents[1]
BASE = "725181149b7bb3f1002c9d36b7fc8e86c78020d7"
BRANCH = "byok-c1-p161-windows-historical-git-call-latency-20261111"
SOURCE_TEST = "tests/test_phase_837_scope_integrity.py"
SOURCE_SHA256 = "A95A967BA892FECADF0811B38C51AE61CD268159766A91B1DC448CF4B1B5C426"
TEST_ID = ("tests.test_phase_837_scope_integrity.Phase837IntegrityTests."
           "test_every_original_836_pin_is_rechecked_including_normalized_self")
EXPECTED_TRACKED = 170
CAP_SECONDS = 105
DENIED_ENV = (
    "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "NAYEON_INTERNAL_SECRET",
    "P161_EVIDENCE_TOKEN",
)
RAN = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
OK = re.compile(r"^OK\s*$", re.M)
FAILED = re.compile(r"^FAILED \(([^)]+)\)\s*$", re.M)
ISSUES = re.compile(r"^(FAIL|ERROR): ([^\r\n]+)", re.M)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL, timeout=25,
    )
    return result.stdout.decode("utf8", "replace").strip()


def require_source() -> str:
    _guard_runner()
    if (os.environ.get("GITHUB_ACTIONS") != "true" or
        os.environ.get("RUNNER_OS") != "Windows" or
        os.environ.get("GITHUB_REF_NAME") != BRANCH):
        raise RuntimeError("P161 only runs on exact hosted Windows branch")
    head = git("rev-parse", "HEAD")
    if (head != os.environ.get("GITHUB_SHA") or
        git("merge-base", BASE, head) != BASE):
        raise RuntimeError("P161 exact P160 base/HEAD mismatch")
    if git("status", "--porcelain=v1"):
        raise RuntimeError("P161 source was not clean")
    tracked = [x for x in git("ls-files", "tests/test_*.py").splitlines()
               if x.startswith("tests/test_") and x.endswith(".py")]
    if len(tracked) != EXPECTED_TRACKED or "tests/test_p158_versioned_connection_ui_contract.py" not in tracked:
        raise RuntimeError("P161 exact source module inventory drift")
    raw = (ROOT / SOURCE_TEST).read_bytes()
    if digest(raw) != SOURCE_SHA256 or git("rev-parse", "HEAD:" + SOURCE_TEST) != git("rev-parse", BASE + ":" + SOURCE_TEST):
        raise RuntimeError("P161 original Phase8.37 test bytes changed")
    tree = ast.parse(raw, filename=SOURCE_TEST)
    cls = [x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "Phase837IntegrityTests"]
    if len(cls) != 1 or len([x for x in cls[0].body if isinstance(x, ast.FunctionDef)
                            and x.name == "test_every_original_836_pin_is_rechecked_including_normalized_self"]) != 1:
        raise RuntimeError("P161 original exact method identity changed")
    historical = (
        "tests/phase_8_30_scope_migration.py",
        "tests/phase_8_32_scope_migration.py",
        "tests/phase_8_34_scope_migration.py",
        "tests/phase_8_36_scope_migration.py",
        "tests/phase_8_37_scope_migration.py",
        "scripts/p139_native_fs_verified_local_temp_root.py",
        "tests/test_phase8_byok_c1_p76_scope.py",
    )
    for path in historical:
        if git("rev-parse", "HEAD:" + path) != git("rev-parse", BASE + ":" + path):
            raise RuntimeError("P161 immutable original security source drift: " + path)
    print("P161_EXACT_P160_SOURCE_AND_170_TEST_MODULE_INVENTORY=PASS", flush=True)
    print("P161_HISTORICAL_PHASE837_ORIGINAL_SHA256_AND_SECURITY_BLOBS=PASS", flush=True)
    return head


def child_main():
    """Pure diagnostic process; delegate byte-identically to original check_output."""
    trace_path = Path(os.environ["P161_GIT_TRACE_PATH"])
    original = subprocess.check_output
    start = time.perf_counter_ns()
    serial = 0
    with trace_path.open("a", encoding="utf8", buffering=1) as trace:
        def observed(*args, **kwargs):
            nonlocal serial
            command = args[0] if args else kwargs.get("args", None)
            if not isinstance(command, (tuple, list)) or not command:
                return original(*args, **kwargs)
            argv = tuple(str(x) for x in command)
            if Path(argv[0]).name.lower() not in ("git", "git.exe"):
                return original(*args, **kwargs)
            serial += 1
            index = serial
            t0 = time.perf_counter_ns()
            output_size = None
            status = "returned"
            try:
                answer = original(*args, **kwargs)
                output_size = len(answer) if isinstance(answer, (bytes, str)) else None
                return answer
            except BaseException as exc:
                status = type(exc).__name__
                raise
            finally:
                # No raw git command arguments, absolute paths, source bytes,
                # stdout or secrets are placed in the trace.
                f = sys._getframe(1)
                frames = []
                for _ in range(12):
                    if f is None:
                        break
                    base = Path(f.f_code.co_filename).name
                    if base.startswith(("phase_8_", "test_phase_")):
                        frames.append(base + ":" + f.f_code.co_name)
                    f = f.f_back
                record = {
                    "index": index,
                    "start_ms": round((t0 - start) / 1e6, 3),
                    "duration_ms": round((time.perf_counter_ns() - t0) / 1e6, 3),
                    "verb": argv[1] if len(argv) > 1 else "none",
                    "arg_count": len(argv),
                    "command_fingerprint_sha256": digest("\x1f".join(argv).encode("utf8", "replace")),
                    "git_output_bytes": output_size,
                    "outcome": status,
                    "historical_call_chain": frames[:8],
                }
                try:
                    trace.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
                    trace.flush()
                except OSError:
                    # Never alter the original test's result due to telemetry.
                    pass

        subprocess.check_output = observed
        try:
            sys.argv = ["unittest", "-v", TEST_ID]
            runpy.run_module("unittest", run_name="__main__")
        finally:
            subprocess.check_output = original


def summarize_events(path: Path):
    items = []
    raw = path.read_bytes() if path.exists() else b""
    for line in raw.decode("utf8", "replace").splitlines():
        item = json.loads(line)
        if not isinstance(item, dict) or item.get("index") != len(items) + 1:
            raise RuntimeError("P161 Git-call sequence invalid")
        if item.get("verb") not in (
            "show", "rev-parse", "merge-base", "rev-list", "ls-tree",
            "ls-files", "cat-file", "show-ref", "diff", "branch", "status",
            "log", "for-each-ref", "symbolic-ref", "check-attr",
        ):
            raise RuntimeError("P161 unexpected observed Git verb " + str(item.get("verb")))
        items.append(item)
    if not items:
        raise RuntimeError("P161 captured zero actual native Git subprocess calls")
    if len(items) > 20000 or len(raw) > 12_000_000:
        raise RuntimeError("P161 diagnostic recording exceeds bounded size")
    totals = defaultdict(lambda: {"count": 0, "total_duration_ms": 0.0, "max_duration_ms": 0.0, "failed": 0})
    shapes = defaultdict(lambda: {"count": 0, "total_duration_ms": 0.0, "sample_call": None})
    for item in items:
        group = totals[item["verb"]]
        group["count"] += 1
        group["total_duration_ms"] += item["duration_ms"]
        group["max_duration_ms"] = max(group["max_duration_ms"], item["duration_ms"])
        group["failed"] += item["outcome"] != "returned"
        shape = shapes[item["command_fingerprint_sha256"]]
        shape["count"] += 1
        shape["total_duration_ms"] += item["duration_ms"]
        shape["sample_call"] = {"verb": item["verb"], "call_chain": item["historical_call_chain"]}
    return raw, items, totals, shapes


def parent_main():
    exact_head = require_source()
    out = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p161-actual-original-phase837-git-profile"
    out.mkdir(parents=True, exist_ok=True)
    host_raw = out / "p161_original_phase837_unittest.log"
    trace_file = out / "p161_original_phase837_git_calls.jsonl"
    temporary = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    made = False
    exit_code = None
    timed_out = False
    t0 = time.monotonic()
    try:
        if temporary.exists() or temporary.is_symlink():
            raise RuntimeError("P161 owned TEMP root already existed")
        os.mkdir(temporary)
        made = True
        _verify_original_handle_policy(str(temporary))
        print("P161_UNCHANGED_P139_NATIVE_WIN32_OPEN_HANDLE_POLICY=PASS", flush=True)
        own_temp = temporary / "p161_child"
        own_temp.mkdir(parents=True, exist_ok=False)
        env = os.environ.copy()
        for variable in DENIED_ENV:
            env.pop(variable, None)
        env.update({
            "TEMP": str(own_temp), "TMP": str(own_temp), "TMPDIR": str(own_temp),
            "PYTHONDONTWRITEBYTECODE": "1", "P161_GIT_TRACE_PATH": str(trace_file),
        })
        with host_raw.open("wb") as raw_output:
            child = subprocess.Popen(
                [sys.executable, "-B", "-m", "scripts.p161_windows_historical_git_call_profile", "--child"],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=raw_output, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            try:
                exit_code = child.wait(timeout=CAP_SECONDS)
            except subprocess.TimeoutExpired:
                timed_out = True
                exit_code = 124
                # Dispose only this owned GitHub-hosted test process tree.
                subprocess.run(
                    ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=15, check=False,
                )
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
    finally:
        if made:
            stat = temporary.lstat()
            if temporary.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                raise RuntimeError("P161 refuse unsafe filesystem cleanup")
            shutil.rmtree(temporary)
    elapsed = round(time.monotonic() - t0, 3)
    raw = host_raw.read_bytes()
    text = raw.decode("utf8", "replace").replace("\r\n", "\n")
    counts = RAN.findall(text)
    observed_count = int(counts[-1]) if counts else None
    issues = [{"kind": a, "original_test": b} for a,b in ISSUES.findall(text)]
    full_footer = observed_count == 1 and (bool(OK.search(text)) or bool(FAILED.search(text)))
    verdict = ("PASS" if exit_code == 0 and full_footer and OK.search(text) and not issues
               else "TIMEOUT" if exit_code == 124 and timed_out
               else "HOLD")
    trace_raw, events, totals, shapes = summarize_events(trace_file)
    if git("status", "--porcelain=v1"):
        raise RuntimeError("P161 historical checkout was changed by test")
    by_verb = {
        key: {
            "calls": value["count"],
            "total_duration_ms": round(value["total_duration_ms"], 3),
            "max_single_duration_ms": round(value["max_duration_ms"], 3),
            "exception_count": value["failed"],
        }
        for key,value in sorted(totals.items(), key=lambda x: -x[1]["total_duration_ms"])
    }
    repeated = [{
        "command_sha256": key,
        "count": value["count"],
        "cumulative_duration_ms": round(value["total_duration_ms"], 3),
        "verb": value["sample_call"]["verb"],
        "historical_call_chain_example": value["sample_call"]["call_chain"],
    } for key,value in sorted(shapes.items(), key=lambda x: -x[1]["total_duration_ms"])[:12]]
    slowest = sorted(events, key=lambda e: -e["duration_ms"])[:12]
    total_git_ms = round(sum(e["duration_ms"] for e in events), 3)
    ledger = {
        "checkpoint": "P161",
        "exact_verified_head_sha": exact_head,
        "exact_P160_parent_sha": BASE,
        "native_windows_source_test": TEST_ID,
        "historical_source_blob_unchanged": True,
        "historical_source_sha256": SOURCE_SHA256,
        "original_test_method_count_executed": observed_count,
        "original_full_unittest_footer": bool(full_footer),
        "native_windows_exit": exit_code,
        "timeout_seconds": CAP_SECONDS,
        "elapsed_seconds": elapsed,
        "original_unfiltered_test_disposition": verdict,
        "original_test_fail_error_records": issues,
        "git_call_count": len(events),
        "git_total_observed_duration_ms": total_git_ms,
        "git_total_observed_time_can_include_nested_calls": False,
        "distinct_hashed_git_command_shapes": len(shapes),
        "git_call_counts_and_durations_by_verb": by_verb,
        "repeated_top_git_call_shapes": repeated,
        "twelve_slowest_real_git_invocations": slowest,
        "stdout_stderr_sha256": digest(raw),
        "git_call_trace_sha256": digest(trace_raw),
        "stdout_stderr_bytes": len(raw),
        "git_call_trace_bytes": len(trace_raw),
        "instrumentation": "subprocess.check_output delegate, timing only, original return/exception untouched",
        "P139_original_native_open_handle_policy": "PASS",
        "P160_original_focused_isolation": "4 PASS / 1 TIMEOUT",
        "historical_original_module_P159": "1 HOLD / 5 TIMEOUT",
        "accepted_complete_full_product_windows_regressions": "0/3",
        "qualified_independent_security_and_test_governance": "NOT_OBTAINED",
        "original_P76_P85_branch_refusals": "UNCHANGED",
        "privileged_BYOK_C1_G0_to_G6": "OPEN",
        "production_release": "HOLD",
        "collector_success_does_not_mean_production_pass": True,
    }
    (out / "p161_native_original_phase837_git_latency_ledger.json").write_text(
        json.dumps(ledger, sort_keys=True, indent=2) + "\n", encoding="utf8",
    )
    print(
        "P161_NATIVE_ORIGINAL_PHASE837_EXIT=" + str(exit_code)
        + "|VERDICT=" + verdict
        + "|UNFILTERED_TEST_COUNT=" + str(observed_count)
        + "|SECONDS=" + str(elapsed)
        + "|REAL_GIT_CALLS=" + str(len(events))
        + "|GIT_TIME_MS=" + str(total_git_ms),
        flush=True,
    )
    for verb,v in list(by_verb.items())[:10]:
        print("P161_GIT_PROFILE_VERB=" + verb + "|COUNT=" + str(v["calls"])
              + "|TOTAL_MS=" + str(v["total_duration_ms"])
              + "|MAX_MS=" + str(v["max_single_duration_ms"]), flush=True)
    print("P161_REAL_GIT_TRACE_SHA256=" + digest(trace_raw), flush=True)
    print("P161_REAL_TEST_LOG_SHA256=" + digest(raw), flush=True)
    print("P161_HISTORICAL_SOURCE_AND_SECURITY_NEGATIVES=UNCHANGED", flush=True)
    print("P161_COMPLETE_PRODUCT_WINDOWS_TRIAD=0/3", flush=True)
    print("P161_PRODUCTION_RELEASE=HOLD", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(child_main() if sys.argv[1:] == ["--child"] else parent_main())
