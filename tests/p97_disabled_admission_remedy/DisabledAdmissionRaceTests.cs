// P97: adversarial real Windows C# threads, FAKE-ONLY corrected lock ordering.
// P96's original design flaw remains unchanged and is exercised separately.
using System;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P97.DisabledOnly;

internal static class P97Tests
{
    private static int passed, failed;
    private static readonly string Session = new String('a', 32);
    private static readonly string Candidate = new String('c', 32);
    private static readonly string Other = new String('d', 32);
    private static readonly LedgerOperation[] Ops =
    {
        LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete
    };

    private static FakeExactBinding Binding(LedgerOperation op)
    { return new FakeExactBinding(op, Session, Candidate); }

    private static DisabledNativeAdmissionCoordinator Prepared(LedgerOperation op,
        bool intent)
    {
        var m = new DisabledNativeAdmissionCoordinator(Binding(op));
        m.FakeApprove(Binding(op));
        if (intent) m.FakePersistAndReadbackIntent(Binding(op));
        return m;
    }

    private static void Demand(bool value, string message)
    { if (!value) throw new Exception("P97 fake test failed: " + message); }

    private static void Denied(Action fn)
    {
        bool denied = false;
        try { fn(); }
        catch (InvalidOperationException) { denied = true; }
        catch (LedgerBlocked) { denied = true; }
        Demand(denied, "expected safe refusal");
    }

    private static string Attempt(DisabledNativeAdmissionCoordinator m,
        FakeExactBinding binding)
    {
        using (var arrived = new ManualResetEventSlim(false))
        using (var release = new ManualResetEventSlim(true))
        {
            string answer = m.FakeDispatch(binding, arrived, release);
            Demand(arrived.IsSet, "dispatched marker");
            return answer;
        }
    }

    private static void NoAuthority(FakeAdmissionSnapshot s)
    {
        Demand(!s.CredentialVerified, "must not verify credential");
        Demand(!s.NativeEffectPermitted, "native effect always disabled");
        Demand(!s.ProductionEligible, "no production release");
        Demand(!s.RetryAllowed, "no retry permission");
        Demand(!s.ToString().Contains(Candidate), "no fixture identifier leak");
    }

    private static void Run(string name, Action action)
    {
        try { action(); passed++; Console.WriteLine("PASS " + name); }
        catch (Exception ex)
        {
            failed++;
            Console.WriteLine("FAIL " + name + " " + ex.GetType().Name);
        }
    }

    private static void ForEachOperation(string label, Action<LedgerOperation> test)
    {
        foreach (LedgerOperation op in Ops)
        {
            LedgerOperation selected = op;
            Run(label + "-" + selected, () => test(selected));
        }
    }

    private static void RevocationCommitsBeforeDispatch(LedgerOperation op)
    {
        var m = Prepared(op, true);
        using (var done = new ManualResetEventSlim(false))
        {
            var revoker = new Thread(() => { m.Revoke(); done.Set(); });
            revoker.Start();
            Demand(done.Wait(2000) && revoker.Join(2000), "revocation commit");
        }
        Denied(() => Attempt(m, Binding(op)));
        var s = m.ReadOnlySnapshot();
        Demand(s.PossibleAttempts == 0, "zero attempts when revoke COMMITTED first");
        Demand(s.Revoked && s.Stage == FakeAdmissionStage.RecoveryOnly, "recovery hold");
        Demand(!s.RevocationCommittedAfterAttempt, "revocation won");
        NoAuthority(s);
    }

