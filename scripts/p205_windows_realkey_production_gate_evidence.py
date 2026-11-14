"""P205: Native Windows current real-key and production NO-GO witness.

EXPLICITLY NO CREDENTIAL ACCESS, NO SERVICE INSTALL, NO BYPASS AND NO REVIEW GO.
Original product/Phase10/P49 frozen source is read only. Compiles actual P49
11-file denial and contemporary 10-original+5-candidate C# denial host under
the ordinary Windows user and executes original 20 + candidate 24 native tests.
DO NOT interpret local CI green as externally signed real-key authority.
"""
from __future__ import annotations
import hashlib, io, json, os, re, subprocess, sys, unittest, zipfile
from pathlib import Path
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from scripts import p204_windows_readonly_source_set_review as previous

ROOT=Path(__file__).resolve().parents[1]
P204="3d91358aa49b31b76db1bb130cf6fef22a800ac6"
BRANCH="byok-c1-p205-realkey-production-gate-evidence-20261114"
NEW={
 "scripts/p205_windows_realkey_production_gate_evidence.py",
 "docs/byok-c1-p205-realkey-production-gate-decision-package.md",
 ".github/workflows/p205-windows-realkey-production-gates.yml",
}
P204_ARTIFACT=14110110651
P204_ZIP_SHA="1D53C003E87303155A61142D2629888B73B5637C79357C00A09337AD1335CA2D"
P204_LOG="p204_real_windows_source_set_9.log"
P204_LOG_SHA="4C92E128DF0293266796581784B4B3D9A2906C17E43CA73C2A9CC501EDB8D9F2"
P204_LEDGER="p204_readonly_source_set_HCR_ledger.json"
P204_LEDGER_SHA="809A0EF1346D75C1C1AA6A655B041378EA2B618E9A786FE2A57C72B1FEBE8098"
FROZEN_P49_PINS={
 "CustodyJournalFile.cs":"483CB220068FE34E28C7D1C58DBC4B6546E9226FC1899B62FAFEE912B6EBF939",
 "CustodyLedger.cs":"93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B",
 "CustodyRegistryAnchor.cs":"AB17A58C9558F0AC05AE7602093FA8338CEDCC91A85DB736A871FDEBF17F7C71",
 "CustodyService.cs":"49217E9018AB2437D3F2B4B2907C08946432352618EDEE065F734D88B93EC093",
 "PendingCustodyTransaction.cs":"D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
 "PendingServiceState.cs":"B194EE6809BEB84502D9CF509D44237E1A2C24D3905F3764DC4DCA425BAB793E",
 "PendingWinCredStore.cs":"4051A48F3062A737D0D9CE212DB9B302C2C22D5ECA2893CE27B35C740A72B93C",
 "ProtectedAcl.cs":"7152A0DB081EE9627B0F8E4D0D0230168FBF194752F3180DC884C694199AEC61",
 "RecoveryReader.cs":"AF2A0BA2F680DAE0A2ACAA4EF626838A20C23001F76799372D9444EE4D50A650",
 "ServiceCustodyMutex.cs":"2C1BD0DFA679D7C97CF124A0F6612E0DA8EE533EADCF29515E233C5EA214F7BE",
 "ServiceGate.cs":"F65EF9F04283B6CA82D42B8D61B6B99B23262DE62E248DC575C0CEF1B3D96B8D",
}
CANDIDATE=[
 "CustodyService.cs",
 "ServiceOwnedAdmissionBoundary.cs",
 "ServiceBoundRequestIdentity.cs",
 "NativeJ2ProtectedReadOnlyPreflight.cs",
 "CandidateCredentialEffectHold.cs",
 "IsolatedCandidateContracts.cs",
]
ACTUAL_GATES={
 "real_key_input":"NO_GO",
 "real_key_Save_Replace_Delete":"NO_GO",
 "trusted_local_UI_and_service":"NOT_SIGNED_OR_INSTALLED",
 "trusted_UI_provenance_and_IPC":"UNRESOLVED",
 "one_use_durable_effect_actor":"DENIAL_ONLY",
 "independent_initial_root_and_rollback":"UNRESOLVED",
 "legacy_python_backend_unified_native_authority":"NOT_ESTABLISHED",
 "original_B_ADS_and_current_Phase10_G0":"NOT_INTEGRATED",
 "privileged_G0_G6":"OPEN",
 "qualified_GOV_SEC_REL":"OPEN_SEVEN",
 "complete_unfiltered_native_Windows_product_regressions":"0/3",
 "production_release":"HOLD",
 "provider_validation_C2":"NOT_PART_OF_C1",
}
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest().upper()
def git(*args:str)->bytes:return previous.git(*args)

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    base=git("merge-base",P204,"HEAD").decode().strip()
    delta=set(git("diff","--name-only",P204,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        git("branch","--show-current").decode().strip()!=BRANCH or
        os.environ.get("GITHUB_SHA")!=head or base!=P204 or delta!=NEW or dirty):
        raise RuntimeError("P205 genuine Windows source trust custody invalid: "+
            json.dumps({"head":head,"base":base,"changed":sorted(delta),"dirty":dirty[:220]}))
    for directory in ("tests","nayeon","native_c1_candidate"):
        if git("rev-parse",P204+":"+directory)!=git("rev-parse","HEAD:"+directory):
            raise RuntimeError("P205 production, native candidate or historical tests edited "+directory)
    for path in ("scripts/p203_windows_current_authority_readiness_audit.py",
                 "scripts/p204_windows_readonly_source_set_review.py",
                 "nayeon/brain/byok_c1_readonly_source_set_candidate.py"):
        if git("show",P204+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P205 previous security witness or candidate source modified "+path)
    return {"P205_HEAD":head,"exact_P204_parent":P204,
            "only_three_review_paths":sorted(NEW),
            "original_native_service_Phase10_and_CredMan_source_unchanged":True}

def authenticate_p204(token:str)->dict:
    if len(token)<8:raise RuntimeError("P205 original authentic P204 artifact token absent")
    raw=_download_artifact(P204_ARTIFACT,P204_ZIP_SHA,token)
    if sha(raw)!=P204_ZIP_SHA:raise RuntimeError("P205 original P204 artifact ZIP SHA invalid")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist())!={P204_LOG,P204_LEDGER}:
            raise RuntimeError("P205 predecessor ZIP CRC or two-member inventory mismatch")
        log=z.read(P204_LOG);ledraw=z.read(P204_LEDGER)
        if sha(log)!=P204_LOG_SHA or sha(ledraw)!=P204_LEDGER_SHA:
            raise RuntimeError("P205 genuine original P204 archive member SHA mismatch")
        txt=log.decode("utf8","replace").replace("\r\n","\n")
        for marker in ("P204_GENUINE_WINDOWS_NAMED_ADS_SOURCE_SET=REFUSED",
                       "P204_CALLER_CONTROLLED_SOURCE_AND_REPIN=UNSAFE_OBSERVATION_ACCEPTED_NO_TRUST_ROOT",
                       "P204_INCONSISTENT_SOURCE_SET_VOLUME_FILEIDS=REFUSED"):
            if marker not in txt:raise RuntimeError("P205 unsafe authentic predecessor outcome missing "+marker)
        if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=["9"] or
            not re.search(r"^OK\s*$",txt,re.M)):
            raise RuntimeError("P205 original P204 genuine 9-case native Windows footer invalid")
        ledger=json.loads(ledraw);native=ledger.get("current_P204_native",{})
        if (ledger.get("checkpoint")!="P204" or
            ledger.get("historical_H")!="HOLD" or ledger.get("production_R")!="HOLD" or
            ledger.get("full_unfiltered_native_Windows_product_regressions_accepted")!="0/3" or
            ledger.get("source_before")!=ledger.get("source_after") or
            ledger.get("source_before",{}).get("P204_HEAD")!=P204 or
            native.get("actual_OS_exit")!=0 or native.get("raw_log_SHA256")!=P204_LOG_SHA or
            native.get("test_footer")!=["9"] or not native.get("complete_OK") or
            ledger.get("selected_experimental_checkpoint_complete_NOT_release") is not True):
            raise RuntimeError("P205 original P204 source H/C/R + OS exit invalid")
    return {"P204_source_bound_native_artifact":P204_ARTIFACT,
            "original_ZIP_SHA256":P204_ZIP_SHA,
            "selected_native_9":"AUTHENTICATED","real_credential_GO":"NO"}

