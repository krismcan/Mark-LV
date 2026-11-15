"""P233: genuine Windows partitioned *unchanged* entire original discovery.

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
import shutil
import uuid
from scripts.p139_native_fs_verified_local_temp_root import _verify_original_handle_policy
import subprocess
import sys
import traceback
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE="35402c7fd532d98d53bf2d29c04670648e3af626"
BRANCH="byok-c1-p233-original-windows-unittest-testcase-lifetime-20261115"
DELTA={
 "scripts/p233_windows_unittest_lifetime_recovery.py",
 ".github/workflows/p233-windows-original-tk-teardown-lifetime.yml",
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
        raise RuntimeError("P233 real Windows source or ephemeral WinCred guard missing")
    if shard not in range(SHARDS):
        raise RuntimeError("P233 invalid original test shard")
    head=git("rev-parse","HEAD").decode().strip()
    if head!=os.getenv("GITHUB_SHA") or git(
        "merge-base",BASE,head).decode().strip()!=BASE:
        raise RuntimeError("P233 real source HEAD ancestor not authentic")
    changed=set(git("diff","--name-only",BASE,head).decode().splitlines())
    if changed!=DELTA or git("status","--porcelain=v1","-uall").strip():
        raise RuntimeError("P233 changed original code, source or pristine checkout")
    watches={}
    for rel in WATCH:
        disk=(ROOT/rel).read_bytes()
        raw=git("show","HEAD:"+rel)
        if raw!=disk or git(
          "rev-parse","HEAD:"+rel)!=git("rev-parse",BASE+":"+rel):
            raise RuntimeError("P233 original frozen source bytes altered: "+rel)
        digest=sha(raw)
        if rel in PINS and PINS[rel]!=digest:
            raise RuntimeError("P233 original ledger or P96 source pin altered")
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
        raise RuntimeError("P233 original unittest discovery unexpectedly partial")
    records=[]
    for test in original:
        tid=test.id()
        module=test.__class__.__module__
        if not module.startswith("tests."):module=tid
        slot=int.from_bytes(hashlib.sha256(module.encode("utf8")).digest()[:4],"big")%SHARDS
        records.append((tid,module,slot,test))
    ids=[tid for tid,_,_,_ in records]
    if len(ids)!=len(set(ids)):
        raise RuntimeError("P233 original discovery contains duplicate test ids")
    digest=sha(("\n".join(ids)+"\n").encode("utf8"))
    return records,digest


def create_guard_verified_local_test_root():
    """Only disposable GitHub Windows; apply exact original P139 Win32 handle guard.

    DO NOT change the original filesystem security policy or trust a generic
    CI TEMP path. The new C: root is random and owned by this one shard.
    """
    root=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    if root.exists() or root.is_symlink():
        raise RuntimeError("P233 isolated C drive fixture already exists")
    root.mkdir()
    try:
        _verify_original_handle_policy(str(root))
    except BaseException:
        # Fail closed: no attempt to traverse unknown reparse/alias roots.
        try:
            attrs=root.lstat()
            if (not root.is_symlink()
               and not (getattr(attrs,"st_file_attributes",0)&0x400)
               and str(root).startswith("C:\\NayeonP139_")):
                shutil.rmtree(root)
        except BaseException:pass
        raise
    return root


def compile_original_test_only_windows_fixtures(shard,folder):
    """P226 already proved the SAME unchanged original P210/P213 builds.

    This is a disposable native fixture provision, not an installed service,
    original source edit, signature trust or real-key/WinCred approval.
    """
    native=Path(os.environ["RUNNER_TEMP"])/("p233-native-original-"+str(shard))
    native.mkdir(parents=True,exist_ok=False)
    from scripts.p210_windows_python_native_synthetic_integration import compile_native_bridge
    from scripts.p213_windows_signed_service_observation import compile_native_wintrust_probe
    bridge=compile_native_bridge(native)
    wintrust=compile_native_wintrust_probe(native)
    for filename in ("p210_native_compiler.log",
                     "p213_original_P116_native_wintrust_compiler.log"):
        source=native/filename
        if source.is_file():
            (folder/filename).write_bytes(source.read_bytes())
    return {
      "P210_NATIVE_EXE":bridge["path"],
      "P213_NATIVE_WINTRUST_EXE":wintrust["exe"],
      "P210_unsigned_native_SHA256":bridge["compiled_exe_SHA256"],
      "P213_unsigned_native_SHA256":wintrust["native_exe_SHA256"],
      "source":"unchanged original P210/P213 review-only synthetic fixtures",
      "no_OS_mutation_or_service_install":True,
    }


def scoped_env(guard_root,fixtures):
    env=os.environ.copy()
    for key in FORBIDDEN: env.pop(key,None)
    env["PYTHONDONTWRITEBYTECODE"]="1"
    for key in ("TEMP","TMP","TMPDIR"):
        env[key]=str(guard_root)
    env["P210_NATIVE_EXE"]=fixtures["P210_NATIVE_EXE"]
    env["P213_NATIVE_WINTRUST_EXE"]=fixtures["P213_NATIVE_WINTRUST_EXE"]
    return env


def worker(shard:int,dir:Path):
    items,inventory=discover()
    selected=[t for tid,mod,k,t in items if k==shard]
    if not selected:
        raise RuntimeError("P233 empty module-affine original discovery shard")
    # The original discovery TestSuite releases completed TestCase objects.
    # The P231/P232 diagnostic mistakenly retained references in 'items' and
    # 'selected' throughout execution. Its stale owner references kept Tk
    # roots alive at original tearDownModule, generating an artificial ERROR.
    # Preserve immutable ID strings then RELEASE all extra TestCase owners.
    original_count=len(items)
    assigned_ids=[t.id() for t in selected]
    suite=unittest.TestSuite(selected)
    del selected
    del items
    # Retain only the single stdlib suite. It removes each completed TestCase
    # from its own list, exactly like regular 'unittest discover' semantics.
    import time
    began=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    status={
      "shard":shard,"shards":SHARDS,"original_discovery_count":original_count,
      "unmodified_discovery_order_sha256":inventory,
      "selected_unmodified_test_ids":assigned_ids,
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
    (dir/"P233-worker-result.json").write_text(
        json.dumps(status,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("P233_ORIGINAL_MODULE_AFFINE_SHARD="+str(shard),flush=True)
    print("P233_ORIGINAL_TESTS_RUN="+str(result.testsRun),flush=True)
    print("P233_ORIGINAL_ERRORS="+str(len(result.errors)),flush=True)
    print("P233_ORIGINAL_FAILURES="+str(len(result.failures)),flush=True)
    print("P233_ORIGINAL_SKIPS="+str(len(result.skipped)),flush=True)
    print("P233_ORIGINAL_EXECUTION_SUCCEEDED="+str(result.wasSuccessful()).upper(),flush=True)
    print("P233_SHARD_NOT_FULL_RELEASE_REGRESSION=TRUE",flush=True)
    return 0 if result.wasSuccessful() else 1


def parent(shard:int):
    folder=Path(os.environ["RUNNER_TEMP"])/("p233-original-Windows-shard-"+str(shard))
    folder.mkdir(parents=True,exist_ok=True)
    payload={
      "checkpoint":"P233","shard":shard,"shards":SHARDS,
      "unfiltered_original_current_suite_release_passes":"0/3",
      "independent_GOV_SEC_REL_signoffs":"0/7",
      "current_original_historical_failures":"REAL_UNWAIVED",
      "original_P96_effect_race":"OPEN","real_keys":"NO_GO",
      "production":"HOLD","master_workbook_dashboard":"NOT_TOUCHED",
      "native_effect_limit":"EPHEMERAL_P134_SYNTHETIC_TEST_NAMESPACE_ONLY",
    }
    complete=False
    guard_root=None
    try:
        payload["source_before"]=verify(shard)
        guard_root=create_guard_verified_local_test_root()
        payload["guard_verified_original_P139_local_C_root"]="PASS"
        fixtures=compile_original_test_only_windows_fixtures(shard,folder)
        payload["unsigned_native_fixture_provenance"]={
          k:v for k,v in fixtures.items() if k not in ("P210_NATIVE_EXE","P213_NATIVE_WINTRUST_EXE")
        }
        alltests,inventory=discover()
        selected=[tid for tid,mod,k,t in alltests if k==shard]
        payload["original_unfiltered_discovery_count"]=len(alltests)
        payload["original_unfiltered_discovery_order_sha256"]=inventory
        payload["selected_unmodified_test_ids"]=selected
        cmd=[sys.executable,"-B","-m",
             "scripts.p233_windows_unittest_lifetime_recovery",
             "--worker",str(shard)]
        log=folder/"P233-raw-original-unittest-output.log"
        code=125
        with log.open("wb") as sink:
            try:
                proc=subprocess.run(cmd,cwd=ROOT,env=scoped_env(guard_root,fixtures),
                     stdin=subprocess.DEVNULL,stdout=sink,
                     stderr=subprocess.STDOUT,timeout=MAX_SECONDS,check=False)
                code=proc.returncode
            except subprocess.TimeoutExpired:
                code=124
        payload["actual_shard_native_exit"]=code
        payload["timed_out"]=code==124
        payload["raw_original_log_sha256"]=sha(log.read_bytes())
        payload["raw_original_log_bytes"]=log.stat().st_size
        response=folder/"P233-worker-result.json"
        if response.exists():
            observed=json.loads(response.read_text("utf8"))
            payload["actual_original_test_result"]=observed
            if (observed["original_discovery_count"]!=len(alltests)
               or observed["unmodified_discovery_order_sha256"]!=inventory
               or observed["selected_unmodified_test_ids"]!=selected):
                raise RuntimeError("P233 independent original test inventory diverged")
            # Original setUpClass/setUpModule errors prevent individual methods
            # from reaching setUp/test, but the original suite still reaches
            # its footer. Record those blocked methods, never report PASS.
            payload["unexecuted_due_original_suite_setup_or_module_error_count"]=(
              len(selected)-observed["actual_tests_run"])
            complete=(0<observed["actual_tests_run"]<=len(selected)
                      and code==(0 if observed["native_original_runner_exit_if_zero"] else 1)
                      and not observed["original_unexpected_successes"])
        payload["source_after"]=verify(shard)
        complete=complete and payload["source_before"]==payload["source_after"]
        print("P233_ORIGINAL_WINDOWS_SHARD="+str(shard)
              +"|NATIVE_EXIT="+str(code)
              +"|TESTS_DISCOVERED="+str(len(alltests))
              +"|SELECTED="+str(len(selected))
              +"|COMPLETE="+str(complete).upper(),flush=True)
        print("P233_UNMODIFIED_ORIGINAL_FAILS_NOT_WAIVED=TRUE",flush=True)
    except Exception as e:
        payload["error"]=type(e).__name__+": "+str(e)
        payload["traceback"]=traceback.format_exc()[-2200:]
        print("P233_ORIGINAL_SHARD_DIAGNOSTIC_ERROR="+type(e).__name__,flush=True)
    finally:
        if guard_root is not None:
            # Original P139's non-reparse disposable-root cleanup discipline.
            # The GitHub-hosted disposable Windows VM destroys any residue.
            try:
                attrs=guard_root.lstat()
                if (guard_root.is_symlink() or
                    getattr(attrs,"st_file_attributes",0)&0x400 or
                    not str(guard_root).startswith("C:\\NayeonP139_")):
                    payload["guarded_temp_cleanup"]="REFUSED_UNTRUSTED"
                    complete=False
                else:
                    shutil.rmtree(guard_root)
                    payload["guarded_temp_cleanup"]="OWNED_ROOT_REMOVED"
            except Exception:
                payload["guarded_temp_cleanup"]="UNCERTAIN_VM_DISPOSAL"
                complete=False
        payload["complete_unchanged_original_shard_NOT_a_full_release_suite"]=complete
        (folder/"P233-shard-evidence.json").write_text(
            json.dumps(payload,sort_keys=True,indent=2)+"\n","utf8")
        with (folder/"P233-sha256-receipts.txt").open("w",encoding="ascii") as f:
            for p in sorted(folder.iterdir()):
                if p.is_file() and p.name!="P233-sha256-receipts.txt":
                    f.write(sha(p.read_bytes())+"  "+p.name+"\n")
        print("P233_FULL_RELEASE=HOLD|R0_R4=NO_GO|ORIGINAL_SUITE=0/3",flush=True)
    # Successful diagnostic completion DOES NOT mean the original tests pass.
    return 0 if complete else 1


if __name__=="__main__":
    if len(sys.argv)!=3 or sys.argv[1] not in ("--worker","--parent"):
        raise SystemExit("P233 shard argument required")
    try:
        n=int(sys.argv[2])
    except ValueError:
        raise SystemExit("P233 invalid shard number")
    if not 0<=n<SHARDS:
        raise SystemExit("P233 shard out of bound")
    if sys.argv[1]=="--worker":
        folder=Path(os.environ["RUNNER_TEMP"])/("p233-original-Windows-shard-"+str(n))
        raise SystemExit(worker(n,folder))
    raise SystemExit(parent(n))
