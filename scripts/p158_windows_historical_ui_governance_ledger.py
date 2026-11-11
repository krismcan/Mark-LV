"""P158 original-historical and versioned post-P133 UI Windows governance.

Expected historical failures remain native exit 1 and FAIL/HOLD in the ledger.
No original tests are skipped, edited, masked, reclassified or counted as PASS.
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

BASE = "061888b3515a2923dc44eb2f17eb46e768266761"
BRANCH = "byok-c1-p158-historical-connection-ui-contract-governance-20261111"
ROOT = Path(__file__).resolve().parents[1]
PINNED_HISTORICAL_FILES = (
    "tests/test_p133_connection_launch.py",
    "tests/test_p86_live_pending_status_integration.py",
    "tests/test_p87_readonly_custody_observation.py",
    "tests/test_p88_pending_observation_lifecycle.py",
    "tests/test_pending_custody_status_view.py",
    "tests/test_phase_831_effect_isolation.py",
    "tests/test_local_user_scope_byok.py",
    "tests/test_windows_credential_backend.py",
    "tests/phase8_byok_c1_p76_scope.py",
    "tests/phase8_byok_c1_p85_scope.py",
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/secrets/windows_credential.py",
    "scripts/p139_native_fs_verified_local_temp_root.py",
    "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
)
SECURE_ENV_DELETE = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY",
    "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "NAYEON_INTERNAL_SECRET",
)
EXACT_ORIGINAL_HOLDS = {
    "original_pre_p133_p86": {
        "test_live_connection_page_default_is_explicitly_unobserved",
        "test_no_credential_action_and_no_implicit_refresh",
    },
    "original_pre_p133_p87": {
        "test_production_default_remains_not_observed_without_any_session",
    },
    "original_phase831_import_closure": {
        "test_static_production_import_closure_forbids_test_and_effect_routes",
    },
}
EXACT_ORIGINAL_ERRORS = {
    "original_phase831_import_closure": {
        "tearDownModule",
    },
}
FOCUSED = (
    ("current_p158_versioned_successor",
     "tests.test_p158_versioned_connection_ui_contract", 9, True),
    ("original_p133_explicit_manual_launch",
     "tests.test_p133_connection_launch", 25, True),
    ("original_p132_fake_credential_tk",
     "tests.test_local_user_scope_byok", 36, True),
    ("original_p84_bounded_pending_view",
     "tests.test_pending_custody_status_view", 6, True),
    ("original_pre_p133_p86",
     "tests.test_p86_live_pending_status_integration", 7, False),
    ("original_pre_p133_p87",
     "tests.test_p87_readonly_custody_observation", 18, False),
    ("original_p88_synthetic_lease",
     "tests.test_p88_pending_observation_lifecycle", 10, True),
    ("original_phase831_import_closure",
     "tests.test_phase_831_effect_isolation.Phase831EffectIsolationTests."
     "test_static_production_import_closure_forbids_test_and_effect_routes", 1, False),
)
COUNT = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
FAILED = re.compile(r"^FAILED \(([^)]+)\)$", re.M)


def _git(*args: str) -> str:
    p = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True,
        stdin=subprocess.DEVNULL, timeout=20, check=True,
    )
    return p.stdout.decode("utf8", "replace").strip()


def _pin_original():
    for path in PINNED_HISTORICAL_FILES:
        present = _git("rev-parse", "HEAD:"+path)
        prior = _git("rev-parse", BASE+":"+path)
        if present != prior:
            raise RuntimeError("P158 historical source/test mutation detected: "+path)
    # Original P86/P87 really still assert two, deliberately not the new three.
    original_p86 = (ROOT/"tests/test_p86_live_pending_status_integration.py").read_text("utf8")
    original_p87 = (ROOT/"tests/test_p87_readonly_custody_observation.py").read_text("utf8")
    for original in (original_p86, original_p87):
        if "ttk.Button" not in original or "), 2)" not in original:
            raise RuntimeError("P158 original two-button claim was changed")
    print("P158_17_PINNED_ORIGINAL_SECURITY_AND_SOURCE_BLOBS_IDENTICAL=PASS",flush=True)


def _child(label: str, module: str, count: int, should_pass: bool,
           *, safe_temp: Path, dest: Path) -> dict:
    env = os.environ.copy()
    for key in SECURE_ENV_DELETE:
        env.pop(key,None)
    env.update({
        "TEMP":str(safe_temp), "TMP":str(safe_temp), "TMPDIR":str(safe_temp),
        "PYTHONDONTWRITEBYTECODE":"1",
    })
    output = dest/(label+".log")
    started = time.monotonic()
    try:
        with output.open("wb") as log:
            p = subprocess.run(
                [sys.executable, "-B", "-m", "unittest", "-v", module],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT,
                timeout=90, check=False,
            )
        code = p.returncode
    except subprocess.TimeoutExpired:
        code = 124
    except OSError:
        code = 125
    raw = output.read_bytes() if output.exists() else b""
    txt = raw.decode("utf8","replace").replace("\r\n","\n")
    actual = COUNT.findall(txt)
    actual_count = int(actual[-1]) if actual else None
    failures = re.findall(r"^FAIL: ([^( \n]+)",txt,re.M)
    errors = re.findall(r"^ERROR: ([^( \n]+)",txt,re.M)
    footer = FAILED.findall(txt)
    ok_footer = bool(re.search(r"^OK\s*$",txt,re.M))
    if should_pass:
        proof = (
            code == 0 and actual_count == count and
            not failures and not errors and ok_footer
        )
        disposition = "PASS" if proof else "UNEXPECTED_FAIL"
    else:
        expected_failures = EXACT_ORIGINAL_HOLDS[label]
        expected_errors = EXACT_ORIGINAL_ERRORS.get(label,set())
        proof = (
            code == 1 and actual_count == count and
            len(failures)==len(expected_failures) and
            set(failures)==expected_failures and
            len(errors)==len(expected_errors) and
            set(errors)==expected_errors and
            bool(footer) and
            (f"failures={len(failures)}" in footer[-1]) and
            (not expected_errors or f"errors={len(errors)}" in footer[-1])
        )
        disposition = "ORIGINAL_FAIL_HOLD" if proof else "UNEXPECTED_FAILURE_DRIFT"
    result = {
        "label":label, "invoked_original_unmodified":label!="current_p158_versioned_successor",
        "test_id_or_module":module,
        "native_exit":code, "unittest_count":actual_count,
        "original_failed_test_names":failures,
        "original_error_names":errors, "original_exact_negative_disposition":not should_pass,
        "disposition":disposition, "expected_disposition_proved":bool(proof),
        "log_sha256":hashlib.sha256(raw).hexdigest().upper(),
        "log_bytes":len(raw), "elapsed_seconds":round(time.monotonic()-started,3),
        "log_file":output.name,
    }
    print("P158_CASE="+label+
          "|EXIT="+str(code)+"|COUNT="+str(actual_count)+
          "|DISPOSITION="+disposition+
          "|EXPECTED_PROVED="+str(proof)+
          "|SHA256="+result["log_sha256"],flush=True)
    return result


def main():
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME")!=BRANCH:
        raise RuntimeError("P158 exact hosted original branch required")
    head = _git("rev-parse","HEAD")
    if head!=os.environ.get("GITHUB_SHA") or _git("merge-base",BASE,"HEAD")!=BASE:
        raise RuntimeError("P158 source SHA does not descend exact P157")
    _pin_original()
    out = Path(os.environ["RUNNER_TEMP"])/"nayeon-p158-ui-governance-evidence"
    out.mkdir(parents=True,exist_ok=True)
    temp = Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made = False
    rows = []
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P158 temp root unexpectedly pre-existing")
        os.mkdir(temp)
        made = True
        _verify_original_handle_policy(str(temp))
        print("P158_UNCHANGED_P139_GENUINE_NATIVE_TEMP_HANDLE_GUARD=PASS",flush=True)
        for label,module,count,green in FOCUSED:
            rows.append(_child(label,module,count,green,safe_temp=temp,dest=out))
    finally:
        if made:
            st=temp.lstat()
            if temp.is_symlink() or getattr(st,"st_file_attributes",0)&0x400:
                raise RuntimeError("P158 refused potentially reparse-point cleanup")
            shutil.rmtree(temp)
    originals = [r for r in rows if r["invoked_original_unmodified"]]
    total = sum(r["unittest_count"] or 0 for r in rows)
    original_failures=sum(len(r["original_failed_test_names"]) for r in originals)
    original_errors=sum(len(r["original_error_names"]) for r in originals)
    current_new = next(r for r in rows if r["label"]=="current_p158_versioned_successor")
    ledger = {
        "checkpoint":"P158", "source_sha":head,"source_parent":BASE,
        "native_windows_runner":os.environ.get("RUNNER_OS"),
        "pinned_historical_original_blobs":list(PINNED_HISTORICAL_FILES),
        "user_scoped_new_successor_test_count":current_new["unittest_count"],
        "all_invoked_test_count":total,
        "unchanged_original_tests_count":sum(r["unittest_count"] or 0 for r in originals),
        "unchanged_original_failed_test_count":original_failures,
        "unchanged_original_teardown_error_count":original_errors,
        "native_children":rows,
        "original_historical_fails_reported_as_PASS":False,
        "qualified_security_reviewer_signoff":"NOT_OBTAINED",
        "qualified_historical_test_governance_signoff":"NOT_OBTAINED",
        "full_product_unfiltered_accepted_windows_regressions":"0/3",
        "privileged_C1_G0_to_G6":"OPEN",
        "production_release":"HOLD",
    }
    (out/"p158_windows_versioned_ui_governance_ledger.json").write_text(
        json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8"
    )
    print("P158_ORIGINAL_HISTORICAL_SECURITY_TESTS_UNCHANGED=TRUE",flush=True)
    print("P158_ORIGINAL_TEST_FAIL_HOLD_COUNT="+str(original_failures),flush=True)
    print("P158_ORIGINAL_TEARDOWN_ERROR_COUNT="+str(original_errors),flush=True)
    print("P158_QUALIFIED_INDEPENDENT_REVIEW=NOT_OBTAINED",flush=True)
    print("P158_FULL_PRODUCT_WINDOWS_REGRESSIONS=0/3",flush=True)
    print("P158_RELEASE=HOLD",flush=True)
    return 0 if len(rows)==len(FOCUSED) and all(r["expected_disposition_proved"] for r in rows) else 1


if __name__=="__main__":
    raise SystemExit(main())
