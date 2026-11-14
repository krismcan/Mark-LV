"""P210: real Windows source-bound Python->native synthetic negative integration.

The P210 executable is compiled with C1_SYNTHETIC_TEST only and accepts a
fixed scenario name, never WinCred effect, key, target path or consent token.
This test does not create a trusted production IPC or signed service. P132
direct Python WinCred remains a HIGH unresolved release blocker.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from scripts.p207_windows_native_consent_acceptance_prep import ROOT,git
from scripts.p206_windows_credential_effect_ownership import PRIOR_BLOBS,run_suite,sha256
from scripts.p208_windows_synthetic_terminal_owner import native as p208_native,CANDIDATE
from scripts.p209_windows_protected_synthetic_custody import p209_native

P209="fb851c6d19ec7000aab3e56c2db3dd78707933ae"
BRANCH="byok-c1-p210-controlled-python-native-integration-20261114"
ADDED={
 "native_c1_candidate/P210SyntheticBoundaryExecutable.cs",
 "tests/test_p210_python_native_synthetic_integration.py",
 "scripts/p210_windows_python_native_synthetic_integration.py",
 "docs/byok-c1-p210-controlled-integration-negative-evidence.md",
 ".github/workflows/p210-windows-python-native-integration.yml",
}
PRIOR_CHECK=[
 "native_c1_candidate/CustodyService.cs",
 "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs",
 "native_c1_candidate/P208SyntheticTerminalOwner.cs",
 "native_c1_candidate/P209SyntheticDurableCustody.cs",
 "native_c1_candidate/P209SyntheticDurableCustodyTests.cs",
 "tests/test_p209_user_scope_native_consent_review.py",
 "tests/test_p207_user_scope_native_consent_review.py",
 "tests/test_p206_unified_effect_ownership.py",
 "nayeon/brain/local_byok_user_scope.py",
 "nayeon/secrets/windows_credential.py",
 "nayeon/desktop_alpha/local_byok_launch_bridge.py",
 "nayeon/desktop_alpha/local_byok_window.py",
]
def custody():
    if (sys.platform!="win32" or os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("RUNNER_OS")!="Windows"
        or os.getenv("GITHUB_EVENT_NAME")!="push"
        or os.getenv("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH):
        raise RuntimeError("P210 requires genuine hosted Windows event source")
    head=git("rev-parse","HEAD")
    if head!=os.getenv("GITHUB_SHA") or git("merge-base",P209,"HEAD")!=P209:
        raise RuntimeError("P210 exact event HEAD/P209 ancestor mismatch")
    if set(git("diff","--name-only",P209,"HEAD").splitlines())!=ADDED:
        raise RuntimeError("P210 modified original security/product source")
    if git("status","--porcelain=v1","-uall"):
        raise RuntimeError("P210 source checkout dirty")
    pins={}
    for path,sha in PRIOR_BLOBS.items():
        if git("rev-parse","HEAD:"+path)!=sha or git("rev-parse",P209+":"+path)!=sha:
            raise RuntimeError("P210 original source changed "+path)
        pins[path]={"git_blob":sha,"file_SHA256":sha256((ROOT/path).read_bytes())}
    for path in PRIOR_CHECK:
        # Missing optional historical test is not silently asserted passing:
        # only pin existing paths at exact parent.
        prior=subprocess.run(["git","cat-file","-e",P209+":"+path],
            cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
        if prior.returncode!=0:
            if path=="tests/test_p209_user_scope_native_consent_review.py":
                continue
            raise RuntimeError("P210 original source unavailable "+path)
        if git("rev-parse","HEAD:"+path)!=git("rev-parse",P209+":"+path):
            raise RuntimeError("P210 original comparator modified "+path)
    return {"checkpoint":"P210","head":head,"parent":P209,
            "only_five_additive_paths":sorted(ADDED),"original_SHA_pins":pins}

def compile_native_bridge(out:Path)->dict:
    csc=Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
    if sys.platform!="win32" or not csc.is_file():
        raise RuntimeError("P210 genuine x64 native CSharp compiler not present")
    frozen=ROOT/"tests/p99_original_native_c1_denial"
    old=sorted(p for p in frozen.glob("*.cs") if p.name not in
        ("CustodyService.cs","FullOriginalNativeDenialTests.cs"))
    directory=ROOT/"native_c1_candidate"
    files=old+[directory/p for p in CANDIDATE]+[
        directory/"P208SyntheticTerminalOwner.cs",
        directory/"P209SyntheticDurableCustody.cs",
        directory/"P210SyntheticBoundaryExecutable.cs"]
    if len(old)!=10 or any(not p.is_file() for p in files):
        raise RuntimeError("P210 actual original P49/C1 native source inventory invalid")
    source=(directory/"P210SyntheticBoundaryExecutable.cs").read_text("utf8")
    if ("#if C1_SYNTHETIC_TEST" not in source or
        any(term in source for term in ("CredWriteW(","CredDeleteW(",
              "ServiceBase.Run(","DllImport(","WindowsCredentialBackend("))):
        raise RuntimeError("P210 test-only native negative isolation violated")
    exe=out/"p210_synthetic_python_native.exe"
    cmd=[str(csc),"/nologo","/target:exe","/platform:x64",
         "/define:C1_SYNTHETIC_TEST","/r:System.ServiceProcess.dll",
         "/r:System.Security.dll","/main:P210SyntheticBoundaryExecutable",
         "/out:"+str(exe)]+[str(f) for f in files]
    c=subprocess.run(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90,check=False)
    compiler_log=out/"p210_native_compiler.log"
    compiler_log.write_bytes(c.stdout)
    if c.returncode!=0 or c.stdout.strip():
        raise RuntimeError("P210 native compiler failed/issued diagnostics, preserve log")
    return {"path":str(exe),"native_csc_exit":c.returncode,
            "compiler_log_SHA256":sha256(c.stdout),
            "compiled_exe_SHA256":sha256(exe.read_bytes()),
            "review_only_synthetic_CSharp":True}

def main()->int:
    out=Path(os.environ.get("RUNNER_TEMP",str(ROOT)))/"nayeon-p210-integration"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
      "checkpoint":"P210",
      "H":"HOLD_LEGACY_P132_DIRECT_WINCRED_G1_G3_NO_EXTERNAL_ACCEPTANCE",
      "C":"TEST_ONLY_ACTUAL_PYTHON_NATIVE_WINDOWS_PROCESS_NEGATIVE_INTEGRATION",
      "R":"PRODUCTION_HOLD",
      "real_key_R0_R4":"NO_GO",
      "production_P0_P5":"HOLD",
      "G0_G6":"OPEN",
      "independent_GOV_SEC_REL":"OPEN_SEVEN",
      "full_unfiltered_accepted_Windows_regressions":"0/3",
      "real_WinCred_or_provider_effects":"NONE",
      "P132_python_mutation_route":"STILL_REACHABLE_UNMODIFIED",
    }
    done=False
    try:
        before=custody();ledger["before"]=before
        suite=[
          ("p132_36",["discover","-s","tests","-p","test_local_user_scope_byok.py","-v"],36),
          ("p206_12",["discover","-s","tests","-p","test_p206_unified_effect_ownership.py","-v"],12),
          ("p207_14",["discover","-s","tests","-p","test_p207_user_scope_native_consent_review.py","-v"],14),
          ("p49_native20_c1_native24",["-v",
            "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_02_original_full_P49_native_release_and_WinCred_denial_20_cases",
            "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_03_current_candidate_service_host_remains_denial_24_cases"],2),
        ]
        for label,args,expected in suite:
            evidence=run_suite(label,args,out/(label+".log"))
            ledger[label]=evidence
            if not evidence["complete_OK"] or evidence["test_footer"]!=[str(expected)]:
                raise RuntimeError("P210 existing Windows original functional negative failed "+label)
        ledger["p208_native20"]=p208_native(out)
        ledger["p209_DPAPI_native18"]=p209_native(out)
        bridge=compile_native_bridge(out)
        ledger["p210_compiler"]=bridge
        os.environ["P210_NATIVE_EXE"]=bridge["path"]
        new=run_suite("p210_python_to_native13",
            ["discover","-s","tests","-p",
             "test_p210_python_native_synthetic_integration.py","-v"],
            out/"p210_python_to_native13.log")
        ledger["p210_python_to_native13"]=new
        if not new["complete_OK"] or new["test_footer"]!=["13"]:
            raise RuntimeError("P210 genuine Windows Python-to-native source-bound negatives FAILED")
        after=custody();ledger["after"]=after
        if before!=after:
            raise RuntimeError("P210 source identity changed during native tests")
        done=True
        print("P210_SELECTED_WINDOWS_P132_36_P206_12_P207_14_P49_20_C1_24_P208_20_P209_18_P210_13=157_PASS",flush=True)
        print("P210_CROSS_LANGUAGE_PROCESS_AND_DPAPI_NEGATIVES=EXECUTED",flush=True)
        print("P210_DIRECT_P132_WINCRED_UNIFIED_OWNERSHIP=NOT_FIXED",flush=True)
        print("P210_REALKEY=NO_GO|PRODUCTION=HOLD|FULL_WINDOWS=0/3",flush=True)
    except BaseException as exc:
        ledger["error"]=type(exc).__name__+": "+str(exc)
        print("P210_GENUINE_WINDOWS_HOLD="+type(exc).__name__,flush=True)
    finally:
        ledger["isolated_P210_negative_integration_complete_NOT_release"]=done
        (out/"p210_HCR_source_and_OS_ledger.json").write_text(
          json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if done else 1

if __name__=="__main__":
    raise SystemExit(main())
