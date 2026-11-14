// P221: ISOLATED WINDOWS SECURITY-REVIEW fixture of the exact ORIGINAL P96
// PendingCustodyTransaction.Apply + the historical P96 fake-only state/lease.
// Demonstrates one shared admission/revocation critical section over that
// exact old call, NOT a production remediation, installer, signed service,
// credential effect, trusted consent or protected journal. Never link this
// source to a shipping binary or use the historical coordinator for real keys.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P221 original P96 review linearizer is NONDEPLOYABLE, test-only
#endif
using System;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class P221OriginalP96ReviewLinearizer
    {
        private readonly object gate = new object();
        private readonly P96Fixture original = new P96Fixture();
        private bool consumed;
        private bool revoked;
        private bool stopped;
        private bool faulted;
        private bool recoveryRequired;
        private int attempts;

        // This deliberately exposes only a FIXED original P96 fake SAVE
        // marker. No key, target, provider, arbitrary adapter or callback
        // can be passed to this review method. Test events can only pause.
        internal CustodyOutcome AttemptFakeSave(
            ManualResetEvent testEntered = null,
            ManualResetEvent testRelease = null)
        {
            lock (gate)
            {
                if (consumed || revoked || stopped)
                    return CustodyOutcome.Denied;
                if (faulted || recoveryRequired)
                    return CustodyOutcome.RecoveryRequired;
                consumed = true; // one attempt BEFORE any work or fake effect
                ++attempts;
                try
                {
                    if (testEntered != null) testEntered.Set();
                    if (testRelease != null && !testRelease.WaitOne(3000))
                        return CustodyOutcome.RecoveryRequired;

                    // The *actual* original P96 coordinator executes only
                    // with fake IProtectedPendingState and fake custody lease.
                    // All Revoke/Stop/Fault transitions through THIS object
                    // serialize with its final fake effect under gate.
                    CustodyOutcome old = original.ActualCoordinator.Apply(
                        LedgerOperation.Save, P96Fixture.Dummy());

                    // Neither the fixture nor legacy source proves a
                    // protected terminal or real service-owned effect.
                    // Even legacy "stored" never turns into a trusted GO.
                    if (old != CustodyOutcome.StoredUnverified &&
                        old != CustodyOutcome.RecoveryRequired &&
                        old != CustodyOutcome.Denied)
                        faulted = true;
                    return CustodyOutcome.RecoveryRequired;
                }
                catch (Exception)
                {
                    faulted = true;
                    return CustodyOutcome.RecoveryRequired;
                }
                finally
                {
                    recoveryRequired = true; // sticky no-retry on any attempt
                }
            }
        }

        internal void Revoke()
        {
            lock (gate)
            {
                revoked = true;
                original.Approval.Revoke();
            }
        }
        internal void Stop()
        {
            lock (gate)
            {
                stopped = true;
                revoked = true;
                original.Approval.Revoke();
            }
        }
        internal void Fault()
        {
            lock (gate)
            {
                faulted = true;
                recoveryRequired = true;
                original.Approval.Revoke();
            }
        }

        internal void MakeFakeCustodyUntrustedBeforeAttempt()
        {
            lock (gate)
            {
                if (consumed) throw new InvalidOperationException();
                original.State.Trusted = false; // fake test seam only
            }
        }
        internal void MakeFakeEffectUncertainBeforeAttempt()
        {
            lock (gate)
            {
                if (consumed) throw new InvalidOperationException();
                original.State.ThrowDuringEffect = true; // fake only
            }
        }
        internal int FakeEffects
        {
            get { lock (gate) { return original.State.PossibleEffects; } }
        }
        internal int FakeEffectsAfterCommittedRevoke
        {
            get { lock (gate) { return original.State.EffectsAfterRevoke; } }
        }
        internal int AttemptCount { get { lock (gate) { return attempts; } } }
        internal bool IsRevoked { get { lock (gate) { return revoked; } } }
        internal bool IsStopped { get { lock (gate) { return stopped; } } }
        internal bool RecoveryRequired
        {
            get { lock (gate) { return recoveryRequired; } }
        }

        internal bool ActualTrustedConsentIssuerAvailable { get { return false; } }
        internal bool ServiceAccountStoreVerified { get { return false; } }
        internal bool OriginalP96ProductionFixImplemented { get { return false; } }
        internal bool NativeCredentialEffectEnabled { get { return false; } }
        internal bool CodeIntegrityReleaseApproved { get { return false; } }
        internal bool ProductionReleaseEligible { get { return false; } }
    }
}
