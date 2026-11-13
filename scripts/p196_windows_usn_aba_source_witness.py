"""P196: genuine Windows NTFS per-file USN witness on P194 held HANDLE.

ISOLATED SECURITY DIAGNOSTIC ONLY. Neither USN metadata nor two observations
constitute an atomic transaction or independent initial root trust. No product
verifier, installer, credential, signer, or frozen historical test is modified.
"""
from __future__ import annotations
import ctypes, hashlib, io, json, os, re, subprocess, sys, zipfile
from ctypes import wintypes
from pathlib import Path
from unittest import mock
from scripts import p195_windows_durable_root_authority_aba_review as p195
from scripts import p194_windows_prebound_source_fileid_authority as p194
from scripts import p190_windows_handle_bound_source_probe as win
from scripts import p188_windows_physical_source_alias_race_witness as aliases
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B
import unittest

ROOT=Path(__file__).resolve().parents[1]
P195="56ff1722a4704c28b228d5f6d5137227bde7ded2"
BRANCH="byok-c1-p196-usn-aba-source-alias-recovery-20261113"
NEW={
 ".github/workflows/p196-windows-usn-aba-witness.yml",
 "docs/byok-c1-p196-usn-alias-witness-security-review.md",
 "scripts/p196_windows_usn_aba_source_witness.py",
}
ARTIFACT=14065617573
ZIP_SHA="82881132D15908E19D4F1761C91D2247C6914F5061640A02007BA2C3F438DF14"
LOG_NAME="p195_native_Windows_22_security_cases.log"
LOG_SHA="7D3AEEC639EE07AD2787F76EB1A657E595F9CEC2F5D809817E7EFC44EF4A2B98"
LEDGER_NAME="p195_source_authority_ABA_HCR_ledger.json"
LEDGER_SHA="46767CC7CF66809D595EBC1D6B4036382A3C8D186CB0824D04115D59A344DAB5"
FSCTL_READ_FILE_USN_DATA=0x000900EB

def sha(raw:bytes)->str: return hashlib.sha256(raw).hexdigest().upper()
def git(*args:str)->bytes: return p194.git(*args)

