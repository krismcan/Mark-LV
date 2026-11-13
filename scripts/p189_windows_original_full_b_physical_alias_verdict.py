"""P189: original full historical BYOK-B native Windows hardlink/ADS verdict.

Experimental read-only assessment using disposable original sealed-A parent
and 23 authentic historical B source bytes. Do not confuse with public Phase10
successor or production authorisation. No original frozen source changes.
"""
from __future__ import annotations
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
import zipfile

from scripts import p188_windows_physical_source_alias_race_witness as previous
from scripts import p187_windows_live_byok_b_equivalence as p187
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P188="d351c1a968991a14c233e53a566b466e5ffe2d19"
BRANCH="byok-c1-p189-full-b-physical-alias-verdict-20261113"
NEW={
 "scripts/p189_windows_original_full_b_physical_alias_verdict.py",
 "docs/byok-c1-p189-original-full-B-alias-admission-review.md",
 ".github/workflows/p189-windows-full-B-alias-admission.yml",
}
ARTIFACT=14028267868
ARCHIVE_SHA="FD6DF6DC1A79D8A3B6BC3C789741C3A625DE2175F9E83AEF18BE2E3A2D8C6C64"
LOGS={
 "p188_original_exact_P184_native_Windows_12.log":("12","1484EFC3590CE35D9F9DA43521E949471B4DCAE2C1267E31DFB16596C9CBD218"),
 "p188_original_exact_P185_native_Windows_12.log":("12","48723A685012C477928DC85EE2D71088ED6F8744912CB3AC403C1B0C3F9BCFDA"),
 "p188_original_exact_P186_native_Windows_12.log":("12","FF9C317F87E98D4109CE08140939F26ABE7A3E03D0BF93E16DBEC8F2AC221A06"),
 "p188_original_exact_P187_native_Windows_6.log":("6","C9C19A770FF97A8C19BBBD8CA5BAC7549117ED2EB87F89562B7F5EB7CE3A5DEC"),
 "p188_current_real_NTFS_hardlink_ADS_junction_race_9.log":("9","D80B44D682715EEB2FC0DE40BCCB35EA1754EEBA7466A876610E4972795F3A39"),
 "p188_diagnostic_original_frozen_B_link_reparse_hardlink.log":("1","C19F779B7A996CFE414F9B7D001F9F44B60E0C1658B04D10E22322C911D14C53"),
}
LEDGER="p188_source_bound_NTFS_alias_race_security_HCR_ledger.json"
REVIEWS=previous.REVIEWS
BHEAD=p187.B_COMMIT

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest().upper()

def git(*args:str,root:Path=ROOT)->bytes:
    p=subprocess.run(["git","-C",str(root),*args],stdin=subprocess.DEVNULL,
       stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=False)
    if p.returncode:
        raise RuntimeError("P189 Git native exit "+str(p.returncode)+
                           " "+repr(args)+" "+p.stderr.decode("utf8","replace")[-300:])
    return p.stdout

