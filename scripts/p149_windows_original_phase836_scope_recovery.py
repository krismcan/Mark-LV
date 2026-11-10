"""P149: exact original Phase8.36 source-integrity MODULE on disposable Windows.

ONE complete unfiltered historical module with an increased bounded runtime.
Test security source and test assertions remain byte-identical to P148.
A successful diagnostic workflow DOES NOT declare whole-product regression GO.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)

BASE = "a08bcb2b459da5edab673333f0e45be52a24230c"
BRANCH = "byok-c1-p149-windows-original-836-scope-module-recovery-20261110"
MODULE = "tests.test_phase_836_scope_integrity"
SOURCE = "tests/test_phase_836_scope_integrity.py"
LIMIT_SECONDS = 170
EXPECTED_CASES = 11
COUNT = re.compile(r"Ran (\d+) tests? in [\d.]+s")
SECRET_ENV = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P149 exact GitHub hosted Windows branch required")
    repo = Path(__file__).resolve().parents[1]
    original = repo / SOURCE
    check = subprocess.run(
        ["git", "-C", str(repo), "show", BASE + ":" + SOURCE],
        capture_output=True, timeout=25, check=False
    )
    if check.returncode != 0 or original.read_bytes() != check.stdout:
        raise RuntimeError("P149 original Phase8.36 historical assertions modified")
    original_sha = hashlib.sha256(original.read_bytes()).hexdigest().upper()
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p149-original-836-scope"
    evidence.mkdir(parents=True, exist_ok=True)
    fixture = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("Unexpected test root reuse")
        os.mkdir(fixture)
        created = True
        _verify_original_handle_policy(str(fixture))
        print("P149_EXACT_ORIGINAL_836_SOURCE_SHA256=" + original_sha, flush=True)
        print("P149_P139_NATIVE_WIN32_OPENED_HANDLE_VERIFIER=PASS", flush=True)
        print("P149_ORIGINAL_TEST_METHODS_FILTERED=FALSE", flush=True)
        print("P149_REAL_PRODUCTION_CREDENTIAL_EFFECTS=NONE", flush=True)
        env = os.environ.copy()
        for key in SECRET_ENV:
            env.pop(key, None)
        env.update({key: str(fixture) for key in ("TMP", "TEMP", "TMPDIR")})
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        raw_log = evidence / "p149_original_phase836_full_module.log"
        began = time.monotonic()
        try:
            with raw_log.open("wb") as output:
                proc = subprocess.run(
                    [sys.executable, "-B", "-m", "unittest", "-v", MODULE],
                    cwd=repo, env=env, stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT,
                    timeout=LIMIT_SECONDS, check=False
                )
            native_exit = proc.returncode
        except subprocess.TimeoutExpired:
            native_exit = 124
        except OSError:
            native_exit = 125
        duration = round(time.monotonic() - began, 3)
        raw = raw_log.read_bytes() if raw_log.exists() else b""
        text = raw.decode("utf-8", "replace")
        lines = text.splitlines()
        matches = COUNT.findall(text)
        cases = int(matches[-1]) if matches else None
        failed = [line.partition(":")[2].strip() for line in lines
                  if line.startswith(("FAIL: ", "ERROR: "))]
        failing_footer = [line for line in lines if line.startswith("FAILED (")]
        passing = (
            native_exit == 0 and cases == EXPECTED_CASES
            and any(line.strip() == "OK" for line in lines)
            and not failed and not failing_footer
        )
        status = ("PASS" if passing else "TIMEOUT" if native_exit == 124
                  else "HOLD")
        receipt = {
            "parent_sha": BASE,
            "original_module": MODULE,
            "historical_test_source_unmodified": True,
            "original_source_sha256": original_sha,
            "unfiltered_test_methods": True,
            "expected_tests_from_original_inventory": EXPECTED_CASES,
            "observed_unittest_count": cases,
            "native_exit_code": native_exit,
            "status": status,
            "duration_seconds": duration,
            "unittest_failed_ids": failed,
            "unittest_failed_footer": failing_footer[-1] if failing_footer else None,
            "raw_log_sha256": hashlib.sha256(raw).hexdigest().upper(),
            "raw_log_bytes": len(raw),
            "safe_test_root_original_native_handle_policy": True,
            "P142_35_second_timeout": "PRESERVED",
            "full_product_three_windows_regressions_passed": 0,
            "reviewer_approved_historical_suite_governance": False,
            "production_release_approved": False,
        }
        (evidence / "p149_phase836_original_module_manifest.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print("P149_ORIGINAL_PHASE836_NATIVE_EXIT=" + str(native_exit), flush=True)
        print("P149_ORIGINAL_PHASE836_CASES=" + str(cases), flush=True)
        print("P149_ORIGINAL_PHASE836_STATUS=" + status, flush=True)
        print("P149_ORIGINAL_PHASE836_DURATION_SEC=" + str(duration), flush=True)
        print("P149_ORIGINAL_PHASE836_FAILURE_IDS=" + str(len(failed)), flush=True)
        print("P149_ORIGINAL_PHASE836_RAW_LOG_SHA256=" +
              receipt["raw_log_sha256"], flush=True)
        print("P149_INDEPENDENT_SECURITY_GOVERNANCE=NOT_OBTAINED", flush=True)
        print("P149_FULL_PRODUCT_WINDOWS_TRIAD=NOT_PASSED", flush=True)
        print("P149_USER_SCOPE_C1_PRODUCTION_RELEASE=HOLD", flush=True)
        # The collector is allowed to succeed after a real test failure:
        # the manifest still records native exit and HOLD.
        return 0 if raw and native_exit in (0, 1, 124, 125) else 1
    finally:
        if created:
            try:
                st = fixture.lstat()
                if (not fixture.is_symlink()
                        and not (getattr(st, "st_file_attributes", 0) & 0x400)
                        and str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P149_OWNED_TEMP_CLEANUP=ATTEMPTED", flush=True)
                else:
                    print("P149_TEMP_REPARSE_CLEANUP=REFUSED", flush=True)
            except Exception:
                print("P149_EPHEMERAL_RUNNER_TEMP_CLEANUP=UNCERTAIN", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
