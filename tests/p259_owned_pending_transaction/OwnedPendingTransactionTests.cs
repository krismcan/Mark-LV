// Windows-thread tests of P259's owned integer algorithm. No original P96 link.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P259 requires isolated synthetic review and is NONDEPLOYABLE
#endif
using System;
using System.Reflection;
using System.Threading;
using Nayeon.P259.ReviewOnly;

internal static class OwnedPendingTransactionTests
{
    private static int passed, failed;
    private const BindingFlags PrivateInstance = BindingFlags.NonPublic | BindingFlags.Instance;

    private static void Need(bool condition, string reason)
    {
        if (!condition) throw new InvalidOperationException(reason);
    }

    private static void Run(string name, Action test)
    {
        try
        {
            test();
            ++passed;
            Console.WriteLine("PASS " + name);
        }
        catch (Exception error)
        {
            ++failed;
            Console.WriteLine("FAIL " + name + " " + error.GetType().Name + " " + error.Message);
        }
    }

    private sealed class Worker
    {
        private readonly Thread thread;
        private Exception error;
        internal Worker(Action action)
        {
            thread = new Thread(() =>
            {
                try { action(); }
                catch (Exception caught) { error = caught; }
            });
            thread.IsBackground = true;
            thread.Start();
        }
        internal void Join()
        {
            Need(thread.Join(5000), "Windows thread did not finish");
            if (error != null) throw new InvalidOperationException("worker failed", error);
        }
        internal void WaitForBlockedGate()
        {
            var timer = System.Diagnostics.Stopwatch.StartNew();
            while ((thread.ThreadState & ThreadState.WaitSleepJoin) == 0)
            {
                Need(thread.IsAlive && timer.ElapsedMilliseconds < 2000,
                    "contender did not block on owned gate");
                Thread.Yield();
            }
        }
        internal void InterruptBlockedGateWait()
        {
            WaitForBlockedGate();
            thread.Interrupt();
        }
    }

    private static void SetProbe(P259OwnedPendingTransaction owner, string field,
        ManualResetEventSlim probe)
    {
        typeof(P259OwnedPendingTransaction).GetField(field, PrivateInstance).SetValue(owner, probe);
    }

    private static void CheckEffect(Snapshot state, FakeOperation operation, int count)
    {
        Need(state.Consumed && state.Recovery, "one-use and recovery must be sticky");
        Need(state.Attempts == count, "wrong fixed dispatch count");
        Need(state.Saves == (operation == FakeOperation.Save ? count : 0), "wrong save count");
        Need(state.Replacements == (operation == FakeOperation.Replace ? count : 0),
            "wrong replacement count");
        Need(state.Deletes == (operation == FakeOperation.Delete ? count : 0), "wrong delete count");
        int expected = operation == FakeOperation.Save ? 17 : operation == FakeOperation.Replace ? 23 : 0;
        Need(state.Marker == expected, "wrong fixed integer mutation");
    }

    private static void CheckPublished(Snapshot state, Lifecycle signal)
    {
        Need(state.Consumed, "publication must invalidate request");
        Need(state.Revoked == (signal == Lifecycle.Revoke || signal == Lifecycle.Stop),
            "revocation publication missing");
        Need(state.Stopped == (signal == Lifecycle.Stop), "stop publication missing");
        Need(state.Faulted == (signal == Lifecycle.Fault), "fault publication missing");
    }

    private static void PublicationFirst(FakeOperation operation, Lifecycle signal)
    {
        var owner = new P259OwnedPendingTransaction(operation);
        new Worker(() =>
        {
            Publication result = owner.Publish(signal);
            Need(result == (signal == Lifecycle.Fault ? Publication.RecoveryRequired :
                Publication.ZeroFakeEffects), "wrong first publication result");
        }).Join();
        new Worker(() =>
        {
            Need(owner.Apply() == (signal == Lifecycle.Fault ? Outcome.RecoveryRequired :
                Outcome.Denied), "completed publication must deny dispatch");
        }).Join();
        Snapshot state = owner.Read();
        CheckPublished(state, signal);
        Need(state.Attempts == 0 && state.Saves == 0 && state.Replacements == 0 &&
            state.Deletes == 0 && state.DispatchOrder == 0, "publication-first produced effect");
        Need(state.Marker == (operation == FakeOperation.Save ? 0 : 1), "marker changed");
        owner.Apply();
        Need(owner.Read().Attempts == 0, "publication-first replay produced effect");
    }

