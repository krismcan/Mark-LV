"""P188 physical Windows source alias and deterministic parent-swap witnesses.

Experimental only. Test the *actual original* 8.31 disk reader used by
historical BYOK-B, then test a separate inspection prototype in disposable
Windows directories. Never change original product/frozen code or secrets.
"""
from __future__ import annotations

import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

from scripts import p187_windows_live_byok_b_equivalence as previous
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B
from tests import phase_8_30_scope_migration as legacy30
from tests import phase_8_31_scope_migration as legacy31

ROOT=Path(__file__).resolve().parents[1]
P187="a00b888e38fad5fed06ba05190be9c2838fb0320"
BRANCH="byok-c1-p188-real-windows-hardlink-ads-junction-race-witness-20261113"
NEW={
    "scripts/p188_windows_physical_source_alias_race_witness.py",
    "docs/byok-c1-p188-real-windows-link-ads-race-security-evidence.md",
    ".github/workflows/p188-windows-source-alias-race-witness.yml",
}
ARTIFACT=14026576593
ZIP_SHA="7D76BFF5944AEF80A0821F295F542E03BBE49A3ADF8A2E298AD8EE67F0B52643"
EXPECTED_LOGS={
 "p187_exact_original_P184_Windows_12.log":("12","302628641133A256D34D27E41E5D7266FB3C0131CA3BE0C405609245FEA6E1DC"),
 "p187_exact_original_P185_Windows_12.log":("12","BD77D4AC73F7AB6DD292BC7672BA372D588A74C58DA4818FD1EA7A6E29CE3CC5"),
 "p187_exact_original_P186_Windows_12.log":("12","C92BDBCEEA5C9A4A137E72A3850596124A4C853D8166C2099E0B317809BD1345"),
 "p187_current_real_and_synthetic_Windows_13.log":("13","5A88F4A790C669AA9BDF1E83880B26FC6EA312C7700422E9DA7CFF7543C44D2C"),
}
REVIEWS=previous.REVIEWS
RELATIVE=B.SELF
SEAL=B.CANDIDATE_SHA256[RELATIVE]

def sha(payload:bytes)->str:return hashlib.sha256(payload).hexdigest().upper()

def git(*args:str,root:Path=ROOT)->bytes:
    process=subprocess.run(["git","-C",str(root),*args],
      stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
      timeout=60,check=False)
    if process.returncode:
        raise RuntimeError("P188 original Git command failed "+repr(args)
                           +" native exit="+str(process.returncode)
                           +" stderr="+process.stderr.decode("utf8","replace")[-800:])
    return process.stdout

def custody()->dict:
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",P187,"HEAD").decode().strip()!=P187
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P188 exact clean original source + hosted native Windows required")
    if set(git("diff","--name-only",P187,"HEAD").decode().splitlines())!=NEW:
        raise RuntimeError("P188 only three new audit-only paths permitted")
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P187+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P188 frozen original product or tests changed")
    for path in (
      "scripts/p182_windows_fail_closed_batch_transport.py",
      "scripts/p184_windows_fresh_historical_source_admission.py",
      "scripts/p186_windows_full_historical_envelope_witness.py",
      "scripts/p187_windows_live_byok_b_equivalence.py",
      "tests/phase8_byok_b_scope_migration.py",
      "tests/phase8_byok_scope_migration.py",
      "tests/test_phase8_byok_b_scope_integrity.py",
      "tests/phase_8_30_scope_migration.py",
      "tests/phase_8_31_scope_migration.py",
    ):
        if (ROOT/path).read_bytes()!=git("show",P187+":"+path):
            raise RuntimeError("P188 original historical source changed: "+path)
    if len(B.CANDIDATE_SHA256)!=23 or B.SELF not in B.ENVELOPE:
        raise RuntimeError("P188 authentic original B 23-pin manifest changed")
    return {"P188_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P187_parent":P187,"only_three_added_audit_paths":sorted(NEW),
            "original_B_and_all_prior_frozen_product_tests_unchanged":True}

