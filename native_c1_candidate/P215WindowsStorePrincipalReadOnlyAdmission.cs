// P215 actual Windows credential STORE PRINCIPAL observation. REVIEW-ONLY.
// Compiled under C1_REVIEW_ISOLATED_ASSEMBLY; never a deployable service.
// Reads the CURRENT OS token via WindowsIdentity and only the per-session
// persistence TYPE CAPABILITY via CredGetSessionTypes. It never enumerates,
// reads, writes, deletes, migrates or displays a credential or identifier.
// It deliberately invokes the ORIGINAL P214 -> existing CustodyService
// refusal; native OS peer equality never grants effects or human consent.
#if C1_REVIEW_ISOLATED_ASSEMBLY
using System;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Security.Principal;

namespace Nayeon.ByokC1
{
    internal sealed class P215StorePrincipalObservation
    {
        internal readonly bool OsCurrentTokenRead;
        internal readonly bool CurrentHostIsLocalSystem;
        internal readonly bool CurrentHostDiffersFromLocalSystem;
        internal readonly bool ConnectedPeerSidMatchesCurrentHost;
        internal readonly bool OsPeerSignalsAgree;
        internal readonly bool GenericPersistenceQueried;
        internal readonly uint GenericCredentialMaxPersistence;
        internal readonly CustodyOutcome CurrentServiceTerminalResult;
        internal readonly CustodyOutcome CurrentServiceRequestResult;

        internal P215StorePrincipalObservation(
            bool observed, bool system, bool distinct, bool matches,
            bool osPeer, bool persisted, uint maximum,
            CustodyOutcome terminal, CustodyOutcome request)
        {
            OsCurrentTokenRead=observed;
            CurrentHostIsLocalSystem=system;
            CurrentHostDiffersFromLocalSystem=distinct;
            ConnectedPeerSidMatchesCurrentHost=matches;
            OsPeerSignalsAgree=osPeer;
            GenericPersistenceQueried=persisted;
            GenericCredentialMaxPersistence=maximum;
            CurrentServiceTerminalResult=terminal;
            CurrentServiceRequestResult=request;
        }

        // The native Windows API reports a MAXIMUM PER-SESSION persistence
        // capability, not credential ownership or existence. A SAME-user
        // CredPersistLocalMachine target is NOT shared across principals.
        internal bool ApprovedServiceStorePrincipal { get { return false; } }
        internal bool OwnProtectedServiceCredentialTarget { get { return false; } }
        internal bool AuthorizedCrossPrincipalMigration { get { return false; } }
        internal bool LegacyPythonWinCredRouteRetired { get { return false; } }
        internal bool AuthorizedStoreReadWrite { get { return false; } }
        internal bool SignedServiceInstalled { get { return false; } }
        internal bool AuthenticatedHumanConsent { get { return false; } }
        internal bool ProtectedOneUseGrant { get { return false; } }
        internal bool WindowsMachinePolicyApproved { get { return false; } }
        internal bool RealKeyPilotAuthorized { get { return false; } }
        internal bool ProductionReleaseAuthorized { get { return false; } }

        public override string ToString()
        {
            // Do not leak actual token SIDs, account names, pipe names,
            // usernames, service paths, secrets or credential target IDs.
            return "<P215 OS account and persistence capability observation; service store HOLD>";
        }
    }

    internal static class P215WindowsStorePrincipalReadOnlyAdmission
    {
        // Native Windows CredGetSessionTypes: READ-ONLY capability observation,
        // no credential target argument, WinCred pointer or secret output.
        // CRED_TYPE_MAXIMUM=8; CRED_TYPE_GENERIC=1.
        private const uint CredentialTypeMaximum=8;
        private const int GenericTypeIndex=1;
        [DllImport("advapi32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredGetSessionTypes(
            uint maximumPersistCount, [Out] uint[] maximumPersist);

        internal static P215StorePrincipalObservation ObserveAndRefuse(
            NamedPipeServerStream alreadyConnectedPeer,
            CustodyService existingCandidate,
            ServiceBoundRequestIdentity untrustedClaim)
        {
            // IMPORTANT: this invokes original P214 integration and actual
            // existing CustodyService terminal/refusal, not a standalone fake.
            P214ActualWindowsHostRefusalObservation original=
                P214ActualWindowsHostReadOnlyIntegration.ObserveAndRefuse(
                    alreadyConnectedPeer,existingCandidate,untrustedClaim);
            bool currentObserved=false,system=false,distinct=false;
            bool matches=false,wasQueried=false;
            uint maxPersist=0;

            try
            {
                using(WindowsIdentity current=WindowsIdentity.GetCurrent(false))
                {
                    SecurityIdentifier localSystem=new SecurityIdentifier(
                        WellKnownSidType.LocalSystemSid,null);
                    if(current!=null && current.User!=null)
                    {
                        currentObserved=true;
                        system=current.User.Equals(localSystem);
                        distinct=!system;
                        if (alreadyConnectedPeer!=null &&
                            alreadyConnectedPeer.IsConnected)
                        {
                            OsPipePeerObservation connected=
                                WindowsPipePeerObservation.
                                    ObserveAfterClientWrite(alreadyConnectedPeer);
                            matches=connected!=null &&
                                connected.OsClientTokenObserved &&
                                String.Equals(current.User.Value,
                                    connected.OsClientSid,
                                    StringComparison.Ordinal);
                        }
                    }
                }

                uint[] values=new uint[CredentialTypeMaximum];
                if(CredGetSessionTypes(CredentialTypeMaximum,values) &&
                    values.Length>GenericTypeIndex &&
                    values[GenericTypeIndex]<=3)
                {
                    wasQueried=true;
                    maxPersist=values[GenericTypeIndex];
                }
            }
            catch(Exception)
            {
                // OS identity/persistence observation failure is UNKNOWN,
                // NEVER evidence of approval or safe cross-user migration.
                currentObserved=false;
                matches=false;
                wasQueried=false;
                maxPersist=0;
            }

            return new P215StorePrincipalObservation(
                currentObserved,system,distinct,matches,
                original.OsPeerIdentitySignalsAgree,wasQueried,maxPersist,
                original.TerminalResult,original.ClaimedRequestResult);
        }

        internal static bool AuthorizeLegacyUserVaultMigration(
            P215StorePrincipalObservation _observation, string _claimedSid,
            bool _userConfirmed, bool _adminApproved)
        {
            // False even for a matching real Windows user and asserted
            // consent; no signed broker, protected store or independent
            // security decision exists. No request may perform migration.
            return false;
        }

        internal static bool AuthorizeServiceCredentialEffect(
            P215StorePrincipalObservation _observation,
            bool _signedClaim, bool _localSystemClaim,
            bool _issuerClaim, bool _machinePolicyClaim)
        {
            return false;
        }
    }
}
#endif
