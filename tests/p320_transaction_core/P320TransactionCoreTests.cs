using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.Service;

internal static class P320TransactionCoreTests
{
    private static int cases;
    private static readonly Guid Id = new Guid("22222222-2222-2222-2222-222222222222");
    private static void Check(bool value) { if (!value) throw new Exception("P320 assertion; HOLD"); }
    private static void Run(Action test) { test(); cases++; }
    private static SyntheticTransactionRequest Request(SyntheticOperation op)
    { return new SyntheticTransactionRequest(Id, 1, 1, op); }
    private static CustodyTransactionCore Create(SyntheticOperation op, SyntheticCrash crash)
    { return new CustodyTransactionCore(new InMemoryCustodyFixture(op == SyntheticOperation.Add ?
        SyntheticSeed.Absent : SyntheticSeed.Present), Request(op), crash); }
    private static CoreOutcome Success(SyntheticOperation op)
    { return op == SyntheticOperation.Delete ? CoreOutcome.RemovedUnverified : CoreOutcome.StoredUnverified; }
    private static object Review(CustodyTransactionCore owner, SyntheticOperation op)
    {
        Check(owner.Observe().Stage == CustodyStage.ReviewPending);
        object ticket = owner.ReviewSynthetic(Request(op));
        Check(ticket != null && owner.Observe().Stage == CustodyStage.Reviewed);
        return ticket;
    }
    private static void Terminal(CustodyTransactionCore owner, CoreOutcome outcome, int attempts)
    {
        CoreSnapshot snapshot = owner.Observe();
        Check(snapshot.Stage == CustodyStage.Terminal && snapshot.Outcome == outcome &&
            snapshot.Attempts == attempts && !snapshot.ProductionEligible);
        Check(owner.ReviewSynthetic(snapshot.Request) == null);
        Check(owner.DispatchSynthetic(null, null) == outcome && owner.Observe().Attempts == attempts);
        Check(owner.Observe().Outcome == outcome); // strict first terminal result; no replay
    }
    private static void Lifecycle(SyntheticOperation op)
    {
        CustodyTransactionCore owner = Create(op, SyntheticCrash.None);
        CoreSnapshot pending = owner.Observe();
        object ticket = Review(owner, op);
        Check(owner.ReviewSynthetic(Request(op)) == null);
        Check(owner.DispatchSynthetic(ticket, Request(op)) == Success(op));
        Terminal(owner, Success(op), 1);
        Check(pending.Stage == CustodyStage.ReviewPending && pending.Outcome == CoreOutcome.None);
        Check(owner.Observe().MayHaveEffect && owner.Observe().RecoveryRequired);
        SyntheticCustodyImage image = owner.CaptureSyntheticCrashImage();
        Check(CustodyTransactionCore.AssessRestart(image) == RestartAssessment.TerminalUnverified);
        Check(CustodyLedger.Verify(image.Journal, image.Anchor) == (op == SyntheticOperation.Delete ?
            LedgerPhase.CommittedAbsent : LedgerPhase.CommittedUnverified));
        Check(image.Marker == (op == SyntheticOperation.Delete ? 0 : 1));
        Check(owner.Control(CoreControl.Cancel) == CoreControlResult.TooLatePossibleEffect);
        Terminal(owner, Success(op), 1);
    }
    private static void Precondition(SyntheticOperation op)
    {
        var owner = new CustodyTransactionCore(new InMemoryCustodyFixture(op == SyntheticOperation.Add ?
            SyntheticSeed.Present : SyntheticSeed.Absent), Request(op), SyntheticCrash.None);
        Terminal(owner, CoreOutcome.Denied, 0);
        Check(!owner.Observe().MayHaveEffect && !owner.Observe().RecoveryRequired);
    }
    private static SyntheticTransactionRequest Alter(SyntheticOperation op, int kind)
    {
        return kind == 0 ? null : new SyntheticTransactionRequest(kind == 1 ? Guid.Empty :
            kind == 2 ? new Guid("33333333-3333-3333-3333-333333333333") : Id,
            kind == 3 ? 0 : kind == 4 ? 2 : 1, kind == 5 ? 0UL : kind == 6 ? 2UL : 1UL,
            kind == 7 ? (SyntheticOperation)99 : kind == 8 ?
            (op == SyntheticOperation.Add ? SyntheticOperation.Delete : SyntheticOperation.Add) : op);
    }
    private static void Identity(SyntheticOperation op, int kind)
    {
        CustodyTransactionCore owner = Create(op, SyntheticCrash.None);
        Check(owner.ReviewSynthetic(Alter(op, kind)) == null);
        Terminal(owner, CoreOutcome.Denied, 0);
        owner = Create(op, SyntheticCrash.None);
        object ticket = Review(owner, op);
        Check(owner.DispatchSynthetic(ticket, Alter(op, kind)) == CoreOutcome.Denied);
        Terminal(owner, CoreOutcome.Denied, 0);
    }
    private static void ControlFirst(SyntheticOperation op, CoreControl control)
    {
        foreach (bool reviewed in new[] { false, true })
        {
            CustodyTransactionCore owner = Create(op, SyntheticCrash.None);
            object ticket = reviewed ? Review(owner, op) : null;
            SyntheticCustodyImage before = owner.CaptureSyntheticCrashImage();
            Check(owner.Control(control) == CoreControlResult.Applied);
            CoreOutcome outcome = control == CoreControl.Cancel ? CoreOutcome.Cancelled : control == CoreControl.Revoke ?
                CoreOutcome.Revoked : control == CoreControl.Stop ? CoreOutcome.Stopped : CoreOutcome.Faulted;
            Check(owner.DispatchSynthetic(ticket, Request(op)) == outcome);
            Terminal(owner, outcome, 0);
            Check(!owner.Observe().MayHaveEffect && !owner.Observe().RecoveryRequired);
            Check(owner.Control(control) == CoreControlResult.AlreadyTerminal);
            SyntheticCustodyImage after = owner.CaptureSyntheticCrashImage();
            Check(before.Journal == after.Journal && before.Anchor == after.Anchor &&
                after.Request == null && before.Marker == after.Marker);
        }
    }
    private static void Crash(SyntheticOperation op, SyntheticCrash point)
    {
        CustodyTransactionCore owner = Create(op, point);
        object ticket = Review(owner, op);
        Check(owner.DispatchSynthetic(ticket, Request(op)) == CoreOutcome.RecoveryRequired);
        bool attempted = point >= SyntheticCrash.AfterAttempt;
        Terminal(owner, CoreOutcome.RecoveryRequired, attempted ? 1 : 0);
        Check(owner.Observe().MayHaveEffect == attempted && owner.Observe().RecoveryRequired);
        SyntheticCustodyImage image = owner.CaptureSyntheticCrashImage();
        RestartAssessment expected = point == SyntheticCrash.BeforeIntent ?
            (op == SyntheticOperation.Add ? RestartAssessment.InitialUnqualified : RestartAssessment.Malformed) :
            point == SyntheticCrash.AfterIdentity || point == SyntheticCrash.AfterIntentJournal ||
            point == SyntheticCrash.AfterTerminalJournal ? RestartAssessment.Malformed :
            point >= SyntheticCrash.AfterTerminalAnchor ? RestartAssessment.TerminalUnverified : RestartAssessment.InFlight;
        Check(CustodyTransactionCore.AssessRestart(image) == expected);
        // Repeated classification is read-only and never yields permission or retry authority.
        Check(CustodyTransactionCore.AssessRestart(image) == expected);
        Check(owner.Observe().Attempts == (attempted ? 1 : 0));
    }
    private sealed class Worker
    {
        private readonly Thread thread;
        private Exception error;
        internal Worker(Action action)
        {
            thread = new Thread(() => { try { action(); } catch (Exception caught) { error = caught; } });
            thread.IsBackground = true; thread.Start();
        }
        internal void Join() { Check(thread.Join(7000)); if (error != null) throw new Exception("worker failed", error); }
    }
    private static void Set(CustodyTransactionCore owner, string name, object value)
    { typeof(CustodyTransactionCore).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic).SetValue(owner, value); }
    private static object Get(CustodyTransactionCore owner, string name)
    { return typeof(CustodyTransactionCore).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic).GetValue(owner); }
    private static void DispatchFirst(SyntheticOperation op, CoreControl control)
    {
        CustodyTransactionCore owner = Create(op, SyntheticCrash.None);
        object ticket = Review(owner, op);
        using (var entered = new ManualResetEventSlim())
        using (var release = new ManualResetEventSlim())
        using (var waiting = new ManualResetEventSlim())
        {
            Set(owner, "dispatchEntered", entered); Set(owner, "dispatchContinue", release); Set(owner, "controlWaiting", waiting);
            CoreOutcome result = CoreOutcome.None;
            CoreControlResult publication = CoreControlResult.HoldUnknown;
            var dispatch = new Worker(() => { result = owner.DispatchSynthetic(ticket, Request(op)); });
            Worker contender = null;
            try
            {
                Check(entered.Wait(1500));
                // Fixed rendezvous establishes happens-before; inspect only while dispatch is paused.
                Check((CustodyStage)Get(owner, "stage") == CustodyStage.IntentDurable &&
                    (int)Get(owner, "attempts") == 0 && !(bool)Get(owner, "possible"));
                Check(CustodyLedger.Verify((string)Get(owner, "journal"), (string)Get(owner, "anchor")) == LedgerPhase.InFlight);
                contender = new Worker(() => { publication = owner.Control(control); });
                Check(waiting.Wait(1000));
            }
            finally { release.Set(); dispatch.Join(); if (contender != null) contender.Join(); }
            Check(result == Success(op) && publication == CoreControlResult.TooLatePossibleEffect);
            Terminal(owner, Success(op), 1);
        }
    }
    private static void DuplicateRace(SyntheticOperation op)
    {
        CustodyTransactionCore owner = Create(op, SyntheticCrash.None);
        object ticket = Review(owner, op);
        CoreOutcome first = CoreOutcome.None, second = CoreOutcome.None;
        using (var start = new ManualResetEventSlim())
        {
            var a = new Worker(() => { Check(start.Wait(1500)); first = owner.DispatchSynthetic(ticket, Request(op)); });
            var b = new Worker(() => { Check(start.Wait(1500)); second = owner.DispatchSynthetic(ticket, Request(op)); });
            start.Set(); a.Join(); b.Join();
        }
        Check(first == Success(op) && second == Success(op)); Terminal(owner, Success(op), 1);
    }
    private static void ReviewRace(SyntheticOperation op, bool cancel)
    {
        var owner = Create(op, SyntheticCrash.None);
        object first = null, second = null;
        CoreControlResult control = CoreControlResult.HoldUnknown;
        using (var start = new ManualResetEventSlim())
        {
            var a = new Worker(() => { Check(start.Wait(1500)); first = owner.ReviewSynthetic(Request(op)); });
            var b = new Worker(() => { Check(start.Wait(1500));
                if (cancel) control = owner.Control(CoreControl.Cancel);
                else second = owner.ReviewSynthetic(Request(op)); });
            start.Set(); a.Join(); b.Join();
        }
        if (cancel)
        {
            Check(control == CoreControlResult.Applied);
            Check(owner.DispatchSynthetic(first, Request(op)) == CoreOutcome.Cancelled);
            Terminal(owner, CoreOutcome.Cancelled, 0);
        }
        else
        {
            Check((first == null) != (second == null));
            Check(owner.DispatchSynthetic(first ?? second, Request(op)) == Success(op));
            Terminal(owner, Success(op), 1);
        }
    }
    private static void MalformedRestart()
    {
        Check(CustodyTransactionCore.AssessRestart(null) == RestartAssessment.Uncertain);
        CustodyTransactionCore owner = Create(SyntheticOperation.Add, SyntheticCrash.None);
        Check(CustodyTransactionCore.AssessRestart(owner.CaptureSyntheticCrashImage()) == RestartAssessment.InitialUnqualified);
        object ticket = Review(owner, SyntheticOperation.Add);
        Check(owner.DispatchSynthetic(ticket, Request(SyntheticOperation.Add)) == CoreOutcome.StoredUnverified);
        SyntheticCustodyImage good = owner.CaptureSyntheticCrashImage();
        foreach (string journal in new[] { null, "", good.Journal.TrimEnd('\n'), good.Journal + "x", new string('x', 32769),
            good.Journal.Replace("COMMITTED_UNVERIFIED", "COMMITTED_ABSENT"), good.Journal.Replace("J2|", "J3|") })
            Check(CustodyTransactionCore.AssessRestart(new SyntheticCustodyImage(journal, good.Anchor,
                good.Request, good.Marker)) == RestartAssessment.Malformed);
        foreach (string anchor in new[] { null, "", good.Anchor + "x", new string('0', 64) })
            Check(CustodyTransactionCore.AssessRestart(new SyntheticCustodyImage(good.Journal, anchor,
                good.Request, good.Marker)) == RestartAssessment.Malformed);
        for (int kind = 0; kind < 9; kind++)
            Check(CustodyTransactionCore.AssessRestart(new SyntheticCustodyImage(good.Journal, good.Anchor,
                Alter(SyntheticOperation.Add, kind), good.Marker)) == RestartAssessment.Malformed);
        foreach (int marker in new[] { -1, 0, 2, Int32.MaxValue })
            Check(CustodyTransactionCore.AssessRestart(new SyntheticCustodyImage(good.Journal, good.Anchor,
                good.Request, marker)) == RestartAssessment.Malformed);
        Terminal(owner, CoreOutcome.StoredUnverified, 1);
    }
    private static void FixtureOwnership()
    {
        var fixture = new InMemoryCustodyFixture(SyntheticSeed.Absent);
        var owner = new CustodyTransactionCore(fixture, Request(SyntheticOperation.Add), SyntheticCrash.None);
        bool refused = false;
        try { new CustodyTransactionCore(fixture, Request(SyntheticOperation.Add), SyntheticCrash.None); }
        catch (InvalidOperationException) { refused = true; }
        Check(refused && owner.Observe().Stage == CustodyStage.ReviewPending);
        for (int kind = 0; kind < 9; kind++)
        {
            if (kind == 2 || kind == 6 || kind == 8) continue; // valid new identities/operations
            var invalid = new CustodyTransactionCore(new InMemoryCustodyFixture(SyntheticSeed.Absent),
                Alter(SyntheticOperation.Add, kind), SyntheticCrash.None);
            Terminal(invalid, CoreOutcome.Denied, 0);
        }
        var max = new CustodyTransactionCore(new InMemoryCustodyFixture(SyntheticSeed.Absent),
            new SyntheticTransactionRequest(Id, 1, UInt64.MaxValue, SyntheticOperation.Add), SyntheticCrash.None);
        object ticket = max.ReviewSynthetic(max.Observe().Request);
        Check(max.DispatchSynthetic(ticket, max.Observe().Request) == CoreOutcome.StoredUnverified);
        Terminal(max, CoreOutcome.StoredUnverified, 1);
        var badCrash = new CustodyTransactionCore(new InMemoryCustodyFixture(SyntheticSeed.Absent),
            Request(SyntheticOperation.Add), (SyntheticCrash)99);
        Terminal(badCrash, CoreOutcome.Denied, 0);
    }
    private static void ForeignReview()
    {
        var a = Create(SyntheticOperation.Add, SyntheticCrash.None);
        var b = Create(SyntheticOperation.Add, SyntheticCrash.None);
        object foreign = Review(a, SyntheticOperation.Add);
        Review(b, SyntheticOperation.Add);
        Check(b.DispatchSynthetic(foreign, Request(SyntheticOperation.Add)) == CoreOutcome.Denied);
        Terminal(b, CoreOutcome.Denied, 0);
        var c = Create(SyntheticOperation.Add, SyntheticCrash.None);
        Check(c.DispatchSynthetic(new object(), Request(SyntheticOperation.Add)) == CoreOutcome.Denied);
        Terminal(c, CoreOutcome.Denied, 0);
    }
    private static void Reentry()
    {
        var owner = Create(SyntheticOperation.Add, SyntheticCrash.None);
        object gate = typeof(CustodyTransactionCore).GetField("gate", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(owner);
        lock (gate) { Check(owner.Control(CoreControl.Cancel) == CoreControlResult.HoldUnknown); }
        Terminal(owner, CoreOutcome.RecoveryRequired, 0);
    }
    private static void Timeout()
    {
        var owner = Create(SyntheticOperation.Add, SyntheticCrash.None);
        object ticket = Review(owner, SyntheticOperation.Add);
        using (var entered = new ManualResetEventSlim())
        using (var release = new ManualResetEventSlim())
        {
            Set(owner, "dispatchEntered", entered); Set(owner, "dispatchContinue", release);
            CoreOutcome result = CoreOutcome.None;
            var dispatch = new Worker(() => { result = owner.DispatchSynthetic(ticket, Request(SyntheticOperation.Add)); });
            try { Check(entered.Wait(1500)); Check(owner.Control(CoreControl.Revoke) == CoreControlResult.HoldUnknown); }
            finally { release.Set(); dispatch.Join(); }
            Check(result == CoreOutcome.RecoveryRequired);
            Terminal(owner, CoreOutcome.RecoveryRequired, 0);
            Check(!owner.Observe().MayHaveEffect && owner.Observe().RecoveryRequired);
            Check(CustodyTransactionCore.AssessRestart(owner.CaptureSyntheticCrashImage()) == RestartAssessment.InFlight);
        }
    }
    private static void InvalidControl()
    {
        var owner = Create(SyntheticOperation.Add, SyntheticCrash.None);
        Check(owner.Control((CoreControl)99) == CoreControlResult.HoldUnknown);
        Terminal(owner, CoreOutcome.RecoveryRequired, 0);
    }
    private static int Main(string[] args)
    {
        try
        {
            Check(args.Length == 0);
            foreach (SyntheticOperation op in new[] { SyntheticOperation.Add, SyntheticOperation.Replace, SyntheticOperation.Delete })
            {
                Run(() => Lifecycle(op)); Run(() => Precondition(op));
                for (int kind = 0; kind < 9; kind++) { int captured = kind; Run(() => Identity(op, captured)); }
                foreach (CoreControl control in new[] { CoreControl.Cancel, CoreControl.Revoke, CoreControl.Stop, CoreControl.Fault })
                { Run(() => ControlFirst(op, control)); Run(() => DispatchFirst(op, control)); }
                foreach (SyntheticCrash crash in new[] { SyntheticCrash.BeforeIntent, SyntheticCrash.AfterIdentity,
                    SyntheticCrash.AfterIntentJournal, SyntheticCrash.AfterIntentAnchor, SyntheticCrash.BeforeEffect,
                    SyntheticCrash.AfterAttempt, SyntheticCrash.AfterMutation, SyntheticCrash.AfterTerminalJournal,
                    SyntheticCrash.AfterTerminalAnchor, SyntheticCrash.AfterTerminalVerify })
                    Run(() => Crash(op, crash));
                Run(() => DuplicateRace(op));
                Run(() => ReviewRace(op, false)); Run(() => ReviewRace(op, true));
            }
            Run(MalformedRestart); Run(FixtureOwnership); Run(ForeignReview); Run(Reentry); Run(Timeout); Run(InvalidControl);
            Check(cases == 102);
            Console.WriteLine("P320 TRANSACTION CORE TESTS PASS count=102 synthetic-only"); return 0;
        }
        catch { Console.Error.WriteLine("P320 FAIL; HOLD"); return 1; }
    }
}
