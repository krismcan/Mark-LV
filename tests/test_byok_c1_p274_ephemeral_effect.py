"""P274 source-only contracts. No native loading, subprocess launch or credential access."""
import ast
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = "native_c1_successor/P274EphemeralWinCredEffect.cs"
DRIVER = "tests/p274_successor/P274EphemeralWinCredEffectTests.cs"
WORKFLOW = ".github/workflows/p274-windows-ephemeral-real-effect.yml"
FROZEN = {
    "tests/p95_native_custody_preflight/CustodyLedger.cs": "93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs": "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
    "tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs": "2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F",
    "native_c1_successor/P268ServiceOwnedPendingTransaction.cs": "964AF496E72C5510823809E4EBB74E045D2F01E7F0A9FABE7DBAE4625B172CFC",
    "tests/p268_successor/P268RemediationTests.cs": "B2C91CA2D203A5825F65ED969BB4DD5D22CEFA6B2A9717A456404D4112A29C14",
    "tests/test_p134_real_wincred_ephemeral.py": "1E4E2F176B98824659246AB57AC7DAB76ECA4D501C93AFC6C07FC981171884C2",
    "docs/byok-c1-p216-service-owned-store-r3-external-decision.md": "897C98B85F5EF2CB40D9FCCDC0D0D6FCB727D941CCFD597036E81391B68EAA85",
    ".github/workflows/p273-p76-current-admission.yml": "0AEC883209771BF7DF3213145CC35CAF2C13952B1DBB055AE873D085E1DC78DC",
    "scripts/p273_p76_current_admission.py": "472684DF6A035C231980D006EE2E954384C0739401BB7A3213868A124251DEEE",
    "tests/test_p273_p76_current_admission.py": "C4E3AA4F5539DCA6758CAA8E0F9E79C27BAB65346983EBD2AA7E577D85C409B1",
}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def compact(text):
    return re.sub(r"\s+", "", re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S))


def require(value):
    if not value:
        raise AssertionError("P274 source boundary")


