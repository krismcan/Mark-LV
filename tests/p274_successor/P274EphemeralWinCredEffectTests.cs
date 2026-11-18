#if !DEBUG
#error P274_TESTS_NO_RELEASE_BUILD
#endif
#if !C1_P268_DEVELOPMENT_ONLY
#error P274_TESTS_REQUIRE_P268_DEVELOPMENT_ONLY
#endif
#if !C1_P274_EPHEMERAL_WINCRED_ONLY
#error P274_TESTS_EPHEMERAL_OPT_IN_REQUIRED
#endif
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Threading;
using System.Web.Script.Serialization;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P268Development;
using Nayeon.ByokC1.P274Development;

internal static class P274EphemeralWinCredEffectTests
{
    private static int cases, checks;
    private static void Demand(bool condition, string reason)
    { Interlocked.Increment(ref checks); if (!condition) throw new Exception("P274 " + reason); }
    private static void Reject(Action action)
    { bool rejected = false; try { action(); } catch (InvalidOperationException) { rejected = true; } Demand(rejected, "negative rejected"); }
    private static void Join(Thread thread)
    { if ((thread.ThreadState & ThreadState.Unstarted) == 0) Demand(thread.Join(3000), "thread deadline"); }
    private static void Run(string name, Action test)
    { test(); cases++; Console.WriteLine("PASS " + name); }
    private sealed class Fixture
    {
        internal readonly P96ApprovalFixture Approval = new P96ApprovalFixture();
        internal readonly P96StateFixture State;
        internal readonly P96GuardFixture Guard;
        internal readonly DevelopmentPendingState Adapter;
        internal readonly ServiceOwnedPendingTransaction Service;
        internal readonly ServiceOwnedPendingTransaction.Approval Ticket;
        internal readonly LedgerOperation Op;
        internal Fixture(P274EphemeralWinCredEffect effect, LedgerOperation op)
        {
            Op = op; State = new P96StateFixture(Approval); Guard = new P96GuardFixture(Approval);
            if (op != LedgerOperation.Save)
            {
                effect.SeedFor(op);
                State.Journal = CustodyLedger.AppendTerminal(CustodyLedger.AppendIntent(
                    State.Journal, LedgerOperation.Save, new string('b', 32)));
                State.Anchor = CustodyLedger.Anchor(State.Journal); State.Present = true;
            }
            Adapter = new DevelopmentPendingState(State);
            Service = ServiceOwnedPendingTransaction.DevelopmentOnlyHost(Adapter, Guard, true);
            Ticket = Service.IssueDevelopmentApproval(op);
            Demand(Ticket != null, "development ticket");
        }
        internal CustodyOutcome Apply()
        { return Service.Apply(Ticket, Op, Op == LedgerOperation.Delete ? null : P96Fixture.Dummy(), Op == LedgerOperation.Delete); }
        internal ControlResult Control(int reason)
        { return reason == 0 ? Service.Revoke() : reason == 1 ? Service.Stop() : Service.Fault(); }
        internal void NoReplay(P274EphemeralWinCredEffect effect)
        {
            int native = effect.TerminalCalls, fake = State.PossibleEffects;
            CustodyOutcome again = Apply();
            Demand(again == CustodyOutcome.Denied || again == CustodyOutcome.RecoveryRequired, "replay refused");
            Demand(effect.TerminalCalls == native && State.PossibleEffects == fake, "no native or fixture replay");
            Demand(Service.IssueDevelopmentApproval(Op) == null, "cannot rearm");
            Demand(Approval.Checks == 0 && Approval.ConsumeCount == 0, "caller fixture is not authority");
        }
        internal void AssertEntry()
        {
            // Observation only: never acquire/release/change the frozen private gate or latch.
            const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
            object gate = typeof(ServiceOwnedPendingTransaction).GetField("gate", flags).GetValue(Service);
            bool latched = (bool)typeof(ServiceOwnedPendingTransaction).GetField("mayHaveEffect", flags).GetValue(Service);
            Demand(Monitor.IsEntered(gate) && latched, "actual P268 gate and mayHaveEffect at native entry");
            Demand(CustodyLedger.Verify(State.Journal, State.Anchor) == LedgerPhase.InFlight, "verified InFlight before OS");
            Demand(Adapter.JournalWrites == 1 && Adapter.AnchorWrites == 1, "intent pair written before OS");
        }
    }
    private static void ControlFirst(LedgerOperation op, int reason)
    {
        using (var effect = new P274EphemeralWinCredEffect())
        {
            var f = new Fixture(effect, op);
            f.Adapter.Inject = point => { if (point == "effect-enter") { f.AssertEntry(); effect.Execute(op, op == LedgerOperation.Delete ? null : P96Fixture.Dummy()); } };
            ControlResult control = ControlResult.TooLate;
            Exception error = null;
            var closer = new Thread(() => { try { control = f.Control(reason); } catch (Exception e) { error = e; } });
            closer.IsBackground = true; closer.Start(); Join(closer);
            Demand(error == null && control == (reason == 0 ? ControlResult.Revoked : reason == 1 ? ControlResult.Stopped : ControlResult.RecoveryRequired), "control committed first");
            f.Approval.Revoke();
            CustodyOutcome outcome = CustodyOutcome.StoredUnverified;
            var writer = new Thread(() => { try { outcome = f.Apply(); } catch (Exception e) { error = e; } });
            writer.IsBackground = true; writer.Start(); Join(writer);
            Demand(error == null && outcome == (reason == 2 ? CustodyOutcome.RecoveryRequired : CustodyOutcome.Denied), "control-first apply refusal");
            Demand(effect.TerminalCalls == 0 && f.State.PossibleEffects == 0 && !f.Service.MayHaveEffect, "zero gated effects");
            Demand(f.Adapter.JournalWrites == 0 && f.Adapter.AnchorWrites == 0, "no intent on refusal");
            effect.Verify(op != LedgerOperation.Save); f.NoReplay(effect);
        }
    }
    private static void EffectFirst(LedgerOperation op, int reason, bool throwAfterNative)
    {
        using (var effect = new P274EphemeralWinCredEffect())
        using (var entered = new ManualResetEvent(false))
        using (var release = new ManualResetEvent(false))
        using (var attempting = new ManualResetEvent(false))
        using (var completed = new ManualResetEvent(false))
        {
            var f = new Fixture(effect, op);
            int nativeFinished = 0;
            Exception writerError = null, controlError = null;
            f.Adapter.Inject = point =>
            {
                if (point != "effect-enter") return;
                f.AssertEntry(); entered.Set();
                Demand(release.WaitOne(2500), "effect release deadline");
                Demand(!completed.WaitOne(0), "control cannot finish before OS");
                effect.Execute(op, op == LedgerOperation.Delete ? null : P96Fixture.Dummy());
                Volatile.Write(ref nativeFinished, 1);
                Demand(!completed.WaitOne(0), "control cannot finish during native readback under gate");
                if (throwAfterNative) throw new InvalidOperationException("P274_UNCERTAIN_AFTER_NATIVE_SUCCESS");
            };
            CustodyOutcome outcome = CustodyOutcome.Denied;
            ControlResult control = ControlResult.Revoked;
            var writer = new Thread(() => { try { outcome = f.Apply(); } catch (Exception e) { writerError = e; } });
            var closer = new Thread(() =>
            {
                attempting.Set();
                try { control = f.Control(reason); f.Approval.Revoke(); }
                catch (Exception e) { controlError = e; }
                finally { completed.Set(); }
            });
            writer.IsBackground = true; closer.IsBackground = true;
            try
            {
                writer.Start(); Demand(entered.WaitOne(2500), "frozen callback entered");
                closer.Start(); Demand(attempting.WaitOne(2500), "control thread attempting");
                // Well below P268's frozen 500ms admission timeout; an overrun fails, never retries.
                Demand(!completed.WaitOne(25), "control blocked by actual gate");
            }
            finally { release.Set(); try { Join(writer); } finally { Join(closer); } }
            Demand(writerError == null && controlError == null, "bounded threads no exception");
            Demand(Volatile.Read(ref nativeFinished) == 1 && effect.TerminalCalls == 1, "one real successful native call and readback");
            Demand(control == ControlResult.TooLate && completed.WaitOne(0), "effect-first control TooLate");
            Demand(f.Service.MayHaveEffect && f.Service.RecoveryRequired, "sticky uncertainty");
            effect.Verify(op != LedgerOperation.Delete);
            if (throwAfterNative)
            {
                Demand(outcome == CustodyOutcome.RecoveryRequired, "successful native then throw requires recovery");
                Demand(CustodyLedger.Verify(f.State.Journal, f.State.Anchor) == LedgerPhase.InFlight, "uncertain result leaves intent");
                Demand(f.State.PossibleEffects == 0 && !f.Guard.TerminalMarked && f.Guard.LeaseDisposed, "native happened before fixture; lease faulted");
                Demand(f.Guard.Fault && f.Adapter.JournalWrites == 1 && f.Adapter.AnchorWrites == 1, "no terminal writes on uncertainty");
            }
            else
            {
                Demand(outcome == (op == LedgerOperation.Delete ? CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified), "unverified terminal result");
                Demand(f.State.PossibleEffects == 1 && f.State.EffectsAfterRevoke == 0, "frozen fixture completes before control");
                Demand(f.Guard.TerminalMarked && f.Guard.LeaseDisposed && f.Adapter.JournalWrites == 2 && f.Adapter.AnchorWrites == 2, "terminal pair and lease");
                Demand(CustodyLedger.Verify(f.State.Journal, f.State.Anchor) == (op == LedgerOperation.Delete ? LedgerPhase.CommittedAbsent : LedgerPhase.CommittedUnverified), "terminal ledger verified");
            }
            f.NoReplay(effect);
        }
    }
    private static void HostNegatives()
    {
        var env = new Dictionary<string, string> {
            { "GITHUB_ACTIONS", "true" }, { "RUNNER_OS", "Windows" }, { "RUNNER_ENVIRONMENT", "github-hosted" },
            { "GITHUB_REPOSITORY", "krismcan/Mark-LV" }, { "GITHUB_EVENT_NAME", "pull_request" },
            { "P274_NATIVE_AUTH", "DISPOSABLE_HOSTED_SYNTHETIC_ONLY" },
            { "P274_HEAD_SHA", new string('a', 40) }, { "P274_BASE_SHA", P274EphemeralWinCredEffect.BaseSha },
            { "GITHUB_HEAD_REF", P274EphemeralWinCredEffect.HeadBranch }, { "GITHUB_BASE_REF", P274EphemeralWinCredEffect.BaseBranch },
            { "GITHUB_REF", "refs/pull/274/merge" } };
        var parser = new JavaScriptSerializer();
        string json = parser.Serialize(new { repository = new { full_name = "krismcan/Mark-LV" },
            pull_request = new { number = 274, draft = true,
                head = new { @ref = P274EphemeralWinCredEffect.HeadBranch, sha = new string('a', 40), repo = new { full_name = "krismcan/Mark-LV" } },
                @base = new { @ref = P274EphemeralWinCredEffect.BaseBranch, sha = P274EphemeralWinCredEffect.BaseSha, repo = new { full_name = "krismcan/Mark-LV" } } } });
        P274EphemeralWinCredEffect.ValidateContext(env, json, true, false);
        foreach (string key in new List<string>(env.Keys))
        {
            string old = env[key]; env[key] = "wrong";
            Reject(() => P274EphemeralWinCredEffect.ValidateContext(env, json, true, false)); env[key] = old;
        }
        Reject(() => P274EphemeralWinCredEffect.ValidateContext(env, json, false, false));
        Reject(() => P274EphemeralWinCredEffect.ValidateContext(env, json, true, true));
        Reject(() => P274EphemeralWinCredEffect.ValidateContext(env, json.Replace("\"draft\":true", "\"draft\":false"), true, false));
        Reject(() => P274EphemeralWinCredEffect.ValidateContext(env, json.Replace("krismcan/Mark-LV", "other/fork"), true, false));
        Reject(() => P274EphemeralWinCredEffect.ValidateContext(env, json.Replace(new string('a', 40), new string('b', 40)), true, false));
        Reject(() => P274EphemeralWinCredEffect.ValidateContext(env, new string(' ', 262145), true, false));
        Reject(() => P274EphemeralWinCredEffect.ValidateContext(env, "{}", true, false));
    }
    private static void CandidateNegatives()
    {
        foreach (LedgerOperation op in new[] { LedgerOperation.Save, LedgerOperation.Replace })
        {
            Demand(P274EphemeralWinCredEffect.ValidCandidate(op, P96Fixture.Dummy()), "literal accepted");
            foreach (byte[] value in new[] { null, new byte[0], new byte[4], new byte[] { 0x31, 0x32, 0x33, 0x35 }, new byte[5] })
                Demand(!P274EphemeralWinCredEffect.ValidCandidate(op, value), "invalid bytes rejected");
        }
        Demand(P274EphemeralWinCredEffect.ValidCandidate(LedgerOperation.Delete, null), "null delete");
        Demand(!P274EphemeralWinCredEffect.ValidCandidate(LedgerOperation.Delete, P96Fixture.Dummy()) &&
            !P274EphemeralWinCredEffect.ValidCandidate((LedgerOperation)99, P96Fixture.Dummy()), "invalid op/delete rejected");
    }
    private static void BindingNegatives()
    {
        for (int mode = 0; mode < 5; mode++)
        using (var effect = new P274EphemeralWinCredEffect())
        {
            var f = new Fixture(effect, LedgerOperation.Save);
            Reject(() => effect.Execute(LedgerOperation.Save, new byte[4]));
            Reject(() => effect.Execute(LedgerOperation.Delete, new byte[0]));
            f.Adapter.Inject = point => { if (point == "effect-enter") { f.AssertEntry(); effect.Execute(LedgerOperation.Save, P96Fixture.Dummy()); } };
            var ticket = f.Ticket;
            LedgerOperation op = LedgerOperation.Save; byte[] bytes = P96Fixture.Dummy(); bool ack = false;
            if (mode == 0) ticket = new ServiceOwnedPendingTransaction.Approval(op);
            if (mode == 1) { op = LedgerOperation.Delete; bytes = null; ack = true; }
            if (mode == 2) bytes = new byte[4];
            if (mode == 3) ack = true;
            if (mode == 4) ticket = null;
            Demand(f.Service.Apply(ticket, op, bytes, ack) == CustodyOutcome.Denied, "binding refusal");
            // Foreign/missing tickets do not consume the genuine ticket: close before probing replay.
            Demand(f.Service.Stop() == ControlResult.Stopped, "close unused valid ticket");
            Demand(effect.TerminalCalls == 0 && f.State.PossibleEffects == 0, "negative no OS effect");
            effect.Verify(false); f.NoReplay(effect);
        }
    }
    private static int Main(string[] args)
    {
        try
        {
            Demand(args.Length == 0, "no target or data arguments");
            P274EphemeralWinCredEffect.RequireHosted();
            Run("host-negatives-no-native", HostNegatives);
            Run("candidate-negatives-no-native", CandidateNegatives);
            Run("binding-negatives", BindingNegatives);
            foreach (LedgerOperation op in new[] { LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete })
            for (int reason = 0; reason < 3; reason++)
            {
                LedgerOperation selected = op; int control = reason;
                Run("control-first-" + op + "-" + reason, () => ControlFirst(selected, control));
                Run("effect-first-" + op + "-" + reason, () => EffectFirst(selected, control, false));
                Run("native-success-then-throw-" + op + "-" + reason, () => EffectFirst(selected, control, true));
            }
            Console.WriteLine("P274_EPHEMERAL=PASS CASES=" + cases + " ASSERTIONS=" + checks + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P274_DEVELOPMENT_OS_TIMING_ONLY PRODUCTION_P96=HOLD REAL_KEYS=NO_GO PRODUCT_REGRESSIONS=0/3");
            return 0;
        }
        catch (Exception error) { Console.WriteLine("P274_HOLD=" + error.GetType().Name); return 1; }
    }
}
