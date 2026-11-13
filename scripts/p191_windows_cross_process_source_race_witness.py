"""P191: real cross-process Win32 exclusive-HANDLE source and ADS race witnesses.

Preserve original product, P190 candidate, old historical sources and holds.
Isolated temporary Windows fixtures only. No real keys, no live provider.
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
import tempfile
import unittest
import zipfile

from scripts import p190_windows_handle_bound_source_probe as p190
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P190="8a94be2670610048416cf6832831a14073a635f5"
BRANCH="byok-c1-p191-concurrent-source-handle-ads-race-witness-20261113"
NEW={
    "scripts/p191_windows_cross_process_source_race_witness.py",
    "docs/byok-c1-p191-concurrent-win32-source-ads-race-review.md",
    ".github/workflows/p191-windows-cross-process-source-race.yml",
}
ARTIFACT=14033988074
ORIGINAL_ZIP_SHA="D353B1AEDC136528EAA301C14848A94EF13B61F89C90A0F17541158126A14036"
EXPECTED_P190_LOGS={
    "p190_original_exact_P189_full_B_physical_alias_4.log":
      ("4","1CF15C42C6B3496DDEFA084D7753C68B96D96C28AD94C3B5D7D08469BCF08E7A"),
    "p190_current_real_Win32_handle_ADS_10.log":
      ("10","08EE33108643255AC1758B4753010CAD471919CBCA92C30A2ABD7ACC6296B6F8"),
}
LEDGER_NAME="p190_handle_bound_ntfs_ADS_HCR_original_source_ledger.json"
ORIGINAL_B_SELF=B.SELF
SOURCE_HASH=B.CANDIDATE_SHA256[ORIGINAL_B_SELF]
REVIEWS=p190.REVIEWS
FAIL_CODES={5,32}
# The same opened Windows HANDLE stays live throughout a separate child process.
# The child only receives runner-owned temporary synthetic paths, never credentials.
CHILD_SCRIPT=r"""
import json
import os
import sys
operation,source,destination=sys.argv[1:4]
try:
    if operation=="write_source":
        # Request native GENERIC_WRITE from an external process to obtain the
        # real GetLastError Win32 sharing decision; do not alter source bytes.
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel.CreateFileW.argtypes=[
            wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,
            ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE
        ]
        kernel.CreateFileW.restype=wintypes.HANDLE
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        kernel.CloseHandle.restype=wintypes.BOOL
        handle=kernel.CreateFileW(source,0x40000000,7,None,3,0x200000,None)
        if handle is None or handle==ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        kernel.CloseHandle(handle)
    elif operation=="create_ads":
        with open(source+":p191_cross_process_stream","wb") as f:
            f.write(b"P191 synthetic named ADS")
    elif operation=="rename_source":
        os.rename(source,destination)
    elif operation=="delete_source":
        os.unlink(source)
    elif operation=="replace_source":
        os.replace(destination,source)
    elif operation=="create_hardlink":
        os.link(source,destination)
    elif operation=="rename_parent":
        os.rename(source,destination)
    elif operation=="write_sibling":
        with open(destination,"wb") as f:f.write(b"P191 independent sibling file")
    else:
        raise ValueError("Unsupported isolated P191 action")
    result={"operation":operation,"succeeded":True,"winerror":None,
            "errno":None,"error_class":None}
except OSError as exc:
    result={"operation":operation,"succeeded":False,
            "winerror":getattr(exc,"winerror",None),
            "errno":exc.errno,"error_class":type(exc).__name__}
