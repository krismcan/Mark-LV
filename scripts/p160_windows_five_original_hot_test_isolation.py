"""P160 source-preserving native Windows diagnosis of five P159 long-running test IDs.

The ORIGINAL test methods run unchanged and are not modified, skipped or waived.
The only instrumentation is faulthandler periodic Python stack snapshots,
in a disposable Windows CI child process, to discriminate Git-history cost,
source-integrity negative refusal, and genuine deadlock. Not a suite PASS.
"""
from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
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

BASE = "a8b317e6ab6cf2ad20514c60bbfaa0babbd5a492"
BRANCH = "byok-c1-p160-windows-five-hot-test-causal-isolation-20261111"
ROOT = Path(__file__).resolve().parents[1]
CURRENT_TEST_MODULES = 170
CAP_SECONDS = 80
WORKERS = 2

# Five exact original last-running case identities established by authentic
# P159 run 43071451824 and individual module raw Windows log output.
HOT = (
    (
        "tests.test_phase_831_scope_integrity.Phase831ScopeTests."
        "test_staged_application_canary_across_exact_832_topologies",
        "tests/test_phase_831_scope_integrity.py",
        "41E23E31D06F699129BD274A29DE103A1917C7E1754B3B0EDDA9658BE15AD20C",
    ),
    (
        "tests.test_phase_832_scope_integrity.Phase832ScopeIntegrityTests."
        "test_historical_second_tree_injection_reached_with_clean_positive_control",
        "tests/test_phase_832_scope_integrity.py",
        "0A25F898CCB374B63B6CD68B0A3488C6F0D8656EC6EA6BAE1FD225CABCF9A689",
    ),
    (
        "tests.test_phase_833_scope_integrity.Phase833CandidateTests."
        "test_clean_legacy_h_preserves_guard_but_cannot_project_new_source",
        "tests/test_phase_833_scope_integrity.py",
        "8BDEECC1D14FFDCFFA2B05B7E3E7409B00E0F211DB5810FEFB9EC96865A7531D",
    ),
    (
        "tests.test_phase_834_scope_integrity.Phase834CandidateTests."
        "test_all_three_complete_controls_reach_current_pin_reads",
        "tests/test_phase_834_scope_integrity.py",
        "8DC69EC770EA008DFF9CD13E15299A73E38044F1671FD4FE78FBE2A431CCF57A",
    ),
    (
        "tests.test_phase_837_scope_integrity.Phase837IntegrityTests."
        "test_every_original_836_pin_is_rechecked_including_normalized_self",
        "tests/test_phase_837_scope_integrity.py",
        "A95A967BA892FECADF0811B38C51AE61CD268159766A91B1DC448CF4B1B5C426",
    ),
)
ENV_DENY = (
    "OPENAI_API_KEY","AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY","GITHUB_TOKEN","GH_TOKEN",
    "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "NAYEON_INTERNAL_SECRET","P160_TOKEN",
)
COUNT = re.compile(r"^Ran (\d+) tests? in [0-9.]+s$",re.M)
OK = re.compile(r"^OK\s*$",re.M)
FAILED = re.compile(r"^FAILED \(([^)]+)\)\s*$",re.M)
HEAD = re.compile(r"^(FAIL|ERROR): ([^\r\n]+)",re.M)
STACK = re.compile(r"^Timeout \(\d+:\d+:\d+\)!$",re.M)
PROBE = r"""
import faulthandler
import runpy
import sys
faulthandler.enable(all_threads=True)
faulthandler.dump_traceback_later(20, repeat=True, file=sys.stderr, exit=False)
case = sys.argv[1]
sys.argv = ["python -m unittest", "-v", case]
runpy.run_module("unittest", run_name="__main__")
"""


def _git(*args):
    child=subprocess.run(
        ["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
        capture_output=True,timeout=25,check=True,
    )
    return child.stdout.decode("utf8","replace").strip()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def _verify_originals():
    _guard_runner()
    if os.environ.get("RUNNER_OS")!="Windows" or os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("P160 requires actual hosted Windows")
    if os.environ.get("GITHUB_REF_NAME")!=BRANCH:
        raise RuntimeError("P160 exact branch required")
    head=_git("rev-parse","HEAD")
    if head!=os.environ.get("GITHUB_SHA") or _git("merge-base",BASE,"HEAD")!=BASE:
        raise RuntimeError("P160 source SHA or P159 ancestry mismatch")
    existing=[
        name for name in _git("ls-files","tests/test_*.py").splitlines()
        if name.startswith("tests/test_") and name.endswith(".py")
    ]
    if len(existing)!=CURRENT_TEST_MODULES:
        raise RuntimeError("P160 source original/current test module inventory drift")
    for qualified,path,hash_value in HOT:
        raw=(ROOT/path).read_bytes()
        if _sha(raw)!=hash_value:
            raise RuntimeError("P160 SHA of original hot-test file changed: "+path)
        if _git("rev-parse","HEAD:"+path)!=_git("rev-parse",BASE+":"+path):
            raise RuntimeError("P160 original historical test blob changed: "+path)
        parts=qualified.split(".")
        if len(parts)!=4 or parts[:1]!=["tests"]:
            raise RuntimeError("P160 malformed fully qualified test")
        _,mod,klass,method=parts
        tree=ast.parse(raw,filename=path)
        cls=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==klass]
        if len(cls)!=1 or len([n for n in cls[0].body
                              if isinstance(n,ast.FunctionDef) and n.name==method])!=1:
            raise RuntimeError("P160 original test AST signature drift: "+qualified)
    if _git("status","--porcelain=v1"):
        raise RuntimeError("P160 original product checkout not clean")
    print("P160_FIVE_EXACT_HISTORICAL_TEST_FILES_SOURCE_SHA256=PASS",flush=True)
    print("P160_170_TRACKED_TEST_MODULE_INVENTORY=PASS",flush=True)
    return head


