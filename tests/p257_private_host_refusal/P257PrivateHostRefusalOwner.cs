// P257 review-only composition of the unchanged actual candidate host.
// Process-local ordering only. OS custody and original P96 repair are NOT_ESTABLISHED.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !P257_EFFECT_FREE_REVIEW || C1_SYNTHETIC_TEST
#error P257 requires isolated effect-free review without synthetic dispatch
#endif
using System;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class P257PrivateHostRefusalOwner : IDisposable
    {
        private readonly object gate = new object();
        private readonly CustodyService actualHost = new CustodyService();
        private bool disposed;

        internal P257PrivateHostRefusalOwner() { }

        internal CustodyOutcome RefuseRequest(ServiceBoundRequestIdentity claim)
        {
            RejectReentry();
            lock (gate)
            {
                RequireOpenLifetime();
                return RefuseUnderGate(claim);
            }
        }

        internal CustodyOutcome Revoke()
        {
            RejectReentry();
            lock (gate)
            {
                RequireOpenLifetime();
                actualHost.RevokePendingAdmission();
                return RefuseUnderGate(null);
            }
        }

        // Review-lifetime stop. Actual SCM OnStop is outside this experiment.
        internal CustodyOutcome Stop()
        {
            RejectReentry();
            lock (gate)
            {
                RequireOpenLifetime();
                actualHost.RevokePendingAdmission();
                return RefuseUnderGate(null);
            }
        }

        internal CustodyOutcome Fault()
        {
            RejectReentry();
            lock (gate)
            {
                RequireOpenLifetime();
                actualHost.FaultPendingAdmission();
                return RefuseUnderGate(null);
            }
        }

        private CustodyOutcome RefuseUnderGate(ServiceBoundRequestIdentity claim)
        {
            // Both original host refusal calls stay inside the owner's gate,
            // including requests after revoke/stop/fault and lifecycle publication.
            CustodyOutcome request = actualHost.RefuseBoundPendingOperation(claim);
            CustodyOutcome terminal = actualHost.RefuseUnreviewedTerminalEffect();
            if (request != CustodyOutcome.Denied || terminal != CustodyOutcome.Denied ||
                actualHost.PendingAdmissionFaulted || actualHost.NativeEffectEnabled ||
                actualHost.AuthenticatedConsentAvailable || actualHost.ProductionReleaseEligible ||
                ServiceGate.LiveEligible() ||
                !CandidateCredentialEffectHold.LegacyEffectEntryDisabled() ||
                !CandidateCredentialEffectHold.NativeMutationAdmissionPending())
                return CustodyOutcome.RecoveryRequired;
            return CustodyOutcome.Denied;
        }

        private void RejectReentry()
        {
            if (Monitor.IsEntered(gate))
                throw new InvalidOperationException("Recursive review owner entry refused");
        }

        private void RequireOpenLifetime()
        {
            if (disposed)
                throw new ObjectDisposedException("P257PrivateHostRefusalOwner");
        }

        public void Dispose()
        {
            RejectReentry();
            lock (gate)
            {
                if (disposed) return;
                disposed = true;
                try
                {
                    actualHost.RevokePendingAdmission();
                    actualHost.RefuseUnreviewedTerminalEffect();
                }
                finally
                {
                    actualHost.Dispose();
                }
            }
        }

        internal bool RealKeyAdmissible { get { return false; } }
        internal bool ProductionReleaseEligible { get { return false; } }
        internal bool OsCustodyEstablished { get { return false; } }
    }
}
