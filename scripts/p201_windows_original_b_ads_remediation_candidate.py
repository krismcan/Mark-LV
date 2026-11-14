"""P201 Windows native true historical 23-pin BYOK-B physical-gate candidate.

Requires intact original P200 Windows evidence. Exercises real original B
Git/index/disk gate and new dormant all-23-source Win32 HANDLE guard on a
self-owned disposable old A+B Git worktree. Production Phase10 unchanged.
"""
from __future__ import annotations
import hashlib, io, json, os, re, subprocess, sys, zipfile
from pathlib import Path
from unittest import mock
import unittest
from nayeon.brain.byok_b_ntfs_physical_admission_candidate import (
    assert_isolated_original_b_with_ntfs_physical_guard, PhysicalAdmissionDenied
)
from scripts import p200_windows_executable_content_binding_review as p200
from scripts import p189_windows_original_full_b_physical_alias_verdict as p189
from scripts import p188_windows_physical_source_alias_race_witness as p188
from scripts import p190_windows_handle_bound_source_probe as p190
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P200="e9f9a0a01d2c2615087a6183c27a8ab478d67c78"
BRANCH="byok-c1-p201-original-b-ads-remediation-candidate-20261114"
NEW={
    "nayeon/brain/byok_b_ntfs_physical_admission_candidate.py",
    "scripts/p201_windows_original_b_ads_remediation_candidate.py",
    "docs/byok-c1-p201-original-B-ADS-remediation-integration-review.md",
    ".github/workflows/p201-windows-original-b-ads-remediation.yml",
}
ARTIFACT=14104818687
ZIP_SHA="42EFB773B25A3A018719A6C1DFAC6F5DA51AD7B8F5A2794ED9A062665F8E1CB0"
LOG_NAME="p200_real_Windows_executable_content_70_selected.log"
LOG_SHA="1FD63A482DDA650FF566CBF8DFC8C4D87BFF9710F560A81B4CCDD0F5EEEF3213"
LEDGER_NAME="p200_executable_content_HCR_ledger.json"
LEDGER_SHA="54B288F6EAEF8063D1277D6C121D51D17C66F726B8858C51A97FA4AED8F004A6"

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest().upper()
def git(*args:str)->bytes:return p200.git(*args)

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    base=git("merge-base",P200,"HEAD").decode().strip()
    diff=set(git("diff","--name-only",P200,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or os.environ.get("GITHUB_SHA")!=head or
        git("branch","--show-current").decode().strip()!=BRANCH or
        base!=P200 or diff!=NEW or dirty):
        raise RuntimeError("P201 exact original native Windows custody mismatch "+
             json.dumps({"head":head,"base":base,"changed":sorted(diff),"dirty":dirty[:320]}))
    if git("rev-parse",P200+":tests")!=git("rev-parse","HEAD:tests"):
        raise RuntimeError("P201 original tests and all frozen B security assertions changed")
    original_nayeon=set(git("diff","--name-only",P200,"HEAD","--","nayeon").decode().splitlines())
    if original_nayeon!={"nayeon/brain/byok_b_ntfs_physical_admission_candidate.py"}:
        raise RuntimeError("P201 existing product source changed; exactly one dormant candidate required")
    for path in ("scripts/p189_windows_original_full_b_physical_alias_verdict.py",
                 "scripts/p190_windows_handle_bound_source_probe.py",
                 "scripts/p195_windows_durable_root_authority_aba_review.py",
                 "scripts/p196_windows_usn_aba_source_witness.py",
                 "scripts/p197_windows_volume_journal_continuity_review.py",
                 "scripts/p198_windows_source_byte_handoff_toctou_review.py",
                 "scripts/p199_windows_consumer_identity_handoff_review.py",
                 "scripts/p200_windows_executable_content_binding_review.py"):
        if git("show",P200+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P201 historical native Windows safety assertion edited: "+path)
    if len(B.CANDIDATE_SHA256)!=23 or set(B.ENVELOPE)!=set(B.CANDIDATE_SHA256):
        raise RuntimeError("P201 historic original 23 source B digest pins changed")
    return {"P201_HEAD":head,"exact_P200_parent":P200,
            "only_new_unintegrated_candidate_and_three_audit_paths":sorted(NEW),
            "original_frozen_B_security_tests_source_history_unchanged":True}

def authenticate_p200(token:str)->dict:
    if len(token)<8:raise RuntimeError("P201 authentic original P200 artifact token missing")
    raw=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(raw)!=ZIP_SHA:raise RuntimeError("P201 historical original P200 ZIP digest altered")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!={LOG_NAME,LEDGER_NAME}:
            raise RuntimeError("P201 source-authenticated P200 ZIP inventory/CRC invalid")
        log=z.read(LOG_NAME);ledraw=z.read(LEDGER_NAME)
        if sha(log)!=LOG_SHA or sha(ledraw)!=LEDGER_SHA:
            raise RuntimeError("P201 P200 source-bound actual Windows member SHA mismatch")
        txt=log.decode("utf8","replace").replace("\r\n","\n")
        for m in ("P200_AFTER_PREVALIDATION_SCRIPT_PATH_SWAP=OS_EXECUTED_WRONG_CONTENT_UNSAFE",
                  "P200_DIFFERENT_OS_EXECUTED_SCRIPT_FAKED_APPROVED_RECEIPT=UNSAFE_SELF_ATTESTATION",
                  "P199_UNPINNED_SCRIPT_WITH_SAME_PROCESS_IMAGE=UNSAFE_SELF_ATTESTED_ACCEPTANCE",
                  "P195_ADS_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP"):
            if m not in txt:raise RuntimeError("P201 original unsafe historical marker absent: "+m)
        if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=["70"] or
            not re.search(r"^OK\s*$",txt,re.M)):
            raise RuntimeError("P201 historical P200 genuine native 70 test footer invalid")
        ledger=json.loads(ledraw);native=ledger.get("current_P200_native",{})
        if (ledger.get("checkpoint")!="P200" or ledger.get("historical_H")!="HOLD" or
            ledger.get("production_R")!="HOLD" or
            ledger.get("unfiltered_genuine_Windows_full_product_regressions")!="0/3" or
            ledger.get("source_before")!=ledger.get("source_after") or
            ledger.get("source_before",{}).get("P200_HEAD")!=P200 or
            native.get("actual_OS_exit")!=0 or native.get("raw_log_SHA256")!=LOG_SHA or
            native.get("test_footer")!=["70"] or not native.get("complete_OK") or
            ledger.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P201 original P200 H/C/R/source custody invalid")
    return {"authentic_original_P200_artifact":ARTIFACT,
            "ZIP_SHA256":ZIP_SHA,"selected_original_Windows_70":"AUTHENTICATED",
            "historical_source_execution_spoof":"PRESERVED_UNSAFE",
            "complete_original_Windows_full_product_regressions":"0/3","production":"HOLD"}

class P201NativeHistoricalBPhysicalCandidate(p189.P189ActualOriginalFullBPhysicalAliasVerdict):
    """Preserve 4 actual original full-B witness cases; add 9 guarded gate cases."""

    def historical_gate(self)->str:
        code,out=self.original.run_original_gate(self)
        if code!=0:
            raise PhysicalAdmissionDenied("P201_ORIGINAL_FULL_B_GATE_REFUSED:"+
                                          out[-550:].replace("\r"," ").replace("\n"," "))
        m=re.search(r"P187_ORIGINAL_B_ADMISSION=(COMPLETE_UNSTAGED|EXACT_STAGED|EXACT_CHILD)",out)
        if not m:raise PhysicalAdmissionDenied("P201_ORIGINAL_B_ADMISSION_STATUS_MISSING")
        return m.group(1)

    def candidate(self,*,gate=None):
        return assert_isolated_original_b_with_ntfs_physical_guard(
            self.path,historical_gate=self.historical_gate if gate is None else gate)

    def stream(self,path:Path,label:str):
        name=str(path)+":"+label
        with open(name,"wb") as f:f.write(b"P201-SELF-OWNED-NONEXECUTING-NTFS-STREAM")
        self.assertIn(":"+label+":$DATA",p188.Win32SourceInspectionCandidate.streams(path))
        return name

    def test_05_pristine_real_full_B_gate_and_all_23_physical_sources_admitted(self):
        self.require_sealed_bytes()
        verdict=self.candidate()
        self.assertEqual(verdict.historical_gate_state,"COMPLETE_UNSTAGED")
        self.assertEqual(verdict.admitted_source_count,23)
        self.assertEqual(len(verdict.original_b_pins),23)
        self.assertEqual(verdict.integration_status,"ISOLATED_P201_CANDIDATE_NOT_PRODUCTION")
        print("P201_NATIVE_ORIGINAL_FULL_B_AND_23_PHYSICAL_SOURCE_HANDLES=ISOLATED_ADMIT",flush=True)

    def test_06_real_named_ads_original_full_B_admits_new_candidate_refuses(self):
        self.require_sealed_bytes()
        name=self.stream(self.source,"p201_named_stream_on_original_B")
        try:
            self.assertEqual(self.observe("P201_ORIGINAL_B_ADS_STILL"),"ADMITTED")
            with self.assertRaisesRegex(PhysicalAdmissionDenied,
                                        "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.candidate()
            print("P201_REAL_ORIGINAL_FULL_B_ADS=OLD_ADMITTED_NEW_CANDIDATE_REFUSED",flush=True)
        finally:os.remove(name)

    def test_07_named_ads_on_different_original_B_pin_refused(self):
        other=self.path/"nayeon/desktop_alpha/application.py"
        self.assertIn("nayeon/desktop_alpha/application.py",B.CANDIDATE_SHA256)
        name=self.stream(other,"p201_other_original_B_pin_stream")
        try:
            self.assertEqual(self.observe("P201_ALTERNATE_B_FILE_ADS_STILL"),"ADMITTED")
            with self.assertRaisesRegex(PhysicalAdmissionDenied,
                                        "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.candidate()
            print("P201_REAL_OTHER_PINNED_B_SOURCE_ADS=OLD_ADMITTED_NEW_CANDIDATE_REFUSED",flush=True)
        finally:os.remove(name)

    def test_08_real_hardlink_refusal_preserved_by_original_and_candidate(self):
        outside=self.path.parent/"p201_disposable_original_B_external_link"
        os.link(self.source,outside)
        try:
            self.assertEqual(self.observe("P201_LINK_ORIGINAL"),"REFUSED_BY_ORIGINAL_8_34_LINK_GUARD")
            with self.assertRaisesRegex(PhysicalAdmissionDenied,"P201_ORIGINAL_FULL_B_GATE_REFUSED"):
                self.candidate()
            # Lab-only forced status isolates Win32 HANDLE check, NOT a
            # supported way to supply a trusted original gate in product.
            with self.assertRaisesRegex(PhysicalAdmissionDenied,"HARDLINK_OR_LINKCOUNT_INVALID"):
                self.candidate(gate=lambda:"COMPLETE_UNSTAGED")
            print("P201_REAL_HARDLINK=ORIGINAL_AND_PHYSICAL_GUARD_REFUSED",flush=True)
        finally:outside.unlink()

    def test_09_real_mutated_original_B_main_bytes_refused_by_full_gate(self):
        before=self.source.read_bytes()
        self.source.write_bytes(before+b"\n# P201 synthetic main-stream corrupt\n")
        try:
            with self.assertRaisesRegex(PhysicalAdmissionDenied,"P201_ORIGINAL_FULL_B_GATE_REFUSED"):
                self.candidate()
            with self.assertRaisesRegex(PhysicalAdmissionDenied,"ORIGINAL_B_SHA256_SOURCE_PIN_MISMATCH"):
                self.candidate(gate=lambda:"COMPLETE_UNSTAGED")
            print("P201_DISPOSABLE_ORIGINAL_B_MAIN_STREAM_TAMPER=DENIED_BOTH_GATES",flush=True)
        finally:self.source.write_bytes(before)

    def test_10_missing_historical_gate_refused(self):
        with self.assertRaisesRegex(PhysicalAdmissionDenied,"P201_INDEPENDENT_FULL_B_GATE_MISSING"):
            assert_isolated_original_b_with_ntfs_physical_guard(self.path)
        print("P201_MISSING_ORIGINAL_HISTORICAL_GATE=FAIL_CLOSED",flush=True)

    def test_11_win32_stream_query_unavailable_fails_closed(self):
        with mock.patch.object(p190.Win32HandleBoundSourceProbe,"_streams",
                               side_effect=p190.SourceDenied("P201_SYNTHETIC_STREAM_QUERY_UNAVAILABLE")):
            with self.assertRaisesRegex(PhysicalAdmissionDenied,
                                        "P201_SYNTHETIC_STREAM_QUERY_UNAVAILABLE"):
                self.candidate()
        print("P201_FAILED_NATIVE_ADS_ENUMERATION=FAIL_CLOSED",flush=True)

    def test_12_real_ads_cleanup_then_new_admission_fresh_23_pin_success(self):
        name=self.stream(self.source,"p201_recovery_ads")
        try:
            with self.assertRaisesRegex(PhysicalAdmissionDenied,
                                        "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.candidate()
        finally:os.remove(name)
        restored=self.candidate()
        self.assertEqual((restored.historical_gate_state,restored.admitted_source_count),
                         ("COMPLETE_UNSTAGED",23))
        print("P201_REAL_ADS_REMOVED_FRESH_ALL_23_HANDLES=REINSPECTED_ADMITTED",flush=True)

    def test_13_original_b_gate_failure_never_falls_back_to_physical_only(self):
        original=self.source.read_bytes()
        self.source.write_bytes(original+b"\n# P201 original Git full gate poison")
        try:
            with self.assertRaisesRegex(PhysicalAdmissionDenied,"P201_ORIGINAL_FULL_B_GATE_REFUSED"):
                self.candidate()
        finally:self.source.write_bytes(original)
        clean=self.candidate()
        self.assertEqual(clean.admitted_source_count,23)
        print("P201_HISTORICAL_FULL_B_GATE_FAILURE=NO_FALLBACK_AND_RECOVERED",flush=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p201-b-ads-remediation"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P201","historical_H":"HOLD",
      "current_C":"SEPARATE_UNINTEGRATED_ORIGINAL_FULL_B_23_HANDLE_ADS_REMEDIATION_CANDIDATE",
      "production_R":"HOLD","full_unfiltered_native_Windows_product_regressions":"0/3",
      "qualified_independent_reviews":p200.p194.REVIEWS,"privileged_G0_G6":"OPEN",
      "original_private_full_B_legacy_gate_ADS_gap":"UNPATCHED_IN_LEGACY_SOURCE",
      "isolated_candidate_current_public_Phase10_integration":"NOT_CONNECTED",
      "P190_handle_parent_path_ABA_and_all_23_atomicity":"UNRESOLVED",
      "trusted_original_gate_callable_in_production":"NOT_BOUND",
      "P195_P198_P199_P200_unsafe_negatives":"HISTORICAL_ASSERTIONS_PRESERVED",
      "source_to_trusted_signed_consumer_handoff":"NOT_INTEGRATED",
      "original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED"}
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["authentic_original_P200"]=authenticate_p200(
            os.environ.get("P201_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if (k in ("GITHUB_TOKEN","GH_TOKEN","P201_ARCHIVE_TOKEN") or
                k.endswith(("_API_KEY","_SECRET"))):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p201_real_original_B_plus_physical_candidate_13.log"
        with log.open("wb") as f:
            process=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                "scripts.p201_windows_original_b_ads_remediation_candidate.P201NativeHistoricalBPhysicalCandidate"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                stderr=subprocess.STDOUT,timeout=310,check=False)
        raw=log.read_bytes();txt=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"^P201_[^\r\n]+",txt,re.M)
        ledger["current_P201_native"]={
          "raw_log":log.name,"raw_log_SHA256":sha(raw),
          "actual_OS_exit":process.returncode,
          "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
          "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
          "P201_events":events,
          "historic_actual_original_B_events":re.findall(r"^P189_ACTUAL_ORIGINAL_FULL_B_[^\r\n]+",txt,re.M),
          "fail_errors":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}
        if (process.returncode!=0 or ledger["current_P201_native"]["test_footer"]!=["13"] or
            not ledger["current_P201_native"]["complete_OK"]):
            raise RuntimeError("P201 original full B guarded candidate native Windows 13 cases failed; HOLD")
        required=(
         "P201_NATIVE_ORIGINAL_FULL_B_AND_23_PHYSICAL_SOURCE_HANDLES=ISOLATED_ADMIT",
         "P201_REAL_ORIGINAL_FULL_B_ADS=OLD_ADMITTED_NEW_CANDIDATE_REFUSED",
         "P201_REAL_OTHER_PINNED_B_SOURCE_ADS=OLD_ADMITTED_NEW_CANDIDATE_REFUSED",
         "P201_REAL_HARDLINK=ORIGINAL_AND_PHYSICAL_GUARD_REFUSED",
         "P201_DISPOSABLE_ORIGINAL_B_MAIN_STREAM_TAMPER=DENIED_BOTH_GATES",
         "P201_MISSING_ORIGINAL_HISTORICAL_GATE=FAIL_CLOSED",
         "P201_FAILED_NATIVE_ADS_ENUMERATION=FAIL_CLOSED",
         "P201_REAL_ADS_REMOVED_FRESH_ALL_23_HANDLES=REINSPECTED_ADMITTED",
         "P201_HISTORICAL_FULL_B_GATE_FAILURE=NO_FALLBACK_AND_RECOVERED",
        )
        for m in required:
            if m not in events:raise RuntimeError("P201 selected security outcome marker missing: "+m)
        originals=ledger["current_P201_native"]["historic_actual_original_B_events"]
        if (len(originals)<6 or
            not any("P189_ACTUAL_ORIGINAL_FULL_B_NAMED_NTFS_ADS=ADMITTED" in x
                    for x in originals)):
            raise RuntimeError("P201 original full historical B named ADS admitted witness missing")
        after=custody();ledger["source_after"]=after
        if before!=after:raise RuntimeError("P201 Git source changed during real Windows run")
        complete=True
        print("P201_AUTHENTIC_P200_70CASE_WINDOWS_PREDECESSOR=VERIFIED",flush=True)
        print("P201_ORIGINAL_FULL_B_23PIN_AND_HANDLE_ADS_CANDIDATE=13/13_SELECTED_NATIVE_WINDOWS",flush=True)
        print("P201_HISTORIC_B_ADS_ADMISSION_VS_UNINTEGRATED_CANDIDATE_REFUSAL=PROVEN",flush=True)
        print("P201_PUBLIC_CURRENT_PHASE10_AND_LEGACY_GATE_SOURCE=UNCHANGED_RELEASE_HOLD",flush=True)
        print("P201_FULL_PRODUCT_NATIVE_WINDOWS=0/3|INDEPENDENT_REVIEW_OPEN|PRODUCTION_HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P201_ORIGINAL_FULL_B_ADS_REMEDIATION=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_production"]=complete
        (out/"p201_original_b_ads_candidate_HCR_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1
if __name__=="__main__":raise SystemExit(main())
