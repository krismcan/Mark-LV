"""P204 current-side nonprivileged Windows HANDLE read-only source-set tests.

No production source, caller-supplied pin, service or code execution authority.
Authenticates P203 current public route map and its genuine Windows evidence.
"""
from __future__ import annotations
import hashlib,io,json,os,re,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest import mock
from nayeon.brain.byok_c1_readonly_source_set_candidate import (
    WindowsReadOnlySourceSetProbe,SourceSetRefused
)
from scripts import p203_windows_current_authority_readiness_audit as previous
from scripts import p190_windows_handle_bound_source_probe as p190
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact

ROOT=Path(__file__).resolve().parents[1]
P203="2ceac3142147f19707d858fa424b7dba1b02592a"
BRANCH="byok-c1-p204-readonly-windows-source-set-20261114"
NEW={"nayeon/brain/byok_c1_readonly_source_set_candidate.py",
     "scripts/p204_windows_readonly_source_set_review.py",
     "docs/byok-c1-p204-readonly-source-set-integration-review.md",
     ".github/workflows/p204-windows-readonly-source-set.yml"}
ARTIFACT=14108879465
ZIP_SHA="B6AF1F87772F78CDE86165E2AEE3CDB6D3C76B6A8746FD3A61FC17C73CE99FFB"
LOG="p203_actual_Windows_current_public_authority_8.log"
LOG_SHA="2C2485E44B84D5477208B99EB111772DA5A45F66A2868337FD058F91AC155C5A"
HCR="p203_current_authority_implementation_readiness_HCR.json"
HCR_SHA="8C0D9ADD30C8909337907710E6E98F0A6BAB6BF9176B70A70F22586103676FF8"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest().upper()
def git(*args:str)->bytes:return previous.git(*args)

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    base=git("merge-base",P203,"HEAD").decode().strip()
    changed=set(git("diff","--name-only",P203,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=head or git("branch","--show-current").decode().strip()!=BRANCH or
        base!=P203 or changed!=NEW or dirty):
        raise RuntimeError("P204 source-bound original Windows HEAD/Git custody invalid: "+
           json.dumps({"head":head,"base":base,"changed":sorted(changed),"dirty":dirty[:300]}))
    for subtree in ("tests","native_c1_candidate"):
        if git("rev-parse",P203+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P204 historical, actual public source or native trusted service modified")
    changed_prod=set(git("diff","--name-only",P203,"HEAD","--","nayeon").decode().splitlines())
    if changed_prod!={"nayeon/brain/byok_c1_readonly_source_set_candidate.py"}:
        raise RuntimeError("P204 existing original product code or dormant candidate edited")
    for path in ("scripts/p203_windows_current_authority_readiness_audit.py",
                 "scripts/p202_windows_fixed_owner_boundary_review.py",
                 "nayeon/brain/byok_b_fixed_owner_bridge_candidate.py",
                 "nayeon/brain/byok_b_ntfs_physical_admission_candidate.py"):
        if git("show",P203+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P204 original historical security witness changed: "+path)
    return {"P204_HEAD":head,"exact_P203_parent":P203,
           "four_additive_paths_only":sorted(NEW),
           "original_phase10_p76_legacy_B_C1_service_unchanged":True}

def authenticate_p203(token:str)->dict:
    if len(token)<8:raise RuntimeError("P204 original P203 evidence token absent")
    raw=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(raw)!=ZIP_SHA:raise RuntimeError("P204 source-authentic P203 original ZIP SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!={LOG,HCR}:
            raise RuntimeError("P204 original P203 ZIP CRC/inventory invalid")
        log=z.read(LOG);rawled=z.read(HCR)
        if sha(log)!=LOG_SHA or sha(rawled)!=HCR_SHA:
            raise RuntimeError("P204 original P203 member SHA mismatch")
        txt=log.decode("utf8","replace").replace("\r\n","\n")
        for marker in ("P203_ACTUAL_PUBLIC_B_TO_PHASE10_1_2_3_TO_P76_SOURCE_ROUTE=VERIFIED_STATIC",
                       "P203_NATIVE_SERVICE_CANDIDATE=DENIAL_ONLY_NO_PRODUCTION_DISPATCH",
                       "P203_REAL_NATIVE_PUBLIC_B_TO_P76_WRONG_BRANCH=REFUSED_NO_HISTORIC_FALLBACK"):
            if marker not in txt:
                raise RuntimeError("P204 original current route/hold negative outcome absent")
        if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=["8"] or
            not re.search(r"^OK\s*$",txt,re.M)):
            raise RuntimeError("P204 genuine P203 Windows 8-case footer invalid")
        old=json.loads(rawled);native=old.get("current_P203_native",{})
        if (old.get("checkpoint")!="P203" or old.get("historical_H")!="HOLD" or
            old.get("production_R")!="HOLD" or
            old.get("full_unfiltered_native_Windows_product_regressions_accepted")!="0/3" or
            old.get("source_before")!=old.get("source_after") or
            old.get("source_before",{}).get("P203_HEAD")!=P203 or
            native.get("actual_OS_exit")!=0 or native.get("raw_log_SHA256")!=LOG_SHA or
            native.get("test_footer")!=["8"] or not native.get("complete_OK") or
            old.get("source_audit_complete_NOT_implementation_GO") is not True):
            raise RuntimeError("P204 original P203 Windows source/HCR no-release ledger invalid")
    return {"P203_original_artifact":ARTIFACT,"ZIP_SHA256":ZIP_SHA,
       "current_authority_selected_native_Windows":"8/8_AUTHENTIC",
       "full_product":"0/3","real_credential_authority":"NO_GO"}

class P204RealWindowsSourceSetProbe(unittest.TestCase):
    """Isolated self-owned benign test files, true Win32 HANDLE operations."""
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P204 requires actual hosted native Windows")
        cls.temp=tempfile.TemporaryDirectory(prefix="p204-source-set-",dir=os.environ["RUNNER_TEMP"])
        cls.root=Path(cls.temp.name)
        cls.parts={
            "tests/p204_alpha.txt":b"P204 fixture approved alpha source bytes",
            "nayeon/brain/p204_beta.txt":b"P204 fixture approved beta source bytes",
        }
        for rel in cls.parts:
            (cls.root/rel).parent.mkdir(parents=True,exist_ok=True)
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"temp"):cls.temp.cleanup()
    def setUp(self):
        for rel,data in self.parts.items():
            (self.root/rel).write_bytes(data)
        self.pins={rel:sha(data) for rel,data in self.parts.items()}
        self.reader=WindowsReadOnlySourceSetProbe(self.root)

    def test_01_real_win32_two_source_handle_bytes_fileid_observed_only(self):
        result=self.reader.inspect_untrusted_pin_set(self.pins)
        self.assertEqual(len(result.items),2)
        self.assertEqual(result.trust_status,
                         "NONATOMIC_SEQUENTIAL_READ_ONLY_OBSERVATION_NOT_ADMISSION")
        for item in result.items:
            self.assertEqual(item.data,self.parts[item.relative_path])
            self.assertEqual(item.sha256,self.pins[item.relative_path])
            self.assertEqual(len(item.fileid),16)
            self.assertEqual(item.trust_status,
                             "OBSERVED_WITH_UNTRUSTED_CALLER_PIN_NOT_ADMITTED")
        print("P204_REAL_WINDOWS_TWO_PINNED_SOURCE_HANDLES_BYTES_AND_FILEIDS=OBSERVED_NOT_ADMITTED",flush=True)

    def test_02_real_named_ads_on_one_source_fail_closed(self):
        source=self.root/"tests/p204_alpha.txt"
        ads=str(source)+":p204_nonexecuting_ads"
        with open(ads,"wb") as f:f.write(b"nonsecret experimental ADS")
        try:
            with self.assertRaisesRegex(SourceSetRefused,"HANDLE_HAS_UNAPPROVED_NTFS_STREAM"):
                self.reader.inspect_untrusted_pin_set(self.pins)
            print("P204_GENUINE_WINDOWS_NAMED_ADS_SOURCE_SET=REFUSED",flush=True)
        finally:os.remove(ads)

    def test_03_native_extra_hardlink_source_set_refused(self):
        source=self.root/"tests/p204_alpha.txt"
        link=self.root/"p204_fixture_extra_hardlink"
        os.link(source,link)
        try:
            with self.assertRaisesRegex(SourceSetRefused,"HARDLINK_OR_LINKCOUNT_INVALID"):
                self.reader.inspect_untrusted_pin_set(self.pins)
            print("P204_GENUINE_WINDOWS_EXTRA_HARDLINK_SOURCE_SET=REFUSED",flush=True)
        finally:link.unlink()

    def test_04_mutated_source_bytes_refused_against_original_independent_test_pin(self):
        source=self.root/"tests/p204_alpha.txt"
        source.write_bytes(self.parts["tests/p204_alpha.txt"]+b"x")
        with self.assertRaisesRegex(SourceSetRefused,"P204_ORIGINAL_PIN_MISMATCH"):
            self.reader.inspect_untrusted_pin_set(self.pins)
        print("P204_GENUINE_WINDOWS_CHANGED_MAIN_SOURCE_BYTES=REFUSED",flush=True)

    def test_05_missing_or_noncanonical_claimed_source_inventory_refused(self):
        for invalid in ({},{'tests/../p204_alpha.txt':"A"*64},
                        {'tests/p204_alpha.txt:injected':"A"*64},
                        {'tests\\p204_alpha.txt':"A"*64},
                        {'tests/p204_alpha.txt':"bad"},
                        {'../other.txt':"A"*64}):
            with self.subTest(invalid=invalid),self.assertRaises(SourceSetRefused):
                self.reader.inspect_untrusted_pin_set(invalid)
        print("P204_UNAPPROVED_PATH_ALIAS_OR_MALFORMED_PIN_SET=REFUSED",flush=True)

    def test_06_after_validated_bytes_path_can_be_replaced_no_false_lease(self):
        old=self.reader.inspect_untrusted_pin_set(self.pins)
        source=self.root/"tests/p204_alpha.txt"
        replaced=source.with_name("p204_replacement_fixture.tmp")
        replaced.write_bytes(b"P204 source substituted AFTER HANDLE return")
        os.replace(replaced,source)
        self.assertEqual(next(x.data for x in old.items if x.relative_path=="tests/p204_alpha.txt"),
                         self.parts["tests/p204_alpha.txt"])
        with self.assertRaisesRegex(SourceSetRefused,"P204_ORIGINAL_PIN_MISMATCH"):
            self.reader.inspect_untrusted_pin_set(self.pins)
        print("P204_POST_HANDLE_CLOSE_PATH_REPLACEMENT=OLD_BYTES_STABLE_NEW_PATH_REFUSED",flush=True)

    def test_07_untrusted_caller_self_repinning_tampered_source_is_unsafe(self):
        source=self.root/"tests/p204_alpha.txt"
        source.write_bytes(b"P204 altered benign bytes chosen by untrusted caller")
        self.pins["tests/p204_alpha.txt"]=sha(source.read_bytes())
        observed=self.reader.inspect_untrusted_pin_set(self.pins)
        self.assertEqual(next(x.data for x in observed.items if x.relative_path=="tests/p204_alpha.txt"),
                         source.read_bytes())
        self.assertNotEqual(self.pins["tests/p204_alpha.txt"],sha(self.parts["tests/p204_alpha.txt"]))
        print("P204_CALLER_CONTROLLED_SOURCE_AND_REPIN=UNSAFE_OBSERVATION_ACCEPTED_NO_TRUST_ROOT",flush=True)

    def test_08_win32_handle_stream_enumeration_error_never_returns_partial_set(self):
        with mock.patch.object(p190.Win32HandleBoundSourceProbe,"_streams",
                               side_effect=p190.SourceDenied("P204_FAKE_STREAM_METADATA_UNAVAILABLE")):
            with self.assertRaisesRegex(SourceSetRefused,"P204_FAKE_STREAM_METADATA_UNAVAILABLE"):
                self.reader.inspect_untrusted_pin_set(self.pins)
        print("P204_OS_STREAM_METADATA_FAILURE=FAIL_CLOSED_NO_PARTIAL_RESULT",flush=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p204-readonly-source-set"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P204","historical_H":"HOLD",
       "current_C":"ISOLATED_CURRENT_SIDE_READ_ONLY_SOURCE_SET_HANDLE_BYTES_CANDIDATE",
       "production_R":"HOLD","full_unfiltered_native_Windows_product_regressions_accepted":"0/3",
       "qualified_external_GOV_SEC_REL_reviews":"OPEN_ALL_SEVEN","G0_G6":"OPEN",
       "current_Phase10_to_P76_public_route":"UNCHANGED",
       "current_c1_native_service_effect_dispatch":"DENIAL_ONLY",
       "source_set_true_atomicity":"NOT_ESTABLISHED",
       "manifest_signer_pins_independent_authority":"NOT_ESTABLISHED",
       "post_close_exact_consumer_handoff":"NOT_ESTABLISHED",
       "original_full_B_legacy_ADS_gap":"UNPATCHED",
       "original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED"}
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["authenticated_P203_predecessor"]=authenticate_p203(os.environ.get("P204_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if k in {"P204_ARCHIVE_TOKEN","GITHUB_TOKEN","GH_TOKEN"} or k.endswith(("_API_KEY","_SECRET")):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p204_real_windows_source_set_8.log"
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                "scripts.p204_windows_readonly_source_set_review.P204RealWindowsSourceSetProbe"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                stdout=f,stderr=subprocess.STDOUT,timeout=130,check=False)
        raw=log.read_bytes();txt=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"P204_[^\r\n]+",txt)
        native={"raw_log":log.name,"raw_log_SHA256":sha(raw),
                "actual_OS_exit":p.returncode,
                "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
                "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
                "events":events,
                "failures":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}
        ledger["current_P204_native"]=native
        if p.returncode!=0 or native["test_footer"]!=["8"] or not native["complete_OK"]:
            raise RuntimeError("P204 source-set actual Windows eight-case review FAILED; HOLD")
        for marker in (
          "P204_REAL_WINDOWS_TWO_PINNED_SOURCE_HANDLES_BYTES_AND_FILEIDS=OBSERVED_NOT_ADMITTED",
          "P204_GENUINE_WINDOWS_NAMED_ADS_SOURCE_SET=REFUSED",
          "P204_GENUINE_WINDOWS_EXTRA_HARDLINK_SOURCE_SET=REFUSED",
          "P204_GENUINE_WINDOWS_CHANGED_MAIN_SOURCE_BYTES=REFUSED",
          "P204_POST_HANDLE_CLOSE_PATH_REPLACEMENT=OLD_BYTES_STABLE_NEW_PATH_REFUSED",
          "P204_CALLER_CONTROLLED_SOURCE_AND_REPIN=UNSAFE_OBSERVATION_ACCEPTED_NO_TRUST_ROOT",
          "P204_OS_STREAM_METADATA_FAILURE=FAIL_CLOSED_NO_PARTIAL_RESULT"
        ):
            if marker not in events:raise RuntimeError("P204 required honest native source-set marker absent "+marker)
        after=custody();ledger["source_after"]=after
        if before!=after:raise RuntimeError("P204 Git source changed during actual Windows audit")
        complete=True
        print("P204_AUTHENTIC_CURRENT_P203_WINDOWS_8CASE_SOURCE_AUTHORITY=VERIFIED",flush=True)
        print("P204_REAL_WINDOWS_PINNED_SOURCE_SET_HANDLE=8/8_SELECTED_TESTS",flush=True)
        print("P204_NONATOMIC_SOURCE_SET_AND_UNAUTHENTICATED_PIN_MANIFEST=NOT_PRODUCTION_ADMISSION",flush=True)
        print("P204_REAL_CREDENTIAL_EFFECT_AND_FULL_PRODUCT_WINDOWS=NO_GO_0/3",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P204_SOURCE_SET_NATIVE_CANDIDATE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["selected_experimental_checkpoint_complete_NOT_release"]=complete
        (out/"p204_readonly_source_set_HCR_ledger.json").write_text(
             json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if complete else 1
if __name__=="__main__":raise SystemExit(main())
