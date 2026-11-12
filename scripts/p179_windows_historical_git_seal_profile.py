"""P179 — source-preserving Git/seal subprocess profiling, never a release PASS.

Authenticates P178 original Windows test logs then profiles the *unmodified*
historical BYOK B pin-witness case in a fresh hosted Windows Python process.
Only observes real subprocess.run calls and returns original OS results
unchanged. Does not edit, cache, skip, monkeypatch security decisions, or
alter a single historical test file. Profiling changes timing: diagnostic only.
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

from scripts.p139_native_fs_verified_local_temp_root import _guard_runner, _verify_original_handle_policy
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact

ROOT=Path(__file__).resolve().parents[1]
BRANCH="byok-c1-p179-historical-git-seal-performance-isolation-20261112"
P178="f114574ec24001103d9be0c421f6be8ff1ab04c9"
P178_ID=13970391463
P178_SHA="676FAD4608D54EC6CDB40D3A1D7E5355F6587476DDB21DA4CFCE979FC4FC1353"
NEW={
    ".github/workflows/p179-windows-historical-git-seal-profile.yml",
    "docs/byok-c1-p179-historical-git-seal-performance-analysis.md",
    "scripts/p179_windows_historical_git_seal_profile.py",
}
ORIGINAL="tests.test_phase8_byok_b_scope_integrity"
CONTROL=ORIGINAL+".ExactBYOKBTests.test_self_canonicalization_only_zeros_own_single_literal"
HOTSPOT=ORIGINAL+".ExactBYOKBTests.test_each_historical_a_pin_remains_an_active_witness"
FOOTER=re.compile(r"^Ran (\d+) tests? in [0-9.]+s$",re.M)
ISSUES=re.compile(r"^(FAIL|ERROR): (.+)$",re.M)
REVIEWS={k:"OPEN" for k in (
    "GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}
SENSITIVE={"GITHUB_TOKEN","GH_TOKEN","P179_ARCHIVE_TOKEN","OPENAI_API_KEY",
           "AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY","ACTIONS_RUNTIME_TOKEN",
           "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}
OLD_LOGS={
    "p178_original_windows_adjacent_original_control_1.log":
        ("AA819DBBA4E5C291EF2FBFA8B34577F43622B2638051B8DDFC5F57343B21F3E4","PASS",1,0),
    "p178_original_windows_exact_P135_uncompleted_case_1.log":
        ("9E8B0E5BA6F4DD6AD173721E0A2967D1A7199F3E343E12E162287E69634A8338","PASS",1,0),
    "p178_original_windows_entire_original_BYOK_B_module.log":
        ("5E5AD8E76C13B3C44152001C7054E770BD31CDAE7FBB78C86E719B2B1D038C92","TIMEOUT",None,124),
}
P135_CASE="test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused"
ORIGINAL_TWO_FAILS=(
    "test_live_brain_reader_tamper_remains_rejected_after_historical_replay",
    "test_projected_historical_brain_corruption_is_causally_rejected",
)

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        check=True,timeout=40).stdout

def custody()->dict:
    _guard_runner()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",P178,"HEAD").decode().strip()!=P178
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P179 source must be clean authentic hosted Windows exact triggering push")
    actual=set(git("diff","--name-only",P178,"HEAD").decode().splitlines())
    if actual!=NEW or any(git("ls-tree","--name-only",P178,"--",p).strip() for p in NEW):
        raise RuntimeError("P179 only three new diagnostic files may be created")
    if (git("rev-parse",P178+":nayeon")!=git("rev-parse","HEAD:nayeon")
        or git("rev-parse",P178+":tests")!=git("rev-parse","HEAD:tests")):
        raise RuntimeError("P179 entire original product/tests Git tree changed")
    source="tests/test_phase8_byok_b_scope_integrity.py"
    raw=(ROOT/source).read_bytes()
    if raw!=git("show",P178+":"+source) or raw!=git("show","HEAD:"+source):
        raise RuntimeError("P179 historically sealed original BYOK-B test file changed")
    files=[p for p in git("ls-tree","-r","--name-only",P178,"--","tests").decode().splitlines()
           if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(files)!=171:
        raise RuntimeError("P179 original test module inventory drift")
    return {"P179_exact_triggered_head":git("rev-parse","HEAD").decode().strip(),
            "exact_P178_parent":P178,
            "three_new_audit_only_paths":sorted(NEW),
            "all_product_and_historical_tests_bit_identical":True,
            "original_BYOK_B_test_SHA256":sha(raw),
            "original_test_module_count":171}

def authenticate_p178(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P179 requires ephemeral read-only GitHub archive token")
    raw=_download_artifact(P178_ID,P178_SHA,token)
    if sha(raw)!=P178_SHA:
        raise RuntimeError("P179 authentic P178 original Windows archive changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        expected=set(OLD_LOGS)|{"p178_source_authenticated_windows_full_regression_recovery_ledger.json"}
        if (z.testzip() is not None or len(z.namelist())!=4
            or set(z.namelist())!=expected):
            raise RuntimeError("P179 original P178 ZIP inventory/CRC invalid")
        ledger=json.loads(z.read("p178_source_authenticated_windows_full_regression_recovery_ledger.json"))
        rows=ledger.get("original_native_bounded_reproduction",{})
        if (ledger.get("checkpoint")!="P178"
            or ledger.get("source_custody_before",{}).get("authentic_P178_head")!=P178
            or ledger.get("source_custody_before")!=ledger.get("source_custody_after")
            or ledger.get("production_R")!="HOLD"
            or ledger.get("full_product_accepted_Windows")!="0/3"
            or ledger.get("independent_decisions")!=REVIEWS
            or ledger.get("evidence_collection_complete_not_a_regression_pass") is not True
            or ledger.get("original_full_product_regression_recovered") is not False):
            raise RuntimeError("P179 genuine P178 custody / full regression HOLDS changed")
        names={"adjacent_control":list(OLD_LOGS)[0],
               "exact_P135_stalled_case":list(OLD_LOGS)[1],
               "entire_BYOK_B_original_module":list(OLD_LOGS)[2]}
        report={}
        if set(rows)!=set(names):
            raise RuntimeError("P179 P178 three unfiltered native case receipt keys changed")
        for label,filename in names.items():
            pin,status,count,code=OLD_LOGS[filename]
            source=z.read(filename)
            t=source.decode("utf8","replace").replace("\r\n","\n")
            row=rows[label]
            foot=FOOTER.findall(t)
            actual_count=int(foot[-1]) if foot else None
            if (sha(source)!=pin or row.get("complete_raw_SHA256")!=pin
                or row.get("observed_status")!=status
                or row.get("real_native_exit")!=code
                or row.get("original_unittest_count_with_footer")!=count
                or row.get("complete_raw_log")!=filename
                or actual_count!=count):
                raise RuntimeError("P179 original genuine P178 raw result invalid: "+label)
            if status=="PASS" and not re.search(r"^OK\s*$",t,re.M):
                raise RuntimeError("P179 original P178 PASS never established: "+label)
            if status=="TIMEOUT":
                if t.count("Timeout (0:00:20)!")<7:
                    raise RuntimeError("P179 genuine historical eight Python stack dumps missing")
                for test in ORIGINAL_TWO_FAILS:
                    if not re.search(r"^"+test+r" \([^\r\n]+\) \.\.\. FAIL$",t,re.M):
                        raise RuntimeError("P179 original genuine historical module failed case erased")
                if "test_each_historical_a_pin_remains_an_active_witness" not in t:
                    raise RuntimeError("P179 historical focused expensive original case absent")
            report[label]={"status":status,"exit":code,"completed_count":count,
                           "original_raw_SHA256":pin,
                           "original_named_historical_HOLD":list(ORIGINAL_TWO_FAILS) if status=="TIMEOUT" else []}
    return {"artifact_ID":P178_ID,"ZIP_SHA256":sha(raw),
            "original_authentic_Windows_case_provenance":report,
            "P135_three_prior_600s_timeouts_remain_unwaived":True}

# This source string executes in a *fresh* child process. Only the Python
# subprocess.run timing entry is observed; every original command, stdout,
# stderr, return and exception flows unaltered. No cached/mocked Git bytes.
CHILD=r"""
import atexit,collections,faulthandler,json,os,subprocess,sys,time,unittest
case=sys.argv[1]
summary_file=sys.argv[2]
real_run=subprocess.run
calls=collections.Counter()
spent=collections.defaultdict(float)
longest=collections.defaultdict(float)
failure=collections.Counter()
global_count=0
def emit(stage):
    data={"stage":stage,"total_real_git_commands":global_count,
          "by_git_verb":{x:{"calls":calls[x],"duration_seconds":round(spent[x],4),
                        "max_single_seconds":round(longest[x],4),
                        "caught_python_exception_count":failure[x]}
                         for x in sorted(calls)}}
    with open(summary_file,"a",encoding="utf8") as fp:
        fp.write(json.dumps(data,sort_keys=True)+"\n")
        fp.flush()
