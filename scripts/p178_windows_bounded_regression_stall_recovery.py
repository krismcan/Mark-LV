"""P178 — source-bound native Windows P135 regression-stall reproduction.

A focused REAL Windows original-test reproduction, NEVER a full product pass.
Authenticated P135 3x600s raw logs, P154 169-module reconciliation and P177
review packet, exact untouched Git source/tree, a bounded single-case test
with faulthandler trace and an optional complete original module only if
the isolated formerly stalled case completes. No original test rewrites.
"""
from __future__ import annotations

from collections import Counter
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
BRANCH="byok-c1-p178-bounded-full-regression-stall-recovery-20261112"
BASE="96e5136a0f78fccde13971350a4afc1b0a26d481"
P135_ID=13721186316
P135_ZIP="AA179E18E3AA39FC3254A6C44D8654FFE93685DD792D84BA1E79049A96F86856"
P135_RAW="31F844EE8C29B9886885303DF983FFA7C0452C2A671866400A9768535C6DD113"
P154_ID=13860513004
P154_ZIP="30C9B618BC1DBCDC09D13181C8DBD0724216373E0CFE35616A82ACE4EFCFF9E7"
P177_ID=13960468475
P177_ZIP="2806AD093645BED6120F54DE7D702A11E4D00D54C6EE32B73CD15432BC4C138B"
NEW={
    "scripts/p178_windows_bounded_regression_stall_recovery.py",
    "docs/byok-c1-p178-authentic-full-regression-stall-recovery.md",
    ".github/workflows/p178-windows-bounded-regression-recovery.yml",
}
ORIGINAL_TEST_MODULE="tests.test_phase8_byok_b_scope_integrity"
SINGLE_STALLED=(ORIGINAL_TEST_MODULE+
    ".ExactBYOKBTests.test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused")
ADJACENT=(ORIGINAL_TEST_MODULE+
    ".ExactBYOKBTests.test_self_canonicalization_only_zeros_own_single_literal")
FOOTER=re.compile(r"^Ran (\d+) tests? in [0-9.]+s$",re.M)
PROBLEM=re.compile(r"^(FAIL|ERROR): (.+)$",re.M)
P135_NATIVE_LINE=re.compile(r"^test_[^\r\n]+ \.\.\. (ok|FAIL|ERROR)$")
SENSITIVE={"GITHUB_TOKEN","GH_TOKEN","P178_EVIDENCE_TOKEN","OPENAI_API_KEY",
           "AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY","ACTIONS_RUNTIME_TOKEN",
           "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}
P135_COMPLETED={"ok":1637,"FAIL":37,"ERROR":7}
REVIEWS={n:"OPEN" for n in ("GOV-01","GOV-02","SEC-03","SEC-04",
                           "REL-05","REL-06","REL-07")}

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        timeout=40,check=True).stdout

def custody()->dict:
    _guard_runner()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("status","--porcelain=v1").strip()
        or git("merge-base",BASE,"HEAD").decode().strip()!=BASE):
        raise RuntimeError("P178 must run on genuine clean GitHub-hosted Windows exact branch")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in NEW):
        raise RuntimeError("P178 exactly three newly added diagnostic paths required")
    if (git("rev-parse",BASE+":nayeon")!=git("rev-parse","HEAD:nayeon")
        or git("rev-parse",BASE+":tests")!=git("rev-parse","HEAD:tests")):
        raise RuntimeError("P178 entire original product or test subtree changed")
    original=(ROOT/"tests/test_phase8_byok_b_scope_integrity.py").read_bytes()
    if (original!=git("show",BASE+":tests/test_phase8_byok_b_scope_integrity.py")
        or original!=git("show","HEAD:tests/test_phase8_byok_b_scope_integrity.py")):
        raise RuntimeError("P178 historical original stalled BYOK B test changed")
    files=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
           if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(files)!=171 or files!=sorted(files):
        raise RuntimeError("P178 original untouched 171 tracked test module custody failed")
    return {"authentic_P178_head":git("rev-parse","HEAD").decode().strip(),
            "P177_source_parent":BASE,"exact_three_additive_audit_paths":sorted(NEW),
            "full_product_and_original_test_trees_unchanged":True,
            "original_stalled_BYOK_B_test_blob_SHA256":sha(original),
            "original_tracked_test_module_count":len(files)}

