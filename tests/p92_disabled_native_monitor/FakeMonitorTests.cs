// P92 native Windows executable runs only a fake, non-credential C# actor.
// No real Windows credential APIs, protected state, or privileged operation.
using System;
using System.Threading;
using Nayeon.P92.FakeOnly;

internal static class FakeMonitorTests
{
    private static readonly string A = new string('a', 32);
    private static readonly string B = new string('b', 32);
    private static readonly string C = new string('c', 32);
    private static int passed, failed;

    private static FakeBinding Bind()
    { return new FakeBinding(FakeOperation.SavePending, A, B); }

    private static DisabledFakeAdmissionMonitor Prepared()
    {
        var m = new DisabledFakeAdmissionMonitor();
        m.Prepare(Bind());
        m.FakeApprove(Bind());
        m.FakeIntentAck();
        return m;
    }

    private static void Require(bool value, string reason)
    { if (!value) throw new Exception("Fixture assertion failed: " + reason); }

    private static void Denied(Action action)
    {
        bool refused = false;
        try { action(); }
        catch (InvalidOperationException) { refused = true; }
        Require(refused, "expected denial");
    }

    private static void Run(string name, Action action)
    {
        try { action(); passed++; Console.WriteLine("PASS " + name); }
        catch (Exception ex) {
            failed++; Console.WriteLine("FAIL " + name + " " + ex.GetType().Name);
        }
    }

    private static void FakeOneAttempt(DisabledFakeAdmissionMonitor m)
    {
        using (var entered = new ManualResetEventSlim(false))
        using (var release = new ManualResetEventSlim(true)) {
            m.FakeDispatchBarrier(Bind(), entered, release);
            Require(entered.IsSet, "fake dispatch must signal");
        }
    }

    private static void RevokeBeforeAttempt()
    {
        var m = Prepared();
        var done = new ManualResetEventSlim(false);
        var other = new Thread(() => { m.Revoke(); done.Set(); });
        other.Start();
        Require(done.Wait(2000), "revocation not committed");
        Require(other.Join(2000), "revoker thread alive");
        Denied(() => FakeOneAttempt(m));
        Require(m.Snapshot().Attempts == 0, "revocation before attempt");
        Require(m.Snapshot().Phase == FakePhase.RecoveryOnly, "recovery");
        done.Dispose();
    }

    private static void FaultBeforeAttempt()
    {
        var m = Prepared();
        var done = new ManualResetEventSlim(false);
        var other = new Thread(() => { m.Fault(); done.Set(); });
        other.Start();
        Require(done.Wait(2000), "fault not published");
        Require(other.Join(2000), "fault thread alive");
        Denied(() => FakeOneAttempt(m));
        Require(m.Snapshot().Attempts == 0, "fault before attempt");
        done.Dispose();
    }

    // An actual *separate* thread attempts revocation while the fake dispatch
    // holds the SAME monitor. It cannot commit until after the attempt.
    private static void DispatchWinsThenRevocation()
    {
        var m = Prepared();
        using (var entered = new ManualResetEventSlim(false))
        using (var request = new ManualResetEventSlim(false))
        using (var release = new ManualResetEventSlim(false))
        using (var revoked = new ManualResetEventSlim(false)) {
            var revoker = new Thread(() => {
                if (entered.Wait(2000)) {
                    request.Set(); m.Revoke(); revoked.Set();
                }
            });
            var releaseThread = new Thread(() => {
                if (request.Wait(2000)) release.Set();
            });
            revoker.Start(); releaseThread.Start();
            m.FakeDispatchBarrier(Bind(), entered, release);
            Require(revoker.Join(3000), "revoker did not finish");
            Require(releaseThread.Join(3000), "release thread did not finish");
            Require(revoked.IsSet, "revoke did not commit");
            Require(m.Snapshot().Attempts == 1, "attempt recorded before revoke");
            Require(m.Snapshot().Phase == FakePhase.RecoveryOnly, "recovery required");
            Denied(() => FakeOneAttempt(m));
        }
    }

    private static void DispatchWinsThenFault()
    {
        var m = Prepared();
        using (var entered = new ManualResetEventSlim(false))
        using (var request = new ManualResetEventSlim(false))
        using (var release = new ManualResetEventSlim(false))
        using (var faulted = new ManualResetEventSlim(false)) {
            var worker = new Thread(() => {
                if (entered.Wait(2000)) {
                    request.Set(); m.Fault(); faulted.Set();
                }
            });
            var releaseThread = new Thread(() => {
                if (request.Wait(2000)) release.Set();
            });
            worker.Start(); releaseThread.Start();
            m.FakeDispatchBarrier(Bind(), entered, release);
            Require(worker.Join(3000), "fault worker hung");
            Require(releaseThread.Join(3000), "release worker hung");
            Require(faulted.IsSet, "fault not published");
            Require(m.Snapshot().Attempts == 1, "one possible attempt");
            Require(m.Snapshot().Phase == FakePhase.RecoveryOnly, "recovery");
        }
    }

    private static void ForeignThreadAttempt()
    {
        var m = Prepared();
        bool denied = false;
        var t = new Thread(() => {
            try { FakeOneAttempt(m); }
            catch (InvalidOperationException) { denied = true; }
        });
        t.Start();
        Require(t.Join(2000), "foreign thread hung");
        Require(denied, "foreign owner denied");
        Require(m.Snapshot().Attempts == 0, "no foreign attempt");
    }

    private static void RestartAfterPossibleAttempt()
    {
        var m = Prepared();
        FakeOneAttempt(m);
        m.FakeRestart();
        Require(m.Snapshot().Attempts == 1, "possible attempt preserved");
        Require(m.Snapshot().Phase == FakePhase.RecoveryOnly, "restart blocks");
        Denied(() => FakeOneAttempt(m));
    }

