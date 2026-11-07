// P98: uninstalled, dormant service COMPOSITION FENCE.
// Production-target interface sketch for qualified source review ONLY.
// Actual P49 CustodyService, ServiceGate and ProtectedAcl are NOT modified.
// Deliberately NOT included by any installed native service or key-entry build.
// No credentials, WinCred, registry, filesystem mutation or dynamic effects.
using System;

namespace Nayeon.ByokC1
{
    internal enum ServiceAdmissionDisposition
    {
        Unavailable,
        RecoveryRequired
    }

    internal sealed class DisabledServiceCompositionFence
    {
        private readonly object gate = new object();
        private bool revoked;
        private bool faulted;
        private int deniedRequests;

        internal ServiceAdmissionDisposition RefuseOpaqueRequest(string request)
        {
            lock (gate)
            {
                deniedRequests++;
                string status = ServiceGate.HandleUntrustedRequest(request);
                if (!String.Equals(status, ServiceGate.Unavailable,
                    StringComparison.Ordinal))
                {
                    faulted = true;
                    return ServiceAdmissionDisposition.RecoveryRequired;
                }
                return faulted ? ServiceAdmissionDisposition.RecoveryRequired :
                    ServiceAdmissionDisposition.Unavailable;
            }
        }

        internal ServiceAdmissionDisposition RefuseEffectAdmission()
        {
            lock (gate)
            {
                deniedRequests++;
                // Deliberately no invocation of IProtectedPendingState,
                // PendingCustodyTransaction, WinCred, listener or service.
                return faulted ? ServiceAdmissionDisposition.RecoveryRequired :
                    ServiceAdmissionDisposition.Unavailable;
            }
        }

        internal void Revoke()
        {
            lock (gate) { revoked = true; }
        }

        internal void Fault()
        {
            lock (gate) { faulted = true; }
        }

        internal int RefusalCount
        {
            get { lock (gate) { return deniedRequests; } }
        }
        internal bool IsRevoked
        {
            get { lock (gate) { return revoked; } }
        }
        internal bool RecoveryFaulted
        {
            get { lock (gate) { return faulted; } }
        }

        internal bool NativeEffectEnabled { get { return false; } }
        internal bool CredentialVerified { get { return false; } }
        internal bool TrustedConsentPresent { get { return false; } }
        internal bool ServiceInstalled { get { return false; } }
        internal bool RetryPermitted { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
    }
}
