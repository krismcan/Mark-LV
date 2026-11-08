// P108: real candidate-host native service-owned terminal *denial* boundary.
// No user secrets, native credential APIs, privileged service install, caller-
// supplied authority, generic callbacks, fake successful dispatch or rearming.
// The legacy P96 race remains OPEN: this test does not simulate a fix.
using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P108NativeTerminalDenialTests
{
    private static int passed, failed;
    private static void Assert(bool ok,string reason)
    { if (!ok) throw new InvalidOperationException("P108: "+reason); }

    private static void Case(string label,Action test)
    {
        try { test();++passed;Console.WriteLine("PASS "+label); }
        catch(Exception e) { ++failed;Console.WriteLine("FAIL "+label+" "+e.GetType().Name); }
    }

    private static void Stop(CustodyService service)
    {
        typeof(CustodyService).GetMethod("OnStop",
            BindingFlags.NonPublic|BindingFlags.Instance).Invoke(service,null);
    }

    private static void Baseline()
    {
        Assert(!ServiceGate.LiveEligible(),"original live service false");
        Assert(PendingServiceState.LegacyEffectEntryDisabled(),"legacy effect disabled");
        Assert(PendingWinCredStore.NativeMutationAdmissionPending(),"WinCred mutation disabled");
    }

    public static int Main()
    {
        Case("unaltered-three-original-native-effect-guards",Baseline);
        Case("terminal-admission-always-denied-unapproved",() =>
        {
            using(var service=new CustodyService())
            {
                Assert(service.RefuseUnreviewedTerminalEffect()==CustodyOutcome.Denied,
                    "no terminal effect");
                Assert(service.TerminalEffectRefusals==1,"counted denied effect");
                Assert(service.TerminalBoundaryObserved,"observation latched");
                Assert(!service.NativeEffectEnabled,"never permission");
                Assert(!service.AuthenticatedConsentAvailable,"no trusted consent");
                Assert(!service.ProductionReleaseEligible,"no release");
            }
        });
        Case("terminal-denial-repeat-never-arms-effect",() =>
        {
            using(var service=new CustodyService())
            {
                for(int i=0;i<200;i++)
                    Assert(service.RefuseUnreviewedTerminalEffect()==CustodyOutcome.Denied,
                        "repeated denial");
                Assert(service.TerminalEffectRefusals==200,"denial count");
                Assert(!service.NativeEffectEnabled,"no effect after repetition");
            }
        });
        Case("revoke-wins-before-terminal-boundary",() =>
        {
            using(var service=new CustodyService())
            {
                service.RevokePendingAdmission();
                Assert(service.RefuseUnreviewedTerminalEffect()==CustodyOutcome.Denied,
                    "revoked before attempt");
                Assert(service.PendingAdmissionRevoked && !service.NativeEffectEnabled,
                    "no post-revoke effect");
            }
        });
        Case("stop-wins-before-terminal-boundary",() =>
        {
            using(var service=new CustodyService())
            {
                Stop(service);
                Assert(service.RefuseUnreviewedTerminalEffect()==CustodyOutcome.Denied,
                    "stopped before attempt");
                Assert(service.PendingAdmissionStopped,"stopped");
            }
        });
        Case("prior-fault-never-becomes-new-permit",() =>
        {
            using(var service=new CustodyService())
            {
                service.FaultPendingAdmission();
                Assert(service.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "fault recovery");
                Assert(!service.NativeEffectEnabled,"no native effect");
            }
        });
        Case("unreviewed-inflight-intent-always-latches-recovery",() =>
        {
            using(var service=new CustodyService())
            {
                Assert(service.RefuseUncertainTerminalIntent()==CustodyOutcome.RecoveryRequired,
                    "intent unknown");
                Assert(service.PendingAdmissionFaulted,"fault latched");
                Assert(service.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "cannot dispatch");
                Assert(service.ObserveNativeJ2CustodyReadOnly().Kind==
                    NativeJ2ReadOnlyKind.RecoveryRequired,"cannot downgrade fault");
            }
        });
        Case("revoked-then-uncertain-intent-still-recovery",() =>
        {
            using(var service=new CustodyService())
            {
                service.RevokePendingAdmission();
                Assert(service.RefuseUncertainTerminalIntent()==CustodyOutcome.RecoveryRequired,
                    "uncertain durable intent needs recovery");
                Assert(service.PendingAdmissionFaulted,"fault after revoke");
            }
        });
        Case("stopped-then-uncertain-intent-still-recovery",() =>
        {
            using(var service=new CustodyService())
            {
                Stop(service);
                Assert(service.RefuseUncertainTerminalIntent()==CustodyOutcome.RecoveryRequired,
                    "uncertain after stop is recovery");
            }
        });
        Case("fault-then-stop-never-resets-fault",() =>
        {
            using(var service=new CustodyService())
            {
                service.RefuseUncertainTerminalIntent();
                Stop(service);
                Assert(service.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "fault persists through stop");
            }
        });
        Case("untrusted-request-always-denied-with-terminal-denial",() =>
        {
            using(var service=new CustodyService())
            {
                Assert(service.RefusePendingOperation(LedgerOperation.Save,10,false)==
                    CustodyOutcome.Denied,"untrusted metadata");
                Assert(service.RefuseUnreviewedTerminalEffect()==CustodyOutcome.Denied,
                    "no escalation");
                Assert(service.RefusePendingOperation(LedgerOperation.Delete,0,true)==
                    CustodyOutcome.Denied,"untrusted deletion");
                Assert(!service.NativeEffectEnabled,"no terminal rights");
            }
        });
        Case("no-caller-approval-or-credential-parameter",() =>
        {
            var t=typeof(CustodyService);
            foreach(string name in new []{"RefuseUnreviewedTerminalEffect",
                "RefuseUncertainTerminalIntent"})
            {
                var m=t.GetMethod(name,BindingFlags.NonPublic|BindingFlags.Instance);
                Assert(m!=null && m.GetParameters().Length==0,"zero caller args "+name);
                Assert(m.ReturnType==typeof(CustodyOutcome),"strict refusal type");
            }
        });
        Case("no-service-deploy-main-and-no-legacy-transaction-reference",() =>
        {
            var t=typeof(CustodyService);
            Assert(t.GetMethod("Main",BindingFlags.Public|BindingFlags.NonPublic|
                BindingFlags.Static)==null,"no entrypoint");
            foreach(var f in t.GetFields(BindingFlags.Instance|BindingFlags.NonPublic|
                BindingFlags.Public))
                Assert(f.FieldType!=typeof(PendingCustodyTransaction),
                    "legacy coordinator not part of candidate host");
            foreach(var m in t.GetMethods(BindingFlags.Instance|BindingFlags.NonPublic|
                BindingFlags.Public|BindingFlags.DeclaredOnly))
            {
                Assert(m.ReturnType!=typeof(IProtectedPendingState),"no effect-bearing return");
                foreach(var param in m.GetParameters())
                    Assert(param.ParameterType!=typeof(ITrustedPendingApproval) &&
                        param.ParameterType!=typeof(IProtectedPendingState),
                        "no arbitrary approval or state injection");
            }
        });
        Case("concurrent-revoke-and-terminal-denial-still-no-effects",() =>
        {
            using(var service=new CustodyService())
            {
                int unexpected=0;
                var threads=new Thread[12];
                for(int i=0;i<threads.Length;i++)
                {
                    int slot=i;
                    threads[i]=new Thread(() =>
                    {
                        try
                        {
                            for(int j=0;j<100;j++)
                            {
                                var x=service.RefuseUnreviewedTerminalEffect();
                                if(x!=CustodyOutcome.Denied && x!=CustodyOutcome.RecoveryRequired)
                                    Interlocked.Increment(ref unexpected);
                                if((slot+j)%13==0)service.RevokePendingAdmission();
                            }
                        }
                        catch(Exception){Interlocked.Increment(ref unexpected);}
                    });
                    threads[i].Start();
                }
                foreach(var t in threads)Assert(t.Join(8000),"thread joined");
                Assert(unexpected==0,"only denial/recovery");
                Assert(service.TerminalEffectRefusals==1200,"all requests counted");
                Assert(service.PendingAdmissionRevoked && !service.NativeEffectEnabled,
                    "concurrent revoke never effect");
            }
        });
        Case("concurrent-fault-publishes-sticky-recovery",() =>
        {
            using(var service=new CustodyService())
            {
                var started=new ManualResetEvent(false);
                var worker=new Thread(() =>
                {
                    started.Set();
                    service.RefuseUncertainTerminalIntent();
                });
                worker.Start();
                Assert(started.WaitOne(3000),"started");
                Assert(worker.Join(3000),"completed");
                for(int i=0;i<100;i++)
                    Assert(service.RefuseUnreviewedTerminalEffect()==
                        CustodyOutcome.RecoveryRequired,"sticky fault");
                Assert(!service.NativeEffectEnabled,"never effects");
                started.Dispose();
            }
        });

        Console.WriteLine("P108_NATIVE_TERMINAL_BOUNDARY_TESTS_PASSED="+passed);
        Console.WriteLine("P108_NATIVE_TERMINAL_BOUNDARY_TESTS_FAILED="+failed);
        Console.WriteLine("P108_NO_TRUSTED_UI_OR_NATIVE_EFFECT_CAPABILITY=TRUE");
        Console.WriteLine("P108_LEGACY_P96_RACE_FIX=NOT_IMPLEMENTED");
        Console.WriteLine("P108_PRODUCTION_C1_G0_G1_G2_G3_G4_G5_G6=HOLD");
        return passed==15 && failed==0 ? 0 : 1;
    }
}
