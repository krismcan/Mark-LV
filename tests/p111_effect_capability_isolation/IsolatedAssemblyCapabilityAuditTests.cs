// P111: actual compiled C1 candidate assembly capability inventory.
// This executable must be built from the strict source allowlist with
// C1_REVIEW_ISOLATED_ASSEMBLY and WITHOUT C1_SYNTHETIC_TEST.
// It must not contain legacy PendingCustodyTransaction, PendingWinCredStore,
// approval injection or a credential Win32 import. Protected journal/registry
// adapters ARE present and retain write methods: this is credential-effect
// isolation, not comprehensive read-only I/O or a production service.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || C1_SYNTHETIC_TEST
#error P111 requires exact no-synthetic review-only isolated assembly
#endif
using System;
using System.Reflection;
using System.Runtime.InteropServices;
using System.ServiceProcess;
using Nayeon.ByokC1;

internal static class P111EffectCapabilityIsolationAuditTests
{
    private static int pass,fail;
    private static void Need(bool condition,string reason)
    { if(!condition)throw new InvalidOperationException("P111 "+reason); }
    private static void Run(string name,Action test)
    {
        try{test();++pass;Console.WriteLine("PASS "+name);}
        catch(Exception e){++fail;Console.WriteLine("FAIL "+name+" "+e.GetType().Name);}
    }
    private static Type Find(string name)
    {return Assembly.GetExecutingAssembly().GetType("Nayeon.ByokC1."+name,false);}
    private static bool Has(Type t,string name)
    {return t.GetMethod(name,BindingFlags.Instance|BindingFlags.Static|
        BindingFlags.NonPublic|BindingFlags.Public|BindingFlags.DeclaredOnly)!=null;}
    public static int Main()
    {
        Run("review-assembly-excludes-legacy-transaction-type",()=>
            Need(Find("PendingCustodyTransaction")==null,"old coordinator must be absent"));
        Run("review-assembly-excludes-mutating-WinCred-adapter",()=>
            Need(Find("PendingWinCredStore")==null,"credential adapter absent"));
        Run("review-assembly-excludes-legacy-effect-state",()=>
            Need(Find("PendingServiceState")==null,"effect composition absent"));
        Run("review-assembly-excludes-injectable-approval-contract",()=>
            Need(Find("ITrustedPendingApproval")==null,"injected approval interface absent"));
        Run("review-assembly-excludes-general-effect-capability-interface",()=>
            Need(Find("IProtectedPendingState")==null,"injected effect interface absent"));
        Run("review-assembly-excludes-old-unarmed-native-mutex",()=>
            Need(Find("ServiceCustodyMutex")==null,"old unarmed mutex absent"));
        Run("review-assembly-excludes-native-credential-DllImports",()=>
        {
            foreach(var t in Assembly.GetExecutingAssembly().GetTypes())
                foreach(var m in t.GetMethods(BindingFlags.Public|BindingFlags.NonPublic|
                    BindingFlags.Instance|BindingFlags.Static|BindingFlags.DeclaredOnly))
                {
                    var attr=Attribute.GetCustomAttribute(m,typeof(DllImportAttribute))
                        as DllImportAttribute;
                    if(attr==null)continue;
                    string method=String.IsNullOrEmpty(attr.EntryPoint)?m.Name:attr.EntryPoint;
                    Need(!method.StartsWith("CredRead",StringComparison.OrdinalIgnoreCase) &&
                        !method.StartsWith("CredWrite",StringComparison.OrdinalIgnoreCase) &&
                        !method.StartsWith("CredDelete",StringComparison.OrdinalIgnoreCase) &&
                        !method.StartsWith("CredFree",StringComparison.OrdinalIgnoreCase),
                        "no Windows Credential Manager PInvoke in reviewed assembly");
                }
        });
        Run("review-assembly-excludes-all-named-credential-mutation-entrypoints",()=>
        {
            foreach(var t in Assembly.GetExecutingAssembly().GetTypes())
            {
                Need(!Has(t,"SaveOrReplace"),"SaveOrReplace absent");
                Need(!Has(t,"DeletePending"),"DeletePending absent");
                Need(!Has(t,"CredWrite") && !Has(t,"CredDelete"),"native API absent");
            }
        });
        Run("review-assembly-contains-original-disabled-service-shell",()=>
        {
            Need(typeof(ServiceBase).IsAssignableFrom(typeof(CustodyService)),
                "same candidate service base");
            Need(!Has(typeof(CustodyService),"Main"),"service cannot start as executable");
            Need(!ServiceGate.LiveEligible(),"actual installed release proof closed");
        });
        Run("candidate-effect-fence-is-unconditionally-closed",()=>
        {
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled(),
                "legacy external effect excluded");
            Need(CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "native WinCred excluded");
        });
        Run("no-synthetic-positive-effect-methods-in-review-assembly",()=>
        {
            Need(!Has(typeof(CustodyService),"PrepareSyntheticFixedEffectOnly") &&
                !Has(typeof(CustodyService),"AttemptSyntheticFixedEffectOnly") &&
                !Has(typeof(CustodyService),"CommitSyntheticDecisionOnly"),
                "no synthetic effect method in release-shape build");
            Need(!Has(typeof(ServiceOwnedAdmissionBoundary),"AttemptSyntheticFixedEffectOnly"),
                "boundary does not expose fake effect");
        });
        Run("candidate-no-authenticated-consent-or-release",()=>
        {
            using(var h=new CustodyService())
            {
                Need(!h.NativeEffectEnabled && !h.AuthenticatedConsentAvailable &&
                    !h.ProductionReleaseEligible,"all effects disabled");
            }
        });
        Run("untrusted-save-is-refused-at-original-host-surface",()=>
        {
            using(var h=new CustodyService())
                Need(h.RefusePendingOperation(LedgerOperation.Save,8,false)==
                    CustodyOutcome.Denied,"untrusted save denial");
        });
        Run("untrusted-acknowledged-delete-refused",()=>
        {
            using(var h=new CustodyService())
                Need(h.RefusePendingOperation(LedgerOperation.Delete,0,true)==
                    CustodyOutcome.Denied,"untrusted delete denial");
        });
        Run("untrusted-null-bound-claim-refused",()=>
        {
            using(var h=new CustodyService())
                Need(h.RefuseBoundPendingOperation(null)==CustodyOutcome.Denied,
                    "untrusted identity cannot mint consent");
        });
        Run("untrusted-host-handler-always-unavailable",()=>
            Need(ServiceGate.HandleUntrustedRequest("synthetic")==ServiceGate.Unavailable,
                "original IPC entry not enabled"));
        Run("candidate-effect-refusal-followed-by-fault-is-sticky",()=>
        {
            using(var h=new CustodyService())
            {
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.Denied,
                    "refusal");
                Need(h.RefuseUncertainTerminalIntent()==CustodyOutcome.RecoveryRequired,
                    "unknown intent");
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "sticky recovery");
            }
        });
        Run("native-J2-observation-denies-when-service-uninstalled",()=>
        {
            using(var h=new CustodyService())
            {
                var v=h.ObserveNativeJ2CustodyReadOnly();
                Need(v.Kind==NativeJ2ReadOnlyKind.Unavailable,
                    "structural uninstalled preflight cannot access protected OS custody");
                Need(!v.AuthenticatedConsent && !v.PendingPresenceVerified &&
                    !v.DurableIndependentWitnessVerified && !v.CanDispatchNativeEffect,
                    "no read-only observation can grant effect");
            }
        });
        Run("P49-protected-journal-append-capability-still-present-and-not-executed",()=>
            Need(Has(typeof(CustodyJournalFile),"Append"),
                "residual journal mutation capability explicitly in review scope"));
        Run("P49-protected-registry-mutation-capability-still-present-and-not-executed",()=>
            Need(Has(typeof(CustodyRegistryAnchor),"WriteAnchor"),
                "residual registry mutation capability explicitly in review scope"));
        Run("audit-does-not-create-a-trusted-consent-issuer",()=>
            Need(Find("TrustedConsentIssuer")==null && Find("OneUseConsentIssuer")==null,
                "no invented authority in review-only assembly"));

        Console.WriteLine("P111_ISOLATED_CREDENTIAL_CAPABILITY_AUDIT_PASSED="+pass);
        Console.WriteLine("P111_ISOLATED_CREDENTIAL_CAPABILITY_AUDIT_FAILED="+fail);
        Console.WriteLine("P111_OLD_PENDING_TRANSACTION_IN_ASSEMBLY=FALSE");
        Console.WriteLine("P111_OLD_PENDING_WINCRED_ADAPTER_IN_ASSEMBLY=FALSE");
        Console.WriteLine("P111_PROTECTED_JOURNAL_REGISTRY_WRITE_METHODS_STILL_PRESENT=TRUE");
        Console.WriteLine("P111_TRUSTED_USER_CONSENT=NOT_IMPLEMENTED");
        Console.WriteLine("P111_NATIVE_CREDENTIAL_EFFECTS=NONE");
        Console.WriteLine("P111_PRODUCTION_RELEASE=HOLD");
        return pass==21 && fail==0?0:1;
    }
}
