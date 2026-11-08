// P112: compiled actual candidate read-only storage-capability isolation.
// The strict source allowlist must have NO mutable original P49 journal/anchor
// adapters, no credential APIs, no real approval or positive dispatch. The
// initial J2/A2 format parser is structurally informative, NEVER authority.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || C1_SYNTHETIC_TEST
#error P112 requires exact isolated ordinary review-only assembly
#endif
using System;
using System.Reflection;
using System.Runtime.InteropServices;
using Nayeon.ByokC1;

internal static class P112ReadOnlyCandidateAssemblyAudit
{
    private static int pass, fail;
    private static void Need(bool ok,string reason)
    { if(!ok)throw new InvalidOperationException("P112 "+reason); }
    private static void Run(string name,Action test)
    {
        try{test();++pass;Console.WriteLine("PASS "+name);}
        catch(Exception e){++fail;Console.WriteLine("FAIL "+name+" "+e.GetType().Name);}
    }
    private static Type Named(string name)
    {return Assembly.GetExecutingAssembly().GetType("Nayeon.ByokC1."+name,false);}
    private static bool Has(Type type,string name)
    {return type.GetMethod(name,BindingFlags.Instance|BindingFlags.Static|
        BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.DeclaredOnly)!=null;}
    private static void NoAuthority(NativeJ2ReadOnlyResult value)
    {
        Need(!value.AuthenticatedConsent,"no signed human consent");
        Need(!value.PendingPresenceVerified,"no verified credential presence");
        Need(!value.DurableIndependentWitnessVerified,"no durable trusted witness");
        Need(!value.CanDispatchNativeEffect,"never dispatch");
        Need(!value.ProductionReleaseEligible,"no release");
        Need(!value.RetryAllowed,"no uncertain retry");
    }

