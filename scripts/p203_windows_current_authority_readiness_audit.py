"""P203 authentic Windows CURRENT public source route and C1 implementation-ready audit.

READ-ONLY, no import/exec of product source except explicit denied public source
gate in a nonprivileged host. No WinCred, secrets, service install, mutation
or product admission. This is an IMPLEMENTATION PLANNING BLOCKER GATE, not GO.
"""
from __future__ import annotations
import ast, hashlib, io, json, os, re, subprocess, sys, zipfile
from pathlib import Path
import unittest
from scripts import p202_windows_fixed_owner_boundary_review as prior
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact

ROOT=Path(__file__).resolve().parents[1]
P202="fb6814fad38fb021576ee3aa7ee01558ea4f3cb5"
BRANCH="byok-c1-p203-current-authority-implementation-readiness-20261114"
NEW={"scripts/p203_windows_current_authority_readiness_audit.py",
     "docs/byok-c1-p203-current-authority-implementation-readiness.md",
     ".github/workflows/p203-windows-implementation-readiness.yml"}
P202_ARTIFACT=14108109712
P202_ARCHIVE_SHA="49C9B967377948C36F05ACBF916EB77142AA3A7BECA18F6B81140621F312CA51"
P202_LOG="p202_real_Windows_fixed_owner_original_B_8.log"
P202_LOG_SHA="FB2C1AADC286AD0748AAA93CF8A05DA064528F37E9183F98A7BC59B14632C405"
P202_LEDGER="p202_fixed_owner_Phase10_boundary_HCR_ledger.json"
P202_LEDGER_SHA="C78EC56DDF029DC4EF9C82719B82C71FDBDEFD744E34D2BC0F9F95CA8147E1D0"
PUBLIC_ROUTE=(
 ("tests/phase8_byok_b_scope_migration.py","assert_byok_b_integrity",
  "tests.phase10_perception_scope_migration","assert_phase10_integrity"),
 ("tests/phase10_perception_scope_migration.py","assert_phase10_integrity",
  "tests.phase10_2_privacy_scope_migration","assert_phase10_2_privacy_integrity"),
 ("tests/phase10_2_privacy_scope_migration.py","assert_phase10_2_privacy_integrity",
  "tests.phase10_3_scope_migration","assert_phase10_3_integrity"),
 ("tests/phase10_3_scope_migration.py","assert_phase10_3_integrity",
  "tests.phase8_byok_c1_p76_scope","assert_p76_offline_integrity"),
)
RELEASE_BLOCKERS=(
 "G0 historical B ADS gate and modern P76/Phase10 provenance integration",
 "G1 independent signed trusted user-consent and authenticated IPC origin",
 "G2 native single-owner linearized terminal custody/WinCred effect dispatch",
 "G3 verified durable one-use consumption, fault/recovery and rollback root",
 "G4 main/helper/installer signed code integrity, secure loader and source-to-consumer custody",
 "G5 installed real Windows target/platform signing policy and x86 admission",
 "G6 qualified independent GOV/SEC/REL acceptance and 3 full original Windows product regressions",
)

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest().upper()
def git(*args:str)->bytes:return prior.git(*args)

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    base=git("merge-base",P202,"HEAD").decode().strip()
    changed=set(git("diff","--name-only",P202,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=head or
        git("branch","--show-current").decode().strip()!=BRANCH or
        base!=P202 or changed!=NEW or dirty):
        raise RuntimeError("P203 authenticated exact GitHub Windows source custody mismatch "+
            json.dumps({"head":head,"base":base,"changed":sorted(changed),"dirty":dirty[:320]}))
    for subtree in ("tests","nayeon","native_c1_candidate"):
        if git("rev-parse",P202+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P203 existing original historical/product/native service source changed "+subtree)
    for path in ("scripts/p202_windows_fixed_owner_boundary_review.py",
                 "scripts/p201_windows_original_b_ads_remediation_candidate.py",
                 "scripts/p200_windows_executable_content_binding_review.py",
                 "scripts/p199_windows_consumer_identity_handoff_review.py",
                 "scripts/p195_windows_durable_root_authority_aba_review.py"):
        if git("show",P202+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P203 predecessor source/native failure witness overwritten "+path)
    return {"P203_HEAD":head,"exact_P202_parent":P202,
            "only_three_new_audit_paths":sorted(NEW),
            "existing_public_Phase10_original_B_and_native_C1_sources_unmodified":True}

def authenticate_p202(token:str)->dict:
    if len(token)<8:raise RuntimeError("P203 original P202 ZIP access unavailable")
    archive=_download_artifact(P202_ARTIFACT,P202_ARCHIVE_SHA,token)
    if sha(archive)!=P202_ARCHIVE_SHA:raise RuntimeError("P203 predecessor ZIP SHA invalid")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        if z.testzip() is not None or set(z.namelist())!={P202_LOG,P202_LEDGER}:
            raise RuntimeError("P203 predecessor original archive inventory/CRC invalid")
        log=z.read(P202_LOG);led=z.read(P202_LEDGER)
        if sha(log)!=P202_LOG_SHA or sha(led)!=P202_LEDGER_SHA:
            raise RuntimeError("P203 original P202 native members SHA mismatch")
        txt=log.decode("utf8","replace").replace("\r\n","\n")
        for marker in (
            "P202_NATIVE_ORIGINAL_B_SELF_ADS_WITH_FIXED_OWNER=REFUSED",
            "P202_NATIVE_OTHER_PINNED_SOURCE_ADS_WITH_FIXED_OWNER=REFUSED",
            "P202_PUBLIC_FIXED_BRIDGE_CALLER_GATE_CALLBACK=NOT_ACCEPTED",
            "P202_CURRENT_PUBLIC_PHASE10_SUCCESSOR_ROUTING=NOT_CHANGED",
        ):
            if marker not in txt:
                raise RuntimeError("P203 original P202 security witness absent "+marker)
        if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=["8"] or
            not re.search(r"^OK\s*$",txt,re.M)):
            raise RuntimeError("P203 original P202 8-case native Windows footer not authentic")
        record=json.loads(led);native=record.get("current_P202_native",{})
        if (record.get("checkpoint")!="P202" or
            record.get("historical_H")!="HOLD" or record.get("production_R")!="HOLD" or
            record.get("native_full_product_regressions_accepted")!="0/3" or
            record.get("source_before")!=record.get("source_after") or
            record.get("source_before",{}).get("P202_HEAD")!=P202 or
            native.get("actual_OS_exit")!=0 or native.get("raw_log_SHA256")!=P202_LOG_SHA or
            native.get("test_footer")!=["8"] or not native.get("complete_OK") or
            record.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P203 original P202 actual OS/Git/HCR HOLD lineage invalid")
    return {"original_P202_artifact":P202_ARTIFACT,
            "ZIP_SHA256":P202_ARCHIVE_SHA,
            "source_bound_8_selected_Windows":"AUTHENTICATED",
            "release_hold":"PRESERVED"}

def latest_function(path:str,func:str)->ast.FunctionDef:
    tree=ast.parse((ROOT/path).read_text(encoding="utf8"),filename=path)
    defs=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==func]
    if not defs:raise AssertionError("P203 public route missing exact function "+path+":"+func)
    return defs[-1]

def static_edge(path:str,owner:str,import_module:str,next_func:str)->bool:
    node=latest_function(path,owner)
    imported=False;returned=False
    for child in ast.walk(node):
        if isinstance(child,ast.ImportFrom) and child.module==import_module and \
           any(alias.name==next_func and alias.asname is None for alias in child.names):
            imported=True
        if isinstance(child,ast.Return) and isinstance(child.value,ast.Call) and \
           isinstance(child.value.func,ast.Name) and child.value.func.id==next_func and \
           not child.value.args and not child.value.keywords:
            returned=True
    return imported and returned

class P203NativeCurrentAuthorityReadiness(unittest.TestCase):
    """Eight genuine hosted Windows *read-only* current source authority tests."""
    def test_01_all_four_actual_public_successor_edges_are_exact_and_unconditional(self):
        for path,entry,imported,fn in PUBLIC_ROUTE:
            with self.subTest(path=path):
                self.assertTrue(static_edge(path,entry,imported,fn),
                                "P203 public route source changed or fallback introduced")
        print("P203_ACTUAL_PUBLIC_B_TO_PHASE10_1_2_3_TO_P76_SOURCE_ROUTE=VERIFIED_STATIC",flush=True)

    def test_02_current_p76_is_offline_source_only_with_independent_branch_requirement(self):
        node=latest_function("tests/phase8_byok_c1_p76_scope.py","assert_p76_offline_integrity")
        text=ast.get_source_segment((ROOT/"tests/phase8_byok_c1_p76_scope.py").read_text(),node)
        self.assertIn('BRANCH',text)
        self.assertIn('wrong exact P76 prototype branch',text)
        self.assertNotIn("CredWrite",text)
        self.assertNotIn("CredDelete",text)
        self.assertNotIn("SaveOrReplace",text)
        print("P203_LIVE_PUBLIC_FINAL_P76=OFFLINE_BRANCH_BOUND_NO_EFFECT_AUTHORITY",flush=True)

    def test_03_private_original_b_and_current_phase10_admission_are_distinct(self):
        src=(ROOT/"tests/phase8_byok_b_scope_migration.py").read_text()
        self.assertIn("_assert_byok_b_historical = assert_byok_b_integrity",src)
        self.assertTrue(static_edge(*PUBLIC_ROUTE[0]))
        other=(ROOT/"tests/phase10_3_scope_migration.py").read_text()
        self.assertIn("_phase10_3_sealed_historical_assert = assert_phase10_3_integrity",other)
        print("P203_ORIGINAL_FULL_B_PRIVATE_NOT_CURRENT_PHASE10_ADMISSION=VERIFIED",flush=True)

    def test_04_actual_native_c1_service_boundary_is_denial_not_privileged_go(self):
        p=(ROOT/"native_c1_candidate/ServiceOwnedAdmissionBoundary.cs").read_text()
        host=(ROOT/"native_c1_candidate/CustodyService.cs").read_text()
        for marker in ("RefuseBoundRequest","RefuseRequest","return CustodyOutcome.Denied;",
                       "CandidateCredentialEffectHold.NativeMutationAdmissionPending()"):
            self.assertIn(marker,p)
        self.assertIn("NO production dispatch",p[:450])
        self.assertIn("NO service Main method",host)
        self.assertIn("NO native effect path",host)
        print("P203_NATIVE_SERVICE_CANDIDATE=DENIAL_ONLY_NO_PRODUCTION_DISPATCH",flush=True)

    def test_05_old_ads_candidate_and_fixed_owner_are_not_public_phase10_callers(self):
        b=(ROOT/"tests/phase8_byok_b_scope_migration.py").read_text()
        p10=(ROOT/"tests/phase10_perception_scope_migration.py").read_text()
        p102=(ROOT/"tests/phase10_2_privacy_scope_migration.py").read_text()
        p103=(ROOT/"tests/phase10_3_scope_migration.py").read_text()
        for text in (b,p10,p102,p103):
            self.assertNotIn("byok_b_fixed_owner_bridge_candidate",text)
            self.assertNotIn("byok_b_ntfs_physical_admission_candidate",text)
        print("P203_P201_P202_ADS_BRIDGE=NOT_WIRED_TO_CURRENT_PUBLIC_ADMISSION",flush=True)

    def test_06_real_current_branch_public_b_gate_refuses_not_old_fallback(self):
        env=os.environ.copy()
        for k in list(env):
            if k in {"GH_TOKEN","GITHUB_TOKEN","P203_ARCHIVE_TOKEN"} or k.endswith(("_API_KEY","_SECRET")):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONNOUSERSITE"]="1"
        env.pop("PYTHONPATH",None)
        command=("from tests.phase8_byok_b_scope_migration import assert_byok_b_integrity; "
                 "assert_byok_b_integrity()")
        proc=subprocess.run([sys.executable,"-B","-c",command],cwd=ROOT,env=env,
           stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
           timeout=65,check=False)
        output=proc.stdout.decode("utf8","replace")
        self.assertNotEqual(proc.returncode,0,"P203 unrelated audit branch admitted public source")
        self.assertIn("P76 offline source refused: wrong exact P76 prototype branch",output)
        self.assertNotIn("COMPLETE_UNSTAGED",output)
        print("P203_REAL_NATIVE_PUBLIC_B_TO_P76_WRONG_BRANCH=REFUSED_NO_HISTORIC_FALLBACK",flush=True)

    def test_07_no_candidate_signer_os_loader_or_service_owner_was_enabled(self):
        # All checks are for current source reality; never elevate names into GO.
        candidate=(ROOT/"nayeon/brain/byok_b_fixed_owner_bridge_candidate.py").read_text()
        self.assertIn("Not the production gate",candidate)
        self.assertIn("admit_isolated_fixed_owner_original_b",candidate)
        self.assertIn("not OS-attested",candidate)
        p76=(ROOT/"tests/phase8_byok_c1_p76_scope.py").read_text()
        self.assertIn("not release authority",p76)
        native=(ROOT/"native_c1_candidate/ServiceOwnedAdmissionBoundary.cs").read_text()
        self.assertIn("return CustodyOutcome.Denied;",native)
        print("P203_PRODUCT_C1_TRUSTED_SIGNER_IPC_EFFECT_DISPATCH=NOT_READY_FOR_PRODUCTION",flush=True)

    def test_08_exact_unwaived_native_regression_and_qualified_review_hold(self):
        self.assertEqual(len(RELEASE_BLOCKERS),7)
        self.assertEqual(len(PUBLIC_ROUTE),4)
        self.assertTrue(all(s.startswith("G"+str(i)+" ") for i,s in enumerate(RELEASE_BLOCKERS)))
        self.assertNotEqual(P202,P201_ORIGINAL_PARENT_FOR_AUDIT)
        print("P203_QUALIFIED_GOV_SEC_REL_AND_G0_G6=OPEN",flush=True)
        print("P203_ORIGINAL_FULL_PRODUCT_NATIVE_WINDOWS=0/3_HOLD",flush=True)

P201_ORIGINAL_PARENT_FOR_AUDIT="97edba1dd4f7a1ed518e8007e9708ecc426598c5"

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p203-current-authority"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
      "checkpoint":"P203","historical_H":"HOLD",
      "current_C":"SOURCE_BOUND_PHASE10_PUBLIC_AUTHORITY_IMPLEMENTATION_READINESS_MAP",
      "production_R":"HOLD","implementation_for_synthetic_isolated_dev":"AUTHORIZED",
      "production_credential_implementation_admission":"NOT_READY",
      "full_unfiltered_native_Windows_product_regressions_accepted":"0/3",
      "source_route":PUBLIC_ROUTE,"implementation_G0_G6_blockers":RELEASE_BLOCKERS,
      "qualified_independent_GOV_SEC_REL":"OPEN_ALL_SEVEN",
      "privileged_G0_G6":"OPEN",
      "trusted_service_effect_dispatch":"DENIAL_ONLY",
      "original_legacy_B_ADS_gap":"UNPATCHED",
      "P201_P202_guard_public_Phase10_integration":"NOT_CONNECTED",
      "signed_loader_source_bundle_IPC_durable_rollback_root":"NOT_ESTABLISHED",
      "original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED"}
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["authenticated_original_P202"]=authenticate_p202(
            os.environ.get("P203_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if k in ("GITHUB_TOKEN","GH_TOKEN","P203_ARCHIVE_TOKEN") or k.endswith(("_API_KEY","_SECRET")):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p203_actual_Windows_current_public_authority_8.log"
        with log.open("wb") as f:
            proc=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                  "scripts.p203_windows_current_authority_readiness_audit.P203NativeCurrentAuthorityReadiness"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                stdout=f,stderr=subprocess.STDOUT,timeout=160,check=False)
        raw=log.read_bytes();txt=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"P203_[^\r\n]+",txt)
        ledger["current_P203_native"]={
            "raw_log":log.name,"raw_log_SHA256":sha(raw),
            "actual_OS_exit":proc.returncode,
            "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
            "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
            "events":events,
            "failures":re.findall(r"^(?:ERROR|FAIL): .+$",txt,re.M)}
        if (proc.returncode!=0 or ledger["current_P203_native"]["test_footer"]!=["8"] or
            not ledger["current_P203_native"]["complete_OK"]):
            raise RuntimeError("P203 current public source authority mapping actual Windows tests FAILED")
        for event in (
            "P203_ACTUAL_PUBLIC_B_TO_PHASE10_1_2_3_TO_P76_SOURCE_ROUTE=VERIFIED_STATIC",
            "P203_LIVE_PUBLIC_FINAL_P76=OFFLINE_BRANCH_BOUND_NO_EFFECT_AUTHORITY",
            "P203_NATIVE_SERVICE_CANDIDATE=DENIAL_ONLY_NO_PRODUCTION_DISPATCH",
            "P203_P201_P202_ADS_BRIDGE=NOT_WIRED_TO_CURRENT_PUBLIC_ADMISSION",
            "P203_REAL_NATIVE_PUBLIC_B_TO_P76_WRONG_BRANCH=REFUSED_NO_HISTORIC_FALLBACK",
            "P203_ORIGINAL_FULL_PRODUCT_NATIVE_WINDOWS=0/3_HOLD"
        ):
            if event not in events:raise RuntimeError("P203 required source-specific Windows gate outcome missing "+event)
        after=custody();ledger["source_after"]=after
        if before!=after:raise RuntimeError("P203 current source Git drift during Windows audit")
        complete=True
        print("P203_SOURCE_AUTHENTIC_P202_8_WINDOWS=VERIFIED",flush=True)
        print("P203_REAL_WINDOWS_CURRENT_PRODUCTION_AUTHORITY_MAPPING=8/8_PASS",flush=True)
        print("P203_NONPRIVILEGED_SYNTHETIC_IMPLEMENTATION_WORK=GO",flush=True)
        print("P203_REAL_CREDENTIAL_OR_PRIVILEGED_SERVICE_IMPLEMENTATION=NO_GO",flush=True)
        print("P203_EXTERNAL_INDEPENDENT_SECURITY_REVIEWS=OPEN|FULL_PRODUCT_WINDOWS=0/3",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P203_READINESS_SOURCE_AUDIT=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["source_audit_complete_NOT_implementation_GO"]=complete
        (out/"p203_current_authority_implementation_readiness_HCR.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if complete else 1
if __name__=="__main__":raise SystemExit(main())
