"""P193 genuine user-mode NT relative component opens, original-source custody.

EXPERIMENTAL ONLY. An absolute-path-acquired Windows root directory HANDLE is
not proof of trusted root provenance. All child opens resolve a single basename
relative to already-held directory HANDLE via NtCreateFile RootDirectory.
Original B private/full gate and production code are never modified. A live
diagnostic deliberately shows an identical-byte alternate ancestor can be
admitted if the first trusted root lacks an independently pinned child identity.
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
import zipfile

from scripts import p192_windows_stable_parent_handle_identity as p192
from scripts import p191_windows_cross_process_source_race_witness as p191
from scripts import p190_windows_handle_bound_source_probe as p190
from scripts import p188_windows_physical_source_alias_race_witness as p188
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P192="3541db02537c1b0ec1c7b3b0be4fb925b0271588"
BRANCH="byok-c1-p193-nt-relative-source-root-admission-20261113"
NEW={
 "scripts/p193_windows_nt_relative_trusted_root_source.py",
 "docs/byok-c1-p193-relative-source-root-admission-security-review.md",
 ".github/workflows/p193-windows-relative-source-root.yml",
}
ARTIFACT=14044379054
ARCHIVE_SHA="F2051FFC5992696EE166F633AAC711E33D96D6C62E8529F26BAF93CD59AE852D"
LOGS={
 "p192_original_exact_P189_windows_4.log":
     ("4","26FDFB95653CF9A9D83C3C5A17E309C5C6B99B9800B35FD4207E262B5166886B"),
 "p192_original_exact_P190_windows_10.log":
     ("10","106002E3D9A430B1C91FD834EC38D95BC208BEC4C8ABAC53C4B2E99F7C83C7A2"),
 "p192_original_exact_P191_windows_10.log":
     ("10","C77DF9DC66C6F0C37C713907EBBB271DCEB0FF4C3E2EEDC3840E4D520EB1E113"),
 "p192_current_true_windows_parent_FileId_12.log":
     ("12","B0C3E6A52ADAFE52B1FF54751A36D92BA69DEA1D6AD6001B12BB92C1899955E5"),
}
LEDGER="p192_stable_parent_handle_source_HCR_ledger.json"
REVIEWS=p192.REVIEWS
REL=B.SELF
SEAL=B.CANDIDATE_SHA256[REL]

# Native NT File create/open constants, Windows only; do not invoke on product.
FILE_TRAVERSE=0x20
SYNCHRONIZE=0x00100000
OBJ_CASE_INSENSITIVE=0x40
FILE_OPEN=1
FILE_DIRECTORY_FILE=0x1
FILE_NON_DIRECTORY_FILE=0x40
FILE_SYNCHRONOUS_IO_NONALERT=0x20
NT_FILE_OPEN_REPARSE_POINT=0x00200000

class UnicodeString(ctypes.Structure):
    _fields_=[("Length",ctypes.c_ushort),
              ("MaximumLength",ctypes.c_ushort),
              ("Buffer",wintypes.LPWSTR)]

class ObjectAttributes(ctypes.Structure):
    _fields_=[("Length",wintypes.ULONG),
              ("RootDirectory",wintypes.HANDLE),
              ("ObjectName",ctypes.POINTER(UnicodeString)),
              ("Attributes",wintypes.ULONG),
              ("SecurityDescriptor",ctypes.c_void_p),
              ("SecurityQualityOfService",ctypes.c_void_p)]

class IoStatusBlock(ctypes.Structure):
    _fields_=[("Status",wintypes.LONG),
              ("Information",ctypes.c_size_t)]

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest().upper()

def git(*args:str,root:Path=ROOT)->bytes:
    result=subprocess.run(["git","-C",str(root),*args],stdin=subprocess.DEVNULL,
         stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=False)
    if result.returncode:
        raise RuntimeError("P193 Git native exit="+str(result.returncode)+
                           " "+repr(args)+" "+
                           result.stderr.decode("utf8","replace")[-450:])
    return result.stdout

def custody()->dict:
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",P192,"HEAD").decode().strip()!=P192
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P193 only exact clean original hosted Windows branch source")
    if set(git("diff","--name-only",P192,"HEAD").decode().splitlines())!=NEW:
        raise RuntimeError("P193 only three audit-only new paths permitted")
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P192+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P193 original historical product or frozen tests modified")
    for path in (
       "scripts/p188_windows_physical_source_alias_race_witness.py",
       "scripts/p189_windows_original_full_b_physical_alias_verdict.py",
       "scripts/p190_windows_handle_bound_source_probe.py",
       "scripts/p191_windows_cross_process_source_race_witness.py",
       "scripts/p192_windows_stable_parent_handle_identity.py",
       "tests/phase8_byok_b_scope_migration.py",
       "tests/phase8_byok_scope_migration.py",
       "tests/test_phase8_byok_b_scope_integrity.py",
    ):
        if git("show",P192+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P193 original source identity/previous witness drift: "+path)
    if len(B.CANDIDATE_SHA256)!=23 or REL not in B.ENVELOPE:
        raise RuntimeError("P193 original B literal source envelope changed")
    return {"P193_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P192_parent":P192,
            "only_three_new_review_files":sorted(NEW),
            "product_historical_B_original_tests_prior_reviews_unchanged":True}

def authenticate_p192(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P193 ephemeral P192 original evidence access denied")
    data=_download_artifact(ARTIFACT,ARCHIVE_SHA,token)
    if sha(data)!=ARCHIVE_SHA:
        raise RuntimeError("P193 original P192 archive SHA mismatched")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(LOGS)|{LEDGER}:
            raise RuntimeError("P193 original P192 ZIP inventory/CRC changed")
        for name,(count,digest) in LOGS.items():
            raw=z.read(name)
            txt=raw.decode("utf8","replace").replace("\r\n","\n")
            if (sha(raw)!=digest or
                re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=[count]
                or not re.search(r"^OK\s*$",txt,re.M)):
                raise RuntimeError("P193 prior source-specific Windows raw SHA/footer: "+name)
        evidence=json.loads(z.read(LEDGER))
        if (evidence.get("checkpoint")!="P192"
            or evidence.get("historical_H")!="HOLD"
            or evidence.get("production_R")!="HOLD"
            or evidence.get("full_product_unfiltered_native_windows_regressions")!="0/3"
            or evidence.get("qualified_external_security_reviewer_decisions")!=REVIEWS
            or evidence.get("source_before")!=evidence.get("source_after")
            or evidence["source_before"].get("P192_HEAD")!=P192
            or evidence.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P193 prior P192 H/C/R source-bound evidence invalid")
    return {"authentic_original_artifact":ARTIFACT,
            "original_ZIP_SHA256":ARCHIVE_SHA,
            "original_source_specific_native_windows_case_counts":[4,10,10,12],
            "original_release":"HOLD"}

class NtRootRelativeSourceCandidate(p192.StableParentHandleReader):
    """Experimental true NtCreateFile(rootdir=parent HANDLE, name=ONE component).

    Root acquired from an externally supplied/runner-owned absolute path;
    proof of its trusted origin does NOT follow from these tests.
    """
    def __init__(self,root:Path):
        super().__init__(root)
        n=ctypes.WinDLL("ntdll",use_last_error=True)
        n.NtCreateFile.argtypes=[
           ctypes.POINTER(wintypes.HANDLE),wintypes.ULONG,
           ctypes.POINTER(ObjectAttributes),ctypes.POINTER(IoStatusBlock),
           ctypes.c_void_p,wintypes.ULONG,wintypes.ULONG,wintypes.ULONG,
           wintypes.ULONG,ctypes.c_void_p,wintypes.ULONG,
        ]
        n.NtCreateFile.restype=wintypes.LONG
        self.ntdll=n

    def _nt_open_relative(self,parent_handle,name:str,is_dir:bool):
        if (not name or name in (".","..") or "\\" in name or "/" in name
            or ":" in name or name.endswith(("."," ")) or "\x00" in name):
            raise p190.SourceDenied("NT_RELATIVE_COMPONENT_NOT_CANONICAL")
        buf=ctypes.create_unicode_buffer(name)
        n=len(name.encode("utf-16-le"))
        if n>=65534:
            raise p190.SourceDenied("NT_RELATIVE_COMPONENT_TOO_LONG")
        us=UnicodeString(n,n+2,ctypes.cast(buf,wintypes.LPWSTR))
        attrs=ObjectAttributes(ctypes.sizeof(ObjectAttributes),parent_handle,
                               ctypes.pointer(us),OBJ_CASE_INSENSITIVE,None,None)
        io=IoStatusBlock()
        out=wintypes.HANDLE()
        access=((p192.FILE_READ_ATTRIBUTES|FILE_TRAVERSE|SYNCHRONIZE)
                if is_dir else (p190.GENERIC_READ|SYNCHRONIZE))
        options=NT_FILE_OPEN_REPARSE_POINT|FILE_SYNCHRONOUS_IO_NONALERT|(
             FILE_DIRECTORY_FILE if is_dir else FILE_NON_DIRECTORY_FILE)
        share=(p190.FILE_SHARE_READ|p190.FILE_SHARE_WRITE) if is_dir else 0
        status=self.ntdll.NtCreateFile(
            ctypes.byref(out),access,ctypes.byref(attrs),ctypes.byref(io),
            None,0,share,FILE_OPEN,options,None,0)
        if status!=0 or not out.value or out.value==p190.INVALID_HANDLE_VALUE:
            if out.value and out.value!=p190.INVALID_HANDLE_VALUE:
                self.api.CloseHandle(out)
            raise p190.SourceDenied("NT_RELATIVE_OPEN_DENIED_STATUS_0x"+
                  format(ctypes.c_uint32(status).value,"08X"))
        return out

    def read(self,path:str,*,on_open=None,on_component=None)->bytes:
        if (path not in B.CANDIDATE_SHA256
            or not p188.previous.previous.canonical_legacy_path(path)
            or ":" in path or "\\" in path):
            raise p190.SourceDenied("UNAPPROVED_OR_NONCANONICAL_B_SOURCE_PATH")
        full=self.root/path
        components=full.relative_to(self.root).parts
        opened=[]
        leaf=None
        try:
            # This initial root is NOT authenticated as a sealed product root.
            # It is a runner-owned temporary root. P193 does not claim more.
            root_handle=self._open_parent(self.root)
            opened.append((self.root,root_handle,
                           self._parent_snapshot(root_handle,self.root)))
            for idx,name in enumerate(components):
                parent,hparent,_=opened[-1]
                is_dir=idx<len(components)-1
                if on_component is not None:
                    on_component(parent,name,is_dir)
                h=self._nt_open_relative(hparent,name,is_dir)
                if is_dir:
                    directory=parent/name
                    # Never allocate a directory HANDLE without entering it
                    # into the cleanup chain: _parent_snapshot can deny a
                    # reparse point after NtCreateFile succeeds. Without this
                    # except/CloseHandle, Windows retains the junction and
                    # subsequent cleanup fails with WinError 32.
                    try:
                        snapshot=self._parent_snapshot(h,directory)
                    except BaseException:
                        self.api.CloseHandle(h)
                        raise
                    opened.append((directory,h,snapshot))
                else:
                    leaf=h
            if leaf is None:
                raise p190.SourceDenied("NT_RELATIVE_LEAF_NOT_OPENED")
            original=self._handle_identity(leaf,full)
            if original[3]>self.max_bytes:
                raise p190.SourceDenied("SOURCE_SIZE_LIMIT")
            if on_open is not None:
                on_open(full)
            raw=self._read_handle(leaf)
            if B._digest(path,raw)!=B.CANDIDATE_SHA256[path]:
                raise p190.SourceDenied("ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH")
            if original!=self._handle_identity(leaf,full):
                raise p190.SourceDenied("HANDLE_ID_OR_SOURCE_METADATA_DRIFT")
            for dirname,h,previous in opened:
                if self._parent_snapshot(h,dirname)!=previous:
                    raise p190.SourceDenied("NT_HELD_PARENT_FILEID_OR_PATH_DRIFT")
            return raw
        finally:
            if leaf is not None:
                self.api.CloseHandle(leaf)
            for _,h,_ in reversed(opened):
                self.api.CloseHandle(h)

class P193NativeWindowsRootRelativeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P193 genuine hosted Win32 required")
        cls.sealed=git("show",p190.p189.BHEAD+":"+REL)
        if B._digest(REL,cls.sealed)!=SEAL:
            raise RuntimeError("P193 original sealed B literal SHA mismatch")
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="p193-nt-root-",dir=os.environ["RUNNER_TEMP"])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/REL
        self.source.parent.mkdir(parents=True,exist_ok=True)
        self.source.write_bytes(self.sealed)
        self.reader=NtRootRelativeSourceCandidate(self.root)
    def child(self,action,src:Path,dst:Path|None=None):
        env=os.environ.copy()
        for key in list(env):
            if key in ("GITHUB_TOKEN","GH_TOKEN","P193_ARCHIVE_TOKEN") or key.endswith(("_API_KEY","_SECRET")):
                env.pop(key,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        res=subprocess.run([sys.executable,"-B","-c",p191.CHILD_SCRIPT,
            action,str(src),str(dst) if dst is not None else ""],
            cwd=self.root,env=env,stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            timeout=15,check=False)
        if res.returncode:raise RuntimeError("P193 Win32 separate process error "+
                     res.stderr.decode("utf8","replace")[-500:])
        record=json.loads(res.stdout.decode("utf8","strict").strip())
        self.assertEqual(record.get("operation"),action)
        self.assertIs(type(record.get("succeeded")),bool)
        print("P193_NATIVE_CHILD_"+action.upper()+"="+
              ("ALLOWED" if record["succeeded"] else "OS_DENIED")+
              "|WINERROR="+str(record.get("winerror")),flush=True)
        return record

    def test_01_real_original_B_source_admitted_by_nt_relative_component_handles(self):
        self.assertEqual(len(B.CANDIDATE_SHA256),23)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_02_actual_ntcreatefile_each_single_component_from_held_parent(self):
        observed=[]
        nt=self.reader._nt_open_relative
        def spy(parent,name,directory):
            observed.append((name,directory))
            return nt(parent,name,directory)
        self.reader._nt_open_relative=spy
        self.assertEqual(self.reader.read(REL),self.sealed)
        self.assertEqual(observed,[("tests",True),("phase8_byok_b_scope_migration.py",False)])
        print("P193_TRUE_NT_ROOTDIRECTORY_COMPONENTS="+str(len(observed)),flush=True)

    def test_03_new_sibling_inside_held_relative_tests_directory_does_not_deny(self):
        sibling=self.source.parent/"p193_new_sibling"
        outcome=[]
        def external(_):outcome.append(self.child("write_sibling",self.source,sibling))
        self.assertEqual(self.reader.read(REL,on_open=external),self.sealed)
        self.assertTrue(outcome[0]["succeeded"])
        self.assertEqual(sibling.read_bytes(),b"P191 independent sibling file")

    def test_04_new_sibling_inside_trusted_temp_root_does_not_deny(self):
        sibling=self.root/"p193_root_sibling"
        outcome=[]
        def external(_):outcome.append(self.child("write_sibling",self.source,sibling))
        self.assertEqual(self.reader.read(REL,on_open=external),self.sealed)
        self.assertTrue(outcome[0]["succeeded"])

    def test_05_real_midread_ads_added_by_other_process_refused_on_same_handle(self):
        results=[]
        stream=str(self.source)+":p191_cross_process_stream"
        try:
            with self.assertRaisesRegex(p190.SourceDenied,"HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(REL,on_open=lambda _:
                    results.append(self.child("create_ads",self.source)))
            self.assertEqual(len(results),1)
            self.assertTrue(results[0]["succeeded"])
        finally:
            if ":p191_cross_process_stream:$DATA" in p188.Win32SourceInspectionCandidate.streams(self.source):
                os.remove(stream)

    def test_06_real_midread_new_hardlink_refused_on_same_leaf_handle(self):
        hardlink=self.root/"p193_new_hardlink"
        results=[]
        try:
            with self.assertRaisesRegex(p190.SourceDenied,"HARDLINK_OR_LINKCOUNT_INVALID"):
                self.reader.read(REL,on_open=lambda _:
                    results.append(self.child("create_hardlink",self.source,hardlink)))
            self.assertEqual(len(results),1)
            self.assertTrue(results[0]["succeeded"])
        finally:
            if hardlink.exists():hardlink.unlink()

    def test_07_preexisting_real_ntfs_junction_parent_not_followed_by_relative_open(self):
        old=self.source.parent
        new=self.root/"p193_real_tests"
        old.rename(new)
        try:
            p188.make_junction(old,new)
            with self.assertRaisesRegex(p190.SourceDenied,"HELD_PARENT_REPARSE_OR_NON_DIRECTORY"):
                self.reader.read(REL)
        finally:
            if old.is_junction():old.rmdir()
            if new.exists() and not old.exists():new.rename(old)

    def test_08_reparse_parent_substituted_between_root_and_relative_open_refused(self):
        old=self.source.parent
        real=self.root/"p193_displaced_source_parent"
        acted=[]
        def swap(parent,name,directory):
            if name=="tests" and directory and not acted:
                old.rename(real)
                p188.make_junction(old,real)
                acted.append("JUNCTION_INJECTED_DURING_ROOTED_RESOLUTION")
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                          "HELD_PARENT_REPARSE_OR_NON_DIRECTORY"):
                self.reader.read(REL,on_component=swap)
            self.assertEqual(acted,["JUNCTION_INJECTED_DURING_ROOTED_RESOLUTION"])
        finally:
            if old.is_junction():old.rmdir()
            if real.exists() and not old.exists():real.rename(old)
        print("P193_JUNCTION_SWAP_DURING_ROOTED_OPEN=HANDLE_METADATA_REFUSED",flush=True)

    def test_09_original_wrong_B_source_main_bytes_denied(self):
        self.source.write_bytes(self.sealed+b"\n# p193 corrupt not original")
        with self.assertRaisesRegex(p190.SourceDenied,"ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH"):
            self.reader.read(REL)

    def test_10_existing_named_ads_on_original_B_source_refused(self):
        stream=str(self.source)+":p193_stream"
        with open(stream,"wb") as f:f.write(b"isolated harmless synthetic stream")
        try:
            with self.assertRaisesRegex(p190.SourceDenied,"HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(REL)
        finally:os.remove(stream)

    def test_11_held_parent_rename_attempt_external_child_os_refusal(self):
        dest=self.root/"p193_renamed_test_dir"
        results=[]
        self.assertEqual(self.reader.read(REL,on_open=lambda _:
            results.append(self.child("rename_parent",self.source.parent,dest))),self.sealed)
        self.assertEqual(len(results),1)
        self.assertFalse(results[0]["succeeded"])
        self.assertIn(results[0].get("winerror"),(5,32))

    def test_12_relative_component_aliases_and_traversal_refused(self):
        for wrong in ("tests\\phase8_byok_b_scope_migration.py",
                      REL+":ADS",
                      "tests/../phase8_byok_b_scope_migration.py",
                      "tests/p193_not_a_pinned_original.py"):
            with self.subTest(value=wrong):
                with self.assertRaisesRegex(p190.SourceDenied,
                         "UNAPPROVED_OR_NONCANONICAL_B_SOURCE_PATH"):
                    self.reader.read(wrong)
        h=self.reader._open_parent(self.root)
        try:
            for wrong in ("..","../tests","tests\\name","name:ADS",""):
                with self.subTest(component=wrong):
                    with self.assertRaisesRegex(p190.SourceDenied,
                               "NT_RELATIVE_COMPONENT_NOT_CANONICAL"):
                        self.reader._nt_open_relative(h,wrong,True)
        finally:self.reader.api.CloseHandle(h)

    def test_13_missing_ntdll_component_open_fails_closed_then_successful_read(self):
        real=self.reader._nt_open_relative
        def unavailable(*_):
            raise p190.SourceDenied("SYNTHETIC_NTDLL_COMPONENT_FAILURE")
        self.reader._nt_open_relative=unavailable
        with self.assertRaisesRegex(p190.SourceDenied,"SYNTHETIC_NTDLL_COMPONENT_FAILURE"):
            self.reader.read(REL)
        self.reader._nt_open_relative=real
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_14_same_sealed_content_different_real_ancestor_is_not_trust_pinned(self):
        # Real diagnostic, expected security limitation: unlike a live trusted
        # file-ID manifest, this prototype has no original child-dir identity.
        old=self.source.parent
        displaced=self.root/"p193_prior_original_tests"
        other=self.root/"p193_alternate_equivalent_tests"
        other.mkdir()
        (other/self.source.name).write_bytes(self.sealed)
        swaps=[]
        def substitute(parent,name,is_directory):
            if name=="tests" and is_directory and not swaps:
                old.rename(displaced)
                other.rename(old)
                swaps.append("ALTERNATE_REAL_DIRECTORY_BINDING")
        try:
            actual=self.reader.read(REL,on_component=substitute)
            self.assertEqual(actual,self.sealed)
            self.assertEqual(swaps,["ALTERNATE_REAL_DIRECTORY_BINDING"])
            print("P193_SECURITY_LIMITATION_IDENTICAL_PINNED_BYTES_UNTRUSTED_ANCESTOR="+
                  "ADMITTED_BY_UNINTEGRATED_PROTOTYPE",flush=True)
        finally:
            if old.exists() and displaced.exists():
                old.rename(other)
                displaced.rename(old)
            elif displaced.exists() and not old.exists():
                displaced.rename(old)
        # This is a recorded failure of identity *provenance*, NOT a security GO.

def native_unittest(directory:Path,selector:str,output:Path,head:str,
                    count:int,env:dict,timeout:int)->dict:
    if not directory.is_dir() or directory.resolve()==ROOT.resolve() and head!=os.environ.get("GITHUB_SHA"):
        raise RuntimeError("P193 original exact source directory isolation invalid")
    if git("rev-parse","HEAD",root=directory).decode().strip()!=head:
        raise RuntimeError("P193 original exact source HEAD drift")
    subprocess_env=dict(env,GITHUB_SHA=head,PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1")
    for name in list(subprocess_env):
        if name in ("GITHUB_TOKEN","GH_TOKEN","P193_ARCHIVE_TOKEN") or name.endswith(("_API_KEY","_SECRET")):
            subprocess_env.pop(name,None)
    with output.open("wb") as sink:
        result=subprocess.run([sys.executable,"-B","-m","unittest","-v",selector],
           cwd=directory,env=subprocess_env,stdin=subprocess.DEVNULL,
           stdout=sink,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    raw=output.read_bytes()
    txt=raw.decode("utf8","replace").replace("\r\n","\n")
    return {"original_source_HEAD":head,"OS_exit":result.returncode,
            "raw_log_filename":output.name,"SHA256":sha(raw),
            "selected_expected":count,
            "true_footers":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
            "footer_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
            "native_rootdir_events":re.findall(r"P193_(?:TRUE|JUNCTION|SECURITY|NATIVE)_[^\r\n]+",txt),
            "errors":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}
def require_pass(result):
    if (result["OS_exit"]!=0 or result["true_footers"]!=[str(result["selected_expected"])]
        or not result["footer_OK"]):
        raise RuntimeError("P193 genuine source-bound native Windows tests failed "+
                           result["raw_log_filename"]+" "+repr(result["errors"]))

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p193-root-relative-Windows"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
       "checkpoint":"P193","historical_H":"HOLD",
       "current_C":"ISOLATED_NT_ROOTDIRECTORY_RELATIVE_SOURCE_OPEN_ONLY",
       "production_R":"HOLD",
       "complete_native_unfiltered_full_product_Windows_regressions":"0/3",
       "qualified_external_seven_reviews":REVIEWS,
       "privileged_G0_G6":"OPEN","signed_main_helper_installer_SAC_WDAC_GO":False,
       "original_complete_historical_B_ADS_admission_gap":"CONFIRMED_OPEN_UNMITIGATED",
       "root_source_provenance_OS_trusted_identity":"NOT_ESTABLISHED",
       "identical_byte_alternate_ancestor_diagnostic":"EXPECTED_ADMITTED_NOT_PROVEN_SAFE",
       "ADS_hardlink_stream_adding_removing_ABA":"NOT_ELIMINATED",
       "current_public_Phase10_integration":"NOT_ATTEMPTED",
       "qualified_independent_security_review":"OPEN",
       "P135_P175_P178_P179_prior_failures":"PRESERVED_UNWAIVED",
    }
    complete=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["authentic_P192_prior"]=authenticate_p192(os.environ.get("P193_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        suites=[
          ("P189","P193_EXACT_P189_ROOT",p190.P189,
            "scripts.p189_windows_original_full_b_physical_alias_verdict.P189ActualOriginalFullBPhysicalAliasVerdict",4),
          ("P190","P193_EXACT_P190_ROOT",p191.P190,
            "scripts.p190_windows_handle_bound_source_probe.P190ActualHandleBoundWin32Tests",10),
          ("P191","P193_EXACT_P191_ROOT",p192.P191,
            "scripts.p191_windows_cross_process_source_race_witness.P191ActualCrossProcessWindowsRaceCases",10),
          ("P192","P193_EXACT_P192_ROOT",P192,
            "scripts.p192_windows_stable_parent_handle_identity.P192ActualStableParentWin32Tests",12),
        ]
        ledger["original_exact_source_native_tests"]={}
        for era,envvar,oldhead,selector,count in suites:
            original=Path(os.environ[envvar])
            if original.resolve()==ROOT.resolve():
                raise RuntimeError("P193 original native source clone overlaps P193 new root")
            result=native_unittest(original,selector,
                 out/("p193_original_exact_"+era+"_native_Windows_"+str(count)+".log"),
                 oldhead,count,env,180)
            ledger["original_exact_source_native_tests"][era]=result
            require_pass(result)
        new=native_unittest(ROOT,
          "scripts.p193_windows_nt_relative_trusted_root_source.P193NativeWindowsRootRelativeCases",
          out/"p193_current_native_nt_rootrelative_14.log",
          os.environ["GITHUB_SHA"],14,env,180)
        ledger["P193_true_rootrelative_Windows"]=new
        require_pass(new)
        markers=new["native_rootdir_events"]
        if not any("P193_TRUE_NT_ROOTDIRECTORY_COMPONENTS=2" in x for x in markers):
            raise RuntimeError("P193 no genuine component-by-component NT RootDirectory evidence")
        if not any("P193_SECURITY_LIMITATION_IDENTICAL_PINNED_BYTES_UNTRUSTED_ANCESTOR=" in x
                   for x in markers):
            raise RuntimeError("P193 unmitigated root-provenance security finding omitted")
        after=custody()
        ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P193 actual source/HCR changed during native execution")
        complete=True
        print("P193_PRIOR_EXACT_P189_4_P190_10_P191_10_P192_12=36/36_PASS",flush=True)
        print("P193_CURRENT_NT_ROOT_RELATIVE_SELECTED=14/14_PASS",flush=True)
        print("P193_SOURCE_BOUND_NATIVE_WINDOWS=50/50_SELECTED_NOT_FULL_PRODUCT",flush=True)
        print("P193_ROOT_PROVENANCE_DIAGNOSTIC=UNSAFE_ACCEPTANCE_OPEN",flush=True)
        print("P193_RELATIVE_OPENS_REPARSE_CHECKS=WIN32_OBSERVED_NOT_FORMAL_PROOF",flush=True)
        print("P193_QUALIFIED_EXTERNAL_REVIEW=OPEN|FULL_PRODUCT=0/3|RELEASE=HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P193_NATIVE_ROOT_RELATIVE_TEST_CUSTODY=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=complete
        (out/"p193_nt_root_directory_original_source_HCR_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":
    raise SystemExit(main())