    private static void DispatchWinsThenRevocation(LedgerOperation op)
    {
        var m = Prepared(op, true);
        using (var entered = new ManualResetEventSlim(false))
        using (var requested = new ManualResetEventSlim(false))
        using (var released = new ManualResetEventSlim(false))
        using (var finished = new ManualResetEventSlim(false))
        {
            var revoker = new Thread(() =>
            {
                if (entered.Wait(2000))
                {
                    requested.Set(); m.Revoke(); finished.Set();
                }
            });
            var releaseThread = new Thread(() =>
            {
                if (requested.Wait(2000)) released.Set();
            });
            revoker.Start(); releaseThread.Start();

            string result = m.FakeDispatch(Binding(op), entered, released);
            Demand(result == "P97_FAKE_ATTEMPT_ONLY__NO_NATIVE_OPERATION",
                "exact in-memory outcome");
            Demand(revoker.Join(2000), "revocation thread completed");
            Demand(releaseThread.Join(2000), "release thread completed");
            Demand(finished.IsSet, "revocation committed only after dispatch lock");
        }
        var view = m.ReadOnlySnapshot();
        Demand(view.PossibleAttempts == 1, "exactly one possible attempt");
        Demand(view.Revoked && view.RevocationCommittedAfterAttempt,
            "revocation happened too late to cancel possible effect");
        Demand(view.Stage == FakeAdmissionStage.RecoveryOnly,
            "no false cancellation or terminal success");
        Denied(() => Attempt(m, Binding(op)));
        Denied(() => m.FakeCompleteEffectAndTerminal(true, true));
        NoAuthority(view);
    }

    private static void FaultCommitsBeforeDispatch(LedgerOperation op)
    {
        var m = Prepared(op, true);
        using (var done = new ManualResetEventSlim(false))
        {
            var worker = new Thread(() => { m.Fault(); done.Set(); });
            worker.Start();
            Demand(done.Wait(2000) && worker.Join(2000), "fault commit");
        }
        Denied(() => Attempt(m, Binding(op)));
        var s = m.ReadOnlySnapshot();
        Demand(s.PossibleAttempts == 0 && s.Faulted, "no effect after committed fault");
        Demand(s.Stage == FakeAdmissionStage.RecoveryOnly, "fault recovery");
        NoAuthority(s);
    }

    private static void DispatchWinsThenFault(LedgerOperation op)
    {
        var m = Prepared(op, true);
        using (var entered = new ManualResetEventSlim(false))
        using (var request = new ManualResetEventSlim(false))
        using (var release = new ManualResetEventSlim(false))
        using (var complete = new ManualResetEventSlim(false))
        {
            var fault = new Thread(() =>
            {
                if (entered.Wait(2000))
                {
                    request.Set(); m.Fault(); complete.Set();
                }
            });
            var releaseThread = new Thread(() =>
            {
                if (request.Wait(2000)) release.Set();
            });
            fault.Start(); releaseThread.Start();
            m.FakeDispatch(Binding(op), entered, release);
            Demand(fault.Join(2000) && releaseThread.Join(2000) && complete.IsSet,
                "fault published after dispatch");
        }
        var s = m.ReadOnlySnapshot();
        Demand(s.PossibleAttempts == 1 && s.Faulted, "possible effect + later fault");
        Demand(s.Stage == FakeAdmissionStage.RecoveryOnly, "no retry");
        Denied(() => Attempt(m, Binding(op)));
    }

    private static void FakeTerminalNoVerification(LedgerOperation op)
    {
        var m = Prepared(op, true);
        Demand(Attempt(m, Binding(op)) ==
            "P97_FAKE_ATTEMPT_ONLY__NO_NATIVE_OPERATION", "fake marker");
        m.FakeCompleteEffectAndTerminal(true, true);
        var s = m.ReadOnlySnapshot();
        Demand(s.Stage == FakeAdmissionStage.ClosedUnverified, "unverified terminal");
        Demand(s.PossibleAttempts == 1, "one marker");
        NoAuthority(s);
        Denied(() => Attempt(m, Binding(op)));
        m.Revoke(); // Revoking after committed terminal cannot undo past effect.
        Demand(m.ReadOnlySnapshot().RevocationCommittedAfterAttempt,
            "late revocation remains observable");
        NoAuthority(m.ReadOnlySnapshot());
    }

