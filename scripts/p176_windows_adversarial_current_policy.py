"""P176 isolated adversarial mutation negatives on genuine current source, NOT release GO.

Authenticated Windows GitHub push, prior P175 original native archive custody,
purely in-memory edits of source maps, no write to any product or original test.
"""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
from unittest import mock
import uuid
import zipfile

from scripts.p139_native_fs_verified_local_temp_root import _guard_runner, _verify_original_handle_policy
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from scripts.p169_windows_failure_causality_and_guard_provenance import (
    APPROVED_SOURCE_CONSUMERS as HISTORICAL_ALLOWED,
)
from scripts.p172_windows_versioned_ui_wincred_admission import CURRENT_CONSUMERS

ROOT=Path(__file__).resolve().parents[1]
BASE="381abcf4976dd01736bb542533c837e9afa66a56"
BRANCH="byok-c1-p176-adversarial-current-policy-review-20261112"
NEW={
    "scripts/p176_windows_adversarial_current_policy.py",
    "docs/byok-c1-p176-adversarial-current-policy-review.md",
    ".github/workflows/p176-windows-adversarial-current-policy.yml",
}
P175_ID=13959541839
P175_SHA="14D1D41E81E9CD1466C2D58244AE55B2C1C54A64D52BF398D79B381202D569BD"
GROUPS={
    "P175_versioned_current_contract_8":(8,0,"PASS",0),
    "P133_original_full_manual_offline_launch_25":(25,0,"PASS",0),
    "WinCred_original_synthetic_fake_native_20":(20,0,"PASS",0),
    "P76_original_wrong_branch_refusal_1":(1,0,"PASS",0),
    "current_actual_three_button_Tk_offline_probe_1":(1,0,"PASS",0),
    "Phase831_original_forbidden_UI_import_1":(1,1,"HOLD",2),
    "WinCred_original_fixed_consumer_denial_1":(1,1,"HOLD",1),
    "P86_original_two_button_assumptions_2":(2,1,"HOLD",2),
    "P87_original_two_button_assumption_1":(1,1,"HOLD",1),
}
CRED_MODULES={"nayeon.secrets.contracts","nayeon.secrets.windows_credential"}
SCOPE_PATH="nayeon/brain/local_byok_user_scope.py"
WINDOW_PATH="nayeon/desktop_alpha/local_byok_window.py"
NEW_SCOPED_PATHS={SCOPE_PATH,WINDOW_PATH}
SENSITIVE={"GITHUB_TOKEN","GH_TOKEN","P176_ARCHIVE_TOKEN","OPENAI_API_KEY",
           "AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY","ACTIONS_RUNTIME_TOKEN",
           "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}
FOOTER=re.compile(r"^Ran (\d+) tests? in [0-9.]+s$",re.M)
FAILURES=re.compile(r"^(FAIL|ERROR): (.+)$",re.M)
REVIEWS={name:"OPEN" for name in
         ("GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=35).stdout

def source_custody()->dict:
    _guard_runner()
    if (sys.platform!="win32" or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",BASE,"HEAD").decode().strip()!=BASE
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P176 hosted Windows exact source or clean Git branch refused")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in NEW):
        raise RuntimeError("P176 must add only the three new diagnostic paths")
    if (git("rev-parse",BASE+":nayeon")!=git("rev-parse","HEAD:nayeon")
        or git("rev-parse",BASE+":tests")!=git("rev-parse","HEAD:tests")):
        raise RuntimeError("P176 original product or historical test tree changed")
    for p in (SCOPE_PATH,WINDOW_PATH,"nayeon/desktop_alpha/frozen_signed_byok_companion.py",
              "tests/test_p140_scope_migration.py","tests/test_p140_frozen_signed_companion.py",
              "tests/test_phase8_byok_c1_p76_scope.py",
              "tests/test_windows_credential_backend.py"):
        data=git("show","HEAD:"+p)
        if data!=git("show",BASE+":"+p) or data!=(ROOT/p).read_bytes():
            raise RuntimeError("P176 protected current-or-historical source drift: "+p)
    existing=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
              if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(existing)!=171:
        raise RuntimeError("P176 original Python test inventory drift")
    return {"authentic_P176_head":git("rev-parse","HEAD").decode().strip(),
            "exact_P175_parent":BASE,"only_new_diagnostic_paths":sorted(NEW),
            "original_nayeon_and_tests_trees_unchanged":True,
            "old_original_test_module_count":len(existing)}

def authenticate_p175(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P176 read-only archive access token unavailable")
    raw=_download_artifact(P175_ID,P175_SHA,token)
    if sha(raw)!=P175_SHA:
        raise RuntimeError("P176 prior Windows native archive ZIP SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=set(z.namelist())
        expected={"p175_source_bound_versioned_current_security_candidate_ledger.json"} | {
            "p175_original_native_"+g+".log" for g in GROUPS}
        if (len(z.namelist())!=10 or names!=expected
            or z.testzip() is not None):
            raise RuntimeError("P176 native P175 archival inventory/CRC invalid")
        ledger=json.loads(z.read("p175_source_bound_versioned_current_security_candidate_ledger.json"))
        if (ledger.get("checkpoint")!="P175"
            or ledger.get("source_custody_before",{}).get("P175_exact_push_head")!=BASE
            or ledger.get("source_custody_after",{}).get("P175_exact_push_head")!=BASE
            or ledger.get("source_custody_before")!=ledger.get("source_custody_after")
            or ledger.get("review_decisions")!=REVIEWS
            or ledger.get("production_R")!="HOLD"
            or ledger.get("historical_H")!="HOLD"
            or ledger.get("accepted_full_product_Windows_regressions")!="0/3"
            or ledger.get("all_expected_native_PASS_and_genuine_historical_HOLD_captured") is not True):
            raise RuntimeError("P176 P175 custody/HCR/reviewer ledger altered")
        rows=ledger["authentic_native_current_and_original_controls"]
        if set(rows)!=set(GROUPS):
            raise RuntimeError("P176 P175 complete nine original Windows group inventory mismatched")
        receipt={}
        for group,(count,exit_code,expected_status,issues_count) in GROUPS.items():
            row=rows[group]
            log=z.read("p175_original_native_"+group+".log")
            text=log.decode("utf8","replace").replace("\r\n","\n")
            foot=FOOTER.findall(text)
            issues=FAILURES.findall(text)
            if (not foot or int(foot[-1])!=count or len(issues)!=issues_count
                or row["actual_complete_unittest_count"]!=count
                or row["native_exit"]!=exit_code
                or row["original_status"]!=expected_status
                or row["raw_SHA256"]!=sha(log)
                or (expected_status=="PASS" and re.search(r"^OK\s*$",text,re.M) is None)
                or (expected_status=="HOLD" and re.search(r"^FAILED \(",text,re.M) is None)):
                raise RuntimeError("P176 prior genuine original native case drift: "+group)
            receipt[group]={"count":count,"exit":exit_code,"status":expected_status,
                            "actual_named_FAIL_ERROR":issues,
                            "original_raw_log_sha256":sha(log)}
    return {"P175_archive_ID":P175_ID,"verified_ZIP_SHA256":sha(raw),
            "original_nine_unfiltered_Windows_log_groups":receipt,
            "historical_original_HOLDS_unwaived":True}

def all_source_map()->dict[str,str]:
    return {p.relative_to(ROOT).as_posix():p.read_text(encoding="utf8")
            for p in (ROOT/"nayeon").rglob("*.py")}

def is_current_candidate_bounded(sources:dict[str,str])->bool:
    # Only the two exact current new consumers may extend the historical
    # original fixed allowlist. The predicate is deliberately exact and
    # rejects missing, duplicate, renamed, wild-card or rogue additions.
    if not NEW_SCOPED_PATHS.issubset(sources):
        return False
    scoped=[]
    for path,src in sources.items():
        try: tree=ast.parse(src)
        except SyntaxError: return False
        for n in ast.walk(tree):
            imports=[]
            if isinstance(n,ast.ImportFrom) and n.module in CRED_MODULES:
                imports=[(n.module,tuple(sorted(x.name for x in n.names)))]
            elif isinstance(n,ast.Import):
                imports=[(alias.name,("*",)) for alias in n.names if alias.name in CRED_MODULES]
            for module,names in imports:
                if path not in HISTORICAL_ALLOWED:
                    scoped.append((path,module,names))
            if path in NEW_SCOPED_PATHS:
                banned={"requests","socket","openai","winreg",
                        "nayeon.secrets.store","nayeon.secrets.resolver",
                        "nayeon.brain.providers.openai_validation"}
                if isinstance(n,ast.ImportFrom) and n.module in banned:return False
                if isinstance(n,ast.Import) and any(alias.name in banned for alias in n.names):
                    return False
    return Counter(scoped)==Counter(CURRENT_CONSUMERS)

class P176AdversarialCurrentScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=all_source_map()
        if not is_current_candidate_bounded(cls.original):
            raise AssertionError("Authenticated original current source predicate refuses baseline")

    def test_01_exact_current_baseline(self):
        self.assertTrue(is_current_candidate_bounded(self.original))

    def test_02_each_missing_source_bound_credential_edge_is_refused(self):
        exact=(
            (SCOPE_PATH,"from nayeon.secrets.contracts import SecretIdentifier, SecretValue"),
            (SCOPE_PATH,"from nayeon.secrets.windows_credential import WindowsCredentialBackend"),
            (WINDOW_PATH,"from nayeon.secrets.contracts import SecretValue"),
        )
        for path,needle in exact:
            with self.subTest(path=path,needle=needle):
                self.assertEqual(self.original[path].count(needle),1)
                mutated=dict(self.original)
                mutated[path]=self.original[path].replace(needle,"",1)
                self.assertFalse(is_current_candidate_bounded(mutated))

    def test_03_extra_UI_native_backend_edge_refused(self):
        mutated=dict(self.original)
        mutated[WINDOW_PATH]+="\nfrom nayeon.secrets.windows_credential import WindowsCredentialBackend\n"
        self.assertFalse(is_current_candidate_bounded(mutated))

    def test_04_new_unreviewed_helper_native_backend_edge_refused(self):
        mutated=dict(self.original)
        mutated["nayeon/desktop_alpha/rogue_review_helper.py"]=(
            "from nayeon.secrets.windows_credential import WindowsCredentialBackend\n")
        self.assertFalse(is_current_candidate_bounded(mutated))

    def test_05_duplicate_current_import_is_refused(self):
        mutated=dict(self.original)
        mutated[WINDOW_PATH]+="\nfrom nayeon.secrets.contracts import SecretValue\n"
        self.assertFalse(is_current_candidate_bounded(mutated))

    def test_06_wildcard_secret_import_refused(self):
        mutated=dict(self.original)
        mutated[WINDOW_PATH]=mutated[WINDOW_PATH].replace(
            "from nayeon.secrets.contracts import SecretValue",
            "from nayeon.secrets.contracts import *",1)
        self.assertFalse(is_current_candidate_bounded(mutated))

    def test_07_different_secret_symbol_is_refused(self):
        mutated=dict(self.original)
        mutated[WINDOW_PATH]=mutated[WINDOW_PATH].replace(
            "from nayeon.secrets.contracts import SecretValue",
            "from nayeon.secrets.contracts import SecretIdentifier",1)
        self.assertFalse(is_current_candidate_bounded(mutated))

    def test_08_no_network_module_from_local_controller(self):
        for statement in ("import requests","import socket","import openai","import winreg"):
            with self.subTest(statement=statement):
                mutated=dict(self.original)
                mutated[SCOPE_PATH]+="\n"+statement+"\n"
                self.assertFalse(is_current_candidate_bounded(mutated))

    def test_09_no_provider_validator_import_from_UI(self):
        mutated=dict(self.original)
        mutated[WINDOW_PATH]+="\nfrom nayeon.brain.providers.openai_validation import validate\n"
        self.assertFalse(is_current_candidate_bounded(mutated))

    def test_10_no_obscured_nonallowlisted_native_consumer(self):
        mutated=dict(self.original)
        mutated["nayeon/brain/unreviewed_consumer.py"]="import nayeon.secrets.windows_credential\n"
        self.assertFalse(is_current_candidate_bounded(mutated))

    def test_11_actual_frozen_launch_gate_unissued_despite_synthetic_environment(self):
        from nayeon.desktop_alpha import frozen_signed_byok_companion as gate
        with mock.patch.dict(os.environ,{
            "NAYEON_P140_APPROVED_MAIN_SHA256":"a"*64,
            "NAYEON_P140_APPROVED_COMPANION_SHA256":"b"*64,
            "NAYEON_P140_APPROVED_SIGNER_CERT_SHA256":"c"*64,
            "NAYEON_P140_APPROVED_CODE_INTEGRITY_RELEASE":"1",
        }):
            self.assertEqual(gate._APPROVED_MAIN_SHA256,"")
            self.assertEqual(gate._APPROVED_COMPANION_SHA256,"")
            self.assertEqual(gate._APPROVED_SIGNER_CERT_SHA256,"")
            self.assertIs(gate._APPROVED_CODE_INTEGRITY_RELEASE,False)
            self.assertFalse(gate._release_pins_issued())
            self.assertIsNone(gate.approved_frozen_local_byok_companion())

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p176-adversarial-current"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P176","historical_H":"HOLD","current_C":"ADVERSARIAL_CANDIDATE_ONLY",
            "release_R":"HOLD","independent_review":REVIEWS,
            "full_product_accepted_Windows":"0/3","real_key_or_native_credentials":"NOT_ATTEMPTED"}
    try:
        before=source_custody()
        ledger["exact_source_custody"]=before
        ledger["prior_P175_original_Windows_archive"]=authenticate_p175(
            os.environ.get("P176_ARCHIVE_TOKEN",""))
        root=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
        if root.exists() or root.is_symlink():
            raise RuntimeError("P176 disposable local root collision")
        os.mkdir(root)
        _verify_original_handle_policy(str(root))
        env=os.environ.copy()
        for k in list(env):
            if k in SENSITIVE or k.endswith("_API_KEY") or k.endswith("_SECRET"):
                env.pop(k,None)
        env.update({"TEMP":str(root),"TMP":str(root),"TMPDIR":str(root),
                    "PYTHONDONTWRITEBYTECODE":"1"})
        log=out/"p176_actual_original_windows_adversarial_candidate_11.log"
        with log.open("wb") as f:
            try:
                p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                    "scripts.p176_windows_adversarial_current_policy.P176AdversarialCurrentScope"],
                    cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                    stderr=subprocess.STDOUT,timeout=90,check=False)
                exit_code=p.returncode
            except subprocess.TimeoutExpired:
                exit_code=124
        raw=log.read_bytes()
        txt=raw.decode("utf8","replace").replace("\r\n","\n")
        footer=FOOTER.findall(txt)
        count=int(footer[-1]) if footer else None
        issues=FAILURES.findall(txt)
        ledger["actual_Windows_p176_candidate"]={"original_count":count,"native_exit":exit_code,
            "original_raw_log":log.name,"SHA256":sha(raw),"named_FAIL_ERROR":issues}
        ledger["source_custody_after"]=source_custody()
        passed=(count==11 and exit_code==0 and not issues
                and re.search(r"^OK\s*$",txt,re.M) is not None
                and before==ledger["source_custody_after"])
        print("P176_ACTUAL_CURRENT_ADVERSARIAL_TESTS="+str(count)+"/11"+
              "|EXIT="+str(exit_code)+"|VERDICT="+("PASS" if passed else "HOLD"),flush=True)
        print("P176_ACTUAL_ORIGINAL_NATIVE_LOG_SHA256="+sha(raw),flush=True)
        print("P176_PRIOR_P175_ALL_NINE_NATIVE_LOGS_REAUTHENTICATED=YES",flush=True)
        print("P176_SEVEN_EXTERNAL_GOVERNANCE_DECISIONS=OPEN",flush=True)
        print("P176_HISTORICAL_H=HOLD|CURRENT_C=SCOPED_ONLY|RELEASE_R=HOLD",flush=True)
        return 0 if passed else 1
    except Exception as exc:
        ledger["collector_failure"]=repr(exc)
        print("P176_AUTHENTIC_SOURCE_OR_NATIVE_EVIDENCE_HOLD="+repr(exc),flush=True)
        return 1
    finally:
        (out/"p176_authenticated_adversarial_security_governance_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
        # Do not traverse/delete potential replacement reparse trees in hosted test.
        # Ephemeral Windows runner is discarded after artifact archive.

if __name__=="__main__":
    raise SystemExit(main())