def custody()->dict:
    # Source identity is mandatory: no local Kristian product checkout permitted.
    actual_head=git("rev-parse","HEAD").decode().strip()
    expected_parent=git("merge-base",P195,"HEAD").decode().strip()
    diff=set(git("diff","--name-only",P195,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=actual_head or
        git("branch","--show-current").decode().strip()!=BRANCH or
        expected_parent!=P195 or diff!=NEW or dirty):
        raise RuntimeError("P196 genuine hosted Windows source custody refused: "+
                           json.dumps({"actual_head":actual_head,"ancestor":expected_parent,
                                       "diff":sorted(diff),"dirty":dirty[:450]}))
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P195+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P196 protected product or frozen security tests changed")
    if git("show",P195+":scripts/p195_windows_durable_root_authority_aba_review.py")!=(
       ROOT/"scripts/p195_windows_durable_root_authority_aba_review.py").read_bytes():
        raise RuntimeError("P196 original P195 ABA witness rewritten")
    return {"P196_HEAD":actual_head,"exact_P195_parent":P195,
            "only_three_additive_review_files":sorted(NEW),
            "original_security_tests_product_and_P195_witness_preserved":True}

def authenticate_original_p195(token:str)->dict:
    if len(token)<8: raise RuntimeError("P196 original P195 evidence authentication unavailable")
    raw=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(raw)!=ZIP_SHA: raise RuntimeError("P196 original P195 ZIP digest invalid")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!={LOG_NAME,LEDGER_NAME}:
            raise RuntimeError("P196 original P195 ZIP members/CRC changed")
        log=z.read(LOG_NAME); evidence=z.read(LEDGER_NAME)
        if sha(log)!=LOG_SHA or sha(evidence)!=LEDGER_SHA:
            raise RuntimeError("P196 original P195 raw log/ledger SHA mismatch")
        text=log.decode("utf8","replace").replace("\r\n","\n")
        if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)!=["22"] or
            not re.search(r"^OK\s*$",text,re.M) or
            "P195_ADS_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP" not in text or
            "P195_HARDLINK_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP" not in text):
            raise RuntimeError("P196 original P195 real ABA observation/log footer invalid")
        led=json.loads(evidence)
        native=led.get("current_native",{})
        if (led.get("checkpoint")!="P195" or led.get("historical_H")!="HOLD" or
            led.get("production_R")!="HOLD" or
            led.get("source_before")!=led.get("source_after") or
            led.get("source_before",{}).get("P195_HEAD")!=P195 or
            native.get("OS_exit")!=0 or native.get("raw_log_SHA256")!=LOG_SHA or
            native.get("footer")!=["22"] or
            led.get("full_product_native_Windows_regressions")!="0/3" or
            led.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P196 original P195 genuine H/C/R/source-identity drift")
    return {"authenticated_original_P195_artifact":ARTIFACT,
            "ZIP_SHA256":ZIP_SHA,"historical_selected_native_Windows":"22/22",
            "ABA_original_ADS_and_hardlink":"ADMITTED_IN_P195_EXPERIMENT",
            "release":"HOLD"}

class UsnGuardedSourceReader(p194.PreboundWin32SourceReader):
    """Proof-of-concept fail-closed LAST-file-USN change witness.

    Not a volume-wide journal proof and not authoritative root attestation.
    Extends P194 unchanged tuple so original FileId, ADS, hardlink, SHA, and
    relative open checks remain active. Not integrated in production.
    """
    def __init__(self,root:Path,anchor:p194.SyntheticPreboundFileIds):
        super().__init__(root,anchor)
        self.usn_observed=[]
        self.api.DeviceIoControl.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.c_void_p,
            wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]
        self.api.DeviceIoControl.restype=wintypes.BOOL

    @staticmethod
    def parse_usn_record(raw:bytes)->int:
        if len(raw)<8: raise win.SourceDenied("USN_RECORD_TOO_SHORT")
        n=int.from_bytes(raw[:4],"little")
        version=int.from_bytes(raw[4:6],"little")
        offset={2:24,3:40}.get(version)
        if offset is None: raise win.SourceDenied("UNSUPPORTED_USN_RECORD_VERSION")
        if n<offset+8 or n>len(raw) or n>4096:
            raise win.SourceDenied("MALFORMED_USN_RECORD_LENGTH")
        usn=int.from_bytes(raw[offset:offset+8],"little",signed=True)
        if usn<=0:raise win.SourceDenied("INVALID_FILE_USN_RECORD_DIAGNOSTIC_SIZE_"+str(len(raw))+"_VERSION_"+str(version)+"_RAWHEX_"+raw[:88].hex())
        return usn

    def _last_file_usn(self,handle)->int:
        buf=ctypes.create_string_buffer(4096)
        returned=wintypes.DWORD(0)
        ok=self.api.DeviceIoControl(
            handle,FSCTL_READ_FILE_USN_DATA,None,0,buf,
            ctypes.sizeof(buf),ctypes.byref(returned),None)
        if not ok:
            raise win.SourceDenied("FILE_USN_WITNESS_UNAVAILABLE_FAIL_CLOSED_WINERROR_"+
                                   str(ctypes.get_last_error()))
        return self.parse_usn_record(buf.raw[:returned.value])

    def _handle_identity(self,handle,path:Path)->tuple:
        base=super()._handle_identity(handle,path)
        usn=self._last_file_usn(handle)
        self.usn_observed.append(usn)
        return (*base,usn)

