"""Bounded source checks only. Never compiles, loads or starts a native service."""
import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "native_c1_successor/P264DevelopmentCustodyService.cs"
DRIVER = "tests/p264_successor/P264DevelopmentServiceTests.cs"
GATE = "tests/p99_original_native_c1_denial/ServiceGate.cs"
# Raw checkout bytes: historical originals are witnesses, never new eligibility.
FROZEN = {
    GATE: "F65EF9F04283B6CA82D42B8D61B6B99B23262DE62E248DC575C0CEF1B3D96B8D",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs": "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
    "tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs": "2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F",
    "tests/p99_original_native_c1_denial/PendingWinCredStore.cs": "4051A48F3062A737D0D9CE212DB9B302C2C22D5ECA2893CE27B35C740A72B93C",
    "tests/p99_original_native_c1_denial/CustodyService.cs": "49217E9018AB2437D3F2B4B2907C08946432352618EDEE065F734D88B93EC093",
    "tests/phase8_byok_c1_p76_scope.py": "1C42912D9FC550DEA56C9BA9BB70D9568F298223B5514AF8D03C1723AAAD3327",
    "tests/test_phase8_byok_c1_p76_scope.py": "EE6BB4CECC5D8A388623B635B8172CA7C526D87F284FEB6B09A5E3E74F651E2D",
    "tests/test_byok_c1_p251_effect_exposure_gate.py": "E943659EEBECC8CC9C84F74E711B243FC1E44024AE9E442AE08FBB169CE873AA",
    "tests/test_byok_c1_p258_legacy_effect_containment.py": "F1857D04BE9013371D54A1BBFBB0FA06B14C2B19CD60ACB521A8D99BA607B75C",
    "tests/test_byok_c1_p261_scm_readonly.py": "935A28276002C95757DE41AF5B03D0F0F9BDC6DD6C350F3A166DFBB9B7E55F09",
    "native_c1_candidate/P261ScmReadOnlyAdmission.cs": "FBBC4AAF4B65D6C4B49DD0EE8B99C391A2E4AC08E1E6454CD10AF26C68804193",
    "nayeon/brain/local_byok_user_scope.py": "24B8457F219F02D3EA47FE59DF2F1E860F01DB3BB6A83531307DA0656759FFE4",
    "nayeon/desktop_alpha/local_byok_window.py": "55EA8B1C9EAF4179725127B36B0A7B0D7342ADCD860FEDC854C330A7926346BA",
    "nayeon/secrets/windows_credential.py": "135810E12A15322A6013694084CD83CB9CA05C5CFEAA63A6D43405B6DA6AFA4D",
    ".codex/CURRENT_STATE.md": "5775C68F8D0428004DE85C9A2695FD7D06EA8BB98D3E8DBBFDF2FE647E8373A1",
    "AGENTS.md": "B39192BEEA574578A9F1822AAD24216838FC1D55B503CA1F7CE1A6B06A4884FB",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def compact(text):
    return re.sub(r"\s+", "", re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S))


