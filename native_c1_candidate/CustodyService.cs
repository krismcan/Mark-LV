// P101 review-only service-host CANDIDATE derived from exact P49 host.
// The original P49 CustodyService.cs stays unchanged and SHA-pinned.
// This intentionally has NO service Main method, NO new privileged listener,
// NO native effect path and NO ability to start as an installed service.
// The new service-owned admission object is a permanent DENIAL fence.
using System;
using System.ServiceProcess;

namespace Nayeon.ByokC1
{
    internal sealed class CustodyService : ServiceBase
    {
        private readonly ServiceOwnedAdmissionBoundary admission;

        internal CustodyService()
        {
            this.ServiceName = ServiceGate.ServiceName;
            this.CanStop = true;
            this.AutoLog = false;
            admission = new ServiceOwnedAdmissionBoundary();
        }

        // Review surface: operation metadata ONLY, never a key or token.
        internal CustodyOutcome RefusePendingOperation(
            LedgerOperation operation, int candidateLength,
            bool deleteAcknowledged)
        {
            return admission.RefuseRequest(operation,
                candidateLength, deleteAcknowledged);
        }

        // Pure metadata, structurally validated but NOT authenticated.
        // Every request remains a denial; no key bytes or WinCred effect.
        internal CustodyOutcome RefuseBoundPendingOperation(
            ServiceBoundRequestIdentity untrustedClaim)
        {
            return admission.RefuseBoundRequest(untrustedClaim);
        }

        // Actual P49 J2 journal + HKLM anchor adapters are referenced only
        // by this service-owned read-only preflight. No IPC or authority.
        internal NativeJ2ReadOnlyResult ObserveNativeJ2CustodyReadOnly()
        { return admission.ObserveNativeJ2CustodyReadOnly(); }

        // Review-only G2 terminal boundary. Caller-provided approval booleans
        // are not accepted. No native mutation method can be reached here.
        internal CustodyOutcome RefuseUnreviewedTerminalEffect()
        { return admission.RefuseUnreviewedTerminalEffect(); }

        internal CustodyOutcome RefuseUncertainTerminalIntent()
        { return admission.RefuseUncertainTerminalIntent(); }

        internal int TerminalEffectRefusals
        { get { return admission.TerminalEffectRefusals; } }
        internal bool TerminalBoundaryObserved
        { get { return admission.TerminalBoundaryObserved; } }

        internal int StructurallyRepeatedRequestCount
        { get { return admission.StructuralReplaysRejected; } }

        internal int TrackedNonSecretRequestCount
        { get { return admission.NonSecretRequestCount; } }

        internal void RevokePendingAdmission()
        {
            admission.Revoke();
        }

        internal void FaultPendingAdmission()
        {
            admission.MarkFault();
        }

        internal bool PendingAdmissionStopped { get { return admission.IsStopped; } }
        internal bool PendingAdmissionRevoked { get { return admission.IsRevoked; } }
        internal bool PendingAdmissionFaulted { get { return admission.IsFaulted; } }
        internal int DeniedPendingRequestCount { get { return admission.RefusedRequests; } }
        internal bool NativeEffectEnabled
        { get { return admission.CanDispatchNativeCredentialEffect; } }
        internal bool AuthenticatedConsentAvailable
        { get { return admission.AuthenticatedConsentAvailable; } }
        internal bool ProductionReleaseEligible
        { get { return admission.ProductionReleaseEligible; } }

        protected override void OnStart(string[] arguments)
        {
            // Preserve the old P49 deployment gate.
            if (!ServiceGate.LiveEligible())
                throw new InvalidOperationException("Custody service is unavailable");

            // Additional candidate-specific mandatory refusal even if a
            // future edit mistakenly changes the original release gate.
            // No approval material or service installation exists here.
            throw new InvalidOperationException("Custody service is unavailable");
        }

        protected override void OnStop()
        {
            admission.Stop(); // revoke while the same service-owned monitor is held
        }

        // No Main/ServiceBase.Run or installer. This C# file can be compiled
        // ONLY as a test/library component and cannot start by itself.
    }
}