def verified_zip(id:int,pin:str,token:str)->zipfile.ZipFile:
    if len(token)<8:raise RuntimeError("P178 ephemeral read-only Actions token unavailable")
    data=_download_artifact(id,pin,token)
    if sha(data)!=pin:
        raise RuntimeError("P178 original Windows evidence ZIP SHA drift: "+str(id))
    z=zipfile.ZipFile(io.BytesIO(data))
    if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())):
        raise RuntimeError("P178 archived original Windows ZIP CRC/name drift")
    if any(n.startswith("/") or ".." in Path(n).parts for n in z.namelist()):
        raise RuntimeError("P178 ambiguous archived ZIP member")
    return z

def authenticate_p135(token:str)->dict:
    z=verified_zip(P135_ID,P135_ZIP,token)
    receipts={}
    for i in (1,2,3):
        name=f"p135_full_python_discovery_pass_{i}.log"
        original=z.read(name)
        view=original.decode("utf8","replace").splitlines()
        counts=Counter(m.group(1) for line in view
                       if (m:=P135_NATIVE_LINE.fullmatch(line)))
        if (sha(original)!=P135_RAW or dict(counts)!=P135_COMPLETED
            or any(FOOTER.findall(line) for line in view)
            or not view or "test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused" not in view[-1]):
            raise RuntimeError("P178 genuine P135 incomplete original Windows timeout changed")
        receipts[str(i)]={"original_full_discovery_complete":False,
            "original_native_outcome":"TIMEOUT",
            "old_native_exit":124,
            "old_worker_time_budget_seconds":600,
            "completed_test_line_count":sum(counts.values()),
            "genuine_completed_counts":dict(counts),
            "original_no_footer":True,
            "last_started_uncompleted_case":view[-1],
            "raw_log_sha256":sha(original)}
    return {"run_id":42717686606,"artifact_id":P135_ID,
            "authenticated_original_ZIP_sha256":P135_ZIP,
            "three_immutable_original_600s_timeout_runs":receipts}

def authenticate_p154(token:str)->dict:
    z=verified_zip(P154_ID,P154_ZIP,token)
    ledger=json.loads(z.read("p154_authenticated_original_169_module_regression_ledger.json"))
    if (ledger.get("checkpoint")!="P154"
        or ledger.get("original_169_module_source_inventory_total")!=169
        or ledger.get("p135_original_attempts_with_completed_full_suite")!=0
        or len(ledger.get("p135_original_three_native_full_discovery_attempts",[]))!=3
        or ledger.get("p142_original_83_suffix_counts")!={"PASS":54,"HOLD":20,"TIMEOUT":9}
        or ledger.get("post_recovery_original_83_suffix_counts")!={"PASS":60,"HOLD":16,"TIMEOUT":7}
        or ledger.get("remaining_83_suffix_modules_not_cleared")!=23
        or ledger.get("pre_stall_prefix_modules_not_cleared_by_complete_regression")!=86
        or ledger.get("three_complete_full_product_native_windows_regressions")!=0
        or ledger.get("user_scoped_C1_production_release")!="HOLD"):
        raise RuntimeError("P178 prior P154 source-scoped full product regression receipt drift")
    for row in ledger["p135_original_three_native_full_discovery_attempts"]:
        if (row.get("prior_github_actions_native_exit")!=124
            or row.get("raw_log_sha256")!=P135_RAW
            or row.get("complete_unittest_footer") is not False):
            raise RuntimeError("P178 P154 historical authentic full timeout disposition drift")
    return {"artifact_id":P154_ID,"zip_SHA256":P154_ZIP,
            "original_169_modules":169,"P135_3_times_600sec_full_timeouts":True,
            "P142_83_suffix_after_recovery":{
                "PASS":60,"HOLD":16,"TIMEOUT":7},
            "P154_still_uncleared_original_83_suffix_modules":23,
            "P154_incomplete_full_regression_prefix_modules":86,
            "P154_full_product_complete_regression_triads":0}

