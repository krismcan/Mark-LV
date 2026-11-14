"""P207: source-pinned genuine Windows P132/P133 review and P49/C1 native denial.

No real API keys, provider validation, live WinCred, executable install or
service launch. Each positive effect is a fake in-memory test adapter ONLY.
Never count selected fake/native negatives as a full product regression.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from scripts.p206_windows_credential_effect_ownership import (
    ROOT, PRIOR_BLOBS, run_suite, sha256,
)

P206 = "d2e31ecc53e7e4c115b00bb527dcc7eb9723d2e9"
BRANCH = "byok-c1-p207-native-consent-design-acceptance-20261114"
CHANGED = {
    "tests/test_p207_user_scope_native_consent_review.py",
    "docs/byok-c1-p207-native-consent-design-acceptance.md",
    "scripts/p207_windows_native_consent_acceptance_prep.py",
    ".github/workflows/p207-windows-native-consent-review.yml",
}


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=30, check=False)
    if p.returncode:
        raise RuntimeError("P207 failed exact source custody command")
    return p.stdout.decode("utf8").strip()


def original_source() -> dict:
    if (sys.platform != "win32" or os.getenv("GITHUB_ACTIONS") != "true"
        or os.getenv("RUNNER_OS") != "Windows"
        or os.getenv("GITHUB_EVENT_NAME") != "push"
        or os.getenv("GITHUB_REPOSITORY") != "krismcan/Mark-LV"
        or os.getenv("GITHUB_REF_NAME") != BRANCH):
        raise RuntimeError("P207 requires native GitHub-hosted Windows push")
    head = git("rev-parse", "HEAD")
    if head != os.getenv("GITHUB_SHA") or git("merge-base", P206, "HEAD") != P206:
        raise RuntimeError("P207 P206 parent/event source mismatch")
    if set(git("diff", "--name-only", P206, "HEAD").splitlines()) != CHANGED:
        raise RuntimeError("P207 unexpected historical source edit")
    if git("status", "--porcelain=v1", "-uall"):
        raise RuntimeError("P207 dirty source custody")
    original = {}
    for path, sha in sorted(PRIOR_BLOBS.items()):
        before = git("rev-parse", P206 + ":" + path)
        now = git("rev-parse", "HEAD:" + path)
        if before != now or now != sha:
            raise RuntimeError("P207 original source blob changed " + path)
        original[path] = {"blob": now, "disk_SHA256": sha256((ROOT/path).read_bytes())}
    # Also protect the P206 actual negative witness and dormant effect holder.
    for path in ("tests/test_p206_unified_effect_ownership.py",
                 "nayeon/brain/p206_legacy_effect_hold_candidate.py",
                 "scripts/p206_windows_credential_effect_ownership.py"):
        if git("rev-parse", P206+":"+path) != git("rev-parse","HEAD:"+path):
            raise RuntimeError("P207 P206 security baseline edited " + path)
    return {"event_HEAD":head, "exact_P206_parent":P206,
            "only_four_new_paths":sorted(CHANGED), "original_source": original}


def main() -> int:
    out=Path(os.environ.get("RUNNER_TEMP", str(ROOT)))/"nayeon-p207-native-consent"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
        "checkpoint":"P207",
        "H":"HOLD_P132_DIRECT_PYTHON_EFFECT_AND_G3_RESTART_GAP",
        "C":"ACTUAL_SOURCE_REVIEW_PACKAGE_AND_FAKE_ONLY_TESTS",
        "R":"PRODUCTION_HOLD",
        "real_key":"NO_GO", "release":"HOLD",
        "full_product_accepted_regressions":"0/3",
        "GOV_SEC_REL":"SEVEN_INDEPENDENT_DECISIONS_OPEN",
        "signed_native_UI_and_service":"NOT_APPROVED",
        "trusted_native_effect_owner":"NOT_IMPLEMENTED",
        "P132_user_scope":"SEPARATE_REDUCED_THREAT_MODEL_DRAFT",
    }
    ok=False
    try:
        before=original_source()
        ledger["source_before"]=before
        suites=[
            ("P207_actual_original_P132_fake_review",
             ["discover","-s","tests","-p","test_local_user_scope_byok.py","-v"],36),
            ("P206_previous_fake_bypass_and_hold",
             ["discover","-s","tests","-p","test_p206_unified_effect_ownership.py","-v"],12),
            ("P207_new_source_native_consent_negative",
             ["discover","-s","tests","-p","test_p207_user_scope_native_consent_review.py","-v"],14),
            ("P207_original_P49_C1_native_denial",
             ["-v",
              "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_02_original_full_P49_native_release_and_WinCred_denial_20_cases",
              "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_03_current_candidate_service_host_remains_denial_24_cases"],2),
        ]
        for label,args,count in suites:
            result=run_suite(label,args,out/(label+".log"))
            ledger[label]=result
            if not result["complete_OK"] or result["test_footer"] != [str(count)]:
                raise RuntimeError("P207 original Windows suite failed "+label)
        native_labels=("p205_original_P49_20","p205_candidate_C1_host_24")
        for label in native_labels:
            native_dir=Path(os.environ["RUNNER_TEMP"])/"nayeon-p205-key-gates"
            compile_log=native_dir/(label+"_compiler.log")
            test_log=native_dir/(label+"_native.log")
            if not compile_log.is_file() or not test_log.is_file():
                raise RuntimeError("P207 original CSharp compiler/native executable logs absent")
            ledger[label]={
                "original_compiler_exit":0,
                "original_compiler_log_SHA256":sha256(compile_log.read_bytes()),
                "original_native_executable_log_SHA256":sha256(test_log.read_bytes()),
            }
        after=original_source()
        ledger["source_after"]=after
        if after != before:
            raise RuntimeError("P207 original Git/source mutated across Windows tests")
        ok=True
        print("P207_WINDOWS_P132_36_P206_12_NEW_14_NATIVE_44=106_SELECTED_PASS",flush=True)
        print("P207_REAL_KEY=NO_GO|PRODUCTION=HOLD|FULL_WINDOWS=0/3",flush=True)
        print("P207_CONSENT_DESIGN_PACKAGE=READY_FOR_EXTERNAL_INDEPENDENT_REVIEW",flush=True)
        print("P207_NATIVE_EFFECTS_SERVICE_AND_PROVIDER_CALLS=NONE",flush=True)
    except BaseException as ex:
        ledger["failure"] = type(ex).__name__+": "+str(ex)
        print("P207_GENUINE_WINDOWS_SOURCE_HOLD="+type(ex).__name__,flush=True)
    finally:
        ledger["isolated_P207_review_package_complete_NOT_external_acceptance"]=ok
        (out/"p207_native_consent_HCR_ledger.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if ok else 1


if __name__=="__main__":
    raise SystemExit(main())
