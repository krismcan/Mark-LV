// Isolated conceptual ordering model. NEVER a service, permit or effect adapter.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P247 NONDEPLOYABLE EFFECT-FREE TEST MODEL
#endif
using System;
using System.Collections.Generic;
using System.Threading;

namespace Nayeon.P247.EffectFree
{
    internal enum Category { Store, Replace, Delete }
    internal enum Phase { Unprepared, Prepared, Cancelled, MayHaveEffect }
    internal enum Decision { Prepared, Denied, Replay, ReentrantRejected,
        ZeroEffectDecision, MayHaveEffect, TooLateMayHaveEffect, RecoveryRequired }
    internal enum Signal { Revoke, Stop, Fault, TornJournal, InFlight, Abandoned, Crash, UnknownEffect }
    internal enum Startup { Missing, CleanClaim, TornJournal, InFlight, Abandoned, Crash, Unknown }

    // Value identity only, never authentication or human consent. No payload.
    internal sealed class Operation
    {
        internal readonly long Id;
        internal readonly Category Category;
        internal Operation(long id, Category category) { Id = id; Category = category; }
    }

    internal sealed class Snapshot
    {
        internal readonly Phase Phase;
        internal readonly bool RecoveryRequired, Revoked, Stopped;
        internal readonly int DispatchDecisions, ReservedIds;
        internal Snapshot(Phase phase, bool recovery, bool revoked, bool stopped, int count, int ids)
        { Phase = phase; RecoveryRequired = recovery; Revoked = revoked; Stopped = stopped;
          DispatchDecisions = count; ReservedIds = ids; }
    }

    internal sealed class OrderingOwner
    {
        private readonly object gate = new object();
        private readonly HashSet<long> reserved = new HashSet<long>();
        private Phase phase;
        private Operation prepared;
        private bool attempted, recovery, revoked, stopped;
        private int decisions;

        private OrderingOwner(bool freshSynthetic) { recovery = !freshSynthetic; }
        // Test scenario construction only. Not startup, installation or enrolment.
        internal static OrderingOwner FreshSyntheticScenario() { return new OrderingOwner(true); }
        internal static OrderingOwner Restart(Startup untrustedHistory)
        {
            // Even a claimed clean history cannot establish durable custody.
            return new OrderingOwner(false);
        }

        internal Decision Prepare(Operation operation)
        {
            if (Monitor.IsEntered(gate)) return Decision.ReentrantRejected;
            lock (gate)
            {
                if (operation == null || operation.Id <= 0 ||
                    !Enum.IsDefined(typeof(Category), operation.Category)) return Decision.Denied;
                if (reserved.Contains(operation.Id)) return Decision.Replay;
                if (reserved.Count == 128) return Decision.Denied; // never evict IDs
                reserved.Add(operation.Id); // consume even refused IDs; category cannot rebind
                if (recovery) return Decision.RecoveryRequired;
                if (revoked || stopped || phase != Phase.Unprepared) return Decision.Denied;
                prepared = operation;
                phase = Phase.Prepared;
                return Decision.Prepared;
            }
        }

        internal Decision DispatchDecision(Operation operation)
        {
            if (Monitor.IsEntered(gate)) return Decision.ReentrantRejected;
            lock (gate)
            {
                if (prepared == null || operation == null || operation.Id != prepared.Id)
                    return recovery ? Decision.RecoveryRequired : Decision.Denied;
                if (attempted) return Decision.Replay;
                attempted = true; // first attempt consumes even a category mismatch
                if (operation.Category != prepared.Category) return Decision.Denied;
                if (recovery) return Decision.RecoveryRequired;
                if (revoked || stopped || phase == Phase.Cancelled) return Decision.ZeroEffectDecision;
                if (phase != Phase.Prepared) return Decision.Denied;
                // THE conceptual linearisation point: fixed metadata assignments only.
                // No terminal call follows, and this return value grants no authority.
                phase = Phase.MayHaveEffect;
                ++decisions;
                recovery = true; // no durability or terminal verification exists
                return Decision.MayHaveEffect;
            }
        }

        internal Decision Publish(Signal signal)
        {
            if (Monitor.IsEntered(gate)) return Decision.ReentrantRejected;
            lock (gate)
            {
                if (!Enum.IsDefined(typeof(Signal), signal))
                { recovery = true; return Decision.RecoveryRequired; }
                if (signal == Signal.Revoke || signal == Signal.Stop) revoked = true;
                if (signal == Signal.Stop) stopped = true;
                if (signal != Signal.Revoke && signal != Signal.Stop) recovery = true;
                if (phase == Phase.MayHaveEffect)
                { recovery = true; return Decision.TooLateMayHaveEffect; }
                phase = Phase.Cancelled;
                return recovery ? Decision.RecoveryRequired : Decision.ZeroEffectDecision;
            }
        }

        internal Decision ObserveSyntheticRecoveryOnly()
        {
            if (Monitor.IsEntered(gate)) return Decision.ReentrantRejected;
            lock (gate)
            {
                recovery = true; // inspection cannot repair/re-enrol/retry
                return Decision.RecoveryRequired;
            }
        }

        internal Snapshot Read()
        {
            lock (gate)
                return new Snapshot(phase, recovery, revoked, stopped, decisions, reserved.Count);
        }
    }
}
