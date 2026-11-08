// P105 native source integration: original J2/A2 custody ledger vs legacy J1/A1 reader.
// Nonsecret, x64-only, no service installation, IPC, native effect or credential.
using System;
using Nayeon.ByokC1;

internal static class P105NativeLedgerFormatTests
{
    private static int passed, failed;
    private static void Need(bool yes) {
        if (!yes) throw new InvalidOperationException("P105 assertion failed");
    }
    private static void Case(string name, Action f) {
        try { f(); ++passed; Console.WriteLine("PASS "+name); }
        catch (Exception e) { ++failed; Console.WriteLine("FAIL "+name+" "+e.GetType().Name); }
    }
    private static void Block(Action f) {
        bool blocked=false;
        try { f(); } catch (LedgerBlocked) { blocked=true; }
        Need(blocked);
    }
    public static int Main() {
        string first=CustodyLedger.CreateInitial(new string('a',32));
        string a1=CustodyLedger.Anchor(first);
        string intent=CustodyLedger.AppendIntent(first,LedgerOperation.Save,new string('b',32));
        string ai=CustodyLedger.Anchor(intent);
        string stored=CustodyLedger.AppendTerminal(intent);
        string asaved=CustodyLedger.Anchor(stored);
        string repl=CustodyLedger.AppendIntent(stored,LedgerOperation.Replace,new string('c',32));
        string repldone=CustodyLedger.AppendTerminal(repl);
        string del=CustodyLedger.AppendIntent(repldone,LedgerOperation.Delete,new string('d',32));
        string deleted=CustodyLedger.AppendTerminal(del);
        string adel=CustodyLedger.Anchor(deleted);
        Case("original-format-exact-j2-a2",()=>Need(first.StartsWith("J2|") && a1.StartsWith("A2|")));
        Case("original-native-initial-verified",()=>Need(CustodyLedger.Verify(first,a1)==LedgerPhase.Initial));
        Case("original-native-intent-verified",()=>Need(CustodyLedger.Verify(intent,ai)==LedgerPhase.InFlight));
        Case("original-native-save-verified",()=>Need(CustodyLedger.Verify(stored,asaved)==LedgerPhase.CommittedUnverified));
        Case("original-native-replace-verified",()=>Need(CustodyLedger.Verify(repl,CustodyLedger.Anchor(repl))==LedgerPhase.InFlight));
        Case("original-native-replace-terminal-verified",()=>Need(CustodyLedger.Verify(repldone,CustodyLedger.Anchor(repldone))==LedgerPhase.CommittedUnverified));
        Case("original-native-delete-intent-verified",()=>Need(CustodyLedger.Verify(del,CustodyLedger.Anchor(del))==LedgerPhase.InFlight));
        Case("original-native-delete-terminal-verified",()=>Need(CustodyLedger.Verify(deleted,adel)==LedgerPhase.CommittedAbsent));
        Case("legacy-reader-refuses-j2-initial",()=>Need(RecoveryReader.Assess(first,a1,false,true)==RecoveryDisposition.RecoveryRequired));
        Case("legacy-reader-refuses-j2-inflight",()=>Need(RecoveryReader.Assess(intent,ai,false,true)==RecoveryDisposition.RecoveryRequired));
        Case("legacy-reader-refuses-j2-saved",()=>Need(RecoveryReader.Assess(stored,asaved,true,true)==RecoveryDisposition.RecoveryRequired));
        Case("legacy-reader-refuses-j2-deleted",()=>Need(RecoveryReader.Assess(deleted,adel,false,true)==RecoveryDisposition.RecoveryRequired));
        Case("legacy-reader-untrusted-os-unavailable",()=>Need(RecoveryReader.Assess(first,a1,false,false)==RecoveryDisposition.Unavailable));
        Case("native-j2-rejects-missing-anchor",()=>Block(()=>{CustodyLedger.Verify(stored,null);}));
        Case("native-j2-rejects-anchor-rollback",()=>Block(()=>{CustodyLedger.Verify(stored,a1);}));
        Case("native-j2-rejects-truncated-file",()=>Block(()=>{CustodyLedger.Verify(stored.Substring(0,stored.Length-1),asaved);}));
        Case("legacy-j1-is-not-native-j2",()=>{
            string old="J1|0|"+new string('a',32)+"|INITIAL|INITIAL";
            string oldA=RecoveryReader.StructuralAnchorForSyntheticTest(old);
            Need(RecoveryReader.Assess(old,oldA,false,true)==RecoveryDisposition.Uninitialized);
            Block(()=>{CustodyLedger.Verify(old,oldA);});
        });
        Case("native-j2-rejects-lost-history",()=>Block(()=>{CustodyLedger.Verify(null,null);}));
        Case("original-three-service-and-effect-guards-closed",()=>{
            Need(!ServiceGate.LiveEligible());
            Need(PendingServiceState.LegacyEffectEntryDisabled());
            Need(PendingWinCredStore.NativeMutationAdmissionPending());
        });
        Console.WriteLine("P105_REAL_NATIVE_LEDGER_CASES_PASSED="+passed);
        Console.WriteLine("P105_REAL_NATIVE_LEDGER_CASES_FAILED="+failed);
        Console.WriteLine("P105_J2_A2_VS_J1_A1=NONINTERCHANGEABLE");
        Console.WriteLine("P105_NATIVE_WINCRED_EFFECTS=NONE");
        Console.WriteLine("P105_G3_PRODUCTION_AUTHORITY=NOT_IMPLEMENTED");
        Console.WriteLine("P105_C1_PRODUCTION_RELEASE=HOLD");
        return passed==19 && failed==0 ? 0 : 1;
    }
}
