"""P231: genuine Windows partitioned *unchanged* entire original discovery.

Diagnostics only; *not* one full unfiltered original-process regression, not
one of the three mandatory green full product suites. Every discovery ID goes
to exactly one of six fixed module-affine shards, with deterministic SHA256
assignment and independent full-suite inventory hash. Original FAIL/ERROR
are never hidden, modified, mocked, marked OK or waived. Only ephemeral
approved P134 synthetic namespace may receive native test credential effects.
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
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE="ba6837852a1a42f9170f123264181e6b241e24f5"
BRANCH="byok-c1-p231-original-windows-regression-full-inventory-20261115"
DELTA={
 "scripts/p231_windows_original_full_test_inventory.py",
 ".github/workflows/p231-windows-original-regression-partitions.yml",
}
SHARDS=6
P96="tests/p96_native_transaction_negative/PendingCustodyTransaction.cs"
P95="tests/p95_native_custody_preflight/CustodyLedger.cs"
PINS={
 P96:"D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
 P95:"93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B",
}
WATCH=(
 "tests/test_p86_live_pending_status_integration.py",
 "tests/test_p87_readonly_custody_observation.py",
 "tests/test_p132_user_scope_migration.py",
 "tests/test_phase10_2_privacy_scope_integrity.py",
 "tests/test_phase10_3_scope_integrity.py",
 "tests/test_phase8_byok_b_scope_integrity.py",
 "nayeon/desktop_alpha/workspace_window.py",
 "nayeon/desktop_alpha/application.py",
 "nayeon/desktop_alpha/local_byok_launch_bridge.py",
 "native_c1_candidate/CustodyService.cs",
 "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs",
 P95,P96,
)
FORBIDDEN=(
 "OPENAI_API_KEY","AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY",
 "GOOGLE_API_KEY","GITHUB_TOKEN","GH_TOKEN",
 "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)
MAX_SECONDS=720


def sha(b):return hashlib.sha256(b).hexdigest().upper()


def git(*args):
    return subprocess.run(["git","-C",str(ROOT),*args],
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,timeout=45).stdout


def verify(shard):
    expected={
      "GITHUB_ACTIONS":"true","RUNNER_OS":"Windows",
      "GITHUB_EVENT_NAME":"push","GITHUB_REPOSITORY":"krismcan/Mark-LV",
      "GITHUB_REF_NAME":BRANCH,
      "P134_NATIVE_WINCRED_EPHEMERAL_AUTH":"EPHEMERAL_GITHUB_WINDOWS_ONLY",
    }
    if sys.platform!="win32" or any(os.getenv(k)!=v for k,v in expected.items()):
        raise RuntimeError("P231 real Windows source or ephemeral WinCred guard missing")
    if shard not in range(SHARDS):
        raise RuntimeError("P231 invalid original test shard")
    head=git("rev-parse","HEAD").decode().strip()
    if head!=os.getenv("GITHUB_SHA") or git(
        "merge-base",BASE,head).decode().strip()!=BASE:
        raise RuntimeError("P231 real source HEAD ancestor not authentic")
    changed=set(git("diff","--name-only",BASE,head).decode().splitlines())
    if changed!=DELTA or git("status","--porcelain=v1","-uall").strip():
        raise RuntimeError("P231 changed original code, source or pristine checkout")
    watches={}
    for rel in WATCH:
        disk=(ROOT/rel).read_bytes()
        raw=git("show","HEAD:"+rel)
        if raw!=disk or git(
          "rev-parse","HEAD:"+rel)!=git("rev-parse",BASE+":"+rel):
            raise RuntimeError("P231 original frozen source bytes altered: "+rel)
        digest=sha(raw)
        if rel in PINS and PINS[rel]!=digest:
            raise RuntimeError("P231 original ledger or P96 source pin altered")
        watches[rel]=digest
    return {"actual_head":head,"parent":BASE,"frozen_source_sha256":watches,
            "two_additive_files_only":sorted(DELTA)}


def flattened(test):
    if isinstance(test,unittest.TestSuite):
        for item in test:
            yield from flattened(item)
    else:
        yield test


def discover():
    loader=unittest.TestLoader()
    suite=loader.discover(start_dir=str(ROOT/"tests"),
                          top_level_dir=str(ROOT),pattern="test_*.py")
    original=list(flattened(suite))
    if len(original)<1000:
        raise RuntimeError("P231 original unittest discovery unexpectedly partial")
    records=[]
    for test in original:
        tid=test.id()
        module=test.__class__.__module__
        if not module.startswith("tests."):module=tid
        slot=int.from_bytes(hashlib.sha256(module.encode("utf8")).digest()[:4],"big")%SHARDS
        records.append((tid,module,slot,test))
    ids=[tid for tid,_,_,_ in records]
    if len(ids)!=len(set(ids)):
        raise RuntimeError("P231 original discovery contains duplicate test ids")
    digest=sha(("\n".join(ids)+"\n").encode("utf8"))
    return records,digest


def scoped_env():
    env=os.environ.copy()
    for key in FORBIDDEN: env.pop(key,None)
    env["PYTHONDONTWRITEBYTECODE"]="1"
    return env


def worker(shard:int,dir:Path):
    items,inventory=discover()
    selected=[t for tid,mod,k,t in items if k==shard]
    if not selected:
        raise RuntimeError("P231 empty module-affine original discovery shard")
    # Single unchanged unittest TextTestRunner for this module-affine subset:
    # original tests use real methods, setUpClass and module setup unmodified.
    import time
    began=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected))
    status={
      "shard":shard,"shards":SHARDS,"original_discovery_count":len(items),
      "unmodified_discovery_order_sha256":inventory,
      "selected_unmodified_test_ids":[t.id() for t in selected],
      "actual_tests_run":result.testsRun,
      "original_failures":[x.id() for x,_ in result.failures],
      "original_errors":[x.id() for x,_ in result.errors],
      "original_skips":[x.id() for x,_ in result.skipped],
      "original_unexpected_successes":[x.id() for x in result.unexpectedSuccesses],
      "native_original_runner_exit_if_zero":result.wasSuccessful(),
      "elapsed_seconds":round(time.monotonic()-began,3),
      "original_untouched_methods_only":True,
      "real_key_effects":"NOT_AUTHORIZED",
    }
    (dir/"P231-worker-result.json").write_text(
        json.dumps(status,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("P231_ORIGINAL_MODULE_AFFINE_SHARD="+str(shard),flush=True)
    print("P231_ORIGINAL_TESTS_RUN="+str(result.testsRun),flush=True)
    print("P231_ORIGINAL_ERRORS="+str(len(result.errors)),flush=True)
    print("P231_ORIGINAL_FAILURES="+str(len(result.failures)),flush=True)
    print("P231_ORIGINAL_SKIPS="+str(len(result.skipped)),flush=True)
    print("P231_ORIGINAL_EXECUTION_SUCCEEDED="+str(result.wasSuccessful()).upper(),flush=True)
    print("P231_SHARD_NOT_FULL_RELEASE_REGRESSION=TRUE",flush=True)
    return 0 if result.wasSuccessful() else 1


def parent(shard:int):
    folder=Path(os.environ["RUNNER_TEMP"])/("p231-original-Windows-shard-"+str(shard))
    folder.mkdir(parents=True,exist_ok=True)
    payload={
      "checkpoint":"P231","shard":shard,"shards":SHARDS,
      "unfiltered_original_current_suite_release_passes":"0/3",
      "independent_GOV_SEC_REL_signoffs":"0/7",
      "current_original_historical_failures":"REAL_UNWAIVED",
      "original_P96_effect_race":"OPEN","real_keys":"NO_GO",
      "production":"HOLD","master_workbook_dashboard":"NOT_TOUCHED",
      "native_effect_limit":"EPHEMERAL_P134_SYNTHETIC_TEST_NAMESPACE_ONLY",
    }
    complete=False
    try:
        payload["source_before"]=verify(shard)
        alltests,inventory=discover()
        selected=[tid for tid,mod,k,t in alltests if k==shard]
        payload["original_unfiltered_discovery_count"]=len(alltests)
        payload["original_unfiltered_discovery_order_sha256"]=inventory
        payload["selected_unmodified_test_ids"]=selected
        cmd=[sys.executable,"-B","-m",
             "scripts.p231_windows_original_full_test_inventory",
             "--worker",str(shard)]
        log=folder/"P231-raw-original-unittest-output.log"
        code=125
        with log.open("wb") as sink:
            try:
                proc=subprocess.run(cmd,cwd=ROOT,env=scoped_env(),
                     stdin=subprocess.DEVNULL,stdout=sink,
                     stderr=subprocess.STDOUT,timeout=MAX_SECONDS,check=False)
                code=proc.returncode
            except subprocess.TimeoutExpired:
                code=124
        payload["actual_shard_native_exit"]=code
        payload["timed_out"]=code==124
        payload["raw_original_log_sha256"]=sha(log.read_bytes())
        payload["raw_original_log_bytes"]=log.stat().st_size
        response=folder/"P231-worker-result.json"
        if response.exists():
            observed=json.loads(response.read_text("utf8"))
            payload["actual_original_test_result"]=observed
            if (observed["original_discovery_count"]!=len(alltests)
               or observed["unmodified_discovery_order_sha256"]!=inventory
               or observed["selected_unmodified_test_ids"]!=selected):
                raise RuntimeError("P231 independent original test inventory diverged")
            complete=(observed["actual_tests_run"]==len(selected)
                      and code==(0 if observed["native_original_runner_exit_if_zero"] else 1)
                      and not observed["original_unexpected_successes"])
        payload["source_after"]=verify(shard)
        complete=complete and payload["source_before"]==payload["source_after"]
        print("P231_ORIGINAL_WINDOWS_SHARD="+str(shard)
              +"|NATIVE_EXIT="+str(code)
              +"|TESTS_DISCOVERED="+str(len(alltests))
              +"|SELECTED="+str(len(selected))
              +"|COMPLETE="+str(complete).upper(),flush=True)
        print("P231_UNMODIFIED_ORIGINAL_FAILS_NOT_WAIVED=TRUE",flush=True)
    except Exception as e:
        payload["error"]=type(e).__name__+": "+str(e)
        payload["traceback"]=traceback.format_exc()[-2200:]
        print("P231_ORIGINAL_SHARD_DIAGNOSTIC_ERROR="+type(e).__name__,flush=True)
    finally:
        payload["complete_unchanged_original_shard_NOT_a_full_release_suite"]=complete
        (folder/"P231-shard-evidence.json").write_text(
            json.dumps(payload,sort_keys=True,indent=2)+"\n","utf8")
        with (folder/"P231-sha256-receipts.txt").open("w",encoding="ascii") as f:
            for p in sorted(folder.iterdir()):
                if p.is_file() and p.name!="P231-sha256-receipts.txt":
                    f.write(sha(p.read_bytes())+"  "+p.name+"\n")
        print("P231_FULL_RELEASE=HOLD|R0_R4=NO_GO|ORIGINAL_SUITE=0/3",flush=True)
    # Successful diagnostic completion DOES NOT mean the original tests pass.
    return 0 if complete else 1


if __name__=="__main__":
    if len(sys.argv)!=3 or sys.argv[1] not in ("--worker","--parent"):
        raise SystemExit("P231 shard argument required")
    try:
        n=int(sys.argv[2])
    except ValueError:
        raise SystemExit("P231 invalid shard number")
    if not 0<=n<SHARDS:
        raise SystemExit("P231 shard out of bound")
    if sys.argv[1]=="--worker":
        folder=Path(os.environ["RUNNER_TEMP"])/("p231-original-Windows-shard-"+str(n))
        raise SystemExit(worker(n,folder))
    raise SystemExit(parent(n))