print(json.dumps(result,sort_keys=True))
"""

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest().upper()

def git(*args:str,root:Path=ROOT)->bytes:
    run=subprocess.run(["git","-C",str(root),*args],stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=False)
    if run.returncode:
        raise RuntimeError("P191 source identity Git native exit="+str(run.returncode)+
          " "+repr(args)+" "+run.stderr.decode("utf8","replace")[-400:])
    return run.stdout

def custody()->dict:
    if (sys.platform!="win32"
        or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",P190,"HEAD").decode().strip()!=P190
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P191 only exact clean hosted original Windows source")
    if set(git("diff","--name-only",P190,"HEAD").decode().splitlines())!=NEW:
        raise RuntimeError("P191 only three new review-only paths allowed")
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P190+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P191 original product or frozen tests modified")
    for path in (
       "scripts/p187_windows_live_byok_b_equivalence.py",
       "scripts/p188_windows_physical_source_alias_race_witness.py",
       "scripts/p189_windows_original_full_b_physical_alias_verdict.py",
       "scripts/p190_windows_handle_bound_source_probe.py",
       "tests/phase8_byok_b_scope_migration.py",
       "tests/phase8_byok_scope_migration.py",
       "tests/test_phase8_byok_b_scope_integrity.py",
    ):
        if git("show",P190+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P191 original source or P190 candidate modified: "+path)
    if len(B.CANDIDATE_SHA256)!=23 or ORIGINAL_B_SELF not in B.ENVELOPE:
        raise RuntimeError("P191 literal immutable historical 23-source B manifest mismatch")
    return {"P191_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P190_parent":P190,"only_three_additive_audit_paths":sorted(NEW),
            "original_product_frozen_tests_historical_P190_unchanged":True}

def authenticate_original_p190(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P191 ephemeral artifact token absent")
    raw=_download_artifact(ARTIFACT,ORIGINAL_ZIP_SHA,token)
    if sha(raw)!=ORIGINAL_ZIP_SHA:
        raise RuntimeError("P191 original P190 ZIP SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(EXPECTED_P190_LOGS)|{LEDGER_NAME}:
            raise RuntimeError("P191 original P190 ZIP CRC or member inventory mismatch")
        for name,(expected,digest) in EXPECTED_P190_LOGS.items():
            rawlog=z.read(name)
            txt=rawlog.decode("utf8","replace").replace("\r\n","\n")
            if (sha(rawlog)!=digest
                or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=[expected]
                or not re.search(r"^OK\s*$",txt,re.M)):
                raise RuntimeError("P191 P190 original Windows log SHA/footer mismatch: "+name)
        record=json.loads(z.read(LEDGER_NAME))
        if (record.get("checkpoint")!="P190"
            or record.get("historical_H")!="HOLD"
            or record.get("production_R")!="HOLD"
            or record.get("complete_native_full_product_regressions")!="0/3"
            or record.get("qualified_independent_security_review")!=REVIEWS
            or record.get("source_before")!=record.get("source_after")
            or record["source_before"].get("P190_HEAD")!=P190
            or record.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P191 authentic P190 original source or H/C/R changed")
    return {"prior_original_artifact":ARTIFACT,
            "original_zip_SHA256":ORIGINAL_ZIP_SHA,
            "P190_original_exact_P189":4,
            "P190_current_win32_handle":10,
            "production_H_R":"HOLD"}

class P191ActualCrossProcessWindowsRaceCases(unittest.TestCase):
    """Each test uses a separate runner-temp source and a separate child process.

    These are bounded deterministic live Windows interleavings, not an exhaustive
    scheduler, privileged attack or formal proof of race freedom.
    """
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P191 real native hosted Windows required")
        cls.sealed=git("show",p190.p189.BHEAD+":"+ORIGINAL_B_SELF)
        if B._digest(ORIGINAL_B_SELF,cls.sealed)!=SOURCE_HASH:
            raise RuntimeError("P191 actual historical sealed B source bytes mismatch")
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="p191-cross-process-",dir=os.environ["RUNNER_TEMP"])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/ORIGINAL_B_SELF
        self.source.parent.mkdir(parents=True,exist_ok=True)
        self.source.write_bytes(self.sealed)
        self.reader=p190.Win32HandleBoundSourceProbe(self.root)
    def child(self,action:str,source:Path,dest:Path|None=None)->dict:
        env=os.environ.copy()
        for key in list(env):
            if key in ("GITHUB_TOKEN","GH_TOKEN","P191_ARCHIVE_TOKEN") or key.endswith(("_API_KEY","_SECRET")):
                env.pop(key,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        p=subprocess.run([sys.executable,"-B","-c",CHILD_SCRIPT,
               action,str(source),str(dest) if dest is not None else ""],
               cwd=self.root,env=env,stdin=subprocess.DEVNULL,
               stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=14,check=False)
        if p.returncode:
            self.fail("P191 external native Windows child process did not complete: "+
                      p.stderr.decode("utf8","replace")[-600:])
        try:
            result=json.loads(p.stdout.decode("utf8","strict").strip())
        except (UnicodeError,ValueError) as exc:
            self.fail("P191 native external child malformed JSON: "+repr(exc))
        if result.get("operation")!=action or result.get("succeeded") not in (True,False):
            self.fail("P191 external Win32 child emitted inconsistent result")
        print("P191_EXTERNAL_PROCESS_"+action.upper()+"="+
              ("SUCCESS" if result["succeeded"] else "OS_DENIED")+
              "|WINERROR="+str(result.get("winerror"))+
              "|ERRNO="+str(result.get("errno")),flush=True)
        return result
    def assert_os_refusal(self,result:dict)->None:
        self.assertFalse(result["succeeded"],"Conflicting Windows child unexpectedly succeeded")
        self.assertIn(result["winerror"],FAIL_CODES,
                      "OS denial must be actual Win32 access/sharing reason")

    def test_01_original_source_handle_identity_baseline_and_literal_B_pin(self):
        self.assertEqual(len(B.CANDIDATE_SHA256),23)
        self.assertEqual(self.reader.read(ORIGINAL_B_SELF),self.sealed)

    def test_02_external_process_attempts_main_file_write_while_exclusive_handle_live(self):
        result=[]
        def competing(_):result.append(self.child("write_source",self.source))
        self.assertEqual(self.reader.read(ORIGINAL_B_SELF,on_open=competing),self.sealed)
        self.assertEqual(len(result),1)
        self.assert_os_refusal(result[0])
        self.assertEqual(self.source.read_bytes(),self.sealed)

    def test_03_external_process_attempts_NTFS_ADS_creation_while_handle_live(self):
        result=[]
        def competing(_):result.append(self.child("create_ads",self.source))
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                   "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(ORIGINAL_B_SELF,on_open=competing)
            self.assertEqual(len(result),1)
            self.assertTrue(result[0]["succeeded"],
               "Native NTFS ADS creation must not be misrepresented as OS refused")
            self.assertIn(":p191_cross_process_stream:$DATA",
                p190.p188.Win32SourceInspectionCandidate.streams(self.source))
            print("P191_ADS_DURING_EXCLUSIVE_SOURCE_HANDLE="+
                  "OS_ALLOWED_AND_POST_HANDLE_SCAN_REFUSED",flush=True)
        finally:
            stream=str(self.source)+":p191_cross_process_stream"
            if ":p191_cross_process_stream:$DATA" in (
               p190.p188.Win32SourceInspectionCandidate.streams(self.source)):
                os.remove(stream)

    def test_04_external_process_attempts_source_leaf_rename_while_handle_live(self):
        target=self.root/"p191_displaced_source"
        result=[]
        def competing(_):result.append(self.child("rename_source",self.source,target))
        outcome=None
        try:
            try:outcome=self.reader.read(ORIGINAL_B_SELF,on_open=competing)
            except p190.SourceDenied as exc:
                outcome="DENIED_"+str(exc)
            self.assertEqual(len(result),1)
            if result[0]["succeeded"]:
                self.assertIsInstance(outcome,str,
                  "Source renamed while open; original candidate must refuse altered file identity")
                self.assertTrue(outcome.startswith("DENIED_"))
            else:
                self.assert_os_refusal(result[0])
                self.assertEqual(outcome,self.sealed)
        finally:
            if target.exists():target.rename(self.source)
        print("P191_LEAF_RENAME_RESULT="+("OS_DENIED" if not result[0]["succeeded"]
              else "READER_DENIED_POST_RENAME"),flush=True)

    def test_05_external_process_attempts_source_deletion_while_handle_live(self):
        result=[]
        def competing(_):result.append(self.child("delete_source",self.source))
        outcome=None
        try:
            try:outcome=self.reader.read(ORIGINAL_B_SELF,on_open=competing)
            except p190.SourceDenied as exc:outcome="DENIED_"+str(exc)
            self.assertEqual(len(result),1)
            if result[0]["succeeded"]:
                self.assertIsInstance(outcome,str)
                self.assertTrue(outcome.startswith("DENIED_"),
                                "Deletion must not produce silent security admission")
            else:
                self.assert_os_refusal(result[0])
                self.assertEqual(outcome,self.sealed)
        finally:
            if not self.source.exists():
                self.source.parent.mkdir(parents=True,exist_ok=True)
                self.source.write_bytes(self.sealed)

    def test_06_external_process_attempts_atomic_replace_of_source_while_exclusive(self):
        replacement=self.root/"p191_wrong_replacement"
        replacement.write_bytes(b"synthetic alternate untrusted file")
        result=[]
        def competing(_):result.append(self.child("replace_source",self.source,replacement))
        outcome=None
        try:
            try:outcome=self.reader.read(ORIGINAL_B_SELF,on_open=competing)
            except p190.SourceDenied as exc:outcome="DENIED_"+str(exc)
            self.assertEqual(len(result),1)
            if result[0]["succeeded"]:
                self.assertIsInstance(outcome,str)
                self.assertTrue(outcome.startswith("DENIED_"),
                                "Successful replace MUST NOT silently admit old opened handle")
            else:
                self.assert_os_refusal(result[0])
                self.assertEqual(outcome,self.sealed)
        finally:
            # Only a runner-owned temporary file, never product/historical worktree.
            if self.source.exists() and self.source.read_bytes()!=self.sealed:
                self.source.write_bytes(self.sealed)

    def test_07_external_process_attempts_link_count_change_while_handle_live(self):
        extra=self.root/"p191_external_hardlink"
        result=[]
        def competing(_):result.append(self.child("create_hardlink",self.source,extra))
        outcome=None
        try:
            try:outcome=self.reader.read(ORIGINAL_B_SELF,on_open=competing)
            except p190.SourceDenied as exc:outcome="DENIED_"+str(exc)
            self.assertEqual(len(result),1)
            if result[0]["succeeded"]:
                self.assertIsInstance(outcome,str)
                self.assertTrue(outcome.startswith("DENIED_"),
                                "Unapproved hardlink count increase MUST be refused")
            else:
                self.assert_os_refusal(result[0])
                self.assertEqual(outcome,self.sealed)
        finally:
            if extra.exists():extra.unlink()

    def test_08_external_process_attempts_parent_dir_rename_and_restore_ABA(self):
        source_parent=self.source.parent
        displaced=self.root/"p191_displaced_source_parent"
        observations=[]
        def competing(_):
            first=self.child("rename_parent",source_parent,displaced)
            observations.append(first)
            if first["succeeded"]:
                second=self.child("rename_parent",displaced,source_parent)
                observations.append(second)
        outcome=None
        try:
            try:outcome=self.reader.read(ORIGINAL_B_SELF,on_open=competing)
            except p190.SourceDenied as exc:outcome="DENIED_"+str(exc)
            self.assertTrue(observations,"P191 child parent mutation was never attempted")
            if not observations[0]["succeeded"]:
                self.assert_os_refusal(observations[0])
                self.assertEqual(outcome,self.sealed)
                evidence="OS_REFUSED_PARENT_RENAME_DURING_OPEN_HANDLE"
            elif len(observations)==2 and observations[1]["succeeded"]:
                # A restored directory may be visually identical at both
                # observational boundaries. Do not label such admission safe.
                evidence=("PARENT_ABA_RESTORED_"+
                          ("READER_ADMITTED_UNPROVEN_ANCESTRY" if outcome==self.sealed
                           else "READER_REFUSED"))
            else:
                self.assertIsInstance(outcome,str)
                self.assertTrue(outcome.startswith("DENIED_"))
                evidence="PARENT_MOVED_AND_READER_REFUSED"
        finally:
            if displaced.exists() and not source_parent.exists():
                displaced.rename(source_parent)
        print("P191_PARENT_ABA_OBSERVATION="+evidence,flush=True)
        self.assertIn(evidence,(
           "OS_REFUSED_PARENT_RENAME_DURING_OPEN_HANDLE",
           "PARENT_ABA_RESTORED_READER_ADMITTED_UNPROVEN_ANCESTRY",
           "PARENT_ABA_RESTORED_READER_REFUSED",
           "PARENT_MOVED_AND_READER_REFUSED",
        ))

    def test_09_external_process_can_write_unrelated_sibling_while_source_locked(self):
        sibling=self.root/"p191_unrelated_sibling"
        result=[]
        def competing(_):
            result.append(self.child("write_sibling",self.source,sibling))
        with self.assertRaisesRegex(p190.SourceDenied,"PARENT_PATH_IDENTITY_DRIFT"):
            self.reader.read(ORIGINAL_B_SELF,on_open=competing)
        self.assertEqual(len(result),1)
        self.assertTrue(result[0]["succeeded"],
                        "Native Windows does not lock unrelated sibling paths")
        self.assertEqual(sibling.read_bytes(),b"P191 independent sibling file")
        self.assertEqual(self.source.read_bytes(),self.sealed)
        print("P191_UNRELATED_SIBLING_FILE_CREATED="+
              "OS_ALLOWED_BUT_P190_PARENT_MTIME_FALSE_REFUSAL",flush=True)

    def test_10_child_stream_creation_after_unlock_refused_on_next_fresh_open(self):
        self.assertEqual(self.reader.read(ORIGINAL_B_SELF),self.sealed)
        result=self.child("create_ads",self.source)
        self.assertTrue(result["succeeded"],"NTFS ADS supported after source HANDLE close")
        self.assertIn(":p191_cross_process_stream:$DATA",
            p190.p188.Win32SourceInspectionCandidate.streams(self.source))
        with self.assertRaisesRegex(p190.SourceDenied,"HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
            self.reader.read(ORIGINAL_B_SELF)
        os.remove(str(self.source)+":p191_cross_process_stream")
        self.assertEqual(self.reader.read(ORIGINAL_B_SELF),self.sealed)

def run_unittest(root:Path,selector:str,output:Path,head:str,count:int,
                 env:dict,timeout:int)->dict:
    if git("rev-parse","HEAD",root=root).decode().strip()!=head:
        raise RuntimeError("P191 original source HEAD mismatch before subprocess")
    cleanenv=dict(env,GITHUB_SHA=head,PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1")
    for key in list(cleanenv):
        if key in ("GITHUB_TOKEN","GH_TOKEN","P191_ARCHIVE_TOKEN") or key.endswith(("_API_KEY","_SECRET")):
            cleanenv.pop(key,None)
    with output.open("wb") as f:
        p=subprocess.run([sys.executable,"-B","-m","unittest","-v",selector],
                         cwd=root,env=cleanenv,stdin=subprocess.DEVNULL,
                         stdout=f,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    raw=output.read_bytes()
    text=raw.decode("utf8","replace").replace("\r\n","\n")
    return {"source_HEAD":head,"native_exit":p.returncode,
            "raw_log":output.name,"raw_SHA256":sha(raw),
            "selected_cases_expected":count,
            "actual_complete_footers":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M),
            "complete_footer_OK":bool(re.search(r"^OK\s*$",text,re.M)),
            "native_observed_child_actions":re.findall(r"P191_EXTERNAL_PROCESS_[^\r\n]+",text,re.M),
            "native_ABA_observation":re.findall(r"^P191_PARENT_ABA_OBSERVATION=[^\r\n]+",text,re.M),
            "native_named_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",text,re.M)}
def demand_pass(result:dict):
    if (result["native_exit"]!=0
        or result["actual_complete_footers"]!=[str(result["selected_cases_expected"])]
        or not result["complete_footer_OK"]):
        raise RuntimeError("P191 native Windows original source specific tests incomplete: "+
         result["raw_log"]+" "+repr(result["native_named_FAIL_ERROR"]))

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p191-win32-cross-process-race"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
       "checkpoint":"P191","historical_H":"HOLD",
       "current_C":"ISOLATED_GENUINE_NATIVE_WINDOWS_CROSS_PROCESS_SOURCE_RACE_WITNESSES_ONLY",
       "production_R":"HOLD","complete_unfiltered_native_windows_full_product_regressions":"0/3",
       "qualified_independent_security_review":REVIEWS,
       "privileged_G0_G6":"OPEN",
       "signed_main_helper_installer_SAC_WDAC_GO":False,
       "original_P189_full_B_NTFS_ADS_gap":"CONFIRMED_AND_NOT_PATCHED",
       "original_P190_handle_probe_integrated":"FALSE",
       "security_ancestry_ABA_proof":"NOT_ESTABLISHED",
       "win32_advanced_process_privilege_filters_and_backup_rights":"NOT_TESTED",
       "filesystem_oplocks_reparse_and_remote_fs":"NOT_EXHAUSTIVE",
       "P135_P175_P178_P179_original_problems":"PRESERVED_UNWAIVED",
    }
    done=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["original_P190_authentic_zip"]=authenticate_original_p190(
            os.environ.get("P191_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        prior=[
          ("P189", "P191_EXACT_P189_ROOT",
             p190.P189,
             "scripts.p189_windows_original_full_b_physical_alias_verdict.P189ActualOriginalFullBPhysicalAliasVerdict",4),
          ("P190", "P191_EXACT_P190_ROOT",P190,
             "scripts.p190_windows_handle_bound_source_probe.P190ActualHandleBoundWin32Tests",10),
        ]
        ledger["old_exact_source_native_tests"]={}
        for name,rootvar,head,selector,n in prior:
            path=Path(os.environ[rootvar])
            if not path.is_dir() or path.resolve()==ROOT.resolve():
                raise RuntimeError("P191 original exact "+name+" clone absent")
            result=run_unittest(path,selector,
               out/("p191_original_exact_"+name+"_native_Windows_"+str(n)+".log"),
               head,n,env,170)
            ledger["old_exact_source_native_tests"][name]=result
            demand_pass(result)
        new=run_unittest(ROOT,
           "scripts.p191_windows_cross_process_source_race_witness.P191ActualCrossProcessWindowsRaceCases",
           out/"p191_current_native_external_process_source_ADS_10.log",
           os.environ["GITHUB_SHA"],10,env,190)
        ledger["P191_actual_cross_process_Windows"]=new
        demand_pass(new)
        if len(new["native_observed_child_actions"])<9 or len(new["native_ABA_observation"])!=1:
            raise RuntimeError("P191 external real Win32 child process or ABA observed evidence missing")
        after=custody()
        ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P191 original source ancestry drift during Windows evidence")
        done=True
        print("P191_OLD_EXACT_P189_4_P190_10=14/14_NATIVE_WIN32_SELECTED_PASS",flush=True)
        print("P191_CURRENT_EXTERNAL_PROCESS_REAL_WIN32_10=10/10_NATIVE_PASS",flush=True)
        print("P191_ORIGINAL_FULL_B_ADS_GAP=UNMITIGATED",flush=True)
        print("P191_ABA_RACE_FREE_PROOF=NOT_ESTABLISHED",flush=True)
        print("P191_SECURITY_REVIEW=OPEN|FULL_PRODUCT_REGRESSIONS=0/3|RELEASE=HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P191_CROSS_PROCESS_NATIVE_WIN32_GOVERNANCE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=done
        (out/"p191_original_source_bound_cross_process_ABA_HCR_ledger.json").write_text(
          json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if done else 1

if __name__=="__main__":
    raise SystemExit(main())