    private static void FakeResultFailureNoReplay(LedgerOperation op)
    {
        var m = Prepared(op, true);
        Attempt(m, Binding(op));
        m.FakeCompleteEffectAndTerminal(false, false);
        var s = m.ReadOnlySnapshot();
        Demand(s.PossibleAttempts == 1 && s.Stage == FakeAdmissionStage.RecoveryOnly,
            "uncertain native result must block");
        Denied(() => Attempt(m, Binding(op)));
        NoAuthority(s);
    }

    private static void FakeTerminalFailureNoReplay(LedgerOperation op)
    {
        var m = Prepared(op, true);
        Attempt(m, Binding(op));
        m.FakeCompleteEffectAndTerminal(true, false);
        var s = m.ReadOnlySnapshot();
        Demand(s.PossibleAttempts == 1 && s.Stage == FakeAdmissionStage.RecoveryOnly,
            "failed persistence readback must block");
        Denied(() => Attempt(m, Binding(op)));
    }

    private static void FakeRestartAfterIntent(LedgerOperation op)
    {
        var m = Prepared(op, true);
        m.FakeRestart();
        var s = m.ReadOnlySnapshot();
        Demand(s.PossibleAttempts == 0 && s.Stage == FakeAdmissionStage.RecoveryOnly,
            "restart before dispatch does not bootstrap");
        Denied(() => Attempt(m, Binding(op)));
    }

    private static void FakeRestartAfterDispatch(LedgerOperation op)
    {
        var m = Prepared(op, true);
        Attempt(m, Binding(op));
        m.FakeRestart();
        var s = m.ReadOnlySnapshot();
        Demand(s.PossibleAttempts == 1 && s.Stage == FakeAdmissionStage.RecoveryOnly,
            "restart after possible effect cannot replay");
        Denied(() => Attempt(m, Binding(op)));
    }

    private static void RejectWrongBinding(LedgerOperation op)
    {
        var m = Prepared(op, true);
        var wrongSession = new FakeExactBinding(op, Other, Candidate);
        var wrongCandidate = new FakeExactBinding(op, Session, Other);
        Denied(() => Attempt(m, wrongSession));
        Denied(() => Attempt(m, wrongCandidate));
        Demand(m.ReadOnlySnapshot().PossibleAttempts == 0, "reject wrong identity");
        NoAuthority(m.ReadOnlySnapshot());
    }

