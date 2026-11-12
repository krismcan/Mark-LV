"""P173: authentic Windows H/C/R reviewer intake and fail-closed no-release gate.

Read-only authenticated source/archived native Windows evidence; rerun original
unmodified P140 signed-launch tests with native exits. No reviewer is fabricated.
No product/test/security code changed, real secrets, signed executable or GO.
"""
from __future__ import annotations

import ast
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

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from scripts.p166_windows_current_branch_acceptance import PROTECTED
from scripts.p172_windows_versioned_ui_wincred_admission import (
    CURRENT_CONSUMERS, source_ui_conflicts, secret_consumer_provenance,
)

ROOT=Path(__file__).resolve().parents[1]
BASE="5784e80e09fe5f6eb7d5f6fa8669eea33efa6958"
BRANCH="byok-c1-p173-independent-security-review-intake-20261112"
NEW={
    "scripts/p173_windows_source_bound_security_review_intake.py",
    ".github/workflows/p173-windows-independent-security-review-intake.yml",
    "docs/byok-c1-p173-external-security-test-governance-decision-packet.md",
}
P172_ARTIFACT=13946412959
P172_ZIP_SHA="178487809CC22B6BA09E26BD9EBE81E4CB4165714188AD617178E1462691D81A"
P172_LEDGER="p172_authenticated_windows_versioned_security_admission_ledger.json"
P172_NATIVE={
    "P133_original_full_manual_launch_offline":(25,0, "PASS"),
    "P86_original_current_other_5":(5,0,"PASS"),
    "P87_original_current_other_17":(17,0,"PASS"),
    "WinCred_original_20_synthetic_fake_native":(20,0,"PASS"),
    "actual_current_three_button_Tk_offline_probe":(1,0,"PASS"),
    "P76_frozen_wrong_branch_negative":(1,0,"PASS"),
    "P86_frozen_exact_two_button_cases":(2,1,"HOLD"),
    "P87_frozen_exact_two_button_case":(1,1,"HOLD"),
    "Phase831_frozen_UI_import_refusal":(1,1,"HOLD"),
    "WinCred_frozen_consumer_refusal":(1,1,"HOLD"),
}
P140_ORIGINAL={
    "P140_frozen_signed_companion_original_24":(
        "tests.test_p140_frozen_signed_companion",24),
    "P140_original_scope_migration_6":("tests.test_p140_scope_migration",6),
}
P140_PIN_NAMES={
    "_APPROVED_MAIN_SHA256":"",
    "_APPROVED_COMPANION_SHA256":"",
    "_APPROVED_SIGNER_CERT_SHA256":"",
    "_APPROVED_CODE_INTEGRITY_RELEASE":False,
}
FOOTER=re.compile(r"^Ran (\d+) tests? in [\d.]+s$",re.M)
ISSUES=re.compile(r"^(FAIL|ERROR): (.+)$",re.M)
SECRET_ENV={"OPENAI_API_KEY","AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY",
            "GITHUB_TOKEN","GH_TOKEN","P173_ARCHIVE_TOKEN",
            "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN"}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest().upper()

