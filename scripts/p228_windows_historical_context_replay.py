"""P228: REAL Windows historical-source compatibility evidence; NO release waiver.

Each original historical test runs on its actual preserved GitHub branch at
the pinned immutable historical commit in a separate disposable clone, with
unaltered original test/source Git blobs. A current-head negative remains a
REAL original current failure. Historical passes do not replace that failure.
No WinCred, credentials, production files or master workbook are modified.
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

ROOT=Path(__file__).resolve().parents[1]
BASE="6ae76e9b3d4ae07d55db8ba9d3b83c52542c988d"
BRANCH="byok-c1-p228-original-historical-source-context-replay-20261115"
ADDED={
 "scripts/p228_windows_historical_context_replay.py",
 ".github/workflows/p228-windows-original-context-replay.yml",
}
HIST=(
 ("p132", "byok-c1-p132-user-scoped-offline-setup-20261109",
  "29c6065c3e04d7af03d97496259e113341994c49",
  "tests/test_p132_user_scope_migration.py",
  "90eeecaa9e7fc69d1164fc624b7b41d1e792b755",
  (
   "tests.test_p132_user_scope_migration.P132ExplicitConsumerMigration."
   "test_direct_p131_ancestry_and_exact_six_new_paths",
   "tests.test_p132_user_scope_migration.P132ExplicitConsumerMigration."
   "test_no_new_direct_credential_references_outside_approved_files",
  )),
 ("phase10-2","phase10-2-trusted-perception-20261102",
  "4aff3459ee127b0a7a124073aac2a9317e467301",
  "tests/test_phase10_2_privacy_scope_integrity.py",
  "bdfc5cf0940eb12cc0cb92bd034880cbeb928029",
  (
   "tests.test_phase10_2_privacy_scope_integrity.NativeExactSourceAdmissionTests."
   "test_real_complete_source_live_admission",
   "tests.test_phase10_2_privacy_scope_integrity.SyntheticTopologyParserTests."
   "test_wrong_branch_rejects_before_any_current_source",
  )),
 ("phase10-3","phase10-3-synthetic-provenance-redaction-20261104",
  "cacb5c320d26ffa28faf1f15a5e088029ee1453b",
  "tests/test_phase10_3_scope_integrity.py",
  "3aae7cb5b33fcb5e1d9c29c339b5160308696401",
  (
   "tests.test_phase10_3_scope_integrity.NativeAdmissionTests."
   "test_live_and_unconditional_predecessor_route",
   "tests.test_phase10_3_scope_integrity.NativeAdmissionTests."
   "test_wrong_branch_extra_ignored_index_alias_and_forged_staged_blob",
  )),
)
READONLY_SOURCES=(
 "tests/test_p132_user_scope_migration.py",
 "tests/test_phase10_2_privacy_scope_integrity.py",
 "tests/test_phase10_3_scope_integrity.py",
 "tests/test_p166_current_branch_acceptance.py",
 "tests/phase8_byok_b_scope_migration.py",
 "tests/phase10_2_privacy_scope_migration.py",
 "tests/phase10_3_scope_migration.py",
 "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs",
 "tests/p95_native_custody_preflight/CustodyLedger.cs",
)
DENIED_ENV=(
 "OPENAI_API_KEY","ANTHROPIC_API_KEY","AZURE_OPENAI_API_KEY",
 "GOOGLE_API_KEY","GITHUB_TOKEN","GH_TOKEN",
 "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
 "P134_NATIVE_WINCRED_EPHEMERAL_AUTH",
)
RAN=re.compile(r"Ran (\d+) tests? in [\d.]+s")
OK=re.compile(r"(?m)^OK\s*$")
FAILED=re.compile(r"(?m)^FAILED \(([^)]*)\)\s*$")


def sha(data:bytes)->str: return hashlib.sha256(data).hexdigest().upper()


def git(root:Path,*args:str,timeout=25)->bytes:
    return subprocess.run(["git","-C",str(root),*args],check=True,timeout=timeout,
                          stdin=subprocess.DEVNULL,capture_output=True).stdout


def require_current_source():
    expected={
      "GITHUB_ACTIONS":"true","RUNNER_OS":"Windows",
      "GITHUB_EVENT_NAME":"push","GITHUB_REPOSITORY":"krismcan/Mark-LV",
      "GITHUB_REF_NAME":BRANCH,
    }
    if sys.platform!="win32" or any(os.getenv(k)!=v for k,v in expected.items()):
        raise RuntimeError("P228 hosted Windows signed event context missing")
    head=git(ROOT,"rev-parse","HEAD").decode().strip()
    if head!=os.getenv("GITHUB_SHA") or git(
        ROOT,"merge-base",BASE,head).decode().strip()!=BASE:
        raise RuntimeError("P228 wrong actual current head or P227 ancestry")
    delta=set(git(ROOT,"diff","--name-only",BASE,head).decode().splitlines())
    if delta!=ADDED or git(ROOT,"status","--porcelain=v1","-uall").strip():
        raise RuntimeError("P228 unauthorized source modifications")
    fingerprints={}
    for source in READONLY_SOURCES:
        now=git(ROOT,"rev-parse","HEAD:"+source).decode().strip()
        old=git(ROOT,"rev-parse",BASE+":"+source).decode().strip()
        raw=git(ROOT,"show","HEAD:"+source)
        disk=(ROOT/source).read_bytes()
        if now!=old or raw!=disk:
            raise RuntimeError("P228 original source not frozen/equal: "+source)
        fingerprints[source]={"git_sha1":now,"sha256":sha(raw)}
    if fingerprints[
      "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs"
    ]["sha256"]!="D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB":
        raise RuntimeError("P228 original P96 production race object changed")
    if fingerprints[
      "tests/p95_native_custody_preflight/CustodyLedger.cs"
    ]["sha256"]!="93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B":
        raise RuntimeError("P228 original P95 custody ledger changed")
    return {"actual_SHA":head,"P227_ancestor":BASE,
            "source_pins":fingerprints,
            "original_test_and_security_file_changes":False}


def replay_clone(label,branch,head,path,source_sha,output,manifest):
    """Authentic remote original branch; never synthesize signed GITHUB_SHA."""
    dst=Path(os.environ["RUNNER_TEMP"])/"p228-ephemeral-historical-clones"/("actual-original-"+label)
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():
        raise RuntimeError("P228 historical workspace unexpectedly preexists")
    command=["git","-c","core.autocrlf=false","clone","--quiet",
             "--branch",branch,"--single-branch",
             "https://github.com/krismcan/Mark-LV.git",str(dst)]
    t=time.monotonic()
    proc=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,
                        timeout=125,check=False)
    if proc.returncode:
        raise RuntimeError("P228 authentic original GitHub branch clone failed: "+label)
    if git(dst,"rev-parse","HEAD").decode().strip()!=head:
        raise RuntimeError("P228 historical GitHub branch has moved: "+label)
    if git(dst,"branch","--show-current").decode().strip()!=branch:
        raise RuntimeError("P228 original literal branch not authenticated: "+label)
    if git(dst,"status","--porcelain=v1","-uall").strip():
        raise RuntimeError("P228 historical source checkout not pristine: "+label)
    orig_oid=git(dst,"rev-parse","HEAD:"+path).decode().strip()
    if orig_oid!=source_sha or git(dst,"show","HEAD:"+path)!=(dst/path).read_bytes():
        raise RuntimeError("P228 historical original test Git blob mismatch: "+label)
    if git(ROOT,"merge-base",head,BASE).decode().strip()!=head:
        raise RuntimeError("P228 historical source not ancestor of P227: "+label)
    live_oid=git(ROOT,"rev-parse","HEAD:"+path).decode().strip()
    return dst,{"label":label,"original_branch":branch,"original_HEAD":head,
                "historic_test_blob":orig_oid,
                "current_test_blob":live_oid,
                "historic_test_amended_in_current_source":orig_oid!=live_oid,
                "independent_authentic_https_clone":True,
                "clone_elapsed_seconds":round(time.monotonic()-t,3),
                "original_source_test_modified_in_historical_clone":False}


def run_real_original(label,root:Path,methods,output,env,seconds)->dict:
    stdout=output/(label+".log")
    started=time.monotonic()
    cmd=[sys.executable,"-B","-m","unittest","-v",*methods]
    code=125; timed=False
    with stdout.open("wb") as sink:
        proc=subprocess.Popen(cmd,cwd=root,env=env,
                              stdin=subprocess.DEVNULL,
                              stdout=sink,stderr=subprocess.STDOUT,
                              creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try:code=proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            code=124;timed=True
            subprocess.run(["taskkill","/PID",str(proc.pid),"/T","/F"],
                           check=False,timeout=15,stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait(timeout=5)
    raw=stdout.read_bytes()
    s=raw.decode("utf8","replace")
    counts=RAN.findall(s)
    ok=code==0 and not timed and counts==[str(len(methods))] and bool(OK.search(s))
    rec={"label":label,"authentic_test_methods":list(methods),
         "native_exit":code,"timed_out":timed,
         "original_unittest_results":counts,
         "passes_without_source_modification":ok,
         "elapsed_seconds":round(time.monotonic()-started,3),
         "raw_output_sha256":sha(raw),"raw_output_bytes":len(raw),
         "original_log":stdout.name,
         "historical_positive_NOT_current_release":True}
    print("P228_ORIGINAL_HISTORICAL="+label+"|EXIT="+str(code)
          +"|PASS="+str(ok).upper()+"|SHA256="+sha(raw),flush=True)
    return rec


def run_current_negative(output,env):
    """REAL failure is intentionally preserved, never labelled a suite pass."""
    target=HIST[0][5][0] # Original P132 source inventory test on current P228 HEAD.
    log=output/"current-original-P132-real-failure.log"
    started=time.monotonic()
    p=subprocess.run([sys.executable,"-B","-m","unittest","-v",target],
                     cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                     capture_output=True,timeout=40,check=False)
    raw=p.stdout+p.stderr
    log.write_bytes(raw)
    s=raw.decode("utf8","replace")
    expected=(p.returncode!=0 and "FAIL" in s and
              target.rsplit(".",1)[-1] in s and
              "AssertionError" in s and "Ran 1 test" in s)
    print("P228_CURRENT_ORIGINAL_P132_IS_STILL_RED="+str(expected).upper()
          +"|ORIGINAL_NATIVE_EXIT="+str(p.returncode),flush=True)
    return {"exact_current_original_test":target,
            "expected_unmodified_original_failure_observed":expected,
            "native_exit":p.returncode,"log_sha256":sha(raw),
            "elapsed_seconds":round(time.monotonic()-started,3),
            "log_name":log.name,
            "not_waived_not_recast_green":True}


def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"p228-original-historical-context"
    out.mkdir(exist_ok=True,parents=True)
    ledger={"checkpoint":"P228","prerequisite_P227":BASE,
            "original_full_product_windows": "0/3",
            "original_current_failures": "NOT_WAIVED",
            "independent_review_signoffs":"0/7",
            "R0_R4":"NO_GO","P0_P5":"HOLD","P96_original_race":"OPEN",
            "workbook_and_dashboard":"NOT_TOUCHED",
            "historical_original_runs":[],"source_replays":[]}
    success=False
    try:
        ledger["source_before"]=require_current_source()
        env=os.environ.copy()
        for item in DENIED_ENV: env.pop(item,None)
        env.update({"PYTHONDONTWRITEBYTECODE":"1"})
        ledger["current_negative"]=run_current_negative(out,env)
        for label,branch,head,path,oid,methods in HIST:
            dst,identity=replay_clone(label,branch,head,path,oid,out,ledger)
            ledger["source_replays"].append(identity)
            ledger["historical_original_runs"].append(run_real_original(
                label,dst,methods,out,env,150))
        ledger["source_after"]=require_current_source()
        success=(ledger["source_before"]==ledger["source_after"] and
                 ledger["current_negative"]["expected_unmodified_original_failure_observed"]
                 and len(ledger["historical_original_runs"])==len(HIST)
                 and all(row["passes_without_source_modification"]
                         for row in ledger["historical_original_runs"]))
    except Exception as exc:
        ledger["error"]=type(exc).__name__+": "+str(exc)
        ledger["traceback"]=traceback.format_exc()[-1900:]
        print("P228_ORIGINAL_SOURCE_REPLAY_FAILURE="+type(exc).__name__,flush=True)
    finally:
        ledger["historical_replay_success_NOT_release"]=success
        # Never delete on a path surprise: ephemeral hosted Windows runner is
        # destroyed by GitHub; preserve its evidence and avoid junction traversal.
        (out/"P228-historical-evidence.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n","utf8")
        with (out/"P228-sha256-receipts.txt").open("w",encoding="ascii") as s:
            for p in sorted(out.iterdir()):
                if p.is_file() and p.name!="P228-sha256-receipts.txt":
                    s.write(sha(p.read_bytes())+"  "+p.name+"\n")
        print("P228_CURRENT_SOURCE_FULL_SUITE_STILL_FAILED=TRUE",flush=True)
        print("P228_HISTORICAL_REPLAY_NEVER_APPROVES_RELEASE=TRUE",flush=True)
    return 0 if success else 1


if __name__=="__main__":
    raise SystemExit(main())