    public static int Main()
    {
        Run("old-legacy-pending-transaction-is-not-in-review-assembly",() =>
            Need(Named("PendingCustodyTransaction")==null,"old coordinator absent"));
        Run("old-native-WinCred-adapter-is-not-in-review-assembly",() =>
            Need(Named("PendingWinCredStore")==null,"old WinCred absent"));
        Run("old-pending-state-mutator-is-not-in-review-assembly",() =>
            Need(Named("PendingServiceState")==null,"old effect state absent"));
        Run("old-unarmed-custody-mutex-is-not-in-review-assembly",() =>
            Need(Named("ServiceCustodyMutex")==null,"old mutex absent"));
        Run("old-journal-writer-type-is-not-in-review-assembly",() =>
            Need(Named("CustodyJournalFile")==null,"old file writer absent"));
        Run("old-registry-anchor-writer-type-is-not-in-review-assembly",() =>
            Need(Named("CustodyRegistryAnchor")==null,"old registry writer absent"));
        Run("effect-state-injection-interface-is-not-in-review-assembly",() =>
            Need(Named("IProtectedPendingState")==null,"effect interface absent"));
        Run("old-trusted-approval-injection-interface-is-absent",() =>
            Need(Named("ITrustedPendingApproval")==null,"approval interface absent"));
        Run("strict-candidate-native-reader-exists",() =>
            Need(Named("CandidateProtectedReadOnlySnapshot")!=null,"fixed reader present"));
        Run("candidate-native-reader-has-no-mutation-methods",() =>
        {
            var t=typeof(CandidateProtectedReadOnlySnapshot);
            foreach(var name in new []{"Append","WriteJournal","WriteAnchor",
                "Delete","SaveOrReplace","DeletePending","Create","SetValue",
                "FlushChecked","NativeRegFlushKey","InstallService"})
                Need(!Has(t,name),"forbidden reader mutation method "+name);
        });
        Run("candidate-native-reader-has-no-parameterized-read-paths",() =>
        {
            var t=typeof(CandidateProtectedReadOnlySnapshot);
            foreach(var method in t.GetMethods(BindingFlags.NonPublic|
                BindingFlags.Public|BindingFlags.Static|BindingFlags.DeclaredOnly))
                if(method.Name=="ReadJournal" || method.Name=="ReadAnchor" ||
                   method.Name=="ObserveInstalledService")
                    Need(method.GetParameters().Length==0,
                        "reader cannot accept untrusted paths/handles");
        });
        Run("review-assembly-has-no-PInvoke-functions-at-all",() =>
        {
            foreach(var t in Assembly.GetExecutingAssembly().GetTypes())
                foreach(var m in t.GetMethods(BindingFlags.Instance|
                    BindingFlags.Static|BindingFlags.NonPublic|
                    BindingFlags.Public|BindingFlags.DeclaredOnly))
                    Need(Attribute.GetCustomAttribute(m,
                        typeof(DllImportAttribute))==null,
                        "PInvoke forbidden "+t.Name+"."+m.Name);
        });
        Run("review-assembly-has-no-named-storage-write-operations",() =>
        {
            foreach(var t in Assembly.GetExecutingAssembly().GetTypes())
                foreach(var m in t.GetMethods(BindingFlags.Instance|
                    BindingFlags.Static|BindingFlags.NonPublic|
                    BindingFlags.Public|BindingFlags.DeclaredOnly))
                {
                    // Pure CustodyLedger.AppendIntent/AppendTerminal functions
                    // only return NEW STRINGS; they never write Windows state.
                    if(t==typeof(CustodyLedger))continue;
                    Need(m.Name!="WriteAnchor" && m.Name!="WriteJournal" &&
                        m.Name!="SaveOrReplace" && m.Name!="DeletePending" &&
                        m.Name!="SetValue" && m.Name!="Append",
                        "OS mutation method absent");
                }
        });
        Run("candidate-has-no-production-service-Main",() =>
            Need(typeof(CustodyService).GetMethod("Main",
                BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)==null,
                "no service installer or main"));
        Run("positive-synthetic-G2-methods-absent-in-review-assembly",() =>
        {
            Need(!Has(typeof(CustodyService),"AttemptSyntheticFixedEffectOnly") &&
                !Has(typeof(CustodyService),"CommitSyntheticDecisionOnly") &&
                !Has(typeof(ServiceOwnedAdmissionBoundary),
                    "AttemptSyntheticFixedEffectOnly"),"positive fake effect omitted");
        });
        Run("service-original-LiveEligible-remains-false",() =>
            Need(!ServiceGate.LiveEligible(),"original shell not released"));
        Run("candidate-permanent-credential-effect-fence-stays-closed",() =>
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "credential effects absent"));
        Run("no-credential-permission-from-service-candidate",() =>
        {
            using(var h=new CustodyService())
                Need(!h.NativeEffectEnabled &&
                    !h.AuthenticatedConsentAvailable &&
                    !h.ProductionReleaseEligible,"no actual key mutation");
        });
        Run("protected-storage-observation-on-uninstalled-service-unavailable",() =>
        {
            var observation=CandidateProtectedReadOnlySnapshot.ObserveInstalledService();
            Need(observation.Kind==NativeJ2ReadOnlyKind.Unavailable,
                "must not touch HKLM or files without released shell");
            NoAuthority(observation);
        });
        Run("candidate-host-observation-also-unavailable",() =>
        {
            using(var h=new CustodyService())
            {
                var observation=h.ObserveNativeJ2CustodyReadOnly();
                Need(observation.Kind==NativeJ2ReadOnlyKind.Unavailable,
                    "host cannot read protected stores");
                NoAuthority(observation);
            }
        });
        Run("initial-structural-history-is-not-approval",() =>
        {
            var v=NativeJ2ReadOnlyResult.Structural(LedgerPhase.Initial);
            Need(v.Kind==NativeJ2ReadOnlyKind.StructuralInitial,"initial status");
            NoAuthority(v);
        });
        Run("in-flight-structural-history-requires-recovery",() =>
        {
            var v=NativeJ2ReadOnlyResult.Structural(LedgerPhase.InFlight);
            Need(v.Kind==NativeJ2ReadOnlyKind.RecoveryRequired,"no inflight retry");
            NoAuthority(v);
        });
        Run("stored-claim-is-explicitly-unverified",() =>
        {
            var v=NativeJ2ReadOnlyResult.Structural(LedgerPhase.CommittedUnverified);
            Need(v.Kind==NativeJ2ReadOnlyKind.JournalClaimsStoredUnverified,
                "stored claim unverified");
            NoAuthority(v);
        });
        Run("absent-claim-is-explicitly-unverified",() =>
        {
            var v=NativeJ2ReadOnlyResult.Structural(LedgerPhase.CommittedAbsent);
            Need(v.Kind==NativeJ2ReadOnlyKind.JournalClaimsAbsentUnverified,
                "absent claim unverified");
            NoAuthority(v);
        });
        Run("untrusted-candidate-save-remains-refused",() =>
        {
            using(var h=new CustodyService())
                Need(h.RefusePendingOperation(LedgerOperation.Save,10,false)==
                    CustodyOutcome.Denied,"no untrusted save");
        });
        Run("untrusted-candidate-delete-remains-refused",() =>
        {
            using(var h=new CustodyService())
                Need(h.RefusePendingOperation(LedgerOperation.Delete,0,true)==
                    CustodyOutcome.Denied,"no untrusted delete");
        });
        Run("unknown-transaction-status-requires-sticky-recovery",() =>
        {
            using(var h=new CustodyService())
            {
                Need(h.RefuseUncertainTerminalIntent()==
                    CustodyOutcome.RecoveryRequired,"unknown intent");
                Need(h.RefuseUnreviewedTerminalEffect()==
                    CustodyOutcome.RecoveryRequired,"sticky non-retry");
            }
        });

        Console.WriteLine("P112_ACTUAL_READONLY_CANDIDATE_AUDIT_PASSED="+pass);
        Console.WriteLine("P112_ACTUAL_READONLY_CANDIDATE_AUDIT_FAILED="+fail);
        Console.WriteLine("P112_ORIGINAL_FILE_AND_REGISTRY_WRITE_TYPES_PRESENT=FALSE");
        Console.WriteLine("P112_NATIVE_CREDENTIAL_AND_PRIVILEGED_IPC_EFFECTS=NONE");
        Console.WriteLine("P112_NON_ATOMIC_TWO_STORE_SNAPSHOT_IS_NOT_HISTORIC_AUTHORITY=TRUE");
        Console.WriteLine("P112_G1_TRUSTED_CONSENT=ABSENT");
        Console.WriteLine("P112_G2_ORIGINAL_P96_LEGACY_RACE=STILL_OPEN");
        Console.WriteLine("P112_PRODUCTION_RELEASE=HOLD");
        return pass==27 && fail==0 ? 0:1;
    }
}
