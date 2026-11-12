"""P171: original-history authenticated, metadata-preserving guard-first scratch study.

No original product/test/security/Git source is modified. P171 edits five
guard-first functions and restores each exact original function.__doc__ ONLY
in a disposed hosted-Windows scratch clone. This is NOT approval to ship.
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
from scripts.p170_windows_disposable_guard_first_candidate import (
    SCOPE, find_method, patch_exact_guard_first, prove_old_contract_conflict,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = "0b1eda4aa1296274df70cb7a4fb09592707bf178"
BRANCH = "byok-c1-p171-cross-era-security-governance-docstring-compat-20261112"
EXPECTED = {
    "scripts/p171_windows_metadata_preserving_original_governance.py",
    ".github/workflows/p171-windows-cross-era-metadata-preservation.yml",
    "docs/byok-c1-p171-cross-era-security-acceptance-governance.md",
}
P170_ARCHIVE_ID = 13939060361
P170_ARCHIVE_SHA256 = "736BA1BE56C3BB533A2E27E15130135AE205745ABFFBC2EECD0E6E6E515BCCDE"
P170_LEDGER = "p170_actual_windows_disposable_compatibility_ledger.json"
P170_LEDGER_HASH = "BE3D9CD1589154C3F41E7D4D4D271454DEBA16C43D0623C798578E9E692E2E8D"
P170_PATCH_HASH = "9358D4B40A61D34A6853A44932B1CFB7E578F8D6B28E6E0A6D9C06D5F70ACAF0"
ORIGINAL = (
    ("full_phase832", ["tests.test_phase_832_lifecycle_assurance"], 14),
    ("full_p86", ["tests.test_p86_live_pending_status_integration"], 7),
    ("full_p87", ["tests.test_p87_readonly_custody_observation"], 18),
    ("frozen_831_static_denial",
     ["tests.test_phase_831_effect_isolation.Phase831EffectIsolationTests.test_static_production_import_closure_forbids_test_and_effect_routes"], 1),
    ("frozen_wincred_consumer_denial",
     ["tests.test_windows_credential_backend.ScopeGuards.test_only_approved_secret_consumers_and_legacy_store_unused"], 1),
    ("frozen_p76_wrong_branch_negative",
     ["tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_wrong_branch_refused_before_other_work"], 1),
)
FOOTER = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
ISSUES = re.compile(r"^(FAIL|ERROR): (.+)$", re.M)
SECRET_ENV = {"OPENAI_API_KEY","AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY",
              "GITHUB_TOKEN","GH_TOKEN","P171_ARCHIVE_TOKEN",
              "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN"}
P86_FAILURES = {
    "test_live_connection_page_default_is_explicitly_unobserved",
    "test_no_credential_action_and_no_implicit_refresh",
}
P87_FAILURES = {"test_production_default_remains_not_observed_without_any_session"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def git(where: Path, *args: str) -> bytes:
    result = subprocess.run(["git","-C",str(where),*args],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        timeout=35,check=True)
    return result.stdout


def custody() -> dict:
    _guard_runner()
    if not (sys.platform == "win32"
            and os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("RUNNER_OS") == "Windows"
            and os.environ.get("GITHUB_EVENT_NAME") == "push"
            and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.environ.get("GITHUB_REF_NAME") == BRANCH
            and os.environ.get("RUNNER_TEMP")):
        raise RuntimeError("P171 authentic Windows GitHub push event required")
    head = git(ROOT,"rev-parse","HEAD").decode().strip()
    if (head != os.environ.get("GITHUB_SHA")
            or git(ROOT,"branch","--show-current").decode().strip() != BRANCH
            or git(ROOT,"merge-base",BASE,"HEAD").decode().strip() != BASE
            or git(ROOT,"status","--porcelain=v1").strip()):
        raise RuntimeError("P171 source/lineage/checkout not exact and clean")
    diff = set(git(ROOT,"diff","--name-only",BASE,"HEAD").decode().splitlines())
    if diff != EXPECTED or any(git(ROOT,"ls-tree","--name-only",BASE,"--",p).strip()
                               for p in diff):
        raise RuntimeError("P171 must have exactly three NEW audit-only paths")
    old = [p for p in git(ROOT,"ls-tree","-r","--name-only",BASE,"--","tests")
           .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    now = [p for p in git(ROOT,"ls-files","tests/test_*.py")
           .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(old) != 171 or sorted(old) != sorted(now):
        raise RuntimeError("P171 all 171 existing original/current modules must remain")
    paths = set(PROTECTED) | set(SCOPE) | {
        "tests/test_phase_831_effect_isolation.py",
        "tests/test_phase_832_lifecycle_assurance.py",
        "tests/test_p86_live_pending_status_integration.py",
        "tests/test_p87_readonly_custody_observation.py",
        "tests/test_windows_credential_backend.py",
        "tests/test_phase8_byok_c1_p76_scope.py",
    }
    protected = {}
    for p in sorted(paths):
        old_bytes = git(ROOT,"show",BASE+":"+p)
        current_bytes = git(ROOT,"show","HEAD:"+p)
        disk = (ROOT/p).read_bytes()
        if old_bytes != current_bytes or disk != current_bytes:
            raise RuntimeError("P171 original protected source/test changed "+p)
        protected[p] = sha(disk)
    return {"head":head,"exact_parent":BASE,"three_new_audit_files":sorted(diff),
            "all_171_original_and_prior_versioned_test_modules_unchanged":True,
            "protected_source_and_historical_tests_sha256":protected}


def historical_p170_archive(token: str) -> dict:
    if len(token)<8:
        raise RuntimeError("P171 only ephemeral Actions read token authorized")
    raw=_download_artifact(P170_ARCHIVE_ID,P170_ARCHIVE_SHA256,token)
    if sha(raw)!=P170_ARCHIVE_SHA256:
        raise RuntimeError("P171 archived P170 evidence mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise RuntimeError("P171 archived evidence ZIP CRC invalid")
        expected={P170_LEDGER, "p170_disposable_guard_first_exact_candidate.patch"} | {
            "p170_original_native_"+name+".log" for name,_,_ in ORIGINAL
            for name in ({
                "full_phase832":"candidate_full_original_phase832",
                "full_p86":"candidate_full_original_P86",
                "full_p87":"candidate_full_original_P87",
                "frozen_831_static_denial":"old_original_phase831_static_import_refusal",
                "frozen_wincred_consumer_denial":"old_original_WinCred_static_consumer_refusal",
                "frozen_p76_wrong_branch_negative":"old_original_P76_wrong_branch_negative",
            }[name],)
        }
        if set(z.namelist())!=expected or len(z.namelist())!=8:
            raise RuntimeError("P170 historical source-bound evidence inventory changed")
        if sha(z.read(P170_LEDGER))!=P170_LEDGER_HASH or sha(z.read(
                "p170_disposable_guard_first_exact_candidate.patch"))!=P170_PATCH_HASH:
            raise RuntimeError("P171 historical P170 original ledger/patch SHA drift")
        obj=json.loads(z.read(P170_LEDGER))
        if (obj.get("checkpoint")!="P170" or
                obj.get("production_R")!="HOLD" or
                obj.get("accepted_complete_full_product_native_Windows_regressions")!="0/3"
                or obj.get("original_P76_P85_and_remaining_historical_failures_unwaived") is not True):
            raise RuntimeError("P171 prior historical H/C/R status falsified")
        rows=obj["genuine_hosted_Windows_unmodified_original_test_outcomes_on_candidate"]
        reference={
            "candidate_full_original_phase832":("PASS",14,0,0),
            "candidate_full_original_P86":("HOLD",7,1,2),
            "candidate_full_original_P87":("HOLD",18,1,1),
            "old_original_phase831_static_import_refusal":("HOLD",1,1,2),
            "old_original_WinCred_static_consumer_refusal":("HOLD",1,1,1),
            "old_original_P76_wrong_branch_negative":("PASS",1,0,0),
        }
        if set(rows)!=set(reference):
            raise RuntimeError("P171 original P170 exact six original-run inventory changed")
        for label,(status,count,native,nissue) in reference.items():
            row=rows[label]
            raw_log=z.read(row["real_original_stdout_stderr_log"])
            if (sha(raw_log)!=row["raw_log_sha256"]
                    or row["real_native_status"]!=status
                    or row["original_unittest_footer_count"]!=count
                    or row["native_exit"]!=native
                    or len(row["genuine_original_failure_error_ids"])!=nissue):
                raise RuntimeError("P171 original P170 Windows native receipt cannot be changed")
    return {"prior_checkpoint":"P170","artifact_id":P170_ARCHIVE_ID,
            "authenticated_prior_archived_zip_sha256":sha(raw),
            "original_six_real_native_Windows_test_receipts":reference,
            "unwaived_frozen_originals":True}


def original_docs(root: Path) -> dict:
    result={}
    for name, methods in SCOPE.items():
        text=(root/name).read_text(encoding="utf8")
        for cls,method in sorted(methods):
            node=find_method(text,cls,method)
            value=node.body[0]
            if not(isinstance(value,ast.Expr) and isinstance(value.value,ast.Constant)
                   and type(value.value.value) is str and
                   isinstance(node.body[1],ast.Expr)
                   and ast.unparse(node.body[1])=="self._require_creator_thread()"):
                raise RuntimeError("P171 original docstring-first guarded function changed")
            result[(name,cls,method)]=value.value.value
    if len(result)!=5:
        raise RuntimeError("P171 exactly five original docstrings expected")
    return result


def candidate_with_metadata_restoration(root: Path, documents: dict) -> dict:
    transformations=[]
    for name, methods in sorted(SCOPE.items()):
        file=root/name
        original=(file.read_text(encoding="utf8"))
        reordered=patch_exact_guard_first(file,methods)
        order_ast=ast.parse(file.read_text(encoding="utf8"))
        additional=[]
        for cls,method in sorted(methods):
            doc=documents[(name,cls,method)]
            additional.append(cls+"."+method+".__doc__ = "+repr(doc)+"\n")
        with file.open("a",encoding="utf8",newline="\n") as stream:
            stream.write("\n# P171 SCRATCH-ONLY original-docstring metadata restoration; NO production commit.\n")
            stream.writelines(additional)
        full_ast=ast.parse(file.read_text(encoding="utf8"))
        if ast.dump(ast.Module(body=full_ast.body[:len(order_ast.body)],type_ignores=[]),
                    include_attributes=False)!=ast.dump(order_ast,include_attributes=False):
            raise RuntimeError("P171 restoration altered callable production code")
        extras=full_ast.body[len(order_ast.body):]
        if len(extras)!=len(methods):
            raise RuntimeError("P171 metadata restoration has unexpected module effects")
        for target_node,(cls,method) in zip(extras,sorted(methods)):
            if not (isinstance(target_node,ast.Assign)
                    and len(target_node.targets)==1
                    and isinstance(target_node.targets[0],ast.Attribute)
                    and target_node.targets[0].attr=="__doc__"
                    and isinstance(target_node.targets[0].value,ast.Attribute)
                    and target_node.targets[0].value.attr==method
                    and isinstance(target_node.targets[0].value.value,ast.Name)
                    and target_node.targets[0].value.value.id==cls
                    and isinstance(target_node.value,ast.Constant)
                    and type(target_node.value.value) is str
                    and target_node.value.value==documents[(name,cls,method)]):
                raise RuntimeError("P171 extra side effect or wrong doc metadata assignment")
        for cls,method in methods:
            node=find_method(file.read_text(encoding="utf8"),cls,method)
            if ast.unparse(node.body[0])!="self._require_creator_thread()":
                raise RuntimeError("P171 real first AST statement guard lost")
        transformations.extend(reordered)
    return {"exact_five_previous_guard_reorders_kept":len(transformations)==5,
            "exact_five_original_docs_rehydrated_only_in_disposable_source":True,
            "all_five_metadata_assignments_are_exact_literals":True,
            "original_doc_sha256_by_method":{
                cls+"."+method:sha(doc.encode("utf8"))
                for (_,cls,method),doc in sorted(documents.items())
            }}


def sanitized_env(temp: Path)->dict:
    e=os.environ.copy()
    for k in list(e):
        if k in SECRET_ENV or k.endswith("_API_KEY") or k.endswith("_SECRET"):
            e.pop(k,None)
    e.update({"TEMP":str(temp),"TMP":str(temp),"TMPDIR":str(temp),
              "PYTHONDONTWRITEBYTECODE":"1"})
    return e


def run_original(label: str, ids: list[str], count: int,
                 scratch: Path, temp: Path, evidence: Path)->dict:
    p=evidence/("p171_original_windows_"+label+".log")
    start=time.monotonic()
    timed_out=False
    with p.open("wb") as stream:
        proc=subprocess.Popen([sys.executable,"-B","-m","unittest","-v",*ids],
            cwd=scratch,env=sanitized_env(temp),stdin=subprocess.DEVNULL,
            stdout=stream,stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try:
            code=proc.wait(timeout=100)
        except subprocess.TimeoutExpired:
            code,timed_out=124,True
            subprocess.run(["taskkill","/PID",str(proc.pid),"/T","/F"],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,timeout=15,check=False)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    raw=p.read_bytes()
    output=raw.decode("utf8","replace").replace("\r\n","\n")
    footers=FOOTER.findall(output)
    ran=int(footers[-1]) if footers else None
    issues=[{"kind":kind,"id":case} for kind,case in ISSUES.findall(output)]
    passed=(code==0 and ran==count and bool(re.search(r"^OK\s*$",output,re.M)))
    failed=(code==1 and ran==count and bool(re.search(r"^FAILED \(",output,re.M)))
    status="PASS" if passed else "HOLD" if failed else "TIMEOUT" if timed_out else "INCOMPLETE"
    print("P171_NATIVE="+label+"|EXIT="+str(code)+"|RAN="+str(ran)+
          "|VERDICT="+status+"|ISSUES="+str(len(issues)),flush=True)
    print("P171_NATIVE_LOG_SHA256="+label+"|"+sha(raw),flush=True)
    return {"label":label,"original_test_ids":ids,"expected_tests":count,
            "original_genuine_native_exit":code,"original_unittest_ran":ran,
            "actual_original_verdict":status,"original_failure_error_ids":issues,
            "raw_stdout_stderr_log":p.name,"raw_log_sha256":sha(raw),
            "raw_log_bytes":len(raw),"seconds":round(time.monotonic()-start,3)}


def metadata_worker_probe(scratch:Path,temp:Path,evidence:Path,expected:dict)->dict:
    expected_map={cls+"."+method:sha(doc.encode("utf8"))
                  for (_,cls,method),doc in expected.items()}
    code = """import hashlib,json,threading
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha.workspace_window import ConnectionWindow
classes={"OfflineWorkspaceApplication":OfflineWorkspaceApplication,"ConnectionWindow":ConnectionWindow}
expected=json.loads(%r)
checks={}
for key,hash_expected in sorted(expected.items()):
    cls_name,meth=key.split(".",1)
    method=getattr(classes[cls_name],meth)
    doc=method.__doc__
    if type(doc) is not str or hashlib.sha256(doc.encode("utf8")).hexdigest().upper()!=hash_expected:
        raise RuntimeError("P171 original function docstring metadata mismatch "+key)
    checks[key]="BYTE_EXACT_DOC_METADATA_SHA256_PASS"
