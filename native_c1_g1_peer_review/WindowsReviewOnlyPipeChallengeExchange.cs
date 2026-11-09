// P121: unprivileged hosted-Windows REAL named-pipe challenge/echo review.
// No production listener, OS image attestation, trusted consent or WinCred.
// Exact G1 positive authority remains permanently disabled.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P121 exchange is ISOLATED REVIEW TEST ONLY, not a production service
#endif
using System;
using System.IO;
using System.IO.Pipes;
using System.Security.Cryptography;
using System.Text;

namespace Nayeon.ByokC1
{
    internal enum OsReviewOnlyExchangeState
    {
        Unavailable,
        Refused,
        EchoObservedWithoutConsent
    }

    internal sealed class OsReviewOnlyExchangeObservation
    {
        internal readonly OsReviewOnlyExchangeState State;
        internal readonly uint OsObservedClientPid;
        internal readonly bool NativeOsProcessAndSessionObserved;
        internal readonly bool NativeChallengeFrameSent;

        internal OsReviewOnlyExchangeObservation(
            OsReviewOnlyExchangeState state, uint pid,
            bool observed, bool sent)
        {
            State=state;
            OsObservedClientPid=pid;
            NativeOsProcessAndSessionObserved=observed;
            NativeChallengeFrameSent=sent;
        }
        internal bool ActualSignedInstalledBrokerAuthenticated {get{return false;}}
        internal bool TrueHumanConsentVerified {get{return false;}}
        internal bool DurableOneUseGrantIssued {get{return false;}}
        internal bool PrivilegedServiceListenerInstalled {get{return false;}}
        internal bool NativeCredentialEffectAllowed {get{return false;}}
        internal bool DiagnosticEchoOnly
        {get{return State==OsReviewOnlyExchangeState.EchoObservedWithoutConsent;}}

        internal static OsReviewOnlyExchangeObservation Unavailable()
        {return new OsReviewOnlyExchangeObservation(
            OsReviewOnlyExchangeState.Unavailable,0,false,false);}

        public override string ToString()
        {return "<P121 OS peer-bound local pipe challenge; no human consent/effect>";}
    }

    internal static class WindowsReviewOnlyPipeChallengeExchange
    {
        private const int NonceBytes=32;
        private const int DigestBytes=32;
        private const int ReadTimeoutMs=3000;

        private static bool Observed(
            NamedPipeServerStream pipe,
            out OsPipeClientProcessProvenance process,
            out OsPipeClientSessionIntegrity session)
        {
            process=WindowsPipeClientProcessProvenance.
                ObserveAfterClientWrite(pipe);
            session=WindowsPipeClientSessionIntegrity.
                ObserveAfterClientWrite(pipe);
            return process!=null && process.KernelProcessObserved &&
                session!=null && session.SessionIntegrityObserved &&
                process.OsClientProcessId!=0 &&
                process.OsClientProcessId==session.OsClientProcessId &&
                process.OsProcessCreatedUtcFileTime==
                    session.OsProcessCreatedUtcFileTime &&
                session.OsPipeSessionId==session.OsTokenSessionId &&
                !String.IsNullOrWhiteSpace(process.OsProcessTokenSid) &&
                !String.IsNullOrWhiteSpace(process.OsImagePath);
        }

        // Bind the review transcript to actual observed OS fields instead
        // of trusting a caller-supplied PID/SID/session/path. This digest is
        // NOT an application signature, protected security principal or
        // reliable proof of a message author's physical user identity.
        private static string OsPeerBindingFingerprint(
            OsPipeClientProcessProvenance p,
            OsPipeClientSessionIntegrity s)
        {
            using(var raw=new MemoryStream())
            using(var writer=new BinaryWriter(raw,Encoding.UTF8))
            {
                writer.Write("P121-read-only-peer-observation-v1");
                writer.Write(p.OsClientProcessId);
                writer.Write(p.OsProcessCreatedUtcFileTime);
                writer.Write(p.OsProcessTokenSid);
                writer.Write(p.OsImagePath);
                writer.Write(s.OsPipeSessionId);
                writer.Write(s.OsTokenSessionId);
                writer.Write(s.OsTokenIntegrityRid);
                writer.Flush();
                using(var sha=SHA256.Create())
                {
                    byte[] digest=sha.ComputeHash(raw.ToArray());
                    return BitConverter.ToString(digest).Replace("-","").
                        ToLowerInvariant();
                }
            }
        }

