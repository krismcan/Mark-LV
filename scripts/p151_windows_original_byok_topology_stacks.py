"""P151: source-preserving Windows traceback evidence for three original BYOK cases.

One dedicated unfaked Python unittest interpreter PER original historical test.
Native faulthandler stack snapshots are observational only; no historical
code or test behavior is patched, bypassed, skipped, rewritten or waived.
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

BASE = "46ca262d7ff7c21a2c6c2dead5d64537cceece1e"
BRANCH = "byok-c1-p151-windows-original-byok-topology-stack-diagnostic-20261111"
MODULE = "tests.test_phase8_byok_scope_integrity"
CLASS = "ExactBYOKScopeTests"
SOURCE = "tests/test_phase8_byok_scope_integrity.py"
CASES = (
    ("current_live", "test_exact_current_unstaged_source_scope", 70),
    ("old_836_live", "test_original_836_live_method_only_update_and_admission_canaries", 90),
    ("synthetic_topology", "test_simulated_exact_staged_and_child_topology", 105),
)
SECRET_ENV = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)
COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")


def run_original_case(label: str, method: str, timeout: int, root: Path,
                      fixture: Path, evidence: Path) -> dict:
    testid = f"{MODULE}.{CLASS}.{method}"
    log = evidence / ("p151_" + label + "_original_native_unittest.log")
    env = os.environ.copy()
    for key in SECRET_ENV:
        env.pop(key, None)
    for key in ("TEMP", "TMP", "TMPDIR"):
        env[key] = str(fixture)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Native CPython faulthandler timer samples the real unchanged test stack.
    # Main is the original unittest CLI with unmodified test-class setUp.
    script = (
        "import faulthandler,runpy,sys;"
        "faulthandler.enable(file=sys.stderr);"
        "faulthandler.dump_traceback_later(20,repeat=True,file=sys.stderr);"
        "sys.argv=['unittest','-v'," + repr(testid) + "];"
        "runpy.run_module('unittest.__main__',run_name='__main__')"
    )
    began = time.monotonic()
    try:
        with log.open("wb") as stream:
            p = subprocess.run(
                [sys.executable, "-B", "-c", script],
                cwd=root, env=env, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT,
                timeout=timeout, check=False,
            )
        exitcode = p.returncode
    except subprocess.TimeoutExpired:
        exitcode = 124
    except OSError:
        exitcode = 125
    seconds = round(time.monotonic() - began, 3)
    raw = log.read_bytes() if log.exists() else b""
    lines = raw.decode("utf8", "replace").splitlines()
    counts = [int(m.group(1)) for line in lines if (m := COUNT.search(line))]
    failed = [line.split(":", 1)[1].strip()
              for line in lines if line.startswith(("FAIL: ", "ERROR: "))]
    stack_lines = [line for line in lines if line.startswith("Timeout (0:00:20)!")]
    status = ("PASS" if exitcode == 0 and counts[-1:] == [1] and
              any(line.strip() == "OK" for line in lines) and not failed
              else "TIMEOUT" if exitcode == 124 else "HOLD")
    receipt = {
        "case": testid,
        "status": status,
        "native_exit": exitcode,
        "duration_seconds": seconds,
        "observed_completed_unittest_count": counts[-1] if counts else None,
        "native_failure_identifiers": failed,
        "faulthandler_native_stack_dumps": len(stack_lines),
        "raw_log_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "raw_log_bytes": len(raw),
        "original_historical_test_unmodified": True,
    }
    print(
        "P151_CASE=" + label +
        "|VERDICT=" + status +
        "|NATIVE_EXIT=" + str(exitcode) +
        "|SECONDS=" + str(seconds) +
        "|TRACEBACK_SNAPSHOTS=" + str(len(stack_lines)) +
        "|SHA256=" + receipt["raw_log_sha256"], flush=True,
    )
    return receipt


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P151 exact GitHub hosted Windows branch only")
    root = Path(__file__).resolve().parents[1]
    original = root / SOURCE
    previous = subprocess.run(
        ["git", "-C", str(root), "show", BASE + ":" + SOURCE],
        capture_output=True, check=False, timeout=25,
    )
    if previous.returncode != 0 or original.read_bytes() != previous.stdout:
        raise RuntimeError("P151 historical BYOK test source was modified")
    original_sha = hashlib.sha256(original.read_bytes()).hexdigest().upper()

    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p151-original-byok-stacks"
    evidence.mkdir(parents=True, exist_ok=True)
    fixture = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("Unexpected reused test-only C: fixture root")
        os.mkdir(fixture)
        created = True
        _verify_original_handle_policy(str(fixture))
        print("P151_ORIGINAL_P139_NATIVE_HANDLE_VERIFIER=PASS", flush=True)
        print("P151_SOURCE_SHA256=" + original_sha, flush=True)
        print("P151_NO_TEST_SOURCE_OR_SECURITY_GUARD_MUTATION=TRUE", flush=True)
        results = []
        for label, method, budget in CASES:
            # Every test's original unittest class fixture and assertion
            # executes in a fresh, isolated real Windows interpreter.
            results.append(run_original_case(label, method, budget,
                                             root, fixture, evidence))

        manifest = {
            "baseline_git_sha": BASE,
            "status": "DIAGNOSTIC_ONLY__NO_PRODUCT_RELEASE",
            "source_file": SOURCE,
            "source_sha256": original_sha,
            "original_test_source_changed": False,
            "cases": results,
            "case_count": len(results),
            "pass_count": sum(r["status"] == "PASS" for r in results),
            "hold_count": sum(r["status"] == "HOLD" for r in results),
            "timeout_count": sum(r["status"] == "TIMEOUT" for r in results),
            "faulthandler_dump_total": sum(
                r["faulthandler_native_stack_dumps"] for r in results
            ),
            "no_real_keys_or_production_wincd_effect": True,
            "P150_unfiltered_original_module": "TIMEOUT_190_SECONDS_HOLD",
            "three_complete_full_product_windows_regressions": "NOT_PASSED",
            "qualified_independent_security_reviewer_GO": False,
            "qualified_legacy_suite_governance_GO": False,
            "publisher_signer_and_SAC_policy_owner_GO": False,
            "byok_user_scope_release": "HOLD",
        }
        (evidence / "p151_original_byok_focused_windows_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf8",
        )
        print("P151_FOCUSED_NATIVE_TESTS_COLLECTED=" + str(len(results)), flush=True)
        print("P151_FOCUSED_PASS=" + str(manifest["pass_count"]), flush=True)
        print("P151_FOCUSED_HOLD=" + str(manifest["hold_count"]), flush=True)
        print("P151_FOCUSED_TIMEOUT=" + str(manifest["timeout_count"]), flush=True)
        print("P151_FAULTHANDLER_NATIVE_STACK_SNAPSHOTS=" +
              str(manifest["faulthandler_dump_total"]), flush=True)
        print("P151_OLD_P150_FULL_MODULE=STILL_HOLD", flush=True)
        print("P151_FULL_PRODUCT_WINDOWS_REGRESSION_TRIAD=NOT_PASSED", flush=True)
        print("P151_USER_SCOPE_BYOK_C1_PRODUCTION_RELEASE=HOLD", flush=True)
        # Diagnostic collection may succeed with genuine FAIL/TIMEOUTs.
        return 0 if len(results) == 3 and all(
            r["raw_log_bytes"] > 0 for r in results
        ) else 1
    finally:
        if created:
            try:
                st = fixture.lstat()
                if (not fixture.is_symlink()
                        and not (getattr(st, "st_file_attributes", 0) & 0x400)
                        and str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P151_OWNED_DISPOSABLE_TEST_ROOT_CLEANUP=ATTEMPTED",
                          flush=True)
                else:
                    print("P151_UNEXPECTED_REPARSE_CLEANUP_REFUSED", flush=True)
            except Exception:
                print("P151_EPHEMERAL_FIXTURE_CLEANUP=UNCERTAIN", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
