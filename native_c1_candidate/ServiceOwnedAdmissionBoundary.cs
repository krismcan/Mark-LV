// P101: REVIEW-ONLY C# native-service-owned admission fence.
// NO production dispatch, WinCred, callback, credential material, IPC, IO,
// service install, or caller-supplied approval interface.
// Distinct from the legacy P49 PendingCustodyTransaction, which remains frozen.
// This class can only refuse requests and latch a fault/revocation/stop.
// Independent native/IPC/security review is required before ANY true dispatch.
using System;

namespace Nayeon.ByokC1
{
    internal sealed class ServiceOwnedAdmissionBoundary
    {
        private readonly object gate = new object();
        private bool revoked;
        private bool faulted;
        private bool stopped;
        private int refusedRequests;

        internal CustodyOutcome RefuseRequest(LedgerOperation operation,
            int candidateLength, bool deleteAcknowledged)
        {
            lock (gate)
            {
                // Reject all requests before any native effect. Do not accept
                // key bytes at this boundary. Metadata is untrusted and
                // cannot grant authorisation even if syntactically valid.
                ++refusedRequests;
                if (faulted) return CustodyOutcome.RecoveryRequired;
                if (revoked || stopped) return CustodyOutcome.Denied;

                bool inputShapeValid =
                    (operation == LedgerOperation.Delete &&
                     candidateLength == 0 && deleteAcknowledged) ||
                    ((operation == LedgerOperation.Save ||
                      operation == LedgerOperation.Replace) &&
                     candidateLength > 0 && candidateLength <= 2560 &&
                     !deleteAcknowledged);

                if (!inputShapeValid) return CustodyOutcome.Denied;

                // All three original P49 admission holds remain intact.
                // These checks are NOT a permission or ticket mint.
                if (!ServiceGate.LiveEligible() ||
                    PendingServiceState.LegacyEffectEntryDisabled() ||
                    PendingWinCredStore.NativeMutationAdmissionPending())
                    return CustodyOutcome.Denied;

                // An independent, security-reviewed service-owned consent
                // issuance/dispatch mechanism does not yet exist.
                // A later release cannot enable this by flipping booleans:
                // this implementation contains NO effect or "true" branch.
                return CustodyOutcome.Denied;
            }
        }

        internal void Revoke()
        {
            lock (gate) { revoked = true; }
        }

        internal void MarkFault()
        {
            lock (gate) { faulted = true; }
        }

        internal void Stop()
        {
            lock (gate) { stopped = true; revoked = true; }
        }

        internal bool IsRevoked
        { get { lock (gate) { return revoked; } } }

        internal bool IsFaulted
        { get { lock (gate) { return faulted; } } }

        internal bool IsStopped
        { get { lock (gate) { return stopped; } } }

        internal int RefusedRequests
        { get { lock (gate) { return refusedRequests; } } }

        // No mutable or test-enabled release permission is implemented.
        internal bool CanDispatchNativeCredentialEffect { get { return false; } }
        internal bool AuthenticatedConsentAvailable { get { return false; } }
        internal bool ProductionReleaseEligible { get { return false; } }
        internal bool RetryAllowed { get { return false; } }
    }
}