class P196NativeUsnReview(p195.P195NativeWindowsReview):
    """Preserves unchanged P194 14 + P195 8 tests; adds 8 P196 experiments."""
    def setUp(self):
        # D: hosted runner is NTFS but lacks a USN journal (Error 1179).
        # Use only pre-existing C: user temp, confirmed via read-only fsutil.
        # Preserve runner.temp on D: for authentic log/ledger upload.
        original=os.environ["RUNNER_TEMP"]
        home=Path(os.environ["LOCALAPPDATA"])/"Temp"
        if home.drive.upper()!="C:" or not home.is_dir():
            raise RuntimeError("P196 independently witnessed C: user temporary volume absent")
        os.environ["RUNNER_TEMP"]=str(home)
        try:
            super().setUp()
        finally:
            os.environ["RUNNER_TEMP"]=original
        print("P196_FIXTURE_SOURCE_VOLUME=C_ACTIVE_JOURNAL_ONLY|RUNNER_ARTIFACT_VOLUME=UNCHANGED",flush=True)
    def guarded(self):
        # P195 signature/physical FileId authority is still synthetic only.
        verified=p195.load(self.record,self.root,self.public,7)
        return UsnGuardedSourceReader(self.root,verified.prebound)

    def test_23_real_same_handle_usn_read_and_original_source_admitted(self):
        reader=self.guarded()
        self.assertEqual(reader.read(B.SELF),self.sealed)
        self.assertEqual(len(reader.usn_observed),2)
        self.assertGreater(reader.usn_observed[0],0)
        self.assertEqual(reader.usn_observed[0],reader.usn_observed[1])
        print("P196_ORIGINAL_SOURCE_USN_STABLE=ADMITTED|USN_READ_REAL_WINDOWS",flush=True)

    def test_24_legitimate_parent_sibling_write_leaves_leaf_USN_stable(self):
        reader=self.guarded()
        child=self.source.parent/"p196-unrelated-sibling"
        self.assertEqual(reader.read(B.SELF,on_open=lambda _:self.assertTrue(
            self.child("write_sibling",self.source,child)["succeeded"])),self.sealed)
        self.assertEqual(len(reader.usn_observed),2)
        self.assertEqual(reader.usn_observed[0],reader.usn_observed[1])
        print("P196_LEGITIMATE_SIBLING_WRITE_USN_STABLE=ADMITTED",flush=True)

    def test_25_real_cross_process_ADS_create_remove_ABA_refused_by_last_USN(self):
        reader=self.guarded()
        childlog=[]
        stream=str(self.source)+":p191_cross_process_stream"
        def mutation(_):
            created=self.child("create_ads",self.source)
            self.assertTrue(created["succeeded"])
            removed=self._remove_other_process(stream)
            self.assertTrue(removed["removed"],str(removed))
            childlog.extend([created,removed])
            print("P196_ADS_ABA_OS_CREATED_AND_REMOVED=TRUE",flush=True)
        try:
            with self.assertRaisesRegex(win.SourceDenied,"HANDLE_ID_OR_SOURCE_METADATA_DRIFT"):
                reader.read(B.SELF,on_open=mutation)
            self.assertEqual(len(childlog),2)
            self.assertEqual(len(reader.usn_observed),2)
            self.assertNotEqual(*reader.usn_observed)
            print("P196_ADS_ABA=REFUSED_BY_REAL_FILE_USN_DRIFT",flush=True)
        finally:
            if ":p191_cross_process_stream:$DATA" in aliases.Win32SourceInspectionCandidate.streams(self.source):
                os.unlink(stream)

    def test_26_real_cross_process_hardlink_create_remove_ABA_refused_by_USN(self):
        reader=self.guarded()
        childlog=[]
        link=self.root/"p196-external-hardlink"
        def mutation(_):
            created=self.child("create_hardlink",self.source,link)
            self.assertTrue(created["succeeded"])
            removed=self._remove_other_process(link)
            self.assertTrue(removed["removed"],str(removed))
            childlog.extend([created,removed])
            print("P196_HARDLINK_ABA_OS_CREATED_AND_REMOVED=TRUE",flush=True)
        try:
            with self.assertRaisesRegex(win.SourceDenied,"HANDLE_ID_OR_SOURCE_METADATA_DRIFT"):
                reader.read(B.SELF,on_open=mutation)
            self.assertEqual(len(childlog),2)
            self.assertEqual(len(reader.usn_observed),2)
            self.assertNotEqual(*reader.usn_observed)
            print("P196_HARDLINK_ABA=REFUSED_BY_REAL_FILE_USN_DRIFT",flush=True)
        finally: link.unlink(missing_ok=True)

    def test_27_unavailable_usn_provenance_denies_even_original_bytes(self):
        reader=self.guarded()
        with mock.patch.object(reader,"_last_file_usn",
               side_effect=win.SourceDenied("SIMULATED_USN_WITNESS_UNAVAILABLE")):
            with self.assertRaisesRegex(win.SourceDenied,"SIMULATED_USN_WITNESS_UNAVAILABLE"):
                reader.read(B.SELF)
        print("P196_UNAVAILABLE_USN_EVIDENCE=FAIL_CLOSED",flush=True)

    def test_28_malformed_and_unsupported_usn_records_fail_closed(self):
        for raw in (b"",b"\0"*12,
                    (64).to_bytes(4,"little")+(9).to_bytes(2,"little")+b"\0"*60,
                    (1000).to_bytes(4,"little")+(2).to_bytes(2,"little")+b"\0"*54,
                    (64).to_bytes(4,"little")+(2).to_bytes(2,"little")+b"\0"*58):
            with self.assertRaises(win.SourceDenied):
                UsnGuardedSourceReader.parse_usn_record(raw)
        print("P196_MALFORMED_USN_RECORD=FAIL_CLOSED",flush=True)

    def test_29_signed_root_record_rollback_still_requires_external_epoch_floor(self):
        before=self.guarded()
        self.assertEqual(before.read(B.SELF),self.sealed)
        self.record.write_bytes(p195.signed(p195.payload(self.anchor,self.root,6),self.signer))
        with self.assertRaisesRegex(win.SourceDenied,"SIGNED_CLAIM_INVALID_OR_ROLLBACK"):
            self.guarded()
        self.assertEqual(p195.load(self.record,self.root,self.public,6).read(B.SELF),self.sealed)
        print("P196_USN_GUARD_DOES_NOT_PROVIDE_INDEPENDENT_ROLLBACK=OPEN",flush=True)

    def test_30_sibling_creation_at_root_does_not_refuse_unchanged_leaf_usn(self):
        reader=self.guarded()
        child=self.root/"p196-unrelated-root-sibling"
        self.assertEqual(reader.read(B.SELF,on_open=lambda _:self.assertTrue(
            self.child("write_sibling",self.source,child)["succeeded"])),self.sealed)
        self.assertEqual(reader.usn_observed[0],reader.usn_observed[1])
        print("P196_ROOT_SIBLING_WRITE_IGNORED_BY_LEAF_USN=ADMITTED",flush=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p196-native-usn"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P196","historical_H":"HOLD",
            "current_C":"EXPERIMENTAL_PER_FILE_USN_ABA_DIAGNOSTIC",
            "production_R":"HOLD","complete_unfiltered_native_Windows_full_product_regressions":"0/3",
            "qualified_independent_reviews":p194.REVIEWS,
            "privileged_G0_G6":"OPEN","signed_executable_installer_CodeIntegrity_GO":False,
            "P189_original_full_BYOK_B_ADS_gap":"CONFIRMED_UNPATCHED",
            "P195_original_ADS_hardlink_ABA_admission":"CONFIRMED",
            "P196_USN_guard_atomic_security_proof":"NOT_ESTABLISHED",
            "trusted_first_enrolment_disk_attestation":"NOT_ESTABLISHED",
            "durable_crash_safe_independent_antirollback":"NOT_ESTABLISHED",
            "complete_original_B_and_current_Phase10_integration":"NOT_ESTABLISHED",
            "P135_P175_P178_P179_PERF_P187_01":"UNWAIVED"}
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["original_authenticated_P195"]=authenticate_original_p195(
            os.environ.get("P196_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if k in ("GITHUB_TOKEN","GH_TOKEN","P196_ARCHIVE_TOKEN") or k.endswith(("_SECRET","_API_KEY")):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p196_exact_Windows_USN_30_native_cases.log"
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                  "scripts.p196_windows_usn_aba_source_witness.P196NativeUsnReview"],
                  cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
                  timeout=210,check=False)
        raw=log.read_bytes()
        txt=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"^P196_[^\r\n]+",txt,re.M)
        ledger["current_P196_native"]={"raw_log":log.name,"raw_log_SHA256":sha(raw),
            "actual_OS_exit":p.returncode,
            "footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
            "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
            "events":events}
        if (p.returncode!=0 or ledger["current_P196_native"]["footer"]!=["30"] or
            not ledger["current_P196_native"]["complete_OK"]):
            raise RuntimeError("P196 original Windows source-bound selected tests failed; retain raw logs")
        for marker in ("P196_ADS_ABA=REFUSED_BY_REAL_FILE_USN_DRIFT",
                       "P196_HARDLINK_ABA=REFUSED_BY_REAL_FILE_USN_DRIFT",
                       "P196_ORIGINAL_SOURCE_USN_STABLE=ADMITTED",
                       "P196_UNAVAILABLE_USN_EVIDENCE=FAIL_CLOSED",
                       "P196_LEGITIMATE_SIBLING_WRITE_USN_STABLE=ADMITTED"):
            if not any(marker in e for e in events):
                raise RuntimeError("P196 genuine Windows required marker absent: "+marker)
        after=custody();ledger["source_after"]=after
        if before!=after: raise RuntimeError("P196 original Git source drift")
        complete=True
        print("P196_ORIGINAL_AUTHENTIC_P195_ZIP_AND_22_TESTS=VERIFIED",flush=True)
        print("P196_SELECTED_NATIVE_WINDOWS_SOURCE_AND_USN=30/30_PASS_NOT_FULL_PRODUCT",flush=True)
        print("P196_ATOMIC_SECURITY_INDEPENDENT_ROOT_EPOCH_PHASE10=NOT_PROVEN",flush=True)
        print("P196_FULL_WINDOWS_0/3|QUALIFIED_REVIEW_OPEN|RELEASE_HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P196_USN_SECURITY_EXPERIMENT=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=complete
        (out/"p196_USN_source_ABA_HCR_ledger.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":raise SystemExit(main())
