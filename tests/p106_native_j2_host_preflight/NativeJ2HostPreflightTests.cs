// P106: original-source Windows C# candidate-host tests of real J2 protected
// read-only preflight, service-owned stop/fault and permanent no-effect rules.
// All 10 original P49 dependency units are linked unchanged; original host
// is replaced by P101/P106 disabled candidate. No service Main/install,
// WinCred read/write, actual key, provider, HKLM mutation or synthetic unlock.
using System;
using System.Reflection;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1;

internal static class P106NativeJ2HostPreflightTests
{
    private static int passed, failed;
    private static void Need(bool yes, string why)
    {
        if (!yes) throw new InvalidOperationException("P106 test: " + why);
    }
    private static void Run(string name, Action action)
    {
        try { action(); ++passed; Console.WriteLine("PASS " + name); }
        catch (Exception ex) { ++failed; Console.WriteLine("FAIL " + name + " " + ex.GetType().Name); }
    }
    private static void NoAuthority(NativeJ2ReadOnlyResult result)
    {
        Need(result != null, "non-null result");
        Need(!result.AuthenticatedConsent, "no consent");
        Need(!result.PendingPresenceVerified, "no WinCred read");
        Need(!result.DurableIndependentWitnessVerified, "no witness");
        Need(!result.CanDispatchNativeEffect, "no effects");
        Need(!result.RetryAllowed, "no retry");
        Need(!result.ProductionReleaseEligible, "no release");
    }
    private static void Stop(CustodyService service)
    {
        typeof(CustodyService).GetMethod("OnStop",
            BindingFlags.Instance | BindingFlags.NonPublic).Invoke(service,null);
    }
    private static NativeJ2ReadOnlyResult HostObservation()
    {
        using (var h=new CustodyService())
        {
            return h.ObserveNativeJ2CustodyReadOnly();
        }
    }
    public static int Main()
    {
        Run("original-native-three-mutation-deny-gates-intact",() =>
        {
            Need(!ServiceGate.LiveEligible(), "service disabled");
            Need(PendingServiceState.LegacyEffectEntryDisabled(), "legacy effect disabled");
            Need(PendingWinCredStore.NativeMutationAdmissionPending(), "WinCred disabled");
        });
        Run("direct-real-os-protected-preflight-refuses-service",() =>
        {
            var result=NativeJ2ProtectedReadOnlyPreflight.ObserveInstalledService();
            Need(result.Kind==NativeJ2ReadOnlyKind.Unavailable, "no released service");
            NoAuthority(result);
        });
        Run("candidate-host-readonly-preflight-not-live",() =>
        {
            var result=HostObservation();
            Need(result.Kind==NativeJ2ReadOnlyKind.Unavailable, "host unavailable");
            NoAuthority(result);
        });
        Run("candidate-has-no-installable-main",() =>
        {
            Need(typeof(CustodyService).GetMethod("Main",
                BindingFlags.NonPublic|BindingFlags.Public|BindingFlags.Static)==null,
                "no Main");
        });
        Run("candidate-onstart-always-refuses",() =>
        {
            using(var h=new CustodyService())
            {
                bool refused=false;
                try {
                    typeof(CustodyService).GetMethod("OnStart",
                        BindingFlags.NonPublic|BindingFlags.Instance)
                        .Invoke(h,new object[] { new string[0] });
                } catch(TargetInvocationException e) {
                    refused=e.InnerException is InvalidOperationException;
                }
                Need(refused,"startup refuses");
                Need(!h.ProductionReleaseEligible && !h.NativeEffectEnabled,"no effect");
            }
        });
        Run("structural-initial-only-is-not-authority",() =>
        {
            var r=NativeJ2ReadOnlyResult.Structural(LedgerPhase.Initial);
            Need(r.Kind==NativeJ2ReadOnlyKind.StructuralInitial,"initial only");
            NoAuthority(r);
        });
        Run("inflight-is-always-recovery-required",() =>
        {
            var r=NativeJ2ReadOnlyResult.Structural(LedgerPhase.InFlight);
            Need(r.Kind==NativeJ2ReadOnlyKind.RecoveryRequired,"inflight recovery");
            NoAuthority(r);
        });
        Run("structural-stored-only-is-not-key-verification",() =>
        {
            var r=NativeJ2ReadOnlyResult.Structural(LedgerPhase.CommittedUnverified);
            Need(r.Kind==NativeJ2ReadOnlyKind.JournalClaimsStoredUnverified,"unverified");
            NoAuthority(r);
        });
        Run("structural-deleted-only-is-not-key-verification",() =>
        {
            var r=NativeJ2ReadOnlyResult.Structural(LedgerPhase.CommittedAbsent);
            Need(r.Kind==NativeJ2ReadOnlyKind.JournalClaimsAbsentUnverified,"absent unverified");
            NoAuthority(r);
        });
        Run("unknown-ledger-phase-requires-recovery",() =>
        {
            var r=NativeJ2ReadOnlyResult.Structural((LedgerPhase)1234);
            Need(r.Kind==NativeJ2ReadOnlyKind.RecoveryRequired,"unknown phase");
            NoAuthority(r);
        });
        Run("all-structural-statuses-remain-non-authority",() =>
        {
            foreach(LedgerPhase p in new [] { LedgerPhase.Initial,
                LedgerPhase.InFlight,LedgerPhase.CommittedUnverified,
                LedgerPhase.CommittedAbsent })
                NoAuthority(NativeJ2ReadOnlyResult.Structural(p));
        });
        Run("result-identity-no-secret-values",() =>
        {
            FieldInfo[] fields=typeof(NativeJ2ReadOnlyResult).GetFields(
                BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance);
            Need(fields.Length==1 && fields[0].IsInitOnly &&
                fields[0].FieldType==typeof(NativeJ2ReadOnlyKind),"immutable nonsecret status");
            Need(!NativeJ2ReadOnlyResult.Recovery().ToString().Contains(
                new string('a',32)),"no request/secret log");
        });
        Run("revoked-host-cannot-probe",() =>
        {
            using(var h=new CustodyService())
            {
                h.RevokePendingAdmission();
                var r=h.ObserveNativeJ2CustodyReadOnly();
                Need(h.PendingAdmissionRevoked && r.Kind==
                    NativeJ2ReadOnlyKind.Unavailable,"revocation");
                NoAuthority(r);
            }
        });
        Run("stopped-host-cannot-probe",() =>
        {
            using(var h=new CustodyService())
            {
                Stop(h);
                var r=h.ObserveNativeJ2CustodyReadOnly();
                Need(h.PendingAdmissionStopped && r.Kind==
                    NativeJ2ReadOnlyKind.Unavailable,"stopped");
                NoAuthority(r);
            }
        });
        Run("faulted-host-report-is-recovery-required",() =>
        {
            using(var h=new CustodyService())
            {
                h.FaultPendingAdmission();
                var r=h.ObserveNativeJ2CustodyReadOnly();
                Need(h.PendingAdmissionFaulted && r.Kind==
                    NativeJ2ReadOnlyKind.RecoveryRequired,"fault");
                NoAuthority(r);
            }
        });
        Run("fault-then-revoke-still-recovery",() =>
        {
            using(var h=new CustodyService())
            {
                h.FaultPendingAdmission();h.RevokePendingAdmission();
                Need(h.ObserveNativeJ2CustodyReadOnly().Kind==
                    NativeJ2ReadOnlyKind.RecoveryRequired,"fault remains");
            }
        });
        Run("stop-then-fault-still-recovery",() =>
        {
            using(var h=new CustodyService())
            {
                Stop(h);h.FaultPendingAdmission();
                Need(h.ObserveNativeJ2CustodyReadOnly().Kind==
                    NativeJ2ReadOnlyKind.RecoveryRequired,"stop can't clear fault");
            }
        });
        Run("repeated-probes-never-track-replay-as-consent",() =>
        {
            using(var h=new CustodyService())
            {
                for(int i=0;i<150;i++)
                {
                    var r=h.ObserveNativeJ2CustodyReadOnly();
                    Need(r.Kind==NativeJ2ReadOnlyKind.Unavailable,"no READY");
                    NoAuthority(r);
                }
                Need(h.TrackedNonSecretRequestCount==0,"no request issuance");
            }
        });
        Run("eight-native-threads-concurrent-stop-and-probe",() =>
        {
            using(var h=new CustodyService())
            {
                int unexpected=0;
                var threads=new Thread[8];
                for(int i=0;i<8;i++)threads[i]=new Thread(() =>
                {
                    try {
                        for(int j=0;j<75;j++)
                        {
                            var r=h.ObserveNativeJ2CustodyReadOnly();
                            if(r.Kind!=NativeJ2ReadOnlyKind.Unavailable || r.CanDispatchNativeEffect)
                                Interlocked.Increment(ref unexpected);
                        }
                    } catch(Exception) { Interlocked.Increment(ref unexpected); }
                });
                foreach(var worker in threads) worker.Start();
                Stop(h);
                foreach(var worker in threads)
                    Need(worker.Join(5000),"workers joined");
                Need(unexpected==0 && h.PendingAdmissionStopped,"all probes denied");
            }
        });
        Run("actual-native-j2-data-does-not-create-approval",() =>
        {
            string ledger=CustodyLedger.CreateInitial(new string('c',32));
            string anchor=CustodyLedger.Anchor(ledger);
            Need(CustodyLedger.Verify(ledger,anchor)==LedgerPhase.Initial,"genuine J2 codec");
            // There is deliberately no journal/anchor parameter on host:
            var m=typeof(CustodyService).GetMethod(
                "ObserveNativeJ2CustodyReadOnly",
                BindingFlags.Instance|BindingFlags.NonPublic);
            Need(m!=null && m.GetParameters().Length==0,"no caller-provided J2 data");
            Need(HostObservation().Kind==NativeJ2ReadOnlyKind.Unavailable,
                "no consent from structurally valid data");
        });
        Run("host-retains-original-untrusted-operation-denials",() =>
        {
            using(var h=new CustodyService())
            {
                Need(h.RefusePendingOperation(LedgerOperation.Save,32,false)==
                    CustodyOutcome.Denied,"original denial");
                Need(!h.ProductionReleaseEligible && !h.NativeEffectEnabled &&
                    !h.AuthenticatedConsentAvailable,"all no effect");
            }
        });
        Run("real-local-system-registry-guard-is-non-bypassable",() =>
        {
            var id=WindowsIdentity.GetCurrent();
            Need(id!=null && id.User!=null &&
                !id.User.IsWellKnown(WellKnownSidType.LocalSystemSid),
                "unprivileged Windows test runner required");
            bool blocked=false;
            try { new CustodyRegistryAnchor().ReadAnchor(); }
            catch(LedgerBlocked) { blocked=true; }
            Need(blocked,"actual original native LocalSystem-only registry guard");
        });
        Run("preflight-never-claims-native-read-or-mutation",() =>
        {
            var r=NativeJ2ProtectedReadOnlyPreflight.ObserveInstalledService();
            NoAuthority(r);
            Need(!ServiceGate.LiveEligible() &&
                PendingWinCredStore.NativeMutationAdmissionPending(),
                "original deny still in effect");
        });

        Console.WriteLine("P106_REAL_NATIVE_SERVICE_J2_PREFLIGHT_TESTS_PASSED="+passed);
        Console.WriteLine("P106_REAL_NATIVE_SERVICE_J2_PREFLIGHT_TESTS_FAILED="+failed);
        Console.WriteLine("P106_REAL_LOCAL_SYSTEM_EFFECTS=NONE");
        Console.WriteLine("P106_G3_STRUCTURAL_STATUS_NOT_AUTHORITY=TRUE");
        Console.WriteLine("P106_ORIGINAL_P61_RACE=OPEN");
        Console.WriteLine("P106_G0_G1_G2_G3_G4_G5_G6=HOLD");
        Console.WriteLine("P106_PRODUCTION_RELEASE=HOLD");
        return passed==23 && failed==0 ? 0:1;
    }
}
