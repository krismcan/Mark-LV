#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P247 NONDEPLOYABLE EFFECT-FREE TESTS
#endif
using System;
using System.Reflection;
using System.Threading;

namespace Nayeon.P247.EffectFree
{
    internal static class OrderingTests
    {
        private static int passed, failed;
        private static void Need(bool value) { if (!value) throw new Exception("assertion failed"); }
        private static void Run(string name, Action test)
        {
            try { test(); ++passed; Console.WriteLine("PASS " + name); }
            catch (Exception e) { ++failed; Console.WriteLine("FAIL " + name + " " + e); }
        }
        private static OrderingOwner Armed(Operation operation)
        {
            var owner = OrderingOwner.FreshSyntheticScenario();
            Need(owner.Prepare(operation) == Decision.Prepared);
            return owner;
        }
        // Sequentially released native threads force each linearisation order;
        // no timing/sleep inference, production hooks or callback inside owner.
        private static void OnThread(Action action)
        {
            Exception error = null;
            var thread = new Thread(() => { try { action(); } catch (Exception e) { error = e; } });
            thread.IsBackground = true;
            thread.Start();
            Need(thread.Join(2000));
            if (error != null) throw error;
        }
        internal static int Main()
        {
            foreach (Category category in Enum.GetValues(typeof(Category)))
            {
                foreach (Signal signal in new[] { Signal.Revoke, Signal.Stop, Signal.Fault })
                {
                    Run(category + "/" + signal + "-wins", () =>
                    {
                        var op = new Operation(1, category); var owner = Armed(op);
                        OnThread(() => Need(owner.Publish(signal) == (signal == Signal.Fault ?
                            Decision.RecoveryRequired : Decision.ZeroEffectDecision)));
                        OnThread(() => Need(owner.DispatchDecision(op) == (signal == Signal.Fault ?
                            Decision.RecoveryRequired : Decision.ZeroEffectDecision)));
                        Need(owner.Read().DispatchDecisions == 0);
                        Need(owner.Read().Revoked == (signal != Signal.Fault));
                        Need(owner.Read().Stopped == (signal == Signal.Stop));
                        Need(owner.DispatchDecision(op) == Decision.Replay);
                    });
                    Run(category + "/dispatch-wins-" + signal, () =>
                    {
                        var op = new Operation(1, category); var owner = Armed(op);
                        OnThread(() => Need(owner.DispatchDecision(op) == Decision.MayHaveEffect));
                        OnThread(() => Need(owner.Publish(signal) == Decision.TooLateMayHaveEffect));
                        Need(owner.Read().Phase == Phase.MayHaveEffect && owner.Read().RecoveryRequired);
                        Need(owner.Read().DispatchDecisions == 1);
                        Need(owner.DispatchDecision(op) == Decision.Replay);
                        Need(owner.ObserveSyntheticRecoveryOnly() == Decision.RecoveryRequired);
                        Need(owner.Prepare(new Operation(2, category)) == Decision.RecoveryRequired);
                    });
                }
                foreach (Signal failure in new[] { Signal.TornJournal, Signal.InFlight,
                    Signal.Abandoned, Signal.Crash, Signal.UnknownEffect })
                {
                    Run(category + "/" + failure + "/before-and-after", () =>
                    {
                        var op = new Operation(1, category); var before = Armed(op);
                        Need(before.Publish(failure) == Decision.RecoveryRequired);
                        Need(before.DispatchDecision(op) == Decision.RecoveryRequired);
                        Need(before.Read().DispatchDecisions == 0 && before.Read().RecoveryRequired);
                        Need(before.ObserveSyntheticRecoveryOnly() == Decision.RecoveryRequired);
                        Need(before.DispatchDecision(op) == Decision.Replay);
                        var after = Armed(op);
                        Need(after.DispatchDecision(op) == Decision.MayHaveEffect);
                        Need(after.Publish(failure) == Decision.TooLateMayHaveEffect);
                        Need(after.Read().Phase == Phase.MayHaveEffect && after.Read().RecoveryRequired);
                        Need(after.DispatchDecision(op) == Decision.Replay);
                    });
                }
                foreach (Category other in Enum.GetValues(typeof(Category)))
                    Run(category + "/rebind-or-replay/" + other, () =>
                    {
                        var op = new Operation(1, category); var owner = Armed(op);
                        Need(owner.Prepare(new Operation(1, other)) == Decision.Replay);
                        Need(owner.DispatchDecision(new Operation(1, other)) ==
                            (other == category ? Decision.MayHaveEffect : Decision.Denied));
                        Need(owner.DispatchDecision(op) == Decision.Replay);
                        Need(owner.Read().DispatchDecisions == (other == category ? 1 : 0));
                    });
            }
            foreach (Startup startup in Enum.GetValues(typeof(Startup)))
                Run("restart/" + startup, () =>
                {
                    var owner = OrderingOwner.Restart(startup); var op = new Operation(1, Category.Store);
                    Need(owner.Prepare(op) == Decision.RecoveryRequired);
                    Need(owner.DispatchDecision(op) == Decision.RecoveryRequired);
                    Need(owner.ObserveSyntheticRecoveryOnly() == Decision.RecoveryRequired);
                    Need(owner.Prepare(new Operation(2, Category.Delete)) == Decision.RecoveryRequired);
                    Need(owner.Read().RecoveryRequired && owner.Read().DispatchDecisions == 0);
                });
            Run("simultaneous-duplicate-prepare-and-dispatch", () =>
            {
                var owner = OrderingOwner.FreshSyntheticScenario(); var op = new Operation(1, Category.Store);
                Decision a = Decision.Denied, b = Decision.Denied;
                Pair(() => a = owner.Prepare(op), () => b = owner.Prepare(op));
                Need((a == Decision.Prepared && b == Decision.Replay) ||
                     (b == Decision.Prepared && a == Decision.Replay));
                Pair(() => a = owner.DispatchDecision(op), () => b = owner.DispatchDecision(op));
                Need((a == Decision.MayHaveEffect && b == Decision.Replay) ||
                     (b == Decision.MayHaveEffect && a == Decision.Replay));
                Need(owner.Read().DispatchDecisions == 1);
            });
            Run("reentrancy-refused-for-every-mutation", () =>
            {
                var op = new Operation(1, Category.Store); var owner = Armed(op);
                object gate = typeof(OrderingOwner).GetField("gate", BindingFlags.NonPublic |
                    BindingFlags.Instance).GetValue(owner);
                // Adversarial reflection exists ONLY in test driver, never owner API.
                lock (gate)
                {
                    Need(owner.Prepare(new Operation(2, Category.Delete)) == Decision.ReentrantRejected);
                    Need(owner.DispatchDecision(op) == Decision.ReentrantRejected);
                    foreach (Signal s in Enum.GetValues(typeof(Signal)))
                        Need(owner.Publish(s) == Decision.ReentrantRejected);
                    Need(owner.ObserveSyntheticRecoveryOnly() == Decision.ReentrantRejected);
                }
                Need(owner.Read().ReservedIds == 1 && owner.Read().Phase == Phase.Prepared);
                Need(owner.DispatchDecision(op) == Decision.MayHaveEffect);
            });
            Run("invalid-input-and-bounded-id-retention", () =>
            {
                var owner = OrderingOwner.Restart(Startup.Missing);
                Need(owner.Prepare(null) == Decision.Denied);
                Need(owner.Prepare(new Operation(0, Category.Store)) == Decision.Denied);
                Need(owner.Prepare(new Operation(1, (Category)999)) == Decision.Denied);
                for (int i = 1; i <= 128; ++i)
                    Need(owner.Prepare(new Operation(i, Category.Store)) == Decision.RecoveryRequired);
                Need(owner.Prepare(new Operation(129, Category.Store)) == Decision.Denied);
                Need(owner.Prepare(new Operation(1, Category.Delete)) == Decision.Replay);
                Need(owner.Read().ReservedIds == 128);
            });
            Run("unknown-signal-and-startup-fail-closed", () =>
            {
                var op = new Operation(1, Category.Delete); var owner = Armed(op);
                Need(owner.Publish((Signal)999) == Decision.RecoveryRequired);
                Need(owner.DispatchDecision(op) == Decision.RecoveryRequired);
                Need(OrderingOwner.Restart((Startup)999).Read().RecoveryRequired);
            });
            Run("model-has-no-effect-extension-port", () =>
            {
                foreach (Type t in new[] { typeof(OrderingOwner), typeof(Operation), typeof(Snapshot) })
                {
                    Need(t.IsSealed);
                    foreach (var m in t.GetMethods(BindingFlags.Instance | BindingFlags.Static |
                        BindingFlags.DeclaredOnly | BindingFlags.NonPublic | BindingFlags.Public))
                    {
                        Need((m.Attributes & MethodAttributes.PinvokeImpl) == 0);
                        foreach (var p in m.GetParameters())
                            Need(!typeof(Delegate).IsAssignableFrom(p.ParameterType) &&
                                p.ParameterType != typeof(byte[]) && p.ParameterType != typeof(string));
                    }
                }
            });
            Console.WriteLine("P247 PASSED=" + passed + " FAILED=" + failed);
            Console.WriteLine("EFFECT_FREE_MODEL_ONLY; P96_RACE_OPEN; REAL_KEY_NO_GO; RELEASE_HOLD");
            return passed == 54 && failed == 0 ? 0 : 1;
        }
        private static void Pair(Action first, Action second)
        {
            using (var ready = new CountdownEvent(2))
            using (var start = new ManualResetEvent(false))
            {
                Exception a = null, b = null;
                var t1 = new Thread(() => { try { ready.Signal(); Need(start.WaitOne(2000)); first(); }
                    catch (Exception e) { a = e; } });
                var t2 = new Thread(() => { try { ready.Signal(); Need(start.WaitOne(2000)); second(); }
                    catch (Exception e) { b = e; } });
                t1.IsBackground = t2.IsBackground = true;
                t1.Start(); t2.Start();
                bool bothReady = ready.Wait(2000); start.Set();
                bool done1 = t1.Join(2500), done2 = t2.Join(2500);
                Need(bothReady && done1 && done2 && a == null && b == null);
            }
        }
    }
}