    private static void FakeTerminalSuccessNeverProviderVerified()
    {
        var m = Prepared();
        FakeOneAttempt(m);
        m.FakeNativeResult(true);
        m.FakeTerminalCommit(true);
        Require(m.Snapshot().Phase == FakePhase.ClosedUnverified, "terminal phase");
        Require(!m.Snapshot().ProductVerified, "no provider assertion");
        Require(!m.Snapshot().ProductionEligible, "no release");
        Denied(() => FakeOneAttempt(m));
    }

    public static int Main()
    {
        Run("no-preparation-refused", () => {
            var m = new DisabledFakeAdmissionMonitor();
            Denied(() => FakeOneAttempt(m));
            Require(m.Snapshot().Attempts == 0, "zero attempts");
        });
        Run("no-consent-refused", () => {
            var m = new DisabledFakeAdmissionMonitor();
            m.Prepare(Bind());
            Denied(() => m.FakeIntentAck());
        });
        Run("no-intent-refused", () => {
            var m = new DisabledFakeAdmissionMonitor();
            m.Prepare(Bind()); m.FakeApprove(Bind());
            Denied(() => FakeOneAttempt(m));
        });
        Run("exact-binding-refusal", () => {
            var m = Prepared();
            var bad = new FakeBinding(FakeOperation.SavePending, A, C);
            using (var e = new ManualResetEventSlim(false))
            using (var r = new ManualResetEventSlim(true))
                Denied(() => m.FakeDispatchBarrier(bad, e, r));
            Require(m.Snapshot().Attempts == 0, "wrong candidate");
        });
        Run("wrong-session-refusal", () => {
            var m = Prepared();
            var bad = new FakeBinding(FakeOperation.SavePending, C, B);
            using (var e = new ManualResetEventSlim(false))
            using (var r = new ManualResetEventSlim(true))
                Denied(() => m.FakeDispatchBarrier(bad, e, r));
            Require(m.Snapshot().Attempts == 0, "wrong session");
        });
        Run("wrong-operation-refusal", () => {
            var m = Prepared();
            var bad = new FakeBinding(FakeOperation.DeletePending, A, B);
            using (var e = new ManualResetEventSlim(false))
            using (var r = new ManualResetEventSlim(true))
                Denied(() => m.FakeDispatchBarrier(bad, e, r));
            Require(m.Snapshot().Attempts == 0, "wrong operation");
        });
        Run("second-consent-refusal", () => {
            var m = Prepared(); Denied(() => m.FakeApprove(Bind()));
        });
        Run("second-prepare-refusal", () => {
            var m = Prepared(); Denied(() => m.Prepare(Bind()));
        });
        Run("revocation-before-dispatch-concurrency", RevokeBeforeAttempt);
        Run("fault-before-dispatch-concurrency", FaultBeforeAttempt);
        Run("dispatch-wins-revocation-concurrency", DispatchWinsThenRevocation);
        Run("dispatch-wins-fault-concurrency", DispatchWinsThenFault);
        Run("foreign-thread-attempt-refusal", ForeignThreadAttempt);
        Run("exactly-one-fake-dispatch", () => {
            var m = Prepared(); FakeOneAttempt(m);
            Denied(() => FakeOneAttempt(m));
            Require(m.Snapshot().Attempts == 1, "one attempt");
        });
        Run("crash-after-intent-no-attempt", () => {
            var m = Prepared(); m.FakeRestart();
            Denied(() => FakeOneAttempt(m));
            Require(m.Snapshot().Attempts == 0, "no attempt");
        });
        Run("restart-after-dispatch-no-retry", RestartAfterPossibleAttempt);
        Run("native-failure-recovery", () => {
            var m = Prepared(); FakeOneAttempt(m);
            m.FakeNativeResult(false);
            Require(m.Snapshot().Phase == FakePhase.RecoveryOnly, "fault state");
            Require(m.Snapshot().Attempts == 1, "preserve possible effect");
        });
        Run("native-success-terminal-failure-recovery", () => {
            var m = Prepared(); FakeOneAttempt(m);
            m.FakeNativeResult(true); m.FakeTerminalCommit(false);
            Require(m.Snapshot().Phase == FakePhase.RecoveryOnly, "persistence");
        });
        Run("terminal-never-provider-verified", FakeTerminalSuccessNeverProviderVerified);
        Run("closed-terminal-restart-blocked", () => {
            var m = Prepared(); FakeOneAttempt(m);
            m.FakeNativeResult(true); m.FakeTerminalCommit(true); m.FakeRestart();
            Require(m.Snapshot().Phase == FakePhase.RecoveryOnly, "restart");
        });
        Run("invalid-fixture-rejected", () => {
            Denied(() => new FakeBinding(FakeOperation.SavePending, "secret", B));
            Denied(() => new FakeBinding((FakeOperation)99, A, B));
        });
        Run("never-production-eligible", () => {
            Require(!new DisabledFakeAdmissionMonitor().Snapshot().ProductionEligible,
                    "no product release");
        });
        Console.WriteLine("P92_FAKE_NATIVE_MONITOR_PASSED=" + passed);
        Console.WriteLine("P92_FAKE_NATIVE_MONITOR_FAILED=" + failed);
        Console.WriteLine("P92_NATIVE_CREDENTIAL_DISPATCH=NONE");
        Console.WriteLine("P92_BYOK_C1_PRODUCTION_RELEASE=HOLD");
        return failed == 0 && passed == 22 ? 0 : 1;
    }
}