owner=threading.get_ident()
for key in expected:
    cls_name,meth=key.split(".",1)
    method=getattr(classes[cls_name],meth)
    calls={"guard":0,"other":0}
    class Sentinel:
        def __getattribute__(self,name):
            if name=="_require_creator_thread":
                def gate():
                    calls["guard"]+=1
                    if threading.get_ident()!=owner: raise RuntimeError("WRONG_THREAD")
                    return None
                return gate
            calls["other"]+=1
            raise RuntimeError("EARLY_FIELD_ACCESS")
    args=(None,)*({"_open_local_byok":3,"begin_synthetic_pending_observation":0,
                   "cancel_synthetic_pending_observation":1,
                   "publish_synthetic_pending_observation":2,
                   "show_pending_custody_advisory":2}[meth])
    seen=[]
    def worker():
        try: method(Sentinel(),*args); seen.append("UNSAFE")
        except RuntimeError as e:seen.append(str(e))
        except Exception as e:seen.append(type(e).__name__)
    t=threading.Thread(target=worker);t.start();t.join(5)
    if t.is_alive() or seen!=["WRONG_THREAD"] or calls!={"guard":1,"other":0}:
        raise RuntimeError("P171 guard must deny before first field read "+key)
    checks[key]+="|WORKER_WRONG_THREAD_PRE_EFFECT_PASS"