def authenticate_original_p187(token:str)->dict:
    if len(token)<8:raise RuntimeError("P188 missing ephemeral original P187 token")
    raw=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(raw)!=ZIP_SHA:raise RuntimeError("P188 original P187 artifact ZIP digest mismatch")
    ledger_name="p187_live_original_B_workspace_index_tamper_HCR_ledger.json"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(EXPECTED_LOGS)|{ledger_name}:
            raise RuntimeError("P188 original P187 five-member ZIP integrity failed")
        for name,(count,digest) in EXPECTED_LOGS.items():
            original=z.read(name)
            text=original.decode("utf8","replace").replace("\r\n","\n")
            if (sha(original)!=digest
                or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)!=[count]
                or not re.search(r"^OK\s*$",text,re.M)):
                raise RuntimeError("P188 original P187 native log SHA/footer changed: "+name)
        record=json.loads(z.read(ledger_name))
        if (record.get("checkpoint")!="P187"
            or record.get("historical_H")!="HOLD" or record.get("production_R")!="HOLD"
            or record.get("full_product_original_native_Windows")!="0/3"
            or record.get("qualified_external_reviewer_decisions")!=REVIEWS
            or record.get("source_before")!=record.get("source_after")
            or record["source_before"].get("source_HEAD")!=P187
            or record.get("experimental_checkpoint_complete_not_product_release") is not True
            or record.get("original_production_verifier_replaced") is not False):
            raise RuntimeError("P188 previous authentic P187 H/C/R or source state drift")
    return {"original_artifact_id":ARTIFACT,"ZIP_SHA256":ZIP_SHA,
            "original_exact_source_selected_windows_tests":[12,12,12,13],
            "previous_selected_native_count":49,"H":"HOLD","R":"HOLD"}

class SourceRefusal(RuntimeError): pass

class Win32SourceInspectionCandidate:
    """Experimental observational rejection. NOT transactional Win32 HANDLE IO.

    Observes each pathname component before and after a read, file mode,
    nlink and reparse attributes, stream enumeration, Git-era immutable B
    digest. Even a PASS cannot rule out reversible/ABA concurrent writers.
    """
    def __init__(self,root:Path):
        if os.name!="nt":raise SourceRefusal("WIN32_ONLY")
        self.root=root
    @staticmethod
    def streams(path:Path)->tuple[str,...]:
        from ctypes import wintypes
        class FindStreamData(ctypes.Structure):
            _fields_=[("size",ctypes.c_int64),("name",ctypes.c_wchar*296)]
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel.FindFirstStreamW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,
                                           ctypes.POINTER(FindStreamData),wintypes.DWORD]
        kernel.FindFirstStreamW.restype=wintypes.HANDLE
        kernel.FindNextStreamW.argtypes=[wintypes.HANDLE,ctypes.POINTER(FindStreamData)]
        kernel.FindNextStreamW.restype=wintypes.BOOL
        kernel.FindClose.argtypes=[wintypes.HANDLE]
        kernel.FindClose.restype=wintypes.BOOL
        record=FindStreamData()
        handle=kernel.FindFirstStreamW(str(path),0,ctypes.byref(record),0)
        bad=ctypes.c_void_p(-1).value
        if handle is None or handle==bad:
            raise SourceRefusal("ADS_ENUMERATION_UNAVAILABLE")
        found=[record.name]
        try:
            while kernel.FindNextStreamW(handle,ctypes.byref(record)):
                found.append(record.name)
            error=ctypes.get_last_error()
            if error!=38:raise SourceRefusal("ADS_ENUMERATION_ERROR_"+str(error))
        finally:
            kernel.FindClose(handle)
        return tuple(found)
    def observe(self,path:str)->tuple:
        if (path not in B.CANDIDATE_SHA256 or not previous.previous.canonical_legacy_path(path)
            or ":" in path or "\\" in path):
            raise SourceRefusal("UNAPPROVED_PATH_ALIAS")
        current=self.root
        details=[]
        for i,part in enumerate(("",*Path(path).parts)):
            if part:current=current/part
            try:info=current.lstat()
            except OSError as exc:raise SourceRefusal("MISSING_OR_UNREADABLE_PATH") from exc
            attrs=getattr(info,"st_file_attributes",0)
            if stat.S_ISLNK(info.st_mode) or (attrs & 0x400):
                raise SourceRefusal("REPARSE_OR_SYMLINK")
            last=(i==len(Path(path).parts))
            if last:
                if not stat.S_ISREG(info.st_mode):raise SourceRefusal("NONREGULAR_SOURCE")
                if info.st_nlink!=1:raise SourceRefusal("HARDLINK_MULTIPLE_LINKS")
                streams=self.streams(current)
                if set(streams)!={"::$DATA"}:
                    raise SourceRefusal("UNAPPROVED_ADS_STREAM")
            elif not stat.S_ISDIR(info.st_mode):
                raise SourceRefusal("NON_DIRECTORY_PARENT")
            details.append((info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns,
                            info.st_ino,info.st_dev,attrs))
        return tuple(details)
    def read(self,path:str,*,reader=None)->bytes:
        first=self.observe(path)
        current=self.root/path
        raw=reader(current) if reader is not None else current.read_bytes()
        if not isinstance(raw,bytes):raise SourceRefusal("MALFORMED_SOURCE_BYTES")
        if B._digest(path,raw)!=B.CANDIDATE_SHA256[path]:
            raise SourceRefusal("BYOK_B_IMMUTABLE_SOURCE_PIN_MISMATCH")
        second=self.observe(path)
        if first!=second:raise SourceRefusal("OBSERVED_FILE_OR_PARENT_CHANGE")
        return raw