def check_service(text, gate):
    require(text.startswith("#if !C1_P264_DEVELOPMENT_ONLY\n"
                            "#error P264_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED\n#endif\n"
                            "#if !DEBUG\n#error P264_NO_RELEASE_BUILD\n#endif\n"),
            "explicit development and non-release compile guards required")
    require(re.findall(r"^using ([^;]+);", text, re.M) ==
            ["System", "System.ServiceProcess", "System.Threading"], "bounded dependencies")
    # Projection avoids linking any obsolete gate/ACL implementation into the EXE.
    frozen_name = re.search(r'const string ServiceName = "([^"]+)";', gate)
    projected_name = re.search(r'const string FrozenServiceName = "([^"]+)";', text)
    require(frozen_name is not None and projected_name is not None and
            frozen_name[1] == projected_name[1] == "NayeonV1ByokCustody", "frozen name linkage")
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)
    require(not re.search(
        r"\b(?:DllImport|LibraryImport|extern|unsafe|dynamic|delegate|interface|Action|Func|"
        r"ServiceGate|ProtectedAcl|LiveEligible|EligibleForService|LocalSystem|WindowsIdentity|"
        r"ServiceController|ServiceInstaller|Process|Assembly|Activator|Type|Environment|"
        r"File|Directory|Registry|NamedPipe\w*|Tcp\w*|Socket|Http\w*|Web\w*|"
        r"Cred(?:Read|Write|Delete|Enumerate|Free|GetSessionTypes|Protect|Unprotect|IsProtected|Pack|UnPack|Marshal|Unmarshal|FindBest|Rename|UI)\w*|"
        r"CreateService\w*|OpenSCManager\w*|OpenService\w*|StartService\w*|"
        r"ControlService\w*|DeleteService\w*|Impersonate\w*|GetProcAddress|LoadLibrary\w*)\b",
        code), "native APIs, old gate, dynamic loading and effects excluded")
    body = compact(text)
    for token in (
        "sealedclassDevelopmentCustodyService:ServiceBase", "ServiceName=FrozenServiceName;",
        "CanStop=true;CanShutdown=true;CanPauseAndContinue=false;AutoLog=false;",
        "privatereadonlyCustodyOwnerowner=newCustodyOwner();",
        "privatesealedclassCustodyOwner", "privatereadonlyobjectsync=newobject();",
        "if(Monitor.IsEntered(sync)){faulted=true;returnView(Refusal.Reentrant);}lock(sync)",
        "if(!started&&!stopped&&!revoked&&!faulted&&!disposed)started=true;elsefaulted=true;",
        "caseCommand.Stop:stopped=true;break;", "caseCommand.Revoke:revoked=true;break;",
        "caseCommand.Fault:faulted=true;break;",
        "caseCommand.Dispose:stopped=true;disposed=true;break;",
        "caseCommand.RejectCredential:caseCommand.RejectIpc:caseCommand.RejectStore:caseCommand.Observe:break;",
        "protectedoverridevoidOnStop(){owner.Apply(Command.Stop);}",
        "protectedoverridevoidOnShutdown(){owner.Apply(Command.Stop);}",
        "protectedoverridevoidDispose(booldisposing){owner.Apply(Command.Dispose);base.Dispose(disposing);}",
        "Denialresult=owner.Apply(Command.Start);if(result.State!=Lifecycle.RunningDenied)",
        'thrownewInvalidOperationException("P264_START_REFUSED");',
        "Lifecycle state = disposed ? Lifecycle.Disposed : faulted ? Lifecycle.Faulted :".replace(" ", ""),
        "privatestaticintMain(string[]arguments)",
        'if(arguments==null||arguments.Length!=1||!String.Equals(arguments[0],"--development-only-no-effects",StringComparison.Ordinal))return64;',
        "using(varservice=newDevelopmentCustodyService())",
        "try{ServiceBase.Run(service);}catch{service.Fault();throw;}",
    ):
        require(token in body, "missing fail-closed boundary: " + token)
    for name in ("CredentialAllowed", "IpcAllowed", "StoreAllowed", "ProductionEligible"):
        require("bool" + name + "{get{returnfalse;}}" in body, "unconditional denial " + name)
    for name, command in (("Revoke", "Revoke"), ("Fault", "Fault"),
                          ("RejectCredential", "RejectCredential"), ("RejectIpc", "RejectIpc"),
                          ("RejectStore", "RejectStore"), ("ObserveDenial", "Observe")):
        require("internalDenial" + name + "(){returnowner.Apply(Command." + command + ");}" in body,
                "private-owner fixed ingress " + name)
    require(body.count("ServiceBase.Run(") == 1, "single actual SCM entrypoint")
    require(not re.search(r"(?:started|stopped|revoked|faulted|disposed)=false;", body),
            "terminal state must never reset")


