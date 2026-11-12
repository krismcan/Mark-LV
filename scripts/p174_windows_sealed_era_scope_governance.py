"""P174 sealed-era original P140 Windows regression evidence collector (not release GO).

Only on an authenticated, isolated GitHub-hosted Windows push. Unmodified
original tests execute on exact historical P140 and P173 detached worktrees.
Preserve all original native stdout/stderr, failures, exit codes and SHA256.
No production file/test editing, WinCred effects, signing or real credentials.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)

ROOT=Path(__file__).resolve().parents[1]
BRANCH="byok-c1-p174-sealed-era-scope-governance-20261112"
P173="b04af8858dbaab6d164352832c6757db0ec1681c"
P140="9c47bac3308822e11300381017b30e913ffbc211"
P139="052cf4f076d5f2c6e170593cab473d0c8eab7c3a"
NEW={
    ".github/workflows/p174-windows-sealed-era-scope-governance.yml",
    "docs/byok-c1-p174-sealed-era-scope-governance-decision-ledger.md",
    "scripts/p174_windows_sealed_era_scope_governance.py",
}
SIX={
    ".github/workflows/p140-windows-frozen-signed-companion-gate.yml",
    "docs/byok-c1-p140-signed-frozen-companion-release-review.md",
    "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "tests/test_p140_frozen_signed_companion.py",
    "tests/test_p140_scope_migration.py",
}
MODULES={
    "original_P140_scope_migration_6":("tests.test_p140_scope_migration",6),
    "original_P140_frozen_signed_companion_24":("tests.test_p140_frozen_signed_companion",24),
}
FOOTER=re.compile(r"^Ran (\d+) tests? in [\d.]+s$",re.MULTILINE)
ISSUES=re.compile(r"^(FAIL|ERROR): (.+)$",re.MULTILINE)
SENSITIVE={"GITHUB_TOKEN","GH_TOKEN","OPENAI_API_KEY","AZURE_OPENAI_API_KEY",
           "ANTHROPIC_API_KEY","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN"}

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str,cwd:Path=ROOT,timeout:int=60)->str:
    p=subprocess.run(["git","-C",str(cwd),*args],stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     timeout=timeout,check=True)
    return p.stdout.decode("utf8","replace").strip()

def source_identity()->dict:
    _guard_runner()
    if (os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=git("rev-parse","HEAD") or
        git("branch","--show-current")!=BRANCH or
        git("merge-base",P173,"HEAD")!=P173 or
        git("status","--porcelain=v1")):
        raise RuntimeError("P174 exact source branch, SHA, ancestry or cleanliness refused")
    delta=set(git("diff","--name-only",P173,"HEAD").splitlines())
    if delta!=NEW or any(git("ls-tree","--name-only",P173,"--",p) for p in NEW):
        raise RuntimeError("P174 must add exactly three new evidence files")
    if (git("rev-parse",P173+":nayeon")!=git("rev-parse","HEAD:nayeon") or
        git("rev-parse",P173+":tests")!=git("rev-parse","HEAD:tests")):
        raise RuntimeError("P174 original product/test source changed")
    if git("merge-base",P139,P140)!=P139 or git("merge-base",P140,P173)!=P140:
        raise RuntimeError("P140 verified P139 ancestry/P173 descendant mismatch")
    if set(git("diff","--name-only",P139,P140).splitlines())!=SIX:
        raise RuntimeError("Original P139 to P140 six-path delta mismatch")
    if git("diff","--check",P139,P140):
        raise RuntimeError("Unexpected original P140 diff check text")
    if git("diff","--name-status",P139,P140).splitlines().count(
            "M\tnayeon/desktop_alpha/local_byok_launch_bridge.py")!=1:
        raise RuntimeError("Original P140 sole modified product path mismatch")
    original_test_hashes={}
    for test in ("tests/test_p140_scope_migration.py",
                 "tests/test_p140_frozen_signed_companion.py"):
        # Compare Git's immutable original blob identities, not an
        # accidentally stripped text rendering of git-show stdout.
        historical_blob=git("rev-parse",P140+":"+test)
        current_blob=git("rev-parse",P173+":"+test)
        worktree_blob=git("hash-object",test)
        if historical_blob!=current_blob or current_blob!=worktree_blob:
            raise RuntimeError("Original P140 test changed between eras: "+test)
        original_test_hashes[test]=sha((ROOT/test).read_bytes())
    return {"P139_authenticated_parent":P139,"P140_historical_source":P140,
            "P173_authenticated_descendant":P173,"P174_actual_head":git("rev-parse","HEAD"),
            "P139_to_P140_exact_six_source_paths":sorted(SIX),
            "P174_exact_three_additive_paths":sorted(NEW),
            "original_test_source_SHA256":original_test_hashes,
            "original_nayeon_and_tests_tree_equal_P173":True}

def native_case(path:Path,era:str,label:str,module:str,expected:int,out:Path,fixture:Path)->dict:
    env=os.environ.copy()
    for k in SENSITIVE:
        env.pop(k,None)
    env["PYTHONDONTWRITEBYTECODE"]="1"
    for k in ("TMP","TEMP","TMPDIR"):
        env[k]=str(fixture)
    argv=[sys.executable,"-B","-m","unittest","-v",module]
    start=time.monotonic()
    status="COMPLETED"
    try:
        p=subprocess.run(argv,cwd=path,env=env,stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         timeout=180,check=False)
        code=p.returncode
        stdout=p.stdout
        stderr=p.stderr
    except subprocess.TimeoutExpired as exc:
        code=124
        status="TIMEOUT"
        stdout=exc.stdout or b""
        stderr=exc.stderr or b""
    except OSError as exc:
        code=125
        status="SPAWN_ERROR"
        stdout=b""
        stderr=str(exc).encode("utf8","replace")
    prefix=era+"_"+label
    (out/(prefix+".stdout.log")).write_bytes(stdout)
    (out/(prefix+".stderr.log")).write_bytes(stderr)
    combined=stdout+b"\n--- ORIGINAL STDERR BELOW ---\n"+stderr
    (out/(prefix+".combined.log")).write_bytes(combined)
    txt=combined.decode("utf8","replace")
    counts=FOOTER.findall(txt)
    count=int(counts[-1]) if counts else None
    named=[{"kind":k,"name":n} for k,n in ISSUES.findall(txt)]
    result={"era":era,"module":module,"native_exit":code,"run_status":status,
            "original_complete_count":count,"expected_module_test_count":expected,
            "named_FAIL_ERROR":named,"elapsed_seconds":round(time.monotonic()-start,3),
            "original_stdout_SHA256":sha(stdout),"original_stderr_SHA256":sha(stderr),
            "complete_combined_log_SHA256":sha(combined),
            "classification":"PASS" if code==0 and count==expected and
            re.search(r"^OK\s*$",txt,re.MULTILINE) else "HOLD"}
    if count!=expected:
        result["test_count_evidence_gap"]=True
    print("P174_ACTUAL_NATIVE="+json.dumps({prefix:result},sort_keys=True),flush=True)
    return result

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p174-sealed-era"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P174","collector_execution":"SOURCE_MATCHED_WINDOWS_EVIDENCE_ONLY",
            "historical_H":"HOLD_UNTIL_QUALIFIED_GOVERNANCE","current_C":"SCOPED_DIAGNOSTIC_ONLY",
            "production_R":"HOLD","independent_security_GO":"NOT_OBTAINED",
            "approved_signed_companion_and_SAC_WDAC_GO":"NOT_OBTAINED",
            "accepted_complete_full_product_Windows_regressions":"0/3",
            "review_decisions":{k:"OPEN" for k in (
                "GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")},
            "never_waive_original_tests":True,"native":{}}
    try:
        ledger["source_custody"]=source_identity()
        # P139's actual original Win32 handle and no-reparse policy verifies
        # the owned unpredictable fixed-local-drive root before use.
        fixture=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("P174 owned temporary root unexpectedly exists")
        os.mkdir(fixture)
        _verify_original_handle_policy(str(fixture))
        ledger["P139_existing_native_handle_policy_on_disposable_root"]="PASS"
        for era,revision in (("P140",P140),("P173",P173)):
            dest=fixture/("source_"+era.lower())
            git("worktree","add","--detach",str(dest),revision,timeout=120)
            if git("rev-parse","HEAD",cwd=dest)!=revision or git("status","--porcelain=v1",cwd=dest):
                raise RuntimeError("P174 detached original Windows worktree not source clean: "+era)
            ledger["native"][era]={}
            for label,(module,expected) in MODULES.items():
                ledger["native"][era][label]=native_case(dest,era,label,module,expected,out,fixture)
        hist=ledger["native"]["P140"]["original_P140_scope_migration_6"]
        later=ledger["native"]["P173"]["original_P140_scope_migration_6"]
        ledger["historical_vs_later_same_immutable_original_test"]={
            "historical_native_exit":hist["native_exit"],"historical_original_tests":hist["original_complete_count"],
            "descendant_native_exit":later["native_exit"],"descendant_original_tests":later["original_complete_count"],
            "original_hist_failures":hist["named_FAIL_ERROR"],
            "original_descendant_failures":later["named_FAIL_ERROR"],
            "historical_hypothesis_verified":hist["classification"]=="PASS" and
                later["classification"]=="HOLD" and
                any("test_exact_p139_ancestry_and_approved_six_path_change" in e["name"]
                    for e in later["named_FAIL_ERROR"])}
        ledger["complete_native_evidence"]=all(
            item["original_complete_count"]==MODULES[label][1]
            for groups in ledger["native"].values()
            for label,item in groups.items())
        print("P174_HISTORICAL_SCOPE_ACTUAL="+hist["classification"],flush=True)
        print("P174_P173_SCOPE_ACTUAL="+later["classification"],flush=True)
        print("P174_PRODUCTION_RELEASE=HOLD",flush=True)
        return 0 if ledger["complete_native_evidence"] else 1
    except Exception as exc:
        ledger["collector_failure"]=repr(exc)
        print("P174_SOURCE_OR_NATIVE_EVIDENCE_HOLD="+repr(exc),flush=True)
        return 1
    finally:
        (out/"p174_historical_current_scope_governance_ledger.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
        # Do not recursively delete owned trees if a reparse point might have
        # appeared. Ephemeral GitHub-hosted machine is discarded by the runner.

if __name__=="__main__":
    raise SystemExit(main())
