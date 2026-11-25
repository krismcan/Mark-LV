using System.Threading;

namespace Nayeon.ByokC1.Service
{
    internal enum DurableIntentAdmission { Unqualified, DenialOnlyMissingLeaf, RecoveryHold }
    internal enum DurableRecoveryState { Unknown, MissingLeaf, InFlight, TerminalUnverified, Malformed }

    // One-use ownership of a metadata observation, NOT proof of durable intent or
    // exclusive OS custody. No production durable writer/recovery issuer exists.
    // A future intent contract must bind immutable request + owner epoch, retained
    // storage identity, flush/readback and restart evidence before commitment.
    // Missing leaf permits only denial; in-flight/terminal/unknown restart holds.
    internal sealed class DenialOnlyRecoveryAdmission
    {
        private int claimed;
        internal readonly DurableRecoveryState Observation;
        internal DenialOnlyRecoveryAdmission(DurableRecoveryState observation) { Observation = observation; }
        internal DurableIntentAdmission Claim()
        {
            if (Interlocked.CompareExchange(ref claimed, 1, 0) != 0 || Observation != DurableRecoveryState.MissingLeaf)
                return DurableIntentAdmission.RecoveryHold;
            return DurableIntentAdmission.DenialOnlyMissingLeaf;
        }
        internal bool EffectAdmissionAllowed { get { return false; } }
        internal bool DurableIntentQualified { get { return false; } }
    }
}
