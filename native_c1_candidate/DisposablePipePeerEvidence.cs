// P103: REAL Windows named-pipe peer-observation in a disposable,
// same-user, unprivileged RESEARCH process. Never an installed service.
// This proves that seeing a Windows SID is INSUFFICIENT for trusted consent.
// No user key, WinCred, system service, HKLM, secret or external networking.
using System;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class DisposablePeerObservation
    {
        internal readonly bool PeerSidObservable;
        internal readonly bool PeerSameWindowsUser;
        internal readonly bool ProtocolClaimedTrusted;
        internal readonly bool SecurityExceptionObserved;

        internal DisposablePeerObservation(bool observable, bool sameUser,
            bool fakeTrustedClaim, bool securityError)
        {
            PeerSidObservable = observable;
            PeerSameWindowsUser = sameUser;
            ProtocolClaimedTrusted = fakeTrustedClaim;
            SecurityExceptionObserved = securityError;
        }

        // These are immutable and ALWAYS false, even with a matching SID.
        internal bool VerifiedTrustedUi { get { return false; } }
        internal bool ElevatedConsentGranted { get { return false; } }
        internal bool CanDispatchNativeEffect { get { return false; } }
        internal bool ProductionEligible { get { return false; } }

        public override string ToString()
        {
            // Do not log an actual SID, user name, nonce or claim body.
            return "P103 disposable Windows peer observation (DENY ONLY)";
        }
    }

    internal static class DisposablePipePeerProbe
    {
        internal static DisposablePeerObservation Observe(int syntheticByte)
        {
            // Local unprivileged pipe, unique per test. Never use the real
            // privileged service name or its operating-system namespace.
            string pipeName = "nayeon_p103_disposable_" +
                Guid.NewGuid().ToString("N");

            SecurityIdentifier localUser =
                WindowsIdentity.GetCurrent().User;
            if (localUser == null)
                return new DisposablePeerObservation(false,false,false,true);

            PipeSecurity security = new PipeSecurity();
            security.SetAccessRuleProtection(true,false);
            security.AddAccessRule(new PipeAccessRule(localUser,
                PipeAccessRights.FullControl, AccessControlType.Allow));

            bool observable = false;
            bool matchingSid = false;
            bool claimedTrusted = false;
            bool securityFailure = false;
            Exception workerFailure = null;

            // Bound all client operations; never block the real product.
            using (var server = new NamedPipeServerStream(pipeName,
                PipeDirection.InOut, 1, PipeTransmissionMode.Byte,
                PipeOptions.None, 256, 256, security))
            {
                Thread worker = new Thread(() =>
                {
                    try
                    {
                        using (var client = new NamedPipeClientStream(
                            ".", pipeName, PipeDirection.InOut,
                            PipeOptions.None,
                            TokenImpersonationLevel.Impersonation))
                        {
                            client.Connect(3000);
                            client.WriteByte((byte)syntheticByte);
                            client.Flush();
                            // The denial byte is a REQUIRED consequence,
                            // never a token, capability or successful consent.
                            int reply=client.ReadByte();
                            if (reply != 0) throw new InvalidOperationException(
                                "Unexpected non-denial reply from pipe");
                        }
                    }
                    catch (Exception e) { workerFailure=e; }
                });
                worker.IsBackground = true;
                worker.Start();

                try
                {
                    server.WaitForConnection();
                    int input=server.ReadByte();
                    claimedTrusted=(input==0x54); // 'T' == forged trusted-UI claim
                    // Read identity using the OS impersonation context only.
                    // Same-user SID matching cannot identify an application,
                    // authenticate a UI ceremony or prove actual consent.
                    server.RunAsClient(() =>
                    {
                        try
                        {
                            var identity=WindowsIdentity.GetCurrent();
                            observable=identity.User!=null;
                            matchingSid=observable &&
                                identity.User.Equals(localUser);
                        }
                        catch (Exception) { securityFailure=true; }
                    });
                    // Every observed peer/claim gets the exact same deny.
                    server.WriteByte(0);
                    server.Flush();
                }
                catch (Exception)
                {
                    securityFailure=true;
                    if (server.IsConnected)
                    {
                        try { server.WriteByte(0); server.Flush(); }
                        catch (Exception) {}
                    }
                }
                if (!worker.Join(4000))
                    throw new TimeoutException("Disposable pipe worker failed to end");
            }

            if (workerFailure!=null)
                throw new InvalidOperationException(
                    "Disposable pipe peer roundtrip failed",workerFailure);

            return new DisposablePeerObservation(observable,
                matchingSid, claimedTrusted, securityFailure);
        }
    }
}
