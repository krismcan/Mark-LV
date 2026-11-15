"""P229 source-authenticated original P86/P87 failure reproduction on genuine Windows.

P86/P87 original three FAIL are NOT waived. Independently exercises new
P229 current-revision read-only Tk three-button contract. Native exit codes,
unchanged original raw source SHA, original failure IDs, raw logs and
cryptographic receipts are retained. No real key or native credential effects.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
BASE="3bf5df0136b2afbf0730b4f3d6c4a2f0abdfcf9d"
BRANCH="byok-c1-p229-current-windows-connection-view-contract-20261115"
ONLY={
 "tests/test_p229_connection_view_current_revision.py",
 "scripts/p229_windows_current_tk_regression_diagnostic.py",
 ".github/workflows/p229-windows-current-connection-view.yml",
}
FROZEN=(
 "tests/test_p86_live_pending_status_integration.py",
 "tests/test_p87_readonly_custody_observation.py",
 "nayeon/desktop_alpha/workspace_window.py",
 "nayeon/desktop_alpha/application.py",
 "nayeon/desktop_alpha/local_byok_launch_bridge.py",
 "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs",
 "tests/p95_native_custody_preflight/CustodyLedger.cs",
)
LEGACY=(
 "tests.test_p86_live_pending_status_integration.P86ActualConnectionViewTests."
 "test_live_connection_page_default_is_explicitly_unobserved",
 "tests.test_p86_live_pending_status_integration.P86ActualConnectionViewTests."
 "test_no_credential_action_and_no_implicit_refresh",
 "tests.test_p87_readonly_custody_observation.P87ActualConnectionTests."
 "test_production_default_remains_not_observed_without_any_session",
)
ORIGINAL_FAIL={
 "test_live_connection_page_default_is_explicitly_unobserved",
 "test_no_credential_action_and_no_implicit_refresh",
 "test_production_default_remains_not_observed_without_any_session",
}
CANDIDATE="tests.test_p229_connection_view_current_revision"
FORBIDDEN=(
 "OPENAI_API_KEY","AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY",
 "GOOGLE_API_KEY","GITHUB_TOKEN","GH_TOKEN",
 "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
 "P134_NATIVE_WINCRED_EPHEMERAL_AUTH",
)
COUNT=re.compile(r"(?m)^Ran (\d+) tests? in [\d.]+s\r?$")
NAMES=re.compile(r"(?m)^FAIL: (test_[^ (]+) \(")
OK=re.compile(r"(?m)^OK\s*$")


def sha(b):return hashlib.sha256(b).hexdigest().upper()


def git(*args):
    p=subprocess.run(["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
                     capture_output=True,check=True,timeout=25)
    return p.stdout


def verify():
    req={"GITHUB_ACTIONS":"true","RUNNER_OS":"Windows","GITHUB_EVENT_NAME":"push",
         "GITHUB_REPOSITORY":"krismcan/Mark-LV","GITHUB_REF_NAME":BRANCH}
    if sys.platform!="win32" or any(os.getenv(k)!=v for k,v in req.items()):
        raise RuntimeError("P229 wrong actual hosted Windows environment")
    head=git("rev-parse","HEAD").decode().strip()
    if head!=os.getenv("GITHUB_SHA") or git(
        "merge-base",BASE,head).decode().strip()!=BASE:
        raise RuntimeError("P229 current source HEAD/ancestor refused")
    if set(git("diff","--name-only",BASE,head).decode().splitlines())!=ONLY:
        raise RuntimeError("P229 source delta changed original historical files")
    if git("status","--porcelain=v1","-uall").strip():
        raise RuntimeError("P229 checkout not exact pristine source")
    frozen={}
    for rel in FROZEN:
        data=git("show","HEAD:"+rel)
        if data!=(ROOT/rel).read_bytes() or git(
            "rev-parse","HEAD:"+rel)!=git("rev-parse",BASE+":"+rel):
            raise RuntimeError("P229 historical original file changed: "+rel)
        frozen[rel]={"raw_SHA256":sha(data),
                     "git_SHA1":git("rev-parse","HEAD:"+rel).decode().strip()}
    if frozen["tests/p96_native_transaction_negative/PendingCustodyTransaction.cs"]["raw_SHA256"]!=(
        "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB"
    ):
        raise RuntimeError("P229 original P96 source security pin changed")
    if frozen["tests/p95_native_custody_preflight/CustodyLedger.cs"]["raw_SHA256"]!=(
        "93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B"
    ):
        raise RuntimeError("P229 original P95 ledger pin changed")
    new=(ROOT/"tests/test_p229_connection_view_current_revision.py").read_bytes()
    tree=ast.parse(new)
    selected=[c for c in tree.body if isinstance(c,ast.ClassDef)
              and c.name=="CurrentConnectionViewRevision"]
    if len(selected)!=1:
        raise RuntimeError("P229 current GUI test class wrong identity")
    expected_count=len([m for m in selected[0].body if isinstance(m,ast.FunctionDef)
                        and m.name.startswith("test_")])
    if expected_count!=4:
        raise RuntimeError("P229 current contract did not expose exactly 4 methods")
    return {"head":head,"parent":BASE,"frozen_originals":frozen,
            "approved_additive_files":sorted(ONLY),
            "new_current_gui_contract_SHA256":sha(new),
            "new_current_gui_test_count":expected_count}


def execute(label,targets,seconds,folder,env):
    log=folder/(label+".log")
    t=time.monotonic()
    code=125
    with log.open("wb") as stream:
        try:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",*targets],
                             cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL,check=False,timeout=seconds)
            code=p.returncode
        except subprocess.TimeoutExpired:code=124
    raw=log.read_bytes()
    s=raw.decode("utf8","replace")
    result={"label":label,"native_exit":code,"elapsed_seconds":round(time.monotonic()-t,3),
            "raw_log_SHA256":sha(raw),"raw_log_bytes":len(raw),"raw_log":log.name,
            "unittest_count":COUNT.findall(s),"failed_test_names":NAMES.findall(s),
            "reports_OK":bool(OK.search(s)),"text_tail":s[-1300:]}
    print("P229_NATIVE_OBSERVATION="+label+"|EXIT="+str(code)
          +"|LOG_SHA256="+result["raw_log_SHA256"],flush=True)
    return result


def main():
    folder=Path(os.environ["RUNNER_TEMP"])/"p229-current-Windows-connection-view"
    folder.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P229","full_original_product_Windows":"0/3",
            "independent_security_review":"0/7",
            "original_P86_P87_current_suite_status":"FAIL_NOT_WAIVED",
            "native_key_effects":"NOT_ATTEMPTED",
            "real_key_R0_R4":"NO_GO","production_P0_P5":"HOLD",
            "Google_MASTER_and_dashboard":"DEFERRED",
            "records":[]}
    pass_diag=False
    try:
        ledger["source_before"]=verify()
        env=os.environ.copy()
        for forbidden in FORBIDDEN:env.pop(forbidden,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        prior=execute("unaltered-original-P86-P87-red",LEGACY,40,folder,env)
        ledger["records"].append(prior)
        new=execute("additive-current-three-button-contract",(CANDIDATE,),40,folder,env)
        ledger["records"].append(new)
        ledger["source_after"]=verify()
        pass_diag=(
            ledger["source_before"]==ledger["source_after"]
            and prior["native_exit"]==1
            and prior["unittest_count"]==["3"]
            and set(prior["failed_test_names"])==ORIGINAL_FAIL
            and not prior["reports_OK"]
            and new["native_exit"]==0
            and new["unittest_count"]==["4"]
            and not new["failed_test_names"]
            and new["reports_OK"]
        )
        ledger["diagnostic_disposition"]=(
            "ORIGINAL_THREE_REAL_FAIL_PRESERVED_AND_FOUR_ADDITIVE_CURRENT_UI_PASS"
            if pass_diag else "UNEXPECTED_WIN_UI_RESULT_RELEASE_HOLD")
    except BaseException as exc:
        ledger["error"]=type(exc).__name__+": "+str(exc)
        ledger["traceback"]=traceback.format_exc()[-2400:]
        print("P229_SOURCE_OR_GUI_DIAGNOSTIC_FAILED="+type(exc).__name__,flush=True)
    finally:
        ledger["successful_diagnostic_not_original_full_suite"]=pass_diag
        (folder/"P229-native-evidence.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n","utf8")
        with (folder/"P229-sha256-receipts.txt").open("w",encoding="ascii") as receipts:
            for p in sorted(folder.iterdir()):
                if p.is_file() and p.name!="P229-sha256-receipts.txt":
                    receipts.write(sha(p.read_bytes())+"  "+p.name+"\n")
        print("P229_ORIGINAL_CURRENT_P86_P87=FAIL_STILL_UNWAIVED",flush=True)
        print("P229_ORIGINAL_FULL_PRODUCT_REGRESSIONS=0/3|REALKEY=NO_GO|RELEASE=HOLD",flush=True)
    return 0 if pass_diag else 1


if __name__=="__main__":
    raise SystemExit(main())
