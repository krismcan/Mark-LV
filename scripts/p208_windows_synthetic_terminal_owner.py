"""P208 genuine Windows native C# synthetic terminal actor; no real WinCred."""
from __future__ import annotations
import json, os, re, subprocess, sys
from pathlib import Path
from scripts.p207_windows_native_consent_acceptance_prep import ROOT, git
from scripts.p206_windows_credential_effect_ownership import PRIOR_BLOBS, run_suite, sha256

P207="5118e29aee5a02d80e329894a45d5e9c06c4c394"
BRANCH="byok-c1-p208-synthetic-terminal-actor-20261114"
ADDED={
 "native_c1_candidate/P208SyntheticTerminalOwner.cs",
 "native_c1_candidate/P208SyntheticTerminalOwnerTests.cs",
 "scripts/p208_windows_synthetic_terminal_owner.py",
 "docs/byok-c1-p208-synthetic-terminal-owner.md",
 ".github/workflows/p208-windows-synthetic-terminal-owner.yml",
}
CANDIDATE=["CustodyService.cs","ServiceOwnedAdmissionBoundary.cs",
 "ServiceBoundRequestIdentity.cs","NativeJ2ProtectedReadOnlyPreflight.cs",
 "CandidateCredentialEffectHold.cs","IsolatedCandidateContracts.cs",
 "CandidateProtectedReadOnlySnapshot.cs"]

def custody():
    if (sys.platform!="win32" or os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("RUNNER_OS")!="Windows"
        or os.getenv("GITHUB_EVENT_NAME")!="push"
        or os.getenv("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH):
        raise RuntimeError("P208 genuine Windows event required")
    head=git("rev-parse","HEAD")
    if head!=os.getenv("GITHUB_SHA") or git("merge-base",P207,"HEAD")!=P207:
        raise RuntimeError("P208 Git event/parent mismatch")
    if set(git("diff","--name-only",P207,"HEAD").splitlines())!=ADDED:
        raise RuntimeError("P208 unapproved historical code mutation")
    if git("status","--porcelain=v1","-uall"):
        raise RuntimeError("P208 source dirty")
    pins={}
    for path,expected in PRIOR_BLOBS.items():
        if git("rev-parse","HEAD:"+path)!=expected or git("rev-parse",P207+":"+path)!=expected:
            raise RuntimeError("P208 original source altered "+path)
        pins[path]={"blob":expected,"disk_SHA256":sha256((ROOT/path).read_bytes())}
    for path in ["native_c1_candidate/CustodyService.cs",
                 "native_c1_candidate/ServiceHostAdmissionTests.cs",
                 "tests/test_p207_user_scope_native_consent_review.py",
                 "tests/test_p206_unified_effect_ownership.py"]:
        if git("rev-parse","HEAD:"+path)!=git("rev-parse",P207+":"+path):
            raise RuntimeError("P208 security-test comparator modified "+path)
    return {"head":head,"parent":P207,"only_five_additions":sorted(ADDED),"original_pins":pins}

def native(out):
    csc=Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
    if not csc.is_file(): raise RuntimeError("P208 genuine native CSharp compiler absent")
    frozen=ROOT/"tests/p99_original_native_c1_denial"
    prior=sorted(x for x in frozen.glob("*.cs") if x.name not in
      ("CustodyService.cs","FullOriginalNativeDenialTests.cs"))
    directory=ROOT/"native_c1_candidate"
    sources=prior+[directory/x for x in CANDIDATE]+[
      directory/"P208SyntheticTerminalOwner.cs",
      directory/"P208SyntheticTerminalOwnerTests.cs"]
    if len(prior)!=10 or any(not x.is_file() for x in sources):
        raise RuntimeError("P208 exact native original source inventory absent")
    code=(directory/"P208SyntheticTerminalOwner.cs").read_text("utf8")
    if ("#if C1_SYNTHETIC_TEST" not in code
        or any(s in code for s in ("CredWriteW(","CredDeleteW(","DllImport(","ServiceBase.Run("))):
        raise RuntimeError("P208 test-only source isolation violated")
    exe=out/"p208_native_synthetic.exe"
    args=[str(csc),"/nologo","/target:exe","/platform:x64",
          "/define:C1_SYNTHETIC_TEST","/r:System.ServiceProcess.dll",
          "/main:P208SyntheticTerminalOwnerTests","/out:"+str(exe)]+[str(x) for x in sources]
    c=subprocess.run(args,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,timeout=90,check=False)
    (out/"p208_compiler.log").write_bytes(c.stdout)
    if c.returncode!=0 or c.stdout.strip():
        raise RuntimeError("P208 actual CSharp compiler emitted errors/warnings")
    p=subprocess.run([str(exe)],cwd=ROOT,stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     timeout=90,check=False)
    (out/"p208_native_20.log").write_bytes(p.stdout)
    txt=p.stdout.decode("utf8","replace").replace("\r\n","\n")
    if (p.returncode!=0 or len(re.findall(r"^PASS ",txt,re.M))!=20
        or "P208_SYNTHETIC_NATIVE_TERMINAL_PASSED=20" not in txt
        or "P208_SYNTHETIC_NATIVE_TERMINAL_FAILED=0" not in txt
        or re.search(r"^FAIL ",txt,re.M)):
        raise RuntimeError("P208 20-case original Windows native synthetic actor FAILED")
    return {"compiler_exit":c.returncode,"compiler_SHA256":sha256(c.stdout),
            "native_exe_exit":p.returncode,"native_log_SHA256":sha256(p.stdout),
            "native_synthetic_cases":20,"real_WinCred_effects":0}

def main():
    out=Path(os.environ.get("RUNNER_TEMP",str(ROOT)))/"nayeon-p208-terminal"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P208","H":"HOLD_NO_G1_G3_P132_DIRECT_EFFECT",
            "C":"ISOLATED_TEST_ONLY_NATIVE_ONE_USE_OWNER",
            "R":"PRODUCTION_HOLD","real_key":"NO_GO",
            "full_unfiltered_accepted_regressions":"0/3",
            "external_GOV_SEC_REL":"SEVEN_OPEN","BYOK_C2":"NOT_AUTHORISED"}
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
        for label,args,count in suites:
            res=run_suite(label,args,out/(label+".log"))
            ledger[label]=res
            if not res["complete_OK"] or res["test_footer"]!=[str(count)]:
                raise RuntimeError("P208 unchanged original suite FAILED "+label)
        ledger["p208_native"]=native(out)
        after=custody();ledger["after"]=after
        if before!=after:raise RuntimeError("P208 source custody changed during native tests")
        complete=True
        print("P208_REAL_WINDOWS_SELECTED_36_12_14_20_24_20=126_PASS",flush=True)
        print("P208_NATIVE_SYNTHETIC_ONLY_ONE_EFFECT_REPLAY_DENIAL=TESTED",flush=True)
        print("P208_REAL_KEY=NO_GO|PRODUCTION=HOLD|FULL_WINDOWS=0/3",flush=True)
    except BaseException as exc:
        ledger["error"]=type(exc).__name__+": "+str(exc)
        print("P208_GENUINE_WINDOWS_HOLD="+type(exc).__name__,flush=True)
    finally:
        ledger["isolated_candidate_complete_NOT_release"]=complete
        (out/"p208_HCR_ledger.json").write_text(
          json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":raise SystemExit(main())
