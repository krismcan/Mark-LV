// P101: REVIEW-ONLY C# native-service-owned admission fence.
// NO production dispatch, WinCred, callback, credential material, IPC, IO,
// service install, or caller-supplied approval interface.
// Distinct from the legacy P49 PendingCustodyTransaction, which remains frozen.
// This class can only refuse requests and latch a fault/revocation/stop.
// Independent native/IPC/security review is required before ANY true dispatch.
using System;
using System.Collections.Generic;

namespace Nayeon.ByokC1
{
    internal sealed class ServiceOwnedAdmissionBoundary
    {
        private readonly object gate = new object();
        private bool revoked;
        private bool faulted;
        private bool stopped;
        private int refusedRequests;
        private int structuralReplaysRejected;
        // Bounded NON-authority bookkeeping only. Untrusted duplicate data
        // cannot create a consent session or grant native effect permission.
        private readonly HashSet<string> seenUntrustedRequests =
            new HashSet<string>(StringComparer.Ordinal);
        private const int MaxTrackedUntrustedRequests = 128;

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

        internal CustodyOutcome RefuseBoundRequest(ServiceBoundRequestIdentity claim)
        {
            lock (gate)
            {
                ++refusedRequests;
                if (faulted) return CustodyOutcome.RecoveryRequired;
                if (revoked || stopped || claim == null)
                    return CustodyOutcome.Denied;

                // The service reads its own clock. Even a syntactically valid
                // digest, session and expiry are UNTRUSTED caller metadata,
                // not an elevated user's one-use approval.
                if (!claim.HasSafeClockWindow(DateTime.UtcNow.Ticks))
                    return CustodyOutcome.Denied;

                string replayKey = claim.NonSecretReplayKey;
                if (seenUntrustedRequests.Contains(replayKey))
                {
                    ++structuralReplaysRejected;
                    return CustodyOutcome.Denied;
                }
                // Do not allow arbitrary unauthenticated requests to grow
                // the service's ledger without bound or latch a recovery
                // fault merely by saturating their metadata.
                if (seenUntrustedRequests.Count >= MaxTrackedUntrustedRequests)
                    return CustodyOutcome.Denied;

                seenUntrustedRequests.Add(replayKey);
                // All original P49 real service/legacy/WinCred guards remain
                // untouched. This is a structurally bound DENIAL boundary
                // with NO issuance, effect or authority path.
                if (!ServiceGate.LiveEligible() ||
                    PendingServiceState.LegacyEffectEntryDisabled() ||
                    PendingWinCredStore.NativeMutationAdmissionPending())
                    return CustodyOutcome.Denied;
                return CustodyOutcome.Denied;
            }
        }

        internal int StructuralReplaysRejected
        { get { lock (gate) { return structuralReplaysRejected; } } }

        internal int NonSecretRequestCount
        { get { lock (gate) { return seenUntrustedRequests.Count; } } }

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
