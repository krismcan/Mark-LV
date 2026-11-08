// P109 ordinary candidate assembly audit (NO C1_SYNTHETIC_TEST define).
// This test exercises actual compiled .NET method surfaces, not source grep.
// It is intentionally unprivileged and cannot touch WinCred or credentials.
#if C1_SYNTHETIC_TEST
#error Ordinary build audit must NEVER compile with synthetic test define.
#endif
using System;
using System.Reflection;
using Nayeon.ByokC1;

internal static class P109OrdinaryAssemblyAuditTests
{
    private static int passed, failed;
    private static void Need(bool ok,string why)
    { if(!ok)throw new InvalidOperationException("P109 ordinary "+why); }
    private static void Run(string label,Action action)
    {
        try{action();passed++;Console.WriteLine("PASS "+label);}
        catch(Exception e){failed++;Console.WriteLine("FAIL "+label+" "+e.GetType().Name);}
    }
    private static bool HasInstance(Type type,string name)
    {
        return type.GetMethod(name,BindingFlags.NonPublic|BindingFlags.Public|
            BindingFlags.Instance|BindingFlags.DeclaredOnly)!=null;
    }
    public static int Main()
    {
        Run("ordinary-host-no-synthetic-preparation",() =>
            Need(!HasInstance(typeof(CustodyService),"PrepareSyntheticOnly"),"prep method"));
        Run("ordinary-host-no-positive-commit",() =>
            Need(!HasInstance(typeof(CustodyService),"CommitSyntheticDecisionOnly"),"commit method"));
        Run("ordinary-host-no-synthetic-terminal-completion",() =>
            Need(!HasInstance(typeof(CustodyService),"FinishSyntheticTerminalUnverified"),"terminal method"));
        Run("ordinary-boundary-no-synthetic-positive-methods",() =>
        {
            var t=typeof(ServiceOwnedAdmissionBoundary);
            Need(!HasInstance(t,"PrepareSyntheticOnly") &&
                !HasInstance(t,"CommitSyntheticDecisionOnly") &&
                !HasInstance(t,"FinishSyntheticTerminalUnverified"),"all omitted");
        });
        Run("ordinary-host-no-synthetic-marker-readback",() =>
        {
            Need(!HasInstance(typeof(CustodyService),"get_SyntheticDecisionCommits") &&
                !HasInstance(typeof(CustodyService),"get_SyntheticTooLateRevocations"),
                "test marker surface absent");
        });
        Run("ordinary-three-original-immutable-gates",() =>
        {
            Need(!ServiceGate.LiveEligible(),"service still disabled");
            Need(PendingServiceState.LegacyEffectEntryDisabled(),"legacy effect disabled");
            Need(PendingWinCredStore.NativeMutationAdmissionPending(),"WinCred disabled");
        });
        Run("ordinary-refusal-and-fault-are-only-terminal-result",() =>
        {
            using(var h=new CustodyService())
            {
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.Denied,"deny");
                Need(h.RefuseUncertainTerminalIntent()==CustodyOutcome.RecoveryRequired,"recovery");
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "sticky recovery");
            }
        });
        Run("ordinary-host-still-cannot-install-or-dispatch",() =>
        {
            var t=typeof(CustodyService);
            Need(t.GetMethod("Main",BindingFlags.Public|BindingFlags.NonPublic|
                BindingFlags.Static)==null,"no Main");
            using(var h=new CustodyService())
                Need(!h.NativeEffectEnabled && !h.AuthenticatedConsentAvailable &&
                    !h.ProductionReleaseEligible,"no effect or approval");
        });

        Console.WriteLine("P109_ORDINARY_ASSEMBLY_AUDIT_CASES_PASSED="+passed);
        Console.WriteLine("P109_ORDINARY_ASSEMBLY_AUDIT_CASES_FAILED="+failed);
        Console.WriteLine("P109_ORDINARY_SYNTHETIC_POSITIVE_METHODS_PRESENT=FALSE");
        Console.WriteLine("P109_ORDINARY_NATIVE_EFFECT_ENABLED=FALSE");
        Console.WriteLine("P109_BYOK_C1_PRODUCTION_RELEASE=HOLD");
        return passed==8 && failed==0 ? 0:1;
    }
}
