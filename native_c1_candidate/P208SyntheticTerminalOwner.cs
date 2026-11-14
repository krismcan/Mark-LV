// P208: TEST-ONLY native synthetic terminal integration. Not a production
// service, consent broker, WinCred dispatcher, signed executable or IPC.
// Entire class compiles away without C1_SYNTHETIC_TEST. No credential bytes,
// callbacks, external adapter, file IO, P/Invoke, or caller-selected target.
// Existing ServiceOwnedAdmissionBoundary and frozen P49 are unchanged.
#if C1_SYNTHETIC_TEST
using System;

namespace Nayeon.ByokC1
{
    internal sealed class P208SyntheticTerminalOwner
    {
        private enum Phase
        {
            Empty, Prepared, Revoked, RecoveryRequired
        }

        // Opaque reference identity is an in-process TEST aid, not a
        // cryptographic human approval, service permit or a bearer token.
        internal sealed class SyntheticReview
        {
            internal SyntheticReview() { }
        }

        private readonly object gate = new object();
        private readonly CustodyService host = new CustodyService();
        private readonly string fixedTarget =
            "nayeon-v1/secret/openai.api_key";
        private Phase phase = Phase.Empty;
        private SyntheticReview pending;
        private LedgerOperation boundOperation;
        private int refusalCount;
        private int attemptCount;

        internal string FixedTarget { get { return fixedTarget; } }
        internal bool NativeEffectEnabled { get { return host.NativeEffectEnabled; } }
        internal bool AuthenticatedConsentAvailable
        { get { return host.AuthenticatedConsentAvailable; } }
        internal bool ProductionReleaseEligible
        { get { return host.ProductionReleaseEligible; } }
        internal int SyntheticEffectAttempts
        { get { lock(gate) { return host.SyntheticEffectAttempts; } } }
        internal int SyntheticUnknownOutcomes
        { get { lock(gate) { return host.SyntheticUnknownEffectOutcomes; } } }
        internal int Refusals { get { lock(gate) { return refusalCount; } } }

        // Explicit synthetic test request, NOT a UI signature or approval.
        // This is deliberately restricted to one fixed target and 3 enums.
        internal SyntheticReview PrepareForTestOnly(
            LedgerOperation operation, bool destructiveAcknowledged)
        {
            lock (gate)
            {
                if (phase != Phase.Empty)
                {
                    ++refusalCount;
                    return null;
                }
                bool valid = ((operation == LedgerOperation.Save ||
                               operation == LedgerOperation.Replace) &&
                               !destructiveAcknowledged) ||
                             (operation == LedgerOperation.Delete &&
                               destructiveAcknowledged);
                if (!valid)
                {
                    ++refusalCount;
                    return null;
                }
                try
                {
                    host.PrepareSyntheticFixedEffectOnly(
                        operation, destructiveAcknowledged);
                }
                catch (Exception)
                {
                    host.FaultPendingAdmission();
                    phase = Phase.RecoveryRequired;
                    ++refusalCount;
                    return null;
                }
                boundOperation = operation;
                pending = new SyntheticReview();
                phase = Phase.Prepared;
                return pending;
            }
        }

        // One terminal attempt under this exact owner lock. The unchanged
        // native host's own lock is also acquired during fake effect.
        // There are no user-supplied callbacks, WinCred APIs or key bytes.
        internal CustodyOutcome AttemptForTestOnly(
            SyntheticReview review, LedgerOperation operation,
            bool simulateUnknownNativeResult)
        {
            lock (gate)
            {
                if (phase == Phase.RecoveryRequired)
                    return CustodyOutcome.RecoveryRequired;
                if (phase != Phase.Prepared)
                {
                    ++refusalCount;
                    return CustodyOutcome.Denied;
                }
                if (review == null || !object.ReferenceEquals(review, pending)
                    || operation != boundOperation)
                {
                    // Forged / cross-operation attempts cannot leave a
                    // successor review live to inherit the wrong consent.
                    host.RevokePendingAdmission();
                    pending = null;
                    phase = Phase.Revoked;
                    ++refusalCount;
                    return CustodyOutcome.Denied;
                }
                pending = null; // consume before entering effect boundary
                phase = Phase.RecoveryRequired; // pessimistic: no retry
                ++attemptCount;
                try
                {
                    host.AttemptSyntheticFixedEffectOnly(
                        operation, null, null, simulateUnknownNativeResult);
                }
                catch (Exception)
                {
                    host.FaultPendingAdmission();
                }
                // An integer fake effect is NEVER evidence of credential
                // durability or terminal success; G3/journal still missing.
                return CustodyOutcome.RecoveryRequired;
            }
        }

        internal void Revoke()
        {
            lock (gate)
            {
                host.RevokePendingAdmission();
                pending = null;
                if (phase != Phase.RecoveryRequired)
                    phase = Phase.Revoked;
            }
        }

        internal void Fault()
        {
            lock (gate)
            {
                host.FaultPendingAdmission();
                pending = null;
                phase = Phase.RecoveryRequired;
            }
        }

        internal void Stop()
        {
            lock (gate)
            {
                host.RevokePendingAdmission();
                host.FaultPendingAdmission();
                pending = null;
                phase = Phase.RecoveryRequired;
            }
        }

        internal int AttemptCount
        { get { lock (gate) { return attemptCount; } } }
        internal bool RequiresReconciliation
        { get { lock (gate) { return phase == Phase.RecoveryRequired; } } }
        internal bool Revoked
        { get { lock (gate) { return phase == Phase.Revoked; } } }
    }
}
#endif
