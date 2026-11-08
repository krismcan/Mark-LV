// P101: REVIEW-ONLY C# native-service-owned admission fence.
// NO production dispatch, WinCred, callback, credential material, IPC, IO,
// service install, or caller-supplied approval interface.
// Distinct from the legacy P49 PendingCustodyTransaction, which remains frozen.
// This class can only refuse requests and latch a fault/revocation/stop.
// Independent native/IPC/security review is required before ANY true dispatch.
using System;
using System.Collections.Generic;
using System.Threading;

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
        private int terminalEffectRefusals;
        private bool terminalBoundaryObserved;
        // Nonsecret terminal sequencing ONLY. This enum does not identify
        // signed UI consent, protected durable state or a WinCred permit.
        private enum TerminalDecisionPhase
        {
            Unavailable, SyntheticPrepared, SyntheticCommitted,
            SyntheticTerminalUnverified, Revoked, RecoveryRequired
        }
        private TerminalDecisionPhase terminalDecision =
            TerminalDecisionPhase.Unavailable;
#if C1_SYNTHETIC_TEST
        private int syntheticDecisionCommits;
        private int syntheticTooLateRevocations;
        // P110: synthetic fixed-pending-effect attempt counters, not credentials.
        // Present in test assemblies only; none are an actual effect permit.
        private LedgerOperation syntheticBoundOperation;
        private int syntheticEffectAttempts;
        private int syntheticUnknownEffectOutcomes;
        private bool syntheticCommitEver;
#endif
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

        // Native J2/A2 protected read-only preflight is serialized with
        // service-owned revocation/stop/fault. It is NEVER an effect permit.
        internal NativeJ2ReadOnlyResult ObserveNativeJ2CustodyReadOnly()
        {
            lock (gate)
            {
                if (faulted) return NativeJ2ReadOnlyResult.Recovery();
                if (stopped || revoked)
                    return NativeJ2ReadOnlyResult.Unavailable();
                return NativeJ2ProtectedReadOnlyPreflight.ObserveInstalledService();
            }
        }

        // P108: terminal-effect boundary for the nondeployable candidate.
        // Serialized with Revoke, Stop, MarkFault and native J2 observation
        // using THIS service-owned gate. It has no effect adapter, trusted
        // consent issuer, key input, callback, grant or WinCred capability.
        // A previous StillCurrent() result cannot be treated as a permit.
        internal CustodyOutcome RefuseUnreviewedTerminalEffect()
        {
            lock (gate)
            {
                ++terminalEffectRefusals;
                terminalBoundaryObserved = true;
                if (faulted) return CustodyOutcome.RecoveryRequired;
                if (revoked || stopped) return CustodyOutcome.Denied;
                // Missing G1 trusted issuer and G2 atomic dispatch actor:
                // terminal admission NEVER approves a native effect.
                return CustodyOutcome.Denied;
            }
        }

        // An uncertain or even reportedly durable IN_FLIGHT intent must
        // remain recovery-required; a caller can NEVER rearm this boundary.
        internal CustodyOutcome RefuseUncertainTerminalIntent()
        {
            lock (gate)
            {
                terminalBoundaryObserved = true;
                faulted = true;
                terminalDecision = TerminalDecisionPhase.RecoveryRequired;
                ++terminalEffectRefusals;
                return CustodyOutcome.RecoveryRequired;
            }
        }

        // The only POSITIVE synthetic commit API is compiled out of all
        // ordinary/production assemblies. It changes in-memory integer
        // metadata, NEVER invokes a callback or a credential API. These
        // methods exercise the SAME lock owned by the candidate host.
