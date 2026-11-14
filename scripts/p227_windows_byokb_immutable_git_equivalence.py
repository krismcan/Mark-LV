"""P227 original Windows BYOK-B regression vs immutable-only Git batch candidate.

No original test or security reader file is changed. The candidate intercepts
ONLY the literal pinned Phase 8.36 Git show requests in its isolated
test-only subprocess. Every request retrieves a fresh authentic immutable
Git blob, independently checks Git SHA-1 identity, the original normalized
SHA-256 pin, and the baseline real Git-show bytes. Mutable ref/tree/index/
worktree/branch checks remain native and unmodified. Never production GO.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import unittest
import uuid

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)

ROOT = Path(__file__).resolve().parents[1]
P226 = "65d4ae740b713a86ed34c0d8fb332877765713d3"
BRANCH = "byok-c1-p227-immutable-git-batch-real-test-equivalence-20261114"
ADDED = {
    "scripts/p227_windows_byokb_immutable_git_equivalence.py",
    ".github/workflows/p227-windows-byokb-git-equivalence.yml",
}
TARGET = (
    "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests."
    "test_frozen_commit_index_and_disk_stay_bound"
)
P96_PIN = "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB"
P95_PIN = "93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B"
FROZEN_PATHS = (
    "scripts/p162_windows_immutable_git_batch_candidate.py",
    "scripts/p139_native_fs_verified_local_temp_root.py",
    "tests/test_phase8_byok_b_scope_integrity.py",
    "tests/phase8_byok_b_scope_migration.py",
    "tests/phase8_byok_scope_migration.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/phase_8_32_scope_migration.py",
    "tests/phase_8_34_scope_migration.py",
    "tests/phase_8_36_scope_migration.py",
    "tests/phase_8_37_scope_migration.py",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs",
    "tests/p95_native_custody_preflight/CustodyLedger.cs",
)
REDACT_ENV = (
    "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "P134_NATIVE_WINCRED_EPHEMERAL_AUTH",
)
RAN = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
OK = re.compile(r"(?m)^OK\s*$")
GIT_OID = re.compile(r"[0-9a-f]{40}\Z")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def git(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *args], cwd=ROOT,
        capture_output=True, stdin=subprocess.DEVNULL,
        timeout=30, check=True,
    )
    return completed.stdout


def source_guard() -> dict:
    _guard_runner()
    required = {
        "GITHUB_ACTIONS": "true",
        "RUNNER_OS": "Windows",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REPOSITORY": "krismcan/Mark-LV",
        "GITHUB_REF_NAME": BRANCH,
    }
    if sys.platform != "win32" or any(os.getenv(k) != v for k,v in required.items()):
        raise RuntimeError("P227 only genuine exact-source hosted Windows event")
    head = git("rev-parse", "HEAD").decode("ascii").strip()
    if head != os.environ.get("GITHUB_SHA") or git(
        "merge-base", P226, head
    ).decode("ascii").strip() != P226:
        raise RuntimeError("P227 source head/P226 ancestry mismatch")
    if set(git("diff", "--name-only", P226, head).decode().splitlines()) != ADDED:
        raise RuntimeError("P227 source diff includes original production/test/security")
    if git("status", "--porcelain=v1", "-uall").strip():
        raise RuntimeError("P227 pristine source worktree refused")
    if git("rev-parse", "--show-object-format").strip() != b"sha1":
        raise RuntimeError("P227 object format not historical SHA1")
    sources={}
    for path in FROZEN_PATHS:
        a=git("rev-parse", "HEAD:"+path).strip()
        b=git("rev-parse", P226+":"+path).strip()
        disk=(ROOT/path).read_bytes()
        original=git("show", "HEAD:"+path)
        if a != b or disk != original:
            raise RuntimeError("P227 frozen original disk/Git mismatch: "+path)
        sources[path]={"git_oid":a.decode("ascii"),"sha256":sha(disk)}
    if sources["tests/p96_native_transaction_negative/PendingCustodyTransaction.cs"]["sha256"] != P96_PIN:
        raise RuntimeError("P227 original P96 source pin mismatch")
    if sources["tests/p95_native_custody_preflight/CustodyLedger.cs"]["sha256"] != P95_PIN:
        raise RuntimeError("P227 original P95 source pin mismatch")
    return {"head":head, "p226_parent":P226, "original_paths":sources,
            "only_two_additive_paths":sorted(ADDED)}


def candidate_child()->int:
    """DIAGNOSTIC substitute for immutable-only Git show; NOT original native pass."""
    from scripts import p162_windows_immutable_git_batch_candidate as proto
    from tests import phase_8_37_scope_migration as scope
    if proto.ROOT != ROOT or scope.PROTECTED != "a12565b9be070684e1d7d801ded4833d13121f94":
        raise RuntimeError("P227 protected original historical identity changed")
    if scope.PROTECTED != scope.PROTECTED.lower() or not GIT_OID.fullmatch(scope.PROTECTED):
        raise RuntimeError("P227 protected OID invalid")
    pins = dict(scope.prior.CANDIDATE_SHA256)
    if len(pins) != 19 or git("rev-parse", "--show-object-format").strip() != b"sha1":
        raise RuntimeError("P227 original 19 literal frozen pins missing")
    tree, tree_sha=proto.read_tree(scope.PROTECTED,pins,os.environ.copy())
    if set(tree)!=set(pins):
        raise RuntimeError("P227 source tree does not cover exact pins")
    originals={}
    # The original Git transport is explicitly observed once for each
    # fixed historical path, then EVERY candidate request independently
    # performs a fresh verified Git object read (not a cached-value return).
    for path in sorted(pins):
        actual = git("show",scope.PROTECTED+":"+path)
        oid=tree[path]
        proto.verify_blob(path, oid,
            (oid+" blob "+str(len(actual))+"\n").encode("ascii"),
            actual,b"\n",oid,pins,scope.prior._digest)
        originals[path]=sha(actual)
    first=sorted(pins)[0]
    first_bytes=git("show",scope.PROTECTED+":"+first)
    negatives=proto.negative_contracts(first,tree[first],first_bytes,tree[first],
                                       pins,scope.prior._digest)
    if negatives < 9:
        raise RuntimeError("P227 candidate original corruption negatives incomplete")
    metrics={"mode":"isolated_candidate_only_not_original_git_test",
             "fixed_commit":scope.PROTECTED, "pinned_paths":len(pins),
             "immutable_tree_SHA256":tree_sha,"initial_real_git_show_baselines":len(originals),
             "adversarial_negative_refusals":negatives,
             "fresh_validated_batch_requests":0,"delegated_original_calls":0,
             "candidate_byte_parity":True,"mutable_source_queries_intercepted":0}
    native=subprocess.Popen(["git","cat-file","--batch"],cwd=ROOT,
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        env=os.environ.copy(),bufsize=0)
    original=subprocess.check_output
    try:
        def limited(*args,**kwargs):
            seq=args[0] if args else kwargs.get("args")
            if (isinstance(seq,(list,tuple)) and len(seq)==3
                and seq[0]=="git" and seq[1]=="show"
                and isinstance(seq[2],str)
                and seq[2].startswith(scope.PROTECTED+":")
                and seq[2][len(scope.PROTECTED)+1:] in pins
                and "cwd" in kwargs and Path(kwargs["cwd"]).resolve()==ROOT
                and set(kwargs).issubset({"cwd","stderr","timeout"})):
                path=seq[2][len(scope.PROTECTED)+1:]
                raw=proto.read_batch(native,path,tree[path],tree[path],
                                     pins,scope.prior._digest)
                if sha(raw)!=originals[path]:
                    metrics["candidate_byte_parity"]=False
                    raise RuntimeError("P227 raw original Git show vs fresh batch bytes mismatch")
                metrics["fresh_validated_batch_requests"]+=1
                return raw
            metrics["delegated_original_calls"]+=1
            return original(*args,**kwargs)
        subprocess.check_output=limited
        try:
            suite=unittest.defaultTestLoader.loadTestsFromName(TARGET)
            result=unittest.TextTestRunner(verbosity=2,stream=sys.stderr).run(suite)
        finally:
            subprocess.check_output=original
    finally:
        if native.stdin is not None:
            native.stdin.close()
        try:
            exit_code=native.wait(timeout=10)
        except subprocess.TimeoutExpired:
            native.kill()
            exit_code=native.wait(timeout=5)
        if native.stdout is not None:
            native.stdout.close()
        metrics["original_git_batch_child_exit"]=exit_code
        path=Path(os.environ["P227_CANDIDATE_METRICS"])
        path.write_text(json.dumps(metrics,indent=2,sort_keys=True)+"\n","utf8")
        print("P227_CANDIDATE_FRESH_BATCH_READS="+str(metrics["fresh_validated_batch_requests"]),flush=True)
        print("P227_CANDIDATE_MUTABLE_GIT_QUERIES_DELEGATED="+str(metrics["delegated_original_calls"]),flush=True)
        print("P227_CANDIDATE_NEGATIVE_REFUSALS="+str(negatives),flush=True)
    if exit_code != 0 or metrics["fresh_validated_batch_requests"] < 1:
        return 1
    return 0 if result.wasSuccessful() and result.testsRun==1 else 1


def run_test(name: str, cmd: list[str], timeout: int, env: dict, out: Path)->dict:
    started=time.monotonic()
    log=out/(name+".log")
    code=125; timed_out=False
    with log.open("wb") as stream:
        proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
            stdout=stream,stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try:
            code=proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True; code=124
            subprocess.run(["taskkill","/PID",str(proc.pid),"/T","/F"],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,timeout=12,check=False)
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait(timeout=5)
    raw=log.read_bytes()
    content=raw.decode("utf8","replace")
    counts=[int(x) for x in RAN.findall(content)]
    passed=(code==0 and not timed_out and len(counts)==1
            and counts[0]==1 and OK.search(content) is not None
            and "FAILED (" not in content)
    rec={"label":name,"native_exit":code,"timed_out":timed_out,
         "elapsed_seconds":round(time.monotonic()-started,3),
         "original_test_id":TARGET,
         "original_source_test_bytes_changed":False,
         "raw_log":log.name,"raw_log_sha256":sha(raw),
         "raw_log_bytes":len(raw),
         "reported_original_method_count":counts,
         "test_pass":bool(passed)}
    print("P227_OBSERVED="+name+"|NATIVE_EXIT="+str(code)+
          "|PASS="+str(passed).upper()+"|ELAPSED="+str(rec["elapsed_seconds"])+
          "|RAW_LOG_SHA256="+rec["raw_log_sha256"],flush=True)
    return rec


def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"p227-actual-original-vs-immutable-candidate"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P227","original_full_windows_regressions":"0/3",
            "independent_GOV_SEC_REL_signoffs":"0/7",
            "real_key_R0_R4":"NO_GO","production_P0_P5":"HOLD",
            "original_P96_race":"OPEN","source_test_files_modified":False,
            "historical_git_reader_deployed_or_changed":False,
            "Google_Drive_master_or_dashboard_updated":False,"records":[]}
    owned=None
    success=False
    try:
        ledger["verified_source_before"]=source_guard()
        # Original P139 Win32 handle-based no-reparse policy remains intact.
        owned=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
        if owned.exists() or owned.is_symlink():
            raise RuntimeError("P227 disposable owned root unexpectedly exists")
        os.mkdir(owned)
        _verify_original_handle_policy(str(owned))
        env=os.environ.copy()
        for key in REDACT_ENV: env.pop(key,None)
        env.update({"TEMP":str(owned),"TMP":str(owned),"TMPDIR":str(owned),
                    "PYTHONDONTWRITEBYTECODE":"1",
                    "P227_CANDIDATE_METRICS":str(out/"candidate-metrics.json")})
        ledger["records"].append(run_test("original-unmodified",
            [sys.executable,"-B","-m","unittest","-v",TARGET],
            125,env,out))
        ledger["records"].append(run_test("immutable-batch-candidate-only",
            [sys.executable,"-B","-m","scripts.p227_windows_byokb_immutable_git_equivalence",
             "--candidate"],125,env,out))
        metrics_path=out/"candidate-metrics.json"
        ledger["candidate_metrics"]=json.loads(metrics_path.read_text("utf8")) if metrics_path.exists() else None
        ledger["verified_source_after"]=source_guard()
        success=(len(ledger["records"])==2
                 and all(x["test_pass"] for x in ledger["records"])
                 and ledger["verified_source_before"]==ledger["verified_source_after"]
                 and ledger["candidate_metrics"] is not None
                 and ledger["candidate_metrics"]["fresh_validated_batch_requests"]>0
                 and ledger["candidate_metrics"]["candidate_byte_parity"]
                 and ledger["candidate_metrics"]["adversarial_negative_refusals"]>=9
                 and ledger["candidate_metrics"]["original_git_batch_child_exit"]==0)
        if success:
            base=ledger["records"][0]["elapsed_seconds"]
            trial=ledger["records"][1]["elapsed_seconds"]
            ledger["observed_single_run_elapsed_ratio"]=round(base/trial,3) if trial>0 else None
    except BaseException as exc:
        ledger["error"]=type(exc).__name__+": "+str(exc)
        ledger["traceback"]=traceback.format_exc()[-2400:]
        print("P227_SOURCE_BOUND_OR_WINDOWS_TEST_FAILURE="+type(exc).__name__,flush=True)
    finally:
        if owned and owned.exists():
            # The disposable runner will destroy itself rather than traverse
            # a potentially replaced junction/reparse-point fixture.
            try:
                attrs=owned.lstat()
                if owned.is_symlink() or getattr(attrs,"st_file_attributes",0)&0x400:
                    ledger["cleanup"]="REFUSED_POTENTIAL_REPARSE"
                else:
                    shutil.rmtree(owned)
                    ledger["cleanup"]="ATTEMPTED"
            except OSError:
                ledger["cleanup"]="FAILED_EPHEMERAL_RUNNER_HOLD"
        ledger["equivalence_diagnostic_success_NOT_release"]=success
        (out/"p227-evidence-manifest.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n","utf8")
        with (out/"p227-sha256-receipts.txt").open("w",encoding="ascii") as f:
            for path in sorted(out.iterdir()):
                if path.is_file() and path.name!="p227-sha256-receipts.txt":
                    f.write(sha(path.read_bytes())+"  "+path.name+"\n")
        print("P227_FULL_WINDOWS_UNFILTERED=0/3|REALKEY=NO_GO|PRODUCTION=HOLD",flush=True)
        print("P227_IMMUTABLE_CANDIDATE_NOT_DEPLOYED=TRUE",flush=True)
    return 0 if success else 1


if __name__=="__main__":
    raise SystemExit(candidate_child() if "--candidate" in sys.argv else main())