    private static void EffectFirst(FakeOperation operation, Lifecycle signal)
    {
        var owner = new P259OwnedPendingTransaction(operation);
        using (var entered = new ManualResetEventSlim())
        using (var release = new ManualResetEventSlim())
        using (var waiting = new ManualResetEventSlim())
        using (var publicationReturned = new ManualResetEventSlim())
        using (var completed = new ManualResetEventSlim())
        {
            SetProbe(owner, "dispatchEntered", entered);
            SetProbe(owner, "dispatchContinue", release);
            SetProbe(owner, "publicationWaiting", waiting);
            var effect = new Worker(() => Need(owner.Apply() == Outcome.RecoveryRequired,
                "integer effect cannot report stored success"));
            Worker publisher = null;
            try
            {
                Need(entered.Wait(2000), "effect did not enter owned gate");
                publisher = new Worker(() =>
                {
                    Publication result = owner.Publish(signal);
                    publicationReturned.Set();
                    Need(result == Publication.TooLatePossibleEffect,
                        "publication falsely claimed zero effects");
                    Snapshot atReturn = owner.Read();
                    Need(atReturn.Attempts == 1 && atReturn.DispatchOrder > 0 &&
                        atReturn.PublicationOrder > atReturn.DispatchOrder,
                        "publication completed before dispatch");
                    completed.Set();
                });
                Need(waiting.Wait(2000), "publication did not contend");
                // The contender event precedes gate acquisition. Observe the worker
                // actually blocked while dispatch remains paused inside that gate.
                // Check Publish's return before Read can block on the same gate.
                publisher.WaitForBlockedGate();
                Need((int)typeof(P259OwnedPendingTransaction).GetField("attempts", PrivateInstance)
                    .GetValue(owner) == 0, "dispatch pause occurred too late");
                Need(!publicationReturned.IsSet, "publication returned while dispatch owned gate");
                Need(!completed.IsSet, "publication observation completed while dispatch owned gate");
            }
            finally
            {
                release.Set();
                effect.Join();
                if (publisher != null) publisher.Join();
                SetProbe(owner, "dispatchEntered", null);
                SetProbe(owner, "dispatchContinue", null);
                SetProbe(owner, "publicationWaiting", null);
            }
            Need(publicationReturned.IsSet && completed.IsSet, "publication completion missing");
        }
        Snapshot state = owner.Read();
        CheckEffect(state, operation, 1);
        CheckPublished(state, signal);
        Need(owner.Apply() == Outcome.RecoveryRequired, "replay must stay in recovery");
        Need(owner.Read().Attempts == 1, "replay dispatched twice");
    }

    private static void ConcurrentOneUse(FakeOperation operation)
    {
        var owner = new P259OwnedPendingTransaction(operation);
        using (var start = new ManualResetEventSlim())
        {
            var workers = new Worker[8];
            for (int index = 0; index < workers.Length; ++index)
                workers[index] = new Worker(() =>
                {
                    Need(start.Wait(2000), "duplicate start barrier failed");
                    Need(owner.Apply() == Outcome.RecoveryRequired, "unexpected duplicate result");
                });
            start.Set();
            foreach (Worker worker in workers) worker.Join();
        }
        CheckEffect(owner.Read(), operation, 1);
    }

    private static void Failure(FakeOperation operation, FakeFailure failure)
    {
        var owner = new P259OwnedPendingTransaction(operation, failure);
        Need(owner.Apply() == Outcome.RecoveryRequired, "failed work must recover");
        Snapshot state = owner.Read();
        int attempts = failure == FakeFailure.BeforeDispatch ? 0 : 1;
        int mutations = failure == FakeFailure.AfterMutation ? 1 : 0;
        Need(state.Consumed && state.Recovery && state.Faulted && state.Attempts == attempts,
            "failed request lost uncertainty");
        Need(state.Saves + state.Replacements + state.Deletes == mutations,
            "incorrect partial mutation evidence");
        Need(owner.Apply() == Outcome.RecoveryRequired && owner.Read().Attempts == attempts,
            "failure retried");
        Publication publication = owner.Publish(Lifecycle.Revoke);
        Need(publication == (attempts == 0 ? Publication.RecoveryRequired :
            Publication.TooLatePossibleEffect), "uncertainty was reported as clean revocation");
    }

    private static void Reentrancy(FakeOperation operation, int entry)
    {
        var owner = new P259OwnedPendingTransaction(operation);
        MethodInfo enter = typeof(P259OwnedPendingTransaction).GetMethod("EnterGate", PrivateInstance);
        MethodInfo exit = typeof(P259OwnedPendingTransaction).GetMethod("ExitGate", PrivateInstance);
        Need((bool)enter.Invoke(owner, null), "test could not hold private gate");
        try
        {
            if (entry == 0)
                Need(owner.Apply() == Outcome.RecoveryRequired, "recursive apply accepted");
            else if (entry == 1)
                Need(owner.Publish(Lifecycle.Revoke) == Publication.RecoveryRequired,
                    "recursive publication claimed completion");
            else
            {
                bool rejected = false;
                try { owner.Read(); }
                catch (InvalidOperationException) { rejected = true; }
                Need(rejected, "recursive observation accepted");
            }
        }
        finally { exit.Invoke(owner, null); }
        Need(owner.Apply() == Outcome.RecoveryRequired, "recursive request revived");
        Snapshot state = owner.Read();
        Need(state.Consumed && state.Recovery && state.Faulted && state.Attempts == 0 &&
            !state.Revoked, "reentry must poison without false revoke completion");
    }