def authenticate_p177(token:str)->dict:
    z=verified_zip(P177_ID,P177_ZIP,token)
    l=z.read("p177_real_Windows_nine_case_review_contract.log")
    ledger=json.loads(z.read("p177_source_bound_qualified_independent_review_packet.json"))
    txt=l.decode("utf8","replace").replace("\r\n","\n")
    foot=FOOTER.findall(txt)
    if (ledger.get("checkpoint")!="P177"
        or ledger.get("source_custody_before",{}).get("P177_exact_head")!=BASE
        or ledger.get("source_custody_before")!=ledger.get("source_custody_after")
        or ledger.get("historical_H")!="HOLD"
        or ledger.get("production_R")!="HOLD"
        or ledger.get("accepted_complete_full_product_Windows_regressions")!="0/3"
        or ledger.get("review_submission_packet_prepared_but_not_sent") is not True
        or set(ledger.get("independent_qualified_review_decisions",{}))!=set(REVIEWS)
        or any(row.get("decision")!="OPEN" for row in ledger["independent_qualified_review_decisions"].values())
        or ledger.get("P177_actual_original_Windows_review_contract",{}).get("raw_log_SHA256")!=sha(l)
        or ledger["P177_actual_original_Windows_review_contract"].get("native_exit")!=0
        or ledger["P177_actual_original_Windows_review_contract"].get("original_case_count")!=9
        or len(foot)!=1 or int(foot[0])!=9
        or not re.search(r"^OK\s*$",txt,re.M)):
        raise RuntimeError("P178 P177 genuine complete original packet or external review hold drift")
    return {"artifact_id":P177_ID,"ZIP_SHA256":P177_ZIP,
            "original_review_contract_9_PASS_native_exit_0":True,
            "all_7_independent_authority_decisions":"OPEN"}