def observe(*a,**kwargs):
    global global_count
    cmd=a[0] if a else kwargs.get("args")
    cmd=cmd if isinstance(cmd,(list,tuple)) else []
    if not cmd or os.path.basename(str(cmd[0])).lower() not in ("git","git.exe"):
        return real_run(*a,**kwargs)
    i=1
    if len(cmd)>3 and cmd[1]=="-C": i=3
    verb=str(cmd[i]) if i<len(cmd) else "unknown"
    start=time.monotonic()
    try:
        return real_run(*a,**kwargs)
    except BaseException:
        failure[verb]+=1
        raise
    finally:
        elapsed=time.monotonic()-start
        calls[verb]+=1
        spent[verb]+=elapsed
        longest[verb]=max(longest[verb],elapsed)
        global_count+=1
        if global_count%12==0: emit("progress")
subprocess.run=observe
atexit.register(emit,"normal_exit")
faulthandler.enable()
faulthandler.dump_traceback_later(25,repeat=True,file=sys.stderr)
unittest.main(module=None,argv=["unittest","-v",case],exit=True)
"""

def run_native(label:str,case:str,deadline:int,profile:bool,fixture:Path,out:Path)->dict:
    env=os.environ.copy()
    for k in list(env):
        if k in SENSITIVE or k.endswith("_API_KEY") or k.endswith("_SECRET"):
            env.pop(k,None)
    env.update({"TEMP":str(fixture),"TMP":str(fixture),"TMPDIR":str(fixture),
                "PYTHONDONTWRITEBYTECODE":"1"})
    log=out/("p179_authentic_Windows_"+label+".log")
    trace=out/("p179_original_Git_invocation_profile_"+label+".jsonl")
    code=CHILD if profile else (
        "import faulthandler,sys,unittest;"
        "faulthandler.dump_traceback_later(25,repeat=True,file=sys.stderr);"
        "unittest.main(module=None,argv=['unittest','-v',sys.argv[1]],exit=True)"
    )
    args=[sys.executable,"-B","-u","-X","faulthandler","-c",code,case]
    if profile:args.append(str(trace))
    start=time.monotonic()
    timeout=False
    with log.open("wb") as f:
        p=subprocess.Popen(args,cwd=ROOT,env=env,
                           stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
                           creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try:exit_code=p.wait(timeout=deadline)
        except subprocess.TimeoutExpired:
            exit_code=124
            timeout=True
            subprocess.run(["taskkill","/PID",str(p.pid),"/T","/F"],
                           stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,timeout=20,check=False)
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=10)
    raw=log.read_bytes()
    t=raw.decode("utf8","replace").replace("\r\n","\n")
    footer=FOOTER.findall(t)
    count=int(footer[-1]) if footer else None
    issues=ISSUES.findall(t)
    status=("TIMEOUT" if timeout else
            "PASS" if exit_code==0 and count==1 and
            re.search(r"^OK\s*$",t,re.M) and not issues else
            "HOLD" if exit_code==1 and count==1 and
            re.search(r"^FAILED \(",t,re.M) else "INCOMPLETE")
    snapshots=[]
    if profile and trace.exists():
        for line in trace.read_text(encoding="utf8").splitlines():
            snapshots.append(json.loads(line))
    observations=snapshots[-1] if snapshots else None
    result={"original_test_case":case,"performance_only_instrumented":profile,
            "real_native_exit":exit_code,"unittest_count":count,
            "disposition":status,"native_elapsed_seconds":round(time.monotonic()-start,3),
            "complete_original_log_sha256":sha(raw),"log_filename":log.name,
            "python_stack_dumps":t.count("Timeout (0:00:25)!"),
            "named_FAIL_ERROR":[{"type":a,"name":b} for a,b in issues],
            "git_profile_progress_snapshot":observations,
            "profile_log_sha256":sha(trace.read_bytes()) if trace.exists() else None,
            "profile_log_filename":trace.name if trace.exists() else None,
            "not_a_full_product_native_regression":True}
    print("P179_NATIVE_WINDOWS="+label+"|STATUS="+status+"|EXIT="+str(exit_code)+
          "|CASE_COUNT="+str(count)+"|SECONDS="+str(result["native_elapsed_seconds"]),flush=True)
    if observations:
        top=sorted(observations["by_git_verb"].items(),
                   key=lambda x:x[1]["duration_seconds"],reverse=True)[:6]
        print("P179_OBSERVED_UNMODIFIED_GIT_SUBPROCESS_CALLS="+
              str(observations["total_real_git_commands"])+
              "|TOP_VERBS="+json.dumps(top,separators=(",",":")),flush=True)
    print("P179_RAW_SHA256="+label+"|"+sha(raw),flush=True)
    return result

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p179-historical-git-seal-profile"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P179","historical_H":"HOLD",
            "current_C":"SOURCE_PRESERVING_PROFILE_DIAGNOSTIC_ONLY",
            "production_R":"HOLD","full_product_Windows_accepted":"0/3",
            "original_P135_3x600s_timeouts":"UNWAIVED",
            "GOV_SEC_REL_qualified_independent_decisions":REVIEWS,
            "privileged_C1_G0_to_G6":"OPEN",
            "real_API_keys_WinCred_provider_or_signed_launch":"NEVER_ATTEMPTED",
            "profiling_changes_timing_not_a_release_acceptance":True}
    ok=False
    try:
        before=custody()
        ledger["exact_source_before"]=before
        ledger["authentic_prior_P178_original_native_Windows_logs"]=authenticate_p178(
            os.environ.get("P179_ARCHIVE_TOKEN",""))
        fixture=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("P179 unique fixed local owned fixture collision")
        os.mkdir(fixture)
        try:
            _verify_original_handle_policy(str(fixture))
            control=run_native("original_uninstrumented_control",CONTROL,30,False,fixture,out)
            # Instrument only a fresh child; no original test/guard source patched.
            hotspot=run_native("historical_seal_pin_witness",HOTSPOT,130,True,fixture,out)
        finally:
            if fixture.exists():
                stat=fixture.lstat()
                if fixture.is_symlink() or getattr(stat,"st_file_attributes",0)&0x400:
                    raise RuntimeError("P179 unsafe reparse temp cleanup refused")
                shutil.rmtree(fixture)
        ledger["actual_bounded_native_Windows_control"]=control
        ledger["actual_instrumented_native_Windows_historical_hotspot"]=hotspot
        ledger["exact_source_after"]=custody()
        ok=(before==ledger["exact_source_after"]
            and control["disposition"]=="PASS" and control["unittest_count"]==1
            and hotspot["disposition"] in ("PASS","HOLD","TIMEOUT")
            and hotspot["git_profile_progress_snapshot"] is not None
            and hotspot["git_profile_progress_snapshot"]["total_real_git_commands"]>0)
        ledger["authentic_profile_evidence_captured_not_performance_fix"]=ok
        print("P179_P178_AUTHENTIC_ORIGINAL_ARCHIVE=YES",flush=True)
        print("P179_PROFILE_DIAGNOSTIC="+("COMPLETE" if ok else "INCOMPLETE"),flush=True)
        print("P179_7_QUALIFIED_DECISIONS=OPEN",flush=True)
        print("P179_FULL_PRODUCT_WINDOWS_3_REGRESSIONS=0/3|PRODUCTION_R=HOLD",flush=True)
    except Exception as exc:
        ledger["collector_failure"]=repr(exc)
        print("P179_AUTHENTIC_GIT_PERFORMANCE_DIAGNOSTIC=HOLD|"+repr(exc),flush=True)
    finally:
        (out/"p179_native_Windows_historical_Git_seal_profile_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
