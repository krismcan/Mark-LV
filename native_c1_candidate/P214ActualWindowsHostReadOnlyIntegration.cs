// P214 REAL Windows OS peer -> actual current CustodyService denial integration.
// TEST/SECURITY REVIEW ASSEMBLY ONLY. This is not a deployable service,
// broker, authenticator, installer, IPC contract, or credential effect.
// It composes unchanged P113-116 native OS observations and invokes the
// original native C1 service-owned terminal refusal, never a grant.
// No client-supplied SID/PID/path/signer/approval can influence a permit.
#if C1_REVIEW_ISOLATED_ASSEMBLY
using System;
using System.IO.Pipes;

namespace Nayeon.ByokC1
{
    internal sealed class P214ActualWindowsHostRefusalObservation
    {
        internal readonly bool OsImpersonatedPeerObserved;
        internal readonly bool OsClientProcessObserved;
        internal readonly bool OsSessionAndIntegrityObserved;
        internal readonly bool OsPeerIdentitySignalsAgree;
        internal readonly bool OsFileSignaturePolicyAttempted;
        internal readonly bool OsFileSignaturePolicyAccepted;
        internal readonly CustodyOutcome TerminalResult;
        internal readonly CustodyOutcome ClaimedRequestResult;

        internal P214ActualWindowsHostRefusalObservation(
            bool peer, bool process, bool session, bool agree,
            bool signedPolicyAttempted, bool signedPolicyAccepted,
            CustodyOutcome result, CustodyOutcome claimed)
        {
            OsImpersonatedPeerObserved = peer;
            OsClientProcessObserved = process;
            OsSessionAndIntegrityObserved = session;
            OsPeerIdentitySignalsAgree = agree;
            OsFileSignaturePolicyAttempted = signedPolicyAttempted;
            OsFileSignaturePolicyAccepted = signedPolicyAccepted;
            TerminalResult = result;
            ClaimedRequestResult = claimed;
        }

        // These are permanently FALSE in both positive and negative OS
        // observation scenarios. No approved signer, signed loaded image,
        // user presence or protected one-use custody issuer exists.
        internal bool ApprovedInstalledServiceSigner { get { return false; } }
        internal bool TrustedClientImageSectionAttested { get { return false; } }
        internal bool TrustedInteractiveHumanConsent { get { return false; } }
        internal bool ProtectedOneUseApprovalIssued { get { return false; } }
        internal bool MachineCodeIntegrityAdmitted { get { return false; } }
        internal bool LegacyP132PythonEffectEliminated { get { return false; } }
        internal bool CredentialEffectAuthorized { get { return false; } }
        internal bool RealKeyEligible { get { return false; } }
        internal bool ProductionReleaseEligible { get { return false; } }

        public override string ToString()
        { return "<P214 Windows peer observed, CustodyService denied, no real-key authority>"; }
    }

    internal static class P214ActualWindowsHostReadOnlyIntegration
    {
        internal static P214ActualWindowsHostRefusalObservation ObserveAndRefuse(
            NamedPipeServerStream connectedPeer,
            CustodyService existingCandidateHost,
            ServiceBoundRequestIdentity untrustedClaim)
        {
            bool peer=false, process=false, session=false;
            bool agrees=false, sigAttempted=false, sigAccepted=false;
            CustodyOutcome terminal=CustodyOutcome.Denied;
            CustodyOutcome request=CustodyOutcome.Denied;

            // Existing candidate host: no service Main or actual effect.
            // OS inspection never acts as a positive admission guard.
            try
            {
                if (connectedPeer!=null && connectedPeer.IsConnected)
                {
                    OsPipePeerObservation p=
                        WindowsPipePeerObservation.ObserveAfterClientWrite(connectedPeer);
                    OsPipeClientProcessProvenance proc=
                        WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(
                            connectedPeer);
                    OsPipeClientSessionIntegrity ses=
                        WindowsPipeClientSessionIntegrity.ObserveAfterClientWrite(
                            connectedPeer);
                    OsWintrustReviewObservation win=
                        WindowsWintrustFilePolicyReview.
                            ObserveConnectedClientFilePolicyOnly(connectedPeer);

                    peer=p!=null && p.OsClientTokenObserved;
                    process=proc!=null && proc.KernelProcessObserved;
                    session=ses!=null && ses.SessionIntegrityObserved;
                    sigAttempted=win!=null && win.NativePolicyAttempted;
                    sigAccepted=win!=null && win.NativePolicyAccepted;
                    agrees=peer && process && session &&
                        !String.IsNullOrWhiteSpace(p.OsClientSid) &&
                        String.Equals(p.OsClientSid,proc.OsProcessTokenSid,
                            StringComparison.Ordinal) &&
                        proc.OsClientProcessId==ses.OsClientProcessId &&
                        proc.OsProcessCreatedUtcFileTime==
                            ses.OsProcessCreatedUtcFileTime &&
                        ses.OsPipeSessionId==ses.OsTokenSessionId;

                    // Even if all signals agree, verified file policy alone
                    // does not authenticate the loaded image or human click.
                    // P116 signed file observation cannot issue consent.
                }
            }
            catch(Exception)
            {
                // Missing/failed OS observation is denial, never authority.
                agrees=false;
            }
            if (existingCandidateHost!=null)
            {
                // This invokes the ACTUAL existing native CustodyService
                // host/admission object, not a newly isolated fake gate.
                terminal=existingCandidateHost.RefuseUnreviewedTerminalEffect();
                if (untrustedClaim!=null)
                    request=existingCandidateHost.
                        RefuseBoundPendingOperation(untrustedClaim);
            }

            return new P214ActualWindowsHostRefusalObservation(
                peer,process,session,agrees,sigAttempted,sigAccepted,
                terminal,request);
        }
    }
}
#endif