def custody()->dict:
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",P188,"HEAD").decode().strip()!=P188
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P189 exact Windows source identity/cleanliness refused")
    if set(git("diff","--name-only",P188,"HEAD").decode().splitlines())!=NEW:
        raise RuntimeError("P189 only three new review-only paths permitted")
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P188+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P189 original frozen tests/product changed")
    for path in (
      "scripts/p187_windows_live_byok_b_equivalence.py",
      "scripts/p188_windows_physical_source_alias_race_witness.py",
      "tests/phase8_byok_b_scope_migration.py",
      "tests/phase8_byok_scope_migration.py",
      "tests/test_phase8_byok_b_scope_integrity.py",
    ):
        if git("show",P188+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P189 original B admission or previous candidate modified")
    return {"P189_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P188_parent":P188,
            "only_three_added_paths":sorted(NEW),
            "original_product_and_frozen_tests_unchanged":True}

def authenticate_P188(token:str)->dict:
    if len(token)<8:raise RuntimeError("P189 absent ephemeral P188 evidence token")
    data=_download_artifact(ARTIFACT,ARCHIVE_SHA,token)
    if sha(data)!=ARCHIVE_SHA:raise RuntimeError("P189 original P188 archive changed")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(LOGS)|{LEDGER}:
            raise RuntimeError("P189 original P188 ZIP inventory or CRC incorrect")
        for name,(n,digest) in LOGS.items():
            raw=z.read(name)
            txt=raw.decode("utf8","replace").replace("\r\n","\n")
            if (sha(raw)!=digest or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=[n]
                or not re.search(r"^OK\s*$",txt,re.M)):
                raise RuntimeError("P189 source-bound original P188 Windows footer/SHA mismatch: "+name)
        record=json.loads(z.read(LEDGER))
        if (record.get("checkpoint")!="P188" or record.get("historical_H")!="HOLD"
            or record.get("production_R")!="HOLD"
            or record.get("full_product_native_windows_regressions")!="0/3"
            or record.get("qualified_independent_review")!=REVIEWS
            or record.get("source_before")!=record.get("source_after")
            or record["source_before"].get("P188_HEAD")!=P188
            or record.get("experimental_checkpoint_complete_not_product_admission") is not True):
            raise RuntimeError("P189 original P188 H/C/R accepted evidence altered")
    return {"original_artifact":ARTIFACT,"SHA256":ARCHIVE_SHA,
            "prior_four_exact_branch_selected_tests":42,
            "prior_P188_9_native_plus_1_frozen_diagnostic":[9,1],
            "qualified_review":"OPEN","production_release":"HOLD"}

class P189ActualOriginalFullBPhysicalAliasVerdict(unittest.TestCase):
    """True original B private gate, physical native Windows real-worktree cases.

    Preserve original bytes, repository root and external hardlink/ADS metadata.
    Refusals only count if they cite relevant link/stream/path reason, rather
    than an unrelated fixture error.
    """
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P189 original native Windows required")
        cls.original=p187.P187RealWindowsDisposableWorktreeTests
        cls.original.setUpClass()
        cls.path=cls.original.path
        cls.source=cls.path/B.SELF
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"original"):cls.original.tearDownClass()
    def observe(self,label:str,*,expected_state="COMPLETE_UNSTAGED")->str:
        started=time.perf_counter()
        code,txt=self.original.run_original_gate(self)
        elapsed=time.perf_counter()-started
        if code==0:
            self.assertIn("P187_ORIGINAL_B_ADMISSION="+expected_state,txt,
                          "Unrelated B success not accepted "+txt[-1300:])
            print("P189_ACTUAL_ORIGINAL_FULL_B_"+label+"=ADMITTED"+
                  "|REAL_NATIVE_EXIT=0|SECONDS="+format(elapsed,".3f"),flush=True)
            return "ADMITTED"
        relevant=("hardlink","link","reparse","stream","alias","ignored","untracked","source")
        if ("AssertionError:" not in txt
            or not any(word in txt.lower() for word in relevant)):
            self.fail("P189 original full B failed for unrelated reason: "+txt[-2600:])
        print("P189_ACTUAL_ORIGINAL_FULL_B_"+label+"=REFUSED_WITH_SOURCE_REASON"+
              "|REAL_NATIVE_EXIT="+str(code)+"|SECONDS="+format(elapsed,".3f")+
              "|TAIL="+repr(txt[-500:]),flush=True)
        return "REFUSED_WITH_SOURCE_REASON"
    def require_sealed_bytes(self):
        raw=self.source.read_bytes()
        self.assertEqual(B._digest(B.SELF,raw),B.CANDIDATE_SHA256[B.SELF])
        self.assertEqual(git("rev-parse","HEAD",root=self.path).decode().strip(),B.PARENT)
    def test_01_baseline_original_full_B_unstaged_gate_accepts_without_alias(self):
        self.require_sealed_bytes()
        self.assertEqual(self.observe("BASELINE"),"ADMITTED")
    def test_02_hardlink_OUTSIDE_repo_preserves_original_git_scope_observe_full_gate(self):
        self.require_sealed_bytes()
        outside=self.path.parent/"p189_alternate_hardlink_outside_repo"
        os.link(self.source,outside)
        try:
            self.assertEqual(self.source.stat().st_nlink,2)
            self.assertEqual(self.observe("HARDLINK_OUTSIDE_GIT_SCOPE"),
                             "ADMITTED")
        finally:
            outside.unlink()
        self.assertEqual(self.source.stat().st_nlink,1)
    def test_03_named_NTFS_ADS_on_original_source_observe_full_gate(self):
        self.require_sealed_bytes()
        stream=str(self.source)+":p189_nonexecuting_data"
        with open(stream,"wb") as f:f.write(b"P189 artificial nonexecuting NTFS metadata")
        try:
            self.assertIn(":p189_nonexecuting_data:$DATA",
                          previous.Win32SourceInspectionCandidate.streams(self.source))
            self.assertEqual(self.observe("NAMED_NTFS_ADS"),"ADMITTED")
        finally:
            try:os.remove(stream)
            except FileNotFoundError:pass
    def test_04_two_aliases_together_observe_original_full_gate_and_recover(self):
        self.require_sealed_bytes()
        outside=self.path.parent/"p189_second_hardlink_outside_repo"
        stream=str(self.source)+":p189_second_data"
        os.link(self.source,outside)
        with open(stream,"wb") as f:f.write(b"synthetic stream")
        try:
            self.assertEqual(self.source.stat().st_nlink,2)
            self.assertIn(":p189_second_data:$DATA",
                          previous.Win32SourceInspectionCandidate.streams(self.source))
            self.assertEqual(self.observe("BOTH_HARDLINK_AND_ADS"),"ADMITTED")
        finally:
            try:os.remove(stream)
            except FileNotFoundError:pass
            outside.unlink()
        self.assertEqual(self.source.stat().st_nlink,1)

