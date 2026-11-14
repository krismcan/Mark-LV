"""P225: source-linked Windows diagnosis of P224 timed-out original tests.

P224 full suite: 600-second timeout; no unittest footer; the original raw
test log recorded 46 FAIL, 10 ERROR and stopped inside BYOK-B. P225 executes
SEVEN isolated *unchanged* tests, each in its own disposable native Windows
child process, with 12-second faulthandler dumps and bounded total lifetimes.
An observed failing original test is NOT reclassified as a passing test.

Does not alter source, Git refs, installed service, native Windows policy,
live credentials, or any protected production state.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

BRANCH = "byok-c1-p225-windows-historical-stall-root-cause-20261114"
PARENT = "43c77651a062a114ded9706a1b5a3731a1d3eed9"
HISTORICAL_BYOK = (
    "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests."
    "test_frozen_commit_index_and_disk_stay_bound"
)
TESTS = (
    ("byok-b-stalled-original", HISTORICAL_BYOK, 65),
    ("p132-frozen-source-admission",
     "tests.test_p132_user_scope_migration.P132ExplicitConsumerMigration."
     "test_direct_p131_ancestry_and_exact_six_new_paths", 32),
    ("native-windows-temporary-file",
     "tests.test_file_creation.NativeCreationTests."
     "test_creates_only_one_self_owned_empty_temporary_file", 32),
    ("p166-exact-source-class-setup",
     "tests.test_p166_current_branch_acceptance.P166RealCurrentBranchAcceptanceTests."
     "test_positive_live_windows_head_tree_and_19_original_security_sources", 32),
    ("p210-native-binary-class-setup",
     "tests.test_p210_python_native_synthetic_integration."
     "P210OriginalPythonNativeBoundaryTests."
     "test_01_missing_owner_denied", 32),
    ("p213-signature-class-setup",
     "tests.test_p213_real_windows_authenticode_service_admission."
     "P213GenuineWindowsSignerReviewTests."
     "test_01_all_nayeon_signer_release_and_code_policy_pins_absent", 32),
    ("phase10-2-literal-source-gate",
     "tests.test_phase10_2_privacy_scope_integrity.NativeExactSourceAdmissionTests."
     "test_real_complete_source_live_admission", 32),
)
RUNNER_ONLY = ("GITHUB_ACTIONS", "RUNNER_OS", "GITHUB_EVENT_NAME",
               "GITHUB_REPOSITORY", "GITHUB_REF_NAME", "GITHUB_SHA",
               "RUNNER_TEMP")
DENY_ENV = ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN",
            "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
            "P134_NATIVE_WINCRED_EPHEMERAL_AUTH")
EMBEDDED = (
    "import faulthandler,sys,unittest;"
    "faulthandler.enable();"
    "faulthandler.dump_traceback_later(12,repeat=True,file=sys.stderr);"
    "s=unittest.defaultTestLoader.loadTestsFromName(sys.argv[1]);"
    "r=unittest.TextTestRunner(verbosity=2).run(s);"
    "faulthandler.cancel_dump_traceback_later();"
    "sys.exit(0 if r.wasSuccessful() and r.testsRun==1 else 1)"
)
OUTCOME = re.compile(r"(?m)^(?:test_[^\r\n]* \.\.\. (?:ok|FAIL|ERROR|skipped .*)|setUpClass \([^\r\n]*\) \.\.\. ERROR)$")
FAIL = re.compile(r"(?m)^FAIL: ([^\r\n]+)")
ERROR = re.compile(r"(?m)^ERROR: ([^\r\n]+)")
STACK = re.compile(r"Timeout \(0:00:12\)!")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def git(root: Path, *argv: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *argv], stdin=subprocess.DEVNULL,
        capture_output=True, check=False, timeout=25,
    )
    if completed.returncode:
        raise RuntimeError("P225 Git source integrity refusal")
    return completed.stdout.decode("utf-8", "replace").strip()


def guard(root: Path) -> dict:
    if (
        sys.platform != "win32"
        or any(not os.getenv(k) for k in RUNNER_ONLY)
        or os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("RUNNER_OS") != "Windows"
        or os.environ.get("GITHUB_EVENT_NAME") != "push"
        or os.environ.get("GITHUB_REPOSITORY") != "krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME") != BRANCH
    ):
        raise RuntimeError("P225 only genuine ephemeral GitHub Windows exact branch")
    head = git(root, "rev-parse", "HEAD")
    if head != os.environ["GITHUB_SHA"] or (
        git(root, "merge-base", PARENT, head) != PARENT
    ):
        raise RuntimeError("P225 original source parent / actual SHA mismatch")
    expected = {
        ".github/workflows/p225-windows-bounded-stall-root-cause.yml",
        "docs/byok-c1-p225-windows-stall-and-error-isolation.md",
        "scripts/p225_windows_original_failure_isolation.py",
    }
    actual = set(git(root, "diff", "--name-only", PARENT, head).splitlines())
    if actual != expected:
        raise RuntimeError("P225 changed original product/test source or unexpected path")
    for source in (
        "tests/test_phase8_byok_b_scope_integrity.py",
        "tests/phase8_byok_b_scope_migration.py",
        "tests/test_file_creation.py",
        "tests/test_p132_user_scope_migration.py",
        "tests/test_p166_current_branch_acceptance.py",
        "tests/test_p210_python_native_synthetic_integration.py",
        "tests/test_p213_real_windows_authenticode_service_admission.py",
        "tests/test_phase10_2_privacy_scope_integrity.py",
        "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs",
        "tests/p95_native_custody_preflight/CustodyLedger.cs",
    ):
        if git(root, "rev-parse", "HEAD:" + source) != git(
            root, "rev-parse", PARENT + ":" + source
        ):
            raise RuntimeError("P225 frozen original test or security source drift")
    if git(root, "status", "--porcelain=v1"):
        raise RuntimeError("P225 initial source workspace not pristine")
    return {"head": head, "base": PARENT,
            "original_source_and_test_bytes": "verified identical"}


def single(root: Path, out: Path, index: int, name: str, test: str,
           seconds: int) -> dict:
    if not re.fullmatch(r"[a-z0-9-]{1,60}", name):
        raise RuntimeError("P225 invalid diagnostic case")
    env = os.environ.copy()
    for key in DENY_ENV:
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    path = out / (str(index).zfill(2) + "-" + name + ".log")
    started = time.monotonic()
    timed_out = False
    code = 125
    # P225 only invokes original test names from the hardcoded allowlist.
    args = [sys.executable, "-B", "-c", EMBEDDED, test]
    with path.open("wb") as writer:
        try:
            proc = subprocess.Popen(
                args, cwd=root, env=env, stdin=subprocess.DEVNULL,
                stdout=writer, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except OSError:
            proc = None
        if proc is not None:
            try:
                code = proc.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                code = 124
                # Terminate ONLY this spawned ephemeral diagnostic child tree.
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=9,
                               check=False)
                try:
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=4)
    raw = path.read_bytes()
    transcript = raw.decode("utf8", "replace")
    match = re.findall(r"Ran (\d+) tests? in [\d.]+s", transcript)
    frames = [
        line.strip()[:240] for line in transcript.splitlines()
        if line.lstrip().startswith('File "') and (
            "phase8_byok_b" in line or "subprocess.py" in line
            or "phase_8_" in line or "test_" in line)
    ]
    record = {
        "name": name, "original_test_id": test,
        "native_exit": code, "timed_out": timed_out,
        "seconds": round(time.monotonic()-started, 2),
        "raw_log": path.name, "raw_log_sha256": sha(raw),
        "raw_log_bytes": len(raw),
        "unittest_reported_count": int(match[-1]) if match else None,
        "in_stream_outcome_count": len(OUTCOME.findall(transcript)),
        "failure_traceback_names": FAIL.findall(transcript)[:8],
        "error_traceback_names": ERROR.findall(transcript)[:8],
        "faulthandler_12s_dumps": len(STACK.findall(transcript)),
        "stack_frames_tail": frames[-12:],
        "summary": (
            "SINGLE_ORIGINAL_TEST_PASS_ONLY_NOT_RELEASE"
            if code == 0 and not timed_out and len(match) == 1
            else "ORIGINAL_TIMEOUT_UNRESOLVED"
            if timed_out else "ORIGINAL_FAILED_OR_ENVIRONMENT_REFUSED"
        ),
    }
    print("P225_CASE=" + name
          + "|ORIGINAL_EXIT=" + str(code)
          + "|TIMEOUT=" + str(timed_out).upper()
          + "|STACK_DUMPS=" + str(record["faulthandler_12s_dumps"])
          + "|LOG_SHA256=" + record["raw_log_sha256"], flush=True)
    return record


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = guard(root)
    out = Path(os.environ["RUNNER_TEMP"]) / "p225-original-Windows-failure-evidence"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for i, (name, test, seconds) in enumerate(TESTS, 1):
        records.append(single(root, out, i, name, test, seconds))
    source["records"] = records
    source["original_test_files_edited"] = False
    source["real_keys_or_providers"] = False
    source["original_P96_race"] = "OPEN"
    source["g0_r3_independent_review"] = "NOT_RECEIVED"
    source["full_unfiltered_windows_regression_passes"] = "0/3"
    source["real_key_gate"] = "NO_GO"
    source["production_release"] = "HOLD"
    source["diagnosis_not_release"] = True
    path = out / "p225-isolation-manifest.json"
    path.write_text(json.dumps(source, sort_keys=True, indent=2), encoding="utf8")
    receipt = out / "p225-evidence-sha256.txt"
    for f in sorted(out.glob("*")):
        if f.is_file() and f != receipt:
            with receipt.open("a", encoding="ascii") as stream:
                stream.write(sha(f.read_bytes())+"  "+f.name+"\n")
    print("P225_ORIGINAL_SEVEN_WINDOWS_CASES_OBSERVED="+str(len(records)))
    print("P225_ORIGINAL_SOURCE_AND_TEST_ASSERTIONS_UNCHANGED=TRUE")
    print("P225_FAILING_OR_TIMED_OUT_TESTS_NOT_WAIVED=TRUE")
    print("P225_FULL_UNFILTERED_WINDOWS=0/3|REALKEY=NO_GO|PRODUCTION=HOLD")
    # An isolated failed original test still provides valid evidence; emit
    # success only for a complete, source-bound, seven-case diagnosis.
    return 0 if len(records) == len(TESTS) and all(
        item["raw_log_bytes"] > 0 for item in records
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
