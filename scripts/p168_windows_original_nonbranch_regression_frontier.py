"""P168: authenticated archived/current original regression frontier (NOT acceptance).

Replay three ENTIRE unmodified original Phase8.31, Phase8.32, and WinCred
test modules on genuine Windows; verify original P144 evidence and preserve
all original results, including legitimate FAIL, ERROR and TIMEOUT.
No historical test changes, credential/live provider use or release GO.
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
BASE = "90955080782cd7449561d21935918a2ac17b66c2"
BRANCH = "byok-c1-p168-original-lifecycle-wincred-regression-triage-20261112"
EXPECTED_ADDITIVE = {
    "scripts/p168_windows_original_nonbranch_regression_frontier.py",
    ".github/workflows/p168-windows-original-nonbranch-regression-frontier.yml",
    "docs/byok-c1-p168-original-regression-frontier-review-packet.md",
}
ORIGINAL = (
    ("tests.test_phase_831_effect_isolation", 19, 2,
     "AE2C8A41E2B0A2EB2100F9896C5870797DFB8BB50D9D00F15993F8DC563BDC9F"),
    ("tests.test_phase_832_lifecycle_assurance", 14, 5,
     "0A4F667918C40FCCEB6FBBE651FC44D1364A790D04ED386C3C920F7FD48C31E2"),
    ("tests.test_windows_credential_backend", 24, 2,
     "4EA9F9EF62EFD5E239F5C90C624CC62A3C3AA015A89D6EA71DA14A63033FAEF0"),
)
P144_ARTIFACT = 13804256598
P144_ARCHIVE_SHA = "4D62B64CB9872601AF271B8D47DE1CE7B76468E9013F0A9A8417CF9DC79C41E3"
P144_MANIFEST = "p144_original_residual_manifest.json"
COUNT = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
ISSUE = re.compile(r"^(FAIL|ERROR): (.+)$", re.M)
FROZEN_REFUSAL = "P76 offline source refused: wrong exact P76 prototype branch"
ENV_SECRETS = {"GITHUB_TOKEN", "GH_TOKEN", "P168_READ_ONLY_ARCHIVE_TOKEN",
               "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY",
               "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def git(*args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(ROOT), *args], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=True, timeout=25)
    return result.stdout


def custody() -> dict:
    _guard_runner()
    if not (sys.platform == "win32"
            and os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("RUNNER_OS") == "Windows"
            and os.environ.get("GITHUB_EVENT_NAME") == "push"
            and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.environ.get("GITHUB_REF_NAME") == BRANCH
            and os.environ.get("RUNNER_TEMP")):
        raise RuntimeError("P168 native verified Windows push event required")
    current = git("rev-parse", "HEAD").decode().strip()
    if (current != os.environ.get("GITHUB_SHA")
            or git("branch", "--show-current").decode().strip() != BRANCH
            or git("merge-base", "HEAD", BASE).decode().strip() != BASE):
        raise RuntimeError("P168 current source or exact P167 lineage mismatch")
    if git("status", "--porcelain=v1").strip():
        raise RuntimeError("P168 modified/disposable source checkout refused")
    changed = set(git("diff", "--name-only", BASE, "HEAD").decode().splitlines())
    if changed != EXPECTED_ADDITIVE:
        raise RuntimeError("P168 source/test/product changed outside three new audit files")
    for name in changed:
        if git("ls-tree", "--name-only", BASE, "--", name).strip():
            raise RuntimeError("P168 previously existing code path modified")
    original_modules = [p for p in git("ls-tree", "-r", "--name-only", BASE, "--", "tests")
                        .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    current_modules = [p for p in git("ls-files", "--", "tests/test_*.py")
                       .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    if len(original_modules) != 171 or sorted(original_modules) != sorted(current_modules):
        raise RuntimeError("P168 original 171 test-module inventory drift")
    assert_paths = sorted(set(PROTECTED) | {
        name.replace(".", "/") + ".py" for name, *_ in ORIGINAL
    })
    secured = {}
    for name in assert_paths:
        before = git("show", BASE + ":" + name)
        after = git("show", "HEAD:" + name)
        disk = (ROOT / name).read_bytes()
        if before != after or after != disk:
            raise RuntimeError("P168 original test or protected source mutated: " + name)
        secured[name] = sha(after)
    return {"head": current, "parent": BASE, "original_test_modules": 171,
            "exact_new_evidence_files": sorted(changed),
            "protected_original_sha256": secured}


def authenticate_p144(token: str) -> dict:
    if not token or len(token) < 8:
        raise RuntimeError("P168 read-only Actions artifact permission unavailable")
    raw = _download_artifact(P144_ARTIFACT, P144_ARCHIVE_SHA, token)
    if sha(raw) != P144_ARCHIVE_SHA:
        raise RuntimeError("P144 original archive SHA256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise RuntimeError("P144 archive corruption")
        names = z.namelist()
        if len(names) != len(set(names)) or any("/" in name or "\\" in name or
                                               name.startswith(".") for name in names):
            raise RuntimeError("P144 ambiguous archive entry")
        if len(names) != 16 or P144_MANIFEST not in names:
            raise RuntimeError("P144 original 15 full-module archive changed")
        data = json.loads(z.read(P144_MANIFEST))
        if (data.get("summary") != {"HOLD": 15, "PASS": 0, "TIMEOUT": 0}
                or len(data.get("results", [])) != 15
                or data.get("original_historical_assertions_modified") is not False
                or data.get("release_approved") is not False):
            raise RuntimeError("P144 original manifest historical disposition changed")
        by_module = {item["module"]: item for item in data["results"]}
        if len(by_module) != 15:
            raise RuntimeError("P144 original manifest duplicate modules")
        authenticated = {}
        for module, expected, failures, old_hash in ORIGINAL:
            if module not in by_module:
                raise RuntimeError("P144 original module absent " + module)
            entry = by_module[module]
            name = "p144_" + module.replace(".", "_") + ".log"
            raw_log = z.read(name)
            text = raw_log.decode("utf-8", "replace").replace("\r\n", "\n")
            headings = ISSUE.findall(text)
            counts = COUNT.findall(text)
            if (sha(raw_log) != old_hash
                    or entry.get("log_sha256") != old_hash
                    or entry.get("completed_unittest_count") != expected
                    or entry.get("native_exit") != 1
                    or entry.get("status") != "HOLD"
                    or len(headings) != failures
                    or len(entry.get("failure_ids", [])) != failures
                    or len(counts) != 1
                    or int(counts[0]) != expected
                    or not re.search(r"^FAILED \(", text, re.M)):
                raise RuntimeError("P144 complete genuine original log/subtest disposition changed")
            root_causes = {
                "historical_branch_refusal": FROZEN_REFUSAL in text,
                "phase831_production_import_closure": "workspace_window.py" in text
                    and "test_static_production_import_closure_forbids_test_and_effect_routes" in text,
                "phase831_fake_tk_survivor": "retired fake Tk roots still live" in text,
                "phase832_first_statement_thread_gate": "self._require_creator_thread()" in text,
                "wincred_unapproved_static_secret_consumer": "'nayeon.secrets.contracts' unexpectedly found" in text,
            }
            authenticated[module] = {
                "original_module": module,
                "original_P144_unchanged_test_count": expected,
                "original_P144_native_exit": 1,
                "original_P144_genuine_FAILURE_OR_ERROR_records": failures,
                "original_P144_raw_log_sha256": old_hash,
                "observed_P144_causal_markers": root_causes,
            }
    if not (
        authenticated["tests.test_phase_831_effect_isolation"]["observed_P144_causal_markers"]["phase831_production_import_closure"]
        and authenticated["tests.test_phase_831_effect_isolation"]["observed_P144_causal_markers"]["phase831_fake_tk_survivor"]
        and authenticated["tests.test_phase_832_lifecycle_assurance"]["observed_P144_causal_markers"]["phase832_first_statement_thread_gate"]
        and authenticated["tests.test_windows_credential_backend"]["observed_P144_causal_markers"]["wincred_unapproved_static_secret_consumer"]
        and authenticated["tests.test_windows_credential_backend"]["observed_P144_causal_markers"]["historical_branch_refusal"]
    ):
        raise RuntimeError("P144 nonbranch causal marker mismatch")
    return {"archive_id": P144_ARTIFACT, "original_archive_sha256": P144_ARCHIVE_SHA,
            "original_15_modules_all_HOLD": True,
            "authenticated_three_original_modules": authenticated}


def run_original(module: str, expected: int, temp_root: Path, evidence_root: Path) -> dict:
    env = os.environ.copy()
    for key in list(env):
        if key in ENV_SECRETS or key.endswith("_API_KEY") or key.endswith("_SECRET"):
            env.pop(key, None)
    env.update({"TEMP": str(temp_root), "TMP": str(temp_root),
                "TMPDIR": str(temp_root), "PYTHONDONTWRITEBYTECODE": "1"})
    name = "p168_actual_" + module.replace(".", "_") + ".log"
    log_path = evidence_root / name
    start = time.monotonic()
    timeout = False
    with log_path.open("wb") as file:
        proc = subprocess.Popen([sys.executable, "-B", "-m", "unittest", "-v", module],
              cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=file,
              stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        try:
            exit_code = proc.wait(timeout=90)
        except subprocess.TimeoutExpired:
            timeout, exit_code = True, 124
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=False, timeout=15)
            try:
                proc.wait(timeout=6)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    raw = log_path.read_bytes()
    text = raw.decode("utf8", "replace").replace("\r\n", "\n")
    count_hits = COUNT.findall(text)
    count = int(count_hits[-1]) if count_hits else None
    issues = [{"kind": kind, "original_unmodified_test": label.strip()}
              for kind, label in ISSUE.findall(text)]
    original_pass = (exit_code == 0 and count == expected
                     and re.search(r"^OK\s*$", text, re.M) is not None)
    original_hold = (exit_code == 1 and count == expected
                     and re.search(r"^FAILED \(", text, re.M) is not None and len(issues)>0)
    verdict = ("PASS" if original_pass else "HOLD" if original_hold
               else "TIMEOUT" if timeout else "INCOMPLETE")
    print("P168_ACTUAL_NATIVE_MODULE="+module+"|EXIT="+str(exit_code)+
          "|RAN="+str(count)+"|VERDICT="+verdict+"|ISSUES="+str(len(issues)),flush=True)
    print("P168_ACTUAL_RAW_LOG_SHA256="+module+"|"+sha(raw),flush=True)
    return {"original_unmodified_full_module": module, "expected_original_tests": expected,
            "actual_native_exit": exit_code, "original_unittest_count": count,
            "actual_original_verdict": verdict, "native_timed_out": timeout,
            "genuine_original_named_FAIL_ERROR_records": issues,
            "archived_raw_log": name, "archived_raw_log_bytes": len(raw),
            "archived_raw_log_sha256": sha(raw),
            "seconds": round(time.monotonic()-start,3),
            "P76_historical_wrong_branch_marker_observed": FROZEN_REFUSAL in text,
            "production_import_closure_marker_observed": "workspace_window.py" in text
                and "test_static_production_import_closure_forbids_test_and_effect_routes" in text,
            "fake_Tk_survivor_marker_observed": "retired fake Tk roots still live" in text,
            "static_thread_gate_first_statement_marker_observed": "self._require_creator_thread()" in text,
            "WinCred_secret_consumer_allowlist_marker_observed": "'nayeon.secrets.contracts' unexpectedly found" in text,
        }


def main() -> int:
    before = custody()
    historical = authenticate_p144(os.environ.get("P168_READ_ONLY_ARCHIVE_TOKEN", ""))
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p168-original-regression-frontier"
    evidence.mkdir(parents=True, exist_ok=True)
    temp = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    made = False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P168 disposable Windows test root collision")
        os.mkdir(temp)
        made = True
        _verify_original_handle_policy(str(temp))
        outcomes = {module: run_original(module, count, temp, evidence)
                    for module, count, *_ in ORIGINAL}
    finally:
        if made:
            stat = temp.lstat()
            if temp.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                raise RuntimeError("P168 linked Windows TEMP removal refused")
            shutil.rmtree(temp)
    if custody() != before:
        raise RuntimeError("P168 original source changed during diagnostics")
    finished = all(x["actual_original_verdict"] in ("PASS", "HOLD")
                   and x["original_unittest_count"] == count
                   for (module, count, *_), x in zip(ORIGINAL,outcomes.values()))
    report = {
        "checkpoint": "P168", "custody_before_after_identical": before,
        "previous_P144_authentic_native_failures_preserved": historical,
        "P168_actual_unmodified_entire_original_native_module_results": outcomes,
        "three_original_modules_completed_genuinely": finished,
        "p167_archived_causality_not_waived": True,
        "historical_P76_P85_holds_unwaived": True,
        "original_test_failures_not_reclassified_or_discarded": True,
        "independent_security_and_test_governance_reviewer_GO": "NOT_OBTAINED",
        "historical_H": "HOLD", "current_C": "REDUCED_SCOPE_CANDIDATE_ONLY",
        "production_R": "HOLD", "accepted_complete_full_product_regressions": "0/3",
        "real_CredWrite_CredDelete_provider_validation_or_signing": "NOT_AUTHORIZED_NOT_ATTEMPTED",
        "no_qualified_production_main_helper_installer_SAC_WDAC_code_integrity_GO": True,
        "privileged_BYOK_C1_G0_to_G6": "OPEN",
        "next_review_questions": [
            "Independent reviewer must decide historical branch test-governance, never waive original P76/P85",
            "Assess Phase8.31 static production import closure and retired fake Tk-root owner; do not suppress teardown",
            "Review Phase8.32 direct-owned methods first-statement contract and actual creator-thread behavior separately",
            "Review WinCred legacy importer / secret consumer allowlist and provenance, no blanket allowlist expansion",
            "Production release still requires signed and Code Integrity-approved executables and three complete original native Windows full-product regressions",
        ],
    }
    (evidence/"p168_source_bound_original_regression_frontier.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("P168_HISTORICAL_P144_15_COMPLETE_HOLD_MODULES_SHA256_AUTHENTICATED=YES",flush=True)
    print("P168_GENUINE_ALL_THREE_ORIGINAL_MODULES_COMPLETE="+str(finished),flush=True)
    print("P168_ACCEPTED_COMPLETE_FULL_PRODUCT_WINDOWS=0/3",flush=True)
    print("P168_INDEPENDENT_SECURITY_GO=NOT_OBTAINED",flush=True)
    print("P168_PRODUCTION_RELEASE=HOLD",flush=True)
    return 0 if finished else 1


if __name__ == "__main__":
    raise SystemExit(main())
