// P113 — actual Windows named-pipe peer TOKEN observation.
// G1 development only. It is NOT human consent, application provenance,
// elevated/signed UI identity, a one-use grant, a credential or an effect.
// The class does NOT create a named pipe, install a listener, issue approval,
// access WinCred or parse untrusted application-level identity claims.
// A future independently reviewed service must own a trusted endpoint,
// OS identity, caller integrity/session, signed client provenance and
// durable binding before any credential effect can be considered.
using System;
using System.IO.Pipes;
using System.Security.Principal;

namespace Nayeon.ByokC1
{
    internal enum OsPipePeerState
    {
        Unavailable,
        ObservedImpersonatedClient
    }

    internal sealed class OsPipePeerObservation
    {
        internal readonly OsPipePeerState State;
        internal readonly string OsClientSid;

        internal OsPipePeerObservation(OsPipePeerState state, string osClientSid)
        {
            State = state;
            OsClientSid = osClientSid;
        }

        internal bool OsClientTokenObserved
        { get { return State == OsPipePeerState.ObservedImpersonatedClient; } }

        // Observing a Windows account SID does not attest a PARTICULAR
        // signed UI binary, a human confirmation or a one-use request.
        internal bool TrustedClientImageVerified { get { return false; } }
        internal bool HumanConsentVerified { get { return false; } }
        internal bool OneUseGrantIssued { get { return false; } }
        internal bool CanAuthorizeCredentialEffect { get { return false; } }

        public override string ToString()
        { return "<P113 OS peer observation only, consent and effects unavailable>"; }

        internal static OsPipePeerObservation Unavailable()
        { return new OsPipePeerObservation(OsPipePeerState.Unavailable, null); }
    }

    internal static class WindowsPipePeerObservation
    {
        // Caller must have accepted a local pipe client connection and read
        // at least one bounded, nonsecret byte so Windows has the client's
        // impersonation token. No caller-provided SID/PID/claim is accepted.
        // OS's impersonation is strictly scoped to the delegate thread.
        // Missing connection, inadequate impersonation, failures or token
        // ambiguity all fail CLOSED. This cannot mint approval.
        internal static OsPipePeerObservation ObserveAfterClientWrite(
            NamedPipeServerStream alreadyConnectedPipe)
        {
            if (alreadyConnectedPipe == null)
                return OsPipePeerObservation.Unavailable();

            try
            {
                if (!alreadyConnectedPipe.IsConnected)
                    return OsPipePeerObservation.Unavailable();

                string observedSid = null;
                bool impersonated = false;

                alreadyConnectedPipe.RunAsClient(delegate
                {
                    // 'ifImpersonating=true' prevents accidentally reporting
                    // the SERVICE's own token as the connected client's.
                    using (WindowsIdentity client = WindowsIdentity.GetCurrent(true))
                    {
                        if (client == null || client.User == null ||
                            !client.IsAuthenticated ||
                            (client.ImpersonationLevel !=
                                TokenImpersonationLevel.Impersonation &&
                             client.ImpersonationLevel !=
                                TokenImpersonationLevel.Delegation))
                            return;

                        observedSid = client.User.Value;
                        impersonated = !String.IsNullOrWhiteSpace(observedSid);
                    }
                });

                if (!impersonated)
                    return OsPipePeerObservation.Unavailable();

                return new OsPipePeerObservation(
                    OsPipePeerState.ObservedImpersonatedClient,
                    observedSid);
            }
            catch (Exception)
            {
                // Never report caller authority on a broken/unverifiable pipe.
                return OsPipePeerObservation.Unavailable();
            }
        }
    }
}