        // The pipe handshake byte is read by the isolated test host FIRST.
        // That lets Windows attach the impersonated client token to the
        // connected pipe. This method NEVER creates a privileged service.
        internal static OsReviewOnlyExchangeObservation RunAfterHandshake(
            NamedPipeServerStream alreadyConnectedPipe,
            ServiceBoundRequestIdentity immutableHostRequest)
        {
            if(alreadyConnectedPipe==null || immutableHostRequest==null)
                return OsReviewOnlyExchangeObservation.Unavailable();

            ReviewOnlyOperationChallenge challenge=null;
            uint pid=0;
            bool sent=false;
            try
            {
                if(!alreadyConnectedPipe.IsConnected)
                    return OsReviewOnlyExchangeObservation.Unavailable();

                OsPipeClientProcessProvenance firstProcess;
                OsPipeClientSessionIntegrity firstSession;
                if(!Observed(alreadyConnectedPipe,out firstProcess,out firstSession))
                    return OsReviewOnlyExchangeObservation.Unavailable();
                pid=firstProcess.OsClientProcessId;
                string fingerprint=OsPeerBindingFingerprint(
                    firstProcess,firstSession);

                // Real host UTC clock on the hosted Windows runner, NOT a
                // deployable privileged service clock or antirollback source.
                challenge=ReviewOnlyOperationChallenge.TryIssue(
                    immutableHostRequest,fingerprint,()=>DateTime.UtcNow.Ticks);
                if(challenge==null)
                    return OsReviewOnlyExchangeObservation.Unavailable();

                byte[] nonce=challenge.GetChallengeCopy();
                byte[] digest=challenge.GetBindingDigestCopy();
                if(nonce==null || digest==null ||
                    nonce.Length!=NonceBytes || digest.Length!=DigestBytes)
                    return OsReviewOnlyExchangeObservation.Unavailable();

                // Bounded fixed 64-byte nonsecret challenge frame.
                byte[] challengeFrame=new byte[NonceBytes+DigestBytes];
                Buffer.BlockCopy(nonce,0,challengeFrame,0,NonceBytes);
                Buffer.BlockCopy(digest,0,challengeFrame,NonceBytes,DigestBytes);
                alreadyConnectedPipe.Write(challengeFrame,0,challengeFrame.Length);
                alreadyConnectedPipe.Flush();
                sent=true;

                // A single 32-byte echoed nonce means the client could
                // read the pipe. It is not a protected signature or click.
                byte[] echoed=new byte[NonceBytes];
                if(!ReadExactBounded(alreadyConnectedPipe,echoed))
                {
                    challenge.FailClosedFault();
                    return new OsReviewOnlyExchangeObservation(
                        OsReviewOnlyExchangeState.Refused,pid,true,sent);
                }

                OsPipeClientProcessProvenance finalProcess;
                OsPipeClientSessionIntegrity finalSession;
                if(!Observed(alreadyConnectedPipe,out finalProcess,out finalSession) ||
                    !String.Equals(fingerprint,
                        OsPeerBindingFingerprint(finalProcess,finalSession),
                        StringComparison.Ordinal))
                {
                    challenge.FailClosedFault();
                    return new OsReviewOnlyExchangeObservation(
                        OsReviewOnlyExchangeState.Refused,pid,true,sent);
                }

                var verdict=challenge.ObserveEchoAndTerminate(
                    immutableHostRequest,fingerprint,echoed);
                bool matched=verdict==
                    ReviewOnlyChallengeVerdict.EchoMatchedWithoutConsentAuthority;
                return new OsReviewOnlyExchangeObservation(
                    matched?OsReviewOnlyExchangeState.EchoObservedWithoutConsent:
                            OsReviewOnlyExchangeState.Refused,
                    pid,true,sent);
            }
            catch(Exception)
            {
                if(challenge!=null)challenge.FailClosedFault();
                return new OsReviewOnlyExchangeObservation(
                    OsReviewOnlyExchangeState.Unavailable,pid,pid!=0,sent);
            }
        }

        private static bool ReadExactBounded(NamedPipeServerStream pipe,
            byte[] destination)
        {
            int offset=0;
            while(offset<destination.Length)
            {
                IAsyncResult pending=null;
                try
                {
                    pending=pipe.BeginRead(destination,offset,
                        destination.Length-offset,null,null);
                    if(!pending.AsyncWaitHandle.WaitOne(ReadTimeoutMs))
                        return false;
                    int count=pipe.EndRead(pending);
                    if(count<=0)return false;
                    offset+=count;
                }
                finally
                {
                    if(pending!=null)pending.AsyncWaitHandle.Close();
                }
            }
            return true;
        }
    }
}
