using System;
using System.Runtime.CompilerServices;

[assembly: InternalsVisibleTo("P304.ProductService.Tests")]
[assembly: InternalsVisibleTo("P305.ProductService.Tests")]

namespace Nayeon.ByokC1.Service
{
    internal enum LifecycleState { Created, Starting, ActiveDenied, Stopped, Faulted, Disposed }

    // Immutable observations, never capabilities or proof of OS service dispatch.
    internal sealed class ServiceReadiness
    {
        internal readonly LifecycleState State;
        internal string Authorization { get { return "NOT AUTHORIZED"; } }
        internal string ReleaseDisposition { get { return "HOLD"; } }
        internal string Reason { get { return "Not safe: custody, client admission and qualified SEC03/04 are not established."; } }
        internal bool ClientAdmissionAllowed { get { return false; } }
        internal bool CredentialOperationsAllowed { get { return false; } }
        internal ServiceReadiness(LifecycleState state) { State = state; }
    }

    // Nonsecret domain state only. No injected ports, delegates, payloads or effects.
    // Startup transitions describe lifecycle, and can never authorize an operation.
    internal sealed class LifecycleCoordinator : IDisposable
    {
        private readonly object gate = new object();
        private LifecycleState state = LifecycleState.Created;

        internal void BeginStart()
        {
            lock (gate)
            {
                if (state != LifecycleState.Created) RejectTransition();
                state = LifecycleState.Starting;
            }
        }

        internal void CompleteStart()
        {
            lock (gate)
            {
                if (state != LifecycleState.Starting) RejectTransition();
                state = LifecycleState.ActiveDenied;
            }
        }

        private void RejectTransition()
        {
            if (state == LifecycleState.Created || state == LifecycleState.Starting ||
                state == LifecycleState.ActiveDenied) state = LifecycleState.Faulted;
            throw new InvalidOperationException("Lifecycle transition denied; no restart.");
        }

        internal ServiceReadiness Observe()
        { lock (gate) { return new ServiceReadiness(state); } }

        // No secret-bearing operation API exists. These queries serialize with closure.
        internal bool DenyClientAdmission() { lock (gate) { return false; } }
        internal bool DenyCredentialOperation() { lock (gate) { return false; } }

        internal void Stop()
        {
            lock (gate)
            {
                if (state != LifecycleState.Faulted && state != LifecycleState.Disposed)
                    state = LifecycleState.Stopped;
            }
        }

        internal void Fault()
        {
            lock (gate)
            {
                if (state != LifecycleState.Stopped && state != LifecycleState.Disposed)
                    state = LifecycleState.Faulted;
            }
        }

        public void Dispose() { lock (gate) { state = LifecycleState.Disposed; } }
    }
}
