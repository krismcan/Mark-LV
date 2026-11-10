"""P145 - original Phase8.31 Tk root retention isolation on genuine Windows.

Run each unmodified historical test method IN ITS OWN fresh Windows interpreter,
using the unchanged P139 native path-handle verified temporary fixture. Preserve
native failures and tell apart individually surviving Tk roots from cross-test
lifecycle accumulation. A successful COLLECTION is not a passing product test.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import unittest
import uuid

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner,
    _verify_original_handle_policy,
)

BASE_SHA = "4c4c8ef05f831e957023ef98d67661818f5e5eac"
MODULE = "tests.test_phase_831_effect_isolation"
EXPECTED_METHODS = 19
WORKERS = 3
METHOD_TIMEOUT_SECONDS = 55
SECRET_VARIABLES = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)
_COUNT = re.compile(r"Ran (\d+) tests? in [\d.]+s")


def _names() -> list[str]:
    suite = unittest.defaultTestLoader.loadTestsFromName(MODULE)
    cases = []
    def collect(node):
        if isinstance(node, unittest.TestSuite):
            for item in node:
                collect(item)
        else:
            cases.append(node.id())
    collect(suite)
    if (len(cases) != EXPECTED_METHODS or len(cases) != len(set(cases))
            or not all(c.startswith(MODULE + ".") for c in cases)):
        raise RuntimeError("P145 original Phase8.31 method inventory drift")
    return sorted(cases)


def _one(test_id: str, repo: Path, fixture: Path, evidence: Path) -> dict:
    file = evidence / ("p145_" + test_id.rsplit(".", 1)[-1] + ".log")
    env = os.environ.copy()
    for variable in SECRET_VARIABLES:
        env.pop(variable, None)
    for variable in ("TEMP", "TMP", "TMPDIR"):
        env[variable] = str(fixture)
    start = time.monotonic()
    try:
        with file.open("wb") as output:
            process = subprocess.run(
                [sys.executable, "-B", "-m", "unittest", "-v", test_id],
                cwd=repo, env=env, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT,
                timeout=METHOD_TIMEOUT_SECONDS, check=False,
            )
        code = process.returncode
    except subprocess.TimeoutExpired:
        code = 124
    except OSError:
        code = 125
    raw = file.read_bytes() if file.exists() else b""
    stdout = raw.decode("utf8", "replace")
    lines = stdout.splitlines()
    counts = _COUNT.findall(stdout)
    fail_ids = [line.split(":", 1)[1].strip()
                for line in lines if line.startswith(("FAIL: ", "ERROR: "))]
    root_errors = [line for line in lines if "retired fake Tk roots still live" in line]
    status = (
        "PASS" if code == 0 and counts == ["1"]
        and any(line.strip() == "OK" for line in lines)
        and not fail_ids
        else "TIMEOUT" if code == 124 else "HOLD"
    )
    result = {
        "test_id": test_id,
        "status": status,
        "exit": code,
        "completed_count": int(counts[-1]) if counts else None,
        "failure_ids": fail_ids,
        "root_lifetime_observations": root_errors,
        "log_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
        "duration_s": round(time.monotonic() - start, 3),
    }
    print(
        "P145_ORIGINAL_METHOD=" + test_id +
        "|STATUS=" + status + "|EXIT=" + str(code) +
        "|ROOT_SURVIVOR=" + str(bool(root_errors)).upper() +
        "|SHA256=" + result["sha256"],
        flush=True,
    )
    return result


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != (
            "byok-c1-p145-isolated-windows-tk-root-lifetime-20261110"):
        raise RuntimeError("P145 exact disposable GitHub branch required")
    repo = Path(__file__).resolve().parents[1]
    if not (repo / "tests/test_phase_831_effect_isolation.py").is_file():
        raise RuntimeError("Original unchanged historical Phase8.31 suite missing")
    names = _names()
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p145-original-tk-root"
    evidence.mkdir(parents=True, exist_ok=True)
    fixture = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("Owned test fixture already exists")
        os.mkdir(fixture)
        created = True
        _verify_original_handle_policy(str(fixture))
        print("P145_ORIGINAL_UNMODIFIED_TEST_METHOD_COUNT=19", flush=True)
        print("P145_P139_UNCHANGED_WIN32_OPEN_HANDLE_POLICY=PASS", flush=True)
        print("P145_REAL_USER_KEY_AND_WINCRED_EFFECT=NONE", flush=True)
        results = []
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(_one, test, repo, fixture, evidence): test
                       for test in names}
            for future in as_completed(futures):
                test = futures[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append({
                        "test_id": test, "status": "HOLD", "exit": 125,
                        "completed_count": None, "failure_ids": [],
                        "root_lifetime_observations": [type(exc).__name__],
                        "log_bytes": 0, "sha256": None, "duration_s": None,
                    })
        results.sort(key=lambda x: x["test_id"])
        summary = {s: sum(row["status"] == s for row in results)
                   for s in ("PASS", "HOLD", "TIMEOUT")}
        lifetime = [r["test_id"] for r in results
                    if any("retired fake Tk roots still live" in v
                           for v in r["root_lifetime_observations"])]
        manifest = {
            "base_commit": BASE_SHA,
            "diagnostic_only": True, "production_release": False,
            "original_source_changed": False,
            "method_count": len(results),
            "summary": summary,
            "standalone_tk_lifetime_failures": lifetime,
            "original_full_module_P144": "19 cases; 1 FAIL; 1 teardown ERROR",
            "full_product_regression_approved": False,
            "records": results,
        }
        (evidence / "p145_tk_root_isolation_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf8")
        print("P145_COMPLETED_METHOD_RECORDS=" + str(len(results)), flush=True)
        for key, value in summary.items():
            print("P145_METHODS_" + key + "=" + str(value), flush=True)
        print("P145_STANDALONE_TK_ROOT_LIFETIME_FAILURES=" +
              str(len(lifetime)), flush=True)
        print("P145_NO_FULL_PRODUCT_WINDOWS_REGRESSION_PASS=TRUE", flush=True)
        print("P145_SIGNED_RELEASE_AND_INDEPENDENT_APPROVAL=HOLD", flush=True)
        return 0 if len(results) == EXPECTED_METHODS else 1
    finally:
        if created:
            try:
                attributes = fixture.lstat()
                if (not fixture.is_symlink() and
                        not (getattr(attributes, "st_file_attributes", 0) & 0x400)
                        and str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P145_VERIFIED_ROOT_CLEANUP=ATTEMPTED", flush=True)
                else:
                    print("P145_UNEXPECTED_REPARSE_CLEANUP_REFUSED", flush=True)
            except Exception:
                print("P145_ROOT_CLEANUP_UNCERTAIN_EPHEMERAL_RUNNER", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