def check_driver(text):
    body = compact(text)
    require("ServiceBase.Run(" not in body, "harness must never start SCM dispatcher")
    for token in (
        "MethodInfoentry=candidate.EntryPoint;", 'entry.Name=="Main"', "entry.ReturnType==typeof(int)",
        "entry.Invoke(null,newobject[]{arguments})==64", "MethodAttributes.PinvokeImpl",
        "method.GetMethodImplementationFlags()", "MethodImplAttributes.InternalCall", "Need(body!=null);",
        "typeof(DllImportAttribute)", "Need(code!=OpCodes.Calli);", "candidate.GetReferencedAssemblies()",
        "candidate.ManifestModule.ResolveMethod", 'if(called.Name=="Run"){Need(method==entry);runCalls++;}',
        "Need(runCalls==1);", "LifecycleTests();", "ReentrantTests();",
        'new[]{"OnStop","Revoke","Fault","Dispose"}',
        'new[]{"RejectCredential","RejectIpc","RejectStore"}', "new[]{true,false}",
        "OrderedPair(terminals[index],reasons[index],admission,first);",
        'lock(sync){Denied(Call(service,"Revoke"),"Reentrant");}',
        'Need(!Flag(receipt,"RevokeRecorded")&&Flag(receipt,"FaultRecorded"));',
        "firstDone.WaitOne(3000)", "first.Join(5000)", "second.Join(5000)",
        "firstError==null&&secondError==null", "firstDone.Set();", "Close(service);",
        "ContendedLifecycleTests();", "Need(!finished.WaitOne(100));", "Need(worker.Join(3000)&&failure==null);",
        "P264_REAL_KEY=HOLDPRODUCTION=HOLDSCM_EXECUTION=NOT_TESTED",
    ):
        require(token in body, "missing native negative evidence: " + token)
    require(body.index("Need(runCalls==1);") < body.index("entry.Invoke("),
            "audit candidate code before invoking it")


class P264DevelopmentServiceSourceTests(unittest.TestCase):
    def test_frozen_raw_bytes(self):
        for path, expected in FROZEN.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), expected)

    def test_executable_denial_and_name_contract(self):
        check_service((ROOT / SOURCE).read_text(encoding="utf-8"),
                      (ROOT / GATE).read_text(encoding="utf-8"))

    def test_native_driver_contract(self):
        check_driver((ROOT / DRIVER).read_text(encoding="utf-8"))

    def test_service_negative_mutations(self):
        source = (ROOT / SOURCE).read_text(encoding="utf-8")
        gate = (ROOT / GATE).read_text(encoding="utf-8")
        for before, after in (
            ("#error P264_NO_RELEASE_BUILD", ""),
            ("#error P264_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED", ""),
            ('FrozenServiceName = "NayeonV1ByokCustody"', 'FrozenServiceName = "NayeonByokCustody"'),
            ("ServiceBase.Run(service);", ""),
            ("arguments.Length != 1", "false"),
            ("owner.Apply(Command.Stop);", "owner.Apply(Command.Observe);"),
            ("Monitor.IsEntered(sync)", "false"),
            ("stopped = true;", "stopped = false;"),
            ("faulted = true;", "faulted = false;"),
            ("bool CredentialAllowed { get { return false; } }", "bool CredentialAllowed { get { return true; } }"),
            ("return 64;", "return 0;"),
            ("ServiceName = FrozenServiceName;", "ServiceName = FrozenServiceName; ServiceGate.LiveEligible();"),
            ("ServiceName = FrozenServiceName;", "ServiceName = FrozenServiceName; CredWriteW();"),
            ("ServiceName = FrozenServiceName;", "ServiceName = FrozenServiceName; NamedPipeServerStream();"),
        ):
            with self.subTest(before=before):
                self.assertIn(before, source)
                with self.assertRaises(AssertionError):
                    check_service(source.replace(before, after), gate)

    def test_driver_negative_mutations(self):
        source = (ROOT / DRIVER).read_text(encoding="utf-8")
        for before, after in (
            ("Need(runCalls == 1);", ""),
            ("MethodAttributes.PinvokeImpl", "MethodAttributes.Public"),
            ("Need(code != OpCodes.Calli);", ""),
            ("new[] { true, false }", "new[] { true }"),
            ("entry.ReturnType == typeof(int)", "true"),
            ("ReentrantTests();", ""),
            ("ContendedLifecycleTests();", ""),
            ("firstError == null && secondError == null", "true"),
        ):
            with self.subTest(before=before):
                self.assertIn(before, source)
                with self.assertRaises(AssertionError):
                    check_driver(source.replace(before, after))


if __name__ == "__main__":
    unittest.main()