def _run(row, base_temp: Path, out: Path):
    test_id,path,pinned_sha=row
    stem=Path(path).stem
    own=base_temp/stem
    own.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    for k in ENV_DENY:
        env.pop(k,None)
    env.update({
        "TEMP":str(own),"TMP":str(own),"TMPDIR":str(own),
        "PYTHONDONTWRITEBYTECODE":"1",
    })
    filename=out/(stem+".log")
    started=time.monotonic()
    code=None
    killed=False
    with filename.open("wb") as stream:
        child=subprocess.Popen(
            [sys.executable,"-B","-c",PROBE,test_id],cwd=ROOT,env=env,
            stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0),
        )
        try:
            code=child.wait(timeout=CAP_SECONDS)
        except subprocess.TimeoutExpired:
            code=124
            killed=True
            subprocess.run(
                ["taskkill","/PID",str(child.pid),"/T","/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                timeout=15,check=False,
            )
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
    raw=filename.read_bytes()
    text=raw.decode("utf8","replace").replace("\r\n","\n")
    found=COUNT.findall(text)
    count=int(found[-1]) if found else None
    original_failures=[
        {"kind":k,"original_test":t} for k,t in HEAD.findall(text)
    ]
    complete=count==1 and (bool(OK.search(text)) or bool(FAILED.search(text)))
    if code==0 and complete and bool(OK.search(text)) and not original_failures:
        verdict="PASS"
    elif code==124 and killed:
        verdict="TIMEOUT"
    else:
        verdict="HOLD"
    result={
        "original_test_id":test_id,
        "original_source_file":path,
        "original_source_sha256":pinned_sha,
        "source_unchanged":True,
        "instrumentation":"periodic faulthandler Python stack only; unmodified original unittest",
        "native_windows_child_exit":code,
        "elapsed_seconds":round(time.monotonic()-started,3),
        "hard_cap_seconds":CAP_SECONDS,
        "full_unittest_footer":bool(complete),
        "actual_original_test_count":count,
        "original_failures_and_errors":original_failures,
        "stack_dump_header_count":len(STACK.findall(text)),
        "original_last_test_line":next(
            (x for x in reversed(text.splitlines())
             if x.startswith("test_") and " ... " in x),None
        ),
        "raw_stdout_stderr_sha256":_sha(raw),
        "log_bytes":len(raw),"log_name":filename.name,
        "disposition":verdict,
    }
    print(
        "P160_CASE="+stem+"|EXIT="+str(code)+"|COUNT="+str(count)+
        "|STATE="+verdict+"|SECONDS="+str(result["elapsed_seconds"])+
        "|STACKS="+str(result["stack_dump_header_count"])+
        "|SHA256="+result["raw_stdout_stderr_sha256"],flush=True
    )
    return result


def main():
    head=_verify_originals()
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p160-isolated-five-hot-tests"
    out.mkdir(parents=True,exist_ok=True)
    temp=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made=False
    rows=[]
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P160 owned test temp already present")
        os.mkdir(temp)
        made=True
        _verify_original_handle_policy(str(temp))
        print("P160_P139_UNCHANGED_NATIVE_WIN32_FILE_HANDLE_POLICY=PASS",flush=True)
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures={pool.submit(_run,x,temp,out):x[0] for x in HOT}
            for done in as_completed(futures):
                rows.append(done.result())
    finally:
        if made:
            st=temp.lstat()
            if temp.is_symlink() or getattr(st,"st_file_attributes",0)&0x400:
                raise RuntimeError("P160 refuse unsafe reparse root removal")
            shutil.rmtree(temp)
    if len(rows)!=len(HOT) or {x["original_test_id"] for x in rows}!={x[0] for x in HOT}:
        raise RuntimeError("P160 missing or duplicate test observations")
    if _git("status","--porcelain=v1"):
        raise RuntimeError("P160 original source mutated during test")
    totals={state:sum(r["disposition"]==state for r in rows) for state in ("PASS","HOLD","TIMEOUT")}
    ledger={
        "checkpoint":"P160","tested_exact_source_head":head,
        "verified_immediate_historical_parent":BASE,
        "prior_P159_windows_source_run":43071451824,
        "historical_original_tests_modified":False,
        "source_pins_unchanged":True,
        "current_test_module_inventory":CURRENT_TEST_MODULES,
        "native_windows_probe_count":len(HOT),
        "results":sorted(rows,key=lambda r:r["original_test_id"]),
        "summary":totals,
        "historical_P76_P85_branch_refusals":"IMMUTABLE",
        "historical_P159_original_module_statuses":"1 HOLD / 5 TIMEOUT",
        "accepted_full_product_windows_regression_triads":"0/3",
        "independent_qualified_security_and_regression_governance":"NOT_OBTAINED",
        "original_privileged_C1_G0_to_G6":"OPEN",
        "production_release":"HOLD",
        "collector_green_does_not_mean_original_green":True,
    }
    (out/"p160_actual_windows_five_hot_test_ledger.json").write_text(
        json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8"
    )
    print("P160_GENUINE_WINDOWS_ORIGINAL_FOCUSED_COUNTS="+json.dumps(totals,sort_keys=True),flush=True)
    print("P160_ORIGINAL_SECURITY_NEGATIVES=UNCHANGED",flush=True)
    print("P160_FULL_PRODUCT_WINDOWS_REGRESSION=0/3",flush=True)
    print("P160_PRODUCTION_RELEASE=HOLD",flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