def make_junction(alias:Path,target:Path)->None:
    # Native PowerShell FileSystem provider creates a true NTFS junction in
    # this disposable host-owned directory; avoid cmd.exe /c quote folding.
    safe_alias=str(alias).replace("'","''")
    safe_target=str(target).replace("'","''")
    operation=("New-Item -ItemType Junction -Path '"+safe_alias+
               "' -Target '"+safe_target+"' -ErrorAction Stop | Out-Null")
    cmd=["powershell.exe","-NoProfile","-NonInteractive","-Command",operation]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     timeout=25,check=False)
    if p.returncode!=0 or not alias.is_junction():
        raise RuntimeError("P188 native Windows disposable junction unavailable: "+
                           (p.stdout+p.stderr).decode("utf8","replace")[-1300:])

class P188NativePhysicalWindowsSourceCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P188 genuine native Windows required")
        cls.temporary=tempfile.TemporaryDirectory(prefix="p188-source-",dir=os.environ["RUNNER_TEMP"])
        cls.root=Path(cls.temporary.name)
        cls.rel=RELATIVE
        cls.sealed=git("show",previous.B_COMMIT+":"+cls.rel)
        if B._digest(cls.rel,cls.sealed)!=SEAL:
            raise RuntimeError("P188 original B sealed source bytes did not match SHA256 pin")
        cls.source=cls.root/cls.rel
        cls.source.parent.mkdir(parents=True,exist_ok=True)
        cls.source.write_bytes(cls.sealed)
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"temporary"):cls.temporary.cleanup()
    def setUp(self):
        self.source.write_bytes(self.sealed)
        self.root_probes=(
            mock.patch.object(legacy30,"ROOT",self.root),
            mock.patch.object(legacy31,"ROOT",self.root),
        )
        for patcher in self.root_probes:patcher.start()
        self.addCleanup(lambda:[p.stop() for p in reversed(self.root_probes)])
    def normal(self):
        return Win32SourceInspectionCandidate(self.root)
    def assert_original_disk_read(self):
        self.assertEqual(legacy31._disk(self.rel),legacy30._normal(self.sealed))
    def make_parent_junction(self):
        original=self.source.parent
        displaced=self.root/"original_tests_directory"
        original.rename(displaced)
        try:make_junction(original,displaced)
        except BaseException:
            displaced.rename(original)
            raise
        return original,displaced
    @staticmethod
    def restore_parent(alias:Path,physical:Path):
        if alias.is_junction():alias.rmdir()
        if not alias.exists() and physical.exists():physical.rename(alias)

    def test_01_source_is_original_sealed_B_not_new_current_branch_bytes(self):
        self.assertEqual(B._digest(self.rel,self.sealed),SEAL)
        self.assertEqual(len(B.CANDIDATE_SHA256),23)
        self.assertEqual(B.PARENT,previous.previous.A_COMMIT)

    def test_02_normal_original_B_source_accepted_by_old_reader_and_new_probe(self):
        self.assert_original_disk_read()
        self.assertEqual(self.normal().read(self.rel),self.sealed)

    def test_03_physical_hardlink_original_disk_reader_accepts_probe_refuses(self):
        alias=self.root/"other_hardlink_copy_of_B"
        os.link(self.source,alias)
        try:
            self.assertGreater(self.source.stat().st_nlink,1)
            self.assert_original_disk_read()
            with self.assertRaisesRegex(SourceRefusal,"HARDLINK_MULTIPLE_LINKS"):
                self.normal().read(self.rel)
        finally:
            alias.unlink()

    def test_04_real_NTFS_ADS_original_base_reader_accepts_probe_refuses(self):
        stream=str(self.source)+":p188_test_stream"
        with open(stream,"wb") as f:f.write(b"non-executable synthetic ADS canary")
        try:
            self.assert_original_disk_read()
            self.assertIn(":p188_test_stream:$DATA",self.normal().streams(self.source))
            with self.assertRaisesRegex(SourceRefusal,"UNAPPROVED_ADS_STREAM"):
                self.normal().read(self.rel)
        finally:
            try:os.remove(stream)
            except FileNotFoundError:pass

    def test_05_physical_NTFS_junction_parent_old_reader_and_probe_refuse(self):
        junction,physical=self.make_parent_junction()
        try:
            with self.assertRaisesRegex(AssertionError,"Linked or reparse production parent"):
                legacy31._disk(self.rel)
            with self.assertRaisesRegex(SourceRefusal,"REPARSE_OR_SYMLINK"):
                self.normal().read(self.rel)
        finally:
            self.restore_parent(junction,physical)

    def test_06_source_byte_change_after_preobservation_denies_before_acceptance(self):
        def changed(path):
            path.write_bytes(self.sealed+b"\n# isolated P188 wrong bytes")
            return path.read_bytes()
        with self.assertRaisesRegex(SourceRefusal,"BYOK_B_IMMUTABLE_SOURCE_PIN_MISMATCH"):
            self.normal().read(self.rel,reader=changed)

    def test_07_parent_replaced_by_junction_during_read_is_denied_on_postobservation(self):
        items=[]
        def raced(path):
            junction,physical=self.make_parent_junction()
            items.append((junction,physical))
            return path.read_bytes()
        try:
            with self.assertRaisesRegex(SourceRefusal,"REPARSE_OR_SYMLINK"):
                self.normal().read(self.rel,reader=raced)
        finally:
            for junction,physical in reversed(items):
                self.restore_parent(junction,physical)

    def test_08_canonical_windows_alias_and_wrong_historical_path_refused(self):
        for path in ("tests/../phase8_byok_b_scope_migration.py",
                     self.rel+":stream","tests\\phase8_byok_b_scope_migration.py",
                     "tests/p188_unapproved_source_alias.py"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(SourceRefusal,"UNAPPROVED_PATH_ALIAS"):
                    self.normal().read(path)

    def test_09_no_cached_success_after_source_poison_and_then_restore(self):
        reader=self.normal()
        self.assertEqual(reader.read(self.rel),self.sealed)
        self.source.write_bytes(self.sealed+b"X")
        with self.assertRaisesRegex(SourceRefusal,"BYOK_B_IMMUTABLE_SOURCE_PIN_MISMATCH"):
            reader.read(self.rel)
        self.source.write_bytes(self.sealed)
        self.assertEqual(reader.read(self.rel),self.sealed)
        # Restored content is not a Win32 atomic-transaction/ABA race proof.

def unittest_run(path:Path,selectors:list[str],output:Path,
                 expected_sha:str,expected_count:int,env:dict,timeout:int)->dict:
    if git("rev-parse","HEAD",root=path).decode().strip()!=expected_sha:
        raise RuntimeError("P188 exact historical branch HEAD drift")
    cleanenv=dict(env,GITHUB_SHA=expected_sha,PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1")
    for key in list(cleanenv):
        if key in {"GH_TOKEN","GITHUB_TOKEN","P188_ARCHIVE_TOKEN"} or key.endswith(("_API_KEY","_SECRET")):
            cleanenv.pop(key,None)
    with output.open("wb") as handle:
        proc=subprocess.run([sys.executable,"-B","-m","unittest","-v",*selectors],
                            cwd=path,env=cleanenv,stdin=subprocess.DEVNULL,
                            stdout=handle,stderr=subprocess.STDOUT,
                            timeout=timeout,check=False)
    raw=output.read_bytes()
    txt=raw.decode("utf8","replace").replace("\r\n","\n")
    footers=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)
    return {"source_SHA":expected_sha,"native_exit":proc.returncode,
            "selected_expected":expected_count,
            "actual_footer_counts":footers,"footer_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
            "raw_log":output.name,"raw_SHA256":sha(raw),
            "original_named_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}

def require_pass(outcome:dict)->None:
    if (outcome["native_exit"]!=0
        or outcome["actual_footer_counts"]!=[str(outcome["selected_expected"])]
        or not outcome["footer_OK"]):
        raise RuntimeError("P188 original native source-bound test scope failed: "+
                           outcome["raw_log"]+" "+repr(outcome["original_named_FAIL_ERROR"]))

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p188-physical-windows-security"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
      "checkpoint":"P188","historical_H":"HOLD",
      "current_C":"ISOLATED_PHYSICAL_WINDOWS_DISK_ALIAS_ADS_JUNCTION_RACE_WITNESS_ONLY",
      "production_R":"HOLD","full_product_native_windows_regressions":"0/3",
      "qualified_independent_review":REVIEWS,"privileged_G0_G6":"OPEN",
      "signed_installer_main_helper_SAC_WDAC_GO":False,
      "original_product_and_frozen_tests_modified":False,
      "original_8_31_component_hardlink_and_ADS_acceptance":"SECURITY_GAP_IF_NATIVE_CONFIRMED",
      "atomic_win32_no_follow_handle_race_proof":"NOT_ESTABLISHED",
      "all_original_P135_P175_P178_P179_failures":"UNWAIVED",
    }
    accepted=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["P187_authenticated"]=authenticate_original_p187(
             os.environ.get("P188_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        prior_runs=[
          ("P184","P188_ORIGINAL_P184_ROOT",
           "a66a5221ab74d0b7f65fd381c554f186cd6c8ed1",
           "scripts.p184_windows_fresh_historical_source_admission.P184FreshHistoricalSourceAdmissionTests",12),
          ("P185","P188_ORIGINAL_P185_ROOT",
           "68b338723ba9130be071289c7662c9d68db748f4",
           "scripts.p185_windows_historical_tag_parent_seal_admission.P185HistoricalTagSealAdmissionTests",12),
          ("P186","P188_ORIGINAL_P186_ROOT",previous.P186,
           "scripts.p186_windows_full_historical_envelope_witness.P186OriginalFullHistoricalPinEnvelopeCases",12),
          ("P187","P188_ORIGINAL_P187_ROOT",P187,
           "scripts.p187_windows_live_byok_b_equivalence.P187RealWindowsDisposableWorktreeTests",6),
        ]
        ledger["exact_source_branch_original_windows"]={}
        for name,var,head,selector,count in prior_runs:
            path=Path(os.environ[var])
            if not path.is_dir() or path.resolve()==ROOT.resolve():
                raise RuntimeError("P188 missing independent original "+name+" Windows clone")
            r=unittest_run(path,[selector],
              out/("p188_original_exact_"+name+"_native_Windows_"+str(count)+".log"),
              head,count,env,150)
            ledger["exact_source_branch_original_windows"][name]=r
            require_pass(r)
        current=unittest_run(ROOT,[
           "scripts.p188_windows_physical_source_alias_race_witness.P188NativePhysicalWindowsSourceCases",
        ],out/"p188_current_real_NTFS_hardlink_ADS_junction_race_9.log",
          os.environ["GITHUB_SHA"],9,env,150)
        ledger["P188_current_real_Windows"]=current
        require_pass(current)
        # Frozen historical negative remains unmodified; run diagnostically,
        # preserve native exit (possibly FAIL) and never count as P188 PASS.
        diagnostic=unittest_run(ROOT,[
           "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_disk_readers_refuse_links_reparse_and_hardlinks"
        ],out/"p188_diagnostic_original_frozen_B_link_reparse_hardlink.log",
          os.environ["GITHUB_SHA"],1,env,130)
        ledger["original_frozen_B_diagnostic_not_waived"]=diagnostic
        after=custody()
        ledger["source_after"]=after
        if before!=after:raise RuntimeError("P188 original frozen source drift during native tests")
        accepted=True
        print("P188_ORIGINAL_P184_12_P185_12_P186_12_P187_6=42/42_TRUE_SOURCE_NATIVE_PASS",flush=True)
        print("P188_PHYSICAL_NTFS_ALIAS_ADS_JUNCTION_AND_RACE_TESTS=9/9_PASS",flush=True)
        print("P188_ORIGINAL_8_31_HARDLINK_ADS_ACCEPTANCE=GAP_WITNESSED_NOT_RELEASE",flush=True)
        print("P188_SEPARATE_INSPECTION_PROBE=EXPERIMENT_ONLY_NOT_ATOMIC_OR_INTEGRATED",flush=True)
        print("P188_FROZEN_B_DIAGNOSTIC_NATIVE_EXIT="+str(diagnostic["native_exit"]),flush=True)
        print("P188_FULL_PRODUCT_REGRESSIONS=0/3|QUALIFIED_EXTERNAL_REVIEW=OPEN|RELEASE=HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P188_AUTHENTIC_NATIVE_WINDOWS_FILESYSTEM_WITNESSES=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_not_product_admission"]=accepted
        (out/"p188_source_bound_NTFS_alias_race_security_HCR_ledger.json").write_text(
             json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if accepted else 1

if __name__=="__main__":
    raise SystemExit(main())
