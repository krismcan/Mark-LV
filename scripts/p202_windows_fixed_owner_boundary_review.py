"""P202 genuine Windows fixed-owner legacy-gate candidate and Phase 10 boundary.

Original P201 ZIP, real 23 pinned source Git context, source-before/after,
OS exit, and all denial markers required. NO production activation.
"""
from __future__ import annotations
import hashlib,io,json,os,re,subprocess,sys,zipfile,unittest
from pathlib import Path
from unittest import mock
from nayeon.brain.byok_b_fixed_owner_bridge_candidate import (
    FixedHistoricalBGateOwner,admit_isolated_fixed_owner_original_b,
    parse_original_gate_response,PhysicalAdmissionDenied,
)
from scripts import p201_windows_original_b_ads_remediation_candidate as previous
from scripts import p187_windows_live_byok_b_equivalence as p187
from scripts import p188_windows_physical_source_alias_race_witness as p188
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P201="97edba1dd4f7a1ed518e8007e9708ecc426598c5"
BRANCH="byok-c1-p202-fixed-owner-trust-boundary-20261114"
NEW={"nayeon/brain/byok_b_fixed_owner_bridge_candidate.py",
     "scripts/p202_windows_fixed_owner_boundary_review.py",
     "docs/byok-c1-p202-fixed-owner-phase10-boundary-review.md",
     ".github/workflows/p202-windows-fixed-owner-boundary.yml"}
ARTIFACT=14109180043
ZIP_SHA="4B650328DD73B9070331A911BE938E671B70D3965E7853F0F3FCC79E77B4940F"
LOG_NAME="p201_real_original_B_plus_physical_candidate_13.log"
LOG_SHA="358453117C7D3824F543C1AFEE2FCA58B50C9F2C92B36540B2A01852901848CC"
LEDGER_NAME="p201_original_b_ads_candidate_HCR_ledger.json"
LEDGER_SHA="FFB7B548C2A325C526CEB7745E0F68C8C3DD5E55A0F68869C96D88EA8AE356A4"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest().upper()
def git(*args:str)->bytes:return previous.git(*args)

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    parent=git("merge-base",P201,"HEAD").decode().strip()
    changed=set(git("diff","--name-only",P201,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=head or git("branch","--show-current").decode().strip()!=BRANCH or
        parent!=P201 or changed!=NEW or dirty):
        raise RuntimeError("P202 original Windows exact source/branch custody denied: "+
            json.dumps({"head":head,"parent":parent,"changed":sorted(changed),"dirty":dirty[:300]}))
    if git("rev-parse",P201+":tests")!=git("rev-parse","HEAD:tests"):
        raise RuntimeError("P202 immutable original Phase 10 and all B test sources changed")
    if set(git("diff","--name-only",P201,"HEAD","--","nayeon").decode().splitlines())!={
          "nayeon/brain/byok_b_fixed_owner_bridge_candidate.py"}:
        raise RuntimeError("P202 existing product code modified or unsafe integration")
    for p in ("nayeon/brain/byok_b_ntfs_physical_admission_candidate.py",
              "scripts/p189_windows_original_full_b_physical_alias_verdict.py",
              "scripts/p190_windows_handle_bound_source_probe.py",
              "scripts/p195_windows_durable_root_authority_aba_review.py",
              "scripts/p196_windows_usn_aba_source_witness.py",
              "scripts/p197_windows_volume_journal_continuity_review.py",
              "scripts/p198_windows_source_byte_handoff_toctou_review.py",
              "scripts/p199_windows_consumer_identity_handoff_review.py",
              "scripts/p200_windows_executable_content_binding_review.py",
              "scripts/p201_windows_original_b_ads_remediation_candidate.py"):
        if git("show",P201+":"+p)!=(ROOT/p).read_bytes():
            raise RuntimeError("P202 original candidate or prior negative tests overwritten "+p)
    return {"P202_HEAD":head,"authenticated_P201_parent":P201,
            "only_four_additive_paths":sorted(NEW),
            "existing_product_phase10_source_and_historical_denials_unchanged":True}

def authenticate_p201(token:str)->dict:
    if len(token)<8:raise RuntimeError("P202 predecessor actual Windows artifact token absent")
    raw=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(raw)!=ZIP_SHA:raise RuntimeError("P202 predecessor P201 original ZIP SHA invalid")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!={LOG_NAME,LEDGER_NAME}:
            raise RuntimeError("P202 predecessor source ZIP CRC/inventory invalid")
        log=z.read(LOG_NAME);lraw=z.read(LEDGER_NAME)
        if sha(log)!=LOG_SHA or sha(lraw)!=LEDGER_SHA:
            raise RuntimeError("P202 P201 genuine Windows member hashes invalid")
        txt=log.decode("utf8","replace").replace("\r\n","\n")
        for m in ("P201_REAL_ORIGINAL_FULL_B_ADS=OLD_ADMITTED_NEW_CANDIDATE_REFUSED",
                  "P201_REAL_OTHER_PINNED_B_SOURCE_ADS=OLD_ADMITTED_NEW_CANDIDATE_REFUSED",
                  "P201_NATIVE_ORIGINAL_FULL_B_AND_23_PHYSICAL_SOURCE_HANDLES=ISOLATED_ADMIT"):
            if m not in txt:raise RuntimeError("P202 old P201 native actual stream outcome absent: "+m)
        if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=["13"] or
            not re.search(r"^OK\s*$",txt,re.M)):
            raise RuntimeError("P202 predecessor source-bound 13 tests footer invalid")
        x=json.loads(lraw);native=x.get("current_P201_native",{})
        if (x.get("checkpoint")!="P201" or x.get("historical_H")!="HOLD" or
            x.get("production_R")!="HOLD" or
            x.get("full_unfiltered_native_Windows_product_regressions")!="0/3" or
            x.get("source_before")!=x.get("source_after") or
            x.get("source_before",{}).get("P201_HEAD")!=P201 or
            native.get("actual_OS_exit")!=0 or native.get("raw_log_SHA256")!=LOG_SHA or
            native.get("test_footer")!=["13"] or not native.get("complete_OK") or
            x.get("experimental_checkpoint_complete_NOT_production") is not True):
            raise RuntimeError("P202 P201 authentic source/OS exit/HCR unresolved")
    return {"P201_native_artifact":ARTIFACT,"original_ZIP_SHA256":ZIP_SHA,
            "P201_true_historical_13_selected_Windows":"AUTHENTICATED",
            "production_release":"HOLD","complete_product_regressions":"0/3"}

