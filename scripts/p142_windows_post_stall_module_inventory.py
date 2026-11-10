"""P142 — audit EVERY Python test module after the exact P135 stall point.

This is a DIAGNOSTIC inventory completion scan, not a release regression:
no original tests changed, no safety failures hidden, no signed package.
P135's authentic full unfiltered discovery timed out after 1,681 outcomes
at one frozen historical source-integrity test. P141's scoped triad passed,
but did not execute the remaining original Python modules. P142 records
every remaining module's actual native Windows exit and named test count.

Runs each existing original test MODULE (not filtered methods) in a separate
bounded Python subprocess. Timeouts, failures and errors stay HOLD. The
host is an ephemeral GitHub Windows runner only. No real API keys or
unapproved WinCred targets.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import time


ORIGINAL_STALL_MODULE = "tests/test_phase8_byok_b_scope_integrity.py"
P141_BASELINE = "bd2c0b7f5d74b2987c82b5802ea66a732d79faa4"
EXPECTED_TOTAL_MODULES = 169
EXPECTED_UNREACHED_MODULES = 83
MAX_MODULE_SECONDS = 35
WORKERS = 4
COUNT = re.compile(r"Ran (\d+) tests? in [\d.]+s")
END_OK = re.compile(r"^OK\s*$", re.MULTILINE)
BAD_TEST = re.compile(r"^(test_[^\r\n]+) \.\.\. (FAIL|ERROR)$", re.MULTILINE)


def _source_inventory(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--", "tests/test_*.py"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    rows = sorted(
        text.strip().replace("\\", "/") for text in result.stdout.splitlines()
        if text.strip()
    )
    if len(rows) != EXPECTED_TOTAL_MODULES or len(rows) != len(set(rows)):
        raise RuntimeError("Test inventory drift; do not silently accept missing cases")
    if rows.count(ORIGINAL_STALL_MODULE) != 1:
        raise RuntimeError("P135 exact stalled module absent")
    return rows


def _run_module(module_path: str, root: Path, output: Path) -> dict:
    name = module_path.replace("/", ".").removesuffix(".py")
    log = output / ("p142_" + name.replace(".", "_") + ".log")
    cmd = [sys.executable, "-B", "-m", "unittest", "-v", name]
    started = time.monotonic()
    try:
        with log.open("wb") as stream:
            proc = subprocess.run(
                cmd, cwd=root, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT,
                check=False, timeout=MAX_MODULE_SECONDS,
            )
        native_exit = proc.returncode
    except subprocess.TimeoutExpired:
        native_exit = 124
    except OSError:
        native_exit = 125

    contents = log.read_bytes() if log.exists() else b""
    text = contents.decode("utf-8", "replace")
    matches = COUNT.findall(text)
    total = int(matches[-1]) if matches else -1
    cases = BAD_TEST.findall(text)
    errors = sum(1 for _, status in cases if status == "ERROR")
    failures = sum(1 for _, status in cases if status == "FAIL")
    passed = native_exit == 0 and total >= 1 and bool(END_OK.search(text))
    return {
        "module": name,
        "exit": native_exit,
        "count": total,
        "failures": failures,
        "errors": errors,
        "status": "PASS" if passed else
                  ("TIMEOUT" if native_exit == 124 else "HOLD"),
        "duration_s": round(time.monotonic() - started, 2),
        "log_sha256": hashlib.sha256(contents).hexdigest().upper(),
        "log_bytes": len(contents),
        "failing_test_names": [t for t, _ in cases][:80],
    }


def main() -> int:
    if not (
        sys.platform == "win32"
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_OS") == "Windows"
        and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
        and os.environ.get("GITHUB_EVENT_NAME") == "push"
        and os.environ.get("RUNNER_TEMP")
    ):
        print("P142_UNPRIVILEGED_HOSTED_WINDOWS_ONLY=REFUSED", flush=True)
        return 4

    root = Path(__file__).resolve().parents[1]
    output = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p142-post-stall-original-tests"
    output.mkdir(parents=True, exist_ok=True)
    all_modules = _source_inventory(root)
    pivot = all_modules.index(ORIGINAL_STALL_MODULE)
    remaining = all_modules[pivot + 1:]
    if len(remaining) != EXPECTED_UNREACHED_MODULES:
        print("P142_SUFFIX_INVENTORY_CHANGED=HOLD", flush=True)
        return 5

    print("P142_P135_AUTHENTIC_PRIOR_PARTIAL=1637_PASS_37_FAIL_7_ERROR", flush=True)
    print("P142_P135_ORIGINAL_HISTORICAL_TEST_STALL=UNRESOLVED", flush=True)
    print("P142_COMPLETE_ORIGINAL_TEST_MODULE_INVENTORY=" + str(len(all_modules)), flush=True)
    print("P142_ORIGINAL_UNREACHED_MODULES=" + str(len(remaining)), flush=True)
    print("P142_ALL_ORIGINAL_TEST_METHODS_WITHIN_EACH_MODULE=EXECUTED_UNFILTERED", flush=True)
    print("P142_MAX_SECONDS_PER_MODULE=" + str(MAX_MODULE_SECONDS), flush=True)
    print("P142_CONCURRENT_DISPOSABLE_WINDOWS_PROCESSES=" + str(WORKERS), flush=True)
    print("P142_REAL_API_KEY_OR_PRODUCTION_WINCRED_TARGET=NONE", flush=True)

    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        future_to_name = {
            pool.submit(_run_module, name, root, output): name
            for name in remaining
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                item = future.result()
            except Exception:
                # Preserve a report row for a failed launch/orchestration.
                item = {
                    "module": name.replace("/", ".").removesuffix(".py"),
                    "exit": 125, "count": -1, "failures": 0,
                    "errors": 0, "status": "HOLD", "duration_s": -1,
                    "log_sha256": "UNAVAILABLE", "log_bytes": 0,
                    "failing_test_names": [],
                }
            results.append(item)
            print(
                "P142_MODULE_RESULT=" + item["module"] +
                "|STATUS=" + item["status"] +
                "|EXIT=" + str(item["exit"]) +
                "|TESTS=" + str(item["count"]) +
                "|FAIL=" + str(item["failures"]) +
                "|ERROR=" + str(item["errors"]) +
                "|SHA256=" + item["log_sha256"],
                flush=True,
            )

    results.sort(key=lambda row: row["module"])
    failures = [r for r in results if r["status"] == "HOLD"]
    timed_out = [r for r in results if r["status"] == "TIMEOUT"]
    passed = [r for r in results if r["status"] == "PASS"]
    known_cases = sum(max(0, r["count"]) for r in results)
    import json
    with (output / "p142_inventory_diagnostic_manifest.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump({
            "exact_baseline": P141_BASELINE,
            "source_modules": len(all_modules),
            "original_p135_stall_module": ORIGINAL_STALL_MODULE,
            "unreached_modules": len(remaining),
            "all_test_methods_unfiltered_within_each_module": True,
            "completed_modules": len(results),
            "pass_modules": len(passed),
            "hold_modules": len(failures),
            "timeout_modules": len(timed_out),
            "known_completed_test_count": known_cases,
            "release_approved": False,
            "results": results,
        }, handle, sort_keys=True, indent=2)

    print("P142_TOTAL_MODULE_ROWS=" + str(len(results)), flush=True)
    print("P142_MODULES_PASS=" + str(len(passed)), flush=True)
    print("P142_MODULES_HOLD=" + str(len(failures)), flush=True)
    print("P142_MODULES_TIMEOUT=" + str(len(timed_out)), flush=True)
    print("P142_COMPLETED_UNFILTERED_PER_MODULE_TEST_COUNT=" + str(known_cases), flush=True)
    print("P142_P135_UNFILTERED_FULL_PRODUCT_TRIPLE_REGRESSIONS=NOT_PASSED", flush=True)
    print("P142_INDEPENDENT_GOVERNANCE_SIGNOFF=NOT_OBTAINED", flush=True)
    print("P142_SIGNED_PRODUCTION_LAUNCH=NOT_APPROVED", flush=True)
    print("P142_USER_SCOPE_RELEASE=HOLD", flush=True)

    # The diagnostic collector should succeed only if every module has an
    # auditable row; individual FAIL/TIMEOUT remain clearly visible as HOLD.
    return 0 if len(results) == EXPECTED_UNREACHED_MODULES else 1


if __name__ == "__main__":
    raise SystemExit(main())