if len(checks)!=5:raise RuntimeError("P171 expected five exact checked methods")
print(json.dumps({"checkpoint":"P171","result":"PASS","five_original_exact_docs":checks},sort_keys=True))
""" % json.dumps(expected_map,sort_keys=True)
    p=evidence/"p171_real_windows_doc_metadata_and_5_worker_negatives.log"
    start=time.monotonic()
    with p.open("wb") as f:
        result=subprocess.run([sys.executable,"-B","-c",code],
            cwd=scratch,env=sanitized_env(temp),stdin=subprocess.DEVNULL,
            stdout=f,stderr=subprocess.STDOUT,timeout=35,check=False)
    raw=p.read_bytes()
    if result.returncode:
        raise RuntimeError("P171 metadata or real worker thread refusal denied; raw evidence retained")
    lines=raw.decode("utf8","replace").splitlines()
    last=json.loads(lines[-1])
    if (last.get("checkpoint")!="P171" or last.get("result")!="PASS" or
            len(last.get("five_original_exact_docs",{}))!=5 or
            any("WORKER_WRONG_THREAD_PRE_EFFECT_PASS" not in x
                for x in last["five_original_exact_docs"].values())):
        raise RuntimeError("P171 original actual Python metadata/worker proof incomplete")
    print("P171_ORIGINAL_FUNCTION_DOCS_BYTES_AND_WORKER_NEGATIVES=5/5_PASS",flush=True)
    print("P171_METADATA_WORKER_LOG_SHA256="+sha(raw),flush=True)
    return {"actual_native_exit":result.returncode,"five_original_exact_docs":last["five_original_exact_docs"],
            "native_original_worker_and_doc_metadata_log":p.name,
            "raw_log_sha256":sha(raw),"seconds":round(time.monotonic()-start,3)}


def historical_governance_matrix(scratch:Path)->dict:
    blocked=prove_old_contract_conflict(scratch)
    current=(scratch/"nayeon/desktop_alpha/workspace_window.py").read_text("utf8")
    source=ast.parse(current)
    conn=next(x for x in source.body if isinstance(x,ast.ClassDef)
              and x.name=="ConnectionWindow")
    buttons=[n for n in ast.walk(next(x for x in conn.body if
             isinstance(x,ast.FunctionDef) and x.name=="__init__"))
             if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
             and n.func.attr=="Button"]
    old_p86=(scratch/"tests/test_p86_live_pending_status_integration.py").read_text("utf8")
    old_p87=(scratch/"tests/test_p87_readonly_custody_observation.py").read_text("utf8")
    if (len(buttons)<3 or "local_byok_button" not in current or
        "self.assertEqual(len(" not in old_p86 or "self.assertEqual(len(" not in old_p87):
        raise RuntimeError("P171 old UI count/source contract provenance drift")
    return {
        "source_era_security_invariant_never_waive": {
            "P76_P85_exact_historical_branch_and_seal":"HOLD_UNWAIVED",
            "WinCred_unapproved_secret_consumer_and_native_CredWrite":"HOLD_UNWAIVED",
            "P139_real_win32_no_reparse_owned_temp":"UNCHANGED",
            "P140_unsigned_unpinned_code_integrity_denial":"UNCHANGED",
        },
        "old_source_era_conflicts_require_independent_governance": {
            "Phase831_forbid_nayeon_brain_vs_original_P86_requires_that_import":blocked,
            "P86_P87_exactly_2_buttons_vs_later_3_button_local_BYOK_UI":
                "ORIGINAL_STATIC_UI_ASSERTIONS_STILL_HOLD_NO_BUTTON_REMOVED",
            "Phase832_creator_guard_first_AST_node_vs_original_method_docstring":
                "P171_SCRATCH_ONLY_GUARD_FIRST_WITH_EXPLICIT_POST_CLASS_DOC_RESTORATION",
            "WinCred_legacy_exact_consumer_allowlist_vs_later_user_scope_paths":
                "REQUIRES_QUALIFIED_REVIEW_NO_AUTOMATIC_ALLOWLIST_EXPANSION",
        },
        "source_era_acceptance_not_equivalent_to_current_prod_release":True,
    }


def main()->int:
    before=custody()
    prior=historical_p170_archive(os.environ.get("P171_ARCHIVE_TOKEN",""))
    docs=original_docs(ROOT)
    evidence=Path(os.environ["RUNNER_TEMP"])/"nayeon-p171-cross-era-metadata-evidence"
    evidence.mkdir(parents=True,exist_ok=True)
    scratch=Path(os.environ["RUNNER_TEMP"])/("p171_scratch_"+uuid.uuid4().hex)
    temp=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made=False
    try:
        if scratch.exists() or temp.exists() or temp.is_symlink():
            raise RuntimeError("P171 scratch verified local Windows root collision")
        os.mkdir(temp)
        made=True
        _verify_original_handle_policy(str(temp))
        subprocess.run(["git","-c","core.autocrlf=false","clone","--quiet",
                        "--no-hardlinks","--single-branch","--branch",BRANCH,
                        str(ROOT),str(scratch)],
                       check=True,timeout=90,stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        git(scratch,"config","--local","core.autocrlf","false")
        if git(scratch,"rev-parse","HEAD").decode().strip()!=before["head"]:
            raise RuntimeError("P171 scratch clone source identity mismatch")
        for p in SCOPE:
            if sha((scratch/p).read_bytes())!=before[
                    "protected_source_and_historical_tests_sha256"][p]:
                raise RuntimeError("P171 second clone original bytes mismatch")
        candidate=candidate_with_metadata_restoration(scratch,docs)
        changed=set(git(scratch,"diff","--name-only").decode().splitlines())
        if changed!=set(SCOPE):
            raise RuntimeError("P171 only two disposable UI product paths can change")
        patch=git(scratch,"diff","--",*sorted(SCOPE))
        (evidence/"p171_scratch_only_metadata_preserving_guard_first.patch").write_bytes(patch)
        matrix=historical_governance_matrix(scratch)
        metadata=metadata_worker_probe(scratch,temp,evidence,docs)
        original={label:run_original(label,ids,count,scratch,temp,evidence)
                  for label,ids,count in ORIGINAL}
        if git(scratch,"rev-parse","HEAD").decode().strip()!=before["head"] or set(
                git(scratch,"diff","--name-only").decode().splitlines())!=set(SCOPE):
            raise RuntimeError("P171 scratch extra change or source identity drift")
    finally:
        if scratch.exists():
            shutil.rmtree(scratch)
        if made:
            st=temp.lstat()
            if temp.is_symlink() or getattr(st,"st_file_attributes",0)&0x400:
                raise RuntimeError("P171 unsafe Windows junction/reparse C root deletion refused")
            shutil.rmtree(temp)
    if custody()!=before:
        raise RuntimeError("P171 immutable GitHub source changed during scratch execution")
    good=(original["full_phase832"]["actual_original_verdict"]=="PASS" and
          original["full_phase832"]["original_unittest_ran"]==14 and
          original["frozen_p76_wrong_branch_negative"]["actual_original_verdict"]=="PASS")
    def fail_names(name):
        row=original[name]
        return {i["id"].split(" (",1)[0] for i in row["original_failure_error_ids"]}
    old_cases=(
        original["full_p86"]["actual_original_verdict"]=="HOLD" and
        fail_names("full_p86")==P86_FAILURES and
        original["full_p87"]["actual_original_verdict"]=="HOLD" and
        fail_names("full_p87")==P87_FAILURES and
        original["frozen_831_static_denial"]["actual_original_verdict"]=="HOLD" and
        original["frozen_wincred_consumer_denial"]["actual_original_verdict"]=="HOLD" and
        len(original["frozen_831_static_denial"]["original_failure_error_ids"])==2 and
        len(original["frozen_wincred_consumer_denial"]["original_failure_error_ids"])==1)
    review="DOC_METADATA_PRESERVED_PHASE832_14_PASS_ALL_HISTORICAL_HOLDS_UNWAIVED" \
           if good and old_cases else "UNEXPECTED_OR_INCOMPLETE_CANDIDATE_REVIEW_HOLD"
    ledger={
        "checkpoint":"P171","source_custody_before_after":before,
        "authenticated_original_P170_immutable_full_native_history":prior,
        "five_disposable_guard_first_plus_exact_docstring_restoration":candidate,
        "real_python_function_docs_and_wrong_thread_negative_probes":metadata,
        "original_native_Windows_tests_on_disposable_candidate_only":original,
        "immutable_historical_cross_era_governance_matrix":matrix,
        "candidate_scratch_patch":"p171_scratch_only_metadata_preserving_guard_first.patch",
        "actual_original_Phase832_14_PASS_IN_DISPOSABLE_ONLY":good,
        "all_other_genuine_original_source_era_HOLDS_unwaived":old_cases,
        "no_historical_test_source_modified_or_waived":True,
        "source_Git_PR_contains_only_3_new_audit_files":True,
        "original_historical_H":"HOLD","current_C":"DISPOSABLE_CANDIDATE_ONLY",
        "production_R":"HOLD","accepted_complete_whole_product_windows_regressions":"0/3",
        "independent_security_and_historical_test_governance_signed_GO":"NOT_OBTAINED",
        "p140_approved_signed_main_helper_installer_and_SAC_WDAC_owner_GO":"NOT_OBTAINED",
        "privileged_BYOK_C1_G0_to_G6":"OPEN",
        "real_keys_live_WinCred_provider_or_protected_host_action":"NOT_ATTEMPTED",
        "qualification": [
            "P171 source overlay only in discarded runner scratch clone. No product source committed",
            "Reassigning function __doc__ at module import is a proposed source technique; requires qualified independent review for import-time effects and code provenance",
            "Original Phase8.31/P86 import conflict and P86/P87 button count remain unresolved by this experiment",
            "Original WinCred allowlist may not be expanded without security/governance approval",
            "Passing 14 original Phase832 cases in scratch does not make source branch or whole-product suites PASS",
        ],
        "candidate_disposition":review,
    }
    (evidence/"p171_authenticated_windows_cross_era_metadata_governance_ledger.json").write_text(
        json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("P171_FULL_PHASE832_14_ORIGINAL_IN_SCRATCH_PASS="+str(good),flush=True)
    print("P171_ALL_FIVE_BYTE_EXACT_ORIGINAL_DOCS_AND_REAL_WORKER_WRONG_THREAD=PASS",flush=True)
    print("P171_OLD_P86_P87_PHASE831_WINCRED_HOLDS_UNWAIVED="+str(old_cases),flush=True)
    print("P171_DISPOSABLE_CANDIDATE_GOVERNANCE="+review,flush=True)
    print("P171_COMPLETE_WINDOWS_FULL_PRODUCT_ACCEPTANCE=0/3",flush=True)
    print("P171_BYOK_C1_PRODUCTION_RELEASE=HOLD",flush=True)
    return 0 if good and old_cases else 1

if __name__=="__main__":
    raise SystemExit(main())
