"""P211 genuine hosted-Windows test of nondeployable package isolation intake.

No signed package, installer, service, WinCred/key effect, policy change,
trusted IPC or real-key pilot. P132 user-scope capability remains untouched.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from scripts.p207_windows_native_consent_acceptance_prep import ROOT,git
from scripts.p206_windows_credential_effect_ownership import PRIOR_BLOBS,run_suite,sha256
from scripts.p208_windows_synthetic_terminal_owner import native as p208_native
from scripts.p209_windows_protected_synthetic_custody import p209_native
from scripts.p210_windows_python_native_synthetic_integration import compile_native_bridge
from nayeon.brain.p211_high_assurance_package_quarantine import (
    P211Refusal, inspect_current_source_tree, review_high_assurance_package_plan,
)

P210="11a7cc3c314458e4ed8e482d5d48734d225dbeca"
BRANCH="byok-c1-p211-high-assurance-package-isolation-20261114"
NEW={
    "nayeon/brain/p211_high_assurance_package_quarantine.py",
    "tests/test_p211_high_assurance_package_quarantine.py",
    "scripts/p211_windows_package_quarantine_evidence.py",
    "docs/byok-c1-p211-high-assurance-package-isolation.md",
    ".github/workflows/p211-windows-package-isolation.yml",
}
HISTORICAL=[
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/secrets/windows_credential.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "nayeon/desktop_alpha/local_byok_window.py",
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
    "native_c1_candidate/CustodyService.cs",
    "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs",
    "native_c1_candidate/P208SyntheticTerminalOwner.cs",
    "native_c1_candidate/P209SyntheticDurableCustody.cs",
    "native_c1_candidate/P210SyntheticBoundaryExecutable.cs",
    "tests/test_p206_unified_effect_ownership.py",
    "tests/test_p207_user_scope_native_consent_review.py",
    "tests/test_p210_python_native_synthetic_integration.py",
]

def custody():
    if (sys.platform!="win32" or os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("RUNNER_OS")!="Windows"
        or os.getenv("GITHUB_EVENT_NAME")!="push"
        or os.getenv("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH):
        raise RuntimeError("P211 requires genuine GitHub-hosted Windows push")
    head=git("rev-parse","HEAD")
    if head!=os.getenv("GITHUB_SHA") or git("merge-base",P210,"HEAD")!=P210:
        raise RuntimeError("P211 HEAD/event or exact P210 parent mismatch")
    if set(git("diff","--name-only",P210,"HEAD").splitlines())!=NEW:
        raise RuntimeError("P211 existing product/security source changed")
    if git("status","--porcelain=v1","-uall"):
        raise RuntimeError("P211 checkout dirty")
    pins={}
    for path,blob in PRIOR_BLOBS.items():
        actual=git("rev-parse","HEAD:"+path)
        if actual!=blob or git("rev-parse",P210+":"+path)!=blob:
            raise RuntimeError("P211 original P205 code changed "+path)
        pins[path]={"Git_blob":blob,"disk_SHA256":sha256((ROOT/path).read_bytes())}
    for path in HISTORICAL:
        if git("rev-parse","HEAD:"+path)!=git("rev-parse",P210+":"+path):
            raise RuntimeError("P211 previous tested source identity modified "+path)
    return {"HEAD":head,"parent":P210,"only_five_additions":sorted(NEW),
            "original_P205_file_pins":pins}

def main():
    out=Path(os.environ.get("RUNNER_TEMP",str(ROOT)))/"nayeon-p211-isolation"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
      "checkpoint":"P211",
      "H":"HOLD_P132_DIRECT_WINCRED_AND_NO_ENFORCED_RUNTIME_OR_SIGNER",
      "C":"DORMANT_PERMANENT_DENY_HIGH_ASSURANCE_PACKAGE_INTAKE",
      "R":"PRODUCTION_HOLD",
      "real_key_R0_R4":"NO_GO","production_P0_P5":"HOLD",
      "GOV_SEC_REL":"SEVEN_INDEPENDENT_DECISIONS_OPEN",
      "G0_G6":"OPEN",
      "accepted_unfiltered_product_Windows_regressions":"0/3",
      "legacy_P132_route":"REAL_SOURCE_REACHABLE_UNMODIFIED",
      "real_WinCred_or_provider_effects":"ZERO",
      "approved_signer_installer":"NONE",
      "OS_enforced_legacy_effect_isolation":"NOT_IMPLEMENTED",
    }
    success=False
    try:
        before=custody()
        ledger["source_before"]=before
        witness=inspect_current_source_tree(ROOT)
        if (not witness.exact_legacy_source_readable
            or not witness.python_direct_native_credential_effect
            or not witness.p132_product_constructor_and_effect
            or not witness.p133_source_mode_launcher
            or not witness.frozen_companion_pins_absent
            or not witness.native_c1_service_denial_only):
            raise RuntimeError("P211 original source risk/denial witness changed")
        legacy=review_high_assurance_package_plan(ROOT,[
            "nayeon/secrets/windows_credential.py",
            "nayeon/brain/local_byok_user_scope.py",
            "nayeon/desktop_alpha/local_byok_launch_bridge.py",
        ])
        harmless=review_high_assurance_package_plan(ROOT,["P211_QUARANTINE_README.txt"])
        if (legacy.reason!=P211Refusal.LEGACY_EFFECT_PATH
            or harmless.reason!=P211Refusal.ABSENT_RELEASE_AUTHORITY
            or legacy.release_eligible or harmless.release_eligible):
            raise RuntimeError("P211 package quarantine fail-closed acceptance violated")
        ledger["original_source_risk_witness"]={
            "python_Direct_WinCred":witness.python_direct_native_credential_effect,
            "P132_source_constructible":witness.p132_product_constructor_and_effect,
            "P133_offline_launcher":witness.p133_source_mode_launcher,
            "P140_frozen_signer_pins_empty":witness.frozen_companion_pins_absent,
            "native_C1_service_denial":witness.native_c1_service_denial_only,
            "unsafe_plan_refusal":legacy.reason.value,
            "review_only_manifest_refusal":harmless.reason.value,
        }
        suites=[
            ("p132_36",["discover","-s","tests","-p","test_local_user_scope_byok.py","-v"],36),
            ("p206_12",["discover","-s","tests","-p","test_p206_unified_effect_ownership.py","-v"],12),
            ("p207_14",["discover","-s","tests","-p","test_p207_user_scope_native_consent_review.py","-v"],14),
            ("p49_20_native_c1_24",["-v",
             "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_02_original_full_P49_native_release_and_WinCred_denial_20_cases",
             "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_03_current_candidate_service_host_remains_denial_24_cases"],2),
        ]
        for label,args,n in suites:
            result=run_suite(label,args,out/(label+".log"))
            ledger[label]=result
            if not result["complete_OK"] or result["test_footer"]!=[str(n)]:
                raise RuntimeError("P211 original Windows suite failed "+label)
        ledger["p208_native_20"]=p208_native(out)
        ledger["p209_DPAPI_native_18"]=p209_native(out)
        bridge=compile_native_bridge(out)
        ledger["p210_native_compiler"]=bridge
        os.environ["P210_NATIVE_EXE"]=bridge["path"]
        for label,filename,n in (
            ("p210_cross_language_13","test_p210_python_native_synthetic_integration.py",13),
            ("p211_package_quarantine_22","test_p211_high_assurance_package_quarantine.py",22),
        ):
            result=run_suite(label,[
                "discover","-s","tests","-p",filename,"-v"
            ],out/(label+".log"))
            ledger[label]=result
            if not result["complete_OK"] or result["test_footer"]!=[str(n)]:
                raise RuntimeError("P211 original-source Windows suite failed "+label)
        after=custody()
        ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P211 Git source custody changed across Windows executions")
        success=True
        print("P211_GENUINE_WINDOWS_P132_36_P206_12_P207_14_P49_20_C1_24_P208_20_P209_18_P210_13_P211_22=179_SELECTED_PASS",flush=True)
        print("P211_HIGH_ASSURANCE_BUNDLE_INTAKE=PERMANENTLY_DENIED",flush=True)
        print("P211_NO_SIGNED_PRODUCTION_PACKAGE_OR_RUNTIME_ISOLATION",flush=True)
        print("P211_REALKEY=NO_GO|PRODUCTION=HOLD|FULL_PRODUCT_WINDOWS=0/3",flush=True)
    except BaseException as error:
        ledger["failure"]=type(error).__name__+": "+str(error)
        print("P211_GENUINE_WINDOWS_HOLD="+type(error).__name__,flush=True)
    finally:
        ledger["isolated_P211_package_intake_test_complete_NOT_release"]=success
        (out/"p211_HCR_original_source_evidence.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if success else 1


if __name__=="__main__":
    raise SystemExit(main())
