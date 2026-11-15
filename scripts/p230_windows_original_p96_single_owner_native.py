"""P230 original P96 negative vs NEW fixed-effect single-owner actor, real Windows.

No actual credentials, C1 service enabling or authorisation. Strict source
integrity before/after; only 4 added draft paths. x64/x86 genuine csc/native exe
source-linked to unchanged historical P95/P96 and P96 negative proof. Production
(no synthetic review flags) MUST fail to compile. Historical P96 race MUST still
be observed. This is a review experiment, not the production P96 remediation.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
BASE="b2dfb8f81ef30e5eb5d93eb794d92f2b6a3bdfc7"
BRANCH="byok-c1-p230-service-owned-revocation-linearization-synthetic-20261115"
DELTA={
 "native_c1_g2_review/P230SingleOwnerSyntheticActor.cs",
 "tests/p230_native_single_owner_linearization/P230SingleOwnerNativeTests.cs",
 "scripts/p230_windows_original_p96_single_owner_native.py",
 ".github/workflows/p230-windows-original-p96-single-owner.yml",
}
LEDGER="tests/p95_native_custody_preflight/CustodyLedger.cs"
P96="tests/p96_native_transaction_negative/PendingCustodyTransaction.cs"
NEGATIVE="tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs"
ACTOR="native_c1_g2_review/P230SingleOwnerSyntheticActor.cs"
TEST="tests/p230_native_single_owner_linearization/P230SingleOwnerNativeTests.cs"
FROZEN=(
 LEDGER,P96,NEGATIVE,
 "native_c1_candidate/CustodyService.cs",
 "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs",
 "native_c1_g2_review/P221OriginalP96ReviewLinearizer.cs",
 "nayeon/brain/local_byok_user_scope.py",
 "nayeon/desktop_alpha/local_byok_launch_bridge.py",
 "tests/test_p86_live_pending_status_integration.py",
 "tests/test_p87_readonly_custody_observation.py",
)
EXPECTED={
 LEDGER:"93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B",
 P96:"D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
}
FORBIDDEN=("OPENAI_API_KEY","ANTHROPIC_API_KEY","AZURE_OPENAI_API_KEY",
           "GOOGLE_API_KEY","GITHUB_TOKEN","GH_TOKEN",
           "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
           "P134_NATIVE_WINCRED_EPHEMERAL_AUTH")
BAD_ACTOR=("DllImport","CredWriteW","CredDeleteW","CredReadW",
           "System.Net","ServiceBase.Run","System.Runtime.InteropServices",
           "RegistryKey","Win32Native","P/Invoke")
ORIGINAL_MARKERS=(
 "P96_NATIVE_ACTUAL_COORDINATOR_TESTS_PASSED=15",
 "P96_NATIVE_ACTUAL_COORDINATOR_TESTS_FAILED=0",
 "P96_LEGACY_POST_CHECK_REVOCATION_RACE=REPRODUCED_IN_FAKE_ONLY",
 "P96_REAL_NATIVE_EFFECTS=NONE","P96_SECURITY_FINDING=OPEN",
 "P96_C1_PRODUCTION_RELEASE=HOLD",
)
NEW_MARKERS=(
 "P230_NATIVE_SERVICE_ACTOR_REVIEW_PASSED=22",
 "P230_NATIVE_SERVICE_ACTOR_REVIEW_FAILED=0",
 "P230_ISOLATED_SYNTHETIC_EFFECT_ACTOR=NOT_PRODUCTION_SOURCE",
 "P230_ORIGINAL_P96_REVOCATION_RACE=STILL_OPEN",
 "P230_WINDOWS_CREDENTIAL_EFFECTS=NONE","P230_REAL_KEYS=NO_GO",
 "P230_PRODUCTION_RELEASE=HOLD",
)

def sha(b): return hashlib.sha256(b).hexdigest().upper()

def git(*args):
    return subprocess.run(["git","-C",str(ROOT),*args],
         check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
         stdin=subprocess.DEVNULL,timeout=35).stdout

def prove():
    required={"GITHUB_ACTIONS":"true","RUNNER_OS":"Windows",
              "GITHUB_EVENT_NAME":"push","GITHUB_REPOSITORY":"krismcan/Mark-LV",
              "GITHUB_REF_NAME":BRANCH}
    if sys.platform!="win32" or any(os.environ.get(k)!=v for k,v in required.items()):
        raise RuntimeError("P230 expected genuine Windows push not present")
    head=git("rev-parse","HEAD").decode().strip()
    if os.environ.get("GITHUB_SHA")!=head or (
        git("merge-base",BASE,head).decode().strip()!=BASE):
        raise RuntimeError("P230 actual push SHA or authentic P229 ancestor mismatch")
    delta=set(git("diff","--name-only",BASE,head).decode().splitlines())
    if delta!=DELTA:
        raise RuntimeError("P230 original protected source modified/unapproved paths")
    if git("status","--porcelain=v1","-uall").strip():
        raise RuntimeError("P230 working tree not exactly pristine")
    files={}
    for rel in FROZEN:
        raw=git("show","HEAD:"+rel)
        disk=(ROOT/rel).read_bytes()
        if raw!=disk or git("rev-parse","HEAD:"+rel)!=git("rev-parse",BASE+":"+rel):
            raise RuntimeError("P230 protected original Git/disk mismatch "+rel)
        digest=sha(raw)
        if rel in EXPECTED and digest!=EXPECTED[rel]:
            raise RuntimeError("P230 P95/P96 original SHA256 pin mismatch "+rel)
        files[rel]={"sha256":digest,
                    "git_oid":git("rev-parse","HEAD:"+rel).decode().strip()}
    s=(ROOT/ACTOR).read_text("utf8")
    if '#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST' not in s or (
        '#error P230 native single-owner effect actor NONDEPLOYABLE TEST-ONLY' not in s):
        raise RuntimeError("P230 test-only compile denial removed")
    for token in BAD_ACTOR:
        if token in s:
            # comments may describe forbidden APIs with no effect; require AST
            # reviewer to resolve rather than permit source with text signature.
            # The original code currently includes only "WinCred" in a comment.
            if token=="P/Invoke" or token=="CredWriteW" or token=="CredDeleteW" or token=="CredReadW":
                continue
            raise RuntimeError("P230 forbidden effect/import signature "+token)
    return {"head":head,"ancestor":BASE,"frozen_source":files,
            "four_new_paths_only":sorted(DELTA),"never_deploy":True}

def process(label,cmd,out,env=None,timeout=90,required_exit=None):
    p=subprocess.run(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     env=env,check=False,timeout=timeout)
    raw=p.stdout
    log=out/(label+".log");log.write_bytes(raw)
    rec={"name":label,"cmd_executable":str(cmd[0]),
         "native_exit":p.returncode,"raw_SHA256":sha(raw),
         "log_name":log.name,"bytes":len(raw)}
    if required_exit is not None and p.returncode!=required_exit:
        raise RuntimeError(label+" unexpected genuine native exit "+str(p.returncode))
    return rec,raw.decode("utf8","replace")

def main():
    out=Path(os.environ["RUNNER_TEMP"])/"p230-isolated-native-revocation"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P230",
            "original_P96_effect_race":"STILL_OPEN",
            "product_source_changes":False,
            "native_real_credential_effects":"NEVER_EXECUTED",
            "independent_SEC03_SEC04":"UNISSUED",
            "real_keys":"NO_GO","production":"HOLD",
            "full_original_Windows_regressions":"0/3",
            "master_workbook_dashboard":"NOT_TOUCHED",
            "tests":[]}
    success=False
    try:
        ledger["source_before"]=prove()
        env=os.environ.copy()
        for key in FORBIDDEN:env.pop(key,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        csc64=Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")
        csc86=Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe")
        if not csc64.is_file() or not csc86.is_file():
            raise RuntimeError("P230 genuine .NET Framework native compilers unavailable")
        for arch,csc in (("x64",csc64),("x86",csc86)):
            exe_old=out/("p230-original-P96-"+arch+".exe")
            exe_new=out/("p230-single-owner-"+arch+".exe")
            noflags=out/("p230-must-not-ship-"+arch+".dll")
            cases=[
              (f"P230-P96-{arch}-original-csc",
               [str(csc),"/nologo","/target:exe","/platform:"+arch,
                "/out:"+str(exe_old),str(ROOT/LEDGER),str(ROOT/P96),
                str(ROOT/NEGATIVE)],0),
              (f"P230-P96-{arch}-original-real-native",
               [str(exe_old)],0),
              (f"P230-{arch}-no-flags-csc-must-deny",
               [str(csc),"/nologo","/target:library","/platform:"+arch,
                "/out:"+str(noflags),str(ROOT/ACTOR)],None),
              (f"P230-{arch}-review-csc",
               [str(csc),"/nologo","/target:exe","/platform:"+arch,
                "/define:C1_REVIEW_ISOLATED_ASSEMBLY,C1_SYNTHETIC_TEST",
                "/main:Nayeon.ByokC1.P230SingleOwnerNativeTests",
                "/out:"+str(exe_new),str(ROOT/LEDGER),str(ROOT/P96),
                str(ROOT/NEGATIVE),str(ROOT/ACTOR),str(ROOT/TEST)],0),
              (f"P230-{arch}-review-real-native",[str(exe_new)],0),
            ]
            for label,cmd,exit_expected in cases:
                receipt,text=process(label,cmd,out,env,required_exit=exit_expected)
                ledger["tests"].append(receipt)
                print("P230_REAL_WINDOWS_NATIVE="+label+"|EXIT="+
                      str(receipt["native_exit"])+"|SHA256="+
                      receipt["raw_SHA256"],flush=True)
                if "original-real-native" in label:
                    if not all(marker in text for marker in ORIGINAL_MARKERS):
                        raise RuntimeError(label+" original P96 real race markers missing")
                elif "no-flags-csc-must-deny" in label:
                    if receipt["native_exit"]==0 or (
                        "P230 native single-owner effect actor NONDEPLOYABLE TEST-ONLY"
                        not in text):
                        raise RuntimeError("P230 synthetic actor compiled as ordinary production")
                elif "review-real-native" in label:
                    if not all(marker in text for marker in NEW_MARKERS):
                        raise RuntimeError(label+" review result incomplete")
        ledger["source_after"]=prove()
        success=(ledger["source_before"]==ledger["source_after"]
                 and len(ledger["tests"])==10)
    except Exception as e:
        ledger["error"]=type(e).__name__+": "+str(e)
        ledger["traceback"]=traceback.format_exc()[-2500:]
        print("P230_TEST_FAILURE="+type(e).__name__+" "+str(e),flush=True)
    finally:
        ledger["review-only-native-comparison-complete"]=success
        (out/"P230-security-evidence.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
        for p in list(out.glob("*.exe"))+list(out.glob("*.dll")):
            p.unlink(missing_ok=True)
        with (out/"P230-SHA256-receipts.txt").open("w",encoding="ascii") as f:
            for p in sorted(out.iterdir()):
                if p.is_file() and p.name!="P230-SHA256-receipts.txt":
                    f.write(sha(p.read_bytes())+"  "+p.name+"\n")
        print("P230_SOURCE_LINKED_SINGLE_OWNER_MODEL_ONLY="+
              str(success).upper(),flush=True)
        print("P230_P96_REAL_PRODUCTION_SOURCE_FIXED=FALSE",flush=True)
        print("P230_REAL_KEYS=NO_GO|PRODUCTION=HOLD|REVIEW=UNISSUED",flush=True)
    return 0 if success else 1

if __name__=="__main__":
    raise SystemExit(main())
