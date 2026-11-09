"""P135: three unfiltered Windows FULL unittest-discovery attempts, never fabricated GO.

Executes the repository's complete Python test discovery three times on a
disposable GitHub-hosted Windows account, with authentic process exit codes,
SHA-256 of complete logs, and verbatim failing test IDs (not secret values).
This is an honest release HOLD audit: an inherited exact-branch historical
seal can fail. We do not skip it, edit it or mark it green. No credential
access or network is performed by this harness itself; P134 child tests are
synthetic-only and strictly gated to the disposable runner.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys


_FAILURE_HEADER = re.compile(
    r"^(?:FAIL|ERROR): (test_[^(\s]+(?:\s*\([^)]*\))?)",
    re.MULTILINE,
)
_COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
_RESULT = re.compile(r"^FAILED \(([^)]*)\)", re.MULTILINE)


def main() -> int:
    if not (
        sys.platform == "win32"
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_OS") == "Windows"
        and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
        and os.environ.get("P134_NATIVE_WINCRED_EPHEMERAL_AUTH")
        == "EPHEMERAL_GITHUB_WINDOWS_ONLY"
    ):
        print("P135_ONLY_HOSTED_WINDOWS_SYNTHETIC_CREDENTIAL_SCOPE=REFUSED")
        return 4

    root = Path(__file__).resolve().parents[1]
    runner_temp = os.environ.get("RUNNER_TEMP")
    if not runner_temp:
        print("P135_DISPOSABLE_RUNNER_TEMP_REQUIRED=REFUSED")
        return 5
    output_dir = Path(runner_temp) / "nayeon-p135-full-suite-audit"
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable, "-B", "-m", "unittest", "discover",
        "-s", "tests", "-t", ".", "-p", "test_*.py", "-v",
    ]
    failed_runs = 0
    observed_counts = []
    all_failures = []
    print("P135_FULL_PRODUCT_SUITE_COMMAND=python -B -m unittest discover -s tests -t . -p test_*.py -v")
    print("P135_RUNS_REQUIRED=3")
    print("P135_NO_TEST_MODULE_EXCLUSIONS=TRUE")
    print("P135_REAL_PROVIDER_KEY=NONE")
    print("P135_GITHUB_EPHEMERAL_WINCRED_SYNTHETIC_NAMESPACE_ONLY=TRUE")

    # Use inherited unmodified runtime environment. No provider variables
    # are read by this harness or passed into emitted status.
    for iteration in range(1, 4):
        path = output_dir / f"p135_full_python_discovery_pass_{iteration}.log"
        try:
            with path.open("wb") as sink:
                result = subprocess.run(
                    command, cwd=root, stdout=sink, stderr=subprocess.STDOUT,
                    timeout=1000, check=False,
                )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            exit_code = 124
        except OSError:
            exit_code = 125

        data = path.read_bytes() if path.exists() else b""
        digest = hashlib.sha256(data).hexdigest().upper()
        output = data.decode("utf-8", errors="replace")
        counts = _COUNT.findall(output)
        count = int(counts[-1]) if counts else -1
        observed_counts.append(count)
        ids = _FAILURE_HEADER.findall(output)
        failed_results = _RESULT.findall(output)
        if exit_code != 0 or count < 1 or ids or failed_results:
            failed_runs += 1
        all_failures.extend(ids)
        print(f"P135_PASS_{iteration}_NATIVE_EXIT={exit_code}")
        print(f"P135_PASS_{iteration}_UNITTEST_COUNT={count}")
        print(f"P135_PASS_{iteration}_COMPLETE_LOG_SHA256={digest}")
        print(f"P135_PASS_{iteration}_ERROR_TEST_COUNT={len(ids)}")
        print(f"P135_PASS_{iteration}_FAILURE_MARKERS={','.join(failed_results) if failed_results else 'NONE'}")
        # Expose only names, never actual exception messages / key bytes.
        for name in sorted(set(ids))[:60]:
            print(f"P135_PASS_{iteration}_FAILED_TEST_ID={name}")
        print(f"P135_PASS_{iteration}_DISPOSITION="
              f"{'PASS' if exit_code==0 and count>=1 and not ids and not failed_results else 'HOLD'}")

    print("P135_THREE_FULL_DISCOVERY_ATTEMPTS_EXECUTED=TRUE")
    print("P135_UNCHANGED_SUITE_COUNT_ACROSS_RUNS="
          + ("TRUE" if len(set(observed_counts)) == 1 else "FALSE"))
    print(f"P135_FULL_DISCOVERY_FAILED_RUNS={failed_runs}")
    print(f"P135_UNIQUE_FAILED_TEST_IDS={len(set(all_failures))}")
    print("P135_HISTORICAL_SEALS_NOT_EDITED_OR_SILENTLY_SKIPPED=TRUE")
    print("P135_G0_INDEPENDENT_SECURITY_REVIEW=NOT_RECEIVED")
    print("P135_PRODUCTION_SIGNATURE_AND_SAC_ACCEPTANCE=NOT_RECEIVED")
    if failed_runs or len(set(observed_counts)) != 1:
        print("P135_TRIPLE_FULL_PRODUCT_WINDOWS_REGRESSIONS=HOLD")
        print("P135_BYOK_C1_USER_SCOPE_RELEASE=HOLD")
        return 1
    print("P135_TRIPLE_FULL_PRODUCT_WINDOWS_REGRESSIONS=FUNCTIONAL_PASS_NOT_RELEASE")
    print("P135_BYOK_C1_USER_SCOPE_RELEASE=HOLD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
