// P95 READ-ONLY NATIVE LEDGER PREFLIGHT (test-source review).
// Uses the authentic unchanged disabled P49 CustodyLedger C# codec.
// NEVER an authenticated storage reader, service admission controller, effect
// permit, provider validation, IPC route, WinCred adapter or installation.
using System;

namespace Nayeon.ByokC1
{
    internal enum LedgerReadoutDisposition
    {
        Unavailable,
        RecoveryRequired,
        StructuralInitialUntrusted,
        StructuralPendingUnverified,
        StructuralAbsentUnverified
    }

    internal sealed class LedgerReadout
    {
        internal readonly LedgerReadoutDisposition Disposition;
        internal bool EffectPermitted { get { return false; } }
        internal bool RetryPermitted { get { return false; } }
        internal bool CredentialVerified { get { return false; } }
        internal bool RecoveryCleared { get { return false; } }
        internal bool TrustedAuthorityGranted { get { return false; } }
        internal LedgerReadout(LedgerReadoutDisposition disposition)
        {
            Disposition = disposition;
        }
        public override string ToString()
        {
            return "Read-only structural custody view (no authority)";
        }
    }

    internal static class NativeLedgerPreflight
    {
        // Every boolean is only an untrusted review fixture assertion.
        // No arbitrary caller can authenticate the OS principal, installer,
        // registry anchor, enrollment witness or consent by setting it true.
        // No result grants a production effect under any combination.
        internal static LedgerReadout InspectUntrustedInputs(
            string journal, string anchor, bool? pendingPresent,
            bool servicePrincipalClaim,
            bool osProtectedJournalClaim,
            bool osProtectedAnchorClaim,
            bool enrollmentWitnessClaim,
            bool persistentFaultClearClaim)
        {
            try
            {
                if (!servicePrincipalClaim || !osProtectedJournalClaim ||
                    !osProtectedAnchorClaim || !enrollmentWitnessClaim ||
                    !persistentFaultClearClaim)
                    return new LedgerReadout(LedgerReadoutDisposition.Unavailable);
                // Missing history is never bootstrap authority. An unknown
                // credential-presence observation cannot clear recovery.
                if (String.IsNullOrEmpty(journal) ||
                    String.IsNullOrEmpty(anchor) || !pendingPresent.HasValue)
                    return new LedgerReadout(LedgerReadoutDisposition.RecoveryRequired);

                LedgerPhase phase = CustodyLedger.Verify(journal, anchor);
                if (phase == LedgerPhase.InFlight)
                    return new LedgerReadout(LedgerReadoutDisposition.RecoveryRequired);
                if (phase == LedgerPhase.Initial)
                    return new LedgerReadout(
                        pendingPresent.Value
                            ? LedgerReadoutDisposition.RecoveryRequired
                            : LedgerReadoutDisposition.StructuralInitialUntrusted);
                if (phase == LedgerPhase.CommittedUnverified)
                    return new LedgerReadout(
                        pendingPresent.Value
                            ? LedgerReadoutDisposition.StructuralPendingUnverified
                            : LedgerReadoutDisposition.RecoveryRequired);
                if (phase == LedgerPhase.CommittedAbsent)
                    return new LedgerReadout(
                        pendingPresent.Value
                            ? LedgerReadoutDisposition.RecoveryRequired
                            : LedgerReadoutDisposition.StructuralAbsentUnverified);
                return new LedgerReadout(LedgerReadoutDisposition.RecoveryRequired);
            }
            catch (Exception)
            {
                // Constant nonsecret, no detail from journal, source or key.
                return new LedgerReadout(LedgerReadoutDisposition.RecoveryRequired);
            }
        }
    }
}
