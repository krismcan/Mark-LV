"""P167 original Windows regression root-cause triage; evidence, not release.

Replay five unchanged original test methods, and SHA-authenticate archived
P159 full original Phase8.30 log. Never suppress/refactor old assertions.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
import zipfile

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from scripts.p166_windows_current_branch_acceptance import PROTECTED

ROOT = Path(__file__).resolve().parents[1]
BASE = "eec397fb90ffbd5c4a8e527904738b0d0668d35b"
BRANCH = "byok-c1-p167-historical-regression-causal-triage-20261112"
EXPECTED = {
    ".github/workflows/p167-windows-original-regression-causal-triage.yml",
    "docs/byok-c1-p167-authenticated-original-regression-causal-triage.md",
    "scripts/p167_windows_original_regression_causal_triage.py",
}
P159_ID = 13878827122
P159_ARCHIVE = "CAB29CC94D2F469FD74DEB3CC5A404624D8AA264826F4652490B6DA5FEF17311"
P159_LOG_NAME = "test_phase_830_scope_integrity.log"
P159_LOG_HASH = "DA6215D76C43265E86B807210B97D3080ECAA9D5D78F5141BB2654735716B95A"
P159_ORIGINAL_SOURCE_HASH = "433A34A48AF83DE3353B2F08ED9EC6B710806E01EC0BE096B082ABD6272C946F"
P159_LEDGER = "p159_six_windows_scope_module_recovery_ledger.json"
OLD_P76_REFUSAL = "P76 offline source refused: wrong exact P76 prototype branch"
PHASE830 = "tests.test_phase_830_scope_integrity.Phase830ScopeIntegrityTests."
P76 = "tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests."
TEST_GROUPS = (
    ("original_830_standalone_path_adversaries_3", [
        PHASE830 + "test_backslash_root_alias_refused",
        PHASE830 + "test_noncanonical_production_path_refused",
        PHASE830 + "test_junction_parent_refused",
    ], 3),
    ("original_830_masked_alias_failure_1", [
        PHASE830 + "test_committed_root_case_alias_refused",
    ], 1),
    ("historical_original_p76_wrong_branch_refusal_1", [
        P76 + "test_wrong_branch_refused_before_other_work",
    ], 1),
)
COUNT = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
ISSUE = re.compile(r"^(FAIL|ERROR): (\S+ \([^)]+\))", re.M)
SECRET_KEYS = {"OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
               "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN",
               "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def git(*args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(ROOT), *args], timeout=25,
                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)
    return p.stdout


def custody() -> dict:
    _guard_runner()
    if (os.environ.get("GITHUB_REF_NAME") != BRANCH or
            os.environ.get("GITHUB_REPOSITORY") != "krismcan/Mark-LV" or
            os.environ.get("GITHUB_EVENT_NAME") != "push"):
        raise RuntimeError("P167 exact hosted Windows source event required")
    head = git("rev-parse", "HEAD").decode().strip()
    if (head != os.environ.get("GITHUB_SHA") or
            git("branch", "--show-current").decode().strip() != BRANCH or
            git("merge-base", BASE, head).decode().strip() != BASE):
        raise RuntimeError("P167 current head/branch/verified P166 parent mismatch")
    if git("status", "--porcelain=v1"):
        raise RuntimeError("P167 dirty checkout refused")
    changed = set(git("diff", "--name-only", BASE, "HEAD").decode().splitlines())
    if changed != EXPECTED or any(git("ls-tree", "--name-only", BASE, "--", p).strip() for p in changed):
        raise RuntimeError("P167 anything other than three newly added evidence paths refused")
    old_tests = [x for x in git("ls-tree", "-r", "--name-only", BASE, "--", "tests").decode().splitlines()
                 if re.fullmatch(r"tests/test_[^/]+\.py", x)]
    new_tests = [x for x in git("ls-files", "tests/test_*.py").decode().splitlines()
                 if re.fullmatch(r"tests/test_[^/]+\.py", x)]
    if len(old_tests) != 171 or old_tests != new_tests:
        raise RuntimeError("P167 original current 171 test modules changed")
    protected = []
    for p in PROTECTED:
        old = git("show", BASE + ":" + p)
        now = git("show", "HEAD:" + p)
        disk = (ROOT / p).read_bytes()
        if old != now or now != disk or git("rev-parse", BASE+":"+p) != git("rev-parse", "HEAD:"+p):
            raise RuntimeError("P167 source/security/trust file modified: " + p)
        protected.append({"path": p, "sha256": sha(disk)})
    return {"head": head, "parent": BASE, "original_modules": len(old_tests),
            "source_security_files_unchanged": protected,
            "exact_additive_files": sorted(changed)}


def historical_p159_authentication(token: str) -> dict:
    if not token:
        raise RuntimeError("P167 read-only GitHub Actions archive token absent")
    raw = _download_artifact(P159_ID, P159_ARCHIVE, token)
    if sha(raw) != P159_ARCHIVE:
        raise RuntimeError("P159 original full archive SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if set(z.namelist()) != {P159_LEDGER, P159_LOG_NAME,
                "test_phase_831_scope_integrity.log",
                "test_phase_832_scope_integrity.log",
                "test_phase_833_scope_integrity.log",
                "test_phase_834_scope_integrity.log",
                "test_phase_837_scope_integrity.log"}:
            raise RuntimeError("P159 archived original evidence inventory drift")
        ledger = json.loads(z.read(P159_LEDGER))
        log_raw = z.read(P159_LOG_NAME)
    if (sha(log_raw) != P159_LOG_HASH or
            ledger.get("exact_source_head") != "a8b317e6ab6cf2ad20514c60bbfaa0babbd5a492"):
        raise RuntimeError("P159 original source-bound log mismatch")
    matched = [e for e in ledger.get("test_module_dispositions", [])
               if e.get("module") == "tests.test_phase_830_scope_integrity"]
    if len(matched) != 1:
        raise RuntimeError("P159 original Phase8.30 source ledger missing")
    entry = matched[0]
    if (entry.get("log_sha256") != P159_LOG_HASH or
            entry.get("source_sha256") != P159_ORIGINAL_SOURCE_HASH or
            entry.get("native_exit") != 1 or
            entry.get("actual_unittest_count") != 21 or
            entry.get("failed_footer") != "failures=23" or
            entry.get("complete_unittest_footer") is not True or
            len(entry.get("original_failure_error_records", [])) != 23):
        raise RuntimeError("P159 full original native test summary changed")
    text = log_raw.decode("utf-8", "replace").replace("\r\n", "\n")
    chunks = [c for c in re.split(r"(?=^FAIL: )", text, flags=re.M) if c.startswith("FAIL: ")]
    if (len(chunks) != 23 or
            any(OLD_P76_REFUSAL not in c or "P76ScopeRefused" not in c for c in chunks) or
            len(re.findall(r"^Ran 21 tests in [\d.]+s$", text, re.M)) != 1 or
            "FAILED (failures=23)" not in text):
        raise RuntimeError("P159 23 historical failures not identical root-cause provenance")
    regex_masked = sum('does not match' in c for c in chunks)
    if regex_masked != 15:
        raise RuntimeError("P159 original 15 branch-before-expected-denial cases changed")
    return {
        "original_checkpoint": "P159", "archive_artifact_id": P159_ID,
        "verified_original_archive_sha256": P159_ARCHIVE,
        "verified_original_log_sha256": sha(log_raw),
        "original_tests_ran": 21, "original_native_exit": 1,
        "original_failed_subtest_records": len(chunks),
        "records_with_p76_frozen_wrong_branch_refusal": len(chunks),
        "records_where_expected_assertion_regex_was_preempted": regex_masked,
        "remaining_records_containing_p76_refusal": len(chunks)-regex_masked,
        "causal_classification_not_a_failure_waiver": True,
    }


def run_originals(label: str, ids: list[str], expected_count: int,
                  native_temp: Path, out: Path) -> dict:
    env = os.environ.copy()
    for k in list(env):
        if k in SECRET_KEYS or k.endswith("_API_KEY"):
            env.pop(k, None)
    env.update({"TEMP": str(native_temp), "TMP": str(native_temp),
                "TMPDIR": str(native_temp), "PYTHONDONTWRITEBYTECODE": "1"})
    path = out / ("p167_native_" + label + ".log")
    start = time.monotonic()
    timedout = False
    with path.open("wb") as stream:
        proc = subprocess.Popen([sys.executable, "-B", "-m", "unittest", "-v", *ids],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=stream,
            stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        try:
            native = proc.wait(timeout=85)
        except subprocess.TimeoutExpired:
            native = 124
            timedout = True
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, check=False, timeout=15)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    raw = path.read_bytes()
    output = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    counts = COUNT.findall(output)
    observed = int(counts[-1]) if counts else None
    failed = [{"kind": kind, "original_test_id": case}
              for kind, case in ISSUE.findall(output)]
    footer = re.findall(r"^FAILED \(([^)]+)\)", output, re.M)
    passed = native == 0 and observed == expected_count and re.search(r"^OK\s*$", output, re.M) is not None
    result = {"native_test_group": label, "original_methods": ids,
        "expected_original_methods": expected_count,
        "original_unittest_observed": observed, "actual_native_exit": native,
        "genuine_native_original_PASS": passed, "original_failure_ids": failed,
        "native_failure_footer": footer[-1] if footer else None,
        "original_wrong_branch_causal_marker_present": OLD_P76_REFUSAL in output,
        "native_timeout": timedout, "seconds": round(time.monotonic()-start,3),
        "original_combined_log": path.name, "original_raw_log_sha256": sha(raw),
        "original_raw_log_bytes": len(raw)}
    print("P167_NATIVE=" + label + "|EXIT="+str(native)+"|RAN="+str(observed)+"|PASS="+str(passed), flush=True)
    print("P167_NATIVE_LOG_SHA256="+label+"|"+sha(raw),flush=True)
    return result


def main() -> int:
    before = custody()
    archive = historical_p159_authentication(os.environ.get("P167_ARCHIVE_TOKEN", ""))
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p167-historical-causal-evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    temp = Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made = False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P167 disposable Windows TEMP collision")
        os.mkdir(temp)
        made = True
        _verify_original_handle_policy(str(temp))
        outcomes = {label: run_originals(label, ids, count, temp, evidence)
                    for label, ids, count in TEST_GROUPS}
    finally:
        if made:
            stat = temp.lstat()
            if temp.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                raise RuntimeError("P167 unsafe Windows TEMP removal refused")
            shutil.rmtree(temp)
    if custody() != before:
        raise RuntimeError("P167 source or Git index drift after original native tests")
    controls = outcomes["original_830_standalone_path_adversaries_3"]
    masked = outcomes["original_830_masked_alias_failure_1"]
    wrong = outcomes["historical_original_p76_wrong_branch_refusal_1"]
    controlled = controls["genuine_native_original_PASS"] and controls["original_unittest_observed"]==3
    masked_historical_failure = (
        masked["actual_native_exit"] == 1
        and masked["original_unittest_observed"] == 1
        and len(masked["original_failure_ids"]) == 1
        and "test_committed_root_case_alias_refused" in masked["original_failure_ids"][0]["original_test_id"]
        and masked["original_wrong_branch_causal_marker_present"]
    )
    original_wrong_branch_pass = wrong["genuine_native_original_PASS"] and wrong["original_unittest_observed"] == 1
    report = {
        "checkpoint": "P167", "source_custody_before_after": before,
        "authenticated_P159_original_full_module_failure_causal_inventory": archive,
        "actual_genuine_windows_original_targeted_outcomes": outcomes,
        "three_original_standalone_negative_path_controls_PASS": controlled,
        "original_masked_alias_test_still_fails_UNWAIVED": masked_historical_failure,
        "original_P76_wrong_branch_negative_control_PASS": original_wrong_branch_pass,
        "historical_P76_P85_branch_tests_or_originals_waived": False,
        "full_product_original_regression_completed": False,
        "accepted_whole_product_windows_regressions": "0/3",
        "qualified_independent_H_C_R_security_regression_governance_GO": "NOT_OBTAINED",
        "signed_main_helper_installer_and_WDAC_SAC_owner_GO": "NOT_OBTAINED",
        "privileged_BYOK_C1_G0_to_G6": "OPEN",
        "production_release": "HOLD",
        "review_limitations": [
            "P159 original Phase8.30 still FAIL with 23 genuine failure entries; grouping common wrong-branch signal is only causal triage",
            "Original failing masked alias test still FAIL here; not fixed, skipped, patched or recast as passing",
            "Original other historical modules and whole-product triad remain incomplete",
            "Historical case branch guard protects its own source era; versioned current candidate not independently approved",
        ],
    }
    (evidence/"p167_actual_windows_authenticated_original_causal_ledger.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("P167_P159_HISTORICAL_23_FAIL_RECORDS_P76_BRANCH_MARKER=VERIFIED",flush=True)
    print("P167_3_ORIGINAL_NATIVE_PATH_NEGATIVES="+("PASS" if controlled else "HOLD"),flush=True)
    print("P167_MASKED_ORIGINAL_TEST="+("HISTORICAL_FAIL_UNWAIVED" if masked_historical_failure else "UNEXPECTED_HOLD"),flush=True)
    print("P167_P76_WRONG_BRANCH_ORIGINAL_NEGATIVE="+("PASS" if original_wrong_branch_pass else "HOLD"),flush=True)
    print("P167_FULL_PRODUCT_REGRESSIONS=0/3",flush=True)
    print("P167_PRODUCTION_RELEASE=HOLD",flush=True)
    return 0 if controlled and masked_historical_failure and original_wrong_branch_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