class P202RealWindowsFixedOwnerBoundary(unittest.TestCase):
    """Eight real old-A/B Git source Windows cases, not Phase 10 product tests."""
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P202 actual hosted Windows only")
        cls.fixture=p187.P187RealWindowsDisposableWorktreeTests
        cls.fixture.setUpClass()
        cls.root=cls.fixture.path
        cls.source=cls.root/B.SELF

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"fixture"):cls.fixture.tearDownClass()

    def add_ads(self,path:Path,label:str)->str:
        stream=str(path)+":"+label
        with open(stream,"wb") as f:f.write(b"P202-OWNED-NONEXECUTING-NAMED-STREAM")
        self.assertIn(":"+label+":$DATA",p188.Win32SourceInspectionCandidate.streams(path))
        return stream

    def test_01_fixed_gate_owner_clean_all_23_historical_sources(self):
        record=admit_isolated_fixed_owner_original_b(self.root)
        self.assertEqual(record.historical_state,"COMPLETE_UNSTAGED")
        self.assertEqual(record.physically_admitted_sources,23)
        self.assertEqual(set(record.source_paths),set(B.ENVELOPE))
        self.assertEqual(record.integration_status,"ISOLATED_P202_OWNER_BRIDGE_NOT_PHASE10")
        print("P202_REAL_FIXED_OWNER_ORIGINAL_B_AND_ALL_23_HANDLES=ISOLATED_ADMIT",flush=True)

    def test_02_original_self_source_ADS_fixed_owner_refuses(self):
        name=self.add_ads(self.source,"p202_b_self_ads")
        try:
            with self.assertRaisesRegex(PhysicalAdmissionDenied,
                                        "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                admit_isolated_fixed_owner_original_b(self.root)
            print("P202_NATIVE_ORIGINAL_B_SELF_ADS_WITH_FIXED_OWNER=REFUSED",flush=True)
        finally:os.remove(name)

    def test_03_other_original_B_source_ADS_fixed_owner_refuses(self):
        other=self.root/"nayeon/desktop_alpha/application.py"
        self.assertIn("nayeon/desktop_alpha/application.py",B.CANDIDATE_SHA256)
        name=self.add_ads(other,"p202_other_source_ads")
        try:
            with self.assertRaisesRegex(PhysicalAdmissionDenied,
                                        "HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                admit_isolated_fixed_owner_original_b(self.root)
            print("P202_NATIVE_OTHER_PINNED_SOURCE_ADS_WITH_FIXED_OWNER=REFUSED",flush=True)
        finally:os.remove(name)

    def test_04_corrupted_historical_main_bytes_cannot_fall_back_to_physical(self):
        original=self.source.read_bytes()
        self.source.write_bytes(original+b"\n# P202 fake-only byte corrupt")
        try:
            with self.assertRaisesRegex(PhysicalAdmissionDenied,"P202_FIXED_FULL_ORIGINAL_B_GATE_DENIED"):
                admit_isolated_fixed_owner_original_b(self.root)
            print("P202_CORRUPTED_FULL_LEGACY_GATE=REFUSED_NO_FALLBACK",flush=True)
        finally:self.source.write_bytes(original)

    def test_05_new_entrypoint_rejects_injected_full_gate_callback(self):
        with self.assertRaises(TypeError):
            admit_isolated_fixed_owner_original_b(self.root,
                historical_gate=lambda:"COMPLETE_UNSTAGED")
        print("P202_PUBLIC_FIXED_BRIDGE_CALLER_GATE_CALLBACK=NOT_ACCEPTED",flush=True)

    def test_06_malformed_duplicate_nonzero_fake_gate_replies_refused(self):
        invalid=((0,"COMPLETE_UNSTAGED\n"),
                 (0,"P202_ORIGINAL_B_GATE_STATE=COMPLETE_UNSTAGED\nP202_ORIGINAL_B_GATE_STATE=COMPLETE_UNSTAGED\n"),
                 (0,"P202_ORIGINAL_B_GATE_STATE=ADMITTED\n"),
                 (1,"P202_ORIGINAL_B_GATE_STATE=COMPLETE_UNSTAGED\n"),
                 (0,"P202_ORIGINAL_B_GATE_STATE=EXACT_CHILD\nerror\n"),
                 (0,"P202_ORIGINAL_B_GATE_STATE=COMPLETE_UNSTAGED"))
        for rc,raw in invalid:
            with self.subTest(rc=rc,raw=raw),self.assertRaises(PhysicalAdmissionDenied):
                parse_original_gate_response(rc,raw)
        self.assertEqual(parse_original_gate_response(
           0,"P202_ORIGINAL_B_GATE_STATE=COMPLETE_UNSTAGED\n"),"COMPLETE_UNSTAGED")
        print("P202_UNTRUSTED_OR_MALFORMED_SUBPROCESS_GATE_REPLY=FAIL_CLOSED",flush=True)

    def test_07_wrong_original_git_branch_or_head_denied_before_child(self):
        owner=FixedHistoricalBGateOwner(self.root)
        with mock.patch.object(owner,"_native_git",return_value="wrong-original-head"):
            with self.assertRaisesRegex(PhysicalAdmissionDenied,"P202_ORIGINAL_A_PARENT_OR_BRANCH_MISMATCH"):
                owner()
        print("P202_INVALID_ORIGINAL_GIT_IDENTITY=REFUSED",flush=True)

    def test_08_native_ADS_cleanup_requires_new_full_admission_and_Phase10_unmodified(self):
        name=self.add_ads(self.source,"p202_recovery_ads")
        try:
            with self.assertRaisesRegex(PhysicalAdmissionDenied,"HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                admit_isolated_fixed_owner_original_b(self.root)
        finally:os.remove(name)
        after=admit_isolated_fixed_owner_original_b(self.root)
        self.assertEqual(after.physically_admitted_sources,23)
        self.assertIsNot(B.assert_byok_b_integrity,B._assert_byok_b_historical)
        from tests import phase10_perception_scope_migration as p10
        self.assertTrue(callable(p10.assert_phase10_integrity))
        print("P202_ADS_REMOVAL_FRESH_FIXED_OWNER_23_HANDLES=ISOLATED_ADMIT",flush=True)
        print("P202_CURRENT_PUBLIC_PHASE10_SUCCESSOR_ROUTING=NOT_CHANGED",flush=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p202-fixed-owner"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P202","historical_H":"HOLD",
        "current_C":"ISOLATED_ORIGINAL_B_FIXED_GATE_OWNER_AND_23_HANDLE_PHYSICAL_CANDIDATE",
        "production_R":"HOLD","native_full_product_regressions_accepted":"0/3",
        "qualified_independent_reviews":"OPEN_GOV01_GOV02_SEC03_SEC04_REL05_REL06_REL07",
        "privileged_G0_G6":"OPEN","current_public_Phase10_integration":"NOT_CHANGED",
        "real_signed_loader_and_trusted_IPC":"NOT_IMPLEMENTED",
        "independent_signer_root_epoch":"NOT_ESTABLISHED",
        "atomic_23_source_root_and_parent_ABA_protection":"UNRESOLVED",
        "untrusted_parent_process_may_spoof_python_script_and_output":"UNRESOLVED",
        "original_full_private_BYOK_B_ADS_gap":"LEGACY_UNPATCHED",
        "original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED",
        "original_worktree_product_tests_modified":False}
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["original_authenticated_P201"]=authenticate_p201(os.environ.get("P202_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if (k in ("GH_TOKEN","GITHUB_TOKEN","P202_ARCHIVE_TOKEN") or
                k.endswith(("_API_KEY","_SECRET"))):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p202_real_Windows_fixed_owner_original_B_8.log"
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                "scripts.p202_windows_fixed_owner_boundary_review.P202RealWindowsFixedOwnerBoundary"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
                timeout=250,check=False)
        raw=log.read_bytes();txt=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"P202_[^\r\n]+",txt)
        native={"raw_log":log.name,"raw_log_SHA256":sha(raw),
                "actual_OS_exit":p.returncode,
                "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
                "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
                "events":events,
                "failures":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}
        ledger["current_P202_native"]=native
        if p.returncode!=0 or native["test_footer"]!=["8"] or not native["complete_OK"]:
            raise RuntimeError("P202 native Windows fixed-owner 8 selected cases failed; HOLD")
        required=(
          "P202_REAL_FIXED_OWNER_ORIGINAL_B_AND_ALL_23_HANDLES=ISOLATED_ADMIT",
          "P202_NATIVE_ORIGINAL_B_SELF_ADS_WITH_FIXED_OWNER=REFUSED",
          "P202_NATIVE_OTHER_PINNED_SOURCE_ADS_WITH_FIXED_OWNER=REFUSED",
          "P202_CORRUPTED_FULL_LEGACY_GATE=REFUSED_NO_FALLBACK",
          "P202_PUBLIC_FIXED_BRIDGE_CALLER_GATE_CALLBACK=NOT_ACCEPTED",
          "P202_UNTRUSTED_OR_MALFORMED_SUBPROCESS_GATE_REPLY=FAIL_CLOSED",
          "P202_INVALID_ORIGINAL_GIT_IDENTITY=REFUSED",
          "P202_ADS_REMOVAL_FRESH_FIXED_OWNER_23_HANDLES=ISOLATED_ADMIT",
          "P202_CURRENT_PUBLIC_PHASE10_SUCCESSOR_ROUTING=NOT_CHANGED")
        if any(m not in events for m in required):
            raise RuntimeError("P202 required real Windows test events not authenticated")
        after=custody();ledger["source_after"]=after
        if before!=after:raise RuntimeError("P202 original audit Git source changed mid-run")
        complete=True
        print("P202_AUTHENTIC_P201_ORIGINAL_13_WINDOWS=VERIFIED",flush=True)
        print("P202_REAL_WINDOWS_FIXED_GATE_OWNER_23_SOURCE=8/8_SELECTED_PASS_NOT_FULL_PRODUCT",flush=True)
        print("P202_PUBLIC_PHASE10_PRODUCT_GATE_NOT_CONNECTED|PRODUCTION_HOLD",flush=True)
        print("P202_UNTRUSTED_PARENT_SIGNING_IPC_23_ATOMICITY=OPEN|FULL_PRODUCT_0/3",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P202_FIXED_OWNER_BOUNDARY=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=complete
        (out/"p202_fixed_owner_Phase10_boundary_HCR_ledger.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if complete else 1
if __name__=="__main__":raise SystemExit(main())
