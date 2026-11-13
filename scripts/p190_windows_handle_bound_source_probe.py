"""P190: isolated Win32 handle-bound B source and alternate-stream experiment.

No original historical or current production verifier integration. Only real
hosted Windows temporary source fixtures + immutable authentic P189 evidence.
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
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

from scripts import p189_windows_original_full_b_physical_alias_verdict as p189
from scripts import p188_windows_physical_source_alias_race_witness as p188
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P189="75a312cce7e0231b41b2920c45c3c002bd59f120"
BRANCH="byok-c1-p190-ntfs-handle-bound-source-inspection-20261113"
NEW={
  "scripts/p190_windows_handle_bound_source_probe.py",
  "docs/byok-c1-p190-handle-bound-ADS-source-threat-review.md",
  ".github/workflows/p190-windows-handle-bound-ADS-source.yml",
}
ARTIFACT=14029676768
ARCHIVE_SHA="54AECDB6A275155D70881761AF4B1ABA602398E8D6DC0E67898DDB1D44447D71"
P189_LOGS={
  "p189_original_exact_P188_native_Windows_9.log":
    ("9","4EA389147C03ABE13DDAF1C98C831BE13E465E9237E7462B90C0C22E51BAA8D5"),
  "p189_current_true_original_full_B_physical_alias_4.log":
    ("4","AD7F0F73AB387F539F1CC687D161B3A8BBF08490035C848A2962BCEBB0D4BB30"),
}
P189_LEDGER="p189_original_full_B_physical_alias_HCR_custody_ledger.json"
REVIEWS=p189.REVIEWS
REL=B.SELF
SEAL=B.CANDIDATE_SHA256[REL]
GENERIC_READ=0x80000000
GENERIC_WRITE=0x40000000
FILE_SHARE_READ=1
FILE_SHARE_WRITE=2
FILE_SHARE_DELETE=4
OPEN_EXISTING=3
FILE_FLAG_OPEN_REPARSE_POINT=0x00200000
FILE_ATTRIBUTE_REPARSE_POINT=0x400
ERROR_SHARING_VIOLATION=32
INVALID_HANDLE_VALUE=ctypes.c_void_p(-1).value

class SourceDenied(RuntimeError):
    pass

class FileIdInfo(ctypes.Structure):
    _fields_=[("volume",ctypes.c_ulonglong),("id",(ctypes.c_ubyte*16))]
class FileStandardInfo(ctypes.Structure):
    _fields_=[("allocation",ctypes.c_longlong),("size",ctypes.c_longlong),
              ("links",wintypes.DWORD),("delete_pending",wintypes.BOOLEAN),
              ("directory",wintypes.BOOLEAN)]
class FileAttributeTagInfo(ctypes.Structure):
    _fields_=[("attributes",wintypes.DWORD),("tag",wintypes.DWORD)]

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str,root:Path=ROOT)->bytes:
    r=subprocess.run(["git","-C",str(root),*args],stdin=subprocess.DEVNULL,
      stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=False)
    if r.returncode:
        raise RuntimeError("P190 Git native exit "+str(r.returncode)+" for "+repr(args)
                           +" "+r.stderr.decode("utf8","replace")[-500:])
    return r.stdout

def custody()->dict:
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
       or os.environ.get("RUNNER_OS")!="Windows"
       or os.environ.get("GITHUB_EVENT_NAME")!="push"
       or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
       or os.environ.get("GITHUB_REF_NAME")!=BRANCH
       or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
       or git("branch","--show-current").decode().strip()!=BRANCH
       or git("merge-base",P189,"HEAD").decode().strip()!=P189
       or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P190 actual clean Windows source/branch admission failed")
    if set(git("diff","--name-only",P189,"HEAD").decode().splitlines())!=NEW:
        raise RuntimeError("P190 only three new audit paths permitted")
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P189+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P190 original frozen product/test source changed")
    for path in (
       "scripts/p187_windows_live_byok_b_equivalence.py",
       "scripts/p188_windows_physical_source_alias_race_witness.py",
       "scripts/p189_windows_original_full_b_physical_alias_verdict.py",
       "tests/phase8_byok_b_scope_migration.py",
       "tests/phase8_byok_scope_migration.py",
       "tests/test_phase8_byok_b_scope_integrity.py",
    ):
        if git("show",P189+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P190 original security/previous review source altered: "+path)
    if len(B.CANDIDATE_SHA256)!=23 or REL not in B.ENVELOPE:
        raise RuntimeError("P190 original literal B 23-source envelope altered")
    return {"P190_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P189_parent":P189,
            "original_product_tests_prior_witnesses_untouched":True,
            "only_three_new_audit_paths":sorted(NEW)}

def authenticate_p189(token:str)->dict:
    if len(token)<8:raise RuntimeError("P190 ephemeral original P189 artifact token absent")
    raw=_download_artifact(ARTIFACT,ARCHIVE_SHA,token)
    if sha(raw)!=ARCHIVE_SHA:
        raise RuntimeError("P190 original P189 ZIP SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(P189_LOGS)|{P189_LEDGER}:
            raise RuntimeError("P190 original P189 ZIP CRC/member inventory invalid")
        for name,(n,digest) in P189_LOGS.items():
            content=z.read(name)
            txt=content.decode("utf8","replace").replace("\r\n","\n")
            if (sha(content)!=digest or
                re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=[n] or
                not re.search(r"^OK\s*$",txt,re.M)):
                raise RuntimeError("P190 original P189 source-specific SHA/footer invalid "+name)
        ledger=json.loads(z.read(P189_LEDGER))
        if (ledger.get("checkpoint")!="P189"
            or ledger.get("historical_H")!="HOLD"
            or ledger.get("production_R")!="HOLD"
            or ledger.get("full_product_native_windows_regressions")!="0/3"
            or ledger.get("qualified_external_seven_reviews")!=REVIEWS
            or ledger.get("source_before")!=ledger.get("source_after")
            or ledger["source_before"].get("P189_HEAD")!=P189
            or ledger.get("experimental_original_full_B_physical_verdict_complete_NOT_release") is not True):
            raise RuntimeError("P190 original P189 H/C/R provenance mismatch")
    return {"original_artifact":ARTIFACT,"original_ZIP_SHA256":ARCHIVE_SHA,
            "original_P189_native_cases":[9,4],"original_release":"HOLD"}

class Win32HandleBoundSourceProbe:
    """Separate fail-closed prototype: real single HANDLE metadata + read.

    Exclusive sharing plus FILE_FLAG_OPEN_REPARSE_POINT, FileIdInfo,
    FileStandardInfo, FileAttributeTagInfo, FileStreamInfo, ReadFile on the
    same HANDLE. Parent path is checked separately, NOT race-proof pinned.
    Does not replace original full B/Phase10 source admission.
    """
    def __init__(self,root:Path,max_bytes:int=1048576):
        if os.name!="nt":raise SourceDenied("WIN32_ONLY")
        self.root=root
        self.max_bytes=max_bytes
        self.api=ctypes.WinDLL("kernel32",use_last_error=True)
        k=self.api
        k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,
                                ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,
                                wintypes.HANDLE]
        k.CreateFileW.restype=wintypes.HANDLE
        k.CloseHandle.argtypes=[wintypes.HANDLE]
        k.CloseHandle.restype=wintypes.BOOL
        k.GetFileInformationByHandleEx.argtypes=[wintypes.HANDLE,wintypes.DWORD,
                                                  ctypes.c_void_p,wintypes.DWORD]
        k.GetFileInformationByHandleEx.restype=wintypes.BOOL
        k.GetFinalPathNameByHandleW.argtypes=[wintypes.HANDLE,wintypes.LPWSTR,
                                               wintypes.DWORD,wintypes.DWORD]
        k.GetFinalPathNameByHandleW.restype=wintypes.DWORD
        k.ReadFile.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD,
                             ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]
        k.ReadFile.restype=wintypes.BOOL

    def _open(self,path:Path,desired:int=GENERIC_READ,sharing:int=0):
        h=self.api.CreateFileW(str(path),desired,sharing,None,OPEN_EXISTING,
                                FILE_FLAG_OPEN_REPARSE_POINT,None)
        if h is None or h==INVALID_HANDLE_VALUE:
            raise SourceDenied("EXCLUSIVE_OPEN_DENIED_WIN32_"+str(ctypes.get_last_error()))
        return h

    def _info(self,handle,kind:int,cls):
        value=cls()
        if not self.api.GetFileInformationByHandleEx(
                handle,kind,ctypes.byref(value),ctypes.sizeof(value)):
            raise SourceDenied("HANDLE_METADATA_UNAVAILABLE_CLASS_"+str(kind)+
                               "_WIN32_"+str(ctypes.get_last_error()))
        return value

    def _streams(self,handle)->tuple[str,...]:
        # FILE_STREAM_INFO variable-length 8-byte-aligned records, bounded.
        raw=ctypes.create_string_buffer(65536)
        if not self.api.GetFileInformationByHandleEx(handle,7,raw,ctypes.sizeof(raw)):
            raise SourceDenied("HANDLE_STREAM_ENUMERATION_FAILED_WIN32_"+
                               str(ctypes.get_last_error()))
        b=raw.raw
        pos=0
        names=[]
        for _ in range(128):
            if pos+24>len(b):
                raise SourceDenied("MALFORMED_STREAM_RECORD")
            step=int.from_bytes(b[pos:pos+4],"little")
            n=int.from_bytes(b[pos+4:pos+8],"little")
            if n==0 or n%2 or pos+24+n>len(b):
                raise SourceDenied("MALFORMED_STREAM_NAME")
            try:
                name=b[pos+24:pos+24+n].decode("utf-16-le","strict")
            except UnicodeDecodeError as exc:
                raise SourceDenied("INVALID_STREAM_NAME_UTF16") from exc
            if name in names:
                raise SourceDenied("DUPLICATED_STREAM_RECORD")
            names.append(name)
            if step==0:
                return tuple(names)
            if step<24+n or step%8 or pos+step<=pos:
                raise SourceDenied("MALFORMED_STREAM_NEXT_OFFSET")
            pos+=step
        raise SourceDenied("TOO_MANY_STREAM_RECORDS")

    def _parent_identity(self,path:Path)->tuple:
        # Observational only: an attacker may race/revert between lstat calls.
        pieces=path.relative_to(self.root).parts
        node=self.root
        identity=[]
        for name in ("",*pieces[:-1]):
            if name:node=node/name
            info=node.lstat()
            attributes=getattr(info,"st_file_attributes",0)
            if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or attributes & FILE_ATTRIBUTE_REPARSE_POINT):
                raise SourceDenied("PARENT_REPARSE_OR_NON_DIRECTORY")
            identity.append((info.st_dev,info.st_ino,info.st_mtime_ns,
                             attributes))
        return tuple(identity)

    @staticmethod
    def _normal_handle_path(path:str)->str:
        if path.startswith("\\\\?\\UNC\\"):
            path="\\\\"+path[8:]
        elif path.startswith("\\\\?\\"):
            path=path[4:]
        return os.path.normcase(os.path.normpath(os.path.abspath(path)))

    def _handle_identity(self,handle,path:Path)->tuple:
        fileid=self._info(handle,18,FileIdInfo)
        standard=self._info(handle,1,FileStandardInfo)
        attr=self._info(handle,9,FileAttributeTagInfo)
        if standard.directory or standard.delete_pending:
            raise SourceDenied("NONREGULAR_OR_DELETING_HANDLE")
        if standard.links!=1:
            raise SourceDenied("HARDLINK_OR_LINKCOUNT_INVALID")
        if attr.attributes & FILE_ATTRIBUTE_REPARSE_POINT:
            raise SourceDenied("LEAF_REPARSE_HANDLE")
        buf=ctypes.create_unicode_buffer(32768)
        n=self.api.GetFinalPathNameByHandleW(handle,buf,len(buf),0)
        if not n or n>=len(buf):
            raise SourceDenied("UNVERIFIABLE_HANDLE_FINAL_PATH")
        if self._normal_handle_path(buf.value)!=self._normal_handle_path(str(path)):
            raise SourceDenied("HANDLE_FINAL_PATH_MISMATCH")
        streams=self._streams(handle)
        if streams!=("::$DATA",):
            raise SourceDenied("HANDLE_HAS_UNAPPROVED_NTFS_STREAM")
        return (int(fileid.volume),bytes(fileid.id),int(standard.links),
                int(standard.size),int(attr.attributes),streams,
                self._normal_handle_path(buf.value))

    def _read_handle(self,handle)->bytes:
        chunks=[]
        total=0
        while True:
            block=ctypes.create_string_buffer(65536)
            count=wintypes.DWORD(0)
            ok=self.api.ReadFile(handle,block,65536,ctypes.byref(count),None)
            if not ok:
                raise SourceDenied("HANDLE_READ_FAILED_WIN32_"+
                                   str(ctypes.get_last_error()))
            if count.value==0:break
            total+=count.value
            if total>self.max_bytes:raise SourceDenied("SOURCE_SIZE_LIMIT")
            chunks.append(block.raw[:count.value])
        return b"".join(chunks)

    def read(self,path:str,*,on_open=None)->bytes:
        if (path not in B.CANDIDATE_SHA256
            or not p188.previous.previous.canonical_legacy_path(path)
            or ":" in path or "\\" in path):
            raise SourceDenied("UNAPPROVED_OR_NONCANONICAL_B_SOURCE_PATH")
        full=self.root/path
        before=self._parent_identity(full)
        handle=None
        try:
            handle=self._open(full)
            identity=self._handle_identity(handle,full)
            if identity[3]>self.max_bytes:
                raise SourceDenied("SOURCE_SIZE_LIMIT")
            if on_open is not None:
                on_open(full)
            raw=self._read_handle(handle)
            if B._digest(path,raw)!=B.CANDIDATE_SHA256[path]:
                raise SourceDenied("ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH")
            after=self._handle_identity(handle,full)
            if identity!=after:
                raise SourceDenied("HANDLE_ID_OR_SOURCE_METADATA_DRIFT")
            if before!=self._parent_identity(full):
                raise SourceDenied("PARENT_PATH_IDENTITY_DRIFT")
            return raw
        finally:
            if handle is not None:
                self.api.CloseHandle(handle)

class P190ActualHandleBoundWin32Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P190 only genuine hosted Windows")
        cls.temp=tempfile.TemporaryDirectory(prefix="p190-handle-",dir=os.environ["RUNNER_TEMP"])
        cls.root=Path(cls.temp.name)
        cls.sealed=git("show",p189.BHEAD+":"+REL)
        if B._digest(REL,cls.sealed)!=SEAL:
            raise RuntimeError("P190 exact sealed original B source mismatch")
        cls.source=cls.root/REL
        cls.source.parent.mkdir(parents=True,exist_ok=True)
        cls.source.write_bytes(cls.sealed)
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"temp"):cls.temp.cleanup()
    def setUp(self):
        self.source.write_bytes(self.sealed)
        self.reader=Win32HandleBoundSourceProbe(self.root)

    def test_01_exact_original_B_23pin_source_and_win32_identity_read(self):
        self.assertEqual(len(B.CANDIDATE_SHA256),23)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_02_handle_stream_enumeration_rejects_real_ads(self):
        stream=str(self.source)+":p190_isolated_data"
        with open(stream,"wb") as f:f.write(b"synthetic non-executing stream")
        try:
            self.assertIn(":p190_isolated_data:$DATA",
                          p188.Win32SourceInspectionCandidate.streams(self.source))
            with self.assertRaisesRegex(SourceDenied,"HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(REL)
        finally:
            try:os.remove(stream)
            except FileNotFoundError:pass

    def test_03_original_hardlink_refusal_preserved_by_handle_link_count(self):
        other=self.root/"p190_synthetic_hardlink"
        os.link(self.source,other)
        try:
            self.assertGreater(self.source.stat().st_nlink,1)
            with self.assertRaisesRegex(SourceDenied,"HARDLINK_OR_LINKCOUNT_INVALID"):
                self.reader.read(REL)
        finally:other.unlink()

    def test_04_real_parent_junction_refused_before_handle_read(self):
        alias=self.source.parent
        physical=self.root/"p190_physical_test_folder"
        alias.rename(physical)
        try:
            p188.make_junction(alias,physical)
            with self.assertRaisesRegex(SourceDenied,"PARENT_REPARSE_OR_NON_DIRECTORY"):
                self.reader.read(REL)
        finally:
            if alias.is_junction():alias.rmdir()
            if physical.exists() and not alias.exists():physical.rename(alias)

    def test_05_noncanonical_ads_traversal_and_unapproved_B_paths_rejected(self):
        for bad in ("tests\\phase8_byok_b_scope_migration.py",REL+":named",
                    "tests/../phase8_byok_b_scope_migration.py",
                    "tests/p190_unreviewed.py"):
            with self.subTest(path=bad),self.assertRaisesRegex(
                  SourceDenied,"UNAPPROVED_OR_NONCANONICAL_B_SOURCE_PATH"):
                self.reader.read(bad)

    def test_06_mutated_original_main_stream_pin_is_denied(self):
        self.source.write_bytes(self.sealed+b"\n# P190 synthetic corruption")
        with self.assertRaisesRegex(SourceDenied,"ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH"):
            self.reader.read(REL)

    def test_07_existing_shared_file_handle_refuses_new_exclusive_admission(self):
        h=self.reader._open(self.source,GENERIC_READ,FILE_SHARE_READ)
        try:
            with self.assertRaisesRegex(SourceDenied,
                    "EXCLUSIVE_OPEN_DENIED_WIN32_"+str(ERROR_SHARING_VIOLATION)):
                self.reader.read(REL)
        finally:self.reader.api.CloseHandle(h)

    def test_08_new_write_open_while_exclusive_read_handle_is_held_refused(self):
        failures=[]
        def attempt(_):
            try:
                h=self.reader._open(self.source,GENERIC_WRITE,
                    FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE)
            except SourceDenied as exc:
                failures.append(str(exc))
            else:
                self.reader.api.CloseHandle(h)
                self.fail("P190 exclusive Win32 source handle admitted another writer")
        self.assertEqual(self.reader.read(REL,on_open=attempt),self.sealed)
        self.assertEqual(failures,["EXCLUSIVE_OPEN_DENIED_WIN32_"+str(ERROR_SHARING_VIOLATION)])

    def test_09_existing_stream_then_removal_recomputation_no_stale_admission(self):
        self.assertEqual(self.reader.read(REL),self.sealed)
        stream=str(self.source)+":p190_reobserve"
        with open(stream,"wb") as f:f.write(b"synthetic")
        try:
            with self.assertRaisesRegex(SourceDenied,"HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(REL)
        finally:
            try:os.remove(stream)
            except FileNotFoundError:pass
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_10_metadata_enumeration_failure_fails_closed(self):
        with mock.patch.object(self.reader,"_streams",
                               side_effect=SourceDenied("SYNTHETIC_KERNEL_QUERY_FAILURE")):
            with self.assertRaisesRegex(SourceDenied,"SYNTHETIC_KERNEL_QUERY_FAILURE"):
                self.reader.read(REL)
        self.assertEqual(self.reader.read(REL),self.sealed)

def run_original(root:Path,selector:str,output:Path,head:str,n:int,env:dict)->dict:
    if not root.is_dir() or root.resolve()==ROOT.resolve():
        raise RuntimeError("P190 distinct historical source clone required")
    if git("rev-parse","HEAD",root=root).decode().strip()!=head:
        raise RuntimeError("P190 exact old historical branch mismatch")
    return run_unittest(root,selector,output,head,n,env,170)

def run_unittest(root:Path,selector:str,output:Path,head:str,n:int,
                 env:dict,timeout:int)->dict:
    if git("rev-parse","HEAD",root=root).decode().strip()!=head:
        raise RuntimeError("P190 current exact source identity changed")
    env=dict(env,GITHUB_SHA=head,PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1")
    for name in list(env):
        if name in ("P190_ARCHIVE_TOKEN","GITHUB_TOKEN","GH_TOKEN") or name.endswith(("_API_KEY","_SECRET")):
            env.pop(name,None)
    with output.open("wb") as f:
        process=subprocess.run([sys.executable,"-B","-m","unittest","-v",selector],
                cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=f,
                stderr=subprocess.STDOUT,timeout=timeout,check=False)
    raw=output.read_bytes()
    text=raw.decode("utf8","replace").replace("\r\n","\n")
    return {"source_HEAD":head,"native_exit":process.returncode,
            "raw_log":output.name,"raw_SHA256":sha(raw),
            "expected_cases":n,
            "footer_counts":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M),
            "complete_footer_OK":bool(re.search(r"^OK\s*$",text,re.M)),
            "named_errors":re.findall(r"^(?:FAIL|ERROR): .+$",text,re.M)}

def demand_pass(r:dict):
    if r["native_exit"]!=0 or r["footer_counts"]!=[str(r["expected_cases"])] or not r["complete_footer_OK"]:
        raise RuntimeError("P190 native source-bound Windows test failure "+
             r["raw_log"]+" "+repr(r["named_errors"]))

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p190-handle-bound-source-security"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
        "checkpoint":"P190","historical_H":"HOLD",
        "current_C":"ISOLATED_WIN32_HANDLE_BOUND_SOURCE_PROTOTYPE_ONLY",
        "production_R":"HOLD","complete_native_full_product_regressions":"0/3",
        "qualified_independent_security_review":REVIEWS,
        "privileged_C1_G0_G6":"OPEN","signed_installer_main_helper_SAC_WDAC_GO":False,
        "original_historical_and_current_Phase10_verifiers_replaced":False,
        "original_P189_full_B_NTFS_ADS_admission_gap":"CONFIRMED_UNMITIGATED_IN_PRODUCT",
        "original_8_34_hardlink_refusal":"PRESERVE_UNCHANGED",
        "race_free_parent_ancestry_handle_proof":"NOT_ESTABLISHED",
        "handle_exclusive_sharing_versus_security_override":"NOT_ESTABLISHED",
        "other_full_product_P135_P175_P178_P179_failures":"PRESERVED_UNWAIVED",
        "candidate_integration_or_production_performance":"NOT_EVALUATED",
    }
    accepted=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["authenticated_original_P189"]=authenticate_p189(
            os.environ.get("P190_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        old=run_original(Path(os.environ["P190_ORIGINAL_P189_ROOT"]),
             "scripts.p189_windows_original_full_b_physical_alias_verdict.P189ActualOriginalFullBPhysicalAliasVerdict",
             out/"p190_original_exact_P189_full_B_physical_alias_4.log",P189,4,env)
        ledger["original_P189_exact_source_native"]=old
        demand_pass(old)
        current=run_unittest(ROOT,
             "scripts.p190_windows_handle_bound_source_probe.P190ActualHandleBoundWin32Tests",
             out/"p190_current_real_Win32_handle_ADS_10.log",
             os.environ["GITHUB_SHA"],10,env,160)
        ledger["current_handle_bound_Windows"]=current
        demand_pass(current)
        after=custody()
        ledger["source_after"]=after
        if before!=after:raise RuntimeError("P190 source before/after immutable custody mismatch")
        accepted=True
        print("P190_ORIGINAL_EXACT_P189_FULL_B_PHYSICAL_ALIAS=4/4_PASS|OS_EXIT=0",flush=True)
        print("P190_NEW_PHYSICAL_WIN32_HANDLE_BOUND_SECURITY=10/10_PASS|OS_EXIT=0",flush=True)
        print("P190_SOURCE_BOUND_NATIVE_WINDOWS_SELECTED=14/14_PASS_NOT_FULL_PRODUCT",flush=True)
        print("P190_ORIGINAL_P189_FULL_B_ADS_GAP=PRESERVED_OPEN",flush=True)
        print("P190_RACE_PROOF_AND_PRODUCTION_INTEGRATION=NOT_ESTABLISHED",flush=True)
        print("P190_QUALIFIED_SECURITY_APPROVAL=OPEN|FULL_PRODUCT=0/3|RELEASE=HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P190_AUTHENTIC_WIN32_HANDLE_EVIDENCE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=accepted
        (out/"p190_handle_bound_ntfs_ADS_HCR_original_source_ledger.json").write_text(
          json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if accepted else 1

if __name__=="__main__":
    raise SystemExit(main())
