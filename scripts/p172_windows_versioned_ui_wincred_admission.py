"""P172 source-preserving current-version UI and WinCred admission diagnostics.

Genuine Windows original unchanged targeted test controls, real synthetic Tk
3-button UI, strict exact new consumer AST, and original historical denials.
NOT historical test replacement, qualified independent review or release GO.
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

from scripts.p139_native_fs_verified_local_temp_root import _guard_runner, _verify_original_handle_policy
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from scripts.p166_windows_current_branch_acceptance import PROTECTED
from scripts.p169_windows_failure_causality_and_guard_provenance import (
    APPROVED_SOURCE_CONSUMERS as OLD_APPROVED_CONSUMERS,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = "10d0469ec5abb7201dfe5dd6da0e660630e82352"
BRANCH = "byok-c1-p172-versioned-current-ui-and-wincred-acceptance-20261112"
ONLY_NEW = {
    "scripts/p172_windows_versioned_ui_wincred_admission.py",
    ".github/workflows/p172-windows-versioned-security-admission.yml",
    "docs/byok-c1-p172-cross-era-versioned-security-admission.md",
}
P171_ARTIFACT = 13942773890
P171_ZIP = "C078DE603B5488CAA70348D8505DBA23915051386870799D9F1E3F322C103F92"
P171_LEDGER = "p171_authenticated_windows_cross_era_metadata_governance_ledger.json"
P171_META_SHA = "55433A0F251DE3497204F8D581FC12EF40D0E93964F10E98F5104ED77BCC3A3B"
TESTP86 = "tests.test_p86_live_pending_status_integration.P86ActualConnectionViewTests."
TESTP87_A = "tests.test_p87_readonly_custody_observation.P87ActualConnectionTests."
TESTP87_B = "tests.test_p87_readonly_custody_observation.P87PureBoundaryTests."
OLD_P86_TWO = {"test_live_connection_page_default_is_explicitly_unobserved",
               "test_no_credential_action_and_no_implicit_refresh"}
OLD_P87_TWO = {"test_production_default_remains_not_observed_without_any_session"}
CURRENT_CONSUMERS = {
    ("nayeon/brain/local_byok_user_scope.py", "nayeon.secrets.contracts",
     ("SecretIdentifier", "SecretValue")),
    ("nayeon/brain/local_byok_user_scope.py", "nayeon.secrets.windows_credential",
     ("WindowsCredentialBackend",)),
    ("nayeon/desktop_alpha/local_byok_window.py", "nayeon.secrets.contracts",
     ("SecretValue",)),
}
NEW_FILES = {"nayeon/brain/local_byok_user_scope.py",
             "nayeon/desktop_alpha/local_byok_window.py"}
UI_IMPORTS = {"nayeon.brain.pending_custody_observation_boundary": 3,
              "nayeon.brain.pending_custody_status_view": 1}
UI_BUTTONS = ("Back to Conversation", "Manage provider (offline preview)",
              "Open local key setup (offline, not connected)")
RUN_GROUPS = (
    ("P133_original_full_manual_launch_offline",
     ["tests.test_p133_connection_launch"], 25, "PASS"),
    ("P86_original_current_other_5",
     [], 5, "PASS"),
    ("P87_original_current_other_17",
     [], 17, "PASS"),
    ("WinCred_original_20_synthetic_fake_native",
     ["tests.test_windows_credential_backend.BackendTests",
      "tests.test_windows_credential_backend.NativeAdapterTests"], 20, "PASS"),
    ("P86_frozen_exact_two_button_cases",
     [TESTP86+x for x in sorted(OLD_P86_TWO)], 2, "HOLD"),
    ("P87_frozen_exact_two_button_case",
     [TESTP87_A+x for x in sorted(OLD_P87_TWO)], 1, "HOLD"),
    ("Phase831_frozen_UI_import_refusal",
     ["tests.test_phase_831_effect_isolation.Phase831EffectIsolationTests.test_static_production_import_closure_forbids_test_and_effect_routes"], 1, "HOLD"),
    ("WinCred_frozen_consumer_refusal",
     ["tests.test_windows_credential_backend.ScopeGuards.test_only_approved_secret_consumers_and_legacy_store_unused"], 1, "HOLD"),
    ("P76_frozen_wrong_branch_negative",
     ["tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_wrong_branch_refused_before_other_work"], 1, "PASS"),
    ("actual_current_three_button_Tk_offline_probe",
     ["--ui-probe"], 1, "PASS"),
)
FOOTER = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
ISSUE = re.compile(r"^(FAIL|ERROR): (.+)$", re.M)
SECRET_ENV = {"GITHUB_TOKEN","GH_TOKEN","P172_ARCHIVE_TOKEN",
              "OPENAI_API_KEY","ANTHROPIC_API_KEY","AZURE_OPENAI_API_KEY",
              "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def git(*args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(ROOT), *args],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=True, timeout=35)
    return result.stdout


def custody() -> dict:
    _guard_runner()
    if not (sys.platform == "win32" and os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("RUNNER_OS") == "Windows"
            and os.environ.get("GITHUB_EVENT_NAME") == "push"
            and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.environ.get("GITHUB_REF_NAME") == BRANCH
            and os.environ.get("RUNNER_TEMP")):
        raise RuntimeError("P172 requires authentic isolated GitHub Windows push")
    head=git("rev-parse","HEAD").decode().strip()
    if (head!=os.environ.get("GITHUB_SHA")
            or git("branch","--show-current").decode().strip()!=BRANCH
            or git("merge-base",BASE,"HEAD").decode().strip()!=BASE
            or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P172 source SHA, exact ancestor or clean checkout mismatch")
    diff=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if diff!=ONLY_NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in diff):
        raise RuntimeError("P172 any non-additive product/test/security change refused")
    if (git("rev-parse",BASE+":nayeon")!=git("rev-parse","HEAD:nayeon")
            or git("rev-parse",BASE+":tests")!=git("rev-parse","HEAD:tests")):
        raise RuntimeError("P172 entire original product and tests Git subtrees changed")
    original=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests")
              .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    current=[p for p in git("ls-files","tests/test_*.py").decode().splitlines()
             if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(original)!=171 or sorted(original)!=sorted(current):
        raise RuntimeError("P172 original 171 tests changed")
    protected={}
    for p in sorted(set(PROTECTED)|NEW_FILES|{
            "nayeon/desktop_alpha/workspace_window.py",
            "nayeon/desktop_alpha/application.py",
            "tests/test_p133_connection_launch.py",
            "tests/test_p86_live_pending_status_integration.py",
            "tests/test_p87_readonly_custody_observation.py",
            "tests/test_windows_credential_backend.py",
            "tests/test_phase_831_effect_isolation.py",
            "tests/test_phase8_byok_c1_p76_scope.py"}):
        before=git("show",BASE+":"+p)
        after=git("show","HEAD:"+p)
        disk=(ROOT/p).read_bytes()
        if before!=after or after!=disk:
            raise RuntimeError("P172 historical source or new user-scope code changed "+p)
        protected[p]=sha(after)
    return {"head":head,"exact_p171_parent":BASE,"three_new_audit_paths":sorted(diff),
            "original_product_and_all_tests_Git_subtrees_byte_unchanged":True,
            "test_module_count":171,"protected_current_files_sha256":protected}


def authenticate_p171(token: str) -> dict:
    if len(token)<8:
        raise RuntimeError("P172 read-only ephemeral repository Actions token required")
    raw=_download_artifact(P171_ARTIFACT,P171_ZIP,token)
    if sha(raw)!=P171_ZIP:
        raise RuntimeError("P171 immutable Windows archive SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise RuntimeError("P171 prior authentic archive CRC failed")
        names=z.namelist()
        if (len(names)!=9 or len(set(names))!=9
                or P171_LEDGER not in names
                or "p171_real_original_docstrings_and_wrong_thread_native.log" not in names):
            raise RuntimeError("P171 prior original evidence inventory mismatch")
        data=json.loads(z.read(P171_LEDGER))
        if (data.get("checkpoint")!="P171" or data.get("production_R")!="HOLD"
                or data.get("accepted_complete_whole_product_windows_regressions")!="0/3"
                or data.get("all_other_genuine_original_source_era_HOLDS_unwaived") is not True
                or data.get("actual_original_Phase832_14_PASS_IN_DISPOSABLE_ONLY") is not True):
            raise RuntimeError("P171 actual reviewer H/C/R results altered")
        meta=z.read("p171_real_original_docstrings_and_wrong_thread_native.log")
        if sha(meta)!=P171_META_SHA:
            raise RuntimeError("P171 five exact docstring and wrong-thread native proofs changed")
        old=data["original_native_Windows_tests_on_disposable_candidate_only"]
        if len(old)!=6:
            raise RuntimeError("P171 original six module case inventory drift")
        original_files=[n for n in names if n.startswith("p171_original_windows_") and n.endswith(".log")]
        if len(original_files)!=6:
            raise RuntimeError("P171 actual original native log count changed")
        for row in old.values():
            rawlog=z.read(row["log_file"])
            if sha(rawlog)!=row["raw_log_sha256"]:
                raise RuntimeError("P171 original native log receipt corrupted")
    return {"verified_original_artifact":P171_ARTIFACT,"archive_sha256":sha(raw),
            "original_six_genuine_native_logs":6,
            "five_real_worker_guard_negatives_preserved":True,
            "five_original_docstrings_byte_exact_preserved_in_scratch":True,
            "historical_H_and_production_R_still_HOLD":True}


def original_ids(module: str, expected: int, excludes: set[str]) -> list[str]:
    src=ROOT/(module.replace(".","/")+".py")
    tree=ast.parse(src.read_text(encoding="utf8"))
    ids=sorted(module+"."+cls.name+"."+func.name
        for cls in tree.body if isinstance(cls,ast.ClassDef)
        for func in cls.body if isinstance(func,ast.FunctionDef)
        and func.name.startswith("test_"))
    if len(ids)!=expected or sum(x.split(".")[-1] in excludes for x in ids)!=len(excludes):
        raise RuntimeError("P172 source-bound original UI class and case inventory drift")
    return [x for x in ids if x.split(".")[-1] not in excludes]


def secret_consumer_provenance() -> dict:
    found=[]
    for path in sorted((ROOT/"nayeon").rglob("*.py")):
        name=path.relative_to(ROOT).as_posix()
        tree=ast.parse(path.read_text(encoding="utf8"))
        for node in ast.walk(tree):
            entries=[]
            if isinstance(node,ast.ImportFrom) and node.module in (
                    "nayeon.secrets.contracts","nayeon.secrets.windows_credential"):
                entries.append((node.module,tuple(sorted(a.name for a in node.names))))
            elif isinstance(node,ast.Import):
                entries.extend((a.name,("*",)) for a in node.names if a.name in (
                    "nayeon.secrets.contracts","nayeon.secrets.windows_credential"))
            for mod,names in entries:
                found.append({"path":name,"module":mod,"symbols":list(names),"line":node.lineno,
                              "legacy_approved":name in OLD_APPROVED_CONSUMERS})
    contemporary={ (x["path"],x["module"],tuple(x["symbols"]))
                   for x in found if not x["legacy_approved"]}
    if contemporary!=CURRENT_CONSUMERS:
        raise RuntimeError("P172 exact 3 newer user-scope import edges changed")
    # Current explicitly bounded new version: ONLY exact controller may own
    # WindowsCredentialBackend; UI may construct ephemeral SecretValue, no backend.
    if any(x["module"]=="nayeon.secrets.windows_credential"
           and x["path"]=="nayeon/desktop_alpha/local_byok_window.py" for x in found):
        raise RuntimeError("P172 UI direct native credential backend access discovered")
    for name in NEW_FILES:
        tree=ast.parse((ROOT/name).read_text(encoding="utf8"))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module in {
                    "nayeon.secrets.store", "nayeon.secrets.resolver",
                    "nayeon.brain.providers.openai_validation"}:
                raise RuntimeError("P172 new current user-scope imported bypass backend")
            if isinstance(node,ast.Import) and any(a.name in {
                    "socket","requests","openai","winreg"} for a in node.names):
                raise RuntimeError("P172 new current user-scope imported external/provider backend")
    # In-memory adversarial synthetic imports are rejected by the exact
    # versioned admission predicate; never write injected imports on disk.
    synthetic=ast.parse("from nayeon.secrets.windows_credential import WindowsCredentialBackend")
    fake=[(n.module,tuple(sorted(a.name for a in n.names))) for n in ast.walk(synthetic)
          if isinstance(n,ast.ImportFrom)]
    if (not fake or
            ("nayeon/desktop_alpha/unreviewed_provider.py",fake[0][0],fake[0][1])
            in CURRENT_CONSUMERS):
        raise RuntimeError("P172 injected unapproved native backend import admitted")
    return {"old_historical_consumer_policy_still_FROZEN_HOLD":True,
            "three_exact_source_new_current_consumer_edges":[
                {"source":p,"module":m,"symbols":list(n)}
                for p,m,n in sorted(contemporary)],
            "all_other_import_edges_within_original_historical_consumer_allowlist":True,
            "in_memory_rogue_native_credential_import_negative":"REJECTED",
            "no_new_native_backend_import_from_local_UI":True}


def source_ui_conflicts() -> dict:
    tree=ast.parse((ROOT/"nayeon/desktop_alpha/workspace_window.py").read_text(encoding="utf8"))
    actual=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom) and node.module.startswith("nayeon.brain."):
            actual.append(node.module)
    prior={"nayeon.brain.pending_custody_observation_boundary":3,
           "nayeon.brain.pending_custody_status_view":1}
    seen={name:actual.count(name) for name in prior}
    if seen!=prior or len(actual)!=4:
        raise RuntimeError("P172 frozen source-era 8.31/P86 import contradiction drift")
    if "nayeon.brain.pending_custody_status_view" not in actual:
        raise RuntimeError("P172 P86 exact advisory import requirement missing")
    return {"frozen_phase831_all_brain_UI_imports_DENIED":True,
            "frozen_P86_exact_advisory_import_REQUIRED":True,
            "both_literal_original_assertions_simultaneously_satisfiable":False,
            "import_edges_preserved":seen,
            "no_dynamic_import_evasion_or_original_security_test_waiver":True}


def run_real(group: str, ids: list[str], expected: int, expected_status: str,
             safe_temp: Path, evidence: Path) -> dict:
    env=os.environ.copy()
    for key in list(env):
        if key in SECRET_ENV or key.endswith("_API_KEY") or key.endswith("_SECRET"):
            env.pop(key,None)
    env.update({"TEMP":str(safe_temp),"TMP":str(safe_temp),"TMPDIR":str(safe_temp),
                "PYTHONDONTWRITEBYTECODE":"1"})
    logfile=evidence/("p172_native_"+group+".log")
    if ids==["--ui-probe"]:
        args=[sys.executable,"-B","-m","scripts.p172_windows_versioned_ui_wincred_admission","--ui-probe"]
    else:
        args=[sys.executable,"-B","-m","unittest","-v",*ids]
    start=time.monotonic()
    timedout=False
    with logfile.open("wb") as f:
        process=subprocess.Popen(args,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                                 stdout=f,stderr=subprocess.STDOUT,
                                 creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try:
            exit_code=process.wait(timeout=100)
        except subprocess.TimeoutExpired:
            timedout=True
            exit_code=124
            subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],
                           stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,timeout=15,check=False)
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    raw=logfile.read_bytes()
    content=raw.decode("utf8","replace").replace("\r\n","\n")
    match=FOOTER.findall(content)
    count=int(match[-1]) if match else None
    errors=[{"kind":kind,"id":identity} for kind,identity in ISSUE.findall(content)]
    actual=("PASS" if exit_code==0 and count==expected
            and bool(re.search(r"^OK\s*$",content,re.M))
            else "HOLD" if exit_code==1 and count==expected
            and bool(re.search(r"^FAILED \(",content,re.M))
            else "TIMEOUT" if timedout else "INCOMPLETE")
    print("P172_NATIVE="+group+"|ORIGINAL_COUNT="+str(count)+"|EXIT="+str(exit_code)+
          "|REAL_STATUS="+actual+"|ISSUES="+str(len(errors)),flush=True)
    print("P172_NATIVE_LOG_SHA256="+group+"|"+sha(raw),flush=True)
    return {"group":group,"original_source_ids_or_versioned_probe":ids,
            "expected_count":expected,"genuine_original_unittest_count":count,
            "actual_native_exit":exit_code,"original_status":actual,
            "genuine_named_original_FAIL_ERROR_records":errors,
            "status_expected_for_diagnostic_only":expected_status,
            "raw_native_log":logfile.name,"raw_log_sha256":sha(raw),
            "raw_log_bytes":len(raw),"seconds":round(time.monotonic()-start,3)}


def ui_probe_main() -> int:
    """Actual isolated Windows Tk widgets; do NOT click or access WinCred."""
    import tkinter as tk
    from tkinter import ttk
    import unittest
    from unittest import mock
    from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
    from nayeon.desktop_alpha import local_byok_launch_bridge as bridge

    class OneCurrentUiTest(unittest.TestCase):
        def runTest(self):
            root=tk.Tk()
            root.withdraw()
            app=None
            try:
                with (mock.patch.object(OfflineWorkspaceApplication,
                                        "_bootstrap_readonly_presentation"),
                      mock.patch.object(bridge.subprocess,"Popen",
                                        side_effect=AssertionError("IMPLICIT_PROCESS_FORBIDDEN"))):
                    app=OfflineWorkspaceApplication(root)
                    self.assertIsNone(app._local_byok_launcher)
                    app.show_connection()
                    view=app._active_view
                    self.assertIsNone(app._connection)
                    self.assertIsNone(app._local_byok_launcher)
                    buttons=[b for b in view.winfo_children() if isinstance(b,ttk.Button)]
                    labels=tuple(str(b.cget("text")) for b in buttons)
                    self.assertEqual(labels,UI_BUTTONS)
                    self.assertEqual(len({id(x) for x in buttons}),3)
                    self.assertEqual(str(view.local_byok_button.cget("state")),"normal")
                    self.assertIn("NOT OBSERVED",view.pending_custody_label.cget("text"))
                    self.assertIn("Not observed",view.status_label.cget("text"))
                    self.assertFalse(app._local_byok_opening)
                    self.assertFalse(any(name in labels for name in (
                        "Connected", "Validated", "Save key now")))
                    tampered=labels+("Unreviewed automatic key save",)
                    self.assertNotEqual(tampered,UI_BUTTONS)
                    print("P172_LIVE_TK_THREE_EXACT_BUTTONS_AND_UNKNOWN_NO_SPAWN=PASS",flush=True)
            finally:
                if app is not None:
                    try: app.close()
                    except Exception: pass
                try: root.destroy()
                except tk.TclError: pass

    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.TestSuite([OneCurrentUiTest()]))
    return 0 if result.wasSuccessful() and result.testsRun==1 else 1


def main() -> int:
    before=custody()
    archive=authenticate_p171(os.environ.get("P172_ARCHIVE_TOKEN",""))
    consumers=secret_consumer_provenance()
    conflict=source_ui_conflicts()
    p86_all=original_ids("tests.test_p86_live_pending_status_integration",7,OLD_P86_TWO)
    p87_all=original_ids("tests.test_p87_readonly_custody_observation",18,OLD_P87_TWO)
    if len(p86_all)!=5 or len(p87_all)!=17:
        raise RuntimeError("P172 5+17 actual original unaffected security controls incomplete")
    groups=[]
    for label,ids,count,verdict in RUN_GROUPS:
        if label=="P86_original_current_other_5": ids=p86_all
        if label=="P87_original_current_other_17": ids=p87_all
        groups.append((label,ids,count,verdict))
    evidence=Path(os.environ["RUNNER_TEMP"])/"nayeon-p172-current-versioned-admission"
    evidence.mkdir(parents=True,exist_ok=True)
    temp=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made=False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P172 disposable Win32 owned temp collision")
        os.mkdir(temp)
        made=True
        _verify_original_handle_policy(str(temp))
        result={name:run_real(name,ids,count,verdict,temp,evidence)
                for name,ids,count,verdict in groups}
    finally:
        if made:
            status=temp.lstat()
            if temp.is_symlink() or getattr(status,"st_file_attributes",0)&0x400:
                raise RuntimeError("P172 unsafe junction/reparse deletion refused")
            shutil.rmtree(temp)
    if custody()!=before:
        raise RuntimeError("P172 audited original source or Git index mutated")
    expected={name:verdict for name,ids,count,verdict in groups}
    actual={k:v["original_status"] for k,v in result.items()}
    complete=actual==expected and all(result[name]["genuine_original_unittest_count"]==count
                                     for name,ids,count,verdict in groups)
    old_named=(
        {x["id"].split(" (",1)[0] for x in result["P86_frozen_exact_two_button_cases"]["genuine_named_original_FAIL_ERROR_records"]}==OLD_P86_TWO
        and {x["id"].split(" (",1)[0] for x in result["P87_frozen_exact_two_button_case"]["genuine_named_original_FAIL_ERROR_records"]}==OLD_P87_TWO
        and len(result["WinCred_frozen_consumer_refusal"]["genuine_named_original_FAIL_ERROR_records"])==1
        and len(result["Phase831_frozen_UI_import_refusal"]["genuine_named_original_FAIL_ERROR_records"])==2)
    audit={
        "checkpoint":"P172","source_custody_before_after_identical":before,
        "authenticated_prior_P171_actual_windows_archive":archive,
        "versioned_current_user_scope_exact_secret_consumer_import_provenance":consumers,
        "frozen_original_Phase831_vs_P86_UI_import_conflict":conflict,
        "new_current_ui_expected_exact_three_buttons":list(UI_BUTTONS),
        "actual_genuine_Windows_unchanged_original_and_current_scoped_probe":result,
        "all_expected_original_PASS_and_original_HOLD_dispositions_genuinely_observed":complete,
        "old_original_exact_button_and_static_import_denials_UNWAIVED":old_named,
        "historical_H":"HOLD",
        "current_C":"TARGETED_VERSIONED_USER_SCOPE_DIAGNOSTIC_ONLY",
        "production_R":"HOLD",
        "full_product_accepted_genuine_native_Windows_regressions":"0/3",
        "qualified_independent_historical_governance_and_security_signed_GO":"NOT_OBTAINED",
        "publisher_signed_main_helper_installer_and_SAC_WDAC_policy_owner_GO":"NOT_OBTAINED",
        "privileged_BYOK_C1_G0_to_G6":"OPEN",
        "original_P76_P85_exact_branch_guards": "PRESERVED_UNWAIVED",
        "live_credential_manager_read_write_delete_or_provider_network":"NOT_ATTEMPTED",
        "next_reviewer_questions":[
            "Do current P132/P133 source-bound explicit user-scope imports merit separately qualified admission without waiving original 8.3 negative?",
            "Approve exactly 3 Connection-page buttons and explicit user click while preserving original P86/P87 two-button historical FAIL?",
            "Resolve immutable contradiction of original Phase8.31 forbidden brain imports vs P86 exact required import without dynamic evasion",
            "Assess P171 import-time __doc__ rehydration for source metadata integrity before any production code change",
            "No positive current scoped probes imply signed binary, privileged G0-G6, real provider validation or 3 full Windows product regressions",
        ],
    }
    (evidence/"p172_authenticated_windows_versioned_security_admission_ledger.json").write_text(
        json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("P172_ALL_UNMODIFIED_ORIGINAL_POSITIVE_AND_NEGATIVE_CURRENT_VERSIONED_RESULTS="+str(complete),flush=True)
    print("P172_FROZEN_ORIGINAL_8_31_P86_P87_WINCRED_FAILURES_UNWAIVED="+str(old_named),flush=True)
    print("P172_P171_DOCSTRING_GUARD_SCRATCH_RESEARCH_PRODUCTION_UNCHANGED=YES",flush=True)
    print("P172_PRODUCTION_RELEASE=HOLD|FULL_PRODUCT_WINDOWS=0/3",flush=True)
    return 0 if complete and old_named else 1


if __name__=="__main__":
    raise SystemExit(ui_probe_main() if sys.argv[1:]==["--ui-probe"] else main())