    private static void InterruptedRequest(FakeOperation operation)
    {
        var owner = new P259OwnedPendingTransaction(operation);
        MethodInfo enter = typeof(P259OwnedPendingTransaction).GetMethod("EnterGate", PrivateInstance);
        MethodInfo exit = typeof(P259OwnedPendingTransaction).GetMethod("ExitGate", PrivateInstance);
        Need((bool)enter.Invoke(owner, null), "test could not hold gate");
        Worker waiter = null;
        try
        {
            waiter = new Worker(() => Need(owner.Apply() == Outcome.RecoveryRequired,
                "interrupted admission did not return recovery"));
            // Apply's only blocking wait at this point is the held private gate.
            waiter.InterruptBlockedGateWait();
        }
        finally
        {
            exit.Invoke(owner, null);
            if (waiter != null) waiter.Join();
        }
        Snapshot state = owner.Read();
        Need(state.Consumed && state.Recovery && state.Faulted && state.Attempts == 0,
            "interrupted request was left reusable");
        Need(owner.Apply() == Outcome.RecoveryRequired && owner.Read().Attempts == 0,
            "interrupted request replay dispatched");
    }

    public static int Main()
    {
        if (Environment.OSVersion.Platform != PlatformID.Win32NT)
        {
            Console.WriteLine("P259_REQUIRES_WINDOWS_THREADS");
            return 2;
        }
        foreach (FakeOperation operation in Enum.GetValues(typeof(FakeOperation)))
        {
            foreach (Lifecycle signal in Enum.GetValues(typeof(Lifecycle)))
            {
                Run(operation + "-" + signal + "-first", () => PublicationFirst(operation, signal));
                Run(operation + "-effect-first-" + signal, () => EffectFirst(operation, signal));
            }
            Run(operation + "-eight-concurrent-one-use", () => ConcurrentOneUse(operation));
            Run(operation + "-interrupted-admission", () => InterruptedRequest(operation));
            foreach (FakeFailure failure in new[] { FakeFailure.BeforeDispatch,
                FakeFailure.AfterAttempt, FakeFailure.AfterMutation })
                Run(operation + "-" + failure, () => Failure(operation, failure));
            for (int entry = 0; entry < 3; ++entry)
            {
                int captured = entry;
                Run(operation + "-reentry-" + entry, () => Reentrancy(operation, captured));
            }
            Run(operation + "-restart-recovery", () =>
            {
                var owner = new P259OwnedPendingTransaction(operation, FakeFailure.None,
                    SyntheticHistory.Restart);
                Need(owner.Apply() == Outcome.RecoveryRequired && owner.Read().Attempts == 0,
                    "restart fabricated fresh authority");
            });
        }
        Run("invalid-bound-operation", () =>
        {
            var owner = new P259OwnedPendingTransaction((FakeOperation)99);
            Need(owner.Apply() == Outcome.RecoveryRequired && owner.Read().Attempts == 0,
                "invalid operation reached effect");
        });
        Run("invalid-failure-scenario", () =>
        {
            var owner = new P259OwnedPendingTransaction(FakeOperation.Save, (FakeFailure)99);
            Need(owner.Apply() == Outcome.RecoveryRequired && owner.Read().Attempts == 0,
                "invalid scenario reached effect");
        });
        Run("invalid-history", () =>
        {
            var owner = new P259OwnedPendingTransaction(FakeOperation.Save, FakeFailure.None,
                (SyntheticHistory)99);
            Need(owner.Apply() == Outcome.RecoveryRequired && owner.Read().Attempts == 0,
                "invalid history bootstrapped authority");
        });
        Run("invalid-lifecycle-poisons-request", () =>
        {
            var owner = new P259OwnedPendingTransaction(FakeOperation.Delete);
            Need(owner.Publish((Lifecycle)99) == Publication.RecoveryRequired,
                "invalid publication claimed completion");
            Need(owner.Apply() == Outcome.RecoveryRequired && owner.Read().Attempts == 0,
                "invalid lifecycle permitted dispatch");
        });
        Console.WriteLine("P259_POINTER_BITS=" + (IntPtr.Size * 8));
        Console.WriteLine("P259_PASSED=" + passed);
        Console.WriteLine("P259_FAILED=" + failed);
        Console.WriteLine("P259_REVIEW_ONLY_P96_PRODUCTION_OPEN_RELEASE_HOLD");
        return failed == 0 && passed == 49 ? 0 : 1;
    }
}
