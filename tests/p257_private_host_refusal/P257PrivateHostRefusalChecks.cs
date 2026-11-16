// Library-only, unexecuted native review checks. Thread delegates and reflection
// belong solely to this fixture and are never passed into the owner.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !P257_EFFECT_FREE_REVIEW || C1_SYNTHETIC_TEST
#error P257 requires isolated effect-free review without synthetic dispatch
#endif
using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P257PrivateHostRefusalChecks
{
    private enum Input { Request, Revoke, Stop, Fault }

    private sealed class Worker
    {
        internal P257PrivateHostRefusalOwner Owner;
        internal Input Kind;
        internal ManualResetEvent Start;
        internal CustodyOutcome Outcome;
        internal Exception Failure;

        internal void Run()
        {
            try
            {
                if (!Start.WaitOne(2000)) throw new InvalidOperationException("start timeout");
                switch (Kind)
                {
                    case Input.Request: Outcome = Owner.RefuseRequest(NewUntrustedClaim()); break;
                    case Input.Revoke: Outcome = Owner.Revoke(); break;
                    case Input.Stop: Outcome = Owner.Stop(); break;
                    case Input.Fault: Outcome = Owner.Fault(); break;
                    default: throw new InvalidOperationException("unknown fixture input");
                }
            }
            catch (Exception error) { Failure = error; }
        }
    }

    private static void Require(bool condition)
    {
        if (!condition) throw new InvalidOperationException("P257 review check failed");
    }

    private static ServiceBoundRequestIdentity NewUntrustedClaim()
    {
        return new ServiceBoundRequestIdentity(LedgerOperation.Save,
            new string('a', 32), new string('b', 32), new string('c', 64),
            DateTime.UtcNow.AddMinutes(1).Ticks, false);
    }

    private static CustodyService Host(P257PrivateHostRefusalOwner owner)
    {
        return (CustodyService)typeof(P257PrivateHostRefusalOwner).GetField(
            "actualHost", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(owner);
    }

    private static void Join(Thread thread, Worker worker)
    {
        Require(thread.Join(2500));
        Require(worker.Failure == null);
        Require(worker.Outcome == CustodyOutcome.Denied ||
            worker.Outcome == CustodyOutcome.RecoveryRequired);
    }

    private static void Pair(Input signal, bool signalFirst, bool overlap)
    {
        using (var owner = new P257PrivateHostRefusalOwner())
        using (var start = new ManualResetEvent(false))
        {
            var request = new Worker { Owner = owner, Kind = Input.Request, Start = start };
            var lifecycle = new Worker { Owner = owner, Kind = signal, Start = start };
            Worker first = signalFirst ? lifecycle : request;
            Worker second = signalFirst ? request : lifecycle;
            var firstThread = new Thread(first.Run) { IsBackground = true };
            var secondThread = new Thread(second.Run) { IsBackground = true };
            firstThread.Start();
            if (overlap) secondThread.Start();
            start.Set();
            Join(firstThread, first);
            if (!overlap) secondThread.Start();
            Join(secondThread, second);

            CustodyService host = Host(owner);
            Require(host.GetType() == typeof(CustodyService));
            Require(host.TerminalEffectRefusals == 2);
            Require(host.DeniedPendingRequestCount == 2);
            Require(!host.NativeEffectEnabled && !host.AuthenticatedConsentAvailable &&
                !host.ProductionReleaseEligible && !owner.RealKeyAdmissible &&
                !owner.ProductionReleaseEligible && !owner.OsCustodyEstablished);
            if (signal == Input.Fault)
            {
                Require(lifecycle.Outcome == CustodyOutcome.RecoveryRequired);
                if (signalFirst && !overlap)
                    Require(request.Outcome == CustodyOutcome.RecoveryRequired);
                Require(owner.Stop() == CustodyOutcome.RecoveryRequired);
                Require(owner.Revoke() == CustodyOutcome.RecoveryRequired);
                Require(owner.RefuseRequest(null) == CustodyOutcome.RecoveryRequired);
            }
            else
            {
                Require(host.PendingAdmissionRevoked);
                Require(request.Outcome == CustodyOutcome.Denied);
                Require(lifecycle.Outcome == CustodyOutcome.Denied);
                Require(owner.Fault() == CustodyOutcome.RecoveryRequired);
            }
        }
    }

    // No Main, loader, runner or service entrypoint. Invocation requires separate
    // environment authorization. This method has NOT been run in P257.
    internal static void VerifyAll()
    {
        foreach (Input signal in new[] { Input.Revoke, Input.Stop, Input.Fault })
        {
            Pair(signal, true, false);
            Pair(signal, false, false);
            Pair(signal, false, true);
        }

        using (var owner = new P257PrivateHostRefusalOwner())
        {
            var claim = NewUntrustedClaim();
            Require(owner.RefuseRequest(claim) == CustodyOutcome.Denied);
            Require(owner.RefuseRequest(claim) == CustodyOutcome.Denied);
            Require(Host(owner).TerminalEffectRefusals == 2);
            Require(Host(owner).StructurallyRepeatedRequestCount == 1);
            object gate = typeof(P257PrivateHostRefusalOwner).GetField(
                "gate", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(owner);
            lock (gate)
            {
                foreach (Input input in new[] { Input.Request, Input.Revoke, Input.Stop, Input.Fault })
                using (var start = new ManualResetEvent(true))
                {
                    var recursive = new Worker { Owner = owner, Kind = input, Start = start };
                    recursive.Run();
                    Require(recursive.Failure is InvalidOperationException);
                    Require(Host(owner).TerminalEffectRefusals == 2);
                }
            }
            owner.Dispose();
            owner.Dispose();
            Require(Host(owner).TerminalEffectRefusals == 3);
            bool refused = false;
            try { owner.RefuseRequest(null); }
            catch (ObjectDisposedException) { refused = true; }
            Require(refused);
        }
    }
}
