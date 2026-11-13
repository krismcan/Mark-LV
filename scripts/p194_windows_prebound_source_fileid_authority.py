"""P194: pre-bound Win32 root, child directory and leaf FileId authority.

ISOLATED TEST PROTOTYPE ONLY. A synthetic externally enrolled in-memory
source identity anchor is captured BEFORE a controlled mutation. The anchor
is NOT signed, durable, production-root-attested or full Git admission.
All historical BYOK-B source, product and frozen tests remain unchanged.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

from scripts import p193_windows_nt_relative_trusted_root_source as p193
from scripts import p192_windows_stable_parent_handle_identity as p192
from scripts import p191_windows_cross_process_source_race_witness as p191
from scripts import p190_windows_handle_bound_source_probe as p190
from scripts import p188_windows_physical_source_alias_race_witness as p188
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P193="ce605cd301f979e735963278c47c09b239b715ce"
BRANCH="byok-c1-p194-prebound-source-root-ancestor-fileid-20261113"
NEW={
 "scripts/p194_windows_prebound_source_fileid_authority.py",
 "docs/byok-c1-p194-prebound-root-ancestor-source-identity-review.md",
 ".github/workflows/p194-windows-prebound-source-fileid.yml",
}
ARTIFACT=14051350366
ARCHIVE_SHA="E6CF30C6C81314E631C12C37F760A628263A90BCD8C71FFC829AA9A2B95149B7"
LOGS={
 "p193_original_exact_P189_native_Windows_4.log":
  ("4","BEE1B3B16421DA7AFDFDB6797FE809EDD452BA221F5F879204606BAE1F26FEC4"),
 "p193_original_exact_P190_native_Windows_10.log":
  ("10","FFE756CB0D1CBACA9BCD0D5494591CADFF1F5301A0453FCF9C4D0FE6F5CA376B"),
 "p193_original_exact_P191_native_Windows_10.log":
  ("10","6344A83FDD8D974098C9E1F5A955C1CCD96DA5E72DCD87BEF095C14DC1ED7DE2"),
 "p193_original_exact_P192_native_Windows_12.log":
  ("12","9D297CA278B826277E33078B8C6A79916EF13C4DF6B8101CDDC13262BB955FB0"),
 "p193_current_native_nt_rootrelative_14.log":
  ("14","E558C56F9484E8E2CB38E5FF2F3E7ED2F0B9DA44E10866ADF1456AF4C0B0EF2C"),
}
OLD_LEDGER="p193_nt_root_directory_original_source_HCR_ledger.json"
REVIEWS=p193.REVIEWS
REL=B.SELF
SEAL=B.CANDIDATE_SHA256[REL]

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str,root:Path=ROOT)->bytes:
    p=subprocess.run(["git","-C",str(root),*args],stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     timeout=60,check=False)
    if p.returncode:
        raise RuntimeError("P194 source Git exit="+str(p.returncode)+" "+
                           repr(args)+" "+
                           p.stderr.decode("utf8","replace")[-500:])
    return p.stdout

def custody()->dict:
    if (sys.platform!="win32"
       or os.environ.get("GITHUB_ACTIONS")!="true"
       or os.environ.get("RUNNER_OS")!="Windows"
       or os.environ.get("GITHUB_EVENT_NAME")!="push"
       or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
       or os.environ.get("GITHUB_REF_NAME")!=BRANCH
       or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
       or git("branch","--show-current").decode().strip()!=BRANCH
       or git("merge-base",P193,"HEAD").decode().strip()!=P193
       or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P194 exact clean hosted Windows original source required")
    if set(git("diff","--name-only",P193,"HEAD").decode().splitlines())!=NEW:
        raise RuntimeError("P194 exactly three additive review-only paths required")
    for directory in ("tests","nayeon"):
        if git("rev-parse",P193+":"+directory)!=git("rev-parse","HEAD:"+directory):
            raise RuntimeError("P194 original historical frozen source/product modified")
    for path in (
      "scripts/p188_windows_physical_source_alias_race_witness.py",
      "scripts/p189_windows_original_full_b_physical_alias_verdict.py",
      "scripts/p190_windows_handle_bound_source_probe.py",
      "scripts/p191_windows_cross_process_source_race_witness.py",
      "scripts/p192_windows_stable_parent_handle_identity.py",
      "scripts/p193_windows_nt_relative_trusted_root_source.py",
      "tests/phase8_byok_b_scope_migration.py",
      "tests/phase8_byok_scope_migration.py",
      "tests/test_phase8_byok_b_scope_integrity.py",
    ):
        if git("show",P193+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P194 previous immutable source/witness changed: "+path)
    if len(B.CANDIDATE_SHA256)!=23 or REL not in B.ENVELOPE:
        raise RuntimeError("P194 historical B 23-pin literal envelope changed")
    return {"P194_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P193_parent":P193,
            "only_three_new_review_paths":sorted(NEW),
            "frozen_historical_source_and_product_preserved":True}

def authenticate_original_p193(token:str)->dict:
    if len(token)<8:raise RuntimeError("P194 missing ephemeral prior evidence token")
    data=_download_artifact(ARTIFACT,ARCHIVE_SHA,token)
    if sha(data)!=ARCHIVE_SHA:
        raise RuntimeError("P194 prior P193 Windows ZIP SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(LOGS)|{OLD_LEDGER}:
            raise RuntimeError("P194 original P193 ZIP inventory/CRC mismatched")
        for name,(n,digest) in LOGS.items():
            raw=z.read(name)
            text=raw.decode("utf8","replace").replace("\r\n","\n")
            if (sha(raw)!=digest or
                re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)!=[n] or
                not re.search(r"^OK\s*$",text,re.M)):
                raise RuntimeError("P194 original P193 exact log SHA/footer invalid: "+name)
        ledger=json.loads(z.read(OLD_LEDGER))
        if (ledger.get("checkpoint")!="P193"
            or ledger.get("historical_H")!="HOLD"
            or ledger.get("production_R")!="HOLD"
            or ledger.get("complete_native_unfiltered_full_product_Windows_regressions")!="0/3"
            or ledger.get("qualified_external_seven_reviews")!=REVIEWS
            or ledger.get("source_before")!=ledger.get("source_after")
            or ledger["source_before"].get("P193_HEAD")!=P193
            or ledger.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P194 original P193 ledger H/C/R provenance invalid")
    return {"original_P193_artifact":ARTIFACT,"ZIP_SHA256":ARCHIVE_SHA,
            "source_identity_specific_native_tests":[4,10,10,12,14],
            "prior_production_release":"HOLD"}

@dataclass(frozen=True)
class SyntheticPreboundFileIds:
    """In-memory lab trust assertion BEFORE mutation, NOT external certificate.

    The original sealed B SHA is a necessary additional byte-authority check;
    these physical FileId tuples must be provisioned by independently
    authenticated trusted authority for any real product use.
    """
    root_snapshot:tuple
    tests_snapshot:tuple
    leaf_volume:int
    leaf_fileid:bytes
    source_path:str
    source_sha:str

def bind_verified_fixture(root:Path,sealed:bytes)->SyntheticPreboundFileIds:
    """Test-only enrolment of approved source pre-mutation into sealed identity.

    Do NOT call from the source admission path (self-pinning would defeat trust).
    """
    if B._digest(REL,sealed)!=SEAL:
        raise p190.SourceDenied("TRUST_ENROLLMENT_ORIGINAL_B_SHA_MISMATCH")
    reader=p193.NtRootRelativeSourceCandidate(root)
    root_handle=tests_handle=leaf=None
    try:
        root_handle=reader._open_parent(root)
        root_info=reader._parent_snapshot(root_handle,root)
        tests_handle=reader._nt_open_relative(root_handle,"tests",True)
        tests_info=reader._parent_snapshot(tests_handle,root/"tests")
        leaf=reader._nt_open_relative(tests_handle,Path(REL).name,False)
        leaf_info=reader._handle_identity(leaf,root/REL)
        if reader._read_handle(leaf)!=sealed:
            raise p190.SourceDenied("TRUST_ENROLLMENT_ORIGINAL_B_BYTES_MISMATCH")
        return SyntheticPreboundFileIds(
            root_info,tests_info,leaf_info[0],leaf_info[1],REL,SEAL)
    finally:
        if leaf is not None:reader.api.CloseHandle(leaf)
        if tests_handle is not None:reader.api.CloseHandle(tests_handle)
        if root_handle is not None:reader.api.CloseHandle(root_handle)

class PreboundWin32SourceReader(p193.NtRootRelativeSourceCandidate):
    """Strict pre-supplied physical root, child and leaf identity admission.

    No directory FileId enrollment occurs inside read(). All opens use
    original P193 NT RootDirectory relative component API and held parents.
    """
    def __init__(self,root:Path,anchor:SyntheticPreboundFileIds):
        super().__init__(root)
        if not isinstance(anchor,SyntheticPreboundFileIds) or anchor.source_path!=REL or anchor.source_sha!=SEAL:
            raise p190.SourceDenied("MISSING_OR_MALFORMED_PREBOUND_SOURCE_AUTHORITY")
        self.prebound=anchor

    def read(self,path:str,*,on_open=None,on_component=None)->bytes:
        if (path!=self.prebound.source_path or
            path not in B.CANDIDATE_SHA256 or
            not p188.previous.previous.canonical_legacy_path(path) or
            ":" in path or "\\" in path):
            raise p190.SourceDenied("UNAPPROVED_OR_NONCANONICAL_B_SOURCE_PATH")
        full=self.root/path
        directory_handles=[]
        leaf=None
        try:
            root_h=self._open_parent(self.root)
            directory_handles.append(root_h)
            root_obs=self._parent_snapshot(root_h,self.root)
            if root_obs!=self.prebound.root_snapshot:
                raise p190.SourceDenied("PINNED_ROOT_FILEID_MISMATCH")
            if on_component is not None:
                on_component(self.root,"tests",True)
            tests_h=self._nt_open_relative(root_h,"tests",True)
            directory_handles.append(tests_h)
            tests_obs=self._parent_snapshot(tests_h,self.root/"tests")
            if tests_obs!=self.prebound.tests_snapshot:
                raise p190.SourceDenied("PINNED_ANCESTOR_FILEID_MISMATCH")
            if on_component is not None:
                on_component(self.root/"tests",Path(path).name,False)
            leaf=self._nt_open_relative(tests_h,Path(path).name,False)
            first=self._handle_identity(leaf,full)
            if (first[0]!=self.prebound.leaf_volume or
                first[1]!=self.prebound.leaf_fileid):
                raise p190.SourceDenied("PINNED_SOURCE_LEAF_FILEID_MISMATCH")
            if first[3]>self.max_bytes:
                raise p190.SourceDenied("SOURCE_SIZE_LIMIT")
            if on_open is not None:
                on_open(full)
            raw=self._read_handle(leaf)
            if B._digest(path,raw)!=self.prebound.source_sha:
                raise p190.SourceDenied("ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH")
            second=self._handle_identity(leaf,full)
            if first!=second:
                raise p190.SourceDenied("HANDLE_ID_OR_SOURCE_METADATA_DRIFT")
            if self._parent_snapshot(root_h,self.root)!=self.prebound.root_snapshot:
                raise p190.SourceDenied("PINNED_ROOT_FILEID_MISMATCH")
            if self._parent_snapshot(tests_h,self.root/"tests")!=self.prebound.tests_snapshot:
                raise p190.SourceDenied("PINNED_ANCESTOR_FILEID_MISMATCH")
            return raw
        finally:
            if leaf is not None:self.api.CloseHandle(leaf)
            for h in reversed(directory_handles):
                self.api.CloseHandle(h)

class P194PreboundTrueWindowsSecurityCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P194 only genuine hosted native Windows")
        cls.sealed=git("show",p190.p189.BHEAD+":"+REL)
        if B._digest(REL,cls.sealed)!=SEAL:
            raise RuntimeError("P194 sealed genuine original B source bytes differ")
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="p194-pinned-fileids-",dir=os.environ["RUNNER_TEMP"])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/REL
        self.source.parent.mkdir(parents=True,exist_ok=True)
        self.source.write_bytes(self.sealed)
        self.anchor=bind_verified_fixture(self.root,self.sealed)
        self.reader=PreboundWin32SourceReader(self.root,self.anchor)

    def child(self,op:str,source:Path,destination:Path|None=None)->dict:
        env=os.environ.copy()
        for key in list(env):
            if key in ("GITHUB_TOKEN","GH_TOKEN","P194_ARCHIVE_TOKEN") or key.endswith(("_API_KEY","_SECRET")):
                env.pop(key,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        r=subprocess.run([sys.executable,"-B","-c",p191.CHILD_SCRIPT,
            op,str(source),str(destination) if destination is not None else ""],
            cwd=self.root,env=env,stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=False)
        if r.returncode:
            self.fail("P194 separate Windows test process unexpectedly failed: "+
                      r.stderr.decode("utf8","replace")[-500:])
        record=json.loads(r.stdout.decode("utf8","strict").strip())
        self.assertEqual(record.get("operation"),op)
        self.assertIs(type(record.get("succeeded")),bool)
        print("P194_EXTERNAL_"+op.upper()+"="+
              ("OS_ALLOWED" if record["succeeded"] else "OS_REFUSED")+
              "|WINERROR="+str(record.get("winerror")),flush=True)
        return record

    def test_01_original_sealed_B_approved_exact_physical_id_admitted(self):
        self.assertEqual(len(B.CANDIDATE_SHA256),23)
        self.assertEqual(self.reader.read(REL),self.sealed)
        print("P194_PREBOUND_ROOT_ANCESTOR_LEAF_FILEIDS=ADMITTED_ORIGINAL",flush=True)

    def test_02_identical_original_B_bytes_substituted_real_parent_refused(self):
        # P193 historical original diagnostic ACCEPTS this same mutation.
        original=self.source.parent
        moved=self.root/"p194_original_tests_held"
        replacement=self.root/"p194_alternate_same_bytes_tests"
        replacement.mkdir()
        (replacement/self.source.name).write_bytes(self.sealed)
        did=[]
        def substitute(directory,name,is_directory):
            if name=="tests" and is_directory and not did:
                original.rename(moved)
                replacement.rename(original)
                did.append(True)
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                             "PINNED_ANCESTOR_FILEID_MISMATCH"):
                self.reader.read(REL,on_component=substitute)
            self.assertTrue(did)
            self.assertEqual((original/self.source.name).read_bytes(),self.sealed)
            print("P194_IDENTICAL_BYTES_DIFFERENT_ANCESTOR_FILEID=REFUSED",flush=True)
        finally:
            if original.exists() and moved.exists():
                original.rename(replacement)
                moved.rename(original)
            elif moved.exists() and not original.exists():
                moved.rename(original)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_03_same_original_bytes_new_leaf_in_original_directory_refused(self):
        old=self.root/"p194_displaced_original_leaf"
        staged=self.source.parent/"p194_equivalent_other_leaf"
        staged.write_bytes(self.sealed)
        self.source.rename(old)
        staged.rename(self.source)
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                                      "PINNED_SOURCE_LEAF_FILEID_MISMATCH"):
                self.reader.read(REL)
            print("P194_IDENTICAL_BYTES_DIFFERENT_LEAF_FILEID=REFUSED",flush=True)
        finally:
            if self.source.exists():self.source.unlink()
            if old.exists():old.rename(self.source)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_04_same_original_bytes_different_temporary_root_refused(self):
        displaced=self.root.with_name(self.root.name+"-original")
        assert not displaced.exists()
        self.root.rename(displaced)
        try:
            self.root.mkdir()
            source=self.root/REL
            source.parent.mkdir()
            source.write_bytes(self.sealed)
            with self.assertRaisesRegex(p190.SourceDenied,
                                       "PINNED_ROOT_FILEID_MISMATCH"):
                self.reader.read(REL)
            print("P194_IDENTICAL_BYTES_ALTERNATE_ROOT_FILEID=REFUSED",flush=True)
        finally:
            if self.root.exists():shutil.rmtree(self.root)
            if displaced.exists():displaced.rename(self.root)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_05_same_original_source_sibling_write_inside_parent_admitted(self):
        target=self.source.parent/"p194_valid_sibling"
        events=[]
        self.assertEqual(self.reader.read(REL,on_open=lambda _:
            events.append(self.child("write_sibling",self.source,target))),self.sealed)
        self.assertTrue(events[0]["succeeded"])
        self.assertEqual(target.read_bytes(),b"P191 independent sibling file")

    def test_06_sibling_write_in_prebound_root_admitted(self):
        target=self.root/"p194_sibling_root"
        events=[]
        self.assertEqual(self.reader.read(REL,on_open=lambda _:
            events.append(self.child("write_sibling",self.source,target))),self.sealed)
        self.assertTrue(events[0]["succeeded"])

    def test_07_cross_process_ADS_while_leaf_handle_held_refused_postscan(self):
        results=[]
        stream=str(self.source)+":p191_cross_process_stream"
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                                "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(REL,on_open=lambda _:
                    results.append(self.child("create_ads",self.source)))
            self.assertTrue(results[0]["succeeded"])
        finally:
            if ":p191_cross_process_stream:$DATA" in (
                 p188.Win32SourceInspectionCandidate.streams(self.source)):
                os.remove(stream)

    def test_08_cross_process_hardlink_while_leaf_handle_held_refused(self):
        link=self.root/"p194_hardlink"
        results=[]
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                                       "HARDLINK_OR_LINKCOUNT_INVALID"):
                self.reader.read(REL,on_open=lambda _:
                    results.append(self.child("create_hardlink",self.source,link)))
            self.assertTrue(results[0]["succeeded"])
        finally:
            if link.exists():link.unlink()

    def test_09_original_B_main_stream_mutation_refused_even_same_file_ID(self):
        self.source.write_bytes(self.sealed+b"\n# P194 synthetic corruption")
        with self.assertRaisesRegex(p190.SourceDenied,
                                  "ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH"):
            self.reader.read(REL)

    def test_10_preexisting_NTFS_ADS_refused_even_pinned_original_FileId(self):
        stream=str(self.source)+":p194_not_authorized"
        with open(stream,"wb") as f:f.write(b"synthetic nonexecutable ADS canary")
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                                    "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.read(REL)
        finally:os.remove(stream)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_11_preexisting_real_ntfs_junction_parent_refused_without_leaking_handle(self):
        directory=self.source.parent
        moved=self.root/"p194_original_tests_dir"
        directory.rename(moved)
        try:
            p188.make_junction(directory,moved)
            with self.assertRaisesRegex(p190.SourceDenied,
                                   "HELD_PARENT_REPARSE_OR_NON_DIRECTORY"):
                self.reader.read(REL)
        finally:
            if directory.is_junction():directory.rmdir()
            if moved.exists() and not directory.exists():moved.rename(directory)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_12_junction_injected_after_bound_root_before_component_refused(self):
        directory=self.source.parent
        moved=self.root/"p194_displaced_tests_dir"
        injected=[]
        def replacement(parent,name,is_dir):
            if name=="tests" and is_dir and not injected:
                directory.rename(moved)
                p188.make_junction(directory,moved)
                injected.append(True)
        try:
            with self.assertRaisesRegex(p190.SourceDenied,
                                   "HELD_PARENT_REPARSE_OR_NON_DIRECTORY"):
                self.reader.read(REL,on_component=replacement)
            self.assertTrue(injected)
        finally:
            if directory.is_junction():directory.rmdir()
            if moved.exists() and not directory.exists():moved.rename(directory)

    def test_13_root_metadata_query_failure_fails_closed_and_releases_handles(self):
        actual=self.reader._parent_snapshot
        def fail(h,path):
            if path==self.root:
                raise p190.SourceDenied("SYNTHETIC_UNTRUSTED_ROOT_METADATA")
            return actual(h,path)
        with mock.patch.object(self.reader,"_parent_snapshot",side_effect=fail):
            with self.assertRaisesRegex(p190.SourceDenied,
                             "SYNTHETIC_UNTRUSTED_ROOT_METADATA"):
                self.reader.read(REL)
        self.assertEqual(self.reader.read(REL),self.sealed)

    def test_14_prebound_manifest_cannot_be_self_enrolled_from_corrupt_bytes(self):
        with self.assertRaisesRegex(p190.SourceDenied,
                                   "TRUST_ENROLLMENT_ORIGINAL_B_SHA_MISMATCH"):
            bind_verified_fixture(self.root,self.sealed+b"unapproved")
        self.assertEqual(self.reader.read(REL),self.sealed)

def native_unittest(path:Path,selector:str,output:Path,head:str,
                    expected:int,env:dict,timeout:int)->dict:
    if not path.is_dir() or git("rev-parse","HEAD",root=path).decode().strip()!=head:
        raise RuntimeError("P194 old source HEAD drift for "+selector)
    runenv=dict(env,GITHUB_SHA=head,PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1")
    for key in list(runenv):
        if key in ("GITHUB_TOKEN","GH_TOKEN","P194_ARCHIVE_TOKEN") or key.endswith(("_API_KEY","_SECRET")):
            runenv.pop(key,None)
    with output.open("wb") as file:
        proc=subprocess.run([sys.executable,"-B","-m","unittest","-v",selector],
                     cwd=path,env=runenv,stdin=subprocess.DEVNULL,
                     stdout=file,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    raw=output.read_bytes()
    text=raw.decode("utf8","replace").replace("\r\n","\n")
    return {"original_source_SHA":head,"raw_log":output.name,
            "raw_log_SHA256":sha(raw),"actual_OS_exit":proc.returncode,
            "expected_cases":expected,
            "footer_counts":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M),
            "complete_OK":bool(re.search(r"^OK\s*$",text,re.M)),
            "real_FileId_pin_events":re.findall(r"P194_(?:PREBOUND|IDENTICAL|EXTERNAL)_[^\r\n]+",text),
            "named_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",text,re.M)}
def require_pass(r:dict):
    if (r["actual_OS_exit"]!=0
        or r["footer_counts"]!=[str(r["expected_cases"])]
        or not r["complete_OK"]):
        raise RuntimeError("P194 original source-bound Win32 suite FAIL: "+
                           r["raw_log"]+" "+repr(r["named_FAIL_ERROR"]))

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p194-prebound-windows-fileid"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
        "checkpoint":"P194","historical_H":"HOLD",
        "current_C":"ISOLATED_PREBOUND_WIN32_ROOT_ANCESTOR_LEAF_FILEID_EXPERIMENT",
        "production_R":"HOLD",
        "complete_native_full_product_regressions":"0/3",
        "qualified_external_security_reviews":REVIEWS,
        "privileged_G0_G6":"OPEN","signed_main_helper_installer_SAC_WDAC_GO":False,
        "P193_untrusted_identical_byte_ancestor":"DENIED_ONLY_WITH_PRIOR_TEST_FILEID_PINS",
        "source_immutable_sealed_B_SHA_preserved":True,
        "P189_original_full_historical_B_ADS_gap":"CONFIRMED_UNPATCHED",
        "trusted_signed_durable_source_root_identity_authority":"NOT_ESTABLISHED",
        "real_provider_production_source_root_binding":"NOT_INTEGRATED",
        "rapid_reversible_ADS_hardlink_ABA_proof":"NOT_ESTABLISHED",
        "complete_historical_Git_index_tree_HEAD_phase10_admission":"NOT_INTEGRATED",
        "P135_P175_P178_P179_original_full_product_failures":"UNWAIVED",
    }
    complete=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["original_P193_evidence"]=authenticate_original_p193(
             os.environ.get("P194_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        old=[
          ("P189","P194_EXACT_P189_ROOT",p190.P189,
            "scripts.p189_windows_original_full_b_physical_alias_verdict.P189ActualOriginalFullBPhysicalAliasVerdict",4),
          ("P190","P194_EXACT_P190_ROOT",p191.P190,
            "scripts.p190_windows_handle_bound_source_probe.P190ActualHandleBoundWin32Tests",10),
          ("P191","P194_EXACT_P191_ROOT",p192.P191,
            "scripts.p191_windows_cross_process_source_race_witness.P191ActualCrossProcessWindowsRaceCases",10),
          ("P192","P194_EXACT_P192_ROOT",p193.P192,
            "scripts.p192_windows_stable_parent_handle_identity.P192ActualStableParentWin32Tests",12),
          ("P193","P194_EXACT_P193_ROOT",P193,
            "scripts.p193_windows_nt_relative_trusted_root_source.P193NativeWindowsRootRelativeCases",14),
        ]
        ledger["original_source_era_native"]={}
        for era,envvar,head,selector,n in old:
            path=Path(os.environ[envvar])
            if path.resolve()==ROOT.resolve():
                raise RuntimeError("P194 original source clone overlaps new source")
            r=native_unittest(path,selector,
                 out/("p194_original_exact_"+era+"_native_Windows_"+str(n)+".log"),
                 head,n,env,180)
            ledger["original_source_era_native"][era]=r
            require_pass(r)
        now=native_unittest(ROOT,
             "scripts.p194_windows_prebound_source_fileid_authority.P194PreboundTrueWindowsSecurityCases",
             out/"p194_current_prebound_Windows_FileId_14.log",
             os.environ["GITHUB_SHA"],14,env,180)
        ledger["current_P194_native"]=now
        require_pass(now)
        markers=now["real_FileId_pin_events"]
        for needed in (
          "P194_IDENTICAL_BYTES_DIFFERENT_ANCESTOR_FILEID=REFUSED",
          "P194_IDENTICAL_BYTES_DIFFERENT_LEAF_FILEID=REFUSED",
          "P194_IDENTICAL_BYTES_ALTERNATE_ROOT_FILEID=REFUSED",
        ):
            if not any(needed in x for x in markers):
                raise RuntimeError("P194 missing real original-source negative custody evidence "+needed)
        after=custody()
        ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P194 source custody before/after drifted")
        complete=True
        print("P194_PRIOR_EXACT_P189_4_P190_10_P191_10_P192_12_P193_14=50/50_NATIVE_PASS",flush=True)
        print("P194_CURRENT_PREBOUND_NATIVE_WINDOWS_14=14/14_PASS",flush=True)
        print("P194_SOURCE_SEPARATED_SELECTED_WIN32=64/64_PASS_NOT_FULL_PRODUCT",flush=True)
        print("P194_P193_IDENTICAL_BYTES_DIFFERENT_ROOT_CHILD_LEAF_FILEIDS=NOW_REFUSED",flush=True)
        print("P194_REAL_DURABLE_TRUST_AUTHORITY_AND_SOURCE_INDEX_EQUIVALENCE=UNPROVEN",flush=True)
        print("P194_EXTERNAL_REVIEW=OPEN|FULL_PRODUCT_WINDOWS=0/3|RELEASE=HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P194_PREBOUND_ROOT_SECURITY_NATIVE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=complete
        (out/"p194_prebound_source_root_FileId_HCR_ledger.json").write_text(
              json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":
    raise SystemExit(main())
