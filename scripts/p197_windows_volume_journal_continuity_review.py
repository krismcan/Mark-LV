"""P197: Windows NTFS volume-journal continuity / rollback lab audit.

Read-only OS volume queries and disposable C: source fixtures only.
Synthetic journal replacement is a TEST INJECTION, not a real journal reset.
No privileged production commands, real signing keys, or product gate edits.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import ctypes, hashlib, io, json, os, re, subprocess, sys, zipfile
from ctypes import wintypes
from pathlib import Path
from unittest import mock
import unittest
from scripts import p196_windows_usn_aba_source_witness as p196
from scripts import p195_windows_durable_root_authority_aba_review as p195
from scripts import p194_windows_prebound_source_fileid_authority as p194
from scripts import p190_windows_handle_bound_source_probe as win
from scripts import p188_windows_physical_source_alias_race_witness as aliases
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P196="b5c37f3e718e7d9e75a0bc891b6a8dd237f7a1e6"
BRANCH="byok-c1-p197-volume-journal-continuity-recovery-20261113"
NEW={
 "scripts/p197_windows_volume_journal_continuity_review.py",
 "docs/byok-c1-p197-volume-journal-continuity-rollback-security-review.md",
 ".github/workflows/p197-windows-volume-journal-continuity.yml",
}
ARTIFACT=14071470076
ARCHIVE_SHA="C82F80658AE6D247ACBE3952C0CF24E7295C1FD7BC0840F9A4C9F863BAF5516D"
LOG_NAME="p196_exact_Windows_USN_30_native_cases.log"
LOG_SHA="7EC368FC2ED0B8C6639C07EE23A9452036C033739FC91014C5A36BC62D7940A3"
LEDGER_NAME="p196_USN_source_ABA_HCR_ledger.json"
LEDGER_SHA="00AF6E2D79A03982C61B86C01E4A5B4D40BA554120DEB7885EEAF2D57EA4FC1F"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest().upper()
def git(*a:str)->bytes:return p194.git(*a)

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    parent=git("merge-base",P196,"HEAD").decode().strip()
    diff=set(git("diff","--name-only",P196,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows" or
        os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=head or
        git("branch","--show-current").decode().strip()!=BRANCH or
        parent!=P196 or diff!=NEW or dirty):
        raise RuntimeError("P197 source-custody fail closed: "+json.dumps(
            {"head":head,"parent":parent,"diff":sorted(diff),"dirty":dirty[:500]}))
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P196+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P197 original product or frozen tests changed")
    for prior in ("scripts/p195_windows_durable_root_authority_aba_review.py",
                  "scripts/p196_windows_usn_aba_source_witness.py"):
        if git("show",P196+":"+prior)!=(ROOT/prior).read_bytes():
            raise RuntimeError("P197 historical negative evidence modified: "+prior)
    return {"P197_HEAD":head,"parent_exact_P196":P196,
            "only_three_new_audit_paths":sorted(NEW),
            "original_product_frozen_tests_P195_P196_unchanged":True}

def authenticate_p196(token:str)->dict:
    if len(token)<8:raise RuntimeError("P197 missing predecessor artifact token")
    raw=_download_artifact(ARTIFACT,ARCHIVE_SHA,token)
    if sha(raw)!=ARCHIVE_SHA:raise RuntimeError("P197 original P196 ZIP digest mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!={LOG_NAME,LEDGER_NAME}:
            raise RuntimeError("P197 original P196 members/CRC invalid")
        log=z.read(LOG_NAME);ledraw=z.read(LEDGER_NAME)
        if sha(log)!=LOG_SHA or sha(ledraw)!=LEDGER_SHA:
            raise RuntimeError("P197 original P196 member digests invalid")
        body=log.decode("utf8","replace").replace("\r\n","\n")
        for marker in ("P196_ADS_ABA=REFUSED_BY_REAL_FILE_USN_DRIFT",
                       "P196_HARDLINK_ABA=REFUSED_BY_REAL_FILE_USN_DRIFT",
                       "P195_ADS_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP",
                       "P195_HARDLINK_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP"):
            if marker not in body:
                raise RuntimeError("P197 preserved authentic negative witness absent: "+marker)
        if re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",body,re.M)!=["30"] or \
           not re.search(r"^OK\s*$",body,re.M):
            raise RuntimeError("P197 original complete P196 30/30 footer absent")
        led=json.loads(ledraw);native=led.get("current_P196_native",{})
        if (led.get("checkpoint")!="P196" or
            led.get("historical_H")!="HOLD" or led.get("production_R")!="HOLD" or
            led.get("complete_unfiltered_native_Windows_full_product_regressions")!="0/3" or
            led.get("source_before")!=led.get("source_after") or
            led.get("source_before",{}).get("P196_HEAD")!=P196 or
            native.get("actual_OS_exit")!=0 or native.get("raw_log_SHA256")!=LOG_SHA or
            native.get("footer")!=["30"] or not native.get("complete_OK") or
            led.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P197 original authenticated P196 source HCR invalid")
    return {"original_P196_artifact_id":ARTIFACT,
            "ZIP_SHA256":ARCHIVE_SHA,"selected_original_native_Windows":"30/30",
            "P195_ABA_admission_and_P196_file_USN_refusal":"AUTHENTICATED",
            "full_product_acceptance":"0/3","production":"HOLD"}

@dataclass(frozen=True)
class Journal:
    journal_id:int
    first_usn:int
    next_usn:int
    lowest_valid:int
    max_usn:int
    volume_serial:int
    volume_guid:str

def observe_journal(root:Path)->Journal:
    """Read-only fsutil query and GetVolume* identity, never journal management."""
    drive=root.drive.upper()
    if drive!="C:":raise win.SourceDenied("P197_ONLY_EXISTING_C_JOURNAL_FIXTURE_ALLOWED")
    try:
        proc=subprocess.run(["fsutil","usn","queryjournal",drive],
          stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
          timeout=15,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:
        raise win.SourceDenied("VOLUME_USN_QUERY_UNAVAILABLE") from e
    if proc.returncode!=0:
        raise win.SourceDenied("VOLUME_USN_QUERY_OS_REFUSED_EXIT_"+str(proc.returncode))
    output=proc.stdout.decode("utf8","replace")
    names={"journal_id":"Usn Journal ID","first_usn":"First Usn",
           "next_usn":"Next Usn","lowest_valid":"Lowest Valid Usn",
           "max_usn":"Max Usn"}
    fields={}
    for field,label in names.items():
        match=re.search(r"(?im)^\s*"+re.escape(label)+r"\s*:\s*0x([0-9A-Fa-f]+)\b",output)
        if not match:raise win.SourceDenied("VOLUME_USN_FIELD_UNAVAILABLE_"+field)
        fields[field]=int(match.group(1),16)
    if (fields["journal_id"]<=0 or fields["next_usn"]<=0 or
        fields["max_usn"]<=fields["next_usn"] or
        fields["first_usn"]<0 or fields["lowest_valid"]<0 or
        fields["first_usn"]>fields["next_usn"] or
        fields["lowest_valid"]>fields["next_usn"]):
        raise win.SourceDenied("INVALID_VOLUME_JOURNAL_BOUNDS")
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.GetVolumeInformationW.argtypes=[wintypes.LPCWSTR,wintypes.LPWSTR,wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),wintypes.LPWSTR,wintypes.DWORD]
    kernel.GetVolumeInformationW.restype=wintypes.BOOL
    serial=wintypes.DWORD()
    if not kernel.GetVolumeInformationW("C:\\",None,0,ctypes.byref(serial),None,None,None,0):
        raise win.SourceDenied("VOLUME_SERIAL_OS_QUERY_UNAVAILABLE_"+str(ctypes.get_last_error()))
    kernel.GetVolumeNameForVolumeMountPointW.argtypes=[wintypes.LPCWSTR,
                                                       wintypes.LPWSTR,wintypes.DWORD]
    kernel.GetVolumeNameForVolumeMountPointW.restype=wintypes.BOOL
    guid=ctypes.create_unicode_buffer(256)
    if not kernel.GetVolumeNameForVolumeMountPointW("C:\\",guid,len(guid)):
        raise win.SourceDenied("VOLUME_GUID_OS_QUERY_UNAVAILABLE_"+str(ctypes.get_last_error()))
    return Journal(**fields,volume_serial=int(serial.value),volume_guid=guid.value.upper())

class VolumeContinuityReader(p196.UsnGuardedSourceReader):
    """Lab witness: requires real journal identity and continuity during a read.

    Still TOCTOU. No trustworthy pin of initial journal ID, serial or GUID;
    these are OS observations, not cryptographic trusted volume authority.
    """
    def observe(self): return observe_journal(self.root)

    @staticmethod
    def validate(a:Journal,b:Journal,leaf_first:int,leaf_last:int):
        if a.journal_id!=b.journal_id:
            raise win.SourceDenied("JOURNAL_ID_CHANGED_OR_REPLACED")
        if a.volume_serial!=b.volume_serial or a.volume_guid!=b.volume_guid:
            raise win.SourceDenied("OBSERVED_VOLUME_IDENTITY_CHANGED")
        if b.next_usn<a.next_usn:
            raise win.SourceDenied("JOURNAL_NEXT_USN_REWOUND")
        if b.first_usn<a.first_usn or b.lowest_valid<a.lowest_valid:
            raise win.SourceDenied("JOURNAL_BOUNDARY_REWOUND")
        if (leaf_first<a.first_usn or leaf_first<a.lowest_valid or
            leaf_first>=a.next_usn):
            raise win.SourceDenied("INITIAL_FILE_USN_OUTSIDE_TRUSTED_JOURNAL_WINDOW")
        if (leaf_first<b.first_usn or leaf_first<b.lowest_valid or
            leaf_last>=b.next_usn):
            raise win.SourceDenied("FILE_USN_JOURNAL_HISTORY_TRUNCATED_OR_INVALID")
        if leaf_last!=leaf_first:
            raise win.SourceDenied("FILE_USN_WITNESS_DRIFT")
        return True

    def read(self,path:str,*,on_open=None,on_component=None)->bytes:
        initial=self.observe()
        before_count=len(self.usn_observed)
        raw=super().read(path,on_open=on_open,on_component=on_component)
        new=self.usn_observed[before_count:]
        if len(new)!=2:
            raise win.SourceDenied("FILE_USN_OBSERVATION_COUNT_UNVERIFIED")
        end=self.observe()
        self.validate(initial,end,new[0],new[1])
        return raw

class P197NativeContinuityReview(p196.P196NativeUsnReview):
    """Preserve prior 30 source-era tests, add 10 volume / recovery audit cases."""
    def new_reader(self)->VolumeContinuityReader:
        anchor=p195.load(self.record,self.root,self.public,7).prebound
        return VolumeContinuityReader(self.root,anchor)

    def test_31_live_journal_observation_and_original_source_read(self):
        reader=self.new_reader()
        j=reader.observe()
        self.assertTrue(j.journal_id>0 and j.next_usn>j.first_usn)
        self.assertTrue(j.volume_guid.startswith("\\\\?\\VOLUME{"))
        self.assertEqual(reader.read(B.SELF),self.sealed)
        print("P197_REAL_C_VOLUME_JOURNAL_ID_STABLE=OBSERVED_AND_ADMITTED",flush=True)

    def test_32_live_parent_sibling_write_without_false_volume_alarm(self):
        reader=self.new_reader()
        target=self.source.parent/"p197-good-sibling"
        result=reader.read(B.SELF,on_open=lambda _:
            self.assertTrue(self.child("write_sibling",self.source,target)["succeeded"]))
        self.assertEqual(result,self.sealed)
        print("P197_REAL_SIBLING_WRITE_JOURNAL_PROGRESS=ADMITTED",flush=True)

    def _inject_change(self,mutation:str,deny:str):
        reader=self.new_reader()
        before=reader.observe()
        after=replace(before,**{mutation:getattr(before,mutation)+1})
        with mock.patch.object(reader,"observe",side_effect=[before,after]):
            with self.assertRaisesRegex(win.SourceDenied,deny):
                reader.read(B.SELF)

    def test_33_synthetic_journal_recreation_same_source_denied(self):
        self._inject_change("journal_id","JOURNAL_ID_CHANGED_OR_REPLACED")
        print("P197_SYNTHETIC_JOURNAL_RESET_ID_CHANGE=FAIL_CLOSED",flush=True)

    def test_34_synthetic_journal_next_usn_rollback_denied(self):
        reader=self.new_reader();before=reader.observe()
        after=replace(before,next_usn=max(1,before.next_usn-512))
        with mock.patch.object(reader,"observe",side_effect=[before,after]):
            with self.assertRaisesRegex(win.SourceDenied,"JOURNAL_NEXT_USN_REWOUND"):
                reader.read(B.SELF)
        print("P197_SYNTHETIC_JOURNAL_NEXT_USN_ROLLBACK=FAIL_CLOSED",flush=True)

    def test_35_synthetic_journal_first_boundary_history_loss_denied(self):
        reader=self.new_reader();before=reader.observe()
        leaf=reader._last_file_usn if False else None
        after=replace(before,first_usn=before.next_usn)
        with mock.patch.object(reader,"observe",side_effect=[before,after]):
            with self.assertRaisesRegex(win.SourceDenied,"FILE_USN_JOURNAL_HISTORY_TRUNCATED_OR_INVALID"):
                reader.read(B.SELF)
        print("P197_SYNTHETIC_FIRST_USN_TRUNCATION=FAIL_CLOSED",flush=True)

    def test_36_synthetic_lowest_valid_journal_restamp_denied(self):
        reader=self.new_reader();before=reader.observe()
        after=replace(before,lowest_valid=before.next_usn)
        with mock.patch.object(reader,"observe",side_effect=[before,after]):
            with self.assertRaisesRegex(win.SourceDenied,"FILE_USN_JOURNAL_HISTORY_TRUNCATED_OR_INVALID"):
                reader.read(B.SELF)
        print("P197_SYNTHETIC_LOWEST_VALID_DISCONTINUITY=FAIL_CLOSED",flush=True)

    def test_37_synthetic_volume_identity_change_denied(self):
        for field in ("volume_serial","volume_guid"):
            reader=self.new_reader();before=reader.observe()
            replacement=(before.volume_serial+1 if field=="volume_serial" else
                         "\\\\?\\VOLUME{NOT-ORIGINAL}\\")
            after=replace(before,**{field:replacement})
            with mock.patch.object(reader,"observe",side_effect=[before,after]):
                with self.assertRaisesRegex(win.SourceDenied,"OBSERVED_VOLUME_IDENTITY_CHANGED"):
                    reader.read(B.SELF)
        print("P197_SYNTHETIC_VOLUME_REPLACEMENT=FAIL_CLOSED",flush=True)

    def test_38_unavailable_journal_query_denies_original_source(self):
        reader=self.new_reader()
        with mock.patch.object(reader,"observe",
            side_effect=win.SourceDenied("SIMULATED_JOURNAL_UNAVAILABLE")):
            with self.assertRaisesRegex(win.SourceDenied,"SIMULATED_JOURNAL_UNAVAILABLE"):
                reader.read(B.SELF)
        print("P197_JOURNAL_UNAVAILABLE=FAIL_CLOSED",flush=True)

    def test_39_real_external_ADS_ABA_still_refused_with_volume_observation(self):
        reader=self.new_reader();observed=[]
        stream=str(self.source)+":p191_cross_process_stream"
        def mutate(_):
            a=self.child("create_ads",self.source);self.assertTrue(a["succeeded"])
            b=self._remove_other_process(stream);self.assertTrue(b["removed"])
            observed.extend([a,b])
            print("P197_REAL_ADS_ADD_REMOVE_OS_ALLOWED=TRUE",flush=True)
        try:
            with self.assertRaisesRegex(win.SourceDenied,"HANDLE_ID_OR_SOURCE_METADATA_DRIFT"):
                reader.read(B.SELF,on_open=mutate)
            self.assertEqual(len(observed),2)
            self.assertNotEqual(reader.usn_observed[0],reader.usn_observed[1])
            print("P197_REAL_ADS_ABA=USN_FILE_DENIAL_PRESERVED",flush=True)
        finally:
            if ":p191_cross_process_stream:$DATA" in aliases.Win32SourceInspectionCandidate.streams(self.source):
                os.unlink(stream)

    def test_40_real_external_hardlink_ABA_still_refused_with_volume_observation(self):
        reader=self.new_reader();observed=[]
        link=self.root/"p197-cross-process-link"
        def mutate(_):
            a=self.child("create_hardlink",self.source,link);self.assertTrue(a["succeeded"])
            b=self._remove_other_process(link);self.assertTrue(b["removed"])
            observed.extend([a,b])
            print("P197_REAL_HARDLINK_ADD_REMOVE_OS_ALLOWED=TRUE",flush=True)
        try:
            with self.assertRaisesRegex(win.SourceDenied,"HANDLE_ID_OR_SOURCE_METADATA_DRIFT"):
                reader.read(B.SELF,on_open=mutate)
            self.assertEqual(len(observed),2)
            self.assertNotEqual(reader.usn_observed[0],reader.usn_observed[1])
            print("P197_REAL_HARDLINK_ABA=USN_FILE_DENIAL_PRESERVED",flush=True)
        finally:link.unlink(missing_ok=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p197-volume-journal"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
        "checkpoint":"P197",
        "historical_H":"HOLD","current_C":"ISOLATED_VOLUME_JOURNAL_CONTINUITY_REVIEW",
        "production_R":"HOLD","unfiltered_full_product_native_Windows_regressions":"0/3",
        "external_independent_reviews":p194.REVIEWS,"privileged_G0_G6":"OPEN",
        "historical_original_BYOK_B_ADS_gap":"CONFIRMED_UNPATCHED",
        "P195_original_ABA_admission":"CONFIRMED_UNPATCHED",
        "P196_file_USN_C_volume_refusal":"PRESERVED_SELECTED_EXPERIMENT",
        "source_root_pre_enrolment_authority":"NOT_ESTABLISHED",
        "independent_trusted_rollback_volume_attestation":"NOT_ESTABLISHED",
        "actual_journal_reset_disk_restore_privileged_attack":"NOT_TESTED_DESTRUCTIVE_ACTIONS_PROHIBITED",
        "complete_original_B_Phase10_product_integration":"NOT_ESTABLISHED",
        "full_product_original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED",
    }
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["authenticated_original_P196"]=authenticate_p196(
            os.environ.get("P197_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if k in ("GITHUB_TOKEN","GH_TOKEN","P197_ARCHIVE_TOKEN") or k.endswith(("_SECRET","_API_KEY")):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p197_original_and_volume_native_Windows_40.log"
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                    "scripts.p197_windows_volume_journal_continuity_review.P197NativeContinuityReview"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                stderr=subprocess.STDOUT,timeout=240,check=False)
        raw=log.read_bytes();txt=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"^P197_[^\r\n]+",txt,re.M)
        ledger["current_P197_native"]={
            "raw_log":log.name,"raw_log_SHA256":sha(raw),"actual_OS_exit":p.returncode,
            "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
            "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),"events":events,
            "original_negative_failures_in_raw_log":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}
        if (p.returncode!=0 or ledger["current_P197_native"]["test_footer"]!=["40"] or
            not ledger["current_P197_native"]["complete_OK"]):
            raise RuntimeError("P197 native Windows selected original and new test failure; retain logs")
        for marker in (
            "P197_REAL_C_VOLUME_JOURNAL_ID_STABLE=OBSERVED_AND_ADMITTED",
            "P197_REAL_SIBLING_WRITE_JOURNAL_PROGRESS=ADMITTED",
            "P197_SYNTHETIC_JOURNAL_RESET_ID_CHANGE=FAIL_CLOSED",
            "P197_SYNTHETIC_JOURNAL_NEXT_USN_ROLLBACK=FAIL_CLOSED",
            "P197_SYNTHETIC_FIRST_USN_TRUNCATION=FAIL_CLOSED",
            "P197_SYNTHETIC_LOWEST_VALID_DISCONTINUITY=FAIL_CLOSED",
            "P197_SYNTHETIC_VOLUME_REPLACEMENT=FAIL_CLOSED",
            "P197_REAL_ADS_ABA=USN_FILE_DENIAL_PRESERVED",
            "P197_REAL_HARDLINK_ABA=USN_FILE_DENIAL_PRESERVED",
        ):
            if not any(marker in s for s in events):
                raise RuntimeError("P197 essential native/synthetic review marker missing: "+marker)
        after=custody();ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P197 source identity drifted across genuine Windows run")
        complete=True
        print("P197_SOURCE_AUTHENTIC_P196_ZIP_AND_PREVIOUS_30=VERIFIED",flush=True)
        print("P197_SELECTED_GENUINE_WINDOWS_AND_SYNTHETIC_REVIEW=40/40_PASS_NOT_FULL_PRODUCT",flush=True)
        print("P197_VOLUME_JOURNAL_AUTHENTICATION_ROLLBACK_PRIVILEGE_ATOMIC_SECURITY=UNPROVEN",flush=True)
        print("P197_COMPLETE_FULL_PRODUCT_WINDOWS=0/3|QUALIFIED_EXTERNAL_REVIEW_OPEN|RELEASE_HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P197_JOURNAL_REVIEW=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=complete
        (out/"p197_volume_journal_source_HCR_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":raise SystemExit(main())