def run_original(label:str,selector:str,deadline:int,fixture:Path,out:Path)->dict:
    env=os.environ.copy()
    for k in list(env):
        if k in SENSITIVE or k.endswith("_API_KEY") or k.endswith("_SECRET"):
            env.pop(k,None)
    env.update({"TEMP":str(fixture),"TMP":str(fixture),"TMPDIR":str(fixture),
                "PYTHONDONTWRITEBYTECODE":"1"})
    # In-process faulthandler dumps original Python thread stacks on watchdog.
    # No test code, fixture or security assertion is monkey-patched.
    diagnostic=("import faulthandler,sys,unittest;"
                "faulthandler.dump_traceback_later(20,repeat=True,file=sys.stderr);"
                "unittest.main(module=None,argv=['unittest','-v',sys.argv[1]],exit=True)")
    args=[sys.executable,"-B","-u","-X","faulthandler","-c",diagnostic,selector]
    logfile=out/("p178_original_windows_"+label+".log")
    started=time.monotonic()
    timed_out=False
    with logfile.open("wb") as f:
        p=subprocess.Popen(args,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                           stdout=f,stderr=subprocess.STDOUT,
                           creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try:
            exit_code=p.wait(timeout=deadline)
        except subprocess.TimeoutExpired:
            timed_out=True
            exit_code=124
            subprocess.run(["taskkill","/PID",str(p.pid),"/T","/F"],check=False,
                           stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,timeout=20)
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=10)
    raw=logfile.read_bytes()
    t=raw.decode("utf8","replace").replace("\r\n","\n")
    foot=FOOTER.findall(t)
    count=int(foot[-1]) if foot else None
    issues=[{"kind":kind,"original_id":test} for kind,test in PROBLEM.findall(t)]
    if timed_out:
        disposition="TIMEOUT"
    elif exit_code==0 and count is not None and re.search(r"^OK\s*$",t,re.M):
        disposition="PASS"
    elif exit_code==1 and count is not None and re.search(r"^FAILED \(",t,re.M):
        disposition="HOLD"
    else:
        disposition="INCOMPLETE"
    # If no completed footer, record literal original last test and tracebacks,
    # but do NOT claim it passed or silently exclude it.
    record={"label":label,"selector":selector,
        "source_module_is_original_untouched":True,"real_native_exit":exit_code,
        "original_unittest_count_with_footer":count,
        "complete_footer_present":count is not None,
        "observed_status":disposition,"named_original_failures":issues,
        "watchdog_seconds":deadline,"elapsed_seconds":round(time.monotonic()-started,3),
        "faulthandler_watchdog_stacks_recorded":("Timeout (0:00:20)!" in t),
        "complete_raw_log":logfile.name,"complete_raw_SHA256":sha(raw),
        "log_bytes":len(raw)}
    print("P178_GENUINE_WINDOWS="+label+"|STATUS="+disposition+
          "|EXIT="+str(exit_code)+"|COUNT="+str(count)+
          "|STACKS="+str(record["faulthandler_watchdog_stacks_recorded"]),flush=True)
    print("P178_GENUINE_LOG_SHA256="+label+"|"+sha(raw),flush=True)
    return record

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p178-bounded-regression"
    out.mkdir(parents=True,exist_ok=True)
    report={"checkpoint":"P178","historical_H":"HOLD","current_C":"REGRESSION_RECOVERY_DIAGNOSTIC_ONLY",
            "production_R":"HOLD","full_product_accepted_Windows":"0/3",
            "independent_decisions":REVIEWS,"privileged_BYOK_C1_G0_to_G6":"OPEN",
            "P135_original_3x600s_timeouts":"FROZEN_UNWAIVED",
            "no_real_credentials_WinCred_effects_provider_or_signed_launch":True}
    ok=False
    try:
        before=custody()
        report["source_custody_before"]=before
        token=os.environ.get("P178_EVIDENCE_TOKEN","")
        report["authenticated_historical_P135"]=authenticate_p135(token)
        report["authenticated_169_module_P154_inventory"]=authenticate_p154(token)
        report["authenticated_P177_review_packet"]=authenticate_p177(token)
        fixture=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("P178 local randomized fixture collision")
        os.mkdir(fixture)
        try:
            _verify_original_handle_policy(str(fixture))
            report["original_native_bounded_reproduction"]={}
            control=run_original("adjacent_original_control_1",ADJACENT,40,fixture,out)
            report["original_native_bounded_reproduction"]["adjacent_control"]=control
            stalled=run_original("exact_P135_uncompleted_case_1",SINGLE_STALLED,105,fixture,out)
            report["original_native_bounded_reproduction"]["exact_P135_stalled_case"]=stalled
            # Avoid an uncontrolled expensive full module if the one genuine
            # previously stalled original case cannot complete. Do not miscount.
            if (control["observed_status"] in {"PASS","HOLD"}
                and stalled["observed_status"] in {"PASS","HOLD"}):
                report["original_native_bounded_reproduction"]["entire_BYOK_B_original_module"]=run_original(
                    "entire_original_BYOK_B_module",ORIGINAL_TEST_MODULE,165,fixture,out)
                report["full_original_BYOK_B_module_attempt"]="BOUNDED_ATTEMPTED_NOT_FULL_PRODUCT"
            else:
                report["full_original_BYOK_B_module_attempt"]="SKIPPED_PREVIOUSLY_STALLED_CASE_STILL_UNRESOLVED"
        finally:
            if fixture.exists():
                st=fixture.lstat()
                if fixture.is_symlink() or getattr(st,"st_file_attributes",0)&0x400:
                    raise RuntimeError("P178 unsafe original local fixture reparse cleanup refused")
                shutil.rmtree(fixture)
        report["source_custody_after"]=custody()
        results=report["original_native_bounded_reproduction"]
        authentic=all(row["observed_status"] in {"PASS","HOLD","TIMEOUT"}
                      and row["log_bytes"]>0
                      and row["real_native_exit"] in {0,1,124}
                      for row in results.values())
        ok=(authentic and report["source_custody_before"]==report["source_custody_after"])
        report["evidence_collection_complete_not_a_regression_pass"]=ok
        report["original_full_product_regression_recovered"]=False
        print("P178_AUTHENTIC_P135_3X600S_LOGS=RECONFIRMED",flush=True)
        print("P178_AUTHENTIC_P154_ORIGINAL_169_MODULE_INVENTORY=RECONFIRMED",flush=True)
        print("P178_AUTHENTIC_P177_INDEPENDENT_GOVERNANCE=OPEN",flush=True)
        print("P178_BOUNDED_ORIGINAL_REPRODUCTION="+("COMPLETE" if ok else "INCOMPLETE"),flush=True)
        print("P178_ACCEPTED_COMPLETE_FULL_PRODUCT_WINDOWS=0/3|PRODUCTION_R=HOLD",flush=True)
    except Exception as exc:
        report["collector_failure"]=repr(exc)
        print("P178_AUTHENTIC_NATIVE_RECOVERY_EVIDENCE=HOLD|"+repr(exc),flush=True)
    finally:
        (out/"p178_source_authenticated_windows_full_regression_recovery_ledger.json").write_text(
            json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