#if C1_SYNTHETIC_TEST
        internal void PrepareSyntheticOnly()
        {
            lock (gate)
            {
                if (revoked || stopped || faulted ||
                    terminalDecision != TerminalDecisionPhase.Unavailable)
                    throw new LedgerBlocked();
                terminalDecision = TerminalDecisionPhase.SyntheticPrepared;
            }
        }

        internal bool CommitSyntheticDecisionOnly()
        {
            lock (gate)
            {
                if (revoked || stopped || faulted ||
                    terminalDecision != TerminalDecisionPhase.SyntheticPrepared)
                    return false;
                // Exact one-use decision linearization point. Only a
                // fake integer changes; there is NO actual native effect.
                terminalDecision = TerminalDecisionPhase.SyntheticCommitted;
                ++syntheticDecisionCommits;
                syntheticCommitEver = true;
                return true;
            }
        }

        internal bool FinishSyntheticTerminalUnverified()
        {
            lock (gate)
            {
                if (faulted || stopped ||
                    terminalDecision != TerminalDecisionPhase.SyntheticCommitted)
                    return false;
                terminalDecision = TerminalDecisionPhase.SyntheticTerminalUnverified;
                return true;
            }
        }

        // P110: sealed test-only fixed operation preparation. The actual
        // candidate remains nondeployable and has NO credential effect port.
        // This is an integration proof for the existing service-owned lock,
        // NOT a signed consent issuer, credential operation or G2 release.
        internal void PrepareSyntheticFixedEffectOnly(
            LedgerOperation operation, bool destructiveAcknowledgement)
        {
            lock (gate)
            {
                bool shape =
                    operation == LedgerOperation.Delete && destructiveAcknowledgement ||
                    (operation == LedgerOperation.Save || operation == LedgerOperation.Replace) &&
                    !destructiveAcknowledgement;
                if (!shape || stopped || revoked || faulted ||
                    terminalDecision != TerminalDecisionPhase.Unavailable)
                    throw new LedgerBlocked();
                syntheticBoundOperation = operation;
                terminalDecision = TerminalDecisionPhase.SyntheticPrepared;
            }
        }

        // Single irreversible *synthetic* attempt is under the SAME lock as
        // Revoke/Stop/Fault. No injected effect callback, key, native adapter,
        // journal or provider. Gate remains held while an optional test-only
        // pause models the in-progress fixed API call. Even a completed fake
        // marker MUST return RecoveryRequired because there is no durable
        // ticket/intent/terminal witness. No automatic retry is possible.
        internal CustodyOutcome AttemptSyntheticFixedEffectOnly(
            LedgerOperation operation, ManualResetEvent entered,
            ManualResetEvent release, bool simulateUnknownNativeResult)
        {
            lock (gate)
            {
                if (faulted) return CustodyOutcome.RecoveryRequired;
                if (revoked || stopped ||
                    terminalDecision != TerminalDecisionPhase.SyntheticPrepared ||
                    operation != syntheticBoundOperation)
                    return CustodyOutcome.Denied;
                terminalDecision = TerminalDecisionPhase.SyntheticCommitted;
                syntheticCommitEver = true;
                ++syntheticDecisionCommits;
                try
                {
                    // This integer is the entire fake effect. Deliberately
                    // NO P/Invoke, WinCred, arbitrary callback or user data.
                    ++syntheticEffectAttempts;
                    if (entered != null) entered.Set();
                    if (release != null && !release.WaitOne(3000))
                        throw new LedgerBlocked();
                    if (simulateUnknownNativeResult)
                        throw new LedgerBlocked();
                }
                catch (Exception)
                {
                    ++syntheticUnknownEffectOutcomes;
                }
                // Missing durable G1/G3 evidence makes every fake attempt
                // unreleasable, irrespective of apparent success.
                faulted = true;
                terminalDecision = TerminalDecisionPhase.RecoveryRequired;
                return CustodyOutcome.RecoveryRequired;
            }
        }

        internal int SyntheticEffectAttempts
        { get { lock (gate) { return syntheticEffectAttempts; } } }
        internal int SyntheticUnknownEffectOutcomes
        { get { lock (gate) { return syntheticUnknownEffectOutcomes; } } }

        internal int SyntheticDecisionCommits
        { get { lock (gate) { return syntheticDecisionCommits; } } }
        internal int SyntheticTooLateRevocations
        { get { lock (gate) { return syntheticTooLateRevocations; } } }
#endif

        internal int TerminalEffectRefusals
        { get { lock (gate) { return terminalEffectRefusals; } } }
        internal bool TerminalBoundaryObserved
        { get { lock (gate) { return terminalBoundaryObserved; } } }

        internal int StructuralReplaysRejected
        { get { lock (gate) { return structuralReplaysRejected; } } }

        internal int NonSecretRequestCount
        { get { lock (gate) { return seenUntrustedRequests.Count; } } }

        internal void Revoke()
        {
            lock (gate)
            {
                bool wasAlreadyRevoked = revoked;
                revoked = true;
                if (terminalDecision == TerminalDecisionPhase.SyntheticPrepared)
                    terminalDecision = TerminalDecisionPhase.Revoked;
#if C1_SYNTHETIC_TEST
                if (!wasAlreadyRevoked && syntheticCommitEver)
                    ++syntheticTooLateRevocations;
#endif
                // Once a decision committed, a late cancel MUST NOT
                // turn its possible effect into an asserted non-effect.
            }
        }

        internal void MarkFault()
        {
            lock (gate)
            {
                faulted = true;
                terminalDecision = TerminalDecisionPhase.RecoveryRequired;
            }
        }

        internal void Stop()
        {
            lock (gate)
            {
                stopped = true;
                revoked = true;
                if (terminalDecision == TerminalDecisionPhase.SyntheticCommitted ||
                    terminalDecision == TerminalDecisionPhase.SyntheticTerminalUnverified)
                {
                    // Stop after a possible attempt is UNKNOWN, never
                    // evidence of cancellation or a safe automatic retry.
                    faulted = true;
                    terminalDecision = TerminalDecisionPhase.RecoveryRequired;
                }
                else if (terminalDecision == TerminalDecisionPhase.SyntheticPrepared)
                    terminalDecision = TerminalDecisionPhase.Revoked;
            }
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
