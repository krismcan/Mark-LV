// P223: SOURCE-BOUND ADAPTER to the ACTUAL unchanged CustodyService denial-only
// admission. This is NOT a service process, native credential effect, installer,
// trusted consent issuer, signature policy, or remediation of historical P96.
// It cannot be compiled into a deployable production assembly: no service
// principal, protected journal, actual OS store or qualified G0/R3 exists.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P223 exact-host denial port is review-only, not production deployable
#endif
using System;

namespace Nayeon.ByokC1
{
    internal sealed class P223ActualHostNoEffectPort
    {
        private readonly object gate = new object();
        private readonly CustodyService actualHost;
        private int refusalCount;
        private bool reviewStopped;

        // Accept ONLY the existing exact native host, never a fake service
        // interface, delegate, effect callback, credential byte[] or target.
        internal P223ActualHostNoEffectPort(CustodyService actualHost)
        {
            if (actualHost == null || actualHost.GetType() != typeof(CustodyService))
                throw new ArgumentException("Exact original native C1 candidate host required");
            this.actualHost = actualHost;
        }

        // Actual original CustodyService still does all bound-request denial
        // and terminal-effect refusal. No second effect-admission decision
        // is introduced. The only caller data is nonsecret UNTRUSTED metadata.
        internal CustodyOutcome RefuseUntrustedRequest(ServiceBoundRequestIdentity claim)
        {
            lock (gate)
            {
                ++refusalCount;
                if (reviewStopped || actualHost.PendingAdmissionStopped ||
                    actualHost.PendingAdmissionRevoked)
                    return CustodyOutcome.Denied;
                if (actualHost.PendingAdmissionFaulted)
                    return CustodyOutcome.RecoveryRequired;
                if (!LocalReleaseHolds())
                    return CustodyOutcome.RecoveryRequired;

                // Both calls enter the EXACT existing service-owned
                // ServiceOwnedAdmissionBoundary, never original P96 Apply.
                // A valid-looking caller claim cannot become authorization.
                CustodyOutcome observed = actualHost.RefuseBoundPendingOperation(claim);
                CustodyOutcome terminal = actualHost.RefuseUnreviewedTerminalEffect();

                if (observed == CustodyOutcome.RecoveryRequired ||
                    terminal == CustodyOutcome.RecoveryRequired ||
                    actualHost.PendingAdmissionFaulted)
                    return CustodyOutcome.RecoveryRequired;
                return CustodyOutcome.Denied;
            }
        }

        internal void RevokeWithoutGrant()
        {
            lock (gate)
            {
                actualHost.RevokePendingAdmission();
            }
        }
        internal void FaultWithoutRetry()
        {
            lock (gate)
            {
                actualHost.FaultPendingAdmission();
            }
        }
        internal void StopReviewWithoutStartingService()
        {
            lock (gate)
            {
                reviewStopped = true;
                actualHost.RevokePendingAdmission();
            }
        }
        internal int RefusedRequests
        {
            get { lock (gate) { return refusalCount; } }
        }

        internal bool LocalReleaseHolds()
        {
            return CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending() &&
                !ServiceGate.LiveEligible() &&
                !actualHost.NativeEffectEnabled &&
                !actualHost.AuthenticatedConsentAvailable &&
                !actualHost.ProductionReleaseEligible;
        }

        // Every OS-sensitive proof remains UNAVAILABLE, not inferred from
        // the source/host-name/token string or this C# test process.
        internal bool ActualWindowsServicePrincipalApproved { get { return false; } }
        internal bool ProtectedStoreVerified { get { return false; } }
        internal bool TrustedConsentIssued { get { return false; } }
        internal bool LoadedSignedImageEnforced { get { return false; } }
        internal bool ActualP96RemediationImplemented { get { return false; } }
        internal bool NativeCredentialEffectAllowed { get { return false; } }
        internal bool RealKeyAdmissible { get { return false; } }
        internal bool ProductionReleaseEligible { get { return false; } }

        public override string ToString()
        {
            return "<P223 actual native CustodyService refusal only, NO G0/R3 authority>";
        }
    }
}
