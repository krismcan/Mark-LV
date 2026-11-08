// P110 ordinary release-intended source audit; NO synthetic feature define.
// The real compiled candidate assembly must expose ZERO synthetic fake-effect
// methods or native credential effects. No local credential access.
#if C1_SYNTHETIC_TEST
#error Ordinary C1 production-boundary audit cannot have a synthetic test define
#endif
using System;
using System.Reflection;
using Nayeon.ByokC1;
internal static class P110OrdinaryEffectSurfaceAuditTests
{
    private static int pass,fail;
    private static void Need(bool b,string message)
    {if(!b)throw new InvalidOperationException("P110 ordinary "+message);}
    private static void Run(string title,Action a)
    {
        try{a();++pass;Console.WriteLine("PASS "+title);}
        catch(Exception e){++fail;Console.WriteLine("FAIL "+title+" "+e.GetType().Name);}
    }
    private static bool Has(Type t,string name)
    {return t.GetMethod(name,BindingFlags.Public|BindingFlags.NonPublic|
        BindingFlags.Instance|BindingFlags.DeclaredOnly)!=null;}
    public static int Main()
    {
        Run("ordinary-host-no-test-effect-preparation",() =>
            Need(!Has(typeof(CustodyService),"PrepareSyntheticFixedEffectOnly"),"prepare absent"));
        Run("ordinary-host-no-fixed-fake-effect-attempt",() =>
            Need(!Has(typeof(CustodyService),"AttemptSyntheticFixedEffectOnly"),"effect absent"));
        Run("ordinary-boundary-no-test-effect-preparation",() =>
            Need(!Has(typeof(ServiceOwnedAdmissionBoundary),"PrepareSyntheticFixedEffectOnly"),"prepare absent"));
        Run("ordinary-boundary-no-fixed-fake-effect-attempt",() =>
            Need(!Has(typeof(ServiceOwnedAdmissionBoundary),"AttemptSyntheticFixedEffectOnly"),"effect absent"));
        Run("ordinary-host-no-positive-P109-commit",() =>
            Need(!Has(typeof(CustodyService),"CommitSyntheticDecisionOnly"),"commit absent"));
        Run("ordinary-host-no-effect-attempt-or-unknown-counters",() =>
        {
            Need(!Has(typeof(CustodyService),"get_SyntheticEffectAttempts"),"attempt counter absent");
            Need(!Has(typeof(CustodyService),"get_SyntheticUnknownEffectOutcomes"),"unknown counter absent");
        });
        Run("ordinary-effect-and-legacy-gates-permanently-closed",() =>
        {
            Need(!ServiceGate.LiveEligible(),"service gate false");
            Need(PendingServiceState.LegacyEffectEntryDisabled(),"legacy effect disabled");
            Need(PendingWinCredStore.NativeMutationAdmissionPending(),"WinCred disabled");
            using(var h=new CustodyService())
                Need(!h.NativeEffectEnabled && !h.AuthenticatedConsentAvailable &&
                    !h.ProductionReleaseEligible,"candidate has no live effect");
        });
        Run("ordinary-host-has-only-refusal-and-no-Main",() =>
        {
            Need(typeof(CustodyService).GetMethod("Main",BindingFlags.Public|
                BindingFlags.NonPublic|BindingFlags.Static)==null,"no Main");
            using(var h=new CustodyService())
            {
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.Denied,"refuse");
                Need(h.RefuseUncertainTerminalIntent()==CustodyOutcome.RecoveryRequired,
                    "uncertain intent recovery");
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "sticky recovery");
            }
        });
        Console.WriteLine("P110_ORDINARY_NO_FAKE_EFFECT_METHODS_CASES_PASSED="+pass);
        Console.WriteLine("P110_ORDINARY_NO_FAKE_EFFECT_METHODS_CASES_FAILED="+fail);
        Console.WriteLine("P110_RELEASE_INTENDED_ASSEMBLY_TEST_ONLY_EFFECTS_ABSENT=TRUE");
        Console.WriteLine("P110_BYOK_C1_RELEASE=HOLD");
        return pass==8 && fail==0?0:1;
    }
}