def check_helper(text):
    body = compact(text)
    for flag, marker in (("DEBUG", "P274_NO_RELEASE_BUILD"),
                         ("C1_P268_DEVELOPMENT_ONLY", "P274_REQUIRES_P268_DEVELOPMENT_ONLY"),
                         ("C1_P274_EPHEMERAL_WINCRED_ONLY", "P274_EPHEMERAL_OPT_IN_REQUIRED")):
        require(f"#if!{flag}#error{marker}#endif" in body)
    for witness in (
        'privateconststringPrefix="Nayeon.P274.Disposable.";',
        'privatereadonlystringtarget;',
        'RequireHosted();Require(Marshal.SizeOf(typeof(CREDENTIALW))==(IntPtr.Size==8?80:52));target=Prefix+Guid.NewGuid().ToString("N");',
        'Require(!ReadOwned());owned=true;',
        'Require(owned&&!disposed);RequireHosted();',
        'Require(windows&&!localSystem&&env!=null);',
        'Env(env,"RUNNER_ENVIRONMENT")=="github-hosted"',
        'Env(env,"GITHUB_EVENT_NAME")=="pull_request"',
        'Env(env,"P274_NATIVE_AUTH")=="DISPOSABLE_HOSTED_SYNTHETIC_ONLY"',
        'Env(env,"P274_BASE_SHA")==BaseSha',
        'Env(env,"GITHUB_HEAD_REF")==HeadBranch',
        'Env(env,"GITHUB_BASE_REF")==BaseBranch',
        'Require(Object.Equals(Field(pr,"draft"),true));',
        'Field(Map(Field(endpoint,"repo")),"full_name")==Repo',
        'Field(endpoint,"sha")==',
        'MaxJsonLength=262144,RecursionLimit=32',
        'Require(stream.Length>0&&stream.Length<=262144);',
        'char[]buffer=newchar[262145];',
        'path.StartsWith(temp.TrimEnd',
        'FileAttributes.ReparsePoint',
        'identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid)',
        'privateconststringRepo="krismcan/Mark-LV";',
        '9546228e5c726a46a3bf91ba05793f38c23d686f',
        'byok-c1-p274-real-os-effect-gate-20261118',
        'byok-c1-p273-current-p76-admission-20261118',
        'if(!found){Require(error==1168&&buffer==IntPtr.Zero);returnfalse;}',
        'value.Type==1&&value.TargetName==target&&value.UserName==target&&value.Persist==1&&value.CredentialBlobSize==4',
        'finally{if(buffer!=IntPtr.Zero)CredFree(buffer);}',
        'bytes.Length==4&&bytes[0]==0x31&&bytes[1]==0x32&&bytes[2]==0x33&&bytes[3]==0x34',
        'if(op==LedgerOperation.Delete)returnbytes==null;',
        'Require(CredWriteW(refvalue,0));',
        'Require(!seeded&&!submitted&&(op==LedgerOperation.Replace||op==LedgerOperation.Delete));',
        'Require(!ReadOwned());seeded=true;',
        'CheckOwner();Require(ValidCandidate(op,candidate)&&!submitted);',
        'Require(ReadOwned()==(op!=LedgerOperation.Save));submitted=true;TerminalCalls++;',
        'if(op==LedgerOperation.Delete)Require(CredDeleteW(target,1,0));elseWriteSynthetic();',
        'Require(ReadOwned()==(op!=LedgerOperation.Delete));',
        'try{if(ReadOwned())Require(CredDeleteW(target,1,0));}finally{Require(!ReadOwned());}',
        'finally{disposed=true;owned=false;}',
    ):
        require(witness in body)
    externs = re.findall(r"private\s+static\s+extern\s+\w+\s+(\w+)\(", text)
    require(externs == ["CredWriteW", "CredReadW", "CredDeleteW", "CredFree"])
    require(text.count('[DllImport("advapi32.dll"') == 4)
    require(body.count("CredReadW(target,1,0,outbuffer)") == 1)
    require(body.count("CredDeleteW(target,1,0)") == 2)
    require(body.count("CredWriteW(refvalue,0)") == 1)
    require("publicP274EphemeralWinCredEffect" not in body)
    require("P274EphemeralWinCredEffect()" in body)
    require(not re.search(r"CredEnumerate|ServiceBase|Process\.Start|DllImport\(\"(?:kernel|user)|HttpClient|WebRequest|ProductionEligible", body))


def check_driver(text):
    body = compact(text)
    for flag, marker in (("DEBUG", "P274_TESTS_NO_RELEASE_BUILD"),
                         ("C1_P268_DEVELOPMENT_ONLY", "P274_TESTS_REQUIRE_P268_DEVELOPMENT_ONLY"),
                         ("C1_P274_EPHEMERAL_WINCRED_ONLY", "P274_TESTS_EPHEMERAL_OPT_IN_REQUIRED")):
        require(f"#if!{flag}#error{marker}#endif" in body)
    for witness in (
        'newP96StateFixture(Approval)', 'newP96GuardFixture(Approval)',
        'newDevelopmentPendingState(State)',
        'ServiceOwnedPendingTransaction.DevelopmentOnlyHost(Adapter,Guard,true)',
        'f.Adapter.Inject=point=>', 'if(point!="effect-enter")return;',
        'f.AssertEntry();entered.Set();', 'Demand(release.WaitOne(2500)',
        'effect.Execute(op,op==LedgerOperation.Delete?null:P96Fixture.Dummy());',
        'Monitor.IsEntered(gate)&&latched', 'GetField("mayHaveEffect",flags).GetValue(Service)',
        'CustodyLedger.Verify(State.Journal,State.Anchor)==LedgerPhase.InFlight',
        'Adapter.JournalWrites==1&&Adapter.AnchorWrites==1',
        'Volatile.Write(refnativeFinished,1);',
        'if(throwAfterNative)thrownewInvalidOperationException("P274_UNCERTAIN_AFTER_NATIVE_SUCCESS");',
        'Demand(!completed.WaitOne(25)', 'control==ControlResult.TooLate',
        'f.Service.MayHaveEffect&&f.Service.RecoveryRequired',
        'outcome==CustodyOutcome.RecoveryRequired', 'f.NoReplay(effect);',
        'effect.TerminalCalls==0&&f.State.PossibleEffects==0',
        'effect.TerminalCalls==native&&State.PossibleEffects==fake',
        'thread.Join(3000)', 'finally{release.Set();try{Join(writer);}finally{Join(closer);}}',
        'P274EphemeralWinCredEffect.RequireHosted();', 'Demand(args.Length==0',
        'ControlFirst(selected,control)', 'EffectFirst(selected,control,false)', 'EffectFirst(selected,control,true)',
        'HostNegatives', 'CandidateNegatives', 'BindingNegatives',
    ):
        require(witness in body)
    require(body.count("effect.Execute(") == 5)
    require(not re.search(r"newPendingCustodyTransaction|ActualCoordinator|DllImport|SetValue\(", body))
    require("LedgerOperation.Save,LedgerOperation.Replace,LedgerOperation.Delete" in body)


