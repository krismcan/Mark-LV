"""Bounded source/mutation checks; NEVER executes native code or accesses credentials."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = "native_c1_successor/P268ServiceOwnedPendingTransaction.cs"
DRIVER = "tests/p268_successor/P268RemediationTests.cs"
WORKFLOW = ".github/workflows/p268-windows-p96-remediation.yml"
FROZEN = {
    "tests/p95_native_custody_preflight/CustodyLedger.cs": "93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs": "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
    "tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs": "2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F",
}


def compact(text):
    return re.sub(r"\s+", "", re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S))


def require(condition):
    if not condition:
        raise AssertionError("P268 successor boundary")


def check_service(text):
    body = compact(text)
    for flag, error in (("DEBUG", "P268_NO_RELEASE_BUILD"),
                        ("C1_P268_DEVELOPMENT_ONLY", "P268_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED")):
        require(f"#if!{flag}#error{error}#endif" in body)
    # Red if the old transaction is ever composed into this candidate closure.
    require(not re.search(r"(?:PendingCustodyTransaction|P96Fixture|ActualCoordinator|P96NegativeProof|ITrustedPendingApproval|StillCurrent|DllImport|extern|unsafe|dynamic|CredWrite|CredDelete|PendingWinCredStore|ServiceBase)", body))
    for witness in (
        "privatereadonlyobjectgate=newobject();", "Monitor.IsEntered(gate)",
        "faulted=true;recoveryRequired=true;closed=true;thrownewInvalidOperationException(\"P268_NONREENTRANT\");",
        "Monitor.TryEnter(gate,500)", "Interlocked.Exchange(refadmissionFailure,1)",
        "finally{Monitor.Exit(gate);}", "Volatile.Read(refadmissionFailure)",
        "privateServiceOwnedPendingTransaction(DevelopmentPendingStatevalue,",
        "P96StateFixturefixture;", "value.Claim();development=value;state=value;custody=lease;",
        "recoveryRequired=!freshSyntheticSession;", "if(!development.Enrolled)thrownewLedgerBlocked();",
        "ProductionEligible{get{returnfalse;}}", "TrustedIssuerConnected{get{returnfalse;}}",
        "!Object.ReferenceEquals(approval,prepared)", "approval.Operation!=op",
        "used=true;prepared=null;", "owned=candidate==null?null:(byte[])candidate.Clone();",
        "CustodyLedger.Verify(before,anchor)", "CustodyLedger.AppendIntent(before,op,CustodyLedger.NewNonce())",
        "Persist(before,anchor,intent);", "!SamePair(intent,intentAnchor)||Present()!=present||!Owned(lease)",
        "Barrier();mayHaveEffect=true;if(op==LedgerOperation.Delete)state.DeletePending();elsestate.SaveOrReplace(owned);Barrier();",
        "stringterminal=CustodyLedger.AppendTerminal(intent);Persist(intent,intentAnchor,terminal);",
        "lease.MarkTerminalVerified();Barrier();",
        "try{if(lease!=null){lease.Dispose();Barrier();}}", "Array.Clear(owned,0,owned.Length);Exit();",
    ):
        require(witness in body)
    require(body.count("Monitor.TryEnter(") == 1)
    require("lock(" not in body and "Monitor.Enter(" not in body)
    require(body.count("state.SaveOrReplace(") == 1 and body.count("state.DeletePending(") == 1)
    require("mayHaveEffect=false" not in body and "recoveryRequired=false" not in body)
    require("Enter();byte[]owned=null;" in body)
    for witness in ("Enter();try{closed=true;prepared=null;", "Enter();try{Barrier();if(closed||recoveryRequired||used||prepared!=null"):
        require(witness in body)
    # Two-store exact intent/terminal readback, with barrier after every call.
    require("state.WriteJournal(before,next);Barrier();" in body)
    require("state.WriteAnchor(anchor,nextAnchor);Barrier();if(!SamePair(next,nextAnchor))thrownewLedgerBlocked();" in body)


class P268SourceTests(unittest.TestCase):
    def test_service_contract(self):
        check_service((ROOT / SERVICE).read_text(encoding="utf-8-sig"))

    def test_frozen_sources(self):
        for path, digest in FROZEN.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), digest, path)

    def test_legacy_reference_red(self):
        text = (ROOT / SERVICE).read_text(encoding="utf-8-sig")
        for call in ("new PendingCustodyTransaction(state, approval, custody);", "ITrustedPendingApproval approval;", "approval.StillCurrent(op, owned);", "new P96Fixture().ActualCoordinator.Apply(op, owned);"):
            with self.assertRaises(AssertionError):
                check_service(text + "\n" + call)

    def test_gate_and_effect_mutations_red(self):
        text = (ROOT / SERVICE).read_text(encoding="utf-8-sig")
        for old, new in (("Monitor.IsEntered(gate)", "false"),
                         ("Monitor.TryEnter(gate, 500)", "true"),
                         ("mayHaveEffect = true;", "mayHaveEffect = false;"),
                         ("state.SaveOrReplace(owned);", "state.SaveOrReplace(owned); state.SaveOrReplace(owned);"),
                         ("!Object.ReferenceEquals(approval, prepared)", "false"),
                         ("Persist(before, anchor, intent);", ";"),
                         ("lease.Dispose(); Barrier();", "lease.Dispose();"),
                         ("return false;", "return true;"),
                         ("#if !DEBUG", "#if false"),
                         ("#if !C1_P268_DEVELOPMENT_ONLY", "#if false")):
            self.assertIn(old, text)
            with self.subTest(old=old), self.assertRaises(AssertionError):
                check_service(text.replace(old, new, 1))

    def test_executable_cases(self):
        text = (ROOT / DRIVER).read_text(encoding="utf-8-sig")
        for witness in ("RevocationWins(selected)", "EffectWins(selected, control)", "Reentry(false)", "Reentry(true)",
                        "LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete", "new P96StateFixture(Approval)",
                        "EffectsAfterRevoke == 0", "ControlResult.TooLate", "LeaseFailures", "TerminalMismatch",
                        "first.Ticket", "fresh", "Enrolled = false", "ThrowDuringEffect = true", "state.PossibleEffects == 0",
                        'FaultInjection("write-journal", 2)', 'FaultInjection("write-anchor", 2)', "thread.Join(3000)"):
            self.assertIn(witness, text)
        self.assertNotIn("PendingCustodyTransaction", text)

    def test_workflow(self):
        text = (ROOT / WORKFLOW).read_text(encoding="utf-8-sig")
        for witness in ("0241b4277b8098c47e4de725bd1425bf0a0e764e", "git rev-parse 'HEAD^'", "changes.Count -ne 5", "^A\\t",
                        "byok-c1-p268-p96-actual-successor-20261118", "byok-c1-p267-service-owned-atomic-ordering-20261118",
                        "arch: x64", "arch: x86", "/warnaserror+", "40000", "Stop-Process", "source-hashes.json",
                        "P96NegativeProof", "P268RemediationTests", "C1_P268_DEVELOPMENT_ONLY", "error CS1029:",
                        "P96_NATIVE_ACTUAL_COORDINATOR_TESTS_PASSED=15", "P268_SUCCESSOR=PASS CASES=33", "*.exit", "*.log"):
            self.assertIn(witness, text)
        for action in ("actions/checkout", "actions/setup-python", "actions/upload-artifact"):
            self.assertRegex(text, re.escape(action) + r"@[0-9a-f]{40}\b")
        self.assertNotIn("*.exe", text)
        self.assertNotIn("pull_request_target", text)


if __name__ == "__main__":
    unittest.main()
