"""Source and mutation checks only; this module never launches native artifacts."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "native_c1_successor/P267DevelopmentAtomicService.cs"
DRIVER = ROOT / "tests/p267_successor/P267DevelopmentAtomicTests.cs"
WORKFLOW = ROOT / ".github/workflows/p267-windows-atomic-ordering.yml"
FROZEN = {
    "native_c1_successor/P264DevelopmentCustodyService.cs": "698600E040C24A8E3A1502C6E417E7CA75522EEC86E90FC88B58C8C6A9A31997",
    "native_c1_successor/P265DevelopmentPipeAdapter.cs": "CC4065A40E8F7C8DD296EE913533E5AA611EDD2BBBE0D830DA8196A74A440636",
    "native_c1_successor/P266DevelopmentServiceIpc.cs": "1230D9531D2459EF933983B62362D878A514A1CDC06F8748BBA71685C8AAF6E4",
    "tests/p266_successor/P266DevelopmentServiceIpcTests.cs": "2A29ACC3E2AEEAAD5A7DB8285AC691D1AB09940FD881B63E532BA76FF89527DF",
    "tests/test_byok_c1_p266_development_service_ipc.py": "F845428364194358CB6BB9002FC4254414ADBF7557A659D8915552997AB49A99",
    ".github/workflows/p266-development-service-ipc.yml": "1315A39131806D098535775BB8FC21C81B1A8A4A35361E5BFDC6A17D66547549",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs": "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
    "tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs": "2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F",
}


def compact(text):
    return re.sub(r"\s+", "", re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S))


def require(value):
    if not value:
        raise AssertionError("P267 bounded source contract")


def block(text, signature):
    start = text.index("{", text.index(signature))
    end, depth = start + 1, 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


def check_service(text):
    body = compact(text)
    for flag, marker in (
        ("DEBUG", "P267_NO_RELEASE_BUILD"),
        ("C1_P267_DEVELOPMENT_ONLY", "P267_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED"),
        ("C1_P265_DEVELOPMENT_ONLY", "P267_REQUIRES_P265_DEVELOPMENT_ONLY"),
    ):
        require(f"#if!{flag}#error{marker}#endif" in body)
    require(body.count("readonlyobjectsync=newobject();") == 1)
    require("lock(" not in body and body.count("Monitor.Enter(sync)") == 1)
    for witness in (
        "if(Monitor.IsEntered(sync)){reentryPending=true;thrownewInvalidOperationException(\"P267_NONREENTRANT\");}",
        "finally{Monitor.Exit(sync);}",
        "RejectReentry();Monitor.Enter(sync);",
        "RejectReentry();try{Terminate(3);}finally{base.Dispose(disposing);}",
        "reentryPending=false;faulted=true;recoveryRequired=true;CloseLocked();",
        "used=true;mayHaveEffect=true;recoveryRequired=true;try{submissions++;",
        "!Object.ReferenceEquals(attempt,prepared)",
        "!started||Closed||recoveryRequired||used||attempt==null",
        "!started||Closed||recoveryRequired||prepared!=null||used",
        "recoveryRequired=!freshSyntheticFixture;",
        "if(faulted)recoveryRequired=true;prepared=null;",
        "DevelopmentAtomicService:ServiceBase", "adapter=newDevelopmentPipeAdapter(current);",
        "serving.ServeOnce(ServeTimeoutMs)", "Closed?null:endpoint",
        "joining.Join(JoinTimeoutMs)", "private static int Main(string[] arguments) { return 64; }".replace(" ", ""),
    ):
        require(witness in body)
    require(body.count("submissions++") == 1 and body.count("mayHaveEffect=true") == 1)
    require("mayHaveEffect=false" not in body and "recoveryRequired=false" not in body)
    for signature in ("Disposition Observe()", "Attempt PrepareSynthetic()", "Disposition Dispatch(Attempt",
                      "Disposition StartDevelopment()", "Disposition Terminate(int", "void ServeLoop()"):
        require("using(Enter())" in compact(block(text, signature)))
    for prop in ("CredentialAllowed", "StoreAllowed", "PrivilegedAllowed", "ProductionEligible"):
        require(f"bool{prop}{{get{{returnfalse;}}}}" in body)
    wire = compact(block(text, "void ServeLoop()"))
    require("Dispatch(" not in wire and "PrepareSynthetic(" not in wire and "submissions" not in wire)
    require(not re.search(r"\b(?:DispatchSynthetic|DispatchSyntheticFailure|PrepareSynthetic)\(", wire))
    require(not re.search(r"\b(?:DllImport|extern|unsafe|dynamic|Action|Func|File|Registry|Process|ServiceController|ServiceBase\.Run|CredWrite|CredRead|CredDelete|DPAPI|HttpClient|Socket)\b", body))
    require(set(re.findall(r"using ([\w.]+);", text)) == {
        "System", "System.Security.Principal", "System.ServiceProcess", "System.Threading",
        "Nayeon.ByokC1.P265Development"})


class AtomicSourceTests(unittest.TestCase):
    def test_01_service_contract(self):
        check_service(SERVICE.read_text())

    def test_02_frozen_bytes(self):
        for path, digest in FROZEN.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), digest, path)

    def test_03_missing_guard_mutations(self):
        text = SERVICE.read_text()
        for flag in ("DEBUG", "C1_P267_DEVELOPMENT_ONLY", "C1_P265_DEVELOPMENT_ONLY"):
            with self.assertRaises(AssertionError):
                check_service(text.replace("#if !" + flag, "#if false", 1))

    def test_04_order_mutations(self):
        text = SERVICE.read_text()
        for before, after in (
            ("mayHaveEffect = true;", "mayHaveEffect = false;"),
            ("recoveryRequired = true; // commitment", "recoveryRequired = false; // commitment"),
            ("submissions++;", "submissions += 2;"),
            ("!Object.ReferenceEquals(attempt, prepared)", "false"),
        ):
            with self.assertRaises(AssertionError):
                check_service(text.replace(before, after, 1))

    def test_05_gate_mutations(self):
        text = SERVICE.read_text()
        for before, after in (("Monitor.IsEntered(sync)", "false"),
                              ("using (Enter())", "lock (sync)"),
                              ("reentryPending = true;", "reentryPending = false;")):
            with self.assertRaises(AssertionError):
                check_service(text.replace(before, after, 1))

    def test_06_wire_and_authority_mutations(self):
        text = SERVICE.read_text()
        for before, after in (("serving.ServeOnce(ServeTimeoutMs)", "serving.ServeOnce(100)"),
                              ("return false;", "return true;"),
                              ("if (Closed) return; serving = adapter;", "DispatchSynthetic(prepared); if (Closed) return; serving = adapter;")):
            with self.assertRaises(AssertionError):
                check_service(text.replace(before, after, 1))
        for call in ("DispatchSynthetic(prepared)", "DispatchSyntheticFailure(prepared)", "PrepareSynthetic()",
                     "current.DispatchSynthetic(prepared)", "current.DispatchSyntheticFailure(prepared)",
                     "current.PrepareSynthetic()"):
            with self.subTest(call=call), self.assertRaises(AssertionError):
                check_service(text.replace("if (Closed) return; serving = adapter;",
                                           call + "; if (Closed) return; serving = adapter;", 1))

    def test_07_native_coverage(self):
        text = DRIVER.read_text()
        for witness in ("OrderedWinners();", "ContendedGate();", "ReentryAndFailure();", "WireAndLifecycle();",
                        "Monitor.Enter(gate)", "firstDone.WaitOne(4000)", "thread.Join(4000)",
                        "new DevelopmentAtomicService(false)", "P267_NONREENTRANT", "DenialReason.Replay",
                        "43-31-44-4E-01-01-00-00", "DispatchSyntheticFailure(attempt)", 'GetMethod("OnStop"'):
            self.assertIn(witness, text)
        self.assertNotIn("ServiceBase.Run", text)

    def test_08_workflow_custody(self):
        text = WORKFLOW.read_text()
        for witness in ("08c5cc6d3c3f9b25bd0b9f85b1c515af960a0169", "git rev-parse 'HEAD^'",
                        "github.event.pull_request.head.sha", "github.event.pull_request.base.sha",
                        "byok-c1-p266-service-bound-ipc-synthetic-20261117", "^A\\t", "changes.Count -ne 5",
                        "arch: x64", "arch: x86", "/warnaserror+", "error CS1029:", "40000",
                        "Stop-Process", "source-hashes.json", "*.log", "*.exit", "*.json", "Ran 8 tests"):
            self.assertIn(witness, text)
        for action in ("actions/checkout", "actions/setup-python", "actions/upload-artifact"):
            self.assertRegex(text, re.escape(action) + r"@[0-9a-f]{40}\b")
        self.assertNotIn("*.exe", text)
        self.assertNotRegex(text, r"(?<!\w)sc\.exe")


if __name__ == "__main__":
    unittest.main()
