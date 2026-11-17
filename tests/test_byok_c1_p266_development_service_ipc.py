"""Bounded source/mutation checks only. Never load or launch native artifacts."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "native_c1_successor/P266DevelopmentServiceIpc.cs"
DRIVER = ROOT / "tests/p266_successor/P266DevelopmentServiceIpcTests.cs"
WORKFLOW = ROOT / ".github/workflows/p266-development-service-ipc.yml"
FROZEN = {
    "native_c1_successor/P264DevelopmentCustodyService.cs": "698600E040C24A8E3A1502C6E417E7CA75522EEC86E90FC88B58C8C6A9A31997",
    "native_c1_successor/P265DevelopmentPipeAdapter.cs": "CC4065A40E8F7C8DD296EE913533E5AA611EDD2BBBE0D830DA8196A74A440636",
    "tests/p265_successor/P265DevelopmentPipeTests.cs": "884C3465AE5B630AE8C1088DCA2F226EBA4E556EFB8305D6A52D3A4A61F7E262",
    "tests/test_byok_c1_p265_development_pipe.py": "C7FFEA665619631498A50E3B9E5C751B20D0A512BA224EC219C0AD54BF96AD54",
    ".github/workflows/p265-windows-development-pipe.yml": "540DE2CEF4BA99FB024453E4A5881669D202CB0AB7AC7B8B39B1BA8BEE4D5DE2",
}


def code(text):
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)


def compact(text):
    return re.sub(r"\s+", "", code(text))


def need(value, message):
    if not value:
        raise AssertionError(message)


def block(text, signature):
    start = text.index("{", text.index(signature))
    depth = 1
    end = start + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


def check_service(text):
    body = compact(text)
    for flag, diagnostic in (
        ("C1_P266_DEVELOPMENT_ONLY", "P266_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED"),
        ("C1_P265_DEVELOPMENT_ONLY", "P266_REQUIRES_P265_DEVELOPMENT_ONLY"),
        ("DEBUG", "P266_NO_RELEASE_BUILD"),
    ):
        need(f"#if!{flag}#error{diagnostic}#endif" in body, "hard development guard")
    need(set(re.findall(r"using ([\w.]+);", code(text))) == {
        "System", "System.Security.Principal", "System.ServiceProcess", "System.Threading",
        "Nayeon.ByokC1.P265Development"}, "bounded dependency imports")
    need(not re.search(r"\b(?:DllImport|LibraryImport|extern|unsafe|dynamic|Reflection|Activator|"
                       r"Assembly|Marshal|ServiceController|DevelopmentCustodyService|ServiceGate|"
                       r"Cred\w*W|WinCred|File|Directory|Registry|Process|HttpClient|WebClient|"
                       r"Socket|TcpClient|Encoding|Action|Func)\b|byte\s*\[|Thread\.Abort", code(text)),
         "no effects, payload, callback, loader or old gate")
    for flag in ("CredentialAllowed", "StoreAllowed", "PrivilegedAllowed", "ProductionEligible"):
        need("bool" + flag + "{get{returnfalse;}}" in body, "fixed refusal")
    for witness in (
        "DevelopmentServiceIpc:ServiceBase", "ServeTimeoutMs=2000,JoinTimeoutMs=2500,MaximumRequests=128;",
        "privatereadonlyobjectsync=newobject();", "WindowsIdentity.GetCurrent(true)",
        'if(thread!=null)thrownewInvalidOperationException("P266_THREAD_IDENTITY")',
        "using(WindowsIdentitycurrent=WindowsIdentity.GetCurrent())", "current.IsAnonymous||current.IsSystem",
        "current.User.IsWellKnown(WellKnownSidType.LocalServiceSid)",
        "current.User.IsWellKnown(WellKnownSidType.NetworkServiceSid)",
        'current.User.Value.StartsWith("S-1-5-80-",StringComparison.Ordinal)',
        "adapter=newDevelopmentPipeAdapter(current);", "if(started||Closed){faulted=true;failed=true;}",
        "worker=newThread(ServeLoop);worker.IsBackground=true;", "worker.Start();started=true;",
        "returnTerminate(2);", "if(!failed)returnView();CloseLocked();",
        "returnstopped||revoked||faulted||disposed;", "Closed?null:endpoint",
        "for(intindex=0;index<MaximumRequests;index++)", "if(Closed)return;serving=adapter;",
        "serving.ServeOnce(ServeTimeoutMs)", "if(Closed)return;requests++;lastReason=evidence.Reason;",
        "!evidence.ThreadRestored||!evidence.ReplyWritten", "evidence.Reason!=DenialReason.DevelopmentHold",
        "evidence.Reason!=DenialReason.Replay", "evidence.Reason!=DenialReason.Capacity",
        "faulted=true;CloseLocked();return;", "fixture.Delete();if(adapter!=null)",
        "try{adapter.Dispose();}catch(Exceptionerror){faulted=true;if(cleanupFailure==null)cleanupFailure=error;}",
        'if(cleanupFailure!=null)thrownewInvalidOperationException("P266_CLEANUP_FAILED",cleanupFailure);',
        "catch{lock(sync){faulted=true;lastReason=DenialReason.Fault;CloseLocked();}}",
        "finally{lock(sync){try{CloseLocked();}finally{workerExited=true;}}}",
        "if(kind==0)stopped=true;elseif(kind==1)revoked=true;elseif(kind==2)faulted=true;",
        "else{stopped=true;disposed=true;}CloseLocked();joining=worker;}",
        "joining!=null&&joining.IsAlive&&!joining.Join(JoinTimeoutMs)",
        'thrownewSystem.TimeoutException("P266_WORKER_JOIN_FAILED")',
        "StopDevelopment(){returnTerminate(0);}", "Revoke(){returnTerminate(1);}", "Fault(){returnTerminate(2);}",
        "try{Terminate(3);}finally{base.Dispose(disposing);}",
        "OnStop(){StopDevelopment();}", "OnShutdown(){StopDevelopment();}",
        "OnCustomCommand(intcommand){Observe();}", "Dispositionresult=StartDevelopment();",
        '!String.Equals(arguments[0],"--development-only-no-effects",StringComparison.Ordinal))return64;',
        "arguments==null||arguments.Length!=1", "ServiceBase.Run(service);",
    ):
        need(witness in body, "missing owner contract: " + witness)
    need(body.count("newDevelopmentPipeAdapter(") == 1 and body.count(".ServeOnce(") == 1,
         "one owned adapter and one dispatch")
    loop = block(body, "privatevoidServeLoop()")
    need("fixture" not in loop and not re.search(
        r"(?<!\w)(?:StageSynthetic|ReplaceSynthetic|DeleteSynthetic)\(", loop),
         "no wire-to-fixture route")
    need(body.count("ServiceBase.Run(") == 1 and "ServiceBase.Run(" in block(body, "privatestaticintMain("),
         "SCM dispatch confined to guarded Main")
    need(not re.search(r"(?<!\w)(?:started|stopped|revoked|faulted|disposed)=false", body), "no latch clearing")
    fixture = block(body, "privatesealedclassSyntheticFixture")
    need(fixture == "{internalintMarker,Stages,Replacements,Deletes;"
         "internalvoidStage(){if(Marker==0){Marker=266;Stages++;}}"
         "internalvoidReplace(){if(Marker==266)Replacements++;}"
         "internalvoidDelete(){if(Marker==266){Marker=0;Deletes++;}}}", "fixed synthetic state only")
    for name, operation in (("Stage", "Stage"), ("Replace", "Replace"), ("Delete", "Delete")):
        need(block(body, "Disposition" + name + "Synthetic()") ==
             "{lock(sync){if(started&&!Closed)fixture." + operation + "();returnView();}}", "local fixture gate")


def check_driver(text):
    body = compact(text)
    for witness in (
        "#errorP266_TESTS_REQUIRE_DEVELOPMENT_BUILD", "#errorP266_TESTS_REQUIRE_P265_DEVELOPMENT_BUILD",
        "#errorP266_TESTS_NO_RELEASE_BUILD", "SyntheticAndWire();", "TerminalsAndScmCallbacks();",
        "TimeoutAndTransportFault();", "ContentionAndIsolation();", "KernelIdentity(service);",
        "BoundedLoop();", "Need(service.Observe().Requests==128);", "Interlocked.Increment(refassertions)",
        "using(WindowsImpersonationContextcontext=current.Impersonate())", "Need(denied.Faulted&&!denied.Started);",
        "foreach(Threadclientinclients)Need(client.Join(4000));", "Need(failure==null);",
        "Need(acl.AreAccessRulesProtected);", "Need(rules.Count==2);",
        "Need(acl.GetOwner(typeof(SecurityIdentifier)).Equals(current.User));",
        "PipeAccessRights.ReadWrite|PipeAccessRights.Synchronize", "WellKnownSidType.NetworkSid",
        "Need(rule.PipeAccessRights==PipeAccessRights.FullControl);", "Need(!rule.IsInherited);",
        "Need(worker==null||worker.Join(1000));", "Need(worker==null||!worker.IsAlive);",
        "SafePipeHandle.IsClosed", "Complete(client,read,delegate{count=client.EndRead(read);});",
        "Complete(client,write,delegate{client.EndWrite(write);});",
        "using(WaitHandlehandle=pending.AsyncWaitHandle)", "if(!ready)client.Dispose();",
        "finally{try{finish();}catch(IOException){if(ready)throw;}catch(ObjectDisposedException){if(ready)throw;}}",
        'Need(BitConverter.ToString(reply)=="43-31-44-4E-01-01-00-00");',
        "Need(service.Observe().Marker==266);", "Need(service.Observe().Stages==1);",
        "Need(service.Observe().Replacements==1);", "Need(service.Observe().Deletes==0);",
        "Need(service.DeleteSynthetic().Marker==0);", "Need(service.Observe().Deletes==2);",
        "Need(after.Stages==before.Stages&&after.Replacements==before.Replacements&&after.Deletes==before.Deletes);",
        "Need(after.Faulted);Exited(service);", "Need(service.Observe().LastReason==DenialReason.Timeout);",
        "Need(service.Observe().LastReason==DenialReason.InvalidFrame);", "new[]{-1,2,10}",
        "Need(service.Observe().Stopped&&service.Observe().Revoked);", "contender.Join(4000)",
        "iteration<16", "Need(error==null);", "Need(watch.ElapsedMilliseconds<=3000);",
        "Need(second.Observe().Stages==0);", "Need(!view.CredentialAllowed);", "Need(!view.StoreAllowed);",
        "Need(!view.PrivilegedAllowed);", "Need(!view.ProductionEligible);",
        "if(view.Stopped||view.Revoked||view.Faulted||view.Disposed){Need(view.Marker==0);Need(view.Endpoint==null);}",
        "P266_NATIVE_TESTS=PASSASSERTIONS=", "BITS=", "REAL_KEY=NO_GOPRODUCTION=HOLD",
        "entry.Invoke(null,newobject[]{invalid})==64",
    ):
        need(witness in body, "runtime test contract: " + witness)
    need("ServiceBase.Run(" not in body and "Assembly.Load" not in body, "in-process lifecycle only")


class P266DevelopmentServiceIpcSourceTests(unittest.TestCase):
    def test_frozen_composition(self):
        for path, expected in FROZEN.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), expected)

    def test_service_contract(self):
        check_service(SERVICE.read_text(encoding="utf-8"))

    def test_driver_contract(self):
        check_driver(DRIVER.read_text(encoding="utf-8"))

    def test_service_mutations(self):
        source = SERVICE.read_text(encoding="utf-8")
        for before, after in (
            ("#error P266_NO_RELEASE_BUILD", ""),
            ("#error P266_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED", ""),
            ("#error P266_REQUIRES_P265_DEVELOPMENT_ONLY", ""),
            ("WindowsIdentity.GetCurrent(true)", "WindowsIdentity.GetCurrent()"),
            ("current.IsAnonymous || current.IsSystem", "false"),
            ("adapter = new DevelopmentPipeAdapter(current);", ""),
            ("if (started || Closed)", "if (false)"),
            ("worker.IsBackground = true;", ""),
            ("joining.Join(JoinTimeoutMs)", "joining.Join()"),
            ("CloseLocked();\n                joining = worker;", "joining = worker;"),
            ("fixture.Delete();", ""), ("adapter.Dispose();", ""),
            ("cleanupFailure = error;", ""),
            ("if (!failed) return View();\n                CloseLocked();", "if (!failed) return View();"),
            ("index < MaximumRequests", "true"),
            ("!evidence.ThreadRestored || !evidence.ReplyWritten", "false"),
            ("faulted = true; CloseLocked(); return;", "return;"),
            ("if (started && !Closed)", "if (started)"),
            ("Marker = 266;", "Marker = 267;"),
            ("Replacements++;", "Marker = 266; Replacements++;"),
            ("serving.ServeOnce(ServeTimeoutMs);", "serving.ServeOnce(ServeTimeoutMs); StageSynthetic();"),
            ("serving.ServeOnce(ServeTimeoutMs);", "serving.ServeOnce(ServeTimeoutMs); this.ReplaceSynthetic();"),
            ("serving.ServeOnce(ServeTimeoutMs);", "serving.ServeOnce(ServeTimeoutMs); this.DeleteSynthetic();"),
            ("return false;", "return true;"),
            ("Observe(); }", "StageSynthetic(); }"),
            ("ServiceBase.Run(service);", ""),
            ("arguments.Length != 1", "arguments.Length < 1"),
            ("started = true;", "started = true; stopped = false;"),
            ("started = true;", "started = true; faulted = false;"),
            ("fixture.Stage();", "fixture.Stage(); File.WriteAllText(\"x\", \"x\");"),
        ):
            with self.subTest(before=before):
                self.assertIn(before, source)
                with self.assertRaises(AssertionError):
                    check_service(source.replace(before, after))

    def test_driver_mutations(self):
        source = DRIVER.read_text(encoding="utf-8")
        for before in ("KernelIdentity(service);", "SyntheticAndWire();", "TimeoutAndTransportFault();",
                       "ContentionAndIsolation();", "Need(rules.Count == 2);", "Need(!rule.IsInherited);",
                       "Need(!view.PrivilegedAllowed);", "Need(service.Observe().Marker == 266);",
                       "Need(worker == null || !worker.IsAlive);", "if (!ready) client.Dispose();",
                       "try { finish(); }", "Need(error == null);", "Need(after.Faulted);"):
            with self.subTest(before=before):
                self.assertIn(before, source)
                with self.assertRaises(AssertionError):
                    check_driver(source.replace(before, ""))

    def test_workflow_contract(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for witness in (
            "byok-c1-p265-authenticated-windows-ipc-20261117", "e835f60447f06a9320d3f474d3320f539f847f0a",
            "contents: read", "fail-fast: false", "arch: x64", "arch: x86", "35000",
            "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
            "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
            "persist-credentials: false", "github.event.pull_request.head.sha",
            "git diff --name-status", "git status --porcelain", "Get-FileHash", "source-hashes.json",
            "P264DevelopmentCustodyService.cs", "P265DevelopmentPipeAdapter.cs", "/warnaserror+",
            "C1_P264_DEVELOPMENT_ONLY", "C1_P265_DEVELOPMENT_ONLY", "C1_P266_DEVELOPMENT_ONLY",
            "P266_NATIVE_TESTS=PASS", "native-runtime.exit", "-WindowStyle Hidden",
            "Ran 6 tests in", "--permitted-disposable-runner", "*.log", "*.exit", "*.json",
        ):
            self.assertIn(witness, workflow)
        self.assertNotRegex(workflow, r"(?i)secrets\.|(?<!\w)sc\.exe|New-Service|Start-Service|ReflectionOnlyLoad|/optimize\+")


if __name__ == "__main__":
    unittest.main()
