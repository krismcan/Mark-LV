// P110: actual candidate service-owned monitor with test-only fixed-effect attempt.
// NOT a native Windows credential call; only a nonsecret integer attempt marker.
// P49 guards, G1 issuer, G3 protected evidence and release remain disabled.
// The old P96 coordinator race continues to be independently demonstrated.
#if !C1_SYNTHETIC_TEST
#error P110 effect harness requires explicit synthetic test-only compilation
#endif
using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P110FixedPendingEffectTests
{
    private static int passed, failed;
    private static void Need(bool condition,string reason)
    { if(!condition)throw new InvalidOperationException("P110 "+reason); }
    private static void Run(string name,Action test)
    {
        try{test();++passed;Console.WriteLine("PASS "+name);}
        catch(Exception e){++failed;Console.WriteLine("FAIL "+name+" "+e.GetType().Name);}
    }
    private static void NoActualEffect(CustodyService h)
    {
        Need(!ServiceGate.LiveEligible(),"service release gate false");
        Need(PendingServiceState.LegacyEffectEntryDisabled(),"legacy effect disabled");
        Need(PendingWinCredStore.NativeMutationAdmissionPending(),"WinCred disabled");
        Need(!h.NativeEffectEnabled && !h.AuthenticatedConsentAvailable &&
            !h.ProductionReleaseEligible,"no production effect permit");
    }
    private static void Stop(CustodyService h)
    {
        typeof(CustodyService).GetMethod("OnStop",
            BindingFlags.NonPublic|BindingFlags.Instance).Invoke(h,null);
    }
    private static void Prepare(CustodyService h,LedgerOperation operation)
    { h.PrepareSyntheticFixedEffectOnly(operation,operation==LedgerOperation.Delete); }
    private static CustodyOutcome Attempt(CustodyService h,LedgerOperation operation,
        bool unknown=false)
    { return h.AttemptSyntheticFixedEffectOnly(operation,null,null,unknown); }

    public static int Main()
    {
        Run("actual-P49-gates-still-hardcoded-closed",() =>
        { using(var h=new CustodyService())NoActualEffect(h); });

        Run("save-fixed-fake-attempt-once-sticky-recovery",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "no fake terminal durable proof");
                Need(h.SyntheticDecisionCommits==1 && h.SyntheticEffectAttempts==1,
                    "one synchronous fake effect");
                Need(h.SyntheticUnknownEffectOutcomes==0,"fake call returned");
                Need(h.PendingAdmissionFaulted,"must fault without G3 durability");
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "no second effect");
                Need(h.SyntheticEffectAttempts==1,"exactly once");
                NoActualEffect(h);
            }
        });

        Run("replace-fixed-fake-attempt-once-only",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Replace);
                Need(Attempt(h,LedgerOperation.Replace)==CustodyOutcome.RecoveryRequired,
                    "unverified replace marker");
                Need(h.SyntheticEffectAttempts==1,"one fake replace attempt");
                NoActualEffect(h);
            }
        });

        Run("delete-requires-test-only-destructive-ack",() =>
        {
            using(var h=new CustodyService())
            {
                bool rejected=false;
                try{h.PrepareSyntheticFixedEffectOnly(LedgerOperation.Delete,false);}
                catch(LedgerBlocked){rejected=true;}
                Need(rejected && h.SyntheticEffectAttempts==0,"missing ack refused");
            }
        });

        Run("delete-with-ack-one-fake-attempt-no-real-credential",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Delete);
                Need(Attempt(h,LedgerOperation.Delete)==CustodyOutcome.RecoveryRequired,
                    "no durable delete proof");
                Need(h.SyntheticEffectAttempts==1,"one fake deletion");
                NoActualEffect(h);
            }
        });

        Run("save-with-destructive-ack-is-invalid",() =>
        {
            using(var h=new CustodyService())
            {
                bool rejected=false;
                try{h.PrepareSyntheticFixedEffectOnly(LedgerOperation.Save,true);}
                catch(LedgerBlocked){rejected=true;}
                Need(rejected && h.SyntheticEffectAttempts==0,"invalid save ack");
            }
        });

        Run("unknown-or-initial-op-cannot-prepare-effect",() =>
        {
            using(var h=new CustodyService())
            {
                bool rejected=false;
                try{h.PrepareSyntheticFixedEffectOnly(LedgerOperation.Initial,false);}
                catch(LedgerBlocked){rejected=true;}
                Need(rejected && h.SyntheticEffectAttempts==0,"invalid operation");
            }
        });

        Run("bound-operation-mismatch-refuses-before-fake-effect",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                Need(Attempt(h,LedgerOperation.Delete)==CustodyOutcome.Denied,
                    "wrong immutable operation");
                Need(h.SyntheticEffectAttempts==0 && h.SyntheticDecisionCommits==0,
                    "zero fake effect");
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "original bound operation only");
                Need(h.SyntheticEffectAttempts==1,"one correct fake effect");
            }
        });

        Run("revocation-before-effect-linearization-is-zero",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                h.RevokePendingAdmission();
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.Denied,
                    "revocation wins");
                Need(h.SyntheticEffectAttempts==0 && h.SyntheticDecisionCommits==0,
                    "zero effects after completed revocation");
                Need(h.SyntheticTooLateRevocations==0,"not late");
            }
        });

        Run("revocation-during-fixed-fake-call-waits-then-is-too-late",() =>
        {
            using(var h=new CustodyService())
            using(var entered=new ManualResetEvent(false))
            using(var release=new ManualResetEvent(false))
            using(var revokerStarted=new ManualResetEvent(false))
            {
                CustodyOutcome outcome=CustodyOutcome.Denied;
                Exception failure=null;
                var dispatch=new Thread(() => {
                    try{outcome=h.AttemptSyntheticFixedEffectOnly(
                        LedgerOperation.Save,entered,release,false);}
                    catch(Exception e){failure=e;}
                });
                Prepare(h,LedgerOperation.Save);
                dispatch.Start();
                Need(entered.WaitOne(3000),"fake effect entered under lock");
                var revoke=new Thread(() => {
                    revokerStarted.Set();
                    h.RevokePendingAdmission();
                });
                revoke.Start();
                Need(revokerStarted.WaitOne(3000),"revoker started");
                // Gate is still held by synthetic fixed-effect attempt.
                // Revocation cannot commit until fake effect leaves the lock.
                release.Set();
                Need(dispatch.Join(4000) && revoke.Join(4000),"threads exited");
                Need(failure==null && outcome==CustodyOutcome.RecoveryRequired,
                    "uncertain outcome");
                Need(h.SyntheticEffectAttempts==1 && h.SyntheticDecisionCommits==1,
                    "exactly one possible effect");
                Need(h.SyntheticTooLateRevocations==1,"revocation too late, not cancelled");
                Need(h.PendingAdmissionFaulted && h.PendingAdmissionRevoked,
                    "fault plus later revoke");
                NoActualEffect(h);
            }
        });

        Run("simulated-native-error-is-recovery-not-retry",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                Need(Attempt(h,LedgerOperation.Save,true)==CustodyOutcome.RecoveryRequired,
                    "native uncertainty");
                Need(h.SyntheticEffectAttempts==1 && h.SyntheticUnknownEffectOutcomes==1,
                    "one unknown fake effect");
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "no retry");
                Need(h.SyntheticEffectAttempts==1,"one attempt forever");
            }
        });

        Run("fault-before-fixed-effect-prevents-attempt",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                h.FaultPendingAdmission();
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "fault before effect");
                Need(h.SyntheticEffectAttempts==0,"zero possible effects");
            }
        });

        Run("stop-before-fixed-effect-prevents-attempt",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                Stop(h);
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.Denied,
                    "stop before effect");
                Need(h.SyntheticEffectAttempts==0,"zero possible effects");
                NoActualEffect(h);
            }
        });

        Run("stop-after-fixed-effect-preserves-sticky-recovery",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                Attempt(h,LedgerOperation.Save);
                Stop(h);
                Need(h.PendingAdmissionFaulted && h.PendingAdmissionStopped,
                    "fault persists");
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "no restart");
                Need(h.SyntheticEffectAttempts==1,"no duplicate");
            }
        });

        Run("revoke-after-fake-effect-must-report-too-late",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                Attempt(h,LedgerOperation.Save);
                h.RevokePendingAdmission();
                h.RevokePendingAdmission();
                Need(h.SyntheticTooLateRevocations==1,
                    "late revocation counted once only");
                Need(h.SyntheticEffectAttempts==1,"possible effect retained");
                NoActualEffect(h);
            }
        });

        Run("inflight-uncertainty-before-effect-prevents-mutation",() =>
        {
            using(var h=new CustodyService())
            {
                Prepare(h,LedgerOperation.Save);
                Need(h.RefuseUncertainTerminalIntent()==CustodyOutcome.RecoveryRequired,
                    "history uncertain");
                Need(Attempt(h,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "no effect on uncertain history");
                Need(h.SyntheticEffectAttempts==0,"zero fake effect");
            }
        });

        Run("twelve-concurrent-fixed-effect-requests-only-one",() =>
        {
            using(var h=new CustodyService())
            using(var start=new ManualResetEvent(false))
            {
                Prepare(h,LedgerOperation.Save);
                var workers=new Thread[12];
                int finished=0,fail=0;
                for(int i=0;i<workers.Length;i++)
                {
                    workers[i]=new Thread(() => {
                        try{
                            start.WaitOne();
                            if(Attempt(h,LedgerOperation.Save)!=CustodyOutcome.RecoveryRequired)
                                Interlocked.Increment(ref fail);
                            Interlocked.Increment(ref finished);
                        }
                        catch(Exception){Interlocked.Increment(ref fail);}
                    });
                    workers[i].Start();
                }
                start.Set();
                foreach(var t in workers)Need(t.Join(5000),"joined");
                Need(fail==0 && finished==12,"consistent outcomes");
                Need(h.SyntheticEffectAttempts==1 && h.SyntheticDecisionCommits==1,
                    "one possible fixed fake attempt");
            }
        });

        Run("sixty-revoke-versus-fixed-effect-races-linearize",() =>
        {
            for(int cycle=0;cycle<60;cycle++)
            {
                using(var h=new CustodyService())
                using(var start=new ManualResetEvent(false))
                {
                    Prepare(h,LedgerOperation.Delete);
                    CustodyOutcome outcome=CustodyOutcome.Denied;
                    Exception error=null;
                    var dispatch=new Thread(() => {
                        try{start.WaitOne();outcome=Attempt(h,LedgerOperation.Delete);}
                        catch(Exception e){error=e;}
                    });
                    var revoke=new Thread(() => {start.WaitOne();h.RevokePendingAdmission();});
                    dispatch.Start();revoke.Start();start.Set();
                    Need(dispatch.Join(3500) && revoke.Join(3500),"race threads joined");
                    Need(error==null,"dispatch did not throw");
                    int attempts=h.SyntheticEffectAttempts;
                    Need(attempts==0 || attempts==1,"bounded single attempt");
                    Need(h.SyntheticDecisionCommits==attempts,"commit tied to attempt");
                    if(attempts==0)
                    {
                        Need(outcome==CustodyOutcome.Denied &&
                            h.SyntheticTooLateRevocations==0,
                            "revoke won, zero effects");
                    }
                    else
                    {
                        Need(outcome==CustodyOutcome.RecoveryRequired &&
                            h.SyntheticTooLateRevocations==1,
                            "effect won, revocation late, recovery");
                    }
                    Need(h.PendingAdmissionRevoked,"revocation done");
                    NoActualEffect(h);
                }
            }
        });

        Run("ordinary-candidate-still-has-no-deployable-Main",() =>
        {
            Need(typeof(CustodyService).GetMethod("Main",
                BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static)==null,
                "not installable");
            using(var h=new CustodyService())NoActualEffect(h);
        });

        Console.WriteLine("P110_REAL_CANDIDATE_SYNTHETIC_FIXED_EFFECT_CASES_PASSED="+passed);
        Console.WriteLine("P110_REAL_CANDIDATE_SYNTHETIC_FIXED_EFFECT_CASES_FAILED="+failed);
        Console.WriteLine("P110_SYNTHETIC_EFFECT_IS_ONLY_AN_INTEGER_COUNTER=TRUE");
        Console.WriteLine("P110_CONSENT_ISSUER_AND_REAL_DURABLE_INTENT=ABSENT");
        Console.WriteLine("P110_REAL_PENDING_WINCRED_EFFECTS=ZERO");
        Console.WriteLine("P110_P96_LEGACY_CHECK_TO_EFFECT_RACE=UNFIXED");
        Console.WriteLine("P110_BYOK_C1_PRODUCTION_RELEASE=HOLD");
        return passed==19 && failed==0?0:1;
    }
}
