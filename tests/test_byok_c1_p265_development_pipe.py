"""Source-only negative checks. No native loading, subprocess, credentials or imports of Nayeon."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native_c1_successor/P265DevelopmentPipeAdapter.cs"
DRIVER = ROOT / "tests/p265_successor/P265DevelopmentPipeTests.cs"
FROZEN = {
    "native_c1_successor/P264DevelopmentCustodyService.cs": "698600E040C24A8E3A1502C6E417E7CA75522EEC86E90FC88B58C8C6A9A31997",
    "tests/p264_successor/P264DevelopmentServiceTests.cs": "BFEE6D3C1DABD7BF28E84C9EBF1708477E957460CBE781AF0525E84BB00D0BEC",
    "tests/test_byok_c1_p264_development_service.py": "B90903D9C631354A6F05EC7AEFD6885F0FD1FE3E1EC5CD107FBCD26187B96747",
    "docs/byok-c1-p264-development-service.md": "0649BB5BC87E8F2A5FF0825DD04E248A8F8B04C774B784E249992F5BD9C18794",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs": "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
    "tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs": "2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F",
    "tests/p99_original_native_c1_denial/PendingWinCredStore.cs": "4051A48F3062A737D0D9CE212DB9B302C2C22D5ECA2893CE27B35C740A72B93C",
    ".codex/CURRENT_STATE.md": "5775C68F8D0428004DE85C9A2695FD7D06EA8BB98D3E8DBBFDF2FE647E8373A1",
}


def compact(text):
    return re.sub(r"\s+", "", re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_adapter(text):
    require(text.startswith("#if !C1_P265_DEVELOPMENT_ONLY\n"
                            "#error P265_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED\n#endif\n"
                            "#if !DEBUG\n#error P265_NO_RELEASE_BUILD\n#endif\n"), "development guards")
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)
    body = compact(text)
    require("CreateNewInstance" not in code, "no client server-instance authority")
    # This is an adapter library only. The native driver also audits every compiled call target.
    require(not re.search(r"\b(?:DllImport|LibraryImport|extern|unsafe|dynamic|ServiceBase|ServiceController|"
                          r"DevelopmentCustodyService|CustodyOwner|ServiceGate|PendingWinCredStore|"
                          r"Cred\w*W|WinCred|File|Directory|Process|Activator|Assembly|Marshal|"
                          r"HttpClient|WebClient|Socket|TcpClient|Registry|Delegate)\b", code), "effect graph isolation")
    require("P264" not in body and "Main(" not in body, "no service integration or entrypoint")
    require("WaitForPipeDrain(" not in body and "Thread.Sleep(" not in body, "no blocking drain/sleep")
    require("Encoding" not in body and "ReadLine(" not in body and "GetString(" not in body, "no identity/text payload")
    for flag in ("CredentialAllowed", "StoreAllowed", "PrivilegedAllowed", "ProductionEligible"):
        require("bool" + flag + "{get{returnfalse;}}" in body, "fixed denial " + flag)
    for witness in (
        "BodyLength=24,FrameLength=28,ReplyLength=8,ReplayCapacity=128;",
        "MinimumTimeoutMs=50,MaximumTimeoutMs=2000;",
        "DevelopmentPipeAdapter(WindowsIdentitytrustedExpected)",
        "!SameSid(trustedExpected.User,current.User)", "expectedSid=trustedExpected.User;",
        'Endpoint="Nayeon-P265-dev-"+Guid.NewGuid().ToString("N");',
        "security.SetAccessRuleProtection(true,false);", "security.SetOwner(expectedSid);",
        "WellKnownSidType.NetworkSid,null),PipeAccessRights.FullControl,AccessControlType.Deny)",
        "newPipeAccessRule(expectedSid,PipeAccessRights.ReadWrite,AccessControlType.Allow)",
        "newNamedPipeServerStream(Endpoint,PipeDirection.InOut,1,PipeTransmissionMode.Message,PipeOptions.Asynchronous,FrameLength,ReplyLength,security,HandleInheritability.None,(PipeAccessRights)0)",
        "observed!=null&&expected!=null&&observed.Equals(expected)",
        "WindowsIdentity.GetCurrent(true)", "if(thread!=null)thrownewSecurityException(",
        "if(remaining<=0)thrownewTimeoutException();", "handle.WaitOne(Remaining(elapsed,timeoutMs))",
        "Dispose();thrownewTimeoutException();", "pipe.BeginRead(", "pipe.EndRead(read)",
        "if(count==0)thrownewEndOfStreamException();",
        "header[0]!=BodyLength||header[1]!=0||header[2]!=0||header[3]!=0",
        "byte[]body=newbyte[BodyLength];", "!pipe.IsMessageComplete", "body[4]!=1||body[6]!=0||body[7]!=0",
        "switch((DenialOperation)body[5])", "default:returnfalse;", "returnrequestId!=Guid.Empty;",
        "Interlocked.CompareExchange(refserving,1,0)!=0", "DenialReason.Busy",
        "Interlocked.CompareExchange(refclosed,0,0)!=0", "DenialReason.Closed",
        "timeoutMs<MinimumTimeoutMs||timeoutMs>MaximumTimeoutMs", "Stopwatch.StartNew()",
        "pipe.BeginWaitForConnection(null,null)", "pipe.EndWaitForConnection(connect)",
        "pipe.RunAsClient(delegate{using(WindowsIdentitypeer=WindowsIdentity.GetCurrent(true))",
        "peer!=null&&peer.User!=null&&!peer.IsAnonymous&&peer.ImpersonationLevel==TokenImpersonationLevel.Impersonation",
        "matched=observed&&SameSid(peer.User,expectedSid);", "finally{RequireNoThreadIdentity();restored=true;}",
        "consumed.Contains(requestId)", "consumed.Count>=ReplayCapacity", "consumed.Add(requestId);",
        "reason=matched?DenialReason.DevelopmentHold:DenialReason.PeerRejected;",
        "byte[]denial=newbyte[]{67,49,68,78,1,1,0,0};", "pipe.EndWrite(write);",
        "byte[]delivery=newbyte[1];ReadExact(delivery,elapsed,timeoutMs);",
        "if(delivery[0]!=165||!pipe.IsMessageComplete)reason=DenialReason.InvalidFrame;",
        "catch(TimeoutException){reason=DenialReason.Timeout;Dispose();}",
        "catch(SecurityException){reason=DenialReason.Fault;Dispose();}",
        "Interlocked.Exchange(refserving,0);", "if(Interlocked.Exchange(refclosed,1)==0)pipe.Dispose();",
    ):
        require(witness in body, "missing boundary: " + witness)
    require(body.count("pipe.RunAsClient(") == 1, "single scoped impersonation")
    require(body.index("ReadRequest(elapsed") < body.index("pipe.RunAsClient("), "read precedes peer capture")
    require(body.index("restored=true;") < body.index("byte[]denial="), "revert before reply")
    require("consumed.Clear(" not in body and "consumed.Remove(" not in body, "never evict replay history")
    require(body.count("caseDenialOperation.") == 4, "fixed operation set")


def check_driver(text):
    body = compact(text)
    for witness in (
        "#errorP265_TESTS_REQUIRE_DEVELOPMENT_BUILD", "#errorP265_TESTS_NO_RELEASE_BUILD",
        'arguments[0]!="--permitted-disposable-runner"', "AuditAssembly(candidate);",
        "Need(candidate.EntryPoint==null)", "candidate.GetReferencedAssemblies()",
        "candidate.ManifestModule.ResolveMethod", "allowed.Contains(declaring.FullName)||guidSet||arrayInitializer",
        "MethodAttributes.PinvokeImpl", "typeof(DllImportAttribute)", "MethodImplAttributes.InternalCall",
        "Need(code!=OpCodes.Calli)", "Need(runAsClient==1&&tokenReads>=3)",
        "PipeSecurityacl=pipe.GetAccessControl()", "Need(acl.AreAccessRulesProtected)",
        "Need(acl.GetOwner(typeof(SecurityIdentifier)).Equals(current.User))",
        "Need(!rule.IsInherited)", "Need(rule.IdentityReference.Equals(current.User))",
        "Need(rule.PipeAccessRights==(PipeAccessRights.ReadWrite|PipeAccessRights.Synchronize))",
        "Need(rule.IdentityReference.Equals(newSecurityIdentifier(WellKnownSidType.NetworkSid,null)))",
        "Need(rule.PipeAccessRights==PipeAccessRights.FullControl)",
        "Need(rules.Count==2)", "Need(allows==1&&denies==1)",
        "SecurityAndProtocolTests();AdverseTransportTests();", "newbyte[]{1,2,3,4}",
        "ProvisioningAndThreadTests();", "DeliveryTests();", "Reply(client,newbyte[]{165});",
        'Reason(evidence)=="DevelopmentHold"', 'Field(evidence,"PeerObserved")', 'Field(evidence,"SidMatched")',
        'Field(evidence,"ThreadRestored")', 'Reason(Exchange(adapter,Frame(replay,3)))=="Replay"',
        'Reason(RejectFrame(adapter,spoof))=="InvalidFrame"', 'Reason(RejectFrame(adapter,duplicate))=="InvalidFrame"',
        'Reason(RejectFrame(adapter,oversized))=="InvalidFrame"', "index<128", '=="Capacity"',
        "new[]{-1,0,2,10}", "TokenImpersonationLevel.Identification", '=="PeerRejected"',
        '=="Disconnected"', '=="Timeout"', '=="Busy"', "server.Join(4000)", "worker.Join(3000)",
        "wait.WaitOne(3000)", "client.Connect(1000)", '"43-31-44-4E-01-01-00-00"',
        "P265_SAME_SID_APP_TRUST=UNTRUSTEDP96=HOLDREAL_KEY=HOLDPRODUCTION=HOLD",
    ):
        require(witness in body, "missing native test: " + witness)
    require(body.index("AuditAssembly(candidate);") < body.index("SecurityAndProtocolTests();"), "audit before execution")


class P265DevelopmentPipeSourceTests(unittest.TestCase):
    def test_frozen_authority_surfaces(self):
        for path, expected in FROZEN.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), expected)

    def test_native_adapter_contract(self):
        check_adapter(SOURCE.read_text(encoding="utf-8"))

    def test_native_driver_contract(self):
        check_driver(DRIVER.read_text(encoding="utf-8"))

    def test_negative_adapter_mutations(self):
        source = SOURCE.read_text(encoding="utf-8")
        for before, after in (
            ("#error P265_NO_RELEASE_BUILD", ""),
            ("#error P265_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED", ""),
            ("SetAccessRuleProtection(true, false)", "SetAccessRuleProtection(false, true)"),
            ("new PipeAccessRule(expectedSid,", "new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.WorldSid, null),"),
            ("AccessControlType.Deny", "AccessControlType.Allow"),
            ("PipeAccessRights.ReadWrite, AccessControlType.Allow", "PipeAccessRights.ReadWrite | PipeAccessRights.CreateNewInstance, AccessControlType.Allow"),
            ("PipeAccessRights.ReadWrite, AccessControlType.Allow", "PipeAccessRights.FullControl, AccessControlType.Allow"),
            ("HandleInheritability.None, (PipeAccessRights)0", "HandleInheritability.None, PipeAccessRights.ReadPermissions"),
            ("WindowsIdentity.GetCurrent(true)", "WindowsIdentity.GetCurrent()"),
            ("observed.Equals(expected)", "true"),
            ("matched = observed && SameSid(peer.User, expectedSid);", "matched = true;"),
            ("finally\n                    {\n                        RequireNoThreadIdentity();", "finally\n                    {"),
            ("!pipe.IsMessageComplete", "false"),
            ("header[0] != BodyLength", "false"),
            ("body[4] != 1", "false"),
            ("consumed.Contains(requestId)", "false"),
            ("consumed.Count >= ReplayCapacity", "false"),
            ("consumed.Add(requestId);", "consumed.Clear();"),
            ("handle.WaitOne(Remaining(elapsed, timeoutMs))", "handle.WaitOne()"),
            ("return false; } }", "return true; } }"),
            ("pipe.EndWrite(write);", "pipe.EndWrite(write); CredWriteW();"),
            ("pipe.EndWrite(write);", "pipe.EndWrite(write); new DevelopmentCustodyService().RejectStore();"),
            ("pipe.EndWrite(write);", 'pipe.EndWrite(write); File.WriteAllText("x", "x");'),
        ):
            with self.subTest(before=before):
                self.assertIn(before, source)
                with self.assertRaises(AssertionError):
                    check_adapter(source.replace(before, after))

    def test_negative_driver_mutations(self):
        source = DRIVER.read_text(encoding="utf-8")
        for before in (
            "AuditAssembly(candidate);", "Need(acl.AreAccessRulesProtected);", "Need(rules.Count == 2);",
            "Need(acl.GetOwner(typeof(SecurityIdentifier)).Equals(current.User));", "Need(!rule.IsInherited);",
            "Need(rule.PipeAccessRights == PipeAccessRights.FullControl);",
            "Need(code != OpCodes.Calli);", "Need(runAsClient == 1 && tokenReads >= 3);",
            "SecurityAndProtocolTests();", "AdverseTransportTests();", "MethodAttributes.PinvokeImpl",
        ):
            with self.subTest(before=before):
                self.assertIn(before, source)
                with self.assertRaises(AssertionError):
                    check_driver(source.replace(before, ""))
        for after in (
            "PipeAccessRights.ReadWrite | PipeAccessRights.CreateNewInstance |",
            "PipeAccessRights.FullControl |",
            "PipeAccessRights.ReadWrite | PipeAccessRights.ReadPermissions |",
            "",
        ):
            with self.subTest(rights=after):
                self.assertIn("PipeAccessRights.ReadWrite |", source)
                with self.assertRaises(AssertionError):
                    check_driver(source.replace("PipeAccessRights.ReadWrite |", after))


if __name__ == "__main__":
    unittest.main()
