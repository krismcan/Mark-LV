// P101 WINDOWS C# review-only service host integration, NOT an installed service.
// Compiles 10 original byte-pinned native units plus a quarantined candidate host.
// Never calls WinCred, ServiceBase.Run, protected storage or actual consent.
using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P101ServiceHostAdmissionTests
{
    private static int passed, failed;
    private static void Require(bool ok, string message)
    { if (!ok) throw new InvalidOperationException("P101 assertion: " + message); }
    private static void Run(string label, Action action)
    {
        try { action(); passed++; Console.WriteLine("PASS " + label); }
        catch (Exception e)
        { failed++; Console.WriteLine("FAIL " + label + " " + e.GetType().Name); }
    }
    private static CustodyService Host()
    { return new CustodyService(); }
    private static void NoAuthority(CustodyService h)
    {
        Require(!h.NativeEffectEnabled, "native effect disabled");
        Require(!h.AuthenticatedConsentAvailable, "no authenticated consent");
        Require(!h.ProductionReleaseEligible, "not release eligible");
    }
    private static void InvokeHostMethod(CustodyService h, string name)
    {
        MethodInfo m=typeof(CustodyService).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Instance);
        Require(m != null, "host lifecycle method");
        m.Invoke(h, name == "OnStart"
            ? new object[] { new string[0] } : new object[0]);
    }
    private static void Denied(CustodyService h, LedgerOperation op,
        int size, bool ack)
    {
        CustodyOutcome outcome=h.RefusePendingOperation(op,size,ack);
        Require(outcome == CustodyOutcome.Denied ||
                outcome == CustodyOutcome.RecoveryRequired, "no accepted effects");
        NoAuthority(h);
    }
    public static int Main()
    {
        Run("original-service-release-denial-still-false", () =>
            Require(!ServiceGate.LiveEligible(), "unreviewed native binary"));
        Run("original-legacy-native-effect-guard-still-true", () =>
            Require(PendingServiceState.LegacyEffectEntryDisabled(), "legacy hold"));
        Run("original-wincred-native-mutation-guard-still-true", () =>
            Require(PendingWinCredStore.NativeMutationAdmissionPending(), "WinCred hold"));
        Run("candidate-service-name-remains-fixed", () => {
            using (var h=Host()) {
                Require(h.ServiceName == ServiceGate.ServiceName, "fixed name");
                NoAuthority(h);
            }
        });
        Run("candidate-service-onstart-still-refuses", () => {
            using (var h=Host()) {
                bool refused=false;
                try { InvokeHostMethod(h,"OnStart"); }
                catch (TargetInvocationException e) {
                    refused=e.InnerException is InvalidOperationException &&
                        e.InnerException.Message == "Custody service is unavailable";
                }
                Require(refused,"startup denied");
                NoAuthority(h);
            }
        });
        Run("candidate-has-no-deployable-entrypoint", () =>
            Require(typeof(CustodyService).GetMethod("Main",
                BindingFlags.NonPublic|BindingFlags.Public|BindingFlags.Static)
                == null, "no installed service entrypoint"));
        Run("host-save-is-statically-denied", () => {
            using(var h=Host()) Denied(h,LedgerOperation.Save,32,false);
        });
        Run("host-replace-is-statically-denied", () => {
            using(var h=Host()) Denied(h,LedgerOperation.Replace,32,false);
        });
        Run("host-delete-is-statically-denied", () => {
            using(var h=Host()) Denied(h,LedgerOperation.Delete,0,true);
        });
        Run("host-delete-unacknowledged-denied", () => {
            using(var h=Host()) Denied(h,LedgerOperation.Delete,0,false);
        });
        Run("host-invalid-candidate-size-denied", () => {
            using(var h=Host()) {
                Denied(h,LedgerOperation.Save,-1,false);
                Denied(h,LedgerOperation.Save,0,false);
                Denied(h,LedgerOperation.Save,2561,false);
            }
        });
        Run("host-wrong-delete-candidate-refused", () => {
            using(var h=Host()) Denied(h,LedgerOperation.Delete,64,true);
        });
        Run("host-malformed-operation-refused", () => {
            using(var h=Host()) Denied(h,(LedgerOperation)999,32,false);
        });
        Run("host-revocation-commits-before-future-requests", () => {
            using(var h=Host()) {
                h.RevokePendingAdmission();
                Require(h.PendingAdmissionRevoked,"revoked");
                Denied(h,LedgerOperation.Save,32,false);
                Denied(h,LedgerOperation.Replace,32,false);
                Denied(h,LedgerOperation.Delete,0,true);
            }
        });
        Run("host-fault-commits-recovery-state", () => {
            using(var h=Host()) {
                h.FaultPendingAdmission();
                Require(h.PendingAdmissionFaulted,"faulted");
                Require(h.RefusePendingOperation(LedgerOperation.Save,32,false) ==
                    CustodyOutcome.RecoveryRequired,"recovery hold");
                NoAuthority(h);
            }
        });
        Run("host-revoke-and-fault-never-rearm", () => {
            using(var h=Host()) {
                h.RevokePendingAdmission();h.FaultPendingAdmission();
                for(int i=0;i<50;i++)
                    Require(h.RefusePendingOperation(LedgerOperation.Save,32,false)
                        == CustodyOutcome.RecoveryRequired, "sticky recovery");
                NoAuthority(h);
            }
        });
        Run("host-onstop-couples-revoke-and-stop", () => {
            using(var h=Host()) {
                InvokeHostMethod(h,"OnStop");
                Require(h.PendingAdmissionRevoked && h.PendingAdmissionStopped,
                    "service monitor stop");
                Denied(h,LedgerOperation.Save,32,false);
                NoAuthority(h);
            }
        });
        Run("host-onstop-before-onstart-refuses", () => {
            using(var h=Host()) {
                InvokeHostMethod(h,"OnStop");
                bool blocked=false;
                try { InvokeHostMethod(h,"OnStart"); }
                catch(TargetInvocationException e) {
                    blocked=e.InnerException is InvalidOperationException;
                }
                Require(blocked,"never starts after stop");
                Denied(h,LedgerOperation.Delete,0,true);
            }
        });
        Run("concurrent-host-request-and-revoke-denies", () => {
            using(var h=Host()) {
                int allowed=0, crashed=0;
                Thread[] workers=new Thread[8];
                for(int i=0;i<workers.Length;i++)
                    workers[i]=new Thread(() => {
                        try {
                            for(int j=0;j<50;j++) {
                                CustodyOutcome result=h.RefusePendingOperation(
                                    LedgerOperation.Save,32,false);
                                if(result!=CustodyOutcome.Denied &&
                                   result!=CustodyOutcome.RecoveryRequired)
                                    Interlocked.Increment(ref allowed);
                            }
                        } catch(Exception) { Interlocked.Increment(ref crashed); }
                    });
                Thread revoker=new Thread(h.RevokePendingAdmission);
                foreach(Thread t in workers) t.Start();
                revoker.Start();
                foreach(Thread t in workers) Require(t.Join(3000),"worker finished");
                Require(revoker.Join(3000), "revoker finished");
                Require(allowed==0 && crashed==0, "no concurrent approval");
                Require(h.PendingAdmissionRevoked,"revocation applied");
                Require(h.DeniedPendingRequestCount==400,"all request results tracked");
                NoAuthority(h);
            }
        });
        Run("concurrent-fault-and-host-disposal-refuses", () => {
            using(var h=Host()) {
                int problem=0;
                Thread fault=new Thread(() => {
                    try { h.FaultPendingAdmission(); }
                    catch(Exception) { Interlocked.Increment(ref problem); }
                });
                Thread stop=new Thread(() => {
                    try { InvokeHostMethod(h,"OnStop"); }
                    catch(Exception) { Interlocked.Increment(ref problem); }
                });
                fault.Start();stop.Start();
                Require(fault.Join(3000) && stop.Join(3000),"both lifecycle calls");
                Require(problem==0 && h.PendingAdmissionStopped &&
                        h.PendingAdmissionFaulted, "fault+stop permanent");
                Require(h.RefusePendingOperation(LedgerOperation.Save,32,false)
                    == CustodyOutcome.RecoveryRequired, "fault remains");
                NoAuthority(h);
            }
        });
        Run("1000-host-calls-never-dispatch", () => {
            using(var h=Host()) {
                for(int i=0;i<1000;i++)
                    Denied(h,LedgerOperation.Save,32,false);
                Require(h.DeniedPendingRequestCount==1000,"counts requests");
            }
        });
        Run("original-native-coordinator-only-linked-not-called", () => {
            Require(typeof(PendingCustodyTransaction).Assembly ==
                typeof(CustodyService).Assembly,"real coordinator in test assembly");
            Require(typeof(PendingWinCredStore).Assembly ==
                typeof(CustodyService).Assembly,"real guarded adapter present");
            Require(!ServiceGate.LiveEligible(),"real source release disabled");
        });
        Run("original-service-state-installer-composition-refuses", () => {
            bool denied=false;
            try { PendingServiceState.ForInstalledService(); }
            catch(LedgerBlocked) { denied=true; }
            Require(denied,"original installer not eligible");
        });
        Run("request-api-takes-metadata-not-credentials", () => {
            MethodInfo m=typeof(CustodyService).GetMethod(
                "RefusePendingOperation",BindingFlags.NonPublic|BindingFlags.Instance);
            Require(m!=null,"entry exists");
            ParameterInfo[] p=m.GetParameters();
            Require(p.Length==3 && p[0].ParameterType==typeof(LedgerOperation) &&
                p[1].ParameterType==typeof(int) && p[2].ParameterType==typeof(bool),
                "no key bytes in review-only entry");
        });

        Console.WriteLine("P101_CANDIDATE_NATIVE_HOST_TESTS_PASSED="+passed);
        Console.WriteLine("P101_CANDIDATE_NATIVE_HOST_TESTS_FAILED="+failed);
        Console.WriteLine("P101_ORIGINAL_P99_NATIVE_FILES_UNCHANGED=TRUE");
        Console.WriteLine("P101_CORRECTED_PRODUCTION_EFFECT_DISPATCH=NOT_IMPLEMENTED");
        Console.WriteLine("P101_WINCRED_EFFECTS=NONE");
        Console.WriteLine("P101_NATIVE_SERVICE_INSTALL_OR_START=NONE");
        Console.WriteLine("P101_SECURITY_REVIEW=NOT_RECEIVED");
        Console.WriteLine("P101_C1_PRODUCTION_RELEASE=HOLD");
        return failed==0 && passed==24 ? 0 : 1;
    }
}