    public static int Main()
    {
        ForEachOperation("revocation-wins-before-dispatch", RevocationCommitsBeforeDispatch);
        ForEachOperation("dispatch-wins-before-revocation", DispatchWinsThenRevocation);
        ForEachOperation("fault-wins-before-dispatch", FaultCommitsBeforeDispatch);
        ForEachOperation("dispatch-wins-before-fault", DispatchWinsThenFault);
        ForEachOperation("terminal-unverified", FakeTerminalNoVerification);
        ForEachOperation("fake-result-failure-no-retry", FakeResultFailureNoReplay);
        ForEachOperation("terminal-persist-failure-no-retry", FakeTerminalFailureNoReplay);
        ForEachOperation("restart-after-intent-no-retry", FakeRestartAfterIntent);
        ForEachOperation("restart-after-dispatch-no-retry", FakeRestartAfterDispatch);
        ForEachOperation("wrong-binding-refused", RejectWrongBinding);

        Run("approval-missing-prevents-intent", () =>
        {
            var m = new DisabledNativeAdmissionCoordinator(Binding(LedgerOperation.Save));
            Denied(() => m.FakePersistAndReadbackIntent(Binding(LedgerOperation.Save)));
            Demand(m.ReadOnlySnapshot().PossibleAttempts == 0, "no attempt");
        });
        Run("duplicate-fake-approval-refused", () =>
        {
            var m = Prepared(LedgerOperation.Save, false);
            Denied(() => m.FakeApprove(Binding(LedgerOperation.Save)));
        });
        Run("approval-binding-mismatch-refused", () =>
        {
            var m = new DisabledNativeAdmissionCoordinator(Binding(LedgerOperation.Save));
            Denied(() => m.FakeApprove(new FakeExactBinding(
                LedgerOperation.Save, Other, Candidate)));
            Denied(() => m.FakeApprove(new FakeExactBinding(
                LedgerOperation.Save, Session, Other)));
        });
        Run("wrong-operation-refused", () =>
        {
            var m = Prepared(LedgerOperation.Save, true);
            Denied(() => Attempt(m, Binding(LedgerOperation.Delete)));
            Demand(m.ReadOnlySnapshot().PossibleAttempts == 0, "zero attempts");
        });
        Run("cross-thread-dispatch-refused", () =>
        {
            var m = Prepared(LedgerOperation.Save, true);
            bool denied = false;
            var worker = new Thread(() =>
            {
                try { Attempt(m, Binding(LedgerOperation.Save)); }
                catch (InvalidOperationException) { denied = true; }
            });
            worker.Start(); Demand(worker.Join(2000) && denied, "thread ownership");
            Demand(m.ReadOnlySnapshot().PossibleAttempts == 0, "no unauthorized attempt");
        });
        Run("cross-thread-fake-approval-refused", () =>
        {
            var m = new DisabledNativeAdmissionCoordinator(Binding(LedgerOperation.Save));
            bool denied = false;
            var worker = new Thread(() =>
            {
                try { m.FakeApprove(Binding(LedgerOperation.Save)); }
                catch (InvalidOperationException) { denied = true; }
            });
            worker.Start(); Demand(worker.Join(2000) && denied, "approval owner");
            Demand(m.ReadOnlySnapshot().PossibleAttempts == 0, "no effect");
        });
        Run("corrupt-untrusted-in-memory-anchor-refused", () =>
        {
            var m = Prepared(LedgerOperation.Save, false);
            m.CorruptFakeAnchorForTest();
            Denied(() => m.FakePersistAndReadbackIntent(Binding(LedgerOperation.Save)));
            Demand(m.ReadOnlySnapshot().PossibleAttempts == 0, "untrusted evidence denies");
            Demand(m.ReadOnlySnapshot().Stage == FakeAdmissionStage.RecoveryOnly,
                "corrupt ledger must latch recovery and not rearm");
            Denied(() => Attempt(m, Binding(LedgerOperation.Save)));
        });
        Run("revocation-before-fake-intent-refused", () =>
        {
            var m = Prepared(LedgerOperation.Save, false);
            m.Revoke();
            Denied(() => m.FakePersistAndReadbackIntent(Binding(LedgerOperation.Save)));
            Demand(m.ReadOnlySnapshot().PossibleAttempts == 0, "no attempt");
        });
        Run("invalid-fake-identity-refused", () =>
        {
            Denied(() => new FakeExactBinding(LedgerOperation.Save, "secret", Candidate));
            Denied(() => new FakeExactBinding(LedgerOperation.Initial, Session, Candidate));
        });
        Run("never-authoritative-even-before-fake-action", () =>
        {
            var m = new DisabledNativeAdmissionCoordinator(Binding(LedgerOperation.Save));
            NoAuthority(m.ReadOnlySnapshot());
        });

        Console.WriteLine("P97_DISABLED_NATIVE_RACE_TESTS_PASSED=" + passed);
        Console.WriteLine("P97_DISABLED_NATIVE_RACE_TESTS_FAILED=" + failed);
        Console.WriteLine("P97_LEGACY_P96_FINDING=STILL_OPEN_IN_ORIGINAL");
        Console.WriteLine("P97_IN_PROCESS_TEST_REMEDY=SERIALIZES_FAKE_DISPATCH_AND_REVOCATION");
        Console.WriteLine("P97_REAL_NATIVE_EFFECTS=NONE");
        Console.WriteLine("P97_PRODUCTION_RELEASE=HOLD");
        return failed == 0 && passed == 40 ? 0 : 1;
    }
}
