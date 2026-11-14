"""P213 Windows source-bound executable build-gate integration and original H/C/R.

Actual Python subprocess exit 41 proves the candidate high-assurance product
build is refused BEFORE any output. A second subprocess may emit a single
non-executable review TEXT note; it is not a product artifact. Real key NO-GO,
production HOLD, external approvals and three full product regressions OPEN.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.p207_windows_native_consent_acceptance_prep import ROOT,git
from scripts.p206_windows_credential_effect_ownership import (
    PRIOR_BLOBS,run_suite,sha256,
)
from scripts.p208_windows_synthetic_terminal_owner import native as p208_native
from scripts.p209_windows_protected_synthetic_custody import p209_native
from scripts.p210_windows_python_native_synthetic_integration import (
    compile_native_bridge,
)
from nayeon.brain.p213_readonly_windows_signer_observer import source_pins_unissued
from nayeon.brain.p211_high_assurance_package_quarantine import (
    inspect_current_source_tree,
)

P212="e5d8f5f92a21d7314bf7ef6a7e9b2f9a95bc658f"
BRANCH="byok-c1-p213-readonly-windows-signed-service-admission-20261114"
ADDED={
 "nayeon/brain/p213_readonly_windows_signer_observer.py",
 "tests/test_p213_real_windows_authenticode_service_admission.py",
 "scripts/p213_windows_signed_service_observation.py",
 "docs/byok-c1-p213-windows-authenticode-service-admission.md",
 ".github/workflows/p213-windows-authenticode-service-admission.yml",
}
UNMODIFIED=(
 "nayeon/secrets/windows_credential.py",
 "nayeon/brain/local_byok_user_scope.py",
 "nayeon/desktop_alpha/local_byok_launch_bridge.py",
 "nayeon/desktop_alpha/local_byok_window.py",
 "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
 "native_c1_candidate/CustodyService.cs",
 "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs",
 "native_c1_candidate/P208SyntheticTerminalOwner.cs",
 "native_c1_candidate/P209SyntheticDurableCustody.cs",
 "native_c1_candidate/P210SyntheticBoundaryExecutable.cs",
 "nayeon/brain/p211_high_assurance_package_quarantine.py",
 "tests/test_p211_high_assurance_package_quarantine.py",
 "tests/test_p210_python_native_synthetic_integration.py",
 "scripts/p212_high_assurance_build_gate.py",
 "tests/test_p212_mandatory_high_assurance_build_gate.py",
 "nayeon/desktop_alpha/application.py",
)

def custody()->dict:
    if (sys.platform!="win32"
        or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH):
        raise RuntimeError("P213 genuine hosted Windows push event REQUIRED")
    head=git("rev-parse","HEAD")
    if (head!=os.environ.get("GITHUB_SHA")
        or git("merge-base",P212,"HEAD")!=P212):
        raise RuntimeError("P213 exact Git event/P211 parent mismatch")
    if set(git("diff","--name-only",P212,"HEAD").splitlines())!=ADDED:
        raise RuntimeError("P213 original product/security source changed")
    if git("status","--porcelain=v1","-uall"):
        raise RuntimeError("P213 Git checkout not clean")
    pins={}
    for path,sha in sorted(PRIOR_BLOBS.items()):
        if (git("rev-parse","HEAD:"+path)!=sha
            or git("rev-parse",P212+":"+path)!=sha):
            raise RuntimeError("P213 original P205 blob changed "+path)
        pins[path]={"git_blob":sha,"disk_SHA256":sha256((ROOT/path).read_bytes())}
    for path in UNMODIFIED:
        if git("rev-parse","HEAD:"+path)!=git("rev-parse",P211+":"+path):
            raise RuntimeError("P213 original named source changed "+path)
    return {"event_HEAD":head,"exact_P212_ancestor":P212,
            "five_additive_paths":sorted(ADDED),
            "original_source_pins":pins}

def exact_build_entrypoint(out:Path)->dict:
    """Exercise REAL Python process/OS exit, not a mocked function result."""
    before=list(out.iterdir())
    cmd=[sys.executable,"-B","-m",
         "scripts.p212_high_assurance_build_gate"]
    env=os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"]="1"
    # Untrusted release claims must have no effect on P211/P212.
    env["NAYEON_P212_RELEASE_GO"]="true"
    env["NAYEON_P212_SIGNER"]="fake-test-only"

    bad=subprocess.run(cmd+["--attempt-ha-release"],cwd=ROOT,env=env,
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,timeout=45,check=False)
    log=out/"p212_high_assurance_product_build_refused.log"
    log.write_bytes(bad.stdout+bad.stderr)
    txt=bad.stdout.decode("utf8","replace").replace("\r\n","\n")
    if (bad.returncode!=41 or bad.stderr or
        "P212_BUILD=DENIED_LEGACY_EFFECT_PATH" not in txt
        or "P212_OUTPUT_PRODUCT_COUNT=0" not in txt
        or "P212_REAL_KEY=NO_GO|PRODUCTION=HOLD" not in txt):
        raise RuntimeError("P213 CLI product build did not fail closed")
    # Before review mode, only original run log is permitted.
    if (set(p.name for p in out.iterdir())
        != set(p.name for p in before)|{log.name}):
        raise RuntimeError("P213 denied product build emitted extra artifact")

    review_dir=Path(os.environ["RUNNER_TEMP"])/"nayeon-p212-build-preflight"
    if review_dir.exists():
        raise RuntimeError("P213 review staging unexpectedly exists")
    review_dir.mkdir()
    good=subprocess.run(cmd+["--emit-review-only"],cwd=ROOT,env=env,
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,timeout=45,check=False)
    receipt_log=out/"p212_nonexecutable_review_only.log"
    receipt_log.write_bytes(good.stdout+good.stderr)
    s=good.stdout.decode("utf8","replace").replace("\r\n","\n")
    if (good.returncode!=0 or good.stderr or
        "P212_REVIEW=NONEXECUTABLE_TEXT_CREATED" not in s or
        "P212_PRODUCT_PACKAGE=NONE|RELEASE=HOLD" not in s):
        raise RuntimeError("P213 fixed review evidence mode failed")
    members=list(review_dir.iterdir())
    if (len(members)!=1 or members[0].name!="P212_QUARANTINE_REVIEW_NO_GO.txt"
        or not members[0].is_file() or members[0].is_symlink()
        or members[0].stat().st_size>2048):
        raise RuntimeError("P213 review folder contains unapproved payloads")
    note=members[0].read_bytes()
    if (b"HIGH_ASSURANCE_RELEASE=NO_GO" not in note
        or b"ARTIFACT_CLASS=NONEXECUTABLE_REVIEW_TEXT_ONLY" not in note
        or b"NO_RELEASE_AUTHORITY_GRANTED" not in note):
        raise RuntimeError("P213 metadata falsely implies production release")
    # All executable/distributable outputs are prohibited. This deliberately
    # is not a PyInstaller, signed installer or product build.
    forbidden={".exe",".dll",".py",".pyc",".pyd",".msi",".msix",".whl",".zip"}
    if any(p.suffix.lower() in forbidden for p in review_dir.rglob("*")):
        raise RuntimeError("P213 unsafe executable or bundled file present")
    return {
      "attempted_real_subprocess_OS_exit":bad.returncode,
      "attempt_stdout_SHA256":sha256(bad.stdout),
      "attempt_stderr_SHA256":sha256(bad.stderr),
      "attempt_log_SHA256":sha256(log.read_bytes()),
      "product_files_created":0,
      "actual_review_subprocess_OS_exit":good.returncode,
      "review_stdout_SHA256":sha256(good.stdout),
      "review_note_SHA256":sha256(note),
      "review_note_bytes":len(note),
      "review_file_count":1,
      "contains_production_payload":False,
      "mandatory_p211_source_refusal":"LEGACY_EFFECT_PATH",
      "real_key_R0_R4":"NO_GO",
      "release_P0_P5":"HOLD",
    }

def main()->int:
    out=Path(os.environ.get("RUNNER_TEMP",str(ROOT)))/"nayeon-p213-evidence"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
       "checkpoint":"P213",
       "H":"HOLD_MICROSOFT_OS_SIGNATURE_NOT_NAYEON_SERVICE_TRUST_ROOT",
       "C":"REAL_WINDOWS_READONLY_AUTHENTICODE_SIGNED_VS_UNSIGNED_NATIVE_SOURCE",
       "R":"PRODUCTION_HOLD",
       "real_key_R0_R4":"NO_GO",
       "production_P0_P5":"HOLD",
       "independent_GOV_SEC_REL":"SEVEN_REVIEW_DECISIONS_OPEN",
       "G0_G6":"OPEN",
       "full_unfiltered_accepted_Windows_product_regressions":"0/3",
       "P132_real_source_Python_WinCred":"REACHABLE_UNGOVERNED",
       "signed_native_UI_service_antirollback":"NOT_APPROVED",
       "C2_provider_validation":"NOT_AUTHORISED",
    }
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        if not source_pins_unissued():
            raise RuntimeError("P213 unsigned service candidate must not be enrolled")
        risk=inspect_current_source_tree(ROOT)
        if not (risk.exact_legacy_source_readable
                and risk.high_assurance_legacy_risk_present
                and risk.frozen_companion_pins_absent
                and risk.native_c1_service_denial_only):
            raise RuntimeError("P213 original real P132/source hold witness differs")
        ledger["P212_product_build_denial_rechecked_by_unmodified_tests"]="YES_TESTED_NO_RELEASE"
        suites=[
         ("p132_original_36",["discover","-s","tests","-p","test_local_user_scope_byok.py","-v"],36),
         ("p206_original_12",["discover","-s","tests","-p","test_p206_unified_effect_ownership.py","-v"],12),
         ("p207_original_14",["discover","-s","tests","-p","test_p207_user_scope_native_consent_review.py","-v"],14),
         ("p49_native20_c1_native24",["-v",
          "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_02_original_full_P49_native_release_and_WinCred_denial_20_cases",
          "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_03_current_candidate_service_host_remains_denial_24_cases"],2),
        ]
        for label,args,n in suites:
            result=run_suite(label,args,out/(label+".log"))
            ledger[label]=result
            if not result["complete_OK"] or result["test_footer"]!=[str(n)]:
                raise RuntimeError("P213 prior Windows selected functional suite failed "+label)
        ledger["p208_original_native_20"]=p208_native(out)
        ledger["p209_real_DPAPI_native_18"]=p209_native(out)
        bridge=compile_native_bridge(out)
        ledger["p210_native_compiler"]=bridge
        os.environ["P210_NATIVE_EXE"]=bridge["path"]
        for label,file,count in (
          ("p210_python_native_13","test_p210_python_native_synthetic_integration.py",13),
          ("p211_package_refusal_22","test_p211_high_assurance_package_quarantine.py",22),
          ("p212_build_gate_20","test_p212_mandatory_high_assurance_build_gate.py",20),
          ("p213_authenticode_live20","test_p213_real_windows_authenticode_service_admission.py",20),
        ):
            result=run_suite(label,["discover","-s","tests","-p",file,"-v"],
                             out/(label+".log"))
            ledger[label]=result
            if not result["complete_OK"] or result["test_footer"]!=[str(count)]:
                raise RuntimeError("P213 original Windows selected suite failed "+label)
        after=custody();ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P213 source custody changed after actual Windows tests")
        complete=True
        print("P213_WINDOWS_ORIGINAL_199_NATIVE_SIGNATURE_20=219_SELECTED_PASS",flush=True)
        print("P213_OS_AUTHENTICODE_WINDOWS_SIGNED_REFERENCE_AND_UNSIGNED_C1=READ_ONLY",flush=True)
        print("P213_SIGNED_SERVICE_TRUST_ROOT=NOT_ENROLLED",flush=True)
        print("P213_REAL_KEY=NO_GO|PRODUCTION=HOLD|FULL_WINDOWS=0/3",flush=True)
    except BaseException as error:
        ledger["error"]=type(error).__name__+": "+str(error)
        print("P213_GENUINE_WINDOWS_FAILURE_HOLD="+type(error).__name__,flush=True)
    finally:
        ledger["isolated_P213_readonly_signature_observation_complete_NOT_release"]=complete
        (out/"p213_HCR_original_Windows_signature_and_source_ledger.json").write_text(
          json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1


if __name__=="__main__":
    raise SystemExit(main())
