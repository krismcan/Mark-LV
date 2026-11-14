"""P209 actual Windows DPAPI/DACL synthetic custody and P208 native integration.

No API key, live WinCred, privileged service, provider, signing or policy change.
"""
from __future__ import annotations
import json,os,re,subprocess,sys
from pathlib import Path
from scripts.p207_windows_native_consent_acceptance_prep import ROOT,git
from scripts.p206_windows_credential_effect_ownership import PRIOR_BLOBS,run_suite,sha256
from scripts.p208_windows_synthetic_terminal_owner import native as p208_native,CANDIDATE

P208="0ade464c0e0d51a03e9cdb976f36f2351f8ed900"
BRANCH="byok-c1-p209-protected-synthetic-durable-custody-20261114"
NEW={
 "native_c1_candidate/P209SyntheticDurableCustody.cs",
 "native_c1_candidate/P209SyntheticDurableCustodyTests.cs",
 "scripts/p209_windows_protected_synthetic_custody.py",
 "docs/byok-c1-p209-protected-synthetic-custody.md",
 ".github/workflows/p209-windows-protected-synthetic-custody.yml",
}

def custody():
    if (sys.platform!="win32" or os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("RUNNER_OS")!="Windows"
        or os.getenv("GITHUB_EVENT_NAME")!="push"
        or os.getenv("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH):
        raise RuntimeError("P209 actual hosted Windows event required")
    head=git("rev-parse","HEAD")
    if head!=os.getenv("GITHUB_SHA") or git("merge-base",P208,"HEAD")!=P208:
        raise RuntimeError("P209 exact event HEAD/P208 parent invalid")
    if set(git("diff","--name-only",P208,"HEAD").splitlines())!=NEW:
        raise RuntimeError("P209 frozen/previous product source changed")
    if git("status","--porcelain=v1","-uall"):
        raise RuntimeError("P209 checkout dirty")
    pins={}
    for p,sha in PRIOR_BLOBS.items():
        if git("rev-parse",P208+":"+p)!=sha or git("rev-parse","HEAD:"+p)!=sha:
            raise RuntimeError("P209 original source sha mismatch "+p)
        pins[p]={"Git_blob":sha,"disk_SHA256":sha256((ROOT/p).read_bytes())}
    for p in ("native_c1_candidate/CustodyService.cs",
              "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs",
              "native_c1_candidate/P208SyntheticTerminalOwner.cs",
              "native_c1_candidate/P208SyntheticTerminalOwnerTests.cs",
              "tests/test_p207_user_scope_native_consent_review.py"):
        if git("rev-parse",P208+":"+p)!=git("rev-parse","HEAD:"+p):
            raise RuntimeError("P209 prior native/test comparator edited "+p)
    return {"event_HEAD":head,"exact_P208_parent":P208,
            "only_five_additive_paths":sorted(NEW),"original_SHA":pins}

def p209_native(out:Path):
    csc=Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
    if not csc.is_file():raise RuntimeError("P209 real Windows CSharp compiler absent")
    p49=ROOT/"tests/p99_original_native_c1_denial"
    original=sorted(p for p in p49.glob("*.cs") if p.name not in
      ("CustodyService.cs","FullOriginalNativeDenialTests.cs"))
    candidate=ROOT/"native_c1_candidate"
    source=original+[candidate/p for p in CANDIDATE]+[
      candidate/"P208SyntheticTerminalOwner.cs",
      candidate/"P209SyntheticDurableCustody.cs",
      candidate/"P209SyntheticDurableCustodyTests.cs"]
    if len(original)!=10 or any(not p.is_file() for p in source):
        raise RuntimeError("P209 native original source inclusion invalid")
    code=(candidate/"P209SyntheticDurableCustody.cs").read_text("utf8")
    if ("#if C1_SYNTHETIC_TEST" not in code or
        any(x in code for x in ("CredWriteW(","CredDeleteW(","ServiceBase.Run(","DllImport("))):
        raise RuntimeError("P209 real credential effect introduced: HOLD")
    exe=out/"p209_original_native_Dpapi.exe"
    args=[str(csc),"/nologo","/target:exe","/platform:x64",
          "/define:C1_SYNTHETIC_TEST",
          "/r:System.ServiceProcess.dll","/r:System.Security.dll",
          "/main:P209SyntheticDurableCustodyTests",
          "/out:"+str(exe)]+[str(p) for p in source]
    c=subprocess.run(args,cwd=ROOT,stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     timeout=90,check=False)
    (out/"p209_native_compiler.log").write_bytes(c.stdout)
    if c.returncode!=0 or c.stdout.strip():
        raise RuntimeError("P209 genuine CSharp compiler emitted diagnostics")
    p=subprocess.run([str(exe)],cwd=ROOT,stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     timeout=120,check=False)
    (out/"p209_native_18.log").write_bytes(p.stdout)
    txt=p.stdout.decode("utf8","replace").replace("\r\n","\n")
    if (p.returncode!=0 or len(re.findall(r"^PASS ",txt,re.M))!=18 or
        "P209_WINDOWS_PROTECTED_SYNTHETIC_PASSED=18" not in txt or
        "P209_WINDOWS_PROTECTED_SYNTHETIC_FAILED=0" not in txt or
        re.search(r"^FAIL ",txt,re.M)):
        raise RuntimeError("P209 actual Windows DPAPI/DACL restart tests FAILED")
    return {"original_compiler_exit":c.returncode,
            "compiler_log_SHA256":sha256(c.stdout),
            "original_Windows_native_exit":p.returncode,
            "native_log_SHA256":sha256(p.stdout),
            "DPAPI_DACL_Windows_synthetic_cases":18,
            "independent_antirollback_proof":"NO",
            "real_CredWrite_CredDelete_attempts":0}

def main():
    out=Path(os.environ.get("RUNNER_TEMP",str(ROOT)))/"nayeon-p209-dpapi"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P209","H":"HOLD_NO_INDEPENDENT_ANTIROLLBACK_ROOT",
            "C":"WINDOWS_DPAPI_DACL_SYNTHETIC_CUSTODY_CANDIDATE",
            "R":"PRODUCTION_HOLD","real_key":"NO_GO","P0_P5":"HOLD",
            "GOV_SEC_REL":"SEVEN_OPEN","full_product_accepted_Windows":"0/3",
            "P132_direct_Python_WinCred":"OPEN_NOT_SERVICE_GOVERNED"}
    complete=False
    try:
        before=custody();ledger["before"]=before
        suites=[
          ("p132_36",["discover","-s","tests","-p","test_local_user_scope_byok.py","-v"],36),
          ("p206_12",["discover","-s","tests","-p","test_p206_unified_effect_ownership.py","-v"],12),
          ("p207_14",["discover","-s","tests","-p","test_p207_user_scope_native_consent_review.py","-v"],14),
          ("p49_20_c1_24",["-v",
            "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_02_original_full_P49_native_release_and_WinCred_denial_20_cases",
            "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_03_current_candidate_service_host_remains_denial_24_cases"],2)]
        for label,args,n in suites:
            value=run_suite(label,args,out/(label+".log"))
            ledger[label]=value
            if not value["complete_OK"] or value["test_footer"]!=[str(n)]:
                raise RuntimeError("P209 original source prior suite failed "+label)
        ledger["p208_native20"]=p208_native(out)
        ledger["p209_native18"]=p209_native(out)
        after=custody();ledger["after"]=after
        if before!=after:
            raise RuntimeError("P209 original SHA custody changed during test")
        complete=True
        print("P209_GENUINE_WINDOWS_P132_36_P206_12_P207_14_P49_20_C1_24_P208_20_P209_18=144_PASS",flush=True)
        print("P209_DPAPI_USER_DACL_RESTART_ROLLBACK_NEGATIVES=TESTED",flush=True)
        print("P209_ANTIROLLBACK=OPEN|REAL_KEY=NO_GO|PRODUCTION=HOLD|FULL_WINDOWS=0/3",flush=True)
    except BaseException as ex:
        ledger["failure"]=type(ex).__name__+": "+str(ex)
        print("P209_GENUINE_WINDOWS_HOLD="+type(ex).__name__,flush=True)
    finally:
        ledger["isolated_P209_complete_NOT_G3_or_release"]=complete
        (out/"p209_HCR_ledger.json").write_text(json.dumps(
            ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":raise SystemExit(main())
