"""P166 Windows-native source-preserving H/C/R security evidence collector.

All historical test failures stay real and visible. Green collector != release.
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

from scripts.p139_native_fs_verified_local_temp_root import _guard_runner, _verify_original_handle_policy
from scripts.p165_windows_versioned_security_review_submission import (
    HISTORICAL_TWO_BRANCH_POSITIVES, original_test_inventory,
)
from scripts.p166_windows_current_branch_acceptance import (
    BRANCH, BASE, verify_current_source, ROOT,
)

RAN = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
ISSUE = re.compile(r"^(FAIL|ERROR): \S+ \(([^)]+)\)", re.M)
CASE = re.compile(r"^(test_\S+) \(([^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped .*?)\s*$", re.M)
SECRETS = (
    "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "NAYEON_INTERNAL_SECRET",
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def run_actual(label: str, ids: list[str], temp: Path, evidence: Path,
               expected_count: int | None = None) -> dict:
    log = evidence / ("p166_native_" + label + ".log")
    env = os.environ.copy()
    for key in list(env):
        if key in SECRETS or key.endswith("_API_KEY"):
            env.pop(key, None)
    env.update({"TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp),
                "PYTHONDONTWRITEBYTECODE": "1"})
    start = time.monotonic()
    timedout = False
    with log.open("wb") as stream:
        child = subprocess.Popen(
            [sys.executable, "-B", "-m", "unittest", "-v", *ids],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        try:
            exitcode = child.wait(timeout=115)
        except subprocess.TimeoutExpired:
            timedout = True
            exitcode = 124
            subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=False, timeout=15)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
    raw = log.read_bytes()
    out = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    ran = RAN.findall(out)
    observed = int(ran[-1]) if ran else None
    expected = len(ids) if expected_count is None else expected_count
    issues = [{"kind": kind, "test_id": testid} for kind, testid in ISSUE.findall(out)]
    cases = [{"test_id": case_id, "outcome": outcome}
             for _, case_id, outcome in CASE.findall(out)]
    passed = (exitcode == 0 and observed == expected
              and re.search(r"^OK\s*$", out, re.M) is not None and not issues)
    footer_failed = re.findall(r"^FAILED \(([^)]+)\)", out, re.M)
    result = {
        "label": label, "actual_native_exit_code": exitcode,
        "expected_methods": expected, "unittest_observed": observed,
        "native_test_method_outcomes": cases, "native_failed_error_ids": issues,
        "native_failed_footer": footer_failed[-1] if footer_failed else None,
        "genuine_complete_unittest_footer": (observed == expected and
            (passed or bool(footer_failed))), "actual_native_pass": passed,
        "timedout": timedout, "seconds": round(time.monotonic() - start, 3),
        "actual_raw_log_file": log.name, "actual_raw_log_sha256": digest(raw),
        "actual_raw_log_bytes": len(raw),
    }
    print("P166_NATIVE=" + label + "|EXIT=" + str(exitcode) +
          "|RAN=" + str(observed) + "|PASS=" + str(passed), flush=True)
    print("P166_LOG_SHA256=" + label + "|" + digest(raw), flush=True)
    for issue in issues:
        print("P166_GENUINE_ORIGINAL_ISSUE=" + label + "|" + issue["kind"] +
              "|" + issue["test_id"], flush=True)
    return result


def main() -> int:
    _guard_runner()
    sha = os.environ.get("GITHUB_SHA", "")
    initial = verify_current_source(expected_branch=BRANCH, expected_head=sha)
    historical_ids, original_c_ids, original_c_groups = original_test_inventory()
    if len(historical_ids) != 10 or len(original_c_ids) != 25:
        raise RuntimeError("P166 full historical P76 or 25-method original test inventory drift")
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p166-windows-current-branch"
    evidence.mkdir(parents=True, exist_ok=True)
    temp = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P166 Windows test-only TEMP collision")
        os.mkdir(temp)
        created = True
        _verify_original_handle_policy(str(temp))
        print("P166_P139_REAL_WIN32_OPEN_HANDLE_NO_REPARSE=PASS", flush=True)
        # Scope order: focused novel positive/negative before the larger original subsets.
        candidate = run_actual("C_new_15", [
            "tests.test_p166_current_branch_acceptance.P166RealCurrentBranchAcceptanceTests"
        ], temp, evidence, expected_count=15)
        historical = run_actual("H_original_P76_all_10", historical_ids, temp, evidence)
        reduced = run_actual("C_unchanged_original_25", original_c_ids, temp, evidence)
    finally:
        if created:
            meta = temp.lstat()
            if temp.is_symlink() or getattr(meta, "st_file_attributes", 0) & 0x400:
                raise RuntimeError("P166 unsafe Windows test temp reparse cleanup refused")
            shutil.rmtree(temp)
    if verify_current_source(expected_branch=BRANCH, expected_head=sha) != initial:
        raise RuntimeError("P166 source/branch custody changed during native Windows tests")

    real_h_failures = {item["test_id"] for item in historical["native_failed_error_ids"]}
    h_expected_hold = (historical["actual_native_exit_code"] == 1
                       and historical["unittest_observed"] == 10
                       and historical["genuine_complete_unittest_footer"]
                       and real_h_failures == set(HISTORICAL_TWO_BRANCH_POSITIVES))
    c_new_pass = (candidate["actual_native_pass"] and
                  candidate["unittest_observed"] == 15 and
                  len(candidate["native_test_method_outcomes"]) == 15)
    c_original_pass = (reduced["actual_native_pass"] and reduced["unittest_observed"] == 25)
    report = {
        "checkpoint": "P166", "actual_current_branch_sha": sha,
        "exact_original_P165_ancestor": BASE, "current_branch_source_provenance": initial,
        "historical_H_original_full_P76": historical,
        "historical_H_disposition": ("HOLD_TWO_ORIGINAL_NATIVE_FAILURES_UNWAIVED"
                                      if h_expected_hold else "UNEXPECTED_HISTORICAL_HOLD"),
        "current_C_additive_positive_and_negative": candidate,
        "current_C_selected_original_unchanged_25": reduced,
        "current_C_original_methods": original_c_groups,
        "current_C_disposition": ("REDUCED_SCOPE_CANDIDATE_PASS_ONLY"
                                  if c_new_pass and c_original_pass else "CANDIDATE_HOLD"),
        "historical_two_real_original_positive_wrong_branch_ids":
            list(HISTORICAL_TWO_BRANCH_POSITIVES),
        "H_never_satisfied_by_C": True, "R_never_satisfied_by_C": True,
        "named_qualified_external_reviewer_GO": "NOT_OBTAINED",
        "original_test_governance_approval": "NOT_OBTAINED",
        "three_complete_unfiltered_full_product_windows_regressions": "0/3",
        "main_helper_installer_exact_signed_release": "NOT_OBTAINED",
        "SAC_WDAC_code_integrity_policy_owner_GO": "NOT_OBTAINED",
        "privileged_BYOK_C1_G0_to_G6": "OPEN",
        "authorised_real_credential_or_provider_calls": False,
        "diagnostic_candidate_is_full_product_regression": False,
        "production_release": "HOLD",
        "limitations": [
            "Not an original H positive PASS; original P76 wrong-branch native failures preserved",
            "Current C tests actual GitHub-hosted Windows source and mocked offline credential scope, not production binaries",
            "No OS-level WinCred or provider network telemetry; instrumented Python/network plus unchanged original fake WinCred tests only",
            "Qualified independent review, production signed binary pins, WDAC/SAC owner and full-product Windows triad absent",
        ],
    }
    ledger = evidence / "p166_actual_windows_H_C_R_reviewer_ledger.json"
    ledger.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("P166_ORIGINAL_H=" + report["historical_H_disposition"], flush=True)
    print("P166_CURRENT_C=" + report["current_C_disposition"], flush=True)
    print("P166_INDEPENDENT_QUALIFIED_REVIEW=NOT_OBTAINED", flush=True)
    print("P166_FULL_PRODUCT_REGRESSIONS=0/3", flush=True)
    print("P166_PRODUCTION_RELEASE=HOLD", flush=True)
    return 0 if h_expected_hold and c_new_pass and c_original_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
