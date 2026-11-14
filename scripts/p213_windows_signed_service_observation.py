"""P213 genuine Windows source-bound Authenticode read-only intake.

Compares actual Windows-signed OS reference and test-only unsigned C1
native candidate. Neither is trusted Nayeon service/UI publisher or installer.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
import subprocess
import sys

from scripts.p207_windows_native_consent_acceptance_prep import ROOT,git
from scripts.p206_windows_credential_effect_ownership import (
    PRIOR_BLOBS,run_suite,sha256,
)
from scripts.p208_windows_synthetic_terminal_owner import native as p208_native
from scripts.p209_windows_protected_synthetic_custody import p209_native
from scripts.p210_windows_python_native_synthetic_integration import (
    compile_native_bridge,
)
from nayeon.brain.p213_readonly_windows_signer_observer import (
    source_pins_unissued, observe_readonly_windows_signer,
    system_powershell_reference, P213SignatureStatus,
)
from nayeon.brain.p211_high_assurance_package_quarantine import (
    inspect_current_source_tree,
)

P212="e5d8f5f92a21d7314bf7ef6a7e9b2f9a95bc658f"
BRANCH="byok-c1-p213-readonly-windows-signed-service-admission-20261114"
ADDED={
 "nayeon/brain/p213_readonly_windows_signer_observer.py",
 "native_c1_candidate/P213NativeWintrustObservation.cs",
 "tests/test_p213_real_windows_authenticode_service_admission.py",
 "scripts/p213_windows_signed_service_observation.py",
 "docs/byok-c1-p213-windows-authenticode-service-admission.md",
 ".github/workflows/p213-windows-authenticode-service-admission.yml",
}
UNMODIFIED=(
 "nayeon/secrets/windows_credential.py",
 "nayeon/brain/local_byok_user_scope.py",
 "nayeon/desktop_alpha/local_byok_launch_bridge.py",
 "nayeon/desktop_alpha/local_byok_window.py",
 "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
 "native_c1_candidate/CustodyService.cs",
 "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs",
 "native_c1_candidate/P208SyntheticTerminalOwner.cs",
 "native_c1_candidate/P209SyntheticDurableCustody.cs",
 "native_c1_candidate/P210SyntheticBoundaryExecutable.cs",
 "nayeon/brain/p211_high_assurance_package_quarantine.py",
 "tests/test_p211_high_assurance_package_quarantine.py",
 "tests/test_p210_python_native_synthetic_integration.py",
 "scripts/p212_high_assurance_build_gate.py",
 "tests/test_p212_mandatory_high_assurance_build_gate.py",
 "nayeon/desktop_alpha/application.py",
)

def custody()->dict:
    if (sys.platform!="win32"
        or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH):
        raise RuntimeError("P213 genuine hosted Windows push event REQUIRED")
    head=git("rev-parse","HEAD")
    if (head!=os.environ.get("GITHUB_SHA")
        or git("merge-base",P212,"HEAD")!=P212):
        raise RuntimeError("P213 exact Git event/P212 parent mismatch")
    if set(git("diff","--name-only",P212,"HEAD").splitlines())!=ADDED:
        raise RuntimeError("P213 original product/security source changed")
    if git("status","--porcelain=v1","-uall"):
        raise RuntimeError("P213 Git checkout not clean")
    pins={}
    for path,sha in sorted(PRIOR_BLOBS.items()):
        if (git("rev-parse","HEAD:"+path)!=sha
            or git("rev-parse",P212+":"+path)!=sha):
            raise RuntimeError("P213 original P205 blob changed "+path)
        pins[path]={"git_blob":sha,"disk_SHA256":sha256((ROOT/path).read_bytes())}
    for path in UNMODIFIED:
        if git("rev-parse","HEAD:"+path)!=git("rev-parse",P212+":"+path):
            raise RuntimeError("P213 original named source changed "+path)
    return {"event_HEAD":head,"exact_P212_ancestor":P212,
            "six_additive_paths":sorted(ADDED),
            "original_source_pins":pins}

def compile_native_wintrust_probe(out:Path)->dict:
    """Build a genuine read-only native WinVerifyTrust helper from P116
    source, with no service Main, credentials, signer or network calls."""
    csc=Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
    if sys.platform!="win32" or not csc.is_file():
        raise RuntimeError("P213 genuine Windows x64 compiler unavailable")
    p49=ROOT/"tests/p99_original_native_c1_denial"
    c1=ROOT/"native_c1_candidate"
    peer=ROOT/"native_c1_g1_peer_review"
    originals=[p49/p for p in (
        "ServiceGate.cs","ProtectedAcl.cs","CustodyLedger.cs")]
    candidates=[c1/p for p in (
        "CustodyService.cs","ServiceOwnedAdmissionBoundary.cs",
        "ServiceBoundRequestIdentity.cs",
        "NativeJ2ProtectedReadOnlyPreflight.cs",
        "CandidateCredentialEffectHold.cs",
        "IsolatedCandidateContracts.cs",
        "CandidateProtectedReadOnlySnapshot.cs")]
    peerfiles=[peer/p for p in (
        "WindowsPipePeerObservation.cs",
        "WindowsPipeClientProcessProvenance.cs",
        "WindowsPipeClientSessionIntegrity.cs",
        "WindowsWintrustFilePolicyReview.cs")]
    sources=originals+candidates+peerfiles+[
        c1/"P213NativeWintrustObservation.cs"]
    if len(sources)!=15 or any(not p.is_file() for p in sources):
        raise RuntimeError("P213 original native P116 source set invalid")
    for p in sources:
        if p.name=="P213NativeWintrustObservation.cs":
            continue  # this exact new test-only entrypoint has no P212 ancestor
        relative=str(p.relative_to(ROOT)).replace("\\","/")
        if git("rev-parse","HEAD:"+relative)!=git(
            "rev-parse",P212+":"+relative
        ):
            raise RuntimeError("P213 original native P116 source drift "+p.name)
    gate=(c1/"P213NativeWintrustObservation.cs").read_text("utf8")
    if ("#if C1_REVIEW_ISOLATED_ASSEMBLY" not in gate or
        any(x in gate for x in ("CredWriteW(","CredDeleteW(","ServiceBase.Run(",
                                "DllImport(","Set-Service","New-Service"))):
        raise RuntimeError("P213 test-only source/native boundary violated")
    exe=out/"p213_original_P116_native_WinTrust_readonly.exe"
    cmd=[str(csc),"/nologo","/target:exe","/platform:x64",
         "/define:C1_REVIEW_ISOLATED_ASSEMBLY",
         "/r:System.ServiceProcess.dll","/r:System.Core.dll",
         "/main:P213NativeWintrustObservation",
         "/out:"+str(exe)]+[str(p) for p in sources]
    c=subprocess.run(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        timeout=90,check=False)
    (out/"p213_original_P116_native_wintrust_compiler.log").write_bytes(c.stdout)
    if c.returncode!=0 or c.stdout.strip():
        raise RuntimeError("P213 original P116 native WinTrust CSharp compile failure")
    return {"exe":str(exe),"csc_OS_exit":c.returncode,
            "original_compiler_stdout_SHA256":sha256(c.stdout),
            "native_exe_SHA256":sha256(exe.read_bytes()),
            "real_Windows_WinTrust_source":"original P116 read-only",
            "local_service_or_credential_effects":"NONE"}


def main()->int:
    out=Path(os.environ.get("RUNNER_TEMP",str(ROOT)))/"nayeon-p213-evidence"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
       "checkpoint":"P213",
       "H":"HOLD_MICROSOFT_OS_SIGNATURE_NOT_NAYEON_SERVICE_TRUST_ROOT",
       "C":"REAL_WINDOWS_READONLY_AUTHENTICODE_SIGNED_VS_UNSIGNED_NATIVE_SOURCE",
       "R":"PRODUCTION_HOLD",
       "real_key_R0_R4":"NO_GO",
       "production_P0_P5":"HOLD",
       "independent_GOV_SEC_REL":"SEVEN_REVIEW_DECISIONS_OPEN",
       "G0_G6":"OPEN",
       "full_unfiltered_accepted_Windows_product_regressions":"0/3",
       "P132_real_source_Python_WinCred":"REACHABLE_UNGOVERNED",
       "signed_native_UI_service_antirollback":"NOT_APPROVED",
       "C2_provider_validation":"NOT_AUTHORISED",
    }
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        if not source_pins_unissued():
            raise RuntimeError("P213 unsigned service candidate must not be enrolled")
        risk=inspect_current_source_tree(ROOT)
        if not (risk.exact_legacy_source_readable
                and risk.high_assurance_legacy_risk_present
                and risk.frozen_companion_pins_absent
                and risk.native_c1_service_denial_only):
            raise RuntimeError("P213 original real P132/source hold witness differs")
        ledger["P212_product_build_denial_rechecked_by_unmodified_tests"]="YES_TESTED_NO_RELEASE"
        suites=[
         ("p132_original_36",["discover","-s","tests","-p","test_local_user_scope_byok.py","-v"],36),
         ("p206_original_12",["discover","-s","tests","-p","test_p206_unified_effect_ownership.py","-v"],12),
         ("p207_original_14",["discover","-s","tests","-p","test_p207_user_scope_native_consent_review.py","-v"],14),
         ("p49_native20_c1_native24",["-v",
          "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_02_original_full_P49_native_release_and_WinCred_denial_20_cases",
          "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_03_current_candidate_service_host_remains_denial_24_cases"],2),
        ]
        for label,args,n in suites:
            result=run_suite(label,args,out/(label+".log"))
            ledger[label]=result
            if not result["complete_OK"] or result["test_footer"]!=[str(n)]:
                raise RuntimeError("P213 prior Windows selected functional suite failed "+label)
        ledger["p208_original_native_20"]=p208_native(out)
        ledger["p209_real_DPAPI_native_18"]=p209_native(out)
        bridge=compile_native_bridge(out)
        ledger["p210_native_compiler"]=bridge
        os.environ["P210_NATIVE_EXE"]=bridge["path"]
        wintrust=compile_native_wintrust_probe(out)
        ledger["p213_native_P116_wintrust_compiler"]=wintrust
        os.environ["P213_NATIVE_WINTRUST_EXE"]=wintrust["exe"]
        reference=system_powershell_reference()
        if reference is None:
            raise RuntimeError("P213 real Windows signed reference unavailable")
        signed=observe_readonly_windows_signer(reference)
        unsigned=observe_readonly_windows_signer(Path(bridge["path"]))
        ledger["real_windows_authenticode_readonly"]={
            "Windows_OS_reference_status":signed.status.value,
            "Windows_OS_reference_file_SHA256":signed.file_sha256,
            "Windows_OS_reference_signer_cert_SHA256":signed.signer_cert_sha256,
            "unsigned_native_C1_candidate_status":unsigned.status.value,
            "unsigned_native_C1_candidate_SHA256":unsigned.file_sha256,
            "signed_binary_is_approved_Nayeon_publisher":False,
            "signed_service_image_load_trust":False,
            "approved_installer_or_code_integrity_policy":False,
            "real_key_or_production_admission":False,
        }
        if (signed.status is not P213SignatureStatus.OS_POLICY_ACCEPTED_UNPINNED
            or unsigned.status is not P213SignatureStatus.OS_POLICY_REJECTED
            or not signed.stable_stat_and_bytes_observed
            or not unsigned.stable_stat_and_bytes_observed):
            raise RuntimeError("P213 actual Windows Authenticode read-only mismatch")
        for label,file,count in (
          ("p210_python_native_13","test_p210_python_native_synthetic_integration.py",13),
          ("p211_package_refusal_22","test_p211_high_assurance_package_quarantine.py",22),
          ("p212_build_gate_20","test_p212_mandatory_high_assurance_build_gate.py",20),
          ("p213_authenticode_live20","test_p213_real_windows_authenticode_service_admission.py",20),
        ):
            result=run_suite(label,["discover","-s","tests","-p",file,"-v"],
                             out/(label+".log"))
            ledger[label]=result
            if not result["complete_OK"] or result["test_footer"]!=[str(count)]:
                raise RuntimeError("P213 original Windows selected suite failed "+label)
        after=custody();ledger["source_after"]=after
        if before!=after:
            raise RuntimeError("P213 source custody changed after actual Windows tests")
        complete=True
        print("P213_WINDOWS_ORIGINAL_199_NATIVE_SIGNATURE_20=219_SELECTED_PASS",flush=True)
        print("P213_ACTUAL_NATIVE_P116_WINVERIFYTRUST_SIGNED_REFERENCE_AND_UNSIGNED_C1=READ_ONLY",flush=True)
        print("P213_SIGNED_SERVICE_TRUST_ROOT=NOT_ENROLLED",flush=True)
        print("P213_REAL_KEY=NO_GO|PRODUCTION=HOLD|FULL_WINDOWS=0/3",flush=True)
    except BaseException as error:
        ledger["error"]=type(error).__name__+": "+str(error)
        print("P213_GENUINE_WINDOWS_FAILURE_HOLD="+type(error).__name__,flush=True)
    finally:
        ledger["isolated_P213_readonly_signature_observation_complete_NOT_release"]=complete
        (out/"p213_HCR_original_Windows_signature_and_source_ledger.json").write_text(
          json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1


if __name__=="__main__":
    raise SystemExit(main())
