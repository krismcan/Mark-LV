// P208: genuine Windows native C# TEST EXECUTABLE ONLY.
// Original frozen P49, live P132 Python backend and native C1 remain unchanged.
// Counts are synthetic integer attempts, never credential effects.
#if C1_SYNTHETIC_TEST
using System;
using System.Threading;
using Nayeon.ByokC1;

internal static class P208SyntheticTerminalOwnerTests
{
    private static int passed, failed;

    private static void Check(bool condition, string reason)
    {
        if (!condition) throw new InvalidOperationException("P208 "+reason);
    }

    private static void Run(string name, Action test)
    {
        try { test(); ++passed; Console.WriteLine("PASS "+name); }
        catch (Exception e)
        { ++failed; Console.WriteLine("FAIL "+name+" "+e.GetType().Name); }
    }

    private static P208SyntheticTerminalOwner Owner()
    { return new P208SyntheticTerminalOwner(); }

    private static void AlwaysHeld(P208SyntheticTerminalOwner owner)
    {
        Check(!owner.NativeEffectEnabled, "native WinCred remains forbidden");
        Check(!owner.AuthenticatedConsentAvailable, "no signed approval");
        Check(!owner.ProductionReleaseEligible, "no release");
        Check(owner.FixedTarget == "nayeon-v1/secret/openai.api_key", "fixed target");
    }

