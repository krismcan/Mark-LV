"""P170 disposable Windows source-overlay compatibility experiment, never a release.

Moves five documented-original function guard statements ahead of docstrings
ONLY inside a disposable independent local Git clone on hosted Windows.
Original tracked product files and every historical original test remain frozen.
Other conflicting historical UI/WinCred admission tests MUST remain visible.
"""
from __future__ import annotations

import ast
import copy
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

ROOT = Path(__file__).resolve().parents[1]
BASE = "00f397f5d397a7b6fba14ab124b71ba1d3b7a99b"
BRANCH = "byok-c1-p170-disposable-windows-thread-guard-compatibility-20261112"
ADDITIVE = {
    "scripts/p170_windows_disposable_guard_first_candidate.py",
    ".github/workflows/p170-windows-disposable-compatibility-candidate.yml",
    "docs/byok-c1-p170-disposable-compatibility-security-review.md",
}
P169_ARTIFACT = 13929023754
P169_ARCHIVE_SHA = "26392F4A186DAD82E9C8BD825686D6D3514D8EC7056E53C34B0923BA6C7CE9BC"
P169_LEDGER = "p169_authentic_original_native_causal_source_bound_ledger.json"
SCOPE = {
    "nayeon/desktop_alpha/application.py": {
        ("OfflineWorkspaceApplication", "_open_local_byok"),
    },
    "nayeon/desktop_alpha/workspace_window.py": {
        ("ConnectionWindow", "begin_synthetic_pending_observation"),
        ("ConnectionWindow", "cancel_synthetic_pending_observation"),
        ("ConnectionWindow", "publish_synthetic_pending_observation"),
        ("ConnectionWindow", "show_pending_custody_advisory"),
    },
}
OLD_UI_REQUIRED_IMPORT = "nayeon.brain.pending_custody_status_view"
BANNED_UI_ROOT = "nayeon.brain"
CRED_UNAPPROVED = "nayeon.secrets.contracts"
TEST_RUNS = (
    ("candidate_full_original_phase832", ["tests.test_phase_832_lifecycle_assurance"]),
    ("candidate_full_original_P86", ["tests.test_p86_live_pending_status_integration"]),
    ("candidate_full_original_P87", ["tests.test_p87_readonly_custody_observation"]),
    ("old_original_phase831_static_import_refusal", [
        "tests.test_phase_831_effect_isolation.Phase831EffectIsolationTests.test_static_production_import_closure_forbids_test_and_effect_routes"]),
    ("old_original_WinCred_static_consumer_refusal", [
        "tests.test_windows_credential_backend.ScopeGuards.test_only_approved_secret_consumers_and_legacy_store_unused"]),
    ("old_original_P76_wrong_branch_negative", [
        "tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_wrong_branch_refused_before_other_work"]),
)
FOOTER = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
ISSUES = re.compile(r"^(FAIL|ERROR): (.+)$", re.M)
SECRET_ENV = {"GITHUB_TOKEN", "GH_TOKEN", "P170_HISTORICAL_ARCHIVE_TOKEN",
              "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY",
              "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(where: Path, *args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(where), *args], stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=30)
    return p.stdout

def custody() -> dict:
    _guard_runner()
    if not (sys.platform == "win32"
            and os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("RUNNER_OS") == "Windows"
            and os.environ.get("GITHUB_EVENT_NAME") == "push"
            and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.environ.get("GITHUB_REF_NAME") == BRANCH
            and os.environ.get("RUNNER_TEMP")):
        raise RuntimeError("P170 authentic Windows source event required")
    head = git(ROOT, "rev-parse", "HEAD").decode().strip()
    if (head != os.environ.get("GITHUB_SHA") or
            git(ROOT, "branch", "--show-current").decode().strip() != BRANCH or
            git(ROOT, "merge-base", "HEAD", BASE).decode().strip() != BASE or
            git(ROOT, "status", "--porcelain=v1").strip()):
        raise RuntimeError("P170 exact authenticated clean P169 descendant refused")
    changed = set(git(ROOT, "diff", "--name-only", BASE, "HEAD").decode().splitlines())
    if changed != ADDITIVE or any(git(ROOT, "ls-tree", "--name-only", BASE, "--", p).strip() for p in changed):
        raise RuntimeError("P170 original product/test/security path modified in Git")
    original = [p for p in git(ROOT, "ls-tree", "-r", "--name-only", BASE, "--", "tests")
                .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    current = [p for p in git(ROOT, "ls-files", "tests/test_*.py").decode().splitlines()
               if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    if len(original) != 171 or sorted(original) != sorted(current):
        raise RuntimeError("P170 original 171 module inventory changed")
    preserved = {}
    all_paths = set(PROTECTED) | set(SCOPE) | {
        "tests/test_phase_831_effect_isolation.py",
        "tests/test_phase_832_lifecycle_assurance.py",
        "tests/test_p86_live_pending_status_integration.py",
        "tests/test_p87_readonly_custody_observation.py",
        "tests/test_windows_credential_backend.py",
        "tests/test_phase8_byok_c1_p76_scope.py",
    }
    for name in sorted(all_paths):
        old = git(ROOT, "show", BASE+":"+name)
        now = git(ROOT, "show", "HEAD:"+name)
        disk = (ROOT/name).read_bytes()
        if old != now or now != disk:
            raise RuntimeError("P170 historical/source code custody failed "+name)
        preserved[name] = digest(now)
    return {"source_head": head, "exact_parent": BASE, "new_additive_paths": sorted(changed),
            "protected_original_source_sha256": preserved,
            "original_module_count": len(original), "production_source_changes": 0}

def authenticate_p169(token: str) -> dict:
    if len(token) < 8:
        raise RuntimeError("P170 read-only Actions evidence token missing")
    raw = _download_artifact(P169_ARTIFACT, P169_ARCHIVE_SHA, token)
    if digest(raw) != P169_ARCHIVE_SHA:
        raise RuntimeError("P170 prior evidence hash mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise RuntimeError("P170 P169 archive CRC failure")
        names = z.namelist()
        if len(names) != 5 or len(names) != len(set(names)) or P169_LEDGER not in names:
            raise RuntimeError("P170 P169 authentic evidence member inventory mismatch")
        ledger = json.loads(z.read(P169_LEDGER))
        if (ledger.get("checkpoint") != "P169" or
                ledger.get("production_R") != "HOLD" or
                ledger.get("accepted_native_complete_whole_product_regressions") != "0/3" or
                ledger.get("historical_H_full_14_case_8_32_original_module") != "HOLD" or
                ledger.get("original_frozen_P76_P85_guards_and_all_failures_waived") is not False):
            raise RuntimeError("P169 immutable original H/C/R results changed")
        prior = ledger["P169_genuine_unmodified_original_targeted_Windows_tests"]
        for item in prior.values():
            log = z.read(item["original_raw_log_file"])
            if digest(log) != item["original_raw_log_sha256"]:
                raise RuntimeError("P170 P169 real native original log changed")
        guards = ledger["P169_5_original_unbound_creatorthread_guard_real_worker_negative_probes"]
        if len(guards) != 5 or any(g["real_worker_thread_original_unbound_method"] != "WRONG_THREAD"
                                   for g in guards):
            raise RuntimeError("P170 prior genuine worker negatives missing")
    return {"source": "P169 authentic GitHub Actions Windows native logs",
            "archive_id": P169_ARTIFACT, "archived_zip_sha256": digest(raw),
            "five_prior_original_guard_worker_negatives": "WRONG_THREAD",
            "historical_H_unwaived": True}

def find_method(src: str, class_name: str, method_name: str):
    tree = ast.parse(src)
    classes = [c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == class_name]
    if len(classes) != 1:
        raise RuntimeError("P170 original production class missing or duplicate")
    matches = [m for m in classes[0].body if isinstance(m, ast.FunctionDef)
               and m.name == method_name]
    if len(matches) != 1:
        raise RuntimeError("P170 original guarded production method identity changed")
    return matches[0]

def patch_exact_guard_first(path: Path, methods: set[tuple[str,str]]) -> list[dict]:
    original = path.read_text(encoding="utf8")
    lines = original.splitlines(keepends=True)
    patch_places = []
    audit = []
    for class_name, method_name in sorted(methods):
        node = find_method(original, class_name, method_name)
        if len(node.body) < 3:
            raise RuntimeError("P170 function unexpectedly truncated")
        a,b = node.body[0], node.body[1]
        if (not isinstance(a, ast.Expr) or not isinstance(a.value, ast.Constant)
            or type(a.value.value) is not str or not isinstance(b, ast.Expr)
            or ast.unparse(b) != "self._require_creator_thread()"
            or a.end_lineno + 1 != b.lineno or b.end_lineno != b.lineno):
            raise RuntimeError("P170 exact original docstring-first thread-guard shape changed")
        original_node = copy.deepcopy(node)
        original_node.body[0],original_node.body[1]=original_node.body[1],original_node.body[0]
        patch_places.append((a.lineno,b.end_lineno,
                             [lines[b.lineno-1]] + lines[a.lineno-1:a.end_lineno]))
        audit.append({"source": path.as_posix(), "class": class_name, "method": method_name,
                      "source_AST_earliest_executable": "self._require_creator_thread()",
                      "candidate_AST_first_node": "self._require_creator_thread()",
                      "source_original_function_docstring_nonempty": bool(ast.get_docstring(node)),
                      "candidate_function_docstring_metadata_lost": True,
                      "semantic_C1_authority_approved": False,
                      "expected_AST_without_line_positions": ast.dump(original_node, include_attributes=False)})
    for start,end,replacement in sorted(patch_places,reverse=True):
        lines[start-1:end]=replacement
    proposed="".join(lines)
    for rec in audit:
        node=find_method(proposed,rec["class"],rec["method"])
        if (ast.unparse(node.body[0]) != "self._require_creator_thread()" or
                ast.get_docstring(node) is not None or
                ast.dump(node,include_attributes=False) != rec.pop("expected_AST_without_line_positions")):
            raise RuntimeError("P170 source overlay changed any behavior outside exact statement order")
    path.write_text(proposed,encoding="utf8",newline="")
    return audit

def prove_old_contract_conflict(overlay: Path) -> dict:
    workspace = (overlay/"nayeon/desktop_alpha/workspace_window.py").read_text(encoding="utf8")
    module = ast.parse(workspace)
    classes = [c for c in module.body if isinstance(c,ast.ClassDef) and c.name=="ConnectionWindow"]
    if len(classes)!=1:
        raise RuntimeError("P170 ConnectionWindow source mismatch")
    advisory=[m for m in classes[0].body if isinstance(m,ast.FunctionDef)
              and m.name=="show_pending_custody_advisory"]
    if len(advisory)!=1:
        raise RuntimeError("P170 advisory method changed")
    imports=[n.module for n in ast.walk(advisory[0]) if isinstance(n,ast.ImportFrom)]
    if imports != [OLD_UI_REQUIRED_IMPORT]:
        raise RuntimeError("P170 exact original P86 required module import moved or removed")
    original_old_forbidden=[
        n.module for n in ast.walk(module) if isinstance(n,ast.ImportFrom) and n.module
        and (n.module == BANNED_UI_ROOT or n.module.startswith(BANNED_UI_ROOT+"."))
    ]
    if OLD_UI_REQUIRED_IMPORT not in original_old_forbidden:
        raise RuntimeError("P170 original Phase8.31 forbidden import unexpectedly absent")
    return {"old_P86_exact_module_import_requirement": imports,
            "old_Phase831_denied_UI_imports_still_present": original_old_forbidden,
            "simultaneously_satisfiable_without_contract_review": False,
            "original_old_Phase831_import_denial_must_remain_HOLD": True,
            "source_imports_transplanted_or_test_waived": False}

def unittest_count(root: Path, module: str) -> int:
    path=root/(module.replace(".","/")+".py")
    tree=ast.parse(path.read_text(encoding="utf8"))
    classes=[c for c in tree.body if isinstance(c,ast.ClassDef)]
    n=sum(1 for c in classes for m in c.body
          if isinstance(m,ast.FunctionDef) and m.name.startswith("test_"))
    if n<1:
        raise RuntimeError("P170 original unittest module inventory missing")
    return n

def run_windows(label: str, ids: list[str], overlay: Path, safe_temp: Path,
                evidence: Path) -> dict:
    env=os.environ.copy()
    for k in list(env):
        if k in SECRET_ENV or k.endswith("_API_KEY") or k.endswith("_SECRET"):
            env.pop(k,None)
    env.update({"TEMP":str(safe_temp),"TMP":str(safe_temp),"TMPDIR":str(safe_temp),
                "PYTHONDONTWRITEBYTECODE":"1"})
    log="p170_original_native_"+label+".log"
    start=time.monotonic()
    timeout=False
    with (evidence/log).open("wb") as f:
        process=subprocess.Popen([sys.executable,"-B","-m","unittest","-v",*ids],
            cwd=overlay,env=env,stdin=subprocess.DEVNULL,stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        try:
            native=process.wait(timeout=100)
        except subprocess.TimeoutExpired:
            timeout,native=True,124
            subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],
                           stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,check=False,timeout=15)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    raw=(evidence/log).read_bytes()
    text=raw.decode("utf8","replace").replace("\r\n","\n")
    counts=FOOTER.findall(text)
    actual=int(counts[-1]) if counts else None
    expected=(unittest_count(overlay,ids[0]) if len(ids)==1 and
              ids[0] in [g[1][0] for g in TEST_RUNS if
              g[0].startswith("candidate_full_")] else 1)
    issues=[{"kind":k,"original_test_id":n} for k,n in ISSUES.findall(text)]
    passed=(native==0 and actual==expected and bool(re.search(r"^OK\s*$",text,re.M)))
    failed=(native==1 and actual==expected and bool(re.search(r"^FAILED \(",text,re.M)))
    status=("PASS" if passed else "HOLD" if failed else "TIMEOUT" if timeout else "INCOMPLETE")
    print("P170_DISPOSABLE_ORIGINAL="+label+"|NATIVE_EXIT="+str(native)+
          "|ORIGINAL_TESTS="+str(actual)+"|STATUS="+status+"|ISSUES="+str(len(issues)),flush=True)
    print("P170_NATIVE_LOG_SHA256="+label+"|"+digest(raw),flush=True)
    return {"group":label,"original_test_ids":ids,"native_exit":native,
            "original_unittest_footer_count":actual,"expected_original_count":expected,
            "real_native_status":status,"genuine_original_failure_error_ids":issues,
            "real_original_stdout_stderr_log":log,"raw_log_sha256":digest(raw),
            "raw_log_bytes":len(raw),"seconds":round(time.monotonic()-start,3)}

def main() -> int:
    before=custody()
    historical=authenticate_p169(os.environ.get("P170_HISTORICAL_ARCHIVE_TOKEN",""))
    evidence=Path(os.environ["RUNNER_TEMP"])/"nayeon-p170-disposable-candidate-evidence"
    evidence.mkdir(parents=True,exist_ok=True)
    scratch=Path(os.environ["RUNNER_TEMP"])/("p170_disposable_"+uuid.uuid4().hex)
    safe_temp=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made=False
    try:
        if scratch.exists() or safe_temp.exists() or safe_temp.is_symlink():
            raise RuntimeError("P170 disposable work root collision")
        os.mkdir(safe_temp)
        made=True
        _verify_original_handle_policy(str(safe_temp))
        p=subprocess.run(["git","-c","core.autocrlf=false","clone","--quiet",
                          "--no-hardlinks","--single-branch",
                          "--branch",BRANCH,str(ROOT),str(scratch)],
                         stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,check=True,timeout=90)
        git(scratch,"config","--local","core.autocrlf","false")
        if git(scratch,"rev-parse","HEAD").decode().strip()!=before["source_head"]:
            raise RuntimeError("P170 copied source clone wrong Git identity")
        original_files={name:digest((scratch/name).read_bytes()) for name in SCOPE}
        reordered=[]
        for name,methods in SCOPE.items():
            changed=patch_exact_guard_first(scratch/name,methods)
            for item in changed:item["relative_path"]=name
            reordered.extend(changed)
        if len(reordered)!=5:
            raise RuntimeError("P170 did not transform exactly five trusted methods")
        changed=set(git(scratch,"diff","--name-only").decode().splitlines())
        if changed!=set(SCOPE):
            raise RuntimeError("P170 disposable candidate modifies forbidden source")
        for name in SCOPE:
            if original_files[name] != before["protected_original_source_sha256"][name]:
                raise RuntimeError("P170 original source overlay provenance mismatch")
        candidate_sources={p:{"source_original_sha256":original_files[p],
                    "only_disposable_candidate_sha256":digest((scratch/p).read_bytes())}
                    for p in SCOPE}
        diff=git(scratch,"diff","--",*sorted(SCOPE))
        diff_name="p170_disposable_guard_first_exact_candidate.patch"
        (evidence/diff_name).write_bytes(diff)
        conflict=prove_old_contract_conflict(scratch)
        result={}
        for label,ids in TEST_RUNS:
            result[label]=run_windows(label,ids,scratch,safe_temp,evidence)
        # Ensure these source changes stayed ONLY in the scratch clone and
        # no original tests were added/modified in either tree.
        if set(git(scratch,"diff","--name-only").decode().splitlines())!=set(SCOPE):
            raise RuntimeError("P170 disposable candidate test run mutated unexpected files")
        if git(scratch,"rev-parse","HEAD").decode().strip()!=before["source_head"]:
            raise RuntimeError("P170 scratch git revision drifted")
    finally:
        if scratch.exists():
            shutil.rmtree(scratch)
        if made:
            stat=safe_temp.lstat()
            if safe_temp.is_symlink() or getattr(stat,"st_file_attributes",0)&0x400:
                raise RuntimeError("P170 unsafe owned temp deletion refused")
            shutil.rmtree(safe_temp)
    if custody()!=before:
        raise RuntimeError("P170 original authoritative GitHub source changed during overlay experiment")
    phase832_pass=(result["candidate_full_original_phase832"]["real_native_status"]=="PASS"
                   and result["candidate_full_original_phase832"]["original_unittest_footer_count"]==14)
    p76_negative_pass=(result["old_original_P76_wrong_branch_negative"]["real_native_status"]=="PASS")
    p86=result["candidate_full_original_P86"]
    p87=result["candidate_full_original_P87"]
    p86_wrong_count_names={"test_live_connection_page_default_is_explicitly_unobserved",
                           "test_no_credential_action_and_no_implicit_refresh"}
    p87_wrong_count_names={"test_production_default_remains_not_observed_without_any_session"}
    def exact_original_failed_methods(actual, expected):
        names={row["original_test_id"].split(" (",1)[0] for row in
               actual["genuine_original_failure_error_ids"]}
        return names==expected and all(
            row["kind"]=="FAIL" for row in actual["genuine_original_failure_error_ids"])
    p86_p87_historical_holds=(
        p86["real_native_status"]=="HOLD" and p86["original_unittest_footer_count"]==7
        and exact_original_failed_methods(p86,p86_wrong_count_names)
        and p87["real_native_status"]=="HOLD" and p87["original_unittest_footer_count"]==18
        and exact_original_failed_methods(p87,p87_wrong_count_names))
    historical_failures=(
        result["old_original_phase831_static_import_refusal"]["real_native_status"]=="HOLD"
        and result["old_original_phase831_static_import_refusal"]["original_unittest_footer_count"]==1
        and result["old_original_WinCred_static_consumer_refusal"]["real_native_status"]=="HOLD"
        and result["old_original_WinCred_static_consumer_refusal"]["original_unittest_footer_count"]==1)
    diagnostic_fully_characterized=(phase832_pass and p76_negative_pass
                                    and p86_p87_historical_holds and historical_failures)
    verdict=("GUARD_FIRST_14_PASS__P86_2_P87_1_GENUINE_HOLDS__REVIEW_REQUIRED"
             if diagnostic_fully_characterized
             else "UNEXPECTED_CANDIDATE_FAILURE_OR_INCOMPLETE_NATIVE_EVIDENCE_HOLD")
    ledger={
        "checkpoint":"P170","source_custody_identical_before_after":before,
        "source_p169_windows_authenticity":historical,
        "disposable_candidate_only_2_modified_production_paths_sha256":candidate_sources,
        "disposable_candidate_exactly_5_guard_first_reorders":reordered,
        "candidate_disposable_unmerged_patch_log":diff_name,
        "frozen_original_P86_and_Phase831_contract_conflict":conflict,
        "genuine_hosted_Windows_unmodified_original_test_outcomes_on_candidate":result,
        "candidate_source_tested_but_NOT_prod_or_branch_modified":True,
        "original_historical_H":"HOLD",
        "current_C":"REVIEW_ONLY_DISPOSABLE_EXPERIMENT",
        "production_R":"HOLD",
        "accepted_complete_full_product_native_Windows_regressions":"0/3",
        "external_qualified_security_and_historical_governance_signed_GO":"NOT_OBTAINED",
        "publisher_signed_main_helper_installer_and_SAC_WDAC_owner_GO":"NOT_OBTAINED",
        "original_P76_P85_and_remaining_historical_failures_unwaived":True,
        "privileged_BYOK_C1_G0_to_G6":"OPEN",
        "live_secret_or_production_WinCred_or_provider_calls":"NOT_AUTHORIZED_NOT_ATTEMPTED",
        "limitations":[
            "Candidate puts guard before docstring: function __doc__ metadata is lost; requires explicit API compatibility review",
            "Candidate changes only disposable copies of product files, not source in PR; passing overlay tests are NOT production admission",
            "Older Phase8.31 static import contract and P86 explicitly contradict each other; no source-only bypass permitted",
            "Original WinCred static consumer refusal is not waived by source relocation or allowlist expansion",
            "No signed binaries, no actual full product regressions and no qualified independent review",
        ],
        "phase832_exact_original_14_full_suite_on_disposable_guard_first_PASS":phase832_pass,
        "p86_p87_exact_original_button_count_old_contract_HOLD":p86_p87_historical_holds,
        "old_P76_wrong_branch_negative_control_still_PASS":p76_negative_pass,
        "old_Phase831_and_WinCred_original_negative_genuine_FAIL_unwaived":historical_failures,
        "candidate_must_NOT_be_merged_or_treated_as_full_historical_suite_PASS":True,
        "diagnostic_verdict":verdict,
    }
    (evidence/"p170_actual_windows_disposable_compatibility_ledger.json").write_text(
        json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("P170_GUARD_FIRST_ORIGINAL_PHASE832_FULL_14_PASS="+str(phase832_pass),flush=True)
    print("P170_OLD_P86_AND_P87_BUTTON_COUNT_HISTORICAL_HOLDS="+str(p86_p87_historical_holds),flush=True)
    print("P170_FROZEN_831_AND_WINCRED_HISTORICAL_FAIL_REMAIN="+str(historical_failures),flush=True)
    print("P170_ORIGINAL_P76_WRONG_BRANCH_REFUSAL_NEGATIVE_PASS="+str(p76_negative_pass),flush=True)
    print("P170_DISPOSABLE_GUARD_FIRST_DIAGNOSTIC_VERDICT="+verdict,flush=True)
    print("P170_PRODUCTION_RELEASE_HOLD=TRUE",flush=True)
    return 0 if diagnostic_fully_characterized else 1

if __name__=="__main__":
    raise SystemExit(main())
