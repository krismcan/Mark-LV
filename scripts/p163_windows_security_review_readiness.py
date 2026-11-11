"""P163 independent-review READINESS only — original Windows security evidence.

Not an independent reviewer approval. Re-executes 25 EXACT unchanged P153
negative/current-user controls, verifies immutable P76/P140 failures-to-open
and probes the not-installed P162 object reader with corruption. No source
or security-test edits, no provider key, production WinCred, Git refs changes.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

from scripts.p139_native_fs_verified_local_temp_root import _guard_runner, _verify_original_handle_policy
from scripts.p153_windows_current_branch_security_candidate import (
    TEST_CLASSES, ORIGINALS, PINNED_ORIGINAL_P76_BRANCH,
    P140_PIN_DEFAULTS, _top_level_constants,
)
from scripts.p162_windows_immutable_git_batch_candidate import (
    verify_blob, negative_contracts, sha1_blob,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = "9c2422eb920d8b478520fca7de4bf974bf7c92c6"
BRANCH = "byok-c1-p163-immutable-git-security-review-readiness-20261111"
COUNT = re.compile(r"^Ran (\d+) tests? in [0-9.]+s$", re.M)
HEADINGS = re.compile(r"^(FAIL|ERROR): ([^\r\n]+)", re.M)
END_OK = re.compile(r"^OK\s*$", re.M)
END_FAIL = re.compile(r"^FAILED \(([^)]+)\)\s*$", re.M)
CANDIDATE = "p162_windows_immutable_git_batch_candidate"
SECRET_ENV = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY",
    "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "NAYEON_INTERNAL_SECRET", "P163_TEST_TOKEN",
)


def _sha(data: bytes):
    return hashlib.sha256(data).hexdigest().upper()


def _git(*args):
    p = subprocess.run(["git", "-C", str(ROOT), *args],
                       stdin=subprocess.DEVNULL, capture_output=True,
                       check=True, timeout=25)
    return p.stdout


def _require_source():
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P163 wrong hosted Windows branch")
    head = _git("rev-parse", "HEAD").decode().strip()
    if head != os.environ.get("GITHUB_SHA") or _git("merge-base", BASE, head).decode().strip() != BASE:
        raise RuntimeError("P163 P162 ancestry / actual source SHA mismatch")
    if _git("status", "--porcelain=v1"):
        raise RuntimeError("P163 checkout dirty")
    inventory = [x for x in _git("ls-files", "tests/test_*.py").decode().splitlines()
                 if x.startswith("tests/test_") and x.endswith(".py")]
    if len(inventory) != 170:
        raise RuntimeError("P163 exact 170 tracked test files drift")
    # Original nine current-scope security/product/test files plus all
    # historical Git, filesystem trust and P162 prototype remain Git-blob exact.
    secure = tuple(ORIGINALS) + (
        "tests/phase_8_36_scope_migration.py",
        "tests/phase_8_37_scope_migration.py",
        "tests/test_phase_837_scope_integrity.py",
        "scripts/p162_windows_immutable_git_batch_candidate.py",
    )
    custody = []
    for path in sorted(set(secure)):
        if _git("rev-parse", "HEAD:" + path) != _git("rev-parse", BASE + ":" + path):
            raise RuntimeError("P163 source custody drift: " + path)
        custody.append({"path":path, "sha256":_sha((ROOT/path).read_bytes()),
                        "original_byte_identity_preserved":True})
    gate = _top_level_constants(ROOT / "tests/phase8_byok_c1_p76_scope.py", {"BRANCH"})
    if gate != {"BRANCH":PINNED_ORIGINAL_P76_BRANCH}:
        raise RuntimeError("P163 frozen P76 wrong-branch fail-closed policy changed")
    p140 = _top_level_constants(
        ROOT / "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
        set(P140_PIN_DEFAULTS),
    )
    if p140 != P140_PIN_DEFAULTS:
        raise RuntimeError("P163 P140 signing/policy NO-GO became permissive")
    for namespace in ("nayeon", "tests"):
        original_git = subprocess.run(
            ["git", "-C", str(ROOT), "grep", "-l", "-F",
             CANDIDATE, BASE, "--", namespace],
            stdin=subprocess.DEVNULL, capture_output=True, check=False, timeout=25,
        )
        if original_git.returncode not in (0,1):
            raise RuntimeError("P163 cannot inspect historical source import/use closure")
        # A P162 candidate must not be integrated anywhere in existing product
        # or tests. Its own script and docs are intentionally outside this scope.
        if original_git.stdout:
            raise RuntimeError("P163 candidate imported into product/tests prior to approval")
    print("P163_EXACT_P162_PARENT_AND_ORIGINAL_SOURCE_CUSTODY=PASS",flush=True)
    print("P163_P76_EXACT_BRANCH_AND_P140_SIGNED_RELEASE_NO_GO=PASS",flush=True)
    print("P163_P162_READER_UNINTEGRATED_IN_PRODUCT_AND_ORIGINAL_TESTS=PASS",flush=True)
    return head,custody


def _selected_original_tests():
    ids=[]
    groups=[]
    for group,(klass,names) in TEST_CLASSES.items():
        prefix,class_name=klass.rsplit(".",1)
        path=ROOT/(prefix.replace(".","/")+".py")
        tree=ast.parse(path.read_bytes(),filename=str(path))
        classes=[x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==class_name]
        if len(classes)!=1:
            raise RuntimeError("P163 original security test class changed: "+klass)
        present={node.name for node in classes[0].body if isinstance(node,ast.FunctionDef)}
        if len(set(names))!=len(names) or not set(names).issubset(present):
            raise RuntimeError("P163 exact original security test method identity changed")
        selected=[klass+"."+name for name in names]
        ids.extend(selected)
        groups.append({"domain":group,"unchanged_original_test_method_ids":selected})
    if len(ids)!=25 or len(set(ids))!=25:
        raise RuntimeError("P163 25 original immutable security tests drift")
    return ids,groups


def _in_memory_reader_probe():
    """Do NOT alter original product tests or Git security fixture mock routes."""
    from tests import phase_8_37_scope_migration as scope
    pins=dict(scope.prior.CANDIDATE_SHA256)
    if len(pins)!=19 or scope.PROTECTED!="a12565b9be070684e1d7d801ded4833d13121f94":
        raise RuntimeError("P163 historical immutable protected object inventory drift")
    path=sorted(pins)[0]
    oid=_git("rev-parse", scope.PROTECTED+":"+path).decode().strip()
    raw=_git("show", scope.PROTECTED+":"+path)
    if len(oid)!=40 or sha1_blob(raw)!=oid:
        raise RuntimeError("P163 actual Git frozen object identity mismatch")
    header=f"{oid} blob {len(raw)}\n".encode("ascii")
    if verify_blob(path,oid,header,raw,b"\n",oid,pins,scope.prior._digest)!=raw:
        raise RuntimeError("P163 correct candidate read rejected")
    n=negative_contracts(path,oid,raw,oid,pins,scope.prior._digest)
    # Additional adverse SOURCE and TRUST cases beyond P162's original nine.
    # All are in-memory, with no filesystem, index, tags or refs mutations.
    variants=(
        ("wrong_pin_sha256",path,oid,header,raw,b"\n",oid,{**pins,path:"f"*64}),
        ("casefold_alias_path",path.upper(),oid,header,raw,b"\n",oid,pins),
        ("backslash_path",path.replace("/","\\"),oid,header,raw,b"\n",oid,pins),
        ("embedded_nul_header",path,oid,header[:-1]+b"\0\n",raw,b"\n",oid,pins),
        ("empty_blob_header",path,oid,f"{oid} blob 0\n".encode(),raw,b"\n",oid,pins),
        ("unexpected_additional_data",path,oid,f"{oid} blob {len(raw)+1}\n".encode(),raw+b"X",b"\n",oid,pins),
        ("wrong_sha1_rebound_to_modified_bytes",path,oid,header,raw[:-1]+bytes([raw[-1]^1]),b"\n",oid,pins),
    )
    rejects=[]
    for name,p,o,h,b,d,e,trust in variants:
        try:
            verify_blob(p,o,h,b,d,e,trust,scope.prior._digest)
        except ValueError:
            rejects.append(name)
        else:
            raise RuntimeError("P163 candidate erroneously accepted adversarial: "+name)
    if len(rejects)!=7 or n!=9:
        raise RuntimeError("P163 refusal coverage incomplete")
    print("P163_REAL_GIT_FROZEN_OBJECT_BASELINE=PASS",flush=True)
    print("P163_IN_MEMORY_CANDIDATE_ADVERSARIAL_REFUSALS="+str(n+len(rejects)),flush=True)
    return {"actual_original_git_blob_oid":oid,
            "original_blob_sha256":_sha(raw),"original_blob_bytes":len(raw),
            "exact_original_historical_sha256_pin":pins[path],
            "p162_original_negative_probes_rejected":n,
            "p163_additional_adverse_cases_rejected":rejects,
            "total_adversarial_candidate_refusals":n+len(rejects)}


def _run_original(ids, out, temp):
    raw_path=out/"p163_original_25_security_methods_native_windows.log"
    env=os.environ.copy()
    for k in SECRET_ENV:
        env.pop(k,None)
    env.update({"TEMP":str(temp),"TMP":str(temp),"TMPDIR":str(temp),
                "PYTHONDONTWRITEBYTECODE":"1"})
    started=time.monotonic()
    timedout=False
    with raw_path.open("wb") as stream:
        proc=subprocess.Popen(
            [sys.executable,"-B","-m","unittest","-v",*ids],
            cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
            stdout=stream,stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0),
        )
        try:
            native=proc.wait(timeout=115)
        except subprocess.TimeoutExpired:
            timedout=True
            native=124
            subprocess.run(
                ["taskkill","/PID",str(proc.pid),"/T","/F"],
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,check=False,timeout=12,
            )
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    raw=raw_path.read_bytes()
    text=raw.decode("utf8","replace").replace("\r\n","\n")
    runs=COUNT.findall(text)
    count=int(runs[-1]) if runs else None
    errors=[{"kind":k,"original_test":name} for k,name in HEADINGS.findall(text)]
    complete=count==25 and (bool(END_OK.search(text)) or bool(END_FAIL.search(text)))
    verdict=("PASS" if native==0 and complete and END_OK.search(text) and not errors
             else "TIMEOUT" if native==124 and timedout else "HOLD")
    print("P163_ORIGINAL_WINDOWS_25_SECURITY_METHODS_NATIVE_EXIT="+str(native)+
          "|UNFILTERED_NAMED_COUNT="+str(count)+"|VERDICT="+verdict+
          "|SECONDS="+str(round(time.monotonic()-started,3)),flush=True)
    return {"original_test_method_expected":len(ids),
            "original_test_method_observed":count,
            "native_exit":native,
            "actual_unittest_footer_complete":bool(complete),
            "original_error_failure_headings":errors,
            "status":verdict,"elapsed_seconds":round(time.monotonic()-started,3),
            "raw_original_test_log_sha256":_sha(raw),
            "raw_original_test_log_bytes":len(raw),
            "original_log_name":raw_path.name}


def main():
    head,custody=_require_source()
    ids,groups=_selected_original_tests()
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p163-security-review-readiness"
    out.mkdir(parents=True,exist_ok=True)
    temp=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made=False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P163 test root already exists")
        os.mkdir(temp)
        made=True
        _verify_original_handle_policy(str(temp))
        print("P163_UNCHANGED_P139_NATIVE_FILE_HANDLE_POLICY=PASS",flush=True)
        probe=_in_memory_reader_probe()
        run=_run_original(ids,out,temp)
    finally:
        if made:
            st=temp.lstat()
            if temp.is_symlink() or getattr(st,"st_file_attributes",0)&0x400:
                raise RuntimeError("P163 unsafe Win temp cleanup refused")
            shutil.rmtree(temp)
    if _git("status","--porcelain=v1"):
        raise RuntimeError("P163 security source changed during tests")
    manifest={
        "checkpoint":"P163",
        "tested_git_sha":head,"exact_p162_predecessor":BASE,
        "source_custody":custody,
        "original_25_method_groups":groups,
        "original_native_windows_security_test_run":run,
        "candidate_in_memory_adversarial_probes":probe,
        "candidate_integrated_into_product_or_original_tests":False,
        "original_P76_P85_exact_branch_security_refusals":"UNCHANGED",
        "original_historical_P76_two_branch_positive_test_failures":"PRESERVED_NOT_WAIVED",
        "P140_signed_release_pins":"EMPTY_AND_CODE_INTEGRITY_GO_FALSE",
        "independent_qualified_security_reviewer_identity":"NOT_OBTAINED",
        "reviewer_go_for_historical_regression_governance":"NOT_OBTAINED",
        "candidate_production_integration_decision":"NO_GO",
        "complete_full_product_native_windows_regression_triad":"0/3",
        "privileged_BYOK_C1_G0_to_G6":"OPEN",
        "production_release":"HOLD",
        "collector_success_not_full_product_security_signoff":True,
    }
    (out/"p163_original_security_reviewer_readiness_ledger.json").write_text(
        json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf8"
    )
    print("P163_SOURCE_AND_CANDIDATE_INTEGRATION_GUARD=PASS",flush=True)
    print("P163_ORIGINAL_SECURITY_TEST_VERDICT="+run["status"],flush=True)
    print("P163_EXTERNAL_INDEPENDENT_SECURITY_GO=NOT_OBTAINED",flush=True)
    print("P163_FULL_PRODUCT_WINDOWS_TRIAD=0/3",flush=True)
    print("P163_PRODUCTION_RELEASE=HOLD",flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