def run_tests(path:Path,selector:str,out:Path,expected_sha:str,count:int,env:dict,
              timeout:int=150)->dict:
    if git("rev-parse","HEAD",root=path).decode().strip()!=expected_sha:
        raise RuntimeError("P189 old original branch HEAD changed")
    env=dict(env,GITHUB_SHA=expected_sha,PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1")
    for k in list(env):
        if k in ("P189_ARCHIVE_TOKEN","GITHUB_TOKEN","GH_TOKEN") or k.endswith(("_API_KEY","_SECRET")):
            env.pop(k,None)
    with out.open("wb") as handle:
        p=subprocess.run([sys.executable,"-B","-m","unittest","-v",selector],
            cwd=path,env=env,stdin=subprocess.DEVNULL,stdout=handle,
            stderr=subprocess.STDOUT,timeout=timeout,check=False)
    raw=out.read_bytes()
    text=raw.decode("utf8","replace").replace("\r\n","\n")
    footers=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)
    return {"source_SHA":expected_sha,"native_exit":p.returncode,
            "expected":count,"actual_footers":footers,
            "full_OK":bool(re.search(r"^OK\s*$",text,re.M)),
            "raw_log":out.name,"log_SHA256":sha(raw),
            "real_B_verdicts":re.findall(r"P189_ACTUAL_ORIGINAL_FULL_B_[^\r\n]+",text),
            "named_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",text,re.M)}
def demand_native(result:dict):
    if (result["native_exit"]!=0 or result["actual_footers"]!=[str(result["expected"])]
        or not result["full_OK"]):
        raise RuntimeError("P189 source-bound native Windows run incomplete "+
                           result["raw_log"]+" "+repr(result["named_FAIL_ERROR"]))

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p189-full-B-physical-admission"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
      "checkpoint":"P189","historical_H":"HOLD",
      "current_C":"ISOLATED_PHYSICAL_ORIGINAL_FULL_B_ALIAS_ADMISSION_VERDICT",
      "production_R":"HOLD","full_product_native_windows_regressions":"0/3",
      "qualified_external_seven_reviews":REVIEWS,
      "privileged_C1_G0_G6":"OPEN",
      "signed_binary_installer_SAC_WDAC_GO":False,
      "public_current_Phase10_verifier_replaced":False,
      "old_original_B_gate_source_or_test_modified":False,
      "original_old_P135_P175_P178_P179_failures":"UNWAIVED",
      "mitigation_architecture_status":"NOT_REVIEWED_NOT_INTEGRATED",
      "unproven_atomic_win32_leaf_parent_handle_security":"OPEN",
    }
    okay=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["authentic_original_P188"]=authenticate_P188(
             os.environ.get("P189_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        root=Path(os.environ["P189_ORIGINAL_P188_ROOT"])
        if not root.is_dir() or root.resolve()==ROOT.resolve():
            raise RuntimeError("P189 original P188 exact branch clone missing")
        old=run_tests(root,
           "scripts.p188_windows_physical_source_alias_race_witness.P188NativePhysicalWindowsSourceCases",
           out/"p189_original_exact_P188_native_Windows_9.log",P188,9,env)
        ledger["original_P188_exact_source_original_tests"]=old
        demand_native(old)
        new=run_tests(ROOT,
           "scripts.p189_windows_original_full_b_physical_alias_verdict.P189ActualOriginalFullBPhysicalAliasVerdict",
           out/"p189_current_true_original_full_B_physical_alias_4.log",
           os.environ["GITHUB_SHA"],4,env,220)
        ledger["current_original_full_B_physical_alias_verdicts"]=new
        demand_native(new)
        if len(new["real_B_verdicts"])!=4:
            raise RuntimeError("P189 missing actual original full B positive/negative provenance")
        after=custody()
        ledger["source_after"]=after
        if before!=after:raise RuntimeError("P189 original frozen source changed during tests")
        okay=True
        print("P189_ORIGINAL_P188_EXACT_SOURCE_PHYSICAL_9=9/9_NATIVE_PASS",flush=True)
        print("P189_CURRENT_ACTUAL_ORIGINAL_FULL_B_PHYSICAL_VERDICT_4=4/4_NATIVE_PASS",flush=True)
        print("P189_SOURCE_BOUND_TRUE_NATIVE_RUNS_13=13/13_SELECTED_NOT_FULL_PRODUCT",flush=True)
        print("P189_HARDLINK_ADS_ACTUAL_FULL_B_VERDICTS_IN_AUTHENTIC_RAW_LOGS",flush=True)
        print("P189_NO_PRODUCT_SECURITY_OR_CURRENT_PHASE10_PRODUCTION_INTEGRATION",flush=True)
        print("P189_FULL_PRODUCT_WINDOWS=0/3|EXTERNAL_REVIEW=OPEN|RELEASE=HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P189_REAL_WINDOWS_ORIGINAL_FULL_B_ALIAS_EVIDENCE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_original_full_B_physical_verdict_complete_NOT_release"]=okay
        (out/"p189_original_full_B_physical_alias_HCR_custody_ledger.json").write_text(
           json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if okay else 1

if __name__=="__main__":
    raise SystemExit(main())
