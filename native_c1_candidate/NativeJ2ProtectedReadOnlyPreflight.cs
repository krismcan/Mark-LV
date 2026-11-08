// P106: service-private, read-only original-native J2/A2 recovery preflight.
// CANDIDATE ONLY. Requires real original P49 protected journal + registry
// adapters; does not accept caller-provided evidence, trusted flags, paths,
// IPC claims, consent or keys. Does not call WinCred or mutate OS state.
// A structurally consistent history is NOT proof of pending key presence,
// anti-rollback, consent, a verified native effect, or production readiness.
using System;

namespace Nayeon.ByokC1
{
    internal enum NativeJ2ReadOnlyKind
    {
        Unavailable,
        RecoveryRequired,
        StructuralInitial,
        JournalClaimsStoredUnverified,
        JournalClaimsAbsentUnverified
    }

    internal sealed class NativeJ2ReadOnlyResult
    {
        internal readonly NativeJ2ReadOnlyKind Kind;
        private NativeJ2ReadOnlyResult(NativeJ2ReadOnlyKind kind) { Kind = kind; }

        internal static NativeJ2ReadOnlyResult Unavailable()
        { return new NativeJ2ReadOnlyResult(NativeJ2ReadOnlyKind.Unavailable); }

        internal static NativeJ2ReadOnlyResult Recovery()
        { return new NativeJ2ReadOnlyResult(NativeJ2ReadOnlyKind.RecoveryRequired); }

        internal static NativeJ2ReadOnlyResult Structural(LedgerPhase phase)
        {
            switch (phase)
            {
                case LedgerPhase.Initial:
                    return new NativeJ2ReadOnlyResult(NativeJ2ReadOnlyKind.StructuralInitial);
                case LedgerPhase.InFlight:
                    // An interrupted or uncertain native operation MUST be
                    // recovery-required, never an informational healthy status.
                    return Recovery();
                case LedgerPhase.CommittedUnverified:
                    return new NativeJ2ReadOnlyResult(NativeJ2ReadOnlyKind.JournalClaimsStoredUnverified);
                case LedgerPhase.CommittedAbsent:
                    return new NativeJ2ReadOnlyResult(NativeJ2ReadOnlyKind.JournalClaimsAbsentUnverified);
                default: return Recovery();
            }
        }

        // Never promote structural history into authenticated consent, trust,
        // a live service, a native effect or a retry after unknown outcome.
        internal bool AuthenticatedConsent { get { return false; } }
        internal bool PendingPresenceVerified { get { return false; } }
        internal bool DurableIndependentWitnessVerified { get { return false; } }
        internal bool CanDispatchNativeEffect { get { return false; } }
        internal bool ProductionReleaseEligible { get { return false; } }
        internal bool RetryAllowed { get { return false; } }

        public override string ToString()
        { return "P106 native protected J2 read-only structural observation; NO AUTHORITY"; }
    }

    internal static class NativeJ2ProtectedReadOnlyPreflight
    {
        internal static NativeJ2ReadOnlyResult ObserveInstalledService()
        {
            // This is a service-private candidate, not an IPC endpoint.
            // No service installation proof exists, so it always short
            // circuits to UNAVAILABLE on Kristian and all ordinary runners.
            if (!ServiceGate.LiveEligible())
                return NativeJ2ReadOnlyResult.Unavailable();

            // Unexpectedly relaxed original effect gates imply tampering,
            // not an opportunity to turn this read-only diagnostic live.
            if (!PendingServiceState.LegacyEffectEntryDisabled() ||
                !PendingWinCredStore.NativeMutationAdmissionPending())
                return NativeJ2ReadOnlyResult.Recovery();

            try
            {
                if (!ProtectedAcl.VerifyInstalledCustodyDirectory())
                    return NativeJ2ReadOnlyResult.Recovery();

                // These are the exact original P49 real OS-protected adapters.
                // Registry OpenFixed enforces LocalSystem token and strict DACL.
                CustodyRegistryAnchor anchor = new CustodyRegistryAnchor();
                if (anchor.RecoveryFaulted())
                    return NativeJ2ReadOnlyResult.Recovery();
                CustodyJournalFile journal = CustodyJournalFile.ForInstalledService();

                string rawJournal = journal.ReadJournal();
                string rawAnchor = anchor.ReadAnchor();
                if (rawJournal == null || rawAnchor == null)
                    return NativeJ2ReadOnlyResult.Recovery();

                // Only the original native J2/A2 parser, NEVER the J1 reader.
                // Structural hashes alone cannot establish historic freshness.
                LedgerPhase phase = CustodyLedger.Verify(rawJournal, rawAnchor);

                // Two-store reads are not atomic; changed values must fail.
                // Even stable reads are merely a non-authoritative snapshot.
                if (!String.Equals(rawJournal, journal.ReadJournal(),
                    StringComparison.Ordinal) ||
                    !String.Equals(rawAnchor, anchor.ReadAnchor(),
                    StringComparison.Ordinal) ||
                    anchor.RecoveryFaulted())
                    return NativeJ2ReadOnlyResult.Recovery();

                return NativeJ2ReadOnlyResult.Structural(phase);
            }
            catch (Exception)
            {
                return NativeJ2ReadOnlyResult.Recovery();
            }
        }
    }
}
