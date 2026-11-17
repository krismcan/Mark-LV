// NONDEPLOYABLE P96 correction comparator. All effects are private integers.
// No consent, service principal, credential store or durable journal is supplied.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P259 requires isolated synthetic review and is NONDEPLOYABLE
#endif
using System;
using System.Threading;

namespace Nayeon.P259.ReviewOnly
{
    internal enum FakeOperation { Save, Replace, Delete }
    internal enum FakeFailure { None, BeforeDispatch, AfterAttempt, AfterMutation }
    internal enum SyntheticHistory { Fresh, Restart }
    internal enum Lifecycle { Revoke, Stop, Fault }
    internal enum Outcome { Denied, RecoveryRequired }
    internal enum Publication { ZeroFakeEffects, TooLatePossibleEffect, RecoveryRequired }

    internal sealed class Snapshot
    {
        internal readonly bool Consumed, Recovery, Revoked, Stopped, Faulted;
        internal readonly int Attempts, Saves, Replacements, Deletes, Marker;
        internal readonly long DispatchOrder, PublicationOrder;

        internal Snapshot(bool consumed, bool recovery, bool revoked, bool stopped,
            bool faulted, int attempts, int saves, int replacements, int deletes,
            int marker, long dispatchOrder, long publicationOrder)
        {
            Consumed = consumed;
            Recovery = recovery;
            Revoked = revoked;
            Stopped = stopped;
            Faulted = faulted;
            Attempts = attempts;
            Saves = saves;
            Replacements = replacements;
            Deletes = deletes;
            Marker = marker;
            DispatchOrder = dispatchOrder;
            PublicationOrder = publicationOrder;
        }
    }

    // One instance owns exactly one immutable synthetic request. No preparation
    // result, approval boolean, lease or effect port can escape or be supplied.
    internal sealed class P259OwnedPendingTransaction
    {
        private readonly SemaphoreSlim gate = new SemaphoreSlim(1, 1);
        private int ownerThread;
        private readonly FakeOperation operation;
        private readonly FakeFailure failure;
        private bool consumed, recovery, revoked, stopped, faulted;
        private int attempts, saves, replacements, deletes, marker;
        private long order, dispatchOrder, publicationOrder;

        // Private test rendezvous only. The driver sets these through reflection.
        // They can pause a fixed path, never choose or perform an effect.
        private ManualResetEventSlim dispatchEntered;
        private ManualResetEventSlim dispatchContinue;
        private ManualResetEventSlim publicationWaiting;

        internal P259OwnedPendingTransaction(FakeOperation operation,
            FakeFailure failure = FakeFailure.None,
            SyntheticHistory history = SyntheticHistory.Fresh)
        {
            this.operation = operation;
            this.failure = failure;
            marker = operation == FakeOperation.Save ? 0 : 1;
            recovery = history != SyntheticHistory.Fresh;
            if ((operation != FakeOperation.Save && operation != FakeOperation.Replace &&
                operation != FakeOperation.Delete) ||
                (failure != FakeFailure.None && failure != FakeFailure.BeforeDispatch &&
                failure != FakeFailure.AfterAttempt && failure != FakeFailure.AfterMutation) ||
                (history != SyntheticHistory.Fresh && history != SyntheticHistory.Restart))
            {
                faulted = true;
                recovery = true;
            }
        }

        // SemaphoreSlim itself cannot recursively enter. Detect the owning thread
        // before waiting, poison its request under its already-held gate, and fail
        // closed. Every mutable request/lifecycle/effect field uses this same gate.
        private bool EnterGate()
        {
            int current = Thread.CurrentThread.ManagedThreadId;
            if (Volatile.Read(ref ownerThread) == current)
            {
                consumed = true;
                recovery = true;
                faulted = true;
                return false;
            }
            bool interrupted = false;
            while (true)
            {
                try { gate.Wait(); break; }
                catch (ThreadInterruptedException) { interrupted = true; }
            }
            Volatile.Write(ref ownerThread, current);
            if (interrupted)
            {
                // Finish publishing uncertainty under the gate before returning.
                // An interrupted waiter cannot leave a reusable request behind.
                consumed = true;
                recovery = true;
                faulted = true;
                ExitGate();
                return false;
            }
            return true;
        }

        private void ExitGate()
        {
            Volatile.Write(ref ownerThread, 0);
            gate.Release();
        }

        internal Outcome Apply()
        {
            if (!EnterGate()) return Outcome.RecoveryRequired;
            try
            {
                if (consumed)
                    return recovery || faulted ? Outcome.RecoveryRequired : Outcome.Denied;
                consumed = true;
                if (recovery || faulted) return Outcome.RecoveryRequired;
                if (revoked || stopped) return Outcome.Denied;
                // Intent is in-memory only. Even a completed integer mutation
                // has no protected terminal proof, so recovery remains sticky.
                recovery = true;
                if (dispatchEntered != null) dispatchEntered.Set();
                if (dispatchContinue != null && !dispatchContinue.Wait(3000))
                    throw new TimeoutException();
                if (failure == FakeFailure.BeforeDispatch)
                    throw new InvalidOperationException();
                DispatchFixedIntegerEffect();
                return Outcome.RecoveryRequired;
            }
            catch (Exception)
            {
                faulted = true;
                recovery = true;
                return Outcome.RecoveryRequired;
            }
            finally { ExitGate(); }
        }

        // Called solely by Apply while the nonreentrant gate remains held.
        // No user-supplied code is consulted between admission and this mutation.
        private void DispatchFixedIntegerEffect()
        {
            dispatchOrder = ++order;
            ++attempts;
            if (failure == FakeFailure.AfterAttempt)
                throw new InvalidOperationException();
            switch (operation)
            {
                case FakeOperation.Save:
                    marker = 17;
                    ++saves;
                    break;
                case FakeOperation.Replace:
                    marker = 23;
                    ++replacements;
                    break;
                case FakeOperation.Delete:
                    marker = 0;
                    ++deletes;
                    break;
                default:
                    throw new InvalidOperationException();
            }
            if (failure == FakeFailure.AfterMutation)
                throw new InvalidOperationException();
        }

        internal Publication Publish(Lifecycle signal)
        {
            // This event announces a contender only. Publication completes below,
            // after acquiring the very gate held through fixed dispatch.
            if (publicationWaiting != null) publicationWaiting.Set();
            if (!EnterGate()) return Publication.RecoveryRequired;
            try
            {
                consumed = true;
                switch (signal)
                {
                    case Lifecycle.Revoke:
                        revoked = true;
                        break;
                    case Lifecycle.Stop:
                        stopped = true;
                        revoked = true;
                        break;
                    case Lifecycle.Fault:
                        faulted = true;
                        recovery = true;
                        break;
                    default:
                        faulted = true;
                        recovery = true;
                        return Publication.RecoveryRequired;
                }
                publicationOrder = ++order;
                if (attempts != 0)
                {
                    recovery = true;
                    return Publication.TooLatePossibleEffect;
                }
                return recovery ? Publication.RecoveryRequired : Publication.ZeroFakeEffects;
            }
            finally { ExitGate(); }
        }

        internal Snapshot Read()
        {
            if (!EnterGate()) throw new InvalidOperationException("P259 recursive read refused");
            try
            {
                return new Snapshot(consumed, recovery, revoked, stopped, faulted,
                    attempts, saves, replacements, deletes, marker,
                    dispatchOrder, publicationOrder);
            }
            finally { ExitGate(); }
        }
    }
}