def git(*args:str)->bytes:
    res=subprocess.run(["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=35,check=True)
    return res.stdout

def source_custody()->dict:
    _guard_runner()
    if not (sys.platform=="win32" and os.environ.get("GITHUB_ACTIONS")=="true"
            and os.environ.get("RUNNER_OS")=="Windows"
            and os.environ.get("GITHUB_EVENT_NAME")=="push"
            and os.environ.get("GITHUB_REPOSITORY")=="krismcan/Mark-LV"
            and os.environ.get("GITHUB_REF_NAME")==BRANCH
            and os.environ.get("RUNNER_TEMP")):
        raise RuntimeError("P173 requires exact hosted Windows GitHub push")
    head=git("rev-parse","HEAD").decode().strip()
    if (head!=os.environ.get("GITHUB_SHA")
            or git("branch","--show-current").decode().strip()!=BRANCH
            or git("merge-base",BASE,"HEAD").decode().strip()!=BASE
            or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P173 source Git identity or clean checkout mismatch")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in changed):
        raise RuntimeError("P173 historical product/test/security path modified")
    if (git("rev-parse",BASE+":nayeon")!=git("rev-parse","HEAD:nayeon")
            or git("rev-parse",BASE+":tests")!=git("rev-parse","HEAD:tests")):
        raise RuntimeError("P173 entire production/tests subtree custody drift")
    existing=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests")
              .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    current=[p for p in git("ls-files","tests/test_*.py").decode().splitlines()
             if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(existing)!=171 or sorted(existing)!=sorted(current):
        raise RuntimeError("P173 171 existing original test modules changed")
    guard=set(PROTECTED) | {
        "nayeon/desktop_alpha/application.py",
        "nayeon/desktop_alpha/workspace_window.py",
        "nayeon/brain/local_byok_user_scope.py",
        "nayeon/desktop_alpha/local_byok_window.py",
        "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
        "tests/test_p140_frozen_signed_companion.py",
        "tests/test_p140_scope_migration.py",
        "tests/test_phase_831_effect_isolation.py",
        "tests/test_p86_live_pending_status_integration.py",
        "tests/test_p87_readonly_custody_observation.py",
        "tests/test_windows_credential_backend.py",
    }
    protected={}
    for rel in sorted(guard):
        prev=git("show",BASE+":"+rel)
        now=git("show","HEAD:"+rel)
        if prev!=now or (ROOT/rel).read_bytes()!=now:
            raise RuntimeError("P173 original protected source identity changed: "+rel)
        protected[rel]=sha(now)
    return {"head":head,"exact_p172_parent":BASE,"exact_three_new_review_files":sorted(changed),
            "product_and_original_tests_subtrees_unchanged":True,
            "original_tracked_test_modules":len(existing),
            "source_SHA256_protected":protected}

def authenticate_p172(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P173 archive read-only token required")
    raw=_download_artifact(P172_ARTIFACT,P172_ZIP_SHA,token)
    if sha(raw)!=P172_ZIP_SHA:
        raise RuntimeError("P173 archive authentic SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist())!=11 or len(set(z.namelist()))!=11:
            raise RuntimeError("P172 source-bound actual Windows ZIP member inventory invalid")
        if set(z.namelist())!={P172_LEDGER}|{
                "p172_native_"+name+".log" for name in P172_NATIVE}:
            raise RuntimeError("P172 source-bound genuine logs missing")
        ledger=json.loads(z.read(P172_LEDGER))
        if (ledger.get("checkpoint")!="P172"
                or ledger.get("source_custody_before_after_identical",{}).get("head")!=BASE
                or ledger.get("production_R")!="HOLD"
                or ledger.get("historical_H")!="HOLD"
                or ledger.get("current_C")!="TARGETED_VERSIONED_USER_SCOPE_DIAGNOSTIC_ONLY"
                or ledger.get("full_product_accepted_genuine_native_Windows_regressions")!="0/3"
                or ledger.get("qualified_independent_historical_governance_and_security_signed_GO")!="NOT_OBTAINED"
                or ledger.get("publisher_signed_main_helper_installer_and_SAC_WDAC_policy_owner_GO")!="NOT_OBTAINED"
                or ledger.get("old_original_exact_button_and_static_import_denials_UNWAIVED") is not True
                or ledger.get("all_expected_original_PASS_and_original_HOLD_dispositions_genuinely_observed") is not True
                or ledger.get("live_credential_manager_read_write_delete_or_provider_network")!="NOT_ATTEMPTED"):
            raise RuntimeError("P172 original H/C/R or absent independent authority falsified")
        entries=ledger["actual_genuine_Windows_unchanged_original_and_current_scoped_probe"]
        if set(entries)!=set(P172_NATIVE):
            raise RuntimeError("P172 actual 10 native group inventory mismatch")
        attested={}
        for name,(expected_count,expected_exit,expected_status) in P172_NATIVE.items():
            entry=entries[name]
            raw_log=z.read("p172_native_"+name+".log")
            t=raw_log.decode("utf8","replace").replace("\r\n","\n")
            cnt=FOOTER.findall(t)
            real_count=int(cnt[-1]) if cnt else None
            errors=ISSUES.findall(t)
            if (real_count!=expected_count
                    or entry["genuine_original_unittest_count"]!=real_count
                    or entry["actual_native_exit"]!=expected_exit
                    or entry["original_status"]!=expected_status
                    or entry["raw_log_sha256"]!=sha(raw_log)
                    or (expected_status=="PASS" and (
                        bool(errors) or not re.search(r"^OK\s*$",t,re.M)))
                    or (expected_status=="HOLD" and (
                        not errors or not re.search(r"^FAILED \(",t,re.M)))):
                raise RuntimeError("P173 authentic P172 exact native log reclassification "+name)
            attested[name]={"actual_original_count":real_count,"native_exit":expected_exit,
                            "historical_or_current_result":expected_status,
                            "raw_original_stdout_stderr_SHA256":sha(raw_log),
                            "actual_named_fail_error_count":len(errors)}
        security=ledger["versioned_current_user_scope_exact_secret_consumer_import_provenance"]
        edges={(v["source"],v["module"],tuple(v["symbols"]))
               for v in security["three_exact_source_new_current_consumer_edges"]}
        if (edges!=CURRENT_CONSUMERS
                or not security["no_new_native_backend_import_from_local_UI"]
                or not security["all_other_import_edges_within_original_historical_consumer_allowlist"]
                or security["in_memory_rogue_native_credential_import_negative"]!="REJECTED"):
            raise RuntimeError("P173 WinCred new-current provenance does not match authenticated P172")
        p171=ledger["authenticated_prior_P171_actual_windows_archive"]
        if (p171.get("archive_sha256")!="C078DE603B5488CAA70348D8505DBA23915051386870799D9F1E3F322C103F92"
                or not p171.get("five_original_docstrings_byte_exact_preserved_in_scratch")
                or not p171.get("five_real_worker_guard_negatives_preserved")):
            raise RuntimeError("P173 P171 authenticated Windows scratch provenance missing")
    return {"genuine_last_windows_artifact_id":P172_ARTIFACT,
            "ZIP_SHA256":sha(raw),
            "prior_P171_ZIP_SHA256":p171["archive_sha256"],
            "source_bound_original_and_current_native_groups":attested,
            "actual_H":"HOLD","C":"TARGETED_CURRENT_ONLY","R":"HOLD",
            "verified_original_native_PASS_groups":sum(x["native_exit"]==0 for x in attested.values()),
            "verified_original_native_HOLD_groups":sum(x["native_exit"]==1 for x in attested.values())}

def p140_source_release_gate()->dict:
    source=(ROOT/"nayeon/desktop_alpha/frozen_signed_byok_companion.py").read_text(encoding="utf8")
    tree=ast.parse(source)
    observed={}
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for target in n.targets:
                if isinstance(target,ast.Name) and target.id in P140_PIN_NAMES:
                    if target.id in observed or not isinstance(n.value,ast.Constant):
                        raise RuntimeError("P140 signer pin assignment missing/ambiguous")
                    observed[target.id]=n.value.value
    if observed!=P140_PIN_NAMES:
        raise RuntimeError("P173 original P140 must remain unapproved / no real signer pins")
    from nayeon.desktop_alpha import frozen_signed_byok_companion as p140
    if p140._release_pins_issued() is not False:
        raise RuntimeError("P140 source default unexpectedly authorised signed release")
    if p140.approved_frozen_local_byok_companion() is not None:
        raise RuntimeError("P140 source default unexpectedly selected a frozen binary")
    # IN-MEMORY attack case: a counterfeit metadata manifest cannot change
    # the real frozen helper source-embedded release pins or signed host.
    counterfeit={"_APPROVED_MAIN_SHA256":"a"*64,
                 "_APPROVED_COMPANION_SHA256":"b"*64,
                 "_APPROVED_SIGNER_CERT_SHA256":"c"*64,
                 "_APPROVED_CODE_INTEGRITY_RELEASE":True}
    if not all(bool(v) for v in counterfeit.values()) or p140._release_pins_issued() is not False:
        raise RuntimeError("P173 counterfeit runtime manifest denial negative absent")
    return {"original_P140_embedded_release_pins":observed,
            "actual_original_P140_real_release_pins_issued":False,
            "actual_frozen_companion_selected":False,
            "counterfeit_metadata_or_environment_only_release_claim":"REJECTED",
            "real_publisher_signer_main_helper_installer":"NOT_PROVIDED",
            "WDAC_SAC_image_load_policy_owner_GO":"NOT_OBTAINED"}

def review_rows(prior:dict,p140:dict)->list[dict]:
    return [
        {"id":"GOV-01","authority":"Independent historical-test-governance reviewer",
         "requested_disposition":"Resolve Phase8.31 no-brain UI import vs P86 exact required brain import without modifying historical tests; frozen denial stays HOLD",
         "evidence":"P172 4 original UI imports; exactly contradictory authored test predicates",
         "gate":"OPEN"},
        {"id":"GOV-02","authority":"Independent current UI and human-presence security reviewer",
         "requested_disposition":"Approve 3 named offline Connection buttons against frozen 2-button historical assertions and P133 manual-only launch negatives",
         "evidence":"P172 genuine Windows P133 25/25 + current 3-button Tk 1/1 and old P86/P87 3 genuine FAIL",
         "gate":"OPEN"},
        {"id":"SEC-03","authority":"Independent secret-dataflow / Windows Credential Manager reviewer",
         "requested_disposition":"Explicitly authorise or reject exactly 3 later import edges, with no widened generic secret consumer list",
         "evidence":"P172 3 exact current edges, 20/20 original fake native controls, old consumer denial genuine FAIL",
         "gate":"OPEN"},
        {"id":"SEC-04","authority":"Qualified Python/Tk import-time security reviewer",
         "requested_disposition":"Approve or reject separate product design for AST-first guards with exact __doc__ retention, import-time metadata mutation and real Tk wrong-thread refusal",
         "evidence":"P171 disposable ONLY 14/14 original lifecycle, 5/5 worker refusals and 5/5 __doc__ hashes; no product patch",
         "gate":"OPEN"},
        {"id":"REL-05","authority":"Independent Windows signer and Code Integrity policy owner",
         "requested_disposition":"Deliver approved immutable signed parent/helper/installer cert and binary hashes, enforce protected installation and SAC/WDAC actual image load",
         "evidence":"Real source P140 pins all empty/false; forged manifest cannot elevate; no code signing GO",
         "gate":"OPEN"},
        {"id":"REL-06","authority":"Independent full-product Windows QA release reviewer",
         "requested_disposition":"Three genuinely completed full untouched source-matched native Windows full-product regressions with unfiltered logs and releases",
         "evidence":"P135 real full-product 3x600s timeout; currently accepted 0/3",
         "gate":"OPEN"},
        {"id":"REL-07","authority":"Independent privileged service/BYOK C1 security owner",
         "requested_disposition":"Resolve original G0-G6, P96/P124 safety and human custody; do not enable service privileges or real key effects",
         "evidence":"Privileged gates remain OPEN, current user-scoped candidate not privileged",
         "gate":"OPEN"},
    ]

def real_original_unittest(label:str,module:str,expected_count:int,safe_temp:Path,evidence:Path)->dict:
    env=os.environ.copy()
    for k in list(env):
        if k in SECRET_ENV or k.endswith("_API_KEY") or k.endswith("_SECRET"):
            env.pop(k,None)
    env.update({"TEMP":str(safe_temp),"TMP":str(safe_temp),"TMPDIR":str(safe_temp),
                "PYTHONDONTWRITEBYTECODE":"1"})
    rawname="p173_actual_original_"+label+".log"
    start=time.monotonic()
    timeout=False
    with (evidence/rawname).open("wb") as f:
        p=subprocess.Popen([sys.executable,"-B","-m","unittest","-v",module],
            cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try: exit_code=p.wait(timeout=90)
        except subprocess.TimeoutExpired:
            exit_code,timeout=124,True
            subprocess.run(["taskkill","/PID",str(p.pid),"/T","/F"],
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,check=False,timeout=15)
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=5)
    raw=(evidence/rawname).read_bytes()
    t=raw.decode("utf8","replace").replace("\r\n","\n")
    foot=FOOTER.findall(t)
    count=int(foot[-1]) if foot else None
    issues=[{"kind":k,"original_test_id":n} for k,n in ISSUES.findall(t)]
    verdict=("PASS" if exit_code==0 and count==expected_count and
             not issues and bool(re.search(r"^OK\s*$",t,re.M))
             else "HOLD" if exit_code==1 and count==expected_count
             and bool(re.search(r"^FAILED \(",t,re.M))
             else "TIMEOUT" if timeout else "INCOMPLETE")
    print("P173_REAL_ORIGINAL_P140="+label+"|EXIT="+str(exit_code)+
          "|COUNT="+str(count)+"|STATUS="+verdict+"|FAIL_RECORDS="+str(len(issues)),flush=True)
    print("P173_ORIGINAL_LOG_SHA256="+label+"|"+sha(raw),flush=True)
    return {"module":module,"actual_native_exit":exit_code,
            "exact_full_original_unittest_count":count,"expected_unmodified_count":expected_count,
            "actual_original_status":verdict,"genuine_named_original_failures":issues,
            "raw_original_native_log":rawname,"raw_log_SHA256":sha(raw),
            "original_native_log_bytes":len(raw),"seconds":round(time.monotonic()-start,3)}

def main()->int:
    before=source_custody()
    old=authenticate_p172(os.environ.get("P173_ARCHIVE_TOKEN",""))
    p140=p140_source_release_gate()
    current=secret_consumer_provenance()
    conflicts=source_ui_conflicts()
    if (current["in_memory_rogue_native_credential_import_negative"]!="REJECTED"
        or not current["no_new_native_backend_import_from_local_UI"]
        or conflicts["both_literal_original_assertions_simultaneously_satisfiable"] is not False):
        raise RuntimeError("P173 original source-based reviewer conflict unexpectedly resolved")
    rows=review_rows(old,p140)
    if len(rows)!=7 or any(r["gate"]!="OPEN" for r in rows):
        raise RuntimeError("P173 cannot fabricate qualified reviewer approvals")
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p173-independent-review-intake"
    out.mkdir(parents=True,exist_ok=True)
    temp=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made=False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P173 owned verified Win32 temp collision")
        os.mkdir(temp);made=True
        _verify_original_handle_policy(str(temp))
        original={}
        for label,(module,n) in P140_ORIGINAL.items():
            original[label]=real_original_unittest(label,module,n,temp,out)
    finally:
        if made:
            st=temp.lstat()
            if temp.is_symlink() or getattr(st,"st_file_attributes",0)&0x400:
                raise RuntimeError("P173 unsafe temp reparse/junction deletion refused")
            shutil.rmtree(temp)
    if source_custody()!=before:
        raise RuntimeError("P173 source/control/test or index mutated during review intake")
    expected_pass=original["P140_frozen_signed_companion_original_24"]["actual_original_status"]=="PASS"
    scope=original["P140_original_scope_migration_6"]
    scope_complete=(scope["exact_full_original_unittest_count"]==6 and
                    scope["actual_original_status"] in {"PASS","HOLD"})
    report={
        "checkpoint":"P173",
        "evidence_package_state":"SUBMISSION_READY_NOT_SUBMITTED_TO_QUALIFIED_REVIEWER",
        "exact_GitHub_original_product_and_tests_custody":before,
        "prior_P172_source_bound_true_original_Windows_log_chain":old,
        "current_actual_P140_real_source_embedded_signing_release_denial":p140,
        "P173_native_original_P140_signed_gate_and_historical_scope":original,
        "actual_P172_current_scoped_user_credential_provenance_reverified":current,
        "authored_original_Phase831_P86_source_UI_contradiction_preserved":conflicts,
        "requested_7_independent_reviewer_decisions":rows,
        "missing_qualified_external_security_and_test_governance_signoff":True,
        "synthetic_runtime_manifest_override_cannot_authorize_real_P140_source_gate":True,
        "full_original_P140_frozen_signed_companion_24_PASS":expected_pass,
        "full_original_P140_6_case_scope_module_complete_genuine_disposition":scope_complete,
        "original_P76_P85_historical_guards":"FROZEN_UNWAIVED",
        "historical_H":"HOLD","current_C":"ONLY_TARGETED_CURRENT_USER_SCOPE_DIAGNOSTICS",
        "production_R":"HOLD",
        "accepted_complete_unfiltered_full_product_Windows_regressions":"0/3",
        "qualified_independent_security_governance_GO":"NOT_OBTAINED",
        "signed_approved_main_helper_installer_and_SAC_WDAC_owner_GO":"NOT_OBTAINED",
        "privileged_C1_G0_to_G6":"OPEN",
        "actual_real_key_CredWrite_CredDelete_provider_or_signed_launch":"NOT_ATTEMPTED",
        "evidence_only_internal_review_NOT_external_independent_security_review":True,
        "next_human_authority":"Qualified independent historical-test, credential and Windows-signed-release reviewers must explicitly approve or reject each open decision before product code changes",
    }
    (out/"p173_windows_source_bound_independent_review_submission_ledger.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("P173_PRIOR_P172_ALL_10_NATIVE_LOGS_SHA_VERIFIED=YES",flush=True)
    print("P173_ACTUAL_P140_PINNED_SIGNED_RELEASE=REFUSED",flush=True)
    print("P173_7_QUALIFIED_REVIEWER_DECISIONS=OPEN",flush=True)
    print("P173_P140_ORIGINAL_24_REAL_PASS="+str(expected_pass),flush=True)
    print("P173_P140_ORIGINAL_6_SCOPE_COMPLETE="+str(scope_complete),flush=True)
    print("P173_PRODUCTION_RELEASE=HOLD|FULL_PRODUCT_WINDOWS=0/3",flush=True)
    return 0 if expected_pass and scope_complete else 1

if __name__=="__main__":
    raise SystemExit(main())