    public static int Main()
    {
        Run("fixed-target-no-service-or-effect-authority", delegate {
            var h=Owner();
            AlwaysHeld(h);
            Check(!ServiceGate.LiveEligible(), "original P49 service refusal");
            Check(h.AttemptCount==0, "no effect");
        });
        Run("absent-review-denied", delegate {
            var h=Owner();
            Check(h.AttemptForTestOnly(null,LedgerOperation.Save,false)==CustodyOutcome.Denied,
                "no review");
            Check(h.AttemptCount==0,"none");
        });
        Run("save-fake-one-attempt-then-recovery", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Save,false);
            Check(r!=null,"prepared");
            Check(h.AttemptForTestOnly(r,LedgerOperation.Save,false)==CustodyOutcome.RecoveryRequired,
                "unknown terminal");
            Check(h.AttemptCount==1 && h.SyntheticEffectAttempts==1,"one fake effect");
            Check(h.RequiresReconciliation,"recovery");
            AlwaysHeld(h);
        });
        Run("replace-fake-one-attempt-then-recovery", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Replace,false);
            Check(r!=null,"prepared");
            Check(h.AttemptForTestOnly(r,LedgerOperation.Replace,false)==CustodyOutcome.RecoveryRequired,
                "unknown terminal");
            Check(h.SyntheticEffectAttempts==1,"one fake");
        });
        Run("acknowledged-delete-fake-one-attempt", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Delete,true);
            Check(r!=null,"prepared");
            Check(h.AttemptForTestOnly(r,LedgerOperation.Delete,false)==CustodyOutcome.RecoveryRequired,
                "unknown terminal");
            Check(h.SyntheticEffectAttempts==1,"one fake");
        });
        Run("unacknowledged-delete-refused", delegate {
            var h=Owner();
            Check(h.PrepareForTestOnly(LedgerOperation.Delete,false)==null,
                "delete requires ack");
            Check(h.SyntheticEffectAttempts==0,"none");
        });
        Run("unnecessary-save-ack-refused", delegate {
            var h=Owner();
            Check(h.PrepareForTestOnly(LedgerOperation.Save,true)==null,
                "save ack shape");
            Check(h.SyntheticEffectAttempts==0,"none");
        });
        Run("invalid-operation-refused", delegate {
            var h=Owner();
            Check(h.PrepareForTestOnly((LedgerOperation)999,false)==null,"unknown op");
            Check(h.SyntheticEffectAttempts==0,"none");
        });
        Run("same-owner-duplicate-prepare-refused", delegate {
            var h=Owner();
            var a=h.PrepareForTestOnly(LedgerOperation.Save,false);
            Check(a!=null,"first");
            Check(h.PrepareForTestOnly(LedgerOperation.Save,false)==null,"duplicate");
            Check(h.SyntheticEffectAttempts==0,"no effect while pending");
        });
        Run("forged-review-fails-closed", delegate {
            var h=Owner();
            Check(h.PrepareForTestOnly(LedgerOperation.Save,false)!=null,"prepared");
            var forged=new P208SyntheticTerminalOwner.SyntheticReview();
            Check(h.AttemptForTestOnly(forged,LedgerOperation.Save,false)==CustodyOutcome.Denied,
                "forged deny");
            Check(h.Revoked && h.SyntheticEffectAttempts==0,"revoked no effect");
        });
        Run("foreign-actor-review-fails-closed", delegate {
            var a=Owner();
            var b=Owner();
            var x=a.PrepareForTestOnly(LedgerOperation.Save,false);
            var y=b.PrepareForTestOnly(LedgerOperation.Save,false);
            Check(x!=null && y!=null,"prepared");
            Check(a.AttemptForTestOnly(y,LedgerOperation.Save,false)==CustodyOutcome.Denied,
                "wrong owner");
            Check(a.Revoked && a.SyntheticEffectAttempts==0,"none");
        });
        Run("wrong-operation-fails-closed", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Save,false);
            Check(h.AttemptForTestOnly(r,LedgerOperation.Replace,false)==CustodyOutcome.Denied,
                "wrong operation");
            Check(h.Revoked && h.SyntheticEffectAttempts==0,"none");
        });
        Run("replay-after-fake-effect-recovery-no-retry", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Save,false);
            h.AttemptForTestOnly(r,LedgerOperation.Save,false);
            for (int i=0;i<5;i++)
                Check(h.AttemptForTestOnly(r,LedgerOperation.Save,false)==CustodyOutcome.RecoveryRequired,
                    "replayed requires recovery");
            Check(h.SyntheticEffectAttempts==1 && h.AttemptCount==1,"no repeat");
        });
        Run("revoke-before-terminal-refuses", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Save,false);
            h.Revoke();
            Check(h.AttemptForTestOnly(r,LedgerOperation.Save,false)==CustodyOutcome.Denied,
                "revoked deny");
            Check(h.SyntheticEffectAttempts==0,"none");
        });
        Run("fault-before-terminal-recovery-no-effect", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Save,false);
            h.Fault();
            Check(h.AttemptForTestOnly(r,LedgerOperation.Save,false)==CustodyOutcome.RecoveryRequired,
                "fault recovery");
            Check(h.SyntheticEffectAttempts==0,"none");
        });
        Run("unknown-fake-native-result-recovery-one-attempt", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Delete,true);
            Check(h.AttemptForTestOnly(r,LedgerOperation.Delete,true)==CustodyOutcome.RecoveryRequired,
                "uncertain recovery");
            Check(h.SyntheticEffectAttempts==1 && h.SyntheticUnknownOutcomes==1,
                "one unknown effect");
        });
        Run("stop-before-effect-recovery-no-retry", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Save,false);
            h.Stop();
            Check(h.AttemptForTestOnly(r,LedgerOperation.Save,false)==CustodyOutcome.RecoveryRequired,
                "stopped recovery");
            Check(h.SyntheticEffectAttempts==0,"no effect");
        });
        Run("concurrent-replay-only-one-fake-attempt", delegate {
            var h=Owner();
            var review=h.PrepareForTestOnly(LedgerOperation.Save,false);
            var gate=new ManualResetEvent(false);
            var first=CustodyOutcome.Denied;
            var second=CustodyOutcome.Denied;
            var t1=new Thread(delegate {
                gate.WaitOne();
                first=h.AttemptForTestOnly(review,LedgerOperation.Save,false);
            });
            var t2=new Thread(delegate {
                gate.WaitOne();
                second=h.AttemptForTestOnly(review,LedgerOperation.Save,false);
            });
            t1.Start();t2.Start();gate.Set();
            Check(t1.Join(3000) && t2.Join(3000),"thread completion");
            Check(first==CustodyOutcome.RecoveryRequired &&
                  second==CustodyOutcome.RecoveryRequired,"recovery only");
            Check(h.SyntheticEffectAttempts==1 && h.AttemptCount==1,"one");
            gate.Dispose();
        });
        Run("new-owner-cannot-reuse-old-inprocess-review", delegate {
            var before=Owner();
            var stale=before.PrepareForTestOnly(LedgerOperation.Save,false);
            var after=Owner();
            Check(after.AttemptForTestOnly(stale,LedgerOperation.Save,false)==CustodyOutcome.Denied,
                "fresh has no pending");
            Check(after.SyntheticEffectAttempts==0,"none");
            // No durable state is implemented: this is NOT G3 recovery.
        });
        Run("late-revocation-cannot-claim-no-effect", delegate {
            var h=Owner();
            var r=h.PrepareForTestOnly(LedgerOperation.Save,false);
            h.AttemptForTestOnly(r,LedgerOperation.Save,false);
            h.Revoke();
            Check(h.RequiresReconciliation,"still unknown");
            Check(h.SyntheticEffectAttempts==1,"one");
        });
        Console.WriteLine("P208_SYNTHETIC_NATIVE_TERMINAL_PASSED="+passed);
        Console.WriteLine("P208_SYNTHETIC_NATIVE_TERMINAL_FAILED="+failed);
        Console.WriteLine("P208_REAL_WINCRED_WRITES=ZERO|RELEASE=HOLD");
        return failed==0 && passed==20 ? 0:1;
    }
}
#endif
