using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1.Service;

// Executes only the selected production metadata sources. No ServiceBase, IPC,
// file journal, native API or effect implementation is linked into this driver.
internal static class HeldFailureServiceOrderingTests
{
    private static int cases;
    private static void Check(bool value) { if (!value) throw new Exception("held-failure assertion; HOLD"); }
    private static void Run(Action action) { action(); cases++; }
    private static SyntheticTransactionRequest Request(SyntheticTransactionOwner owner, ulong id, SyntheticOperation op)
    {
        SyntheticTransactionResult view = owner.Observe();
        return new SyntheticTransactionRequest(view.Owner, view.Epoch, id, op);
    }
    private static void Denied(SyntheticTransactionResult result)
    { Check(!result.Allowed && !result.MayHaveEffect && !result.DurableIntentQualified && result.Attempts == 0); }
    private static void Held(SyntheticTransactionResult result)
    {
        Denied(result);
        Check(result.RecoveryRequired && result.State == TransactionOwnerState.RecoveryHeld &&
            result.Disposition == TransactionDisposition.RecoveryRequired && result.OrderingOutcome == CoreOutcome.RecoveryRequired);
    }
    private static object Gate(SyntheticTransactionOwner owner)
    { return typeof(SyntheticTransactionOwner).GetField("gate", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(owner); }
    private static void Close(SyntheticTransactionOwner owner, int kind)
    {
        if (kind == 0) owner.Stop(); else if (kind == 1) owner.Shutdown();
        else if (kind == 2) owner.Fault(); else owner.Dispose();
    }
    private static void RefusedClose(SyntheticTransactionOwner owner, int kind)
    {
        bool refused = false;
        try { Close(owner, kind); }
        catch (InvalidOperationException) { refused = true; }
        Check(refused);
    }
    private static void Lifecycle(SyntheticOperation op, int kind)
    {
        var receipt = new DenialOnlyRecoveryAdmission(DurableRecoveryState.MissingLeaf);
        using (var owner = new SyntheticTransactionOwner(receipt))
        {
            SyntheticTransactionRequest request = Request(owner, 1, op);
            SyntheticTransactionResult first = owner.Deny(request);
            Denied(first);
            Check(first.Disposition == TransactionDisposition.Denied && first.OrderingOutcome == CoreOutcome.Denied &&
                Object.ReferenceEquals(first.Request, request) && !first.RecoveryRequired &&
                first.RecoveryAdmission == DurableIntentAdmission.DenialOnlyMissingLeaf);
            Check(owner.Cancel(request).Disposition == TransactionDisposition.Replay);
            SyntheticTransactionRequest second = Request(owner, 2, op);
            SyntheticTransactionResult cancel = owner.Cancel(second);
            Denied(cancel);
            Check(cancel.Disposition == TransactionDisposition.Cancelled && cancel.OrderingOutcome == CoreOutcome.Cancelled);
            Check(owner.Deny(second).Disposition == TransactionDisposition.Replay);
            Close(owner, kind);
            Denied(owner.Deny(second));
            Check(owner.Deny(second).Disposition == TransactionDisposition.OwnerTerminated && owner.Observe().Epoch == 2);
            Check(owner.Observe().OrderingOutcome == (kind == 2 ? CoreOutcome.Faulted : CoreOutcome.Stopped));
            Check(first.Epoch == 1 && first.State == TransactionOwnerState.ActiveDenied && !first.RecoveryRequired);
        }
    }
    private static void RecoveryOwnership()
    {
        var receipt = new DenialOnlyRecoveryAdmission(DurableRecoveryState.MissingLeaf);
        Check(!receipt.EffectAdmissionAllowed && !receipt.DurableIntentQualified);
        using (var first = new SyntheticTransactionOwner(receipt))
        using (var duplicate = new SyntheticTransactionOwner(receipt))
        using (var unknown = new SyntheticTransactionOwner((DenialOnlyRecoveryAdmission)null))
        using (var inFlightOrUnknown = new SyntheticTransactionOwner(new DenialOnlyRecoveryAdmission(DurableRecoveryState.InFlight)))
        {
            Check(first.Observe().State == TransactionOwnerState.ActiveDenied);
            Held(duplicate.Observe()); Held(unknown.Observe()); Held(inFlightOrUnknown.Observe());
            duplicate.Stop(); duplicate.Dispose(); Held(duplicate.Deny(null));
            // Retirement and a new identity cannot clear uncertainty on this owner.
            Held(unknown.Cancel(new SyntheticTransactionRequest(Guid.NewGuid(), 1, 1, SyntheticOperation.Add)));
            Check(first.Observe().Owner != duplicate.Observe().Owner);
        }
        foreach (DurableRecoveryState observation in new[] { DurableRecoveryState.Unknown, DurableRecoveryState.InFlight,
            DurableRecoveryState.TerminalUnverified, DurableRecoveryState.Malformed, (DurableRecoveryState)99 })
        using (var held = new SyntheticTransactionOwner(new DenialOnlyRecoveryAdmission(observation)))
        { Held(held.Observe()); held.Stop(); Held(held.Observe()); }
    }
    private static void Identity(SyntheticOperation op)
    {
        using (var owner = new SyntheticTransactionOwner())
        using (var other = new SyntheticTransactionOwner())
        {
            var valid = Request(owner, 1, op);
            Check(owner.Deny(null).Disposition == TransactionDisposition.InvalidRequest);
            Check(owner.Deny(Request(owner, 0, op)).Disposition == TransactionDisposition.InvalidRequest);
            Check(owner.Deny(Request(other, 9, op)).Disposition == TransactionDisposition.WrongOwner);
            Check(owner.Deny(new SyntheticTransactionRequest(valid.Owner, 2, 9, op)).Disposition == TransactionDisposition.StaleEpoch);
            Check(owner.Deny(Request(owner, 9, (SyntheticOperation)99)).Disposition == TransactionDisposition.InvalidOperation);
            Check(owner.Deny(valid).Disposition == TransactionDisposition.Denied);
            Check(owner.Deny(new SyntheticTransactionRequest(valid.Owner, valid.Epoch, valid.RequestId, op)).Disposition == TransactionDisposition.Replay);
            Check(owner.Deny(Request(owner, ulong.MaxValue, op)).Disposition == TransactionDisposition.Denied);
            Check(owner.Deny(valid).Disposition == TransactionDisposition.Replay);
        }
    }
    private static void Reentry(int route)
    {
        using (var owner = new SyntheticTransactionOwner())
        {
            var request = Request(owner, 1, SyntheticOperation.Add);
            SyntheticTransactionResult earlier = owner.Deny(request);
            lock (Gate(owner))
            {
                if (route == 0) Held(owner.Observe());
                else if (route == 1) Held(owner.Deny(request));
                else if (route == 2) Held(owner.Cancel(request));
                else RefusedClose(owner, route - 3);
            }
            Held(owner.Observe()); Held(owner.Deny(request)); Held(owner.Cancel(request));
            for (int kind = 0; kind < 4; kind++) { Close(owner, kind); Held(owner.Observe()); }
            Check(!earlier.RecoveryRequired && earlier.OrderingOutcome == CoreOutcome.Denied);
        }
    }
    private static void Timeout(int route)
    {
        using (var owner = new SyntheticTransactionOwner())
        {
            var request = Request(owner, 1, SyntheticOperation.Delete);
            Exception failure = null;
            var worker = new Thread(delegate()
            {
                try
                {
                    if (route == 0) Held(owner.Observe());
                    else if (route == 1) Held(owner.Deny(request));
                    else if (route == 2) Held(owner.Cancel(request));
                    else RefusedClose(owner, route - 3);
                }
                catch (Exception error) { failure = error; }
            });
            worker.IsBackground = true;
            lock (Gate(owner)) { worker.Start(); Check(worker.Join(6000)); }
            Check(failure == null);
            Held(owner.Observe()); Held(owner.Deny(request)); Held(owner.Cancel(request));
        }
    }
    private static void ExclusiveClaim()
    {
        var receipt = new DenialOnlyRecoveryAdmission(DurableRecoveryState.MissingLeaf);
        using (var start = new ManualResetEventSlim(false))
        {
            SyntheticTransactionOwner left = null, right = null;
            var a = new Thread(delegate() { start.Wait(); left = new SyntheticTransactionOwner(receipt); });
            var b = new Thread(delegate() { start.Wait(); right = new SyntheticTransactionOwner(receipt); });
            a.IsBackground = true; b.IsBackground = true;
            a.Start(); b.Start(); start.Set(); Check(a.Join(5000) && b.Join(5000));
            using (left) using (right)
            {
                Check(left.Observe().RecoveryRequired != right.Observe().RecoveryRequired);
                Denied(left.Observe()); Denied(right.Observe());
            }
        }
    }
    private static void Contention(SyntheticOperation op)
    {
        using (var owner = new SyntheticTransactionOwner())
        using (var start = new ManualResetEventSlim(false))
        {
            var request = Request(owner, 1, op);
            SyntheticTransactionResult left = null, right = null;
            var a = new Thread(delegate() { start.Wait(); left = owner.Deny(request); });
            var b = new Thread(delegate() { start.Wait(); right = owner.Cancel(request); });
            a.IsBackground = true; b.IsBackground = true;
            a.Start(); b.Start(); start.Set(); Check(a.Join(5000) && b.Join(5000));
            Denied(left); Denied(right);
            Check((left.Disposition == TransactionDisposition.Replay) != (right.Disposition == TransactionDisposition.Replay));
            Check(left.Disposition == TransactionDisposition.Denied || right.Disposition == TransactionDisposition.Cancelled);
        }
    }
    private static void Publication()
    {
        var before = new AtomicCustodyPublication();
        before.PublishUnknown(); Check(!before.TryCommitPossibleEffect()); before.Finish(CoreOutcome.Denied);
        Check(AtomicCustodyPublication.Outcome(before.Read()) == CoreOutcome.RecoveryRequired &&
            !AtomicCustodyPublication.MayHaveEffect(before.Read()));
        var after = new AtomicCustodyPublication();
        Check(after.TryCommitPossibleEffect()); after.Finish(CoreOutcome.StoredUnverified); after.PublishUnknown();
        after.Finish(CoreOutcome.Cancelled);
        Check(AtomicCustodyPublication.Outcome(after.Read()) == CoreOutcome.RecoveryRequired &&
            AtomicCustodyPublication.MayHaveEffect(after.Read()) && !after.TryCommitPossibleEffect());
        var terminal = new AtomicCustodyPublication();
        terminal.Finish(CoreOutcome.Cancelled); terminal.Finish(CoreOutcome.Denied);
        Check(!terminal.TryCommitPossibleEffect() && AtomicCustodyPublication.Outcome(terminal.Read()) == CoreOutcome.Cancelled);
    }
    private static void RetirementContention(SyntheticOperation op, int kind)
    {
        using (var owner = new SyntheticTransactionOwner())
        using (var start = new ManualResetEventSlim(false))
        {
            var request = Request(owner, 1, op);
            SyntheticTransactionResult deny = null, cancel = null;
            Exception failure = null;
            var a = new Thread(delegate() { start.Wait(); deny = owner.Deny(request); });
            var b = new Thread(delegate() { start.Wait(); cancel = owner.Cancel(request); });
            var c = new Thread(delegate() { start.Wait(); try { Close(owner, kind); } catch (Exception e) { failure = e; } });
            a.IsBackground = true; b.IsBackground = true; c.IsBackground = true;
            a.Start(); b.Start(); c.Start(); start.Set();
            Check(a.Join(5000) && b.Join(5000) && c.Join(5000) && failure == null);
            Denied(deny); Denied(cancel);
            Check(deny.Disposition == TransactionDisposition.Denied || deny.Disposition == TransactionDisposition.Replay ||
                deny.Disposition == TransactionDisposition.OwnerTerminated);
            Check(cancel.Disposition == TransactionDisposition.Cancelled || cancel.Disposition == TransactionDisposition.Replay ||
                cancel.Disposition == TransactionDisposition.OwnerTerminated);
            Check(!(deny.Disposition == TransactionDisposition.Denied && cancel.Disposition == TransactionDisposition.Cancelled));
            Check(owner.Deny(request).Disposition == TransactionDisposition.OwnerTerminated && owner.Observe().Epoch == 2);
        }
    }
    private static int Main(string[] args)
    {
        try
        {
            Check(args.Length == 0);
            foreach (SyntheticOperation op in new[] { SyntheticOperation.Add, SyntheticOperation.Replace, SyntheticOperation.Delete })
            {
                for (int kind = 0; kind < 4; kind++)
                { int captured = kind; Run(delegate { Lifecycle(op, captured); }); Run(delegate { RetirementContention(op, captured); }); }
                Run(delegate { Identity(op); }); Run(delegate { Contention(op); });
            }
            for (int route = 0; route < 7; route++)
            { int captured = route; Run(delegate { Reentry(captured); }); Run(delegate { Timeout(captured); }); }
            Run(RecoveryOwnership); Run(ExclusiveClaim); Run(Publication);
            Check(cases == 47);
            Console.WriteLine("HELD FAILURE SHARED SERVICE ORDERING PASS count=47 denial-only; production HOLD");
            return 0;
        }
        catch { Console.Error.WriteLine("HELD FAILURE SHARED SERVICE ORDERING FAIL; HOLD"); return 1; }
    }
}
