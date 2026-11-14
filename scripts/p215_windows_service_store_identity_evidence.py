"""P215 genuine Windows account principal and read-only CredGetSessionTypes to actual CustodyService.

Source-bound on exact P214 and original P49/P96/P113..P116/P132..P214.
Compiles existing reviewed native dependencies and new TEST-ONLY glue, then
executes 16 real Windows principal and named-pipe tests against the current C1 host
(admission permanently DENIED). Zero keys, credential effects, service
installation, actual signed UI, installer or Code Integrity changes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.p207_windows_native_consent_acceptance_prep import ROOT,git
from scripts.p206_windows_credential_effect_ownership import PRIOR_BLOBS,run_suite,sha256
from scripts.p208_windows_synthetic_terminal_owner import native as p208_native
from scripts.p209_windows_protected_synthetic_custody import p209_native
from scripts.p210_windows_python_native_synthetic_integration import compile_native_bridge
from scripts.p213_windows_signed_service_observation import compile_native_wintrust_probe
from nayeon.brain.p213_readonly_windows_signer_observer import (
    observe_readonly_windows_signer,
    system_powershell_reference,P213SignatureStatus,source_pins_unissued,
)
from nayeon.brain.p211_high_assurance_package_quarantine import (
    inspect_current_source_tree,
)

P214="707e591417aa81b61ad9d97c6c90c0f5e7dec5ac"
BRANCH="byok-c1-p215-windows-store-principal-ownership-20261114"
ADDED={
 "native_c1_candidate/P215WindowsStorePrincipalReadOnlyAdmission.cs",
 "tests/p215_native_store_principal/P215RealWindowsStorePrincipalTests.cs",
 "scripts/p215_windows_service_store_identity_evidence.py",
 "docs/byok-c1-p215-windows-credential-store-principal-decision.md",
 ".github/workflows/p215-windows-store-principal-admission.yml",
}
ORIGINAL_PRESERVE=(
 "nayeon/secrets/windows_credential.py",
 "nayeon/brain/local_byok_user_scope.py",
 "nayeon/desktop_alpha/local_byok_launch_bridge.py",
 "nayeon/desktop_alpha/local_byok_window.py",
 "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
 "native_c1_candidate/CustodyService.cs",
 "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs",
 "native_c1_candidate/ServiceBoundRequestIdentity.cs",
 "native_c1_candidate/P208SyntheticTerminalOwner.cs",
 "native_c1_candidate/P209SyntheticDurableCustody.cs",
 "native_c1_candidate/P210SyntheticBoundaryExecutable.cs",
 "native_c1_candidate/P213NativeWintrustObservation.cs",
 "native_c1_candidate/P214ActualWindowsHostReadOnlyIntegration.cs",
 "tests/p214_native_host_integration/P214RealWindowsHostIntegrationTests.cs",
 "native_c1_g1_peer_review/WindowsPipePeerObservation.cs",
 "native_c1_g1_peer_review/WindowsPipeClientProcessProvenance.cs",
 "native_c1_g1_peer_review/WindowsPipeClientSessionIntegrity.cs",
 "native_c1_g1_peer_review/WindowsWintrustFilePolicyReview.cs",
 "scripts/p212_high_assurance_build_gate.py",
 "scripts/p213_windows_signed_service_observation.py",
 "nayeon/brain/p211_high_assurance_package_quarantine.py",
 "nayeon/brain/p213_readonly_windows_signer_observer.py",
 "tests/test_p213_real_windows_authenticode_service_admission.py",
)

def custody()->dict:
    if (sys.platform!="win32" or os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("RUNNER_OS")!="Windows"
        or os.getenv("GITHUB_EVENT_NAME")!="push"
        or os.getenv("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH):
        raise RuntimeError("P214 requires authentic hosted Windows GitHub push")
    head=git("rev-parse","HEAD")
    if head!=os.getenv("GITHUB_SHA") or git("merge-base",P214,"HEAD")!=P214:
        raise RuntimeError("P215 exact current event/P214 source baseline mismatch")
    if set(git("diff","--name-only",P214,"HEAD").splitlines())!=ADDED:
        raise RuntimeError("P214 historical source drift/not precisely 5 additions")
    if git("status","--porcelain=v1","-uall"):
        raise RuntimeError("P215 checkout dirty")
    pins={}
    for p,expected in PRIOR_BLOBS.items():
        if git("rev-parse","HEAD:"+p)!=expected or git(
            "rev-parse",P213+":"+p)!=expected:
            raise RuntimeError("P215 frozen P205 original source modified "+p)
        pins[p]={"git_blob":expected,"disk_SHA256":sha256((ROOT/p).read_bytes())}
    for p in ORIGINAL_PRESERVE:
        old=git("rev-parse",P214+":"+p)
        if old!=git("rev-parse","HEAD:"+p):
            raise RuntimeError("P214 original P49/P113-116/P132/C1 source changed "+p)
        pins[p]={"git_blob":old,"disk_SHA256":sha256((ROOT/p).read_bytes())}
    return {"head":head,"exact_P214_ancestor":P214,
            "five_additive_paths":sorted(ADDED),
            "original_frozen_and_peer_source_pins":pins}

from scripts.p214_windows_real_peer_service_admission import native_p214_integration

def native_p215_integration(out:Path)->dict:
    compiler=Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
    if sys.platform!="win32" or not compiler.is_file():
        raise RuntimeError("P215 genuine native Windows compiler absent")
    old=ROOT/"tests/p99_original_native_c1_denial"
    candidate=ROOT/"native_c1_candidate"
    peer=ROOT/"native_c1_g1_peer_review"
    src=[
        old/"ServiceGate.cs",old/"ProtectedAcl.cs",old/"CustodyLedger.cs",
        candidate/"CustodyService.cs",
        candidate/"ServiceOwnedAdmissionBoundary.cs",
        candidate/"ServiceBoundRequestIdentity.cs",
        candidate/"NativeJ2ProtectedReadOnlyPreflight.cs",
        candidate/"CandidateCredentialEffectHold.cs",
        candidate/"IsolatedCandidateContracts.cs",
        candidate/"CandidateProtectedReadOnlySnapshot.cs",
        peer/"WindowsPipePeerObservation.cs",
        peer/"WindowsPipeClientProcessProvenance.cs",
        peer/"WindowsPipeClientSessionIntegrity.cs",
        peer/"WindowsWintrustFilePolicyReview.cs",
        candidate/"P215ActualWindowsHostReadOnlyIntegration.cs",
        candidate/"P215WindowsStorePrincipalReadOnlyAdmission.cs",
        ROOT/"tests/p215_native_store_principal/P215RealWindowsStorePrincipalTests.cs",
    ]
    if len(src)!=17 or any(not f.is_file() for f in src):
        raise RuntimeError("P215 original P113-P116 + service C1 source inventory invalid")
    for f in src[:-2]:
        path=f.relative_to(ROOT).as_posix()
        if git("rev-parse","HEAD:"+path)!=git("rev-parse",P213+":"+path):
            raise RuntimeError("P215 native baseline drift "+path)
    for f in src[-2:]:
        code=f.read_text("utf8")
        if "#if C1_REVIEW_ISOLATED_ASSEMBLY" not in code:
            raise RuntimeError("P215 production assembly source lacks test isolation")
        for pattern in ("CredWriteW(","CredDeleteW(","ServiceBase.Run(",
                        "SetNamedSecurityInfo(","WindowsCredentialBackend("):
            if pattern in code:
                raise RuntimeError("P215 forbidden production effect in test bridge "+pattern)
    exe=out/"p214_native_real_OS_peer_to_C1_refusal.exe"
    args=[str(compiler),"/nologo","/target:exe","/platform:x64",
        "/define:C1_REVIEW_ISOLATED_ASSEMBLY",
        "/r:System.ServiceProcess.dll","/r:System.Core.dll",
        "/main:P215RealWindowsStorePrincipalTests",
        "/out:"+str(exe)]+[str(f) for f in src]
    c=subprocess.run(args,cwd=ROOT,stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        timeout=90,check=False)
    clog=out/"p214_native_real_OS_compiler.log"
    clog.write_bytes(c.stdout)
    if c.returncode!=0 or c.stdout.strip():
        raise RuntimeError("P215 native compiler failed/diagnostics emitted")
    p=subprocess.run([str(exe)],cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        timeout=90,check=False)
    nlog=out/"p214_native_OS_peer_to_CustodyService_14.log"
    nlog.write_bytes(p.stdout)
    raw=p.stdout.decode("utf8","replace").replace("\r\n","\n")
    count=sum(line.startswith("PASS ") for line in raw.splitlines())
    fail=sum(line.startswith("FAIL ") for line in raw.splitlines())
    if (p.returncode!=0 or count!=16 or fail!=0
        or "P215_REAL_WINDOWS_PRINCIPAL_C1_HOST_PASS=16" not in raw
        or "P215_REAL_WINDOWS_PRINCIPAL_C1_HOST_FAIL=0" not in raw
        or "P215_REAL_KEY=NO_GO|PRODUCTION=HOLD" not in raw):
        raise RuntimeError("P215 authentic Windows native C1 peer/host integration failed")
    return {
       "csc_exit":c.returncode,
       "csc_raw_SHA256":sha256(c.stdout),
       "native_exe_SHA256":sha256(exe.read_bytes()),
       "OS_native_process_exit":p.returncode,
       "OS_native_stdout_SHA256":sha256(p.stdout),
       "genuine_namedpipe_cross_process_cases":True,
       "real_client_token_process_session_and_native_WinTrust":True,
       "actual_native_CustodyService_admission_methods_invoked":True,
       "P215_native_pass":count,
       "P215_native_fail":fail,
       "actual_WinCred_keys_services_installers_or_machine_policy":"NONE",
    }


def main()->int:
    out=Path(os.getenv("RUNNER_TEMP",str(ROOT)))/"nayeon-p215-evidence"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
        "checkpoint":"P215",
        "H":"HOLD_NO_INDEPENDENT_SERVICE_PRINCIPAL_OR_PROTECTED_STORE_SELECTION",
        "C":"REAL_WINDOWS_TOKEN_CREDGETSESSIONTYPES_TO_CURRENT_C1_HOST_REFUSAL",
        "R":"PRODUCTION_HOLD",
        "real_key_R0_R4":"NO_GO",
        "production_P0_P5":"HOLD",
        "G0_G6":"OPEN",
        "independent_GOV_SEC_REL":"SEVEN_REVIEW_DECISIONS_OPEN",
        "unfiltered_accepted_native_Windows_product_regressions":"0/3",
        "P132_Python_CredWriteW_DeleteW":"SOURCE_REACHABLE_UNCHANGED",
        "actual_signed_UI_service_OS_policy":"NOT_AUTHORISED",
        "provider_C2":"NOT_AUTHORISED",
    }
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        risk=inspect_current_source_tree(ROOT)
        if (not source_pins_unissued()
            or not risk.exact_legacy_source_readable
            or not risk.high_assurance_legacy_risk_present
            or not risk.native_c1_service_denial_only):
            raise RuntimeError("P215 original product/native risk source no longer matches")
        old=[
            ("p132_original_36",["discover","-s","tests","-p","test_local_user_scope_byok.py","-v"],36),
            ("p206_original_12",["discover","-s","tests","-p","test_p206_unified_effect_ownership.py","-v"],12),
            ("p207_original_14",["discover","-s","tests","-p","test_p207_user_scope_native_consent_review.py","-v"],14),
            ("p49_native_20_c1_24",["-v",
                "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_02_original_full_P49_native_release_and_WinCred_denial_20_cases",
                "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_03_current_candidate_service_host_remains_denial_24_cases"],2),
        ]
        for name,args,expected in old:
            item=run_suite(name,args,out/(name+".log"))
            ledger[name]=item
            if not item["complete_OK"] or item["test_footer"]!=[str(expected)]:
                raise RuntimeError("P215 prior Windows source tests failed "+name)
        ledger["p208_native_20"]=p208_native(out)
        ledger["p209_windows_DPAPI_native_18"]=p209_native(out)
        p210=compile_native_bridge(out)
        ledger["p210_compiler"]=p210
        os.environ["P210_NATIVE_EXE"]=p210["path"]
        p213=compile_native_wintrust_probe(out)
        ledger["p213_compiler"]=p213
        os.environ["P213_NATIVE_WINTRUST_EXE"]=p213["exe"]
        systemfile=system_powershell_reference()
        if systemfile is None:
            raise RuntimeError("P214 missing real Windows system signature reference")
        system=observe_readonly_windows_signer(systemfile)
        unsigned=observe_readonly_windows_signer(Path(p210["path"]))
        if (system.status is P213SignatureStatus.UNKNOWN
            or unsigned.status is not P213SignatureStatus.OS_POLICY_REJECTED):
            raise RuntimeError("P214 original P213 real Windows signature status unavailable")
        ledger["original_P213_OS_WinTrust"]={
            "system_reference_status":system.status.value,
            "unsigned_C1_candidate_status":unsigned.status.value,
            "source_image_release_authority":False,
        }
        for label,pattern,n in (
          ("p210_cross_process_13","test_p210_python_native_synthetic_integration.py",13),
          ("p211_package_quarantine_22","test_p211_high_assurance_package_quarantine.py",22),
          ("p212_mandatory_build_20","test_p212_mandatory_high_assurance_build_gate.py",20),
          ("p213_native_WinTrust_20","test_p213_real_windows_authenticode_service_admission.py",20),
        ):
            item=run_suite(label,["discover","-s","tests","-p",pattern,"-v"],
                           out/(label+".log"))
            ledger[label]=item
            if not item["complete_OK"] or item["test_footer"]!=[str(n)]:
                raise RuntimeError("P214 original selected Windows security suite failed "+label)
        ledger["p214_actual_native_C1_host"]=native_p214_integration(out)
        ledger["p215_actual_Windows_store_principal_to_C1_host"]=native_p215_integration(out)
        after=custody();ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P215 source identity changed during Windows execution")
        complete=True
        print("P215_REAL_WINDOWS_SELECTED_233_PLUS_PRINCIPAL_CAPABILITY_16=249_PASS",flush=True)
        print("P215_REAL_OS_IDENTITY_CREDGETSESSIONTYPES_TO_CUSTODY_SERVICE=EXECUTED",flush=True)
        print("P215_REAL_KEY=NO_GO|PRODUCTION=HOLD|FULL_PRODUCT_WINDOWS=0/3",flush=True)
    except BaseException as error:
        ledger["error"]=type(error).__name__+": "+str(error)
        print("P214_REAL_WINDOWS_HOLD="+type(error).__name__,flush=True)
    finally:
        ledger["P215_source_integrated_store_identity_negative_COMPLETE_NOT_release"]=complete
        (out/"p215_HCR_real_Windows_store_principal_source.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":
    raise SystemExit(main())
