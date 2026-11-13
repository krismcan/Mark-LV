"""P192 stable directory HANDLE identity and bounded ADS/alias interleavings.

Purely audit-only, separate from frozen historical BYOK-B and product. P190
used mutable ancestor mtime; this experimental candidate holds directory
handles with FILE_SHARE_DELETE omitted and compares volume/FileId/attributes.
No formal claim of atomic rooted CreateFileW or stream/link ABA resistance.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
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
from unittest import mock
import zipfile

from scripts import p191_windows_cross_process_source_race_witness as p191
from scripts import p190_windows_handle_bound_source_probe as p190
from scripts import p188_windows_physical_source_alias_race_witness as p188
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P191="6c759056b380626991e86e2543fac855da8fc5c9"
BRANCH="byok-c1-p192-stable-parent-handle-identity-ads-race-20261113"
NEW={
  "scripts/p192_windows_stable_parent_handle_identity.py",
  "docs/byok-c1-p192-stable-parent-handle-race-review.md",
  ".github/workflows/p192-windows-stable-parent-handle-race.yml",
}
ARTIFACT=14037690093
ARCHIVE_SHA="91AA20D52EC8DD713C422548BF2C32637321B041D8815D40F943DAEF56E92A00"
ORIGINAL_LOGS={
 "p191_original_exact_P189_native_Windows_4.log":
    ("4","F00E31D1FCE01CD32D49E986A14556497505DAE6B3D6508346AAC6BFF26C0D66"),
 "p191_original_exact_P190_native_Windows_10.log":
    ("10","6F95249C112635923E92E3B6B6726E17B4F242BAAE2A010F538C1CC722F2E44B"),
 "p191_current_native_external_process_source_ADS_10.log":
    ("10","A13DA55003F534A21C34DE20F0A600E426E118FAEC459D03078F9E441AC40022"),
}
OLD_LEDGER="p191_original_source_bound_cross_process_ABA_HCR_ledger.json"
REVIEWS=p191.REVIEWS
REL=B.SELF
SEAL=B.CANDIDATE_SHA256[REL]
FILE_READ_ATTRIBUTES=0x80
FILE_FLAG_BACKUP_SEMANTICS=0x02000000
FILE_ATTRIBUTE_DIRECTORY=0x10
WINERROR_SHARING_OR_ACCESS={5,32}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest().upper()

def git(*args:str,root:Path=ROOT)->bytes:
    p=subprocess.run(["git","-C",str(root),*args],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=False)
    if p.returncode:
        raise RuntimeError("P192 original Git native exit="+str(p.returncode)+" "+repr(args)+
                           " stderr="+p.stderr.decode("utf8","replace")[-600:])
    return p.stdout

def custody()->dict:
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",P191,"HEAD").decode().strip()!=P191
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P192 requires clean authenticated original Win32 source")
    if set(git("diff","--name-only",P191,"HEAD").decode().splitlines())!=NEW:
        raise RuntimeError("P192 only three new audit-only paths")
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P191+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P192 frozen product and original tests modified")
    for path in (
      "scripts/p187_windows_live_byok_b_equivalence.py",
      "scripts/p188_windows_physical_source_alias_race_witness.py",
      "scripts/p189_windows_original_full_b_physical_alias_verdict.py",
      "scripts/p190_windows_handle_bound_source_probe.py",
      "scripts/p191_windows_cross_process_source_race_witness.py",
      "tests/phase8_byok_b_scope_migration.py",
      "tests/phase8_byok_scope_migration.py",
      "tests/test_phase8_byok_b_scope_integrity.py",
    ):
        if git("show",P191+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P192 previous test/product or historical verifier drift: "+path)
    if len(B.CANDIDATE_SHA256)!=23 or REL not in B.ENVELOPE:
        raise RuntimeError("P192 original literal B source envelope changed")
    return {"P192_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P191_parent":P191,
            "three_only_review_additions":sorted(NEW),
            "unchanged_original_historical_product_frozen_tests":True}

def authenticate_p191(token:str)->dict:
    if len(token)<8:raise RuntimeError("P192 original P191 download auth unavailable")
    data=_download_artifact(ARTIFACT,ARCHIVE_SHA,token)
    if sha(data)!=ARCHIVE_SHA:
        raise RuntimeError("P192 original P191 artifact bytes altered")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(ORIGINAL_LOGS)|{OLD_LEDGER}:
            raise RuntimeError("P192 original P191 ZIP CRC or inventory changed")
        for name,(n,digest) in ORIGINAL_LOGS.items():
            raw=z.read(name)
            txt=raw.decode("utf8","replace").replace("\r\n","\n")
            if (sha(raw)!=digest or
                re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=[n] or
                not re.search(r"^OK\s*$",txt,re.M)):
                raise RuntimeError("P192 original P191 exact source log checksum/footer wrong: "+name)
        record=json.loads(z.read(OLD_LEDGER))
        if (record.get("checkpoint")!="P191"
            or record.get("historical_H")!="HOLD"
            or record.get("production_R")!="HOLD"
            or record.get("complete_unfiltered_native_windows_full_product_regressions")!="0/3"
            or record.get("qualified_independent_security_review")!=REVIEWS
            or record.get("source_before")!=record.get("source_after")
            or record["source_before"].get("P191_HEAD")!=P191
            or record.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P192 prior original P191 H/C/R custody drift")
    return {"artifact":ARTIFACT,"ZIP_SHA256":ARCHIVE_SHA,
            "native_source_bound_tests":[4,10,10],"release":"HOLD"}

class StableParentHandleReader(p190.Win32HandleBoundSourceProbe):
    """Experimental directory HANDLE pinning and stable FileId comparison.

    Open each parent directory with FILE_FLAG_BACKUP_SEMANTICS and
    FILE_FLAG_OPEN_REPARSE_POINT, FILE_READ_ATTRIBUTES, share READ|WRITE but
    NOT DELETE. Keep all parent handles open until leaf FileId, FileStreamInfo,
    pinned B SHA and post-read handle identities have been reverified.

    Unlike P190, do not treat ordinary directory mtime as a source identity.
    Still NOT a trusted relative-open rooted Win32 transaction.
    """
    def _open_parent(self,path:Path):
        flags=p190.FILE_FLAG_OPEN_REPARSE_POINT|FILE_FLAG_BACKUP_SEMANTICS
        h=self.api.CreateFileW(str(path),FILE_READ_ATTRIBUTES,
            p190.FILE_SHARE_READ|p190.FILE_SHARE_WRITE,
            None,p190.OPEN_EXISTING,flags,None)
        if h is None or h==p190.INVALID_HANDLE_VALUE:
            raise p190.SourceDenied("PARENT_HANDLE_OPEN_DENIED_WIN32_"+
                                    str(ctypes.get_last_error()))
        return h

    def _parent_snapshot(self,handle,path:Path)->tuple:
        info=self._info(handle,18,p190.FileIdInfo)
        standard=self._info(handle,1,p190.FileStandardInfo)
        attrs=self._info(handle,9,p190.FileAttributeTagInfo)
        if (not standard.directory or
            not (attrs.attributes & FILE_ATTRIBUTE_DIRECTORY) or
            attrs.attributes & p190.FILE_ATTRIBUTE_REPARSE_POINT or
            standard.delete_pending):
            raise p190.SourceDenied("HELD_PARENT_REPARSE_OR_NON_DIRECTORY")
        buffer=ctypes.create_unicode_buffer(32768)
        n=self.api.GetFinalPathNameByHandleW(handle,buffer,len(buffer),0)
        if not n or n>=len(buffer):
            raise p190.SourceDenied("HELD_PARENT_FINAL_PATH_UNVERIFIABLE")
        norm=self._normal_handle_path(buffer.value)
        if norm!=self._normal_handle_path(str(path)):
            raise p190.SourceDenied("HELD_PARENT_FINAL_PATH_MISMATCH")
        # mtime intentionally excluded. Directory FileId is stable if sibling
        # files are created, and links/streams on the leaf are separately checked.
        return (int(info.volume),bytes(info.id),int(attrs.attributes),norm)

    def _parent_paths(self,full:Path)->tuple[Path,...]:
        parts=full.relative_to(self.root).parts
        paths=[self.root]
        for part in parts[:-1]:
            paths.append(paths[-1]/part)
        return tuple(paths)

    def read(self,path:str,*,on_open=None)->bytes:
        if (path not in B.CANDIDATE_SHA256
           or not p188.previous.previous.canonical_legacy_path(path)
           or ":" in path or "\\" in path):
            raise p190.SourceDenied("UNAPPROVED_OR_NONCANONICAL_B_SOURCE_PATH")
        full=self.root/path
        parents=self._parent_paths(full)
        opened=[]
        leaf=None
        try:
            for directory in parents:
                h=self._open_parent(directory)
                opened.append((directory,h,self._parent_snapshot(h,directory)))
            leaf=self._open(full)
            ident=self._handle_identity(leaf,full)
            if ident[3]>self.max_bytes:
                raise p190.SourceDenied("SOURCE_SIZE_LIMIT")
            if on_open is not None:
                on_open(full)
            raw=self._read_handle(leaf)
            if B._digest(path,raw)!=B.CANDIDATE_SHA256[path]:
                raise p190.SourceDenied("ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH")
            if ident!=self._handle_identity(leaf,full):
                raise p190.SourceDenied("HANDLE_ID_OR_SOURCE_METADATA_DRIFT")
            for directory,h,original in opened:
                if self._parent_snapshot(h,directory)!=original:
                    raise p190.SourceDenied("HELD_PARENT_FILEID_OR_ATTRIBUTE_DRIFT")
            return raw
        finally:
            if leaf is not None:
                self.api.CloseHandle(leaf)
            for _,h,_ in reversed(opened):
                self.api.CloseHandle(h)

class P192ActualStableParentWin32Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P192 genuine hosted native Windows required")
        cls.sealed=git("show",p190.p189.BHEAD+":"+REL)
        if B._digest(REL,cls.sealed)!=SEAL:
            raise RuntimeError("P192 original sealed B source authority mismatch")
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="p192-held-parents-",dir=os.environ["RUNNER_TEMP"])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/REL
        self.source.parent.mkdir(parents=True,exist_ok=True)
        self.source.write_bytes(self.sealed)
        self.reader=StableParentHandleReader(self.root)

    def child(self,action:str,source:Path,destination:Path|None=None)->dict:
        env=os.environ.copy()
        for key in list(env):
            if key in ("GITHUB_TOKEN","GH_TOKEN","P192_ARCHIVE_TOKEN") or key.endswith(("_API_KEY","_SECRET")):
                env.pop(key,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        p=subprocess.run([sys.executable,"-B","-c",p191.CHILD_SCRIPT,
            action,str(source),str(destination) if destination is not None else ""],
            cwd=self.root,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=15,check=False)
        if p.returncode:
            self.fail("P192 native cross-process child failed before result: "+
                      p.stderr.decode("utf8","replace")[-700:])
        try:
            result=json.loads(p.stdout.decode("utf8","strict").strip())
        except (UnicodeError,ValueError) as exc:
            self.fail("P192 native cross-process child malformed result: "+repr(exc))
        self.assertEqual(result.get("operation"),action)
        self.assertIs(type(result.get("succeeded")),bool)
        print("P192_CHILD_"+action.upper()+"="+
              ("ALLOWED" if result["succeeded"] else "REFUSED")+
              "|WINERROR="+str(result.get("winerror")),flush=True)
        return result

    def test_01_original_sealed_B_valid_source_accepted_with_held_directory_ids(self):
        self.assertEqual(len(B.CANDIDATE_SHA256),23)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_02_external_sibling_file_creation_no_false_parent_mtime_denial(self):
        result=[]
        sibling=self.root/"p192_other_sibling"
        def concurrent(_):
            result.append(self.child("write_sibling",self.source,sibling))
        self.assertEqual(self.reader.read(REL,on_open=concurrent),self.sealed)
        self.assertTrue(result[0]["succeeded"])
        self.assertEqual(sibling.read_bytes(),b"P191 independent sibling file")
        print("P192_ORDINARY_SIBLING=ALLOWED_WITH_HELD_PARENT_FILEID",flush=True)

    def test_03_external_sibling_inside_held_tests_directory_also_allowed(self):
        result=[]
        sibling=self.source.parent/"p192_other_test_sibling"
        def concurrent(_):
            result.append(self.child("write_sibling",self.source,sibling))
        self.assertEqual(self.reader.read(REL,on_open=concurrent),self.sealed)
        self.assertTrue(result[0]["succeeded"])
        self.assertEqual(sibling.read_bytes(),b"P191 independent sibling file")
        print("P192_HELD_ANCESTOR_SIBLING=ALLOWED_WITH_STABLE_FILEID",flush=True)

    def test_04_external_NTFS_ADS_creation_mid_handle_refused_on_postscan(self):
        attempted=[]
        def concurrent(_):
            attempted.append(self.child("create_ads",self.source))
        stream=str(self.source)+":p191_cross_process_stream"
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                  "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(REL,on_open=concurrent)
            self.assertTrue(attempted[0]["succeeded"],
                "P192 must preserve actual Windows ADS creation, not fabricate OS refusal")
            self.assertIn(":p191_cross_process_stream:$DATA",
                p188.Win32SourceInspectionCandidate.streams(self.source))
        finally:
            if ":p191_cross_process_stream:$DATA" in (
                 p188.Win32SourceInspectionCandidate.streams(self.source)):
                os.remove(stream)

    def test_05_external_hardlink_creation_refused_by_posthandle_link_count(self):
        attempted=[]
        extra=self.root/"p192_other_hardlink"
        def concurrent(_):
            attempted.append(self.child("create_hardlink",self.source,extra))
        try:
            with self.assertRaisesRegex(p190.SourceDenied,"HARDLINK_OR_LINKCOUNT_INVALID"):
                self.reader.read(REL,on_open=concurrent)
            self.assertTrue(attempted[0]["succeeded"],
                "P192 must record actual Win32 hardlink creation while leaf HANDLE open")
            self.assertEqual(self.source.stat().st_nlink,2)
        finally:
            if extra.exists():extra.unlink()

    def test_06_external_parent_dir_rename_denied_while_held_ancestor_handles(self):
        attempts=[]
        parent=self.source.parent
        target=self.root/"p192_displaced_tests_parent"
        def concurrent(_):
            attempts.append(self.child("rename_parent",parent,target))
        self.assertEqual(self.reader.read(REL,on_open=concurrent),self.sealed)
        self.assertEqual(len(attempts),1)
        self.assertFalse(attempts[0]["succeeded"])
        self.assertIn(attempts[0]["winerror"],WINERROR_SHARING_OR_ACCESS)
        self.assertFalse(target.exists())
        print("P192_PARENT_RENAME_DURING_HELD_ANCESTRY=OS_DENIED",flush=True)

    def test_07_external_leaf_replace_denied_or_reader_refuses_changed_leaf(self):
        replacement=self.root/"p192_untrusted_replacement"
        replacement.write_bytes(b"P192 unapproved replacement")
        outcomes=[]
        def concurrent(_):
            outcomes.append(self.child("replace_source",self.source,replacement))
        try:
            try:
                result=self.reader.read(REL,on_open=concurrent)
            except p190.SourceDenied as exc:
                result="READER_DENIED_"+str(exc)
            self.assertEqual(len(outcomes),1)
            if outcomes[0]["succeeded"]:
                self.assertIsInstance(result,str)
                self.assertTrue(result.startswith("READER_DENIED_"),
                  "P192 must not silently admit replaced source")
            else:
                self.assertIn(outcomes[0]["winerror"],WINERROR_SHARING_OR_ACCESS)
                self.assertEqual(result,self.sealed)
        finally:
            if self.source.exists() and self.source.read_bytes()!=self.sealed:
                self.source.write_bytes(self.sealed)

    def test_08_existing_ntfs_junction_parent_rejected_as_reparse_handle(self):
        directory=self.source.parent
        real=self.root/"p192_separate_real_tests_dir"
        directory.rename(real)
        try:
            p188.make_junction(directory,real)
            with self.assertRaisesRegex(p190.SourceDenied,
                       "HELD_PARENT_REPARSE_OR_NON_DIRECTORY"):
                self.reader.read(REL)
        finally:
            if directory.is_junction():directory.rmdir()
            if real.exists() and not directory.exists():real.rename(directory)

    def test_09_wrong_original_B_pin_refused_after_held_parent_open(self):
        self.source.write_bytes(self.sealed+b"\n# P192 wrong original B byte")
        with self.assertRaisesRegex(p190.SourceDenied,
                       "ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH"):
            self.reader.read(REL)

    def test_10_preexisting_named_ntfs_ads_refused_from_same_leaf_handle(self):
        stream=str(self.source)+":p192_named_stream"
        with open(stream,"wb") as f:
            f.write(b"nonexecuting P192 test data")
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                        "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(REL)
        finally:
            os.remove(stream)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_11_parent_metadata_error_refuses_closed_and_releases_all_handles(self):
        with mock.patch.object(self.reader,"_parent_snapshot",
                     side_effect=p190.SourceDenied("SYNTHETIC_PARENT_METADATA_UNAVAILABLE")):
            with self.assertRaisesRegex(p190.SourceDenied,
                         "SYNTHETIC_PARENT_METADATA_UNAVAILABLE"):
                self.reader.read(REL)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_12_after_security_refusal_unrelated_source_is_not_locked_forever(self):
        self.source.write_bytes(self.sealed+b"not approved")
        with self.assertRaisesRegex(p190.SourceDenied,
                             "ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH"):
            self.reader.read(REL)
        self.source.write_bytes(self.sealed)
        sibling=self.root/"p192_after_denial_file"
        self.assertTrue(self.child("write_sibling",self.source,sibling)["succeeded"])
        self.assertEqual(self.reader.read(REL),self.sealed)

def native_unittest(path:Path,selector:str,out:Path,head:str,n:int,
                    env:dict,timeout:int)->dict:
    if not path.is_dir() or git("rev-parse","HEAD",root=path).decode().strip()!=head:
        raise RuntimeError("P192 exact native source identity mismatch for "+selector)
    runenv=dict(env,GITHUB_SHA=head,PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1")
    for key in list(runenv):
        if key in ("GITHUB_TOKEN","GH_TOKEN","P192_ARCHIVE_TOKEN") or key.endswith(("_API_KEY","_SECRET")):
            runenv.pop(key,None)
    with out.open("wb") as file:
        proc=subprocess.run([sys.executable,"-B","-m","unittest","-v",selector],
                cwd=path,env=runenv,stdin=subprocess.DEVNULL,stdout=file,
                stderr=subprocess.STDOUT,timeout=timeout,check=False)
    raw=out.read_bytes()
    txt=raw.decode("utf8","replace").replace("\r\n","\n")
    return {"source_HEAD":head,"native_exit":proc.returncode,
            "raw_log":out.name,"SHA256":sha(raw),
            "expected":n,"actual_footers":re.findall(
              r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
            "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
            "scenario_markers":re.findall(r"P192_(?:CHILD|ORDINARY|HELD|PARENT)_[^\r\n]+",txt),
            "named_failures":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}
def require_native_pass(r:dict):
    if (r["native_exit"]!=0 or r["actual_footers"]!=[str(r["expected"])]
        or not r["complete_OK"]):
        raise RuntimeError("P192 genuine Windows failure "+r["raw_log"]+
                           " "+repr(r["named_failures"]))

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p192-held-parent-security"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
       "checkpoint":"P192","historical_H":"HOLD",
       "current_C":"ISOLATED_STABLE_PARENT_HANDLE_IDENTITY_WINDOWS_EXPERIMENT",
       "production_R":"HOLD","full_product_unfiltered_native_windows_regressions":"0/3",
       "qualified_external_security_reviewer_decisions":REVIEWS,
       "privileged_G0_G6":"OPEN","signed_main_helper_installer_SAC_WDAC_GO":False,
       "P189_historical_full_B_ADS_gap":"CONFIRMED_UNPATCHED",
       "P190_original_frozen_handle_reader_changed":False,
       "P191_parent_mtime_false_denial_in_product":"EXPERIMENTAL_P190_DESIGN_ONLY",
       "relative_open_trusted_root_atomic_ancestor_proof":"NOT_ESTABLISHED",
       "ADS_and_link_creation_removal_ABA_proof":"NOT_ESTABLISHED",
       "qualified_review_and_prod_integration":"NOT_DONE",
       "P135_P175_P178_P179_full_product_failures":"UNWAIVED",
    }
    success=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["original_P191_authentic"]=authenticate_p191(os.environ.get("P192_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        original=[
          ("P189","P192_ORIGINAL_P189_ROOT",p190.P189,
           "scripts.p189_windows_original_full_b_physical_alias_verdict.P189ActualOriginalFullBPhysicalAliasVerdict",4),
          ("P190","P192_ORIGINAL_P190_ROOT",p191.P190,
           "scripts.p190_windows_handle_bound_source_probe.P190ActualHandleBoundWin32Tests",10),
          ("P191","P192_ORIGINAL_P191_ROOT",P191,
           "scripts.p191_windows_cross_process_source_race_witness.P191ActualCrossProcessWindowsRaceCases",10),
        ]
        ledger["true_original_source_bound_tests"]={}
        for name,environment,head,selector,n in original:
            path=Path(os.environ[environment])
            if path.resolve()==ROOT.resolve():
                raise RuntimeError("P192 original and active source isolation failed")
            record=native_unittest(path,selector,out/(
               "p192_original_exact_"+name+"_windows_"+str(n)+".log"),head,n,env,180)
            ledger["true_original_source_bound_tests"][name]=record
            require_native_pass(record)
        current=native_unittest(ROOT,
          "scripts.p192_windows_stable_parent_handle_identity.P192ActualStableParentWin32Tests",
          out/"p192_current_true_windows_parent_FileId_12.log",
          os.environ["GITHUB_SHA"],12,env,140)
        ledger["current_native_source"]=current
        require_native_pass(current)
        if len(current["scenario_markers"])<6:
            raise RuntimeError("P192 missing genuine expected Windows child/parent event logs")
        after=custody()
        ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P192 exact original Git source drift")
        success=True
        print("P192_ORIGINAL_P189_4_P190_10_P191_10=24/24_EXACT_SOURCE_NATIVE_PASS",flush=True)
        print("P192_CURRENT_STABLE_PARENT_HANDLE_WIN32=12/12_NATIVE_PASS",flush=True)
        print("P192_SELECTED_SOURCE_BOUND_WINDOWS=36/36_NOT_FULL_PRODUCT",flush=True)
        print("P192_SIBLING_AVAILABILITY_FALSE_REFUSAL=EXPERIMENTAL_CANDIDATE_REMEDIED",flush=True)
        print("P192_ADS_HARDLINK_RACE_POST_READ_REFUSAL=OBSERVED_NOT_PROOF",flush=True)
        print("P192_ATOMIC_ROOTED_RELATIVE_OPENS_AND_ABA=NOT_PROVEN",flush=True)
        print("P192_EXTERNAL_REVIEW=OPEN|FULL_PRODUCT=0/3|PRODUCTION_RELEASE=HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P192_GENUINE_WINDOWS_STABLE_PARENT_EVIDENCE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=success
        (out/"p192_stable_parent_handle_source_HCR_ledger.json").write_text(
           json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if success else 1

if __name__=="__main__":
    raise SystemExit(main())
