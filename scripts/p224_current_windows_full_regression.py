"""P224 genuine *one* full unfiltered Windows regression on exact current P223.

This is a scope-precise historical failure rebaseline, not a release gate or a
way to manufacture an independent security review. It makes ONE Windows CI
attempt and preserves original failing unittest IDs. It never modifies tests,
credentials, P96 source or security policy. The existing P134 test may operate
on its owned disposable synthetic WinCred namespace ONLY on GitHub Windows.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys


_COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
_BAD = re.compile(r"^(?:FAIL|ERROR): (.+)$", re.MULTILINE)
_LAST = re.compile(r"^FAILED \((.+)\)$", re.MULTILINE)
_MAX_SECONDS = 600
_MAX_TEST_ID_COUNT = 120


def main() -> int:
    if not (
        sys.platform == "win32"
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_OS") == "Windows"
        and os.environ.get("GITHUB_EVENT_NAME") == "push"
        and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
        and os.environ.get("GITHUB_REF_NAME")
        == "byok-c1-p224-full-windows-product-regression-rebaseline-20261114"
        and os.environ.get("P134_NATIVE_WINCRED_EPHEMERAL_AUTH")
        == "EPHEMERAL_GITHUB_WINDOWS_ONLY"
        and os.environ.get("RUNNER_TEMP")
        and os.environ.get("GITHUB_SHA")
    ):
        print("P224_AUTHENTIC_HOSTED_WINDOWS_REGRESSION=REFUSED")
        return 4
    root = Path(__file__).resolve().parents[1]
    assert root.is_dir()
    output = Path(os.environ["RUNNER_TEMP"]) / "p224-full-Windows-unfiltered"
    output.mkdir(parents=True, exist_ok=True)
    log = output / "full-unfiltered-Windows-discovery.log"
    sha = output / "full-unfiltered-Windows-sha256.txt"
    command = [
        sys.executable, "-B", "-m", "unittest", "discover",
        "-s", "tests", "-t", ".", "-p", "test_*.py", "-v",
    ]
    exit_code = 125
    timeout = False
    with log.open("wb") as sink:
        try:
            result = subprocess.run(
                command, cwd=root, stdout=sink, stderr=subprocess.STDOUT,
                timeout=_MAX_SECONDS, stdin=subprocess.DEVNULL,
                check=False,
            )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            exit_code = 124
            timeout = True
        except OSError:
            exit_code = 125
    data = log.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    sha.write_text(digest + "  " + log.name + "\n", encoding="ascii")
    decoded = data.decode("utf-8", errors="replace")
    counts = _COUNT.findall(decoded)
    count = int(counts[-1]) if counts else -1
    failures = sorted(set(_BAD.findall(decoded)))
    footers = _LAST.findall(decoded)
    ok = (
        exit_code == 0 and not timeout and count > 0
        and not failures and not footers
        and re.search(r"^OK(?: \([^)]*\))?$", decoded, re.MULTILINE)
        is not None
    )
    print("P224_COMMAND=python -B -m unittest discover -s tests -t . -p test_*.py -v")
    print("P224_UNFILTERED_SUITE=TRUE")
    print("P224_EXPECTED_SOURCE_HEAD=" + os.environ["GITHUB_SHA"])
    print("P224_WINDOWS_NATIVE_EXIT=" + str(exit_code))
    print("P224_TIMED_OUT=" + str(timeout).upper())
    print("P224_OBSERVED_TESTS=" + str(count))
    print("P224_TOTAL_LOG_BYTES=" + str(len(data)))
    print("P224_COMPLETE_LOG_SHA256=" + digest)
    print("P224_DISTINCT_FAILURE_IDS=" + str(len(failures)))
    for item in failures[:_MAX_TEST_ID_COUNT]:
        # Test IDs only, never runtime exception values or credential data.
        print("P224_FAILED_TEST_ID=" + item[:350])
    if footers:
        print("P224_FAILURE_SUMMARY=" + footers[-1][:350])
    print("P224_P134_EFFECT_SCOPE=EPHEMERAL_RANDOM_SYNTHETIC_WINCRED_ONLY")
    print("P224_REAL_OPENAI_API_KEY_TARGET=NEVER_TOUCHED_BY_RUNNER")
    print("P224_INDEPENDENT_SEC03_SEC04_REVIEWS=NOT_RECEIVED")
    print("P224_ORIGINAL_P96_PRODUCTION_FIX=STILL_OPEN")
    print("P224_RELEASE_REAL_KEYS=NO_GO")
    print("P224_PRODUCTION_RELEASE=HOLD")
    print("P224_FULL_REGRESSION_DISPOSITION=" + (
        "CURRENT_SHA_SINGLE_RUN_FUNCTIONAL_PASS_NOT_RELEASE"
        if ok else "CURRENT_SHA_UNFILTERED_TESTS_FAILED_OR_INCOMPLETE_HOLD"
    ))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