def check_workflow(text):
    for witness in (
        "pull_request:", "pull_request.draft == true", "runs-on: windows-2022",
        "branches: [byok-c1-p273-current-p76-admission-20261118]",
        "9546228e5c726a46a3bf91ba05793f38c23d686f", "byok-c1-p274-real-os-effect-gate-20261118",
        "github.event.pull_request.head.repo.full_name == github.repository",
        "github.event.pull_request.base.repo.full_name == github.repository",
        "git rev-parse 'HEAD^'", "changes.Count -ne 5", "^A\\t", "^100644 blob",
        "RUNNER_ENVIRONMENT -cne 'github-hosted'", "LocalSystemSid", "$eventFile.Length -gt 262144",
        "$event.pull_request.draft -ne $true", "source-hashes.json", "Get-FileHash",
        "arch: x64", "arch: x86", "framework: Framework64", "framework: Framework",
        "'/noconfig'", "'/warnaserror+'", "'/debug+'", "'/optimize-'",
        "C1_P274_EPHEMERAL_WINCRED_ONLY", "foreach ($missing in @('ALL') + $flags)",
        "error CS1029:", "P274_TESTS_EPHEMERAL_OPT_IN_REQUIRED", "P96NegativeProof",
        "P268RemediationTests", "P274EphemeralWinCredEffectTests", "$info.EnvironmentVariables.Clear()",
        "$info.CreateNoWindow = $true", "WaitForExit(60000)", "$process.Kill()", "STOP no retry",
        "P96_NATIVE_ACTUAL_COORDINATOR_TESTS_PASSED=15", "P96_SECURITY_FINDING=OPEN",
        "P268_SUCCESSOR=PASS CASES=33", "P274_EPHEMERAL=PASS CASES=30", "$initial.Count -ne 32",
        "$cleanup.Count -ne 32", "*.log", "*.exit", "*.json", "evidence-sha256.log",
    ):
        require(witness in text)
    for action in ("actions/checkout", "actions/setup-python", "actions/upload-artifact"):
        require(re.search(re.escape(action) + r"@[0-9a-f]{40}\b", text))
    require("pull_request_target" not in text and "*.exe" not in text and "secrets." not in text)


