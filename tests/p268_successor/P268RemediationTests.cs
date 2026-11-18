#if !DEBUG
#error P268_TESTS_NO_RELEASE_BUILD
#endif
#if !C1_P268_DEVELOPMENT_ONLY
#error P268_TESTS_REQUIRE_DEVELOPMENT_BUILD
#endif
using System;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P268Development;

internal static class P268RemediationTests
{
    private static int checks, cases;
    private static void Demand(bool condition, string message)
    { checks++; if (!condition) throw new Exception(message); }
    private static void Join(Thread thread)
    { Demand(thread.Join(3000), "thread deadline"); }
    private sealed class Fixture
    {
        internal readonly P96ApprovalFixture Approval = new P96ApprovalFixture();
        internal readonly P96StateFixture State;
        internal readonly P96GuardFixture Guard;
        internal readonly DevelopmentPendingState Adapter;
        internal readonly ServiceOwnedPendingTransaction Service;
        internal readonly ServiceOwnedPendingTransaction.Approval Ticket;
        internal readonly LedgerOperation Op;
        internal Fixture(LedgerOperation op, bool fresh)
        {
            Op = op; State = new P96StateFixture(Approval); Guard = new P96GuardFixture(Approval);
            if (op != LedgerOperation.Save)
            {
                State.Journal = CustodyLedger.AppendTerminal(CustodyLedger.AppendIntent(
                    State.Journal, LedgerOperation.Save, new string('b', 32)));
                State.Anchor = CustodyLedger.Anchor(State.Journal); State.Present = true;
            }
            Adapter = new DevelopmentPendingState(State);
            Service = ServiceOwnedPendingTransaction.DevelopmentOnlyHost(Adapter, Guard, fresh);
            Ticket = Service.IssueDevelopmentApproval(op);
        }
        internal CustodyOutcome Apply()
        { return Service.Apply(Ticket, Op, Op == LedgerOperation.Delete ? null : P96Fixture.Dummy(), Op == LedgerOperation.Delete); }
        internal void NoReplay()
        {
            int before = State.PossibleEffects;
            Demand(Apply() != CustodyOutcome.StoredUnverified, "no repeated success");
            Demand(State.PossibleEffects == before, "no replay submission");
            Demand(Service.IssueDevelopmentApproval(Op) == null, "cannot rearm");
        }
    }
    private static void Run(string name, Action test)
    { test(); cases++; Console.WriteLine("PASS " + name); }
    private static void RevocationWins(LedgerOperation op)
    {
        var f = new Fixture(op, true);
        ControlResult control = ControlResult.TooLate;
        var revoker = new Thread(() => { control = f.Service.Revoke(); f.Approval.Revoke(); });
        revoker.Start(); Join(revoker);
        Demand(control == ControlResult.Revoked, "revocation wins under service gate");
        Demand(f.Apply() == CustodyOutcome.Denied, "post-revoke refusal");
        Demand(f.State.PossibleEffects == 0 && f.State.EffectsAfterRevoke == 0, "zero identical P96 effects");
        Demand(f.Approval.Checks == 0 && f.Approval.ConsumeCount == 0, "caller approval is never authority");
        f.NoReplay();
    }
    private static void EffectWins(LedgerOperation op, int reason)
    {
        var f = new Fixture(op, true);
        using (var entered = new ManualResetEvent(false))
        using (var release = new ManualResetEvent(false))
        using (var revoking = new ManualResetEvent(false))
        using (var revoked = new ManualResetEvent(false))
        {
            f.Adapter.Inject = point => { if (point == "effect-enter")
                { Demand(CustodyLedger.Verify(f.State.Journal, f.State.Anchor) == LedgerPhase.InFlight, "verified pending marker before dispatch"); entered.Set(); if (!release.WaitOne(2500)) throw new Exception("release deadline"); } };
            CustodyOutcome outcome = CustodyOutcome.Denied;
            ControlResult control = ControlResult.Revoked;
            var writer = new Thread(() => { outcome = f.Apply(); });
            var revoker = new Thread(() => { revoking.Set(); control = reason == 0 ? f.Service.Revoke() : reason == 1 ? f.Service.Stop() : f.Service.Fault();
                f.Approval.Revoke(); revoked.Set(); });
            writer.Start(); Demand(entered.WaitOne(2500), "actual interface call entered");
            revoker.Start(); Demand(revoking.WaitOne(2500), "revoker started");
            Demand(!revoked.WaitOne(50), "revocation cannot complete across dispatch gate");
            release.Set(); Join(writer); Join(revoker);
            Demand(control == ControlResult.TooLate, "never cancellation success");
            Demand(outcome == (op == LedgerOperation.Delete ? CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified), "terminal unverified result");
            Demand(f.State.PossibleEffects == 1 && f.State.EffectsAfterRevoke == 0, "effect first, no post revocation effect");
            Demand(f.Service.MayHaveEffect && f.Service.RecoveryRequired, "sticky uncertainty even after terminal");
            Demand(CustodyLedger.Verify(f.State.Journal, f.State.Anchor) ==
                (op == LedgerOperation.Delete ? LedgerPhase.CommittedAbsent : LedgerPhase.CommittedUnverified), "actual terminal ledger");
            Demand(f.Guard.TerminalMarked && f.Guard.LeaseDisposed, "lease lifecycle");
            Demand(f.Adapter.JournalWrites == 2 && f.Adapter.AnchorWrites == 2 && f.Adapter.SaveCalls + f.Adapter.DeleteCalls == 1, "real ledger and one effect call");
            f.NoReplay();
        }
    }
    private static void FaultInjection(string point, int occurrence)
    {
        var f = new Fixture(LedgerOperation.Save, true);
        int seen = 0;
        f.Adapter.Inject = at => { if (at == point && ++seen == occurrence) throw new LedgerBlocked(); };
        Demand(f.Apply() == CustodyOutcome.RecoveryRequired, "exception recovery " + point);
        Demand(f.State.PossibleEffects <= 1, "at most one effect");
        Demand(f.Service.RecoveryRequired, "sticky fault");
        f.NoReplay();
    }
    private sealed class LeaseSeam : IExclusiveCustodyLock, IContinuousCustodyLease
    {
        internal Action Callback;
        internal bool FailAcquire, FailOwned, FailMark, FailDispose;
        internal int Reads;
        public bool RecoveryFaulted { get { return false; } }
        public IContinuousCustodyLease Acquire()
        { if (FailAcquire) throw new LedgerBlocked(); return this; }
        public bool IsOwned { get { if (++Reads == 4 && Callback != null) Callback(); return !FailOwned; } }
        public void MarkTerminalVerified() { if (FailMark) throw new LedgerBlocked(); }
        public void Dispose() { if (FailDispose) throw new LedgerBlocked(); }
    }
    private static void LeaseFailures()
    {
        for (int i = 0; i < 4; i++)
        {
            var approval = new P96ApprovalFixture(); var state = new P96StateFixture(approval);
            var lease = new LeaseSeam { FailAcquire = i == 0, FailOwned = i == 1,
                FailMark = i == 2, FailDispose = i == 3 };
            var service = ServiceOwnedPendingTransaction.DevelopmentOnlyHost(new DevelopmentPendingState(state), lease, true);
            var ticket = service.IssueDevelopmentApproval(LedgerOperation.Save);
            Demand(service.Apply(ticket, LedgerOperation.Save, P96Fixture.Dummy(), false) == CustodyOutcome.RecoveryRequired, "lease failure");
            Demand(state.PossibleEffects == (i < 2 ? 0 : 1), "lease effect bound");
            Demand(service.RecoveryRequired, "lease sticky fault");
        }
    }
    private static void Reentry(bool separateThread)
    {
        var a = new P96ApprovalFixture(); var state = new P96StateFixture(a);
        var lease = new LeaseSeam();
        var service = ServiceOwnedPendingTransaction.DevelopmentOnlyHost(new DevelopmentPendingState(state), lease, true);
        bool rejected = false;
        lease.Callback = () =>
        {
            Action callback = () => { try { service.Revoke(); }
                catch (InvalidOperationException) { rejected = true; } };
            if (separateThread) { var thread = new Thread(() => callback()); thread.Start(); Join(thread); }
            else callback(); // swallow exception adversarially; owner still must fail closed
        };
        var ticket = service.IssueDevelopmentApproval(LedgerOperation.Save);
        Demand(service.Apply(ticket, LedgerOperation.Save, P96Fixture.Dummy(), false) == CustodyOutcome.RecoveryRequired, "reentry recovery");
        Demand(rejected && state.PossibleEffects == 0, "last lease callback cannot bypass final barrier");
        Demand(service.RecoveryRequired, "reentry sticky");
        Demand(CustodyLedger.Verify(state.Journal, state.Anchor) == LedgerPhase.InFlight, "pending marker retained");
    }
    private static void Preconditions()
    {
        for (int i = 0; i < 8; i++)
        {
            var f = new Fixture(LedgerOperation.Save, true);
            if (i == 0) { f.State.Journal = null; f.State.Anchor = null; }
            if (i == 1) f.Adapter.Enrolled = false;
            if (i == 2) f.State.Anchor = "mismatch";
            if (i == 3) f.State.Present = true;
            if (i == 4) { f.State.Journal = CustodyLedger.AppendIntent(f.State.Journal, LedgerOperation.Save, new string('b', 32)); f.State.Anchor = CustodyLedger.Anchor(f.State.Journal); }
            if (i == 5) f.Guard.Fault = true;
            if (i == 6) f.State.Trusted = false;
            if (i == 7) f.State.Journal = "corrupt";
            Demand(f.Apply() == CustodyOutcome.RecoveryRequired, "invalid witness or trust");
            Demand(f.State.PossibleEffects == 0, "no unsafe precondition effects"); f.NoReplay();
        }
        var restart = new Fixture(LedgerOperation.Save, false);
        Demand(restart.Ticket == null && restart.Apply() == CustodyOutcome.RecoveryRequired, "restart never auto-enrolls");
        Demand(restart.State.PossibleEffects == 0, "restart no effects");
        var mismatch = new Fixture(LedgerOperation.Replace, true);
        mismatch.State.Present = false;
        Demand(mismatch.Apply() == CustodyOutcome.RecoveryRequired && mismatch.State.PossibleEffects == 0, "stored mismatch");
    }
    private static void ControlsAndBindings()
    {
        for (int i = 0; i < 2; i++)
        {
            var f = new Fixture(LedgerOperation.Save, true);
            ControlResult result = i == 0 ? f.Service.Stop() : f.Service.Fault();
            Demand(result == (i == 0 ? ControlResult.Stopped : ControlResult.RecoveryRequired), "service control gate");
            f.Apply(); Demand(f.State.PossibleEffects == 0, "control first denies");
        }
        var first = new Fixture(LedgerOperation.Save, true); var second = new Fixture(LedgerOperation.Save, true);
        Demand(second.Service.Apply(first.Ticket, LedgerOperation.Save, P96Fixture.Dummy(), false) == CustodyOutcome.Denied, "foreign identity");
        Demand(first.Service.Apply(first.Ticket, LedgerOperation.Delete, null, true) == CustodyOutcome.Denied, "operation binding");
        Demand(first.Service.Apply(first.Ticket, LedgerOperation.Save, new byte[4], false) == CustodyOutcome.Denied, "literal candidate only");
        first.NoReplay();
        Demand(!ServiceOwnedPendingTransaction.ProductionEligible && !ServiceOwnedPendingTransaction.TrustedIssuerConnected, "issuer and production disconnected");
    }
    private static void TerminalMismatch()
    {
        var f = new Fixture(LedgerOperation.Save, true); int writes = 0;
        f.Adapter.Inject = point => { if (point == "after-anchor" && ++writes == 2) f.State.Anchor = "wrong"; };
        Demand(f.Apply() == CustodyOutcome.RecoveryRequired, "terminal readback mismatch");
        Demand(f.State.PossibleEffects == 1 && f.Service.MayHaveEffect && f.Service.RecoveryRequired, "terminal uncertainty");
        Demand(f.Service.Revoke() == ControlResult.TooLate, "terminal failure not cancellation"); f.NoReplay();
        var failure = new Fixture(LedgerOperation.Delete, true); failure.State.ThrowDuringEffect = true;
        Demand(failure.Apply() == CustodyOutcome.RecoveryRequired && failure.State.PossibleEffects == 1, "effect throws after entry");
        Demand(CustodyLedger.Verify(failure.State.Journal, failure.State.Anchor) == LedgerPhase.InFlight, "effect failure leaves pending intent"); failure.NoReplay();
    }
    private static int Main()
    {
        try
        {
            foreach (LedgerOperation op in new[] { LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete })
            {
                LedgerOperation selected = op;
                Run("revoke-wins-" + op, () => RevocationWins(selected));
                for (int reason = 0; reason < 3; reason++)
                { int control = reason; Run("effect-wins-" + op + "-" + reason, () => EffectWins(selected, control)); }
            }
            foreach (string point in new[] { "trust", "read-journal", "read-anchor", "present", "write-journal", "after-journal", "write-anchor", "after-anchor", "effect-enter", "effect-return" })
            { string selected = point; Run("exception-" + point, () => FaultInjection(selected, 1)); }
            Run("terminal-journal-exception", () => FaultInjection("write-journal", 2));
            Run("terminal-anchor-exception", () => FaultInjection("write-anchor", 2));
            Run("effect-callback-reentry", () =>
            {
                var f = new Fixture(LedgerOperation.Save, true); bool refused = false;
                f.Adapter.Inject = point => { if (point == "effect-enter")
                    { try { f.Service.Revoke(); } catch (InvalidOperationException) { refused = true; } } };
                Demand(f.Apply() == CustodyOutcome.RecoveryRequired && refused, "effect callback cannot cancel or report success");
                Demand(f.Service.MayHaveEffect && f.Service.RecoveryRequired && f.State.PossibleEffects <= 1, "effect entry stays uncertain");
                Demand(CustodyLedger.Verify(f.State.Journal, f.State.Anchor) == LedgerPhase.InFlight, "no terminal after reentry");
                Demand(f.Service.Revoke() == ControlResult.TooLate, "never cancellation success"); f.NoReplay();
            });
            Run("same-thread-reentry", () => Reentry(false));
            Run("synchronized-thread-callback", () => Reentry(true));
            Run("initial-readback-drift", () =>
            {
                var f = new Fixture(LedgerOperation.Save, true); int reads = 0;
                f.Adapter.Inject = point => { if (point == "read-journal" && ++reads == 2) f.State.Journal = null; };
                Demand(f.Apply() == CustodyOutcome.RecoveryRequired && f.State.PossibleEffects == 0, "initial pair drift");
                f.NoReplay();
            });
            Run("post-intent-present-drift", () =>
            {
                var f = new Fixture(LedgerOperation.Save, true); int reads = 0;
                f.Adapter.Inject = point => { if (point == "present" && ++reads == 3) f.State.Present = true; };
                Demand(f.Apply() == CustodyOutcome.RecoveryRequired && f.State.PossibleEffects == 0, "pre-effect drift");
                f.NoReplay();
            });
            Run("lease-failures", LeaseFailures); Run("preconditions", Preconditions);
            Run("controls-and-bindings", ControlsAndBindings); Run("terminal-mismatch-and-effect-failure", TerminalMismatch);
            Console.WriteLine("P268_SUCCESSOR=PASS CASES=" + cases + " ASSERTIONS=" + checks + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P268_FIXED_PATH=ISOLATED_FAKE_ONLY PRODUCTION=HOLD TRUSTED_ISSUER=NOT_CONNECTED");
            return 0;
        }
        catch (Exception error) { Console.WriteLine("P268_FAIL=" + error); return 1; }
    }
}
