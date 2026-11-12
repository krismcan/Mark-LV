"""P175: isolated, versioned current-source security candidate and historical H/C/R.

Diagnostic ONLY. Authenticated hosted-Windows GitHub push, immutable original
production/test trees, source-bound original negative results, genuine native
unittest counts and log hashes. No approval, live credential or release.
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
import unittest
import uuid
import zipfile

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from scripts.p172_windows_versioned_ui_wincred_admission import (
    CURRENT_CONSUMERS, UI_BUTTONS, secret_consumer_provenance,
    source_ui_conflicts,
)

ROOT=Path(__file__).resolve().parents[1]
BRANCH="byok-c1-p175-current-source-security-admission-20261112"
BASE="98437f4c4e8a09b507bc998a2829bafcc430f8a7"
P140="9c47bac3308822e11300381017b30e913ffbc211"
P173="b04af8858dbaab6d164352832c6757db0ec1681c"
P174_ARTIFACT=13957432345
P174_SHA="D91607E9076A488F32023D257F106F0FB70A4AC5D408B38A870AC68F6E1A2853"
NEW={
    "scripts/p175_windows_current_source_security_candidate.py",
    "docs/byok-c1-p175-versioned-current-candidate-security-review.md",
    ".github/workflows/p175-windows-current-source-security-candidate.yml",
}
P140_CASES={
    "original_P140_scope_migration_6":(6,0,"PASS",None),
    "original_P140_frozen_signed_companion_24":(24,0,"PASS",None),
}
P173_CASES={
    "original_P140_scope_migration_6":(6,1,"HOLD",
        "test_exact_p139_ancestry_and_approved_six_path_change"),
    "original_P140_frozen_signed_companion_24":(24,0,"PASS",None),
}
ORIGINAL_P86=("tests.test_p86_live_pending_status_integration.P86ActualConnectionViewTests.")
ORIGINAL_P87=("tests.test_p87_readonly_custody_observation.P87ActualConnectionTests.")
GROUPS=(
    ("P175_versioned_current_contract_8",
     ["scripts.p175_windows_current_source_security_candidate.P175CurrentContracts"],8,"PASS"),
    ("P133_original_full_manual_offline_launch_25",
     ["tests.test_p133_connection_launch"],25,"PASS"),
    ("WinCred_original_synthetic_fake_native_20",
     ["tests.test_windows_credential_backend.BackendTests",
      "tests.test_windows_credential_backend.NativeAdapterTests"],20,"PASS"),
    ("P76_original_wrong_branch_refusal_1",
     ["tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_wrong_branch_refused_before_other_work"],1,"PASS"),
    ("current_actual_three_button_Tk_offline_probe_1",
     ["--ui-probe"],1,"PASS"),
    ("Phase831_original_forbidden_UI_import_1",
     ["tests.test_phase_831_effect_isolation.Phase831EffectIsolationTests.test_static_production_import_closure_forbids_test_and_effect_routes"],1,"HOLD"),
    ("WinCred_original_fixed_consumer_denial_1",
     ["tests.test_windows_credential_backend.ScopeGuards.test_only_approved_secret_consumers_and_legacy_store_unused"],1,"HOLD"),
    ("P86_original_two_button_assumptions_2",
     [ORIGINAL_P86+n for n in (
       "test_live_connection_page_default_is_explicitly_unobserved",
       "test_no_credential_action_and_no_implicit_refresh")],2,"HOLD"),
    ("P87_original_two_button_assumption_1",
     [ORIGINAL_P87+"test_production_default_remains_not_observed_without_any_session"],1,"HOLD"),
)
FOOTER=re.compile(r"^Ran (\d+) tests? in [0-9.]+s$",re.M)
FAILURES=re.compile(r"^(FAIL|ERROR): (.+)$",re.M)
SENSITIVE={"GITHUB_TOKEN","GH_TOKEN","P175_ARCHIVE_TOKEN","OPENAI_API_KEY",
           "AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY",
           "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN"}
REVIEW={name:"OPEN" for name in
        ("GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        check=True,timeout=35).stdout

def custody()->dict:
    _guard_runner()
    if (sys.platform!="win32" or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",BASE,"HEAD").decode().strip()!=BASE
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P175 source identity, event or clean branch refused")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip()
                           for p in NEW):
        raise RuntimeError("P175 product/test/security change not authorised")
    if (git("rev-parse","HEAD:nayeon")!=git("rev-parse",BASE+":nayeon")
        or git("rev-parse","HEAD:tests")!=git("rev-parse",BASE+":tests")):
        raise RuntimeError("P175 original production/test tree altered")
    existing=[x for x in git("ls-tree","-r","--name-only",BASE,"--","tests")
             .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py",x)]
    if len(existing)!=171:
        raise RuntimeError("P175 original 171 tracked test modules changed")
    for p in ("tests/test_p140_scope_migration.py","tests/test_p140_frozen_signed_companion.py",
              "tests/test_p133_connection_launch.py","tests/test_windows_credential_backend.py",
              "tests/test_phase8_byok_c1_p76_scope.py",
              "nayeon/desktop_alpha/workspace_window.py",
              "nayeon/brain/local_byok_user_scope.py",
              "nayeon/desktop_alpha/local_byok_window.py",
              "nayeon/desktop_alpha/frozen_signed_byok_companion.py"):
        raw=git("show","HEAD:"+p)
        if git("show",BASE+":"+p)!=raw or (ROOT/p).read_bytes()!=raw:
            raise RuntimeError("P175 original current and historical source changed: "+p)
    for p in ("tests/test_p140_scope_migration.py","tests/test_p140_frozen_signed_companion.py"):
        if git("rev-parse",P140+":"+p)!=git("rev-parse","HEAD:"+p):
            raise RuntimeError("P175 immutable P140 original test blob modified")
    return {"P175_exact_push_head":git("rev-parse","HEAD").decode().strip(),
            "P174_parent":BASE,"P140_original_source":P140,"P173_descendant":P173,
            "three_new_evidence_only_paths":sorted(NEW),
            "original_test_module_count":len(existing),
            "original_nayeon_and_tests_trees_unchanged":True}

def authenticate_p174_archive(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P175 read-only GitHub artifact token unavailable")
    raw=_download_artifact(P174_ARTIFACT,P174_SHA,token)
    if sha(raw)!=P174_SHA:
        raise RuntimeError("P174 ZIP authenticity mismatch")
    report={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise RuntimeError("P174 archive CRC invalid")
        needed={"p174_historical_current_scope_governance_ledger.json"}
        for era in ("P140","P173"):
            for label in P140_CASES:
                for ext in ("stdout.log","stderr.log","combined.log"):
                    needed.add(era+"_"+label+"."+ext)
        if len(z.namelist())!=13 or set(z.namelist())!=needed:
            raise RuntimeError("P174 exact 13 original native archive members changed")
        ledger=json.loads(z.read("p174_historical_current_scope_governance_ledger.json"))
        if (ledger.get("checkpoint")!="P174"
            or ledger.get("source_custody",{}).get("P174_actual_head")!=BASE
            or ledger.get("source_custody",{}).get("P140_historical_source")!=P140
            or ledger.get("source_custody",{}).get("P173_authenticated_descendant")!=P173
            or ledger.get("production_R")!="HOLD"
            or ledger.get("historical_H")!="HOLD_UNTIL_QUALIFIED_GOVERNANCE"
            or ledger.get("accepted_complete_full_product_Windows_regressions")!="0/3"
            or ledger.get("review_decisions")!=REVIEW
            or not ledger.get("complete_native_evidence")):
            raise RuntimeError("P174 historical/current/release governance ledger drift")
        for era,expected in (("P140",P140_CASES),("P173",P173_CASES)):
            rows=ledger["native"][era]
            if set(rows)!=set(expected):
                raise RuntimeError("P174 native four-group inventory drift")
            for label,(expected_count,expected_exit,expected_status,required_failure) in expected.items():
                row=rows[label]
                prefix=era+"_"+label
                stdout=z.read(prefix+".stdout.log")
                stderr=z.read(prefix+".stderr.log")
                combined=z.read(prefix+".combined.log")
                if combined!=stdout+b"\n--- ORIGINAL STDERR BELOW ---\n"+stderr:
                    raise RuntimeError("P174 raw original stdout/stderr log altered")
                text=combined.decode("utf8","replace").replace("\r\n","\n")
                matches=FOOTER.findall(text)
                count=int(matches[-1]) if matches else None
                issues=FAILURES.findall(text)
                if (count!=expected_count or row["original_complete_count"]!=count
                    or row["native_exit"]!=expected_exit
                    or row["classification"]!=expected_status
                    or row["original_stdout_SHA256"]!=sha(stdout)
                    or row["original_stderr_SHA256"]!=sha(stderr)
                    or row["complete_combined_log_SHA256"]!=sha(combined)
                    or bool(issues)!=(expected_status=="HOLD")
                    or (expected_status=="PASS" and
                        re.search(r"^OK\s*$",text,re.M) is None)
                    or (required_failure and not any(required_failure in name for _,name in issues))):
                    raise RuntimeError("P174 original immutable test run reclassification: "+prefix)
                report[prefix]={"count":count,"native_exit":expected_exit,
                    "original_status":expected_status,
                    "original_combined_log_SHA256":sha(combined),
                    "named_fail_errors":[{"type":k,"name":n} for k,n in issues]}
    return {"P174_artifact_id":P174_ARTIFACT,"P174_ZIP_SHA256":sha(raw),
            "authenticated_four_unchanged_original_Windows_source_era_runs":report,
            "historical_P140_six_path_test_PASS_on_its_source_only":True,
            "descendant_P173_original_six_path_failure_UNWAIVED":True}

def importer_edges(path:str,src:str)->set[tuple[str,str,tuple[str,...]]]:
    found=set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node,ast.ImportFrom) and node.module in {
                "nayeon.secrets.contracts","nayeon.secrets.windows_credential"}:
            found.add((path,node.module,tuple(sorted(x.name for x in node.names))))
        elif isinstance(node,ast.Import):
            for x in node.names:
                if x.name in {"nayeon.secrets.contracts","nayeon.secrets.windows_credential"}:
                    found.add((path,x.name,("*",)))
    return found

def deny_unapproved_new_imports(path:str,src:str)->bool:
    tree=ast.parse(src)
    if not importer_edges(path,src).issubset(CURRENT_CONSUMERS):
        return True
    if path=="nayeon/desktop_alpha/local_byok_window.py":
        if any(mod=="nayeon.secrets.windows_credential"
               for _,mod,_ in importer_edges(path,src)):
            return True
    banned={"requests","socket","openai","winreg",
            "nayeon.brain.providers.openai_validation","nayeon.secrets.store"}
    for n in ast.walk(tree):
        if isinstance(n,ast.Import) and any(
            x.name in banned for x in n.names):
            return True
        if isinstance(n,ast.ImportFrom) and n.module in banned:
            return True
    return False

class P175CurrentContracts(unittest.TestCase):
    """Versioned candidate; NEVER substitutes original frozen tests or reviewer."""
    def test_01_exact_current_three_button_names_source_bound(self):
        self.assertEqual(UI_BUTTONS,(
            "Back to Conversation","Manage provider (offline preview)",
            "Open local key setup (offline, not connected)"))
    def test_02_current_secret_imports_exactly_three_scoped_edges(self):
        result=secret_consumer_provenance()
        found={(row["source"],row["module"],tuple(row["symbols"]))
              for row in result["three_exact_source_new_current_consumer_edges"]}
        self.assertEqual(found,CURRENT_CONSUMERS)
        self.assertTrue(result["no_new_native_backend_import_from_local_UI"])
    def test_03_unreviewed_native_credential_import_rejected_in_memory(self):
        src="from nayeon.secrets.windows_credential import WindowsCredentialBackend"
        self.assertTrue(deny_unapproved_new_imports(
            "nayeon/desktop_alpha/unreviewed_helper.py",src))
    def test_04_direct_credential_backend_from_UI_rejected_in_memory(self):
        src="from nayeon.secrets.windows_credential import WindowsCredentialBackend"
        self.assertTrue(deny_unapproved_new_imports(
            "nayeon/desktop_alpha/local_byok_window.py",src))
    def test_05_unreviewed_network_or_provider_import_refused_in_memory(self):
        p="nayeon/desktop_alpha/local_byok_window.py"
        for src in ("import requests","import socket",
                    "from nayeon.brain.providers.openai_validation import validate"):
            with self.subTest(src=src):
                self.assertTrue(deny_unapproved_new_imports(p,src))
    def test_06_missing_expected_scoped_source_edge_refused(self):
        for lost in CURRENT_CONSUMERS:
            with self.subTest(lost=lost):
                self.assertNotEqual(CURRENT_CONSUMERS-{lost},CURRENT_CONSUMERS)
    def test_07_phase831_P86_original_import_conflict_unwaived(self):
        conflict=source_ui_conflicts()
        self.assertFalse(conflict["both_literal_original_assertions_simultaneously_satisfiable"])
        self.assertEqual(conflict["import_edges_preserved"],{
            "nayeon.brain.pending_custody_observation_boundary":3,
            "nayeon.brain.pending_custody_status_view":1})
    def test_08_actual_frozen_companion_source_pins_fail_closed(self):
        from nayeon.desktop_alpha import frozen_signed_byok_companion as gate
        self.assertEqual(gate._APPROVED_MAIN_SHA256,"")
        self.assertEqual(gate._APPROVED_COMPANION_SHA256,"")
        self.assertEqual(gate._APPROVED_SIGNER_CERT_SHA256,"")
        self.assertFalse(gate._APPROVED_CODE_INTEGRITY_RELEASE)
        self.assertFalse(gate._release_pins_issued())
        self.assertIsNone(gate.approved_frozen_local_byok_companion())

def run_native(label:str,ids:list[str],expected_count:int,
               target:str,out:Path,fixture:Path)->dict:
    env=os.environ.copy()
    for k in list(env):
        if k in SENSITIVE or k.endswith("_API_KEY") or k.endswith("_SECRET"):
            env.pop(k,None)
    env.update({"TMP":str(fixture),"TEMP":str(fixture),"TMPDIR":str(fixture),
                "PYTHONDONTWRITEBYTECODE":"1"})
    argv=([sys.executable,"-B","-m","scripts.p172_windows_versioned_ui_wincred_admission",
           "--ui-probe"] if ids==["--ui-probe"]
          else [sys.executable,"-B","-m","unittest","-v",*ids])
    fn=out/("p175_original_native_"+label+".log")
    started=time.monotonic()
    timed_out=False
    with fn.open("wb") as f:
        p=subprocess.Popen(argv,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                           stdout=f,stderr=subprocess.STDOUT,
                           creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try:
            exit_code=p.wait(timeout=100)
        except subprocess.TimeoutExpired:
            exit_code=124
            timed_out=True
            subprocess.run(["taskkill","/PID",str(p.pid),"/T","/F"],stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                           check=False,timeout=15)
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=5)
    raw=fn.read_bytes()
    txt=raw.decode("utf8","replace").replace("\r\n","\n")
    counts=FOOTER.findall(txt)
    count=int(counts[-1]) if counts else None
    failures=[{"kind":kind,"original_id":name} for kind,name in FAILURES.findall(txt)]
    actual=("PASS" if exit_code==0 and count==expected_count
            and not failures and re.search(r"^OK\s*$",txt,re.M)
            else "HOLD" if exit_code==1 and count==expected_count
                 and failures and re.search(r"^FAILED \(",txt,re.M)
            else "TIMEOUT" if timed_out else "INCOMPLETE")
    print("P175_ORIGINAL_NATIVE="+label+"|COUNT="+str(count)+"|EXIT="+str(exit_code)+
          "|STATUS="+actual+"|RAW_SHA256="+sha(raw)+"|ISSUES="+str(len(failures)),flush=True)
    return {"expected_original_count":expected_count,"actual_complete_unittest_count":count,
        "native_exit":exit_code,"original_status":actual,"recorded_historical_or_current":target,
        "named_fail_errors":failures,"log_filename":fn.name,"raw_SHA256":sha(raw),
        "seconds":round(time.monotonic()-started,3)}

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p175-current-security-candidate"
    out.mkdir(parents=True,exist_ok=True)
    result={"checkpoint":"P175","source_bound_candidate_NOT_authority":True,
            "review_decisions":REVIEW,"historical_H":"HOLD",
            "current_C":"VERSIONED_SCOPED_CANDIDATE_PENDING_INDEPENDENT_REVIEW",
            "production_R":"HOLD","accepted_full_product_Windows_regressions":"0/3",
            "real_credentials_native_CredRead_Write_Delete_or_provider":"NOT_ATTEMPTED"}
    try:
        before=custody()
        result["source_custody_before"]=before
        result["prior_authentic_P174_original_Windows_evidence"]=authenticate_p174_archive(
            os.environ.get("P175_ARCHIVE_TOKEN",""))
        result["current_credential_source_provenance"]=secret_consumer_provenance()
        result["historical_source_UI_import_conflict"]=source_ui_conflicts()
        fixture=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("P175 randomized local temp root collision")
        os.mkdir(fixture)
        _verify_original_handle_policy(str(fixture))
        original={}
        try:
            for label,ids,count,verdict in GROUPS:
                original[label]=run_native(label,ids,count,verdict,out,fixture)
        finally:
            # Refuse to traverse any replaced junction/reparse target.
            # If uncertain, leave residue to ephemeral host teardown.
            if fixture.exists():
                st=fixture.lstat()
                if fixture.is_symlink() or getattr(st,"st_file_attributes",0)&0x400:
                    raise RuntimeError("P175 unsafe reparse root cleanup refused")
                shutil.rmtree(fixture)
        result["authentic_native_current_and_original_controls"]=original
        result["source_custody_after"]=custody()
        complete=(before==result["source_custody_after"] and
                  all(original[label]["original_status"]==verdict and
                  original[label]["actual_complete_unittest_count"]==count
                  for label,ids,count,verdict in GROUPS))
        result["all_expected_native_PASS_and_genuine_historical_HOLD_captured"]=complete
        result["original_legacy_negative_HOLD_unwaived"]=True
        result["qualified_independent_review_GO"]="NOT_OBTAINED"
        result["signed_main_helper_installer_and_code_integrity_owner_GO"]="NOT_OBTAINED"
        result["privileged_C1_G0_to_G6"]="OPEN"
        print("P175_AUTHENTIC_P174_ARCHIVE=YES",flush=True)
        print("P175_CURRENT_SOURCE_BOUND_DIAGNOSTIC="+("COMPLETE" if complete else "HOLD"),flush=True)
        print("P175_HISTORICAL_NEGATIVES=UNWAIVED",flush=True)
        print("P175_INDEPENDENT_REVIEW_GO=NOT_OBTAINED",flush=True)
        print("P175_PRODUCTION_RELEASE=HOLD|FULL_PRODUCT_ACCEPTED=0/3",flush=True)
        return 0 if complete else 1
    except Exception as exc:
        result["collector_failure"]=repr(exc)
        print("P175_AUTHENTIC_SOURCE_OR_NATIVE_EVIDENCE=HOLD|"+repr(exc),flush=True)
        return 1
    finally:
        (out/"p175_source_bound_versioned_current_security_candidate_ledger.json").write_text(
            json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")

if __name__=="__main__":
    raise SystemExit(main())
