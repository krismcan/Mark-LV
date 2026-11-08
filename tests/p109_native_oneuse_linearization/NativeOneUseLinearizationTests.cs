// P109: the REAL candidate service-owned monitor, not a disconnected model.
// TEST-ASSEMBLY ONLY, compiled with C1_SYNTHETIC_TEST; no WinCred, key, UI,
// service install, IPC, persistent tickets or provider effect.
// Successful synthetic commit is only an integer decision marker.
// P96 negative comparator remains the unresolved genuine P49 bug.
#if !C1_SYNTHETIC_TEST
#error P109 test driver cannot exist without explicit synthetic build
#endif
using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P109NativeOneUseLinearizationTests
{
    private static int passed, failed;
    private static void Need(bool value,string reason)
    { if (!value) throw new InvalidOperationException("P109 "+reason); }
    private static void Run(string label,Action action)
    {
        try {action();++passed;Console.WriteLine("PASS "+label);}
        catch(Exception ex){++failed;Console.WriteLine("FAIL "+label+" "+ex.GetType().Name);}
    }
    private static void Stop(CustodyService h)
    {
        typeof(CustodyService).GetMethod("OnStop",
            BindingFlags.NonPublic|BindingFlags.Instance).Invoke(h,null);
    }
    private static void NoActualEffect(CustodyService h)
    {
        Need(!ServiceGate.LiveEligible(),"P49 service guard");
        Need(PendingServiceState.LegacyEffectEntryDisabled(),"P49 effect adapter guard");
        Need(PendingWinCredStore.NativeMutationAdmissionPending(),"P49 WinCred guard");
        Need(!h.NativeEffectEnabled && !h.AuthenticatedConsentAvailable &&
            !h.ProductionReleaseEligible,"no release eligibility");
    }
    public static int Main()
    {
        Run("P49-real-native-three-gates-unchanged",() =>
        {
            using(var h=new CustodyService()) NoActualEffect(h);
        });
        Run("no-synthetic-preparation-cannot-commit",() =>
        {
            using(var h=new CustodyService())
            {
                Need(!h.CommitSyntheticDecisionOnly(),"cannot commit without prep");
                Need(h.SyntheticDecisionCommits==0,"zero possible dispatch marker");
                NoActualEffect(h);
            }
        });
        Run("one-prepared-decision-commits-once",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                Need(h.CommitSyntheticDecisionOnly(),"first marker");
                Need(h.SyntheticDecisionCommits==1,"one decision");
                Need(!h.CommitSyntheticDecisionOnly(),"no duplicate commit");
                NoActualEffect(h);
            }
        });
        Run("synthetic-preparation-is-one-use",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                bool blocked=false;
                try{h.PrepareSyntheticOnly();}
                catch(LedgerBlocked){blocked=true;}
                Need(blocked && h.SyntheticDecisionCommits==0,"cannot mint two grants");
            }
        });
        Run("revocation-before-commit-wins-and-prevents-marker",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                h.RevokePendingAdmission();
                Need(!h.CommitSyntheticDecisionOnly(),"early revoke deny");
                Need(h.SyntheticDecisionCommits==0,"no marker");
                Need(h.SyntheticTooLateRevocations==0,"not late");
                NoActualEffect(h);
            }
        });
        Run("revoke-after-decision-is-explicitly-too-late",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                Need(h.CommitSyntheticDecisionOnly(),"commit");
                h.RevokePendingAdmission();
                Need(h.SyntheticDecisionCommits==1,"possible dispatch remains");
                Need(h.SyntheticTooLateRevocations==1,"late revoke recorded");
                Need(!h.CommitSyntheticDecisionOnly(),"no replay");
                NoActualEffect(h);
            }
        });
        Run("late-revoke-does-not-claim-cancelled-terminal",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                h.CommitSyntheticDecisionOnly();
                h.RevokePendingAdmission();
                Need(h.FinishSyntheticTerminalUnverified(),"unverified not cancelled");
                Need(h.SyntheticDecisionCommits==1,"still possibly attempted");
                NoActualEffect(h);
            }
        });
        Run("no-terminal-without-dispatch-decision",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                Need(!h.FinishSyntheticTerminalUnverified(),"must commit first");
                Need(h.SyntheticDecisionCommits==0,"never effect");
            }
        });
        Run("synthetic-terminal-cannot-be-written-twice",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                h.CommitSyntheticDecisionOnly();
                Need(h.FinishSyntheticTerminalUnverified(),"first terminal");
                Need(!h.FinishSyntheticTerminalUnverified(),"second terminal");
                Need(h.SyntheticDecisionCommits==1,"one decision");
            }
        });
        Run("fault-before-commit-prevents-any-decision",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                h.FaultPendingAdmission();
                Need(!h.CommitSyntheticDecisionOnly(),"fault denies");
                Need(h.SyntheticDecisionCommits==0,"no decision marker");
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "sticky recovery");
            }
        });
        Run("fault-after-commit-never-erases-possible-effect",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                h.CommitSyntheticDecisionOnly();
                h.FaultPendingAdmission();
                Need(!h.FinishSyntheticTerminalUnverified(),"unknown result");
                Need(h.SyntheticDecisionCommits==1,"possible effect not erased");
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "recovery no retry");
            }
        });
        Run("stop-before-commit-must-deny",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                Stop(h);
                Need(!h.CommitSyntheticDecisionOnly(),"stop beats commit");
                Need(h.SyntheticDecisionCommits==0,"no possible effect");
                NoActualEffect(h);
            }
        });
        Run("stop-after-commit-requires-sticky-recovery",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                h.CommitSyntheticDecisionOnly();
                Stop(h);
                Need(h.SyntheticDecisionCommits==1,"unknown possible effect");
                Need(h.PendingAdmissionFaulted,"sticky fault after stop");
                Need(h.RefuseUnreviewedTerminalEffect()==CustodyOutcome.RecoveryRequired,
                    "no replay after stop");
            }
        });
        Run("inflight-uncertainty-blocks-future-commit",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();
                Need(h.RefuseUncertainTerminalIntent()==CustodyOutcome.RecoveryRequired,
                    "uncertain intent");
                Need(!h.CommitSyntheticDecisionOnly(),"cannot dispatch after unknown");
                Need(h.SyntheticDecisionCommits==0,"zero markers");
                NoActualEffect(h);
            }
        });
        Run("no-rearm-after-revocation",() =>
        {
            using(var h=new CustodyService())
            {
                h.RevokePendingAdmission();
                bool denied=false;
                try{h.PrepareSyntheticOnly();}
                catch(LedgerBlocked){denied=true;}
                Need(denied,"cannot reissue");
            }
        });
        Run("no-rearm-after-unverified-terminal",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();h.CommitSyntheticDecisionOnly();
                h.FinishSyntheticTerminalUnverified();
                bool denied=false;
                try{h.PrepareSyntheticOnly();}
                catch(LedgerBlocked){denied=true;}
                Need(denied,"one-use only");
            }
        });
        Run("twelve-simultaneous-committers-only-one-marker",() =>
        {
            using(var h=new CustodyService())
            using(var ready=new ManualResetEvent(false))
            {
                h.PrepareSyntheticOnly();
                int winners=0;
                var workers=new Thread[12];
                for(int i=0;i<workers.Length;i++)
                {
                    workers[i]=new Thread(() => {
                        ready.WaitOne();
                        if(h.CommitSyntheticDecisionOnly())
                            Interlocked.Increment(ref winners);
                    });
                    workers[i].Start();
                }
                ready.Set();
                foreach(var worker in workers)Need(worker.Join(5000),"worker joined");
                Need(winners==1 && h.SyntheticDecisionCommits==1,"one winner");
                NoActualEffect(h);
            }
        });
        Run("commit-versus-revoke-linearizes-without-cancel-lie",() =>
        {
            for(int cycle=0;cycle<80;cycle++)
            {
                using(var h=new CustodyService())
                using(var go=new ManualResetEvent(false))
                {
                    h.PrepareSyntheticOnly();
                    bool commitWon=false;
                    Exception workerFailure=null;
                    var dispatch=new Thread(() => {
                        try{go.WaitOne();commitWon=h.CommitSyntheticDecisionOnly();}
                        catch(Exception e){workerFailure=e;}
                    });
                    var revoke=new Thread(() => {
                        try{go.WaitOne();h.RevokePendingAdmission();}
                        catch(Exception e){workerFailure=e;}
                    });
                    dispatch.Start();revoke.Start();go.Set();
                    Need(dispatch.Join(3000) && revoke.Join(3000),"threads joined");
                    Need(workerFailure==null,"threads succeeded");
                    int markers=h.SyntheticDecisionCommits;
                    Need(markers==(commitWon?1:0),"commit counter linearizable");
                    if(commitWon)
                        Need(h.SyntheticTooLateRevocations==1,
                            "revocation too late, not cancellation");
                    else
                        Need(h.SyntheticTooLateRevocations==0,
                            "revocation before commit, zero possible effect");
                    Need(h.PendingAdmissionRevoked,"revocation eventually committed");
                    NoActualEffect(h);
                }
            }
        });
        Run("repeat-concurrent-revoke-does-not-create-new-marker",() =>
        {
            using(var h=new CustodyService())
            {
                h.PrepareSyntheticOnly();h.CommitSyntheticDecisionOnly();
                var t=new Thread(() => {for(int i=0;i<50;i++)h.RevokePendingAdmission();});
                t.Start();Need(t.Join(5000),"revoke thread");
                Need(h.SyntheticDecisionCommits==1,"still one decision");
                Need(!h.CommitSyntheticDecisionOnly(),"cannot mint another decision");
                NoActualEffect(h);
            }
        });
        Run("legacy-real-coordinator-not-in-candidate-host-fields",() =>
        {
            foreach(var f in typeof(CustodyService).GetFields(
                BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Public))
                Need(f.FieldType!=typeof(PendingCustodyTransaction) &&
                    f.FieldType!=typeof(IProtectedPendingState) &&
                    f.FieldType!=typeof(ITrustedPendingApproval),
                    "no injectable legacy effect state or approval");
        });
        Run("candidate-has-no-executable-service-main",() =>
        {
            Need(typeof(CustodyService).GetMethod("Main",
                BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static)==null,
                "no deployable main");
            using(var h=new CustodyService())NoActualEffect(h);
        });

        Console.WriteLine("P109_SYNTHETIC_NATIVE_CASES_PASSED="+passed);
        Console.WriteLine("P109_SYNTHETIC_NATIVE_CASES_FAILED="+failed);
        Console.WriteLine("P109_SYNTHETIC_DECISION_MARKER_NOT_A_WIN_CRED_CALL=TRUE");
        Console.WriteLine("P109_ACTUAL_TRUSTED_G1_CONSENT_ISSUER=ABSENT");
        Console.WriteLine("P109_REAL_DISPATCH_G2_NATIVE_EFFECT_REPLACEMENT=NOT_IMPLEMENTED");
        Console.WriteLine("P109_ORIGINAL_P96_RACE_STILL_OPEN=TRUE");
        Console.WriteLine("P109_BYOK_C1_PRODUCTION_RELEASE=HOLD");
        return passed==21 && failed==0 ? 0 : 1;
    }
}
