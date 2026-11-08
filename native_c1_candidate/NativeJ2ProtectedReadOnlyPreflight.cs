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

    // The fixed-path candidate reader has NO write-capable journal or registry
    // class in the allowlisted production-shaped review assembly.
    // Structural observations remain NON-AUTHORITY even when consistent.
    internal static class NativeJ2ProtectedReadOnlyPreflight
    {
        internal static NativeJ2ReadOnlyResult ObserveInstalledService()
        {
            return CandidateProtectedReadOnlySnapshot.ObserveInstalledService();
        }
    }
}
