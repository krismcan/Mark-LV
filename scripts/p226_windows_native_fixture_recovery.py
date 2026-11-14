"""P226: genuine hosted-Windows recovery of UNCHANGED native filesystem,
P210 Python/native and P213 Authenticode original tests.

Diagnostic/test provisioning only. No real key, production service,
privileged installation or security-assertion changes. A clean diagnostic
collector is not a full product regression or a production approval.
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
import traceback

P225 = "0da53ded42e0bdccc057759883f09404ad978935"
BRANCH = "byok-c1-p226-windows-native-regression-recovery-20261114"
P96_SHA256 = "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB"
P95_SHA256 = "93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B"
ROOT = Path(__file__).resolve().parents[1]
ADDED = {
    "scripts/p226_windows_native_fixture_recovery.py",
    ".github/workflows/p226-windows-native-fixture-recovery.yml",
}
FROZEN = (
    "scripts/p139_native_fs_verified_local_temp_root.py",
    "scripts/p210_windows_python_native_synthetic_integration.py",
    "scripts/p213_windows_signed_service_observation.py",
    "tests/test_file_creation.py",
    "tests/test_directory_creation.py",
    "tests/test_directory_deletion.py",
    "tests/test_directory_listing.py",
    "tests/test_file_copy.py",
    "tests/test_file_deletion.py",
    "tests/test_filesystem.py",
    "tests/test_p210_python_native_synthetic_integration.py",
    "tests/test_p213_real_windows_authenticode_service_admission.py",
    "native_c1_candidate/P210SyntheticBoundaryExecutable.cs",
    "native_c1_candidate/P213NativeWintrustObservation.cs",
    "native_c1_candidate/CustodyService.cs",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs",
    "tests/p95_native_custody_preflight/CustodyLedger.cs",
)
SECRET_ENV = (
    "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "P134_NATIVE_WINCRED_EPHEMERAL_AUTH",
)
RAN = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
OK = re.compile(r"(?m)^OK\s*$")

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        stdin=subprocess.DEVNULL, capture_output=True, check=False, timeout=25,
    )
    if proc.returncode:
        raise RuntimeError("P226 authentic Git source identity command refused: " + args[0])
    return proc.stdout.decode("utf8", "strict").strip()

def verify_source() -> dict:
    expected = {
        "GITHUB_ACTIONS": "true",
        "RUNNER_OS": "Windows",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REPOSITORY": "krismcan/Mark-LV",
        "GITHUB_REF_NAME": BRANCH,
    }
    if sys.platform != "win32" or any(os.getenv(k) != v for k, v in expected.items()):
        raise RuntimeError("P226 requires real hosted Windows on exact push branch")
    if not os.getenv("RUNNER_TEMP") or not os.getenv("GITHUB_SHA"):
        raise RuntimeError("P226 Windows source event identity absent")
    head = git("rev-parse", "HEAD")
    if head != os.environ["GITHUB_SHA"] or git("merge-base", P225, head) != P225:
        raise RuntimeError("P226 exact P225 ancestry/HEAD refused")
    if set(git("diff", "--name-only", P225, head).splitlines()) != ADDED:
        raise RuntimeError("P226 unexpected source or security-test delta")
    if git("status", "--porcelain=v1", "-uall"):
        raise RuntimeError("P226 original source checkout dirty")
    observed = {}
    for path in FROZEN:
        current = git("rev-parse", "HEAD:" + path)
        if current != git("rev-parse", P225 + ":" + path):
            raise RuntimeError("P226 frozen Git blob changed: " + path)
        data = (ROOT / path).read_bytes()
        old = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + path],
                             capture_output=True, timeout=25, check=True).stdout
        if data != old:
            raise RuntimeError("P226 frozen working disk vs original Git bytes differ: " + path)
        observed[path] = {"git_blob": current, "sha256": sha(data)}
    if observed["tests/p96_native_transaction_negative/PendingCustodyTransaction.cs"]["sha256"] != P96_SHA256:
        raise RuntimeError("P226 original P96 native SHA256 drift")
    if observed["tests/p95_native_custody_preflight/CustodyLedger.cs"]["sha256"] != P95_SHA256:
        raise RuntimeError("P226 original P95 native SHA256 drift")
    return {"source_head": head, "p225_ancestor": P225,
            "frozen_original_paths": observed, "additive_only": sorted(ADDED)}

def run_test(label: str, argv: list[str], seconds: int,
             output: Path, env: dict[str, str], expected: int | None) -> dict:
    started = time.monotonic()
    log = output / (label + ".log")
    timeout = False
    code = 125
    with log.open("wb") as stream:
        try:
            proc = subprocess.run(
                [sys.executable, "-B", *argv], cwd=ROOT, env=env,
                stdin=subprocess.DEVNULL, stdout=stream,
                stderr=subprocess.STDOUT, timeout=seconds, check=False,
            )
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code, timeout = 124, True
        except OSError:
            code = 125
    raw = log.read_bytes()
    printed = raw.decode("utf8", "replace")
    counts = [int(x) for x in RAN.findall(printed)]
    passed = code == 0 and not timeout and (
        (counts[-1] == expected and bool(OK.search(printed)))
        if expected is not None
        else all("P139_ORIGINAL_NATIVE_FILESYSTEM_CASES_PASS=7" in printed
                 for _ in (0,)) and "P139_ORIGINAL_NATIVE_FILESYSTEM_CASES_HOLD=0" in printed
    )
    row = {"label": label, "native_exit": code, "timeout": timeout,
           "elapsed_seconds": round(time.monotonic() - started, 3),
           "raw_log": log.name, "raw_log_sha256": sha(raw),
           "raw_log_bytes": len(raw),
           "original_unittest_count": counts[-1] if counts else None,
           "original_test_pass": passed}
    print("P226_CASE=" + label + "|NATIVE_EXIT=" + str(code)
          + "|ORIGINAL_PASS=" + str(passed).upper()
          + "|LOG_SHA256=" + row["raw_log_sha256"], flush=True)
    return row

def main() -> int:
    output = Path(os.environ["RUNNER_TEMP"]) / "p226-original-Windows-fixture-recovery"
    output.mkdir(parents=True, exist_ok=True)
    ledger = {
        "P226": "ORIGINAL_NATIVE_WINDOWS_REGRESSION_RECOVERY_ONLY",
        "real_key": "NO_GO", "production": "HOLD",
        "full_unfiltered_windows_regressions": "0/3",
        "independent_security_reviews": "0/7",
        "P96_production_effect_race": "OPEN",
        "original_tests_modified": False,
        "real_WinCred_or_provider_effect": "NONE",
        "records": [],
    }
    complete = False
    try:
        before = verify_source()
        ledger["verified_before"] = before
        env = os.environ.copy()
        for key in SECRET_ENV:
            env.pop(key, None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # Existing P139 performs the genuine strict Win32 handle check on
        # C:\NayeonP139_<random>, runs seven untouched original tests with
        # TEMP/TMP/TMPDIR set only in their own children, and cleans cautiously.
        ledger["records"].append(run_test(
            "P139-seven-unchanged-native-filesystem",
            ["-m", "scripts.p139_native_fs_verified_local_temp_root"],
            420, output, env, None,
        ))
        for log in sorted((Path(os.environ["RUNNER_TEMP"]) /
                           "nayeon-p139-safe-root-regression").glob("*.log")):
            raw = log.read_bytes()
            ledger.setdefault("P139_original_per_case_logs", {})[log.name] = {
                "sha256": sha(raw), "bytes": len(raw),
            }
        # Only the existing source-custodied, C1_SYNTHETIC_TEST-only original
        # compiler entrypoint; no signed C1 service is built or installed.
        from scripts.p210_windows_python_native_synthetic_integration import (
            compile_native_bridge,
        )
        bridge = compile_native_bridge(output)
        ledger["original_P210_native_compiler"] = bridge
        env["P210_NATIVE_EXE"] = bridge["path"]
        ledger["records"].append(run_test(
            "P210-thirteen-original-python-native-negative-tests",
            ["-m", "unittest", "-v",
             "tests.test_p210_python_native_synthetic_integration."
             "P210OriginalPythonNativeBoundaryTests"],
            180, output, env, 13,
        ))
        # P213 requires TWO originals: P210's unsigned synthetic test
        # binary AND a separate read-only P116 WinVerifyTrust test assembly.
        # Its original compiler verifies every original P116 source blob
        # against frozen P212, and does not sign/install/elevate anything.
        from scripts.p213_windows_signed_service_observation import (
            compile_native_wintrust_probe,
        )
        wintrust = compile_native_wintrust_probe(output)
        ledger["original_P213_P116_native_wintrust_compiler"] = wintrust
        env["P213_NATIVE_WINTRUST_EXE"] = wintrust["exe"]
        ledger["records"].append(run_test(
            "P213-twenty-original-Windows-Authenticode-review-tests",
            ["-m", "unittest", "-v",
             "tests.test_p213_real_windows_authenticode_service_admission."
             "P213GenuineWindowsSignerReviewTests"],
            180, output, env, 20,
        ))
        ledger["verified_after"] = verify_source()
        if ledger["verified_before"] != ledger["verified_after"]:
            raise RuntimeError("P226 verified source identity changed during tests")
        complete = all(x["original_test_pass"] for x in ledger["records"])
    except BaseException as exc:
        ledger["error"] = type(exc).__name__ + ": " + str(exc)
        ledger["error_traceback"] = traceback.format_exc()[-3000:]
        print("P226_ORIGINAL_NATIVE_RECOVERY_HOLD=" + type(exc).__name__, flush=True)
    finally:
        ledger["all_original_selected_tests_passed"] = complete
        ledger["diagnostic_not_full_product_pass"] = True
        ledger["real_key"] = "NO_GO"
        ledger["production"] = "HOLD"
        receipt_path = output / "p226-original-native-evidence.json"
        receipt_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n",
                                encoding="utf8")
        with (output / "p226-original-sha256-receipts.txt").open("w", encoding="ascii") as receipt:
            for path in sorted(output.glob("*")):
                if path.is_file() and path.name != "p226-original-sha256-receipts.txt":
                    receipt.write(sha(path.read_bytes()) + "  " + path.name + "\n")
        print("P226_FOCUSED_ORIGINAL_TEST_PASS_RESULTS="
              + str(sum(x["original_test_pass"] for x in ledger["records"]))
              + "/" + str(len(ledger["records"])), flush=True)
        print("P226_FULL_UNFILTERED_WINDOWS=0/3|REAL_KEY=NO_GO|PRODUCTION=HOLD", flush=True)
    return 0 if complete else 1

if __name__ == "__main__":
    raise SystemExit(main())