class P274SourceTests(unittest.TestCase):
    def test_frozen_sha_and_p268_source_binding(self):
        for path, digest in FROZEN.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), digest, path)
        body = compact(read("native_c1_successor/P268ServiceOwnedPendingTransaction.cs"))
        self.assertIn('Barrier();mayHaveEffect=true;if(op==LedgerOperation.Delete)state.DeletePending();elsestate.SaveOrReplace(owned);Barrier();', body)
        self.assertIn('SaveCalls++;Probe("effect-enter");fixture.SaveOrReplace(value);Probe("effect-return");', body)
        self.assertIn('DeleteCalls++;Probe("effect-enter");fixture.DeletePending();Probe("effect-return");', body)

    def test_helper_contract(self):
        check_helper(read(HELPER))

    def test_actual_callback_driver(self):
        check_driver(read(DRIVER))

    def test_hosted_workflow_contract(self):
        check_workflow(read(WORKFLOW))

    def test_helper_causal_mutations_rejected(self):
        source = read(HELPER)
        mutations = (
            ("#if !DEBUG", "#if false"),
            ("#if !C1_P268_DEVELOPMENT_ONLY", "#if false"),
            ("#if !C1_P274_EPHEMERAL_WINCRED_ONLY", "#if false"),
            ('Guid.NewGuid().ToString("N")', '"fixed"'),
            ("Require(!ReadOwned()); owned = true;", "owned = true;"),
            ('Env(env, "RUNNER_ENVIRONMENT") == "github-hosted"', "true"),
            ("Require(Object.Equals(Field(pr, \"draft\"), true));", ";"),
            ("!localSystem", "true"),
            ("stream.Length <= 262144", "true"),
            ("bytes[3] == 0x34", "true"),
            ("&& !submitted", ""),
            ("if (buffer != IntPtr.Zero) CredFree(buffer);", ";"),
            ("finally { Require(!ReadOwned()); }", "finally { }"),
            ("Require(CredWriteW(ref value, 0));", "Require(CredWriteW(ref value, 0)); Require(CredWriteW(ref value, 0));"),
        )
        for old, new in mutations:
            self.assertIn(old, source)
            with self.subTest(old=old), self.assertRaises(AssertionError):
                check_helper(source.replace(old, new, 1))

    def test_driver_causal_mutations_rejected(self):
        source = read(DRIVER)
        for old, new in (
            ("#if !DEBUG", "#if false"),
            ("#if !C1_P268_DEVELOPMENT_ONLY", "#if false"),
            ("#if !C1_P274_EPHEMERAL_WINCRED_ONLY", "#if false"),
            ('if (point != "effect-enter") return;', 'if (point != "effect-return") return;'),
            ("f.AssertEntry(); entered.Set();", "entered.Set();"),
            ("Monitor.IsEntered(gate) && latched", "true"),
            ("if (throwAfterNative) throw", "if (false) throw"),
            ("f.NoReplay(effect);", ";"),
            ("control == ControlResult.TooLate", "true"),
            ("P274EphemeralWinCredEffect.RequireHosted();", ";"),
        ):
            self.assertIn(old, source)
            # Remove every copy when the assertion is intentionally shared by cases.
            with self.subTest(old=old), self.assertRaises(AssertionError):
                check_driver(source.replace(old, new))

    def test_workflow_mutations_rejected(self):
        source = read(WORKFLOW)
        for old, new in (("pull_request.draft == true", "true"),
                         ("runs-on: windows-2022", "runs-on: self-hosted"),
                         ("changes.Count -ne 5", "changes.Count -ne 6"),
                         ("$info.EnvironmentVariables.Clear()", "# omitted"),
                         ("WaitForExit(60000)", "WaitForExit()"),
                         ("*.log", "*.exe")):
            self.assertIn(old, source)
            with self.subTest(old=old), self.assertRaises(AssertionError):
                check_workflow(source.replace(old, new))

    def test_python_syntax_and_syntax_negative_without_execution(self):
        source = Path(__file__).read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=__file__)
        compile(tree, __file__, "exec")
        with self.assertRaises(SyntaxError):
            compile(source + "\ndef broken(:\n", "p274-syntax-negative", "exec")
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        imports.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
        self.assertEqual(imports, {"ast", "hashlib", "re", "unittest", "pathlib"})


if __name__ == "__main__":
    unittest.main()