class P205NativeRealKeyAndReleaseGates(unittest.TestCase):
    """Only nonprivileged native-source denial tests; no WinCred operations."""
    @classmethod
    def setUpClass(cls):
        cls.out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p205-key-gates"
        cls.out.mkdir(parents=True,exist_ok=True)
        cls.csc=Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
        if sys.platform!="win32" or not cls.csc.is_file() or \
           os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P205 requires original native Windows C# compiler")
        cls.p49dir=ROOT/"tests/p99_original_native_c1_denial"
        cls.native=ROOT/"native_c1_candidate"

    def _compile_and_run(self,label:str,sources:list[Path],entry:str,summary:str,
                         count:int)->None:
        exe=self.out/(label+".exe")
        args=[str(self.csc),"/nologo","/target:exe","/platform:x64",
              "/r:System.ServiceProcess.dll","/main:"+entry,
              "/out:"+str(exe)]+[str(x) for x in sources]
        compile=subprocess.run(args,cwd=ROOT,stdin=subprocess.DEVNULL,
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=80,check=False)
        (self.out/(label+"_compiler.log")).write_bytes(compile.stdout)
        self.assertEqual(compile.returncode,0,"P205 C# compiler failed; raw compiler log retained")
        self.assertFalse(compile.stdout.strip(),"P205 C# emitted unexpected compile warnings; HOLD")
        proc=subprocess.run([str(exe)],cwd=ROOT,stdin=subprocess.DEVNULL,
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=80,check=False)
        output=proc.stdout
        (self.out/(label+"_native.log")).write_bytes(output)
        self.assertEqual(proc.returncode,0,"P205 actual native Windows C# executable failed")
        txt=output.decode("utf8","replace").replace("\r\n","\n")
        self.assertIn(summary,txt)
        self.assertNotIn("FAIL ",txt)
        self.assertEqual(len(re.findall(r"^PASS ",txt,re.M)),count)
        print("P205_"+label.upper()+"_ACTUAL_WINDOWS_NATIVE_CASES="+str(count)+"_OS_EXIT_0",flush=True)

    def test_01_original_P49_11_native_protection_source_shas_unchanged(self):
        for name,expected in FROZEN_P49_PINS.items():
            with self.subTest(path=name):
                self.assertEqual(sha((self.p49dir/name).read_bytes()),expected)
        self.assertEqual(len(FROZEN_P49_PINS),11)
        print("P205_ORIGINAL_FROZEN_P49_11_SHA256=EXACT",flush=True)

    def test_02_original_full_P49_native_release_and_WinCred_denial_20_cases(self):
        source=sorted(self.p49dir.glob("*.cs"))
        self.assertEqual(len(source),12)
        self._compile_and_run("p205_original_P49_20",
           source,"P99FullOriginalNativeDenialTests",
           "P99_ORIGINAL_NATIVE_DENIAL_TESTS_PASSED=20",20)
        print("P205_REALKEY_ORIGINAL_P49_EFFECT_DENIAL=ACTIVE",flush=True)

    def test_03_current_candidate_service_host_remains_denial_24_cases(self):
        old=sorted(p for p in self.p49dir.glob("*.cs")
                   if p.name not in ("CustodyService.cs","FullOriginalNativeDenialTests.cs"))
        self.assertEqual(len(old),10)
        candidate=[self.native/name for name in CANDIDATE]
        self.assertTrue(all(p.is_file() for p in candidate))
        test=self.native/"ServiceHostAdmissionTests.cs"
        self._compile_and_run("p205_candidate_C1_host_24",
             old+candidate+[test],"P101ServiceHostAdmissionTests",
             "P101_CANDIDATE_NATIVE_HOST_TESTS_PASSED=24",24)
        print("P205_C1_REALKEY_CURRENT_NATIVE_SERVICE_HOST=DENIAL_ONLY",flush=True)

    def test_04_current_source_still_has_no_trusted_signer_IPC_or_effect_GO(self):
        host=(self.native/"CustodyService.cs").read_text("utf8")
        boundary=(self.native/"ServiceOwnedAdmissionBoundary.cs").read_text("utf8")
        hold=(self.native/"CandidateCredentialEffectHold.cs").read_text("utf8")
        self.assertIn("NO service Main method",host)
        self.assertIn("throw new InvalidOperationException",host)
        self.assertIn("return CustodyOutcome.Denied;",boundary)
        self.assertIn("NativeMutationAdmissionPending()",boundary)
        self.assertIn("internal static bool LegacyEffectEntryDisabled() { return true; }",hold)
        self.assertIn("internal static bool NativeMutationAdmissionPending() { return true; }",hold)
        self.assertNotIn("ServiceBase.Run(",host)
        print("P205_TRUSTED_CONSENT_SERVICE_EFFECT_AND_INSTALLED_LOADER=NOT_IMPLEMENTED",flush=True)

    def test_05_old_Python_CredMan_backend_not_a_unified_product_trust_gate(self):
        path=ROOT/"nayeon/secrets/windows_credential.py"
        code=path.read_text("utf8")
        self.assertIn("self._dll.CredWriteW(",code)
        self.assertIn("self._dll.CredDeleteW(",code)
        self.assertIn('"""Isolated Windows Generic Credential storage; no production consumers yet."""',code)
        self.assertNotIn("ServiceOwnedAdmissionBoundary",code)
        # Review ONLY; never import/instantiate the backend or native DLL here.
        print("P205_OLDER_PYTHON_CREDMAN_BACKEND=EXISTS_NOT_GOVERNED_BY_NATIVE_C1",flush=True)

    def test_06_real_key_and_production_HCR_both_deny_forged_readiness(self):
        self.assertEqual(ACTUAL_GATES["real_key_Save_Replace_Delete"],"NO_GO")
        self.assertEqual(ACTUAL_GATES["production_release"],"HOLD")
        self.assertEqual(ACTUAL_GATES["complete_unfiltered_native_Windows_product_regressions"],"0/3")
        self.assertEqual(ACTUAL_GATES["qualified_GOV_SEC_REL"],"OPEN_SEVEN")
        self.assertEqual(ACTUAL_GATES["privileged_G0_G6"],"OPEN")
        print("P205_REAL_KEY_GATE=NO_GO|PRODUCTION_RELEASE_GATE=HOLD",flush=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p205-key-gates"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
      "checkpoint":"P205","historical_H":"HOLD",
      "current_C":"FRESH_NATIVE_WINDOWS_REAL_KEY_AND_PRODUCTION_GATE_EVIDENCE",
      "production_R":"HOLD",
      "real_key_admission":"NO_GO",
      "production_release":"NO_GO",
      "native_C1_signed_UI_and_IPC":"NOT_IMPLEMENTED",
      "native_C1_one_use_credential_actor":"DENIAL_ONLY",
      "legacy_Python_WinCred":"REAL_DLL_BACKEND_EXISTS_NOT_UNIFIED_WITH_C1_SERVICE_GATE",
      "G0_G6_qualified_authority":"OPEN",
      "current_Phase10_P76_live_G0":"UNINTEGRATED",
      "original_private_B_ADS_gap":"UNPATCHED",
      "independent_GOV_SEC_REL":"OPEN_SEVEN",
      "original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED",
      "complete_unfiltered_native_Windows_full_product_regressions":"0/3",
      "release_readiness":ACTUAL_GATES}
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["authenticated_original_P204"]=authenticate_p204(
             os.environ.get("P205_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if k in ("P205_ARCHIVE_TOKEN","GH_TOKEN","GITHUB_TOKEN") or k.endswith(("_API_KEY","_SECRET")):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        rawlog=out/"p205_actual_windows_realkey_release_6.log"
        with rawlog.open("wb") as f:
            proc=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                  "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                stdout=f,stderr=subprocess.STDOUT,timeout=280,check=False)
        raw=rawlog.read_bytes();txt=raw.decode("utf8","replace").replace("\r\n","\n")
        markers=re.findall(r"P205_[^\r\n]+",txt)
        ledger["current_P205_native"]={
          "raw_log":rawlog.name,"raw_log_SHA256":sha(raw),
          "actual_OS_exit":proc.returncode,
          "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
          "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
          "events":markers,"failures":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}
        if proc.returncode!=0 or ledger["current_P205_native"]["test_footer"]!=["6"] or \
           not ledger["current_P205_native"]["complete_OK"]:
            raise RuntimeError("P205 native real-key/production gated test execution FAILED; preserve logs")
        for label in ("p205_original_P49_20","p205_candidate_C1_host_24"):
            log=out/(label+"_native.log")
            if not log.is_file():
                raise RuntimeError("P205 genuine Windows C# original native test log missing "+label)
            ledger[label+"_SHA256"]=sha(log.read_bytes())
            comp=out/(label+"_compiler.log")
            ledger[label+"_compiler_OS_exit"]="0"
            ledger[label+"_compiler_log_SHA256"]=sha(comp.read_bytes())
        for marker in (
          "P205_ORIGINAL_FROZEN_P49_11_SHA256=EXACT",
          "P205_P205_ORIGINAL_P49_20_ACTUAL_WINDOWS_NATIVE_CASES=20_OS_EXIT_0",
          "P205_P205_CANDIDATE_C1_HOST_24_ACTUAL_WINDOWS_NATIVE_CASES=24_OS_EXIT_0",
          "P205_C1_REALKEY_CURRENT_NATIVE_SERVICE_HOST=DENIAL_ONLY",
          "P205_OLDER_PYTHON_CREDMAN_BACKEND=EXISTS_NOT_GOVERNED_BY_NATIVE_C1",
          "P205_REAL_KEY_GATE=NO_GO|PRODUCTION_RELEASE_GATE=HOLD"):
            if marker not in markers:
                raise RuntimeError("P205 real OS/security proof marker absent "+marker)
        after=custody();ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P205 exact Git HEAD/source changed during native Windows audit")
        complete=True
        print("P205_FROZEN_P49_20_AND_NATIVE_C1_24_REAL_WINDOWS=44_SELECTED_DENIAL_CASES_PASS",flush=True)
        print("P205_CURRENT_WIN_CRED_REALKEY=NO_GO|PRODUCTION=HOLD",flush=True)
        print("P205_REVIEW_AND_PLATFORM_ADMIN_DECISIONS=REQUIRED_EXTERNAL",flush=True)
        print("P205_REAL_KEY_LOCAL_ENTRY=NOT_AUTHORIZED",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P205_REALKEY_PRODUCTION_GATE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["source_bound_checkpoint_complete_NOT_real_key_or_production_GO"]=complete
        (out/"p205_realkey_production_HCR_ledger.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":raise SystemExit(main())
