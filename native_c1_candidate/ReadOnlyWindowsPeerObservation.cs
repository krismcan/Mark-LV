// P103: disposable Windows named-pipe IDENTITY OBSERVATION, not consent.
// Review/test only: never referenced by installed CustodyService, Main,
// production credential adapter, UI or a Windows service installer.
// A Windows SID proves a connecting token, NOT user intent or permission.
// No credential bytes, approvals, native WinCred, registry, provider or keys.
using System;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;

namespace Nayeon.ByokC1
{
    internal sealed class ReadOnlyWindowsPeerObservation
    {
        internal readonly bool OsPeerWasObserved;
        internal readonly string PeerSid;
        internal readonly string ServerSid;
        internal readonly string Response;
        internal readonly bool TrustedUserConsent;
        internal readonly bool CredentialOperationAllowed;
        internal readonly bool ProductionEligible;

        internal ReadOnlyWindowsPeerObservation(bool observed,
            string peerSid, string serverSid, string response)
        {
            OsPeerWasObserved = observed;
            PeerSid = peerSid;
            ServerSid = serverSid;
            Response = response;
            TrustedUserConsent = false;
            CredentialOperationAllowed = false;
            ProductionEligible = false;
        }

        public override string ToString()
        {
            // Do not log user SID or any peer identity by default.
            return "P103_PEER_OBSERVATION_ONLY_DENIED";
        }
    }

    internal static class ReadOnlyWindowsPipeObserver
    {
        internal const string Denial = "DENIED";
        internal const string Prefix = "NayeonP103ReadOnly_";

        private static string CurrentSid()
        {
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
            {
                if (identity == null || identity.User == null)
                    throw new InvalidOperationException("No Windows identity");
                return identity.User.Value;
            }
        }

        internal static string CurrentServerSidForTest()
        {
            return CurrentSid(); // verification only, not consent
        }

        internal static PipeSecurity LimitedAccessForTest()
        {
            // Test owner plus LocalSystem and built-in administrators.
            // Never Everyone, Anonymous, Network or AuthenticatedUsers.
            // The test is not elevated or installed as a LocalSystem service.
            PipeSecurity security = new PipeSecurity();
            SecurityIdentifier owner;
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
            {
                if (identity == null || identity.User == null)
                    throw new InvalidOperationException("No Windows owner token");
                owner = identity.User;
            }
            security.SetAccessRuleProtection(true, false);
            security.AddAccessRule(new PipeAccessRule(owner,
                PipeAccessRights.ReadWrite | PipeAccessRights.CreateNewInstance,
                AccessControlType.Allow));
            security.AddAccessRule(new PipeAccessRule(
                new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null),
                PipeAccessRights.FullControl, AccessControlType.Allow));
            security.AddAccessRule(new PipeAccessRule(
                new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null),
                PipeAccessRights.FullControl, AccessControlType.Allow));
            return security;
        }

        internal static ReadOnlyWindowsPeerObservation ObserveOneForTest(
            string pipeName)
        {
            if (pipeName == null || !pipeName.StartsWith(Prefix,
                StringComparison.Ordinal) || pipeName.Length != Prefix.Length + 32)
                throw new ArgumentException("Only fresh disposable P103 pipe names");

            for (int i = Prefix.Length; i < pipeName.Length; i++)
            {
                char ch = pipeName[i];
                if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f')))
                    throw new ArgumentException("Invalid disposable pipe suffix");
            }

            string serverSid = CurrentSid();
            using (NamedPipeServerStream server = new NamedPipeServerStream(
                pipeName, PipeDirection.InOut, 1, PipeTransmissionMode.Byte,
                PipeOptions.None, 128, 128, LimitedAccessForTest()))
            {
                server.WaitForConnection(); // only invoked by the test harness
                string peerSid = null;
                bool observed = false;
                try
                {
                    server.RunAsClient(delegate
                    {
                        using (WindowsIdentity peer = WindowsIdentity.GetCurrent())
                        {
                            if (peer != null && peer.User != null)
                            {
                                peerSid = peer.User.Value;
                                observed = true;
                            }
                        }
                    });
                }
                catch (Exception)
                {
                    observed = false;
                    peerSid = null;
                }

                // Regardless of success or failure of OS peer observation,
                // the only response to an untrusted client is a denial.
                byte[] denial = Encoding.ASCII.GetBytes(Denial);
                server.Write(denial, 0, denial.Length);
                server.Flush();
                return new ReadOnlyWindowsPeerObservation(
                    observed, peerSid, serverSid, Denial);
            }
        }
    }
}
